# PHASE3_10C_AUTOSAVE_DRY_RUN.md

## 1. Purpose

Document a deterministic end-to-end walk for the Phase 3.10c
Autosave Policy layer. The walk exercises the OBSERVED row
`I-AUTOSAVE-15` and demonstrates that the default-OFF, opt-in
autosave runtime fires exactly once after a successful mutating
dispatch, never fires after a failed dispatch, never fires after
a read-only dispatch, never fires inside `tick()`, and absorbs
every `PersistenceError` into the typed
`AutosaveStatusReport.last_attempt_outcome="error"` without
mutating the live `OperatorSession` or the on-disk session DB.

This is an audit artifact, not a runtime mutation. It edits no
catalog row, no fixture, no runtime module, and no guarded kernel
path.

## 2. Baseline

```text
Catalog version:  v0.19
REQUIRED:        212
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         15
Total fixtures:  131
Default LLM mode:    offline (OfflineStandInClient)
Default autosave:    OFF (cold-start; not opt-in by default)
Default DB path:     not configured (set via --session-db)
```

All Phase 3.10c fixture-backed rows (`I-AUTOSAVE-01..14`) pass
under the runner. The Step 20 integrated audit certifies the full
gate; this document captures the inspectable scripted walk that
`I-AUTOSAVE-15` points at.

## 3. Scripted scenario

The walk uses the deterministic offline stand-in client. Every
typed-verb command is parsed by
`brain.ui.command_line.LocalCommandLine.parse` and dispatched
through `OperatorSession.dispatch`. The `--autosave-mode` CLI flag
short-circuits in `brain.ui.__main__.main()`: a non-OFF mode
without `--session-db` raises argparse error code 2 BEFORE
`main()`'s body executes.

No file outside the configured session DB is mutated; no network
call is made; no subprocess is spawned. The Phase 3.10c trigger
set is closed: `STEP_TICK` (a successful `/step` advances the
tick counter) and `STREAM_PROMOTE` (a successful `/stream-promote`
queues exactly one validated payload).

### 3.1 Setup

```python
import pathlib
from brain.ui.__main__ import build_default_session, OfflineStandInClient
from brain.ui.autosave import AutosaveMode, autosave_enable, autosave_disable
from brain.ui.command_line import LocalCommandLine
from brain.ui.persistence import SessionStoreConfig

db_path     = pathlib.Path("brain/session.sqlite3")
config      = SessionStoreConfig(db_path=db_path)

session = build_default_session()
session.session_store_config = config
client  = OfflineStandInClient()
parser  = LocalCommandLine()
```

### 3.2 Cold-start default is OFF

```text
After build_default_session():
  session.autosave_config       = None
  session.last_autosave_status  = None

Inspection (no /autosave-enable yet):
  > /autosave-status
    status="autosave status (mode=off db= last_tick=0 last_outcome= last_at= last_trigger= last_error=)"
    AutosaveStatusReport:
      mode                     = AutosaveMode.OFF
      db_path_str              = ""
      last_attempt_tick        = 0
      last_attempt_outcome     = ""
      last_attempt_at          = ""
      last_attempt_trigger     = ""
      last_error_text          = ""
    (autosave_status() never raises; the bounded report fields
     reflect the cold-start null state explicitly)

CLI defaults:
  $ python3 -m brain.ui --print-once 2>&1 | head -1
  (default --autosave-mode is "off" with no DB configured;
   no startup-error)

  $ python3 -m brain.ui --autosave-mode after-successful-mutation
  brain.ui: --autosave-mode after-successful-mutation requires --session-db
  $ echo $?
  2
  (argparse rejects non-OFF mode without --session-db BEFORE
   main()'s body executes)
```

### 3.3 Enable autosave for the session

```text
> /autosave-enable after-successful-mutation
  status="autosave enabled (mode=after-successful-mutation db=brain/session.sqlite3)"
  AutosaveStatusReport:
    mode                     = AutosaveMode.AFTER_SUCCESSFUL_MUTATION
    db_path_str              = "brain/session.sqlite3"
    last_attempt_tick        = 0
    last_attempt_outcome     = ""
    last_attempt_at          = ""
    last_attempt_trigger     = ""
    last_error_text          = ""
  (session.autosave_config.mode now AFTER_SUCCESSFUL_MUTATION;
   session.last_autosave_status still None until the first
   successful mutating dispatch)

Negative path: enable without --session-db
  > /autosave-enable after-successful-mutation
    (session.session_store_config is None)
    error="autosave enable failed: requires a configured session DB"
    PersistenceError absorbed by the dispatcher; live session
    unchanged; session.autosave_config still None.
```

### 3.4 Successful mutation triggers autosave (STEP_TICK)

```text
> /stream hello world
  status="stream chunk 'strm-chunk-1' appended (history size = 1)"
  view=stream_summary
  (this is /stream, NOT in the trigger set; autosave does NOT
   fire; session.last_autosave_status unchanged)

> /stream-promote promo-strm-chunk-1
  status="promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)"
  view=queue
  event_queue: 1
  AutosaveStatusReport (autosave fired with STREAM_PROMOTE):
    mode                     = AutosaveMode.AFTER_SUCCESSFUL_MUTATION
    db_path_str              = "brain/session.sqlite3"
    last_attempt_tick        = 0     (tick has not yet advanced)
    last_attempt_outcome     = "ok"
    last_attempt_at          = "<ISO-8601 UTC>"
    last_attempt_trigger     = "stream_promote"
    last_error_text          = ""
  (the saved DB now reflects the queued payload + session state)

> /step
  status="tick 1 ok (MODE_C)"
  view=tick
  tick_counter: 1
  AutosaveStatusReport (autosave fired with STEP_TICK):
    last_attempt_tick        = 1
    last_attempt_outcome     = "ok"
    last_attempt_at          = "<ISO-8601 UTC, later than above>"
    last_attempt_trigger     = "step_tick"
    last_error_text          = ""
  (the saved DB's meta.updated_at advances; the DB on-disk size
   is non-zero; the round-trip through load_session yields a
   session equal to the live one under __eq__)
```

### 3.5 Read-only dispatch does NOT trigger autosave

Each command in the closed read-only list is dispatched against
the autosave-enabled session; `session.last_autosave_status` is
unchanged after every one and the saved DB's `meta.updated_at`
is unchanged.

```text
> /state                           (INSPECT_STATE)
> /tick                            (INSPECT_TICK)
> /output                          (INSPECT_OUTPUT)
> /worldlet                        (INSPECT_WORLDLET)
> /repl                            (INSPECT_REPL)
> /stream-summary                  (INSPECT_STREAM_SUMMARY)
> /stream-candidates               (INSPECT_STREAM_CANDIDATES)
> /clear                           (CLEAR_STATUS)
> /help                            (HELP)
> /session-status                  (SESSION_STATUS; Phase 3.10a)
> /db-status                       (DB_STATUS; Phase 3.10a)
> /db-verify                       (DB_VERIFY; Phase 3.10a)
> /db-summary                      (DB_SUMMARY; Phase 3.10b)
> /profile-summary                 (PROFILE_SUMMARY; Phase 3.10b)
> /stream-db-summary               (STREAM_DB_SUMMARY; Phase 3.10b)
> /db-diff                         (DB_DIFF; Phase 3.10b)
> /db-backup /tmp/bak.sqlite3      (DB_BACKUP; Phase 3.10a)
> /autosave-status                 (AUTOSAVE_STATUS; Phase 3.10c)
> /save-session                    (SAVE_SESSION; Phase 3.9 explicit
                                    save; the dispatcher writes via
                                    save_session, but the central
                                    dispatch does NOT post-trigger
                                    autosave for SAVE_SESSION — the
                                    operator already saved)
> /load-session                    (LOAD_SESSION; Phase 3.9)

For every one: session.last_autosave_status is unchanged;
the saved DB's meta.updated_at is unchanged.
```

### 3.6 Failed dispatch does NOT trigger autosave

```text
Drain the event queue first:
> /step                            (advances tick to 2; autosave
                                    fires with last_attempt_tick=2)

Now /step against an empty queue:
> /step
  error="step failed: event_queue is empty"
  tick_counter: 2                  (unchanged)
  AutosaveStatusReport:
    last_attempt_tick        = 2   (unchanged; previous successful
                                    /step value)
    last_attempt_outcome     = "ok" (unchanged)
    last_attempt_trigger     = "step_tick" (unchanged)
  (the failed dispatcher returned False to the central dispatch;
   _maybe_autosave_after_dispatch saw False and did NOT call
   maybe_autosave_after_mutation; session.last_autosave_status
   reflects the LAST SUCCESSFUL autosave, not the most recent
   failed attempt)
```

### 3.7 PersistenceError absorption (corrupt DB / RO destination)

Inject a transactional failure by pointing autosave at a
read-only path or a corrupted DB file. The helper absorbs the
exception into the typed report; the live `OperatorSession` is
preserved exactly.

```text
> /autosave-enable after-successful-mutation
  (against a session whose session_store_config.db_path points at
   a read-only or non-writable destination)

> /stream-promote promo-foo
  (succeeds at the dispatcher level; the post-dispatch autosave
   attempt fails inside save_session with PersistenceError)
  status="promoted stream candidate 'promo-foo' (queue size = 1)"
  AutosaveStatusReport (failure absorbed):
    mode                     = AutosaveMode.AFTER_SUCCESSFUL_MUTATION
    db_path_str              = "<ro_path>"
    last_attempt_tick        = <prev>
    last_attempt_outcome     = "error"
    last_attempt_at          = "<ISO-8601 UTC>"
    last_attempt_trigger     = "stream_promote"
    last_error_text          = "<bounded printable error>"
  (no exception propagates; the dispatcher caught nothing because
   maybe_autosave_after_mutation NEVER raises; the live session's
   BrainState and stream state are byte-identical to the pre-call
   state; the on-disk DB file is unchanged because save_session's
   transactional BEGIN IMMEDIATE / ROLLBACK preserved it)

A subsequent attempt against the same broken target reports
outcome="error" again; the operator can disable autosave or fix
the underlying issue:

> /autosave-disable
  status="autosave disabled"
  AutosaveStatusReport:
    mode = AutosaveMode.OFF
  (idempotent; calling /autosave-disable again returns the same
   report; never raises)
```

### 3.8 Re-arming works

```text
Fix the destination (move the DB to a writable path; reconfigure
session.session_store_config):

> /autosave-enable after-successful-mutation
  status="autosave enabled (mode=after-successful-mutation db=...)"

> /step
  status="tick N ok (MODE_C)"
  AutosaveStatusReport:
    last_attempt_outcome     = "ok"
    last_attempt_at          = "<new ISO timestamp>"
    last_attempt_trigger     = "step_tick"
    last_error_text          = "" (cleared on success)
```

## 4. Invariants confirmed by the walk

```text
- Default OFF on every cold start.                         (I-AUTOSAVE-01)
- AutosaveConfig with non-OFF mode + empty db_path_str
    raises ValueError.                                     (I-AUTOSAVE-02)
- /autosave-enable without --session-db raises
    PersistenceError.                                      (I-AUTOSAVE-03)
- /autosave-enable transitions session.autosave_config
    correctly.                                             (I-AUTOSAVE-04)
- /autosave-disable is idempotent and never raises.        (I-AUTOSAVE-05)
- /autosave-status returns a bounded report and never
    raises.                                                (I-AUTOSAVE-06)
- maybe_autosave_after_mutation NEVER raises (absorbs every
    PersistenceError into the typed report).               (I-AUTOSAVE-07)
- /step + autosave + success -> last_attempt_outcome="ok". (I-AUTOSAVE-08)
- Failed dispatch does NOT trigger autosave.               (I-AUTOSAVE-09)
- Read-only dispatch does NOT trigger autosave (closed
    20-verb list audited).                                 (I-AUTOSAVE-10)
- Autosave reuses save_session; no second save code path
    exists.                                                (I-AUTOSAVE-11)
- Phase 3.10c autosave dry run is inspectable.             (I-AUTOSAVE-15)
```

The static-AST audits (`I-AUTOSAVE-12`, `I-AUTOSAVE-13`,
`I-AUTOSAVE-14`) are enforced by the runner-loaded fixture
modules and do not need to be exercised through a live operator
walk.

## 5. Non-mutations confirmed by the walk

```text
- The live OperatorSession.state field-for-field equals the
  pre-call state after every read-only dispatch and after every
  failed dispatch.
- The source DB file byte-equals the pre-call file after every
  read-only dispatch, after every failed dispatch, and after
  every absorbed-PersistenceError autosave attempt.
- No new OperatorSession field appears beyond autosave_config
  and last_autosave_status (both Optional[frozen+slotted record]).
- No sqlite3.Connection / Cursor / subprocess / socket / file /
  callable / curses object appears in any session field after
  any /autosave-* verb or any post-dispatch autosave attempt.
- No tick() call occurs inside any Phase 3.10c dispatcher or
  inside maybe_autosave_after_mutation.
- No save_session call occurs from any read-only dispatch or
  failed dispatch.
- No @atexit / signal handler / threading / asyncio loop fires.
- No second save_session helper exists anywhere in brain/.
- The autosave entry point lives only at the post-dispatch site
  in OperatorSession.dispatch (no /step / /stream-promote
  dispatcher body invokes autosave directly).
```

## 6. Conclusion

The deterministic walk through Phase 3.10c succeeds on the
offline stand-in client. Autosave fires exactly once after each
successful mutating dispatch on the closed trigger set, never
fires after read-only or failed dispatches, never fires inside
`tick()`, and absorbs every `PersistenceError` into the typed
status report. The live session and source DB are preserved
across every failure path.

```text
I-AUTOSAVE-15 cited from this document.
```
