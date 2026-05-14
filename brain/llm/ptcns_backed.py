"""LLM-backed PtCns implementation (Phase 2 v1).

Implements the same duck-typed surface as the v0 ``PtCns`` dataclass
(``eval``, ``eval_map``, ``positive_contents``, ``negative_contents``,
``neutral_contents``) so downstream code (``boundary``, ``from_eval``,
``assert_state_invariants``) accepts both implementations
interchangeably. The shared structural type is ``PtCnsLike`` declared in
``brain/tlica/ptcns.py``.

Catalog rows owned: I-LLM-01..04.
"""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from brain.llm.client import LLMClient
from brain.llm.parse import parse_consistency_eval, ParseError
from brain.llm.prompts import PROMPT_TEMPLATE, RETRY_TEMPLATE
from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval


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
        """
        if max_attempts < 1:
            raise ValueError(
                f"LLMBackedPtCns: max_attempts must be >= 1, got {max_attempts}"
            )
        self._msi = msi
        self._texts = MappingProxyType(dict(content_texts))
        self._client = client
        self._max_attempts = max_attempts
        # I-LLM-03: cogito is short-circuited at construction; never an
        # LLM call regardless of client state.
        self._cache: dict[ContentID, ConsistencyEval] = {
            COGITO_ID: ConsistencyEval.PRESERVE
        }

    @property
    def eval_map(self) -> Mapping[ContentID, ConsistencyEval]:
        """Lazily-populated map; total over ``msi.profile.domain`` only
        once every domain element has been evaluated. Tick orchestration
        is responsible for evaluating each new content before reading
        ``eval_map`` to satisfy I-RT-04.
        """
        return MappingProxyType(self._cache)

    def eval(self, content_id: ContentID) -> ConsistencyEval:
        # I-LLM-03: cached-cogito short-circuit (and any subsequent
        # cached values).
        if content_id in self._cache:
            return self._cache[content_id]

        prompt = self._build_prompt(content_id)
        last_error: ParseError | None = None
        last_raw: str | None = None

        for _ in range(self._max_attempts):
            raw = self._client.eval_consistency(prompt)
            last_raw = raw
            try:
                parsed = parse_consistency_eval(raw)
            except ParseError as exc:
                last_error = exc
                prompt = self._build_retry_prompt(prompt, raw, str(exc))
                continue
            self._cache[content_id] = parsed
            return parsed

        raise ValueError(
            f"I-LLM-01 violated: PtCns.eval({content_id!r}) failed after "
            f"{self._max_attempts} attempts. Last raw response: {last_raw!r}. "
            f"Last parse error: {last_error}"
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


__all__ = ["LLMBackedPtCns"]
