"""Phase 3.10c single-save-path audit fixture.

Drives:

* ``I-AUTOSAVE-11`` (REQUIRED) — autosave reuses :func:`save_session`;
  no second save code path exists. Static AST audit confirms
  ``brain/ui/autosave.py`` imports ``save_session`` from
  :mod:`brain.ui.persistence` and contains no other save helper
  definition or import; the audit also confirms exactly one
  ``save_session`` helper definition exists in
  :mod:`brain.ui.persistence`.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_AUTOSAVE_PATH = (
    Path(__file__).resolve().parents[1] / "autosave.py"
)
_PERSISTENCE_PATH = (
    Path(__file__).resolve().parents[1] / "persistence.py"
)


def _collect_save_definitions(tree: ast.Module) -> list[str]:
    """Return the names of every ``def save_*`` / ``class Save*`` node."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("save_") or node.name == "save":
                names.append(node.name)
    return names


def _collect_save_session_imports(tree: ast.Module) -> list[tuple[str, str]]:
    """Return every ``from M import save_session`` entry as ``(M, alias)``."""
    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "save_session":
                    out.append((module, alias.asname or alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith(".save_session"):
                    out.append((alias.name, alias.asname or alias.name))
    return out


@register("I-AUTOSAVE-11", status="REQUIRED")
def check_i_autosave_11_single_save_path() -> None:
    # brain/ui/autosave.py: no save_* helper definition; the only
    # save_session reference is the import from brain.ui.persistence.
    autosave_source = _AUTOSAVE_PATH.read_text(encoding="utf-8")
    autosave_tree = ast.parse(autosave_source, filename=str(_AUTOSAVE_PATH))
    autosave_defs = _collect_save_definitions(autosave_tree)
    if autosave_defs:
        raise AssertionError(
            "I-AUTOSAVE-11 violated: brain/ui/autosave.py defines a "
            f"save_* helper ({autosave_defs!r})"
        )
    imports = _collect_save_session_imports(autosave_tree)
    if not any(
        module == "brain.ui.persistence"
        for module, _alias in imports
    ):
        raise AssertionError(
            "I-AUTOSAVE-11 violated: brain/ui/autosave.py does not "
            "import save_session from brain.ui.persistence "
            f"(imports={imports!r})"
        )
    for module, _alias in imports:
        if module != "brain.ui.persistence":
            raise AssertionError(
                "I-AUTOSAVE-11 violated: brain/ui/autosave.py imports "
                f"save_session from {module!r} (only "
                "brain.ui.persistence is allowed)"
            )

    # brain/ui/persistence.py: exactly one top-level save_session
    # function definition.
    persistence_source = _PERSISTENCE_PATH.read_text(encoding="utf-8")
    persistence_tree = ast.parse(
        persistence_source, filename=str(_PERSISTENCE_PATH)
    )
    save_session_defs = [
        node
        for node in ast.walk(persistence_tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "save_session"
    ]
    if len(save_session_defs) != 1:
        raise AssertionError(
            "I-AUTOSAVE-11 violated: brain/ui/persistence.py has "
            f"{len(save_session_defs)} save_session definitions "
            "(expected exactly 1)"
        )

    # No save_session definition lives anywhere else under brain/ui/.
    ui_root = _AUTOSAVE_PATH.parent
    rogue: list[str] = []
    for path in sorted(ui_root.rglob("*.py")):
        if path == _PERSISTENCE_PATH:
            continue
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "save_session":
                rogue.append(f"{path}:{node.lineno}")
    if rogue:
        raise AssertionError(
            "I-AUTOSAVE-11 violated: a second save_session definition "
            f"exists under brain/ui/: {rogue!r}"
        )
