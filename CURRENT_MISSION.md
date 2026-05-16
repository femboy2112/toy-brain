# CURRENT_MISSION.md — Phase 3.10 Operational Hardening + Persistence Observability + Autosave Entry Point

## One-line instruction

When a repo-capable agent receives `go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

This mission replaces the completed Phase 3.9 Persistent Session Store campaign. The repo can now persist and restore `BrainState` / `OperatorSession` through an explicit SQLite session store, but the operator still needs robust status, verification, backup, observability, and a carefully gated autosave policy before the persistence layer should be treated as operationally mature.

---

## Current mission

Execute the **Phase 3.10 Operational Hardening + Persistence Observability + Autosave Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Campaign target:

```text
Phase 3.10a Operational Hardening      — DB/session status, verification, backup, bounded recovery UX
Phase 3.10b Persistence Observability  — read-only DB/session/profile/stream summaries and saved-state diff
Phase 3.10c Autosave Policy            — explicit opt-in autosave after accepted backup/verify/observability gates
```

Intended result:

```text
python3 -m brain.ui --session-db brain/session.sqlite3 --load-session

/session-status
/db-status
/db-verify
/db-summary
/profile-summary
/db-diff
/db-backup
/autosave-status
/autosave-enable     # only after the accepted autosave phase lands
/autosave-disable
```

Autosave is **not** authorized by default. It must remain off unless an accepted Phase 3.10c catalog patch and implementation explicitly enable a finite, opt-in mode.

---

## Branch / push / PR rule

Future campaign work must use a branch-first workflow.

Preferred branch:

```text
campaign/operational-hardening-observability-autosave
```

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
```

This review bundle is not a Git push. If these files are installed later, the branch-first rule governs the campaign implementation after installation.

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md
PHASE3_9_PERSISTENCE_DRY_RUN.md
PHASE3_TEXT_INTERACTION_DRY_RUN.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
brain/ui/persistence.py
brain/ui/session.py
brain/ui/__main__.py
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Baseline to verify

Expected current baseline:

```text
Catalog: v0.19
Counts:
  REQUIRED:        212
  STRUCTURAL:       83
  NOT-EXERCISED:     9
  DEFERRED:         12
  OBSERVED:         15
Latest completed campaign: Phase 3.9 Persistent Session Store
Required latest audit:
  PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md      PASS
Required latest dry run:
  PHASE3_9_PERSISTENCE_DRY_RUN.md
```

Stop if these facts are false or the catalog gate disagrees.

---

## Architectural guardrails

Preserve these constraints throughout Phase 3.10:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
loaded state must reconstruct through public builders / constructors
loaded state must pass invariants before becoming active
failed load must not replace the live session
failed save / verify / backup must not mutate the live session
tick() remains the only TLICA runtime transition route
/step remains the operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
no LLM client, socket, file handle, subprocess handle, callable, curses object, or sqlite3.Connection is stored on OperatorSession
no autosave until Phase 3.10c explicitly accepts and implements it
```

Persistence writes may occur only to an explicitly configured session database path or to an explicit backup path after the backup policy is accepted. No implicit background persistence, no unreviewed export path, and no autosave may land before its review gate.

Guarded paths may be touched only when the current campaign step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

---

## Command rule

Use `python3 -m ...` for Python module commands. Convert historical `python -m ...` examples to `python3 -m ...` unless the user has explicitly confirmed a `python` alias.

---

## Final report format

After each run, report:

```text
Campaign step executed:
- <step name>

Created/updated:
- <files>

Validation:
- <commands and results>

Git:
- commit: <sha or none>
- branch: <campaign branch>
- push: success / not needed
- PR: <url if opened, otherwise not opened yet>

Next:
- <next campaign step or stop condition>
```

Stop according to `CURRENT_CAMPAIGN.md` and do not pass a review gate without a fresh instruction.
