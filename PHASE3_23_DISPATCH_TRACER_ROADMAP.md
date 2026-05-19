# PHASE3_23_DISPATCH_TRACER_ROADMAP.md

> Phase 3.23 stacks on the in-flight `campaign/phase3-22-agent-communication-loop`
> branch (Phase 3.22 + 3.22b, PR #27). It does NOT modify any merged surface and
> does NOT alter existing command semantics. It adds a bounded, deterministic,
> externally inspectable **dispatch trace** substrate through
> `OperatorSession.dispatch`, then threads the trace through the Phase 3.22b
> `AgentLoopResult` so the resulting reasoning trace and learning evidence can
> cite the dispatch trace digest.

## Goal

Make every `OperatorSession.dispatch` call carry a bounded, deterministic,
non-claim-clean `DispatchTrace`. The trace is a **structural audit artifact**:

```text
operator input
  -> command / dispatch route
  -> public substrate touched
  -> mutation or non-mutation outcome
  -> learning evidence update
  -> reasoning trace update
  -> reply emitted
```

It is NOT a cognitive claim. It is NOT introspection, awareness, agency,
will, intent, or subjective experience. The closed
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS` audit applies
to every produced trace string. Cognitive-claim probes still trigger the
existing REFUSAL path and the dispatch trace records the structural route
without mutating session state.

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective experience,
  human-like understanding, real agency, will, desire, belief, intent,
  introspection, or metacognition.
- No new aggregate scalar field (no "consciousness score", "sentience score",
  "awareness score", "I-ness score").
- Cognitive-claim refusal still wins. Asking ToyI whether it is conscious,
  sentient, aware, etc., yields a REFUSAL reply and the dispatch trace records
  that refusal route — never the cognitive claim.

## Branch

```text
campaign/phase3-23-dispatch-tracer
```

Base: `campaign/phase3-22-agent-communication-loop` (PR #27).
PR (likely #28): `phase3.23: dispatch tracer wiring`.
Do NOT merge until PR #27 / #26 / #25 have merged or been retargeted.

## Catalog patch

- v0.31 -> v0.32.
- Row family `I-DTRACE-01..12`.
- +11 REQUIRED rows (I-DTRACE-01..11).
- +1 STRUCTURAL row (I-DTRACE-12).
- NOT-EXERCISED / DEFERRED / OBSERVED unchanged.

Expected counts after patch:

```text
REQUIRED       324
STRUCTURAL      96
NOT-EXERCISED   14
DEFERRED        15
OBSERVED        16
```

## Module / file changes

```text
NEW   brain/development/dispatch_tracer.py
NEW   brain/ui/fixtures/dispatch_tracer_constructor.py
NEW   brain/ui/fixtures/dispatch_tracer_session_stream.py
NEW   brain/ui/fixtures/dispatch_tracer_processing_window.py
NEW   brain/ui/fixtures/dispatch_tracer_step_tick_error.py
NEW   brain/ui/fixtures/dispatch_tracer_noop.py
NEW   brain/ui/fixtures/dispatch_tracer_mutation_kinds.py
NEW   brain/ui/fixtures/dispatch_tracer_agent_loop_integration.py
NEW   brain/ui/fixtures/dispatch_tracer_reasoning_learning_integration.py
NEW   brain/ui/fixtures/dispatch_tracer_benchmark_axis.py
NEW   brain/ui/fixtures/dispatch_tracer_static_audit.py
EDIT  brain/ui/session.py              add latest_dispatch_trace + wire dispatch
EDIT  brain/development/agent_loop.py  surface latest_dispatch_trace on AgentLoopResult
EDIT  brain/development/reasoning_trace.py  add CHECK_DISPATCH_TRACE step kind
EDIT  brain/development/learning_evidence.py  add DISPATCH_TRACE_RECORDED kind
EDIT  brain/development/agent_benchmark.py    add A10 dispatch_trace axis (12 cases)
EDIT  brain/invariants.py             register the 10 new fixture modules
EDIT  brain/_catalog_ids.py           regen for new IDs (via tools.catalog)
EDIT  tools/catalog.py                EXPECTED_COUNTS bump
EDIT  INVARIANT_CATALOG.md            +I-DTRACE row family + banner update
EDIT  README.md                       catalog banner / history
EDIT  CURRENT_MISSION.md              Phase 3.23 mission record
EDIT  CURRENT_CAMPAIGN.md             Phase 3.23 campaign record
EDIT  PHASE3_HANDOFF_STATE.md         Phase 3.23 in-flight + complete
```

## Step ledger

```text
Step 1  Mission + design + roadmap docs                 commit phase3.23 step1
Step 2  Dispatch trace substrate (dispatch_tracer.py)   commit phase3.23 step2
Step 3  Session dispatch trace wiring (session.py)      commit phase3.23 step3
Step 4  Agent loop / reasoning / learning integration   commit phase3.23 step4
Step 5  Benchmark A10 dispatch_trace axis               commit phase3.23 step5
Step 6  Catalog + fixtures + EXPECTED_COUNTS bump       commit phase3.23 step6
Step 7  Trace proof + behavior + findings reports       commit phase3.23 step7
Step 8  Final audit + handoff + open PR #28             commit phase3.23 step8
```

Push after every successful step.

## Benchmark expectation

- 53 existing cases (Phase 3.22 + 3.22b) keep their statuses.
- A3.04 WARN remains (the documented Phase 3.21 W3 follow-up blocker;
  `NOT_APPLICABLE` overall is not publicly reachable).
- New A10 axis adds 12 PASS cases (A10.01..A10.12).
- Total cases: 65; 64 PASS + 1 WARN + 0 FAIL.
- `real_model_calls == 0`, `cache_writes == 0`, `forbidden_term_hits == 0`,
  `determinism_failures == 0`, `invariant_failures == 0`.
- The Phase 3.22 transcript digest changes only for the A10 lines; A1..A9
  per-axis digests are unchanged because the new substrate is additive on
  the session.

## Acceptance criteria

Phase 3.23 succeeds only when:

- `DispatchTrace` substrate exists with closed `DispatchTraceKind`,
  `DispatchMutationKind`, `DispatchTraceStatus` enums and bounded
  `DispatchTraceStep`, `DispatchTrace`, `DispatchTraceReport`,
  `DispatchTraceDigest` records.
- `OperatorSession.dispatch` stores the latest bounded
  `DispatchTraceReport` on `session.latest_dispatch_trace`, without changing
  `dispatch()`'s `None` return or any existing semantics.
- `AgentLoopResult` exposes the dispatch trace report.
- `ReasoningTrace` references the dispatch trace digest via a
  `CHECK_DISPATCH_TRACE` step.
- `LearningEvidenceRecord` (kind `DISPATCH_TRACE_RECORDED`) can cite the
  dispatch trace digest where relevant.
- Benchmark A10 is green; existing A1..A9 do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.32 banner.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5 PASS.
- No new `brain.llm` import, no `brain.tick.tick` call outside the existing
  `STEP_TICK` route, no host execution, no DB schema change, no curses.
- PR #28 is open with base `campaign/phase3-22-agent-communication-loop`;
  no PR is merged.
