"""Phase 3.10b persistence_observe module static AST audit fixture.

Drives:

* ``I-OBSERVE-06`` (STRUCTURAL) — Static AST audit over
  ``brain/ui/persistence_observe.py`` confirms imports are confined to
  the documented seam set; rejects ``pickle``, ``shelve``, ``marshal``,
  ``dill``, ``cloudpickle``, ``joblib``, ``subprocess``, ``socket``,
  ``urllib``, ``http``, ``requests``, ``curses``, ``__import__``,
  ``importlib.import_module``, ``eval(``, ``exec(``, ``compile(``,
  ``atexit.register``, ``threading``, ``asyncio``, signal handlers,
  ``brain.tick``, ``brain.tlica`` internals beyond what
  ``brain.ui.persistence`` re-exports, and ``brain.llm``. Module-level
  statements are limited to imports, constants, function defs, and
  class defs (plus the module docstring).
* ``I-OBSERVE-10`` (STRUCTURAL) — Phase 3.10b defensive autosave-absent
  audit. The module contains no ``@atexit.register``, no
  ``threading.Thread`` / ``Timer``, no ``asyncio`` loop, no signal
  handler, no curses callback, and no ``save_session`` call site.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_PERSISTENCE_OBSERVE_PATH = (
    Path(__file__).resolve().parents[1] / "persistence_observe.py"
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
    "brain.tick",
    "brain.llm",
})


_ALLOWED_STDLIB_IMPORTS: frozenset[str] = frozenset({
    "__future__",
    "pathlib",
    "sqlite3",
    "dataclasses",
    "fractions",
    "typing",
})


#: Sub-modules of ``brain.tlica`` whose imports the corrigenda allows
#: into ``brain/ui/persistence_observe.py``. Section 6 of the catalog
#: patch plan permits ``brain.tlica.profile`` for ``COGITO_ID`` only.
_ALLOWED_FROM_MODULES: frozenset[str] = frozenset({
    "__future__",
    "pathlib",
    "sqlite3",
    "dataclasses",
    "fractions",
    "typing",
    "brain.io_types",
    "brain.tlica.profile",
    "brain.ui.persistence",
    "brain.ui.persistence_ops",
    "brain.ui.session",
})


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
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
})


_FORBIDDEN_CALL_FUNC_NAMES: frozenset[str] = frozenset({
    "save_session",
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
                        f"forbidden call {func.id!r}() at line {node.lineno}"
                    )
                if func.id in _FORBIDDEN_CALL_FUNC_NAMES:
                    errors.append(
                        f"forbidden call {func.id!r}() at line "
                        f"{node.lineno} (autosave-adjacent helper)"
                    )
                if func.id == "tick":
                    errors.append(
                        f"forbidden call tick(...) at line {node.lineno} "
                        "(brain.tick is forbidden in persistence_observe)"
                    )
            elif isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    pair = (func.value.id, func.attr)
                    if pair in _FORBIDDEN_ATTR_CALLS:
                        errors.append(
                            f"forbidden call {func.value.id}.{func.attr}() "
                            f"at line {node.lineno}"
                        )
                if func.attr in _FORBIDDEN_CALL_FUNC_NAMES:
                    errors.append(
                        f"forbidden call <module>.{func.attr}() at line "
                        f"{node.lineno} (autosave-adjacent helper)"
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
                    f"unexpected module-level expression at line {node.lineno}"
                )
            continue
        errors.append(
            f"unexpected module-level node {type(node).__name__} at "
            f"line {node.lineno}"
        )
    return errors


def _audit_no_decorators(tree: ast.Module) -> list[str]:
    """Defensive autosave-absent: no @atexit.register-style decorators."""
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for deco in node.decorator_list:
                deco_str = ast.unparse(deco)
                for needle in (
                    "atexit.register",
                    "atexit",
                    "signal.signal",
                ):
                    if needle in deco_str:
                        errors.append(
                            f"forbidden decorator {deco_str!r} on "
                            f"{node.name!r} at line {node.lineno}"
                        )
                        break
    return errors


def _audit_tlica_imports(tree: ast.Module) -> list[str]:
    """Only ``brain.tlica.profile`` (COGITO_ID) is permitted from tlica.

    Drives the section-6 corrigenda clause: persistence_observe.py may
    import from ``brain.tlica.profile`` (to access ``COGITO_ID``) but
    must not import any other ``brain.tlica.*`` submodule. ``brain.tlica.X``
    where X is not ``profile`` is rejected.
    """
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("brain.tlica") and module != "brain.tlica.profile":
                errors.append(
                    f"forbidden 'from {module!r} import ...' at line "
                    f"{node.lineno} (only brain.tlica.profile permitted)"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("brain.tlica") and alias.name != "brain.tlica.profile":
                    errors.append(
                        f"forbidden import {alias.name!r} at line "
                        f"{node.lineno} (only brain.tlica.profile permitted)"
                    )
    return errors


@register("I-OBSERVE-06", status="STRUCTURAL")
def check_i_observe_06_static_audit() -> None:
    """brain/ui/persistence_observe.py passes the documented static audit."""
    source = _PERSISTENCE_OBSERVE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_OBSERVE_PATH))

    errors: list[str] = []
    errors.extend(_audit_imports(tree))
    errors.extend(_audit_calls(tree))
    errors.extend(_audit_module_level(tree))
    errors.extend(_audit_tlica_imports(tree))

    if errors:
        raise AssertionError(
            "I-OBSERVE-06 violated:\n  - " + "\n  - ".join(errors)
        )


@register("I-OBSERVE-10", status="STRUCTURAL")
def check_i_observe_10_autosave_absent() -> None:
    """brain/ui/persistence_observe.py contains no autosave entry point."""
    source = _PERSISTENCE_OBSERVE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_OBSERVE_PATH))

    errors: list[str] = []
    errors.extend(_audit_no_decorators(tree))
    # No save_session call sites (re-checked via call audit).
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _FORBIDDEN_CALL_FUNC_NAMES:
                errors.append(
                    f"forbidden call {func.id!r}() at line {node.lineno} "
                    "(persistence_observe must not register an autosave path)"
                )
            elif isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_CALL_FUNC_NAMES:
                errors.append(
                    f"forbidden call <module>.{func.attr}() at line "
                    f"{node.lineno} (persistence_observe must not register an "
                    "autosave path)"
                )
    # No threading / asyncio / signal / atexit module-level imports
    # (the import audit already catches these; we duplicate here so the
    # row failure message is specific).
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in {
                    "threading", "asyncio", "signal", "atexit",
                }:
                    errors.append(
                        f"forbidden module import {alias.name!r} at line "
                        f"{node.lineno} (autosave-adjacent)"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in {
                "threading", "asyncio", "signal", "atexit",
            }:
                errors.append(
                    f"forbidden 'from {module!r} import ...' at line "
                    f"{node.lineno} (autosave-adjacent)"
                )

    if errors:
        raise AssertionError(
            "I-OBSERVE-10 violated:\n  - " + "\n  - ".join(errors)
        )
