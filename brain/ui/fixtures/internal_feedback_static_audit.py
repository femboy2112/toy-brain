"""Phase 3.19 internal feedback static audit.

Drives ``I-IFBK-02`` (STRUCTURAL). The audit confirms that:

* :class:`FeedbackMode` is a closed ``(str, Enum)`` whose
  membership exactly matches ``{OFF, PATTERN_LEDGER}``.
* :func:`validate_feedback_mode` accepts every member and rejects
  non-``FeedbackMode`` input (``bool``, ``int``, ``str``,
  ``None``, dotted lookalikes).
* :func:`build_pledger_summary_text` is a pure deterministic
  function: same inputs yield byte-identical output across two
  invocations.
* Output of :func:`build_pledger_summary_text` over a
  representative input set is bounded printable, under
  ``STREAM_TEXT_MAX_LEN`` and ``PLEDGER_SUMMARY_TEXT_MAX_LEN``,
  contains no ``COGITO_ID``, and contains no term from
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  (case-insensitive).
* Bounded constructor invariants on
  :func:`build_pledger_summary_text`:
    - rejects non-``str`` ``pattern_id``;
    - rejects empty / non-printable ``pattern_id``;
    - rejects ``COGITO_ID`` as ``pattern_id``;
    - rejects ``bool`` / non-``int`` ``recurrence_count``;
    - rejects negative ``recurrence_count``;
    - rejects ``recurrence_count > 256``;
    - rejects non-``str`` ``saturation_state_value``;
    - rejects unknown ``saturation_state_value``.
* The widened ``_V1_EMITTED_SOURCES`` set behavior is observable
  through :func:`build_rehearsal_provenance`:
    - ``REHEARSAL`` produces a non-claim-clean bounded provenance;
    - ``PLEDGER_SUMMARY`` produces a non-claim-clean bounded
      provenance (Phase 3.19 addition);
    - ``COHMON_SUMMARY`` continues to raise (LOCK F).
* :data:`MODULE_PRODUCED_STRINGS` extends to include every new
  bounded printable constant introduced by Phase 3.19 (the
  feedback-text prefix, both ``FeedbackMode`` values) without
  violating the non-claim audit.

The audit does NOT re-do the import / module-level / dynamic-
execution scan over ``brain/development/processing_window.py`` —
that surface remains covered by the Phase 3.18 ``I-PWND-02``
audit, which is widened to include the new
``PLEDGER_SUMMARY`` emit path.
"""
from __future__ import annotations

from brain.development.coherence_monitor import (
    _FORBIDDEN_NON_CLAIM_TERMS,
)
from brain.development.processing_window import (
    FeedbackMode,
    InternalEventSource,
    MODULE_PRODUCED_STRINGS,
    PLEDGER_SUMMARY_TEXT_MAX_LEN,
    PLEDGER_SUMMARY_TEXT_PREFIX,
    build_pledger_summary_text,
    build_rehearsal_provenance,
    validate_feedback_mode,
)
from brain.development.text_stream import STREAM_TEXT_MAX_LEN
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


_EXPECTED_FEEDBACK_MODE_VALUES: frozenset[str] = frozenset({
    "off",
    "pattern_ledger",
})


_REPRESENTATIVE_SUMMARY_INPUTS: tuple[tuple[str, int, str], ...] = (
    ("pledger:0000000000000000", 0, "open"),
    ("pledger:a5e6f92cd3330c9b", 1, "open"),
    ("pledger:a5e6f92cd3330c9b", 2, "open"),
    ("pledger:a5e6f92cd3330c9b", 3, "open"),
    ("pledger:a5e6f92cd3330c9b", 42, "open"),
    ("pledger:a5e6f92cd3330c9b", 255, "open"),
    ("pledger:a5e6f92cd3330c9b", 256, "saturated"),
    ("pledger:ffffffffffffffff", 100, "quiesced"),
)


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-IFBK-02", status="STRUCTURAL")
def check_internal_feedback_static_audit() -> None:
    """Static audit for the Phase 3.19 internal-feedback surface."""

    # 1. FeedbackMode is a closed (str, Enum) with the locked
    # value set {off, pattern_ledger}.
    assert issubclass(FeedbackMode, str), (
        "I-IFBK-02 violated: FeedbackMode is not a str enum"
    )
    actual_values = frozenset(m.value for m in FeedbackMode)
    assert actual_values == _EXPECTED_FEEDBACK_MODE_VALUES, (
        "I-IFBK-02 violated: FeedbackMode value set drifted "
        f"(got {sorted(actual_values)!r}, expected "
        f"{sorted(_EXPECTED_FEEDBACK_MODE_VALUES)!r})"
    )

    # 2. validate_feedback_mode accepts every member and rejects
    # non-FeedbackMode input with a typed ValueError.
    for member in FeedbackMode:
        assert validate_feedback_mode(member) is member, (
            "I-IFBK-02 violated: validate_feedback_mode did not "
            f"return identity for {member!r}"
        )
    rejection_inputs: tuple[object, ...] = (
        "off",
        "pattern_ledger",
        0,
        1,
        True,
        False,
        None,
        (),
        [],
        object(),
    )
    for bad in rejection_inputs:
        raised = False
        try:
            validate_feedback_mode(bad)  # type: ignore[arg-type]
        except ValueError:
            raised = True
        assert raised, (
            "I-IFBK-02 violated: validate_feedback_mode accepted "
            f"non-FeedbackMode input {bad!r}"
        )

    # 3. build_pledger_summary_text is deterministic and produces
    # bounded printable non-claim-clean strings over the
    # representative input set.
    for (pattern_id, recurrence_count, sat_value) in (
        _REPRESENTATIVE_SUMMARY_INPUTS
    ):
        first = build_pledger_summary_text(
            pattern_id=pattern_id,
            recurrence_count=recurrence_count,
            saturation_state_value=sat_value,
        )
        second = build_pledger_summary_text(
            pattern_id=pattern_id,
            recurrence_count=recurrence_count,
            saturation_state_value=sat_value,
        )
        assert first == second, (
            "I-IFBK-02 violated: build_pledger_summary_text not "
            f"deterministic for inputs ({pattern_id!r}, "
            f"{recurrence_count!r}, {sat_value!r}): "
            f"{first!r} != {second!r}"
        )
        assert isinstance(first, str) and first.isprintable(), (
            "I-IFBK-02 violated: build_pledger_summary_text "
            f"produced non-printable output {first!r}"
        )
        assert len(first) <= PLEDGER_SUMMARY_TEXT_MAX_LEN, (
            "I-IFBK-02 violated: build_pledger_summary_text output "
            f"length {len(first)} exceeds "
            f"PLEDGER_SUMMARY_TEXT_MAX_LEN={PLEDGER_SUMMARY_TEXT_MAX_LEN}"
        )
        assert len(first) <= STREAM_TEXT_MAX_LEN, (
            "I-IFBK-02 violated: build_pledger_summary_text output "
            f"length {len(first)} exceeds "
            f"STREAM_TEXT_MAX_LEN={STREAM_TEXT_MAX_LEN}"
        )
        assert first.startswith(PLEDGER_SUMMARY_TEXT_PREFIX + " "), (
            "I-IFBK-02 violated: build_pledger_summary_text output "
            f"{first!r} does not begin with "
            f"{PLEDGER_SUMMARY_TEXT_PREFIX!r}"
        )
        assert COGITO_ID not in first, (
            "I-IFBK-02 violated: build_pledger_summary_text output "
            f"{first!r} contains COGITO_ID"
        )
        term = _has_forbidden_term(first)
        assert term is None, (
            "I-IFBK-02 violated: build_pledger_summary_text output "
            f"{first!r} contains forbidden non-claim term {term!r}"
        )

    # 4. Bounded-shape rejections on build_pledger_summary_text.
    rejection_cases: tuple[tuple[object, object, object, str], ...] = (
        (None, 1, "open", "non-str pattern_id"),
        (123, 1, "open", "non-str pattern_id"),
        ("", 1, "open", "empty pattern_id"),
        ("pledger:bad\x00", 1, "open", "non-printable pattern_id"),
        (COGITO_ID, 1, "open", "cogito pattern_id"),
        ("pledger:a", "1", "open", "non-int recurrence_count"),
        ("pledger:a", True, "open", "bool recurrence_count"),
        ("pledger:a", -1, "open", "negative recurrence_count"),
        ("pledger:a", 257, "open", "over-cap recurrence_count"),
        ("pledger:a", 1, None, "non-str saturation_state_value"),
        ("pledger:a", 1, "weird", "unknown saturation_state_value"),
    )
    for (pattern_id, recurrence_count, sat_value, tag) in rejection_cases:
        raised = False
        try:
            build_pledger_summary_text(
                pattern_id=pattern_id,  # type: ignore[arg-type]
                recurrence_count=recurrence_count,  # type: ignore[arg-type]
                saturation_state_value=sat_value,  # type: ignore[arg-type]
            )
        except ValueError:
            raised = True
        assert raised, (
            "I-IFBK-02 violated: build_pledger_summary_text accepted "
            f"invalid input ({tag})"
        )

    # 5. The widened _V1_EMITTED_SOURCES set is observable through
    # build_rehearsal_provenance: REHEARSAL and PLEDGER_SUMMARY now
    # both produce non-claim-clean bounded provenances;
    # COHMON_SUMMARY continues to raise.
    for source in (
        InternalEventSource.REHEARSAL,
        InternalEventSource.PLEDGER_SUMMARY,
    ):
        for k in (1, 2, 3, 42, 255):
            provenance = build_rehearsal_provenance(tick_index=k, source=source)
            assert isinstance(provenance, str) and provenance.isprintable(), (
                "I-IFBK-02 violated: build_rehearsal_provenance produced "
                f"non-printable output for ({source.value!r}, {k})"
            )
            assert COGITO_ID not in provenance, (
                "I-IFBK-02 violated: build_rehearsal_provenance output "
                f"{provenance!r} contains COGITO_ID"
            )
            term = _has_forbidden_term(provenance)
            assert term is None, (
                "I-IFBK-02 violated: build_rehearsal_provenance output "
                f"{provenance!r} contains forbidden non-claim term "
                f"{term!r}"
            )
    raised = False
    try:
        build_rehearsal_provenance(
            tick_index=1, source=InternalEventSource.COHMON_SUMMARY
        )
    except ValueError:
        raised = True
    assert raised, (
        "I-IFBK-02 violated: build_rehearsal_provenance accepted "
        "reserved source COHMON_SUMMARY"
    )

    # 6. MODULE_PRODUCED_STRINGS extends to include the new Phase
    # 3.19 constants without violating the non-claim audit.
    expected_subset: frozenset[str] = frozenset({
        PLEDGER_SUMMARY_TEXT_PREFIX,
        FeedbackMode.OFF.value,
        FeedbackMode.PATTERN_LEDGER.value,
    })
    actual_set = frozenset(MODULE_PRODUCED_STRINGS)
    missing = expected_subset - actual_set
    assert not missing, (
        "I-IFBK-02 violated: MODULE_PRODUCED_STRINGS missing Phase "
        f"3.19 entries {sorted(missing)!r}"
    )
    for produced in MODULE_PRODUCED_STRINGS:
        term = _has_forbidden_term(produced)
        assert term is None, (
            "I-IFBK-02 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden non-claim term {term!r}"
        )
