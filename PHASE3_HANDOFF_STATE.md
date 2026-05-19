# PHASE3_HANDOFF_STATE.md — Multi-campaign state for a fresh Claude Code

This file lets a new Claude Code instance pick up the in-flight work
without losing context. It is updated after every meaningful step so
a fresh session can `git status`, read this file, then keep going.

**Last updated:** Phase 3.32 Mainline Reconciliation in flight;
Phase 3.31 PR #33 MERGED into
`campaign/phase3-30-curriculum-consolidation` on 2026-05-19.
**Active branch:** `campaign/phase3-32-mainline-reconciliation`
**Active campaign:** Phase 3.32 Mainline Reconciliation — bringing
`main` current with the completed campaign stack through Phase 3.31
(catalog v0.37). No new runtime features; documentation /
catalog-banner / handoff staleness corrections only. Will open a PR
targeting `main`; operator merges manually.
**Prior campaigns:**
  - Phase 3.32 Mainline Reconciliation — IN FLIGHT.
    `main` was stale at Phase 3.19 / catalog v0.27 because the
    Phases 3.20–3.31 stack landed as stacked PRs that merged into
    the prior campaign branch instead of `main`. Reconciliation
    branch `campaign/phase3-32-mainline-reconciliation` is cut from
    `main` and merges `origin/campaign/phase3-30-curriculum-
    consolidation` (which now contains Phase 3.31 via PR #33).
    No theory-semantics changes, no new behavioral features, no
    new fixtures, no new catalog rows; non-claim discipline
    preserved.
  - Phase 3.31 Caregiver-Scaffolded Proto-Speech Acquisition —
    COMPLETE; PR #33 MERGED into
    `campaign/phase3-30-curriculum-consolidation`. Catalog v0.36
    -> v0.37. +I-PSPEECH-01..19 (18 REQUIRED + 1 STRUCTURAL).
    Benchmark: 137 cases (119 + 18), 136 PASS + 1 WARN (A3.04
    carry-over) + 0 FAIL. Live-test runner: 10/10 PASS,
    false_positive=0, false_negative=0, stable_single=5,
    stable_combination=0, suppressed=2, transfer_success=1,
    digest `f6a83b9caef0ac17`, drive_stream_digest
    `dc060a88a814f448`. Adds `brain/development/
    proto_speech_acquisition.py`: a pure deterministic OFFLINE
    live-test runner that probes the operational analogue of
    caregiver-scaffolded proto-speech acquisition under ten
    conditions (BABBLE_BASELINE, AMBIENT_IMPRINTING,
    FEEDBACK_REINFORCEMENT, CORRECTION_SHAPING,
    HOLOPHRASE_TRANSFER, TWO_TOKEN_COMBINATION, SUPPRESSION,
    TURN_TAKING, REFUSAL_HELD, DRIVE_STREAM_PRESSURE). The
    drive-stream-grounded babble selector reads from a bounded
    explicit `ProtoSpeechDriveStream` (the audit substitute for
    inner speech) and filters by a session-local
    `ProtoSpeechEvidenceTable` with closed-rule integer-weight
    updates (`ACCEPTED` +3, `ECHO` +3, `EXPANDED` +1/+4,
    `CORRECTED` -2/+3, `IGNORED` -1, `AMBIENT_ONLY` +1) and
    shape-digest transfer. No new `OperatorCommand`, no new
    `LOCAL_COMMAND_VERBS` entry, no new `ACTIVE_VIEWS` value,
    no new `GrowthEventType` / `GrowthEventSource`, no new
    `LearningEvidenceKind` / `ReasoningStepKind` member, no DB
    schema change, no autosave-policy change, no `brain.llm`
    import, no `brain.tick.tick` call outside the existing
    `STEP_TICK` route.
**Older campaigns:**
  > All PRs below (PR #25 .. PR #33) are MERGED into the stacked
  > chain that lands on `campaign/phase3-30-curriculum-consolidation`
  > and are being reconciled into `main` by the Phase 3.32 PR. Any
  > "PR #N open" wording below is historical record from when each
  > step was first authored; treat the merged-state above as
  > authoritative.

  - Phase 3.20 Coherence Feedback Bridge — COMPLETE (PR #25 open)
  - Phase 3.21 Developmental Trajectory — COMPLETE (PR #26 open)
  - Phase 3.21 corrigendum: M10 success criterion reframed against
    `STREAM_HISTORY_MAX_CHUNKS = 256` bound — landed at
    `fb870d5` on the Phase 3.21 branch.
  - Phase 3.22 Agent Communication Loop + Behavioral
    Indistinguishability Harness — COMPLETE; PR #27 open.
  - Phase 3.22b Learning Evidence + Reasoning Trace Continuation —
    COMPLETE; pushed to PR #27 (same branch). Catalog v0.30 -> v0.31.
    +I-AGENTLEARN-01..11.
  - Phase 3.23 Dispatch Tracer Wiring — COMPLETE; PR #28 open
    (base = `campaign/phase3-22-agent-communication-loop`,
    head = `campaign/phase3-23-dispatch-tracer`). Catalog v0.31 ->
    v0.32. +I-DTRACE-01..12.
  - Phase 3.24 Worldlet Feedback Bridge — COMPLETE; PR #29 open
    (base = `campaign/phase3-23-dispatch-tracer`,
    head = `campaign/phase3-24-worldlet-feedback-bridge`). Catalog
    v0.32 -> v0.33. +I-WFDBK-01..12. Benchmark digest
    `b91c4ece90c8706f`.
  - Phase 3.25 Osmotic Learning Live Test — COMPLETE; PR #30 open
    (base = `campaign/phase3-24-worldlet-feedback-bridge`,
    head = `campaign/phase3-25-osmotic-learning-live-test`). Catalog
    v0.33 -> v0.34. +I-OSMO-01..14 (13 REQUIRED + 1 STRUCTURAL).
    Benchmark: 91 cases (77 + 14), 90 PASS + 1 WARN (A3.04
    carry-over) + 0 FAIL, transcript digest `50d1a0ffefcf5ce4`.
    Live-test runner: 10/10 PASS, false_positive=0,
    false_negative=0, transfer_success=7, digest `7aa91075cd76ea73`.
  - Phase 3.26 Active Hypothesis + Self-Directed Probe Loop —
    COMPLETE; pushed to a new stacked branch
    `campaign/phase3-26-active-hypothesis-probe` for PR #31. Catalog
    v0.34 -> v0.35. +I-AHYP-01..14 (13 REQUIRED + 1 STRUCTURAL).
    Benchmark: 105 cases (91 + 14), 104 PASS + 1 WARN (A3.04
    carry-over) + 0 FAIL, transcript digest `0169f117497dba08`.
    Live-test runner: 10/10 PASS, false_positive=0,
    false_negative=0, winner_selected=3, no_hypothesis_survives=3,
    cache_reuse=2, digest `86b67d97daeb251d`.
  - Phase 3.30 Curriculum Consolidation Live Test — COMPLETE;
    pushed to a new stacked branch
    `campaign/phase3-30-curriculum-consolidation` for PR #32
    (base = `campaign/phase3-26-active-hypothesis-probe`,
    head = `campaign/phase3-30-curriculum-consolidation`). Catalog
    v0.35 -> v0.36. +I-CURR-01..14 (13 REQUIRED + 1 STRUCTURAL).
    Benchmark: 119 cases (105 + 14), 118 PASS + 1 WARN (A3.04
    carry-over) + 0 FAIL. Live-test runner: 10/10 PASS,
    false_positive=0, false_negative=0, total_survived=23,
    total_decayed=3, total_rejected=3, reuse_observed=1,
    digest `9412acec1163b978`. Adds
    `brain/development/curriculum_consolidation_probe.py`: a pure
    deterministic OFFLINE live-test runner that probes the
    operational analogue of *curriculum consolidation* under five
    conditions (SINGLE_STRUCTURE / SEQUENTIAL_NONINTERFERING /
    SEQUENTIAL_INTERFERING / DECAY_ON_DISUSE / REUSE_AFTER_NEWER)
    with a bounded session-local slate (size 4), closed admission
    rule (classification gate + digest-collision gate), LRU
    eviction on overflow, probe-time reuse via digest match, and
    a tri-disposition audit trail (SURVIVED / DECAYED / REJECTED).
    No new `OperatorCommand` member; no new `LOCAL_COMMAND_VERBS`
    entry; no new `ACTIVE_VIEWS` value; no new `GrowthEventType`
    / `GrowthEventSource`; no new `LearningEvidenceKind` /
    `ReasoningStepKind` member; no DB schema change; no autosave-
    policy change; no `brain.llm` import; no `brain.tick.tick`
    call outside the existing `STEP_TICK` route.

---

## What is in flight

No active campaign. Phase 3.31 Caregiver-Scaffolded Proto-Speech
Acquisition is COMPLETE on the
`campaign/phase3-31-caregiver-proto-speech` branch. A new PR
opens against the active base branch identified at recovery time
(`campaign/phase3-30-curriculum-consolidation` while PR #32 was
open; the operator should retarget the PR up the stack as
upstream PRs merge).

The non-claim discipline anchored by
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
applies in full. "Active hypothesis" / "self-directed probe" is a
controlled technical metaphor for *bounded structural candidate
enumeration + falsification + caching at the substrate level*; it
is engineering shorthand and does NOT claim psychological
hypothesis formation, inquiry, deliberation, decision-making,
planning, introspection, metacognition, intuition, awareness,
consciousness, sentience, agency, will, desire, belief, intent, or
any cognitive process. "Self-directed" means the probe text is
derived from the input by a closed deterministic rule; it does
NOT mean the runtime has a goal, plan, or wish.

---

## Current step pointer

```text
campaign:   none in flight; Phase 3.31 COMPLETE
status:     nine PRs (#25 + #26 + #27 + #28 + #29 + #30 + #31 +
            #32 + #33) awaiting operator merge decision; #33 is
            stacked on #32 and depends on it.
gates:      v0.37; all 5 gates PASS at Phase 3.31 close
branch:     campaign/phase3-31-caregiver-proto-speech
            (stacked on campaign/phase3-30-curriculum-consolidation)

queued next-campaign candidates (after Phase 3.26 lands):
  - Phase 3.27 worldlet UI construction (operator command + payload
    to populate worldlet_history; Phase 3.24 W2 follow-up).
  - Phase 3.28 coherence aggregation refinement (A3.04 follow-up).
  - Phase 3.29 dispatch trace ring buffer.
  - Phase 3.30 osmotic live-test multi-session retention (future
    extension if substrate ever supports cross-session
    persistence).
  - Phase 3.31 active-hypothesis cross-session reuse cache (future
    extension if substrate ever supports cross-session
    persistence; would require a persistence schema field, an
    autosave trigger, and corresponding non-claim guardrails).
  - Phase 3.32 active-hypothesis adaptive candidate generation
    (bounded learning loop where candidate sets depend on prior
    outcomes; explicit designer choice required).
  - Phase 3.33 active-hypothesis tie-breaker rule for multi-survivor
    trials (explicit designer choice required; v1 deliberately
    preserves multiplicity).
```

---

## Phase 3.31 step ledger (COMPLETE)

```text
Step 1  Design + alignment + roadmap + mission/campaign sync   DONE   commit 0da5e82 (pushed)
Step 2  proto_speech_acquisition.py inventory + records        DONE   commit f25c4b9 (pushed)
Step 3  ProtoSpeechDriveStream + frame builder                 DONE   commit 7b23341 (pushed)
Step 4  Caregiver feedback + evidence updates                  DONE   commit a635c12 (pushed)
Step 5  Drive-grounded babble + ambient + reinforcement        DONE   commit 9ef0748 (pushed)
Step 6  Correction + suppression + transfer                    DONE   commit d05e004 (pushed)
Step 7  Two-token combination + turn-taking + refusal guard    DONE   commit 4871e38 (pushed)
Step 8  Benchmark A15 proto_speech_acquisition axis            DONE   commit 5801c9d (pushed)
Step 9  Catalog v0.37 + I-PSPEECH-01..19 fixtures              DONE   commit 58e7744 (pushed)
Step 10 Proof + transcripts + behavior + findings + audit      DONE   (this commit)
```

Verdict: **PASS WITH NO PHASE-3.31-INTRODUCED FOLLOW-UPS**
(A3.04 carry-over noted but is a Phase 3.21 W3 blocker, not new
in Phase 3.31). Catalog v0.37.

Catalog patch: `I-PSPEECH-01..I-PSPEECH-19` (18 REQUIRED + 1
STRUCTURAL); all rows green in the runner. Eleven new fixtures.
Benchmark: 137 cases (119 from Phase 3.22..3.30 + 18 from Phase
3.31), 136 PASS + 1 documented WARN (A3.04 carry-over) + 0
FAIL, 0 real model calls.

Live-test verdict: 10/10 conditions PASS,
false_positive_count=0, false_negative_count=0,
stable_single_count=5, stable_combination_count=0,
suppressed_count=2, transfer_success_count=1,
digest `f6a83b9caef0ac17`, drive_stream_digest
`dc060a88a814f448`.

Phase 3.21 W3 (A3.04 NOT_APPLICABLE blocker) — REMAINS WARN.

## Phase 3.30 step ledger (COMPLETE — historical)

```text
Step 1  Mission + design + roadmap docs                       DONE   commit f8d3e6f (pushed)
Step 2..5  Curriculum consolidation runner substrate + trials + audit  DONE   commit aaeeb71 (pushed)
Step 6  Benchmark A14 curriculum_consolidation axis           DONE   commit ab4a461 (pushed)
Step 7  Catalog v0.36 + I-CURR-01..14 fixtures                DONE   commit 98c120b (pushed)
Step 8  Live test proof + transcripts + spec + synthesis +
        behavior + findings + audit                           DONE   commit 84dd619 (pushed)
Step 9  Final audit + handoff + open PR #32                   DONE   (this commit)
```

Verdict: **PASS WITH NO PHASE-3.30-INTRODUCED FOLLOW-UPS** (A3.04
carry-over noted but is a Phase 3.21 W3 blocker, not new in
Phase 3.30). Catalog v0.36.

Catalog patch: `I-CURR-01..I-CURR-14` (13 REQUIRED + 1 STRUCTURAL);
all rows green in the runner. Eleven new fixtures. Benchmark: 119
cases (105 from Phase 3.22 / 3.22b / 3.23 / 3.24 / 3.25 / 3.26 +
14 from Phase 3.30), 118 PASS + 1 documented WARN (A3.04 carry-
over) + 0 FAIL, 0 real model calls.

Live-test verdict: 10/10 PASS, false_positive=0, false_negative=0,
total_survived=23, total_decayed=3, total_rejected=3,
reuse_observed=1, digest `9412acec1163b978`.

Phase 3.21 W3 (A3.04 NOT_APPLICABLE blocker) — REMAINS WARN.

## Phase 3.26 step ledger (COMPLETE — historical)

```text
Step 1..9   active hypothesis substrate + benchmark A13 +
            catalog v0.34->v0.35 + reports + handoff           DONE
Catalog patch: I-AHYP-01..14 (13 REQUIRED + 1 STRUCTURAL).
Live-test digest: 86b67d97daeb251d.
```

---

## Recovery procedure (fresh Claude Code)

```bash
cd /home/leah/brain/toy-brain
git fetch origin
git status --short --branch
git log --oneline -25
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
  perception / learning / osmotic-absorption / intuition /
  hypothesis-confidence / active-inquiry score
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
- no new LearningEvidenceKind or ReasoningStepKind member
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
- the active-hypothesis runner MUST NOT import brain.llm.*,
  MUST NOT call brain.tick.tick outside STEP_TICK, MUST NOT pass
  the candidate's predicted_digest_hex16 or predicted_shape into
  the runtime path, MUST NOT use forbidden direct-instruction
  terms in operator-input text, MUST NOT claim hypothesis
  formation / inquiry / deliberation / decision-making /
  introspection / metacognition as cognitive processes
```

---

## Bridge / PR map

- PR #24 Phase 3.19 → `main`, OPEN, MERGEABLE.
- PR #25 Phase 3.20 → `campaign/phase3-19-internal-feedback-loop`, OPEN, MERGEABLE.
- PR #26 Phase 3.21 → `campaign/phase3-20-coherence-feedback-bridge`, OPEN.
- PR #27 (Phase 3.22 + 3.22b) → `campaign/phase3-21-developmental-trajectory`.
- PR #28 (Phase 3.23) → `campaign/phase3-22-agent-communication-loop`.
- PR #29 (Phase 3.24) → `campaign/phase3-23-dispatch-tracer`.
- PR #30 (Phase 3.25) → `campaign/phase3-24-worldlet-feedback-bridge`.
- PR #31 (Phase 3.26) → `campaign/phase3-25-osmotic-learning-live-test`
  while PR #30 is open; retargets up the stack as upstream PRs merge.
- PR #32 (Phase 3.30) → `campaign/phase3-26-active-hypothesis-probe`
  while PR #31 is open; retargets up the stack as upstream PRs merge.
- PR #33 (Phase 3.31) → `campaign/phase3-30-curriculum-consolidation`
  while PR #32 is open; retargets up the stack as upstream PRs merge.
- Stack merge order (operator-controlled):
  PR #24 → #25 → #26 → #27 → #28 → #29 → #30 → #31 → #32 → #33.

---

## Disclosure block (kept up to date)

```text
Stage A ChatGPT/Codex consultation:  not used in this session
Stage B limited-write collaboration: not used in this session
Stage C.1 flow orchestration:        not used in this session
brain-catalog-lint:                  not used in this session
brain-campaign-state:                not used in this session
brain-explorer:                      not used in this session
brain-campaign-state (Phase 3.30):   used (1x at session start for
                                     pre-flight diagnostic)
brain-runner-debugger:               not used in this session
brain-row-implementer:               not used in this session
brain-spec-refresher:                not used in this session
Real model calls used this session:  0
Cumulative real model calls used:    0 / 20
```

Update this block after every notable agent invocation.
