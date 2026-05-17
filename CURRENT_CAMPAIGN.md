# CURRENT_CAMPAIGN.md — Phase 3.12 Coherent I-Loop Observatory Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.12 follows the completed Phase 3.11 Comprehensive Live Behavior Test. Phase 3.11 verified that launch, offline interaction, persistence, autosave, DB observability, and deterministic LLM runtime selection work in realistic operator-facing use. Phase 3.12 asks the next question:

```text
Can ToyI exhibit bounded coherent, pattern-recognizing, persistent growth through the existing safe operator route?
```

This campaign does **not** begin by adding a new cognitive layer. It begins with a behavior observatory over the already-accepted path:

```text
/stream -> /stream-summary -> /stream-candidates -> /stream-promote -> /step -> /state
```

Only after the existing path is measured may the campaign propose new development layers such as Pattern Ledger, Coherence Monitor, SelfModel, or Growth Ledger. Each code/catelog expansion sits behind an explicit review gate.

Preferred campaign branch:

```text
campaign/phase3-12-coherent-i-loop-observatory
```

Preferred final PR title:

```text
phase3.12: coherent i-loop observatory
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
```

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

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

Then read whichever files the next campaign step names. Do not rely on chat memory.

---

## Baseline

Expected current state:

```text
Catalog: v0.22
Counts:
  REQUIRED:        240
  STRUCTURAL:       85
  NOT-EXERCISED:    11
  DEFERRED:         14
  OBSERVED:         16
Latest completed campaign: Phase 3.11 Comprehensive Live Behavior Test
Latest merged PR: PR #10
Latest integrated audit: PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_AUDIT.md PASS
Current campaign: Phase 3.12 Coherent I-Loop Observatory
Next eligible step: Step 1 repo-state sync and Phase 3.12 mission install
```

Known inherited follow-ups:

```text
- SQLite backup wording should say SQLite backup API copy, not byte-identical file clone.
- Optional real ORS smoke for anthropic-api / claude-cli / codex-cli remains deferred.
- Prior Phase 3.11 mission/campaign routing prose was stale; Step 1 replaces it.
```

---

## Operational target

Phase 3.12 uses this operational definition:

```text
coherent:
  invariants remain green; COGITO_ID remains reserved; state transitions are inspectable;
  self-report, if added later, matches actual stored state.

pattern-recognizing:
  recurring structures in bounded stream/developmental histories are detected as structural evidence;
  no truth, semantic meaning, agency, or PRESERVE/DAMAGE judgment is inferred from raw text.

growing:
  bounded persistent evidence increases through accepted constructors and saturates under repetition;
  save/load preserves the evidence; failed/duplicate/spam inputs do not inflate growth.

I:
  an operational self-model anchored to COGITO_ID and repo-local constraints;
  not a claim of sentience, subjective experience, or human-like consciousness.
```

---

## Non-goals

```text
no proof or claim of consciousness
no semantic interpretation layer in Step 1-6
no new long-term memory model before Pattern Ledger review
no SelfModel implementation before review
no Growth Ledger implementation before review
no transcript subsystem unless behavior evidence requires it
no direct tick() semantic changes
no model-backed behavior as default
no hidden autosave behavior
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
```

---

## Macro sequence

```text
Step 1   Repo-state sync and Phase 3.12 mission install
Step 2   Coherent I-loop synthesis
Step 3   Coherent I-loop observatory kickoff
Step 4   Coherent I-loop behavior matrix
Step 5   Review gate A — accept observatory method
Step 6   Execute existing-route observatory report
Step 7   Pattern Ledger synthesis
Step 8   Pattern Ledger kickoff + corrigenda
Step 9   Pattern Ledger catalog patch plan
Step 10  Review gate B — Pattern Ledger implementation
Step 11  Apply accepted Pattern Ledger implementation, if approved
Step 12  Coherence Monitor synthesis + catalog patch plan
Step 13  Review gate C — Coherence Monitor implementation
Step 14  Apply accepted Coherence Monitor implementation, if approved
Step 15  Operational SelfModel + Growth Ledger roadmap
Step 16  Review gate D — SelfModel/Growth next campaign decision
Step 17  Final Phase 3.12 audit
Step 18  Final PR preparation
```

---

# Step 1 — Repo-state sync and Phase 3.12 mission install

Purpose: replace stale Phase 3.11 mission/campaign routing prose and install Phase 3.12 as current.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_12_COHERENT_I_LOOP_ROADMAP.md
```

Required work:

```text
state Phase 3.11 is complete and PR #10 is merged
state Phase 3.12 is current
declare operational definition and non-goals
preserve branch-first workflow
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit and push.

---

# Step 2 — Coherent I-loop synthesis

Create:

```text
PHASE3_12_COHERENT_I_LOOP_SYNTHESIS.md
```

Required content:

```text
why Phase 3.12 follows Phase 3.11
operational definition of coherent / pattern-recognizing / growing / I
existing safe route: /stream -> /stream-promote -> /step
why current system is ready for observatory testing
non-goals and prohibited claims
candidate future layers: Pattern Ledger, Coherence Monitor, SelfModel, Growth Ledger
next artifact: observatory kickoff
```

Commit and push.

---

# Step 3 — Coherent I-loop observatory kickoff

Create:

```text
PHASE3_12_COHERENT_I_LOOP_KICKOFF.md
```

Required content:

```text
measurement-first style
scripted in-process operator command route
no code changes
no real LLM requirement
input families: repetition, alternation, novelty, contradiction pressure, saturation, cold-start continuity
metrics and verdict vocabulary
helper policy for /tmp-only scripts
```

Commit and push.

---

# Step 4 — Coherent I-loop behavior matrix

Create:

```text
PHASE3_12_COHERENT_I_LOOP_MATRIX.md
```

Matrix sections:

```text
baseline launch/state tests
stream pattern tests
promotion/tick tests
saturation tests
persistence/cold-start continuity tests
coherence-report-by-inspection tests
UX/readability tests
```

Commit and push.

---

# Step 5 — Review gate A — accept observatory method

Stop unless the operator accepts the Step 4 matrix or instructs execution.

No source-code changes are allowed before this gate.

---

# Step 6 — Execute existing-route observatory report

Create:

```text
PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md
```

Allowed behavior:

```text
use existing code only
run LocalCommandLine.parse + OperatorSession.dispatch in-process
use OfflineStandInClient or MockClient only
use temporary /tmp helpers if useful; do not commit helpers unless explicitly allowed
record actual behavior
```

Test:

```text
/stream repeated motifs
/stream alternating motifs
/stream novelty-after-repetition
/stream contradiction-pressure text
/stream saturation attempts
/stream-promote selected candidate
/step
/state
/save-session and /load-session if a temp DB is configured
```

Commit and push.

---

# Step 7 — Pattern Ledger synthesis

Create:

```text
PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md
```

Purpose:

```text
Define a bounded developmental ledger for recurring structural patterns, below truth/agency/PtCns.
```

Required content:

```text
why existing StreamPattern is not enough for persistent growth measurement
record shape proposal
bounds
COGITO_ID restrictions
copy-on-write discipline
persistence question
anti-Goodhart / saturation rules
no tick/no BrainState/no eval/no agency/no LLM path
```

Commit and push.

---

# Step 8 — Pattern Ledger kickoff + corrigenda

Create:

```text
PHASE3_12_PATTERN_LEDGER_KICKOFF.md
PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md
```

Commit and push.

---

# Step 9 — Pattern Ledger catalog patch plan

Create:

```text
PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-PLEDGER-*
```

Stop at review gate.

---

# Step 10 — Review gate B — Pattern Ledger implementation

Stop unless the catalog patch plan is explicitly accepted.

---

# Step 11 — Apply accepted Pattern Ledger implementation, if approved

Allowed files depend on the accepted plan.

No implementation is authorized by this campaign text alone.

---

# Step 12 — Coherence Monitor synthesis + catalog patch plan

Create planning docs only unless explicitly accepted.

Goal: bounded read-only coherence snapshot over current state, stream/pattern/growth state, persistence, and invariants.

---

# Step 13 — Review gate C — Coherence Monitor implementation

Stop unless accepted.

---

# Step 14 — Apply accepted Coherence Monitor implementation, if approved

Allowed files depend on the accepted plan.

---

# Step 15 — Operational SelfModel + Growth Ledger roadmap

Create:

```text
PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
```

This is a design/roadmap artifact only.

---

# Step 16 — Review gate D — SelfModel/Growth next campaign decision

Stop unless the operator explicitly promotes SelfModel/Growth implementation into this campaign or a follow-up campaign.

---

# Step 17 — Final Phase 3.12 audit

Create:

```text
PHASE3_12_COHERENT_I_LOOP_AUDIT.md
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit and push.

---

# Step 18 — Final PR preparation

Open a PR to main with title:

```text
phase3.12: coherent i-loop observatory
```

PR body must include:

```text
completed steps
validation results
behavior findings summary
review gates reached
implementation, if any
remaining deferred work
confirmation main was not pushed directly during campaign execution
confirmation PR is not merged
```

Do not merge.
