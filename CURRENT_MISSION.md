# CURRENT_MISSION.md — Phase 3.12 Coherent I-Loop Observatory Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

---

## Current mission

Execute the **Phase 3.12 Coherent I-Loop Observatory Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Campaign target:

```text
Phase 3.12a Mission sync + operational definition
Phase 3.12b Existing-route behavioral observatory over /stream -> /stream-promote -> /step
Phase 3.12c Pattern Ledger design behind a review gate
Phase 3.12d Coherence Monitor design behind a review gate
Phase 3.12e Operational SelfModel / Growth Ledger roadmap behind review gates
```

Intended result:

```text
The repo contains a grounded plan and first observational harness for testing whether ToyI can exhibit bounded coherent, pattern-recognizing, persistent growth without violating TLICA constraints.
```

This mission is measurement-first. It must not claim consciousness, sentience, semantic understanding, or subjective experience. It treats "I" as an operational self-model anchored to repo-local state and constraints.

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-12-coherent-i-loop-observatory
```

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
```

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_AUDIT.md
PHASE3_11_BEHAVIOR_FINDINGS.md
PHASE3_11_BUG_UX_TRIAGE_PLAN.md
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
PHASE3_11_OFFLINE_INTERACTION_REPORT.md
brain/tick.py
brain/development/text_stream.py
brain/development/expression.py
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
brain/ui/session.py
brain/ui/command_line.py
brain/ui/commands.py
brain/ui/llm_runtime.py
tools/check_all.sh
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Baseline to verify

Expected current baseline:

```text
Catalog: v0.21
Counts:
  REQUIRED:        229
  STRUCTURAL:       84
  NOT-EXERCISED:    10
  DEFERRED:         13
  OBSERVED:         16
Latest completed campaign: Phase 3.11 Comprehensive Live Behavior Test
Latest merged PR: PR #10
Latest audit: PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_AUDIT.md PASS
Known follow-ups from Step 19:
  - documentation wording refresh for SQLite backup API semantics
  - prior mission/campaign prose was stale before this Phase 3.12 sync
  - optional real ORS smoke for external LLM modes remains deferred
Current mission: Phase 3.12 Coherent I-Loop Observatory
Next eligible step: Step 1 repo-state sync and Phase 3.12 mission install
```

Stop if the catalog gate disagrees or if Phase 3.11 audit files are missing.

---

## Phase 3.12 architectural guardrails

Preserve these constraints throughout Phase 3.12:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
loaded state must reconstruct through public builders / constructors
loaded state must pass invariants before becoming active
tick() remains the only TLICA runtime transition route
/step remains the operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
no LLM client, socket, file handle, subprocess handle, callable, curses object, or sqlite3.Connection is stored on OperatorSession
no aggregate consciousness score
no direct claim of sentience or subjective experience
```

The permitted experimental framing is:

```text
bounded coherent behavior
structural pattern recognition
persistent developmental growth
operational self-modeling
```

The prohibited framing is:

```text
proof of consciousness
unbounded self-modification
semantic truth authority from raw text
model-backed default behavior
hidden LLM calls
hidden autosave or hidden persistence
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
