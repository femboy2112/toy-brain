"""Fixtures for I-COHMON-01..03, I-COHMON-09 (constructor + aggregation).

* I-COHMON-01 — :class:`CoherenceCheckStatus` is a finite closed enum.
* I-COHMON-02 — :class:`CoherenceCheck` constructor enforces bounded
  printable ``check_id`` / ``summary`` / ``detail`` / ``source`` and
  a closed-set ``source`` membership.
* I-COHMON-03 — :class:`CoherenceSnapshot` and :class:`CoherenceReport`
  constructors enforce bounded non-negative counts, tuple checks, a
  cap of ``COHERENCE_MAX_CHECKS`` entries, and deterministic
  ``counts_by_status`` shape.
* I-COHMON-09 — :func:`compute_overall_status` is deterministic:
  ``FAIL`` dominates ``WARN`` dominates ``PASS``; ``NOT_APPLICABLE``
  does not create a false PASS or FAIL.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

from brain.development.coherence_monitor import (
    CHECK_SOURCES,
    COHERENCE_MAX_CHECKS,
    MAX_CHECK_ID_LEN,
    MAX_DETAIL_LEN,
    MAX_SOURCE_LEN,
    MAX_SUMMARY_LEN,
    CoherenceCheck,
    CoherenceCheckStatus,
    CoherenceReport,
    CoherenceSnapshot,
    compute_overall_status,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _valid_check_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        check_id="kernel.example",
        status=CoherenceCheckStatus.PASS,
        summary="example summary",
        detail="example detail",
        source="kernel",
    )
    base.update(overrides)
    return base


def _valid_snapshot_kwargs(**overrides: object) -> dict[str, object]:
    sample_check = CoherenceCheck(**_valid_check_kwargs())
    base: dict[str, object] = dict(
        snapshot_id="coh-snap-1",
        tick_counter=0,
        profile_domain_size=1,
        msi_size=1,
        registry_size=0,
        stream_chunk_count=0,
        stream_candidate_count=0,
        pattern_ledger_entry_count=0,
        autosave_mode="",
        session_db_configured=False,
        checks=(sample_check,),
    )
    base.update(overrides)
    return base


def _valid_report_kwargs(**overrides: object) -> dict[str, object]:
    snap = CoherenceSnapshot(**_valid_snapshot_kwargs())
    base: dict[str, object] = dict(
        snapshot=snap,
        overall_status=CoherenceCheckStatus.PASS,
        counts_by_status=(
            ("pass", 1),
            ("warn", 0),
            ("fail", 0),
            ("not_applicable", 0),
        ),
        summary_text="ok",
    )
    base.update(overrides)
    return base


def _assert_rejects(call, tag: str) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert tag in str(exc), (
            f"{tag} negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            f"{tag} violated: invalid record was accepted"
        )


@register("I-COHMON-01", status="REQUIRED")
def check_coherence_check_status_closed() -> None:
    members = {m.value for m in CoherenceCheckStatus}
    expected = {"pass", "warn", "fail", "not_applicable"}
    assert members == expected, (
        f"I-COHMON-01 violated: CoherenceCheckStatus membership drifted "
        f"(got {members!r}, expected {expected!r})"
    )

    try:
        CoherenceCheckStatus("unknown")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-COHMON-01 violated: CoherenceCheckStatus accepted unknown value"
        )

    # CHECK_SOURCES is also a finite closed set used by I-COHMON-02.
    expected_sources = {
        "kernel",
        "session",
        "stream",
        "pattern_ledger",
        "persistence_autosave",
        "non_claim",
    }
    assert CHECK_SOURCES == expected_sources, (
        f"I-COHMON-01 / CHECK_SOURCES drifted: got {CHECK_SOURCES!r}, "
        f"expected {expected_sources!r}"
    )


@register("I-COHMON-02", status="REQUIRED")
def check_coherence_check_constructor() -> None:
    check = CoherenceCheck(**_valid_check_kwargs())
    assert check.check_id == "kernel.example"
    assert check.status is CoherenceCheckStatus.PASS
    assert check.source == "kernel"

    # Frozen / slotted.
    assert is_dataclass(check)
    assert getattr(type(check), "__dataclass_params__").frozen
    try:
        check.check_id = "mutated"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-COHMON-02 violated: CoherenceCheck is not frozen"
        )

    # Bounded printable + COGITO_ID rejection on id-bearing fields.
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(check_id="")),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(check_id="bad\x00id")),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(
            **_valid_check_kwargs(check_id="c" * (MAX_CHECK_ID_LEN + 1))
        ),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(check_id=COGITO_ID)),
        tag="I-COHMON-02",
    )

    # status must be a CoherenceCheckStatus.
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(status="pass")),
        tag="I-COHMON-02",
    )

    # Bounded printable summary / detail (detail allows empty).
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(summary="")),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(
            **_valid_check_kwargs(summary="s" * (MAX_SUMMARY_LEN + 1))
        ),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(
            **_valid_check_kwargs(detail="d" * (MAX_DETAIL_LEN + 1))
        ),
        tag="I-COHMON-02",
    )
    # Empty detail is allowed (the constructor accepts it).
    check_empty_detail = CoherenceCheck(**_valid_check_kwargs(detail=""))
    assert check_empty_detail.detail == ""

    # Source must be bounded printable and in the closed set.
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(source="")),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(
            **_valid_check_kwargs(source="s" * (MAX_SOURCE_LEN + 1))
        ),
        tag="I-COHMON-02",
    )
    _assert_rejects(
        lambda: CoherenceCheck(**_valid_check_kwargs(source="not-a-source")),
        tag="I-COHMON-02",
    )

    # Forbidden attribute surface (defense against accidental
    # truth / agency / I-ness fields).
    forbidden_attrs = (
        "score",
        "iness",
        "confidence",
        "rating",
        "mode_op",
        "mode",
    )
    for name in forbidden_attrs:
        assert not hasattr(check, name), (
            f"I-COHMON-02 violated: CoherenceCheck exposes forbidden field {name!r}"
        )


@register("I-COHMON-03", status="REQUIRED")
def check_coherence_snapshot_and_report_constructor() -> None:
    # Valid construction.
    snap = CoherenceSnapshot(**_valid_snapshot_kwargs())
    assert snap.snapshot_id == "coh-snap-1"
    assert isinstance(snap.checks, tuple)
    assert is_dataclass(snap)
    assert getattr(type(snap), "__dataclass_params__").frozen

    # Non-negative int counts.
    for field_name in (
        "tick_counter",
        "profile_domain_size",
        "msi_size",
        "registry_size",
        "stream_chunk_count",
        "stream_candidate_count",
        "pattern_ledger_entry_count",
    ):
        _assert_rejects(
            lambda fn=field_name: CoherenceSnapshot(
                **_valid_snapshot_kwargs(**{fn: -1})
            ),
            tag="I-COHMON-03",
        )
        _assert_rejects(
            lambda fn=field_name: CoherenceSnapshot(
                **_valid_snapshot_kwargs(**{fn: "0"})
            ),
            tag="I-COHMON-03",
        )

    # snapshot_id rejects COGITO_ID and over-length.
    _assert_rejects(
        lambda: CoherenceSnapshot(**_valid_snapshot_kwargs(snapshot_id="")),
        tag="I-COHMON-03",
    )
    _assert_rejects(
        lambda: CoherenceSnapshot(
            **_valid_snapshot_kwargs(snapshot_id=COGITO_ID)
        ),
        tag="I-COHMON-03",
    )

    # session_db_configured must be bool.
    _assert_rejects(
        lambda: CoherenceSnapshot(
            **_valid_snapshot_kwargs(session_db_configured=1)
        ),
        tag="I-COHMON-03",
    )

    # checks must be a tuple of CoherenceCheck.
    _assert_rejects(
        lambda: CoherenceSnapshot(**_valid_snapshot_kwargs(checks=[])),
        tag="I-COHMON-03",
    )
    _assert_rejects(
        lambda: CoherenceSnapshot(
            **_valid_snapshot_kwargs(checks=("not-a-check",))
        ),
        tag="I-COHMON-03",
    )

    # Cap enforced.
    too_many = tuple(
        CoherenceCheck(**_valid_check_kwargs(check_id=f"x{i}"))
        for i in range(COHERENCE_MAX_CHECKS + 1)
    )
    _assert_rejects(
        lambda: CoherenceSnapshot(**_valid_snapshot_kwargs(checks=too_many)),
        tag="I-COHMON-03",
    )
    # Exactly at cap is accepted.
    at_cap = tuple(
        CoherenceCheck(**_valid_check_kwargs(check_id=f"x{i}"))
        for i in range(COHERENCE_MAX_CHECKS)
    )
    cap_snap = CoherenceSnapshot(**_valid_snapshot_kwargs(checks=at_cap))
    assert len(cap_snap.checks) == COHERENCE_MAX_CHECKS

    # autosave_mode is bounded printable; empty is allowed.
    _assert_rejects(
        lambda: CoherenceSnapshot(
            **_valid_snapshot_kwargs(autosave_mode="m" * (MAX_SOURCE_LEN + 1))
        ),
        tag="I-COHMON-03",
    )
    snap_no_autosave = CoherenceSnapshot(**_valid_snapshot_kwargs(autosave_mode=""))
    assert snap_no_autosave.autosave_mode == ""

    # CoherenceReport constructor.
    report = CoherenceReport(**_valid_report_kwargs())
    assert report.overall_status is CoherenceCheckStatus.PASS

    # counts_by_status must be a tuple of (str, int) pairs.
    _assert_rejects(
        lambda: CoherenceReport(
            **_valid_report_kwargs(counts_by_status=[("pass", 1)])
        ),
        tag="I-COHMON-03",
    )
    _assert_rejects(
        lambda: CoherenceReport(
            **_valid_report_kwargs(counts_by_status=(("pass", -1),))
        ),
        tag="I-COHMON-03",
    )
    _assert_rejects(
        lambda: CoherenceReport(
            **_valid_report_kwargs(
                counts_by_status=(("pass", 1), ("pass", 2))
            )
        ),
        tag="I-COHMON-03",
    )

    # overall_status must be a closed enum value.
    _assert_rejects(
        lambda: CoherenceReport(**_valid_report_kwargs(overall_status="pass")),
        tag="I-COHMON-03",
    )


@register("I-COHMON-09", status="REQUIRED")
def check_overall_status_is_deterministic() -> None:
    pass_check = CoherenceCheck(**_valid_check_kwargs())
    warn_check = CoherenceCheck(**_valid_check_kwargs(status=CoherenceCheckStatus.WARN))
    fail_check = CoherenceCheck(**_valid_check_kwargs(status=CoherenceCheckStatus.FAIL))
    na_check = CoherenceCheck(**_valid_check_kwargs(status=CoherenceCheckStatus.NOT_APPLICABLE))

    # FAIL dominates everything else.
    assert (
        compute_overall_status((pass_check, warn_check, fail_check, na_check))
        is CoherenceCheckStatus.FAIL
    )
    assert (
        compute_overall_status((fail_check, pass_check))
        is CoherenceCheckStatus.FAIL
    )

    # WARN dominates PASS and NOT_APPLICABLE.
    assert (
        compute_overall_status((pass_check, warn_check, na_check))
        is CoherenceCheckStatus.WARN
    )
    assert (
        compute_overall_status((warn_check, na_check))
        is CoherenceCheckStatus.WARN
    )

    # PASS applies when at least one PASS exists and no FAIL/WARN.
    assert (
        compute_overall_status((pass_check, na_check))
        is CoherenceCheckStatus.PASS
    )
    assert (
        compute_overall_status((pass_check,))
        is CoherenceCheckStatus.PASS
    )

    # NOT_APPLICABLE alone yields NOT_APPLICABLE.
    assert (
        compute_overall_status((na_check,))
        is CoherenceCheckStatus.NOT_APPLICABLE
    )
    # Empty tuple yields NOT_APPLICABLE (no false PASS).
    assert (
        compute_overall_status(())
        is CoherenceCheckStatus.NOT_APPLICABLE
    )

    # Argument shape validated.
    try:
        compute_overall_status([pass_check])  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-COHMON-09 violated: compute_overall_status accepted non-tuple"
        )
    try:
        compute_overall_status(("not-a-check",))  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-COHMON-09 violated: compute_overall_status accepted non-CoherenceCheck"
        )
