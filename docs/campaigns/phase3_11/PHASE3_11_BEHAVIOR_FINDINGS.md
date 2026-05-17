# PHASE3_11_BEHAVIOR_FINDINGS.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 18: aggregate the live behavior
findings from Phase 3.11 Steps 13-17.

Source reports:

```text
PHASE3_11_OFFLINE_INTERACTION_REPORT.md
PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
```

This is a report-only findings artifact. It does not edit source code,
fixtures, catalog rows, mission/campaign routing prose, or prior reports.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 18
Prior step evidence: 5c2dce9 phase3.11 step17: llm runtime behavior report
```

## Verdict Counts

Aggregated from the observation tables in Steps 13-17:

| Verdict | Count | Notes |
| --- | ---: | --- |
| works | 56 | Launch, offline interaction, persistence, autosave, DB observability, deterministic LLM runtime gates. |
| awkward | 2 | SQLite backup hash/wording mismatch in Step 16. |
| confusing | 0 | No observation used this verdict. |
| fails | 0 | No gating behavior row failed. |
| missing | 0 | No expected feature was absent in the deterministic test scope. |
| blocked by env | 0 | No required deterministic row was blocked by local environment. |
| ORS skipped | 3 | Real anthropic-api, Claude CLI, and Codex CLI smoke were skipped by deterministic policy. |

## Works As Expected

- `python3 -m brain.ui --print-once` renders a deterministic operator
  frame.
- `python3 -m brain.ui --check-terminal` returns bounded environment
  status in both non-TTY and PTY contexts.
- A real PTY launch renders the curses operator layout and `/quit`
  exits cleanly.
- `/help`, `/stream`, `/stream-summary`, `/stream-candidates`,
  `/stream-promote`, `/step`, and `/state` all route through the typed
  local command path and behave coherently under the offline stand-in.
- `/step` consumes a queued promotion candidate, advances the tick, and
  calls the offline client exactly once.
- `/save-session` persists kernel/profile/stream state to a configured
  SQLite DB.
- Direct `load_session(config)`, in-process `/load-session`, and a real
  PTY cold start with `--load-session` reconstruct the saved state
  through the persistence layer.
- Failed `/load-session` from a missing DB surfaces bounded local error
  text and preserves the live session.
- Autosave is off by default on cold in-process sessions.
- Non-off autosave requires `--session-db` and fails locally before
  launch if omitted.
- `/autosave-enable after-successful-mutation` enables autosave without
  immediately saving.
- Successful `/stream-promote` and `/step` each trigger autosave.
- Read-only `/state` and failed `/step` do not trigger autosave.
- `/autosave-disable` stops later successful mutations from saving.
- Injected autosave persistence failure is absorbed into a typed status
  report rather than raising through dispatch.
- `/db-status`, `/db-verify`, `/db-summary`, `/profile-summary`,
  `/stream-db-summary`, and `/db-diff` all execute successfully against
  a real saved session DB.
- One-shot `--db-status`, `--db-verify`, and `--db-backup` short-circuit
  commands work without curses launch.
- Backup overwrite refusal, explicit force overwrite, and URI-scheme
  destination rejection all behave as expected.
- Offline and mock LLM `--print-once` paths render deterministically.
- Anthropic API, Claude CLI, and Codex CLI fail closed before curses
  when required credentials or executables are missing.
- `codex-cli` is part of the accepted LLM runtime mode set.
- `--print-once` remains independent of LLM backend construction for all
  accepted modes.
- Cache wrapping is accepted for model-backed configuration and rejected
  for deterministic offline/mock modes.

## Works But Awkward

- Step 16 observed that SQLite backup files created through the backup
  API had the same size as the source but a different SHA-256 hash. The
  source DB hash stayed unchanged, and the backup operation reported
  `pages=18/18`, so operational behavior appears correct. The matrix
  wording "byte-faithful SQLite backup" overstates the file-hash
  property observed in practice.
- The `/db-backup file:/tmp/disallowed.db` parse rejection leaves the
  previous success status visible because parsing failed before
  dispatch. The parse error is bounded and clear, but the stale status
  can be mildly distracting.

## Confusing Output

No row was classified as `confusing`.

The nearest mild issue is documentation/test wording rather than runtime
output: Step 16's matrix expectation says "byte-faithful", while runtime
evidence supports "SQLite backup API copy that preserves source bytes
and produces a valid same-size backup".

## Incorrect Behavior

No row was classified as `fails`.

No critical correctness or safety/invariant behavior was observed during
Steps 13-17.

## Missing Feature

No row was classified as `missing`.

## Blocked By Environment

No required deterministic observation was blocked by the environment.

Optional real-smoke rows were intentionally skipped:

```text
anthropic-api ORS: skipped; no API key accepted/configured for real smoke
claude-cli ORS: skipped; claude executable exists, but deterministic Step 17 did not invoke it
codex-cli ORS: skipped; codex executable exists, but deterministic Step 17 did not invoke it
```

## Should Be Next Campaign

- If real external runtime confidence is needed, run a separate
  operator-approved manual ORS pass for `anthropic-api`, `claude-cli`,
  and `codex-cli` with explicit credentials/tool-auth expectations.
- If file-byte identity is truly required for backups, add a future
  explicit backup-copy requirement. Otherwise, update matrix wording to
  say SQLite backup API copy / source-preserving logical backup rather
  than byte-faithful clone.
- Refresh stale current-mission/current-campaign baseline prose after
  the active step boundary so "next eligible step" no longer points at
  Step 13.

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
git status --short                    only PHASE3_11_BEHAVIOR_FINDINGS.md
git diff --name-only                  no tracked source/catalog/mission diff
```

## Next

The next campaign step after this report is Step 19:

```text
PHASE3_11_BUG_UX_TRIAGE_PLAN.md
```
