"""Static import-graph audit for I-PCE-05.

The catalog requires that ``brain/tlica/agency.py`` never imports
``brain.tlica.pce`` (the foundation-default PCE is action-constant by Lean
theorem; using it for action selection would make all actions equivalent).

This module lives inside ``brain/`` (not ``tools/``) so that
``brain.invariants.run`` has no runtime dependency outside the package.

Phase 2 v1.2 corrigenda (C1): the AST walker now also catches
``from brain.tlica import pce`` (where ``node.module == "brain.tlica"``
and ``"pce"`` appears in ``node.names``). The walker is factored into a
pure helper ``_audit_pce_imports`` so the negative case is testable.
"""
from __future__ import annotations

import ast
from pathlib import Path

_AGENCY_PATH = Path(__file__).resolve().parent / "tlica" / "agency.py"


def _audit_pce_imports(tree: ast.Module, filename: str) -> tuple[bool, str]:
    """Pure AST audit over a parsed module.

    Returns ``(passed, message)`` for the supplied AST + label. Tests
    construct synthetic trees and call this directly; the public
    ``audit_agency_no_pce_import`` reads ``brain/tlica/agency.py`` from
    disk and delegates here.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = {alias.name for alias in node.names}

            # Form: ``from brain.tlica import pce`` — module is the
            # parent package and the alias surfaces the leaf. Previously
            # missed because the audit only inspected ``node.module``.
            if module == "brain.tlica" and "pce" in names:
                return False, (
                    f"I-PCE-05 violated: {filename} imports pce from brain.tlica. "
                    "Action selection must route through feasibleProjectedPCE, "
                    "not the foundation-default PCE."
                )

            # Form: ``from brain.tlica.pce import ...`` (any submodule
            # whose name ends in ``.pce`` or whose name is bare ``pce``).
            if (
                module == "brain.tlica.pce"
                or module.endswith(".pce")
                or module == "pce"
            ):
                return False, (
                    f"I-PCE-05 violated: {filename} imports {module!r}. "
                    "Action selection must route through feasibleProjectedPCE, "
                    "not the foundation-default PCE."
                )

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if (
                    name == "brain.tlica.pce"
                    or name.endswith(".pce")
                    or name == "pce"
                ):
                    return False, (
                        f"I-PCE-05 violated: {filename} imports {name!r}. "
                        "Action selection must route through feasibleProjectedPCE, "
                        "not the foundation-default PCE."
                    )

    return True, f"I-PCE-05: {filename} is clean of pce imports."


def audit_agency_no_pce_import(path: Path | None = None) -> tuple[bool, str]:
    """Return ``(passed, message)``. I-PCE-05.

    Public entry point. Reads the canonical ``brain/tlica/agency.py``
    (or ``path`` if supplied), parses it, and runs ``_audit_pce_imports``.
    """
    src_path = path or _AGENCY_PATH
    if not src_path.exists():
        return True, f"I-PCE-05: {src_path.name} does not exist yet (audit skipped)."
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    return _audit_pce_imports(tree, src_path.name)
