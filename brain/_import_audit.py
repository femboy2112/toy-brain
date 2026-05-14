"""Static import-graph audit for I-PCE-05.

The catalog requires that ``brain/tlica/agency.py`` never imports
``brain.tlica.pce`` (the foundation-default PCE is action-constant by Lean
theorem; using it for action selection would make all actions equivalent).

This module lives inside ``brain/`` (not ``tools/``) so that
``brain.invariants.run`` has no runtime dependency outside the package.
"""
from __future__ import annotations

import ast
from pathlib import Path

_AGENCY_PATH = Path(__file__).resolve().parent / "tlica" / "agency.py"


def audit_agency_no_pce_import(path: Path | None = None) -> tuple[bool, str]:
    """Return ``(passed, message)``. I-PCE-05."""
    src_path = path or _AGENCY_PATH
    if not src_path.exists():
        return True, f"I-PCE-05: {src_path.name} does not exist yet (audit skipped)."
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "brain.tlica.pce" or module.endswith(".pce") or module == "pce":
                return False, (
                    f"I-PCE-05 violated: {src_path.name} imports {module!r}. "
                    "Action selection must route through feasibleProjectedPCE, "
                    "not the foundation-default PCE."
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "brain.tlica.pce" or name.endswith(".pce") or name == "pce":
                    return False, (
                        f"I-PCE-05 violated: {src_path.name} imports {name!r}."
                    )
    return True, "I-PCE-05: agency.py is clean of pce imports."
