# CURRENT_CAMPAIGN.md — Phase 3.21 Developmental Trajectory

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.21 follows the completed Phase 3.20 Coherence Feedback Bridge
campaign (PR #25, open against `campaign/phase3-19-internal-feedback-loop`
at campaign start). Phase 3.21 asks one bounded operational question:

```text
Can ToyI's runtime exhibit a recognizable structural developmental
trajectory -- a deterministic sequence of bounded behaviors that
approximate, in operational terms only, ten distinct human-development
analogues -- using only the surfaces Phases 3.0 through 3.20 have
built, without touching brain/tick.py, the LLM, the parser, the cache,
the schema, or any consciousness-adjacent boundary?
```

This is a **research / architecture demonstration** campaign. It is
**not** a proof of consciousness, sentience, subjective experience,
agency, semantic understanding, truth, intent, will, desire,
introspection, metacognition, or psychological development.

Phase 3.21 does **not** implement SelfModel; does **not** modify
Growth Ledger / Pattern Ledger / Coherence Monitor semantics; does
**not** modify L1 / L2 / parser / prompt / tick / persistence /
autosave / DB schema. The runtime touches are limited to:

- A new helper module `brain/development/milestone_harness.py`
  that defines a closed `DevelopmentalMilestone` enumeration over
  ten distinct milestones and one pure deterministic helper per
  milestone. The module imports only from
  `brain.development.processing_window`,
  `brain.development.coherence_monitor`,
  `brain.development.text_stream`, `brain.tick` (BrainState +
  initial_state only — never the tick callable), and
  `brain.ui.session`. No LLM import, no curses, no I/O.
- `INVARIANT_CATALOG.md` v0.28 -> v0.29 with bounded new row
  family `I-DEVMILE-01..I-DEVMILE-11` (ten milestone rows +
  one static audit row — exact count fixed in Step 4).
- Eleven new fixtures under `brain/ui/fixtures/` (one per
  milestone + one static audit) OR one consolidated fixture
  file covering the milestone harness with eleven `@register`
  entries — exact shape fixed in Step 4.

Preferred campaign branch:

```text
campaign/phase3-21-developmental-trajectory
```

Preferred final PR title:

```text
phase3.21: developmental trajectory
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into the correct base (Phase 3.20 branch
  while PR #25 is open; main once both PR #24 and PR #25 merge)
never push campaign work directly to main
never merge without explicit user approval
never edit brain/tick.py in Phase 3.21
```

---

## Mandatory files to read

See `CURRENT_MISSION.md` "Required source files to read first".

---

## Baseline

Expected current state at campaign start (pre-Step-6):

```text
Catalog: v0.28
Counts:
  REQUIRED:        284
  STRUCTURAL:       91
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.20 Coherence Feedback Bridge
                              (PR #25 open against Phase 3.19 branch)
Current campaign:             Phase 3.21 Developmental Trajectory
Next eligible step:           Step 1 mission sync (in flight)
Canonical design seed:        PHASE3_21_DEVELOPMENTAL_TRAJECTORY_ROADMAP.md
```

Inherited follow-ups deliberately deferred:

```text
- SelfModel implementation remains OUT OF SCOPE.
- REPL / worldlet feedback remain DEFERRED.
- Real-model reflection over feedback events remains DEFERRED.
- /pattern-ledger / /coherence-summary / /growth-ledger UIs
  remain DEFERRED.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- Tracer wiring through OperatorSession.dispatch remains DEFERRED.
- Raising PROCESSING_WINDOW_SIZE_MAX above 255 remains OUT OF SCOPE.
- Any change to Coherence Monitor's check set, status enum, or
  source labels remains OUT OF SCOPE for v1 (carryover Phase 3.20
  LOCK E).
- Pattern Ledger structural-signature derivation remains
  unchanged.
```

---

## Operational target

Phase 3.21 uses this operational definition:

```text
The ten-milestone developmental trajectory WORKS iff:
  - The closed enum DevelopmentalMilestone has exactly ten
    members in the order:
        M01_REFLEXIVE_BASELINE
        M02_HABITUATION
        M03_RECOGNITION
        M04_REHEARSAL
        M05_PATTERN_SELF_FEEDBACK
        M06_STRUCTURAL_SELF_MONITORING
        M07_MULTI_MODAL_INTEGRATION
        M08_SATURATION_NOVELTY
        M09_CROSS_INPUT_DIFFERENTIATION
        M10_SUSTAINED_BEHAVIOR
  - Each milestone has a pure deterministic helper
    run_M0N_<name>(state, ...) -> MilestoneResult on
    brain/development/milestone_harness.py that returns a frozen
    bounded record describing the milestone's outcome.
  - Each MilestoneResult contains a closed-enum
    MilestoneStatus in {PASS, WARN, FAIL, NOT_APPLICABLE} and
    a bounded printable summary string.
  - Each milestone helper is bit-deterministic: two invocations
    with identical inputs produce identical MilestoneResult.
  - The full ten-milestone sequence run by run_all_milestones()
    completes without any FAIL outcome; every milestone is
    either PASS or WARN with a documented WARN reason.
  - Zero real model calls; brain/tick.py untouched; cache
    counters unchanged; no schema change; OFFLINE default
    preserved; canonical _FORBIDDEN_NON_CLAIM_TERMS audit
    passes on every produced summary string.
  - The new module's import set is closed and audited; no
    forbidden import appears.
  - The Lean spec in lean_reference/ is not contradicted: every
    new catalog row is marked as Engineering hypothesis and
    binds to an existing Python surface (no new Lean theorem is
    claimed).
```

---

## Real model call budget

```text
Max 20 real external model-backed calls total across the campaign.
Phase 3.21 expects to consume ZERO real model calls.
Stop before exceeding 20.
```

---

## Non-goals

Same hard-constraint list as `CURRENT_MISSION.md`.

---

## Macro sequence

```text
Step 1   Mission sync + roadmap
Step 2   Human-development synthesis
Step 3   Ten-milestone definition + corrigenda
Step 4   Catalog patch plan
Step 5   Review Gate B
Step 6   Implement milestone harness + fixtures
Step 7   Run all 10 milestones; record outcomes
Step 8   Behavior + findings report
Step 9   Final audit
Step 10  PR preparation
```

Every step that lands files must pass the standard preflight gates
before commit and must push the campaign branch on success.

---

## ChatGPT/Codex consultation policy

Same as Phase 3.20 (max 5 Stage C.1 nodes; never raw codex; same
forbidden surfaces).

---

# Step 1 — Mission sync + roadmap

Purpose: install Phase 3.21 as the current mission and land the
Phase 3.21 roadmap at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_21_DEVELOPMENTAL_TRAJECTORY_ROADMAP.md
PHASE3_HANDOFF_STATE.md
```

Forbidden in Step 1:

```text
brain/**
tools/**
.claude/**
INVARIANT_CATALOG.md
README.md
docs/campaigns/**
lean_reference/**
scenarios/**
traces/**
```

Required work: write Phase 3.21 mission / campaign / roadmap;
verify gate_runner --json green.

Commit message:

```text
phase3.21 step1: developmental trajectory mission sync
```

Push.

---

# Step 2 — Human-development synthesis

Create:

```text
docs/campaigns/phase3_21/PHASE3_21_HUMAN_DEVELOPMENT_SYNTHESIS.md
```

Deep analysis of human-development stages framed by *structural
markers only*. Specifically map ten well-studied human-development
stages / phenomena to the ten ToyI milestones, with the analogy
clearly bounded at the structural level. Cite the bounded markers
the runtime can deterministically demonstrate. Make the
non-claim discipline explicit at the top.

Commit message:

```text
phase3.21 step2: human-development synthesis
```

Push.

---

# Step 3 — Ten-milestone definition + corrigenda

Create:

```text
docs/campaigns/phase3_21/PHASE3_21_TEN_MILESTONES.md
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CORRIGENDA.md
```

Define each of the ten milestones in exact terms: human-development
analogue, ToyI structural marker, the bounded helper signature,
the bounded inputs, the success criterion, the failure
classification. Lock the design LOCK A through LOCK K (same
discipline as Phase 3.20).

Commit message:

```text
phase3.21 step3: ten milestones + corrigenda
```

Push.

---

# Step 4 — Catalog patch plan

Create:

```text
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CATALOG_PATCH_PLAN.md
```

Exact patch plan: catalog v0.28 -> v0.29; row family I-DEVMILE-01..11
(10 REQUIRED + 1 STRUCTURAL); exact fixture list; module
inventory; behavior plan; review-gate decision request.

Commit message:

```text
phase3.21 step4: developmental trajectory catalog patch plan
```

Push.

---

# Step 5 — Review Gate B

Apply autonomy authorization. Eleven conditions (same shape as
Phase 3.20 Review Gate A):

```text
 1. zero critical correctness blockers
 2. zero safety / invariant blockers
 3. no brain/tick.py edits
 4. preserves L1 / L2 cache semantics
 5. preserves parser and prompt semantics
 6. preserves OFFLINE default + explicit opt-in
 7. exact row family, statuses, count delta, fixture list,
    implementation files, validation plan
 8. bounded developmental-trajectory design (10 closed-enum
    milestones; bounded helpers; deterministic outcomes)
 9. no cognitive overclaims; no aggregate scalar
10. Stage A review identifies no blocking flaw
11. implementation fits allowed file set; stays within Lean spec
    (engineering hypothesis rows only)
```

If acceptable, record `Review Gate B — ACCEPT PLAN AS WRITTEN`
and proceed. If not acceptable, stop.

---

# Step 6 — Implement milestone harness + fixtures

Implement bounded deterministic milestone harness per the accepted
plan. Required properties:

```text
- closed DevelopmentalMilestone enum (10 members)
- closed MilestoneStatus enum (4 members)
- frozen / slotted MilestoneResult record
- pure deterministic per-milestone helper
- no tick.py change
- no real model calls
- provenance on every internal artifact
- closed import set on milestone_harness.py
- non-claim audit on every produced summary string
- tests for every milestone (one fixture per milestone or
  consolidated fixture per Step 4 plan)
- catalog v0.28 -> v0.29 landing
```

Commit message:

```text
phase3.21 step6: implement developmental trajectory harness
```

Push.

---

# Step 7 — Run all 10 milestones

Run `run_all_milestones()` against a fresh OperatorSession and
record the outcomes in:

```text
docs/campaigns/phase3_21/PHASE3_21_MILESTONE_LOG.md
```

This step does not change runtime code; it only records the live
behavior.

Commit message:

```text
phase3.21 step7: ten-milestone log
```

Push.

---

# Step 8 — Behavior + findings report

Create:

```text
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_BEHAVIOR_REPORT.md
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_FINDINGS.md
```

Cross-milestone aggregate behavior + findings triage.

Commit message:

```text
phase3.21 step8: behavior report + findings
```

Push.

---

# Step 9 — Final audit

Create:

```text
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_AUDIT.md
```

Same verdict options as Phase 3.20.

Commit message:

```text
phase3.21 step9: final developmental trajectory audit
```

Push.

---

# Step 10 — PR preparation

Open a PR with title:

```text
phase3.21: developmental trajectory
```

Base resolution: target `campaign/phase3-20-coherence-feedback-bridge`
while PR #25 remains open; retarget to `main` once both PR #24 and
PR #25 merge.

Do not merge.
