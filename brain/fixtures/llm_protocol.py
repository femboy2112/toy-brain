"""LLM protocol fixture (Phase 2 v1).

Drives:
  I-LLM-01 (REQUIRED) — retry shell: max_attempts attempts; success
    on attempt N; raise after exhausting all attempts.
  I-LLM-02 (OBSERVED) — CachedClient determinism: same prompt routed
    twice returns same answer without re-calling the inner client.
  I-LLM-03 (REQUIRED) — cogito short-circuit: eval(COGITO_ID) returns
    PRESERVE without consulting the LLM.
  I-LLM-04 (STRUCTURAL) — Protocol conformance: MockClient and
    AnthropicAPIClient both satisfy isinstance(LLMClient).

All assertions use ``MockClient`` (deterministic) — no real API call.
"""
from __future__ import annotations

from fractions import Fraction

from brain.invariants import register
from brain.llm.client import (
    AnthropicAPIClient,
    CachedClient,
    LLMClient,
    MockClient,
)
from brain.llm.ptcns_backed import LLMBackedPtCns
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval


def _make_msi_with_one_extra():
    """Smallest MSI that has a non-cogito member to talk about in
    prompts; threshold tuned to admit the extra at value 3/4.
    """
    profile = make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    return msi


@register("I-LLM-01")
def check_I_LLM_01() -> None:
    """Retry shell: succeeds within budget; raises after exhausting it."""
    msi = _make_msi_with_one_extra()
    texts = {ContentID("test_content"): "an arbitrary new content for testing"}

    # Success on the third (final) attempt — two parse failures consumed.
    success_client = MockClient(["nonsense", "still bad", "PRESERVE"])
    ptcns = LLMBackedPtCns(
        msi=msi, content_texts=texts, client=success_client, max_attempts=3
    )
    result = ptcns.eval(ContentID("test_content"))
    assert result is ConsistencyEval.PRESERVE, (
        f"expected PRESERVE on attempt 3, got {result!r}"
    )
    assert len(success_client.calls) == 3, (
        f"expected 3 LLM calls (3 attempts), got {len(success_client.calls)}"
    )

    # Failure: every response unparseable; must raise with I-LLM-01 tag.
    fail_client = MockClient(["a", "b", "c"])
    fail_ptcns = LLMBackedPtCns(
        msi=msi, content_texts=texts, client=fail_client, max_attempts=3
    )
    raised = False
    try:
        fail_ptcns.eval(ContentID("test_content"))
    except ValueError as exc:
        raised = True
        assert "I-LLM-01" in str(exc), (
            f"raised ValueError missing I-LLM-01 tag: {exc}"
        )
    assert raised, "I-LLM-01 violated: failure path did not raise"
    assert len(fail_client.calls) == 3, (
        f"expected 3 LLM calls before giving up, got {len(fail_client.calls)}"
    )


@register("I-LLM-02", status="OBSERVED")
def check_I_LLM_02() -> None:
    """CachedClient: same prompt → same answer, inner called once.

    OBSERVED: surfaced in the run summary; not a runner gate.
    """
    import tempfile
    from pathlib import Path

    inner = MockClient(["PRESERVE", "DAMAGE"])  # second answer would differ
    with tempfile.TemporaryDirectory() as tmp:
        cache = CachedClient(inner=inner, cache_dir=Path(tmp))
        first = cache.eval_consistency("identical prompt please")
        second = cache.eval_consistency("identical prompt please")
        assert first == second == "PRESERVE", (
            f"cache failed determinism: first={first!r} second={second!r}"
        )
        assert len(inner.calls) == 1, (
            f"inner client called {len(inner.calls)} times; expected 1"
        )
        assert cache.hit_count == 1 and cache.miss_count == 1


@register("I-LLM-03")
def check_I_LLM_03() -> None:
    """Cogito short-circuit: eval(COGITO_ID) returns PRESERVE; no LLM call."""
    msi = _make_msi_with_one_extra()
    # MockClient with no responses — would raise RuntimeError if called.
    starvation_client = MockClient([])
    ptcns = LLMBackedPtCns(
        msi=msi,
        content_texts={},
        client=starvation_client,
    )
    result = ptcns.eval(COGITO_ID)
    assert result is ConsistencyEval.PRESERVE, (
        f"cogito short-circuit returned {result!r}, must be PRESERVE"
    )
    assert len(starvation_client.calls) == 0, (
        f"client was called {len(starvation_client.calls)} times for cogito; "
        "must be 0 (I-LLM-03)"
    )


@register("I-LLM-04", status="STRUCTURAL")
def check_I_LLM_04() -> None:
    """Protocol conformance: MockClient and AnthropicAPIClient satisfy LLMClient."""
    assert isinstance(MockClient([]), LLMClient), (
        "MockClient does not satisfy LLMClient Protocol"
    )
    # AnthropicAPIClient does not need an API key to construct the object;
    # only resolution at call time. isinstance check is structural-only.
    assert isinstance(
        AnthropicAPIClient(api_key="dummy-not-used"), LLMClient
    ), "AnthropicAPIClient does not satisfy LLMClient Protocol"
    # CachedClient also conforms.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        wrapped = CachedClient(MockClient([]), cache_dir=Path(tmp))
        assert isinstance(wrapped, LLMClient), (
            "CachedClient does not satisfy LLMClient Protocol"
        )
