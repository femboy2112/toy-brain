# PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_KICKOFF.md

## Purpose

Define the Phase 3.10 build shape for tracks A (Operational Hardening)
and B (Persistence Observability) before any catalog or runtime
change. Sketch track C (Autosave Policy) without locking it — the
autosave kickoff (Step 13) refines this sketch after the Step 11
audit.

This is a planning artifact only. It does not edit
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, `brain/ui/persistence.py`, or any other
`brain/ui/` module.

Phase 3.10 closes the operability gap left by Phase 3.9:

```text
operator launches python3 -m brain.ui --session-db PATH --load-session
  -> the existing flow stays the same.

operator launches python3 -m brain.ui --session-db PATH --db-status
  -> bounded local report; no curses; exit.

operator launches python3 -m brain.ui --session-db PATH --db-verify
  -> bounded local report (PASS / FAIL); no curses; exit.

operator launches python3 -m brain.ui --session-db PATH --db-backup OUT
  -> bounded local report; no curses; exit.

operator types in TUI:
  /session-status        bounded local report on live OperatorSession.
  /db-status             bounded local report on the configured DB.
  /db-verify             reconstruct candidate, run invariants, DROP
                         candidate, report PASS / FAIL.
  /db-summary            bounded local read-only summary of the DB.
  /profile-summary       bounded local exact-Fraction profile listing.
  /stream-db-summary     bounded local saved stream summary.
  /db-diff               bounded local live-vs-saved diff (typed
                         snapshot shape; missing-on-one-side explicit).
  /db-backup PATH        bounded byte-faithful sqlite3 backup.

  /autosave-status       sketch only; locked in Step 13/15.
  /autosave-enable       sketch only; locked in Step 13/15.
  /autosave-disable      sketch only; locked in Step 13/15.
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
Prior artifact:  PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_SYNTHESIS.md
```

Existing surfaces this kickoff must consume (not modify outside the
documented extension points):

```text
brain.ui.persistence:
  PersistenceError
  SessionStoreConfig
  SCHEMA_VERSION_V1
  SUPPORTED_SCHEMA_VERSIONS
  CATALOG_VERSION_STAMP
  PersistentBrainStateSnapshot
  PersistentStreamChunkSnapshot
  PersistentStreamCandidateSnapshot
  PersistentSessionSnapshot
  SaveSessionResult
  LoadSessionResult
  schema_statements()
  save_session(session, config, *, now=None) -> SaveSessionResult
  load_session(config, *, rebuild_candidates_if_missing=True)
      -> tuple[OperatorSession, LoadSessionResult]
  internal helpers:
    _snapshot_brain_state, _snapshot_session,
    _create_schema, _read_meta_value, _write_meta_value,
    _serialize_to_db, _deserialize_from_db,
    _reconstruct_brain_state, _reconstruct_stream_history,
    _reconstruct_stream_candidates

brain.ui.session.OperatorSession (Phase 3.9 frozen-by-convention
  record with session_store_config: Optional[SessionStoreConfig]).
brain.ui.commands.OperatorCommand
  (existing kinds: INSPECT_*, QUEUE_PERCEPT, STEP_TICK, CLEAR_STATUS,
   HELP, QUIT, NOOP, STREAM_APPEND, STREAM_PROMOTE, SAVE_SESSION,
   LOAD_SESSION).
brain.ui.commands.Command / make_command.
brain.ui.command_line.LocalCommandLine.parse.
brain.ui.__main__.build_default_session,
  parse_session_db_args, configure_session_store, attempt_load.
brain.tick.BrainState / assert_state_invariants.
```

## 2. Module placement decision

Two candidate placements were called out in the synthesis. This
kickoff proposes:

```text
Option K-B (split): one thin module per track.

  brain/ui/persistence.py                  unchanged save/load core.
  brain/ui/persistence_ops.py              new (Phase 3.10a).
  brain/ui/persistence_observe.py          new (Phase 3.10b).
  brain/ui/autosave.py                     new (Phase 3.10c only;
                                              created at Step 18).
  brain/ui/fixtures/persistence_ops_*.py            new.
  brain/ui/fixtures/persistence_observe_*.py        new.
  brain/ui/fixtures/autosave_*.py                   new (Step 18).
```

Rationale:

```text
- Phase 3.10c is the policy-loaded track. Putting autosave in its
  own module keeps the Step 16 review gate a small, isolated diff
  and lets the static audit fixture target a single file.
- Phase 3.10a and 3.10b are different kinds of operation (a + b
  write; b reads). Keeping the read path (persistence_observe.py)
  separate from the write path (persistence_ops.py /db-backup)
  makes the static audit clearer: persistence_observe.py imports
  nothing that opens the DB for write, and the audit fixture
  enforces it.
- brain/ui/persistence.py stays a focused save/load core. The
  Phase 3.10 modules import it for typed records (PersistentBrainStateSnapshot
  etc.), the schema constants, and SessionStoreConfig.
- The existing _serialize_to_db / _deserialize_from_db helpers
  are reused via load_session for /db-verify; the new modules do
  not duplicate the deserialization code path.
```

The corrigenda (Step 4) is the canonical place to lock placement.
For the rest of this kickoff, file paths use the Option K-B layout.

## 3. Typed report records

All Phase 3.10 reports are frozen / slotted dataclasses with
deterministic, bounded printable shapes. Field types use stdlib + the
existing kernel types.

### 3.1 Phase 3.10a — Operational Hardening reports

```python
@dataclass(frozen=True, slots=True)
class SessionStatusReport:
    tick_counter: int
    queue_size: int
    active_view: str
    has_latest_tick: bool
    has_output_history: bool
    has_worldlet_history: bool
    has_repl_history: bool
    stream_chunk_count: int
    stream_candidate_count: int
    stream_chunk_serial: int
    session_db_configured: bool
    session_db_path_str: str    # "" iff not configured
    quit_flag: bool

@dataclass(frozen=True, slots=True)
class DbStatusReport:
    db_path_str: str
    db_exists: bool
    db_byte_size: int           # 0 iff missing
    db_modified_at: str         # ISO-8601; "" iff missing
    schema_version: int         # 0 iff missing or unreadable
    catalog_version: str        # "" iff missing or unreadable
    created_at: str             # "" iff missing
    updated_at: str             # "" iff missing
    error_text: str             # "" iff PASS; bounded printable
                                #   error message on failure

@dataclass(frozen=True, slots=True)
class DbVerifyReport:
    db_path_str: str
    passed: bool
    schema_version: int
    catalog_version: str
    loaded_chunks: int
    loaded_candidates: int
    rebuilt_candidates: bool
    error_text: str             # "" iff PASS; bounded local message

@dataclass(frozen=True, slots=True)
class DbBackupReport:
    source_path_str: str
    dest_path_str: str
    source_byte_size: int
    dest_byte_size: int          # 0 iff backup failed before write
    pages_copied: int            # 0 iff backup failed before copy
    total_pages: int             # 0 iff backup failed before copy
    succeeded: bool
    overwritten: bool            # true iff --force-replaced existing
    error_text: str              # "" iff succeeded
```

Construction rules:

```text
- All integer fields are non-negative.
- All path / version / timestamp / error strings are bounded printable
  (the corrigenda fixes the cap; recommended OPS_REPORT_TEXT_MAX_LEN
  = 256).
- error_text uses brain.ui.persistence's existing
  _require_bounded_text helper (lifted into a shared `_text_utils`
  module if the corrigenda accepts that refactor; otherwise inlined).
- Boolean fields are bool, not int.
- The reports are produced inside the persistence_ops helpers and
  surfaced as bounded local UI status / error messages by the
  dispatcher.
```

### 3.2 Phase 3.10b — Persistence Observability reports

```python
@dataclass(frozen=True, slots=True)
class DbSummaryReport:
    db_path_str: str
    schema_version: int
    catalog_version: str
    created_at: str
    updated_at: str
    profile_row_count: int
    msi_content_count: int
    msi_threshold: str            # exact "num/den"
    ptcns_eval_row_count: int
    registry_row_count: int
    stream_chunk_count: int
    stream_candidate_count: int
    tick_counter: int
    stream_chunk_serial: int
    error_text: str               # "" iff PASS

@dataclass(frozen=True, slots=True)
class ProfileSummaryRow:
    content_id: str
    value_str: str                # exact "num/den"

@dataclass(frozen=True, slots=True)
class ProfileSummaryReport:
    db_path_str: str
    rows: tuple[ProfileSummaryRow, ...]   # sorted by content_id,
                                          # COGITO_ID first
    truncated: bool                       # true iff row cap hit
    error_text: str

@dataclass(frozen=True, slots=True)
class StreamDbSummaryRow:
    ordinal: int
    chunk_id: str
    source: str
    tick_at_event: int
    provenance_tag: str
    text_preview: str            # bounded preview, never the full
                                 # chunk; cap declared in source

@dataclass(frozen=True, slots=True)
class StreamDbSummaryReport:
    db_path_str: str
    chunk_count: int
    candidate_count: int
    first_ordinal: int           # 0 iff empty
    last_ordinal: int            # 0 iff empty
    head: tuple[StreamDbSummaryRow, ...]   # bounded head slice
    tail: tuple[StreamDbSummaryRow, ...]   # bounded tail slice
    truncated: bool
    error_text: str

@dataclass(frozen=True, slots=True)
class DbDiffField:
    field: str                   # "profile.alpha", "msi.threshold",
                                 # "stream_history.count", etc.
    live: str                    # exact value or "<missing>"
    saved: str                   # exact value or "<missing>"

@dataclass(frozen=True, slots=True)
class DbDiffReport:
    db_path_str: str
    matches: bool
    diff_count: int
    differences: tuple[DbDiffField, ...]   # bounded; truncated flag
    truncated: bool
    error_text: str
```

Construction rules:

```text
- ProfileSummaryReport.rows is sorted deterministically by
  content_id with COGITO_ID first.
- text_preview uses the existing Phase 3.7 bounded-printable
  policy. The cap (recommended STREAM_TEXT_PREVIEW_MAX_LEN = 64)
  is declared as a module constant and a fixture asserts it.
- DbDiffField.field strings come from a finite enumeration of
  comparable fields declared at module load time. Unknown fields
  cannot appear.
- DbDiffField.live / .saved use exact-Fraction "num/den" strings
  for kernel numeric fields, integer text for counters, and the
  literal "<missing>" for one-sided absence. No float, no JSON,
  no repr().
- All reports have a finite row cap declared in source; the
  corrigenda fixes the numbers.
```

### 3.3 Phase 3.10c — Autosave reports (sketch; not locked)

```python
@dataclass(frozen=True, slots=True)
class AutosaveConfig:
    mode: AutosaveMode           # enum: OFF, AFTER_SUCCESSFUL_MUTATION
    db_path_str: str

@dataclass(frozen=True, slots=True)
class AutosaveStatusReport:
    mode: AutosaveMode
    db_path_str: str
    last_attempt_tick: int       # 0 iff never
    last_attempt_outcome: str    # "" / "ok" / "error"
    last_attempt_at: str         # ISO-8601; "" iff never
    last_error_text: str         # "" iff never failed
```

The Step 13 kickoff locks the enum members, the trigger set, the
report shape, and the exact wiring through dispatch.

## 4. Helper signatures

### 4.1 Phase 3.10a — persistence_ops.py

```python
def session_status(session: OperatorSession) -> SessionStatusReport:
    """Read live OperatorSession fields; no disk; no tick()."""

def db_status(config: SessionStoreConfig) -> DbStatusReport:
    """Open the configured DB in mode=ro, read meta, close."""

def db_verify(
    config: SessionStoreConfig,
    *,
    rebuild_candidates_if_missing: bool = True,
) -> DbVerifyReport:
    """Reconstruct a throwaway candidate through the same path as
    load_session, run assert_state_invariants on the candidate, drop
    the candidate, and return a bounded PASS / FAIL report. The
    candidate is never assigned to the live OperatorSession."""

def db_backup(
    config: SessionStoreConfig,
    dest_path: pathlib.Path,
    *,
    force: bool = False,
) -> DbBackupReport:
    """Copy the source DB to dest_path via the sqlite3 Backup API.
    Refuses to overwrite an existing dest unless force=True. Source
    is opened in mode=ro; dest is created in normal write mode.
    Returns a bounded report; raises PersistenceError on argument
    errors."""
```

Behavior contracts (driven by Step 5 catalog rows):

```text
- session_status reads from in-memory fields only; no IO.
- db_status / db_verify / db_backup open the DB in `with` blocks;
  no sqlite3.Connection escapes the helper.
- db_status / db_verify use mode=ro so the source DB is never
  written.
- db_verify reuses load_session (not a parallel deserializer) and
  immediately discards the returned candidate session.
- db_backup uses sqlite3.Connection.backup() (page-faithful).
  Source connection: mode=ro. Dest connection: writable. Both
  inside `with conn:` blocks.
- db_backup refuses dest_path.exists() unless force=True;
  refuses if dest_path == source_path; refuses if dest_path is a
  directory; refuses URI-like dest strings (sqlite://, file:, etc.).
- All four helpers raise PersistenceError on invalid arguments
  (TypeError-style) and return a report with error_text populated
  on operational failures.
```

### 4.2 Phase 3.10b — persistence_observe.py

```python
def db_summary(config: SessionStoreConfig) -> DbSummaryReport:
    """Read meta + per-table row counts in mode=ro."""

def profile_summary(
    config: SessionStoreConfig,
    *,
    row_cap: int = PROFILE_SUMMARY_ROW_CAP,
) -> ProfileSummaryReport:
    """Read profile_values in mode=ro, sort by content_id with
    COGITO_ID first, render Fraction values as exact 'num/den'
    strings, truncate at row_cap."""

def stream_db_summary(
    config: SessionStoreConfig,
    *,
    head_cap: int = STREAM_DB_SUMMARY_HEAD_CAP,
    tail_cap: int = STREAM_DB_SUMMARY_TAIL_CAP,
) -> StreamDbSummaryReport:
    """Read stream_chunks + stream_candidates row counts in mode=ro
    and emit a bounded head + tail slice. Text fields use the
    declared text_preview cap; no full-chunk text is rendered."""

def db_diff(
    session: OperatorSession,
    config: SessionStoreConfig,
    *,
    row_cap: int = DB_DIFF_ROW_CAP,
) -> DbDiffReport:
    """Snapshot the live OperatorSession to a typed
    PersistentSessionSnapshot, read the saved snapshot in mode=ro,
    diff over the finite field set declared in source, truncate
    at row_cap."""
```

Behavior contracts:

```text
- Every helper opens the DB inside a `with conn:` block; no
  sqlite3.Connection escapes.
- No helper calls any *_session builder. db_summary, profile_summary,
  and stream_db_summary read typed rows directly without
  reconstructing kernel state.
- db_diff calls _snapshot_session(session) on the live session
  (the existing private helper in brain.ui.persistence; the
  corrigenda may promote it to a public helper) and reads the
  saved snapshot through _deserialize_from_db without invoking
  builders.
- Fractions are rendered as exact "num/den" strings via a small
  shared helper (placed in brain.ui.persistence_observe or
  promoted to brain.ui.persistence). Never via float() or repr().
- Truncation is explicit: `truncated=True` and the operator-visible
  output names the row cap.
```

### 4.3 Phase 3.10c — autosave.py (sketch; locked at Step 13)

```python
class AutosaveMode(str, Enum):
    OFF = "off"
    AFTER_SUCCESSFUL_MUTATION = "after-successful-mutation"

def autosave_status(session: OperatorSession) -> AutosaveStatusReport: ...
def autosave_enable(session: OperatorSession,
                    mode: AutosaveMode) -> AutosaveStatusReport: ...
def autosave_disable(session: OperatorSession) -> AutosaveStatusReport: ...
def maybe_autosave_after_mutation(
    session: OperatorSession,
    *,
    triggered_by: AutosaveTrigger,
) -> Optional[AutosaveStatusReport]: ...
```

The Step 13/15 work locks the trigger enum, the dispatcher wiring,
and the fixture roster.

## 5. CLI flag set

Phase 3.10a adds two one-shot launch flags. Phase 3.10b adds none.
Phase 3.10c adds one mode flag (locked at Step 13).

```text
--db-status              Run db_status against the configured
                         --session-db and print a bounded report
                         to stdout, then exit. Requires
                         --session-db. Does not load curses.

--db-verify              Run db_verify against the configured
                         --session-db and print a bounded
                         PASS / FAIL report to stdout, then exit
                         with code 0 (PASS) or 1 (FAIL). Requires
                         --session-db. Does not load curses.

--db-backup PATH         Run db_backup with dest_path = PATH and
                         print a bounded report to stdout, then
                         exit with code 0 (success) or 1 (failure).
                         Requires --session-db. Refuses to overwrite
                         an existing PATH unless --db-backup-force
                         is also supplied. Does not load curses.

--db-backup-force        Permit --db-backup to overwrite an
                         existing destination file.

--autosave-mode <mode>   Sketch only; not implemented before
                         Step 18. Defaults to "off". The corrigenda
                         and Step 13 kickoff lock the accepted mode
                         strings.
```

Behavior rules:

```text
- --db-status, --db-verify, --db-backup are mutually exclusive at
  the parser level. Combining them raises a local argument error.
- --db-backup without PATH raises a local argument error.
- --db-backup PATH where PATH parses as a URI scheme (sqlite://,
  file:, http://, etc.) raises a local argument error.
- All three short-circuit before parse_llm_runtime_args and
  curses initialization. They emit a single bounded line to stdout
  and exit.
- --print-once and --check-terminal continue to short-circuit
  before these flags.
- --autosave-mode is parsed but, in Phase 3.10a/b work, only "off"
  is accepted. The corrigenda may instead defer the flag entirely
  to Step 18; the catalog plan must agree with the corrigenda.
```

Bounded launch log line additions:

```text
"brain.ui: db status = <pass/fail/missing> (schema=v1; chunks=N; candidates=M)"
"brain.ui: db verify = <pass/fail/skipped> (<bounded reason>)"
"brain.ui: db backup = <succeeded/failed> (pages=K/T; bytes=B)"
"brain.ui: autosave mode = off"   (default; locked here)
```

## 6. Typed commands

New OperatorCommand enum members:

```text
SESSION_STATUS         = "session_status"
DB_STATUS              = "db_status"
DB_VERIFY              = "db_verify"
DB_SUMMARY             = "db_summary"
PROFILE_SUMMARY        = "profile_summary"
STREAM_DB_SUMMARY      = "stream_db_summary"
DB_DIFF                = "db_diff"
DB_BACKUP              = "db_backup"
AUTOSAVE_STATUS        = "autosave_status"     # Step 18 wiring
AUTOSAVE_ENABLE        = "autosave_enable"     # Step 18 wiring
AUTOSAVE_DISABLE       = "autosave_disable"    # Step 18 wiring
```

Payloads:

```python
@dataclass(frozen=True, slots=True)
class DbBackupPayload:
    dest_path: pathlib.Path
    force: bool = False

@dataclass(frozen=True, slots=True)
class AutosaveEnablePayload:
    mode: AutosaveMode
```

All other Phase 3.10 commands take no payload (parallel to the
no-payload Phase 3.9 SAVE_SESSION / LOAD_SESSION shape).

Parser additions in LocalCommandLine.parse:

```text
/session-status                    no args; rejects trailing args.
/db-status                         no args; rejects trailing args.
/db-verify                         no args; rejects trailing args.
/db-summary                        no args; rejects trailing args.
/profile-summary                   no args; rejects trailing args.
/stream-db-summary                 no args; rejects trailing args.
/db-diff                           no args; rejects trailing args.
/db-backup <path> [--force]        path is required; --force is
                                   optional. The token "--force"
                                   maps to DbBackupPayload.force=True.
                                   No other flag is recognized.
/autosave-status                   no args (Step 18).
/autosave-enable <mode>            mode in AutosaveMode (Step 18).
/autosave-disable                  no args (Step 18).
```

Dispatcher additions (OperatorSession):

```text
_dispatch_session_status            calls session_status(self) and
                                    surfaces the bounded report
                                    through status_message.
_dispatch_db_status                 requires session_store_config;
                                    calls db_status(config);
                                    surfaces via status_message
                                    or error_message.
_dispatch_db_verify                 requires session_store_config;
                                    calls db_verify(config); surfaces
                                    a bounded PASS / FAIL line.
_dispatch_db_summary                requires session_store_config;
                                    calls db_summary(config);
                                    surfaces a bounded summary line.
_dispatch_profile_summary           requires session_store_config;
                                    calls profile_summary(config);
                                    surfaces a bounded listing.
_dispatch_stream_db_summary         requires session_store_config;
                                    calls stream_db_summary(config);
                                    surfaces head + tail line.
_dispatch_db_diff                   requires session_store_config;
                                    calls db_diff(self, config);
                                    surfaces bounded diff line(s).
_dispatch_db_backup                 requires session_store_config;
                                    parses payload.dest_path /
                                    payload.force; calls db_backup;
                                    surfaces bounded report.
_dispatch_autosave_status           Step 18 wiring.
_dispatch_autosave_enable           Step 18 wiring.
_dispatch_autosave_disable          Step 18 wiring.
```

Dispatch rules (all driven by catalog rows):

```text
- No dispatcher calls tick().
- No dispatcher reads from a live sqlite3.Connection on the session.
- /session-status executes even when session_store_config is None
  (the report flag session_db_configured carries the answer).
- All other persistence-adjacent commands require session_store_config
  and surface a bounded error_message ("no session DB configured")
  otherwise.
- Each dispatcher catches PersistenceError and surfaces a bounded
  error_message; no exception propagates into the curses wrapper.
```

## 7. Session attachment

Phase 3.10 adds at most these new fields to OperatorSession:

```text
autosave_config: Optional[AutosaveConfig] = None  (Step 18 only)
last_autosave_status: Optional[AutosaveStatusReport] = None
                                                  (Step 18 only)
```

It does NOT add:

```text
- sqlite3.Connection (forbidden -- not resource-free)
- a "last db status" / "last db summary" cache (every command
  re-reads from disk; staleness is the point)
- a background thread / signal handler / atexit / asyncio loop
- a callable trigger map (autosave triggers are static enum members)
```

Phase 3.10a and 3.10b add **no** new session fields. All status /
verify / summary / diff / backup output flows through the existing
status_message / error_message pipeline.

## 8. Likely file budget

For Step 8 (status + verify core), Step 9 (summaries + diff), and
Step 10 (backup):

```text
brain/ui/persistence_ops.py                       new
brain/ui/persistence_observe.py                   new
brain/ui/__main__.py                              extend (new flags +
                                                    short-circuit
                                                    branches)
brain/ui/commands.py                              extend (new enum
                                                    members + payloads
                                                    + helper updates)
brain/ui/command_line.py                          extend (new parser
                                                    verbs)
brain/ui/session.py                               extend (new dispatch
                                                    handlers; no new
                                                    fields in 3.10a/b)
brain/ui/render.py                                optional (status
                                                    display)
brain/ui/fixtures/persistence_ops_session_status.py    new
brain/ui/fixtures/persistence_ops_db_status.py          new
brain/ui/fixtures/persistence_ops_db_verify.py          new
brain/ui/fixtures/persistence_ops_db_verify_drop.py     new
brain/ui/fixtures/persistence_ops_db_backup.py          new
brain/ui/fixtures/persistence_ops_db_backup_force.py    new
brain/ui/fixtures/persistence_ops_db_backup_dest_uri.py new
brain/ui/fixtures/persistence_ops_resource_audit.py     new
brain/ui/fixtures/persistence_ops_static_audit.py       new
brain/ui/fixtures/persistence_observe_db_summary.py     new
brain/ui/fixtures/persistence_observe_profile_summary.py new
brain/ui/fixtures/persistence_observe_stream_db_summary.py new
brain/ui/fixtures/persistence_observe_db_diff.py        new
brain/ui/fixtures/persistence_observe_no_builder_call.py new
brain/ui/fixtures/persistence_observe_resource_audit.py new
brain/ui/fixtures/persistence_observe_static_audit.py   new
brain/invariants.py                               extend
  (_PHASE3_10_OPS_PENDING_ROWS,
   _PHASE3_10_OBSERVE_PENDING_ROWS,
   FIXTURE_MODULES additions)
brain/_catalog_ids.py                             regenerated
INVARIANT_CATALOG.md                              extend (Step 7)
tools/catalog.py                                  bump EXPECTED_COUNTS
                                                  + banner (Step 7)
README.md                                         document new commands
                                                  after Step 10
```

For Step 18 (autosave; gated):

```text
brain/ui/autosave.py                              new
brain/ui/__main__.py                              extend (--autosave-mode
                                                    parsing)
brain/ui/commands.py                              extend
  (AUTOSAVE_*, AutosaveEnablePayload)
brain/ui/command_line.py                          extend
brain/ui/session.py                               extend
  (autosave_config, last_autosave_status fields;
   dispatch handlers; maybe_autosave_after_mutation call sites)
brain/ui/fixtures/autosave_default_off.py         new
brain/ui/fixtures/autosave_requires_db.py         new
brain/ui/fixtures/autosave_trigger_set.py         new
brain/ui/fixtures/autosave_no_tick_call.py        new
brain/ui/fixtures/autosave_no_after_read_only.py  new
brain/ui/fixtures/autosave_no_after_failure.py    new
brain/ui/fixtures/autosave_failure_preserves.py   new
brain/ui/fixtures/autosave_no_background.py       new
brain/ui/fixtures/autosave_single_save_path.py    new
brain/ui/fixtures/autosave_status_after_event.py  new
brain/ui/fixtures/autosave_static_audit.py        new
```

Excluded unless a later accepted plan reopens them:

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
brain/ui/persistence.py                  (Phase 3.9 core stays as is;
                                          new helpers may need it to
                                          publish a public _snapshot
                                          accessor — corrigenda
                                          decides if that small
                                          extension is allowed.)
```

## 9. Fixture roster sketch

The Step 5 catalog patch plan binds exact row IDs. The likely
fixtures (Phase 3.10a + 3.10b):

```text
persistence_ops_session_status.py
  - session_status produces a bounded report on a default session;
    Fractions are not displayed (this command returns counts /
    flags only); no disk access occurs.

persistence_ops_db_status.py
  - db_status on a missing DB returns db_exists=False and an
    empty schema_version; no IOError propagates.
  - db_status on a freshly saved DB returns schema_version=1,
    catalog_version="v0.17", and non-empty timestamps.

persistence_ops_db_verify.py
  - db_verify on a freshly saved DB returns passed=True with
    accurate chunk / candidate counts.
  - db_verify on a DB with a tampered profile_values row (rho_den=0)
    returns passed=False with bounded error_text.

persistence_ops_db_verify_drop.py
  - The candidate returned internally by load_session inside
    db_verify is not assigned anywhere on the live session; the
    live OperatorSession's id() is unchanged after db_verify.

persistence_ops_db_backup.py
  - db_backup copies the source DB byte-faithfully; load_session
    succeeds against the backup file with identical
    PersistentSessionSnapshot content.
  - Source and dest are different files; both connections closed
    after the call.

persistence_ops_db_backup_force.py
  - db_backup refuses to overwrite an existing dest by default.
  - db_backup with force=True overwrites and reports overwritten=True.

persistence_ops_db_backup_dest_uri.py
  - db_backup rejects dest_path strings that parse as URIs
    (sqlite://, file:, http://, https://, ftp://).

persistence_ops_resource_audit.py
  - After /session-status, /db-status, /db-verify, /db-backup,
    OperatorSession holds no sqlite3.Connection in any field.

persistence_ops_static_audit.py
  - brain/ui/persistence_ops.py imports are confined to the
    documented set (sqlite3, dataclasses, fractions, datetime,
    pathlib, typing, brain.ui.persistence, brain.ui.session;
    no pickle / shelve / marshal / eval / exec / compile /
    subprocess / socket / urllib / http / requests / curses /
    brain.tick / brain.tlica internals / brain.llm).

persistence_observe_db_summary.py
  - db_summary on a default-session DB reports the expected
    counts: profile_row_count=2, msi_content_count=2,
    msi_threshold="1/2", registry_row_count=1,
    ptcns_eval_row_count=2, stream_chunk_count=0,
    stream_candidate_count=0.

persistence_observe_profile_summary.py
  - profile_summary returns rows in COGITO_ID-first sort order
    with exact "num/den" strings; no float, no repr.
  - row_cap truncates and sets truncated=True.

persistence_observe_stream_db_summary.py
  - stream_db_summary on a DB with N chunks returns head and tail
    slices bounded by the declared head_cap / tail_cap.
  - text_preview is bounded by STREAM_TEXT_PREVIEW_MAX_LEN; full
    chunk text is never returned.

persistence_observe_db_diff.py
  - On a freshly saved DB matching the live session, db_diff
    reports matches=True with diff_count=0.
  - When the live session adds a profile content_id absent from
    the saved DB, db_diff reports the difference with
    live="<num>/<den>" and saved="<missing>".

persistence_observe_no_builder_call.py
  - Static AST check that persistence_observe.py does not call any
    make_profile_with_cogito / make_msi / make_ptcns /
    make_text_stream_chunk / make_stream_promotion_candidate /
    ContentRegistry / BrainState / OperatorSession constructor.

persistence_observe_resource_audit.py
  - After /db-summary, /profile-summary, /stream-db-summary,
    /db-diff, OperatorSession holds no sqlite3.Connection in any
    field.

persistence_observe_static_audit.py
  - brain/ui/persistence_observe.py imports are confined to the
    documented set; mirrors persistence_ops_static_audit.
```

OBSERVED rows (Step 11 audit):

```text
- A bounded operability dry run (operator opens a session, runs
  /step, runs /save-session, then /db-status, /db-verify,
  /db-summary, /profile-summary, /db-diff, /db-backup, /quit;
  relaunches with --load-session against the backup file and
  verifies the loaded session matches) is OBSERVED.
- The fixture either runs a deterministic stand-in or cites the
  audit. This is parallel to the Phase 3.9 cold-start dry run.
```

For Step 18 (autosave; Phase 3.10c):

```text
autosave_default_off.py
  - On every cold start, regardless of prior autosave_config,
    AutosaveMode is OFF.

autosave_requires_db.py
  - /autosave-enable without --session-db raises a bounded local
    error and leaves the live session unchanged.

autosave_trigger_set.py
  - The trigger enum is finite and matches the value declared in
    the catalog row.

autosave_no_tick_call.py
  - Triggering autosave during dispatch does NOT route through
    tick(); the call site is post-dispatch.

autosave_no_after_read_only.py
  - /db-status, /db-summary, /profile-summary, /db-diff,
    /db-backup, /session-status, /db-verify, /tick, /state,
    /output, /worldlet, /repl, /stream-summary,
    /stream-candidates, /help, /clear, /quit do NOT trigger
    autosave.

autosave_no_after_failure.py
  - A failed /step or failed /stream-promote does NOT trigger
    autosave.

autosave_failure_preserves.py
  - Simulated IntegrityError during autosave -> ROLLBACK; live
    session preserved; AutosaveStatusReport.last_attempt_outcome
    = "error".

autosave_no_background.py
  - No thread, no signal handler, no atexit, no asyncio loop
    triggers autosave.

autosave_single_save_path.py
  - Autosave invokes save_session through the same code path as
    /save-session. No second save helper exists.

autosave_status_after_event.py
  - After a successful /step that triggered autosave,
    last_autosave_status reflects the new timestamp + outcome=ok.

autosave_static_audit.py
  - brain/ui/autosave.py imports are confined to the documented
    set.
```

## 10. Failure isolation contract

Phase 3.10 reuses the Phase 3.9 envelope. Every Phase 3.10 helper:

```text
- raises PersistenceError on invalid argument or unrecoverable
  precondition failure;
- returns a typed report with error_text populated on operational
  failure (corrupt DB, missing meta row, sqlite IntegrityError,
  etc.);
- never partially mutates the live OperatorSession;
- never partially writes the source DB except in the explicit
  /db-backup destination path;
- closes every sqlite3.Connection inside a `with conn:` block;
- runs inside a try / except in the dispatcher so no exception
  reaches the curses wrapper.
```

## 11. Phase 3.10c (autosave) separation

Phase 3.10a + 3.10b must NOT introduce:

```text
- any code path that invokes save_session outside the existing
  /save-session dispatch;
- any timer / thread / signal handler / atexit / asyncio loop;
- a "convenience" autosave call inside _dispatch_step_tick,
  _dispatch_stream_promote, _dispatch_load_session, or any other
  dispatch handler;
- a callable / hook / observer / event-bus subscription that
  reaches save_session;
- a flag that flips autosave on at startup.
```

The Step 5 ops/observability catalog patch plan must include a
defensive row that asserts the autosave entry point is absent before
Step 17 lands.

## 12. Stop point

Next artifact:

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md
```

The corrigenda should audit this kickoff for:

```text
- module placement (Option K-A vs K-B);
- typed report shapes (every field bounded; no float; no repr;
  no raw bytes);
- helper signatures (positional vs keyword; defaults; required
  vs optional args);
- exact CLI flag shapes (--db-status, --db-verify, --db-backup,
  --db-backup-force; mutual exclusion; URI rejection);
- closed parser verb additions (/session-status, /db-status,
  /db-verify, /db-summary, /profile-summary, /stream-db-summary,
  /db-diff, /db-backup);
- closed OperatorCommand additions;
- dispatch handler placement (single module vs split);
- whether _snapshot_session may be promoted to a public helper;
- whether ProfileSummaryReport row_cap, STREAM_DB_SUMMARY head /
  tail caps, DbDiffReport row_cap are the right defaults;
- whether STREAM_TEXT_PREVIEW_MAX_LEN should be 64, 128, 256;
- whether db_backup uses sqlite3 Backup API or audited shutil;
- whether --db-backup-force is the right name;
- whether autosave_config and last_autosave_status are the right
  session attachments for Step 18;
- which Phase 3.10a/b rows should be REQUIRED / STRUCTURAL /
  OBSERVED / NOT-EXERCISED in the catalog patch plan;
- which Phase 3.10c rows should be flagged as not yet authored
  (deferred to Step 15).
```

After the corrigenda, the catalog patch plan (Step 5) binds rows
and stops at the Step 6 review gate before any catalog or runtime
implementation begins. The autosave kickoff (Step 13) and autosave
catalog patch plan (Step 15) follow only after the Step 11
ops/observability audit is PASS.
