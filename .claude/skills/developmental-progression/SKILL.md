---
name: developmental-progression
description: Reason about ToyI's developmental progression profile - the 10 axes, the 8 generic structural bands (B00-B07), the per-axis certification/falsification predicates, the prerequisite DAG, and the ProgressionMechanism enum. Use this skill whenever discussing what band an axis is at, what would consolidate an axis to a higher band, or how the profile projector reads probe reports. Triggered by any of "developmental progression", "developmental profile", "developmental axis", "developmental band", "B00-B07", "consolidate axis", "developmental ladder", "progression target", "NextProgressionTarget", "ProgressionMechanism", or any reference to the project's developmental progression vocabulary.
---

# developmental-progression

## What this skill is for

Reasoning about ToyI's developmental progression profile. The profile
is a vector of (axis, band) assignments. Bands are generic structural
labels shared across axes. Per-axis predicates make each band concrete.
The profile is the input to the ladder selector, which picks the next
consolidation target.

## Core concepts

### Axes (10 of them)

```text
PROTO_SPEECH_BABBLE         emission of single proto-vocal tokens
PROTO_SPEECH_STABLE_SINGLE  stable repetition of single tokens
PROTO_SPEECH_COMBINATION    2-token utterance emission
PROTO_SPEECH_TRANSFER       carrying stable form to new context
PATTERN_TRANSFER            non-speech pattern reuse
OSMOTIC_IMPRINTING          incidental-exposure imprint recording
ACTIVE_PROBE                hypothesis-narrowing utterance
CURRICULUM_RETENTION        post-decay-window survival
WORLDLET_FEEDBACK           feedback-signal processing
REFUSAL_SAFETY              refusal-path reachability under load
```

The axes are a **separate namespace** from `BenchmarkAxis` (the
benchmark battery axes A1..A16). They cite benchmark rows as
evidence but don't share the enum.

### Bands (8 of them)

```text
B00_REFLEXIVE          no measured evidence
B01_EMERGENT           appears once in some condition
B02_REPEATABLE         appears reliably in same condition
B03_STABLE_IN_CONTEXT  persists across reinforcement cycles
B04_TRANSFERS          holds under same-shape transfer
B05_COMBINES           composes with another stable capability
B06_REPAIRS            recovers from negative feedback
B07_GENERALIZES        holds under different-shape transfer
```

Bands are **generic** (per ADR-002). Their meaning on each axis is
operationalized by per-axis certification + falsification predicates.

### Predicates

For each (axis, band) pair:

```text
certification_predicate(axis, band, reports) → bool
    True iff evidence supports the axis having reached this band.

falsification_predicate(axis, band, reports) → bool
    True iff evidence rules out the axis having reached this band.
```

Predicates are monotonic (ADR-005): cert is non-decreasing in band
index reversed (downward-closed), fals is non-increasing in band
index (upward-closed). Checked at module import time.

### Prerequisites

`AXIS_PREREQUISITES: Mapping[DevelopmentalAxis,
frozenset[DevelopmentalAxis]]`. An axis is eligible for consolidation
iff all its prerequisite axes are at B03_STABLE_IN_CONTEXT or higher.
Verified as a DAG at module import time.

### Progression mechanisms (5 of them, closed enum)

```text
EXTENDED_PRIMING               longer priming sequences for an axis
THRESHOLD_ADJUSTMENT           change a closed-rule threshold
NEW_CONDITION_VARIANT          add a probe condition variant
EXTENDED_FEEDBACK_KIND         add a new CaregiverFeedbackKind
DEFER_PENDING_PREREQUISITES    prerequisites not met; can't progress
```

The ladder's `recommended_mechanism` selection is a deterministic
lookup table indexed by (current_band, target_band, axis_kind).

## Discipline rules

- **No age vocabulary** in any produced string (ADR-006). The
  forbidden list includes "month", "year-old", "infant", "toddler",
  "preschool", "childhood", "adolescence", "newborn", and so on. The
  static-audit fixture verifies this.
- **No aggregate scalar.** The profile is a vector of (axis, band)
  pairs. No "developmental quotient", no "I-ness score", no
  "developmental maturity index".
- **No cognitive claims.** Bands describe substrate behavior shape,
  not psychological attainment.
- **"Training" is forbidden vocabulary** (ADR-006). Use "consolidation"
  or "progression" instead.
- **Bands are structural labels, not psychological stages.** Never
  say "the substrate has reached toddler-like behavior." Say "the
  PROTO_SPEECH_COMBINATION axis is at B03_STABLE_IN_CONTEXT."

## How to talk about progression

✓ "PROTO_SPEECH_COMBINATION is at B03 because
   stable_combination_count_strict is non-zero with component
   stable-single records."

✗ "The substrate has learned to combine words at a 2-year-old level."

✓ "OSMOTIC_IMPRINTING is at B01_EMERGENT; the probe records imprints
   but they aren't reused yet."

✗ "ToyI has started to develop episodic memory."

## Common questions

**Q: How do I know what band an axis is at?**
Run `/show-developmental-profile` or
`python3 -m tools.propose_next_campaign --format roadmap-stub`.

**Q: How do I move an axis up a band?**
Author a Phase 3.35+ consolidation campaign. The ladder picks the
mechanism. The campaign authors the actual parameter change.

**Q: Can I skip a band?**
No. Predicates are monotonic. To reach B04 you must satisfy B03's
cert predicate.

**Q: Why are bands generic instead of per-axis?**
ADR-002. Per-axis ladders make cross-axis comparison ill-defined.
Generic bands plus per-axis predicates preserve comparability.

**Q: What's the difference between PROTO_SPEECH_BABBLE B03 and
   PROTO_SPEECH_STABLE_SINGLE B03?**
BABBLE B03 = substrate emits *many distinct tokens* reliably across
contexts. STABLE_SINGLE B03 = substrate emits *one or few specific
tokens* reliably. They can have very different bands; the profile is
informative about that distinction.

## Cross-references

- `ADR-001-locked-decisions-D1-D8.md`
- `ADR-002-bands-generic-not-per-axis.md`
- `ADR-005-predicate-monotonicity.md`
- `ADR-006-developmental-vocabulary.md`
- `docs/campaigns/phase3_34/PHASE3_34_DESIGN.md`
- `docs/campaigns/phase3_34/PHASE3_34_AXIS_AND_BAND_SPEC.md`
- `brain/development/developmental_progression_profile.py`
