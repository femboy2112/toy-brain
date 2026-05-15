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

from brain._catalog_ids import EXPECTED_REQUIRED_IDS, EXPECTED_STRUCTURAL_IDS
from brain._import_audit import audit_agency_no_pce_import

# Catalog rows whose ``Fixture`` column is ``_meta`` are enforced by the
# runner itself rather than by a fixture function alone. They are still
# registered (so they appear in the summary) but their @register entries
# live in this module rather than under ``brain/fixtures/``.
_META_ROWS: frozenset[str] = frozenset({"I-CAT-01"})

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
    "brain.fixtures.llm_protocol",
    "brain.fixtures.scenario_v1",
    "brain.fixtures.trace_v1_1",
    "brain.development.fixtures.source_tag_audit",
    "brain.development.fixtures.recurrence_detection",
    "brain.development.fixtures.unstable_noise_rejection",
    "brain.development.fixtures.salience_is_not_truth",
    "brain.development.fixtures.focus_contact_protocol",
    "brain.development.fixtures.focus_stabilizes_or_dissolves",
    "brain.development.fixtures.proto_content_promotion",
    "brain.development.fixtures.output_echo",
    "brain.development.fixtures.output_pattern",
    "brain.development.fixtures.output_token_candidate",
    "brain.development.fixtures.worldlet_state",
    "brain.development.fixtures.worldlet_response",
    "brain.development.fixtures.worldlet_attempt",
    "brain.development.fixtures.worldlet_consequence",
    "brain.development.fixtures.repl_grammar",
    "brain.development.fixtures.repl_feedback",
    "brain.development.fixtures.repl_execution",
    "brain.development.fixtures.repl_history",
    "brain.ui.fixtures.snapshot_view",
    "brain.ui.fixtures.render_view",
    "brain.ui.fixtures.command_router",
    "brain.ui.fixtures.bottom_up_tick",
    "brain.ui.fixtures.tui_smoke",
    "brain.ui.fixtures.agent_layout",
    "brain.ui.fixtures.composer_input",
    "brain.ui.fixtures.transcript_log",
    "brain.ui.fixtures.agent_tui_smoke",
    "brain.development.fixtures.expression_source_enum_closed",
    "brain.development.fixtures.expression_item_bounded",
    "brain.development.fixtures.expression_feature_vector_exact",
    "brain.development.fixtures.expression_no_brainstate_mutation",
    "brain.development.fixtures.expression_no_source_history_mutation",
    "brain.development.fixtures.expression_static_audit",
    "brain.development.fixtures.readability_score_fraction_bounded",
    "brain.development.fixtures.readability_prediction_tagged",
    "brain.development.fixtures.readability_predictor_empty_item",
    "brain.development.fixtures.readability_predictor_repetition_only",
    "brain.development.fixtures.readability_predictor_length_cap",
    "brain.development.fixtures.readability_predictor_determinism",
    "brain.development.fixtures.expression_history_cow_bounded",
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
        # OBSERVED rows are reported but never gate the runner.
        return all(r.passed for r in self.rows if r.spec.status != "OBSERVED")

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            key_pass = f"{r.spec.status}/pass" if r.passed else f"{r.spec.status}/fail"
            out[key_pass] = out.get(key_pass, 0) + 1
        return out


def _audit_coverage() -> list[str]:
    """I-CAT-01: every REQUIRED / STRUCTURAL catalog row has a registered check.

    Returns a list of error messages; empty means coverage is complete.
    Called at runner entry (after all fixture imports) and again from the
    registered I-CAT-01 check so the row appears in the run summary.
    """
    registered = frozenset(s.id for s in REGISTRY)
    missing_required = EXPECTED_REQUIRED_IDS - registered
    missing_structural = EXPECTED_STRUCTURAL_IDS - registered
    errors: list[str] = []
    if missing_required:
        errors.append(
            "REQUIRED catalog rows missing registration: "
            f"{sorted(missing_required)}"
        )
    if missing_structural:
        errors.append(
            "STRUCTURAL catalog rows missing registration: "
            f"{sorted(missing_structural)}"
        )
    return errors


@register("I-CAT-01", status="STRUCTURAL")
def check_I_CAT_01() -> None:
    """Re-run the coverage audit. The hard fail at runner entry has
    already run; this registered check makes I-CAT-01 visible in the
    standard pass/fail summary.
    """
    errors = _audit_coverage()
    if errors:
        raise AssertionError("I-CAT-01 violated: " + "; ".join(errors))


# ---------------------------------------------------------------------------
# Phase 2 v1.2: explicit registrations for previously fixture-less STRUCTURAL
# rows. The I-CAT-01 audit caught these; making them registered checks brings
# the catalog into full coverage compliance.
# ---------------------------------------------------------------------------


@register("I-PCE-05", status="STRUCTURAL")
def check_I_PCE_05() -> None:
    """Action selection never reads foundation PCE.

    Positive case: the canonical ``agency.py`` audits clean. The runner
    already runs ``audit_agency_no_pce_import`` at startup; this
    registered check re-asserts it so the row appears in the pass/fail
    summary like every other STRUCTURAL row.

    Negative case (Phase 2 v1.2 corrigenda C1): the audit must catch
    ``from brain.tlica import pce`` — a form that previously slipped
    through because the walker only inspected ``node.module``.
    """
    ok, msg = audit_agency_no_pce_import()
    if not ok:
        raise AssertionError(f"I-PCE-05 violated: {msg}")

    import ast
    from brain._import_audit import _audit_pce_imports

    bad_tree = ast.parse(
        "from brain.tlica import pce\n"
        "def f():\n"
        "    return pce\n"
    )
    bad_ok, bad_msg = _audit_pce_imports(bad_tree, "synthetic_agency.py")
    assert not bad_ok, (
        "I-PCE-05 audit failed to reject `from brain.tlica import pce` "
        "(C1 regression check)"
    )
    assert "I-PCE-05" in bad_msg, (
        f"I-PCE-05 negative-case message lacks the row tag: {bad_msg!r}"
    )


@register("I-ISO-01", status="STRUCTURAL")
def check_I_ISO_01() -> None:
    """ProfileIso.refl(P) constructs successfully and reflects P."""
    from fractions import Fraction
    from brain.tlica.builders import make_profile_with_cogito
    from brain.tlica.profile import COGITO_ID
    from brain.tlica.profile_iso import ProfileIso

    P = make_profile_with_cogito({COGITO_ID: 1, "a": Fraction(1, 2)})
    iso = ProfileIso.refl(P)
    assert iso.lhs is P and iso.rhs is P, "ProfileIso.refl drift"


@register("I-ISO-02", status="STRUCTURAL")
def check_I_ISO_02() -> None:
    """ProfileIso.symm(h) flips lhs and rhs."""
    from fractions import Fraction
    from brain.tlica.builders import make_profile_with_cogito
    from brain.tlica.profile import COGITO_ID
    from brain.tlica.profile_iso import ProfileIso

    P = make_profile_with_cogito({COGITO_ID: 1, "a": Fraction(1, 2)})
    iso = ProfileIso.refl(P)
    flipped = iso.symm()
    assert flipped.lhs is iso.rhs and flipped.rhs is iso.lhs


@register("I-ISO-03", status="STRUCTURAL")
def check_I_ISO_03() -> None:
    """ProfileIso.trans(h1, h2) chains compatible isos."""
    from fractions import Fraction
    from brain.tlica.builders import make_profile_with_cogito
    from brain.tlica.profile import COGITO_ID
    from brain.tlica.profile_iso import ProfileIso

    P = make_profile_with_cogito({COGITO_ID: 1, "a": Fraction(1, 2)})
    h1 = ProfileIso.refl(P)
    h2 = ProfileIso.refl(P)
    chained = ProfileIso.trans(h1, h2)
    assert chained.lhs is P and chained.rhs is P


# ---------------------------------------------------------------------------
# Phase 3.1 Osmotic Chamber: pending row registrations.
#
# Step 1 of the campaign applies the accepted v0.6 catalog patch before the
# runtime developmental layer exists. These registrations keep I-CAT-01
# coverage coherent while making any attempted row execution fail explicitly.
# Later campaign steps replace these with real fixture-backed checks.
# ---------------------------------------------------------------------------


_PHASE3_1_PENDING_ROWS: dict[str, str] = {}


def _make_phase3_1_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.1 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_1_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_1_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.2 Output Ladder: pending row registrations.
#
# Step 6 applies the accepted v0.7 catalog patch before the output runtime
# layer exists. These registrations keep I-CAT-01 coverage coherent while
# making any attempted row execution fail explicitly. Later campaign steps
# replace these with real fixture-backed checks.
# ---------------------------------------------------------------------------


_PHASE3_2_PENDING_ROWS: dict[str, str] = {}


def _make_phase3_2_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.2 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_2_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_2_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.3 Minimal Worldlet: pending row registrations.
#
# Step 6 applies the accepted v0.8 catalog patch before the worldlet runtime
# layer exists. These registrations keep I-CAT-01 coverage coherent while
# making any attempted row execution fail explicitly. Later campaign steps
# replace these with real fixture-backed checks.
# ---------------------------------------------------------------------------


_PHASE3_3_PENDING_ROWS: dict[str, str] = {}


def _make_phase3_3_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.3 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_3_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_3_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.4 Proto-BASIC REPL: pending row registrations.
#
# Step 6 applies the accepted v0.9 catalog patch before the Proto-BASIC REPL
# runtime layer exists. These registrations keep I-CAT-01 coverage coherent
# while making any attempted row execution fail explicitly. Later campaign
# steps (Step 7, Step 8, Step 9) replace these with real fixture-backed
# checks. I-REPL-18 is OBSERVED and is not pending here; it does not
# participate in I-CAT-01 coverage and will be registered when its fixture
# lands.
# ---------------------------------------------------------------------------


_PHASE3_4_PENDING_ROWS: dict[str, str] = {
    # Step 7 landed I-REPL-01..10 and I-REPL-17 via
    # brain.development.fixtures.repl_grammar and
    # brain.development.fixtures.repl_feedback. Step 8 landed I-REPL-11..14
    # and I-REPL-16 via brain.development.fixtures.repl_execution and
    # brain.development.fixtures.repl_history. Step 9 landed I-REPL-15
    # (diminishing returns) via brain.development.fixtures.repl_history,
    # which also adds the OBSERVED I-REPL-18 summary check. No Proto-BASIC
    # REPL rows remain pending.
}


def _make_phase3_4_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.4 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_4_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_4_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Operator TUI: pending row registrations.
#
# Step 6 of the Operator TUI campaign applies the accepted v0.10 catalog patch
# before the operator UI runtime layer exists under brain/ui/. These pending
# registrations keep I-CAT-01 coverage coherent while making any attempted
# row execution fail explicitly. Step 7 (snapshots + renderer), Step 8
# (commands + session + bottom-up event path), and Step 9 (curses wrapper +
# entrypoint + UI import audit) replace these with real fixture-backed
# checks. Step 7 lands I-UI-01, I-UI-02 (REQUIRED) and I-UI-08, I-UI-09
# (STRUCTURAL) via brain.ui.fixtures.snapshot_view and
# brain.ui.fixtures.render_view. I-UI-14 is OBSERVED and is not pending here;
# it is registered when its fixture lands. I-UI-15 is NOT-EXERCISED and does
# not participate in I-CAT-01 coverage.
# ---------------------------------------------------------------------------


_OPERATOR_TUI_PENDING_ROWS: dict[str, str] = {
    # Step 7 landed I-UI-01, I-UI-02 (REQUIRED) and I-UI-08, I-UI-09
    # (STRUCTURAL) via brain.ui.fixtures.snapshot_view and
    # brain.ui.fixtures.render_view. Step 8 landed I-UI-03, I-UI-04
    # (REQUIRED), I-UI-05 (REQUIRED bottom-up tick path), I-UI-06
    # (REQUIRED failure-isolation), I-UI-10 (STRUCTURAL resource-free
    # session), and I-UI-13 (STRUCTURAL bounded UI status text) via
    # brain.ui.fixtures.command_router and brain.ui.fixtures.bottom_up_tick.
    # Step 9 landed I-UI-07 (REQUIRED no-host-execution UI audit),
    # I-UI-11 (STRUCTURAL curses-wrapper thinness), I-UI-12 (STRUCTURAL
    # fail-closed entrypoint), and I-UI-14 (OBSERVED aggregate session
    # walk) via brain.ui.tui, brain.ui.__main__, and
    # brain.ui.fixtures.tui_smoke. No pending v0.10 Operator TUI rows
    # remain.
}


# ---------------------------------------------------------------------------
# Operator TUI Agent-Style Layout (v0.11): pending row registrations.
#
# Step 6 of the Operator TUI Agent-Style Layout campaign applies the accepted
# v0.11 catalog patch (I-UI-16..I-UI-23) before the agent-layout runtime
# modules (brain/ui/layout.py, brain/ui/composer.py,
# brain/ui/command_line.py, brain/ui/transcript.py) and their fixtures exist.
# These pending registrations keep I-CAT-01 coverage coherent while making
# any attempted row execution fail explicitly. Step 7 (layout module + pure
# renderer upgrade) drives I-UI-16, I-UI-20, I-UI-22 via
# brain.ui.fixtures.agent_layout. Step 8 (bottom composer + typed local
# command parser) drives I-UI-17 and I-UI-18 via
# brain.ui.fixtures.composer_input. Step 9 (transcript + session
# integration) drives I-UI-19 via brain.ui.fixtures.transcript_log.
# Step 10 (curses wrapper integration + README sync) drives I-UI-21
# (STRUCTURAL) and registers I-UI-23 (OBSERVED) via
# brain.ui.fixtures.agent_tui_smoke. I-UI-23 is OBSERVED and is not pending
# here; it is registered when its fixture lands.
# ---------------------------------------------------------------------------


_OPERATOR_TUI_AGENT_LAYOUT_PENDING_ROWS: dict[str, str] = {
    # Step 7 of the Operator TUI Agent-Style Layout campaign landed
    # I-UI-16 (REQUIRED), I-UI-20 (STRUCTURAL), and I-UI-22 (STRUCTURAL)
    # via brain.ui.layout, brain.ui.render (render_agent), and
    # brain.ui.fixtures.agent_layout. Step 8 landed I-UI-17 (REQUIRED)
    # and I-UI-18 (REQUIRED) via brain.ui.composer, brain.ui.command_line,
    # and brain.ui.fixtures.composer_input. Step 9 landed I-UI-19
    # (REQUIRED) via brain.ui.transcript and
    # brain.ui.fixtures.transcript_log. Step 10 landed I-UI-21
    # (STRUCTURAL) and I-UI-23 (OBSERVED) via the agent-style curses
    # wrapper integration in brain.ui.tui and
    # brain.ui.fixtures.agent_tui_smoke. No Operator TUI Agent-Style
    # Layout rows remain pending.
}


def _make_operator_tui_agent_layout_pending_check(
    row_id: str,
) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Operator TUI Agent-Style Layout "
            "catalog coverage but its runtime implementation has not "
            "landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _OPERATOR_TUI_AGENT_LAYOUT_PENDING_ROWS.items():
    register(_row_id, status=_status)(
        _make_operator_tui_agent_layout_pending_check(_row_id)
    )


def _make_operator_tui_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Operator TUI catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _OPERATOR_TUI_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_operator_tui_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.5 Expression + ReadabilityPredictor: pending row registrations.
#
# Step 6 of the Phase 3.5 campaign applies the accepted v0.12 catalog patch
# (I-EXP-01..I-EXP-18) before the expression runtime layer
# (brain/development/expression.py) and its fixtures exist. These pending
# registrations keep I-CAT-01 coverage coherent while making any attempted
# row execution fail explicitly. Step 7 (expression core) replaces the
# I-EXP-01, I-EXP-02, I-EXP-03, I-EXP-07, I-EXP-08, I-EXP-13, I-EXP-14, and
# I-EXP-15 entries with real fixture-backed checks. Step 8
# (ReadabilityPredictor) replaces I-EXP-04, I-EXP-05, I-EXP-09, I-EXP-10,
# I-EXP-11, I-EXP-12, and I-EXP-16. Step 9 (ExpressionHistory + summary)
# replaces I-EXP-06 and documents the OBSERVED I-EXP-17 in the audit.
# I-EXP-17 (OBSERVED) and I-EXP-18 (NOT-EXERCISED) do not participate in
# I-CAT-01 coverage and are not pending here.
# ---------------------------------------------------------------------------


_PHASE3_5_PENDING_ROWS: dict[str, str] = {
    # Step 7 landed I-EXP-01, I-EXP-02, I-EXP-03, I-EXP-07, I-EXP-08,
    # I-EXP-13, I-EXP-14, I-EXP-15, and I-EXP-16 (the static audit
    # fixture covers all three structural audit rows together per the
    # catalog patch plan's optional bundling allowance). Step 8 landed
    # I-EXP-04, I-EXP-05, I-EXP-09, I-EXP-10, I-EXP-11, and I-EXP-12
    # via the readability_score_fraction_bounded,
    # readability_prediction_tagged, readability_predictor_empty_item,
    # readability_predictor_repetition_only,
    # readability_predictor_length_cap, and
    # readability_predictor_determinism fixtures. Step 9 landed
    # I-EXP-06 via expression_history_cow_bounded. I-EXP-17 (OBSERVED)
    # and I-EXP-18 (NOT-EXERCISED) do not participate in I-CAT-01
    # coverage. No Phase 3.5 Expression + ReadabilityPredictor rows
    # remain pending.
}


def _make_phase3_5_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.5 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_5_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_5_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.6 Reflective Inspection: pending row registrations.
#
# Step 6 of the Phase 3.6 campaign applies the accepted v0.13 catalog patch
# (I-REF-01..I-REF-14) before the reflective runtime layer
# (brain/development/reflective.py) and its fixtures exist. These pending
# registrations keep I-CAT-01 coverage coherent while making any attempted
# row execution fail explicitly. Step 7 (reflective core + fixtures)
# replaces them with real fixture-backed checks. I-REF-13 (OBSERVED) and
# I-REF-14 (NOT-EXERCISED) do not participate in I-CAT-01 coverage and are
# not pending here.
# ---------------------------------------------------------------------------


_PHASE3_6_PENDING_ROWS: dict[str, str] = {
    "I-REF-01": "REQUIRED",
    "I-REF-02": "REQUIRED",
    "I-REF-03": "REQUIRED",
    "I-REF-04": "REQUIRED",
    "I-REF-05": "REQUIRED",
    "I-REF-06": "REQUIRED",
    "I-REF-07": "REQUIRED",
    "I-REF-08": "REQUIRED",
    "I-REF-09": "STRUCTURAL",
    "I-REF-10": "STRUCTURAL",
    "I-REF-11": "STRUCTURAL",
    "I-REF-12": "STRUCTURAL",
}


def _make_phase3_6_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.6 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_6_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_6_pending_check(_row_id))


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

    # I-CAT-01 entry audit: refuse to run if any catalog REQUIRED /
    # STRUCTURAL row lacks a registered check. This is a hard fail —
    # it precedes every per-row check below.
    coverage_errors = _audit_coverage()
    if coverage_errors:
        raise RuntimeError(
            "I-CAT-01 violated. Catalog rows without registered checks:\n  - "
            + "\n  - ".join(coverage_errors)
        )

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
            if r.spec.status == "OBSERVED":
                mark = "OBS-PASS" if r.passed else "OBS-FAIL"
            else:
                mark = "PASS" if r.passed else "FAIL"
            print(f"  {mark:8s}  {r.spec.id:11s}  {r.spec.status}")
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
    required_pass = summary.get("REQUIRED/pass", 0)
    required_fail = summary.get("REQUIRED/fail", 0)
    structural_pass = summary.get("STRUCTURAL/pass", 0)
    structural_fail = summary.get("STRUCTURAL/fail", 0)
    observed_pass = summary.get("OBSERVED/pass", 0)
    observed_fail = summary.get("OBSERVED/fail", 0)
    gate_failed = sum(
        1 for r in report.rows if not r.passed and r.spec.status != "OBSERVED"
    )
    line = (
        f"\n{total_rows} rows checked  ·  REQUIRED green: {required_pass} "
        f"·  REQUIRED red: {required_fail}  ·  STRUCTURAL green: {structural_pass} "
        f"·  STRUCTURAL red: {structural_fail}"
    )
    if observed_pass or observed_fail:
        line += f"  ·  OBSERVED: {observed_pass} pass / {observed_fail} fail"
    line += f"  ·  gate failures: {gate_failed}"
    print(line)


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
