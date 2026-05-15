# CURRENT_CAMPAIGN.md — Phase 3.5 Expression + ReadabilityPredictor Campaign

## Purpose

Begin the next developmental campaign after the completed Operator TUI work.

This campaign designs and implements a bounded local **Expression + ReadabilityPredictor** layer over existing bottom-up evidence:

```text
Phase 3.1 Osmotic Chamber
Phase 3.2 Output Ladder
Phase 3.3 Minimal Worldlet
Phase 3.4 Proto-BASIC REPL
Operator TUI v0.11 + input/switch repair
```

The goal is to inspect and score local expression/readability properties without creating language understanding, social communication, Mode B planning, or a real LLM-backed writer.

---

## Saved baseline

Expected baseline before this campaign:

```text
Catalog: v0.11
Operator TUI Agent-Style Layout: PASS
Operator TUI input/switch repair: merged
Counts: 127 REQUIRED / 44 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 7 OBSERVED
Full gate: green
Entrypoint: python3 -m brain.ui
```

Required audit artifacts:

```text
OPERATOR_TUI_AUDIT.md
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md
```

Stop if any required audit is absent or not PASS.

---

## Model-agnostic execution rule

When the user says `go`, the active repo-capable agent should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
run preflight
infer the next eligible step from repo state
execute only that step's allowed scope
validate as specified
commit and push after successful steps
stop at review gates, failures requiring user judgment, or campaign completion
```

Use `python3 -m ...` for Python module commands. Do not use `python -m ...` unless the user explicitly says a `python` alias exists.

---

## Hard boundaries

Do not modify unless a step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

Do not implement:

```text
real LLM calls
social/language harness
Mode B reflective planning
natural-language teacher/corrector
host execution
shell execution
network I/O
filesystem save/export
arbitrary Python execution
TLICA runtime promotion
PerceptEvent/tick() promotion from expression evidence
```

No external dependencies. Use only standard library and existing project APIs.

---

## Phase 3.5 thesis

Expression and readability are local deterministic harness constructs:

```text
Expression = a bounded local representation of how an output-like item is shaped for display/inspection.
ReadabilityPredictor = a bounded local predictor over expression features, not a measure of truth, intelligence, language understanding, social success, or agency.
```

Expression evidence may inspect earlier local histories, but must remain local:

```text
OutputHistory / WorldletHistory / ProtoBasicHistory / OperatorTranscript
    -> ExpressionRecord / ReadabilityPrediction
    -> local ExpressionHistory only
```

No reverse mutation is allowed:

```text
ExpressionHistory -> BrainState / MSI / PtCns / registry / tick / PerceptEvent / traces / scenarios  NOT ALLOWED
```

---

# Step 0 — Preflight

Read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
OPERATOR_TUI_AUDIT.md
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
brain/ui/session.py
brain/ui/transcript.py
brain/ui/render.py
```

Run:

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-UI-23
bash tools/check_all.sh
```

Stop if the tree is dirty, full gate fails, or any required audit is absent/not PASS.

---

# Step 1 — Phase 3.5 synthesis

Create `PHASE3_5_EXPRESSION_READABILITY_SYNTHESIS.md`.

Include:

```text
v0.11 baseline summary
why Expression follows Proto-BASIC + Operator TUI
Expression thesis
ReadabilityPredictor thesis
local evidence boundaries
why readability is not truth / language / social success / intelligence
one-way bridge from earlier histories
non-goals
risks
next artifact: PHASE3_5_EXPRESSION_READABILITY_KICKOFF.md
```

Validate:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 2 — Phase 3.5 kickoff

Create `PHASE3_5_EXPRESSION_READABILITY_KICKOFF.md`.

Cover only:

```text
ExpressionSource
ExpressionItem
ExpressionFeatureVector
ExpressionRecord
ReadabilityScore exact Fraction in [0, 1]
ReadabilityPrediction
ReadabilityPredictor
ExpressionHistory
bounded feature extraction from local histories
anti-Goodhart rules
non-mutating inspection of OutputHistory / WorldletHistory / ProtoBasicHistory / OperatorTranscript
```

Do not include real language-model scoring, natural-language teacher/corrector, social feedback, Mode B planning, external corpus, file/network access, PerceptEvent promotion, or TLICA runtime mutation.

Validate and commit/push.

---

# Step 3 — Kickoff corrigenda

Create `PHASE3_5_EXPRESSION_READABILITY_CORRIGENDA.md`.

Check:

```text
expression vs language distinction
readability vs truth distinction
readability vs social success distinction
readability vs agency distinction
feature extraction determinism
bounded exact score discipline
anti-Goodhart requirements
which rows should be REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED
whether ExpressionHistory must remain local only
whether any UI integration is allowed or deferred
```

Validate and commit/push.

---

# Step 4 — Catalog patch plan

Create `PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md`.

Design the future catalog patch without applying it.

Likely row family:

```text
I-EXP-*
```

Likely row themes:

```text
ExpressionSource is a finite closed enumeration
ExpressionItem is bounded printable local evidence
ExpressionFeatureVector is deterministic and exact
ReadabilityScore is Fraction in [0,1]
ReadabilityPrediction is local and source-tagged
valid readability does not imply truth/language/social success
anti-Goodhart prevents score inflation by repetition/length alone
ExpressionHistory is copy-on-write and local
no mutation of BrainState/MSI/PtCns/registry/developmental histories
aggregate expression summaries are OBSERVED only
```

Specify row table, statuses, owning modules, fixture roster, count impact from v0.11, catalog patch mechanics, pending registration plan, strict implementation order, open decisions, and stop conditions.

Validate and commit/push.

---

# Step 5 — Review gate

Do not proceed to Step 6 unless the catalog patch plan is coherent and no open decision blocks implementation.

Stop if the plan requires real LLM calls, external corpus, social/language harness, Mode B planning, truth scoring, host/shell/network/file execution, BrainState/MSI/PtCns mutation, tick() semantic changes, scenario/trace schema changes, new external dependencies, or weakening existing I-* safety rows.

Proceed only when the user says `go` again or explicitly accepts the plan.

---

# Step 6 — Apply accepted catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional package markers only if accepted by the patch plan:

```text
brain/development/expression.py
brain/development/fixtures/expression_core.py
```

Apply only accepted rows, expected count updates, generated IDs, and pending registrations. Do not implement runtime behavior unless explicitly allowed by the accepted plan.

Run:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 7 — Implement expression core

Allowed files depend on accepted plan, likely:

```text
brain/development/expression.py
brain/development/fixtures/expression_core.py
brain/invariants.py
```

Expected behavior:

```text
finite ExpressionSource
bounded ExpressionItem
deterministic ExpressionFeatureVector
no LLM / shell / network / file access
no BrainState mutation
```

Run targeted checks and commit/push.

---

# Step 8 — Implement ReadabilityPredictor

Allowed files likely:

```text
brain/development/expression.py
brain/development/fixtures/readability_predictor.py
brain/invariants.py
```

Expected behavior:

```text
ReadabilityScore exact Fraction in [0,1]
ReadabilityPrediction source-tagged and local
score computed deterministically from ExpressionFeatureVector
valid score does not imply truth/language/social success/intelligence
anti-Goodhart rules for repetition/length/no-op inflation
```

Run targeted checks and commit/push.

---

# Step 9 — Implement ExpressionHistory and local summaries

Allowed files likely:

```text
brain/development/expression.py
brain/development/fixtures/expression_history.py
brain/invariants.py
```

Expected behavior:

```text
copy-on-write ExpressionHistory
bounded local entries
summary inspection only
OBSERVED aggregate row if accepted
no mutation of OutputHistory / WorldletHistory / ProtoBasicHistory / OperatorTranscript
no PerceptEvent/tick promotion
```

Run targeted checks and commit/push.

---

# Step 10 — Optional UI inspection bridge if accepted

Only if the accepted catalog plan explicitly authorizes a UI inspection pane.

Allowed files likely:

```text
brain/ui/render.py
brain/ui/session.py
brain/ui/fixtures/agent_tui_smoke.py
README.md
```

Expected behavior:

```text
UI may display ExpressionHistory summaries
UI must not compute or mutate expression state unless routed through public helper
no new save/export path
no LLM calls
```

Skip this step if the catalog plan defers UI integration.

Run targeted checks and commit/push.

---

# Step 11 — Full gate

Run:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit/push final sync docs if needed.

---

# Step 12 — Post-completion audit

Create `PHASE3_5_EXPRESSION_READABILITY_AUDIT.md`.

Verdict must be PASS / PASS WITH PATCHES / BLOCKED.

Audit scope creep, row registration, expression vs language distinction, readability vs truth/social/agency distinction, score boundedness, anti-Goodhart behavior, history locality, kernel boundary, full gate, and recommended next mission.

Commit/push.

---

## Campaign complete output

```text
Phase 3.5 Expression + ReadabilityPredictor campaign complete.
Catalog: <version>
Counts: <actual>
Full gate: pass
Remaining deferred work: social/language harness, Mode B reflective planning, and later cognitive campaigns
```
