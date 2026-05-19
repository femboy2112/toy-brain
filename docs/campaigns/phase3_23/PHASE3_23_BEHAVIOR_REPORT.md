# PHASE3_23_BEHAVIOR_REPORT.md — Behavior under the Phase 3.23 dispatch tracer

> Behavioral report on the Phase 3.23 dispatch tracer. Documents the
> A10 benchmark axis outcomes, the carried-forward A1..A9 statuses,
> the canonical gate verdicts, and the dispatch-trace properties
> observed on the deterministic test substrate. No row makes any
> cognitive claim.

## 1. Headline numbers

| Metric                          | Value                                |
|---------------------------------|--------------------------------------|
| `BATTERY_VERSION`               | `phase3.23.v1`                       |
| Total benchmark cases           | 65                                   |
| PASS                            | 64                                   |
| WARN                            | 1 (A3.04 — Phase 3.21 W3 carry-over) |
| FAIL                            | 0                                    |
| `real_model_calls`              | 0                                    |
| `cache_writes`                  | 0                                    |
| `forbidden_term_hits`           | 0                                    |
| `determinism_failures`          | 0                                    |
| `invariant_failures`            | 0                                    |
| `transcript_digest_hex16`       | `8cc4a4ca1845c6a4`                   |
| Catalog version                 | v0.32 (REQUIRED 324, STRUCTURAL 96, NOT-EXERCISED 14, DEFERRED 15, OBSERVED 16) |
| Canonical gates                 | 5 / 5 PASS                           |
| `brain.invariants run`          | 428 rows checked, 0 red              |

## 2. Per-axis status

| Axis                          | Cases | Status |
|-------------------------------|-------|--------|
| A1 pattern_recognition        | 9     | PASS   |
| A2 cross_input_structural     | 5     | PASS   |
| A3 coherence_variation        | 4     | WARN (A3.04 documented blocker) |
| A4 repl_coherence             | 5     | PASS   |
| A5 communication              | 9     | PASS   |
| A6 session_continuity         | 3     | PASS   |
| A7 blind_transcript           | 4     | PASS   |
| A8 learning_evidence          | 7     | PASS   |
| A9 reasoning_trace            | 7     | PASS   |
| A10 dispatch_trace            | 12    | **PASS** |

A1..A9 case ids and case statuses are unchanged from Phase 3.22b
(53 cases). The per-axis cases produce slightly different transcript
text in A8 / A9 because the reasoning trace and learning proof
summary lines now embed the Phase 3.23 `dtr=<n>` /
`dispatch_trace=<n>` counts; every case still PASSes its closed
criterion.

## 3. A10 axis case roll-up

| Case   | Result | Notes                                                                 |
|--------|--------|-----------------------------------------------------------------------|
| A10.01 | PASS   | STREAM_APPEND produces a non-empty dispatch trace                     |
| A10.02 | PASS   | STREAM_APPEND records `cmd=stream_append`, `mut=stream_append`        |
| A10.03 | PASS   | window=2 + PATTERN_LEDGER -> `STREAM_WINDOW_INTERNAL`                 |
| A10.04 | PASS   | window=2 + PATTERN_AND_COHERENCE captured in pre_state                |
| A10.05 | PASS   | cognitive-claim refusal records `mut=none`; session untouched         |
| A10.06 | PASS   | `EMIT ALPHA` records synthetic `route=repl-bridge`, `mut=none`        |
| A10.07 | PASS   | renamed-transfer reasoning trace cites dispatch digest                |
| A10.08 | PASS   | STEP_TICK with `client=None` records `mut=error_only`; no kernel mutation |
| A10.09 | PASS   | NOOP records `route=noop-early-return`, `mut=none`, 5 steps           |
| A10.10 | PASS   | dispatch trace digest stable across two fresh-session runs            |
| A10.11 | PASS   | `dispatch_tracer.py` source forbidden-term audit returns no hits      |
| A10.12 | PASS   | A1..A9 case totals retained (axis is additive)                        |

## 4. Dispatch trace digest budget

The Phase 3.23 dispatch tracer is bounded:

| Bound                                       | Value |
|---------------------------------------------|-------|
| `DISPATCH_TRACE_MAX_STEPS`                  | 16    |
| `DISPATCH_TRACE_STEP_FIELD_MAX_LEN`         | 160   |
| `DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES`   | 12    |
| `DISPATCH_TRACE_FACT_KEY_MAX_LEN`           | 32    |
| `DISPATCH_TRACE_FACT_VALUE_MAX_LEN`         | 64    |
| `DISPATCH_TRACE_DIGEST_HEX_LEN`             | 16    |
| `DISPATCH_TRACE_INTERACTION_ID_MAX_LEN`     | 64    |
| `DISPATCH_TRACE_ROUTE_LABEL_MAX_LEN`        | 64    |
| `DISPATCH_TRACE_ROUTE_PATH_MAX_LEN`         | 240   |
| `DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN`     | 320   |

Every produced trace fits inside these caps; the per-field non-claim
audit rejects strings that contain any `_FORBIDDEN_NON_CLAIM_TERMS`
term, so the bounded-printable + non-claim-clean discipline is
enforced at construction time, not at audit time.

## 5. What changed and what did not

**Changed:**

- A new module `brain/development/dispatch_tracer.py`.
- One new `OperatorSession` field (`latest_dispatch_trace`) and a
  bounded inline trace builder inside `OperatorSession.dispatch`.
- `AgentLoopResult` exposes `latest_dispatch_trace`.
- `ReasoningStepKind` and `LearningEvidenceKind` each gain exactly
  one new closed value.
- `BATTERY_VERSION` bumped to `phase3.23.v1`; benchmark adds A10.
- Catalog v0.31 -> v0.32 (+11 REQUIRED, +1 STRUCTURAL).

**Unchanged:**

- `brain/tick.py`.
- `brain/llm/`, the parser, the prompt, the cache, the DB schema, the
  autosave trigger contract.
- `OperatorCommand`, `LOCAL_COMMAND_VERBS`, `ACTIVE_VIEWS`.
- The `None` return of `OperatorSession.dispatch`.
- The I-UI-10 self-audit.
- The OFFLINE default.
- The kernel-side invariance on failure (I-UI-06).

## 6. Determinism evidence

Two fresh `OperatorSession` instances advanced by the same command
sequence produce equal `latest_dispatch_trace.trace_digest_hex16`
after every dispatch. Two fresh `make_initial_agent_loop_state()` /
`run_agent_interaction_step(...)` sequences produce equal
`latest_dispatch_trace.trace_digest_hex16` per result. Two
`run_full_battery()` invocations produce equal `transcript_digest_hex16`.

## 7. Risk surface (no new risks introduced)

- No new aggregate scalar field.
- No new claim about cognition.
- No new LLM-touching surface.
- No new persistence surface.
- No new autosave trigger.
- No new operator verb.

## 8. Sample digest table

| Dispatch                                    | digest_hex16        | mutation kind        |
|---------------------------------------------|---------------------|----------------------|
| STREAM_APPEND (window OFF)                  | `157ebd9f1fc740c1`  | `stream_append`      |
| STREAM_APPEND (window=2 + PATTERN_AND_COH.) | `ac51977543d73b50`  | `stream_window_internal` |
| Renamed-transfer 2nd step                   | `01c579fb54050712`  | `stream_append`      |
| REPL valid-effective (synthetic)            | `c9aa31dc485e4850`  | `none`               |
| REPL near-miss (synthetic)                  | `c9aa31dc485e4850`  | `none`               |
| Cognitive-claim refusal (synthetic)         | `59a4d000e3ba23c3`  | `none`               |
| STEP_TICK missing client                    | `bba939629d84cff7`  | `error_only`         |
| NOOP                                        | `768ead89acd215ab`  | `none`               |
