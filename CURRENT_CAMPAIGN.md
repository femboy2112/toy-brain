# CURRENT_CAMPAIGN.md — Phase 3.23 Dispatch Tracer Wiring

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.23 stacks on the completed Phase 3.22 + Phase 3.22b work
(`campaign/phase3-22-agent-communication-loop`, PR #27 open). Phase
3.23 asks one bounded operational question:

```text
Can every public OperatorSession.dispatch call carry a bounded,
deterministic, externally inspectable dispatch trace that records the
command kind, route label, pre/post substrate facts, mutation
classification, autosave consideration, and resource audit outcome --
without changing any existing command semantics, without touching the
kernel, the LLM seam, the parser, the cache, the DB schema, or the
autosave policy, and without claiming consciousness, sentience, agency,
or understanding?
```

This is a **research / integration / behavioral-benchmark** campaign.
It is **not** a proof of consciousness, sentience, subjective
experience, agency, semantic understanding, truth-adjudication, intent,
will, desire, introspection, metacognition, or psychological development.

Phase 3.23 does **not** implement SelfModel; does **not** add any new
`OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS`
value, `GrowthEventType`, `GrowthEventSource`, persistence schema column,
or autosave trigger; does **not** change L1 / L2 / parser / prompt / tick
/ persistence / autosave / DB schema semantics. The runtime touches are
limited to:

- **One new closed module** `brain/development/dispatch_tracer.py`
  (pure / deterministic / bounded). Closed import set: `__future__`,
  `dataclasses`, `enum`, `hashlib`, `typing`,
  `brain.development.coherence_monitor` (only
  `_FORBIDDEN_NON_CLAIM_TERMS` for the non-claim audit). No
  `brain.llm.*`, no `brain.tick`, no curses, no I/O, no host execution.
- **One new field** on `OperatorSession`:
  `latest_dispatch_trace: Optional[DispatchTraceReport] = None`.
  Added to `_ALLOWED_SESSION_ATTRS`, validated in `__post_init__`. The
  single-slot post-action precedent is `last_autosave_status`.
- **`OperatorSession.dispatch` wiring**: builds a bounded
  `DispatchTrace` inline and assigns the report to
  `self.latest_dispatch_trace`. Existing semantics, the `None` return,
  and the post-dispatch autosave + resource audit are preserved.
- **`AgentLoopResult` extension**: new optional field
  `latest_dispatch_trace: Optional[DispatchTraceReport]`.
- **`ReasoningStepKind` extension**: one new closed value
  `CHECK_DISPATCH_TRACE`.
- **`LearningEvidenceKind` extension**: one new closed value
  `DISPATCH_TRACE_RECORDED`.
- **Benchmark axis extension**: `BenchmarkAxis.DISPATCH_TRACE` and the
  twelve `A10.01..A10.12` cases.

Catalog patch: v0.31 -> v0.32 with the bounded `I-DTRACE-01..12` row
family (Engineering hypothesis, Phase 3 source label). Split:
11 REQUIRED (I-DTRACE-01..11) + 1 STRUCTURAL (I-DTRACE-12). New
fixtures live under `brain/ui/fixtures/`.

Branch:

```text
campaign/phase3-23-dispatch-tracer
```

Base: `campaign/phase3-22-agent-communication-loop` (PR #27).
Final PR (likely #28): `phase3.23: dispatch tracer wiring`.

---

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

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, or metacognition.
- No new aggregate scalar field (no "consciousness score",
  "sentience score", "awareness score", "I-ness score").
- Cognitive-claim probes still trigger the existing REFUSAL path and
  the dispatch trace records the no-mutation route — never the
  cognitive claim.

---

## Acceptance criteria

Phase 3.23 succeeds only when:

- `DispatchTrace` substrate exists with closed `DispatchTraceKind`,
  `DispatchMutationKind`, `DispatchTraceStatus` enums and bounded
  `DispatchTraceStep`, `DispatchTrace`, `DispatchTraceReport`,
  `DispatchTraceDigest` records.
- `OperatorSession.dispatch` stores the latest bounded
  `DispatchTraceReport` on `session.latest_dispatch_trace`, without
  changing `dispatch()`'s `None` return or any existing semantics.
- `AgentLoopResult` exposes the dispatch trace report.
- `ReasoningTrace` references the dispatch trace digest via a
  `CHECK_DISPATCH_TRACE` step.
- `LearningEvidenceRecord` of kind `DISPATCH_TRACE_RECORDED` can cite
  the dispatch trace digest where relevant.
- Benchmark A10 is green; existing A1..A9 axes do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.32 banner.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5 PASS.
- No new `brain.llm` import, no `brain.tick.tick` call outside the
  approved `STEP_TICK` route, no host execution, no DB schema change,
  no curses.
- PR #28 is open with base `campaign/phase3-22-agent-communication-loop`;
  no PR is merged.
