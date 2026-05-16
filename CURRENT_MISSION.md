# CURRENT_MISSION.md — Phase 3.9 Persistent Session Store Entry Point

## One-line instruction

When a repo-capable agent receives `go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

This mission replaces the completed Fast Safe Text Interaction campaign. The repo can now run a bounded text-stream interaction loop with an explicit LLM runtime toggle, but it does not yet preserve profile/session state across cold starts. Phase 3.9 exists to add persistent session/profile continuity without weakening the existing `PerceptEvent` / `tick()` boundary.

---

## Current mission

Execute the **Phase 3.9 Persistent Session Store Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Campaign target:

```text
Phase 3.9 Persistent Session Store — exact, invariant-checked cold-start continuity for BrainState, profile, registry, session counters, and local text-stream history.
```

Intended result:

```text
python3 -m brain.ui --session-db brain/session.sqlite3 --load-session

/save-session
/load-session
```

The persistence layer must be explicit, typed, transactional, schema-versioned, and constructor-validated. It must not pickle arbitrary Python objects or assign deserialized data directly into kernel state.

---

## Branch / push / PR rule

Future campaign work must use a branch-first workflow.

Preferred branch:

```text
campaign/persistent-session-store
```

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
```

This file itself may already have been installed on `main` by explicit user request. That does not change the branch-first rule for the new campaign implementation.

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_TEXT_INTERACTION_DRY_RUN.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Baseline to verify

Expected current baseline:

```text
Catalog: v0.16
Counts:
  REQUIRED:        178
  STRUCTURAL:       64
  NOT-EXERCISED:     9
  DEFERRED:         12
  OBSERVED:         12
Latest completed campaign: Fast Safe Text Interaction through Phase 3.8b and Step 26 dry run
Required latest audits:
  PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md      PASS
  PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md             PASS
Required latest dry run:
  PHASE3_TEXT_INTERACTION_DRY_RUN.md
```

Stop if these facts are false or the catalog gate disagrees.

---

## Architectural guardrails

Preserve these constraints throughout Phase 3.9:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
loaded state must reconstruct through public builders / constructors
loaded state must pass invariants before becoming active
failed load must not replace the live session
failed save must not mutate the live session
tick() remains the only TLICA runtime transition route
/step remains the operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
no LLM client, socket, file handle, subprocess handle, callable, or curses object is persisted
```

Persistence may write only to an explicitly configured session database path. No autosave is authorized until a cataloged autosave policy is accepted.

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
