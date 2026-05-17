# PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md

## Purpose

Define the Phase 3.9 Persistent Session Store build shape before any
catalog or runtime change. This is a planning artifact only. It does
not edit `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `brain/invariants.py`, any `brain/ui/`
module, or any `brain/persistence/` module (the latter does not yet
exist).

Phase 3.9 closes the cold-start gap left by Phase 3.7 / 3.8 / 3.8b:

```text
operator launches python3 -m brain.ui --session-db ... --load-session
  -> existing DB?       load through public builders, run invariants,
                         replace live session only if all checks pass
  -> missing DB?        log a bounded local status; continue with
                         build_default_session()
operator types in TUI
  -> /save-session       transactional SQLite write of the current
                         session through typed snapshot records;
                         live session preserved on failure
operator quits, relaunches with same DB and --load-session
  -> restored BrainState / profile / MSI / PtCns / registry /
     tick_counter / stream_history / stream_chunk_serial /
     stream_candidates (restored or deterministically rebuilt)
```

## 1. Baseline

```text
Catalog version:  v0.16
REQUIRED:         178
STRUCTURAL:        64
NOT-EXERCISED:      9
DEFERRED:          12
OBSERVED:          12
Total fixtures:    91
Prior artifact:   PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md
```

Existing surfaces this kickoff must consume (not modify):

```text
brain.tick.BrainState              (frozen state record)
brain.io_types.ContentRegistry     (frozen registry)
brain.io_types.TickRecord          (frozen tick record)
brain.tlica.profile.ScalarProfile  (frozen profile)
brain.tlica.profile.COGITO_ID      (reserved sentinel)
brain.tlica.msi.MSI                (frozen MSI)
brain.tlica.ptcns.PtCns            (frozen PtCns)
brain.tlica.ptcns.ConsistencyEval  (closed enum)
brain.tlica.builders.make_profile_with_cogito
brain.tlica.builders.make_msi
brain.tlica.builders.make_ptcns
brain.development.text_stream.TextStreamSource
brain.development.text_stream.TextStreamChunk
brain.development.text_stream.TextStreamHistory
brain.development.text_stream.StreamPromotionCandidate
brain.development.text_stream.make_text_stream_chunk
brain.development.text_stream.make_stream_promotion_candidate
brain.ui.session.OperatorSession
brain.ui.session.OperatorEventQueue
brain.ui.commands.OperatorCommand
brain.ui.commands.Command
brain.ui.commands.make_command
brain.ui.command_line.LocalCommandLine
brain.ui.__main__.build_default_session
```

## 2. Module placement decision

Two candidate placements were called out in the synthesis. This
kickoff proposes:

```text
brain/ui/persistence.py
brain/ui/fixtures/persistence_*.py
```

Rationale:

```text
- The data being saved is exactly the OperatorSession + BrainState
  pair. Both are already UI-adjacent: OperatorSession lives in
  brain/ui/session.py.
- The entry points -- /save-session and /load-session typed commands
  plus --session-db / --load-session / --no-load-session CLI flags --
  are operator-facing. Putting the helper next to its callers keeps
  the import graph local.
- Phase 3.7 / 3.8 / 3.8b established a precedent: session-local
  machinery (text stream, stream promotion, LLM runtime toggle) lives
  in brain/ui/ with bounded fixtures in brain/ui/fixtures/. Phase 3.9
  follows the same pattern.
- A future, larger persistence subsystem (multi-profile, network,
  replication, autosave) can graduate into brain/persistence/ when a
  later campaign justifies it. The corrigenda may overrule this and
  prefer brain/persistence/session_store.py instead.
```

The corrigenda (Step 4) is the canonical place to lock placement.
For the rest of this kickoff, file paths use the
`brain/ui/persistence.py` placement.

## 3. Typed records

The persistence module exposes the following frozen / slotted
dataclasses. Field types use stdlib + the existing kernel types
already imported above.

### 3.1 SessionStoreConfig

```python
@dataclass(frozen=True, slots=True)
class SessionStoreConfig:
    db_path: pathlib.Path
    schema_version: int = SCHEMA_VERSION_V1
    catalog_version: str = "v0.16"
```

Rules:

```text
- db_path is a pathlib.Path; non-Path inputs raise TypeError.
- The Path must be a regular file or non-existent. A directory raises.
- schema_version is a positive int; only SCHEMA_VERSION_V1 is
  accepted by v0.16.
- catalog_version is a bounded ASCII string.
```

### 3.2 SessionStoreSchemaVersion

```python
SCHEMA_VERSION_V1: int = 1
SUPPORTED_SCHEMA_VERSIONS: frozenset[int] = frozenset({SCHEMA_VERSION_V1})
```

Loads with `schema_version not in SUPPORTED_SCHEMA_VERSIONS` raise
`PersistenceError`.

### 3.3 Persistent snapshot records

```python
@dataclass(frozen=True, slots=True)
class PersistentBrainStateSnapshot:
    profile_values: tuple[tuple[str, int, int], ...]
        # (content_id, rho_num, rho_den) ; sorted by content_id
    msi_contents: tuple[str, ...]
        # sorted content_ids in MSI
    msi_threshold_num: int
    msi_threshold_den: int
    ptcns_eval: tuple[tuple[str, str], ...]
        # (content_id, ConsistencyEval.name)
    registry_texts: tuple[tuple[str, str], ...]
        # (content_id, text)


@dataclass(frozen=True, slots=True)
class PersistentStreamChunkSnapshot:
    ordinal: int          # insertion order (1-based)
    chunk_id: str         # TextStreamChunk.chunk_id
    source: str           # TextStreamSource.name
    text: str             # bounded printable text
    tick_at_event: int    # TextStreamChunk.tick_at_event
    provenance_tag: str   # TextStreamChunk.provenance


@dataclass(frozen=True, slots=True)
class PersistentStreamCandidateSnapshot:
    ordinal: int
    candidate_id: str
    target_content_id: str
    chunk_id: str
    pattern_id: Optional[str]
    source: str
    text: str
    provenance_tag: str


@dataclass(frozen=True, slots=True)
class PersistentSessionSnapshot:
    schema_version: int
    catalog_version: str
    created_at: str       # ISO-8601 string
    updated_at: str       # ISO-8601 string
    brain_state: PersistentBrainStateSnapshot
    tick_counter: int
    stream_chunk_serial: int
    stream_chunks: tuple[PersistentStreamChunkSnapshot, ...]
    stream_candidates: tuple[PersistentStreamCandidateSnapshot, ...]
```

Construction rules:

```text
- All fields are immutable values (int, str, Optional[str], tuples
  of frozen records).
- Every constructor validates type and bound and raises ValueError
  on violation; constructors never silently coerce.
- text fields use the same bounded-printable policy as Phase 3.7
  TextStreamChunk (STREAM_TEXT_MAX_LEN = 1024).
- content_id / chunk_id / candidate_id strings use the existing
  Phase 3.7 require_printable_id helper.
- provenance_tag fields are bounded by STREAM_PROVENANCE_MAX_LEN = 64.
- registry_texts entries are bounded by an explicit cap (corrigenda
  decides; recommended >= STREAM_TEXT_MAX_LEN so existing kernel
  registry texts always fit).
- catalog_version is bounded ASCII.
```

### 3.4 Result and error records

```python
@dataclass(frozen=True, slots=True)
class SaveSessionResult:
    db_path: pathlib.Path
    schema_version: int
    catalog_version: str
    updated_at: str
    saved_chunks: int
    saved_candidates: int


@dataclass(frozen=True, slots=True)
class LoadSessionResult:
    db_path: pathlib.Path
    schema_version: int
    catalog_version: str
    loaded_chunks: int
    loaded_candidates: int
    rebuilt_candidates: bool  # True iff candidates were not stored
                              # and were rebuilt deterministically


class PersistenceError(Exception):
    """Bounded local error raised by save / load helpers."""
```

Rules:

```text
- SaveSessionResult / LoadSessionResult are returned on success.
- PersistenceError is raised on any failure: schema mismatch,
  constructor rejection, integrity error, IO error, etc.
- PersistenceError carries a bounded printable message that callers
  may surface as a UI status / error string.
- Failure paths must never partially mutate either the live
  OperatorSession or the SQLite database.
```

## 4. SQLite schema

`SCHEMA_VERSION_V1` = 1. The schema is finite and closed:

```sql
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- meta rows used by v1:
--   schema_version       (TEXT representation of an integer)
--   catalog_version      (e.g. "v0.16")
--   created_at           (ISO-8601 timestamp)
--   updated_at           (ISO-8601 timestamp)

CREATE TABLE IF NOT EXISTS content_registry (
    content_id TEXT PRIMARY KEY,
    text       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_values (
    content_id TEXT PRIMARY KEY,
    rho_num    INTEGER NOT NULL,
    rho_den    INTEGER NOT NULL CHECK (rho_den > 0)
);

CREATE TABLE IF NOT EXISTS msi_contents (
    content_id TEXT PRIMARY KEY,
    FOREIGN KEY (content_id) REFERENCES profile_values(content_id)
);

CREATE TABLE IF NOT EXISTS msi_threshold (
    id        INTEGER PRIMARY KEY CHECK (id = 1),
    num       INTEGER NOT NULL,
    den       INTEGER NOT NULL CHECK (den > 0)
);

CREATE TABLE IF NOT EXISTS ptcns_eval (
    content_id TEXT PRIMARY KEY,
    eval       TEXT NOT NULL,
    FOREIGN KEY (content_id) REFERENCES profile_values(content_id)
);

CREATE TABLE IF NOT EXISTS session_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- session_state rows used by v1:
--   tick_counter         (integer text)
--   stream_chunk_serial  (integer text)

CREATE TABLE IF NOT EXISTS stream_chunks (
    ordinal       INTEGER PRIMARY KEY,
    chunk_id      TEXT NOT NULL UNIQUE,
    source        TEXT NOT NULL,
    text          TEXT NOT NULL,
    tick_at_event INTEGER NOT NULL,
    provenance_tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stream_candidates (
    ordinal           INTEGER PRIMARY KEY,
    candidate_id      TEXT NOT NULL UNIQUE,
    target_content_id TEXT NOT NULL,
    chunk_id          TEXT NOT NULL,
    pattern_id        TEXT,
    source            TEXT NOT NULL,
    text              TEXT NOT NULL,
    provenance_tag    TEXT NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES stream_chunks(chunk_id)
);
```

Schema rules:

```text
- No table stores executable code, callable names, import paths,
  shell commands, pickle blobs, or arbitrary Python object repr as
  authoritative state.
- No column uses REAL for kernel numeric state. rho / threshold are
  stored as integer numerator / denominator pairs.
- No column is BLOB. All persisted text is TEXT and bounded by the
  existing Phase 3.7 / kernel bounds.
- Foreign keys are enabled with PRAGMA foreign_keys = ON at every
  connect.
- The schema is created idempotently with CREATE TABLE IF NOT
  EXISTS and a single transactional bootstrap on first save.
- A schema_version meta row is INSERTed on first save. Subsequent
  saves UPDATE updated_at.
- The corrigenda may rename columns or add CHECK constraints
  before locking the schema.
```

Optional later (not Phase 3.9 v1):

```text
CREATE TABLE IF NOT EXISTS persistence_events (
    event_id   INTEGER PRIMARY KEY,
    event_kind TEXT NOT NULL,
    created_at TEXT NOT NULL,
    detail     TEXT NOT NULL
);
```

The persistence_events table is sketched in the campaign body but
deferred until an autosave / journaling policy exists.

## 5. Save helper signature

```python
def save_session(
    session: OperatorSession,
    config: SessionStoreConfig,
    *,
    now: Optional[datetime.datetime] = None,
) -> SaveSessionResult:
    """Transactionally save `session` to `config.db_path`."""
```

Behavior:

```text
1. Validate config; raise PersistenceError on invalid config.
2. Open sqlite3.connect(config.db_path, isolation_level=None,
   uri=False) in a with block so the connection closes deterministically.
3. PRAGMA foreign_keys = ON.
4. BEGIN IMMEDIATE.
5. CREATE TABLE IF NOT EXISTS for every v1 table (idempotent).
6. UPSERT meta rows: schema_version, catalog_version, created_at
   (only if missing), updated_at.
7. DELETE FROM content_registry, profile_values, msi_contents,
   msi_threshold, ptcns_eval, session_state, stream_chunks,
   stream_candidates.
8. INSERT one row per profile content with rho_num + rho_den.
9. INSERT one row per MSI content; UPSERT the single
   msi_threshold row (id=1) with num/den.
10. INSERT one row per ptcns_eval entry with eval = enum.name.
11. INSERT one row per registry text.
12. INSERT session_state rows: tick_counter, stream_chunk_serial.
13. INSERT stream_chunks rows in TextStreamHistory order.
14. INSERT stream_candidates rows in current candidate order.
15. COMMIT.
16. Return SaveSessionResult.
```

Failure paths:

```text
- Any constructor / validation error before opening the DB raises
  PersistenceError without touching the file.
- Any sqlite3.IntegrityError / OperationalError / DatabaseError
  during the transaction triggers ROLLBACK and re-raises as
  PersistenceError. The DB file may exist but reverts to the
  pre-call state.
- The live OperatorSession is never mutated by save_session.
```

## 6. Load helper signature

```python
def load_session(
    config: SessionStoreConfig,
    *,
    rebuild_candidates_if_missing: bool = True,
) -> tuple[OperatorSession, LoadSessionResult]:
    """Read `config.db_path` and reconstruct an OperatorSession."""
```

Behavior:

```text
1. Validate config; raise PersistenceError on invalid config.
2. Open sqlite3.connect("file:<db_path>?mode=ro", uri=True) so
   load cannot create or write the DB.
3. PRAGMA foreign_keys = ON.
4. Read meta rows: schema_version, catalog_version, created_at,
   updated_at.
5. Reject unknown schema_version locally as PersistenceError.
6. Read profile_values, msi_contents, msi_threshold, ptcns_eval,
   content_registry rows.
7. Read session_state rows: tick_counter, stream_chunk_serial.
8. Read stream_chunks rows in ordinal order.
9. Read stream_candidates rows in ordinal order.
10. Build Persistent*Snapshot records (constructors validate
    types, bounds, printability).
11. Reconstruct kernel state through public builders:
      profile  = make_profile_with_cogito(
                    {row.content_id: Fraction(row.num, row.den)
                     for row in profile_rows})
      msi      = make_msi(profile,
                          contents=set(msi_content_ids),
                          threshold=Fraction(msi_threshold_num,
                                             msi_threshold_den))
      ptcns    = make_ptcns(msi,
                            eval_map={cid: ConsistencyEval[name]
                                      for cid, name in eval_rows})
      registry = ContentRegistry(
                    texts=MappingProxyType(
                        {cid: text for cid, text in registry_rows}))
      state    = BrainState(profile=profile, msi=msi, ptcns=ptcns,
                            registry=registry)
12. Reconstruct stream_history via make_text_stream_chunk on each
    PersistentStreamChunkSnapshot, then TextStreamHistory(chunks=...).
13. Reconstruct stream_candidates:
      if stream_candidate rows exist:
          rebuild StreamPromotionCandidate values through
          make_stream_promotion_candidate, sorted by ordinal;
          rebuilt_candidates = False.
      else if rebuild_candidates_if_missing:
          recompute promotion candidates deterministically from
          the restored TextStreamHistory using the existing
          Phase 3.7 helpers; rebuilt_candidates = True.
      else:
          stream_candidates = ();
          rebuilt_candidates = False.
14. Construct the candidate OperatorSession through its existing
    constructor (no field bypass).
15. Run brain.validation.assert_state_invariants(state) (or the
    Phase 1 / 2 equivalent) before returning. If assertion raises,
    raise PersistenceError without returning a candidate session.
16. Return (candidate_session, LoadSessionResult).
```

Failure paths:

```text
- DB does not exist: PersistenceError ("no session DB at <path>").
- DB is not a regular file: PersistenceError.
- meta rows missing or malformed: PersistenceError.
- schema_version not in SUPPORTED_SCHEMA_VERSIONS: PersistenceError.
- any builder raises: PersistenceError wrapping the underlying
  ValueError / TypeError; live session preserved.
- assert_state_invariants raises: PersistenceError; live session
  preserved.
- The candidate session is the load helper's return value, not a
  live mutation. The caller (UI dispatch) is responsible for
  swapping it into the live session only if load_session returned
  successfully.
```

## 7. CLI flag set

```text
--session-db PATH        Path to the session database file. If
                         omitted, persistence commands and
                         --load-session are unavailable. The flag
                         is bounded; no shell expansion beyond the
                         OS-level argv handling.

--load-session           After argument parsing and LLM-runtime
                         resolution, attempt to load the session
                         from --session-db before launching the
                         curses wrapper. On success, replace
                         build_default_session(). On failure, log
                         a bounded informational message to stdout
                         and fall back to build_default_session().

--no-load-session        Explicit opposite. Useful when the
                         operator wants the DB present but does not
                         want to load it on this launch. Default
                         when --session-db is supplied without
                         --load-session.
```

Behavior rules:

```text
- --print-once and --check-terminal continue to short-circuit
  before any persistence call. They do not open the DB.
- The LLM-runtime resolution path (parse_llm_runtime_args /
  build_llm_client_from_config) is independent of persistence.
- If --load-session is supplied without --session-db, the
  argument parser raises a local error before any IO.
- A bounded local launch log line announces the persistence mode:
    "brain.ui: session db = <path> (<status>)"
  where <status> is one of:
    "not configured"
    "load skipped"
    "loaded (schema=v1; catalog=v0.16; chunks=N; candidates=M)"
    "load failed: <bounded reason> (using default session)"
```

## 8. Typed commands

```text
OperatorCommand.SAVE_SESSION
OperatorCommand.LOAD_SESSION

@dataclass(frozen=True, slots=True)
class SaveSessionPayload:
    pass    # no operator-supplied arguments in v1

@dataclass(frozen=True, slots=True)
class LoadSessionPayload:
    pass    # no operator-supplied arguments in v1
```

Parser:

```text
- LocalCommandLine.parse accepts /save-session and /load-session as
  closed verbs.
- Trailing arguments to either verb are rejected as
  LocalCommandError ("'/save-session' takes no arguments").
- Both commands require the session to have an attached
  SessionStoreConfig (set at session construction time from the
  CLI flag). Without one, the dispatcher surfaces a bounded local
  status error.
```

Dispatcher:

```text
- /save-session calls save_session(session, config); on success,
  status_message reports the bounded result. On failure, the
  PersistenceError message is surfaced as error_message. The live
  session is unchanged.
- /load-session calls load_session(config); on success, the
  candidate session replaces the live session through a controlled
  swap routine (see Section 9). On failure, error_message reports
  the bounded reason; the live session is unchanged.
- Neither command calls tick(). /step remains the only tick route.
```

## 9. Swap routine

```text
- The UI dispatcher owns the swap. It receives the candidate
  OperatorSession returned by load_session and either:
    a) returns the candidate from its router so the curses wrapper
       picks it up as the new session for the next render; or
    b) updates a single session reference held by the wrapper.
  The corrigenda decides between (a) and (b); the catalog plan
  encodes the chosen route.
- The swap routine does not mutate fields on either the live or
  candidate session. Both remain frozen / slotted records.
- The swap propagates the active_view, status_message, and
  error_message from the live session to the candidate (so the
  operator's current view is not silently lost), then applies
  the load result status.
```

## 10. Session attachment of the SessionStoreConfig

```text
- OperatorSession gains a new optional field:
    session_store_config: Optional[SessionStoreConfig] = None
- _ALLOWED_SESSION_ATTRS adds "session_store_config".
- The field is a frozen immutable SessionStoreConfig or None. It
  carries:
    - a pathlib.Path (immutable);
    - bounded primitive fields;
    - no sqlite3.Connection (the connection lifetime is scoped to
      the save / load helper only).
- The resource-free audit (I-UI-10 style) is updated to accept
  Optional[SessionStoreConfig] as a permitted shape.
```

The corrigenda may instead carry the config on a separate
ApplicationContext record and pass it as a save/load argument. Both
shapes are acceptable as long as no sqlite3.Connection lives on
OperatorSession.

## 11. Allowed session state changes

Phase 3.9 adds at most these new fields to OperatorSession:

```text
session_store_config: Optional[SessionStoreConfig] = None
```

It does NOT add:

```text
- sqlite3.Connection (forbidden -- not resource-free)
- a "last loaded result" record beyond the bounded status message
- raw bytes blobs
- callables / hooks / observers
- mutable lists
```

The Phase 3.7 / 3.8 stream fields remain untouched: this campaign
serializes them, but does not change their shape on the session.

## 12. Likely file budget

For Step 8 (implementation):

```text
brain/ui/persistence.py                  new
brain/ui/__main__.py                     extend (CLI flags + launch wiring)
brain/ui/commands.py                     extend (SAVE_SESSION,
                                          LOAD_SESSION enum + payloads)
brain/ui/command_line.py                 extend (parser verbs)
brain/ui/session.py                      extend (Optional config field,
                                          _ALLOWED_SESSION_ATTRS,
                                          _dispatch_save_session,
                                          _dispatch_load_session)
brain/ui/render.py                       optional (status display)
brain/ui/fixtures/persistence_schema.py        new
brain/ui/fixtures/persistence_save_roundtrip.py new
brain/ui/fixtures/persistence_load_constructor_only.py new
brain/ui/fixtures/persistence_load_invariants.py new
brain/ui/fixtures/persistence_cogito_protected.py new
brain/ui/fixtures/persistence_failed_save.py    new
brain/ui/fixtures/persistence_failed_load.py    new
brain/ui/fixtures/persistence_atomic_save.py    new
brain/ui/fixtures/persistence_session_resource_audit.py new
brain/ui/fixtures/persistence_static_audit.py   new
brain/ui/fixtures/persistence_commands.py       new
brain/ui/fixtures/persistence_autosave_absent.py new
brain/invariants.py                      extend (_PHASE3_9_PENDING_ROWS
                                          + FIXTURE_MODULES additions)
brain/_catalog_ids.py                    regenerated
INVARIANT_CATALOG.md                     extend
tools/catalog.py                         bump EXPECTED_COUNTS + banner
README.md                                document save/load after impl
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
```

## 13. Fixture roster sketch

The Step 5 catalog patch plan binds exact row IDs. The likely
fixtures:

```text
persistence_schema.py
  - schema is finite and closed
  - SCHEMA_VERSION_V1 constant
  - Fraction columns are integer pairs (no REAL kernel numeric)
  - meta row keys are exactly the documented set

persistence_save_roundtrip.py
  - save(session) -> load(config) -> session' yields a session
    with profile / MSI / PtCns / registry exactly equal under
    Fraction == and frozenset ==
  - tick_counter / stream_chunk_serial / stream_history /
    stream_candidates round-trip exactly

persistence_load_constructor_only.py
  - load_session calls make_profile_with_cogito, make_msi,
    make_ptcns, ContentRegistry, BrainState, OperatorSession;
    no direct attribute assignment into any kernel record
  - static AST check that BrainState( ... ) construction in
    brain/ui/persistence.py only occurs as the final assembly
    step after builder calls

persistence_load_invariants.py
  - load runs assert_state_invariants (or the equivalent)
    before returning a candidate session

persistence_cogito_protected.py
  - a DB row claiming COGITO_ID at a non-1 value triggers a
    PersistenceError; the live session is preserved

persistence_failed_save.py
  - simulated IntegrityError or OperationalError mid-save
    triggers ROLLBACK; the live OperatorSession is preserved
    and the DB reverts

persistence_failed_load.py
  - missing DB / corrupt DB / unknown schema_version raises
    PersistenceError; the candidate is discarded

persistence_atomic_save.py
  - save is single BEGIN IMMEDIATE / COMMIT pair (or ROLLBACK
    on failure); no intermediate state is observable

persistence_session_resource_audit.py
  - OperatorSession with session_store_config still satisfies
    the resource-free policy; no sqlite3.Connection appears in
    any session field

persistence_static_audit.py
  - brain/ui/persistence.py imports are confined to the
    documented set
  - no pickle / shelve / marshal / eval / exec / compile /
    subprocess / socket / urllib / http / requests / curses
    appears in the module
  - no module-level side effects beyond imports / constants /
    function defs / class defs
  - no @atexit registration
  - no autosave entry point reachable from /step or /stream

persistence_commands.py
  - LocalCommandLine.parse accepts /save-session and
    /load-session exactly; trailing args are rejected
  - SAVE_SESSION / LOAD_SESSION dispatchers do not call tick()
  - dispatch failures surface as bounded local status/error

persistence_autosave_absent.py
  - NOT-EXERCISED placeholder; rejects any future autosave hook
    until a new catalog row authorizes it
```

OBSERVED row:

```text
cold-start continuity dry run is documented in
PHASE3_9_PERSISTENCE_DRY_RUN.md (Step 11). The fixture either
runs the deterministic walk or cites the audit; this is the only
OBSERVED row in the Phase 3.9 family.
```

The exact REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED split is
deferred to the Step 5 catalog patch plan.

## 14. Failure isolation contract

```text
- Constructor failures inside save / load raise PersistenceError.
- IO failures inside save / load raise PersistenceError.
- PersistenceError messages are bounded printable text; they pass
  through _bound_printable before being stored on
  OperatorSession.error_message.
- No exception from save / load propagates into the curses
  wrapper. /save-session and /load-session always return cleanly
  to the dispatcher, either with a status update or an error
  update.
- A failed save never mutates the live session.
- A failed load never replaces the live session.
- A failed load may have partially read the DB; because the
  connection is read-only, this never mutates the on-disk file.
```

## 15. Phase 3.10+ separation

Phase 3.9 must NOT introduce:

```text
- autosave (deferred; NOT-EXERCISED row holds the place).
- multi-profile / multi-user.
- network-backed persistence.
- full TickRecord / event-log replay.
- migrations between schema versions.
- persistence of LLM client / cache / runtime mode.
- persistence of operator transcripts beyond bounded session-local
  state.
- persistence of curses configuration / terminal state.
- raw-text-to-COGITO mappings.
- raw-text-to-BrainState direct writes.
- a second classification path through /save-session or
  /load-session.
- changes to tick() semantics.
```

The corrigenda must restate these as hard non-goals.

## 16. Stop point

Next artifact:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md
```

The corrigenda should audit this kickoff for:

```text
- module placement (UI-owned vs subsystem)
- schema closure (finite, no executable columns, no REAL kernel
  numeric)
- exact Fraction persistence (num INTEGER + den INTEGER)
- COGITO_ID reservation on load
- constructor-only reconstruction
- load failure isolation (live session preserved)
- save transaction atomicity
- no pickle / no object-repr authority
- session resource-free property (no sqlite3.Connection on
  OperatorSession)
- whether DB connection may be long-lived or operation-scoped
- whether autosave is deferred
- which Phase 3.9 rows should be REQUIRED / STRUCTURAL / OBSERVED /
  NOT-EXERCISED in the catalog patch plan
```

After the corrigenda, the catalog patch plan (Step 5) binds rows
and stops at the Step 6 review gate before any catalog or runtime
implementation begins.
