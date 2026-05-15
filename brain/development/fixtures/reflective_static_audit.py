"""Fixtures for I-REF-09, I-REF-11, and I-REF-12: static audit of reflective.py.

The audit is local to this fixture and does not extend
``tools.import_audit``.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_REFLECTIVE_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "reflective.py"
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
    "brain.tlica",
    "brain.tick",
)


def _parse_reflective_module() -> ast.Module:
    source = _REFLECTIVE_SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_REFLECTIVE_SOURCE_PATH))


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
    return False


@register("I-REF-09", status="STRUCTURAL")
def check_reflective_module_has_no_forbidden_imports() -> None:
    assert _REFLECTIVE_SOURCE_PATH.exists(), (
        f"I-REF-09 violated: reflective.py not found at {_REFLECTIVE_SOURCE_PATH}"
    )
    tree = _parse_reflective_module()
    bad = [name for name in _import_targets(tree) if _is_forbidden_import(name)]
    assert not bad, (
        f"I-REF-09 violated: reflective.py imports forbidden modules {bad}"
    )


def _module_level_statements(tree: ast.Module) -> list[ast.stmt]:
    return list(tree.body)


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


def _is_under_function_or_class(root: ast.stmt, target: ast.Call) -> bool:
    for node in ast.walk(root):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            for child in ast.walk(node):
                if child is target:
                    return True
    return False


def _module_level_calls(tree: ast.Module) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for stmt in tree.body:
        for node in ast.walk(stmt):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                continue
            if isinstance(node, ast.Call):
                if not _is_under_function_or_class(stmt, node):
                    calls.append(node)
    return calls


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


_FORBIDDEN_MODULE_LEVEL_CALLS: tuple[str, ...] = (
    "atexit.register",
    "signal.signal",
    "open",
)


@register("I-REF-12", status="STRUCTURAL")
def check_reflective_constructors_pure_no_callbacks() -> None:
    tree = _parse_reflective_module()
    for stmt in _module_level_statements(tree):
        assert _is_allowed_module_level(stmt), (
            "I-REF-12 violated: disallowed module-level statement "
            f"{type(stmt).__name__} at line {stmt.lineno}"
        )

    for call in _module_level_calls(tree):
        name = _call_name(call)
        assert name not in _FORBIDDEN_MODULE_LEVEL_CALLS, (
            f"I-REF-12 violated: forbidden module-level call {name!r}"
        )
        for bad_prefix in ("atexit.", "signal."):
            assert not name.startswith(bad_prefix), (
                f"I-REF-12 violated: forbidden module-level call {name!r}"
            )

    forbidden_call_substrings = (
        "brain.ui",
        "brain.tlica",
        "brain.llm",
        "brain.tick",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            for bad in forbidden_call_substrings:
                assert bad not in name, (
                    "I-REF-12 violated: reflective.py reaches into "
                    f"{bad!r} via call {name!r}"
                )


# ---------------------------------------------------------------------------
# I-REF-11 — no float / round / math on the count / statistic path.
#
# Reachable functions: make_reflective_snapshot, make_reflective_summary,
# the make_reflective_item_from_* bridges, plus the helpers
# _enum_kind_name and _require_int_nonneg, plus the __post_init__ of the
# three frozen records.
# ---------------------------------------------------------------------------


_COUNT_PATH_FUNCTIONS: frozenset[str] = frozenset({
    "make_reflective_snapshot",
    "make_reflective_summary",
    "make_reflective_item_from_output_history",
    "make_reflective_item_from_worldlet_history",
    "make_reflective_item_from_proto_basic_history",
    "make_reflective_item_from_expression_history",
    "make_reflective_item_from_operator_transcript",
    "_enum_kind_name",
    "_require_int_nonneg",
})

_COUNT_PATH_CLASSES: tuple[str, ...] = (
    "ReflectiveSummaryItem",
    "ReflectiveInspectionSnapshot",
    "ReflectiveInspectionSummary",
)


def _find_functions(
    tree: ast.Module, names: frozenset[str]
) -> list[ast.FunctionDef]:
    out: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in names:
            out.append(node)
    return out


def _find_class_post_init(
    tree: ast.Module, class_name: str
) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for body in node.body:
                if (
                    isinstance(body, ast.FunctionDef)
                    and body.name == "__post_init__"
                ):
                    return body
    return None


def _calls_in(fn: ast.FunctionDef) -> list[ast.Call]:
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call)]


@register("I-REF-11", status="STRUCTURAL")
def check_reflective_module_has_no_float_round_math() -> None:
    tree = _parse_reflective_module()
    fns = _find_functions(tree, _COUNT_PATH_FUNCTIONS)
    for class_name in _COUNT_PATH_CLASSES:
        post_init = _find_class_post_init(tree, class_name)
        assert post_init is not None, (
            f"I-REF-11 violated: {class_name}.__post_init__ not found"
        )
        fns.append(post_init)

    for fn in fns:
        for call in _calls_in(fn):
            name = _call_name(call)
            if name == "float" or name == "round":
                raise AssertionError(
                    "I-REF-11 violated: count/statistic-path function "
                    f"{fn.name!r} calls {name}() at line {call.lineno}"
                )
            if name.startswith("math."):
                raise AssertionError(
                    "I-REF-11 violated: count/statistic-path function "
                    f"{fn.name!r} calls {name}() at line {call.lineno}"
                )

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "math":
            raise AssertionError(
                "I-REF-11 violated: reflective.py imports from math"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "math":
                    raise AssertionError(
                        "I-REF-11 violated: reflective.py imports math"
                    )
