"""Phase 3.8b LLM runtime static audit fixture.

Drives:

* ``I-LLMTOG-13`` (STRUCTURAL) — Static AST audit over
  ``brain/ui/llm_runtime.py`` and the toggle path additions in
  ``brain/ui/__main__.py`` rejects imports of ``curses``,
  ``brain.tlica``, ``brain.tick``, and anything outside the
  documented seam set; module-level statements other than imports,
  constants, function defs, and class defs are rejected (no
  ``@atexit``, no module-load subprocess call, no module-load HTTP
  probe).
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_REPO_BRAIN_UI = Path(__file__).resolve().parents[1]
_REPO_BRAIN = _REPO_BRAIN_UI.parent
_LLM_RUNTIME_PATH = _REPO_BRAIN_UI / "llm_runtime.py"
_MAIN_PATH = _REPO_BRAIN_UI / "__main__.py"
_LLM_CLIENT_PATH = _REPO_BRAIN / "llm" / "client.py"

# Forbidden import roots for brain/ui/llm_runtime.py. The patch plan
# section 4 + the corrigenda ruling H scope the toggle helper's
# permitted imports to stdlib + brain.llm.client + brain.ui.__main__.
# `os` is allowed only for read-only PATH resolution + os.environ; the
# os.<attr> audit below rejects os.system / os.exec* / os.spawn* etc.
_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset({
    "curses",
    "brain.tlica",
    "brain.tick",
    "socket",
    "urllib",
    "http",
    "requests",
    "tempfile",
    "shutil",
    "subprocess",
})

# Imports specifically allowed in brain/ui/llm_runtime.py beyond stdlib.
# The seam set lets the helper import the LLM client backends and the
# OfflineStandInClient from brain.ui.__main__ for the OFFLINE factory.
_ALLOWED_LLM_RUNTIME_IMPORTS: frozenset[str] = frozenset({
    "brain.llm.client",
    "brain.ui.__main__",
})

# Standard library imports the static audit explicitly allows in
# brain/ui/llm_runtime.py.
_ALLOWED_STDLIB_IMPORTS: frozenset[str] = frozenset({
    "__future__",
    "os",              # os.path / os.environ["PATH"] / os.access only
    "dataclasses",
    "enum",
    "pathlib",
    "typing",
})

# Allowed module-level node types (everything else is rejected).
_ALLOWED_MODULE_LEVEL_TYPES: tuple = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Assign,           # constants
    ast.AnnAssign,        # typed constants
    ast.Expr,             # docstrings only — guarded below
)


_FORBIDDEN_OS_ATTRS: frozenset[str] = frozenset({
    "system",
    "popen",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "spawnl",
    "spawnle",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "fork",
    "forkpty",
    "kill",
})


def _audit_llm_runtime_imports(tree: ast.Module) -> list[str]:
    """Audit imports in brain/ui/llm_runtime.py."""
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                full = alias.name
                # Forbidden tokens win.
                for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                    if full == forbidden or full.startswith(forbidden + "."):
                        errors.append(
                            f"forbidden import {full!r} at line {node.lineno}"
                        )
                # If not forbidden, must be allowed.
                if (
                    full not in _ALLOWED_STDLIB_IMPORTS
                    and full not in _ALLOWED_LLM_RUNTIME_IMPORTS
                    and root not in _ALLOWED_STDLIB_IMPORTS
                ):
                    errors.append(
                        f"unrecognized import {full!r} at line {node.lineno}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                if module == forbidden or module.startswith(forbidden + "."):
                    errors.append(
                        f"forbidden import-from {module!r} at line {node.lineno}"
                    )
            # Allowed roots.
            if not (
                module in _ALLOWED_STDLIB_IMPORTS
                or module in _ALLOWED_LLM_RUNTIME_IMPORTS
                or module.split(".")[0] in _ALLOWED_STDLIB_IMPORTS
            ):
                errors.append(
                    f"unrecognized import-from {module!r} "
                    f"at line {node.lineno}"
                )
        # Reject os.<forbidden> attribute access (os.system, os.exec*, etc.).
        elif isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and node.attr in _FORBIDDEN_OS_ATTRS
            ):
                errors.append(
                    f"forbidden attribute os.{node.attr} at line {node.lineno}"
                )
    return errors


def _audit_module_level_shape(tree: ast.Module, name: str) -> list[str]:
    """Reject module-level side effects in the given module."""
    errors: list[str] = []
    for stmt in tree.body:
        if isinstance(stmt, _ALLOWED_MODULE_LEVEL_TYPES):
            # Expr at module level must be a docstring (str constant).
            if isinstance(stmt, ast.Expr):
                if not (
                    isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)
                ):
                    errors.append(
                        f"non-docstring module-level Expr in {name} at "
                        f"line {stmt.lineno}"
                    )
            continue
        errors.append(
            f"disallowed module-level statement {type(stmt).__name__} in "
            f"{name} at line {stmt.lineno}"
        )

    # Reject decorator usage at module level that could install hooks
    # (e.g. @atexit.register). Decorator audit walks function/class defs.
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                src = ast.unparse(dec)
                if "atexit" in src.lower():
                    errors.append(
                        f"forbidden atexit decorator in {name} at line "
                        f"{node.lineno}"
                    )
    return errors


def _audit_main_toggle_calls(tree: ast.Module) -> list[str]:
    """Audit that __main__.py uses parse_llm_runtime_args + factory.

    We confirm the imports `parse_llm_runtime_args` and
    `build_llm_client_from_config` appear, and that no second
    classification path (a direct AnthropicAPIClient / ClaudeCLIClient /
    MockClient construction) exists at module level in __main__.py.
    """
    errors: list[str] = []
    found_parse = False
    found_factory = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "brain.ui.llm_runtime":
            for alias in node.names:
                if alias.name == "parse_llm_runtime_args":
                    found_parse = True
                if alias.name == "build_llm_client_from_config":
                    found_factory = True
        if isinstance(node, ast.Call):
            func_src = ast.unparse(node.func)
            for forbidden in (
                "AnthropicAPIClient",
                "ClaudeCLIClient",
                "MockClient",
                "CachedClient",
            ):
                if func_src.endswith(forbidden):
                    errors.append(
                        f"__main__.py constructs {forbidden} directly at "
                        f"line {node.lineno} (must go through "
                        "build_llm_client_from_config)"
                    )
    if not found_parse:
        errors.append(
            "__main__.py does not import parse_llm_runtime_args from "
            "brain.ui.llm_runtime"
        )
    if not found_factory:
        errors.append(
            "__main__.py does not import build_llm_client_from_config "
            "from brain.ui.llm_runtime"
        )
    return errors


def _audit_llm_client_codex_class(tree: ast.Module) -> list[str]:
    """Audit that ``brain/llm/client.py`` defines CodexCLIClient and
    keeps the existing backends intact (Phase 3.11 extension).

    The new class must be a dataclass with the locked default
    command tuple ``("codex", "exec")``; the surrounding classes
    (``ClaudeCLIClient`` etc.) must remain present. We do not police
    the class body here beyond a presence check; the construction
    semantics are covered by I-LLMTOG-17.
    """
    errors: list[str] = []
    expected_classes = frozenset({
        "AnthropicAPIClient",
        "MockClient",
        "CachedClient",
        "ClaudeCLIClient",
        "CodexCLIClient",
    })
    found_classes: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            found_classes.add(node.name)
    missing = expected_classes - found_classes
    if missing:
        errors.append(
            "brain/llm/client.py missing expected classes: "
            + ", ".join(sorted(missing))
        )
    return errors


@register("I-LLMTOG-13", status="STRUCTURAL")
def check_I_LLMTOG_13_static_audit() -> None:
    runtime_source = _LLM_RUNTIME_PATH.read_text(encoding="utf-8")
    main_source = _MAIN_PATH.read_text(encoding="utf-8")
    client_source = _LLM_CLIENT_PATH.read_text(encoding="utf-8")
    runtime_tree = ast.parse(runtime_source, filename=str(_LLM_RUNTIME_PATH))
    main_tree = ast.parse(main_source, filename=str(_MAIN_PATH))
    client_tree = ast.parse(client_source, filename=str(_LLM_CLIENT_PATH))

    errors: list[str] = []
    errors += _audit_llm_runtime_imports(runtime_tree)
    errors += _audit_module_level_shape(runtime_tree, "brain/ui/llm_runtime.py")
    errors += _audit_main_toggle_calls(main_tree)
    errors += _audit_llm_client_codex_class(client_tree)

    if errors:
        raise AssertionError(
            "I-LLMTOG-13 violated: " + "; ".join(errors)
        )
