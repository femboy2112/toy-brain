"""Phase 3.14 L1 transport cache fixture.

Drives:

* ``I-LLMCACHE-05`` (REQUIRED) — L1 ``CachedClient`` semantics remain
  prompt-hash transport cache with hit/no-inner-call and miss/inner-call
  behavior.
* ``I-LLMCACHE-14`` (REQUIRED) — Cache hit path does not call the inner
  client; cache miss path calls the inner client (proven here for L1).

Corrupt-L1 fail-loud behavior is exercised together with corrupt-L2
behavior in ``llm_cache_parse_failure.py`` under the single
``I-LLMCACHE-10`` registration.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from brain.invariants import register
from brain.llm.client import CachedClient


class _CountingClient:
    """Local counting LLM client used to prove hit/miss inner-call discipline."""

    def __init__(self, response: str = "PRESERVE") -> None:
        self.response = response
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


@register("I-LLMCACHE-05", status="REQUIRED")
def check_I_LLMCACHE_05_l1_prompt_hash_semantics() -> None:
    inner = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_l1_") as tmp:
        cache_dir = Path(tmp)
        cache = CachedClient(inner=inner, cache_dir=cache_dir)
        first = cache.eval_consistency("identical prompt please")
        second = cache.eval_consistency("identical prompt please")
        assert first == second == "PRESERVE", (
            "I-LLMCACHE-05 violated: cache did not return same answer "
            f"twice (first={first!r}, second={second!r})"
        )
        assert len(inner.calls) == 1, (
            "I-LLMCACHE-05 violated: inner client called more than once "
            f"under identical prompt (got {len(inner.calls)})"
        )
        files = sorted(cache_dir.glob("*.json"))
        assert len(files) == 1, (
            "I-LLMCACHE-05 violated: cache wrote more than one file for "
            f"a single prompt (got {len(files)})"
        )
        # The file name is the SHA-256 hex digest of the prompt.
        import hashlib
        expected = hashlib.sha256(b"identical prompt please").hexdigest()
        assert files[0].name == f"{expected}.json", (
            "I-LLMCACHE-05 violated: cache file is not "
            f"<sha256>.json (got {files[0].name!r})"
        )
        # Different prompt -> different key -> miss -> inner called.
        cache.eval_consistency("different prompt")
        assert len(inner.calls) == 2, (
            "I-LLMCACHE-05 violated: different prompt did not call "
            f"inner (got {len(inner.calls)})"
        )


@register("I-LLMCACHE-14", status="REQUIRED")
def check_I_LLMCACHE_14_hit_no_inner_call() -> None:
    inner = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_hit_") as tmp:
        cache = CachedClient(inner=inner, cache_dir=Path(tmp))
        cache.eval_consistency("prompt-A")
        cache.eval_consistency("prompt-A")
        cache.eval_consistency("prompt-A")
        # First call is miss + inner; subsequent two are hits.
        assert len(inner.calls) == 1, (
            "I-LLMCACHE-14 violated: cache hit path called inner "
            f"(got inner calls={len(inner.calls)})"
        )
        assert cache.hit_count == 2 and cache.miss_count == 1, (
            "I-LLMCACHE-14 violated: hit/miss counters drifted "
            f"(hit={cache.hit_count}, miss={cache.miss_count})"
        )
        # Different prompt - miss path calls inner.
        cache.eval_consistency("prompt-B")
        assert len(inner.calls) == 2, (
            "I-LLMCACHE-14 violated: miss did not call inner "
            f"(got inner calls={len(inner.calls)})"
        )
