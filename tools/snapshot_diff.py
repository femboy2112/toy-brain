"""Compute a structured diff between the local ``lean_reference/`` snapshot
and an upstream clone (per SPEC_UPDATES.md step 2-3).

Reports:
  - new files in upstream (candidates for catalog rows)
  - removed files / removed declarations (citations going stale)
  - added declarations in unchanged files

Does NOT mutate ``lean_reference/`` — that overwrite is a separate manual
step per SPEC_UPDATES.md §8.

CLI:
    python -m tools.snapshot_diff /tmp/lean-scratch-latest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.catalog import REPO_ROOT
from tools.decl_index import extract_decls

LOCAL_SNAPSHOT = REPO_ROOT / "lean_reference"


def diff_snapshot(upstream_root: Path) -> int:
    if not upstream_root.exists():
        print(f"upstream path does not exist: {upstream_root}", file=sys.stderr)
        return 1
    local = extract_decls(LOCAL_SNAPSHOT)
    upstream = extract_decls(upstream_root)

    # Normalize keys: strip a leading "TLICA/" or similar so both indices
    # are comparable. We pair files by their basename when ambiguous.
    def by_basename(idx: dict[str, list[str]]) -> dict[str, tuple[str, list[str]]]:
        out: dict[str, tuple[str, list[str]]] = {}
        for path, decls in idx.items():
            base = path.split("/")[-1]
            out[base] = (path, decls)
        return out

    local_b = by_basename(local)
    upstream_b = by_basename(upstream)

    added_files = sorted(set(upstream_b) - set(local_b))
    removed_files = sorted(set(local_b) - set(upstream_b))
    common = sorted(set(local_b) & set(upstream_b))

    if added_files:
        print("== Added files upstream (candidate for new catalog rows) ==")
        for f in added_files:
            print(f"  + {upstream_b[f][0]}  ({len(upstream_b[f][1])} decls)")
    if removed_files:
        print("== Removed files upstream (citations going stale) ==")
        for f in removed_files:
            print(f"  - {local_b[f][0]}  ({len(local_b[f][1])} decls)")

    drift_count = 0
    for f in common:
        _, local_decls = local_b[f]
        _, upstream_decls = upstream_b[f]
        added = sorted(set(upstream_decls) - set(local_decls))
        removed = sorted(set(local_decls) - set(upstream_decls))
        if added or removed:
            drift_count += 1
            print(f"== Drift in {f} ==")
            for d in added:
                print(f"  + {d}")
            for d in removed:
                print(f"  - {d}")

    if not (added_files or removed_files or drift_count):
        print("Snapshot matches upstream: no drift detected.")
        return 0
    print(
        f"\nSummary: {len(added_files)} files added, "
        f"{len(removed_files)} files removed, "
        f"{drift_count} files with declaration drift."
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.snapshot_diff")
    parser.add_argument("upstream_root", type=Path)
    args = parser.parse_args(argv)
    return diff_snapshot(args.upstream_root)


if __name__ == "__main__":
    raise SystemExit(main())
