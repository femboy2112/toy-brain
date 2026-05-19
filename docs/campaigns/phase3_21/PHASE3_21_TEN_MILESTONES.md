# PHASE3_21_TEN_MILESTONES.md

## Purpose

Bind each of the ten developmental milestones to an exact helper
signature, bounded inputs, success criterion, primary metric,
secondary metric, summary text shape, and failure classification.
This document is the single source of truth for the Step 6
implementation; any divergence between it and Step 6 is a
campaign error.

The discipline of Step 2 holds: every milestone tests a
**structural marker only**; no psychological claim appears.
`PASS / WARN / FAIL / NOT_APPLICABLE` are structural status
labels only.

---

## 0. Common shape

Every milestone helper has signature:

```python
def run_m0N_<name>(*, seed_offset: int = 0) -> MilestoneResult: ...
```

`seed_offset` is a bounded non-negative int (default 0) that
shifts the per-milestone canonical input sequence by a documented
offset; it lets the static-audit fixture run each helper with two
different offsets to confirm determinism without coupling to the
default value.

Each helper:

- constructs its own fresh `OperatorSession(state=initial_state(), ...)`;
- dispatches the milestone's canonical input sequence through the
  public `STREAM_APPEND` path;
- inspects the resulting `OperatorSession` (Pattern Ledger, stream
  history, Growth Ledger, optional Coherence Monitor report) to
  compute the milestone's primary and secondary metrics;
- runs `assert_state_invariants(session.state)`; on raise, returns
  `MilestoneStatus.FAIL` with the exception message in the summary;
- runs the canonical `_FORBIDDEN_NON_CLAIM_TERMS` audit over its
  own summary string before returning;
- returns a frozen `MilestoneResult` record.

All inputs are bounded printable text under `STREAM_TEXT_MAX_LEN`,
contain no `COGITO_ID`, and contain no forbidden non-claim term.

---

## 1. M01 — Reflexive baseline

```text
helper signature : run_m01_reflexive_baseline(*, seed_offset: int = 0) -> MilestoneResult
canonical input  : seed_text = "alpha-{seed_offset}" (single STREAM_APPEND)
config           : processing_window_size=0; feedback_mode=OFF
primary_metric   : stream chunk count (expected 1)
secondary_metric : pattern ledger entry count (expected 1)
success          : primary == 1 AND secondary == 1 AND seed entry's
                   recurrence_count == STREAM_PATTERN_RECURRENCE_MIN
                   AND assert_state_invariants green
summary shape    : "m01 reflexive_baseline chunks=1 entries=1 rec=<MIN>"
status           : PASS on all criteria; FAIL on any mismatch;
                   NOT_APPLICABLE only if the substrate refuses
                   STREAM_APPEND (which would be a regression)
```

## 2. M02 — Habituation

```text
helper signature : run_m02_habituation(*, seed_offset: int = 0) -> MilestoneResult
canonical input  : seed_text = "beta-{seed_offset}" (single STREAM_APPEND)
config           : processing_window_size=10; feedback_mode=OFF
primary_metric   : stream chunk count (expected 11 = 1 + N)
secondary_metric : seed entry recurrence_count after dispatch
                   (expected MIN + 10 = 11)
success          : primary == 1 + 10 AND
                   secondary == STREAM_PATTERN_RECURRENCE_MIN + 10 AND
                   pattern entry count == 1 AND saturation_state == OPEN
                   AND invariants green
summary shape    : "m02 habituation chunks=11 entries=1 rec=11 sat=open"
```

## 3. M03 — Recognition

```text
helper signature : run_m03_recognition(*, seed_offset: int = 0) -> MilestoneResult
canonical inputs : two STREAM_APPEND dispatches in order:
                   "gamma-{seed_offset}" then "delta-{seed_offset}"
config           : processing_window_size=0; feedback_mode=OFF
primary_metric   : pattern ledger entry count (expected 2)
secondary_metric : count of distinct pattern_ids among entries
                   (expected 2)
success          : primary == 2 AND secondary == 2 AND
                   stream chunk count == 2 AND invariants green
summary shape    : "m03 recognition chunks=2 entries=2 distinct_ids=2"
```

## 4. M04 — Rehearsal

```text
helper signature : run_m04_rehearsal(*, seed_offset: int = 0) -> MilestoneResult
canonical input  : seed_text = "epsilon-{seed_offset}"
config           : processing_window_size=10; feedback_mode=OFF
                   (same shape as M02 but tested as the substrate-
                    layer marker explicitly)
primary_metric   : count of chunks whose provenance suffix is
                   ":rehearsal" (expected 10)
secondary_metric : seed entry recurrence_count (expected MIN + 10)
success          : primary == 10 AND secondary == MIN + 10 AND
                   total chunks == 11 AND invariants green
summary shape    : "m04 rehearsal chunks=11 rehearsal_chunks=10 rec=11"
```

(M02 and M04 are deliberately overlapping shapes — M02 frames the
"recurrence climbs" marker, M04 frames the "internal-rehearsal
chunks present" marker. They are distinct rows because the
analogue framing is different.)

## 5. M05 — Pattern self-feedback

```text
helper signature : run_m05_pattern_self_feedback(*, seed_offset: int = 0) -> MilestoneResult
canonical input  : seed_text = "zeta-{seed_offset}"
config           : processing_window_size=10; feedback_mode=PATTERN_LEDGER
primary_metric   : count of chunks whose provenance suffix is
                   ":pledger_summary" (expected 10)
secondary_metric : pattern ledger entry count (expected >= 2)
success          : primary == 10 AND secondary >= 2 AND
                   total chunks == 1 + 2*10 == 21 AND
                   the sum over second-order entries of
                   (recurrence_count - MIN + 1) == 10 AND invariants
                   green
summary shape    : "m05 pattern_self_feedback chunks=21 pledger=10 entries>=2"
```

## 6. M06 — Structural self-monitoring approximation

```text
helper signature : run_m06_structural_self_monitoring(*, seed_offset: int = 0) -> MilestoneResult
canonical input  : seed_text = "eta-{seed_offset}"
config           : processing_window_size=10; feedback_mode=COHERENCE
primary_metric   : count of chunks whose provenance suffix is
                   ":cohmon_summary" (expected 10)
secondary_metric : pattern ledger entry count (expected >= 2)
success          : primary == 10 AND secondary >= 2 AND
                   total chunks == 1 + 2*10 == 21 AND
                   the sum over second-order entries with cohmon
                   evidence of (recurrence_count - MIN + 1) == 10 AND
                   the post-dispatch CoherenceReport overall_status
                   is in {"pass", "warn", "fail", "not_applicable"}
                   (closed set) AND invariants green
summary shape    : "m06 structural_self_monitoring chunks=21 cohmon=10 entries>=2"
```

## 7. M07 — Multi-modal integration

```text
helper signature : run_m07_multi_modal_integration(*, seed_offset: int = 0) -> MilestoneResult
canonical input  : seed_text = "theta-{seed_offset}"
config           : processing_window_size=10; feedback_mode=PATTERN_AND_COHERENCE
primary_metric   : total stream chunk count (expected 1 + 3*10 == 31)
secondary_metric : pattern ledger entry count (expected >= 3)
success          : primary == 31 AND secondary >= 3 AND
                   pledger_summary count == 10 AND cohmon_summary
                   count == 10 AND rehearsal count == 10 AND
                   pledger and cohmon families are disjoint
                   pattern_id sets AND both family observation sums
                   equal 10 AND invariants green
summary shape    : "m07 multi_modal_integration chunks=31 entries>=3"
```

## 8. M08 — Saturation + novelty

```text
helper signature : run_m08_saturation_novelty(*, seed_offset: int = 0) -> MilestoneResult
canonical inputs : two STREAM_APPEND dispatches in order:
                   "iota-{seed_offset}" with processing_window_size=255
                     feedback_mode=OFF
                   then a distinct text "kappa-{seed_offset}" with
                     processing_window_size=0 feedback_mode=OFF
config           : per-dispatch as above (single session)
primary_metric   : seed (iota) entry's saturation_state value
                   (expected "saturated")
secondary_metric : pattern ledger entry count after the second
                   dispatch (expected 2 — the saturated entry
                   plus the new distinct entry)
success          : primary == "saturated" AND secondary == 2 AND
                   first entry recurrence_count == STREAM_PATTERN_RECURRENCE_MAX
                   AND second entry recurrence_count == MIN AND
                   invariants green
summary shape    : "m08 saturation_novelty seed_sat=saturated entries=2"
```

## 9. M09 — Cross-input differentiation under feedback

```text
helper signature : run_m09_cross_input_differentiation(*, seed_offset: int = 0) -> MilestoneResult
canonical inputs : two STREAM_APPEND dispatches in order on the
                   same OperatorSession:
                   "lambda-{seed_offset}" with N=10 PATTERN_AND_COHERENCE
                   then "mu-{seed_offset}" with N=10 PATTERN_AND_COHERENCE
config           : per-dispatch as above
primary_metric   : pattern ledger entry count after second
                   dispatch (expected >= 4 — two seed entries +
                   each input's second-order families)
secondary_metric : count of distinct pattern_ids across all entries
                   (expected == primary_metric — no collisions)
success          : primary >= 4 AND secondary == primary AND
                   total stream chunks == 2 * (1 + 3*10) == 62
                   AND invariants green
summary shape    : "m09 cross_input_differentiation chunks=62 entries>=4 distinct=match"
```

## 10. M10 — Sustained complex behavior

```text
helper signature : run_m10_sustained_behavior(*, seed_offset: int = 0) -> MilestoneResult
canonical inputs : three STREAM_APPEND dispatches in order on the
                   same OperatorSession, each with N=50
                   PATTERN_AND_COHERENCE:
                   "nu-{seed_offset}"
                   "xi-{seed_offset}"
                   "omicron-{seed_offset}"
config           : per-dispatch as above
primary_metric   : stored stream chunk count observed in
                   stream_history.chunks (BOUNDED by
                   STREAM_HISTORY_MAX_CHUNKS = 256). Expected
                   dispatched = 3 * (1 + 3*50) = 453; expected
                   stored = min(453, STREAM_HISTORY_MAX_CHUNKS) = 256.
                   The bounded saturation IS the correct sustained-
                   load behavior; the history correctly retains the
                   N most recent chunks without eviction beyond the
                   documented bound.
secondary_metric : growth ledger event count (bounded at
                   GROWTH_LEDGER_MAX_EVENTS = 256; expected to be
                   256 because three N=50 dispatches generate well
                   past 256 events).
success          : primary == min(3 * (1 + 3*50), STREAM_HISTORY_MAX_CHUNKS)
                   AND secondary <= GROWTH_LEDGER_MAX_EVENTS
                   AND invariants green after every dispatch
                   AND pattern ledger entry count >= 3 (one seed
                   per distinct input).
summary shape    : "m10 sustained_behavior chunks=<n>/256 growth=<n>/256 entries=<n>"
status           : PASS on all criteria. The substrate-bounded
                   saturation behavior is a correctness property,
                   not a WARN — both stream_history and growth_ledger
                   are documented to cap at 256 without eviction.
```

---

## 11. Aggregator

```python
def run_all_milestones() -> tuple[MilestoneResult, ...]:
    return (
        run_m01_reflexive_baseline(),
        run_m02_habituation(),
        run_m03_recognition(),
        run_m04_rehearsal(),
        run_m05_pattern_self_feedback(),
        run_m06_structural_self_monitoring(),
        run_m07_multi_modal_integration(),
        run_m08_saturation_novelty(),
        run_m09_cross_input_differentiation(),
        run_m10_sustained_behavior(),
    )
```

The function is pure deterministic over its (empty) input set.
Bit-identical across two invocations.

---

## 12. MilestoneResult record

```python
@dataclass(frozen=True, slots=True)
class MilestoneResult:
    milestone: DevelopmentalMilestone        # closed enum, 10 members
    status: MilestoneStatus                  # closed enum, 4 members
    summary: str                             # bounded printable, non-claim-clean,
                                             # len <= MILESTONE_SUMMARY_MAX_LEN = 240
    primary_metric: int                      # bounded; non-negative
    secondary_metric: int                    # bounded; non-negative
```

Constructor enforces:

- `milestone` is a `DevelopmentalMilestone` member;
- `status` is a `MilestoneStatus` member;
- `summary` is a non-empty bounded printable str, not equal to
  `COGITO_ID`, length `<= MILESTONE_SUMMARY_MAX_LEN`;
- `primary_metric` and `secondary_metric` are non-negative ints
  (not bool).

---

## 13. Closed enums

```python
class DevelopmentalMilestone(str, Enum):
    M01_REFLEXIVE_BASELINE = "m01_reflexive_baseline"
    M02_HABITUATION = "m02_habituation"
    M03_RECOGNITION = "m03_recognition"
    M04_REHEARSAL = "m04_rehearsal"
    M05_PATTERN_SELF_FEEDBACK = "m05_pattern_self_feedback"
    M06_STRUCTURAL_SELF_MONITORING = "m06_structural_self_monitoring"
    M07_MULTI_MODAL_INTEGRATION = "m07_multi_modal_integration"
    M08_SATURATION_NOVELTY = "m08_saturation_novelty"
    M09_CROSS_INPUT_DIFFERENTIATION = "m09_cross_input_differentiation"
    M10_SUSTAINED_BEHAVIOR = "m10_sustained_behavior"


class MilestoneStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
```

---

## 14. v1 acceptance condition

```text
run_all_milestones() returns ten MilestoneResult records.
The v1 acceptance condition is:
  - status == MilestoneStatus.PASS for every member;
  - cumulative real model calls = 0;
  - cumulative L1/L2 cache writes = 0;
  - assert_state_invariants(state) green after every milestone;
  - the canonical _FORBIDDEN_NON_CLAIM_TERMS audit returns zero
    hits on every produced summary string.

Any FAIL halts the campaign at Step 7. Any WARN must be
documented in PHASE3_21_MILESTONE_LOG.md with a justification
(see Step 3 corrigenda LOCK J).
```

---

## 15. Disclosure block

```text
Stage A ChatGPT/Codex consultation: not used
Stage B limited-write collaboration: not used
Stage C.1 flow orchestration: not used
```

---

## 16. Next artifact

`docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CORRIGENDA.md`
— the Step 3 design locks (LOCK A through LOCK K).
