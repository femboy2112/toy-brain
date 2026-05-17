"""Parser and query interface for INVARIANT_CATALOG.md.

Reads the catalog's markdown tables into structured rows so other tooling
(citation verifier, runner sanity checks, subagents) can query by ID,
status, module, or fixture without re-parsing the file each time.

CLI:
    python3 -m tools.catalog list [--status REQUIRED] [--module modes]
                                  [--source-kind LEAN]
    python3 -m tools.catalog show I-AGN-03
    python3 -m tools.catalog counts
    python3 -m tools.catalog generate-ids   # writes brain/_catalog_ids.py
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "INVARIANT_CATALOG.md"
GENERATED_IDS_PATH = REPO_ROOT / "brain" / "_catalog_ids.py"

# v0.21 expected counts — bumped by the Phase 3.12c Pattern Ledger
# catalog patch (I-PLEDGER-01..18 Option A: +15 REQUIRED rows, +1
# STRUCTURAL row, +1 NOT-EXERCISED row, +1 DEFERRED row; OBSERVED
# unchanged). The Phase 3.12c family is session-local only; no
# persistence schema, no /pattern-ledger UI, no observed dry run in
# v1.
EXPECTED_COUNTS: dict[str, int] = {
    "REQUIRED": 229,
    "STRUCTURAL": 84,
    "NOT-EXERCISED": 10,
    "DEFERRED": 13,
    "OBSERVED": 16,
}

# Module header lines look like "### `brain/tlica/profile.py` — ..."
_MODULE_HEADER_RE = re.compile(r"^###\s+`([^`]+)`")
# Row IDs look like I-XXX-NN
_ROW_ID_RE = re.compile(r"^I-[A-Z]+-\d+[a-z]?$")
# Banner counts at the summary block
_REQUIRED_BANNER_RE = re.compile(r"\*\*REQUIRED[^*]*\*\*\s*(\d+)")
_STRUCTURAL_BANNER_RE = re.compile(r"\*\*STRUCTURAL[^*]*\*\*\s*(\d+)")
_NOT_EXERCISED_BANNER_RE = re.compile(r"\*\*NOT-EXERCISED[^*]*\*\*\s*(\d+)")
_DEFERRED_BANNER_RE = re.compile(r"\*\*DEFERRED[^*]*\*\*\s*(\d+)")
_OBSERVED_BANNER_RE = re.compile(r"\*\*OBSERVED[^*]*\*\*\s*(\d+)")


class SourceKind(Enum):
    """Phase 2 v1.2: explicit classification of each catalog row's origin.

    Inferred from the row's ``Source`` field and ``Status`` by
    :func:`infer_source_kind`. Becomes load-bearing in Phase 3 when
    developmental / engineering rows need to be enumerable separately
    from theory-derived rows.
    """

    LEAN = "lean"
    PLAN_CONVENTION = "plan_convention"
    ENGINEERING_HYPOTHESIS = "engineering_hypothesis"
    OBSERVED = "observed"
    DEFERRED = "deferred"


_ENGINEERING_MARKERS: tuple[str, ...] = (
    "phase 2 v1",
    "phase 2 v1.1",
    "phase 2 v1.2",
    "phase 3",
    "developmental layer",
    "engineering hypothesis",
)


def infer_source_kind(source: str, status: str) -> SourceKind:
    """Classify a catalog row's source/status as a :class:`SourceKind`.

    Status-driven overrides win first (OBSERVED, DEFERRED, NOT-EXERCISED);
    otherwise infer from the free-text Source field via heuristics that
    detect Lean citations and Phase 2/3 engineering markers.
    """
    if status == "OBSERVED":
        return SourceKind.OBSERVED
    if status in ("DEFERRED", "NOT-EXERCISED"):
        return SourceKind.DEFERRED
    src_low = source.lower()
    if "::" in source and ".lean" in src_low:
        return SourceKind.LEAN
    if any(marker in src_low for marker in _ENGINEERING_MARKERS):
        return SourceKind.ENGINEERING_HYPOTHESIS
    return SourceKind.PLAN_CONVENTION


@dataclass(frozen=True, slots=True)
class InvariantRow:
    id: str
    lean_source: str
    proposition: str
    py_assertion: str
    fixture: str
    status: str
    module: str  # the brain/ owning module (last seen module header)
    source_kind: SourceKind = SourceKind.PLAN_CONVENTION


def _split_pipes(line: str) -> list[str]:
    """Split markdown-table row on `|`, treating backtick-quoted spans as opaque.

    This matters because catalog rows like I-PROF-07 contain expressions like
    `f.domain | g.domain` inside backticks; a naive split mangles them.
    """
    parts: list[str] = []
    buf: list[str] = []
    in_tick = False
    for ch in line:
        if ch == "`":
            in_tick = not in_tick
            buf.append(ch)
        elif ch == "|" and not in_tick:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def load_catalog(path: Path | None = None) -> list[InvariantRow]:
    """Parse the catalog markdown into InvariantRow records."""
    p = path or CATALOG_PATH
    text = p.read_text(encoding="utf-8")
    rows: list[InvariantRow] = []
    current_module = ""
    for raw_line in text.splitlines():
        m = _MODULE_HEADER_RE.match(raw_line)
        if m:
            current_module = m.group(1)
            continue
        if not raw_line.startswith("|"):
            continue
        cells = _split_pipes(raw_line)
        if len(cells) < 6:
            continue
        first = cells[0]
        if not _ROW_ID_RE.match(first):
            continue
        # Standard catalog rows have 6 columns:
        #   ID | Lean source | Proposition | Python assertion | Fixture | Status
        # The Phase 2 v1 cross-cutting table has 7 columns:
        #   ID | Source | Proposition | Python assertion | Owning module | Fixture | Status
        # Read Status/Fixture from the right end so both shapes parse correctly;
        # when an Owning module column is present, prefer it over current_module.
        status = cells[-1]
        fixture = cells[-2]
        if len(cells) >= 7:
            module = cells[-3]
        else:
            module = current_module
        rows.append(
            InvariantRow(
                id=first,
                lean_source=cells[1],
                proposition=cells[2],
                py_assertion=cells[3],
                fixture=fixture,
                status=status,
                module=module,
                source_kind=infer_source_kind(cells[1], status),
            )
        )
    return rows


def filter_rows(
    rows: list[InvariantRow],
    *,
    status: str | None = None,
    module: str | None = None,
    fixture: str | None = None,
    id_prefix: str | None = None,
    source_kind: SourceKind | None = None,
) -> list[InvariantRow]:
    out = rows
    if status is not None:
        out = [r for r in out if r.status == status]
    if module is not None:
        out = [r for r in out if module in r.module]
    if fixture is not None:
        out = [r for r in out if fixture in r.fixture]
    if id_prefix is not None:
        out = [r for r in out if r.id.startswith(id_prefix)]
    if source_kind is not None:
        out = [r for r in out if r.source_kind == source_kind]
    return out


def banner_counts(path: Path | None = None) -> dict[str, int]:
    """Return the catalog's self-reported summary counts."""
    p = path or CATALOG_PATH
    text = p.read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for label, pattern in (
        ("REQUIRED", _REQUIRED_BANNER_RE),
        ("STRUCTURAL", _STRUCTURAL_BANNER_RE),
        ("NOT-EXERCISED", _NOT_EXERCISED_BANNER_RE),
        ("DEFERRED", _DEFERRED_BANNER_RE),
        ("OBSERVED", _OBSERVED_BANNER_RE),
    ):
        m = pattern.search(text)
        counts[label] = int(m.group(1)) if m else -1
    return counts


def actual_counts(rows: list[InvariantRow]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r.status] = out.get(r.status, 0) + 1
    return out


def _fmt_row(r: InvariantRow) -> str:
    return f"{r.id:11s}  {r.status:14s}  {r.module:42s}  fixture={r.fixture}"


def _cmd_list(args: argparse.Namespace) -> int:
    rows = load_catalog()
    kind = None
    if args.source_kind:
        try:
            kind = SourceKind[args.source_kind.upper()]
        except KeyError:
            print(
                f"unknown --source-kind {args.source_kind!r}; expected one of "
                f"{[k.name for k in SourceKind]}",
                file=sys.stderr,
            )
            return 1
    filtered = filter_rows(
        rows,
        status=args.status,
        module=args.module,
        fixture=args.fixture,
        id_prefix=args.id_prefix,
        source_kind=kind,
    )
    for r in filtered:
        print(_fmt_row(r))
    print(f"\n{len(filtered)} rows.")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    rows = load_catalog()
    matches = [r for r in rows if r.id == args.row_id]
    if not matches:
        print(f"No row with ID {args.row_id!r}.", file=sys.stderr)
        return 1
    for r in matches:
        print(f"ID:           {r.id}")
        print(f"Status:       {r.status}")
        print(f"Module:       {r.module}")
        print(f"Fixture:      {r.fixture}")
        print(f"Lean source:  {r.lean_source}")
        print(f"Proposition:  {r.proposition}")
        print(f"Py assertion: {r.py_assertion}")
    return 0


def _cmd_counts(args: argparse.Namespace) -> int:
    rows = load_catalog()
    banner = banner_counts()
    actual = actual_counts(rows)
    if args.by_source_kind:
        return _print_counts_by_source_kind(rows)
    print(f"{'Category':16s}  {'Banner':>8s}  {'Actual':>8s}  {'Expected':>8s}")
    ok = True
    # Strict gate (P6): banner ≠ actual ≠ expected ⇒ failure.
    # Previously only actual-vs-expected mismatch failed, so stale banners
    # could sneak past the gate.
    for k in ("REQUIRED", "STRUCTURAL", "NOT-EXERCISED", "DEFERRED", "OBSERVED"):
        b = banner.get(k, -1)
        a = actual.get(k, 0)
        e = EXPECTED_COUNTS[k]
        passing = b == a == e
        mark = "  ok" if passing else "  !!"
        if not passing:
            ok = False
        print(f"{k:16s}  {b:8d}  {a:8d}  {e:8d}{mark}")
    return 0 if ok else 1


def _print_counts_by_source_kind(rows: list[InvariantRow]) -> int:
    counts: dict[SourceKind, int] = {kind: 0 for kind in SourceKind}
    for r in rows:
        counts[r.source_kind] += 1
    print(f"{'Source kind':24s}  {'Count':>8s}")
    for kind in SourceKind:
        print(f"{kind.name:24s}  {counts[kind]:8d}")
    print(f"\n{sum(counts.values())} total rows.")
    return 0


def _cmd_generate_ids(args: argparse.Namespace) -> int:
    """Write ``brain/_catalog_ids.py`` from the catalog.

    Source of truth for I-CAT-01 — every REQUIRED / STRUCTURAL ID listed
    in the catalog appears in the generated frozenset; the runner audits
    its registry against these at startup.
    """
    rows = load_catalog()
    required = sorted(r.id for r in rows if r.status == "REQUIRED")
    structural = sorted(r.id for r in rows if r.status == "STRUCTURAL")
    lines = [
        '"""Auto-generated from INVARIANT_CATALOG.md by tools/catalog.py.',
        "",
        "DO NOT EDIT BY HAND. Regenerate via:",
        "",
        "    python3 -m tools.catalog generate-ids",
        "",
        "This file is the source of truth for I-CAT-01 (every REQUIRED or",
        "STRUCTURAL catalog row has a corresponding @register entry).",
        '"""',
        "from __future__ import annotations",
        "",
        "EXPECTED_REQUIRED_IDS: frozenset[str] = frozenset({",
    ]
    for rid in required:
        lines.append(f'    "{rid}",')
    lines.append("})")
    lines.append("")
    lines.append("EXPECTED_STRUCTURAL_IDS: frozenset[str] = frozenset({")
    for rid in structural:
        lines.append(f'    "{rid}",')
    lines.append("})")
    lines.append("")
    content = "\n".join(lines)
    GENERATED_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    GENERATED_IDS_PATH.write_text(content, encoding="utf-8")
    print(
        f"wrote {GENERATED_IDS_PATH}  "
        f"(REQUIRED={len(required)}, STRUCTURAL={len(structural)})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.catalog")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List rows (optionally filtered).")
    p_list.add_argument("--status")
    p_list.add_argument("--module")
    p_list.add_argument("--fixture")
    p_list.add_argument("--id-prefix")
    p_list.add_argument(
        "--source-kind",
        help="Filter by inferred SourceKind: LEAN, PLAN_CONVENTION, "
        "ENGINEERING_HYPOTHESIS, OBSERVED, DEFERRED.",
    )
    p_list.set_defaults(func=_cmd_list)

    p_show = sub.add_parser("show", help="Show a single row by ID.")
    p_show.add_argument("row_id")
    p_show.set_defaults(func=_cmd_show)

    p_counts = sub.add_parser(
        "counts",
        help="Compare banner vs actual vs expected counts (strict gate).",
    )
    p_counts.add_argument(
        "--by-source-kind",
        action="store_true",
        help="Print counts grouped by SourceKind instead of the strict gate.",
    )
    p_counts.set_defaults(func=_cmd_counts)

    p_gen = sub.add_parser(
        "generate-ids",
        help="Write brain/_catalog_ids.py for the I-CAT-01 runner audit.",
    )
    p_gen.set_defaults(func=_cmd_generate_ids)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
