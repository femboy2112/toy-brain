# PHASE3_23_DISPATCH_TRACER_SYNTHESIS.md — Phase 3.23 design synthesis

> This document captures the Phase 3.23 design locks. Implementation in
> `brain/development/dispatch_tracer.py`, `brain/ui/session.py`,
> `brain/development/agent_loop.py`,
> `brain/development/reasoning_trace.py`,
> `brain/development/learning_evidence.py`, and
> `brain/development/agent_benchmark.py` must satisfy every lock named below.

## 1. Why this campaign

Phase 3.22 added a closed deterministic agent communication loop.
Phase 3.22b extended it with learning evidence + a reasoning trace.
Both layers are observable from outside the call, but the **internal
routing** through `OperatorSession.dispatch` is still implicit. A
campaign auditor cannot today answer questions like:

- "Which dispatch route did the loop pick for this operator input?"
- "What kernel / stream / ledger fields changed as a result?"
- "Did this dispatch consult the LLM client, or stay deterministic?"

Phase 3.23 makes that routing structurally inspectable. The
**dispatch trace** is the missing audit artifact. It is bounded,
deterministic, externally inspectable, and ships with a digest the
reasoning trace and learning evidence can cite.

## 2. Non-claim discipline

"Dispatch trace" is an **explicit audit record of the public route**
taken through `OperatorSession.dispatch` and the **structural
effects** observed. It is NOT:

- subjective reasoning,
- introspection,
- self-awareness,
- agency,
- will, desire, belief, intent,
- metacognition,
- understanding,
- experience.

Every produced string passes the closed
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
case-insensitive substring audit. Cognitive-claim probes still produce
the REFUSAL reply and a dispatch trace that records the no-mutation
route — never the cognitive claim itself.

## 3. Substrate locks

### 3.1 Module

```text
brain/development/dispatch_tracer.py
```

Closed import set:

- `__future__`, `dataclasses`, `enum`, `hashlib`, `typing`
- `brain.development.coherence_monitor` (only `_FORBIDDEN_NON_CLAIM_TERMS`)

No `brain.llm.*`. No `brain.tick`. No curses. No subprocess / socket /
urllib / http / requests / tempfile / shutil / threading / asyncio /
atexit / signal / importlib / time / random / pathlib / math.

### 3.2 Closed enums

`DispatchTraceKind` (closed; `(str, Enum)`):

```text
COMMAND_RECEIVED
ROUTE_SELECTED
PRE_STATE_SNAPSHOT
HANDLER_ENTERED
HANDLER_RETURNED
POST_STATE_SNAPSHOT
MUTATION_CLASSIFIED
AUTOSAVE_CHECKED
RESOURCE_AUDIT_CHECKED
TRACE_FINALIZED
ERROR_RECORDED
NOOP_RECORDED
```

`DispatchMutationKind` (closed; `(str, Enum)`):

```text
NONE
UI_ONLY
STREAM_APPEND
STREAM_WINDOW_INTERNAL
STREAM_PROMOTE
QUEUE_MUTATION
STEP_TICK
SESSION_PERSISTENCE
AUTOSAVE
DB_OBSERVE
DB_BACKUP
VIEW_CHANGE
QUIT_FLAG
ERROR_ONLY
```

`DispatchTraceStatus` (closed; `(str, Enum)`):

```text
PASS
WARN
FAIL
NOT_APPLICABLE
```

Every enum is closed at definition time. New values require a catalog
patch.

### 3.3 Frozen / slotted records

`DispatchTraceStep` carries:

- `step_index: int` (1..`DISPATCH_TRACE_MAX_STEPS`)
- `kind: DispatchTraceKind`
- `command_kind: str` (bounded printable, source from `OperatorCommand.value`
  or `""` for the early `COMMAND_RECEIVED` row when not yet classified)
- `mutation_kind: DispatchMutationKind`
- `status: DispatchTraceStatus`
- `route_label: str` (bounded printable, short)
- `before_facts: tuple[tuple[str, str], ...]` (bounded)
- `after_facts: tuple[tuple[str, str], ...]` (bounded)
- `derived_facts: str` (bounded printable summary)
- `limitation_label: str` (bounded printable)
- `digest_contribution: str` (bounded; the serialized form fed to the
  trace digest)

`DispatchTrace` is a bounded tuple of `DispatchTraceStep` records plus
a bounded `interaction_id: str`.

`DispatchTraceReport` carries the trace plus per-kind counts, the
`trace_digest_hex16`, the `command_kind` summary, the `mutation_kind`
summary, the `route_path: str` (a `->`-joined bounded path label), and a
`summary_line: str` audited for forbidden non-claim terms.

`DispatchTraceDigest` is a tiny `(digest_hex16, command_kind,
mutation_kind, route_path)` record so callers can cite the trace
without serializing the whole report.

`DispatchTraceConfig` carries the trace bounds (kept tiny — defaults
hard-coded into the substrate).

### 3.4 Bounds

```text
DISPATCH_TRACE_MAX_STEPS                  = 16
DISPATCH_TRACE_STEP_FIELD_MAX_LEN         = 160
DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES   = 12
DISPATCH_TRACE_FACT_KEY_MAX_LEN           = 32
DISPATCH_TRACE_FACT_VALUE_MAX_LEN         = 64
DISPATCH_TRACE_DIGEST_HEX_LEN             = 16
DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN     = 320
DISPATCH_TRACE_INTERACTION_ID_MAX_LEN     = 64
DISPATCH_TRACE_ROUTE_LABEL_MAX_LEN        = 64
DISPATCH_TRACE_ROUTE_PATH_MAX_LEN         = 240
```

### 3.5 Digest rule

```text
payload = interaction_id + "\n" + "\n".join(_serialize_step(s) for s in steps)
digest_hex16 = sha256(payload).hexdigest()[:16]
```

Every digest serialization includes `step_index`, `kind.value`,
`command_kind`, `mutation_kind.value`, `status.value`,
`route_label`, and the canonical key=value listing of `before_facts`
and `after_facts`. `derived_facts` and `limitation_label` are also
included verbatim. Two identical sessions advanced by the same
operator inputs produce equal `dispatch_trace_digest_hex16` for each
interaction.

### 3.6 Builder helpers

The substrate exports:

- `new_dispatch_trace_builder(interaction_id)` returning a private
  `_DispatchTraceBuilder` with `add(...)` and `freeze()` operations,
  mirroring the Phase 3.22b reasoning trace builder.
- `build_dispatch_trace_report(trace)` deterministically rendering the
  per-kind counts, digest, and summary line.
- `format_dispatch_trace_table(trace)` returning a bounded printable
  table projection (one row per step).
- `dispatch_trace_digest_from_report(report)` returning a
  `DispatchTraceDigest`.

## 4. Wiring lock — `OperatorSession.dispatch`

`OperatorSession` gains exactly one new attribute:

```python
latest_dispatch_trace: Optional[DispatchTraceReport] = None
```

added to:

- the `@dataclass(slots=True)` field list,
- `_ALLOWED_SESSION_ATTRS`,
- `__post_init__` validation (None or a `DispatchTraceReport`).

The new field is the precedent precedent set by `last_autosave_status`
(single-slot post-action record). The `_assert_no_unsafe_resources`
check is preserved as-is; `DispatchTraceReport` is a frozen / slotted
record without a `read`/`write` pair, `fileno`, `eval_consistency`,
`send_signal`, or `communicate` attribute.

`dispatch(command, *, client=None)` is extended to build a bounded
trace inline:

1. Open a builder with `interaction_id = f"dispatch:{n:05d}"` where
   `n` is derived from the existing tick / dispatch counter via a
   private session-local serial that increments deterministically.
2. Record `COMMAND_RECEIVED` step with the command's kind value.
3. Record `ROUTE_SELECTED` step naming the route label.
4. Record `PRE_STATE_SNAPSHOT` step with bounded before-facts.
5. Record `HANDLER_ENTERED` step.
6. Execute the existing handler exactly as today.
7. Record `HANDLER_RETURNED` step with the existing
   `mutation_outcome` translated to `DispatchTraceStatus`.
8. Record `POST_STATE_SNAPSHOT` step with bounded after-facts.
9. Record `MUTATION_CLASSIFIED` step mapping the route to its closed
   `DispatchMutationKind`.
10. Record `AUTOSAVE_CHECKED` step iff the autosave hook ran
    (`autosave_config is not None` and route in the trigger set).
11. Record `RESOURCE_AUDIT_CHECKED` step (always after the call).
12. Record `TRACE_FINALIZED` step.
13. Freeze the trace and build the report; assign to
    `self.latest_dispatch_trace`.

The `NOOP` early-return path is preserved: NOOP records exactly two
steps (`COMMAND_RECEIVED`, `NOOP_RECORDED`) plus `TRACE_FINALIZED`, with
`mutation_kind == NONE`, before returning. `_assert_no_unsafe_resources`
still runs at the end of every non-NOOP dispatch.

Error paths (validation rejections, missing client on `STEP_TICK`,
queue full, etc.) record an `ERROR_RECORDED` step with
`mutation_kind == ERROR_ONLY` and `status == FAIL`, then
`POST_STATE_SNAPSHOT` confirming substrate-side fields are unchanged,
then `TRACE_FINALIZED`. Existing semantics (kernel state untouched on
failure) are not modified.

## 5. Wiring lock — `AgentLoopResult`

`AgentLoopResult` gains:

```python
latest_dispatch_trace: Optional[DispatchTraceReport] = None
```

`run_agent_interaction_step` reads `state.session.latest_dispatch_trace`
after the dispatch is complete and copies the reference onto the result.
For the no-dispatch paths (REFUSAL / FAIL / WARN-empty), the loop builds
a **synthetic** dispatch-trace report that records the early-exit route
without touching the session. The synthetic report sets
`mutation_kind == NONE` and `status == NOT_APPLICABLE`; it is bounded
and printable like every other report.

## 6. Wiring lock — `ReasoningTrace`

`ReasoningStepKind` gains exactly one new closed member:

```text
CHECK_DISPATCH_TRACE = "check_dispatch_trace"
```

`run_agent_interaction_step` appends a `CHECK_DISPATCH_TRACE` step to
the reasoning trace immediately before `EMIT_REPLY`, recording:

- `input_facts="dispatch_digest=<hex16>"` (always present)
- `derived_facts="route_path=<...>"`
- `next_action="cite-in-emit-reply"`

Two fresh sessions advanced by the same operator sequence produce
equal reasoning-trace digests. Distinct dispatch paths produce
distinct reasoning-trace digests.

## 7. Wiring lock — `LearningEvidenceTrace`

`LearningEvidenceKind` gains exactly one new closed member:

```text
DISPATCH_TRACE_RECORDED = "dispatch_trace_recorded"
```

When a structural learning evidence record would be emitted, the agent
loop appends a `DISPATCH_TRACE_RECORDED` evidence record that cites
the dispatch trace digest in its `post_facts`. The new record uses an
empty `abstract_pattern_digest` and empty `pattern_id` (the dispatch
trace digest goes into `post_facts` and the summary line). This
preserves the FIFO bounded ledger behavior.

## 8. Benchmark A10 axis

`brain/development/agent_benchmark.py` gains:

```text
BenchmarkAxis.DISPATCH_TRACE = "dispatch_trace"
```

with twelve closed cases A10.01..A10.12 as named in
`PHASE3_23_DISPATCH_TRACE_SPEC.md`. Existing axes
A1..A9 keep their case ids, statuses, and per-axis digests.

`run_full_battery()` is updated to include A10. The transcript
digest changes because of the appended A10 lines; per-axis digests
for A1..A9 are unchanged.

## 9. Catalog patch

New row family `I-DTRACE-01..12`:

- I-DTRACE-01..11: REQUIRED.
- I-DTRACE-12: STRUCTURAL (static audit).

EXPECTED_COUNTS bump:

```text
REQUIRED      313 -> 324
STRUCTURAL     95 ->  96
```

Other counts unchanged. Catalog version becomes v0.32.

## 10. Out of scope

- No new `OperatorCommand` member.
- No new `LOCAL_COMMAND_VERBS` entry.
- No new `ACTIVE_VIEWS` value.
- No new `GrowthEventType` / `GrowthEventSource`.
- No new persistence schema column.
- No new autosave trigger.
- No host execution. No subprocess. No socket. No network.
- No `brain.llm` import. No `brain.tick.tick` call outside the existing
  approved `STEP_TICK` route.
- No filesystem writes from deterministic runtime modules.
- No `OFFLINE` default change.
- No new aggregate scalar field. No "consciousness score", "sentience
  score", "awareness score", "I-ness score".
- No SelfModel implementation.
