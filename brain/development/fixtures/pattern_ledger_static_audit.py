"""Fixture for I-PLEDGER-15: static audit of pattern_ledger.py.

The audit confirms that:

* ``brain/development/pattern_ledger.py`` imports only from the
  allowed seam (``dataclasses``, ``enum``, ``fractions``, ``hashlib``,
  ``typing``, ``brain.development.text_stream``,
  ``brain.tlica.profile``).
* No forbidden module / submodule appears in any import
  statement (``os``, ``subprocess``, ``socket``, ``urllib``, ``http``,
  ``requests``, ``pathlib``, ``tempfile``, ``shutil``, ``curses``,
  ``brain.tick``, ``brain.llm``, ``brain.ui``, ``brain.tlica`` other
  than ``brain.tlica.profile`` for ``COGITO_ID``, ``threading``,
  ``asyncio``, ``atexit``, ``signal``, ``importlib``, ``math``).
* No dynamic-execution call appears (``eval``, ``exec``, ``compile``,
  ``__import__``, ``importlib.import_module``).
* No ``float`` / ``round`` / ``math.*`` call participates in any
  module-level function (defense in depth on the exact-Fraction
  confidence path).
* Module-level statements are limited to imports, constants,
  function defs, class defs, and a module docstring.

The audit is local to this fixture and does not extend
``tools.import_audit``.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_PATTERN_LEDGER_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "pattern_ledger.py"
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
    "brain.tick",
    "brain.llm",
    "brain.ui",
    "threading",
    "asyncio",
    "atexit",
    "signal",
    "importlib",
    "math",
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
    "dataclasses",
    "enum",
    "fractions",
    "hashlib",
    "typing",
    "brain.development.text_stream",
    "brain.tlica.profile",
    "__future__",
})


def _parse_module() -> ast.Module:
    source = _PATTERN_LEDGER_SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_PATTERN_LEDGER_SOURCE_PATH))


def _import_targets(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level
            prefix = "." * level
            out.append(prefix + module)
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


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "float",
    "round",
})


_FORBIDDEN_CALL_PREFIXES: tuple[str, ...] = (
    "importlib.",
    "atexit.",
    "signal.",
    "math.",
)


@register("I-PLEDGER-15", status="REQUIRED")
def check_pattern_ledger_static_audit() -> None:
    assert _PATTERN_LEDGER_SOURCE_PATH.exists(), (
        "I-PLEDGER-15 violated: pattern_ledger.py not found at "
        f"{_PATTERN_LEDGER_SOURCE_PATH}"
    )
    tree = _parse_module()

    # Forbidden imports rejected.
    targets = _import_targets(tree)
    bad_forbidden = [name for name in targets if _is_forbidden_import(name)]
    assert not bad_forbidden, (
        "I-PLEDGER-15 violated: pattern_ledger.py imports forbidden modules "
        f"{bad_forbidden}"
    )

    # Allowed imports only.
    for name in targets:
        bare = name.lstrip(".")
        if not bare:
            continue
        assert bare in _ALLOWED_IMPORT_NAMES, (
            "I-PLEDGER-15 violated: pattern_ledger.py imports unexpected "
            f"target {name!r} (allowed: {sorted(_ALLOWED_IMPORT_NAMES)})"
        )

    # Module-level statements limited to imports / constants / class /
    # function defs / docstring.
    for stmt in tree.body:
        assert _is_allowed_module_level(stmt), (
            "I-PLEDGER-15 violated: disallowed module-level statement "
            f"{type(stmt).__name__} at line {stmt.lineno}"
        )

    # No forbidden call appears anywhere in the module (including
    # function bodies).
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            assert name not in _FORBIDDEN_CALL_NAMES, (
                f"I-PLEDGER-15 violated: forbidden call {name!r} at "
                f"line {node.lineno}"
            )
            for prefix in _FORBIDDEN_CALL_PREFIXES:
                assert not name.startswith(prefix), (
                    f"I-PLEDGER-15 violated: forbidden call {name!r} at "
                    f"line {node.lineno}"
                )

    # No string-form forbidden references slip past the AST walk.
    source_text = _PATTERN_LEDGER_SOURCE_PATH.read_text(encoding="utf-8")
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
    ):
        assert needle not in source_text, (
            "I-PLEDGER-15 violated: pattern_ledger.py contains forbidden "
            f"text {needle!r}"
        )
