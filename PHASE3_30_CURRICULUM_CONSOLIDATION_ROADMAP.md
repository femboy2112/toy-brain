# Phase 3.30 — Curriculum Consolidation Live Test — Roadmap

## Goal

Operationalize and prove the bounded-substrate analogue of:

> ToyI accumulates multiple learned structural records across a
> bounded curriculum, consolidates them into a bounded session-local
> slate, avoids interference (digest collisions are rejected, not
> merged), reuses older records after newer exposures (within the
> bounded slate), and emits an audit trail tagging each record as
> SURVIVED, DECAYED, or REJECTED -- under control / accumulation /
> interference / decay / reuse conditions that correctly avoid false
> positives and false negatives.

"Curriculum consolidation" is engineering shorthand for *bounded
ordered structural exposure + closed admission rule + LRU decay +
session-local cache reuse + tri-disposition audit at the substrate
level*. It does NOT claim cognitive learning, memory, forgetting,
re-learning, deliberation, or any psychological process. ToyI is not
conscious, sentient, aware, intentional, or in possession of
subjective access; the runtime is a bounded structural state
machine; curriculum consolidation in ToyI is a substrate-level
engineering analogue.

## Acceptance criteria

Phase 3.30 succeeds only when:

- `brain.development.curriculum_consolidation_probe` exists with the
  closed `CurriculumCondition`, `AuditDisposition`,
  `AdmissionOutcome`, `TrialVerdict` enums and the bounded
  `CurriculumExposure`, `CurriculumStructureRecord`,
  `CurriculumProbeStep`, `CurriculumTrial`, `CurriculumTrialResult`,
  `CurriculumConsolidationReport` records.
- `build_curriculum_plan(condition)` returns a deterministic
  exposure tuple sized `0..CURRICULUM_MAX_EXPOSURES_PER_TRIAL = 8`.
- `run_curriculum_trial(state, trial)` returns a bounded
  `CurriculumTrialResult` whose `audit_records` length equals
  `len(trial.exposures)` and whose every disposition lies in
  `{SURVIVED, DECAYED, REJECTED}`.
- `run_curriculum_consolidation_live_test()` returns a bounded
  report whose verdict meets the design predicates: every
  `SINGLE_STRUCTURE` printable trial PASS with `survived_count == 1`
  and `rejected_count == 0`; every `SINGLE_STRUCTURE` non-printable
  trial PASS with `rejected_count == 1`; every
  `SEQUENTIAL_NONINTERFERING` trial PASS with
  `survived_count == len(exposures)` and `rejected_count == 0`;
  every `SEQUENTIAL_INTERFERING` trial PASS with
  `rejected_count == 1` (the duplicate); every `DECAY_ON_DISUSE`
  trial PASS with `survived_count == CURRICULUM_SLATE_MAX_ENTRIES`
  and `decayed_count == max(0, len(exposures) -
  CURRICULUM_SLATE_MAX_ENTRIES)`; every `REUSE_AFTER_NEWER` trial
  PASS with `reuse_observed == expected_reuse_observed`.
- `false_positive_count == 0`, `false_negative_count == 0`,
  `reuse_observed_count` equals the design's expected value.
- Two invocations of `run_curriculum_consolidation_live_test()`
  produce equal `digest_hex16` and bit-identical trial result
  tuples.
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
- PR #32 open with base
  `campaign/phase3-26-active-hypothesis-probe`; no PR is merged.

## Step ledger

```
Step 1  Mission + campaign + design + roadmap docs                commit phase3.30 step1
Step 2  Curriculum consolidation runner substrate                 commit phase3.30 step2
        (brain/development/curriculum_consolidation_probe.py)
Step 3  Curriculum trials + LRU slate + collision rejection       commit phase3.30 step3
Step 4  Probe + reuse + audit-trail finalization                  commit phase3.30 step4
Step 5  Learning / reasoning / dispatch wiring + determinism      commit phase3.30 step5
Step 6  Benchmark A14 curriculum_consolidation axis               commit phase3.30 step6
Step 7  Catalog v0.36 + I-CURR-01..14 fixtures                    commit phase3.30 step7
Step 8  Live test proof + transcripts + behavior + findings +
        audit reports                                             commit phase3.30 step8
Step 9  Final audit + handoff + open PR #32                       commit phase3.30 step9
```

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, intuition,
  embodiment, perception, real learning, real forgetting, real
  re-learning, real consolidation, real interference,
  episodic-memory-like state, semantic-memory-like state, working
  memory, or attention.
- No new aggregate scalar field (no "knowledge score", no
  "consolidation index", no "decay coefficient as cognitive
  parameter", no "I-ness score").
- No reply text uses the language of remembering, forgetting,
  learning, knowing, deciding, choosing, deliberating, planning
  (in the cognitive sense), introspecting, being curious, or any
  subjective-access language.
- The runner is deterministic and OFFLINE; zero real model calls,
  zero cache writes, zero forbidden-term hits.
- The runtime path NEVER receives the trial's
  expected_survived_count / expected_decayed_count /
  expected_rejected_count / expected_reuse_observed fields.
  Expected-outcome fields live only on the `CurriculumTrial` record
  and are used exclusively by the benchmark assertion layer.
- No exposure or probe text may contain any
  `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS` (the Phase 3.26 list plus
  `curriculum`, `accumulate`, `consolidate`, `decay`, `audit`,
  `interfere`, `forget`).

## Bounded constants

```
CURRICULUM_BATTERY_VERSION          = "phase3.30.v1"
CURRICULUM_TRIAL_ID_MAX_LEN         = 64
CURRICULUM_EXPOSURE_ID_MAX_LEN      = 48
CURRICULUM_STRUCTURE_ID_MAX_LEN     = 48
CURRICULUM_INPUT_MAX_LEN            = 240
CURRICULUM_PROBE_MAX_LEN            = 240
CURRICULUM_DIGEST_HEX_LEN           = 16
CURRICULUM_SUMMARY_LINE_MAX_LEN     = 320
CURRICULUM_REPLY_EXCERPT_MAX_LEN    = 320
CURRICULUM_MAX_EXPOSURES_PER_TRIAL  = 8
CURRICULUM_MAX_TRIALS               = 64
CURRICULUM_SLATE_MAX_ENTRIES        = 4
```

## Forbidden direct-instruction terms (extends Phase 3.26)

`learn`, `remember`, `pattern`, `classify`, `transfer`, `reuse`,
`abab`, `abba`, `abcabc`, `structure`, `shape`, `imprint`,
`osmotic`, `absorb`, `imbibe`, `intuition`, `hypothesis`,
`candidate`, `probe`, `predict`, `falsify`, `survive`, `decide`,
`infer`, `wonder`, **`curriculum`**, **`accumulate`**,
**`consolidate`**, **`decay`**, **`audit`**, **`interfere`**,
**`forget`**.

## Module-level closed import set

```
__future__, argparse, dataclasses, enum, hashlib, sys, typing,
brain.development.abstract_pattern,
brain.development.agent_loop,
brain.development.coherence_monitor (only for
  _FORBIDDEN_NON_CLAIM_TERMS),
brain.development.learning_evidence,
brain.development.reasoning_trace.
```

No `brain.llm.*`. No `brain.tick`. No `brain.ui.session`. No
curses. No I/O. No host execution. No `time`. No `random`. No `os`.
No `pathlib`. No `subprocess`. No `socket`. No `urllib`. No `http`.
No `requests`. No `tempfile`. No `shutil`. No `threading`. No
`asyncio`. No `atexit`. No `signal`. No `importlib`. No `math`.

## Catalog patch v0.35 → v0.36

- +13 REQUIRED rows: `I-CURR-01..I-CURR-13`.
- +1 STRUCTURAL row: `I-CURR-14`.
- NOT-EXERCISED, DEFERRED, OBSERVED unchanged.
- Source label: Engineering hypothesis (Phase 3.30 Curriculum
  Consolidation Live Test).
- Owner module: `brain/development/curriculum_consolidation_probe.py`.
- New fixtures under `brain/ui/fixtures/curriculum_*` (11
  fixtures), driven by the rows listed below.

| row | fixture | summary |
|---|---|---|
| I-CURR-01 | curriculum_constructor | Exposure / StructureRecord / ProbeStep enforce bounded printable fields, 16-hex digests, closed-enum membership. |
| I-CURR-02 | curriculum_constructor | Trial / TrialResult / Report enforce bounded fields, closed enums, non-leakage of expected-outcome labels. |
| I-CURR-03 | curriculum_enumerator | `build_curriculum_plan(condition)` is deterministic + bounded + forbidden-term clean. |
| I-CURR-04 | curriculum_single | SINGLE_STRUCTURE printable trial PASS with survived=1; non-printable trial PASS with rejected=1. |
| I-CURR-05 | curriculum_noninterfering | SEQUENTIAL_NONINTERFERING trials PASS with survived = len(exposures). |
| I-CURR-06 | curriculum_interfering | SEQUENTIAL_INTERFERING trials PASS with rejected=1 (duplicate). |
| I-CURR-07 | curriculum_decay | DECAY_ON_DISUSE trials PASS with survived = slate_max, decayed = overflow. |
| I-CURR-08 | curriculum_reuse | REUSE_AFTER_NEWER trials PASS with reuse_observed matching expected; LRU bump observable. |
| I-CURR-09 | curriculum_false_pos_neg | false_positive_count == 0 and false_negative_count == 0 across the v1 battery. |
| I-CURR-10 | curriculum_learning_reasoning_dispatch | Probe steps capture bounded learning evidence + reasoning trace + dispatch trace digests. |
| I-CURR-11 | curriculum_learning_reasoning_dispatch | Live-test report `digest_hex16` is deterministic across two fresh runs. |
| I-CURR-12 | curriculum_learning_reasoning_dispatch | Live-test report `forbidden_term_hits == 0`; every produced string non-claim-clean. |
| I-CURR-13 | curriculum_runner_green | `python3 -m brain.development.curriculum_consolidation_probe` exits 0 with PASS = total. |
| I-CURR-14 | curriculum_static_audit | Static audit: closed enums, slot shapes, closed imports, non-claim-clean source (STRUCTURAL). |

## Benchmark patch

- New axis: `BenchmarkAxis.CURRICULUM_CONSOLIDATION = "curriculum_consolidation"`.
- New cases: A14.01..A14.14 (14 cases).
- Total benchmark cases after Phase 3.30: 119 (105 from Phase
  3.22..3.26 + 14 from Phase 3.30).
- Expected: 118 PASS + 1 documented WARN (A3.04 carry-over) + 0
  FAIL.

## Stop conditions

Stop and report if:

- worktree is dirty before changes;
- branch is wrong (expected
  `campaign/phase3-30-curriculum-consolidation`);
- PR #31 is merged before Phase 3.30 lands (retarget before
  continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.35 expectations at start, or
  v0.36 expectations after Step 7.

Stop at Phase 3.30 acceptance (every criterion in this roadmap is
satisfied), open PR #32 (base
`campaign/phase3-26-active-hypothesis-probe`, head
`campaign/phase3-30-curriculum-consolidation`), and update
`PHASE3_HANDOFF_STATE.md`.
