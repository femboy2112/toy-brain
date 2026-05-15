"""Fixtures for I-STRM-12, I-STRM-14, I-STRM-15: static audit of text_stream.py.

The audit is local to this fixture and does not extend
``tools.import_audit``.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_TEXT_STREAM_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "text_stream.py"
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
    "brain.tick",
    "brain.ui",
)


def _parse_module() -> ast.Module:
    source = _TEXT_STREAM_SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_TEXT_STREAM_SOURCE_PATH))


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


@register("I-STRM-12", status="STRUCTURAL")
def check_text_stream_has_no_forbidden_imports() -> None:
    assert _TEXT_STREAM_SOURCE_PATH.exists(), (
        f"I-STRM-12 violated: text_stream.py not found at {_TEXT_STREAM_SOURCE_PATH}"
    )
    tree = _parse_module()
    bad = [name for name in _import_targets(tree) if _is_forbidden_import(name)]
    assert not bad, (
        f"I-STRM-12 violated: text_stream.py imports forbidden modules {bad}"
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


@register("I-STRM-15", status="STRUCTURAL")
def check_text_stream_constructors_pure_no_callbacks() -> None:
    tree = _parse_module()
    for stmt in _module_level_statements(tree):
        assert _is_allowed_module_level(stmt), (
            "I-STRM-15 violated: disallowed module-level statement "
            f"{type(stmt).__name__} at line {stmt.lineno}"
        )

    for call in _module_level_calls(tree):
        name = _call_name(call)
        assert name not in _FORBIDDEN_MODULE_LEVEL_CALLS, (
            f"I-STRM-15 violated: forbidden module-level call {name!r}"
        )
        for bad_prefix in ("atexit.", "signal."):
            assert not name.startswith(bad_prefix), (
                f"I-STRM-15 violated: forbidden module-level call {name!r}"
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
                    "I-STRM-15 violated: text_stream.py reaches into "
                    f"{bad!r} via call {name!r}"
                )


_COUNT_PATH_FUNCTIONS: frozenset[str] = frozenset({
    "extract_stream_features",
    "extract_segment_candidates",
    "make_stream_pattern",
    "make_stream_promotion_candidate",
    "make_text_stream_chunk",
    "_require_int_nonneg",
    "_require_bounded_printable",
})

_COUNT_PATH_CLASSES: tuple[str, ...] = (
    "TextStreamChunk",
    "TextStreamHistory",
    "StreamFeatureVector",
    "SegmentCandidate",
    "StreamPattern",
    "StreamPromotionCandidate",
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


@register("I-STRM-14", status="STRUCTURAL")
def check_text_stream_has_no_float_round_math() -> None:
    tree = _parse_module()
    fns = _find_functions(tree, _COUNT_PATH_FUNCTIONS)
    for class_name in _COUNT_PATH_CLASSES:
        post_init = _find_class_post_init(tree, class_name)
        assert post_init is not None, (
            f"I-STRM-14 violated: {class_name}.__post_init__ not found"
        )
        fns.append(post_init)

    for fn in fns:
        for call in _calls_in(fn):
            name = _call_name(call)
            if name == "float" or name == "round":
                raise AssertionError(
                    "I-STRM-14 violated: count/statistic-path function "
                    f"{fn.name!r} calls {name}() at line {call.lineno}"
                )
            if name.startswith("math."):
                raise AssertionError(
                    "I-STRM-14 violated: count/statistic-path function "
                    f"{fn.name!r} calls {name}() at line {call.lineno}"
                )

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "math":
            raise AssertionError(
                "I-STRM-14 violated: text_stream.py imports from math"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "math":
                    raise AssertionError(
                        "I-STRM-14 violated: text_stream.py imports math"
                    )
