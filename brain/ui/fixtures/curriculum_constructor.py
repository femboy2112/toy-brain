"""Phase 3.30 curriculum consolidation constructor + bounds fixture.

Drives ``I-CURR-01`` (REQUIRED) and ``I-CURR-02`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.curriculum_consolidation_probe import (
    CURRICULUM_DIGEST_HEX_LEN,
    CURRICULUM_INPUT_MAX_LEN,
    CURRICULUM_MAX_EXPOSURES_PER_TRIAL,
    CURRICULUM_MAX_TRIALS,
    CURRICULUM_PROBE_MAX_LEN,
    CURRICULUM_SLATE_MAX_ENTRIES,
    AdmissionOutcome,
    AuditDisposition,
    CurriculumCondition,
    CurriculumConsolidationReport,
    CurriculumExposure,
    CurriculumProbeStep,
    CurriculumStructureRecord,
    CurriculumTrial,
    CurriculumTrialResult,
    TrialVerdict,
)
from brain.invariants import register


_ZERO_DIGEST = "0" * CURRICULUM_DIGEST_HEX_LEN


def _make_exposure(**overrides):
    base = dict(exposure_id="X01", input_text="alpha beta")
    base.update(overrides)
    return CurriculumExposure(**base)


def _make_record(**overrides):
    base = dict(
        structure_id="S01_abcdef01",
        source_digest_hex16="0123456789abcdef",
        admitted_at_step=0,
        last_access_step=0,
        disposition=AuditDisposition.SURVIVED,
    )
    base.update(overrides)
    return CurriculumStructureRecord(**base)


def _make_probe_step(**overrides):
    base = dict(
        probe_input="alpha beta",
        probe_digest_hex16="fedcba9876543210",
        reuse_observed=False,
        probe_reused_structure_id="",
        interaction_id="agent-input:001",
        dispatch_trace_digest=_ZERO_DIGEST,
        reasoning_trace_digest=_ZERO_DIGEST,
        reply_excerpt="ok",
        summary_line="ok",
    )
    base.update(overrides)
    return CurriculumProbeStep(**base)


def _make_trial(**overrides):
    base = dict(
        trial_id="T_smoke",
        condition=CurriculumCondition.SINGLE_STRUCTURE,
        exposures=(_make_exposure(),),
        probe_input="",
        slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
        expected_survived_count=1,
        expected_decayed_count=0,
        expected_rejected_count=0,
        expected_reuse_observed=False,
    )
    base.update(overrides)
    return CurriculumTrial(**base)


def _make_result(**overrides):
    base = dict(
        trial_id="T_smoke",
        condition=CurriculumCondition.SINGLE_STRUCTURE,
        verdict=TrialVerdict.PASS,
        audit_records=(),
        probe_step=None,
        survived_count=0,
        decayed_count=0,
        rejected_count=0,
        reuse_observed=False,
        false_positive=False,
        false_negative=False,
        learning_evidence_digest=_ZERO_DIGEST,
        reasoning_trace_digest=_ZERO_DIGEST,
        dispatch_trace_digests=(),
        summary_line="ok",
    )
    base.update(overrides)
    return CurriculumTrialResult(**base)


def _make_report(**overrides):
    base = dict(
        battery_version="phase3.30.v1",
        trials=(),
        pass_count=0,
        warn_count=0,
        fail_count=0,
        not_applicable_count=0,
        false_positive_count=0,
        false_negative_count=0,
        total_survived_count=0,
        total_decayed_count=0,
        total_rejected_count=0,
        reuse_observed_count=0,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=_ZERO_DIGEST,
        summary_line="ok",
    )
    base.update(overrides)
    return CurriculumConsolidationReport(**base)


def _assert_raises(callable_):
    try:
        callable_()
    except (TypeError, ValueError):
        return
    raise AssertionError("expected TypeError or ValueError; none raised")


@register("I-CURR-01", status="REQUIRED")
def check_curriculum_constructor_bounds() -> None:
    """Exposure / StructureRecord / ProbeStep validators reject invalid input."""
    # CurriculumExposure happy path.
    e = _make_exposure()
    assert e == _make_exposure()
    # Oversize exposure_id rejected.
    _assert_raises(lambda: _make_exposure(exposure_id="x" * 64))
    # Non-printable input rejected.
    _assert_raises(lambda: _make_exposure(input_text="alpha\x00beta"))
    # Oversize input rejected.
    _assert_raises(
        lambda: _make_exposure(input_text="a " * (CURRICULUM_INPUT_MAX_LEN))
    )
    # Forbidden direct-instruction term rejected.
    _assert_raises(lambda: _make_exposure(input_text="alpha consolidate"))

    # CurriculumStructureRecord happy path + bounds.
    r = _make_record()
    assert r == _make_record()
    _assert_raises(lambda: _make_record(source_digest_hex16="0xshort"))
    _assert_raises(lambda: _make_record(admitted_at_step=-1))
    _assert_raises(
        lambda: _make_record(admitted_at_step=5, last_access_step=2)
    )
    _assert_raises(lambda: _make_record(disposition="survived"))

    # CurriculumProbeStep happy path + bounds.
    p = _make_probe_step()
    assert p == _make_probe_step()
    _assert_raises(lambda: _make_probe_step(reuse_observed="yes"))
    _assert_raises(lambda: _make_probe_step(probe_digest_hex16="short"))
    _assert_raises(lambda: _make_probe_step(probe_input="alpha forget"))


@register("I-CURR-02", status="REQUIRED")
def check_curriculum_trial_result_report_bounds() -> None:
    """Trial / TrialResult / Report validators reject invalid input."""
    # CurriculumTrial happy path + bounds.
    t = _make_trial()
    assert t == _make_trial()
    _assert_raises(lambda: _make_trial(condition="single_structure"))
    _assert_raises(lambda: _make_trial(exposures=[_make_exposure()]))
    _assert_raises(
        lambda: _make_trial(
            exposures=tuple(
                _make_exposure(exposure_id=f"X{i:02d}", input_text="alpha beta")
                for i in range(CURRICULUM_MAX_EXPOSURES_PER_TRIAL + 1)
            )
        )
    )
    _assert_raises(lambda: _make_trial(slate_max_entries=0))
    _assert_raises(
        lambda: _make_trial(slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES + 1)
    )
    _assert_raises(lambda: _make_trial(expected_survived_count=-1))
    _assert_raises(lambda: _make_trial(expected_reuse_observed="no"))
    _assert_raises(lambda: _make_trial(probe_input="alpha curriculum"))

    # CurriculumTrialResult happy path + bounds.
    res = _make_result()
    assert res == _make_result()
    _assert_raises(lambda: _make_result(verdict="pass"))
    _assert_raises(lambda: _make_result(audit_records=[]))
    _assert_raises(
        lambda: _make_result(
            audit_records=tuple(
                _make_record() for _ in range(CURRICULUM_MAX_EXPOSURES_PER_TRIAL + 1)
            )
        )
    )
    _assert_raises(lambda: _make_result(learning_evidence_digest="short"))
    _assert_raises(lambda: _make_result(dispatch_trace_digests=[_ZERO_DIGEST]))

    # CurriculumConsolidationReport happy path + bounds.
    rep = _make_report()
    assert rep == _make_report()
    _assert_raises(lambda: _make_report(trials=[]))
    _assert_raises(
        lambda: _make_report(
            trials=tuple(_make_result() for _ in range(CURRICULUM_MAX_TRIALS + 1))
        )
    )
    _assert_raises(lambda: _make_report(pass_count=-1))
    _assert_raises(lambda: _make_report(digest_hex16="short"))

    # Closed enum membership: AdmissionOutcome carries the 3 documented
    # values.
    assert frozenset(o.value for o in AdmissionOutcome) == frozenset({
        "admitted", "rejected_collision", "rejected_nonprintable",
    })
