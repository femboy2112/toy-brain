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
    "brain.development.fixtures.reflective_source_enum_closed",
    "brain.development.fixtures.reflective_summary_item_bounded",
    "brain.development.fixtures.reflective_snapshot_deterministic",
    "brain.development.fixtures.reflective_no_brainstate_mutation",
    "brain.development.fixtures.reflective_no_source_history_mutation",
    "brain.development.fixtures.reflective_no_aggregate_score",
    "brain.development.fixtures.reflective_static_audit",
    "brain.development.fixtures.text_stream_source_enum_closed",
    "brain.development.fixtures.text_stream_chunk_bounded",
    "brain.development.fixtures.text_stream_history_cow_bounded",
    "brain.development.fixtures.text_stream_feature_vector_exact",
    "brain.development.fixtures.text_stream_no_brainstate_mutation",
    "brain.development.fixtures.text_stream_no_source_history_mutation",
    "brain.development.fixtures.text_stream_no_tick",
    "brain.development.fixtures.text_stream_static_audit",
    "brain.development.fixtures.text_stream_anti_growth",
    "brain.development.fixtures.text_stream_segment_candidate",
    "brain.development.fixtures.text_stream_pattern_recurrence",
    "brain.development.fixtures.text_stream_promotion_candidate",
    "brain.ui.fixtures.stream_command_parser",
    "brain.ui.fixtures.stream_session_append",
    "brain.ui.fixtures.stream_summary_candidates",
    "brain.ui.fixtures.stream_promotion_queue",
    "brain.ui.fixtures.stream_tick_boundary",
    "brain.ui.fixtures.stream_failure_isolation",
    "brain.ui.fixtures.stream_snapshot_render",
    "brain.ui.fixtures.stream_static_audit",
    "brain.ui.fixtures.stream_session_resource_audit",
    "brain.ui.fixtures.stream_constant_parity",
    "brain.ui.fixtures.llm_runtime_default_offline",
    "brain.ui.fixtures.llm_runtime_mode_closed",
    "brain.ui.fixtures.llm_runtime_factory_per_mode",
    "brain.ui.fixtures.llm_runtime_explicit_opt_in",
    "brain.ui.fixtures.llm_runtime_anthropic_requires_key",
    "brain.ui.fixtures.llm_runtime_claude_cli_requires_executable",
    "brain.ui.fixtures.llm_runtime_codex_cli_factory",
    "brain.ui.fixtures.llm_runtime_codex_cli_requires_executable",
    "brain.ui.fixtures.llm_runtime_mock_requires_responses",
    "brain.ui.fixtures.llm_runtime_cache_gated",
    "brain.ui.fixtures.llm_runtime_tick_seam",
    "brain.ui.fixtures.llm_runtime_print_once_independent",
    "brain.ui.fixtures.llm_runtime_config_frozen",
    "brain.ui.fixtures.llm_runtime_static_audit",
    "brain.ui.fixtures.persistence_schema",
    "brain.ui.fixtures.persistence_static_audit",
    "brain.ui.fixtures.persistence_save_roundtrip",
    "brain.ui.fixtures.persistence_failed_load",
    "brain.ui.fixtures.persistence_cogito_protected",
    "brain.ui.fixtures.persistence_load_constructor_only",
    "brain.ui.fixtures.persistence_load_invariants",
    "brain.ui.fixtures.persistence_failed_save",
    "brain.ui.fixtures.persistence_atomic_save",
    "brain.ui.fixtures.persistence_session_resource_audit",
    "brain.ui.fixtures.persistence_commands",
    "brain.ui.fixtures.persistence_ops_session_status",
    "brain.ui.fixtures.persistence_ops_db_status",
    "brain.ui.fixtures.persistence_ops_db_verify",
    "brain.ui.fixtures.persistence_ops_db_verify_drop",
    "brain.ui.fixtures.persistence_ops_db_backup",
    "brain.ui.fixtures.persistence_ops_db_backup_force",
    "brain.ui.fixtures.persistence_ops_db_backup_dest_uri",
    "brain.ui.fixtures.persistence_ops_cli_short_circuit",
    "brain.ui.fixtures.persistence_ops_resource_audit",
    "brain.ui.fixtures.persistence_ops_static_audit",
    "brain.ui.fixtures.persistence_observe_db_summary",
    "brain.ui.fixtures.persistence_observe_profile_summary",
    "brain.ui.fixtures.persistence_observe_stream_db_summary",
    "brain.ui.fixtures.persistence_observe_db_diff",
    "brain.ui.fixtures.persistence_observe_no_builder_call",
    "brain.ui.fixtures.persistence_observe_resource_audit",
    "brain.ui.fixtures.persistence_observe_default_caps",
    "brain.ui.fixtures.persistence_observe_static_audit",
    "brain.ui.fixtures.autosave_default_off",
    "brain.ui.fixtures.autosave_mode_closed",
    "brain.ui.fixtures.autosave_requires_db",
    "brain.ui.fixtures.autosave_status_after_event",
    "brain.ui.fixtures.autosave_failure_preserves",
    "brain.ui.fixtures.autosave_no_after_failure",
    "brain.ui.fixtures.autosave_no_after_read_only",
    "brain.ui.fixtures.autosave_single_save_path",
    "brain.ui.fixtures.autosave_trigger_set",
    "brain.ui.fixtures.autosave_static_audit",
    "brain.ui.fixtures.autosave_resource_audit",
    "brain.development.fixtures.pattern_ledger_constructor",
    "brain.development.fixtures.pattern_ledger_signature_id",
    "brain.development.fixtures.pattern_ledger_observe",
    "brain.development.fixtures.pattern_ledger_static_audit",
    "brain.development.fixtures.pattern_ledger_no_runtime_coupling",
    "brain.development.fixtures.pattern_ledger_stream_integration",
    "brain.development.fixtures.coherence_monitor_constructor",
    "brain.development.fixtures.coherence_monitor_kernel_checks",
    "brain.development.fixtures.coherence_monitor_session_checks",
    "brain.development.fixtures.coherence_monitor_pattern_ledger_checks",
    "brain.development.fixtures.coherence_monitor_static_audit",
    "brain.development.fixtures.coherence_monitor_no_runtime_coupling",
    "brain.development.fixtures.growth_ledger_constructor",
    "brain.development.fixtures.growth_ledger_event_id",
    "brain.development.fixtures.growth_ledger_observe",
    "brain.development.fixtures.growth_ledger_static_audit",
    "brain.development.fixtures.growth_ledger_no_runtime_coupling",
    "brain.development.fixtures.growth_ledger_session_integration",
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
    # Step 7 landed I-REF-01..12 via brain.development.reflective and the
    # seven reflective_* fixtures (one shared reflective_static_audit.py
    # fixture covering I-REF-09, I-REF-11, I-REF-12 per the catalog patch
    # plan's bundling allowance, and one shared
    # reflective_summary_item_bounded.py fixture covering I-REF-02, I-REF-03,
    # I-REF-04, and I-REF-10). I-REF-13 (OBSERVED) and I-REF-14
    # (NOT-EXERCISED) do not participate in I-CAT-01 coverage and are not
    # pending here. No Phase 3.6 Reflective Inspection rows remain pending.
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


# ---------------------------------------------------------------------------
# Phase 3.7 Text Stream Ingress: pending row registrations.
#
# Step 14 of the Phase 3.7 campaign applies the accepted v0.14 catalog patch
# (I-STRM-01..I-STRM-17) before the text-stream runtime layer
# (brain/development/text_stream.py) and its fixtures exist. These pending
# registrations keep I-CAT-01 coverage coherent while making any attempted
# row execution fail explicitly. Step 15 (text-stream core + fixtures)
# replaces I-STRM-01..04, I-STRM-08..15 with real fixture-backed checks, and
# Step 16 (segment / pattern / promotion-candidate layer) replaces
# I-STRM-05, I-STRM-06, and I-STRM-07. I-STRM-16 (OBSERVED) and I-STRM-17
# (NOT-EXERCISED) do not participate in I-CAT-01 coverage and are not
# pending here.
# ---------------------------------------------------------------------------


_PHASE3_7_PENDING_ROWS: dict[str, str] = {
    # Step 15 landed I-STRM-01..04 and I-STRM-08..15. Step 16 landed
    # I-STRM-05 (text_stream_segment_candidate), I-STRM-06
    # (text_stream_pattern_recurrence), and I-STRM-07
    # (text_stream_promotion_candidate). I-STRM-16 (OBSERVED) and
    # I-STRM-17 (NOT-EXERCISED) do not participate in I-CAT-01 coverage
    # and are not pending here. No Phase 3.7 Text Stream Ingress rows
    # remain pending.
}


def _make_phase3_7_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.7 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_7_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_7_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.8 Operator Stream Interaction: pending row registrations.
#
# Step 23 of the Phase 3.8 campaign applies the accepted v0.15 catalog patch
# (I-UISTRM-01..I-UISTRM-17) before the Phase 3.8 operator stream runtime
# (brain/ui/commands.py, brain/ui/command_line.py, brain/ui/session.py,
# brain/ui/snapshot.py, brain/ui/render.py) and its fixtures exist. These
# pending registrations keep I-CAT-01 coverage coherent while making any
# attempted row execution fail explicitly. Step 24 (stream commands +
# fixtures) replaces I-UISTRM-01..15 with real fixture-backed checks.
# I-UISTRM-16 (OBSERVED) and I-UISTRM-17 (NOT-EXERCISED) do not participate
# in I-CAT-01 coverage and are not pending here.
# ---------------------------------------------------------------------------


_PHASE3_8_PENDING_ROWS: dict[str, str] = {
    # Step 24 landed I-UISTRM-01..15 via brain/ui/{commands,command_line,
    # session,snapshot,render}.py plus the ten stream_* fixtures.
    # I-UISTRM-16 (OBSERVED) and I-UISTRM-17 (NOT-EXERCISED) do not
    # participate in I-CAT-01 coverage and are not pending here. No
    # Phase 3.8 Operator Stream Interaction rows remain pending.
}


def _make_phase3_8_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.8 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_8_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_8_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.8b LLM Runtime Toggle pending rows. Step 24F landed
# brain/ui/llm_runtime.py, extended brain/ui/__main__.py, and added the
# twelve llm_runtime_* fixtures. I-LLMTOG-14 (OBSERVED) and
# I-LLMTOG-15 (NOT-EXERCISED) do not participate in I-CAT-01 coverage
# and are not pending here. No Phase 3.8b LLM Runtime Toggle rows
# remain pending.
# ---------------------------------------------------------------------------


_PHASE3_8B_PENDING_ROWS: dict[str, str] = {}


def _make_phase3_8b_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.8b catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_8B_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_8b_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.9 Persistent Session Store pending rows. Step 7 of the Phase 3.9
# campaign applies the accepted v0.17 catalog patch (I-PERSIST-01..16)
# before the Phase 3.9 persistence runtime (brain/ui/persistence.py) and
# its eleven persistence_* fixtures exist. These pending registrations
# keep I-CAT-01 coverage coherent while making any attempted row
# execution fail explicitly. Steps 8-10 replace I-PERSIST-01..14 with
# real fixture-backed checks (Step 8 lands the schema + typed records +
# static audit; Step 9 lands save / load reconstruction and the failure-
# isolation / atomic-save / resource-audit fixtures; Step 10 lands the
# /save-session and /load-session commands fixture). I-PERSIST-15
# (OBSERVED, cold-start dry run) does not participate in I-CAT-01
# coverage. I-PERSIST-16 was later reclassified to STRUCTURAL at v0.19
# and is registered below by reusing persistence_static_audit.py.
# ---------------------------------------------------------------------------


_PHASE3_9_PENDING_ROWS: dict[str, str] = {
    # Step 8 landed I-PERSIST-01, I-PERSIST-12, I-PERSIST-13.
    # Step 9 landed I-PERSIST-02..08, I-PERSIST-10, I-PERSIST-11,
    # I-PERSIST-14. Step 10 landed I-PERSIST-09 via brain/ui/commands.py
    # (SAVE_SESSION / LOAD_SESSION enum), brain/ui/command_line.py
    # (/save-session and /load-session typed verbs),
    # brain/ui/session.py (_dispatch_save_session /
    # _dispatch_load_session), brain/ui/__main__.py (--session-db /
    # --load-session / --no-load-session CLI flags), and
    # brain/ui/fixtures/persistence_commands.py. No Phase 3.9
    # Persistent Session Store rows remain pending. I-PERSIST-15
    # (OBSERVED, cold-start dry run) is documented in Step 11's
    # PHASE3_9_PERSISTENCE_DRY_RUN.md. I-PERSIST-16 was reclassified
    # to STRUCTURAL at v0.19 and is registered below by reusing
    # persistence_static_audit.py.
}


def _make_phase3_9_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.9 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_9_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_9_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.10a Operational Hardening + Phase 3.10b Persistence Observability
# pending rows. Step 7 of the Phase 3.10 campaign applies the accepted v0.18
# catalog patch (I-OPSHARDEN-01..14 + I-OBSERVE-01..11; tracks A + B only;
# track C autosave is gated behind its own review gate and is not in this
# patch) before the Phase 3.10 runtime modules (brain/ui/persistence_ops.py
# and brain/ui/persistence_observe.py) and their eighteen fixture files
# exist. These pending registrations keep I-CAT-01 coverage coherent while
# making any attempted row execution fail explicitly. Steps 8-10 replace
# I-OPSHARDEN-01..14 and I-OBSERVE-01..10 with real fixture-backed checks
# (Step 8 lands the operational-hardening core: session_status, db_status,
# db_verify, db_backup helpers + persistence_ops fixtures (DONE); Step 9
# lands the observability summaries + diff: db_summary, profile_summary,
# stream_db_summary, db_diff helpers + persistence_observe fixtures (DONE,
# all 10 I-OBSERVE rows drained); Step 10 lands the explicit
# backup-command docs / README updates).
# I-OBSERVE-11 (OBSERVED, ops/observability dry run) is documented in
# Step 11's PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md and does not
# participate in I-CAT-01 coverage.
# ---------------------------------------------------------------------------


_PHASE3_10_OPS_PENDING_ROWS: dict[str, str] = {
    # Step 8 landed I-OPSHARDEN-01..14 via brain/ui/persistence_ops.py
    # (session_status, db_status, db_verify, db_backup helpers + typed
    # reports), brain/ui/commands.py (SESSION_STATUS / DB_STATUS /
    # DB_VERIFY / DB_BACKUP enum members + DbBackupPayload),
    # brain/ui/command_line.py (the four Phase 3.10a verbs),
    # brain/ui/session.py (the four Phase 3.10a dispatchers),
    # brain/ui/__main__.py (the four --db-* short-circuit flags + the
    # _dispatch_ops_short_circuit helper), and the ten
    # persistence_ops_* fixtures. No Phase 3.10a Operational
    # Hardening rows remain pending.
}


_PHASE3_10_OBSERVE_PENDING_ROWS: dict[str, str] = {
    # Step 9 landed I-OBSERVE-01..10 via brain/ui/persistence_observe.py
    # (db_summary, profile_summary, stream_db_summary, db_diff helpers
    # + typed reports + locked default caps), the narrow extension that
    # promoted brain.ui.persistence._snapshot_session to the public
    # snapshot_session helper, brain/ui/commands.py (DB_SUMMARY /
    # PROFILE_SUMMARY / STREAM_DB_SUMMARY / DB_DIFF enum members),
    # brain/ui/command_line.py (the four Phase 3.10b verbs),
    # brain/ui/session.py (the four Phase 3.10b dispatchers), and the
    # eight persistence_observe_* fixtures. No Phase 3.10b Persistence
    # Observability rows remain pending. I-OBSERVE-11 (OBSERVED) is
    # documented in Step 11's PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md
    # and does not participate in I-CAT-01 coverage.
}


def _make_phase3_10_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.10 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_10_OPS_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_10_pending_check(_row_id))

for _row_id, _status in _PHASE3_10_OBSERVE_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_10_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.10c Autosave Policy pending rows. The accepted v0.19 catalog
# patch added I-AUTOSAVE-01..15 before the Phase 3.10c runtime module
# (brain/ui/autosave.py) and its autosave_* fixtures existed. These
# pending registrations kept I-CAT-01 coverage coherent while making any
# attempted row execution fail explicitly. The live autosave fixtures later
# replaced I-AUTOSAVE-01..14 with real fixture-backed checks; I-AUTOSAVE-15
# is OBSERVED and is documented in PHASE3_10C_AUTOSAVE_DRY_RUN.md without
# participating in I-CAT-01 coverage.
# ---------------------------------------------------------------------------


_PHASE3_10C_PENDING_ROWS: dict[str, str] = {
    # The autosave fixture landing drained I-AUTOSAVE-01..14 via the
    # eleven brain/ui/fixtures/autosave_*.py fixtures registered in
    # FIXTURE_MODULES. The runtime lives in brain/ui/autosave.py
    # (default-OFF opt-in autosave that hooks the central
    # OperatorSession.dispatch post-mutation site and routes through
    # the existing brain.ui.persistence.save_session helper). The
    # autosave Phase 3.10c verbs (/autosave-status, /autosave-enable,
    # /autosave-disable) and the --autosave-mode CLI flag are wired in
    # brain/ui/commands.py, brain/ui/command_line.py,
    # brain/ui/__main__.py, and brain/ui/session.py. I-AUTOSAVE-15
    # (OBSERVED) is documented in PHASE3_10C_AUTOSAVE_DRY_RUN.md and
    # does not participate in I-CAT-01 coverage.
}


def _make_phase3_10c_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.10c catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_10C_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_10c_pending_check(_row_id))


# ---------------------------------------------------------------------------
# Phase 3.9 I-PERSIST-16 reclassification (v0.19; NOT-EXERCISED ->
# STRUCTURAL). The row's narrowed proposition (brain/ui/persistence.py
# owns no autosave trigger or background autosave hook) is already
# enforced by the I-PERSIST-12 static-AST audit body inside
# brain.ui.fixtures.persistence_static_audit. The v0.19 patch keeps the
# fixture file unchanged in the v0.19 catalog patch; the registration
# below re-runs the existing audit and surfaces it under the I-PERSIST-16
# row ID so I-CAT-01 coverage stays coherent without a fixture-file
# edit. The catalog Fixture column for I-PERSIST-16 names
# persistence_static_audit.py for documentation; the actual @register
# entry lives here because the v0.19 file budget is documented-only and
# does not include fixture edits.
# ---------------------------------------------------------------------------


def _check_i_persist_16_autosave_absent() -> None:
    """brain/ui/persistence.py owns no autosave trigger or hook.

    Re-runs the existing I-PERSIST-12 static-AST audit body over
    brain/ui/persistence.py. The audit already rejects @atexit /
    threading / asyncio / signal handlers, importlib /
    eval / exec / compile, every forbidden import, and every
    non-imports / -constants / -function-def / -class-def
    module-level statement. The set of autosave entry points
    forbidden by the narrowed I-PERSIST-16 proposition is a
    subset of the I-PERSIST-12 audit body, so re-running that
    audit is sufficient. If brain/ui/persistence.py ever fails
    the I-PERSIST-12 audit, both rows will report red together;
    that is the intended coupling.
    """
    # Local import: the fixture module is loaded lazily so this
    # check function does not fight module-load ordering. The
    # registration below runs as @register decoration time, but
    # the body only executes when the runner walks the registry.
    from brain.ui.fixtures.persistence_static_audit import (  # noqa: PLC0415
        check_i_persist_12_static_audit,
    )

    check_i_persist_12_static_audit()


register("I-PERSIST-16", status="STRUCTURAL")(
    _check_i_persist_16_autosave_absent
)


# ---------------------------------------------------------------------------
# Phase 3.11 Codex CLI Runtime Option: pending row registrations.
#
# Step 8 applies the accepted v0.20 catalog patch (I-LLMTOG-16/17 REQUIRED,
# I-LLMTOG-18 OBSERVED) before the Phase 3.11 Step 9 runtime extension
# (CODEX_CLI enum member, _build_codex_cli_client, CodexCLIClient) and its
# two new fixtures land. These pending registrations keep I-CAT-01 coverage
# coherent while making any attempted row execution fail explicitly. Step 9
# replaces I-LLMTOG-16/17 with real fixture-backed checks via the two new
# llm_runtime_codex_cli_* modules registered in FIXTURE_MODULES.
# I-LLMTOG-18 is OBSERVED and does not participate in I-CAT-01 coverage;
# its smoke walk is documented in PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md
# Section 11 and recorded by the operator in
# PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md.
# ---------------------------------------------------------------------------


_PHASE3_11_PENDING_ROWS: dict[str, str] = {}


def _make_phase3_11_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.11 catalog coverage "
            "but its runtime implementation has not landed yet"
        )

    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check


for _row_id, _status in _PHASE3_11_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_11_pending_check(_row_id))


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
