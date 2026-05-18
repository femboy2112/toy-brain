"""LLM-backed PtCns implementation (Phase 2 v1; Phase 3.14 L2 cache).

Implements the same duck-typed surface as the v0 ``PtCns`` dataclass
(``eval``, ``eval_map``, ``positive_contents``, ``negative_contents``,
``neutral_contents``) so downstream code (``boundary``, ``from_eval``,
``assert_state_invariants``) accepts both implementations
interchangeably. The shared structural type is ``PtCnsLike`` declared in
``brain/tlica/ptcns.py``.

Phase 3.14 adds an L2 canonical semantic evaluation cache near
``LLMBackedPtCns``. L2 is enabled iff the wrapped client is a
``CachedClient`` (i.e. the operator selected a model-backed mode and did
not pass ``--llm-disable-cache``). L2 keys exclude the evaluated
``content_id`` / ``new_id`` so semantically equivalent evaluations under
different content IDs reuse a single model call. ``brain/tick.py`` is
untouched.

Catalog rows owned: I-LLM-01..04, I-LLMCACHE-01, I-LLMCACHE-05..18.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

from brain.llm.client import CachedClient, LLMClient
from brain.llm.parse import PARSE_SCHEMA_VERSION, parse_consistency_eval, ParseError
from brain.llm.prompts import PROMPT_TEMPLATE, PROMPT_TEMPLATE_VERSION, RETRY_TEMPLATE
from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval
from brain.trace import CognitionTracer, NullTracer


# ---------------------------------------------------------------------------
# Phase 3.14 L2 canonical semantic evaluation cache.
# ---------------------------------------------------------------------------


# Bump rule (Phase 3.14 LOCK D / LOCK M): any change to the L2 entry
# schema or the canonicalization function requires bumping this version
# string. Bumping invalidates older L2 entries by key namespace
# separation; no migration / silent reuse.
SEMANTIC_CACHE_SCHEMA_VERSION = "llm-semantic-cache-v1"

# LOCK I / I-LLMCACHE-11: bounded L2 cache; at cap, hits still read,
# misses may call inner but do not write a new entry.
SEMANTIC_CACHE_MAX_ENTRIES = 1024

# L2 cache directory; subdirectory under the existing gitignored root.
# LOCK L / I-LLMCACHE-12: cache files are sensitive local artifacts;
# brain/.llm_cache is already gitignored, so eval_v1/ is covered.
SEMANTIC_CACHE_DIR = Path("brain/.llm_cache") / "eval_v1"


def _derive_l2_metadata(client: object) -> tuple[str, str] | None:
    """Return ``(backend_family, model_identity)`` if L2 should be enabled.

    L2 is enabled iff the outermost client is :class:`CachedClient`. In
    production this means the runtime factory wrapped a known
    model-backed transport (anthropic-api / claude-cli / codex-cli)
    because OFFLINE / MOCK are factory-rejected from caching. If
    ``--llm-disable-cache`` was set, the factory does not wrap in
    :class:`CachedClient`, so L2 stays off. Returns ``None`` when L2 is
    disabled (OFFLINE / MOCK / explicitly-disabled paths).

    For the three known model-backed inners, ``backend_family`` and
    ``model_identity`` are derived to their production values. For any
    other inner (test fakes wrapped in ``CachedClient``), the values
    are derived from the inner's class name and a short attribute fall
    back so distinct test classes still hash to distinct L2 namespaces.

    The class-name check on the inner client avoids importing
    ``brain.ui``; the I-LLMCACHE-19 dependency-direction audit relies on
    this module not importing the UI seam.
    """
    if not isinstance(client, CachedClient):
        return None
    inner = client._inner
    cls_name = type(inner).__name__
    if cls_name == "AnthropicAPIClient":
        model = getattr(inner, "model", "") or ""
        return ("anthropic-api", str(model))
    if cls_name == "ClaudeCLIClient":
        command = getattr(inner, "command", ()) or ()
        exe = str(command[0]) if command else ""
        return ("claude-cli", exe)
    if cls_name == "CodexCLIClient":
        command = getattr(inner, "command", ()) or ()
        exe = str(command[0]) if command else ""
        return ("codex-cli", exe)
    # Test-fake path: any other inner wrapped in CachedClient gets a
    # synthetic namespace. The factory never produces this path in
    # production because OFFLINE / MOCK are cache-rejected; only
    # fixtures construct CachedClient(<fake>). Using the class name
    # keeps distinct fakes isolated in the L2 keyspace.
    return (cls_name, "")


def _canonical_l2_key(
    *,
    backend_family: str,
    model_identity: str,
    existing_msi_context: tuple[tuple[str, str], ...],
    new_text: str,
) -> str:
    """Return the deterministic SHA-256 hex key for an L2 lookup.

    The key tuple is restricted to immutable ``str`` and nested
    ``tuple[str, ...]`` leaves so Python ``repr()`` is deterministic
    across processes for this closed value space.
    """
    payload = (
        SEMANTIC_CACHE_SCHEMA_VERSION,
        PROMPT_TEMPLATE_VERSION,
        PARSE_SCHEMA_VERSION,
        backend_family,
        model_identity,
        existing_msi_context,
        new_text,
    )
    return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


_VALID_PARSED_NAMES: frozenset[str] = frozenset(e.name for e in ConsistencyEval)


class LLMBackedPtCns:
    """LLM-backed ``PtCns`` implementation.

    Cache lifecycle (corrigenda C7): The internal ``_cache`` is
    per-instance and per-tick. Each ``tick(...)`` call constructs a
    fresh ``LLMBackedPtCns``; the cache starts seeded only with
    ``{COGITO_ID: PRESERVE}`` (I-LLM-03). Across-tick determinism —
    same prompt → same response across runs — is provided by
    ``CachedClient`` at the LLM transport layer, not here.

    Rationale: MSI membership changes between ticks alter the prompt
    context (the list of existing MSI contents in ``PROMPT_TEMPLATE``),
    so a prompt for content X under MSI = {cogito, A} is semantically
    different from a prompt for content X under MSI = {cogito, A, B}.
    Caching at the LLM-prompt-hash level (``CachedClient``) handles
    this correctly because different prompts → different cache keys.
    """

    def __init__(
        self,
        msi: MSI,
        content_texts: Mapping[ContentID, str],
        client: LLMClient,
        max_attempts: int = 3,
        tracer: CognitionTracer | None = None,
    ) -> None:
        """Construct an LLM-backed PtCns.

        max_attempts: Total number of LLM calls per ``eval(...)`` call
        (NOT additional attempts after the first). With
        ``max_attempts=3``, the LLM is called up to 3 times; after the
        3rd parse failure, ``ValueError`` is raised with the
        ``I-LLM-01`` tag. ``llm_protocol.py::check_I_LLM_01`` exercises
        this convention with ``MockClient(["nonsense", "still bad",
        "PRESERVE"])`` — third attempt succeeds, two parse failures
        consumed.

        tracer (Phase 2 v1.1): observation-only tracer. Emits
        ``llm.request``, ``llm.response``, ``llm.retry``,
        ``parse.success``, and ``parse.failure`` events during the
        retry loop. Default ``NullTracer()`` — zero overhead.
        """
        if max_attempts < 1:
            raise ValueError(
                f"LLMBackedPtCns: max_attempts must be >= 1, got {max_attempts}"
            )
        self._msi = msi
        self._texts = MappingProxyType(dict(content_texts))
        self._client = client
        self._max_attempts = max_attempts
        self._tracer: CognitionTracer = tracer if tracer is not None else NullTracer()
        # I-LLM-03: cogito is short-circuited at construction; never an
        # LLM call regardless of client state.
        self._cache: dict[ContentID, ConsistencyEval] = {
            COGITO_ID: ConsistencyEval.PRESERVE
        }
        # Phase 3.14 L2: derive metadata once at construction. L2 is
        # enabled iff the wrapped client is CachedClient over a known
        # model-backed transport. OFFLINE / MOCK / --llm-disable-cache
        # paths all yield ``None`` here, which disables L2 lookup and
        # write.
        self._l2_metadata: tuple[str, str] | None = _derive_l2_metadata(client)
        self._l2_dir: Path = SEMANTIC_CACHE_DIR

    @property
    def eval_map(self) -> Mapping[ContentID, ConsistencyEval]:
        """Lazily-populated map; total over ``msi.profile.domain`` only
        once every domain element has been evaluated. Tick orchestration
        is responsible for evaluating each new content before reading
        ``eval_map`` to satisfy I-RT-04.
        """
        return MappingProxyType(self._cache)

    def eval(self, content_id: ContentID) -> ConsistencyEval:
        # I-LLM-03 / I-LLMCACHE-01: L0 cached-cogito short-circuit (and
        # any subsequent cached values).
        if content_id in self._cache:
            return self._cache[content_id]

        # I-LLMCACHE-06..08: L2 canonical semantic evaluation cache.
        # The L2 key excludes the evaluated content_id; identical
        # existing_msi_context + new_text under different content IDs
        # produce the same L2 key.
        l2_key: str | None = None
        if self._l2_metadata is not None:
            backend_family, model_identity = self._l2_metadata
            l2_key = _canonical_l2_key(
                backend_family=backend_family,
                model_identity=model_identity,
                existing_msi_context=self._derive_existing_msi_context(),
                new_text=self._texts.get(content_id, ""),
            )
            cached = self._l2_lookup(l2_key, content_id=content_id)
            if cached is not None:
                self._cache[content_id] = cached
                return cached

        prompt = self._build_prompt(content_id)
        last_error: ParseError | None = None
        last_raw: str | None = None

        for attempt in range(1, self._max_attempts + 1):
            self._tracer.record(
                "llm.request",
                {"content_id": content_id, "attempt": attempt, "prompt": prompt},
            )
            start_ns = time.time_ns()
            raw = self._client.eval_consistency(prompt)
            latency_ms = (time.time_ns() - start_ns) // 1_000_000
            last_raw = raw
            self._tracer.record(
                "llm.response",
                {
                    "content_id": content_id,
                    "attempt": attempt,
                    "raw": raw,
                    "latency_ms": latency_ms,
                },
            )
            try:
                parsed = parse_consistency_eval(raw)
            except ParseError as exc:
                last_error = exc
                self._tracer.record(
                    "parse.failure",
                    {"content_id": content_id, "attempt": attempt, "raw": raw, "error": str(exc)},
                )
                if attempt < self._max_attempts:
                    self._tracer.record(
                        "llm.retry",
                        {"content_id": content_id, "attempt": attempt + 1, "reason": str(exc)},
                    )
                prompt = self._build_retry_prompt(prompt, raw, str(exc))
                continue
            self._tracer.record(
                "parse.success",
                {"content_id": content_id, "raw": raw, "parsed": parsed.name},
            )
            self._cache[content_id] = parsed
            # I-LLMCACHE-09 / I-LLMCACHE-11: write L2 only on parse
            # success and only when below cap.
            if l2_key is not None:
                self._l2_store(l2_key, parsed=parsed, content_id=content_id)
            return parsed

        # I-LLMCACHE-09: retries exhausted with no parse success -> no
        # L2 entry is written; surface a bounded skip event before
        # raising the existing I-LLM-01 error.
        if l2_key is not None:
            self._tracer.record(
                "llm.semantic_cache_skip",
                {
                    "content_id": content_id,
                    "key_prefix": l2_key[:8],
                    "reason": "parse_failure",
                },
            )
        raise ValueError(
            f"I-LLM-01 violated: PtCns.eval({content_id!r}) failed after "
            f"{self._max_attempts} attempts. Last raw response: {last_raw!r}. "
            f"Last parse error: {last_error}"
        )

    # ---- Phase 3.14 L2 helpers -------------------------------------------

    def _derive_existing_msi_context(self) -> tuple[tuple[str, str], ...]:
        """Return the existing MSI context tuple for the L2 key.

        Tuple of ``(content_id, text)`` pairs for non-cogito MSI
        contents, sorted by ``content_id`` ascending. ``text`` is taken
        from ``content_texts`` and falls back to the empty string for
        unregistered ids. The evaluated ``new_id`` is excluded by
        design (LOCK E / I-LLMCACHE-06): identical existing_msi_context
        + new_text under different new_id values must produce the same
        L2 key.
        """
        return tuple(
            (str(cid), str(self._texts.get(cid, "")))
            for cid in sorted(self._msi.contents)
            if cid != COGITO_ID
        )

    def _l2_lookup(
        self, key: str, *, content_id: ContentID
    ) -> ConsistencyEval | None:
        """Return the cached parsed enum for ``key`` or ``None``.

        Fails loud on a corrupt entry (LOCK G / I-LLMCACHE-10). Emits
        ``llm.semantic_cache_hit`` on hit, ``llm.semantic_cache_miss``
        on miss; trace payload carries the 8-char key prefix only.
        """
        path = self._l2_dir / f"{key}.json"
        if not path.exists():
            self._tracer.record(
                "llm.semantic_cache_miss",
                {"content_id": content_id, "key_prefix": key[:8]},
            )
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                f"LLMBackedPtCns L2: corrupt cache entry at {path}: "
                f"{type(exc).__name__}"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError(
                f"LLMBackedPtCns L2: corrupt cache entry at {path}: "
                "payload is not a JSON object"
            )
        if set(payload.keys()) != {"key_prefix", "parsed"}:
            raise RuntimeError(
                f"LLMBackedPtCns L2: corrupt cache entry at {path}: "
                "unexpected key set"
            )
        parsed_name = payload.get("parsed")
        if (
            not isinstance(parsed_name, str)
            or parsed_name not in _VALID_PARSED_NAMES
        ):
            raise RuntimeError(
                f"LLMBackedPtCns L2: corrupt cache entry at {path}: "
                "parsed field is not a valid ConsistencyEval name"
            )
        prefix = payload.get("key_prefix")
        if not isinstance(prefix, str) or prefix != key[:8]:
            raise RuntimeError(
                f"LLMBackedPtCns L2: corrupt cache entry at {path}: "
                "key_prefix mismatch"
            )
        self._tracer.record(
            "llm.semantic_cache_hit",
            {"content_id": content_id, "key_prefix": key[:8]},
        )
        return ConsistencyEval[parsed_name]

    def _l2_store(
        self,
        key: str,
        *,
        parsed: ConsistencyEval,
        content_id: ContentID,
    ) -> None:
        """Write an L2 entry if below cap; otherwise emit a skip event.

        Capacity check counts existing ``.json`` files under the cache
        dir (LOCK I / I-LLMCACHE-11). At cap, no entry is written and
        ``llm.semantic_cache_skip`` is emitted with ``reason="capacity"``.
        Entry payload is exactly ``{"key_prefix", "parsed"}`` — no raw
        prompt, raw response, provider metadata, or full key (LOCK L /
        I-LLMCACHE-12).
        """
        try:
            self._l2_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(
                f"LLMBackedPtCns L2: cannot create cache dir {self._l2_dir}: "
                f"{type(exc).__name__}"
            ) from exc
        existing = list(self._l2_dir.glob("*.json"))
        path = self._l2_dir / f"{key}.json"
        if path.exists():
            # Already cached; no write required. Treat as a successful
            # no-op store so observability stays consistent.
            return
        if len(existing) >= SEMANTIC_CACHE_MAX_ENTRIES:
            self._tracer.record(
                "llm.semantic_cache_skip",
                {
                    "content_id": content_id,
                    "key_prefix": key[:8],
                    "reason": "capacity",
                },
            )
            return
        payload = {"key_prefix": key[:8], "parsed": parsed.name}
        path.write_text(json.dumps(payload), encoding="utf-8")
        self._tracer.record(
            "llm.semantic_cache_store",
            {"content_id": content_id, "key_prefix": key[:8]},
        )

    @property
    def positive_contents(self) -> frozenset[ContentID]:
        return frozenset(
            k for k, v in self._cache.items() if v is ConsistencyEval.PRESERVE
        )

    @property
    def negative_contents(self) -> frozenset[ContentID]:
        return frozenset(
            k for k, v in self._cache.items() if v is ConsistencyEval.DAMAGE
        )

    @property
    def neutral_contents(self) -> frozenset[ContentID]:
        return frozenset(
            k for k, v in self._cache.items() if v is ConsistencyEval.NEUTRAL
        )

    def _build_prompt(self, content_id: ContentID) -> str:
        existing_lines = [
            f"- {cid}: {self._texts.get(cid, '(no description)')}"
            for cid in sorted(self._msi.contents)
            if cid != COGITO_ID
        ]
        existing = (
            "\n".join(existing_lines)
            if existing_lines
            else "(empty — only the cogito anchor is present)"
        )
        new_text = self._texts.get(content_id, "(no description)")
        return PROMPT_TEMPLATE.format(
            existing_msi=existing,
            new_id=content_id,
            new_text=new_text,
        )

    def _build_retry_prompt(self, original: str, raw: str | None, error: str) -> str:
        return RETRY_TEMPLATE.format(
            original=original,
            raw=raw if raw is not None else "(no response received)",
            error=error,
        )


__all__ = [
    "LLMBackedPtCns",
    "SEMANTIC_CACHE_SCHEMA_VERSION",
    "SEMANTIC_CACHE_MAX_ENTRIES",
    "SEMANTIC_CACHE_DIR",
]
