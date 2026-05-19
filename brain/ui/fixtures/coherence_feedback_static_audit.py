"""Phase 3.20 coherence feedback static audit.

Drives ``I-CFBK-02`` (STRUCTURAL). The audit confirms that:

* :class:`FeedbackMode` is a closed ``(str, Enum)`` whose
  membership exactly matches
  ``{OFF, PATTERN_LEDGER, COHERENCE, PATTERN_AND_COHERENCE}``.
* :func:`validate_feedback_mode` accepts every member and
  rejects non-``FeedbackMode`` input (``bool``, ``int``,
  ``str``, ``None``, ``object()``).
* :func:`build_cohmon_summary_text` is a pure deterministic
  function: same inputs yield byte-identical output across two
  invocations.
* Output of :func:`build_cohmon_summary_text` over a
  representative input set is bounded printable, under
  :data:`STREAM_TEXT_MAX_LEN` and
  :data:`COHMON_SUMMARY_TEXT_MAX_LEN`, starts with
  ``"cohmon_summary "``, contains no :data:`COGITO_ID`, and
  contains no term from
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  (case-insensitive).
* Bounded constructor invariants on
  :func:`build_cohmon_summary_text`:
    - rejects non-``str`` / empty / non-printable / ``COGITO_ID``
      ``overall_status_value``;
    - rejects unknown ``overall_status_value``;
    - rejects non-``int`` / ``bool`` / negative / over-cap per-status
      counts;
    - rejects mismatched ``check_count`` (one that does not equal
      ``pass_count + warn_count + fail_count + na_count``).
* The widened :data:`_V1_EMITTED_SOURCES` set is observable
  through :func:`build_rehearsal_provenance`: ``REHEARSAL``,
  ``PLEDGER_SUMMARY``, AND ``COHMON_SUMMARY`` now all produce
  non-claim-clean bounded provenances. No
  :class:`InternalEventSource` member is reserved at v0.28.
* :data:`MODULE_PRODUCED_STRINGS` extends to include
  :data:`COHMON_SUMMARY_TEXT_PREFIX` (``"cohmon_summary"``),
  ``FeedbackMode.COHERENCE.value`` (``"coherence"``), and
  ``FeedbackMode.PATTERN_AND_COHERENCE.value``
  (``"pattern_and_coherence"``) without violating the non-claim
  audit.

The audit does NOT re-do the import / module-level / dynamic-
execution scan over ``brain/development/processing_window.py`` —
that surface remains covered by the Phase 3.18 ``I-PWND-02``
audit, which is widened to include the new ``COHMON_SUMMARY``
emit path.
"""
from __future__ import annotations

from brain.development.coherence_monitor import (
    _FORBIDDEN_NON_CLAIM_TERMS,
)
from brain.development.processing_window import (
    COHMON_SUMMARY_TEXT_MAX_LEN,
    COHMON_SUMMARY_TEXT_PREFIX,
    FeedbackMode,
    InternalEventSource,
    MODULE_PRODUCED_STRINGS,
    build_cohmon_summary_text,
    build_rehearsal_provenance,
    validate_feedback_mode,
)
from brain.development.text_stream import STREAM_TEXT_MAX_LEN
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


_EXPECTED_FEEDBACK_MODE_VALUES: frozenset[str] = frozenset({
    "off",
    "pattern_ledger",
    "coherence",
    "pattern_and_coherence",
    "worldlet",
    "pattern_coherence_worldlet",
})


# Representative input set for build_cohmon_summary_text. Every
# tuple is (overall_status_value, pass_count, warn_count,
# fail_count, na_count, check_count) with check_count =
# pass+warn+fail+na.
_REPRESENTATIVE_COHMON_INPUTS: tuple[
    tuple[str, int, int, int, int, int], ...
] = (
    ("pass", 0, 0, 0, 0, 0),
    ("pass", 1, 0, 0, 0, 1),
    ("pass", 20, 0, 0, 5, 25),
    ("warn", 18, 2, 0, 5, 25),
    ("fail", 10, 5, 5, 5, 25),
    ("not_applicable", 0, 0, 0, 25, 25),
    ("pass", 64, 0, 0, 0, 64),
    ("fail", 0, 0, 64, 0, 64),
)


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-CFBK-02", status="STRUCTURAL")
def check_coherence_feedback_static_audit() -> None:
    """Static audit for the Phase 3.20 coherence-feedback surface."""

    # 1. FeedbackMode is a closed (str, Enum) with the locked v0.28
    # value set.
    assert issubclass(FeedbackMode, str), (
        "I-CFBK-02 violated: FeedbackMode is not a str enum"
    )
    actual_values = frozenset(m.value for m in FeedbackMode)
    assert actual_values == _EXPECTED_FEEDBACK_MODE_VALUES, (
        "I-CFBK-02 violated: FeedbackMode value set drifted "
        f"(got {sorted(actual_values)!r}, expected "
        f"{sorted(_EXPECTED_FEEDBACK_MODE_VALUES)!r})"
    )

    # 2. validate_feedback_mode accepts every member and rejects
    # non-FeedbackMode input with a typed ValueError.
    for member in FeedbackMode:
        assert validate_feedback_mode(member) is member, (
            "I-CFBK-02 violated: validate_feedback_mode did not "
            f"return identity for {member!r}"
        )
    rejection_inputs: tuple[object, ...] = (
        "off",
        "pattern_ledger",
        "coherence",
        "pattern_and_coherence",
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
            "I-CFBK-02 violated: validate_feedback_mode accepted "
            f"non-FeedbackMode input {bad!r}"
        )

    # 3. build_cohmon_summary_text is deterministic and produces
    # bounded printable non-claim-clean strings over the
    # representative input set.
    for inputs in _REPRESENTATIVE_COHMON_INPUTS:
        (status, np_, nw, nf, nna, nc) = inputs
        first = build_cohmon_summary_text(
            overall_status_value=status,
            pass_count=np_,
            warn_count=nw,
            fail_count=nf,
            na_count=nna,
            check_count=nc,
        )
        second = build_cohmon_summary_text(
            overall_status_value=status,
            pass_count=np_,
            warn_count=nw,
            fail_count=nf,
            na_count=nna,
            check_count=nc,
        )
        assert first == second, (
            "I-CFBK-02 violated: build_cohmon_summary_text not "
            f"deterministic for inputs {inputs!r}: "
            f"{first!r} != {second!r}"
        )
        assert isinstance(first, str) and first.isprintable(), (
            "I-CFBK-02 violated: build_cohmon_summary_text "
            f"produced non-printable output {first!r}"
        )
        assert len(first) <= COHMON_SUMMARY_TEXT_MAX_LEN, (
            "I-CFBK-02 violated: build_cohmon_summary_text output "
            f"length {len(first)} exceeds "
            f"COHMON_SUMMARY_TEXT_MAX_LEN={COHMON_SUMMARY_TEXT_MAX_LEN}"
        )
        assert len(first) <= STREAM_TEXT_MAX_LEN, (
            "I-CFBK-02 violated: build_cohmon_summary_text output "
            f"length {len(first)} exceeds "
            f"STREAM_TEXT_MAX_LEN={STREAM_TEXT_MAX_LEN}"
        )
        assert first.startswith(COHMON_SUMMARY_TEXT_PREFIX + " "), (
            "I-CFBK-02 violated: build_cohmon_summary_text output "
            f"{first!r} does not begin with "
            f"{COHMON_SUMMARY_TEXT_PREFIX!r}"
        )
        assert COGITO_ID not in first, (
            "I-CFBK-02 violated: build_cohmon_summary_text output "
            f"{first!r} contains COGITO_ID"
        )
        term = _has_forbidden_term(first)
        assert term is None, (
            "I-CFBK-02 violated: build_cohmon_summary_text output "
            f"{first!r} contains forbidden non-claim term {term!r}"
        )

    # 4. Bounded-shape rejections on build_cohmon_summary_text.
    rejection_cases: tuple[tuple[dict[str, object], str], ...] = (
        (
            {"overall_status_value": None,
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "non-str overall_status_value",
        ),
        (
            {"overall_status_value": 123,
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "int overall_status_value",
        ),
        (
            {"overall_status_value": "",
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "empty overall_status_value",
        ),
        (
            {"overall_status_value": "bad\x00",
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "non-printable overall_status_value",
        ),
        (
            {"overall_status_value": COGITO_ID,
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "cogito overall_status_value",
        ),
        (
            {"overall_status_value": "PASS",
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "uppercase overall_status_value",
        ),
        (
            {"overall_status_value": "weird",
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 0},
            "unknown overall_status_value",
        ),
        (
            {"overall_status_value": "pass",
             "pass_count": "1", "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 1},
            "non-int pass_count",
        ),
        (
            {"overall_status_value": "pass",
             "pass_count": True, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 1},
            "bool pass_count",
        ),
        (
            {"overall_status_value": "pass",
             "pass_count": -1, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": -1},
            "negative pass_count",
        ),
        (
            {"overall_status_value": "pass",
             "pass_count": 65, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 65},
            "over-cap pass_count",
        ),
        (
            {"overall_status_value": "pass",
             "pass_count": 5, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 10},
            "check_count != sum",
        ),
        (
            {"overall_status_value": "pass",
             "pass_count": 0, "warn_count": 0,
             "fail_count": 0, "na_count": 0, "check_count": 1},
            "check_count > sum",
        ),
    )
    for (kwargs, tag) in rejection_cases:
        raised = False
        try:
            build_cohmon_summary_text(**kwargs)  # type: ignore[arg-type]
        except ValueError:
            raised = True
        assert raised, (
            "I-CFBK-02 violated: build_cohmon_summary_text accepted "
            f"invalid input ({tag})"
        )

    # 5. Widened _V1_EMITTED_SOURCES observable through
    # build_rehearsal_provenance: REHEARSAL, PLEDGER_SUMMARY, and
    # COHMON_SUMMARY all produce non-claim-clean bounded
    # provenances; no source is reserved at v0.28.
    for source in (
        InternalEventSource.REHEARSAL,
        InternalEventSource.PLEDGER_SUMMARY,
        InternalEventSource.COHMON_SUMMARY,
        InternalEventSource.WORLDLET_SUMMARY,
    ):
        for k in (1, 2, 3, 42, 255):
            provenance = build_rehearsal_provenance(
                tick_index=k, source=source
            )
            assert (
                isinstance(provenance, str) and provenance.isprintable()
            ), (
                "I-CFBK-02 violated: build_rehearsal_provenance produced "
                f"non-printable output for ({source.value!r}, {k})"
            )
            assert COGITO_ID not in provenance, (
                "I-CFBK-02 violated: build_rehearsal_provenance output "
                f"{provenance!r} contains COGITO_ID"
            )
            term = _has_forbidden_term(provenance)
            assert term is None, (
                "I-CFBK-02 violated: build_rehearsal_provenance output "
                f"{provenance!r} contains forbidden non-claim term "
                f"{term!r}"
            )

    # 6. MODULE_PRODUCED_STRINGS extends to include the new Phase
    # 3.20 constants without violating the non-claim audit.
    expected_subset: frozenset[str] = frozenset({
        COHMON_SUMMARY_TEXT_PREFIX,
        FeedbackMode.COHERENCE.value,
        FeedbackMode.PATTERN_AND_COHERENCE.value,
    })
    actual_set = frozenset(MODULE_PRODUCED_STRINGS)
    missing = expected_subset - actual_set
    assert not missing, (
        "I-CFBK-02 violated: MODULE_PRODUCED_STRINGS missing Phase "
        f"3.20 entries {sorted(missing)!r}"
    )
    for produced in MODULE_PRODUCED_STRINGS:
        term = _has_forbidden_term(produced)
        assert term is None, (
            "I-CFBK-02 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden non-claim term {term!r}"
        )
