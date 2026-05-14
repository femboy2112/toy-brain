"""Parser and query interface for INVARIANT_CATALOG.md.

Reads the catalog's markdown tables into structured rows so other tooling
(citation verifier, runner sanity checks, subagents) can query by ID,
status, module, or fixture without re-parsing the file each time.

CLI:
    python -m tools.catalog list [--status REQUIRED] [--module modes]
    python -m tools.catalog show I-AGN-03
    python -m tools.catalog counts
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "INVARIANT_CATALOG.md"

# Module header lines look like "### `brain/tlica/profile.py` — ..."
_MODULE_HEADER_RE = re.compile(r"^###\s+`([^`]+)`")
# Row IDs look like I-XXX-NN
_ROW_ID_RE = re.compile(r"^I-[A-Z]+-\d+[a-z]?$")
# Banner counts at the summary block
_REQUIRED_BANNER_RE = re.compile(r"\*\*REQUIRED v0 invariants:\*\*\s*(\d+)")
_STRUCTURAL_BANNER_RE = re.compile(r"\*\*STRUCTURAL[^*]*\*\*\s*(\d+)")
_NOT_EXERCISED_BANNER_RE = re.compile(r"\*\*NOT-EXERCISED[^*]*\*\*\s*(\d+)")
_DEFERRED_BANNER_RE = re.compile(r"\*\*DEFERRED[^*]*\*\*\s*(\d+)")
_OBSERVED_BANNER_RE = re.compile(r"\*\*OBSERVED[^*]*\*\*\s*(\d+)")


@dataclass(frozen=True, slots=True)
class InvariantRow:
    id: str
    lean_source: str
    proposition: str
    py_assertion: str
    fixture: str
    status: str
    module: str  # the brain/ owning module (last seen module header)


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
    filtered = filter_rows(
        rows,
        status=args.status,
        module=args.module,
        fixture=args.fixture,
        id_prefix=args.id_prefix,
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
    expected = {
        "REQUIRED": 84,
        "STRUCTURAL": 10,
        "NOT-EXERCISED": 3,
        "DEFERRED": 12,
        "OBSERVED": 1,
    }
    print(f"{'Category':16s}  {'Banner':>8s}  {'Actual':>8s}  {'Expected':>8s}")
    ok = True
    for k in ("REQUIRED", "STRUCTURAL", "NOT-EXERCISED", "DEFERRED", "OBSERVED"):
        b = banner.get(k, -1)
        a = actual.get(k, 0)
        e = expected[k]
        mark = "  ok" if (a == b == e) else "  !!"
        if a != e:
            ok = False
        print(f"{k:16s}  {b:8d}  {a:8d}  {e:8d}{mark}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.catalog")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List rows (optionally filtered).")
    p_list.add_argument("--status")
    p_list.add_argument("--module")
    p_list.add_argument("--fixture")
    p_list.add_argument("--id-prefix")
    p_list.set_defaults(func=_cmd_list)

    p_show = sub.add_parser("show", help="Show a single row by ID.")
    p_show.add_argument("row_id")
    p_show.set_defaults(func=_cmd_show)

    p_counts = sub.add_parser("counts", help="Compare banner vs actual vs expected counts.")
    p_counts.set_defaults(func=_cmd_counts)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
