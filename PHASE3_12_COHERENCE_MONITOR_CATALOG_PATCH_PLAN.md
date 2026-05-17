# PHASE3_12_COHERENCE_MONITOR_CATALOG_PATCH_PLAN.md

## Purpose

Plan a future Coherence Monitor catalog patch. This document is
documentation only and does **not** implement the Coherence Monitor.
It does not edit `brain/**`, `tools/**`, `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`lean_reference/**`, `scenarios/**`, or `traces/**`, and it does
not change runtime behavior.

The plan must be precise enough that Step 13 Review Gate C can
decide one of:

```text
ACCEPT PLAN AS WRITTEN — Step 14 may implement within the declared surface
ACCEPT WITH AMENDMENTS — list amendments; Step 14 implements with them
REJECT / REVISE       — Step 12 must be revised before implementation
```

## Baseline

```text
Catalog version:                  v0.21
Counts:
  REQUIRED:                       229
  STRUCTURAL:                      84
  NOT-EXERCISED:                   10
  DEFERRED:                        13
  OBSERVED:                        16
Branch:                           campaign/phase3-12-coherent-i-loop-observatory
Phase 3.11:                       complete; PR #10 merged at 98b55ab
Phase 3.12 steps complete (in commit order on this branch):
  Step 1  566b109  coherent i-loop mission sync
  Step 2  631ae5a  coherent i-loop synthesis
  Step 3  c395989  coherent i-loop kickoff
  Step 4  10a93ee  coherent i-loop matrix
  Step 5  (Review Gate A — passed implicitly by Step 6 execution)
  Step 6  c65d37b  coherent i-loop observatory report
  Step 7  013585e  pattern ledger synthesis
  Step 8  7839f7d  pattern ledger kickoff + corrigenda
  Step 9  ffbe4d9  pattern ledger catalog patch plan
  Step 10 (Review Gate B — ACCEPT PLAN AS WRITTEN)
  Step 11 05e214c  implement pattern ledger option A
Pattern Ledger status:
  Option A implemented as accepted at Review Gate B.
  I-PLEDGER-01..15 REQUIRED (15) — live and green.
  I-PLEDGER-16 STRUCTURAL (1) — live and green.
  I-PLEDGER-17 DEFERRED — /pattern-ledger UI not in v1.
  I-PLEDGER-18 NOT-EXERCISED — end-to-end dry run not in v1.
Step 12 stop condition:
  Step 13 Review Gate C (no implementation in this step).
Preflight (verified at the start of Step 12):
  python3 -m tools.catalog counts     PASS  (229/84/10/13/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (321 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Step 11 Deviation Note

Step 11 added a Phase 3.12c attribute-tier extension to:

```text
brain/ui/fixtures/persistence_observe_resource_audit.py
brain/ui/fixtures/persistence_ops_resource_audit.py
```

Each file already used phase-tier allowlists for the
`OperatorSession.__slots__` attribute surface (see the
`_PHASE_3_10C_SESSION_ATTRS` block baked into the fixtures). The
Phase 3.12c catalog-authorized `OperatorSession.pattern_ledger`
field would otherwise have registered as "drift" against the
I-OBSERVE-08 / I-OPSHARDEN-13 audits. Adding a
`_PHASE_3_12C_SESSION_ATTRS = frozenset({"pattern_ledger"})` tier
and folding it into the `allowed` union is the minimal coherent
fix and mirrors the documented Phase 3.10c precedent in the same
fixtures.

The operator reviewed this deviation and **ACCEPTED IT AS
JUSTIFIED**. The Step 11 implementation did not change runtime
behavior beyond the catalog-authorized Pattern Ledger surface;
positive resource-shape validation of `pattern_ledger` remains
owned by `I-PLEDGER-16` (STRUCTURAL — Pattern Ledger records
carry no callable / handle / client field).

This catalog patch plan **inherits** that mechanism: when Step 14
lands `coherence_monitor.py`, the Coherence Monitor itself adds
**no** new `OperatorSession` slot (Option A is a read-only helper
API; see "Proposed Implementation Surface" below), so no
additional `_PHASE_3_*_SESSION_ATTRS` tier is required in those
two fixtures for Step 14. If a future Step (or Option B
amendment at Review Gate C) ever adds a session field, that step
must add the corresponding phase tier to both audit fixtures and
disclose the addition as a Step 14 deviation in the same shape as
Step 11.

## Proposed Version / Count Strategy

```text
Current catalog version:    v0.21
Proposed catalog version:   v0.22  (if Step 13 accepts)
```

**Reason.** The Coherence Monitor adds a new
engineering-hypothesis row family (`I-COHMON-NN`) that constrains
a new module (`brain/development/coherence_monitor.py`) and a
new set of helper functions that consume existing records. Every
prior catalog expansion (v0.6 through v0.21) bumped the version
on a row-family addition; this plan follows the same convention.

**Exact counts are TBD at implementation planning time.** The
"Proposed Row Family" table below lists 14 candidate rows with
proposed statuses; the operator may amend at Review Gate C
(promote / demote rows, split or merge entries, add or remove
checks). The implementation step (Step 14, if accepted) must
publish exact counts before patching `tools/catalog.py`
`EXPECTED_COUNTS`. As a rough indicator, the table below would
produce:

```text
Δ REQUIRED       : +11   (I-COHMON-01..11)
Δ STRUCTURAL     :  +1   (I-COHMON-12)
Δ DEFERRED       :  +1   (I-COHMON-13 — UI)
Δ NOT-EXERCISED  :  +1   (I-COHMON-14 — end-to-end dry run)
Δ OBSERVED       :   0
Total new rows   : +14
```

Step 14 (if accepted) must update each of:

```text
INVARIANT_CATALOG.md
  - top-of-file version banner: v0.21 -> v0.22
  - new v0.22 banner block documenting the I-COHMON-* expansion
  - new section header for the new owning module
  - new I-COHMON-* row table entries (with Status / Proposition /
    Module / Fixture / Source columns matching the existing schema)

tools/catalog.py
  - EXPECTED_COUNTS dict updated to the v0.22 totals (exact deltas
    above; recompute against the live counts at patch time)

brain/_catalog_ids.py
  - regenerated via `python3 -m tools.catalog generate-ids`

brain/invariants.py
  - FIXTURE_MODULES list extended with the new fixture module paths

README.md
  - top heading "(catalog v0.21)" -> "(catalog v0.22)"
  - Constraints section "Version banner inside should say v0.21" ->
    v0.22, plus the updated counts banner
  - Version-history bullet appended with the v0.22 entry

CURRENT_MISSION.md
  - "Catalog: v0.21" -> "Catalog: v0.22"
  - Counts baseline -> updated totals

CURRENT_CAMPAIGN.md
  - "Catalog: v0.21" -> "Catalog: v0.22"
  - Counts baseline -> updated totals
```

**Step 12 does NOT edit any of the files above.** Step 12 is
documentation only.

## Proposed Row Family

Working name: `I-COHMON-01..I-COHMON-14`. Exact row text, fixture
filenames, and per-row category assignments are finalized at
Review Gate C; the table below is the Step 12 proposal.

| Row ID | Status | Proposition (summary) | Owning module | Fixture | Notes |
|--------|--------|-----------------------|---------------|---------|-------|
| I-COHMON-01 | REQUIRED | `CoherenceCheckStatus` is a finite closed enum with exactly `PASS`, `WARN`, `FAIL`, `NOT_APPLICABLE`. Construction with any other value raises. | `brain/development/coherence_monitor.py` | `coherence_monitor_constructor.py` | Mirrors I-STRM-01 / I-PLEDGER-01 / I-PLEDGER-02 enum-closure pattern. |
| I-COHMON-02 | REQUIRED | `CoherenceCheck` constructor enforces bounded printable `check_id` / `summary` / `detail` / `source`, a closed `CoherenceCheckStatus`, no `COGITO_ID` in any string field, and length caps (`MAX_CHECK_ID_LEN`, `MAX_SUMMARY_LEN`, `MAX_DETAIL_LEN`); `source` is one of the closed `CHECK_SOURCES` values. | `brain/development/coherence_monitor.py` | `coherence_monitor_constructor.py` | Strict constructor; silent normalization forbidden. |
| I-COHMON-03 | REQUIRED | `CoherenceSnapshot` constructor enforces non-negative int counts (`tick_counter`, `profile_domain_size`, `msi_size`, `registry_size`, `stream_chunk_count`, `stream_candidate_count`, `pattern_ledger_entry_count`), bool `session_db_configured`, bounded printable `autosave_mode` (either `""` or an `AutosaveMode` enum value), tuple-typed `checks` capped at `COHERENCE_MAX_CHECKS`, frozen/slotted shape, and no callable / handle / client field. | `brain/development/coherence_monitor.py` | `coherence_monitor_constructor.py` | Mirrors I-PLEDGER-03 / I-PLEDGER-08 constructor + cap discipline. |
| I-COHMON-04 | REQUIRED | Kernel coherence checks are read-only and detect COGITO / profile / MSI / PtCns / domain consistency without mutating `BrainState`. | `brain/development/coherence_monitor.py` | `coherence_monitor_kernel_checks.py` | Covers the six kernel rows from the synthesis's "Kernel coherence" list. Identity-stable assertions on `state.profile` / `state.msi` / `state.ptcns` / `state.registry` before vs after the check run. |
| I-COHMON-05 | REQUIRED | OperatorSession coherence checks are read-only and detect unsafe resources, illegal `active_view`, oversized queue / status / error without mutating the session. | `brain/development/coherence_monitor.py` | `coherence_monitor_session_checks.py` | Re-uses the I-UI-10 / I-UI-13 audit bodies as read-only checks; identity-stable assertions on every `OperatorSession` slot. |
| I-COHMON-06 | REQUIRED | Stream coherence checks are read-only and respect `STREAM_HISTORY_MAX_CHUNKS`, `STREAM_PROMOTION_MAX`, `stream_chunk_serial`, and `COGITO_ID` rejection. | `brain/development/coherence_monitor.py` | `coherence_monitor_pattern_ledger_checks.py` (shared with pledger checks) or a dedicated `coherence_monitor_stream_checks.py` if Review Gate C prefers the split | Covers the four stream rows from the synthesis. |
| I-COHMON-07 | REQUIRED | Pattern Ledger coherence checks validate entry bounds, deterministic ids, the locked confidence formula, recurrence caps, evidence caps, and the session-local / non-persistence policy. | `brain/development/coherence_monitor.py` | `coherence_monitor_pattern_ledger_checks.py` | Re-runs the I-PLEDGER-* constructor invariants on every live entry, and (statically) asserts `brain/ui/persistence*.py` contains no `pattern_ledger` reference (LOCK B). |
| I-COHMON-08 | REQUIRED | Persistence / autosave coherence reporting is read-only and does not open the DB or call `save_session` / `load_session` / `db_backup` / autosave unless a later review gate explicitly authorizes it. | `brain/development/coherence_monitor.py` | `coherence_monitor_no_runtime_coupling.py` | Static AST audit asserts no `sqlite3.connect`, no `save_session(` call, no `load_session(` call, no `db_backup(` call, no `maybe_autosave_after_mutation(` call in `coherence_monitor.py`. |
| I-COHMON-09 | REQUIRED | Overall status aggregation is deterministic: `FAIL` dominates `WARN` dominates `PASS`; `NOT_APPLICABLE` does not create a false `PASS` / `FAIL`. | `brain/development/coherence_monitor.py` | `coherence_monitor_constructor.py` | Pure-function unit check on `compute_overall_status(...)` over hand-crafted tuples of `CoherenceCheck` values. |
| I-COHMON-10 | REQUIRED | Coherence Monitor has no `tick()` / LLM / network / filesystem / shell / curses / `importlib` side effects and no dynamic execution. | `brain/development/coherence_monitor.py` | `coherence_monitor_static_audit.py` | Static AST audit (Section "Proposed Static Audit" below) plus a runtime cross-check that `coherence_monitor` module globals contain neither `tick`, `LLMClient`, nor a real DB / filesystem handle. |
| I-COHMON-11 | REQUIRED | No consciousness / sentience / subjective / semantic / truth / agency / self-modification claims or aggregate "I-ness" score appear in fields, docstrings, or report output. | `brain/development/coherence_monitor.py` | `coherence_monitor_static_audit.py` | Static string audit over the module source AND over every `CoherenceCheck.summary` / `.detail` template; mirrors LOCK N from the Pattern Ledger corrigenda. The bounded report rendering function returns text whose lowercased form contains no forbidden term. |
| I-COHMON-12 | STRUCTURAL | `CoherenceSnapshot` / `CoherenceReport` store no callable, file handle, socket, subprocess handle, `pathlib.Path`, `sqlite3.Connection` / `Cursor`, curses object, or LLM-client-shaped object (no `eval_consistency`). | `brain/development/coherence_monitor.py` | `coherence_monitor_no_runtime_coupling.py` | Mirrors I-UI-10 / I-PLEDGER-16 runtime resource audit. |
| I-COHMON-13 | DEFERRED | Optional `/coherence-summary` read-only operator command is deferred unless a later review gate accepts UI expansion. | `brain/ui/` | (none) | Mirrors the I-PLEDGER-17 DEFERRED pattern. If a follow-up review gate promotes this row, the dispatch must set `active_view = "coherence_summary"` and a bounded status line only, call no `observe(...)`, call no `tick(...)`, open no DB, and mutate no kernel container. |
| I-COHMON-14 | NOT-EXERCISED | End-to-end Coherence Monitor report dry run placeholder. | `brain/development/coherence_monitor.py` | (none) | Mirrors the I-PLEDGER-18 NOT-EXERCISED pattern. A future campaign step may promote this row to OBSERVED with a documented helper that produces a `CoherenceReport` over a deterministic scripted session. |

Per-row category summary (proposed):

```text
REQUIRED      : 11  (I-COHMON-01..11)
STRUCTURAL    :  1  (I-COHMON-12)
DEFERRED      :  1  (I-COHMON-13)
NOT-EXERCISED :  1  (I-COHMON-14)
OBSERVED      :  0
Total new rows: 14
```

## Proposed Implementation Surface

Planning only. Step 14 (if accepted) is limited to the surface
below.

### Required if accepted

```text
brain/development/coherence_monitor.py
  new module; data substrate + pure builder/aggregator helpers;
  imports limited to dataclasses, enum, fractions, typing,
  brain.development.pattern_ledger, brain.development.text_stream,
  brain.io_types, brain.tlica.profile (COGITO_ID),
  brain.tlica.msi, brain.tlica.ptcns,
  brain.tick (BrainState typed record only — NOT the tick
  callable), brain.ui.session (OperatorSession typed record
  only), brain.ui.snapshot (ACTIVE_VIEWS),
  brain.ui.commands (closed read-only command set, used for
  static cross-checks only); read-only.

brain/development/fixtures/coherence_monitor_constructor.py
  fixture for I-COHMON-01, I-COHMON-02, I-COHMON-03, I-COHMON-09.

brain/development/fixtures/coherence_monitor_kernel_checks.py
  fixture for I-COHMON-04 (kernel coherence checks).

brain/development/fixtures/coherence_monitor_session_checks.py
  fixture for I-COHMON-05 (operator-session coherence checks).

brain/development/fixtures/coherence_monitor_pattern_ledger_checks.py
  fixture for I-COHMON-06 (stream coherence) and I-COHMON-07
  (pattern ledger coherence). Review Gate C may split this into
  two fixture files if it prefers tighter scope.

brain/development/fixtures/coherence_monitor_static_audit.py
  fixture for I-COHMON-10, I-COHMON-11 (static / string audits).

brain/development/fixtures/coherence_monitor_no_runtime_coupling.py
  fixture for I-COHMON-08, I-COHMON-12 (runtime resource +
  persistence-no-open audits).

brain/invariants.py
  FIXTURE_MODULES extension (six new module paths above; one
  more if Review Gate C splits the stream / pledger fixture).

INVARIANT_CATALOG.md
  new I-COHMON-* row entries; version banner v0.21 -> v0.22;
  new v0.22 banner block.

brain/_catalog_ids.py
  regenerated by `python3 -m tools.catalog generate-ids`.

tools/catalog.py
  EXPECTED_COUNTS dict updated to v0.22 totals.

README.md
  catalog-version stamp v0.21 -> v0.22 (top heading + Constraints
  block); appended v0.22 entry in version history.

CURRENT_MISSION.md
  baseline block catalog/counts update v0.21 -> v0.22.

CURRENT_CAMPAIGN.md
  baseline block catalog/counts update v0.21 -> v0.22.
```

### Explicitly excluded for first implementation

```text
brain/tick.py
brain/llm/**
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
brain/ui/commands.py        (no INSPECT_COHERENCE_SUMMARY in v1)
brain/ui/command_line.py    (no /coherence-summary verb in v1)
brain/ui/render.py
brain/ui/snapshot.py        (no new active_view in v1; ACTIVE_VIEWS unchanged)
brain/ui/session.py         (no new OperatorSession field in v1)
brain/development/text_stream.py    (no signature changes)
brain/development/pattern_ledger.py (no signature changes; Pattern Ledger is read as-is)
DB schema files / SCHEMA_VERSION bumps
lean_reference/**
scenarios/**
traces/**
```

Step 14 may not exceed this surface. A broader scope must be
re-routed through a new campaign step and a new review gate.

### Notes on dependency direction

The Coherence Monitor reads from the kernel and the operator UI
side — it depends on `brain.ui.session` and `brain.ui.snapshot`.
This is acceptable for a *development substrate* that exists
outside the operator UI and consumes UI records read-only. The
implementation must keep this dependency direction shallow:
import only the typed records and the `ACTIVE_VIEWS` /
`_ALLOWED_SESSION_ATTRS` constants, **not** the dispatchers,
**not** the renderer, **not** the parser. The static audit row
(I-COHMON-10) and the resource audit row (I-COHMON-12) lock that
shape.

The Coherence Monitor **must not** be imported from `brain.tick`,
`brain.llm`, `brain.tlica`, `brain.development.text_stream`, or
`brain.development.pattern_ledger`. The dependency arrow points
only one way: monitor → existing records.

## Proposed Static Audit

For the future `brain/development/coherence_monitor.py`, the
static AST audit (driving I-COHMON-10 and I-COHMON-11) must
reject every entry in the forbidden list below.

Forbidden imports / module references:

```text
os
os.system
subprocess
socket
urllib
http
requests
pathlib
tempfile
shutil
curses
brain.llm
brain.tick                  (the tick callable; the BrainState typed
                             record may be imported as a TYPE only,
                             not the function tick(...))
threading
asyncio
atexit
signal
signal.signal
importlib
```

Forbidden builtins / dynamic-execution calls:

```text
eval
exec
compile
__import__
importlib.import_module
importlib.__import__
```

Allowed imports:

```text
dataclasses
enum
fractions
typing
brain.development.pattern_ledger    (PatternLedger / PatternLedgerEntry
                                     / derive_pattern_id / derive_pattern_signature;
                                     read-only)
brain.development.text_stream       (constants and bounded record types;
                                     read-only)
brain.io_types                      (ContentRegistry / shared bounded primitives;
                                     read-only)
brain.tlica.profile                 (COGITO_ID for rejection checks; read-only)
brain.tlica.msi                     (MSI typed record; read-only)
brain.tlica.ptcns                   (PtCns typed record; ConsistencyEval enum;
                                     read-only — never PtCns.evaluate(...))
brain.tick                          (BrainState typed record ONLY; the audit
                                     must reject any reference to the tick(...)
                                     callable; the corresponding pattern is the
                                     I-PERSIST-12 audit that allows
                                     `from brain.tick import BrainState` but
                                     rejects `from brain.tick import tick` and
                                     any `tick(...)` call.)
brain.ui.session                    (OperatorSession typed record + the
                                     _ALLOWED_SESSION_ATTRS constant; read-only)
brain.ui.snapshot                   (ACTIVE_VIEWS constant; read-only)
brain.ui.commands                   (closed OperatorCommand set; read-only — never
                                     dispatched from inside the monitor)
```

The audit must additionally:

- Reject any module-level statement other than imports, constants,
  function defs, class defs, and an optional docstring.
- Reject any module-level call that invokes `tick(`,
  `save_session(`, `load_session(`, `db_backup(`,
  `db_verify(`, `sqlite3.connect(`, or
  `maybe_autosave_after_mutation(`.
- Reject string-form references to forbidden behaviors (`eval(`,
  `exec(`, `compile(`, `__import__(`, `importlib.import_module`,
  `atexit.register`, `signal.signal`, `subprocess.`, `socket.`,
  `pathlib.`, `tempfile.`, `shutil.`).
- Reject the appearance of any forbidden non-claim term inside
  the module source or inside any `CoherenceCheck.summary` /
  `.detail` template (case-insensitive): `conscious`,
  `consciousness`, `sentience`, `sentient`, `subjective`,
  `subjective experience`, `qualia`, `aware`, `awareness`,
  `I-ness`, `understand`, `understands`, `understanding`,
  `comprehend`, `comprehends`, `comprehension`, `believe`,
  `believes`, `intends`, `intent`. The runtime cross-check
  asserts the same property over `build_coherence_report(...)`
  output for representative inputs.

Implementation reminder for Step 14: the audit's
allowed-imports list above is broader than the Pattern Ledger's
LOCK M list because the Coherence Monitor must *read* the
operator-side records (OperatorSession, ACTIVE_VIEWS, OperatorCommand)
to compute structural agreement. The audit must enforce that
those imports are used **as types and as bounded constants
only** — never as call surfaces.

## Proposed Review Gate C

Step 12 stops here. Step 13 is Review Gate C. The operator must
explicitly choose exactly one:

```text
[ ] ACCEPT PLAN AS WRITTEN
    Step 14 may implement the surface declared in this document,
    within the locks of PHASE3_12_COHERENCE_MONITOR_SYNTHESIS.md.

[ ] ACCEPT WITH AMENDMENTS
    Step 14 may implement, subject to the amendments listed below.
    Common amendments:
      - Promote I-COHMON-13 (UI) to REQUIRED and add an
        Option B `/coherence-summary` surface in v1.
      - Promote I-COHMON-14 to OBSERVED with a documented dry-run
        helper.
      - Split the I-COHMON-06 / I-COHMON-07 fixture into separate
        stream-checks / pattern-ledger-checks fixture modules.
      - Adjust per-check `check_id` strings or status defaults.
      - Adjust `COHERENCE_MAX_CHECKS` / `MAX_SUMMARY_LEN` /
        `MAX_DETAIL_LEN` constants.
      - Adjust row text wording.

[ ] REJECT / REVISE
    Step 12 must be revised before implementation. Provide the
    revision direction.
```

Step 14 may apply the implementation **only after** Step 13
acceptance, and **only within** the surface declared in this
document and the synthesis. Until then, no file under
`brain/**`, `tools/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`lean_reference/**`, `scenarios/**`, or `traces/**` may be
modified.

## Validation

Re-ran after writing this plan (no source under `brain/**`,
`tools/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, `lean_reference/**`,
`scenarios/**`, or `traces/**` was touched; only this new
documentation file and its companion synthesis were added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
