# CURRENT_MISSION.md — Phase 3.11 Comprehensive Live Behavior Test Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

This mission replaces the completed Phase 3.10 campaign. The next mission is to test actual live behavior before building a scenario harness or adding new cognitive layers.

---

## Current mission

Execute the **Phase 3.11 Comprehensive Live Behavior Test Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Campaign target:

```text
Phase 3.11a Codex CLI Runtime Option
Phase 3.11b Comprehensive Live Behavior Test
Phase 3.11c Behavior Findings + Triage
```

The campaign must include `codex-cli` as an explicit LLM runtime option target.

---

## Branch / push / PR rule

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

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_10_INTEGRATED_AUDIT.md
PHASE3_10C_AUTOSAVE_AUDIT.md
PHASE3_10_OPS_OBSERVABILITY_AUDIT.md
PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
PHASE3_11_COMPREHENSIVE_LIVE_BEHAVIOR_TEST_ROADMAP.md
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

```text
Catalog: v0.19
Counts: 212 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 15 OBSERVED
Latest completed campaign: Phase 3.10 Operational Hardening + Persistence Observability + Autosave Policy
Required latest audit: PHASE3_10_INTEGRATED_AUDIT.md PASS
Required latest PR: PR #9 merged
```

Stop if these facts are false or the catalog gate disagrees.

---

## Codex CLI requirement

This mission must include:

```text
--llm-mode codex-cli
```

The final spelling and implementation details must be locked by the Phase 3.11 Codex CLI synthesis, kickoff, corrigenda, and catalog patch plan before implementation.

Required constraints:

```text
offline remains default
codex-cli is explicit opt-in
standard fixtures do not require real Codex access
real Codex smoke is OBSERVED/manual unless explicitly accepted as gating
selected client enters through the existing LLMClient / tick(..., client, ...) seam
```

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
