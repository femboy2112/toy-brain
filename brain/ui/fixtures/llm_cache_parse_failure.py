"""Phase 3.14 L2 parse-failure / corruption fixture.

Drives:

* ``I-LLMCACHE-09`` (REQUIRED) — L2 stores only parse-success entries;
  parse failures, provider failures, timeouts, refusals, schema
  mismatches, and corrupt entries do not become L2 success hits.
* ``I-LLMCACHE-10`` (REQUIRED) — Corrupt L1 / L2 cache entries fail
  loud with bounded error and do not silently call the inner client.
  Both layers are exercised here.
"""
from __future__ import annotations

import json
import tempfile
from fractions import Fraction
from pathlib import Path

from brain.invariants import register
from brain.llm.client import CachedClient, MockClient
from brain.llm.ptcns_backed import LLMBackedPtCns
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval


class _SequentialClient:
    """LLM client that returns a queued list of responses; counts calls."""

    def __init__(self, responses: list[str]) -> None:
        self._iter = iter(responses)
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise RuntimeError("_SequentialClient exhausted") from exc


def _make_msi() -> tuple:
    profile = make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    texts = {
        ContentID("anchor_a"): "anchor a description",
        ContentID("new_x"): "the new content under evaluation",
    }
    return msi, texts


@register("I-LLMCACHE-09", status="REQUIRED")
def check_I_LLMCACHE_09_parse_failure_not_cached() -> None:
    msi, texts = _make_msi()
    # All max_attempts attempts return unparseable text -> retries
    # exhausted -> I-LLM-01 ValueError -> L2 must NOT write.
    fail_inner = _SequentialClient(["nonsense", "still bad", "also bad"])
    with tempfile.TemporaryDirectory(prefix="phase3_14_pf09_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_pf09_l2_") as l2_tmp:
        l1 = CachedClient(inner=fail_inner, cache_dir=Path(l1_tmp))
        p = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p._l2_dir = Path(l2_tmp)
        try:
            p.eval(ContentID("new_x"))
        except ValueError as exc:
            assert "I-LLM-01" in str(exc), (
                "I-LLMCACHE-09 violated: exhausted-retry failure did not "
                f"raise I-LLM-01 (got {exc!r})"
            )
        else:
            raise AssertionError(
                "I-LLMCACHE-09 violated: parse failures did not raise"
            )
        # No L2 entries written.
        files = sorted(Path(l2_tmp).glob("*.json"))
        assert len(files) == 0, (
            "I-LLMCACHE-09 violated: parse failures wrote L2 entries "
            f"(got {len(files)})"
        )

    # Retry-then-success: L2 must write exactly one parse-success entry.
    msi, texts = _make_msi()
    retry_inner = _SequentialClient(["nonsense", "PRESERVE"])
    with tempfile.TemporaryDirectory(prefix="phase3_14_pf09b_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_pf09b_l2_") as l2_tmp:
        l1 = CachedClient(inner=retry_inner, cache_dir=Path(l1_tmp))
        p = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p._l2_dir = Path(l2_tmp)
        result = p.eval(ContentID("new_x"))
        assert result is ConsistencyEval.PRESERVE
        files = sorted(Path(l2_tmp).glob("*.json"))
        assert len(files) == 1, (
            "I-LLMCACHE-09 violated: retry-then-success did not write "
            f"exactly one L2 entry (got {len(files)})"
        )
        # Entry payload contains only key_prefix + parsed; no raw
        # response, no raw prompt.
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        assert set(payload.keys()) == {"key_prefix", "parsed"}, (
            "I-LLMCACHE-09 violated: L2 entry has unexpected keys "
            f"({sorted(payload.keys())})"
        )
        assert payload["parsed"] == "PRESERVE", (
            "I-LLMCACHE-09 violated: L2 entry parsed field drifted "
            f"(got {payload['parsed']!r})"
        )


@register("I-LLMCACHE-10", status="REQUIRED")
def check_I_LLMCACHE_10_corrupt_cache_fail_loud() -> None:
    # ---- L1 branch: CachedClient corrupt entry --------------------------
    l1_inner = _SequentialClient(["PRESERVE"])
    with tempfile.TemporaryDirectory(prefix="phase3_14_pf10_l1_") as l1_tmp:
        cache_dir = Path(l1_tmp)
        cache = CachedClient(inner=l1_inner, cache_dir=cache_dir)
        cache.eval_consistency("some prompt")
        l1_files = sorted(cache_dir.glob("*.json"))
        assert len(l1_files) == 1, (
            "I-LLMCACHE-10 violated: L1 setup did not write exactly one "
            f"entry (got {len(l1_files)})"
        )
        l1_files[0].write_text("not-json-{", encoding="utf-8")
        l1_inner.calls.clear()
        try:
            cache.eval_consistency("some prompt")
        except RuntimeError as exc:
            assert "corrupt" in str(exc).lower(), (
                "I-LLMCACHE-10 violated: corrupt L1 error does not name "
                f"'corrupt' (got {exc!r})"
            )
        else:
            raise AssertionError(
                "I-LLMCACHE-10 violated: corrupt L1 entry did not raise"
            )
        assert l1_inner.calls == [], (
            "I-LLMCACHE-10 violated: corrupt L1 entry silently called "
            f"inner ({len(l1_inner.calls)} calls)"
        )

    # ---- L2 branch: LLMBackedPtCns L2 corrupt entry ---------------------
    msi, texts = _make_msi()
    inner = _SequentialClient(["PRESERVE", "PRESERVE"])
    with tempfile.TemporaryDirectory(prefix="phase3_14_pf10_l2a_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_pf10_l2b_") as l2_tmp:
        l1 = CachedClient(inner=inner, cache_dir=Path(l1_tmp))
        l2_dir = Path(l2_tmp)
        p = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p._l2_dir = l2_dir
        # Populate one L2 entry, then corrupt it.
        p.eval(ContentID("new_x"))
        files = sorted(l2_dir.glob("*.json"))
        assert len(files) == 1
        corrupt_target = files[0]
        # Variant 1: invalid JSON.
        corrupt_target.write_text("not-json-{", encoding="utf-8")
        inner.calls.clear()
        # Force the L0 cache to miss by reconstructing the PtCns.
        p2 = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p2._l2_dir = l2_dir
        try:
            p2.eval(ContentID("new_x"))
        except RuntimeError as exc:
            assert "corrupt" in str(exc).lower(), (
                "I-LLMCACHE-10 violated: corrupt L2 entry error does not "
                f"name 'corrupt' (got {exc!r})"
            )
        else:
            raise AssertionError(
                "I-LLMCACHE-10 violated: corrupt L2 JSON did not raise"
            )
        # Inner client must not have been called.
        assert inner.calls == [], (
            "I-LLMCACHE-10 violated: corrupt L2 entry silently called "
            f"inner ({len(inner.calls)} calls)"
        )

        # Variant 2: payload with unexpected key set.
        corrupt_target.write_text(
            json.dumps({"prompt": "leaked", "response": "PRESERVE"}),
            encoding="utf-8",
        )
        p3 = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p3._l2_dir = l2_dir
        try:
            p3.eval(ContentID("new_x"))
        except RuntimeError as exc:
            assert "corrupt" in str(exc).lower(), (
                "I-LLMCACHE-10 violated: corrupt L2 keyset error does "
                f"not name 'corrupt' (got {exc!r})"
            )
        else:
            raise AssertionError(
                "I-LLMCACHE-10 violated: corrupt L2 keyset did not raise"
            )

        # Variant 3: payload with invalid parsed value.
        corrupt_target.write_text(
            json.dumps({"key_prefix": "deadbeef", "parsed": "MAYBE"}),
            encoding="utf-8",
        )
        p4 = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p4._l2_dir = l2_dir
        try:
            p4.eval(ContentID("new_x"))
        except RuntimeError as exc:
            assert "corrupt" in str(exc).lower(), (
                "I-LLMCACHE-10 violated: corrupt L2 parsed-value error "
                f"does not name 'corrupt' (got {exc!r})"
            )
        else:
            raise AssertionError(
                "I-LLMCACHE-10 violated: corrupt L2 parsed value did not raise"
            )
