# CURRENT_MISSION.md — Phase 3.11 Comprehensive Live Behavior Test Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

This mission replaces the completed Phase 3.10 Operational Hardening + Persistence Observability + Autosave Policy campaign. The repo now has stream interaction, persistence, database observability, backup, and opt-in autosave. The next mission is not to add a new cognitive layer. The next mission is to test the actual live behavior of the system, including launch paths, real operator command behavior, persistence, autosave, observability, and LLM runtime modes.

---

## Current mission

Execute the **Phase 3.11 Comprehensive Live Behavior Test Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Campaign target:

```text
Phase 3.11a Codex CLI Runtime Option        — add codex-cli as an explicit LLM runtime mode candidate before live test coverage
Phase 3.11b Comprehensive Live Behavior     — test actual operator behavior across offline, mock, Claude CLI, Codex CLI, optional API/real modes
Phase 3.11c Behavior Findings + Triage      — document what actually works, what is awkward, what fails, and what should be fixed next
```

Intended result:

```text
The repo contains a grounded behavior report that says what the system actually does when launched and used.
```

This campaign is evidence-seeking. It should not presume the system behaves well merely because invariant fixtures pass.

---

## Branch / push / PR rule

Future campaign work must use a branch-first workflow.

Preferred branch:

```text
campaign/comprehensive-live-behavior-test
```

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
```

This file itself may be installed on `main` only by explicit user request. Campaign execution still uses the branch-first rule.

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_10_INTEGRATED_AUDIT.md
PHASE3_10C_AUTOSAVE_AUDIT.md
PHASE3_10C_AUTOSAVE_DRY_RUN.md
PHASE3_10_OPS_OBSERVABILITY_AUDIT.md
PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md
PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md
PHASE3_9_PERSISTENCE_DRY_RUN.md
PHASE3_TEXT_INTERACTION_DRY_RUN.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
brain/ui/llm_runtime.py
brain/ui/autosave.py
brain/ui/persistence.py
brain/ui/session.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Baseline to verify

Expected current baseline:

```text
Catalog: v0.20
Counts:
  REQUIRED:        214
  STRUCTURAL:       83
  NOT-EXERCISED:     9
  DEFERRED:         12
  OBSERVED:         16
Latest completed campaign: Phase 3.10 Operational Hardening + Persistence Observability + Autosave Policy
Required latest audit:
  PHASE3_10_INTEGRATED_AUDIT.md      PASS
Required latest PR:
  PR #9 merged
In-flight: Phase 3.11 Comprehensive Live Behavior Test
  Steps 8-11 complete on campaign branch:
    Step 8 Codex CLI catalog patch applied (v0.19 -> v0.20)
    Step 9 Codex CLI runtime option implemented
    Step 10 live test kickoff created
    Step 11 live test corrigenda created
  Next eligible step: Step 12 live test matrix
```

Stop if these facts are false or the catalog gate disagrees.

---

## Codex CLI requirement

This mission must include `codex-cli` as an explicit LLM runtime option target.

Required planning outcome:

```text
--llm-mode codex-cli
```

or the exact final spelling accepted by the campaign corrigenda.

The `codex-cli` mode must follow the existing runtime discipline:

```text
default remains offline
Codex CLI is explicit opt-in
missing executable / missing auth fails locally before launch
no network/API assumption inside deterministic fixtures
standard tests do not require real Codex access
real Codex CLI smoke is OBSERVED/manual unless explicitly accepted as gating
selected client enters through the existing LLMClient / tick(..., client, ...) seam
```

If current Codex CLI invocation details are uncertain, the synthesis/kickoff/corrigenda must make the executable/argument contract explicit before implementation.

---

## Architectural guardrails

Preserve these constraints throughout Phase 3.11:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
loaded state must reconstruct through public builders / constructors
loaded state must pass invariants before becoming active
failed load/save/verify/backup/autosave must not corrupt live state
tick() remains the only TLICA runtime transition route
/step remains the operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
Codex CLI mode must be explicit opt-in
no LLM client, socket, file handle, subprocess handle, callable, curses object, or sqlite3.Connection is stored on OperatorSession
```

Test campaigns may expose uncomfortable behavior. Do not hide or patch around behavior findings unless the campaign explicitly authorizes a correctness patch step.

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
