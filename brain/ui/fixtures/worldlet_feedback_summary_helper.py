"""Phase 3.24 worldlet summary helper determinism / bounds fixture.

Drives ``I-WFDBK-01`` (REQUIRED). Audits the pure deterministic
``build_worldlet_summary_text`` helper.
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.processing_window import (
    WORLDLET_SUMMARY_ABSENT_SENTINEL,
    WORLDLET_SUMMARY_TEXT_MAX_LEN,
    WORLDLET_SUMMARY_TEXT_PREFIX,
    build_worldlet_summary_text,
)
from brain.development.text_stream import STREAM_TEXT_MAX_LEN
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


_REPRESENTATIVE_INPUTS = (
    dict(
        state_id_value=WORLDLET_SUMMARY_ABSENT_SENTINEL,
        step_index=0,
        object_count=0,
        attempt_count=0,
        response_count=0,
        accepted_count=0,
        pushback_count=0,
        last_reason_value=WORLDLET_SUMMARY_ABSENT_SENTINEL,
    ),
    dict(
        state_id_value="wld:state:0000000000000000",
        step_index=1,
        object_count=1,
        attempt_count=1,
        response_count=1,
        accepted_count=1,
        pushback_count=0,
        last_reason_value="accepted",
    ),
    dict(
        state_id_value="wld:state:abcdef0123456789",
        step_index=42,
        object_count=4,
        attempt_count=8,
        response_count=8,
        accepted_count=3,
        pushback_count=5,
        last_reason_value="rejected",
    ),
    dict(
        state_id_value="wld:state:ffffffffffffffff",
        step_index=255,
        object_count=8,
        attempt_count=10,
        response_count=10,
        accepted_count=4,
        pushback_count=6,
        last_reason_value="target-unavailable",
    ),
    dict(
        state_id_value="wld:state:1234567890abcdef",
        step_index=65535,
        object_count=256,
        attempt_count=256,
        response_count=256,
        accepted_count=128,
        pushback_count=128,
        last_reason_value="missing-target",
    ),
)


@register("I-WFDBK-01", status="REQUIRED")
def check_worldlet_summary_helper() -> None:
    """Audit build_worldlet_summary_text determinism + bounds."""

    # 1. Determinism + bounds + printability + non-claim audit.
    for kwargs in _REPRESENTATIVE_INPUTS:
        text_a = build_worldlet_summary_text(**kwargs)
        text_b = build_worldlet_summary_text(**kwargs)
        assert text_a == text_b, (
            f"I-WFDBK-01 violated: helper not deterministic for {kwargs!r}"
        )
        assert text_a.startswith(WORLDLET_SUMMARY_TEXT_PREFIX + " "), (
            f"I-WFDBK-01 violated: helper output {text_a!r} does not start "
            f"with {WORLDLET_SUMMARY_TEXT_PREFIX + ' '!r}"
        )
        assert text_a.isprintable(), (
            f"I-WFDBK-01 violated: helper output not printable: {text_a!r}"
        )
        assert len(text_a) <= WORLDLET_SUMMARY_TEXT_MAX_LEN, (
            f"I-WFDBK-01 violated: helper output length {len(text_a)} > "
            f"WORLDLET_SUMMARY_TEXT_MAX_LEN={WORLDLET_SUMMARY_TEXT_MAX_LEN}"
        )
        assert len(text_a) <= STREAM_TEXT_MAX_LEN, (
            f"I-WFDBK-01 violated: helper output length {len(text_a)} > "
            f"STREAM_TEXT_MAX_LEN={STREAM_TEXT_MAX_LEN}"
        )
        assert COGITO_ID not in text_a, (
            f"I-WFDBK-01 violated: helper output contains COGITO_ID: "
            f"{text_a!r}"
        )
        term = _has_forbidden(text_a)
        assert term is None, (
            f"I-WFDBK-01 violated: helper output {text_a!r} contains "
            f"forbidden non-claim term {term!r}"
        )

    # 2. Invalid inputs raise ValueError.
    base = dict(
        state_id_value="wld:state:abc",
        step_index=0,
        object_count=0,
        attempt_count=0,
        response_count=0,
        accepted_count=0,
        pushback_count=0,
        last_reason_value="absent",
    )
    rejection_cases = (
        ("non-empty state_id", {**base, "state_id_value": ""}),
        ("non-str state_id", {**base, "state_id_value": 123}),
        ("cogito state_id", {**base, "state_id_value": COGITO_ID}),
        ("oversize state_id", {**base, "state_id_value": "x" * 65}),
        ("bool step_index", {**base, "step_index": True}),
        ("negative step_index", {**base, "step_index": -1}),
        ("over-cap step_index", {**base, "step_index": 65536}),
        ("over-cap object_count", {**base, "object_count": 257}),
        ("negative response_count", {**base, "response_count": -1}),
        ("over-cap accepted_count", {**base, "accepted_count": 257}),
        (
            "accepted+pushback > response",
            {
                **base,
                "response_count": 1,
                "accepted_count": 1,
                "pushback_count": 1,
                "last_reason_value": "accepted",
            },
        ),
        ("non-member last_reason", {**base, "last_reason_value": "weird"}),
        ("non-str last_reason", {**base, "last_reason_value": 1}),
    )
    for tag, bad_kwargs in rejection_cases:
        raised = False
        try:
            build_worldlet_summary_text(**bad_kwargs)
        except ValueError:
            raised = True
        assert raised, (
            f"I-WFDBK-01 violated: helper accepted invalid input ({tag})"
        )

    # 3. The "absent" sentinel summary contains both state=absent and
    # last_reason=absent literally.
    absent_text = build_worldlet_summary_text(
        state_id_value=WORLDLET_SUMMARY_ABSENT_SENTINEL,
        step_index=0,
        object_count=0,
        attempt_count=0,
        response_count=0,
        accepted_count=0,
        pushback_count=0,
        last_reason_value=WORLDLET_SUMMARY_ABSENT_SENTINEL,
    )
    assert "state=absent" in absent_text and "last_reason=absent" in absent_text
