# PHASE3_HANDOFF_STATE.md — Multi-campaign state for a fresh Claude Code

This file lets a new Claude Code instance pick up the in-flight work
without losing context. It is updated after every meaningful step so
a fresh session can `git status`, read this file, then keep going.

**Last updated:** Phase 3.23 COMPLETE; PR #28 to be opened against PR #27
**Active branch:** `campaign/phase3-23-dispatch-tracer`
**Active campaign:** none in flight; Phase 3.23 ready for review
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
  - Phase 3.23 Dispatch Tracer Wiring — COMPLETE; pushed to a new
    stacked branch `campaign/phase3-23-dispatch-tracer` for PR #28.
    Catalog v0.31 -> v0.32. +I-DTRACE-01..12 (11 REQUIRED + 1
    STRUCTURAL). Benchmark: 65 cases (53 + 12), 64 PASS + 1 WARN
    (A3.04 carry-over) + 0 FAIL, transcript digest
    `8cc4a4ca1845c6a4`. Adds `brain/development/dispatch_tracer.py`
    and wires `OperatorSession.dispatch` to store a bounded
    `DispatchTraceReport` on the new `latest_dispatch_trace` field.

---

## What is in flight

No active campaign. Phase 3.23 Dispatch Tracer Wiring is COMPLETE on
the `campaign/phase3-23-dispatch-tracer` branch, stacked on PR #27
(Phase 3.22 + 3.22b). PR #28 should be opened with base
`campaign/phase3-22-agent-communication-loop` and head
`campaign/phase3-23-dispatch-tracer`.

The non-claim discipline anchored by
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
applies in full. "Dispatch trace" is engineering shorthand for
"explicit bounded audit record of public dispatch route and
structural effects", NOT a claim of cognitive agency, sentience,
or understanding.

---

## Current step pointer

```text
campaign:   none in flight; Phase 3.23 COMPLETE
status:     four PRs (#25 + #26 + #27 + #28) awaiting operator
            merge decision; #28 is stacked on #27 and depends on it.
gates:      v0.32; all 5 gates PASS at Phase 3.23 close
branch:     campaign/phase3-23-dispatch-tracer
            (stacked on campaign/phase3-22-agent-communication-loop)

queued next-campaign candidates (after Phase 3.23 lands):
  - Phase 3.24 worldlet feedback bridge (deferred Phase 3.19 /
    3.20 architecture review). Bounded extension following the
    FeedbackMode precedent.
  - Phase 3.25 coherence aggregation refinement (A3.04 follow-up).
  - Phase 3.26 dispatch trace ring buffer.
  - Phase 3.27 per-dispatch interaction_id serial (NOOP collision
    deferred enhancement from Phase 3.23 F4).
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

The 10 milestones (working titles; Step 3 of Phase 3.21 finalized):

```text
M01  Reflexive baseline       deterministic STREAM_APPEND, single chunk
M02  Habituation              recurrence climbs on repeated input
M03  Recognition              distinct inputs -> distinct pattern_ids
M04  Working-memory rehearsal Phase 3.18 N>0 path exercised
M05  Pattern self-feedback    Phase 3.19 PATTERN_LEDGER mode
M06  Structural self-         Phase 3.20 COHERENCE mode
     monitoring
M07  Multi-modal integration  Phase 3.20 PATTERN_AND_COHERENCE
M08  Saturation + novelty     SATURATED transition followed by
     bias                     new MIN entry
M09  Cross-input              distinct PATTERN_AND_COHERENCE inputs
     differentiation          produce pairwise-disjoint families
M10  Sustained behavior       long sequence saturates bounded
                              substrates at exactly 256 chunks +
                              256 growth events (correct
                              substrate-bounded behavior)
```

---

## Phase 3.22 step ledger (COMPLETE)

```text
Step  1  Mission sync + roadmap + handoff state        DONE   commit 13f8206 (pushed)
Step  2  Benchmark spec + design locks                 DONE   commit 91b3963 (pushed)
Step  3  REPL bridge pure helpers                      DONE   commit 2b32e06 (pushed)
Step  4  Agent loop / communication module             DONE   commit 7419a82 (pushed)
Step  5  Pattern recognition benchmark battery         DONE   commit 7d78cb8 (pushed)
Step  6  Coherence variation probe (W3 follow-up)      DONE   commit b6b600a (pushed)
Step  7  Benchmark runner + transcript generator       DONE   commit ae98933 (pushed)
Step  8  Run + iterate until PASS or blocker           DONE   (no-op; benchmark PASSed on first run)
Step  9  Catalog reconciliation + canonical gates      DONE   commit a158ea5 (pushed)
Step 10  Behavior report + findings + final audit      DONE   commit 4f6e25f (pushed)
Step 11  PR preparation                                IN PROGRESS
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.30.

Catalog patch: `I-AGENTLOOP-01..I-AGENTLOOP-11` (9 REQUIRED + 2
STRUCTURAL); all rows green in the runner. Three new modules:
`brain/development/agent_repl_bridge.py`,
`brain/development/agent_loop.py`,
`brain/development/agent_benchmark.py`. Eleven new fixtures.
Benchmark: 39 cases, 38 PASS + 1 documented WARN (A3.04 — the
Phase 3.21 W3 follow-up not_applicable-overall blocker), 0 FAIL,
0 real model calls, transcript digest `b6a93e11a105edd3`.

---

## Phase 3.22b step ledger (COMPLETE)

```text
Step  1  Design docs (synthesis + proof spec + trace spec)  DONE   commit cf16b97 (pushed)
Step  2  abstract_pattern.py + AbstractPatternSignature     DONE   commit 9f5ea5b (pushed)
Step  3  learning_evidence.py + 8 evidence kinds            DONE   commit 660f572 (pushed)
Step  4  reasoning_trace.py + 10 step kinds                 DONE   commit 941f34b (pushed)
Step  5  Integrate into agent_loop                          DONE   commit c408556 (pushed)
Step  6  Extend benchmark A8 + A9                           DONE   commit 1e58c83 (pushed)
Step  7  Catalog v0.31 + I-AGENTLEARN fixtures              DONE   commit 3ce46ac (pushed)
Step  8  Behavior + findings + audit + proof + trace        DONE   commit 5bfe14e (pushed)
Step  9  Final gates + handoff + PR update                  DONE   (this commit)
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.31.

Catalog patch: `I-AGENTLEARN-01..I-AGENTLEARN-11` (10 REQUIRED + 1
STRUCTURAL); all rows green in the runner. Three new modules:
`brain/development/abstract_pattern.py`,
`brain/development/learning_evidence.py`,
`brain/development/reasoning_trace.py`. Eleven new fixtures.
Benchmark: 53 cases (39 from Phase 3.22 + 14 from Phase 3.22b), 52
PASS + 1 documented WARN (A3.04 carry-over) + 0 FAIL, 0 real model
calls, transcript digest `aa4fae94b8c9a8e4`. Learning proof digest
(sample 6-step sequence): `df75162f93605181`. Reasoning trace
digest (renamed-transfer reply): `5d8feb2a3096c3ad`.

Phase 3.22 W2 (renamed-structure transfer) — RESOLVED.
Phase 3.22 W3 (refusal overbreadth) — REFINED with narrower
  cognitive-claim classifier; wider audit-tuple scan retained as
  defense-in-depth floor.
Phase 3.22 W4 (tick routing) — DOCUMENTED via dispatch-path label
  in reasoning trace's OBSERVE_INPUT step; OFFLINE path preserved.
Phase 3.22 W5 (REPL valid-effective) — RESOLVED with
  DIMINISHING_RETURNS_UPDATED evidence + CORRECTION evidence.
Phase 3.22 W1 (not_applicable overall blocker) — REMAINS WARN,
  documented as A3.04.

---

## Phase 3.23 step ledger (COMPLETE)

```text
Step 1  Mission + design + roadmap docs                    DONE   commit 3afa173 (pushed)
Step 2  Dispatch trace substrate (dispatch_tracer.py)      DONE   commit a1be9b0 (pushed)
Step 3  Session dispatch trace wiring (session.py)         DONE   commit e9f0320 (pushed)
Step 4  Agent loop / reasoning / learning integration      DONE   commit f829d07 (pushed)
Step 5  Benchmark A10 dispatch_trace axis                  DONE   commit cd0d6da (pushed)
Step 6  Catalog v0.32 + I-DTRACE-01..12 fixtures           DONE   commit 1ac4d2f (pushed)
Step 7  Trace proof + behavior + findings reports          DONE   commit 8ae09d6 (pushed)
Step 8  Final audit + handoff + open PR #28                DONE   (this commit)
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.32.

Catalog patch: `I-DTRACE-01..I-DTRACE-12` (11 REQUIRED + 1 STRUCTURAL);
all rows green in the runner. One new module
`brain/development/dispatch_tracer.py`. Nine new fixtures. Benchmark:
65 cases (53 from Phase 3.22 / 3.22b + 12 from Phase 3.23), 64 PASS
+ 1 documented WARN (A3.04 carry-over) + 0 FAIL, 0 real model calls,
transcript digest `8cc4a4ca1845c6a4`. Dispatch trace proof digests
documented in `PHASE3_23_TRACE_PROOF_REPORT.md`.

Phase 3.22 W4 (dispatch trace deferral) — RESOLVED via the new
  bounded substrate + AgentLoopResult / reasoning / learning citation.
Phase 3.21 W3 (A3.04 NOT_APPLICABLE blocker) — REMAINS WARN (carried
  forward; future coherence-aggregation refinement).

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
  maturity / capability / mild-agent score
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
- the new agent communication loop module MUST NOT import
  brain.llm.* and MUST NOT call brain.tick.tick
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
  (to be opened at Step 8). Retargets up the stack as upstream
  PRs merge.
- Stack merge order (operator-controlled): PR #24 → #25 → #26 → #27 → #28.

---

## Disclosure block (kept up to date)

```text
Stage A ChatGPT/Codex consultation:  not used in this session
Stage B limited-write collaboration: not used in this session
Stage C.1 flow orchestration:        not used in this session
brain-catalog-lint:                  ran once at Step 1 (PASS)
brain-campaign-state:                not used yet
brain-explorer:                      not used yet  (Explore agent
                                     used once for public surface
                                     survey in Phase 3.22 Step 1)
brain-runner-debugger:               not used yet
brain-row-implementer:               not used yet
brain-spec-refresher:                not used yet
Real model calls used this session:  0
Cumulative real model calls used:    0 / 20
```

Update this block after every notable agent invocation.
