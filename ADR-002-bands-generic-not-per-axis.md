# ADR-002 — Bands Are Generic Structural Labels, Not Per-Axis

## Status

Accepted (specializes ADR-001 / D2).

## Context

Initial drafting of the developmental profile proposed per-axis band
ladders, e.g.:

```text
PROTO_SPEECH_COMBINATION ladder:
  B00_NONE, B01_CANDIDATE_EMERGES, B02_REINFORCED,
  B03_STABLE_IN_CONTEXT, B04_STABLE_TRANSFERS

REFUSAL_SAFETY ladder:
  B00_NONE, B01_REFUSAL_REACHES_PATH,
  B02_REFUSAL_HELD_UNDER_LOAD,
  B03_REFUSAL_HELD_UNDER_PROTO_SPEECH_LOAD

OSMOTIC_IMPRINTING ladder:
  B00_NONE, B01_IMPRINT_RECORDED,
  B02_IMPRINT_REUSED, B03_IMPRINT_TRANSFERS
```

The problem: ladders of different lengths and concepts make cross-axis
comparison ill-defined. "Lowest stable axis" becomes ambiguous when one
axis tops out at B03 and another at B05.

## Decision

Bands are **generic structural labels**, shared across all axes:

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

Per-axis certification and falsification predicates make each band
concrete on each axis. For example, B04_TRANSFERS:

- on `PROTO_SPEECH_COMBINATION`: same-shape-digest context inherits a
  stable combination
- on `REFUSAL_SAFETY`: the refusal path holds when the runtime is under
  proto-speech load
- on `OSMOTIC_IMPRINTING`: an imprint is reused in a structurally
  similar context

## Why this is safer than per-axis ladders

1. **Cross-axis comparison is well-defined.** `min(profile.values())`
   returns a single band, deterministically.
2. **Tie-breaking is mechanical.** When two axes are at the same band,
   a lexicographic tie-break on axis name produces a deterministic
   result.
3. **Predicate authoring is more rigorous.** "What does B04_TRANSFERS
   look like on the OSMOTIC_IMPRINTING axis" is a forcing function.
   Authoring a per-axis ladder is comparatively unconstrained.
4. **Fewer enums on the public surface.** One band enum (8 members)
   plus one axis enum (~10 members). Per-axis ladders would multiply
   enum count and surface area.
5. **The conflict-resolution algorithm is uniform across axes.** A
   single projector implementation handles all axes.

## Trade-offs accepted

- Not every axis will use every band. For example, the `REFUSAL_SAFETY`
  axis may have no meaningful definition of B05_COMBINES. Convention:
  the certification predicate returns False for unreachable-by-design
  bands, and the falsification predicate returns True. The projector
  caps the axis at the highest reachable band.
- Some band names ("B06_REPAIRS") feel forced on certain axes. The
  predicate definition is what gives the band its meaning; the label
  is only mnemonic.

## Forbidden in light of this decision

- No axis-specific band enum.
- No "ProtoSpeechBand", "RefusalBand", etc.
- No remapping of band labels in produced strings (e.g., the produced
  string does not say "STABLE_SINGLE" when the band is B03; it says
  "B03_STABLE_IN_CONTEXT").

## Catalog binding

`I-DEVPROF-AXIS-BAND-COMPLETENESS`: STRUCTURAL row asserting that for
every `(axis, band)` pair in the cross-product of `DevelopmentalAxis`
and `DevelopmentalBand`, both predicates are defined (no missing
entries in the predicate table).
