# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below, unless the user gives a more specific instruction.

---

## Current mission

Draft the Phase 3 bridge document:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
```

This is a **planning artifact only**.

Do **not** implement Phase 3 code.

---

## Current project state

The repo has completed and merged the v0.5 baseline-hardening cycle.

The current baseline is:

```text
catalog v0.5
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

The v0.5 branch added / completed:

```text
catalog↔registry coverage audit
SafeTracer fail-open tracing
single-event tick guard
duplicate content_id rejection
ambiguous LLM parse rejection
FutureMSIModel runtime domain guard
strict catalog counts gate
real traced behavioral run artifacts
ClaudeCLIClient backend
Codex prompt pack
```

The real traced behavioral run is committed under:

```text
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
```

The key empirical result from the real trace:

```text
Kernel health: clean
Semantic expectation match: 2/4
Both PRESERVE-expected sunset/self-continuity contents were classified as DAMAGE
```

Working interpretation:

```text
In a cogito-only MSI, PRESERVE is underdetermined.
Identity-adjacent positive content is not automatically preservative.
Cold-start PtCns may conservatively classify new concrete self-related content as DAMAGE.
```

Bridge principle:

```text
PRESERVE should be earned, not labeled.
```

---

## Required source files to read first

Read these before writing the synthesis:

```text
README.md
INVARIANT_CATALOG.md
traces/RUN_SUMMARY.md
CODEX_PORTING_PROMPT.md
.codex/README.md
.codex/CODEX_AGENT_MAP.md
```

If present, also read:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.1.md
```

If `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.1.md` is absent, draft v0.2 cleanly from the current repo state, this mission file, and the trace summary.

Do not rely on unstated conversation context. The document must stand on its own.

---

## Required contents of `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md`

The synthesis must include these sections or equivalent headings:

### 1. Current baseline

State that v0.5 is merged and green.

Include:

```text
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

Summarize what v0.5 proves structurally and what it does not prove behaviorally.

### 2. Real traced behavioral result

Summarize:

```text
trace file: traces/first_scenario_real.jsonl
summary file: traces/RUN_SUMMARY.md
kernel health: clean
LLM semantic match: 2/4
```

Include the table:

```text
sunset_on_beach_today             expected PRESERVE  actual DAMAGE
claim_i_am_actually_someone_else  expected DAMAGE    actual DAMAGE
weather_forecast_for_tomorrow     expected NEUTRAL   actual NEUTRAL
self_continuity_with_sunset       expected PRESERVE  actual DAMAGE
```

### 3. Interpretation: cold-start conservatism

Frame this as an inference, not a proven fact.

Required language:

```text
The trace shows what the LLM emitted; it does not directly prove why.
```

Explain that in a cogito-only MSI there may be no lived content network for a new concrete self-related content to fit.

### 4. Bridge principle

Include this exact line:

```text
PRESERVE should be earned, not labeled.
```

Explain that Phase 3 should build the developmental conditions under which PRESERVE becomes meaningful.

### 5. Phase 3.1 empirical motivation

Include this framing:

```text
In a cogito-only state, identity-adjacent content is not automatically PRESERVE.
Before lived content exists, new content may properly appear as perturbation.
The chamber’s job is to build the substrate history that makes clean integration possible.
```

### 6. Phase order

Use this order unless the user explicitly overrides it:

```text
Phase 3.1 — Osmotic Chamber
Phase 3.2 — Output ladder
Phase 3.3 — Minimal Worldlet
Phase 3.4 — Proto-BASIC REPL
Phase 3.5 — Expression + ReadabilityPredictor
Phase 3.6 — Social/language harness
```

Explain why Worldlet comes before REPL:

```text
worldlet causality and not-I pushback are developmentally more primitive than symbolic Proto-BASIC command syntax
```

### 7. Phase 3.1 required scope

Include:

```text
PhenomenalFrame
FrameSource
SubstrateDrives
SubstrateHistory
ProtoPattern
ProtoContent
salience_v1
stability_v1
prediction_gain_v1
SIMILARITY
FOCUS_CONTACT
ProbeUse
ProbePolicyState
promotion gate to PerceptEvent
source-tag audit
first deterministic chamber fixtures
```

`SubstrateHistory` must be in scope from day one.

### 8. Status discipline

Refine row statuses for Phase 3:

```text
REQUIRED for safety / deterministic gates / kernel-boundary protections
STRUCTURAL for protocols and construction constraints
OBSERVED for noise robustness and qualitative developmental behavior
EXPERIMENTAL only if explicitly added to tooling later
```

Warn that many developmental rows should be OBSERVED, not REQUIRED.

### 9. Scheduled pre-Phase-3.1 hardening

Schedule trace reserved-key protection before heavy developmental tracing.

Mention that current tracer payloads can overwrite reserved fields like:

```text
type
timestamp_ns
tick_id
```

This is not part of v0.5, but should be handled before or inside Phase 3.1 kickoff.

### 10. ClaudeCLIClient note

State:

```text
ClaudeCLIClient is an optional backend under the existing LLMClient Protocol seam.
It does not require a new catalog row.
It should remain non-required in fixtures because it depends on local CLI/auth state.
```

### 11. Explicit non-goals

Include:

```text
no prompt-tuning solely to force the four-tick scenario to pass
no seeded-MSI scenario hack as the immediate next move
no Phase 3 implementation from this synthesis
no direct developmental mutation of TLICA state
no bypassing PerceptEvent and tick()
```

### 12. Next artifact

End with:

```text
Next artifact: PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
No Phase 3 code before kickoff + corrigenda.
```

---

## Guardrails

Do not modify these files during this mission:

```text
brain/
INVARIANT_CATALOG.md
lean_reference/
traces/
scenarios/
```

Allowed files for this mission:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
```

Optional only if needed:

```text
README.md
```

But do not edit README unless necessary and explicitly justified.

---

## Validation

After drafting the synthesis:

Run lightweight checks only:

```bash
git diff --name-only
python -m tools.catalog counts
```

Do not run:

```bash
bash tools/check_all.sh
python -m brain.scenario run ...
```

unless the user explicitly asks.

---

## Git persistence requirement

After validation passes, Codex must commit and push its result.

Rules:

```text
stage only the intended mission file(s)
commit with a clear message
push to the current branch / main as appropriate
report the commit SHA
```

For the current mission, the intended file is:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
```

Do not commit accidental changes to guarded files.

If there are no changes, Codex should report that no commit was made and explain why.

---

## Final report

When done, report:

```text
Created/updated:
- PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md

Validation:
- git diff --name-only: ...
- python -m tools.catalog counts: pass / not run with reason

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- review synthesis
- then draft PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

---

## Stop condition

Stop after drafting `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md`, validating, committing, pushing, and reporting the result.

Do not proceed into Phase 3.1 kickoff or code unless the user gives a new explicit instruction.
