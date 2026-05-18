# CURRENT_MISSION.md — Phase 3.21 Developmental Trajectory

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read
this file, read `CURRENT_CAMPAIGN.md`, create or continue the active
campaign branch, run the next eligible campaign step, commit successful
results, push the branch, and stop exactly where the campaign says to
stop.

---

## Current mission

Execute the **Phase 3.21 Developmental Trajectory Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.21 follows the completed Phase 3.20 Coherence Feedback Bridge
campaign (PR #25, open against `campaign/phase3-19-internal-feedback-loop`
at campaign start; stacked on PR #24). Phase 3.20 shipped:

- `FeedbackMode.COHERENCE` and `FeedbackMode.PATTERN_AND_COHERENCE`;
- a pure deterministic `build_cohmon_summary_text(...)` helper;
- widened `_V1_EMITTED_SOURCES` to include `COHMON_SUMMARY`;
- `OperatorSession._run_cohmon_feedback_step` with deferred-import
  of `build_full_coherence_report`;
- catalog v0.27 → v0.28 with `I-CFBK-01` and `I-CFBK-02`;
- zero real model calls; `brain/tick.py` untouched.

Phase 3.21 takes the next bounded operational question:

> Can ToyI's runtime exhibit a recognizable **structural
> developmental trajectory** — a deterministic sequence of bounded
> behaviors that approximate, in operational terms only, ten
> distinct human-development analogues — using only the surfaces
> Phases 3.0 through 3.20 have built, without touching
> `brain/tick.py`, the LLM, the parser, the cache, the schema, or
> any consciousness-adjacent boundary?

Phase 3.21 takes ToyI from:

```text
single-dispatch deterministic recurrence + feedback (Phases 3.0-3.20)
```

toward:

```text
sequential ten-milestone trajectory:
  reflexive baseline ->
    habituation ->
      recognition ->
        rehearsal ->
          pattern self-feedback ->
            structural self-monitoring approximation ->
              multi-modal integration ->
                saturation + novelty discrimination ->
                  cross-input differentiation under feedback ->
                    sustained complex behavior
```

This is an **operational architecture campaign**: ToyI's runtime
is shown to support a deterministic sequence of bounded structural
behaviors that mirror well-studied human-development analogues at
the level of *structural marker* only — never at the level of
phenomenology, semantic content, agency, or self-awareness.

Allowed claim shape:

```text
"ToyI's runtime supports a bounded deterministic ten-step
developmental trajectory where each step has a clear structural
marker (chunk count formula, Pattern Ledger entry shape,
recurrence-count climb, saturation-state transition, or
second-order entry emergence) that can be deterministically
demonstrated against the public surfaces of brain/development/,
brain/ui/session.py, and brain/development/processing_window.py
without invoking the LLM, the kernel tick path, the cache, or
the persistence layer."
```

Forbidden claim shape:

```text
"ToyI is conscious / sentient / understands / has a self / has
agency / desires / introspects / develops in any psychological
sense / experiences / matures / grows up."
```

The word "develops" is used throughout this campaign in the
**operational** sense ("the runtime *develops a deterministic
trajectory across the ten milestones*") never in the
**psychological / subjective** sense.

Campaign target:

```text
Phase 3.21 Step 1   Mission sync + roadmap
Phase 3.21 Step 2   Human-development synthesis
Phase 3.21 Step 3   Ten-milestone definition + corrigenda
Phase 3.21 Step 4   Catalog patch plan
Phase 3.21 Step 5   Review Gate B
Phase 3.21 Step 6   Implement milestone harness + fixtures
Phase 3.21 Step 7   Run all 10 milestones; record outcomes
Phase 3.21 Step 8   Behavior + findings report
Phase 3.21 Step 9   Final audit
Phase 3.21 Step 10  PR preparation
```

Intended result:

```text
A small, reviewed runtime helper module
brain/development/milestone_harness.py that defines a closed-enum
DevelopmentalMilestone enumeration over ten distinct milestones,
provides one pure deterministic helper per milestone that takes a
fresh OperatorSession and asserts the milestone's bounded
structural marker(s), and exposes a single run_milestone(...)
entry point. A new catalog row family I-DEVMILE-01..I-DEVMILE-11
(ten milestone rows + one static audit row) lands at catalog
v0.28 -> v0.29. Eleven new fixtures (or one fixture per
milestone, plus one static audit fixture) drive the row family.
brain/tick.py untouched; LLM unused; cache untouched; OFFLINE
default preserved; no consciousness-adjacent claim.
```

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-21-developmental-trajectory
```

If Phase 3.20 PR #25 has not yet merged at campaign start, the
Phase 3.21 branch is **stacked** on the current Phase 3.20 HEAD and
the final PR targets `campaign/phase3-20-coherence-feedback-bridge`.
If PR #24 + PR #25 both merge during the campaign, the final PR
retargets to `main` before final PR preparation.

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into the correct base at campaign completion
never merge the PR without explicit user approval
never edit brain/tick.py in Phase 3.21
```

---

## Baseline to verify

Expected current baseline (must match before any step runs):

```text
Catalog: v0.28 (inherited from Phase 3.20; will become v0.29 at Step 6)
Counts (pre-Step-6):
  REQUIRED:        284
  STRUCTURAL:       91
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.20 Coherence Feedback Bridge
                              (PR #25 open against Phase 3.19 branch)
Current mission:              Phase 3.21 Developmental Trajectory
Next eligible step:           Step 2 human-development synthesis
                              (after Step 1 commits/pushes)
```

Stop if catalog counts disagree.

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
PHASE3_21_DEVELOPMENTAL_TRAJECTORY_ROADMAP.md
PHASE3_HANDOFF_STATE.md
docs/campaigns/phase3_18/PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md
docs/campaigns/phase3_18/PHASE3_18_PATTERN_RECOGNITION_DEMO.md
docs/campaigns/phase3_18/PHASE3_18_AUDIT.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_SYNTHESIS.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_AUDIT.md
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_SYNTHESIS.md
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_BEHAVIOR_REPORT.md
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_FINDINGS.md
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_AUDIT.md
brain/development/processing_window.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/ui/session.py
brain/tick.py
brain/llm/client.py
brain/llm/ptcns_backed.py
lean_reference/TLICA.lean
lean_reference/TLICA/
tools/claude_helpers/campaign_state.py
tools/claude_helpers/gate_runner.py
tools/check_all.sh
```

Then read whichever files the next campaign step names.

---

## Phase 3.21 architectural guardrails

Preserve these constraints throughout Phase 3.21:

```text
no consciousness / sentience / subjective / semantic / truth /
  agency / self-modification / introspection / metacognition /
  desire / will / belief / understanding claim
no claim that ToyI "develops" or "matures" in the psychological
  sense (operational use only — never psychological)
no aggregate consciousness / sentience / awareness / I-ness /
  growth / maturity / capability score
no SelfModel implementation
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no model-backed default behavior; OFFLINE remains the default
no hidden LLM calls
no silent network/model calls
no silent repair calls
no DB schema change
no SCHEMA_VERSION bump
no persistence / autosave runtime change
no tick semantic change (brain/tick.py untouched)
no L1 cache semantic change
no L2 (eval_v1) semantic change
no parser change
no prompt change
no UI verb addition unless explicitly review-gated
no /save-session / /load-session / autosave extension
no raw prompts / responses / cache files / secrets committed
no Stage C.1 broad repo edits
no unbounded loops; no unbounded state growth
50 internal ticks remains the recommended high-window default;
  the runtime bound stays at PROCESSING_WINDOW_SIZE_MAX = 255
PASS / WARN / FAIL / NOT_APPLICABLE remain structural statuses
the TLICA Lean spec in lean_reference/ remains authoritative;
  any new catalog row must either bind to a Lean theorem or be
  marked as Engineering hypothesis, and must not contradict
  any existing REQUIRED row
```

Real model-call budget for the entire campaign:

```text
Max 20 real external model-backed calls total.
Phase 3.21 expects to consume ZERO real model calls because every
  milestone uses STREAM_APPEND only.
Stop before exceeding 20.
```

---

## ChatGPT/Codex consultation (Stage A, Stage B, and Stage C.1)

Same as Phase 3.20:

- Stage A (PR #13) read-only, advisory.
- Stage B (PR #15) limited-write, allowlist-based, sequential.
- Stage C.1 (PR #19) dynamic-flow, allowlist-based, max two active
  Codex nodes, no automatic retry, hard cap 8 nodes.
  **For Phase 3.21, max total Stage C.1 real Codex nodes = 5
  unless operator approves more.**

Same allowed-at / forbidden-at lists as Phase 3.20.

---

## Workflow tools

Same as Phase 3.20.

---

## Command rule

Use `python3 -m ...` for Python module commands. Do not run real
LLM scenario commands unless the user explicitly asks.

---

## Final report format (per step)

Same as Phase 3.20 (see Phase 3.19's CURRENT_MISSION.md for the
template; preserved unchanged).
