---
name: brain-invariants
description: Orchestrate the TLICA invariant catalog and runner for toy-brain. Use when working on brain/ implementation, debugging a red invariant row, looking up a row by ID, verifying Lean citations, auditing the agency→pce import rule, or applying the SPEC_UPDATES protocol after upstream Lean evolves.
---

# brain-invariants skill

The `brain/` package is a theorem-constrained Python state machine.
`INVARIANT_CATALOG.md` (v0.5) binds each Lean theorem — plus engineering-
hypothesis rows added by Phase 2 — to a Python runtime check; success is
`python -m brain.invariants run` reporting all 84 REQUIRED rows green plus
15 STRUCTURAL rows green (1 OBSERVED logged). This skill bundles every
helper that supports that loop.

## When to use this skill

- Implementing a new fixture or module — look up the rows it owns.
- A row is red — find its Lean citation, fixture path, and module.
- Checking catalog hygiene — banner counts, citation resolution,
  `_catalog_ids.py` freshness (regenerate via `python -m tools.catalog
  generate-ids`).
- The Lean upstream changed — run the refresh protocol.
- Auditing the I-PCE-05 import rule (`agency.py` ⊄ `pce.py`).
- Auditing catalog↔registry coverage (I-CAT-01).
- Wiring the LLM seam (`brain/llm/`, `PtCns.eval`), the cognition
  tracer (`brain/trace.py`, `SafeTracer`), or the tick guards
  (I-RT-11 single-event, I-RT-12 duplicate content_id).

## Helpers

### `tools.catalog` — parse and query INVARIANT_CATALOG.md

```bash
python -m tools.catalog list                       # all rows
python -m tools.catalog list --status REQUIRED     # filter by status
python -m tools.catalog list --module modes        # filter by owning module
python -m tools.catalog list --fixture cogito      # filter by fixture
python -m tools.catalog list --id-prefix I-AFF     # filter by ID prefix
python -m tools.catalog list --source-kind LEAN    # filter by inferred source kind
python -m tools.catalog show I-AGN-03              # full row detail
python -m tools.catalog counts                     # strict banner vs actual vs expected gate
python -m tools.catalog counts --by-source-kind    # counts grouped by SourceKind
python -m tools.catalog generate-ids               # regen brain/_catalog_ids.py
```

The `counts` command must report `84 / 15 / 3 / 12 / 1` for REQUIRED /
STRUCTURAL / NOT-EXERCISED / DEFERRED / OBSERVED. The v0.5 strict gate
exits non-zero on any banner ≠ actual ≠ expected drift. (OBSERVED rows
are recorded in the run summary but do not fail the runner; they were
added in v0.3 for the LLM seam. SourceKind is inferred from each row's
Source/Status by `tools.catalog.infer_source_kind`.)

### `tools.citations` — verify Lean citations

```bash
python -m tools.citations verify
```

Walks every `<file>::<decl>` citation in the catalog and confirms the
declaration exists in `lean_reference/`. Exit 0 = all resolve.

### `tools.import_audit` — I-PCE-05 enforcement

```bash
python -m tools.import_audit
```

Thin CLI around `brain._import_audit.audit_agency_no_pce_import()`. The
runner re-runs the same audit inside `python -m brain.invariants run`, so
this command exists primarily for fast local checks.

### `tools.snapshot_diff` — local vs upstream Lean drift

```bash
python -m tools.snapshot_diff /tmp/lean-scratch-latest
```

Reports added files, removed files, and per-file declaration drift. Use
inside the refresh protocol below.

### `tools.decl_index` — extract declarations from a Lean tree

```bash
python -m tools.decl_index lean_reference        # local
python -m tools.decl_index /tmp/lean-scratch-latest  # upstream
```

### `tools/refresh_snapshot.sh` — clone upstream + diff

```bash
tools/refresh_snapshot.sh
```

Clones (or fetches) `github.com/femboy2112/lean-scratch` into
`/tmp/lean-scratch-latest/`, then runs `snapshot_diff` and `citations
verify`. **Does NOT overwrite `lean_reference/`** — that is a deliberate
manual step gated on catalog review per `SPEC_UPDATES.md` §8.

### `tools/run_invariants.sh` — wrap the runner

```bash
tools/run_invariants.sh                # default
tools/run_invariants.sh --json         # machine-readable
tools/run_invariants.sh --module modes # filter
tools/run_invariants.sh --id I-AGN     # filter by ID prefix
```

### `tools/check_all.sh` — full health check

```bash
tools/check_all.sh
```

Runs, in order: generated-ids freshness → catalog counts (strict) →
citation verification → import audit → invariant runner (with I-CAT-01
coverage audit at startup). Exits non-zero on the first failure. Use
this for the "is everything green?" gate.

## Conventions (canonical from the catalog)

- All numeric values in `brain/tlica/`, `brain/fixtures/`,
  `brain/invariants.py` are `fractions.Fraction`. `math.inf` is the only
  permitted float (encodes Lean's `⊤` for empty-shared-domain
  `dInfShared`).
- `rho(value)` normalizes input at the I/O boundary and raises on
  out-of-`[0,1]`; never clamps silently. For float input, normalize via
  `Fraction(str(v))` to avoid binary drift.
- `Act` is an `enum.Enum`, not `typing.Literal`. `proj.no_action is
  Act.NOOP`.
- `ModeOp.from_eval` is a lookup dict, never returns `MODE_B`.
- `PreservationRanking.rank` is cogito-gated.
  `GlobalPreservationRanking.rank` is not.
- Every projected profile from v0 `ProjectMap` stubs preserves
  `COGITO_ID` at value `1` (I-RT-07).
- `agency.py` never imports `pce.py` (I-PCE-05, audited).
- `AffectKernelWitness.__post_init__` raises when its baseline/action
  pair has equal branch profiles AND equal projected PCE (I-AFF-05).
- Every dataclass `__post_init__` raises on invariant violation;
  builders also raise and add axiom-tagged messages.
- The `CognitionTracer` Protocol (`brain/trace.py`) is observation-only:
  swapping `NullTracer` / `MemoryTracer` / `FileTracer` must not change
  `(BrainState, TickRecord)` output for a given seed (I-TRACE-01).
  Backend failures are swallowed by `SafeTracer` (I-TRACE-02).
- `tick()` rejects multi-event lists (I-RT-11) and duplicate
  `content_id` re-promotion (I-RT-12); both raise `ValueError` with the
  row name in the message.
- Every catalog REQUIRED/STRUCTURAL row must have a `@register` entry;
  the I-CAT-01 audit runs at runner startup and fails fast if any are
  missing.

## Refresh protocol (when upstream Lean evolves)

Per `SPEC_UPDATES.md`:

```bash
tools/refresh_snapshot.sh                       # 1. fetch + diff
python -m tools.catalog counts                  # 2. baseline counts
python -m tools.catalog list --status DEFERRED  # 3. look for resolved deferreds
# ... edit INVARIANT_CATALOG.md per SPEC_UPDATES.md §4 ...
python -m tools.citations verify                # 4. re-verify
# ... overwrite lean_reference/ per SPEC_UPDATES.md §8 ...
tools/check_all.sh                              # 5. full health check
```

## Subagents that pair with this skill

- `brain-row-implementer` — implements one or a small range of rows.
- `brain-runner-debugger` — diagnoses a red row.
- `brain-spec-refresher` — drives the refresh protocol.
- `brain-explorer` — read-only navigator for Lean + catalog.
