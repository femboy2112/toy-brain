# PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md

## 1. Purpose

Document a deterministic end-to-end ops/observability walk for the
Phase 3.10 Operational Hardening + Persistence Observability layer.
The walk exercises the OBSERVED row `I-OBSERVE-11` and demonstrates
that the eight Phase 3.10a/b typed verbs and the four short-circuit
CLI flags produce bounded, read-mostly reports without mutating the
live `OperatorSession` or the source session DB.

This is an audit artifact, not a runtime mutation. It edits no
catalog row, no fixture, no runtime module, and no guarded kernel
path.

## 2. Baseline

```text
Catalog version:  v0.18
REQUIRED:        201
STRUCTURAL:       79
NOT-EXERCISED:    10
DEFERRED:         12
OBSERVED:         14
Total fixtures:  120
Default LLM mode: offline (OfflineStandInClient)
Default DB path:  not configured (set via --session-db)
```

All Phase 3.10a/b fixture-backed rows (`I-OPSHARDEN-01..14`,
`I-OBSERVE-01..10`) pass under the runner. The Step 11 audit
certifies the full gate; this document captures the inspectable
scripted walk that `I-OBSERVE-11` points at.

## 3. Scripted scenario

The walk uses the deterministic offline stand-in client. Every
typed-verb command is parsed by
`brain.ui.command_line.LocalCommandLine.parse` and dispatched
through `OperatorSession.dispatch`. The four CLI flags
(`--db-status`, `--db-verify`, `--db-backup PATH`,
`--db-backup-force`) short-circuit through
`brain.ui.__main__.main()` after `--check-terminal` /
`--print-once` but before `_resolve_llm_runtime_config`.

No file outside the configured session DB and the explicit
`/db-backup` destination is mutated; no network call is made; no
subprocess is spawned.

### 3.1 Setup

```python
import pathlib
from brain.ui.__main__ import build_default_session, OfflineStandInClient
from brain.ui.command_line import LocalCommandLine
from brain.ui.persistence import SessionStoreConfig

db_path     = pathlib.Path("brain/session.sqlite3")
backup_path = pathlib.Path("brain/session.bak.sqlite3")
config      = SessionStoreConfig(db_path=db_path)

session = build_default_session()
session.session_store_config = config
client  = OfflineStandInClient()
parser  = LocalCommandLine()
```

### 3.2 First process — operator builds, saves, then exercises Phase 3.10

```text
> /stream hello world
  status="stream chunk 'strm-chunk-1' appended (history size = 1)"
  view=stream_summary

> /stream-promote promo-strm-chunk-1
  status="promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)"
  view=queue
  event_queue: 1

> /step
  status="tick 1 ok (MODE_C)"
  view=tick
  tick_counter: 1
  profile.domain: ['__cogito__', 'alpha', 'strm-strm-chunk-1']
  msi.contents:   ['__cogito__', 'alpha', 'strm-strm-chunk-1']
  msi.threshold:  1/2
  profile['__cogito__']        = 1
  profile['alpha']             = 3/4
  profile['strm-strm-chunk-1'] = 1/2

> /save-session
  status="saved session to brain/session.sqlite3 (chunks=1, candidates=1)"
  view=tick
  tick_counter: 1            (unchanged)
  on-disk DB:
    meta:
      schema_version  = "1"
      catalog_version = "v0.18"
      created_at      = "<ISO-8601 UTC>"
      updated_at      = "<ISO-8601 UTC>"
    profile_values rows = 3
    msi_contents rows   = 3
    msi_threshold       = (1, 2)
    ptcns_eval rows     = 3
    content_registry rows = 2
    session_state.tick_counter        = "1"
    session_state.stream_chunk_serial = "1"
    stream_chunks rows                = 1
    stream_candidates rows            = 1
```

### 3.3 Phase 3.10a — operational hardening

```text
> /session-status
  status="session status (tick=1 queue=0 view=tick chunks=1 candidates=1 db=brain/session.sqlite3 quit=False)"
  SessionStatusReport:
    tick_counter             = 1
    queue_size               = 0
    active_view              = "tick"
    has_latest_tick          = True
    has_output_history       = False
    has_worldlet_history     = False
    has_repl_history         = False
    stream_chunk_count       = 1
    stream_candidate_count   = 1
    stream_chunk_serial      = 1
    session_db_configured    = True
    session_db_path_str      = "brain/session.sqlite3"
    quit_flag                = False
  (no disk IO; live session field-for-field equal to pre-call)

> /db-status
  status="db status (path=brain/session.sqlite3 size=B mtime=<ISO> schema=1 catalog=v0.18)"
  DbStatusReport:
    db_path_str       = "brain/session.sqlite3"
    db_exists         = True
    db_byte_size      = <positive int>
    db_modified_at    = "<ISO-8601 UTC>"
    schema_version    = 1
    catalog_version   = "v0.18"
    created_at        = "<ISO-8601 UTC>"
    updated_at        = "<ISO-8601 UTC>"
    error_text        = ""
  (sqlite3 mode=ro open; closed via `with conn:`; no mutation)

> /db-verify
  status="db verify PASS (schema=1 catalog=v0.18 chunks=1 candidates=1)"
  DbVerifyReport:
    db_path_str          = "brain/session.sqlite3"
    passed               = True
    schema_version       = 1
    catalog_version      = "v0.18"
    loaded_chunks        = 1
    loaded_candidates    = 1
    rebuilt_candidates   = False
    error_text           = ""
  (load_session returned a candidate; the candidate was IMMEDIATELY
   dropped; id(session) is unchanged before and after the call;
   the live OperatorSession field-for-field equals the pre-call
   session)
```

### 3.4 Phase 3.10b — persistence observability

```text
> /db-summary
  status="db summary (profile=3 msi=3 ptcns=3 registry=2 streams=1 candidates=1 tick=1 serial=1)"
  DbSummaryReport:
    db_path_str              = "brain/session.sqlite3"
    schema_version           = 1
    catalog_version          = "v0.18"
    created_at               = "<ISO>"
    updated_at               = "<ISO>"
    profile_row_count        = 3
    msi_content_count        = 3
    msi_threshold            = "1/2"
    ptcns_eval_row_count     = 3
    registry_row_count       = 2
    stream_chunk_count       = 1
    stream_candidate_count   = 1
    tick_counter             = 1
    stream_chunk_serial      = 1
    error_text               = ""

> /profile-summary
  status="profile summary (rows=3 truncated=False)"
  ProfileSummaryReport:
    db_path_str = "brain/session.sqlite3"
    rows:
      ProfileSummaryRow(content_id="__cogito__",          value_str="1/1")
      ProfileSummaryRow(content_id="alpha",               value_str="3/4")
      ProfileSummaryRow(content_id="strm-strm-chunk-1",   value_str="1/2")
    truncated  = False
    error_text = ""
  (COGITO_ID first; remainder sorted ASCII-ascending; every value
   rendered as exact "num/den" via a single shared helper; no
   float() / repr() leakage)

> /stream-db-summary
  status="stream db summary (chunks=1 candidates=1 head=1 tail=1)"
  StreamDbSummaryReport:
    db_path_str        = "brain/session.sqlite3"
    chunk_count        = 1
    candidate_count    = 1
    first_ordinal      = 1
    last_ordinal       = 1
    head:
      StreamDbSummaryRow(ordinal=1, chunk_id="strm-chunk-1",
        source="operator", tick_at_event=0,
        provenance_tag="operator-stream",
        text_preview="hello world")
    tail: (same single row as head; the bounded slice never
      duplicates when chunk_count <= head_cap + tail_cap)
    truncated  = False
    error_text = ""

> /db-diff
  status="db diff matches (diff_count=0)"
  DbDiffReport:
    db_path_str  = "brain/session.sqlite3"
    matches      = True
    diff_count   = 0
    differences  = ()
    truncated    = False
    error_text   = ""
```

If the operator now runs `/step` again without saving and then
re-runs `/db-diff`, the diff surfaces the divergence explicitly:

```text
> /step
  status="tick 2 ok (MODE_C)"
  tick_counter: 2

> /db-diff
  status="db diff diverged (diff_count=1)"
  DbDiffReport:
    matches      = False
    diff_count   = 1
    differences  = (
      DbDiffField(field="tick_counter", live="2", saved="1"),
    )
    truncated    = False
    error_text   = ""
  (the diff names the divergent field explicitly; if a content_id
   appeared on only one side the row would carry the literal
   "<missing>" on the other side — never a silent 0 / null)
```

### 3.5 Phase 3.10a — explicit backup

```text
> /db-backup brain/session.bak.sqlite3
  status="db backup OK (dest=brain/session.bak.sqlite3 pages=K/T bytes=B)"
  DbBackupReport:
    source_path_str   = "brain/session.sqlite3"
    dest_path_str     = "brain/session.bak.sqlite3"
    source_byte_size  = <positive int>
    dest_byte_size    = <equal to source_byte_size>
    pages_copied      = <positive int>
    total_pages       = <equal to pages_copied>
    succeeded         = True
    overwritten       = False
    error_text        = ""
  (sqlite3.Connection.backup(); mode=ro source connection inside
   `with conn:`; the source DB file byte-equals the pre-call file
   after the backup completes)

> /db-backup brain/session.bak.sqlite3
  error="db backup failed (dest exists; pass --force to overwrite)"
  DbBackupReport:
    succeeded   = False
    overwritten = False
    error_text  = "..."
  (refused without --force; destination untouched)

> /db-backup brain/session.bak.sqlite3 --force
  status="db backup OK overwritten (dest=brain/session.bak.sqlite3 pages=K/T bytes=B)"
  DbBackupReport:
    succeeded   = True
    overwritten = True
    error_text  = ""

> /db-backup sqlite:///tmp/anything
  error="db backup failed (refusing URI-scheme destination 'sqlite')"
  (rejected at parse time; no sqlite3 call; no file touched)
```

### 3.6 Second process — relaunch against the backup file

```bash
$ python3 -m brain.ui --session-db brain/session.bak.sqlite3 --db-verify
brain.ui: db verify PASS (schema=1 catalog=v0.18 chunks=1 candidates=1)
$ echo $?
0

$ python3 -m brain.ui --session-db brain/session.bak.sqlite3 --db-status
brain.ui: db status (path=brain/session.bak.sqlite3 size=B mtime=<ISO> schema=1 catalog=v0.18)
$ echo $?
0
```

```text
> python3 -m brain.ui --session-db brain/session.bak.sqlite3 --load-session
brain.ui: session db = brain/session.bak.sqlite3 (loaded; schema=v1; catalog=v0.18; chunks=1; candidates=1)
brain.ui: llm runtime mode = offline (deterministic stand-in)

  After load:
    BrainState.profile.domain      == ['__cogito__', 'alpha', 'strm-strm-chunk-1']
    BrainState.profile['__cogito__']       == Fraction(1, 1)
    BrainState.profile['alpha']            == Fraction(3, 4)
    BrainState.profile['strm-strm-chunk-1'] == Fraction(1, 2)
    BrainState.msi.contents        == {'__cogito__', 'alpha', 'strm-strm-chunk-1'}
    BrainState.msi.threshold       == Fraction(1, 2)
    BrainState.ptcns.eval_map      == {COGITO_ID: PRESERVE, 'alpha': PRESERVE, 'strm-strm-chunk-1': PRESERVE}
    BrainState.registry.texts      == {'alpha': 'alpha text', 'strm-strm-chunk-1': 'hello world'}
    OperatorSession.tick_counter   == 1
    OperatorSession.stream_history.chunks                  == 1
    OperatorSession.stream_chunk_serial                    == 1
    OperatorSession.stream_candidates                       == ('promo-strm-chunk-1',)
    OperatorSession.session_store_config.db_path           == brain/session.bak.sqlite3
```

The backup file produced by `/db-backup` parses through
`load_session` identically to the source DB.

### 3.7 Negative paths exercised

The walk also produces these failure-isolation envelopes that the
fixtures (`persistence_ops_db_verify.py`,
`persistence_ops_db_backup.py`,
`persistence_ops_db_backup_force.py`,
`persistence_ops_db_backup_dest_uri.py`,
`persistence_observe_db_diff.py`) pin programmatically:

```text
> /db-verify   (against a missing DB)
  error="db verify FAIL (session DB at /tmp/missing.sqlite3 does not exist)"
  DbVerifyReport.passed = False
  live session unchanged

> /db-verify   (against a tampered DB with rho_den=0)
  error="db verify FAIL (profile_values den must be positive)"
  DbVerifyReport.passed = False
  live session unchanged

> /db-backup ./session.sqlite3   (dest == source)
  error="db backup failed (dest_path equals source_path)"
  DbBackupReport.succeeded = False
  source DB unchanged

> /db-backup file:///tmp/anything   (URI scheme)
  error="db backup failed (refusing URI-scheme destination 'file')"
  DbBackupReport.succeeded = False
  no destination touched
```

## 4. Invariants confirmed by the walk

```text
- /session-status is read-only and bounded.               (I-OPSHARDEN-01)
- /db-status is read-only mode=ro and bounded.            (I-OPSHARDEN-02)
- /db-verify reuses load_session and DROPS the candidate. (I-OPSHARDEN-03)
- /db-verify failure preserves the live session.          (I-OPSHARDEN-04)
- /db-backup uses sqlite3.Connection.backup().            (I-OPSHARDEN-05)
- /db-backup refuses to overwrite without --force.        (I-OPSHARDEN-06)
- /db-backup refuses URI-scheme destinations.             (I-OPSHARDEN-07)
- /db-backup never modifies the source DB.                (I-OPSHARDEN-08)
- CLI flags exit 0 on success and 1 on failure.           (I-OPSHARDEN-09, I-OPSHARDEN-14)
- Source connection mode=ro during backup.                (I-OPSHARDEN-10)
- /db-summary reads in mode=ro; bounded report.           (I-OBSERVE-01)
- /profile-summary returns exact "num/den" rows.          (I-OBSERVE-02)
- /stream-db-summary returns bounded head + tail.         (I-OBSERVE-03)
- /db-diff reports finite field enumeration; "<missing>". (I-OBSERVE-04)
- Observability commands never activate saved state.      (I-OBSERVE-05)
- Locked default row caps are honored.                    (I-OBSERVE-09)
- Phase 3.10 ops/observability dry run is inspectable.    (I-OBSERVE-11)
```

The static-AST audits (`I-OPSHARDEN-11`, `I-OPSHARDEN-12`,
`I-OPSHARDEN-13`, `I-OBSERVE-06`, `I-OBSERVE-07`, `I-OBSERVE-08`,
`I-OBSERVE-10`) are enforced by the runner-loaded fixture modules
and do not need to be exercised through a live operator walk.

## 5. Non-mutations confirmed by the walk

```text
- The live OperatorSession field-for-field equals the pre-call
  session after every Phase 3.10a/b verb.
- The source DB file byte-equals the pre-call file after every
  read-only verb and after a successful /db-backup.
- No new OperatorSession field appears.
- No sqlite3.Connection / Cursor / subprocess / socket / file /
  callable / curses object appears in any session field after
  any verb.
- No call to tick() occurs inside any Phase 3.10a/b dispatcher.
- No save_session call occurs from any Phase 3.10a/b path; the
  /save-session verb in section 3.2 is the Phase 3.9 explicit
  command.
- No @atexit / signal handler / threading / asyncio loop fires.
```

## 6. Conclusion

The deterministic walk through Phase 3.10a and 3.10b succeeds on
the offline stand-in client. Every typed verb produces a bounded
report; every short-circuit CLI flag exits with the documented
code; the live session and source DB are unchanged after every
read-only verb; the backup file parses through `load_session`
identically to the source.

```text
I-OBSERVE-11 cited from this document.
```
