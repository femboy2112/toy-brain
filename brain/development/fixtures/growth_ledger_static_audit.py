"""Fixtures for I-GROW-10, I-GROW-11, I-GROW-19.

* I-GROW-10 — :mod:`brain.development.growth_ledger` has the locked
  import surface only: ``dataclasses``, ``enum``, ``hashlib``,
  ``typing``, and ``brain.tlica.profile`` for ``COGITO_ID``.
* I-GROW-11 — static AST audit rejects every LOCK P forbidden
  import / call / dynamic-execution surface, including raw ``tick``,
  LLM imports, persistence / autosave calls, Pattern Ledger /
  Coherence Monitor builder calls, ``open``, ``eval`` / ``exec`` /
  ``compile`` / ``__import__``.
* I-GROW-19 — non-claim and banned-interpretation audit: no banned
  label appears in the module source (outside an explicitly skipped
  block, if any) or in representative bounded printable strings
  produced by the module.

The fixture imports the canonical
:data:`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
tuple on the FIXTURE side (Option A from corrigenda LOCK Q);
``growth_ledger.py`` itself does not import Coherence Monitor.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.development.coherence_monitor import (
    _FORBIDDEN_NON_CLAIM_TERMS,
)
from brain.development.growth_ledger import (
    GrowthEventSource,
    GrowthEventType,
    GrowthLedger,
)
from brain.invariants import register


_GROWTH_LEDGER_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "growth_ledger.py"
)


_FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "os",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "pathlib",
    "tempfile",
    "shutil",
    "curses",
    "sqlite3",
    "brain.llm",
    "brain.tick",
    "brain.ui",
    "brain.development.pattern_ledger",
    "brain.development.coherence_monitor",
    "brain.development.text_stream",
    "threading",
    "asyncio",
    "atexit",
    "signal",
    "importlib",
    "math",
    "fractions",
)


# Allow only brain.tlica.profile from brain.tlica (for COGITO_ID).
_FORBIDDEN_TLICA_SUBMODULES: tuple[str, ...] = (
    "brain.tlica.action_projection",
    "brain.tlica.agency",
    "brain.tlica.preservation",
    "brain.tlica.affect",
    "brain.tlica.modes",
    "brain.tlica.msi",
    "brain.tlica.ptcns",
    "brain.tlica.iboundary",
    "brain.tlica.project_map",
    "brain.tlica.pce",
    "brain.tlica.trajectory",
    "brain.tlica.builders",
    "brain.tlica.integration_graph",
    "brain.tlica.phi_coordinate",
    "brain.tlica.free_will",
    "brain.tlica.dynamics",
    "brain.tlica.mode_aggregation",
    "brain.tlica.non_reducibility",
    "brain.tlica.comparison",
)


_ALLOWED_IMPORT_NAMES: frozenset[str] = frozenset({
    "__future__",
    "dataclasses",
    "enum",
    "hashlib",
    "typing",
    "brain.tlica.profile",
})


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "tick",
    "save_session",
    "load_session",
    "db_backup",
    "db_verify",
    "maybe_autosave_after_mutation",
    "build_coherence_report",
    "build_full_coherence_report",
})


_FORBIDDEN_CALL_PREFIXES: tuple[str, ...] = (
    "importlib.",
    "atexit.",
    "signal.",
    "threading.",
    "asyncio.",
    "sqlite3.",
    "subprocess.",
    "socket.",
    "urllib.",
    "http.",
    "shutil.",
    "tempfile.",
    "pathlib.",
    "math.",
    "fractions.",
    "PatternLedger.",
)


def _parse_module() -> tuple[ast.Module, str]:
    source = _GROWTH_LEDGER_SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_GROWTH_LEDGER_SOURCE_PATH)), source


def _import_targets(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            out.append("." * node.level + (node.module or ""))
    return out


def _is_forbidden_import(name: str) -> bool:
    bare = name.lstrip(".")
    if not bare:
        return False
    for prefix in _FORBIDDEN_IMPORT_PREFIXES:
        if bare == prefix or bare.startswith(prefix + "."):
            return True
    for prefix in _FORBIDDEN_TLICA_SUBMODULES:
        if bare == prefix or bare.startswith(prefix + "."):
            return True
    return False


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def _is_allowed_module_level(stmt: ast.stmt) -> bool:
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return True
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
        return True
    if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return True
    return False


@register("I-GROW-10", status="REQUIRED")
def check_growth_ledger_allowed_imports() -> None:
    assert _GROWTH_LEDGER_SOURCE_PATH.exists(), (
        "I-GROW-10 violated: growth_ledger.py not found at "
        f"{_GROWTH_LEDGER_SOURCE_PATH}"
    )
    tree, _ = _parse_module()

    targets = _import_targets(tree)
    for name in targets:
        bare = name.lstrip(".")
        if not bare:
            continue
        assert bare in _ALLOWED_IMPORT_NAMES, (
            "I-GROW-10 violated: growth_ledger.py imports unexpected "
            f"target {name!r} (allowed: {sorted(_ALLOWED_IMPORT_NAMES)})"
        )


@register("I-GROW-11", status="REQUIRED")
def check_growth_ledger_static_audit() -> None:
    assert _GROWTH_LEDGER_SOURCE_PATH.exists(), (
        "I-GROW-11 violated: growth_ledger.py not found at "
        f"{_GROWTH_LEDGER_SOURCE_PATH}"
    )
    tree, source = _parse_module()

    # Forbidden imports rejected.
    targets = _import_targets(tree)
    bad = [name for name in targets if _is_forbidden_import(name)]
    assert not bad, (
        "I-GROW-11 violated: growth_ledger.py imports forbidden modules "
        f"{bad}"
    )

    # Module-level statements limited.
    for stmt in tree.body:
        assert _is_allowed_module_level(stmt), (
            "I-GROW-11 violated: disallowed module-level statement "
            f"{type(stmt).__name__} at line {stmt.lineno}"
        )

    # No forbidden call name or prefix appears.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            assert name not in _FORBIDDEN_CALL_NAMES, (
                f"I-GROW-11 violated: forbidden call {name!r} at "
                f"line {node.lineno}"
            )
            for prefix in _FORBIDDEN_CALL_PREFIXES:
                assert not name.startswith(prefix), (
                    f"I-GROW-11 violated: forbidden call {name!r} at "
                    f"line {node.lineno}"
                )

    # String-form forbidden references rejected as defense-in-depth.
    # Needles are narrow call-site forms (not bare module prefixes), so
    # negatively-phrased docstring mentions of those names — used to
    # document "this module never opens a sqlite3 connection or
    # subprocess" — do not trigger a false positive.
    for needle in (
        "eval(",
        "exec(",
        "compile(",
        "__import__(",
        "importlib.import_module",
        "atexit.register",
        "signal.signal",
        "subprocess.Popen",
        "subprocess.run",
        "socket.socket",
        "sqlite3.connect",
        "save_session(",
        "load_session(",
        "db_backup(",
        "db_verify(",
        "maybe_autosave_after_mutation(",
        "build_coherence_report(",
        "build_full_coherence_report(",
        "PatternLedger.observe(",
    ):
        assert needle not in source, (
            "I-GROW-11 violated: growth_ledger.py contains forbidden "
            f"text {needle!r}"
        )


@register("I-GROW-19", status="REQUIRED")
def check_growth_ledger_no_disallowed_terms() -> None:
    """Inherit the Coherence Monitor forbidden-terms set (Option A)."""
    _, source = _parse_module()
    raw_lines = source.splitlines()

    # Source-line scan: no forbidden term appears on any line.
    for idx, line in enumerate(raw_lines, start=1):
        lowered = line.lower()
        for term in _FORBIDDEN_NON_CLAIM_TERMS:
            assert term not in lowered, (
                "I-GROW-19 violated: disallowed term "
                f"{term!r} in growth_ledger.py source at line {idx}: "
                f"{line.strip()!r}"
            )

    # Representative bounded printable strings produced by the module
    # contain no forbidden term. Construct a small ledger across every
    # v1 event type, then scan every bounded printable string the
    # module surfaces for it.
    led = GrowthLedger()
    v1_kwargs = [
        dict(
            event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
            tick=1,
            source=GrowthEventSource.STREAM_APPEND,
            references=("strm-chunk-1",),
            provenance="stream_append:_dispatch_stream_append",
        ),
        dict(
            event_type=GrowthEventType.PATTERN_ENTRY_CREATED,
            tick=1,
            source=GrowthEventSource.PATTERN_LEDGER_OBSERVE,
            references=("pledger:0000000000000001",),
            provenance="pattern_ledger:observe",
        ),
        dict(
            event_type=GrowthEventType.PATTERN_ENTRY_UPDATED,
            tick=2,
            source=GrowthEventSource.PATTERN_LEDGER_OBSERVE,
            references=("pledger:0000000000000001",),
            provenance="pattern_ledger:observe",
        ),
        dict(
            event_type=GrowthEventType.STREAM_PROMOTION_QUEUED,
            tick=2,
            source=GrowthEventSource.STREAM_PROMOTE,
            references=("promo-strm-chunk-1",),
            provenance="stream_promote:_dispatch_stream_promote",
        ),
        dict(
            event_type=GrowthEventType.TICK_SUCCEEDED,
            tick=3,
            source=GrowthEventSource.STEP_DISPATCH,
            references=("tick-1",),
            provenance="step_dispatch:_dispatch_step",
        ),
        dict(
            event_type=GrowthEventType.PROFILE_DOMAIN_ADDED,
            tick=3,
            source=GrowthEventSource.STEP_DISPATCH,
            references=("alpha",),
            provenance="step_dispatch:profile_delta",
        ),
        dict(
            event_type=GrowthEventType.MSI_MEMBER_ADDED,
            tick=3,
            source=GrowthEventSource.STEP_DISPATCH,
            references=("alpha",),
            provenance="step_dispatch:msi_delta",
        ),
    ]
    for kwargs in v1_kwargs:
        led = led.observe(**kwargs)

    # Every bounded printable surface (event_id, references entries,
    # provenance) must contain none of the forbidden terms.
    for evt in led.events:
        bounded_strings = (
            evt.event_id,
            evt.provenance,
        ) + tuple(evt.references)
        for text in bounded_strings:
            lowered = text.lower()
            for term in _FORBIDDEN_NON_CLAIM_TERMS:
                assert term not in lowered, (
                    "I-GROW-19 violated: disallowed term "
                    f"{term!r} in bounded printable string {text!r}"
                )

    # counts_by_type labels (enum values) must contain no forbidden term.
    for label, _count in led.counts_by_type():
        lowered = label.lower()
        for term in _FORBIDDEN_NON_CLAIM_TERMS:
            assert term not in lowered, (
                "I-GROW-19 violated: disallowed term "
                f"{term!r} in counts_by_type label {label!r}"
            )
