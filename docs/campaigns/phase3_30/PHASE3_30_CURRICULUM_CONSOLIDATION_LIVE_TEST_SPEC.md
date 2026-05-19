# Phase 3.30 — Curriculum Consolidation Live Test — Spec (v1)

This document pins the v1 contract of the curriculum consolidation
live-test runner that lands in
`brain/development/curriculum_consolidation_probe.py`. The spec is
the lightweight companion to
`docs/campaigns/phase3_30/PHASE3_30_CURRICULUM_CONSOLIDATION_TEST_DESIGN.md`.

## Module location

```
brain/development/curriculum_consolidation_probe.py
```

## Public surface

```python
BATTERY_VERSION                       = "phase3.30.v1"
CURRICULUM_SLATE_MAX_ENTRIES          = 4
CURRICULUM_MAX_EXPOSURES_PER_TRIAL    = 8
CURRICULUM_MAX_TRIALS                 = 64
CURRICULUM_INPUT_MAX_LEN              = 240
CURRICULUM_PROBE_MAX_LEN              = 240
CURRICULUM_DIGEST_HEX_LEN             = 16

class CurriculumCondition(str, Enum):
    SINGLE_STRUCTURE
    SEQUENTIAL_NONINTERFERING
    SEQUENTIAL_INTERFERING
    DECAY_ON_DISUSE
    REUSE_AFTER_NEWER

class AuditDisposition(str, Enum):
    SURVIVED
    DECAYED
    REJECTED

class AdmissionOutcome(str, Enum):
    ADMITTED
    REJECTED_COLLISION
    REJECTED_NONPRINTABLE

class TrialVerdict(str, Enum):
    PASS / WARN / FAIL / NOT_APPLICABLE

@dataclass(frozen=True, slots=True)
class CurriculumExposure:               # 2 fields
class CurriculumStructureRecord:        # 5 fields
class CurriculumProbeStep:              # 9 fields
class CurriculumTrial:                  # 9 fields
class CurriculumTrialResult:            # 15 fields
class CurriculumConsolidationReport:    # 17 fields

def build_curriculum_plan(condition) -> tuple[CurriculumExposure, ...]
def build_curriculum_trials()         -> tuple[CurriculumTrial, ...]
def run_curriculum_trial(trial)        -> CurriculumTrialResult
def run_curriculum_consolidation_live_test() -> CurriculumConsolidationReport
def format_curriculum_consolidation_report(report) -> str
def curriculum_consolidation_digest(report) -> str
def main(argv=None) -> int
```

## Closed import set

```
__future__, argparse, dataclasses, enum, hashlib, sys, typing
brain.development.abstract_pattern         (derive_abstract_pattern_signature)
brain.development.agent_loop               (AgentLoopState, make_initial_*, run_agent_interaction_step)
brain.development.coherence_monitor        (_FORBIDDEN_NON_CLAIM_TERMS)
brain.development.learning_evidence        (LearningEvidenceTrace)
brain.development.reasoning_trace          (build_reasoning_trace_report)
```

No `brain.llm.*`, no `brain.tick`, no `brain.ui.session`, no
curses, no host execution, no `time`, no `random`, no `os` /
`pathlib` / `subprocess` / `socket` / `urllib` / `http` /
`requests` / `tempfile` / `shutil` / `threading` / `asyncio` /
`atexit` / `signal` / `importlib` / `math`.

## v1 trial battery (ten trials)

| trial_id | condition | exposures | probe | exp_survived | exp_decayed | exp_rejected | exp_reuse |
|---|---|---|---|---|---|---|---|
| T01_single_printable    | SINGLE_STRUCTURE          | (E_AB,)                  | -      | 1 | 0 | 0 | False |
| T02_single_singleton    | SINGLE_STRUCTURE          | (E_SINGLETON,)           | -      | 0 | 0 | 1 | False |
| T03_seq_distinct_2      | SEQUENTIAL_NONINTERFERING | (E_AB, E_AA)             | -      | 2 | 0 | 0 | False |
| T04_seq_distinct_3      | SEQUENTIAL_NONINTERFERING | (E_AB, E_AA, E_ABC)      | -      | 3 | 0 | 0 | False |
| T05_collision_pair      | SEQUENTIAL_INTERFERING    | (E_AB, E_AB)             | -      | 1 | 0 | 1 | False |
| T06_collision_in_3      | SEQUENTIAL_INTERFERING    | (E_AB, E_AA, E_AB)       | -      | 2 | 0 | 1 | False |
| T07_decay_overflow_5    | DECAY_ON_DISUSE           | 5 distinct-shape         | -      | 4 | 1 | 0 | False |
| T08_decay_overflow_6    | DECAY_ON_DISUSE           | 6 distinct-shape         | -      | 4 | 2 | 0 | False |
| T09_reuse_oldest        | REUSE_AFTER_NEWER         | (E_AB, E_AA, E_ABC)      | E_AB   | 3 | 0 | 0 | True  |
| T10_reuse_negative      | REUSE_AFTER_NEWER         | (E_AB, E_AA, E_ABC)      | E_AAB  | 3 | 0 | 0 | False |

Aggregate v1 expected: `false_positive_count==0`,
`false_negative_count==0`, `total_survived_count==23`,
`total_decayed_count==3`, `total_rejected_count==3`,
`reuse_observed_count==1`, `digest_hex16=="9412acec1163b978"`.

## Canonical exposure pool

| id | input_text | shape | classification | digest |
|---|---|---|---|---|
| E_AB     | `alpha beta`               | A B     | all-distinct      | 457c99dd93973d27 |
| E_AA     | `gamma gamma`              | A A     | repeated          | a996ad3d8bdc5e3b |
| E_ABC    | `delta epsilon zeta`       | A B C   | all-distinct      | 9bb2ad079f553a05 |
| E_AAB    | `eta eta theta`            | A A B   | partial-recurring | e8cfe826475e7d96 |
| E_ABA    | `iota kappa iota`          | A B A   | partial-recurring | 9dfde01c9a4cfc38 |
| E_ABB    | `mu nu nu`                 | A B B   | partial-recurring | 81e8ce9bc640c0b0 |
| E_ABCD   | `rho sigma tau upsilon`    | A B C D | all-distinct      | (reserved)       |
| E_ABAB   | `phi chi phi chi`          | A B A B | recurring-form    | (reserved)       |
| E_SINGLETON | `psi`                   | A       | singleton         | 8b0635ab66676036 |
| E_EMPTY  | ``                         | (empty) | empty             | (synthetic key)  |

## Admission rule

```
classify_admission(input_text):
    sig = derive_abstract_pattern_signature(input_text)
    if not sig.valid:                          return REJECTED_NONPRINTABLE
    if sig.classification in {empty, singleton, overlong, non-printable, too-many-tokens}:
        return REJECTED_NONPRINTABLE
    if sig.digest in {entry.digest for entry in slate}:
        return REJECTED_COLLISION
    return ADMITTED
```

LRU eviction on overflow: pop `slate[0]` (insertion order is
adjusted by the probe-time bump), mark its exposure DECAYED, then
append the new admitted record.

## Probe rule

```
on probe:
    sig = derive_abstract_pattern_signature(probe_input)
    for entry in slate:
        if entry.digest == sig.digest:
            entry.last_access_step = step_index   # bump LRU
            return reuse_observed=True, reused_id=entry.structure_id
    return reuse_observed=False, reused_id=""
```

The probe **never** admits a new entry, even when no match is
found.

## Determinism

`run_curriculum_consolidation_live_test()` is deterministic across
two invocations. Two fresh runs produce bit-identical
`CurriculumConsolidationReport.digest_hex16 == "9412acec1163b978"`
and bit-identical `trials` tuples.

## Anti-cheating discipline

- The runtime path never receives `expected_survived_count`,
  `expected_decayed_count`, `expected_rejected_count`, or
  `expected_reuse_observed`. These are used **only** by the
  benchmark assertion layer after the runner returns.
- Exposure and probe texts contain no forbidden direct-instruction
  term.
- Module-produced strings contain no `_FORBIDDEN_NON_CLAIM_TERMS`
  substring.
- The slate is a per-trial in-memory list. No cross-trial state
  leaks.

## Falsification conditions

The claim is falsified if any of the following holds (see test
design §Falsification for the full list):

- `build_curriculum_plan(condition)` is non-deterministic.
- A `SEQUENTIAL_INTERFERING` trial overwrites the first occurrence
  on collision.
- A `DECAY_ON_DISUSE` trial evicts the wrong entry or the wrong
  count.
- A `REUSE_AFTER_NEWER` probe matching a slate digest returns
  `reuse_observed=False`.
- The report digest is non-deterministic across two fresh runs.
- Any module-produced string contains a forbidden non-claim term.

The v1 battery exhibits **none** of these failure modes.
