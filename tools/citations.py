"""Verify that every `<file>::<decl>` citation in the catalog resolves to a
real Lean declaration in `lean_reference/`.

A "match" means the file exists under `lean_reference/` (anywhere in TLICA/ or
at the root) and contains a line beginning with one of the declaration-class
keywords followed by `<decl>` as its first identifier.

CLI:
    python -m tools.citations verify
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from tools.catalog import REPO_ROOT, load_catalog

LEAN_REF = REPO_ROOT / "lean_reference"

_DECL_KEYWORDS = ("theorem", "def", "structure", "class", "inductive", "abbrev")
_DECL_LINE_RE = re.compile(
    rf"^\s*(?:@\[[^\]]*\]\s*)?(?:noncomputable\s+)?(?:{'|'.join(_DECL_KEYWORDS)})\s+([A-Za-z_][A-Za-z0-9_'.]*)"
)
# Catalog citations look like `Profile.lean::ScalarProfile.toFun_nonneg` or
# `ProfileComparison/Pointwise.lean::dInfUnion`.
_CITATION_RE = re.compile(r"`([A-Za-z][A-Za-z0-9_/]*\.lean)::([A-Za-z_][A-Za-z0-9_'.]*)`")


def _find_lean_file(filename: str) -> Path | None:
    candidates = list(LEAN_REF.rglob(filename))
    if candidates:
        return candidates[0]
    return None


def _file_has_decl(path: Path, decl: str) -> bool:
    # Match either fully-qualified `Namespace.foo.<short_decl>` or short.
    # We accept any line declaring `<short>` where short is the last segment.
    short = decl.split(".")[-1]
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _DECL_LINE_RE.match(line)
        if m and m.group(1).split(".")[-1] == short:
            return True
        # Also accept structure field declarations (the catalog cites
        # `ProjectMap` field `noAction` etc.). These appear as `noAction : ...`
        # inside a structure body. Recognize as a bare identifier followed by `:`.
        stripped = line.strip()
        if stripped.startswith(f"{short} :") or stripped.startswith(f"{short}:"):
            return True
    return False


def verify_citations() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Return (missing, ok) lists of (row_id, file, decl)."""
    rows = load_catalog()
    text = (REPO_ROOT / "INVARIANT_CATALOG.md").read_text(encoding="utf-8")
    # Pull all citations directly from the document so we don't depend on
    # field-extraction subtleties. Also pair each citation with the row IDs
    # that appear on the same line (best-effort).
    missing: list[tuple[str, str, str]] = []
    ok: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    by_id = {r.id: r for r in rows}
    for line in text.splitlines():
        ids = re.findall(r"I-[A-Z]+-\d+[a-z]?", line)
        row_id = ids[0] if ids else ""
        for m in _CITATION_RE.finditer(line):
            file_part, decl = m.group(1), m.group(2)
            key = (file_part, decl)
            if key in seen:
                continue
            seen.add(key)
            lean_file = _find_lean_file(file_part.split("/")[-1])
            if lean_file is None or not _file_has_decl(lean_file, decl):
                missing.append((row_id, file_part, decl))
            else:
                ok.append((row_id, file_part, decl))
    return missing, ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.citations")
    parser.add_argument("cmd", choices=["verify"], help="What to do.")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    missing, ok = verify_citations()
    print(f"Verified {len(ok)} citations.")
    if missing:
        print(f"\n{len(missing)} unresolved citation(s):")
        for row_id, file_part, decl in missing:
            print(f"  {row_id:11s}  {file_part}::{decl}")
        return 1
    if args.verbose:
        for row_id, file_part, decl in ok:
            print(f"  {row_id:11s}  {file_part}::{decl}")
    print("All catalog citations resolve in lean_reference/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
