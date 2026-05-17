# PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md

## Purpose

This document plans the Pattern Ledger catalog patch and the Step 11
implementation surface. It is documentation only. It does **not** edit
the invariant catalog, the runner, the fixtures, the operator UI, the
persistence layer, or any other source under `brain/**`, `tools/**`,
`lean_reference/**`, `scenarios/**`, or `traces/**`. It does not
authorize Step 11. Step 11 may proceed only after explicit operator
acceptance at Step 10 Review Gate B.

The plan is precise enough that Step 10 Review Gate B can decide one of:

```text
ACCEPT PLAN AS WRITTEN — Step 11 may implement within the declared surface
ACCEPT WITH AMENDMENTS — list amendments; Step 11 implements with them
REJECT / REVISE       — Step 9 must be revised before implementation
```

## Baseline

```text
Catalog version:                  v0.20
Counts:
  REQUIRED:                       214
  STRUCTURAL:                      83
  NOT-EXERCISED:                    9
  DEFERRED:                        12
  OBSERVED:                        16
Branch:                           campaign/phase3-12-coherent-i-loop-observatory
Phase 3.11:                       complete; PR #10 merged at 98b55ab
Phase 3.12 steps complete (in commit order on this branch):
  Step 1  566b109  coherent i-loop mission sync
  Step 2  631ae5a  coherent i-loop synthesis
  Step 3  c395989  coherent i-loop kickoff
  Step 4  10a93ee  coherent i-loop matrix
  Step 5  (review gate A — passed implicitly by Step 6 execution)
  Step 6  c65d37b  coherent i-loop observatory report
  Step 7  013585e  pattern ledger synthesis
  Step 8  7839f7d  pattern ledger kickoff + corrigenda
Locked decisions (carried from Step 8 corrigenda):
  LOCK A..LOCK O   (see PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md)
Step 9 stop condition:
  Step 10 Review Gate B (no implementation in this step).
Preflight (verified at the start of Step 9):
  python3 -m tools.catalog counts     PASS  (214/83/9/12/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (305 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Locked decisions imported from corrigenda

The Step 8 corrigenda (`PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md`) locks
the following material decisions. Each LOCK below is binding on this
plan and on any Step 11 implementation, unless explicitly overridden by
a later review gate that cites the LOCK label.

```text
LOCK A — Implementation authorization
  Step 8 is documentation only. No file under brain/, tools/,
  INVARIANT_CATALOG.md, lean_reference/, scenarios/, or traces/ was
  modified. No fixture was added. No committed helper script was added.
  Step 9 inherits the same scope (this file is documentation only).
  Implementation requires Step 9 (this plan) plus explicit operator
  acceptance at Step 10 Review Gate B.

LOCK B — First implementation persistence policy
  Pattern Ledger v1 is session-local only:
    no `pattern_ledger` table is added to the session DB schema;
    SCHEMA_VERSION_V* is not bumped;
    /save-session does not serialize the ledger;
    /load-session does not restore the ledger;
    autosave (_maybe_autosave_after_dispatch) is not extended;
    brain/ui/persistence.py, brain/ui/persistence_ops.py,
    brain/ui/persistence_observe.py, brain/ui/autosave.py are NOT
    edited by Step 11.
  Reason: avoid persistence schema creep before runtime invariants
  are validated.

LOCK C — Cold-start behavior
  Fresh session            -> empty PatternLedger().
  /load-session            -> does NOT touch session.pattern_ledger.
  Cold start across runs   -> ledger does NOT survive.
  A future option to rebuild from a loaded TextStreamHistory by
  replay is explicitly deferred.

LOCK D — Duplicate-evidence handling
  PatternLedger.observe(...) is idempotent against duplicate
  evidence delivery for the same entry (duplicate chunk_id or
  candidate_id is filtered, not raising).
  PatternLedgerEntry's constructor remains strict: direct
  construction with a tuple containing a duplicate element raises
  ValueError. observe deduplicates before constructing.

LOCK E — Max-entry behavior
  When len(entries) >= PATTERN_LEDGER_MAX_ENTRIES and a NEW
  signature arrives, observe(...) returns the same PatternLedger
  unchanged. No LRU. No oldest-drop. No random eviction. No
  least-confident eviction. No silent overwrite.

LOCK F — Evidence-list cap
  When len(entry.evidence_chunk_ids) == PATTERN_LEDGER_EVIDENCE_MAX,
  no further chunk IDs are appended to that entry. Same for
  evidence_candidate_ids. recurrence_count may continue saturating.
  Chunk and candidate evidence lists are treated independently.
  No FIFO drop.

LOCK G — Recurrence count saturation
  recurrence_count saturates at STREAM_PATTERN_RECURRENCE_MAX
  (currently 256). STREAM_PATTERN_RECURRENCE_MIN (currently 2) is
  the lower bound for a freshly constructed entry. Direct
  construction outside [MIN, MAX] raises ValueError.

LOCK H — Confidence formula
  confidence = Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)
  Result is an exact fractions.Fraction, bounded [0, 1] by
  construction. Recomputed on every observe(...) increment. No
  float, no round, no math.*. No length weighting. No semantic
  weighting. No model weighting. Direct construction with a
  confidence value outside [0, 1], or inconsistent with the
  formula, raises ValueError.

LOCK I — Pattern signatures
  v1 signature is structural and non-semantic.
  Recommended shape:
      ( f"source:{chunk.source.value}",
        f"len:{len(chunk.text)}",
        f"lines:{<line_count>}",
        f"ws:{<whitespace_run_count>}",
        f"distinct:{<distinct_char_count>}",
        f"repeat:{<repeat_ratio.numerator>}/{<repeat_ratio.denominator>}" )
  Element count between 1 and STREAM_PATTERN_SIG_MAX = 16. Each
  element is a bounded printable str. No element equals COGITO_ID.
  Numeric values come from extract_stream_features(chunk) only.
  No float, no round, no math.*. No semantic labels. No raw text.

LOCK J — Pattern ID
  pattern_id = "pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]
  Deterministic. No randomness, no time, no PID, no hostname, no
  id(...), no env lookup. Total length 24 characters (well below
  PATTERN_LEDGER_ID_MAX = 64).

LOCK K — UI surface
  /pattern-ledger is OPTIONAL for v1. Read-only if included
  (set active_view='pattern_ledger', bounded status). It does not
  call observe(...), does not call tick(), does not mutate state,
  latest_tick, tick_counter, event_queue, stream_history,
  stream_candidates, or stream_chunk_serial.
  Step 9 may split /pattern-ledger out into a follow-up row family
  and a follow-up campaign step if it would broaden Step 11 too
  much. v1 then implements only the data substrate and the /stream
  integration trigger.

LOCK L — Integration trigger
  v1 integration is exactly one trigger: successful /stream append.
  Read-only commands do NOT observe. Parse failures do NOT observe.
  Dispatch failures do NOT observe. /step does NOT observe.
  /stream-promote does NOT observe (the chunk was already observed
  on /stream). Pattern Ledger does NOT alter /step behavior, the
  tick() signature, or the _dispatch_step failure path.

LOCK M — Static audit
  brain/development/pattern_ledger.py must pass an AST audit that
  rejects every forbidden import / module reference / dynamic call
  enumerated in the corrigenda LOCK M section (os, subprocess,
  socket, urllib, http, requests, pathlib, tempfile, shutil,
  curses, brain.tick, brain.llm, brain.tlica, brain.ui, threading,
  asyncio, atexit, signal, signal.signal, plus eval / exec /
  compile / __import__ / importlib.import_module /
  importlib.__import__).
  Allowed imports are exactly: dataclasses, enum, fractions,
  hashlib, typing, brain.development.text_stream (for bounded
  constants only), brain.tlica.profile (for COGITO_ID), and
  optionally brain.io_types.

LOCK N — Non-claims
  No consciousness, no sentience, no subjective experience, no
  semantic understanding, no truth adjudication, no agency, no
  self-modification, no aggregate consciousness score. No field /
  method / docstring / row asserts any of those. /pattern-ledger
  status text (if included per LOCK K) is factual and bounded
  (entry counts, IDs, recurrence counts). Confidence is per-entry
  and is the LOCK H exact-Fraction formula only. The ledger does
  not produce truth labels, PRESERVE/DAMAGE evaluations, semantic
  categories, or language labels. The ledger does not adjudicate
  contradictions (door=open vs door=closed are stored as
  structurally distinct evidence; the ledger never picks a side).

LOCK O — Step 9 obligation
  Step 9 produces exactly PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md
  and STOPS at Step 10 Review Gate B. Step 9 must not edit
  brain/, tools/, INVARIANT_CATALOG.md, lean_reference/,
  scenarios/, or traces/, must not add fixtures, must not add
  committed helper scripts, and must not run real LLM-backed
  commands.
```

These locks are preserved verbatim against the corrigenda; do not
rewrite them loosely.

## Version / count strategy

```text
Current catalog version:    v0.20
Proposed catalog version:   v0.21
```

**Reason.** The Pattern Ledger row family (`I-PLEDGER-NN`) is a
catalog expansion: it adds engineering-hypothesis REQUIRED rows that
constrain a new module (`brain/development/pattern_ledger.py`), a
session field (`OperatorSession.pattern_ledger`), and a new
integration trigger (successful `/stream` append). Every prior
catalog expansion (v0.6 through v0.20) bumped the version when a new
row family or count category delta was introduced; this plan follows
the same convention.

Step 11, if accepted at Review Gate B, must update each of the
following in a single coordinated patch:

```text
INVARIANT_CATALOG.md
  - top-of-file version banner: v0.20 -> v0.21
  - new v0.21 banner block documenting the I-PLEDGER-* expansion
  - new section header(s) for the new owning module(s)
  - new I-PLEDGER-* row table entries (with Status / Proposition /
    Module / Fixture / Source columns matching the existing schema)

tools/catalog.py
  - EXPECTED_COUNTS dict updated to the v0.21 totals
    (see "Count impact estimate" below for both Option A and Option B)

brain/_catalog_ids.py
  - regenerated via `python3 -m tools.catalog generate-ids`
  - contains the new I-PLEDGER-* IDs as Python module constants

brain/invariants.py
  - FIXTURE_MODULES list extended with the new fixture module paths
  - _PHASE3_12_PENDING_ROWS dict added (or _PHASE3_12_PATTERN_LEDGER_PENDING_ROWS)
    so any row temporarily pending a fixture is tracked the same
    way as the existing _PHASE3_*_PENDING_ROWS guards

README.md
  - top heading "brain — TLICA-constrained Python kernel (catalog v0.20)"
    -> "(catalog v0.21)"
  - Constraints section "Use INVARIANT_CATALOG.md as shipped. Version
    banner inside should say v0.20." -> v0.21, plus the updated
    counts banner string ("214 / 83 / 9 / 12 / 16 / 137 fixtures"
    -> the chosen Option A or Option B totals)
  - Version-history bullet appended with the v0.21 entry

CURRENT_MISSION.md
  - "Catalog: v0.20" baseline block -> "Catalog: v0.21"
  - "Counts: ..." baseline block -> updated totals

CURRENT_CAMPAIGN.md
  - "Catalog: v0.20" baseline block -> "Catalog: v0.21"
  - "Counts: ..." baseline block -> updated totals
```

**Step 9 does NOT edit any of the files above.** Step 9 is
documentation only (LOCK A, LOCK O).

## Proposed row family

Working name: `I-PLEDGER-01..I-PLEDGER-18`.

The categories below reflect **Option A** (preferred — see
"Count impact estimate"). Option B variants are noted inline.

| Row ID | Status | Proposition (summary) | Owning module | Fixture | Notes |
|--------|--------|-----------------------|---------------|---------|-------|
| I-PLEDGER-01 | REQUIRED | `PatternLedgerSourceKind` is a finite closed enum whose members match the accepted text-stream source surface (`OPERATOR`, `SYSTEM`, `PROBE_ECHO`, `GENERATED`). Adding or removing a member raises at runner time. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_constructor.py` | Mirrors `I-STRM-01` shape. Source value strings are bounded printable. |
| I-PLEDGER-02 | REQUIRED | `PatternLedgerSaturationState` is a finite closed enum with exactly `OPEN`, `SATURATED`, `QUIESCED`. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_constructor.py` | v1 may collapse `QUIESCED` into `SATURATED` if the inactivity bound is hard to justify; if collapsed, the row still requires three closed members with `QUIESCED` reserved. |
| I-PLEDGER-03 | REQUIRED | `PatternLedgerEntry` constructor enforces bounded printable identifiers (`pattern_id`, every signature element, every evidence id, `provenance`); rejects `COGITO_ID` on every id-bearing field; requires tuple-typed evidence; requires exact `Fraction` confidence consistent with LOCK H; requires `first_seen_tick <= last_seen_tick`; requires closed `source_kind` and `saturation_state` enums; requires `provenance` length `<= STREAM_PROVENANCE_MAX_LEN`. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_constructor.py` | Constructor is strict (LOCK D); silent normalization is forbidden. |
| I-PLEDGER-04 | REQUIRED | Pattern signatures are structural/non-semantic. Each signature is a tuple of bounded printable strings, length in `[1, STREAM_PATTERN_SIG_MAX]`, every element `<= STREAM_PATTERN_SIG_ELEM_MAX` (proposed 64), no element equal to `COGITO_ID`, no raw text payload, all numeric values derived from exact `StreamFeatureVector` ints/`Fraction`. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_signature_id.py` | LOCK I. |
| I-PLEDGER-05 | REQUIRED | `pattern_id` is deterministic and equals `"pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]`. Same signature -> same `pattern_id` across runs, processes, and operating systems. No nondeterministic input (no `time`, `random`, `secrets`, `uuid.uuid4`, `os.getpid`, `socket.gethostname`, `id(...)`, env lookup) appears on the ID path. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_signature_id.py` | LOCK J. |
| I-PLEDGER-06 | REQUIRED | `recurrence_count` is bounded by `[STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX]`. `observe(...)` saturates at the max; direct construction outside the range raises. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_observe.py` | LOCK G. |
| I-PLEDGER-07 | REQUIRED | `confidence` is `Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)`, bounded `[0, 1]` by construction. No `float`, no `round`, no `math.*` on the count/statistic path. Direct construction with an inconsistent or out-of-range confidence raises. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_observe.py` | LOCK H. |
| I-PLEDGER-08 | REQUIRED | `PatternLedger` is frozen / slotted / copy-on-write. `entries` is a `tuple`. `observe(...)` returns a NEW `PatternLedger` and never mutates `self`; the original `entries` tuple identity is unchanged after observe. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_observe.py` | The CoW assertion follows the `TextStreamHistory` / `OutputHistory` / `ExpressionHistory` style. |
| I-PLEDGER-09 | REQUIRED | `observe(...)` is idempotent for duplicate delivered chunk/candidate evidence: duplicate ids are filtered before reconstruction and not appended to the evidence lists. `recurrence_count` still saturates per `I-PLEDGER-06`. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_observe.py` | LOCK D. |
| I-PLEDGER-10 | REQUIRED | Direct construction of `PatternLedgerEntry` with duplicate evidence ids rejects with `ValueError` rather than silently normalizing. Normalization is the responsibility of `observe(...)`, not the constructor. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_constructor.py` | LOCK D split-of-responsibility. |
| I-PLEDGER-11 | REQUIRED | Evidence lists cap at `PATTERN_LEDGER_EVIDENCE_MAX` (= 32) independently for `evidence_chunk_ids` and `evidence_candidate_ids`. No FIFO drop, no eviction; new ids past the cap are no-op appends. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_observe.py` | LOCK F. |
| I-PLEDGER-12 | REQUIRED | When `len(entries) >= PATTERN_LEDGER_MAX_ENTRIES` (= 64), `observe(...)` of a new (unseen) signature returns the same `PatternLedger` unchanged. No eviction, no LRU, no overwrite. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_observe.py` | LOCK E. |
| I-PLEDGER-13 | REQUIRED | `observe(...)` is invoked exactly once per successful `/stream` append (after `_dispatch_stream_append` has appended a chunk and a candidate). It is NOT invoked on read-only commands, parse failures, dispatch failures, `/step`, or `/stream-promote`. | `brain/ui/session.py` (integration) | `brain/development/fixtures/pattern_ledger_stream_integration.py` | LOCK L. |
| I-PLEDGER-14 | REQUIRED | Pattern Ledger has no `BrainState` / `MSI` / `PtCns` / `ContentRegistry` / `latest_tick` / `tick_counter` / `event_queue` / agency / LLM coupling. Across every `observe(...)` call those identities are unchanged. `/step` behavior, the `tick()` signature, and the `_dispatch_step` failure path are bit-for-bit identical. | `brain/development/pattern_ledger.py` (constraints) and `brain/ui/session.py` (integration) | `brain/development/fixtures/pattern_ledger_no_runtime_coupling.py` | LOCK L, LOCK M. |
| I-PLEDGER-15 | REQUIRED | Static AST audit over `brain/development/pattern_ledger.py` rejects every forbidden import / module reference / dynamic call listed in LOCK M and accepts only the allowed-imports list. Module-level statements are limited to imports, constants, function defs, class defs, and a docstring. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_static_audit.py` | Mirrors `I-STRM-12` / `I-EXP-13` / `I-REF-09` style. |
| I-PLEDGER-16 | STRUCTURAL | `PatternLedgerEntry` and `PatternLedger` records carry only bounded primitives, tuples of bounded primitives, `Fraction`, and the two closed enums. No field is a callable, file handle, socket, subprocess handle, `pathlib.Path`, `sqlite3.Connection`, curses object, or object with `eval_consistency`. | `brain/development/pattern_ledger.py` | `brain/development/fixtures/pattern_ledger_no_runtime_coupling.py` | Mirrors `I-UI-10`-style runtime resource audit. |
| I-PLEDGER-17 | DEFERRED | The optional `/pattern-ledger` read-only operator command. If included in v1 (LOCK K), this row promotes to REQUIRED with the contract: dispatch sets `active_view = "pattern_ledger"` and a bounded status; does not call `observe(...)`; does not call `tick()`; does not mutate kernel containers or stream state; parser accepts no arguments; extra tokens reject as `LocalCommandError`. **Option A defers** this row to a follow-up campaign step. | `brain/ui/commands.py`, `brain/ui/command_line.py`, `brain/ui/session.py` (if promoted) | `brain/ui/fixtures/pattern_ledger_ui_read_only.py` (if promoted) | LOCK K. Per the recommendation below, Option A keeps this DEFERRED; Option B promotes it to REQUIRED and adds a paired parser fixture row (see Option B note). |
| I-PLEDGER-18 | NOT-EXERCISED | Pattern Ledger end-to-end scripted walk: repeated stream observations produce one deterministic ledger entry per signature with saturated bounded evidence and no kernel mutation. **Option A** leaves this NOT-EXERCISED until a follow-up step adds a documented dry-run helper. **Option B** promotes this to OBSERVED with a Step 11 dry-run helper file cited by the audit. | `brain/development/pattern_ledger.py` (no fixture-side runtime behavior) | none in Option A; documented dry run in Option B | Mirrors the `I-STRM-17` NOT-EXERCISED vs `I-UISTRM-16` OBSERVED dichotomy. |

**Per-row category summary (Option A — preferred):**

```text
REQUIRED      : 15  (I-PLEDGER-01..15)
STRUCTURAL    :  1  (I-PLEDGER-16)
DEFERRED      :  1  (I-PLEDGER-17 — UI optional)
NOT-EXERCISED :  1  (I-PLEDGER-18 — placeholder)
OBSERVED      :  0
Total new rows: 18
```

**Per-row category summary (Option B — UI included + observed dry run):**

```text
REQUIRED      : 16  (I-PLEDGER-01..15 + I-PLEDGER-17)
STRUCTURAL    :  2  (I-PLEDGER-16 + a new I-PLEDGER-19 parser-shape row;
                    see Option B note below)
DEFERRED      :  0
OBSERVED      :  1  (I-PLEDGER-18 promoted)
NOT-EXERCISED :  0
Total new rows: 19
```

**Option B note.** Promoting `/pattern-ledger` to v1 (LOCK K) generally
requires both the dispatch-side REQUIRED row (I-PLEDGER-17) and a
parser-shape STRUCTURAL row that asserts:

```text
/pattern-ledger is added to LOCAL_COMMAND_VERBS,
OperatorCommand.INSPECT_PATTERN_LEDGER is added to the closed
OperatorCommand enumeration and to INSPECT_VIEW_MAP with view
string "pattern_ledger", _COMMANDS_WITHOUT_PAYLOAD gains
INSPECT_PATTERN_LEDGER, and the parser accepts no arguments
(extra tokens reject).
```

This parser-shape row is what `I-UISTRM-01`/`02` do for `/stream`.
Option B labels it `I-PLEDGER-19` (STRUCTURAL). Step 9's preferred
option is A (see "Count impact estimate" below); Option B is sketched
so the operator can ACCEPT WITH AMENDMENTS without re-running Step 9.

## Proposed constants

Step 11 (if accepted) must declare the following module-level
constants in `brain/development/pattern_ledger.py`:

```python
PATTERN_LEDGER_MAX_ENTRIES         : int = 64
PATTERN_LEDGER_EVIDENCE_MAX        : int = 32
PATTERN_LEDGER_ID_MAX              : int = 64
PATTERN_LEDGER_SIGNATURE_ELEM_MAX  : int = 64
```

Rationale:

- `64` matches `STREAM_PROMOTION_MAX` so the ledger can hold at most
  one entry per recently-promoted candidate signature without
  re-saturating at a different cap.
- `32` is half of the entry cap, biased toward keeping the per-entry
  evidence list compact for the snapshot view.
- `64` for both the pattern-id length and per-signature-element length
  mirrors `STREAM_PROVENANCE_MAX_LEN` and keeps the snapshot rendering
  bounded.

The following constants are **reused** unchanged from
`brain.development.text_stream` and must not be redefined in
`pattern_ledger.py`:

```text
STREAM_PATTERN_RECURRENCE_MIN  =   2
STREAM_PATTERN_RECURRENCE_MAX  = 256
STREAM_PATTERN_SIG_MAX         =  16
STREAM_PROVENANCE_MAX_LEN      =  64
```

Step 11 may import these from `brain.development.text_stream` per the
LOCK M allowed-imports list.

## Proposed implementation files for Step 11

Files Step 11 may touch fall into three buckets: **required if
accepted**, **likely required for `/stream` integration**, and
**optional under LOCK K**. Files in any **excluded** bucket are
forbidden in v1.

### Required if accepted

```text
brain/development/pattern_ledger.py
  new module; data substrate; LOCK M static-audit shape;
  imports limited to dataclasses, enum, fractions, hashlib,
  typing, brain.development.text_stream (constants),
  brain.tlica.profile (COGITO_ID).

brain/development/fixtures/pattern_ledger_constructor.py
  fixture for I-PLEDGER-01, I-PLEDGER-02, I-PLEDGER-03, I-PLEDGER-10.

brain/development/fixtures/pattern_ledger_signature_id.py
  fixture for I-PLEDGER-04, I-PLEDGER-05.

brain/development/fixtures/pattern_ledger_observe.py
  fixture for I-PLEDGER-06, I-PLEDGER-07, I-PLEDGER-08,
  I-PLEDGER-09, I-PLEDGER-11, I-PLEDGER-12.

brain/development/fixtures/pattern_ledger_static_audit.py
  fixture for I-PLEDGER-15 (AST audit of pattern_ledger.py).

brain/development/fixtures/pattern_ledger_no_runtime_coupling.py
  fixture for I-PLEDGER-14, I-PLEDGER-16.

brain/invariants.py
  FIXTURE_MODULES extension (six new module paths above; one more
  if Option B is selected).
  optional _PHASE3_12_PATTERN_LEDGER_PENDING_ROWS guard (only if
  fixtures land in a different commit than rows; for a single
  coordinated Step 11 patch the guard is unused).

INVARIANT_CATALOG.md
  new I-PLEDGER-* row entries; version banner v0.20 -> v0.21;
  new v0.21 banner block.

brain/_catalog_ids.py
  regenerated by `python3 -m tools.catalog generate-ids`.

tools/catalog.py
  EXPECTED_COUNTS dict updated to the chosen Option A or Option B
  totals (see "Count impact estimate" below).

README.md
  catalog-version stamp v0.20 -> v0.21 (top heading + Constraints
  block); appended v0.21 entry in version history.

CURRENT_MISSION.md
  baseline block catalog/counts update v0.20 -> v0.21.

CURRENT_CAMPAIGN.md
  baseline block catalog/counts update v0.20 -> v0.21.
```

### Likely required for `/stream` integration (LOCK L)

```text
brain/ui/session.py
  one new optional session field
    pattern_ledger: PatternLedger = field(default_factory=PatternLedger)
  added to _ALLOWED_SESSION_ATTRS so _assert_no_unsafe_resources accepts it;
  one new line at the end of the successful path inside
  _dispatch_stream_append:
    self.pattern_ledger = self.pattern_ledger.observe(
        chunk, candidate, current_tick=self.tick_counter,
    )
  no other dispatch handler is modified.

brain/development/fixtures/pattern_ledger_stream_integration.py
  fixture for I-PLEDGER-13.
```

### Optional under LOCK K (Option B only)

```text
brain/ui/commands.py
  add OperatorCommand.INSPECT_PATTERN_LEDGER member;
  add INSPECT_VIEW_MAP[INSPECT_PATTERN_LEDGER] = "pattern_ledger";
  add INSPECT_PATTERN_LEDGER to _COMMANDS_WITHOUT_PAYLOAD.

brain/ui/command_line.py
  add "pattern-ledger" to LOCAL_COMMAND_VERBS;
  add a parser branch that rejects extra arguments;
  add a HELP entry.

brain/ui/session.py
  add a _dispatch_inspect_pattern_ledger handler that sets
  active_view="pattern_ledger" and writes a bounded status line.
  Does not call observe(...). Does not call tick().

brain/ui/snapshot.py
  optional: extend the snapshot to expose the bounded
  PatternLedgerEntrySummary tuple if a rendered view pane is added.

brain/ui/render.py
  optional: add a "pattern_ledger" view branch that renders the
  bounded snapshot (no observe; no kernel mutation).

brain/ui/fixtures/pattern_ledger_ui_read_only.py
  fixture for I-PLEDGER-17 (and I-PLEDGER-19 in Option B).
```

### Explicitly excluded in v1 (LOCK B, LOCK C)

```text
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
any DB schema file
any SCHEMA_VERSION_V* bump
brain/tick.py
brain/llm/**
brain/tlica/**         (read-only import of COGITO_ID is allowed)
brain/development/text_stream.py   (no changes; only re-imports of constants)
lean_reference/**
scenarios/**
traces/**
```

Step 11 may not exceed this surface. A broader scope must be re-routed
through a new campaign step and a new review gate.

## Proposed fixture plan

Each fixture below names the assertions Step 11 must implement. The
exact filenames match the "Required if accepted" / "Optional under
LOCK K" buckets above.

1. **`pattern_ledger_constructor.py`** — covers I-PLEDGER-01, 02, 03, 10
   - `PatternLedgerSourceKind` has exactly `{OPERATOR, SYSTEM, PROBE_ECHO, GENERATED}` members; iteration order stable; values are bounded printable strings.
   - `PatternLedgerSaturationState` has exactly `{OPEN, SATURATED, QUIESCED}` members.
   - `PatternLedgerEntry(...)` constructs a valid entry from in-bounds inputs.
   - Constructor rejects `COGITO_ID` on `pattern_id`, every signature element, every chunk/candidate evidence id, and `provenance`.
   - Constructor rejects non-printable ids, over-length ids (> `PATTERN_LEDGER_ID_MAX`), non-tuple evidence, and ids whose length exceeds `STREAM_PROVENANCE_MAX_LEN`.
   - Constructor rejects `confidence` not equal to `Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)`.
   - Constructor rejects `confidence` outside `[0, 1]`.
   - Constructor rejects `last_seen_tick < first_seen_tick`.
   - Constructor rejects `source_kind` / `saturation_state` not in the closed enums.
   - Direct constructor with a tuple containing a duplicate evidence id raises `ValueError`.

2. **`pattern_ledger_signature_id.py`** — covers I-PLEDGER-04, 05
   - For a fixed `TextStreamChunk`, the signature derived via the LOCK I formula has element count between 1 and `STREAM_PATTERN_SIG_MAX` and every element bounded printable, never equal to `COGITO_ID`, and contains no raw text payload (no substring of `chunk.text` outside the structural counts).
   - The signature is computed only from `extract_stream_features(chunk)` exact `int` / `Fraction` values.
   - The deterministic id formula `"pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]` is stable across repeated calls on the same chunk.
   - Two chunks whose structural features differ produce different ids.
   - Two chunks whose structural features are identical produce the same id (even if `chunk_id` / `provenance` differ).

3. **`pattern_ledger_observe.py`** — covers I-PLEDGER-06, 07, 08, 09, 11, 12
   - `PatternLedger().observe(chunk, candidate, current_tick=0)` returns a new ledger with exactly one entry; `entries[0].recurrence_count == STREAM_PATTERN_RECURRENCE_MIN`; `confidence == Fraction(STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX)`; `saturation_state == OPEN`.
   - Repeated `observe(...)` on the same signature increments `recurrence_count` by exactly 1 each time and saturates at `STREAM_PATTERN_RECURRENCE_MAX`; no growth beyond cap.
   - Evidence lists cap at `PATTERN_LEDGER_EVIDENCE_MAX` independently for chunk and candidate ids; further unique ids are no-op appends; recurrence may still saturate.
   - Duplicate `chunk_id` (resp. `candidate_id`) is filtered before append; `observe(...)` does not raise.
   - At `len(entries) == PATTERN_LEDGER_MAX_ENTRIES`, a new (unseen) signature returns the same ledger object's content unchanged (identity-equal `entries` tuple); recurrence on existing entries is still possible.
   - `observe(...)` returns a NEW `PatternLedger` (identity check) and the original `entries` tuple is unchanged.
   - Returned entries are tuples (not lists); records are frozen / slotted.

4. **`pattern_ledger_static_audit.py`** — covers I-PLEDGER-15
   - AST audit over `brain/development/pattern_ledger.py` rejects every forbidden module / call enumerated in LOCK M.
   - Allowed imports are exactly the LOCK M allowed list.
   - Module-level statements are limited to imports, constants, function defs, class defs, and an optional docstring.

5. **`pattern_ledger_no_runtime_coupling.py`** — covers I-PLEDGER-14, 16
   - Pre- and post-`observe(...)`, the following identities are unchanged:
     `BrainState`, `MSI`, `PtCns`, `ContentRegistry`, `latest_tick`, `tick_counter`, `event_queue`, source histories.
   - No callable / file handle / socket / subprocess handle / `pathlib.Path` / `sqlite3.Connection` / `sqlite3.Cursor` / curses object / object exposing `eval_consistency` appears in `PatternLedgerEntry` or `PatternLedger` fields (mirrors the `_assert_no_unsafe_resources` discipline).
   - `pattern_ledger.py` does not import `brain.tick` and never invokes `tick(...)`.

6. **`pattern_ledger_stream_integration.py`** — covers I-PLEDGER-13
   - A successful `/stream <text>` dispatch ends with `session.pattern_ledger.entries` length equal to 1 (first call) or 1+N for repeated distinct signatures.
   - A parse failure (`LocalCommandError` from `/stream ""`) leaves `session.pattern_ledger` identity-unchanged.
   - A dispatch failure (e.g. a malformed payload caught after parse) leaves `session.pattern_ledger` identity-unchanged.
   - `/stream-promote <candidate_id>` does not call `observe(...)`; `session.pattern_ledger` identity unchanged.
   - `/step` (success and empty-queue failure) does not call `observe(...)`; `session.pattern_ledger` identity unchanged.
   - Read-only commands (`/stream-summary`, `/stream-candidates`, `/state`, `/tick`, `/session-status`, `/db-summary`, `/profile-summary`, `/stream-db-summary`, `/db-diff`, `/autosave-status`, and the optional `/pattern-ledger`) do not call `observe(...)`; `session.pattern_ledger` identity unchanged across each.
   - `/step` behavior is bit-for-bit identical to its pre-ledger behavior (tick counter, latest_tick, queue, state).

7. **`pattern_ledger_ui_read_only.py`** — covers I-PLEDGER-17 (and I-PLEDGER-19 in Option B). *Only required if Option B is selected.*
   - `LocalCommandLine().parse("/pattern-ledger")` returns a typed command with no payload.
   - `LocalCommandLine().parse("/pattern-ledger foo")` returns `LocalCommandError`.
   - `OperatorSession.dispatch(INSPECT_PATTERN_LEDGER, ...)` sets `active_view = "pattern_ledger"`, writes a bounded printable status line, does not call `observe(...)`, does not call `tick(...)`, and leaves `state`, `latest_tick`, `tick_counter`, `event_queue`, `stream_history`, `stream_candidates`, and `stream_chunk_serial` unchanged.

## Proposed implementation sequence for Step 11

If Step 10 accepts this plan, Step 11 must follow this dependency
order so each intermediate commit is green by `bash tools/check_all.sh`:

```text
1.  Add brain/development/pattern_ledger.py
    - data substrate only;
    - no fixture registered yet (test by `python3 -c` only inside the
      step; do not commit experimental scripts);
    - the static audit fixture exists, so this commit may keep this
      module untracked by the runner if the fixtures are added in
      the same commit (preferred).

2.  Add the constructor / signature / observe fixture modules
    (pattern_ledger_constructor.py, pattern_ledger_signature_id.py,
    pattern_ledger_observe.py).

3.  Add the static audit and no-runtime-coupling fixtures
    (pattern_ledger_static_audit.py, pattern_ledger_no_runtime_coupling.py).

4.  Extend brain/invariants.py FIXTURE_MODULES with the new modules
    (and the _PHASE3_12_PATTERN_LEDGER_PENDING_ROWS guard if rows
    will land in a separate commit; preferred is to land rows and
    fixtures in the same commit).

5.  Patch INVARIANT_CATALOG.md with the I-PLEDGER-* rows and the
    v0.20 -> v0.21 banner block.

6.  Regenerate brain/_catalog_ids.py via
    `python3 -m tools.catalog generate-ids`.

7.  Update tools/catalog.py EXPECTED_COUNTS to the Option A (or B)
    totals.

8.  Add the OperatorSession.pattern_ledger session-local field only
    (do not yet wire the observe call). Extend _ALLOWED_SESSION_ATTRS
    accordingly. Run `bash tools/check_all.sh`; expect green.

9.  Wire the observe call into the successful path of
    _dispatch_stream_append. Add
    brain/development/fixtures/pattern_ledger_stream_integration.py.
    Extend FIXTURE_MODULES. Run `bash tools/check_all.sh`; expect green.

10. (Option B only) Add the /pattern-ledger UI (commands.py,
    command_line.py, session.py dispatcher) and
    brain/ui/fixtures/pattern_ledger_ui_read_only.py.
    Promote I-PLEDGER-17 to REQUIRED in INVARIANT_CATALOG.md and add
    I-PLEDGER-19 STRUCTURAL parser-shape row.
    Update tools/catalog.py EXPECTED_COUNTS to Option B totals.
    Regenerate brain/_catalog_ids.py.

11. Update README.md, CURRENT_MISSION.md, CURRENT_CAMPAIGN.md
    catalog-version stamps.

12. Run `bash tools/check_all.sh` plus the per-fixture commands
    listed below.
```

Each step above must end with `bash tools/check_all.sh` green before
the next is attempted.

## Proposed validation for Step 11

Step 11 must run, in this order, and report PASS/FAIL for each:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Use the repo's existing invariant runner; do not invent a new runner.
The runner's auto-discovery walks `FIXTURE_MODULES`, so adding fixture
modules to that list is the only routing required.

If the operator wants targeted fixture runs while iterating, the
repo's existing convention is to spell out the fixture module path,
e.g.:

```bash
python3 -c "from brain.development.fixtures import pattern_ledger_observe; pattern_ledger_observe.run()"
```

…but the operator-blessed runner is `python3 -m brain.invariants run`.
Step 11 must close with the full five-gate validation above before
committing.

## Count impact estimate

Baseline (current v0.20):

| Category       | Count |
|----------------|-------|
| REQUIRED       |   214 |
| STRUCTURAL     |    83 |
| NOT-EXERCISED  |     9 |
| DEFERRED       |    12 |
| OBSERVED       |    16 |

Proposed v0.21 — **Option A** (no UI, no observed dry run; preferred):

| Category       | Δ | Total |
|----------------|---|-------|
| REQUIRED       | +15 |  229  |
| STRUCTURAL     |  +1 |   84  |
| NOT-EXERCISED  |  +1 |   10  |
| DEFERRED       |  +1 |   13  |
| OBSERVED       |   0 |   16  |
| Total new rows | +18 | (305 → 323 catalog rows; 297 → 315 counted-toward-coverage) |

Proposed v0.21 — **Option B** (include `/pattern-ledger` UI + observed dry run):

| Category       | Δ | Total |
|----------------|---|-------|
| REQUIRED       | +16 |  230  |
| STRUCTURAL     |  +2 |   85  |
| NOT-EXERCISED  |   0 |    9  |
| DEFERRED       |   0 |   12  |
| OBSERVED       |  +1 |   17  |
| Total new rows | +19 | (305 → 324 catalog rows; 297 → 316 counted-toward-coverage) |

**Preferred:** Option A.

**Justification.**

- LOCK K explicitly allows the `/pattern-ledger` UI to be split out
  into a follow-up row family and a follow-up campaign step if it
  broadens Step 11 too much. Step 6 found that recurrence is visible
  through `/session-status`, the rendered view pane, and the stream
  command surface — operators have working surfaces even without
  `/pattern-ledger`. The dispatch-status UX gap is recorded but not
  load-bearing.
- The minimum implementation needed to validate the locks is exactly
  the data substrate plus the `/stream` integration trigger. Option A
  delivers that and no more.
- An OBSERVED end-to-end dry run is valuable but adds a documented
  helper file and an extra fixture-side audit; Step 11's scope is
  already non-trivial. Option A keeps I-PLEDGER-18 as NOT-EXERCISED
  and lets a follow-up campaign step promote it once the data
  substrate is stable.
- Option A's catalog patch is smaller, which reduces review burden at
  Gate B and reduces the risk of an off-by-one in `EXPECTED_COUNTS`.
- Option A is reversible: if Review Gate B (or a later campaign)
  decides the `/pattern-ledger` UI is load-bearing, promoting
  I-PLEDGER-17 from DEFERRED to REQUIRED and adding I-PLEDGER-19 is a
  small, well-scoped follow-up patch.

If Step 10 chooses **ACCEPT WITH AMENDMENTS** with Option B selected,
Step 11 must implement the full Option B surface in one coordinated
patch (including the parser-shape STRUCTURAL row, the UI fixture, and
the observed dry-run helper).

## Risks and mitigations

```text
Semantic / truth creep
  Risk:  signatures that include text-derived fields drift toward
         language labels or readability claims.
  Mitig: LOCK I locks the signature shape to structural counts only;
         I-PLEDGER-04 fixture asserts every element is bounded
         printable and contains no raw text payload; LOCK N forbids
         truth / language labels in any field, method, or docstring.

Growth spam inflation
  Risk:  repeated low-information /stream input could push
         recurrence_count past the saturation cap or extend evidence
         lists indefinitely.
  Mitig: LOCK G saturates recurrence_count; LOCK F caps evidence
         lists independently; LOCK L restricts observe to the
         successful /stream append path only; failed parse / dispatch
         leave the ledger unchanged; I-PLEDGER-06, 11, 12 fixtures
         assert each cap directly.

Session / load mismatch because v1 is not persisted
  Risk:  /save-session then /load-session leaves the on-disk session
         unchanged from the operator's perspective, but the live
         ledger silently snapshots forward across load (it is not
         reset).
  Mitig: LOCK C documents that /load-session does NOT touch
         session.pattern_ledger and explicitly defers any rebuild-on-
         load behavior. The /pattern-ledger snapshot (if Option B is
         chosen) and /session-status report counts that the operator
         can read; the ledger does not pretend to be persisted.
         Documentation in PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md and
         this plan calls out v1's session-local scope.

Accidental tick / BrainState coupling
  Risk:  observe(...) or a constructor reaches into BrainState / MSI
         / PtCns / ContentRegistry / tick_counter / latest_tick, or
         imports brain.tick, brain.llm, brain.ui, or brain.tlica
         beyond the COGITO_ID read.
  Mitig: LOCK M static AST audit enforces the import set;
         I-PLEDGER-15 fixture asserts the audit; I-PLEDGER-14
         runtime fixture asserts identity-stability of every kernel
         container across observe; allowed-import list is exhaustive.

UI scope creep
  Risk:  /pattern-ledger grows into a diff / search / filter API or
         starts mutating state.
  Mitig: LOCK K caps /pattern-ledger as read-only with bounded
         status; I-PLEDGER-17 fixture asserts no observe / no tick
         calls and identity-stability of every kernel container;
         Option A defers the UI entirely. If the UI grows, Step 9
         must be re-run and the UI row family split out into a new
         campaign step.

Catalog count mismatch
  Risk:  Step 11 commits a row but not the EXPECTED_COUNTS bump (or
         vice versa) and the strict gate fails.
  Mitig: Step 11 sequence above ties the row patch and the
         tools/catalog.py EXPECTED_COUNTS bump and the
         brain/_catalog_ids.py regeneration into one coordinated
         commit; check_all.sh runs the strict gate first, so any
         drift fails before the runner.

Fixture sprawl
  Risk:  one fixture per row pattern multiplies maintenance cost.
  Mitig: This plan consolidates 18 rows into 6 fixture modules in
         Option A (7 in Option B), each scoped to a single concern
         (constructor / signature+id / observe / static audit /
         no-coupling / stream integration / optional UI).

Overclaiming operational I as consciousness
  Risk:  row text, status text, or docstrings drift toward
         consciousness / sentience / awareness language.
  Mitig: LOCK N forbids it; this plan repeats LOCK N verbatim
         (see "Locked decisions imported from corrigenda"); Step 11
         must not introduce any aggregate "I-ness" or coherence
         scalar; confidence is per-entry and bounded; PHASE3_12
         non-goals stamp each artifact.
```

## Review Gate B decision request

Step 9 stops here. Step 10 is Review Gate B. The operator must
explicitly choose exactly one:

```text
[ ] ACCEPT PLAN AS WRITTEN
    Step 11 may implement the Option A surface declared in this
    document, within the locks of PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md.

[ ] ACCEPT WITH AMENDMENTS
    Step 11 may implement, subject to the amendments listed below.
    Common amendments:
      - Select Option B (include /pattern-ledger UI + observed dry run).
      - Adjust per-row category (e.g. promote I-PLEDGER-18 to OBSERVED
        without including the UI).
      - Adjust PATTERN_LEDGER_MAX_ENTRIES / PATTERN_LEDGER_EVIDENCE_MAX
        / PATTERN_LEDGER_ID_MAX / PATTERN_LEDGER_SIGNATURE_ELEM_MAX
        constants.
      - Adjust row text wording.
    Amendments must cite the LOCK label being overridden, if any.

[ ] REJECT / REVISE
    Step 9 must be revised before implementation. Provide the
    revision direction.
```

Until Step 10 explicitly accepts (with or without amendments), Step 11
is not authorized. No file under `brain/**`, `tools/**`,
`INVARIANT_CATALOG.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**` may be modified.

## Validation

Re-ran after writing this plan (no source under `brain/**`,
`tools/**`, `INVARIANT_CATALOG.md`, `lean_reference/**`,
`scenarios/**`, or `traces/**` was touched; only this new
documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
