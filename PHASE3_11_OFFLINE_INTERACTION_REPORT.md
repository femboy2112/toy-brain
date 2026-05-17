# PHASE3_11_OFFLINE_INTERACTION_REPORT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 13: launch, offline, and basic
interaction observations for the Phase 3.11 live behavior campaign.

```text
Status: COMPLETE / REPORT-ONLY / NO-IMPLEMENTATION
Source: CURRENT_CAMPAIGN.md Step 13
Matrix: PHASE3_11_LIVE_TEST_MATRIX.md
Discipline: PHASE3_11_LIVE_TEST_KICKOFF.md + PHASE3_11_LIVE_TEST_CORRIGENDA.md
```

This report records actual behavior only. It does not edit source code,
fixtures, catalog rows, runtime logic, persistence, autosave, traces, or
scenarios.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 13
Step artifact before execution: PHASE3_11_OFFLINE_INTERACTION_REPORT.md absent
```

Pre-step gates and diagnostics were green:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (gate failures: 0)
bash tools/check_all.sh               PASS
brain_campaign_state                  READY
brain_catalog_lint                    READY
brain_diff_guardian                   PASS
```

## Helper

A temporary helper was created outside the repository:

```text
/tmp/phase3_11_step13_observe.py
```

It performed only local, deterministic observations:

```text
no network
no real LLM calls
no repo writes
no DB writes
offline client only for /step
stdout-only JSON/markdown observations
```

The helper reduced repeated manual parse/dispatch observation across:

```text
/help
/stream
/stream-summary
/stream-candidates
/stream-promote
/step
/state
```

## Observation Table

| ID | Style | Gate | Observation | Verdict |
|----|-------|------|-------------|---------|
| 13.print-once.1 | SST | yes | `python3 -m brain.ui --print-once` exited 0. It rendered the agent layout with `view=state`, `tick=0`, `queue=0`, the core profile, transcript area, composer, and key help. | works |
| 13.check-terminal.1 | SST | yes | Captured non-TTY shell returned exit 1 with `usable=False, reason=stdout is not attached to a terminal`. A tool-provided PTY returned exit 0 with `usable=True, reason=TERM=xterm-256color`. Both outcomes match the environment-dependent contract. | works |
| 13.launch.1 | MOT | env | In a usable PTY, `python3 -m brain.ui` printed startup lines for offline LLM mode, autosave off, and no configured session DB, then rendered the curses operator layout. | works |
| 13.help.1 | RFI | yes | Source inspection confirms `brain/ui/command_line.py` contains the closed command verb list and handlers for `help`, `stream`, and `stream-promote`; `brain/ui/commands.py` defines `OperatorCommand.HELP`, `STREAM_APPEND`, and `STREAM_PROMOTE`; `brain/ui/session.py` dispatches HELP, STREAM_APPEND, STREAM_PROMOTE, and STEP_TICK through the typed route. | works |
| 13.help.2 | SST | yes | In-process `/help` parsed as `help`, set `active_view=help`, set status to `help`, left error empty, kept `queue_size=0`, `stream_chunks=0`, and `tick_counter=0`. | works |
| 13.quit.1 | MOT | env | In the same usable PTY launch, sending `/quit` through the composer exited the curses session with process exit 0. Raw terminal output contained normal alternate-screen ANSI escape sequences. | works |
| 13.stream.1 | SST | yes | In-process `/stream phase3 step13 offline observation` parsed as `stream_append`, appended `strm-chunk-1`, created candidate `promo-strm-chunk-1`, set `active_view=stream_summary`, left queue size 0, and did not call the offline client. | works |
| 13.stream-summary.1 | SST | yes | `/stream-summary` set `active_view=stream_summary`, status `view = stream_summary`, retained one stream chunk and one candidate, left queue size 0, and did not call the offline client. | works |
| 13.stream-candidates.1 | SST | yes | `/stream-candidates` set `active_view=stream_candidates`, status `view = stream_candidates`, retained candidate `promo-strm-chunk-1`, and did not mutate queue or tick state. | works |
| 13.stream-promote.1 | SST | yes | `/stream-promote promo-strm-chunk-1` parsed as `stream_promote`, set `active_view=queue`, status `promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)`, and increased queue size to 1. | works |
| 13.step.1 | SST | yes | `/step` with `OfflineStandInClient` parsed as `step_tick`, consumed the queued event, set `active_view=tick`, status `tick 1 ok (MODE_C)`, advanced `tick_counter` from 0 to 1, reduced queue size to 0, and called the offline client once. | works |
| 13.state.1 | SST | yes | `/state` parsed as `inspect_state`, set `active_view=state`, status `view = state`, preserved `tick_counter=1`, `queue_size=0`, one stream chunk, and the candidate record. | works |
| 13.failure-terminal.1 | SST | yes | The captured non-TTY `--check-terminal` path returned exit 1 with a bounded reason string. This is the expected non-TTY result, not a campaign failure. | works |
| 13.ux-print-once.1 | MOT | env | Default `--print-once` output is readable in this shell: header, core state, latest tick, transcript, composer, mode, cursor, history, and key hints are all visible. | works |
| 13.ux-stream.1 | MOT | env | Stream and promotion statuses are terse but intelligible: chunk ID, candidate ID, queue size, tick result, and active views are visible without reading source. | works |

## Raw Evidence Summary

### Exact Launch Commands

```text
python3 -m brain.ui --print-once
exit: 0
observed: toy-brain operator frame with view=state, tick=0, queue=0
```

```text
python3 -m brain.ui --check-terminal
exit: 1 in captured non-TTY shell
observed: usable=False, reason=stdout is not attached to a terminal
```

```text
python3 -m brain.ui --check-terminal   # tool-provided PTY
exit: 0
observed: usable=True, reason=TERM=xterm-256color
```

```text
python3 -m brain.ui                    # tool-provided PTY
then /quit
exit: 0
observed: offline startup lines, curses layout, composer accepted /quit
```

### In-Process Command Sequence

```text
/help
  kind=help
  active_view=help
  status=help
  error=
  queue=0 ticks=0 chunks=0 candidates=[] offline_calls=0

/stream phase3 step13 offline observation
  kind=stream_append
  active_view=stream_summary
  status=stream chunk 'strm-chunk-1' appended (history size = 1)
  error=
  queue=0 ticks=0 chunks=1 candidates=[promo-strm-chunk-1] offline_calls=0

/stream-summary
  kind=inspect_stream_summary
  active_view=stream_summary
  status=view = stream_summary
  error=
  queue=0 ticks=0 chunks=1 candidates=[promo-strm-chunk-1] offline_calls=0

/stream-candidates
  kind=inspect_stream_candidates
  active_view=stream_candidates
  status=view = stream_candidates
  error=
  queue=0 ticks=0 chunks=1 candidates=[promo-strm-chunk-1] offline_calls=0

/stream-promote promo-strm-chunk-1
  kind=stream_promote
  active_view=queue
  status=promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)
  error=
  queue=1 ticks=0 chunks=1 candidates=[promo-strm-chunk-1] offline_calls=0

/step
  kind=step_tick
  active_view=tick
  status=tick 1 ok (MODE_C)
  error=
  queue=0 ticks=1 chunks=1 candidates=[promo-strm-chunk-1] offline_calls=1

/state
  kind=inspect_state
  active_view=state
  status=view = state
  error=
  queue=0 ticks=1 chunks=1 candidates=[promo-strm-chunk-1] offline_calls=1
```

## Findings

```text
works:         15
awkward:        0
confusing:      0
fails:          0
missing:        0
blocked by env: 0
ORS skipped:    0
```

No Step 13 observation produced a gating failure. No behavior was patched.

## Validation

Post-report validation:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

## Next

The next campaign step after this report is Step 14:

```text
PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
```
