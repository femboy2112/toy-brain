# CURRENT_MISSION.md — Fast Safe Text Interaction Entry Point

## One-line instruction

When a repo-capable agent receives `go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

This mission replaces the completed Phase 3.5 mission. It aims for the first safe text-stream interaction loop while preserving the catalog, `COGITO_ID` reservation, and the existing `PerceptEvent` / `tick()` boundary.

---

## Current mission

Execute the **Fast Safe Text Interaction Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Campaign target:

```text
Phase 3.6  Reflective Inspection       — minimal read-only developmental summary layer
Phase 3.7  Text Stream Ingress          — raw text chunks below promotion boundary
Phase 3.8  Operator Stream Interaction  — typed TUI route to feed chunks and promote only explicit candidates
Phase 3.8b LLM Runtime Toggle           — explicit opt-in model-backed testing mode, default offline
```

The intended path is:

```text
repo-state sync
  -> minimal reflective inspection
  -> bounded text stream substrate
  -> explicit operator-facing stream commands
  -> optional model-backed testing toggle
  -> promotion candidates only through PerceptEvent + tick()
```

---

## Branch / push / PR rule

This mission must use a branch-first Git workflow.

Preferred branch:

```text
campaign/fast-safe-text-interaction
```

Rules:

```text
never commit directly to main
never push directly to main
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
```

If the preferred branch already exists, continue it when it is clearly the active campaign branch. Otherwise use a timestamped variant.

Preferred PR title:

```text
phase3: fast safe text interaction campaign
```

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
PHASE3_8B_LLM_TOGGLE_AMENDMENT.md
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

The LLM toggle amendment is mandatory campaign context. A repo-capable agent must not pass final Phase 3.8 interaction testing unless that amendment has either been incorporated into `CURRENT_CAMPAIGN.md` or explicitly superseded by a later accepted campaign document.

---

## Baseline to verify

Expected starting state:

```text
Catalog: v0.12
Counts: 139 REQUIRED / 48 STRUCTURAL / 5 NOT-EXERCISED / 12 DEFERRED / 8 OBSERVED
Latest completed campaign: Phase 3.5 Expression + ReadabilityPredictor
Required latest audit: PHASE3_5_EXPRESSION_READABILITY_AUDIT.md with PASS verdict
```

Stop if these facts are false or the catalog gate disagrees.

---

## Architectural guardrails

Preserve the old kernel invariants and Phase 3 discipline:

```text
raw text never mutates BrainState directly
raw text never becomes COGITO_ID
raw text never bypasses PerceptEvent construction
tick() remains the only TLICA runtime mutation route
single-event tick discipline remains intact
Expression evidence remains local-only
Reflective Inspection remains read-only and below Mode B
Text Stream evidence remains developmental evidence until explicit promotion
operator commands remain finite, typed, bounded, and inspectable
model-backed testing remains explicit opt-in and defaults to offline mode
```

Do not add unrestricted host access, unrestricted code evaluation, unbounded model-backed behavior, social/language harnesses, Mode B planning, or direct TLICA mutation from developmental histories.

The only model-backed behavior authorized by this mission is the later explicit LLM Runtime Toggle subcampaign described in `PHASE3_8B_LLM_TOGGLE_AMENDMENT.md`. It must remain non-default and must use the existing `LLMClient` / `tick(..., client, ...)` seam.

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
