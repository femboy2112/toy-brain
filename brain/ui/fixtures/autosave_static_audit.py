"""Phase 3.10c autosave module static AST audit fixture.

Drives:

* ``I-AUTOSAVE-13`` (STRUCTURAL) — Static AST audit over
  ``brain/ui/autosave.py``. Imports are confined to the documented
  seam set (``dataclasses``, ``datetime``, ``enum``, ``pathlib``,
  ``typing``, ``brain.io_types`` (if needed), ``brain.ui.commands``,
  ``brain.ui.persistence``, ``brain.ui.persistence_ops``,
  ``brain.ui.session``). The module imports neither ``pickle``,
  ``shelve``, ``marshal``, ``dill``, ``cloudpickle``, ``joblib``,
  ``subprocess``, ``socket``, ``urllib``, ``http``, ``requests``,
  ``curses``, ``brain.tick``, ``brain.tlica`` internals, nor
  ``brain.llm``. It contains no ``importlib.import_module``,
  ``__import__``, ``eval(``, ``exec(``, ``compile(``,
  ``atexit.register``, ``threading``, ``asyncio``, or signal handler.
  No ``tick(`` call appears anywhere. Module-level statements are
  limited to imports, constants, function defs, and class defs (plus
  the module docstring).
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_AUTOSAVE_PATH = (
    Path(__file__).resolve().parents[1] / "autosave.py"
)


_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset({
    "pickle",
    "shelve",
    "marshal",
    "dill",
    "cloudpickle",
    "joblib",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "curses",
    "threading",
    "asyncio",
    "signal",
    "atexit",
    "tempfile",
    "shutil",
    "ctypes",
    "sqlite3",
    "brain.tick",
    "brain.tlica",
    "brain.llm",
})


_ALLOWED_STDLIB_IMPORTS: frozenset[str] = frozenset({
    "__future__",
    "datetime",
    "pathlib",
    "dataclasses",
    "enum",
    "typing",
})


_ALLOWED_FROM_MODULES: frozenset[str] = frozenset({
    "__future__",
    "datetime",
    "pathlib",
    "dataclasses",
    "enum",
    "typing",
    "brain.io_types",
    "brain.ui.commands",
    "brain.ui.persistence",
    "brain.ui.persistence_ops",
    "brain.ui.session",
})


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "tick",
})


_FORBIDDEN_ATTR_CALLS: frozenset[tuple[str, str]] = frozenset({
    ("importlib", "import_module"),
    ("importlib", "reload"),
    ("atexit", "register"),
    ("os", "system"),
    ("os", "popen"),
    ("os", "exec"),
    ("os", "execv"),
    ("os", "execve"),
    ("os", "execvp"),
    ("os", "fork"),
    ("os", "kill"),
    ("signal", "signal"),
    ("threading", "Thread"),
    ("threading", "Timer"),
    ("asyncio", "run"),
    ("asyncio", "get_event_loop"),
    ("asyncio", "new_event_loop"),
    ("curses", "wrapper"),
})


_ALLOWED_MODULE_LEVEL_TYPES: tuple = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Assign,
    ast.AnnAssign,
    ast.Expr,
)


def _is_docstring(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_forbidden_root(name: str) -> bool:
    for forbidden in _FORBIDDEN_IMPORT_ROOTS:
        if name == forbidden or name.startswith(forbidden + "."):
            return True
    return False


def _audit_imports(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                full = alias.name
                root = full.split(".")[0]
                if full in _ALLOWED_FROM_MODULES:
                    continue
                if _is_forbidden_root(full):
                    errors.append(
                        f"forbidden import {full!r} at line {node.lineno}"
                    )
                    continue
                if (
                    full not in _ALLOWED_STDLIB_IMPORTS
                    and root not in _ALLOWED_STDLIB_IMPORTS
                ):
                    errors.append(
                        f"unrecognized import {full!r} at line "
                        f"{node.lineno}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0] if module else ""
            if module in _ALLOWED_FROM_MODULES:
                continue
            if _is_forbidden_root(module):
                errors.append(
                    f"forbidden import from {module!r} at line "
                    f"{node.lineno}"
                )
                continue
            if (
                module not in _ALLOWED_FROM_MODULES
                and root not in _ALLOWED_STDLIB_IMPORTS
            ):
                errors.append(
                    f"unrecognized 'from {module!r} import ...' at line "
                    f"{node.lineno}"
                )
    return errors


def _audit_calls(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id in _FORBIDDEN_CALL_NAMES:
                    errors.append(
                        f"forbidden call {func.id!r}() at line "
                        f"{node.lineno}"
                    )
            elif isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    pair = (func.value.id, func.attr)
                    if pair in _FORBIDDEN_ATTR_CALLS:
                        errors.append(
                            f"forbidden call {func.value.id}.{func.attr}() "
                            f"at line {node.lineno}"
                        )
                if func.attr == "tick":
                    errors.append(
                        f"forbidden call <...>.tick(...) at line "
                        f"{node.lineno} (autosave must not call tick)"
                    )
    return errors


def _audit_module_level(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for idx, node in enumerate(tree.body):
        if isinstance(node, _ALLOWED_MODULE_LEVEL_TYPES):
            if isinstance(node, ast.Expr):
                if idx == 0 and _is_docstring(node):
                    continue
                errors.append(
                    f"unexpected module-level expression at line "
                    f"{node.lineno}"
                )
            continue
        errors.append(
            f"unexpected module-level node {type(node).__name__} at "
            f"line {node.lineno}"
        )
    return errors


def _audit_no_decorators(tree: ast.Module) -> list[str]:
    """No @atexit.register / threading / asyncio / signal handler decorators."""
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            for deco in node.decorator_list:
                deco_str = ast.unparse(deco)
                for needle in (
                    "atexit.register",
                    "atexit",
                    "signal.signal",
                    "threading",
                    "asyncio",
                ):
                    if needle in deco_str:
                        errors.append(
                            f"forbidden decorator {deco_str!r} on "
                            f"{node.name!r} at line {node.lineno}"
                        )
                        break
    return errors


def _audit_no_tick_text(source: str, tree: ast.Module) -> list[str]:
    """Reject any literal ``tick(`` substring in the module body code.

    Defense in depth on top of the AST call audit: an autosave path
    that calls ``tick(...)`` is a hard guard rail. The AST walk above
    catches every Call node; this textual check catches any string
    literal that *could* be parsed and eval'd downstream. The module
    docstring and the line ranges spanned by string-literal docstring
    bodies inside class / function defs are exempt: those are
    documentation prose, not executable code.
    """
    # Collect the line ranges covered by every docstring constant
    # (module-level + every class/function docstring).
    docstring_lines: set[int] = set()
    body_iters = [tree.body]
    for body in body_iters:
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            start = first.lineno
            end = getattr(first, "end_lineno", start)
            for line in range(start, end + 1):
                docstring_lines.add(line)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            body_iters.append(node.body)
            if node.body:
                first = node.body[0]
                if (
                    isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)
                ):
                    start = first.lineno
                    end = getattr(first, "end_lineno", start)
                    for line in range(start, end + 1):
                        docstring_lines.add(line)

    errors: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if lineno in docstring_lines:
            continue
        stripped = line.split("#", 1)[0]
        if "tick(" in stripped:
            errors.append(
                f"forbidden literal 'tick(' at line {lineno}"
            )
    return errors


@register("I-AUTOSAVE-13", status="STRUCTURAL")
def check_i_autosave_13_static_audit() -> None:
    source = _AUTOSAVE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_AUTOSAVE_PATH))

    errors: list[str] = []
    errors.extend(_audit_imports(tree))
    errors.extend(_audit_calls(tree))
    errors.extend(_audit_module_level(tree))
    errors.extend(_audit_no_decorators(tree))
    errors.extend(_audit_no_tick_text(source, tree))

    if errors:
        raise AssertionError(
            "I-AUTOSAVE-13 violated:\n  - " + "\n  - ".join(errors)
        )
