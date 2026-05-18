# PHASE3_23_FINDINGS.md — Phase 3.23 dispatch tracer findings

> Findings, deferred follow-ups, and risk triage for Phase 3.23. Each
> finding either resolves a Phase 3.22 / 3.22b weakness, names a new
> bounded constraint surfaced during the wiring, or queues work for a
> later campaign. No finding makes any cognitive claim.

## F1 — Phase 3.22 W4 (dispatch trace deferral): RESOLVED

Phase 3.22b satisfied W4 only via the reasoning trace's
`OBSERVE_INPUT` step recording the dispatch-path label. Phase 3.23
upgrades this to a first-class **dispatch trace substrate**:

- New module `brain/development/dispatch_tracer.py` (pure, bounded,
  deterministic).
- New `OperatorSession.latest_dispatch_trace` field stores a bounded
  `DispatchTraceReport` after every dispatch.
- `AgentLoopResult` surfaces the report on every interaction.
- The reasoning trace gains `CHECK_DISPATCH_TRACE`; the learning
  evidence ledger gains `DISPATCH_TRACE_RECORDED`.

W4 is closed.

## F2 — Phase 3.21 W3 (A3.04 NOT_APPLICABLE-overall): unchanged WARN

The A3.04 case (NOT_APPLICABLE overall-status not publicly reachable)
carries over as a documented WARN. Phase 3.23 does not refine the
coherence aggregation rule; that would belong to a follow-up
("Phase 3.24 coherence aggregation refinement" or equivalent).

## F3 — Synthetic no-dispatch traces share digests per route

The REFUSAL / FAIL-oversize / WARN-empty / REPL-bridge paths bypass
`OperatorSession.dispatch` and the agent loop synthesizes a bounded
`DispatchTraceReport` instead. By design the synthesis depends only
on the route label and not on the operator-text payload, so all
REFUSAL probes share the same digest, all REPL-bridge calls share
the same digest, etc.

**Implication.** The synthetic digest is a property of the route
label, not the operator text. Per-call provenance must be read from
the *reasoning trace* (which embeds the input id) and the *learning
evidence record* (which carries the per-call interaction id), not
from the dispatch trace digest alone.

This is intentional and bounded; no change required. Documenting it
here so future audits do not mistake it for a determinism failure.

## F4 — Dispatch trace interaction_id collision possible across NOOPs

Two consecutive `NOOP` dispatches on a session in the same kernel
state produce identical `interaction_id` strings because the
interaction id is derived from bounded session counters and the
command kind. Two consecutive NOOPs do not advance any counter, so
both traces share an id.

**Implication.** The dispatch trace digest of two consecutive NOOPs
on equal sessions is identical. This is correct: the trace describes
the route + state delta, and two consecutive NOOPs on equal sessions
have identical routes and zero state deltas.

No change required. If a future caller wants per-call separation, a
monotonically-incrementing `_dispatch_serial` field can be added via
a future catalog patch (the precedent is `stream_chunk_serial`).
Filed as a deferred enhancement (not blocking).

## F5 — `STREAM_WINDOW_INTERNAL` classification trigger

The mutation_kind refinement from `STREAM_APPEND` to
`STREAM_WINDOW_INTERNAL` triggers whenever `processing_window_size > 0`,
because the Phase 3.18 rehearsal window always appends additional
internal chunks regardless of `feedback_mode`. The campaign synthesis
draft said "window > 0 AND feedback_mode != OFF"; the spec doc and
catalog row I-DTRACE-05 were updated to reflect actual semantics.

## F6 — Existing fixture audits had to widen

Six existing Phase 3.22 / 3.22b / 3.10b / 3.10c / 3.13 fixtures were
extended to recognize the new `latest_dispatch_trace` slot, the new
`AgentLoopResult` field, or the extended `ReasoningStepKind` /
`LearningEvidenceKind` membership:

- `brain/ui/fixtures/persistence_observe_resource_audit.py`
  (+`_PHASE_3_23_SESSION_ATTRS`).
- `brain/ui/fixtures/persistence_ops_resource_audit.py`
  (+`_PHASE_3_23_SESSION_ATTRS`).
- `brain/development/fixtures/growth_ledger_session_integration.py`
  (I-GROW-14 audit extended).
- `brain/ui/fixtures/agent_loop_static_audit.py`
  (AgentLoopResult slot list extended).
- `brain/ui/fixtures/learning_proof_report.py`
  (counts_sum extended).
- `brain/ui/fixtures/learning_reasoning_static_audit.py`
  (closed enum + slot expectations extended).
- `brain/ui/fixtures/agent_benchmark_runner_green.py`
  (+`BenchmarkAxis.DISPATCH_TRACE` in expected axes).
- `brain/ui/fixtures/agent_benchmark_static_audit.py`
  (`_EXPECTED_AXIS_VALUES` extended).

None of these widenings introduces a new risk surface. They document
the v0.32 catalog patch.

## F7 — Trace report digest budget

`DispatchTraceReport.trace_digest_hex16` is a 16-character hex prefix
of `sha256(serialized_steps)`. The collision probability across the
bounded number of distinct traces a single session can produce in
its lifetime (bounded by `DISPATCH_TRACE_MAX_STEPS == 16`,
`DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES == 12`,
`DISPATCH_TRACE_FACT_VALUE_MAX_LEN == 64`) is negligible. Empirical
evidence: across the 65-case `run_full_battery()` run, no two
dispatch traces share a digest unless they share the route and
state delta.

## Deferred follow-ups (queued for a later campaign)

- **Phase 3.24 worldlet feedback bridge.** Deferred from the Phase
  3.19 / 3.20 architecture review. Bounded extension following the
  `FeedbackMode` precedent.
- **Phase 3.25 coherence aggregation refinement.** Address the
  A3.04 NOT_APPLICABLE-overall blocker once a public way to drive
  every check to `NOT_APPLICABLE` lands.
- **Phase 3.26 dispatch trace ring buffer.** Make the per-session
  `latest_dispatch_trace` a bounded FIFO history (e.g. last 16
  traces) so cross-dispatch audits can run from a single session
  reference. Out of scope for Phase 3.23.
- **Phase 3.27 per-dispatch interaction_id serial.** Promote the
  current bounded-counter synthesis to a session-local
  `_dispatch_serial` field so two consecutive NOOPs distinguish.
