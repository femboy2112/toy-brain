# PHASE3_23_TRACE_PROOF_REPORT.md — Dispatch trace proof tables

> Compact proof tables for eight representative dispatches. Each row
> documents the structural audit artifact produced by the Phase 3.23
> dispatch tracer. No row makes any cognitive claim. The proof is a
> property of the substrate: every digest is reproducible from the
> public OperatorSession.dispatch / agent loop entry points.

## 1. Definition

A **dispatch trace** is an explicit, bounded, deterministic,
externally inspectable audit record of the public route taken through
`OperatorSession.dispatch` and the structural effects observed. The
trace is NOT a cognitive claim. The digest is a structural hash, not
a meaning hash.

## 2. What counts as proof

| Property                 | Check                                                                  |
|--------------------------|------------------------------------------------------------------------|
| Determinism              | Two fresh sessions advanced by the same commands yield equal digests   |
| Bounded                  | Every field is below the per-field cap in PHASE3_23_DISPATCH_TRACE_SPEC|
| Non-claim-clean          | Every produced string passes `_FORBIDDEN_NON_CLAIM_TERMS` audit        |
| Externally inspectable   | `session.latest_dispatch_trace` and `result.latest_dispatch_trace`     |
| Route-classified         | `MUTATION_CLASSIFIED` step records a closed `DispatchMutationKind`     |

## 3. What does NOT count as proof

The dispatch trace MAY NOT be cited as evidence of cognition,
sentience, awareness, intent, will, agency, understanding, or any
other subjective property. Determinism of the trace is a property of
the substrate; it does NOT imply the substrate has any cognitive
property.

## 4. Proof tables

The case rows below reproduce on `campaign/phase3-23-dispatch-tracer`
at commit `phase3.23 step7` (see PHASE3_23_BEHAVIOR_REPORT.md for the
canonical gate / benchmark summary).

### Row 1 — STREAM_APPEND with processing window OFF

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-01                                                 |
| command                     | `STREAM_APPEND` (text="alpha line one")                  |
| pre-state                   | active_view=state, stream_history_len=0, pattern_entry_count=0, processing_window_size=0, feedback_mode=off, tick_counter=0 |
| dispatch route              | stream-append                                            |
| mutation kind               | `STREAM_APPEND`                                          |
| post-state                  | active_view=stream_summary, stream_history_len=1, pattern_entry_count=1, growth_event_total=2 |
| reasoning trace             | OBSERVE_INPUT -> CLASSIFY_REFUSAL -> DERIVE_PATTERN -> LOOKUP_PRIOR_STRUCTURE -> COMPARE_STRUCTURE -> CHECK_COHERENCE -> CHECK_REPL -> SELECT_REPLY_DISPOSITION -> CHECK_DISPATCH_TRACE -> EMIT_REPLY |
| learning evidence           | `OBSERVED` -> `DISPATCH_TRACE_RECORDED` (cites digest)   |
| reply excerpt               | five-section OK reply                                    |
| dispatch trace digest       | `157ebd9f1fc740c1`                                       |
| verdict                     | PASS                                                     |

### Row 2 — STREAM_APPEND with PATTERN_AND_COHERENCE

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-02                                                 |
| command                     | `STREAM_APPEND` (text="alpha line two")                  |
| pre-state                   | processing_window_size=2, feedback_mode=pattern_and_coherence |
| dispatch route              | stream-append                                            |
| mutation kind               | `STREAM_WINDOW_INTERNAL`                                 |
| post-state                  | stream_history_len=7 (seed + 2 rehearsals + 2 pledger summaries + 2 cohmon summaries) |
| reasoning trace             | full sequence including CHECK_DISPATCH_TRACE             |
| learning evidence           | `OBSERVED` -> `DISPATCH_TRACE_RECORDED`                  |
| dispatch trace digest       | `ac51977543d73b50`                                       |
| verdict                     | PASS                                                     |

### Row 3 — Renamed-transfer agent reply

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-03                                                 |
| operator input              | `cat dog cat dog` (after `red blue red blue`)            |
| dispatch route              | stream-append                                            |
| mutation kind               | `STREAM_APPEND`                                          |
| reasoning trace             | full sequence; CHECK_DISPATCH_TRACE cites digest         |
| learning evidence           | `OBSERVED` -> `ABSTRACT_PATTERN_REUSED` -> `TRANSFER_RECOGNIZED` -> `DISPATCH_TRACE_RECORDED` |
| reply disposition           | OK                                                       |
| dispatch trace digest       | `01c579fb54050712`                                       |
| verdict                     | PASS                                                     |

### Row 4 — REPL valid-effective reply

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-04                                                 |
| operator input              | `EMIT ALPHA`                                             |
| dispatch route              | repl-bridge                                              |
| mutation kind               | `NONE` (no `OperatorSession.dispatch` call; synthetic)   |
| reasoning trace             | full sequence (REPL path); CHECK_DISPATCH_TRACE present  |
| learning evidence           | (none specific to REPL emit alpha) -> `DISPATCH_TRACE_RECORDED` |
| dispatch trace digest       | `c9aa31dc485e4850`                                       |
| verdict                     | PASS                                                     |

### Row 5 — REPL near-miss reply

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-05                                                 |
| operator input              | `emit alpha`                                             |
| dispatch route              | repl-bridge                                              |
| mutation kind               | `NONE`                                                   |
| reasoning trace             | full sequence; CHECK_REPL records `parse=near-miss`      |
| learning evidence           | `DISPATCH_TRACE_RECORDED`                                |
| dispatch trace digest       | `c9aa31dc485e4850` (same synthetic route as valid path)  |
| verdict                     | PASS                                                     |

### Row 6 — Cognitive-claim refusal

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-06                                                 |
| operator input              | a probe synthesized from `_FORBIDDEN_NON_CLAIM_TERMS[0]` |
| dispatch route              | refusal-no-dispatch                                      |
| mutation kind               | `NONE` (no session dispatch)                             |
| pre/post chunk counts       | unchanged (0 == 0)                                       |
| reasoning trace             | OBSERVE_INPUT -> CLASSIFY_REFUSAL (matched) -> CHECK_LIMITATION -> CHECK_DISPATCH_TRACE -> EMIT_REPLY |
| learning evidence           | `LIMITATION_RECORDED` -> `DISPATCH_TRACE_RECORDED`       |
| reply disposition           | REFUSAL                                                  |
| dispatch trace digest       | `59a4d000e3ba23c3`                                       |
| verdict                     | PASS — refusal path records the route structurally without mutating the session |

### Row 7 — STEP_TICK missing-client error route

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-07                                                 |
| command                     | `STEP_TICK` (client=None)                                |
| pre/post tick_counter       | unchanged (0 == 0)                                       |
| dispatch route              | step-tick-via-public-tick                                |
| mutation kind               | `ERROR_ONLY`                                             |
| trace shape                 | includes `ERROR_RECORDED` step                           |
| overall_status              | FAIL                                                     |
| dispatch trace digest       | `bba939629d84cff7`                                       |
| verdict                     | PASS — error path records the route structurally; no kernel-side substrate mutates |

### Row 8 — NOOP route

| Field                       | Value                                                    |
|-----------------------------|----------------------------------------------------------|
| case_id                     | proof-08                                                 |
| command                     | `NOOP`                                                   |
| dispatch route              | noop-early-return                                        |
| mutation kind               | `NONE`                                                   |
| trace shape                 | COMMAND_RECEIVED -> ROUTE_SELECTED -> PRE_STATE_SNAPSHOT -> NOOP_RECORDED -> TRACE_FINALIZED (5 steps) |
| autosave / audit step       | both absent (the early-return path bypasses both)        |
| dispatch trace digest       | `768ead89acd215ab`                                       |
| verdict                     | PASS                                                     |

## 5. Aggregate proof

- Total benchmark cases: **65** (53 from Phase 3.22 / 3.22b + 12 new A10 cases).
- PASS: **64** · WARN: **1** (A3.04 — the documented Phase 3.21 W3 carry-over) · FAIL: **0**.
- `BATTERY_VERSION` = `phase3.23.v1`.
- `transcript_digest_hex16` = `8cc4a4ca1845c6a4` (deterministic across two `run_full_battery()` invocations).
- `real_model_calls` = 0 · `cache_writes` = 0 · `forbidden_term_hits` = 0 · `determinism_failures` = 0 · `invariant_failures` = 0.
- Canonical gates: 5 / 5 PASS.
- Catalog v0.32: 324 REQUIRED green · 96 STRUCTURAL green · 0 red rows.

## 6. Limitations

- The trace records *structural* effects only. It does NOT claim
  meaning, value, agency, intent, or experience.
- The synthetic no-dispatch report on the REFUSAL / FAIL / WARN-empty
  / REPL-bridge paths shares a single `digest_hex16` per route label
  (the bounded carrier text varies but the synthesis pattern is
  identical). This is intentional: those paths bypass
  `OperatorSession.dispatch`, so the dispatch trace digest is a
  property of the route label, not the per-call payload.
- The trace digest is computed from a serialized step record. Two
  identical sessions advanced by the same command sequence always
  produce the same digest.
- The trace cannot tell whether a session "remembers" anything; it
  only records bounded `before_facts` / `after_facts` deltas.

## 7. Reproduction

```bash
python3 -m brain.invariants run                # 0 red, 0 gate failures
python3 -m brain.development.agent_benchmark    # 65 cases, digest 8cc4a4ca1845c6a4
python3 -m tools.claude_helpers.gate_runner --json   # 5/5 PASS
python3 -m tools.catalog counts                  # 324 / 96 / 14 / 15 / 16
```
