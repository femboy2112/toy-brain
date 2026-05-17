# PHASE3_9_PERSISTENCE_DRY_RUN.md

## 1. Purpose

Document a deterministic end-to-end cold-start continuity walk for
the Phase 3.9 Persistent Session Store. The walk exercises the
OBSERVED row `I-PERSIST-15` and demonstrates that a session can be
saved on one process invocation, the process can exit, and a
subsequent invocation with `--session-db` and `--load-session`
restores the exact kernel + session-local stream state.

This is an audit artifact, not a runtime mutation. It edits no
catalog row, no fixture, no runtime module, and no guarded kernel
path.

## 2. Baseline

```text
Catalog version:  v0.17
REQUIRED:         187
STRUCTURAL:        69
NOT-EXERCISED:     10
DEFERRED:          12
OBSERVED:          13
Total fixtures:   103
Default LLM mode: offline (OfflineStandInClient)
Default DB path:  not configured (set via --session-db)
```

All Phase 3.9 fixture-backed rows (I-PERSIST-01..14) pass under
the runner. The Step 12 audit certifies the full gate; this
document captures the inspectable scripted walk that `I-PERSIST-15`
points at.

## 3. Scripted scenario

The walk uses the deterministic offline stand-in client. Every
command is parsed by `brain.ui.command_line.LocalCommandLine.parse`
and dispatched through `OperatorSession.dispatch`. No file outside
the configured session DB is mutated; no network call is made; no
subprocess is spawned.

### 3.1 Setup

```python
import pathlib
from brain.ui.__main__ import build_default_session, OfflineStandInClient
from brain.ui.command_line import LocalCommandLine
from brain.ui.persistence import SessionStoreConfig, load_session

db_path = pathlib.Path("brain/session.sqlite3")  # any writable path
config  = SessionStoreConfig(db_path=db_path)

session = build_default_session()
session.session_store_config = config
client  = OfflineStandInClient()
parser  = LocalCommandLine()
```

### 3.2 First process — operator builds and saves a session

```text
> /stream hello world
  status="stream chunk 'strm-chunk-1' appended (history size = 1)"
  view=stream_summary
  stream_history.chunks: 1
  stream_candidates: 1     (id: 'promo-strm-chunk-1')
  event_queue: 0
  tick_counter: 0

> /stream-promote promo-strm-chunk-1
  status="promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)"
  view=queue
  stream_history.chunks: 1
  stream_candidates: 1
  event_queue: 1
  tick_counter: 0

> /step
  status="tick 1 ok (MODE_C)"
  view=tick
  stream_history.chunks: 1
  stream_candidates: 1
  event_queue: 0
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
  stream_history.chunks: 1   (unchanged)
  stream_candidates: 1       (unchanged)
  event_queue: 0             (unchanged)
  on-disk DB:
    meta.schema_version  = "1"
    meta.catalog_version = "v0.17"
    meta.created_at      = <ISO-8601 UTC>
    meta.updated_at      = <ISO-8601 UTC>
    profile_values       = 3 rows (cogito / alpha / strm-strm-chunk-1)
    msi_contents         = 3 rows
    msi_threshold        = (id=1, num=1, den=2)
    ptcns_eval           = 3 rows (all PRESERVE)
    content_registry     = 2 rows (alpha / strm-strm-chunk-1)
    session_state.tick_counter        = "1"
    session_state.stream_chunk_serial = "1"
    stream_chunks        = 1 row  (chunk_id 'strm-chunk-1')
    stream_candidates    = 1 row  (candidate_id 'promo-strm-chunk-1')
```

Observations:

```text
- /save-session never calls tick(); tick_counter is unchanged
  across the save dispatch (a save-then-state assertion of
  tick_counter equality holds by construction).
- BrainState identity, ContentRegistry identity, stream_history
  identity, stream_candidates identity, event_queue length, and
  latest_tick are all unchanged across /save-session.
- The on-disk DB is a typed v1 SQLite snapshot. Every kernel-numeric
  column is INTEGER. No REAL / NUMERIC / FLOAT / DOUBLE column
  exists.
- No `sqlite3.Connection` is left attached to OperatorSession.
```

### 3.3 Second process — fresh launch, load, verify

```python
import pathlib
from brain.ui.__main__ import build_default_session
from brain.ui.persistence import SessionStoreConfig, load_session

db_path = pathlib.Path("brain/session.sqlite3")
config  = SessionStoreConfig(db_path=db_path)

# Fresh default session in the new process.
session = build_default_session()
session.session_store_config = config

# Load.
candidate, result = load_session(config)
```

Result:

```text
result.schema_version       = 1
result.catalog_version      = "v0.17"
result.loaded_chunks        = 1
result.loaded_candidates    = 1
result.rebuilt_candidates   = False  (candidates were persisted, not rebuilt)

candidate.tick_counter      = 1
candidate.stream_chunk_serial = 1
candidate.stream_history.chunks: 1
candidate.stream_candidates:    1

candidate.state.profile.domain:
  ['__cogito__', 'alpha', 'strm-strm-chunk-1']
candidate.state.profile.values['__cogito__']        = 1
candidate.state.profile.values['alpha']             = 3/4
candidate.state.profile.values['strm-strm-chunk-1'] = 1/2

candidate.state.msi.contents:
  ['__cogito__', 'alpha', 'strm-strm-chunk-1']
candidate.state.msi.threshold = 1/2

candidate.state.ptcns.eval_map['__cogito__']        = PRESERVE
candidate.state.ptcns.eval_map['alpha']             = PRESERVE
candidate.state.ptcns.eval_map['strm-strm-chunk-1'] = PRESERVE
```

Round-trip equality holds field-for-field. Every `Fraction` value
round-trips byte-for-byte because the SQLite schema stores
numerator and denominator as separate `INTEGER` columns; the load
helper reconstructs each value through `Fraction(num, den)`.

### 3.4 Inside-TUI launch path

The same behaviour is available through the operator-facing CLI:

```bash
# First launch: save then quit.
python3 -m brain.ui --session-db brain/session.sqlite3
> /stream hello world
> /stream-promote promo-strm-chunk-1
> /step
> /save-session
> /quit

# Subsequent launch: load before the TUI opens.
python3 -m brain.ui --session-db brain/session.sqlite3 --load-session
# stdout: brain.ui: session db = brain/session.sqlite3
#          (loaded; schema=v1; catalog=v0.17; chunks=1; candidates=1)
```

The `--load-session` launch path is independent of `--print-once`
/ `--check-terminal` (both short-circuit before any persistence
call) and independent of `--llm-mode` (offline remains the default;
explicit model-backed modes are still opt-in through the existing
Phase 3.8b toggle).

## 4. What this walk does not exercise

The dry run intentionally does NOT cover:

```text
- autosave (NOT-EXERCISED in Phase 3.9; placeholder held by
  I-PERSIST-16 and structurally enforced by
  persistence_static_audit.py).
- migrations between schema versions (only v1 is defined;
  load_session raises PersistenceError for any other version).
- multi-profile / multi-user persistence (out of scope).
- network-backed persistence (out of scope).
- persistence of OperatorTranscript / OutputHistory /
  WorldletHistory / ProtoBasicHistory / ExpressionHistory /
  ReflectiveInspectionSummary (deferred).
- persistence of LLM client / cache / runtime mode (forbidden by
  I-PERSIST-12 and the existing Phase 3.8b toggle audits).
- persistence of curses configuration / terminal state.
- save / export to any path other than the configured DB.
- raw-text-to-COGITO_ID mappings or raw-text-to-BrainState direct
  writes (forbidden by every existing kernel guardrail).
- changes to `tick()` semantics.
```

## 5. Recovery paths

```text
- A failed /save-session (mid-INSERT IntegrityError /
  OperationalError, on-disk space exhausted, locked DB) raises
  PersistenceError inside the dispatcher, ROLLBACKs the data
  transaction (the schema bootstrap is autocommit and persists),
  and surfaces a bounded local error message via
  OperatorSession.error_message. The live OperatorSession is
  unchanged. A subsequent successful /save-session produces a
  clean snapshot.

- A failed /load-session (DB missing, DB is a directory, schema
  version mismatch, FOREIGN KEY violation, malformed Fraction
  pair, builder rejection, invariant assertion failure) raises
  PersistenceError inside the dispatcher and surfaces a bounded
  local error message via OperatorSession.error_message. The
  live OperatorSession is unchanged. The on-disk DB is unchanged
  (the load path opens in sqlite3 uri `mode=ro`).

- A persisted row attempting to overwrite COGITO_ID (rho != 1,
  missing MSI membership, or eval != PRESERVE) raises
  PersistenceError before any reconstruction reaches a candidate
  session.

- A `--load-session` launch with a missing or corrupt DB prints a
  bounded informational line on stdout, then falls back to the
  default session (`build_default_session()`).

- Ctrl-C inside the curses wrapper still exits cleanly via the
  documented KeyboardInterrupt path; pressing Ctrl-C mid-save is
  caught by the BaseException branch of save_session's transaction
  envelope, which rolls back before re-raising.
```

## 6. Catalog rows exercised

```text
Persistent Session Store (Phase 3.9):
  I-PERSIST-01..09  REQUIRED + STRUCTURAL  (drained Step 8-10)
  I-PERSIST-10..14  STRUCTURAL              (drained Step 8-9)
  I-PERSIST-15      OBSERVED               (this walk's primary target)
  I-PERSIST-16      NOT-EXERCISED          (autosave; statically enforced)

Indirectly exercised:
  I-UI-03 / I-UI-05 / I-UI-06 / I-UI-10 / I-UI-13       (Operator TUI)
  I-UISTRM-01..15                                       (Phase 3.8)
  I-STRM-01..15                                         (Phase 3.7)
  I-MSI-01/02/03/04/05/06, I-PROF-01/02, I-PTC-01..05   (kernel)
```

## 7. Reproducibility

The walk in section 3 is deterministic across runs:

```text
- build_default_session() always produces the same profile / MSI /
  PtCns / registry shape (cogito + alpha with rho 3/4).
- /stream uses OperatorSession.stream_chunk_serial, which starts at
  0 and increments deterministically. Successive chunks are named
  'strm-chunk-1', 'strm-chunk-2', etc.
- /stream-promote uses the deterministic 'promo-<chunk_id>' naming
  the Phase 3.7 substrate produces.
- /step calls tick() with the OfflineStandInClient which always
  returns "PRESERVE"; the resulting MSI grows by one content
  ('strm-strm-chunk-1') under MODE_C.
- /save-session writes a fresh transactional snapshot, overwriting
  any previous rows. created_at / updated_at differ across runs
  (they are real-clock timestamps), but every kernel-numeric and
  identifier column round-trips exactly.
- /load-session in a second process restores the same field-for-
  field state. The diagnostic timestamps are preserved (created_at
  from the original save; updated_at from the most recent save).
```

## 8. Conclusion

End-to-end cold-start continuity is operational, deterministic, and
audit-clean. `--session-db` configures the SQLite path;
`--load-session` restores prior state before the TUI opens;
`/save-session` and `/load-session` are explicit operator commands
that route through the existing typed parser and dispatcher chain;
neither command calls `tick()`. The persistence layer preserves
exact `Fraction` round-trip, the `COGITO_ID` reservation, and the
resource-free `OperatorSession` shape; failed save / failed load
preserve the live session.

The recommended next step is `PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md`
(Step 12), then the final PR (Step 13).
