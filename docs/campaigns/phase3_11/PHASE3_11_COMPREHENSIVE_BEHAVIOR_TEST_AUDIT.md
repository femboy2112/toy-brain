# PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_AUDIT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 22: final comprehensive behavior
audit for the Phase 3.11 live behavior campaign.

This audit consolidates the accepted Codex CLI runtime option work and
the live behavior reports from Steps 13-19. It is an audit artifact. It
does not edit source code, fixtures, catalog rows, mission/campaign
routing prose, runtime logic, persistence, autosave, traces, or
scenarios.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 22
Prior step evidence: afa9111 phase3.11 step19: bug ux triage plan
Step 20 gate result: no critical correctness or safety/invariant patch proposed
Step 21 status: skipped; no accepted critical fix to apply
```

`CURRENT_MISSION.md` and `CURRENT_CAMPAIGN.md` still contain stale
baseline prose saying the next eligible step is Step 13. The committed
branch history and Phase 3.11 reports show Steps 13-19 complete. Step
19 records the stale prose as a documentation follow-up, not a blocking
runtime or catalog issue.

## Evidence Set

Primary Phase 3.11 behavior evidence:

```text
PHASE3_11_OFFLINE_INTERACTION_REPORT.md
PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
PHASE3_11_BEHAVIOR_FINDINGS.md
PHASE3_11_BUG_UX_TRIAGE_PLAN.md
```

The aggregated Step 18 verdict counts are:

| Verdict | Count |
| --- | ---: |
| works | 56 |
| awkward | 2 |
| confusing | 0 |
| fails | 0 |
| missing | 0 |
| blocked by env | 0 |
| ORS skipped | 3 |

Step 19 triage classified the findings as:

| Triage bucket | Count |
| --- | ---: |
| critical correctness | 0 |
| safety/invariant | 0 |
| operator UX | 1 |
| documentation | 2 |
| deferred enhancement | 1 |

## Codex CLI Option Status

`codex-cli` is implemented as an explicit LLM runtime option.

Current accepted LLM runtime modes:

```text
offline
mock
anthropic-api
claude-cli
codex-cli
```

Audit status:

```text
default remains offline                         PASS
codex-cli requires explicit opt-in              PASS
missing codex executable fails before curses    PASS
standard gates require no real Codex access     PASS
real Codex CLI smoke remains OBSERVED/manual    PASS
tick seam remains the runtime route             PASS
```

Step 17 observed `codex` on this machine at `/usr/local/bin/codex`, but
did not invoke a real external Codex CLI smoke because the live test
campaign kept real external model calls OBSERVED/manual by default.

## Launch Behavior

Launch behavior passed the deterministic and environment-sensitive
checks.

Observed:

```text
python3 -m brain.ui --print-once       rendered the operator frame
python3 -m brain.ui --check-terminal   returned bounded non-TTY / PTY status
python3 -m brain.ui                    launched in a usable PTY
/quit                                  exited the curses session with code 0
```

`--print-once` renders a deterministic agent layout at `tick=0` and
`queue=0`. `--check-terminal` correctly reports non-TTY capture as
unusable and a usable PTY as usable. The real PTY launch printed the
offline LLM line, autosave-off line, no-session-DB line, and then
rendered the operator layout.

## Offline Interaction Behavior

Offline operator behavior passed.

The Step 13 in-process walk exercised:

```text
/help
/stream
/stream-summary
/stream-candidates
/stream-promote
/step
/state
```

Observed behavior:

```text
/stream             appends a stream chunk and candidate without calling tick()
/stream-summary     read-only view change
/stream-candidates  read-only view change
/stream-promote     queues exactly one promotion candidate
/step               consumes the queued event, advances tick, calls offline client once
/state              read-only state inspection after the tick
```

No offline interaction row failed, and no behavior was patched during
the report-only step.

## Persistence Behavior

Persistence and cold-start behavior passed.

Step 14 observed:

```text
/save-session                         saved tick/profile/stream state to SQLite
direct load_session(config)            reconstructed the saved session
in-process /load-session               restored saved state into a cold live session
PTY --session-db ... --load-session     loaded before TUI display
missing DB /load-session               reported bounded error and preserved live state
```

The saved kernel state and tick counter restore correctly. `latest_tick`
is intentionally not persisted or reconstructed; a loaded session starts
with saved kernel/profile/stream state and display view `state`.

## Autosave Behavior

Autosave behavior passed.

Step 15 observed:

```text
cold session default                   autosave_config=None, mode=off
non-off CLI without --session-db        argparse exit 2 before launch
/autosave-enable                       enables after-successful-mutation without saving
/autosave-status                       reports bounded mode/DB/last-attempt state
/stream-promote                        triggers autosave after successful mutation
/step                                  triggers autosave after successful mutation
/state                                 read-only; no autosave trigger
failed /step                           no autosave trigger
/autosave-disable                      stops later successful mutations from saving
injected PersistenceError              absorbed into AutosaveStatusReport
```

No hidden autosave behavior, background trigger, or second save path was
observed.

## DB Observability And Backup

DB observability behavior passed, with one documentation wording
finding.

Step 16 observed:

```text
/db-status                 works against a real saved DB
/db-verify                 verifies without activating saved state
/db-summary                reports bounded row counts
/profile-summary           reports exact Fraction values
/stream-db-summary         reports bounded head/tail stream rows
/db-diff                   reports live-vs-saved match
--db-status                one-shot short-circuit works
--db-verify                one-shot short-circuit works
--db-backup                one-shot short-circuit works
backup overwrite refusal   works without force
backup force overwrite     works with explicit force
URI destination rejection  works at parse time
```

Backup preserved the source DB hash and reported successful page-copy
completion, but the backup file hash differed from the source file hash
while retaining the same size. The behavior is best described as a
SQLite backup API copy / source-preserving logical backup. The earlier
matrix phrase "byte-faithful SQLite backup" overstates the observed
file-hash property and should be corrected at a later documentation
refresh boundary.

The only operator UX issue recorded in this area is low severity:
forbidden URI parse rejection can leave the previous success status
visible because parsing fails before dispatch.

## LLM Runtime Behavior

Deterministic LLM runtime behavior passed.

Step 17 observed:

```text
offline --print-once                       renders deterministically
mock --print-once                          renders deterministically
anthropic-api without key                  fails closed before curses
claude-cli with forced missing executable  fails closed before curses
codex-cli with forced missing executable   fails closed before curses
model-backed cache config                  accepted without making a request
offline/mock cache config                  rejected with bounded error
--print-once across accepted modes         returns before backend construction
```

Real external smokes were intentionally skipped:

```text
anthropic-api ORS  skipped; no accepted/configured API key
claude-cli ORS     skipped; executable found, no external model command invoked
codex-cli ORS      skipped; executable found, no external model command invoked
```

The audit therefore certifies deterministic runtime selection and
fail-closed behavior, not successful real model responses from external
services.

## Critical Fixes

No critical correctness fixes were applied.

Step 19 found:

```text
critical correctness: 0
safety/invariant:     0
```

Step 20 therefore did not require a code-fix stop. Step 21 is skipped
because no critical correctness or safety/invariant patch was proposed
or accepted.

## Full Gate

Step 22 validation:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

`tools/check_all.sh` refreshed `brain/_catalog_ids.py` with the current
v0.20 generated IDs and left no tracked source/catalog diff outside this
audit artifact.

## Audit Verdict

```text
Phase 3.11 Comprehensive Live Behavior Test: PASS
```

The repository now contains a grounded behavior record for launch,
offline operator interaction, persistence, autosave, DB
observability/backup, and deterministic LLM runtime selection. No
critical correctness or safety/invariant patch was identified by the
live behavior campaign.

## Recommended Next Mission

Recommended next work:

```text
Step 23: open the final Phase 3.11 PR into main.
```

Deferred follow-ups to carry into the PR body or a later campaign:

```text
1. Optional operator-approved real ORS smoke for anthropic-api, claude-cli, and codex-cli.
2. Documentation wording refresh for SQLite backup API semantics.
3. Mission/campaign baseline prose refresh so current routing text no longer says Step 13.
4. Optional UX cleanup for stale status display after parser rejection.
```

None of these deferred items is a blocker for the Step 22 audit verdict.
