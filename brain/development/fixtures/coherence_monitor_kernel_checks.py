"""Fixture for I-COHMON-04: kernel coherence checks are read-only.

A healthy initial :class:`BrainState` yields PASS on every kernel
coherence check; running the checks leaves ``BrainState`` /
``profile`` / ``MSI`` / ``PtCns`` / ``ContentRegistry`` /
``latest_tick`` / ``tick_counter`` identity-stable.

The fixture also exercises a controlled FAIL path through the
:func:`compute_overall_status` aggregator without mutating the live
``BrainState`` — it builds a fresh `CoherenceCheck` list that
includes a FAIL entry and confirms the overall status reflects it.
The kernel check builders themselves only return FAIL when the
underlying record violates an invariant the kernel itself rejects
at construction time, so a purely-runtime FAIL trip would require
bypassing the kernel record constructors (out of scope).
"""
from __future__ import annotations

from brain.development.coherence_monitor import (
    CoherenceCheck,
    CoherenceCheckStatus,
    build_kernel_checks,
    compute_overall_status,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.session import OperatorSession


def _kernel_identity(session: OperatorSession) -> tuple:
    state = session.state
    return (
        id(state),
        id(state.profile),
        id(state.profile.values),
        id(state.msi),
        id(state.msi.contents),
        id(state.ptcns),
        id(state.ptcns.eval_map),
        id(state.registry),
        id(state.registry.texts),
        session.tick_counter,
        id(session.latest_tick),
        repr(state),
    )


@register("I-COHMON-04", status="REQUIRED")
def check_kernel_coherence_checks_are_read_only() -> None:
    session = OperatorSession(state=initial_state())
    pre = _kernel_identity(session)

    checks = build_kernel_checks(session)
    assert isinstance(checks, tuple), (
        "I-COHMON-04 violated: build_kernel_checks did not return a tuple"
    )
    assert len(checks) >= 5, (
        f"I-COHMON-04 violated: expected at least 5 kernel checks, "
        f"got {len(checks)}"
    )
    for c in checks:
        assert isinstance(c, CoherenceCheck), (
            f"I-COHMON-04 violated: kernel check has wrong type "
            f"{type(c).__name__}"
        )
        assert c.source == "kernel", (
            f"I-COHMON-04 violated: kernel check {c.check_id!r} has source "
            f"{c.source!r} != 'kernel'"
        )

    # On a healthy initial session, every kernel check is either PASS
    # or NOT_APPLICABLE (e.g. latest_tick is None on a fresh session).
    for c in checks:
        assert c.status in (
            CoherenceCheckStatus.PASS,
            CoherenceCheckStatus.NOT_APPLICABLE,
        ), (
            f"I-COHMON-04 violated: healthy kernel check {c.check_id!r} "
            f"status={c.status.value} (expected PASS or NOT_APPLICABLE)"
        )

    # Aggregated kernel status is PASS (at least one PASS, no
    # FAIL / WARN). Drives the kernel-checks slice of I-COHMON-09.
    overall = compute_overall_status(checks)
    assert overall is CoherenceCheckStatus.PASS, (
        f"I-COHMON-04 violated: healthy kernel overall status "
        f"{overall.value}"
    )

    # Required check_ids appear.
    ids = {c.check_id for c in checks}
    required_ids = {
        "kernel.cogito_in_profile",
        "kernel.cogito_in_msi",
        "kernel.profile_values_bounded",
        "kernel.ptcns_total_over_profile_domain",
        "kernel.msi_subset_profile_domain",
        "kernel.latest_tick_index_agrees",
    }
    missing = required_ids - ids
    assert not missing, (
        f"I-COHMON-04 violated: kernel checks missing {sorted(missing)!r}"
    )

    # Identity-stable: no kernel container changed.
    post = _kernel_identity(session)
    assert pre == post, (
        "I-COHMON-04 violated: kernel state mutated by check run"
    )

    # Defense in depth: a synthetic check list including a FAIL
    # entry aggregates to FAIL without touching the live session.
    synthetic = checks + (
        CoherenceCheck(
            check_id="synthetic.fail",
            status=CoherenceCheckStatus.FAIL,
            summary="synthetic fail",
            detail="",
            source="kernel",
        ),
    )
    assert compute_overall_status(synthetic) is CoherenceCheckStatus.FAIL
    # Synthetic build did not mutate either.
    assert _kernel_identity(session) == post, (
        "I-COHMON-04 violated: synthetic FAIL build mutated session"
    )
