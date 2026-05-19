"""Phase 3.26 active hypothesis probe constructor + bounds fixture.

Drives ``I-AHYP-01`` (REQUIRED) and ``I-AHYP-02`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN,
    ACTIVE_HYPOTHESIS_INPUT_MAX_LEN,
    ACTIVE_HYPOTHESIS_MAX_CANDIDATES,
    ACTIVE_HYPOTHESIS_MAX_TRIALS,
    ACTIVE_HYPOTHESIS_PROBE_MAX_LEN,
    ActiveHypothesisCandidate,
    ActiveHypothesisLiveTestReport,
    ActiveHypothesisResult,
    ActiveHypothesisStatus,
    ActiveHypothesisTrial,
    ActiveProbeStep,
    AmbiguityCondition,
    ProbeConstructionRule,
    ProbeOutcome,
    TrialVerdict,
)
from brain.invariants import register


_ZERO_DIGEST = "0" * ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN


def _make_candidate(**overrides):
    base = dict(
        candidate_id="H_x",
        predicted_shape_name="S_AB",
        predicted_shape="A B",
        predicted_classification="all-distinct",
        predicted_digest_hex16="0123456789abcdef",
        probe_construction_rule=ProbeConstructionRule.RENAME_ONLY,
        status=ActiveHypothesisStatus.PENDING,
    )
    base.update(overrides)
    return ActiveHypothesisCandidate(**base)


def _make_probe_step(**overrides):
    base = dict(
        candidate_id="H_x",
        probe_text="alpha beta",
        probe_digest_hex16="fedcba9876543210",
        probe_shape="A B",
        probe_classification="all-distinct",
        predicted_digest_hex16="0123456789abcdef",
        outcome=ProbeOutcome.FALSIFIED,
        interaction_id="agent-input:001",
        dispatch_trace_digest=_ZERO_DIGEST,
        reasoning_trace_digest=_ZERO_DIGEST,
        reply_excerpt="ok",
    )
    base.update(overrides)
    return ActiveProbeStep(**base)


def _make_trial(**overrides):
    base = dict(
        trial_id="T_smoke",
        condition=AmbiguityCondition.CONTROL_NO_AMBIGUITY,
        input_text="",
        expected_survivors_count=0,
        expected_winner_id="",
        expected_no_hypothesis_survives=False,
        expected_second_visit_cache_hit=False,
    )
    base.update(overrides)
    return ActiveHypothesisTrial(**base)


def _make_result(**overrides):
    base = dict(
        trial_id="T_smoke",
        condition=AmbiguityCondition.CONTROL_NO_AMBIGUITY,
        verdict=TrialVerdict.PASS,
        input_digest_hex16="0123456789abcdef",
        candidates=(),
        probe_steps=(),
        survivors_count=0,
        winner_id="",
        no_hypothesis_survives=False,
        second_visit_cache_hit=False,
        second_visit_probe_count=0,
        false_positive=False,
        false_negative=False,
        learning_evidence_digest=_ZERO_DIGEST,
        reasoning_trace_digest=_ZERO_DIGEST,
        dispatch_trace_digests=(),
        summary_line="ok",
    )
    base.update(overrides)
    return ActiveHypothesisResult(**base)


def _make_report(**overrides):
    base = dict(
        battery_version="phase3.26.v1",
        trials=(),
        pass_count=0,
        warn_count=0,
        fail_count=0,
        not_applicable_count=0,
        false_positive_count=0,
        false_negative_count=0,
        winner_selected_count=0,
        no_hypothesis_survives_count=0,
        cache_reuse_count=0,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=_ZERO_DIGEST,
        summary_line="ok",
    )
    base.update(overrides)
    return ActiveHypothesisLiveTestReport(**base)


@register("I-AHYP-01", status="REQUIRED")
def check_active_hypothesis_candidate_and_probe_step() -> None:
    """Audit ActiveHypothesisCandidate + ActiveProbeStep bounds."""
    c = _make_candidate()
    assert isinstance(c, ActiveHypothesisCandidate)
    assert isinstance(c.probe_construction_rule, ProbeConstructionRule)
    assert isinstance(c.status, ActiveHypothesisStatus)

    # Reject non-string candidate_id.
    try:
        _make_candidate(candidate_id=123)
        raise AssertionError("non-string candidate_id should have raised")
    except TypeError:
        pass

    # Reject non-16-hex predicted_digest_hex16.
    try:
        _make_candidate(predicted_digest_hex16="short")
        raise AssertionError("short predicted_digest_hex16 should have raised")
    except ValueError:
        pass

    # Reject non-ProbeConstructionRule rule.
    try:
        _make_candidate(probe_construction_rule="rename_only")
        raise AssertionError("string probe_construction_rule should have raised")
    except TypeError:
        pass

    # Reject non-ActiveHypothesisStatus status.
    try:
        _make_candidate(status="pending")
        raise AssertionError("string status should have raised")
    except TypeError:
        pass

    # Reject non-claim term in candidate_id.
    try:
        _make_candidate(candidate_id="H_conscious")
        raise AssertionError("forbidden non-claim term should have raised")
    except ValueError:
        pass

    # Equality: two candidates with identical fields compare equal.
    c2 = _make_candidate()
    assert c == c2

    # ActiveProbeStep: reject probe_text containing predicted digest.
    leaky_digest = "deadbeefdeadbeef"
    try:
        _make_probe_step(
            probe_text="alpha " + leaky_digest,
            predicted_digest_hex16=leaky_digest,
        )
        raise AssertionError("leaking predicted_digest should have raised")
    except ValueError:
        pass

    # Reject probe_text containing forbidden direct-instruction term.
    try:
        _make_probe_step(probe_text="learn this")
        raise AssertionError("forbidden direct-instruction term should have raised")
    except ValueError:
        pass

    # Reject non-16-hex probe_digest_hex16.
    try:
        _make_probe_step(probe_digest_hex16="short")
        raise AssertionError("short probe_digest_hex16 should have raised")
    except ValueError:
        pass

    # Reject non-ProbeOutcome outcome.
    try:
        _make_probe_step(outcome="confirmed")
        raise AssertionError("string outcome should have raised")
    except TypeError:
        pass


@register("I-AHYP-02", status="REQUIRED")
def check_active_hypothesis_trial_result_report() -> None:
    """Audit ActiveHypothesisTrial / Result / Report bounds."""
    t = _make_trial()
    assert isinstance(t, ActiveHypothesisTrial)
    assert t.condition is AmbiguityCondition.CONTROL_NO_AMBIGUITY

    # Reject non-AmbiguityCondition condition.
    try:
        _make_trial(condition="control_no_ambiguity")
        raise AssertionError("string condition should have raised")
    except TypeError:
        pass

    # Reject oversize input_text.
    try:
        _make_trial(input_text="x" * (ACTIVE_HYPOTHESIS_INPUT_MAX_LEN + 1))
        raise AssertionError("oversize input_text should have raised")
    except ValueError:
        pass

    # Reject input_text with forbidden direct-instruction term.
    try:
        _make_trial(input_text="please learn")
        raise AssertionError("forbidden direct-instruction term should have raised")
    except ValueError:
        pass

    # Reject expected_survivors_count out of range.
    try:
        _make_trial(expected_survivors_count=ACTIVE_HYPOTHESIS_MAX_CANDIDATES + 1)
        raise AssertionError("out-of-range survivors_count should have raised")
    except ValueError:
        pass

    # Reject non-bool flags.
    try:
        _make_trial(expected_no_hypothesis_survives="yes")
        raise AssertionError("non-bool flag should have raised")
    except TypeError:
        pass

    # ActiveHypothesisResult: reject oversize candidates tuple.
    too_many = tuple(
        _make_candidate(candidate_id=f"H_{i}")
        for i in range(ACTIVE_HYPOTHESIS_MAX_CANDIDATES + 1)
    )
    try:
        _make_result(candidates=too_many)
        raise AssertionError("oversize candidates tuple should have raised")
    except ValueError:
        pass

    # Reject non-tuple dispatch_trace_digests.
    try:
        _make_result(dispatch_trace_digests=[_ZERO_DIGEST])
        raise AssertionError("non-tuple dispatch_trace_digests should have raised")
    except TypeError:
        pass

    # Reject non-TrialVerdict verdict.
    try:
        _make_result(verdict="pass")
        raise AssertionError("string verdict should have raised")
    except TypeError:
        pass

    # ActiveHypothesisLiveTestReport: reject oversize trials tuple.
    huge_trials = tuple(
        _make_result(trial_id=f"T_{i}")
        for i in range(ACTIVE_HYPOTHESIS_MAX_TRIALS + 1)
    )
    try:
        _make_report(trials=huge_trials)
        raise AssertionError("oversize trials tuple should have raised")
    except ValueError:
        pass

    # Reject negative counts.
    try:
        _make_report(pass_count=-1)
        raise AssertionError("negative pass_count should have raised")
    except ValueError:
        pass

    # Probe construction max length is 240.
    assert ACTIVE_HYPOTHESIS_PROBE_MAX_LEN == 240
