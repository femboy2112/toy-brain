# ADR-005 — Predicate Monotonicity as a Checked Invariant

## Status

Accepted (specializes ADR-001 / D6).

## Context

Phase 3.34 needs ~120 predicates: 10 axes × 6 non-trivial bands × 2
predicates (certification + falsification). Hand-authored predicates
at that scale will have authoring bugs. The bugs most likely to slip
past review:

1. A certification predicate that returns True for B05 but False for
   B03 (non-monotonic), making band assignment ambiguous.
2. A falsification predicate that returns True for B03 but False for
   B05 (non-monotonic in the other direction).
3. A predicate that depends on a probe report field that doesn't
   exist on every probe (raising AttributeError at runtime).
4. A predicate that returns a non-boolean value.

These are all caught by a single import-time check.

## Decision

The `predicate_table` module exposes a function:

```python
def verify_predicate_table_monotonicity(
    table: Mapping[
        tuple[DevelopmentalAxis, DevelopmentalBand],
        tuple[CertificationPredicate, FalsificationPredicate],
    ],
    probe_reports: Optional[tuple[ProbeReport, ...]] = None,
) -> None:
    """Raise PredicateMonotonicityError on any violation.

    Called at module import time with a small set of synthetic
    ProbeReport fixtures that exercise the boundary cases. If
    probe_reports is None, uses the canonical static fixtures.
    """
```

The checks performed:

1. **Completeness.** For every `(axis, band)` in the cross-product of
   `DevelopmentalAxis` and `DevelopmentalBand`, both predicates are
   defined. No `KeyError` on lookup.

2. **Type.** Both predicates return `bool` (not `int`, not `Optional[bool]`).

3. **Certification monotonicity per axis.** For each axis, if
   `cert(axis, B_n) == False` on a given fixture, then
   `cert(axis, B_m) == False` for all m > n on the same fixture.

4. **Falsification monotonicity per axis.** For each axis, if
   `fals(axis, B_n) == True` on a given fixture, then
   `fals(axis, B_m) == True` for all m < n on the same fixture.

5. **At-least-one-determines-band.** For each axis on each fixture,
   there exists at least one band `B_n` where `cert(axis, B_n) == True`
   and `fals(axis, B_{n+1}) == True`. (Or the axis is at B00.) This
   ensures the projector always terminates with a concrete assignment.

## Fixture set

A small set of canonical `ProbeReport` tuples that exercise:

- All zeros (`B00_REFLEXIVE` everywhere).
- A typical post-3.31 baseline (varying bands across axes).
- An all-strong fixture (axes near top of ladder).
- One fixture per axis with that axis maximally strong and others zero
  (exercises predicate independence).
- One fixture per condition designed to trip a specific non-monotonicity
  if the predicate is mis-authored.

Fixtures live in `brain/development/fixtures/predicate_monotonicity_*.py`.

## Why import-time

Calling `verify_predicate_table_monotonicity()` from the bottom of
`predicate_table.py` ensures any violation is caught when the module
is first imported, before any campaign runs. This is the cheapest
possible signal: if monotonicity is broken, the test suite fails to
even start.

The check runs on synthetic fixtures, not on real probe reports, so it
adds no I/O and no nondeterminism. Pure deterministic boolean logic.

## Catalog binding

- `I-DEVPROF-PREDICATE-MONOTONIC`: STRUCTURAL row asserting the four
  monotonicity rules hold on all fixtures.
- `I-DEVPROF-PREDICATE-COMPLETE`: STRUCTURAL row asserting every
  `(axis, band)` pair has both predicates defined.

## Authoring discipline

When adding or modifying a predicate:

1. Update the predicate in `predicate_table.py`.
2. If the change affects monotonicity on existing fixtures, the
   import-time check will fail and tell you exactly which fixture and
   which band pair.
3. If the change requires a new fixture (e.g., to exercise a
   boundary case that didn't exist before), add the fixture under
   `brain/development/fixtures/predicate_monotonicity_*.py`.
4. Run `python3 -m tools.verify_predicate_monotonicity` before
   committing.

## Forbidden

- Suppressing the import-time check ("disabled in dev").
- Predicates that are not pure functions of their input `ProbeReport`.
- Predicates that read mutable module state.
- Hand-waving "this predicate is monotonic, trust me" instead of
  running the check.
