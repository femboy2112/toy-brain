# PHASE3_HANDOFF_STATE.md — Multi-campaign state for a fresh Claude Code

This file lets a new Claude Code instance pick up the in-flight work
without losing context. It is updated after every meaningful step so
a fresh session can `git status`, read this file, then keep going.

**Last updated:** Phase 3.24 COMPLETE; PR #29 to be opened against PR #28
**Active branch:** `campaign/phase3-24-worldlet-feedback-bridge`
**Active campaign:** none in flight; Phase 3.24 ready for review
**Prior campaigns:**
  - Phase 3.20 Coherence Feedback Bridge — COMPLETE (PR #25 open)
  - Phase 3.21 Developmental Trajectory — COMPLETE (PR #26 open)
  - Phase 3.21 corrigendum: M10 success criterion reframed against
    `STREAM_HISTORY_MAX_CHUNKS = 256` bound — landed at
    `fb870d5` on the Phase 3.21 branch.
  - Phase 3.22 Agent Communication Loop + Behavioral
    Indistinguishability Harness — COMPLETE; PR #27 open.
  - Phase 3.22b Learning Evidence + Reasoning Trace Continuation —
    COMPLETE; pushed to PR #27 (same branch).
    Catalog v0.30 -> v0.31. +I-AGENTLEARN-01..11 (10 REQUIRED + 1
    STRUCTURAL). Benchmark: 53 cases, 52 PASS + 1 WARN + 0 FAIL,
    transcript digest `aa4fae94b8c9a8e4`.
  - Phase 3.23 Dispatch Tracer Wiring — COMPLETE; PR #28 open
    (base = `campaign/phase3-22-agent-communication-loop`,
    head = `campaign/phase3-23-dispatch-tracer`). Catalog v0.31 ->
    v0.32. +I-DTRACE-01..12 (11 REQUIRED + 1 STRUCTURAL).
    Benchmark: 65 cases (53 + 12), 64 PASS + 1 WARN (A3.04
    carry-over) + 0 FAIL, transcript digest `8cc4a4ca1845c6a4`.
    Adds `brain/development/dispatch_tracer.py` and wires
    `OperatorSession.dispatch` to store a bounded
    `DispatchTraceReport` on the new `latest_dispatch_trace` field.
  - Phase 3.24 Worldlet Feedback Bridge — COMPLETE; pushed to a new
    stacked branch `campaign/phase3-24-worldlet-feedback-bridge`
    for PR #29. Catalog v0.32 -> v0.33. +I-WFDBK-01..12 (11
    REQUIRED + 1 STRUCTURAL). Benchmark: 77 cases (65 + 12), 76
    PASS + 1 WARN (A3.04 carry-over) + 0 FAIL, transcript digest
    `b91c4ece90c8706f`. Adds bounded
    `processing_window.build_worldlet_summary_text`, the
    `FeedbackMode.WORLDLET` + `FeedbackMode.PATTERN_COHERENCE_WORLDLET`
    enum members, the `InternalEventSource.WORLDLET_SUMMARY`
    member, the `OperatorSession._run_worldlet_feedback_step`
    helper, the `ReasoningStepKind.CHECK_WORLDLET_FEEDBACK` +
    `LearningEvidenceKind.WORLDLET_FEEDBACK_RECORDED` extensions,
    three new bounded `AgentObservationSummary` fields, and the
    A11 benchmark axis (12 cases). No new `OperatorCommand` member;
    no new `LOCAL_COMMAND_VERBS` entry; no new `ACTIVE_VIEWS`
    value; no new `GrowthEventType` / `GrowthEventSource`; no DB
    schema change; no autosave-policy change; no `brain.llm`
    import; no `brain.tick.tick` call outside the existing
    `STEP_TICK` route.

---

## What is in flight

No active campaign. Phase 3.24 Worldlet Feedback Bridge is COMPLETE on
the `campaign/phase3-24-worldlet-feedback-bridge` branch, stacked on
PR #28 (Phase 3.23). PR #29 should be opened with base
`campaign/phase3-23-dispatch-tracer` and head
`campaign/phase3-24-worldlet-feedback-bridge`.

The non-claim discipline anchored by
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
applies in full. "Worldlet feedback" is engineering shorthand for
"a bounded structural summary of the session-local Minimal Worldlet
substrate replayed through the processing window so the Pattern
Ledger and downstream traces can observe it" — NEVER a claim of
perception, embodiment, world-modeling, understanding, consciousness,
sentience, agency, will, desire, belief, intent, introspection, or
metacognition.

---

## Current step pointer

```text
campaign:   none in flight; Phase 3.24 COMPLETE
status:     five PRs (#25 + #26 + #27 + #28 + #29) awaiting
            operator merge decision; #29 is stacked on #28 and
            depends on it.
gates:      v0.33; all 5 gates PASS at Phase 3.24 close
branch:     campaign/phase3-24-worldlet-feedback-bridge
            (stacked on campaign/phase3-23-dispatch-tracer)

queued next-campaign candidates (after Phase 3.24 lands):
  - Phase 3.25 osmotic learning live test (already scoped; builds
    on the Phase 3.24 worldlet feedback path).
  - Phase 3.26 worldlet UI construction (operator command + payload
    to populate worldlet_history; Phase 3.24 W2 follow-up).
  - Phase 3.27 coherence aggregation refinement (A3.04 follow-up).
  - Phase 3.28 dispatch trace ring buffer.
```

---

## Phase 3.20 step ledger (COMPLETE)

```text
Step 1   Mission sync + roadmap                        DONE   commit 80ae05e (pushed)
Step 2   Coherence feedback synthesis                  DONE   commit a797753 (pushed)
Step 3   Coherence feedback probe matrix               DONE   commit eca1a6a (pushed)
Step 4   Corrigenda / design locks                     DONE   commit e012ca7 (pushed)
Step 5   Catalog patch plan                            DONE   commit 946ab72 (pushed)
Step 6   Review Gate A                                 DONE   (in Step 7 commit preamble)
Step 7   Apply implementation                          DONE   commit 6c6eda8 (pushed)
Step 8   Behavior report                               DONE   commit 7e46c9f (pushed)
Step 9   Findings / triage                             DONE   commit ed1ad72 (pushed)
Step 10  Final audit                                   DONE   commit 1ecb810 (pushed)
Step 11  PR preparation                                DONE   PR #25 opened (base=Phase 3.19 branch)
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.28.

---

## Phase 3.21 step ledger (COMPLETE)

```text
Step  1  Mission sync + roadmap                        DONE   commit 5eefd28 (pushed)
Step  2  Human-development synthesis                   DONE   commit 4d6abf4 (pushed)
Step  3  Ten milestones + corrigenda                   DONE   commit 45f5ca9 (pushed)
Step  4  Catalog patch plan                            DONE   commit 8c5bdbe (pushed)
Step  5  Review Gate B                                 DONE   (in Step 6 preamble)
Step  6  Implement milestone harness + fixtures        DONE   commit c25d726 (pushed)
Step  7  Run all 10 milestones                         DONE   commit f035836 (pushed)
Step  8  Behavior + findings report                    DONE   commit b0ab467 (pushed)
Step  9  Final audit                                   DONE   commit aff48e0 (pushed)
Step 10  PR preparation                                DONE   PR #26 opened (base=Phase 3.20 branch)
Phase3.21 corrigendum: M10 stream-bound clarification  DONE   commit fb870d5 (pushed)
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.29.

---

## Phase 3.22 step ledger (COMPLETE)

See prior handoff state for the per-step commits. Catalog v0.30.

---

## Phase 3.22b step ledger (COMPLETE)

See prior handoff state. Catalog v0.31.

---

## Phase 3.23 step ledger (COMPLETE)

See prior handoff state. Catalog v0.32. Benchmark digest
`8cc4a4ca1845c6a4`.

---

## Phase 3.24 step ledger (COMPLETE)

```text
Step 1  Mission + design + roadmap + substrate survey docs   DONE   commit ec90ff3 (pushed)
Step 2  Worldlet summary helper + FeedbackMode.WORLDLET +
        InternalEventSource.WORLDLET_SUMMARY                  DONE   commit 8d6ce41 (pushed)
Step 3  Session worldlet feedback wiring                      DONE   commit ab87516 (pushed)
Step 4  Dispatch / Reasoning / Learning / AgentLoop wiring    DONE   commit f8574f3 (pushed)
Step 5  Benchmark A11 worldlet_feedback axis                  DONE   commit 1ee428b (pushed)
Step 6  Catalog v0.33 + I-WFDBK-01..12 fixtures              DONE   commit ca6d766 (pushed)
Step 7  Worldlet feedback proof + behavior + findings reports DONE   commit 633d96f (pushed)
Step 8  Final audit + handoff + open PR #29                   DONE   (this commit)
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.33.

Catalog patch: `I-WFDBK-01..I-WFDBK-12` (11 REQUIRED + 1 STRUCTURAL);
all rows green in the runner. Eight new fixtures.
Benchmark: 77 cases (65 from Phase 3.22 / 3.22b / 3.23 + 12 from
Phase 3.24), 76 PASS + 1 documented WARN (A3.04 carry-over) + 0
FAIL, 0 real model calls, transcript digest `b91c4ece90c8706f`.
Worldlet feedback proof digests documented in
`docs/campaigns/phase3_24/PHASE3_24_WORLDLET_FEEDBACK_PROOF_REPORT.md`.

Sample digests:
  worldlet feedback dispatch digest (alpha line one):     bf33af2938fb773a
  reasoning trace digest (alpha line one, WORLDLET):      690e2c923e1c1e16
  learning proof digest (alpha line one, WORLDLET):       2dc1523baa8a31dc

Phase 3.22 follow-ups: unchanged.
Phase 3.21 W3 (A3.04 NOT_APPLICABLE blocker) — REMAINS WARN
  (carried forward; future coherence-aggregation refinement).

---

## Recovery procedure (fresh Claude Code)

```bash
cd /home/leah/brain/toy-brain
git fetch origin
git status --short --branch
git log --oneline -20
cat PHASE3_HANDOFF_STATE.md          # read this file
cat CURRENT_MISSION.md               # active mission
cat CURRENT_CAMPAIGN.md              # active campaign body
python3 -m tools.claude_helpers.gate_runner --json | tail -20
```

Then resume at the step named under **Current step pointer** above.

---

## Hard constraints recap (apply to all in-flight campaigns)

```text
- no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim
- no aggregate I-ness / awareness / consciousness / sentience /
  maturity / capability / mild-agent / world / world-modeling /
  perception score
- no SelfModel implementation
- no brain/tick.py edit
- no brain/llm/** edit
- no parser change
- no prompt change
- no DB schema or SCHEMA_VERSION change
- no autosave change
- no L1 / L2 cache semantic change
- no Pattern Ledger / Coherence Monitor / Growth Ledger semantic
  change
- no new GrowthEventType or GrowthEventSource
- no new OperatorCommand member; no new ACTIVE_VIEWS value
- OFFLINE default; model-backed modes explicit opt-in only
- 20 real model calls budgeted across the session (expected: 0)
- max Stage C.1 nodes per campaign = 5 unless operator approves
  more
- every step that lands files commits + pushes
- PR opens against the correct base; merge requires explicit
  operator approval
- stay within the TLICA Lean spec in lean_reference/; engineering
  hypothesis rows are allowed but must not contradict existing
  REQUIRED rows
- the new worldlet-feedback path MUST NOT import brain.llm.*,
  MUST NOT call brain.tick.tick outside STEP_TICK, MUST NOT
  mutate OperatorSession.worldlet_history, MUST NOT claim
  perception / embodiment / external-world understanding
```

---

## Bridge / PR map

- PR #24 Phase 3.19 → `main`, OPEN, MERGEABLE.
- PR #25 Phase 3.20 → `campaign/phase3-19-internal-feedback-loop`, OPEN, MERGEABLE.
  Retargets to `main` once PR #24 merges.
- PR #26 Phase 3.21 → `campaign/phase3-20-coherence-feedback-bridge`, OPEN.
  Retargets to `main` once both PR #24 and PR #25 merge.
- PR #27 (Phase 3.22 + 3.22b) → `campaign/phase3-21-developmental-trajectory`
  while PR #26 is open; retargets to `main` once #24/#25/#26 merge.
- PR #28 (Phase 3.23) → `campaign/phase3-22-agent-communication-loop`
  while PR #27 is open; retargets up the stack as upstream PRs merge.
- PR #29 (Phase 3.24) → `campaign/phase3-23-dispatch-tracer`
  while PR #28 is open; retargets up the stack as upstream PRs merge.
- Stack merge order (operator-controlled):
  PR #24 → #25 → #26 → #27 → #28 → #29.

---

## Disclosure block (kept up to date)

```text
Stage A ChatGPT/Codex consultation:  not used in this session
Stage B limited-write collaboration: not used in this session
Stage C.1 flow orchestration:        not used in this session
brain-catalog-lint:                  not used in this session
brain-campaign-state:                not used in this session
brain-explorer:                      not used in this session
brain-runner-debugger:               not used in this session
brain-row-implementer:               not used in this session
brain-spec-refresher:                not used in this session
Real model calls used this session:  0
Cumulative real model calls used:    0 / 20
```

Update this block after every notable agent invocation.
