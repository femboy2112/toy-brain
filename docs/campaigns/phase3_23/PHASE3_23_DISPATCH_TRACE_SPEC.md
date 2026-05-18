# PHASE3_23_DISPATCH_TRACE_SPEC.md — Trace schema + benchmark spec

> Bounded structural audit specification for Phase 3.23. Trace shape,
> digest discipline, A10 benchmark axis, and limitation table. No
> cognitive claim is made by this document.

## 1. Definition

**Dispatch trace** = an explicit, bounded, deterministic, externally
inspectable audit record of which public route was taken through
`OperatorSession.dispatch` and what structural effects occurred. It
is a *property of the runtime substrate*, not a claim about the
runtime's cognition.

## 2. What counts as proof

A dispatch trace is considered correct when:

1. Two fresh `OperatorSession` instances advanced by the same command
   sequence produce equal `DispatchTraceReport.trace_digest_hex16`
   per dispatch.
2. Distinct command kinds produce distinct `command_kind` summaries
   and distinct `route_path` strings.
3. The closed `DispatchMutationKind` membership matches the route
   table (section 5).
4. Every produced string is bounded, printable, and passes the
   `_FORBIDDEN_NON_CLAIM_TERMS` audit.
5. The trace makes the substrate observation reproducible from
   outside the call.

## 3. What does NOT count as proof

- The trace MAY NOT be cited as evidence of cognition, sentience,
  awareness, intent, will, agency, understanding, or any other
  subjective property.
- The trace MAY NOT be cited as evidence that the runtime "thinks",
  "decides", "knows", "believes", or "experiences".
- Determinism of the trace is a property of the substrate; it does
  NOT imply the substrate is conscious.

## 4. Trace schema

Per dispatch, the trace records up to `DISPATCH_TRACE_MAX_STEPS = 16`
steps. Canonical (non-error) order is:

```text
01  COMMAND_RECEIVED
02  ROUTE_SELECTED
03  PRE_STATE_SNAPSHOT
04  HANDLER_ENTERED
05  HANDLER_RETURNED
06  POST_STATE_SNAPSHOT
07  MUTATION_CLASSIFIED
08  AUTOSAVE_CHECKED      (omitted when autosave_config is None)
09  RESOURCE_AUDIT_CHECKED
10  TRACE_FINALIZED
```

`NOOP` short-circuits to:

```text
01  COMMAND_RECEIVED
02  NOOP_RECORDED
03  TRACE_FINALIZED
```

Error paths (validation rejection, missing client on `STEP_TICK`,
queue full, etc.):

```text
01  COMMAND_RECEIVED
02  ROUTE_SELECTED
03  PRE_STATE_SNAPSHOT
04  HANDLER_ENTERED
05  ERROR_RECORDED
06  POST_STATE_SNAPSHOT       (substrate fields unchanged)
07  MUTATION_CLASSIFIED       (mutation_kind == ERROR_ONLY)
08  RESOURCE_AUDIT_CHECKED
09  TRACE_FINALIZED
```

## 5. Route table (command -> mutation kind)

| OperatorCommand kind                  | route_label                  | mutation_kind            |
|---------------------------------------|------------------------------|--------------------------|
| INSPECT_STATE / INSPECT_TICK / ...    | inspect-view-change          | VIEW_CHANGE              |
| QUEUE_PERCEPT                         | queue-percept                | QUEUE_MUTATION           |
| STEP_TICK (with client + queue)       | step-tick-via-public-tick    | STEP_TICK                |
| STEP_TICK (missing client / no queue) | step-tick-error              | ERROR_ONLY               |
| CLEAR_STATUS                          | clear-status                 | UI_ONLY                  |
| HELP                                  | help-view                    | VIEW_CHANGE              |
| QUIT                                  | quit-flag                    | QUIT_FLAG                |
| NOOP                                  | noop-early-return            | NONE                     |
| STREAM_APPEND (window OFF)            | stream-append                | STREAM_APPEND            |
| STREAM_APPEND (window ON, feedback)   | stream-append-internal       | STREAM_WINDOW_INTERNAL   |
| STREAM_PROMOTE                        | stream-promote               | STREAM_PROMOTE           |
| SAVE_SESSION / LOAD_SESSION           | session-persistence          | SESSION_PERSISTENCE      |
| SESSION_STATUS                        | session-status               | UI_ONLY                  |
| DB_STATUS / DB_VERIFY / DB_SUMMARY    | db-observe                   | DB_OBSERVE               |
| PROFILE_SUMMARY / STREAM_DB_SUMMARY   | db-observe                   | DB_OBSERVE               |
| DB_DIFF                               | db-observe                   | DB_OBSERVE               |
| DB_BACKUP                             | db-backup                    | DB_BACKUP                |
| AUTOSAVE_STATUS                       | autosave-status              | UI_ONLY                  |
| AUTOSAVE_ENABLE / AUTOSAVE_DISABLE    | autosave-config              | AUTOSAVE                 |

The `STREAM_APPEND` route splits at the post-handler step: when
`processing_window_size > 0` and `feedback_mode != OFF`, the
`MUTATION_CLASSIFIED` step records `STREAM_WINDOW_INTERNAL` instead
of `STREAM_APPEND`. This mirrors the existing rehearsal-window
implementation in `_dispatch_stream_append` / `_run_processing_window`.

## 6. Required trace facts

`PRE_STATE_SNAPSHOT.before_facts` records (bounded):

- `active_view`
- `event_queue_size`
- `stream_history_len`
- `stream_candidate_count`
- `pattern_entry_count`
- `growth_event_total`
- `processing_window_size`
- `feedback_mode`
- `tick_counter`
- `status_message_present` (`"0"` or `"1"`)
- `error_message_present` (`"0"` or `"1"`)

`POST_STATE_SNAPSHOT.after_facts` records the same key set after
the handler has run.

`HANDLER_ENTERED.derived_facts` records the handler method name
(e.g. `"_dispatch_stream_append"`).

`HANDLER_RETURNED.derived_facts` records the bounded `mutation_outcome`
classification (`"mutated"` / `"failed"` / `"read-only"`).

`MUTATION_CLASSIFIED.route_label` = the route label.
`MUTATION_CLASSIFIED.derived_facts` = `"mutation_kind=<value>"`.

`AUTOSAVE_CHECKED.derived_facts` records the bounded autosave outcome
(`"considered:no-config"` / `"considered:enabled-not-triggered"` /
`"considered:fired-ok"` / `"considered:fired-failed"`).

`RESOURCE_AUDIT_CHECKED.derived_facts` records `"audit:ok"` (the
audit raises on failure, so a recorded step always means PASS).

`TRACE_FINALIZED.derived_facts` records the trace digest
contribution counters used for the final hash (kept short).

## 7. Critical structural invariants

- The trace MUST be deterministic across two equal sessions.
- The trace MUST NOT contain raw long text (truncate over the per-field
  bound; never store unbounded strings).
- The trace MUST NOT contain any `_FORBIDDEN_NON_CLAIM_TERMS` term
  (case-insensitive) in any field.
- The trace MUST NOT call `brain.tick.tick`.
- The trace MUST NOT call any `brain.llm.*` symbol.
- The trace MUST NOT widen the `_ALLOWED_SESSION_ATTRS` surface beyond
  the one new `latest_dispatch_trace` slot.
- The trace MUST NOT change existing command semantics.

## 8. Benchmark A10 axis spec

`BenchmarkAxis.DISPATCH_TRACE = "dispatch_trace"` (twelve closed cases).

| Case   | Description                                                                     |
|--------|---------------------------------------------------------------------------------|
| A10.01 | `STREAM_APPEND` produces a non-empty dispatch trace                             |
| A10.02 | `STREAM_APPEND` trace records the route label and mutation kind                 |
| A10.03 | Processing window ON + `PATTERN_LEDGER` records `STREAM_WINDOW_INTERNAL`        |
| A10.04 | `PATTERN_AND_COHERENCE` feedback mode is recorded in `before_facts.feedback_mode`|
| A10.05 | Cognitive-claim refusal records dispatch route NONE without session mutation    |
| A10.06 | REPL valid-effective reply records the synthetic REPL dispatch route            |
| A10.07 | Renamed-transfer reply reasoning trace references the dispatch trace digest     |
| A10.08 | Missing-client `STEP_TICK` records `ERROR_ONLY` and no kernel mutation          |
| A10.09 | `NOOP` records the NOOP route and no mutation                                   |
| A10.10 | Dispatch trace digest is stable across two fresh-session runs (determinism)     |
| A10.11 | Dispatch trace module source has zero forbidden-term hits                       |
| A10.12 | Adding the A10 axis preserves prior benchmark axis digests (A1..A9 unchanged)   |

Every A10 case must be PASS. `real_model_calls == 0`,
`cache_writes == 0`, `forbidden_term_hits == 0`,
`determinism_failures == 0`, `invariant_failures == 0`.

## 9. Limitations (recorded openly)

- The trace records *structural* effects only. Higher-level
  observations (e.g. "this dispatch was important to the loop") are
  NOT made. The trace remains agnostic about meaning.
- The trace records the route after the fact. It does NOT plan, infer,
  or anticipate.
- The trace cannot tell whether a session "remembers" anything; it
  only records bounded `before_facts` / `after_facts` deltas.
- The trace's digest is a structural hash, not a meaning hash.
- The trace cannot be used to claim agency, will, intent, or any
  cognitive property.

## 10. Sample row

For `STREAM_APPEND` with `text="alpha line one"`, `processing_window_size=0`,
`feedback_mode=OFF`:

```text
01  COMMAND_RECEIVED        kind=stream_append      status=NOT_APPLICABLE   mut=NONE
02  ROUTE_SELECTED          route=stream-append     status=NOT_APPLICABLE   mut=NONE
03  PRE_STATE_SNAPSHOT      active_view=state, stream_history_len=0, ...
04  HANDLER_ENTERED         handler=_dispatch_stream_append
05  HANDLER_RETURNED        outcome=mutated
06  POST_STATE_SNAPSHOT     active_view=stream_summary, stream_history_len=1, ...
07  MUTATION_CLASSIFIED     mut=STREAM_APPEND       status=PASS
08  AUTOSAVE_CHECKED        outcome=considered:no-config
09  RESOURCE_AUDIT_CHECKED  audit:ok
10  TRACE_FINALIZED         digest_contribution=...
```

`route_path = "stream-append"`. The digest is a deterministic
16-character hex prefix of `sha256(...)`.

## 11. Next campaign recommendation

Phase 3.24 could extend the dispatch tracer into a **bounded
per-session dispatch history** (FIFO bounded ring buffer of the last
`K` `DispatchTraceReport` records), enabling cross-dispatch audits
without touching the kernel. Out of scope for Phase 3.23.
