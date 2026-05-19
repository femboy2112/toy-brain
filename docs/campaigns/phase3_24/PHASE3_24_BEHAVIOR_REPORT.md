# Phase 3.24 — Behavior Report

This document records the *operational behavior* changes that Phase 3.24
introduces to ToyI's deterministic runtime. Behavior here means
"observable structural-effect changes" only — not psychological or
phenomenal behavior.

## What changed

1. `FeedbackMode` is widened from four to six closed members:
   `OFF`, `PATTERN_LEDGER`, `COHERENCE`, `PATTERN_AND_COHERENCE`,
   `WORLDLET`, `PATTERN_COHERENCE_WORLDLET`.
2. `InternalEventSource` is widened from three to four members; the
   new member `WORLDLET_SUMMARY` is in `_V1_EMITTED_SOURCES`.
3. `build_worldlet_summary_text(...)` produces a bounded printable
   summary line (≤ 240 chars) over bounded primitives extracted from
   `OperatorSession.worldlet_history` (or the `"absent"` sentinel
   triple when `worldlet_history is None`).
4. `OperatorSession._run_worldlet_feedback_step` fires the summary
   chunk via the same internal `STREAM_APPEND` seam used today for
   `pledger_summary` / `cohmon_summary`.
5. `OperatorSession._run_processing_window` fires the worldlet
   summary after each rehearsal when `feedback_mode in {WORLDLET,
   PATTERN_COHERENCE_WORLDLET}`; the combined mode fires four chunks
   per rehearsal in the fixed order `rehearsal -> pledger_summary
   -> cohmon_summary -> worldlet_summary`.
6. The dispatch trace records `feedback_mode=worldlet` (or
   `pattern_coherence_worldlet`) in pre/post-state facts and a new
   `("worldlet_summary_chunks", "<int>")` derived fact in the same
   snapshots. The mutation classification stays
   `STREAM_WINDOW_INTERNAL`; no new `DispatchMutationKind` is added.
7. `ReasoningStepKind` adds one closed value
   `CHECK_WORLDLET_FEEDBACK`, inserted immediately before
   `CHECK_DISPATCH_TRACE` in every trace.
8. `LearningEvidenceKind` adds one closed value
   `WORLDLET_FEEDBACK_RECORDED`. The agent loop emits one such record
   per interaction when worldlet_summary chunks are present in the
   post-state stream.
9. `AgentObservationSummary` gains three bounded fields
   (`worldlet_feedback_present`, `worldlet_summary_count`,
   `feedback_mode_value`); `AgentReply`'s PATTERN_REPORT section
   body cites the bounded fact when present.
10. The benchmark battery gains one axis `A11 worldlet_feedback` with
    12 cases; full battery now reports 77 cases.

## What did NOT change

- `brain/tick.py` — unchanged.
- `brain/llm/**` — unchanged.
- Parser, prompt, DB schema, autosave policy, L1 / L2 cache, Pattern
  Ledger semantics, Coherence Monitor semantics, Growth Ledger
  semantics — unchanged.
- No new `OperatorCommand` member, no new `LOCAL_COMMAND_VERBS`
  entry, no new `ACTIVE_VIEWS` value, no new `GrowthEventType`, no
  new `GrowthEventSource`.
- No new aggregate scalar field (no "consciousness score", no "world
  score", no "awareness score", no "I-ness score").
- The closed `DispatchTraceKind` (12) and `DispatchMutationKind`
  (14) and `DispatchTraceStatus` (4) enums are unchanged.
- OFFLINE default — unchanged.
- Real model calls budget consumed: 0 / 20.

## Observable run-time effects

| feedback_mode | extra chunks per tick (in addition to rehearsal) | pattern ledger entries created |
|---|---|---|
| `OFF` | 0 | 1 (seed) |
| `PATTERN_LEDGER` | 1 | 2 (seed + pledger summary) |
| `COHERENCE` | 1 | 2 (seed + cohmon summary) |
| `PATTERN_AND_COHERENCE` | 2 | 3 (seed + pledger + cohmon) |
| `WORLDLET` | 1 | 2 (seed + worldlet summary) |
| `PATTERN_COHERENCE_WORLDLET` | 3 | 4 (seed + all three summaries) |

Chunk total per `STREAM_APPEND` with `processing_window_size = N`:

```text
chunks = 1 (operator) + N * (1 + alpha)
alpha = number of feedback paths enabled by feedback_mode
```

Bounded by `STREAM_HISTORY_MAX_CHUNKS = 256`; with `processing_window_size = 255`
and `PATTERN_COHERENCE_WORLDLET` (`alpha = 3`), the chunk count is
`1 + 255 * 4 = 1021` — over the bound; in practice the Pattern Ledger
saturates first and the chunk loop hits its own bound. The
deterministic OFFLINE benchmark exercises the bounded short-window
case (`N = 2`); the 1021 edge is exercised only by the
substrate-bound fixture coverage of `_run_processing_window`.

## Non-claim discipline

The new path adds **zero** new candidate cognitive-claim probes.
Refusal classifier behavior is bit-identical:

- a cognitive-claim probe triggers the existing REFUSAL path;
- the dispatch trace records `route_path = "refusal-no-dispatch"`,
  `mutation_kind = NONE`;
- no worldlet_summary chunks are emitted on the refusal path;
- the agent reply text contains `"worldlet_feedback=absent"` (because
  the post-state has zero worldlet_summary chunks).

The static-audit fixture `worldlet_feedback_static_audit.py` exhaustively
scans `processing_window.py` source, every member of `FeedbackMode`,
every member of `InternalEventSource`, the locked closed sets, the
helper output over a representative input set, and `MODULE_PRODUCED_STRINGS`
for any `_FORBIDDEN_NON_CLAIM_TERMS` term. The scan is green.

## Benchmark delta

```text
before Phase 3.24:   65 cases   64 PASS + 1 WARN + 0 FAIL  digest 8cc4a4ca1845c6a4
after Phase 3.24:    77 cases   76 PASS + 1 WARN + 0 FAIL  digest b91c4ece90c8706f
```

The single WARN (A3.04) is the Phase 3.21 W3 follow-up
`not_applicable` blocker, unchanged. The transcript digest changed
because the new `worldlet_summary_chunks` dispatch-fact re-bases every
dispatch trace's digest deterministically; A1..A10 logic is unchanged.

## Resource discipline

```text
real_model_calls:    0
cache_writes:        0
forbidden_term_hits: 0
determinism_failures: 0
invariant_failures:   0
```

The new helper uses no `hashlib`, no `time`, no `random`, no `os`,
no `pathlib`, no `subprocess`, no `socket`, no `urllib`, no `http`,
no `requests`. The new code does not import `brain.development.worldlet`
(the substrate is read via the existing `OperatorSession.worldlet_history`
field; the helper accepts bounded primitives extracted by the caller).
