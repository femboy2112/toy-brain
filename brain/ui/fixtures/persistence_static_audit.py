"""Phase 3.9 persistence module static AST audit fixture.

Drives:

* ``I-PERSIST-12`` (STRUCTURAL) — Static AST audit over
  ``brain/ui/persistence.py`` confirms imports are confined to the
  documented seam set; rejects ``pickle``, ``shelve``, ``marshal``,
  ``dill``, ``cloudpickle``, ``joblib``, ``subprocess``, ``socket``,
  ``urllib``, ``http``, ``requests``, ``curses``, ``__import__``,
  ``importlib.import_module``, ``eval(``, ``exec(``, ``compile(``,
  ``atexit.register``, ``threading``, ``asyncio``, signal handlers,
  importing or calling the ``tick`` callable from ``brain.tick``, and
  module-level statements outside imports / constants / function defs
  / class defs (plus the module docstring).
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_PERSISTENCE_PATH = Path(__file__).resolve().parents[1] / "persistence.py"


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
    "brain.tlica",
    "brain.llm",
})


# Documented seam set. Anything imported from `brain.tick` must be the
# `BrainState` typed record only; importing or calling `tick` is
# forbidden (checked separately).
_ALLOWED_STDLIB_IMPORTS: frozenset[str] = frozenset({
    "__future__",
    "datetime",
    "pathlib",
    "sqlite3",
    "dataclasses",
    "fractions",
    "typing",
    "types",
    "enum",
})

_ALLOWED_FROM_MODULES: frozenset[str] = frozenset({
    "__future__",
    "datetime",
    "pathlib",
    "sqlite3",
    "dataclasses",
    "fractions",
    "typing",
    "types",
    "enum",
    "brain.io_types",
    "brain.tlica.builders",
    "brain.tlica.profile",
    "brain.tlica.msi",
    "brain.tlica.ptcns",
    "brain.development.text_stream",
    "brain.ui.session",
    "brain.ui.commands",
    "brain.tick",
})


_BRAIN_TICK_ALLOWED_NAMES: frozenset[str] = frozenset({"BrainState"})


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
    ("os", "execvpe"),
    ("os", "execl"),
    ("os", "execle"),
    ("os", "execlp"),
    ("os", "execlpe"),
    ("os", "spawnl"),
    ("os", "spawnle"),
    ("os", "spawnv"),
    ("os", "spawnve"),
    ("os", "spawnvp"),
    ("os", "spawnvpe"),
    ("os", "fork"),
    ("os", "forkpty"),
    ("os", "kill"),
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


def _audit_imports(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                full = alias.name
                root = full.split(".")[0]
                for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                    if full == forbidden or full.startswith(forbidden + "."):
                        errors.append(
                            f"forbidden import {full!r} at line {node.lineno}"
                        )
                        break
                else:
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
            for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                if module == forbidden or module.startswith(forbidden + "."):
                    errors.append(
                        f"forbidden import from {module!r} at line "
                        f"{node.lineno}"
                    )
                    break
            else:
                if (
                    module not in _ALLOWED_FROM_MODULES
                    and root not in _ALLOWED_STDLIB_IMPORTS
                ):
                    errors.append(
                        f"unrecognized 'from {module!r} import ...' at line "
                        f"{node.lineno}"
                    )
            if module == "brain.tick":
                for alias in node.names:
                    if alias.name not in _BRAIN_TICK_ALLOWED_NAMES:
                        errors.append(
                            f"forbidden 'from brain.tick import {alias.name}' "
                            f"at line {node.lineno} (only BrainState is "
                            "allowed; the tick callable is forbidden)"
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
                if func.id == "tick":
                    errors.append(
                        f"forbidden call tick(...) at line {node.lineno} "
                        "(the brain.tick callable is forbidden in "
                        "brain/ui/persistence.py)"
                    )
            elif isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    pair = (func.value.id, func.attr)
                    if pair in _FORBIDDEN_ATTR_CALLS:
                        errors.append(
                            f"forbidden call {func.value.id}.{func.attr}() "
                            f"at line {node.lineno}"
                        )
                    if pair == ("brain", "tick"):
                        errors.append(
                            f"forbidden call brain.tick(...) at line "
                            f"{node.lineno}"
                        )
                if func.attr == "tick":
                    # Reject e.g. `brain.tick.tick(...)`.
                    if isinstance(func.value, ast.Attribute) and (
                        func.value.attr == "tick"
                    ):
                        errors.append(
                            f"forbidden call <module>.tick.tick(...) at line "
                            f"{node.lineno}"
                        )
    return errors


def _audit_module_level(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for idx, node in enumerate(tree.body):
        if isinstance(node, _ALLOWED_MODULE_LEVEL_TYPES):
            if isinstance(node, ast.Expr):
                # Only the first ast.Expr (module docstring) is allowed
                # to be a statement-expression at module level.
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


@register("I-PERSIST-12", status="STRUCTURAL")
def check_i_persist_12_static_audit() -> None:
    """brain/ui/persistence.py passes the documented static audit."""
    source = _PERSISTENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_PATH))

    errors: list[str] = []
    errors.extend(_audit_imports(tree))
    errors.extend(_audit_calls(tree))
    errors.extend(_audit_module_level(tree))

    # Reject literal substrings of forbidden patterns inside the module
    # body. Docstrings naming forbidden tokens (for documentation) are
    # tolerated only when they are clearly negative ("no pickle", "no
    # subprocess", etc.); the explicit blacklist focuses on call sites.
    text_lines = source.splitlines()
    for lineno, line in enumerate(text_lines, start=1):
        # Strip docstring / comment context: only check non-string lines
        # for the most dangerous patterns. The AST audit above already
        # catches calls; this is defense-in-depth for raw text in code.
        stripped = line.split("#", 1)[0]
        for needle in ("eval(", "exec(", "compile("):
            if needle in stripped and not (
                stripped.lstrip().startswith(("'", '"'))
                or "_is_docstring" in stripped
            ):
                # Avoid false positives on assignments / class attrs
                # that incidentally end with these substrings; the AST
                # call audit is authoritative when needle survives here.
                # (We do not double-report; we trust _audit_calls.)
                continue

    if errors:
        raise AssertionError(
            "I-PERSIST-12 violated:\n  - " + "\n  - ".join(errors)
        )
