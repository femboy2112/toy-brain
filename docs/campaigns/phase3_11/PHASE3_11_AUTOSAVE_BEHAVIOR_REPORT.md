# PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 15: autosave behavior tests for the
Phase 3.11 comprehensive live behavior campaign.

Source: CURRENT_CAMPAIGN.md Step 15

Required artifact:

```text
PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
```

This is a report-only step. It does not edit runtime code, fixtures,
catalog rows, mission/campaign routing prose, or prior phase audits.
The mission/campaign baseline still contains stale "next eligible step:
Step 13" prose; the committed Step 13 and Step 14 reports, branch head,
preflight diagnostics, and user instruction identify Step 15 as current.
That stale baseline is left unchanged here because campaign-level
document refresh is deferred until a complete step boundary.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 15
Prior step evidence: 2b32eae phase3.11 step14: persistence behavior report
Required Step 15 report before execution: absent
```

Preflight:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
bash tools/check_all.sh               PASS (All checks passed)
brain_campaign_state                  READY: Step 15
brain_catalog_lint                    PASS catalog/counts; stale Step 13 routing prose noted
brain_diff_guardian                   PASS clean worktree/index on campaign branch
brain_parallel_planner                DAG produced; report-only write scope
```

## Test Method

The live behavior test used fresh current-branch observations rather
than relying on the Phase 3.10c dry run.

Temporary helper:

```text
/tmp/phase3_11_autosave_step15/run_autosave_observations.py
```

Helper policy:

```text
deterministic local Python stdlib helper
no network
no real LLM calls
no repo writes
SQLite files only under /tmp/phase3_11_autosave_*
temporary DB directory removed after successful observation run
```

Primary scripted state test:

```text
temporary DB: /tmp/phase3_11_autosave_b7x_exb3/session.sqlite3
client: OfflineStandInClient
commands:
  python3 -m brain.ui --print-once
  python3 -m brain.ui --autosave-mode after-successful-mutation
  /autosave-enable after-successful-mutation
  /autosave-status
  /stream phase3 step15 autosave payload
  /stream-promote promo-strm-chunk-1
  /step
  /state
  /step
  /autosave-disable
  /stream phase3 step15 disabled payload
  /stream-promote promo-strm-chunk-2
  /step
```

Failure injection:

```text
temporary DB: /tmp/phase3_11_autosave_b7x_exb3/injected.sqlite3
method: monkeypatch brain.ui.autosave.save_session inside the helper
trigger: maybe_autosave_after_mutation(..., triggered_by=STREAM_PROMOTE)
purpose: verify PersistenceError absorption without depending on host
         filesystem permission behavior
```

The helper removed `/tmp/phase3_11_autosave_b7x_exb3` before this report
was written.

## Observation Table

| ID | Type | Automation | Observation | Verdict |
| --- | --- | --- | --- | --- |
| 15.autosave-default.1 | SST | yes | `python3 -m brain.ui --print-once` exited 0 and rendered the default operator frame at `tick=0`, `queue=0`, profile domain size 2. The frame does not print the startup autosave line because `--print-once` short-circuits before normal session launch. | works |
| 15.autosave-default.2 | SST | yes | A cold `build_default_session()` had `autosave_config=None`, `last_autosave_status=None`, and `autosave_status(session)` reported `mode=off`, empty DB path, no last attempt, and no error. | works |
| 15.autosave-enable.1 | SST | yes | With `session.session_store_config` pointing at `/tmp/.../session.sqlite3`, `/autosave-enable after-successful-mutation` returned `autosave-enable ok: mode=after-successful-mutation db='...'`; no save fired at enable time. | works |
| 15.autosave-status.1 | SST | yes | `/autosave-status` reported `mode=after-successful-mutation`, the configured DB path, `last_tick=0`, empty `last_outcome`, empty trigger, and empty timestamp. | works |
| 15.autosave-stream-promote.1 | SST | yes | After `/stream`, the DB did not exist. `/stream-promote promo-strm-chunk-1` queued one event and triggered autosave with `last_attempt_outcome=ok`, `last_attempt_trigger=stream_promote`, `last_attempt_tick=0`; the DB then existed with one chunk and one candidate. | works |
| 15.autosave-step.1 | SST | yes | `/step` consumed the queued event, advanced to `tick=1`, triggered autosave with `last_attempt_outcome=ok`, `last_attempt_trigger=step_tick`, `last_attempt_tick=1`, and changed the DB hash. Reloaded DB state had `tick_counter=1`, queue size 0, and `db_diff(...).matches=True`. | works |
| 15.autosave-read-only.1 | SST | yes | `/state` with autosave enabled changed only the operator view/status. The DB hash, byte size, saved profile rows, saved stream chunks, saved candidates, and autosave status stayed unchanged. | works |
| 15.autosave-failed.1 | SST | yes | A second `/step` against an empty queue set error `STEP_TICK with empty event queue`. The DB hash and autosave status stayed unchanged from the prior successful `/step`; no autosave fired after the failed dispatch. | works |
| 15.autosave-toggle.2 | SST | yes | `/autosave-disable` returned `autosave-disable ok: mode=off` while preserving the previous last-attempt history. A later successful `/stream`, `/stream-promote`, `/step` advanced the live tick to 2 but left the DB hash unchanged. | works |
| 15.failure-autosave-db.1 | SST | yes | `python3 -m brain.ui --autosave-mode after-successful-mutation` without `--session-db` exited 2 through argparse and printed `--autosave-mode after-successful-mutation requires --session-db`; no session launched. | works |
| 15.failure-injection.1 | SST | yes | Monkeypatching `brain.ui.autosave.save_session` to raise `PersistenceError("injected autosave failure for Step 15")` produced an `AutosaveStatusReport` with `last_attempt_outcome=error`, `last_attempt_trigger=stream_promote`, bounded error text, `tick=0`, `queue=0`, and no DB file created. | works |
| 15.ux-autosave.1 | MOT | env | Autosave status text distinguishes disabled (`mode=off`), enabled (`mode=after-successful-mutation` with DB path), success (`last_outcome=ok` with trigger/tick), and error (`last_outcome=error` with bounded message). The text is terse but readable. | works |

## Raw Evidence Summary

### Default Off

```text
python3 -m brain.ui --print-once:
  exit=0
  first line: toy-brain operator . view=state . tick=0 . queue=0
  autosave startup line present: false
```

`--print-once` remains useful as a launch-smoke row, but it is not a
startup-line test: it returns before normal LLM/autosave/session startup
messages. The in-process cold session check supplied the direct default
autosave evidence:

```text
autosave_config=None
last_autosave_status=None
autosave_status:
  mode=off
  db_path_str=""
  last_attempt_tick=0
  last_attempt_outcome=""
  last_attempt_trigger=""
  last_error_text=""
```

### Enable And Status

```text
/autosave-enable after-successful-mutation:
  status=autosave-enable ok: mode=after-successful-mutation db='/tmp/.../session.sqlite3'
  tick=0
  queue=0
  chunks=0
  candidates=0
  last_attempt_outcome=""

/autosave-status:
  status=autosave-status: mode=after-successful-mutation db='/tmp/.../session.sqlite3' last_tick=0 last_outcome='' last_trigger='' last_at=''
```

### Stream Promote Autosave

```text
before /stream-promote:
  db_exists=False

/stream phase3 step15 autosave payload:
  status=stream chunk 'strm-chunk-1' appended (history size = 1)
  last_attempt_outcome=""

/stream-promote promo-strm-chunk-1:
  status=promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)
  last_attempt_outcome=ok
  last_attempt_trigger=stream_promote
  last_attempt_tick=0

after /stream-promote DB:
  exists=True
  bytes=73728
  profile_rows=2
  stream_chunks=1
  stream_candidates=1
  db_diff.matches=True
```

### Step Autosave

```text
before /step DB:
  sha256=d7ee8337bd2fee11c277a0cebffd4c83c1007bacf6d4a7e2dab184e641e6a126
  profile_rows=2
  stream_chunks=1
  stream_candidates=1

/step:
  status=tick 1 ok (MODE_C)
  tick=1
  queue=0
  last_attempt_outcome=ok
  last_attempt_trigger=step_tick
  last_attempt_tick=1

after /step DB:
  sha256=0455d146192d9b90b91913c0a56eb73098a6ea99c38d3bf9eec46fda50875967
  profile_rows=3
  stream_chunks=1
  stream_candidates=1
  loaded_tick=1
  loaded_queue=0
  db_diff.matches=True
```

### Read-Only No-Save

```text
/state:
  status=view = state
  tick=1
  queue=0
  last_attempt_outcome=ok
  last_attempt_trigger=step_tick

before/after DB:
  sha256 unchanged
  byte_size unchanged
  profile_rows unchanged
  stream_chunks unchanged
  stream_candidates unchanged
```

### Failed Dispatch No-Save

```text
/step with empty queue:
  error=STEP_TICK with empty event queue
  tick=1
  queue=0

before/after DB:
  sha256 unchanged
  byte_size unchanged
  profile_rows unchanged
  stream_chunks unchanged
  stream_candidates unchanged

last autosave before/after:
  last_attempt_outcome=ok
  last_attempt_trigger=step_tick
  last_attempt_tick=1
  unchanged=True
```

### Disable

```text
/autosave-disable:
  status=autosave-disable ok: mode=off
  mode=off
  last_attempt history preserved from prior successful /step

after disable:
  /stream phase3 step15 disabled payload
  /stream-promote promo-strm-chunk-2
  /step
  live tick advanced to 2
  DB sha256 unchanged
```

### Failure Injection

```text
injected save_session failure:
  last_attempt_outcome=error
  last_attempt_trigger=stream_promote
  last_attempt_tick=0
  last_error_text=injected autosave failure for Step 15
  tick=0
  queue=0
  db_exists=False
```

This injection tests the local `maybe_autosave_after_mutation` failure
contract. It is not a real host-permission failure; the normal live
dispatch observations above are separate from this injected path.

## Findings

- Default autosave is off on cold in-process sessions.
- `--print-once` is independent of autosave startup wiring and does not
  print the autosave startup line; use in-process/default config checks
  or normal TTY launch for autosave startup-line evidence.
- Non-off autosave requires a configured `--session-db` and fails before
  launch when omitted.
- `/autosave-enable after-successful-mutation` enables autosave without
  immediately saving.
- `/stream-promote` and `/step` each trigger one autosave after
  successful mutation.
- Read-only `/state` does not autosave.
- Failed `/step` with an empty queue does not autosave.
- `/autosave-disable` stops subsequent successful mutations from saving
  while preserving the last-attempt history for operator inspection.
- Injected `PersistenceError` is absorbed into a typed autosave status
  report instead of raising through dispatch.

No Step 15 observation produced a gating failure. No behavior was
patched.

## Validation

Post-report validation:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

Scope guard after validation:

```text
git status --short                    only PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
git diff --name-only                  no tracked source/catalog/mission diff
temporary DB/helper state             DB temp dir removed; helper remains only under /tmp
```

## Next

The next campaign step after this report is Step 16:

```text
PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
```
