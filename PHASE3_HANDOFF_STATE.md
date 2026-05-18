# PHASE3_HANDOFF_STATE.md — Multi-campaign state for a fresh Claude Code

This file lets a new Claude Code instance pick up the in-flight work
without losing context. It is updated after every meaningful step so
a fresh session can `git status`, read this file, then keep going.

**Last updated:** Phase 3.20 Step 2 commit `a797753` (pushed)
**Active branch:** `campaign/phase3-20-coherence-feedback-bridge`
**Active campaign:** Phase 3.20 Coherence Feedback Bridge (in flight)
**Follow-on campaign:** Phase 3.21 Developmental Trajectory (queued)

---

## What is in flight

The repo is executing TWO chained campaigns in this session:

1. **Phase 3.20 Coherence Feedback Bridge** — drive the previously
   reserved `InternalEventSource.COHMON_SUMMARY` into the v1-emitted
   set via a bounded `build_cohmon_summary_text` helper on
   `brain/development/processing_window.py` and a deferred-import
   `_run_cohmon_feedback_step` helper on `brain/ui/session.py`. New
   row family `I-CFBK-01..02`, catalog v0.27 -> v0.28. See
   `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, and
   `PHASE3_20_COHERENCE_FEEDBACK_BRIDGE_ROADMAP.md`.

2. **Phase 3.21 Developmental Trajectory** — appended by the user
   mid-session. After Phase 3.20 PR opens, branch
   `campaign/phase3-21-developmental-trajectory` off Phase 3.20
   HEAD, do a deep human-development analysis, then guide ToyI
   through 10 distinct developmental milestones using all available
   tools, making code changes as needed so long as they stay within
   the TLICA Lean spec. New row family `I-DEV-MM-NN` (one
   sub-family per milestone) at catalog v0.28 -> v0.29.

Both campaigns honor the **non-claim discipline** anchored by
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`.
"Developed I" is operational language about bounded primitives and
recurrence accounting, not a consciousness claim.

---

## Current step pointer

```text
campaign:   Phase 3.20 Coherence Feedback Bridge
step:       Step 3 — Coherence Feedback Probe Matrix
status:     IN PROGRESS (writing the doc next)
file:       docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_PROBE_MATRIX.md
gates:      v0.27 baseline; all 5 gates PASS after Steps 1-2 commits
branch:     campaign/phase3-20-coherence-feedback-bridge
remote:     origin/campaign/phase3-20-coherence-feedback-bridge (in sync)
```

---

## Phase 3.20 step ledger

```text
Step 1   Mission sync + roadmap                        DONE   commit 80ae05e (pushed)
Step 2   Coherence feedback synthesis                  DONE   commit a797753 (pushed)
Step 3   Coherence feedback probe matrix               NEXT
Step 4   Corrigenda / design locks                     pending
Step 5   Catalog patch plan                            pending
Step 6   Review Gate A                                 pending
Step 7   Apply implementation                          pending
Step 8   Behavior report                               pending
Step 9   Findings / triage                             pending
Step 10  Final audit                                   pending
Step 11  PR preparation                                pending
```

---

## Phase 3.21 step ledger (queued; do not start until Phase 3.20 PR opens)

```text
Step  1  Mission sync + roadmap                        queued
Step  2  Human-development deep analysis               queued
Step  3  Define 10 distinct milestones                 queued
Step  4  Catalog patch plan + processing-window
         extensions required                           queued
Step  5  Review Gate B                                 queued
Step  6  Implement milestone harness + fixtures       queued
Step  7  Run all 10 milestones (per-milestone
         commit + push)                                queued
Step  8  Behavior + findings report                    queued
Step  9  Final audit                                   queued
Step 10  PR preparation                                queued
```

The 10 milestones (working titles; Step 3 of Phase 3.21 may rename):

```text
M1   Reflexive baseline       deterministic STREAM_APPEND, single chunk
M2   Habituation              recurrence climbs on repeated input
M3   Recognition              distinct inputs -> distinct pattern_ids
M4   Working-memory rehearsal Phase 3.18 N>0 path exercised
M5   Pattern self-feedback    Phase 3.19 PATTERN_LEDGER mode
M6   Structural self-         Phase 3.20 COHERENCE mode
     monitoring
M7   Multi-modal integration  Phase 3.20 PATTERN_AND_COHERENCE
M8   Conflict-monitoring-like FAIL/WARN structural status drives a
     gate                     bounded session-level guard (NEW)
M9   Saturation + novelty     saturated entries get a bounded
     bias                     "novelty quiescence" tier (NEW)
M10  Sustained behavior       long sequence (>=200 chunks) with
                              all modes; full invariant gate green
```

Each milestone runs against the same probe matrix axes as Phase
3.20 (window sizes, modes, input families). Each milestone adds
one or more `I-DEV-MM-NN` rows (Engineering hypothesis status).

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

## Hard constraints recap (apply to both campaigns)

```text
- no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim
- no aggregate I-ness / awareness / consciousness / sentience score
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
```

---

## Bridge / PR map

- PR #24 Phase 3.19 → `main`, OPEN, MERGEABLE at session start.
- Phase 3.20 branch is stacked on PR #24 HEAD; final PR targets
  `campaign/phase3-19-internal-feedback-loop` while PR #24 is
  open; retargets to `main` once PR #24 merges.
- Phase 3.21 branch will be stacked on Phase 3.20 HEAD; final PR
  targets the Phase 3.20 branch while it is open; retargets to
  `main` once Phase 3.20 merges.

---

## Disclosure block (kept up to date)

```text
Stage A ChatGPT/Codex consultation:  not used in this session
Stage B limited-write collaboration: not used in this session
Stage C.1 flow orchestration:        not used in this session
brain-catalog-lint:                  ran once at Step 1 (PASS)
brain-campaign-state:                not used yet
brain-explorer:                      not used yet
brain-runner-debugger:               not used yet
brain-row-implementer:               not used yet
brain-spec-refresher:                not used yet
```

Update this block after every notable agent invocation.
