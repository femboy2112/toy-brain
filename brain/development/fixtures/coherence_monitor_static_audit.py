"""Fixture for I-COHMON-10 and I-COHMON-11.

* I-COHMON-10 — static AST audit over
  ``brain/development/coherence_monitor.py`` rejects every forbidden
  import / module reference / dynamic-execution call. Allowed
  imports are exactly the documented seam.
* I-COHMON-11 — no disallowed non-claim term appears in the module
  source (outside the canonical ``_FORBIDDEN_NON_CLAIM_TERMS``
  constant whose runtime job is to *detect* such terms in generated
  output). The non-claim audit also runs over a representative
  :func:`build_full_coherence_report` output to confirm the
  generated bounded printable strings contain none of the forbidden
  terms.

The audit is local to this fixture and does not extend
``tools.import_audit``.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.development.coherence_monitor import (
    CoherenceCheckStatus,
    build_full_coherence_report,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.session import OperatorSession


_COHERENCE_MONITOR_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "coherence_monitor.py"
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
    "brain.llm",
    "threading",
    "asyncio",
    "atexit",
    "signal",
    "importlib",
)


_ALLOWED_IMPORT_NAMES: frozenset[str] = frozenset({
    "__future__",
    "dataclasses",
    "enum",
    "fractions",
    "typing",
    "brain.development.pattern_ledger",
    "brain.development.text_stream",
    "brain.io_types",
    "brain.tick",
    "brain.tlica.msi",
    "brain.tlica.profile",
    "brain.tlica.ptcns",
    "brain.ui.session",
    "brain.ui.snapshot",
    "brain.ui.commands",
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
})


_FORBIDDEN_CALL_PREFIXES: tuple[str, ...] = (
    "importlib.",
    "atexit.",
    "signal.",
    "sqlite3.",
    "subprocess.",
    "socket.",
    "urllib.",
    "http.",
    "shutil.",
    "tempfile.",
    "pathlib.",
)


#: Non-claim disciplinary term list. Mirrors the runtime
#: ``_FORBIDDEN_NON_CLAIM_TERMS`` constant in
#: :mod:`brain.development.coherence_monitor`.
_AUDIT_FORBIDDEN_NON_CLAIM_TERMS: tuple[str, ...] = (
    "conscious",
    "consciousness",
    "sentient",
    "sentience",
    "subjective",
    "qualia",
    "aware",
    "awareness",
    "i-ness",
    "understand",
    "understanding",
    "comprehend",
    "comprehension",
    "believe",
    "belief",
    "intent",
    "agency",
    "self-modification",
    "truth",
    "preserve",
    "damage",
)


def _parse_module() -> tuple[ast.Module, str]:
    source = _COHERENCE_MONITOR_SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_COHERENCE_MONITOR_SOURCE_PATH)), source


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


def _forbidden_terms_lineranges(tree: ast.Module) -> set[int]:
    """Return the set of line numbers occupied by the
    ``_FORBIDDEN_NON_CLAIM_TERMS`` assignment (so the string-content
    audit can skip them).
    """
    lines: set[int] = set()
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "_FORBIDDEN_NON_CLAIM_TERMS"
            ):
                start = node.lineno
                end = getattr(node, "end_lineno", start) or start
                for line in range(start, end + 1):
                    lines.add(line)
    return lines


@register("I-COHMON-10", status="REQUIRED")
def check_coherence_monitor_static_audit() -> None:
    assert _COHERENCE_MONITOR_SOURCE_PATH.exists(), (
        "I-COHMON-10 violated: coherence_monitor.py not found at "
        f"{_COHERENCE_MONITOR_SOURCE_PATH}"
    )
    tree, source = _parse_module()

    # Forbidden imports rejected.
    targets = _import_targets(tree)
    bad_forbidden = [name for name in targets if _is_forbidden_import(name)]
    assert not bad_forbidden, (
        "I-COHMON-10 violated: coherence_monitor.py imports forbidden modules "
        f"{bad_forbidden}"
    )

    # Allowed imports only.
    for name in targets:
        bare = name.lstrip(".")
        if not bare:
            continue
        assert bare in _ALLOWED_IMPORT_NAMES, (
            "I-COHMON-10 violated: coherence_monitor.py imports unexpected "
            f"target {name!r} (allowed: {sorted(_ALLOWED_IMPORT_NAMES)})"
        )

    # Module-level statements limited.
    for stmt in tree.body:
        assert _is_allowed_module_level(stmt), (
            "I-COHMON-10 violated: disallowed module-level statement "
            f"{type(stmt).__name__} at line {stmt.lineno}"
        )

    # No forbidden call name appears in the module body.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in _FORBIDDEN_CALL_NAMES:
                raise AssertionError(
                    "I-COHMON-10 violated: forbidden call "
                    f"{name!r} at line {node.lineno}"
                )
            for prefix in _FORBIDDEN_CALL_PREFIXES:
                if name.startswith(prefix):
                    raise AssertionError(
                        "I-COHMON-10 violated: forbidden call "
                        f"{name!r} at line {node.lineno}"
                    )

    # No string-form forbidden references.
    for needle in (
        "eval(",
        "exec(",
        "compile(",
        "__import__(",
        "importlib.import_module",
        "atexit.register",
        "signal.signal",
        "subprocess.",
        "socket.",
        "sqlite3.connect",
        "save_session(",
        "load_session(",
        "db_backup(",
        "db_verify(",
        "maybe_autosave_after_mutation(",
    ):
        assert needle not in source, (
            "I-COHMON-10 violated: coherence_monitor.py contains forbidden "
            f"text {needle!r}"
        )


def _ast_strings_outside_forbidden_block(
    tree: ast.Module, skip_lines: set[int]
) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lineno = getattr(node, "lineno", 0) or 0
            if lineno in skip_lines:
                continue
            out.append((lineno, node.value))
    return out


@register("I-COHMON-11", status="REQUIRED")
def check_coherence_monitor_no_disallowed_terms() -> None:
    tree, source = _parse_module()
    skip_lines = _forbidden_terms_lineranges(tree)
    assert skip_lines, (
        "I-COHMON-11 violated: _FORBIDDEN_NON_CLAIM_TERMS constant not "
        "found in coherence_monitor.py — runtime non-claim check cannot "
        "operate without it"
    )

    strings = _ast_strings_outside_forbidden_block(tree, skip_lines)
    for lineno, value in strings:
        lowered = value.lower()
        for term in _AUDIT_FORBIDDEN_NON_CLAIM_TERMS:
            assert term not in lowered, (
                "I-COHMON-11 violated: disallowed term "
                f"{term!r} in string at line {lineno}"
            )

    # Defense-in-depth: also scan the raw source outside the
    # forbidden-terms block by stripping lines in the skip set.
    raw_lines = source.splitlines()
    for idx, line in enumerate(raw_lines, start=1):
        if idx in skip_lines:
            continue
        lowered = line.lower()
        for term in _AUDIT_FORBIDDEN_NON_CLAIM_TERMS:
            assert term not in lowered, (
                "I-COHMON-11 violated: disallowed term "
                f"{term!r} in source at line {idx}: {line.strip()!r}"
            )

    # Run a representative report over a healthy session AFTER a
    # /stream append (so pledger/stream check messages exercise the
    # non-claim path with real data). Every bounded printable
    # string in the report must avoid the forbidden terms; the
    # corresponding non_claim check inside the report should PASS.
    session = OperatorSession(state=initial_state())
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    report = build_full_coherence_report(session)

    nonclaim_seen = False
    for check in report.snapshot.checks:
        if check.check_id == "nonclaim.no_forbidden_terms_in_report":
            assert check.status is CoherenceCheckStatus.PASS, (
                "I-COHMON-11 violated: non-claim term audit reports "
                f"{check.status.value}"
            )
            nonclaim_seen = True
        for text in (check.check_id, check.summary, check.detail):
            lowered = text.lower()
            for term in _AUDIT_FORBIDDEN_NON_CLAIM_TERMS:
                assert term not in lowered, (
                    "I-COHMON-11 violated: disallowed term "
                    f"{term!r} in check {check.check_id!r} text {text!r}"
                )
    assert nonclaim_seen, (
        "I-COHMON-11 violated: representative report did not include the "
        "non-claim audit check"
    )

    summary_lowered = report.summary_text.lower()
    for term in _AUDIT_FORBIDDEN_NON_CLAIM_TERMS:
        assert term not in summary_lowered, (
            "I-COHMON-11 violated: disallowed term "
            f"{term!r} in report.summary_text {report.summary_text!r}"
        )
