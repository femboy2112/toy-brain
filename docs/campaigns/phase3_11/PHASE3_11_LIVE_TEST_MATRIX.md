# PHASE3_11_LIVE_TEST_MATRIX.md

## Purpose

Enumerate the Phase 3.11 live behavior observations that Steps 13-17
will execute and report. This is a planning artifact only. It does not
run live tests, edit source code, edit fixtures, change the catalog, or
create any temporary session database.

```text
Status: LOCKED / MATRIX / NO-IMPLEMENTATION
Source: CURRENT_CAMPAIGN.md Step 12
Discipline: PHASE3_11_LIVE_TEST_KICKOFF.md + PHASE3_11_LIVE_TEST_CORRIGENDA.md
```

The later behavior reports fill the `Expected`, `Observed`, and
`Verdict` cells. Verdicts must use only the locked vocabulary:

```text
works
awkward
confusing
fails
missing
blocked by env
ORS skipped
```

---

## Matrix Rules

```text
Styles:
  SST  scripted subprocess or in-process dispatch test
  MOT  manual observed TTY/curses test
  RFI  read-only file inspection
  ORS  optional real-LLM smoke

Gating:
  yes       row must be attempted and reported; campaign gates remain
            catalog counts, citation verifier, import audit, invariant
            runner, and check_all.sh
  no        row is OBSERVED-only and cannot fail the campaign
  env       environment-dependent row; absence is recorded, not failed

Temporary DB policy:
  Steps 14-16 use /tmp/phase3_11_<step_name>_<utc_nanos>/<file>.db
  No DB path is committed.
  Cleanup follows PHASE3_11_LIVE_TEST_CORRIGENDA.md Section 5.
```

The matrix intentionally separates the operator-facing observation IDs
from catalog IDs. These IDs describe behavior observations, not
invariant rows.

---

## Launch Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 13.print-once.1 | 13 | SST | yes | `python3 -m brain.ui --print-once` | Render one deterministic agent frame and exit 0. |  |  |  |
| 13.check-terminal.1 | 13 | SST | yes | `python3 -m brain.ui --check-terminal` | Print bounded terminal usability reason; exit 0 on usable TTY, 1 on non-TTY. |  |  |  |
| 13.launch.1 | 13 | MOT | env | `python3 -m brain.ui` | Full curses launch is observed manually when a usable TTY is available. |  |  |  |
| 13.help.1 | 13 | RFI | yes | `brain/ui/command_line.py`, `brain/ui/commands.py`, `brain/ui/session.py` | Help and command coverage are inspectable without executing a curses session. |  |  |  |
| 13.help.2 | 13 | SST | yes | `/help` through `LocalCommandLine.parse` + `OperatorSession.dispatch` | Help command dispatches locally without kernel mutation. |  |  |  |
| 13.quit.1 | 13 | MOT | env | `/quit` inside curses TUI | Quit exits a live TTY session without kernel mutation. |  |  |  |

---

## Offline Interaction Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 13.stream.1 | 13 | SST | yes | `/stream <text>` in-process | Appends one bounded stream chunk and creates a promotion candidate without calling `tick()`. |  |  |  |
| 13.stream-summary.1 | 13 | SST | yes | `/stream-summary` in-process | Shows bounded stream history summary. |  |  |  |
| 13.stream-candidates.1 | 13 | SST | yes | `/stream-candidates` in-process | Shows bounded promotion-candidate summary. |  |  |  |
| 13.stream-promote.1 | 13 | SST | yes | `/stream-promote <candidate_id>` in-process | Promotes a stream candidate into the event queue. |  |  |  |
| 13.step.1 | 13 | SST | yes | `/step` in-process with offline client | Advances one tick through the public `tick(..., client, ...)` route and mutates BrainState coherently. |  |  |  |
| 13.state.1 | 13 | SST | yes | `/state` in-process | Shows bounded BrainState snapshot after interaction. |  |  |  |

---

## Persistence Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 14.save-load.1 | 14 | SST | yes | `/save-session` with `/tmp/phase3_11_persistence_*/sess.db` | Saves BrainState plus session-local stream state to configured SQLite DB. |  |  |  |
| 14.save-load.2 | 14 | SST | yes | `/load-session` against the saved DB | Reconstructs through public builders and replaces live session only after invariant checks pass. |  |  |  |
| 14.session-status.1 | 14 | SST | yes | `/session-status` in-process | Reports bounded live session state without disk IO. |  |  |  |
| 14.cold-start.1 | 14 | SST | yes | `python3 -m brain.ui --session-db <tmp>/sess.db --load-session --print-once` | Fresh process can load the saved session before rendering a one-shot frame. |  |  |  |
| 14.restore.1 | 14 | SST | yes | saved vs loaded session inspection | Restored profile, stream state, and latest tick/session counters match the saved state. |  |  |  |

---

## Autosave Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 15.autosave-default.1 | 15 | SST | yes | `python3 -m brain.ui --print-once` | Default autosave mode is off. |  |  |  |
| 15.autosave-default.2 | 15 | SST | yes | in-process default `OperatorSession` | Cold-start session has no active autosave behavior. |  |  |  |
| 15.autosave-enable.1 | 15 | SST | yes | `--autosave-mode after-successful-mutation` with `--session-db <tmp>/sess.db` | Non-off autosave requires an explicit session DB. |  |  |  |
| 15.autosave-status.1 | 15 | SST | yes | `/autosave-status` in-process | Reports bounded autosave mode and last attempt status. |  |  |  |
| 15.autosave-toggle.1 | 15 | SST | yes | `/autosave-enable after-successful-mutation` | Enables autosave for the configured session DB. |  |  |  |
| 15.autosave-toggle.2 | 15 | SST | yes | `/autosave-disable` | Disables autosave idempotently. |  |  |  |
| 15.autosave-step.1 | 15 | SST | yes | `/step` with autosave enabled | Successful step mutation triggers a save after dispatch. |  |  |  |
| 15.autosave-stream-promote.1 | 15 | SST | yes | `/stream-promote <candidate_id>` with autosave enabled | Successful stream promotion triggers a save after dispatch. |  |  |  |
| 15.autosave-read-only.1 | 15 | SST | yes | read-only command with autosave enabled | Read-only dispatch does not autosave. |  |  |  |
| 15.autosave-failed.1 | 15 | SST | yes | failed dispatch with autosave enabled | Failed dispatch does not autosave and preserves live state. |  |  |  |

---

## DB Observability Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 16.db-status.1 | 16 | SST | yes | `/db-status` in-process | Reports bounded read-only DB status for configured session DB. |  |  |  |
| 16.db-status.2 | 16 | SST | yes | `python3 -m brain.ui --session-db <tmp>/sess.db --db-status` | One-shot DB status exits 0 for an existing saved DB. |  |  |  |
| 16.db-verify.1 | 16 | SST | yes | `/db-verify` in-process | Reconstructs candidate, runs invariants, drops candidate, and preserves live session. |  |  |  |
| 16.db-verify.2 | 16 | SST | yes | `python3 -m brain.ui --session-db <tmp>/sess.db --db-verify` | One-shot DB verify exits 0 for a valid saved DB. |  |  |  |
| 16.db-summary.1 | 16 | SST | yes | `/db-summary` in-process | Reports bounded row counts and metadata. |  |  |  |
| 16.profile-summary.1 | 16 | SST | yes | `/profile-summary` in-process | Reports COGITO-first exact Fraction profile rows. |  |  |  |
| 16.stream-db-summary.1 | 16 | SST | yes | `/stream-db-summary` in-process | Reports bounded stream chunk/candidate head-tail summary. |  |  |  |
| 16.db-diff.1 | 16 | SST | yes | `/db-diff` in-process | Compares live session with saved snapshot and reports finite-field diff. |  |  |  |

---

## Backup Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 16.db-backup.1 | 16 | SST | yes | `/db-backup <tmp>/sess.db.bak` in-process | Creates byte-faithful SQLite backup without mutating source DB. |  |  |  |
| 16.db-backup.2 | 16 | SST | yes | `python3 -m brain.ui --session-db <tmp>/sess.db --db-backup <tmp>/sess.db.bak` | One-shot backup exits 0 when destination does not exist. |  |  |  |
| 16.db-backup-force.1 | 16 | SST | yes | repeat `--db-backup` without `--db-backup-force` | Refuses overwrite and exits nonzero without corrupting existing backup. |  |  |  |
| 16.db-backup-force.2 | 16 | SST | yes | repeat `--db-backup` with `--db-backup-force` | Overwrites destination through explicit force flag. |  |  |  |
| 16.db-backup-uri.1 | 16 | SST | yes | `/db-backup file:/tmp/disallowed.db` or one-shot equivalent | Rejects URI-scheme backup destinations. |  |  |  |

---

## LLM Runtime Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 17.offline.1 | 17 | SST | yes | `python3 -m brain.ui --llm-mode offline --print-once` | Offline mode is explicit and print-once remains client-independent. |  |  |  |
| 17.mock.1 | 17 | SST | yes | `python3 -m brain.ui --llm-mode mock --llm-mock-response PRESERVE --print-once` | Mock mode accepts explicit canned response and print-once remains client-independent. |  |  |  |
| 17.anthropic-api.1 | 17 | SST | yes | `python3 -m brain.ui --llm-mode anthropic-api` without API key | Fails closed before launch with bounded API-key resolution error and no network call. |  |  |  |
| 17.anthropic-api.2 | 17 | ORS | no | `python3 -m brain.ui --llm-mode anthropic-api --llm-anthropic-api-key <key>` | Optional real API smoke only when credentials are explicitly available. |  |  |  |
| 17.claude-cli.1 | 17 | SST | yes | `python3 -m brain.ui --llm-mode claude-cli` with missing binary path forced if needed | Missing executable fails closed before launch with bounded `claude-cli` error. |  |  |  |
| 17.claude-cli.2 | 17 | ORS | no | `python3 -m brain.ui --llm-mode claude-cli` with real `claude` on PATH | Optional real Claude CLI smoke only when executable/auth are available. |  |  |  |
| 17.codex-cli.1 | 17 | SST | yes | `python3 -m brain.ui --llm-mode codex-cli` with missing binary path forced if needed | Missing executable fails closed before launch with bounded `codex-cli` error. |  |  |  |
| 17.codex-cli.2 | 17 | ORS | no | `python3 -m brain.ui --llm-mode codex-cli` with real `codex` on PATH | Optional real Codex CLI smoke only when executable/auth are available. |  |  |  |
| 17.cache.1 | 17 | SST | yes | in-process factory with `--llm-enable-cache` | Cache wrapping is mode-gated and opt-in only. |  |  |  |
| 17.print-once-mode-independence.1 | 17 | SST | yes | `--print-once` combined with each accepted `--llm-mode` | Print-once branch returns before backend construction for every accepted mode. |  |  |  |

---

## Failure-Path Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 13.failure-terminal.1 | 13 | SST | yes | `--check-terminal` in non-TTY/captured shell if applicable | Non-TTY is reported as bounded `works`, not a campaign failure. |  |  |  |
| 14.failure-load.1 | 14 | SST | yes | `/load-session` against missing or invalid temp DB | Failed load preserves live session and records bounded error. |  |  |  |
| 15.failure-autosave-db.1 | 15 | SST | yes | enable non-off autosave without `--session-db` | Fails locally before mutation and names missing session DB requirement. |  |  |  |
| 15.failure-autosave-dispatch.1 | 15 | SST | yes | failed `/step` or invalid `/stream-promote` with autosave enabled | Failed mutation does not autosave. |  |  |  |
| 16.failure-backup-overwrite.1 | 16 | SST | yes | backup to existing destination without force | Refuses overwrite without corrupting source or destination. |  |  |  |
| 17.failure-anthropic-key.1 | 17 | SST | yes | `--llm-mode anthropic-api` without key | Fails closed before launch and performs no network call. |  |  |  |
| 17.failure-claude-missing.1 | 17 | SST | yes | `--llm-mode claude-cli` with missing executable | Fails closed before launch and performs no subprocess call. |  |  |  |
| 17.failure-codex-missing.1 | 17 | SST | yes | `--llm-mode codex-cli` with missing executable | Fails closed before launch and performs no subprocess call. |  |  |  |

---

## UX / Readability Tests

| ID | Step | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|------|-------|------|----------------|----------|----------|----------|---------|
| 13.ux-print-once.1 | 13 | MOT | env | inspect `--print-once` output | Output is readable enough for an operator to understand current view, tick, queue, and command area. |  |  |  |
| 13.ux-stream.1 | 13 | MOT | env | inspect Step 13 stream/status outputs | Stream and promotion statuses are intelligible without reading source. |  |  |  |
| 14.ux-persistence.1 | 14 | MOT | env | inspect save/load/session-status output | Persistence output names path, action, and result clearly. |  |  |  |
| 15.ux-autosave.1 | 15 | MOT | env | inspect autosave-status and autosave mutation output | Autosave output distinguishes disabled, enabled, success, and error states. |  |  |  |
| 16.ux-db.1 | 16 | MOT | env | inspect DB observability outputs | DB reports are bounded, truthful, and easy to scan. |  |  |  |
| 17.ux-llm-errors.1 | 17 | MOT | env | inspect LLM runtime failure messages | Missing key/executable messages are bounded and actionable. |  |  |  |

---

## Step Coverage Summary

```text
Step 13 rows: launch + offline interaction + launch/stream UX
Step 14 rows: persistence/cold-start + load failure + persistence UX
Step 15 rows: autosave + autosave failure paths + autosave UX
Step 16 rows: DB observability + backup + backup failure paths + DB UX
Step 17 rows: LLM runtime modes + failure paths + optional ORS smoke + LLM error UX
```

The next campaign step is Step 13:

```text
PHASE3_11_OFFLINE_INTERACTION_REPORT.md
```

Step 13 executes only its assigned launch/offline/basic interaction
observations and records actual behavior. It does not patch failures.
