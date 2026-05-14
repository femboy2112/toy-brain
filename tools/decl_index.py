"""Extract a declaration index from a directory of Lean source files.

Used by `tools.snapshot_diff` to compute what changed between the local
snapshot in ``lean_reference/`` and an upstream clone.

CLI:
    python -m tools.decl_index <root>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_DECL_RE = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:noncomputable\s+)?"
    r"(theorem|def|structure|class|inductive|abbrev)\s+"
    r"([A-Za-z_][A-Za-z0-9_'.]*)"
)


def extract_decls(root: Path) -> dict[str, list[str]]:
    """Return ``{relative_lean_path: [decl_name, ...]}``."""
    out: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.lean")):
        decls: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            m = _DECL_RE.match(line)
            if m:
                decls.append(m.group(2))
        rel = path.relative_to(root).as_posix()
        out[rel] = decls
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.decl_index")
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    if not args.root.exists():
        print(f"path does not exist: {args.root}", file=sys.stderr)
        return 1
    index = extract_decls(args.root)
    for file, decls in index.items():
        print(f"=== {file} ===")
        for d in decls:
            print(f"  {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
