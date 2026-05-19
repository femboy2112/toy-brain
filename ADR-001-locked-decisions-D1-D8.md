# ADR-001 — Locked Decisions D1–D8 for the Developmental Progression Track

## Status

Accepted. Do not relitigate inside a campaign. If new evidence demands
revisiting, open a successor ADR (ADR-007+) that explicitly supersedes the
specific decision.

## Context

After Phase 3.31 (caregiver-scaffolded proto-speech acquisition) landed,
planning revealed that the proto-speech probe reports
`stable_combination_count = 0` while passing all ten conditions because
the TWO_TOKEN_COMBINATION condition has a graceful-pass acceptance
(`CANDIDATE` / `REINFORCED` / `STABLE_COMBINATION` all pass). This means
the project has a *masked capability gap*: combinations emerge as 2-token
utterances but never cross the `STABLE_COMBINATION_THRESHOLD = 8`.

A natural reflex is to either (a) lower the threshold or (b) extend the
priming sequence until combinations stabilize, then build a developmental
profile on top. Both reflexes contaminate the measurement instrument
before the measurement happens. So the work is split across three
campaigns, with the eight decisions below locked before any of them
runs.

## Decisions

### D1 — Phase 3.33 is diagnostic-only

The Phase 3.33 corrigendum surfaces the masked combination gap and adds
a project-wide `_strict` counter discipline. **It does not change any
probe's test conditions.** Priming-length adjustments, threshold tuning,
and new condition variants are forbidden in 3.33. They are reserved for
Phase 3.35+ targeted consolidation campaigns, which run on the
already-honest baseline.

Rationale: the proto-speech runner is the measurement instrument for
the `PROTO_SPEECH_*` axes in Phase 3.34's profile. Changing the
instrument before reading from it makes the resulting profile
unable to distinguish "substrate improved" from "test got easier."

### D2 — Bands are GENERIC structural labels, shared across axes

```text
B00_REFLEXIVE          no measured evidence beyond a single-step trace
B01_EMERGENT           capability appears under at least one condition
B02_REPEATABLE         capability appears reliably under same condition
B03_STABLE_IN_CONTEXT  capability persists across repeated reinforcement
B04_TRANSFERS          capability holds under same-shape transfer
B05_COMBINES           composes with another stable capability
B06_REPAIRS            recovers from negative evidence / correction
B07_GENERALIZES        different-shape transfer or rule-guided extension
```

Per-axis certification and falsification predicates operationalize what
each band means for that specific axis. The axis namespace
`DevelopmentalAxis` and the band namespace `DevelopmentalBand` are
disjoint from `BenchmarkAxis` and `BenchmarkCaseStatus`; the profile
cites benchmark rows as evidence but does not reuse their enums.

Rationale: per-axis ladders break cross-axis comparison ("lowest axis"
becomes ill-defined when ladders are different lengths). Generic bands
plus per-axis predicates preserve comparability while keeping each
band's meaning concrete.

### D3 — Strict counter pattern is project-wide discipline

Every probe report whose live-test runner uses graceful-pass acceptance
exposes both `<metric>_count` (graceful) and `<metric>_count_strict`
(no graceful degradation). The strict count is the canonical input to
the Phase 3.34 profile projector.

Rationale: graceful-pass masking is unlikely to be unique to proto-speech.
Adding strict counters everywhere in 3.33 gives 3.34 a clean baseline
across all axes simultaneously. Cost: one audit pass plus mechanical
field additions.

### D4 — Phase 3.32 lands a ProbeReport protocol

Phase 3.32 is not just PR-stack merge plumbing. It also lands
`brain/development/probe_report_protocol.py`: a thin `typing.Protocol`
that every existing probe report already satisfies by name. No probe
module changes. The Phase 3.34 projector consumes the protocol, not
five distinct dataclasses.

Rationale: without a common interface, the projector's import set has
to widen to include every probe module, which couples the profile to
the probes' internal layout. The protocol decouples them.

### D5 — Regression gate uses TARGET_AXES / NON_TARGET_AXES scoping

```text
For every campaign:
  TARGET_AXES: explicit set declared in the roadmap (may be empty)
  NON_TARGET_AXES: every axis not in TARGET_AXES

Gate:
  for axis in NON_TARGET_AXES:
    observed_band(axis) >= prior_recorded_band(axis)

TARGET_AXES may move in either direction; the campaign's acceptance
criteria document the expected direction and magnitude.
```

For Phase 3.33: `TARGET_AXES = {PROTO_SPEECH_COMBINATION}` and the
expected direction is downward (B04 → B03 under strict counting) or
unchanged. Upward = catalog error.

For Phase 3.34: `TARGET_AXES = {}`. The profile projector cannot change
any band by construction; it just reports current bands. Any apparent
change = projector bug.

For Phase 3.35+: `TARGET_AXES = the campaign's specific target axis`.
Upward movement expected. No other axis may drop.

Rationale: a strict "any axis drop = fail" rule would block the 3.33
corrigendum (which legitimately re-rates the combination axis downward
under strict counting). Scoping the gate to non-target axes preserves
strictness where it matters.

### D6 — Predicate monotonicity is a checked invariant

For each `(axis, band)` pair, two predicates exist:
- `certification_predicate(axis, band)` — true if evidence supports the
  axis having reached this band.
- `falsification_predicate(axis, band)` — true if evidence rules out the
  axis having reached this band (or any higher band).

Design rules, checked at module import time:
1. `certification_predicate` is **monotonic non-decreasing in band
   index**: if `cert(axis, B_n)` is False, then `cert(axis, B_m)` is
   False for all m > n.
2. `falsification_predicate` is **monotonic non-increasing in band
   index**: if `fals(axis, B_n)` is True, then `fals(axis, B_m)` is
   True for all m < n.
3. For at least one band `B_n` per axis, neither predicate produces
   undefined / "unknown"; one of the two must determine band membership.

Catalog: `I-DEVPROF-PREDICATE-MONOTONIC` STRUCTURAL row.

Rationale: with ~120 predicates authored across 10 axes, manual review
is error-prone. The monotonicity check catches authoring bugs at
import time, before anything runs.

### D7 — NextProgressionTarget is a structured roadmap stub

The ladder's output is not just "axis X needs progression." It is:

```python
@dataclass(frozen=True, slots=True)
class NextProgressionTarget:
    axis: DevelopmentalAxis
    current_band: DevelopmentalBand
    target_band: DevelopmentalBand
    prerequisites_satisfied: tuple[DevelopmentalAxis, ...]
    prerequisites_missing: tuple[DevelopmentalAxis, ...]
    recommended_mechanism: ProgressionMechanism
    rationale_summary: str           # bounded, non-claim-clean
    cited_evidence_rows: tuple[str, ...]  # catalog row IDs
```

Where `ProgressionMechanism` is a closed enum:
```text
EXTENDED_PRIMING
THRESHOLD_ADJUSTMENT
NEW_CONDITION_VARIANT
EXTENDED_FEEDBACK_KIND
DEFER_PENDING_PREREQUISITES
```

The ladder plans. Humans (or Codex) author the actual roadmap from the
stub.

Rationale: a bare axis name is too thin to act on. A roadmap stub plus
recommended mechanism is enough that the next campaign's roadmap can
be authored mechanically.

### D8 — Benchmark axis A16 lands with Phase 3.34

```text
A16  developmental_progression_profile
  A16.01  profile digest matches a recorded expected digest
  A16.02  every band assignment cites at least one
          I-DEVPROF-* structural row
  A16.03  every produced string is non-claim-clean and
          contains no age-month vocabulary
```

Rationale: a single "digest stable across runs" case is trivial for a
deterministic projector. Adding (02) and (03) makes the axis a real
audit, not a smoke test.

## Forbidden in this track (carried over from project-wide rules)

- No claim of consciousness / sentience / awareness / subjective experience.
- No aggregate scalar (no I-ness score, fluency index, developmental
  quotient, mental age).
- No new `OperatorCommand` member, `ACTIVE_VIEWS` value, `GrowthEventType`,
  `GrowthEventSource`, `LearningEvidenceKind`, or `ReasoningStepKind`.
- No DB schema change, no autosave-policy change, no parser change, no
  prompt change.
- No `brain.llm` import in any new module.
- No `brain.tick.tick` call outside the existing `STEP_TICK` route.
- No `random`, `time`, or external nondeterministic source.
- Zero real model calls across the whole track.

## Consequences

- Three campaigns instead of one; each one frozen before the next begins.
- A clean separation of measurement instrument (probes), measurement
  (profile), and intervention (consolidation).
- Predicate authoring is the largest single piece of work and is fan-out-
  friendly to Codex.
