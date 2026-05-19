# Phase 3.30 — Curriculum Consolidation Live Test — Test Design

Curriculum consolidation is a bounded operational accumulation +
session-local-slate + decay + reuse effect over structural records,
not a psychological or phenomenological claim. "Curriculum" means an
ordered sequence of bounded structural exposures; "consolidation"
means closed-rule admission into a fixed-size session-local slate;
"decay" means closed-rule eviction under bounded slate pressure;
"reuse" means returning a cached prior admitted record on a later
probe; "audit trail" means a tuple of `CurriculumStructureRecord`
entries each tagged with a closed `AuditDisposition` value. None of
these terms claim cognitive learning, memory, forgetting,
re-learning, deliberation, or any psychological process.

## Operational definition

For the ToyI runtime, *curriculum consolidation* means:

> Given a bounded ordered tuple of structural exposures
> `E = (e_0, e_1, ..., e_{n-1})` and a bounded session-local slate
> capacity `CURRICULUM_SLATE_MAX_ENTRIES = 4`, the runtime processes
> each `e_i` in order through `run_agent_interaction_step` and tries
> to admit a `CurriculumStructureRecord` keyed on
> `derive_abstract_pattern_signature(e_i.input_text).digest_hex16`
> into a session-local in-memory slate `S`.
>
> Admission is governed by a closed deterministic rule:
>
>   - if `e_i.input_text` has classification in
>     `{empty, singleton, overlong, non-printable, too-many-tokens}`,
>     the record is `REJECTED_NONPRINTABLE` and never enters `S`;
>   - else if `S` already contains a record with the same
>     `source_digest_hex16`, the new record is
>     `REJECTED_COLLISION` and never enters `S`;
>   - else if `len(S) < CURRICULUM_SLATE_MAX_ENTRIES`, the record is
>     `ADMITTED` and appended to `S`;
>   - else (`len(S) == CURRICULUM_SLATE_MAX_ENTRIES`), the record
>     `S[0]` (the least-recently-accessed entry, by `last_access_step`
>     with insertion order as tiebreaker) is evicted with disposition
>     `DECAYED` and the new record is `ADMITTED` and appended to `S`.
>
> After processing the full curriculum, the runtime optionally probes
> a single bounded probe input. If
> `derive_abstract_pattern_signature(probe).digest_hex16` matches the
> `source_digest_hex16` of any record currently in `S`, that record's
> `last_access_step` is bumped, `reuse_observed = True`, and the
> probe's `CurriculumProbeStep` reports the prior admitted record's
> `structure_id`. Otherwise `reuse_observed = False` and the probe
> emits a single `CurriculumProbeStep` with no admitted-record link.
>
> The trial's `audit_records` tuple contains one
> `CurriculumStructureRecord` per exposure in the original
> exposure order. Each record's `disposition` is one of:
>
>   - `SURVIVED` -- still in `S` at end of curriculum (and after
>     optional probe);
>   - `DECAYED` -- was `ADMITTED` but evicted by the LRU rule;
>   - `REJECTED` -- never admitted (classification or collision).

The four sub-effects -- multi-structure accumulation, bounded slate
pressure with LRU decay, collision rejection, and probe-time reuse
of older admitted records -- are distinct and each is observable
from the bounded `CurriculumTrialResult` record.

## Positive evidence

- After a `SINGLE_STRUCTURE` curriculum with one printable
  unambiguous exposure, `survived_count == 1`, `decayed_count == 0`,
  `rejected_count == 0`.
- After a `SEQUENTIAL_NONINTERFERING` curriculum with two
  non-overlapping exposures (distinct digests, both within slate
  bound), `survived_count == 2`, `decayed_count == 0`,
  `rejected_count == 0`.
- After a `SEQUENTIAL_INTERFERING` curriculum where the second
  exposure has the same digest as the first, `survived_count == 1`,
  `decayed_count == 0`, `rejected_count == 1`. The first record
  survives; the duplicate is rejected on admission.
- After a `DECAY_ON_DISUSE` curriculum with five distinct exposures
  against `CURRICULUM_SLATE_MAX_ENTRIES == 4`, `survived_count == 4`,
  `decayed_count == 1`, `rejected_count == 0`. The earliest
  admitted record is evicted.
- After a `REUSE_AFTER_NEWER` curriculum with three distinct
  exposures (older first), followed by a probe matching the digest
  of the earliest exposure, `reuse_observed == True`,
  `probe_reused_structure_id` equals the earliest exposure's
  `structure_id`, and the earliest record's `last_access_step` is
  bumped past the more recent records.

## Negative evidence

- A `SINGLE_STRUCTURE` curriculum whose only exposure is empty /
  singleton / non-printable yields `survived_count == 0`,
  `decayed_count == 0`, `rejected_count == 1`.
- A `SEQUENTIAL_INTERFERING` curriculum's `rejected_count == 1`
  reflects the duplicate; the runner does NOT overwrite the first
  record or invent a merge.
- A `DECAY_ON_DISUSE` curriculum NEVER drops more entries than the
  excess; with five exposures and capacity four, exactly one is
  decayed.
- A `REUSE_AFTER_NEWER` probe whose digest matches none of the
  surviving records yields `reuse_observed == False`,
  `probe_reused_structure_id == ""`, and emits exactly one probe
  step (no fabricated reuse).
- The probe step NEVER admits a new structure even if the probe's
  digest is novel; admission is curriculum-phase only.

## Falsification

The curriculum-consolidation claim is falsified if:

- `build_curriculum_plan(condition)` returns a non-deterministic
  exposure tuple across two invocations on the same condition;
- a `SINGLE_STRUCTURE` trial yields `survived_count != 1` when its
  one exposure is printable and unique;
- a `SEQUENTIAL_NONINTERFERING` trial admits fewer than two
  records;
- a `SEQUENTIAL_INTERFERING` trial overwrites the first record or
  admits the duplicate;
- a `DECAY_ON_DISUSE` trial evicts the wrong record (not the
  least-recently-accessed) or evicts the wrong count;
- a `REUSE_AFTER_NEWER` probe of a surviving older record returns
  `reuse_observed == False`;
- the audit-trail `disposition` of any record drifts from the
  closed `AuditDisposition` enum;
- the live-test runner's `digest_hex16` is not deterministic
  across two fresh runs of
  `run_curriculum_consolidation_live_test()`;
- any produced string contains a `_FORBIDDEN_NON_CLAIM_TERMS`
  entry.

## Out of scope

- Real-time external-world signals (no perception, no embodiment).
- Persistence across sessions (Phase 3.30 is session-local; the
  slate is an in-memory tuple bound to the trial-runner caller).
- Model-backed curriculum generation (deterministic OFFLINE only;
  no LLM is consulted at any point).
- Multi-step probes (each trial has exactly zero or one probe).
- Adaptive curriculum scheduling (exposure order is a pure function
  of `condition`; it does NOT depend on prior trial outcomes).
- Cross-trial transfer (each trial owns its own slate; the slate
  does NOT survive trial boundaries).
- Real "forgetting curves" or "consolidation" in the
  psychological / neurological sense; the LRU eviction is a
  closed engineering rule.
- Cognitive interference / blocking / proactive or retroactive
  inhibition; "interference" here means *digest collision*.

## Anti-cheating discipline

- The **runtime path** (`run_agent_interaction_step` inside
  `run_curriculum_trial`) never receives the expected admission
  disposition, the expected survived/decayed/rejected counts, or
  the expected probe reuse flag as part of operator-input text.
  These live on the `CurriculumTrial` record and are used **only by
  the benchmark assertion layer** after the runner returns.
- The probe text is the trial's `probe_input` field verbatim; the
  runner does NOT synthesize a probe from the slate's contents.
- Exposure and probe texts MUST NOT contain any of the forbidden
  direct-instruction terms (Phase 3.26 list plus `curriculum`,
  `accumulate`, `consolidate`, `decay`, `audit`, `interfere`,
  `forget`).
- Exposure and probe texts MUST NOT contain any
  `_FORBIDDEN_NON_CLAIM_TERMS` substring.
- The admission and decay rules are a closed deterministic
  function of the slate and the incoming digest; no rule consults
  external state (no time, no random, no environment).

## Trial battery (10 trials)

| trial_id | condition | exposures (digests by canonical name) | probe | expected_survived | expected_decayed | expected_rejected | expected_reuse |
|---|---|---|---|---|---|---|---|
| `T01_single_printable`    | SINGLE_STRUCTURE          | `(alpha beta,)`                              | (none)               | 1 | 0 | 0 | False |
| `T02_single_singleton`    | SINGLE_STRUCTURE          | `(alpha,)` (classification `singleton`)      | (none)               | 0 | 0 | 1 | False |
| `T03_seq_distinct_2`      | SEQUENTIAL_NONINTERFERING | `(alpha beta, gamma delta)`                  | (none)               | 2 | 0 | 0 | False |
| `T04_seq_distinct_3`      | SEQUENTIAL_NONINTERFERING | `(alpha beta, gamma delta, epsilon zeta)`    | (none)               | 3 | 0 | 0 | False |
| `T05_collision_pair`      | SEQUENTIAL_INTERFERING    | `(alpha beta, alpha beta)`                   | (none)               | 1 | 0 | 1 | False |
| `T06_collision_in_3`      | SEQUENTIAL_INTERFERING    | `(alpha beta, gamma delta, alpha beta)`      | (none)               | 2 | 0 | 1 | False |
| `T07_decay_overflow_5`    | DECAY_ON_DISUSE           | five distinct two-token exposures            | (none)               | 4 | 1 | 0 | False |
| `T08_decay_overflow_6`    | DECAY_ON_DISUSE           | six distinct two-token exposures             | (none)               | 4 | 2 | 0 | False |
| `T09_reuse_oldest`        | REUSE_AFTER_NEWER         | three distinct two-token exposures           | `(first exposure)`   | 3 | 0 | 0 | True  |
| `T10_reuse_negative`      | REUSE_AFTER_NEWER         | three distinct two-token exposures           | `(novel two-token)`  | 3 | 0 | 0 | False |

Notes:

- Each exposure's `input_text` is a closed two-token printable
  string (e.g. `alpha beta`) with classification `all-distinct` or
  `repeated` per `derive_abstract_pattern_signature`. The runner
  selects exposures from a small frozen pool whose digests are
  computed once at module load.
- T02's `singleton` exposure rejects on classification, not on
  collision.
- T07 and T08 verify that the LRU eviction rule cleanly handles
  one and two overflow respectively.
- T09 probes the *first* exposure after two newer non-overlapping
  exposures; the trial verifies that the older record's
  `last_access_step` is updated.
- T10 probes a novel two-token input whose digest is not in the
  slate; the trial verifies no fabricated reuse.

## Verdict mapping

For each trial:

- `PASS` iff every observed predicate matches the expected:
  - `survived_count == expected_survived_count`;
  - `decayed_count == expected_decayed_count`;
  - `rejected_count == expected_rejected_count`;
  - `reuse_observed == expected_reuse_observed`;
  - each record's `disposition` value is in
    `{SURVIVED, DECAYED, REJECTED}`;
  - no forbidden non-claim term in the trial's probe reply or any
    bounded summary;
  - bounded structural records were emitted per design.
- `FAIL` if any observed predicate disagrees.
- `WARN` if a trial cannot be evaluated due to a runtime
  structural refusal (v1 design avoids this).
- `NOT_APPLICABLE` only if a trial is skipped by design (none in
  v1).

## Aggregate counters

`CurriculumConsolidationReport` exposes:

- `pass_count`, `warn_count`, `fail_count`, `not_applicable_count`,
- `false_positive_count` (probe reports reuse when none
  expected),
- `false_negative_count` (probe reports no reuse when reuse was
  expected),
- `total_survived_count`, `total_decayed_count`,
  `total_rejected_count` (summed across the battery),
- `reuse_observed_count` (probes that reported reuse).

For the v1 battery: `false_positive_count == 0`,
`false_negative_count == 0`, `total_survived_count == 23`,
`total_decayed_count == 3`, `total_rejected_count == 3`,
`reuse_observed_count == 1` (the committed Step 8 spec finalizes
these once the v1 enumerator is verified end-to-end in Steps 2-5).

## Determinism

Two invocations of `run_curriculum_consolidation_live_test()`
produce equal `CurriculumConsolidationReport.digest_hex16` and
bit-identical trial result tuples. The digest is computed as the
SHA-256 of the canonical serialization of each
`CurriculumTrialResult` in order (including each
`CurriculumStructureRecord`'s id, digest, disposition,
admitted_at_step, last_access_step, the probe step's digest and
reuse flag, the survived/decayed/rejected counts, and the trial
verdict).

## Resource discipline

- Zero real model calls.
- Zero cache writes (the in-memory slate is module-local and not
  the L1 / L2 LLM cache).
- Zero forbidden-term hits in any produced string.
- Zero invariant failures.
- No `brain.tick.tick` call outside the approved `STEP_TICK`
  route.

## Citation pipeline

Each trial's `CurriculumTrialResult` includes the bounded
reasoning trace digest, the bounded learning evidence trace
digest, and the bounded dispatch trace digests for the curriculum
exposure steps plus the optional probe step. These are captured
directly from the `AgentLoopResult` records.

## Naming discipline

The module-produced strings are audited against
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`.
The following technical labels are safe:

- `curriculum_consolidation`, `slate`, `admission`, `eviction`,
  `disposition`, `survived`, `decayed`, `rejected`, `reuse`,
  `accumulation`, `audit_trail` (these appear only in technical
  contexts; they are not in the forbidden non-claim list).

The forbidden direct-instruction list for OPERATOR-INPUT TEXTS
(exposure texts, probe texts) extends Phase 3.26's list with:

- `curriculum`, `accumulate`, `consolidate`, `decay`, `audit`,
  `interfere`, `forget`.

This prevents operator inputs from leaking the experimental
contract into the runtime path.

## Closed enums

```
class CurriculumCondition(str, Enum):
    SINGLE_STRUCTURE         = "single_structure"
    SEQUENTIAL_NONINTERFERING = "sequential_noninterfering"
    SEQUENTIAL_INTERFERING   = "sequential_interfering"
    DECAY_ON_DISUSE          = "decay_on_disuse"
    REUSE_AFTER_NEWER        = "reuse_after_newer"


class AuditDisposition(str, Enum):
    SURVIVED = "survived"
    DECAYED  = "decayed"
    REJECTED = "rejected"


class AdmissionOutcome(str, Enum):
    ADMITTED            = "admitted"
    REJECTED_COLLISION  = "rejected_collision"
    REJECTED_NONPRINTABLE = "rejected_nonprintable"


class TrialVerdict(str, Enum):
    PASS           = "pass"
    WARN           = "warn"
    FAIL           = "fail"
    NOT_APPLICABLE = "not_applicable"
```

## Frozen records

```
@dataclass(frozen=True, slots=True)
class CurriculumExposure:
    exposure_id: str          # bounded printable
    input_text: str           # bounded printable, forbidden-term clean

@dataclass(frozen=True, slots=True)
class CurriculumStructureRecord:
    structure_id: str         # bounded printable
    source_digest_hex16: str  # 16-hex
    admitted_at_step: int     # >= 0
    last_access_step: int     # >= admitted_at_step
    disposition: AuditDisposition

@dataclass(frozen=True, slots=True)
class CurriculumProbeStep:
    probe_input: str
    probe_digest_hex16: str
    reuse_observed: bool
    probe_reused_structure_id: str
    interaction_id: str
    dispatch_trace_digest: str
    reasoning_trace_digest: str
    reply_excerpt: str
    summary_line: str

@dataclass(frozen=True, slots=True)
class CurriculumTrial:
    trial_id: str
    condition: CurriculumCondition
    exposures: tuple[CurriculumExposure, ...]
    probe_input: str          # "" if no probe
    slate_max_entries: int    # == CURRICULUM_SLATE_MAX_ENTRIES
    expected_survived_count: int
    expected_decayed_count: int
    expected_rejected_count: int
    expected_reuse_observed: bool

@dataclass(frozen=True, slots=True)
class CurriculumTrialResult:
    trial_id: str
    condition: CurriculumCondition
    verdict: TrialVerdict
    audit_records: tuple[CurriculumStructureRecord, ...]
    probe_step: Optional[CurriculumProbeStep]
    survived_count: int
    decayed_count: int
    rejected_count: int
    reuse_observed: bool
    false_positive: bool
    false_negative: bool
    learning_evidence_digest: str
    reasoning_trace_digest: str
    dispatch_trace_digests: tuple[str, ...]
    summary_line: str

@dataclass(frozen=True, slots=True)
class CurriculumConsolidationReport:
    battery_version: str
    trials: tuple[CurriculumTrialResult, ...]
    pass_count: int
    warn_count: int
    fail_count: int
    not_applicable_count: int
    false_positive_count: int
    false_negative_count: int
    total_survived_count: int
    total_decayed_count: int
    total_rejected_count: int
    reuse_observed_count: int
    real_model_calls: int   # == 0
    cache_writes: int       # == 0
    forbidden_term_hits: int # == 0
    digest_hex16: str
    summary_line: str
```
