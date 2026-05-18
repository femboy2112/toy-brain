"""Phase 3.23 dispatch tracer constructor + report bounds fixture.

Drives ``I-DTRACE-01`` and ``I-DTRACE-02`` (REQUIRED). Audits the
constructor discipline of ``DispatchTraceStep`` / ``DispatchTrace``
and the deterministic report builder ``build_dispatch_trace_report`` /
``dispatch_trace_digest_from_report``.
"""
from __future__ import annotations

from brain.development.dispatch_tracer import (
    DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES,
    DISPATCH_TRACE_FACT_KEY_MAX_LEN,
    DISPATCH_TRACE_FACT_VALUE_MAX_LEN,
    DISPATCH_TRACE_MAX_STEPS,
    DISPATCH_TRACE_STEP_FIELD_MAX_LEN,
    DispatchMutationKind,
    DispatchTrace,
    DispatchTraceDigest,
    DispatchTraceKind,
    DispatchTraceReport,
    DispatchTraceStatus,
    DispatchTraceStep,
    build_dispatch_trace_report,
    dispatch_trace_digest_from_report,
    format_dispatch_trace_table,
    new_dispatch_trace_builder,
)
from brain.invariants import register


def _seed_builder(interaction_id: str):
    b = new_dispatch_trace_builder(interaction_id)
    b.add(
        DispatchTraceKind.COMMAND_RECEIVED,
        command_kind="stream_append",
        route_label="stream-append",
        digest_contribution="cmd:stream_append",
    )
    b.add(
        DispatchTraceKind.ROUTE_SELECTED,
        command_kind="stream_append",
        route_label="stream-append",
        digest_contribution="route:stream-append",
    )
    b.add(
        DispatchTraceKind.MUTATION_CLASSIFIED,
        command_kind="stream_append",
        mutation_kind=DispatchMutationKind.STREAM_APPEND,
        status=DispatchTraceStatus.PASS,
        route_label="stream-append",
        derived_facts="mutation_kind=stream_append",
        digest_contribution="mut:stream_append",
    )
    b.add(
        DispatchTraceKind.TRACE_FINALIZED,
        command_kind="stream_append",
        route_label="stream-append",
        derived_facts="trace-finalized",
        digest_contribution="trace-finalized",
    )
    return b


@register("I-DTRACE-01", status="REQUIRED")
def check_dispatch_tracer_constructor_bounds() -> None:
    """Audit DispatchTraceStep + DispatchTrace bounds + step_index."""

    # 1. step_index out of range.
    for bad_idx in (0, -1, DISPATCH_TRACE_MAX_STEPS + 1):
        raised = False
        try:
            DispatchTraceStep(
                step_index=bad_idx,
                kind=DispatchTraceKind.COMMAND_RECEIVED,
                command_kind="x",
                mutation_kind=DispatchMutationKind.NONE,
                status=DispatchTraceStatus.NOT_APPLICABLE,
                route_label="r",
                before_facts=(),
                after_facts=(),
                derived_facts="",
                limitation_label="",
                digest_contribution="dc",
            )
        except (ValueError, TypeError):
            raised = True
        assert raised, f"step_index={bad_idx} should have raised"

    # 2. kind type mismatch.
    raised = False
    try:
        DispatchTraceStep(
            step_index=1,
            kind="command_received",  # type: ignore[arg-type]
            command_kind="x",
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label="r",
            before_facts=(),
            after_facts=(),
            derived_facts="",
            limitation_label="",
            digest_contribution="dc",
        )
    except TypeError:
        raised = True
    assert raised

    # 3. Oversize derived_facts.
    raised = False
    try:
        DispatchTraceStep(
            step_index=1,
            kind=DispatchTraceKind.COMMAND_RECEIVED,
            command_kind="x",
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label="r",
            before_facts=(),
            after_facts=(),
            derived_facts="x" * (DISPATCH_TRACE_STEP_FIELD_MAX_LEN + 1),
            limitation_label="",
            digest_contribution="dc",
        )
    except ValueError:
        raised = True
    assert raised

    # 4. Oversize before_facts cardinality.
    raised = False
    too_many_pairs = tuple(
        (f"k{i}", "v") for i in range(DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES + 1)
    )
    try:
        DispatchTraceStep(
            step_index=1,
            kind=DispatchTraceKind.PRE_STATE_SNAPSHOT,
            command_kind="x",
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label="r",
            before_facts=too_many_pairs,
            after_facts=(),
            derived_facts="",
            limitation_label="",
            digest_contribution="dc",
        )
    except ValueError:
        raised = True
    assert raised

    # 5. Oversize fact-key.
    raised = False
    try:
        DispatchTraceStep(
            step_index=1,
            kind=DispatchTraceKind.PRE_STATE_SNAPSHOT,
            command_kind="x",
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label="r",
            before_facts=(("k" * (DISPATCH_TRACE_FACT_KEY_MAX_LEN + 1), "v"),),
            after_facts=(),
            derived_facts="",
            limitation_label="",
            digest_contribution="dc",
        )
    except ValueError:
        raised = True
    assert raised

    # 6. Oversize fact-value.
    raised = False
    try:
        DispatchTraceStep(
            step_index=1,
            kind=DispatchTraceKind.PRE_STATE_SNAPSHOT,
            command_kind="x",
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label="r",
            before_facts=(("k", "v" * (DISPATCH_TRACE_FACT_VALUE_MAX_LEN + 1)),),
            after_facts=(),
            derived_facts="",
            limitation_label="",
            digest_contribution="dc",
        )
    except ValueError:
        raised = True
    assert raised

    # 7. DispatchTrace: empty step tuple.
    raised = False
    try:
        DispatchTrace(steps=(), interaction_id="dispatch:00001")
    except ValueError:
        raised = True
    assert raised

    # 8. DispatchTrace: out-of-order step_index.
    s1 = DispatchTraceStep(
        step_index=1,
        kind=DispatchTraceKind.COMMAND_RECEIVED,
        command_kind="x",
        mutation_kind=DispatchMutationKind.NONE,
        status=DispatchTraceStatus.NOT_APPLICABLE,
        route_label="r",
        before_facts=(),
        after_facts=(),
        derived_facts="",
        limitation_label="",
        digest_contribution="dc",
    )
    s3 = DispatchTraceStep(
        step_index=3,
        kind=DispatchTraceKind.TRACE_FINALIZED,
        command_kind="x",
        mutation_kind=DispatchMutationKind.NONE,
        status=DispatchTraceStatus.NOT_APPLICABLE,
        route_label="r",
        before_facts=(),
        after_facts=(),
        derived_facts="",
        limitation_label="",
        digest_contribution="dc",
    )
    raised = False
    try:
        DispatchTrace(steps=(s1, s3), interaction_id="dispatch:00002")
    except ValueError:
        raised = True
    assert raised

    # 9. Builder + freeze deterministic.
    b1 = _seed_builder("dispatch:00003")
    b2 = _seed_builder("dispatch:00003")
    trace_1 = b1.freeze()
    trace_2 = b2.freeze()
    assert trace_1 == trace_2
    assert trace_1.steps == trace_2.steps
    assert format_dispatch_trace_table(trace_1).strip() != ""
    assert isinstance(format_dispatch_trace_table(trace_1), str)


@register("I-DTRACE-02", status="REQUIRED")
def check_dispatch_trace_report_determinism() -> None:
    """Audit build_dispatch_trace_report + dispatch_trace_digest_from_report."""

    b1 = _seed_builder("dispatch:00010")
    b2 = _seed_builder("dispatch:00010")
    trace_a = b1.freeze()
    trace_b = b2.freeze()
    report_a = build_dispatch_trace_report(trace_a)
    report_b = build_dispatch_trace_report(trace_b)
    assert isinstance(report_a, DispatchTraceReport)
    assert report_a.trace_digest_hex16 == report_b.trace_digest_hex16
    assert len(report_a.trace_digest_hex16) == 16
    assert int(report_a.trace_digest_hex16, 16) >= 0  # valid hex
    assert report_a.summary_line.startswith("dispatch-trace iid=")
    assert report_a.command_kind == "stream_append"
    assert report_a.mutation_kind is DispatchMutationKind.STREAM_APPEND
    assert report_a.overall_status is DispatchTraceStatus.PASS
    assert report_a.route_path == "stream-append"

    # Distinct traces produce distinct digests.
    b_other = new_dispatch_trace_builder("dispatch:00011")
    b_other.add(
        DispatchTraceKind.COMMAND_RECEIVED,
        command_kind="noop",
        route_label="noop-early-return",
        digest_contribution="cmd:noop",
    )
    b_other.add(
        DispatchTraceKind.NOOP_RECORDED,
        command_kind="noop",
        mutation_kind=DispatchMutationKind.NONE,
        route_label="noop-early-return",
        digest_contribution="noop",
    )
    b_other.add(
        DispatchTraceKind.TRACE_FINALIZED,
        command_kind="noop",
        route_label="noop-early-return",
        digest_contribution="trace-finalized",
    )
    other_report = build_dispatch_trace_report(b_other.freeze())
    assert other_report.trace_digest_hex16 != report_a.trace_digest_hex16
    assert other_report.command_kind == "noop"
    assert other_report.mutation_kind is DispatchMutationKind.NONE

    # digest_from_report mirrors the report's identity bits.
    digest_rec = dispatch_trace_digest_from_report(report_a)
    assert isinstance(digest_rec, DispatchTraceDigest)
    assert digest_rec.digest_hex16 == report_a.trace_digest_hex16
    assert digest_rec.command_kind == report_a.command_kind
    assert digest_rec.mutation_kind is report_a.mutation_kind
    assert digest_rec.route_path == report_a.route_path

    # Overall-status aggregation: a single WARN step yields WARN overall.
    b_warn = new_dispatch_trace_builder("dispatch:warn")
    b_warn.add(
        DispatchTraceKind.COMMAND_RECEIVED,
        command_kind="x",
        route_label="r",
        digest_contribution="cmd:x",
    )
    b_warn.add(
        DispatchTraceKind.MUTATION_CLASSIFIED,
        command_kind="x",
        mutation_kind=DispatchMutationKind.UI_ONLY,
        status=DispatchTraceStatus.WARN,
        route_label="r",
        digest_contribution="mut:warn",
    )
    b_warn.add(
        DispatchTraceKind.TRACE_FINALIZED,
        command_kind="x",
        route_label="r",
        digest_contribution="trace-finalized",
    )
    warn_report = build_dispatch_trace_report(b_warn.freeze())
    assert warn_report.overall_status is DispatchTraceStatus.WARN
