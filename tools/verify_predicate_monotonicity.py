"""tools/verify_predicate_monotonicity.py — standalone predicate monotonicity checker.

Phase 3.34+ tool. Runs the import-time monotonicity check on the
predicate table without requiring a full test-suite run. Useful for
quick local verification while authoring predicates.

Usage:
    python3 -m tools.verify_predicate_monotonicity
    python3 -m tools.verify_predicate_monotonicity --verbose
    python3 -m tools.verify_predicate_monotonicity --axis AXIS_NAME

Exit codes:
    0  all predicates monotonic on all fixtures
    1  monotonicity violation found
    2  predicate table not yet importable (Phase 3.34 not landed)
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify predicate monotonicity on all fixtures.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-axis check progress.",
    )
    parser.add_argument(
        "--axis",
        help="Check only the named axis (default: all).",
    )
    parser.add_argument(
        "--fixture",
        help="Check only the named fixture (default: all).",
    )
    args = parser.parse_args(argv)

    try:
        from brain.development.developmental_progression_profile import (
            DevelopmentalAxis,
            DevelopmentalBand,
        )
        from brain.development.predicate_table import (
            PREDICATE_TABLE,
            PredicateMonotonicityError,
        )
    except ImportError as exc:
        print(
            "ERROR: brain.development.predicate_table is not importable.",
            file=sys.stderr,
        )
        print(f"  {exc}", file=sys.stderr)
        return 2

    # Collect fixtures.
    try:
        from brain.development.fixtures import predicate_monotonicity_basic
        fixtures_basic = predicate_monotonicity_basic.FIXTURES
    except ImportError:
        fixtures_basic = ()

    try:
        from brain.development.fixtures import (
            predicate_monotonicity_axis_independence,
        )
        fixtures_axis = (
            predicate_monotonicity_axis_independence.FIXTURES
        )
    except ImportError:
        fixtures_axis = ()

    try:
        from brain.development.fixtures import (
            predicate_monotonicity_boundary,
        )
        fixtures_boundary = predicate_monotonicity_boundary.FIXTURES
    except ImportError:
        fixtures_boundary = ()

    all_fixtures = [
        ("basic", fixtures_basic),
        ("axis_independence", fixtures_axis),
        ("boundary", fixtures_boundary),
    ]

    if args.fixture:
        all_fixtures = [
            (name, fxs) for name, fxs in all_fixtures
            if name == args.fixture
        ]
        if not all_fixtures:
            print(f"ERROR: no fixture named {args.fixture!r}", file=sys.stderr)
            return 2

    axes_to_check = list(DevelopmentalAxis)
    if args.axis:
        try:
            axes_to_check = [DevelopmentalAxis(args.axis)]
        except ValueError:
            print(f"ERROR: no axis named {args.axis!r}", file=sys.stderr)
            return 2

    bands = list(DevelopmentalBand)

    violations: list[str] = []
    checks = 0

    for fixture_set_name, fixtures in all_fixtures:
        for fixture_index, fixture in enumerate(fixtures):
            if args.verbose:
                print(
                    f"[{fixture_set_name}#{fixture_index}] "
                    f"checking {len(axes_to_check)} axes..."
                )
            for axis in axes_to_check:
                checks += 1
                try:
                    _check_axis_monotonicity(
                        axis, bands, fixture, PREDICATE_TABLE,
                    )
                except PredicateMonotonicityError as exc:
                    violations.append(
                        f"[{fixture_set_name}#{fixture_index}] "
                        f"{axis.value}: {exc}"
                    )

    if violations:
        print(
            f"FAIL: {len(violations)} monotonicity violation(s) across "
            f"{checks} (axis, fixture) checks:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print(
        f"OK: {checks} (axis, fixture) checks passed. Predicate table "
        f"is monotonic on all fixtures."
    )
    return 0


def _check_axis_monotonicity(axis, bands, fixture, table):
    """Raise PredicateMonotonicityError on any violation."""
    from brain.development.predicate_table import PredicateMonotonicityError

    cert_values = [table[(axis, b)][0](fixture) for b in bands]
    for i, v in enumerate(cert_values):
        if not v:
            for j in range(i + 1, len(cert_values)):
                if cert_values[j]:
                    raise PredicateMonotonicityError(
                        f"cert({bands[j].value}) is True but "
                        f"cert({bands[i].value}) is False"
                    )

    fals_values = [table[(axis, b)][1](fixture) for b in bands]
    for i, v in enumerate(fals_values):
        if v:
            for j in range(0, i):
                if not fals_values[j]:
                    raise PredicateMonotonicityError(
                        f"fals({bands[i].value}) is True but "
                        f"fals({bands[j].value}) is False"
                    )


if __name__ == "__main__":
    raise SystemExit(main())
