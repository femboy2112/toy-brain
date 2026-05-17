# PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 14: persistence and cold-start
behavior tests for the Phase 3.11 comprehensive live behavior campaign.

Source: CURRENT_CAMPAIGN.md Step 14

Required artifact:

```text
PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
```

This is a report-only step. It does not edit runtime code, fixtures,
catalog rows, mission/campaign routing prose, or prior phase audits.
The mission/campaign baseline still contains stale "next eligible step:
Step 13" prose; the committed Step 13 report, branch head, and user
instruction identify Step 14 as current. That stale baseline is left
unchanged here because campaign-level document refresh is deferred until
campaign completion.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 14
Prior step evidence: ff812d7 phase3.11 step13: offline interaction report
Required Step 14 report before execution: absent
```

Preflight:

```text
python3 -m tools.catalog counts       PASS
brain_campaign_state                  READY: Step 14
brain_catalog_lint                    PASS catalog/counts; stale Step 13 routing prose noted
brain_diff_guardian                   PASS clean worktree/index on campaign branch
brain_parallel_planner                DAG produced; report-only write scope
```

## Test Method

The live behavior test used fresh current-branch observations rather
than relying on the Phase 3.9 dry run.

Primary scripted state test:

```text
temporary DB: /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3
client: OfflineStandInClient
commands:
  /session-status
  /stream phase3 step14 persistence payload
  /stream-promote promo-strm-chunk-1
  /step
  /save-session
  direct load_session(config)
  /load-session into a cold live OperatorSession
```

Cold-start operator launch test:

```text
python3 -m brain.ui --session-db /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3 --load-session
```

This was run in a real PTY and exited with `/quit`. `--print-once` was
not used for the cold-start load check because `brain.ui.__main__.main`
returns from the `--print-once` branch before session DB loading.

Failure preservation test:

```text
temporary missing DB: /tmp/toy-brain-step14-missing-yahsv83h/missing.sqlite3
command: /load-session
```

All temporary SQLite files stayed under `/tmp`.

## Observation Table

| ID | Type | Automation | Observation | Verdict |
| --- | --- | --- | --- | --- |
| 14.session-status.1 | SST | yes | Before mutation, `/session-status` returned `tick=0 queue=0 view=state chunks=0 candidates=0 db=configured`. The session had a configured DB path and no stream/tick state. | works |
| 14.save.1 | SST | yes | After `/stream`, `/stream-promote`, and `/step`, `/save-session` returned `saved session to /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3 (chunks=1, candidates=1)`. | works |
| 14.restore.direct.1 | SST | yes | Direct `load_session(config)` reconstructed a session with `tick_counter=1`, `stream_chunk_serial=1`, one stream chunk, one stream candidate, profile domain size 3, and `db_diff(...).matches=True`. | works |
| 14.restore.dispatch.1 | SST | yes | Dispatching `/load-session` into a fresh live `OperatorSession` returned `loaded session from /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3 (chunks=1, candidates=1)` and restored the saved tick/profile/stream state. | works |
| 14.cold-start.1 | MOT | env | Launching `python3 -m brain.ui --session-db ... --load-session` in a PTY printed the offline runtime line, autosave-off line, and `session db = ... (loaded; schema=v1; catalog=v0.17; chunks=1; candidates=1)`, then rendered the operator layout at `tick=1` with profile domain size 3. `/quit` exited with code 0. | works |
| 14.failure-load.1 | SST | yes | Loading a missing DB surfaced bounded local error text, `/load-session failed: session DB path ... does not exist`, and left the in-memory status snapshot unchanged. | works |

## Raw Evidence Summary

### Save and Restore Walk

```text
initial:
  tick_counter=0
  queue_size=0
  active_view=state
  stream_chunk_count=0
  stream_candidate_count=0
  stream_chunk_serial=0
  session_db_configured=True

/stream phase3 step14 persistence payload:
  stream chunk 'strm-chunk-1' appended (history size = 1)

/stream-promote promo-strm-chunk-1:
  promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)

/step:
  tick 1 ok (MODE_C)

/save-session:
  saved session to /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3 (chunks=1, candidates=1)

after save:
  tick_counter=1
  queue_size=0
  active_view=tick
  has_latest_tick=True
  stream_chunk_count=1
  stream_candidate_count=1
  stream_chunk_serial=1
```

### DB Readback

```text
db-status:
  exists=True
  schema_version=1
  catalog_version=v0.17
  byte_size=73728
  error_text=""

db-verify:
  passed=True
  loaded_chunks=1
  loaded_candidates=1
  rebuilt_candidates=False
  error_text=""

profile-summary:
  __cogito__ = 1/1
  alpha = 3/4
  strm-strm-chunk-1 = 1/2

stream-db-summary:
  chunk_count=1
  candidate_count=1
  first_ordinal=1
  last_ordinal=1
  chunk_id=strm-chunk-1
  source=OPERATOR
  tick_at_event=0
  text_preview=phase3 step14 persistence payload

db-diff after save:
  matches=True
  diff_count=0
```

### Direct Load

```text
LoadSessionResult:
  schema_version=1
  catalog_version=v0.17
  loaded_chunks=1
  loaded_candidates=1
  rebuilt_candidates=False

loaded session status:
  tick_counter=1
  queue_size=0
  active_view=state
  has_latest_tick=False
  stream_chunk_count=1
  stream_candidate_count=1
  stream_chunk_serial=1
  session_db_configured=True

loaded db-diff:
  matches=True
  diff_count=0
```

`latest_tick` is not persisted or reconstructed; the saved kernel state
and tick counter are restored, while the live operator display starts on
`active_view=state`.

### Dispatch Load Into Cold Live Session

```text
before /load-session:
  tick_counter=0
  stream_chunk_count=0
  stream_candidate_count=0
  stream_chunk_serial=0

/load-session:
  loaded session from /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3 (chunks=1, candidates=1)

after /load-session:
  tick_counter=1
  stream_chunk_count=1
  stream_candidate_count=1
  stream_chunk_serial=1
  db-diff.matches=True
```

### Cold-Start PTY Launch

```text
brain.ui: llm runtime mode = offline (default offline stand-in; no network, no shell)
brain.ui: autosave mode = off
brain.ui: session db = /tmp/toy-brain-step14-iw0jjxpa/session.sqlite3 (loaded; schema=v1; catalog=v0.17; chunks=1; candidates=1)
toy-brain operator . view=state . tick=1 . queue=0
profile domain size : 3
__cogito__ = 1
alpha = 3/4
strm-strm-chunk-1 = 1/2
```

The raw PTY transcript contains normal alternate-screen ANSI escape
sequences. `/quit` exited with process exit 0.

### Missing DB Failure

```text
before:
  tick_counter=0
  queue_size=0
  active_view=state
  stream_chunk_count=0
  stream_candidate_count=0
  stream_chunk_serial=0

error:
  /load-session failed: session DB path /tmp/toy-brain-step14-missing-yahsv83h/missing.sqlite3 does not exist

after:
  tick_counter=0
  queue_size=0
  active_view=state
  stream_chunk_count=0
  stream_candidate_count=0
  stream_chunk_serial=0

preserved:
  True
```

## Findings

- Explicit `/save-session` saves the live stream/tick state to the
  configured SQLite DB.
- Direct `load_session(config)` reconstructs through the persistence
  layer and produces a DB-equivalent session under `db_diff`.
- Dispatching `/load-session` into a cold live session restores the
  saved kernel/profile/stream/tick counters while preserving live
  operator-surface fields such as `active_view`.
- Cold-start `--session-db ... --load-session` works in a real PTY and
  renders the restored profile at `tick=1`.
- Failed load from a missing DB is bounded local UI error text and does
  not mutate the in-memory session.
- `--print-once` is not a persistence cold-start test surface because
  it returns before session DB loading. Use PTY launch or in-process
  `load_session` for Step 14 evidence.

No Step 14 observation produced a gating failure. No behavior was
patched.

## Validation

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

Scope guard after validation:

```text
git status --short                    only PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
git diff --name-only                  no tracked source/catalog/mission diff
```

## Next

The next campaign step after this report is Step 15:

```text
PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
```
