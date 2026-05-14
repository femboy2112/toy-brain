"""Catalog registry + runner.

Each fixture module under ``brain.fixtures`` registers checks via
``@register(row_id, status='REQUIRED')`` decorators. The runner walks the
registry, runs each check inside a try/except, and prints a structured
pass/fail table grouped by module.

The runner also performs:
  - the import-graph audit for I-PCE-05 (via ``brain._import_audit``;
    corrigenda C2 keeps ``brain/`` free of any ``tools/`` runtime dep),
  - a STRUCTURAL builder smoke-test: any ``ValueError`` raised at
    fixture-module import time bubbles up before per-row checks run, per
    catalog §"Validation procedure".

@register order is irrelevant (M10): output sorts by row ID.

CLI:
    python -m brain.invariants run [--json] [--strict] [--module M]
                                   [--id PREFIX]
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from brain._import_audit import audit_agency_no_pce_import

# v0 fixture modules. Importing each one populates ``REGISTRY`` via the
# @register decorator. The list mirrors the catalog's fixture roster.
FIXTURE_MODULES: list[str] = [
    "brain.fixtures.minimal",
    "brain.fixtures.cogito_invariants",
    "brain.fixtures.content_classification",
    "brain.fixtures.profile_distance",
    "brain.fixtures.mode_a_dispatch",
    "brain.fixtures.mode_c_dispatch",
    "brain.fixtures.neutral_encapsulation",
    "brain.fixtures.action_selection",
    "brain.fixtures.projected_pce",
    "brain.fixtures.affect_kernel_collapse",
    "brain.fixtures.trajectory_step",
]


@dataclass(frozen=True, slots=True)
class InvariantSpec:
    """A single registered runtime check."""

    id: str
    fixture_module: str
    status: str
    runner: Callable[[], None]


REGISTRY: list[InvariantSpec] = []


def register(row_id: str, *, status: str = "REQUIRED") -> Callable[[Callable[[], None]], Callable[[], None]]:
    """Decorator: attach a fixture's check function to the catalog row.

    The check function takes no arguments and either returns ``None``
    (pass) or raises (fail).
    """

    def _decorate(fn: Callable[[], None]) -> Callable[[], None]:
        REGISTRY.append(
            InvariantSpec(
                id=row_id,
                fixture_module=fn.__module__,
                status=status,
                runner=fn,
            )
        )
        return fn

    return _decorate


@dataclass
class RunResult:
    spec: InvariantSpec
    passed: bool
    detail: str = ""


@dataclass
class RunReport:
    structural_errors: list[tuple[str, str]] = field(default_factory=list)
    audit_message: str = ""
    audit_passed: bool = True
    rows: list[RunResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        if self.structural_errors:
            return False
        if not self.audit_passed:
            return False
        return all(r.passed for r in self.rows)

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            key_pass = f"{r.spec.status}/pass" if r.passed else f"{r.spec.status}/fail"
            out[key_pass] = out.get(key_pass, 0) + 1
        return out


def _import_fixtures(report: RunReport) -> None:
    """Import every fixture module; collect ValueError at import time."""
    for mod in FIXTURE_MODULES:
        try:
            importlib.import_module(mod)
        except ValueError as exc:
            report.structural_errors.append(
                (mod, f"STRUCTURAL builder check failed: {exc}")
            )
        except ModuleNotFoundError as exc:
            # A fixture file may not exist yet during incremental
            # development. Surface it but do not crash; the row-level
            # checks will simply be missing.
            report.structural_errors.append((mod, f"module not found: {exc}"))


def run(
    *,
    module_filter: str | None = None,
    id_prefix: str | None = None,
) -> RunReport:
    report = RunReport()

    ok, msg = audit_agency_no_pce_import()
    report.audit_message = msg
    report.audit_passed = ok

    _import_fixtures(report)

    for spec in sorted(REGISTRY, key=lambda s: s.id):
        if module_filter and module_filter not in spec.fixture_module:
            continue
        if id_prefix and not spec.id.startswith(id_prefix):
            continue
        try:
            spec.runner()
        except Exception as exc:  # noqa: BLE001 — runner records every failure
            tb = traceback.format_exception_only(type(exc), exc)
            report.rows.append(
                RunResult(spec=spec, passed=False, detail="".join(tb).strip())
            )
        else:
            report.rows.append(RunResult(spec=spec, passed=True))

    return report


def _print_table(report: RunReport) -> None:
    by_module: dict[str, list[RunResult]] = {}
    for r in report.rows:
        by_module.setdefault(r.spec.fixture_module, []).append(r)
    for mod in sorted(by_module):
        print(f"\n[{mod}]")
        for r in sorted(by_module[mod], key=lambda x: x.spec.id):
            mark = "PASS" if r.passed else "FAIL"
            print(f"  {mark}  {r.spec.id:11s}  {r.spec.status}")
            if not r.passed:
                for line in r.detail.splitlines():
                    print(f"        {line}")

    print()
    if report.structural_errors:
        print("STRUCTURAL errors during fixture import:")
        for mod, msg in report.structural_errors:
            print(f"  {mod}: {msg}")
        print()
    print(report.audit_message)
    summary = report.summary()
    total_rows = len(report.rows)
    failed = sum(1 for r in report.rows if not r.passed)
    required_pass = summary.get("REQUIRED/pass", 0)
    required_fail = summary.get("REQUIRED/fail", 0)
    print(
        f"\n{total_rows} rows checked  ·  REQUIRED green: {required_pass} "
        f"·  REQUIRED red: {required_fail}  ·  total failed: {failed}"
    )


def _cmd_run(args: argparse.Namespace) -> int:
    report = run(module_filter=args.module, id_prefix=args.id)
    if args.json:
        payload: dict[str, Any] = {
            "structural_errors": [
                {"module": m, "message": msg} for m, msg in report.structural_errors
            ],
            "audit_passed": report.audit_passed,
            "audit_message": report.audit_message,
            "rows": [
                {
                    "id": r.spec.id,
                    "status": r.spec.status,
                    "fixture": r.spec.fixture_module,
                    "passed": r.passed,
                    "detail": r.detail,
                }
                for r in sorted(report.rows, key=lambda x: x.spec.id)
            ],
            "summary": report.summary(),
            "all_passed": report.all_passed,
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_table(report)

    if not report.all_passed:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brain.invariants")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run", help="Walk the registry; report pass/fail.")
    p_run.add_argument("--json", action="store_true")
    p_run.add_argument("--module", help="Restrict to fixtures matching this substring.")
    p_run.add_argument("--id", help="Restrict to row IDs with this prefix.")
    p_run.set_defaults(func=_cmd_run)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    # `python -m brain.invariants` loads this file as __main__, but fixture
    # modules import via the canonical name `brain.invariants`, so the
    # @register decorators populate that copy's REGISTRY, not __main__'s.
    # Defer to the canonical module to keep state coherent.
    import brain.invariants as _canonical
    sys.exit(_canonical.main())
