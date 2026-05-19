# ADR-004 — TARGET_AXES / NON_TARGET_AXES Regression Gate

## Status

Accepted (specializes ADR-001 / D5).

## Context

A naive regression rule for the developmental track would be:

> Any axis that drops a band between two consecutive campaigns fails
> the later campaign.

This is too strict. Phase 3.33's job is to make the
`PROTO_SPEECH_COMBINATION` axis honest — likely moving it from an
inflated B04 (under graceful counting) to B03 (under strict counting).
That **is** a band drop, but it's the intentional and correct outcome
of the campaign. A naive gate would fail Phase 3.33 by design.

## Decision

Every campaign declares an explicit `TARGET_AXES` set in its roadmap.
The regression gate applies only to axes **not** in that set:

```text
TARGET_AXES         the axes whose band the campaign expects to change
NON_TARGET_AXES     every axis not in TARGET_AXES

Gate:
  for axis in NON_TARGET_AXES:
    observed_band(axis) >= prior_recorded_band(axis)

TARGET_AXES may move in either direction. The campaign's acceptance
criteria document the expected direction and magnitude.
```

`prior_recorded_band(axis)` is the band assigned by Phase 3.34's
projector on the previous campaign's HEAD commit. It is stored as a
catalog-row-bound constant so it cannot drift quietly between campaigns.

## Phase-by-phase TARGET_AXES

```text
Phase 3.32  TARGET_AXES = {}
            All axes must stay green. 3.32 only reconciles branches
            and lands a thin protocol; no probe behavior changes.

Phase 3.33  TARGET_AXES = {PROTO_SPEECH_COMBINATION,
                          and any axis affected by the strictness
                          audit}
            Expected direction: downward or unchanged.
            Upward direction on any TARGET_AXES axis = catalog error.

Phase 3.34  TARGET_AXES = {}
            The projector is a pure consumer of probe outputs; no
            band may change as a result of profile construction.
            Any apparent change = projector bug.

Phase 3.35+ TARGET_AXES = {the campaign's specific target axis}
            Expected direction: upward.
            No other axis may drop.
```

## How "prior_recorded_band" is established

- Phase 3.34 builds the projector. After 3.34 lands, every axis has
  a recorded baseline band on every commit.
- For Phase 3.33, which runs **before** Phase 3.34, there is no
  recorded baseline. The gate for 3.33 is therefore **forward-only**:
  Phase 3.34 will retroactively check that 3.33's strict-counter
  effects produce the expected bands.
- This is acknowledged by the ADR. The gate has no power before the
  projector exists. Discipline is enforced by careful authoring of
  3.33's acceptance criteria, by the strict-counter WARN signal, and
  by the explicit declaration of TARGET_AXES in 3.33's roadmap.

## Why this is rigorous, not lax

- TARGET_AXES is declared in the roadmap **before the campaign runs**.
  You cannot retroactively widen TARGET_AXES to swallow an unexpected
  drop.
- TARGET_AXES being non-empty means the campaign has explicit
  permission to change bands, and the expected direction must be
  documented. Hidden movement is not permitted.
- The NON_TARGET_AXES gate is hard. Even one unintended band drop on
  a non-target axis fails the campaign.

## Catalog binding

- `I-DEVPROF-REGRESSION-GATE`: STRUCTURAL row asserting the gate is
  applied at every campaign boundary.
- `I-DEVPROF-BASELINE-RECORDED`: REQUIRED row asserting every axis has
  a recorded baseline at the head of every campaign branch.

## Forbidden

- Retroactively adding an axis to TARGET_AXES to make a campaign pass.
- Computing "prior_recorded_band" from anything other than the
  predecessor campaign's final commit.
- Skipping the gate "because the change is small."
