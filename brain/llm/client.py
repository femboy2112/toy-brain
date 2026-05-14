"""``LLMClient`` Protocol + three v1 backends.

Per the Phase 2 v1 plan, the brain stays decoupled from any specific LLM
access mechanism via the ``LLMClient`` Protocol seam. v1 ships:

  - ``AnthropicAPIClient``: direct HTTP via stdlib ``urllib.request``
    (no third-party dep). Used in cloud-sandbox runs.
  - ``MockClient``: pre-canned sequential responses. Used by every
    fixture that needs a deterministic LLM stand-in.
  - ``CachedClient``: wraps another client with a SHA-256 prompt cache
    on disk under ``brain/.llm_cache/``. Used by the scenario CLI to
    make replays deterministic across runs.

Future backends (``SubprocessClient``, ``IPCClient``) are deliberately
out of scope for v1 — see ``PHASE2_v1_KICKOFF.md`` and the plan.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol, runtime_checkable

from brain.trace import CognitionTracer, NullTracer


@runtime_checkable
class LLMClient(Protocol):
    """Minimal LLM transport seam.

    Implementations submit ``prompt`` to the underlying model and return
    the raw string response. The caller is responsible for parsing /
    validating; transport failures (network, auth, rate limit) raise as
    ordinary exceptions and are *operational* failures, not invariant
    violations.
    """

    def eval_consistency(self, prompt: str) -> str:
        ...


# ---------------------------------------------------------------------------
# AnthropicAPIClient — direct HTTP, no SDK dependency.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AnthropicAPIClient:
    """Direct HTTP client for the Anthropic Messages API.

    Uses ``urllib.request`` so we incur no third-party runtime dep
    (consistent with v0's stdlib-only convention). Reads
    ``ANTHROPIC_API_KEY`` from env when ``api_key`` is None; raises
    ``RuntimeError`` if neither is set at first call time.

    Default model: ``claude-sonnet-4-6`` (Sonnet 4.5 is on a retirement
    path, per corrigenda C2).

    Phase 2 v1.1: ``tracer`` is stored at construction for symmetry with
    ``CachedClient``. The retry shell (``LLMBackedPtCns``) owns the
    ``llm.request`` / ``llm.response`` events because it has the
    content_id / attempt context the taxonomy requires. ``tracer`` is
    observation-only; its presence cannot affect the returned string.
    """

    api_key: str | None = None
    model: str = "claude-sonnet-4-6"
    base_url: str = "https://api.anthropic.com"
    # max_tokens=256: enough budget for verbose failure responses so the
    # retry feedback loop can include the LLM's actual bad output verbatim.
    # Happy path uses ~5 tokens; the headroom is for retry observability
    # (corrigenda C3).
    max_tokens: int = 256
    anthropic_version: str = "2023-06-01"
    timeout_seconds: float = 30.0
    tracer: CognitionTracer = field(default_factory=NullTracer)

    def _resolved_key(self) -> str:
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "AnthropicAPIClient: no API key (set ANTHROPIC_API_KEY or "
                "pass api_key= explicitly)"
            )
        return key

    def eval_consistency(self, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/v1/messages",
            data=body,
            method="POST",
            headers={
                "content-type": "application/json",
                "x-api-key": self._resolved_key(),
                "anthropic-version": self.anthropic_version,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise RuntimeError(
                f"AnthropicAPIClient HTTP {exc.code}: {err_body[:500]}"
            ) from exc
        # Messages API returns {"content": [{"type":"text","text":"..."}], ...}
        content = payload.get("content")
        if not content or not isinstance(content, list):
            raise RuntimeError(
                f"AnthropicAPIClient: unexpected response payload: {payload!r}"
            )
        first = content[0]
        text = first.get("text") if isinstance(first, dict) else None
        if not isinstance(text, str):
            raise RuntimeError(
                f"AnthropicAPIClient: response missing text content: {payload!r}"
            )
        return text


# ---------------------------------------------------------------------------
# MockClient — deterministic canned responses for fixtures.
# ---------------------------------------------------------------------------


class MockClient:
    """Sequential canned-response client. Pops one response per call.

    Used by ``brain/fixtures/llm_protocol.py`` and
    ``brain/fixtures/scenario_v1.py`` to drive deterministic test
    behavior without touching the real API.
    """

    def __init__(self, responses: Iterable[str]) -> None:
        self._iter: Iterator[str] = iter(responses)
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise RuntimeError("MockClient exhausted") from exc


# ---------------------------------------------------------------------------
# CachedClient — disk-backed prompt cache wrapping any inner client.
# ---------------------------------------------------------------------------


class CachedClient:
    """SHA-256 prompt-keyed disk cache wrapping an inner ``LLMClient``.

    On hit: returns the cached response without calling ``inner``.
    On miss: calls ``inner``, persists ``{key}.json`` under
    ``cache_dir``, returns the response.

    This is the across-tick / across-run determinism layer that I-LLM-02
    reports on. ``LLMBackedPtCns`` does its own per-instance caching for
    cogito short-circuit only; everything else flows through here.

    Phase 2 v1.1: optional ``tracer`` records ``llm.cache_hit`` and
    ``llm.cache_miss`` events with an 8-char key prefix for debugging.
    """

    def __init__(
        self,
        inner: LLMClient,
        cache_dir: Path = Path("brain/.llm_cache"),
        tracer: CognitionTracer | None = None,
    ) -> None:
        self._inner = inner
        self._cache_dir = cache_dir
        self._tracer: CognitionTracer = tracer if tracer is not None else NullTracer()
        self.hit_count = 0
        self.miss_count = 0

    def _key_path(self, prompt: str) -> tuple[Path, str]:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json", digest

    def eval_consistency(self, prompt: str) -> str:
        path, digest = self._key_path(prompt)
        key_prefix = digest[:8]
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                response = payload["response"]
            except (OSError, ValueError, KeyError) as exc:
                raise RuntimeError(
                    f"CachedClient: corrupt cache entry at {path}: {exc}"
                ) from exc
            self.hit_count += 1
            self._tracer.record("llm.cache_hit", {"cache_key_prefix": key_prefix})
            return response
        self.miss_count += 1
        self._tracer.record("llm.cache_miss", {"cache_key_prefix": key_prefix})
        response = self._inner.eval_consistency(prompt)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"prompt": prompt, "response": response}, indent=2),
            encoding="utf-8",
        )
        return response


__all__ = ["LLMClient", "AnthropicAPIClient", "MockClient", "CachedClient"]
