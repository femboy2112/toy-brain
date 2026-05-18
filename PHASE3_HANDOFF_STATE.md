# PHASE3_HANDOFF_STATE.md — Multi-campaign state for a fresh Claude Code

This file lets a new Claude Code instance pick up the in-flight work
without losing context. It is updated after every meaningful step so
a fresh session can `git status`, read this file, then keep going.

**Last updated:** Phase 3.22 Step 1 landed (mission sync + roadmap)
**Active branch:** `campaign/phase3-22-agent-communication-loop`
**Active campaign:** Phase 3.22 Agent Communication Loop + Behavioral
                     Indistinguishability Harness (Step 2 next)
**Prior campaigns:**
  - Phase 3.20 Coherence Feedback Bridge — COMPLETE (PR #25 open)
  - Phase 3.21 Developmental Trajectory — COMPLETE (PR #26 open)
  - Phase 3.21 corrigendum: M10 success criterion reframed against
    `STREAM_HISTORY_MAX_CHUNKS = 256` bound — landed at
    `fb870d5` on the Phase 3.21 branch.

---

## What is in flight

The repo is now executing ONE active campaign:

1. **Phase 3.22 Agent Communication Loop** — build a closed
   deterministic operator-facing interaction loop that routes
   operator input through the existing Phase 3.18-3.21 surfaces
   (text stream / Pattern Ledger / Coherence Monitor / Growth Ledger
   / Proto-BASIC REPL) and emits bounded operator-facing replies.
   Add a closed deterministic benchmark battery exercising pattern
   recurrence, cross-input structural transfer, coherence-status
   variation (the Phase 3.21 W3 follow-up), REPL coherence,
   communication, session continuity, and a blind-transcript
   "mild-agent-like under bounded tests" criterion. New row family
   `I-AGENTLOOP-01..11` (9 REQUIRED + 2 STRUCTURAL), catalog
   v0.29 -> v0.30. See `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
   and `PHASE3_22_AGENT_COMMUNICATION_LOOP_ROADMAP.md`.

The non-claim discipline anchored by
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
applies in full. "Agent communication loop" is engineering shorthand
for "operator-input -> public-surface routing -> bounded reply",
NOT a claim of cognitive agency, sentience, or understanding.

---

## Current step pointer

```text
campaign:   Phase 3.22 Agent Communication Loop
status:     Step 1 landed; Step 2 next
gates:      v0.29 baseline; all 5 gates PASS at Phase 3.21 close
branch:     campaign/phase3-22-agent-communication-loop
base PR:    will target campaign/phase3-21-developmental-trajectory
            while PR #26 is open; retarget to main once #24/#25/#26
            merge.

queued next-campaign candidates (post Phase 3.22):
  - Phase 3.23 tracer wiring through OperatorSession.dispatch
    (deferred since Phase 3.7); enables per-loop observability
    without new runtime state.
  - Phase 3.24 worldlet feedback bridge (deferred Phase 3.19 / 3.20
    architecture review).
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

## Phase 3.22 step ledger (IN PROGRESS)

```text
Step  1  Mission sync + roadmap + handoff state        DONE   (this commit, pending)
Step  2  Benchmark spec + design locks                 TODO
Step  3  REPL bridge pure helpers                      TODO
Step  4  Agent loop / communication module             TODO
Step  5  Pattern recognition benchmark battery         TODO
Step  6  Coherence variation probe (W3 follow-up)      TODO
Step  7  Benchmark runner + transcript generator       TODO
Step  8  Run + iterate until PASS or blocker           TODO
Step  9  Catalog reconciliation + canonical gates      TODO
Step 10  Behavior report + findings + final audit      TODO
Step 11  PR preparation                                TODO
```

Target catalog: v0.30 (Phase 3.22 catalog patch).

Row family: `I-AGENTLOOP-01..I-AGENTLOOP-11` (Engineering
hypothesis; provisional split 9 REQUIRED + 2 STRUCTURAL — exact
split locked in Step 2).

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
- PR #27 (planned at Phase 3.22 close) → `campaign/phase3-21-developmental-trajectory`
  while PR #26 is open; retargets to `main` once #24/#25/#26 merge.
- Stack merge order (operator-controlled): PR #24 → #25 → #26 → #27.

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
