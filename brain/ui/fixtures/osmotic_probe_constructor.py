"""Phase 3.25 osmotic probe constructor + bounds fixture.

Drives ``I-OSMO-01`` (REQUIRED) and ``I-OSMO-02`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.osmotic_learning_probe import (
    OSMOTIC_MAX_EXPOSURES_PER_TRIAL,
    OsmoticCondition,
    OsmoticExposureEvent,
    OsmoticProbeStatus,
    OsmoticProbeTrial,
    build_osmotic_exposure_plan,
)
from brain.invariants import register


@register("I-OSMO-01", status="REQUIRED")
def check_osmotic_exposure_event() -> None:
    """Audit OsmoticExposureEvent bounds + non-claim cleanliness."""
    ev = OsmoticExposureEvent(
        text="red blue red blue",
        interaction_id="agent-input:00001",
        abstract_digest_hex16="d37efc29b0c680ba",
        classification="recurring-form",
        shape="A B A B",
    )
    assert ev.text == "red blue red blue"
    assert ev.interaction_id == "agent-input:00001"
    assert ev.abstract_digest_hex16 == "d37efc29b0c680ba"
    assert ev.classification == "recurring-form"
    assert ev.shape == "A B A B"

    # Equal field values -> equal records.
    ev2 = OsmoticExposureEvent(
        text="red blue red blue",
        interaction_id="agent-input:00001",
        abstract_digest_hex16="d37efc29b0c680ba",
        classification="recurring-form",
        shape="A B A B",
    )
    assert ev == ev2

    # Rejections.
    rejection_cases = (
        (
            "non-hex digest",
            dict(
                text="red blue red blue",
                interaction_id="agent-input:00001",
                abstract_digest_hex16="not-hex",
                classification="recurring-form",
                shape="A B A B",
            ),
        ),
        (
            "empty text",
            dict(
                text="",
                interaction_id="agent-input:00001",
                abstract_digest_hex16="d37efc29b0c680ba",
                classification="recurring-form",
                shape="A B A B",
            ),
        ),
        (
            "non-printable text",
            dict(
                text="red\x00blue",
                interaction_id="agent-input:00001",
                abstract_digest_hex16="d37efc29b0c680ba",
                classification="recurring-form",
                shape="A B A B",
            ),
        ),
        (
            "non-printable interaction_id",
            dict(
                text="red blue red blue",
                interaction_id="iid\x00",
                abstract_digest_hex16="d37efc29b0c680ba",
                classification="recurring-form",
                shape="A B A B",
            ),
        ),
    )
    for tag, bad in rejection_cases:
        raised = False
        try:
            OsmoticExposureEvent(**bad)
        except (TypeError, ValueError):
            raised = True
        assert raised, (
            f"I-OSMO-01 violated: OsmoticExposureEvent accepted invalid "
            f"input ({tag})"
        )


@register("I-OSMO-02", status="REQUIRED")
def check_osmotic_probe_trial() -> None:
    """Audit OsmoticProbeTrial closed-enum + forbidden-term scan."""

    # Closed enum membership.
    actual_conditions = frozenset(c.value for c in OsmoticCondition)
    assert actual_conditions == frozenset(
        {
            "control_no_exposure",
            "true_exposure",
            "sham_exposure",
            "distractor_interference",
        }
    )
    actual_statuses = frozenset(s.value for s in OsmoticProbeStatus)
    assert actual_statuses == frozenset(
        {"pass", "warn", "fail", "not_applicable"}
    )

    # Build a valid trial.
    trial = OsmoticProbeTrial(
        trial_id="T_valid",
        condition=OsmoticCondition.TRUE_EXPOSURE,
        exposure_texts=("red blue red blue",),
        probe_text="cat dog cat dog",
        expected_target_digest="d37efc29b0c680ba",
        expected_target_shape="A B A B",
        expected_prior_acquired=True,
        expected_transfer=True,
    )
    assert trial.condition is OsmoticCondition.TRUE_EXPOSURE

    # The v1 ten-trial plan is valid + reproducible.
    plan_a = build_osmotic_exposure_plan()
    plan_b = build_osmotic_exposure_plan()
    assert plan_a == plan_b
    assert len(plan_a) == 10
    trial_ids = tuple(t.trial_id for t in plan_a)
    assert trial_ids == (
        "T01_control_abab",
        "T02_true_abab",
        "T03_true_abba",
        "T04_true_abcabc",
        "T05_sham_abba_for_abab",
        "T06_distractor_abab",
        "T07_delayed_abab",
        "T08_control_aab",
        "T09_renamed_aab",
        "T10_distractor_abcabc",
    )

    # Rejections: forbidden direct-instruction term in exposure / probe.
    rejection_cases = (
        (
            "forbidden term in exposure",
            dict(
                trial_id="T_bad",
                condition=OsmoticCondition.TRUE_EXPOSURE,
                exposure_texts=("learn the pattern",),
                probe_text="cat dog cat dog",
                expected_target_digest="d37efc29b0c680ba",
                expected_target_shape="A B A B",
                expected_prior_acquired=True,
                expected_transfer=True,
            ),
        ),
        (
            "forbidden term in probe",
            dict(
                trial_id="T_bad",
                condition=OsmoticCondition.TRUE_EXPOSURE,
                exposure_texts=("red blue red blue",),
                probe_text="remember this structure",
                expected_target_digest="d37efc29b0c680ba",
                expected_target_shape="A B A B",
                expected_prior_acquired=True,
                expected_transfer=True,
            ),
        ),
        (
            "non-OsmoticCondition condition",
            dict(
                trial_id="T_bad",
                condition="true_exposure",
                exposure_texts=(),
                probe_text="cat dog cat dog",
                expected_target_digest="d37efc29b0c680ba",
                expected_target_shape="A B A B",
                expected_prior_acquired=True,
                expected_transfer=True,
            ),
        ),
        (
            "non-tuple exposure_texts",
            dict(
                trial_id="T_bad",
                condition=OsmoticCondition.TRUE_EXPOSURE,
                exposure_texts=["red blue red blue"],
                probe_text="cat dog cat dog",
                expected_target_digest="d37efc29b0c680ba",
                expected_target_shape="A B A B",
                expected_prior_acquired=True,
                expected_transfer=True,
            ),
        ),
        (
            "oversize exposure batch",
            dict(
                trial_id="T_bad",
                condition=OsmoticCondition.TRUE_EXPOSURE,
                exposure_texts=tuple(
                    [f"alpha {i}" for i in range(OSMOTIC_MAX_EXPOSURES_PER_TRIAL + 1)]
                ),
                probe_text="cat dog cat dog",
                expected_target_digest="d37efc29b0c680ba",
                expected_target_shape="A B A B",
                expected_prior_acquired=True,
                expected_transfer=True,
            ),
        ),
        (
            "non-hex digest",
            dict(
                trial_id="T_bad",
                condition=OsmoticCondition.TRUE_EXPOSURE,
                exposure_texts=("red blue red blue",),
                probe_text="cat dog cat dog",
                expected_target_digest="not-hex",
                expected_target_shape="A B A B",
                expected_prior_acquired=True,
                expected_transfer=True,
            ),
        ),
        (
            "non-bool expected_prior",
            dict(
                trial_id="T_bad",
                condition=OsmoticCondition.TRUE_EXPOSURE,
                exposure_texts=("red blue red blue",),
                probe_text="cat dog cat dog",
                expected_target_digest="d37efc29b0c680ba",
                expected_target_shape="A B A B",
                expected_prior_acquired=1,
                expected_transfer=True,
            ),
        ),
    )
    for tag, bad in rejection_cases:
        raised = False
        try:
            OsmoticProbeTrial(**bad)
        except (TypeError, ValueError):
            raised = True
        assert raised, (
            f"I-OSMO-02 violated: OsmoticProbeTrial accepted invalid "
            f"input ({tag})"
        )
