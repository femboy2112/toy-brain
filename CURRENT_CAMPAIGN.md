# CURRENT_CAMPAIGN.md — Phase 3.30 Curriculum Consolidation Live Test

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.30 stacks on the completed Phase 3.26 work
(`campaign/phase3-26-active-hypothesis-probe`, PR #31 open). Phase
3.30 asks one bounded operational question:

```text
Under bounded live-test conditions, can the existing substrate
(abstract_pattern signature + learning evidence + reasoning trace
+ dispatch trace + worldlet feedback + Phase 3.25 osmotic
imprinting+activation surface + Phase 3.26 active-hypothesis
enumeration+falsification+caching surface) realize the operational
analogue of "curriculum consolidation"? That is: given a bounded
ordered tuple of structural exposures and a bounded session-local
slate capacity, can the runtime admit each exposure into the slate
under a closed admission rule, reject duplicates without
overwriting the first record, evict the least-recently-accessed
record once the slate capacity is exceeded, on a later probe whose
digest matches a surviving record return the prior admitted record
without re-admitting, decline to fabricate reuse for probes whose
digest is novel, and emit an audit trail tagging every exposure as
SURVIVED, DECAYED, or REJECTED -- while control / accumulation /
interference / decay / reuse conditions correctly avoid false
positives and false negatives?
```

This is a **research / integration / behavioral-benchmark**
campaign. It is **NOT** a proof of consciousness, sentience,
subjective experience, agency, semantic understanding, real
reasoning, real learning, real memory, real forgetting, real
consolidation, real curriculum learning (in the psychological
sense), intentionality, awareness, intuition, embodiment,
psychological development, or any cognitive process. "Curriculum
consolidation" is a controlled technical metaphor for *bounded
ordered structural exposure + closed admission rule + LRU decay +
session-local cache reuse + tri-disposition audit at the substrate
level*; it is engineering shorthand and does NOT claim
psychological learning, memory, forgetting, consolidation,
interference, attention, working memory, episodic memory, semantic
memory, or any cognitive process.

Phase 3.30 does **not** implement SelfModel; does **not** add any
new `OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry,
`ACTIVE_VIEWS` value, `GrowthEventType`, `GrowthEventSource`,
persistence schema column, autosave trigger, `LearningEvidenceKind`
member, or `ReasoningStepKind` member; does **not** change L1 / L2
/ parser / prompt / tick / persistence / autosave / DB schema
semantics. The runtime touches are limited to:

- **One new closed module**
  `brain/development/curriculum_consolidation_probe.py`
  (pure / deterministic / bounded). Closed import set: `__future__`,
  `argparse`, `dataclasses`, `enum`, `hashlib`, `sys`, `typing`,
  `brain.development.abstract_pattern`,
  `brain.development.agent_loop`,
  `brain.development.coherence_monitor` (only for
  `_FORBIDDEN_NON_CLAIM_TERMS`),
  `brain.development.learning_evidence`,
  `brain.development.reasoning_trace`. No `brain.llm.*`, no
  `brain.tick`, no `brain.ui.session`, no curses, no I/O, no host
  execution, no `time`, no `random`.
- **One new benchmark axis**
  `BenchmarkAxis.CURRICULUM_CONSOLIDATION` with the fourteen cases
  `A14.01..A14.14`. The full battery now runs A1..A14 (119 cases
  total = 105 from Phase 3.22 / 3.22b / 3.23 / 3.24 / 3.25 / 3.26
  + 14 from Phase 3.30).

Catalog patch: v0.35 → v0.36 with the bounded `I-CURR-01..14` row
family (Engineering hypothesis, Phase 3 source label). Split: 13
REQUIRED (I-CURR-01..13) + 1 STRUCTURAL (I-CURR-14). New fixtures
live under `brain/ui/fixtures/`.

Branch:

```text
campaign/phase3-30-curriculum-consolidation
```

Base: `campaign/phase3-26-active-hypothesis-probe` (PR #31).
Final PR (likely #32):
`phase3.30: curriculum consolidation live test`.

---

## Step ledger

```text
Step 1  Mission + design + roadmap docs                        commit phase3.30 step1
Step 2  Curriculum consolidation runner substrate              commit phase3.30 step2
        (brain/development/curriculum_consolidation_probe.py)
Step 3  Curriculum trials + LRU slate + collision rejection    commit phase3.30 step3
Step 4  Probe + reuse + audit-trail finalization               commit phase3.30 step4
Step 5  Learning / reasoning / dispatch wiring + determinism   commit phase3.30 step5
Step 6  Benchmark A14 curriculum_consolidation axis            commit phase3.30 step6
Step 7  Catalog v0.36 + I-CURR-01..14 fixtures                 commit phase3.30 step7
Step 8  Live test proof + transcripts + behavior +
        findings reports                                       commit phase3.30 step8
Step 9  Final audit + handoff + open PR #32                    commit phase3.30 step9
```

Push after every successful step.

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, intuition,
  embodiment, perception, real learning, real memory, real
  forgetting, real consolidation, real interference, real
  curriculum learning, working memory, episodic memory, semantic
  memory, or attention.
- No new aggregate scalar field (no "knowledge score", no
  "consolidation index", no "memory strength", no "decay
  coefficient as cognitive parameter", no "I-ness score").
- No reply text uses the language of remembering, forgetting,
  learning, knowing, deciding, choosing, deliberating, planning
  (in the cognitive sense), introspecting, being curious, wanting
  to consolidate, or any subjective-access language.
- The curriculum-consolidation runner is deterministic and
  OFFLINE; zero real model calls, zero cache writes, zero
  forbidden-term hits.
- The runtime path NEVER receives the trial's
  `expected_survived_count`, `expected_decayed_count`,
  `expected_rejected_count`, or `expected_reuse_observed` fields.
  Expected-outcome fields on the trial record are used ONLY by the
  benchmark assertion layer after the runtime path emits its
  result.
- No exposure text or probe text may contain any
  `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS` (the Phase 3.26 list plus
  `curriculum`, `accumulate`, `consolidate`, `decay`, `audit`,
  `interfere`, `forget`).

---

## Acceptance criteria

Phase 3.30 succeeds only when:

- `brain.development.curriculum_consolidation_probe` exists with
  the closed `CurriculumCondition`, `AuditDisposition`,
  `AdmissionOutcome`, `TrialVerdict` enums and the bounded
  `CurriculumExposure`, `CurriculumStructureRecord`,
  `CurriculumProbeStep`, `CurriculumTrial`,
  `CurriculumTrialResult`, `CurriculumConsolidationReport`
  records.
- `build_curriculum_plan(condition)` returns a deterministic
  exposure tuple sized `0..CURRICULUM_MAX_EXPOSURES_PER_TRIAL`.
- `run_curriculum_trial(state, trial)` returns a bounded
  `CurriculumTrialResult` whose `audit_records` length equals
  `len(trial.exposures)` and whose every disposition lies in
  `{SURVIVED, DECAYED, REJECTED}`.
- `run_curriculum_consolidation_live_test()` returns a bounded
  report meeting every design predicate from
  `PHASE3_30_CURRICULUM_CONSOLIDATION_ROADMAP.md`.
- `false_positive_count == 0`, `false_negative_count == 0`,
  `reuse_observed_count` equals the design's expected value.
- Two invocations produce equal `digest_hex16` and bit-identical
  trial result tuples.
- Benchmark A14 is green; existing A1..A13 axes do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.36 banner
  (REQUIRED 374, STRUCTURAL 100).
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5
  PASS.
- No new `brain.llm` import; no `brain.tick.tick` call outside the
  approved `STEP_TICK` route; no host execution; no DB schema
  change; no curses; no new `LearningEvidenceKind` member; no new
  `ReasoningStepKind` member.
- PR #32 is open with base
  `campaign/phase3-26-active-hypothesis-probe`; no PR is merged.
