# PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md

## Purpose

Audit `PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_KICKOFF.md`
before the ops/observability catalog patch plan. This is a planning
artifact only. It does not edit the catalog, runtime modules,
fixtures, README, traces, scenarios, or guarded kernel paths.

Verdict for Step 4:

```text
COHERENT - PROCEED TO OPS/OBSERVABILITY CATALOG PATCH PLAN
```

## 1. Baseline

```text
Catalog version:  v0.17
REQUIRED:        187
STRUCTURAL:       69
NOT-EXERCISED:    10
DEFERRED:         12
OBSERVED:         13
Total fixtures:  106
Current phase:    Phase 3.10 Operational Hardening + Persistence
                  Observability + Autosave
```

Accepted prior artifacts:

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_SYNTHESIS.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_KICKOFF.md
```

## 2. Module placement

Kickoff proposal:

```text
Option K-B (split).
  brain/ui/persistence.py            unchanged save/load core.
  brain/ui/persistence_ops.py        new (Phase 3.10a).
  brain/ui/persistence_observe.py    new (Phase 3.10b).
  brain/ui/autosave.py               new (Phase 3.10c only; Step 18).
```

Corrigendum:

```text
ACCEPTED.
```

Reasoning:

```text
- Track A (write: /db-backup) and track B (read-only) have
  materially different audit surfaces. Keeping them in separate
  files lets the Phase 3.10b static audit reject every code path
  that could open the DB for write inside the observability
  module.
- Phase 3.10c autosave is the highest-policy track; isolating it
  in its own file makes the Step 16 review gate a minimal diff.
- brain/ui/persistence.py stays the canonical save/load home; its
  existing static audit (I-PERSIST-12) is unchanged. The new
  modules import its typed records and helpers.
- The corrigenda does NOT authorize any change to
  brain/ui/persistence.py's public API in Phase 3.10a/b except
  one narrow extension: promoting _snapshot_session to a public
  helper. See Section 9.
```

Decision:

```text
The catalog plan must use the following owning-module identifiers:

  Phase 3.10a rows:  brain/ui/persistence_ops.py
  Phase 3.10b rows:  brain/ui/persistence_observe.py

Fixtures live under brain/ui/fixtures/persistence_ops_*.py and
brain/ui/fixtures/persistence_observe_*.py.
```

## 3. Typed report records

Kickoff proposal:

```text
SessionStatusReport
DbStatusReport
DbVerifyReport
DbBackupReport
DbSummaryReport
ProfileSummaryRow
ProfileSummaryReport
StreamDbSummaryRow
StreamDbSummaryReport
DbDiffField
DbDiffReport
```

Corrigendum:

```text
ACCEPTED WITH BOUNDED-STRING / NO-FLOAT / NO-REPR RULES.
```

Additions required for the catalog patch plan:

```text
- Every string field in every report is bounded printable. The
  corrigenda fixes the cap as OPS_REPORT_TEXT_MAX_LEN = 256 (path,
  version, timestamp, error_text) and PROFILE_VALUE_STRING_MAX_LEN
  = 64 (rendered Fraction "num/den" strings). The catalog plan
  must encode the bound enforcement in a fixture.
- Every integer field is non-negative; the constructors raise on
  negatives.
- No report stores a Fraction, float, list, or sqlite3.Connection.
  Fractions are rendered as exact "num/den" strings at the
  boundary; the catalog plan must include a fixture that asserts
  no float() / repr() / str(Fraction(...)) appears in the render
  paths (the "exact 'num/den' renderer" is a single helper).
- DbDiffField.field strings come from a finite enumeration declared
  in source. The enumeration is:
    "profile.<content_id>"
    "msi.contents"
    "msi.threshold"
    "ptcns_eval.<content_id>"
    "registry.<content_id>"
    "tick_counter"
    "stream_chunk_serial"
    "stream_history.count"
    "stream_candidates.count"
  Any other field name raises at construction time.
- DbDiffField.live / .saved use exact-Fraction "num/den" strings
  for kernel numeric values, integer text for counters, the
  literal "<missing>" for one-sided absence, and a hash-stable
  string for the msi.contents set diff (sorted comma-joined
  content_ids).
- StreamDbSummaryRow.text_preview cap STREAM_TEXT_PREVIEW_MAX_LEN
  is locked at 64. The corrigenda forbids 256+; a long preview is
  effectively the full chunk for typical sessions and would
  duplicate the Phase 3.7 bounded text policy.
- ProfileSummaryReport sorts COGITO_ID first, then other
  content_ids ASCII-ascending. The fixture asserts the sort order
  is deterministic across runs.
```

Decision:

```text
The kickoff's report shapes are coherent. The catalog plan must
add bound-enforcement and finite-field-enumeration rows.
```

## 4. Helper signatures

Kickoff proposal:

```text
session_status(session) -> SessionStatusReport
db_status(config) -> DbStatusReport
db_verify(config, *, rebuild_candidates_if_missing=True) -> DbVerifyReport
db_backup(config, dest_path, *, force=False) -> DbBackupReport
db_summary(config) -> DbSummaryReport
profile_summary(config, *, row_cap=PROFILE_SUMMARY_ROW_CAP)
                                -> ProfileSummaryReport
stream_db_summary(config, *, head_cap, tail_cap)
                                -> StreamDbSummaryReport
db_diff(session, config, *, row_cap=DB_DIFF_ROW_CAP)
                                -> DbDiffReport
```

Corrigendum:

```text
ACCEPTED WITH LOCKED DEFAULTS.
```

Locked defaults (catalog plan binds to these):

```text
PROFILE_SUMMARY_ROW_CAP       = 64
STREAM_DB_SUMMARY_HEAD_CAP    = 8
STREAM_DB_SUMMARY_TAIL_CAP    = 8
DB_DIFF_ROW_CAP               = 32
STREAM_TEXT_PREVIEW_MAX_LEN   = 64
OPS_REPORT_TEXT_MAX_LEN       = 256
PROFILE_VALUE_STRING_MAX_LEN  = 64
```

Behavior contracts (catalog plan binds these):

```text
- session_status performs NO disk IO. It reads OperatorSession
  fields only.
- db_status / db_verify / db_summary / profile_summary /
  stream_db_summary / db_diff open the DB in mode=ro through
  sqlite3.connect("file:<path>?mode=ro", uri=True) inside a
  `with conn:` block.
- db_backup opens the source DB in mode=ro and the destination in
  normal write mode; both connections live inside `with conn:`
  blocks.
- db_verify reuses load_session (not a parallel deserializer) and
  immediately discards the returned candidate. The static AST
  audit confirms the call chain.
- db_diff reuses _snapshot_session on the live session and reuses
  _deserialize_from_db on the saved snapshot. It does NOT invoke
  any kernel builder.
- All eight helpers return a typed report with error_text
  populated on operational failure; PersistenceError is reserved
  for argument errors and TypeError-style violations.
- No helper calls tick().
- No helper opens an LLM client / socket / subprocess / curses
  context.
- No helper stores a sqlite3.Connection on OperatorSession.
```

Decision:

```text
The helper signatures are coherent. The catalog plan must lock the
default constants in a STRUCTURAL row and the no-builder-call
property in a separate STRUCTURAL row.
```

## 5. CLI flag set

Kickoff proposal:

```text
--db-status
--db-verify
--db-backup PATH
--db-backup-force
--autosave-mode <mode>   (sketch; Step 18 locks)
```

Corrigendum:

```text
ACCEPTED FOR --db-status / --db-verify / --db-backup /
--db-backup-force.

--autosave-mode IS DEFERRED to Step 18. Phase 3.10a/b does NOT
land an --autosave-mode flag.
```

Reasoning:

```text
- A flag that is "parsed but only accepts 'off'" is misleading
  and increases the static-audit surface unnecessarily. Phase
  3.10a/b is read-mostly; autosave wiring belongs entirely in
  Step 18.
- --db-status / --db-verify / --db-backup short-circuit before
  parse_llm_runtime_args and curses initialization. The corrigenda
  pins this order:
    1. argparse
    2. --check-terminal short-circuit (existing)
    3. --print-once short-circuit (existing)
    4. --db-status / --db-verify / --db-backup short-circuit
       (new; mutually exclusive)
    5. parse_llm_runtime_args + LLM client construction
    6. configure_session_store + (optional) attempt_load
    7. curses initialization
- The three new flags are mutually exclusive at the argparse
  level. The catalog plan must include a fixture that asserts
  the parser raises on combining them.
- --db-backup PATH rejects URI-like destinations
  (sqlite://, file:, http://, https://, ftp://, ws://, wss://).
  The corrigenda requires a fixture asserting this rejection.
- --db-backup-force is the right name (parallel to existing
  --no-load-session / --load-session boolean pairs). The
  corrigenda forbids --force as a global flag; backup-force
  must be backup-scoped.
- Exit code 0 on PASS / success; exit code 1 on FAIL / failure.
  The catalog plan must include a fixture asserting the exit
  code mapping.
```

Decision:

```text
The kickoff's CLI surface is coherent except for --autosave-mode,
which is removed from Phase 3.10a/b and reintroduced at Step 18.
The catalog plan must include:
  - one REQUIRED row for short-circuit ordering;
  - one REQUIRED row for mutual exclusion;
  - one REQUIRED row for URI rejection on --db-backup;
  - one STRUCTURAL row for exit code mapping.
```

## 6. Closed parser verb additions

Kickoff proposal:

```text
/session-status
/db-status
/db-verify
/db-summary
/profile-summary
/stream-db-summary
/db-diff
/db-backup <path> [--force]
/autosave-status      (sketch)
/autosave-enable      (sketch)
/autosave-disable     (sketch)
```

Corrigendum:

```text
ACCEPTED FOR THE EIGHT NON-AUTOSAVE VERBS.
THE THREE AUTOSAVE VERBS ARE DEFERRED to Step 18.
```

Parser-shape rules (catalog plan binds these):

```text
- /session-status, /db-status, /db-verify, /db-summary,
  /profile-summary, /stream-db-summary, /db-diff take no args;
  trailing args are rejected as LocalCommandError.
- /db-backup takes exactly one positional argument (the
  destination path) plus an optional --force flag token. Other
  flags raise LocalCommandError.
- The path argument to /db-backup is parsed as a pathlib.Path
  through the existing bounded printable id rules; it is then
  validated for URI-scheme rejection. The composer parser does
  NOT perform shell expansion / glob expansion / variable
  substitution.
- All eight verbs are reachable only from the typed composer.
  The catalog plan must include a static-audit row asserting
  no curses keybinding shortcut invokes a Phase 3.10 command
  (parallel to the existing /save-session / /load-session
  audit).
```

Decision:

```text
The kickoff's parser surface is coherent. The catalog plan must
add one STRUCTURAL row per verb covering the closed-arg shape
plus one REQUIRED row asserting the typed composer is the only
entry point.
```

## 7. OperatorCommand additions

Kickoff proposal:

```text
SESSION_STATUS
DB_STATUS
DB_VERIFY
DB_SUMMARY
PROFILE_SUMMARY
STREAM_DB_SUMMARY
DB_DIFF
DB_BACKUP
AUTOSAVE_STATUS    (Step 18 wiring)
AUTOSAVE_ENABLE    (Step 18 wiring)
AUTOSAVE_DISABLE   (Step 18 wiring)
```

Corrigendum:

```text
ACCEPTED FOR THE EIGHT NON-AUTOSAVE MEMBERS.
THE THREE AUTOSAVE MEMBERS ARE DEFERRED to Step 18.
```

Payload shapes:

```text
- SESSION_STATUS, DB_STATUS, DB_VERIFY, DB_SUMMARY, PROFILE_SUMMARY,
  STREAM_DB_SUMMARY, DB_DIFF: no payload.
- DB_BACKUP: DbBackupPayload(dest_path: pathlib.Path, force: bool).
```

The catalog plan must include a row asserting:

```text
- _COMMANDS_WITHOUT_PAYLOAD is extended to include SESSION_STATUS,
  DB_STATUS, DB_VERIFY, DB_SUMMARY, PROFILE_SUMMARY,
  STREAM_DB_SUMMARY, DB_DIFF (parallel to the existing Phase 3.9
  SAVE_SESSION / LOAD_SESSION rule).
- DB_BACKUP's payload is the only Phase 3.10a/b payload; make_command
  validates it through DbBackupPayload's constructor.
```

## 8. Dispatch handler placement

Kickoff proposal:

```text
_dispatch_session_status
_dispatch_db_status
_dispatch_db_verify
_dispatch_db_summary
_dispatch_profile_summary
_dispatch_stream_db_summary
_dispatch_db_diff
_dispatch_db_backup
_dispatch_autosave_*   (Step 18)
```

Corrigendum:

```text
ACCEPTED ON OperatorSession.
```

Behavior contract for every Phase 3.10a/b dispatch handler:

```text
- Reads session_store_config (or, for /session-status, reads no
  config); surfaces a bounded error_message ("no session DB
  configured") if the config is None.
- Calls the persistence_ops or persistence_observe helper inside
  a try / except.
- On PersistenceError: stores a bounded printable error_text into
  error_message; clears status_message; returns without
  mutating any other field.
- On success: stores a bounded printable summary line into
  status_message; clears error_message.
- Never calls tick().
- Never imports curses.
- Never opens a sqlite3.Connection directly (the helpers own
  connection lifetime).
```

The catalog plan must include one REQUIRED row covering the
common dispatch shape and one STRUCTURAL row asserting the
try/except + bounded-error envelope is present in every handler.

## 9. _snapshot_session promotion

Kickoff question:

```text
Whether _snapshot_session (currently private inside
brain/ui/persistence.py) may be promoted to a public helper for
db_diff.
```

Corrigendum:

```text
PROMOTED TO PUBLIC.
```

Rationale:

```text
- db_diff requires a typed snapshot of the live session. Calling
  the private helper from outside brain/ui/persistence.py would
  re-export it informally; promotion makes the contract explicit.
- _snapshot_session is a pure projection: OperatorSession ->
  PersistentSessionSnapshot. It performs no IO, no builder call,
  no mutation. Promoting it does not widen the persistence
  module's behavior surface.
- The promotion is a one-name change (drop leading underscore).
  The existing Phase 3.9 static audit (I-PERSIST-12) need not
  change beyond the new public-name allowance.
```

The catalog plan must include:

```text
- One STRUCTURAL row asserting snapshot_session(session) is a
  pure projection (no IO; no builder; no mutation).
- An update to the Phase 3.9 static-audit fixture allowing the
  new public name (kept under the same I-PERSIST-12 row; the
  corrigenda treats this as a tightening, not a new row).
```

The Phase 3.10 catalog plan does NOT modify any existing
I-PERSIST-* row; it adds an annotation to the existing static
audit fixture if needed.

## 10. Backup mechanism

Kickoff proposal:

```text
db_backup uses sqlite3.Connection.backup() (the typed page-level
Backup API).
```

Corrigendum:

```text
ACCEPTED.
```

Reasoning:

```text
- sqlite3.Connection.backup() is the standard-library typed API
  for copying a SQLite database. It is page-faithful and works
  even if the source is being written by another process (not
  relevant here, since the source is opened in mode=ro).
- shutil.copy2 / shutil.copyfile would also work, but they bypass
  the SQLite layer and are harder to audit (e.g. they can copy
  -journal / -wal files that the campaign has not authorized).
  Using Connection.backup() keeps the copy through a typed SQLite
  call that the static audit can target precisely.
- The destination is created inside a `with sqlite3.connect(...)
  as dest:` context. Source uses mode=ro `with` connection.
- Page progress is exposed by Connection.backup(); the catalog
  plan must include the pages_copied / total_pages report fields.
```

The catalog plan must include:

```text
- One REQUIRED row asserting db_backup uses
  sqlite3.Connection.backup() (not shutil).
- One STRUCTURAL row asserting source connection mode=ro
  during backup.
- One REQUIRED row asserting db_backup never overwrites without
  force=True and never overwrites the source file.
```

## 11. URI rejection on --db-backup PATH

Kickoff proposal:

```text
--db-backup PATH rejects URI-like destinations (sqlite://, file:,
http://, etc.).
```

Corrigendum:

```text
ACCEPTED.
```

Forbidden scheme list (catalog plan must encode):

```text
sqlite:
file:
http:
https:
ftp:
ws:
wss:
data:
gopher:
ssh:
git:
```

The catalog plan must include:

```text
- One REQUIRED row asserting the forbidden scheme list is rejected
  at argparse time (before any sqlite3 call).
- One REQUIRED row asserting the same rejection applies to the
  /db-backup composer verb (parser symmetry with the CLI flag).
- A single fixture covers both call sites by sharing the URI
  scheme rejection helper.
```

## 12. Resource discipline

Kickoff proposal:

```text
No sqlite3.Connection on OperatorSession.
Connections opened inside `with conn:` blocks.
No thread / signal handler / atexit / asyncio loop.
Persistence-adjacent modules import only a documented set.
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require:

```text
- A persistence_ops_resource_audit.py fixture confirming the
  session field shape is unchanged by Phase 3.10a (no new
  OperatorSession fields in 3.10a/b).
- A persistence_observe_resource_audit.py fixture mirror.
- persistence_ops_static_audit.py and
  persistence_observe_static_audit.py covering the import sets:
    sqlite3, dataclasses, fractions, datetime, pathlib, typing,
    brain.ui.persistence, brain.ui.session, brain.io_types,
    brain.tlica.profile (COGITO_ID only).
  Forbidden imports (catalog plan encodes):
    pickle, shelve, marshal, dill, cloudpickle, joblib,
    subprocess, socket, urllib, http, requests, curses,
    brain.tick, brain.tlica internals beyond builders,
    brain.llm.
- The Phase 3.10b static audit additionally rejects every
  *_session builder import (the observability module does NOT
  call builders).
```

## 13. Failure isolation contract

Kickoff proposal:

```text
- PersistenceError on invalid arguments / unrecoverable preconditions.
- Typed report with error_text populated on operational failure.
- Never partially mutates the live OperatorSession.
- Never partially writes the source DB except for /db-backup
  destination.
- Every Connection inside a `with conn:` block.
- Dispatcher catches every exception; no propagation into curses.
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require fixtures for:

```text
- DB does not exist                                    (status / verify / summary / diff / backup)
- DB is a directory                                    (status / verify / summary / diff / backup)
- DB schema_version row missing                        (status / verify)
- DB schema_version row holds unknown integer          (verify)
- profile_values row violates CHECK rho_den > 0        (verify / summary / diff)
- ContentRegistry text exceeds bounded length          (verify)
- Fraction(rho_num, rho_den) is outside [0, 1]         (verify)
- make_profile_with_cogito raises                      (verify)
- assert_state_invariants raises after assembly        (verify)
- destination path exists and force=False              (backup)
- destination path is the source path                  (backup)
- destination path parses as URI                       (backup)
- sqlite3.Connection.backup() raises mid-copy          (backup)
```

Every fixture asserts:

```text
- PersistenceError raised OR typed report with error_text
  populated, depending on the helper's contract.
- The live OperatorSession field-for-field equals the pre-call
  session.
- The source DB file is byte-identical to the pre-call state.
- For backup failure: the report explicitly warns about
  destination state; the source is unchanged.
```

The catalog plan may consolidate read-side failures into one or
two parameterized fixtures, mirroring how Phase 3.9 consolidated
its failed_load cases.

## 14. Phase 3.10c (autosave) separation

Kickoff proposal:

```text
Phase 3.10a + 3.10b must NOT introduce any code path that invokes
save_session outside the existing /save-session dispatch, any
timer / thread / signal handler / atexit / asyncio loop, or any
flag that flips autosave on at startup.
```

Corrigendum:

```text
ACCEPTED AS HARD BOUNDARY.
```

The catalog plan must include:

```text
- One STRUCTURAL row (a defensive autosave-absent audit, parallel
  to the existing I-PERSIST autosave NOT-EXERCISED row) asserting
  no autosave entry point exists in brain/ui/persistence_ops.py or
  brain/ui/persistence_observe.py.
- One STRUCTURAL row asserting no @atexit, signal handler,
  threading primitive, or asyncio primitive appears in either
  module.
```

These rows extend the autosave-absent posture from Phase 3.9 to
the new modules; they do NOT modify any existing I-PERSIST row.

## 15. Catalog row status assignment

The corrigenda proposes the following status assignment, subject
to the Step 5 catalog patch plan:

### 15.1 Phase 3.10a — Operational Hardening (I-OPSHARDEN-*)

```text
REQUIRED (9 rows):
  /session-status is read-only and bounded
  /db-status is read-only mode=ro and bounded
  /db-verify reuses load_session and DROPS the candidate
  /db-verify failure preserves the live session
  /db-backup uses sqlite3.Connection.backup() (page-faithful)
  /db-backup refuses to overwrite without --force
  /db-backup refuses URI-scheme destinations
  /db-backup never modifies the source DB
  CLI short-circuit ordering and mutual exclusion + exit codes

STRUCTURAL (5 rows):
  source connection mode=ro during backup
  persistence_ops_static_audit (import set + no pickle / shelve /
    subprocess / curses / brain.tick / brain.tlica / brain.llm)
  persistence_ops_resource_audit (no new session fields; no
    sqlite3.Connection on session)
  exit-code mapping fixture
  Phase 3.10a defensive autosave-absent audit
```

### 15.2 Phase 3.10b — Persistence Observability (I-OBSERVE-*)

```text
REQUIRED (5 rows):
  /db-summary reads in mode=ro; closed `with` block; bounded report
  /profile-summary returns exact-Fraction "num/den" rows, COGITO
    first, deterministic sort
  /stream-db-summary returns bounded head + tail with text_preview
    cap STREAM_TEXT_PREVIEW_MAX_LEN = 64
  /db-diff reports finite field enumeration; "<missing>" on
    one-sided absence; never invents defaults
  observability commands never activate saved state and never
    mutate live BrainState

STRUCTURAL (5 rows):
  persistence_observe_no_builder_call (no make_* / no
    BrainState() / no OperatorSession() inside the module)
  persistence_observe_static_audit (import set; same forbidden
    set as ops + no builder imports)
  persistence_observe_resource_audit (no new session fields)
  locked default row caps (PROFILE_SUMMARY_ROW_CAP=64,
    STREAM_DB_SUMMARY_HEAD_CAP=8, STREAM_DB_SUMMARY_TAIL_CAP=8,
    DB_DIFF_ROW_CAP=32, STREAM_TEXT_PREVIEW_MAX_LEN=64,
    OPS_REPORT_TEXT_MAX_LEN=256)
  Phase 3.10b defensive autosave-absent audit
```

### 15.3 OBSERVED

```text
OBSERVED (1 row):
  Phase 3.10 ops/observability dry run
    (operator: /save-session, /db-status, /db-verify, /db-summary,
     /profile-summary, /db-diff, /db-backup, /quit; relaunch with
     --load-session against the backup; verify identity. Step 11
     audit cites this dry run.)
```

### 15.4 NOT-EXERCISED

```text
NOT-EXERCISED (0 rows):
  Autosave NOT-EXERCISED row is already in v0.17 (I-PERSIST family,
  Phase 3.9). The Phase 3.10a/b plan does NOT add a second
  autosave-NOT-EXERCISED row; the existing one continues to hold
  the place until Step 15/17 lands an explicit autosave row family.
```

### 15.5 Resulting count delta

```text
+14 REQUIRED   (9 ops + 5 observe)
+10 STRUCTURAL (5 ops + 5 observe)
+ 1 OBSERVED
+ 0 NOT-EXERCISED
+ 0 DEFERRED

v0.17 -> v0.18 (Phase 3.10a/b catalog patch):
  REQUIRED       = 187 + 14 = 201
  STRUCTURAL     =  69 + 10 =  79
  NOT-EXERCISED  =  10           (unchanged)
  DEFERRED       =  12           (unchanged)
  OBSERVED       =  13 +  1 =  14
```

The Step 5 plan is canonical; it may shift one or two rows between
REQUIRED and STRUCTURAL if a fixture turns out to cover two rows
naturally. Any change to this split must keep the delta totals
coherent with the next catalog banner.

Phase 3.10c (autosave) catalog patch (Step 15) is expected to add:

```text
+ ~10 REQUIRED  (autosave rules per kickoff section 4.3 sketch)
+ ~2 STRUCTURAL (autosave static audit; autosave resource audit)
+ 1 OBSERVED   (autosave dry run)
+ 0 NOT-EXERCISED (the existing one is promoted to REQUIRED at
                    Step 17)
```

These Phase 3.10c numbers are estimates only; they are pinned at
Step 15.

## 16. File budget audit

Kickoff proposal:

```text
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/render.py                    (optional)
brain/ui/fixtures/persistence_ops_*.py
brain/ui/fixtures/persistence_observe_*.py
brain/invariants.py
brain/_catalog_ids.py
INVARIANT_CATALOG.md
tools/catalog.py
README.md
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must NOT touch (Phase 3.10a/b):

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
brain/development/text_stream.py
brain/development/fixtures/text_stream_*.py
brain/ui/persistence.py             (except the narrow promotion
                                     of _snapshot_session described
                                     in Section 9)
brain/ui/autosave.py                  (Phase 3.10c only; Step 18)
```

## 17. Hard non-goals (restated)

The Phase 3.10a/b catalog plan must not authorize any of the
following in any row, fixture, or runtime path:

```text
- raw text -> COGITO_ID
- raw text -> BrainState direct mutation
- pickle / shelve / marshal / dill / cloudpickle / joblib as a
  format
- JSON / TOML / YAML as the authoritative kernel-state format
- REAL / NUMERIC / FLOAT / DOUBLE columns
- a sqlite3.Connection on OperatorSession
- autosave from any dispatch path
- network-backed persistence / observability
- multi-profile / multi-user persistence
- migrations between schema versions
- persistence of LLM client / cache / runtime mode
- persistence of operator transcripts beyond bounded session-local
  state
- persistence of curses configuration / terminal state
- modifications to tick() semantics
- new typed operator commands outside the eight Phase 3.10a/b
  verbs
- any save / export path outside the configured session DB and
  the explicit /db-backup destination
```

## 18. Stop point

Next artifact:

```text
PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md
```

The plan must:

```text
- bind the row family names (I-OPSHARDEN-* for 3.10a and
  I-OBSERVE-* for 3.10b);
- bind row statuses per Section 15;
- compute the exact count delta and the resulting v0.18 banner;
- pin the file budget per Section 16;
- pin the fixture roster;
- pin pending-registration mechanics
  (_PHASE3_10_OPS_PENDING_ROWS, _PHASE3_10_OBSERVE_PENDING_ROWS);
- restate the v0.18 review-gate stop condition.
```

Then the campaign must stop at the Step 6 review gate. No catalog
row, runtime module, fixture, or README change may land until the
Step 5 plan is explicitly accepted.

## Conclusion

The Phase 3.10 kickoff is coherent. The next artifact is:

```text
PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md
```

After that plan is committed and pushed, the campaign halts at the
Step 6 review gate.
