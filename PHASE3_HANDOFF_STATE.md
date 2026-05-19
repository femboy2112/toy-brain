# PHASE3_HANDOFF_STATE.md — Multi-campaign state for a fresh Claude Code

This file lets a new Claude Code instance pick up the in-flight work
without losing context. It is updated after every meaningful step so
a fresh session can `git status`, read this file, then keep going.

**Last updated:** Phase 3.25 COMPLETE; PR #30 to be opened against PR #29
**Active branch:** `campaign/phase3-25-osmotic-learning-live-test`
**Active campaign:** none in flight; Phase 3.25 ready for review
**Prior campaigns:**
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
    `b91c4ece90c8706f`. Sample dispatch / reasoning / learning
    digests in `docs/campaigns/phase3_24/`.
  - Phase 3.25 Osmotic Learning Live Test — COMPLETE; pushed to a
    new stacked branch `campaign/phase3-25-osmotic-learning-live-test`
    for PR #30. Catalog v0.33 -> v0.34. +I-OSMO-01..14 (13 REQUIRED
    + 1 STRUCTURAL). Benchmark: 91 cases (77 + 14), 90 PASS + 1 WARN
    (A3.04 carry-over) + 0 FAIL, transcript digest
    `50d1a0ffefcf5ce4`. Live-test runner: 10 / 10 PASS,
    false_positive=0, false_negative=0, transfer_success=7,
    digest `7aa91075cd76ea73`. Adds
    `brain/development/osmotic_learning_probe.py`: a pure
    deterministic OFFLINE live-test runner that probes the
    operational analogue of osmotic imprinting + activation under
    CONTROL_NO_EXPOSURE / TRUE_EXPOSURE / SHAM_EXPOSURE /
    DISTRACTOR_INTERFERENCE conditions. No new `OperatorCommand`
    member; no new `LOCAL_COMMAND_VERBS` entry; no new
    `ACTIVE_VIEWS` value; no new `GrowthEventType` /
    `GrowthEventSource`; no DB schema change; no autosave-policy
    change; no `brain.llm` import; no `brain.tick.tick` call outside
    the existing `STEP_TICK` route; no new `LearningEvidenceKind` /
    `ReasoningStepKind` value (reuses
    `ABSTRACT_PATTERN_ACQUIRED`, `ABSTRACT_PATTERN_REUSED`,
    `TRANSFER_RECOGNIZED`).

---

## What is in flight

No active campaign. Phase 3.25 Osmotic Learning Live Test is COMPLETE
on the `campaign/phase3-25-osmotic-learning-live-test` branch,
stacked on PR #29 (Phase 3.24). PR #30 should be opened with base
`campaign/phase3-24-worldlet-feedback-bridge` and head
`campaign/phase3-25-osmotic-learning-live-test`.

The non-claim discipline anchored by
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
applies in full. "Osmotic learning" / "osmotic imprinting" is a
controlled technical metaphor for *unlabeled exposure-driven
structural uptake at the substrate level*; it is engineering
shorthand and does NOT claim psychological learning, intuition,
awareness, embodiment, consciousness, sentience, agency, will,
desire, belief, intent, introspection, metacognition, or unconscious
learning.

---

## Current step pointer

```text
campaign:   none in flight; Phase 3.25 COMPLETE
status:     six PRs (#25 + #26 + #27 + #28 + #29 + #30) awaiting
            operator merge decision; #30 is stacked on #29 and
            depends on it.
gates:      v0.34; all 5 gates PASS at Phase 3.25 close
branch:     campaign/phase3-25-osmotic-learning-live-test
            (stacked on campaign/phase3-24-worldlet-feedback-bridge)

queued next-campaign candidates (after Phase 3.25 lands):
  - Phase 3.26 worldlet UI construction (operator command + payload
    to populate worldlet_history; Phase 3.24 W2 follow-up).
  - Phase 3.27 coherence aggregation refinement (A3.04 follow-up).
  - Phase 3.28 dispatch trace ring buffer.
  - Phase 3.29 osmotic live-test multi-session retention (future
    extension if substrate ever supports cross-session
    persistence).
```

---

## Phase 3.25 step ledger (COMPLETE)

```text
Step 1  Mission + design + roadmap docs                   DONE   commit c060f51 (pushed)
Step 2..5  Osmotic probe substrate + trials + integration  DONE   commit 0fd55c2 (pushed)
Step 6  Benchmark A12 osmotic_learning axis               DONE   commit e2a3152 (pushed)
Step 7  Catalog v0.34 + I-OSMO-01..14 fixtures            DONE   commit 266b201 (pushed)
Step 8  Live test proof + transcripts + spec + synthesis +
        behavior + findings + audit                       DONE   commit 31e9eb3 (pushed)
Step 9  Final audit + handoff + open PR #30               DONE   (this commit)
```

Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Catalog v0.34.

Catalog patch: `I-OSMO-01..I-OSMO-14` (13 REQUIRED + 1 STRUCTURAL);
all rows green in the runner. Ten new fixtures. Benchmark: 91 cases
(77 from Phase 3.22 / 3.22b / 3.23 / 3.24 + 14 from Phase 3.25), 90
PASS + 1 documented WARN (A3.04 carry-over) + 0 FAIL, 0 real model
calls, transcript digest `50d1a0ffefcf5ce4`.

Live-test verdict: 10 / 10 PASS, false_positive=0,
false_negative=0, transfer_success=7, digest `7aa91075cd76ea73`.

Phase 3.21 W3 (A3.04 NOT_APPLICABLE blocker) — REMAINS WARN.

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
  perception / learning / osmotic-absorption / intuition score
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
- the osmotic-learning runner MUST NOT import brain.llm.*,
  MUST NOT call brain.tick.tick outside STEP_TICK, MUST NOT pass
  the expected target digest or expected shape into the runtime
  path, MUST NOT use forbidden direct-instruction terms in
  operator-input text, MUST NOT claim intuition / awareness /
  unconscious learning / understanding
```

---

## Bridge / PR map

- PR #24 Phase 3.19 → `main`, OPEN, MERGEABLE.
- PR #25 Phase 3.20 → `campaign/phase3-19-internal-feedback-loop`, OPEN, MERGEABLE.
- PR #26 Phase 3.21 → `campaign/phase3-20-coherence-feedback-bridge`, OPEN.
- PR #27 (Phase 3.22 + 3.22b) → `campaign/phase3-21-developmental-trajectory`.
- PR #28 (Phase 3.23) → `campaign/phase3-22-agent-communication-loop`.
- PR #29 (Phase 3.24) → `campaign/phase3-23-dispatch-tracer`.
- PR #30 (Phase 3.25) → `campaign/phase3-24-worldlet-feedback-bridge`
  while PR #29 is open; retargets up the stack as upstream PRs merge.
- Stack merge order (operator-controlled):
  PR #24 → #25 → #26 → #27 → #28 → #29 → #30.

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
