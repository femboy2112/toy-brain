# CURRENT_CAMPAIGN.md — Phase 3.4 Proto-BASIC REPL Campaign

## Purpose

This campaign lets any repo-capable model agent proceed through Phase 3.4 without requiring a new `CURRENT_MISSION.md` for every micro-step.

When the user says `go`, the active agent should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
run preflight
find the next eligible campaign step
execute only that step's allowed scope
use test results to choose the next branch
commit and push after each completed step
stop only at explicit gates, failures requiring user judgment, or campaign completion
```

This campaign is bounded to **Phase 3.4 Proto-BASIC REPL** only.

It does not authorize expression/readability, social/language, Mode B, real host execution, open-ended process execution, or arbitrary code execution.

---

## Local command rule

Use `python3 -m ...` for every Python module command.

Do **not** use `python -m ...` unless the user explicitly confirms a `python` alias exists.

If copied instructions say `python -m`, silently convert them to `python3 -m` before running.

---

## Accepted inputs

Treat these repo-local files as accepted inputs unless the user explicitly says otherwise:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
PHASE3_2_OUTPUT_LADDER_AUDIT.md
PHASE3_3_MINIMAL_WORLDLET_SYNTHESIS.md
PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md
PHASE3_3_MINIMAL_WORLDLET_CORRIGENDA.md
PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md
PHASE3_3_MINIMAL_WORLDLET_AUDIT.md
INVARIANT_CATALOG.md
```

Inherited principle:

```text
PRESERVE should be earned, not labeled.
```

Phase 3.3 boundary inherited into Phase 3.4:

```text
Worldlet consequence evidence is local deterministic harness evidence; it is not external reality, reflective agency, language, Mode B, or runtime promotion.
```

Phase 3.4-specific principle:

```text
Proto-BASIC is a constrained local output-worldlet interface. It teaches syntax, near-miss correction, bounded consequence, and proto-agency pressure without host execution, arbitrary code execution, language understanding, or reflective Mode B agency.
```

---

## Current baseline

Current baseline should be v0.8 after the Phase 3.3 Minimal Worldlet campaign.

Expected baseline:

```text
105 REQUIRED
29 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
4 OBSERVED
```

The Phase 3.3 audit reports PASS. `I-WLD-*` rows are green, worldlet responses remain local harness evidence, valence is bounded, and not-I pushback is not an external-reality claim.

---

## Global hard boundaries

Never modify unless a campaign step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

Never implement in this campaign:

```text
real host execution
open-ended process execution
arbitrary Python execution
shell command execution
network I/O
file-system mutation outside local in-memory REPL state
expression layer
readability predictor
social/language harness
Mode B developmental layer
real LLM training behavior
prompt-tuning solely to force the four-tick scenario to pass
seeded-MSI scenario shortcut
```

Do not run real LLM commands unless the user explicitly asks.

---

## Git persistence rule

After every successful campaign step:

```text
stage only intended files
commit with a clear message
push to current branch / main as appropriate
report commit SHA
```

If no files changed, report no commit and why.

If tests fail, fix within the step's allowed scope. If the fix requires files outside the allowed scope, stop and report.

---

## Campaign state detection

The agent should infer completed steps from repo state:

- If `PHASE3_4_PROTO_BASIC_REPL_SYNTHESIS.md` exists, Step 1 may be complete.
- If `PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md` exists, Step 2 may be complete.
- If `PHASE3_4_PROTO_BASIC_REPL_CORRIGENDA.md` exists, Step 3 may be complete.
- If `PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md` exists, Step 4 may be complete.
- If `INVARIANT_CATALOG.md` has v0.9 Proto-BASIC REPL rows and `tools/catalog.py` expected counts match, Step 6 may be complete.
- If `brain/development/repl.py` or equivalent REPL modules exist with targeted rows green, implementation steps may be complete.
- If `PHASE3_4_PROTO_BASIC_REPL_AUDIT.md` exists and full gate is green, the campaign may be complete.

When in doubt, inspect files and tests before deciding.

---

# Step 0 — Preflight

## Purpose

Confirm the repo is ready for Phase 3.4 planning.

## Required reads

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_3_MINIMAL_WORLDLET_AUDIT.md
brain/development/worldlet.py
brain/development/output.py
```

## Commands

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-WLD-12
bash tools/check_all.sh
```

## Branch logic

- If there are uncommitted external changes, stop and report.
- If the full gate fails, do not start Phase 3.4; diagnose within current scope or stop.
- If Phase 3.3 audit is absent or not PASS, stop and report.
- If preflight is green, proceed to Step 1.

---

# Step 1 — Phase 3.4 synthesis

## Purpose

Draft the bridge document explaining why Proto-BASIC REPL follows the Minimal Worldlet.

## Output file

```text
PHASE3_4_PROTO_BASIC_REPL_SYNTHESIS.md
```

## Allowed files

```text
PHASE3_4_PROTO_BASIC_REPL_SYNTHESIS.md
```

## Required contents

Include:

```text
v0.8 Phase 3.3 baseline summary
why a constrained REPL follows worldlet consequence evidence
Proto-BASIC thesis
syntax as bounded worldlet interaction, not language
valid / invalid / near-miss / unavailable / resource-limit / sandbox-fault categories
bounded valence and anti-Goodhart requirements
why this remains below expression, social language, and Mode B
non-goals
expected phase ordering
risks
next artifact: PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md
```

Core thesis:

```text
Proto-BASIC gives the system a deterministic rule-governed output worldlet where syntax, near-miss correction, and bounded consequence can be learned through local feedback. It is not a real interpreter, not host execution, not language understanding, and not reflective agency.
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 2 — Phase 3.4 kickoff

## Purpose

Draft a precise kickoff for the Proto-BASIC REPL implementation plan.

## Output file

```text
PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md
```

## Allowed files

```text
PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md
```

## Required scope

The kickoff should cover only:

```text
ProtoBasicToken
ProtoBasicLine
ProtoBasicProgram / one-line command surface
ProtoBasicParseResult
ProtoBasicCommand
ProtoBasicExecutionResult
ProtoBasicFeedback
ProtoBasicValence bounded in [-1, 1]
ProtoBasicHistory
near-miss correction hints
resource-limit / unavailable / syntax-invalid / semantic-invalid / sandbox-fault categories
anti-Goodhart controls such as diminishing returns and effect-required reward
connection from WorldletHistory / learned output token support to Proto-BASIC attempts
```

Do not include:

```text
real BASIC interpreter
host execution
shell access
file I/O
network I/O
arbitrary Python execution
natural language teacher
expression/readability
social/language harness
Mode B reflective planning
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 3 — Kickoff corrigenda

## Purpose

Review and tighten the kickoff before catalog rows or code.

## Output file

```text
PHASE3_4_PROTO_BASIC_REPL_CORRIGENDA.md
```

## Allowed files

```text
PHASE3_4_PROTO_BASIC_REPL_CORRIGENDA.md
```

## Required issues to check

At minimum:

```text
REPL consequence vs agency distinction
Proto-BASIC syntax vs language distinction
whether the grammar is intentionally tiny and deterministic
whether valid syntax alone is insufficient for strong positive feedback
whether invalid / near-miss / sandbox-fault feedback is bounded
whether repeated no-op spam is prevented by diminishing returns or effect-required reward
whether rows should be REQUIRED / STRUCTURAL / OBSERVED
whether expression/readability/social/Mode B semantics leaked in
whether REPL evidence can ever enter PerceptEvent/tick in this phase or must remain local
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 4 — Catalog patch plan

## Purpose

Design the future v0.9 Phase 3.4 catalog patch without applying it yet.

## Output file

```text
PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md
```

## Allowed files

```text
PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md
```

## Required contents

Specify:

```text
proposed row families, likely I-REPL-*
row IDs, statuses, owning modules, fixtures
count impact from current v0.8
fixture roster
owning module map
catalog patch mechanics
strict implementation order
open decisions
stop condition
```

Likely row themes:

```text
grammar is finite and deterministic
parse result distinguishes valid, near-miss, syntax-invalid, semantic-invalid, tool-unavailable, resource-limit, sandbox-fault
feedback valence is exact and bounded in [-1, 1]
valid syntax alone does not grant strong positive feedback
valid-effective commands produce bounded positive feedback
invalid / fault cases produce bounded negative feedback
near-miss correction hints are structured local feedback, not language understanding
history is copy-on-write and local
REPL operations do not call tick(), emit PerceptEvent, or mutate TLICA runtime state
anti-Goodhart prevents repeated no-op spam from dominating
```

Do not apply the catalog patch in this step.

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 5 — Review gate before implementation

## Purpose

Do not automatically apply the v0.9 catalog patch unless the catalog patch plan is coherent and no open decision blocks implementation.

## Branch logic

- If the catalog patch plan contains unresolved blockers, stop and report.
- If the plan is coherent and internally complete, the agent may proceed to Step 6 when the user says `go` again.
- If the user explicitly says the plan is accepted, proceed to Step 6 in the same campaign.

This is an explicit review gate.

---

# Step 6 — Apply accepted v0.9 catalog patch

## Purpose

Apply the accepted Proto-BASIC REPL catalog rows.

## Allowed files

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/development/fixtures/__init__.py
```

Only create module/fixture placeholders if necessary for registry coherence. Do not implement full REPL behavior in this step unless the plan explicitly allows it.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push when catalog and generated IDs are coherent. If I-CAT-01 requires fixture registration immediately, create minimal intentional fixture registrations only within the accepted plan.

---

# Step 7 — Implement grammar/parser/feedback boundary rows

## Purpose

Implement the deterministic syntax and feedback surface.

## Allowed files

```text
brain/development/repl.py
brain/development/fixtures/repl_grammar.py
brain/development/fixtures/repl_feedback.py
brain/invariants.py
brain/_catalog_ids.py
```

## Expected behavior

```text
finite command grammar
parse result categories
near-miss correction hint structure
bounded feedback valence
no language/social/Mode B fields
no TLICA runtime mutation
```

Run targeted rows from the accepted plan and commit/push when green.

---

# Step 8 — Implement command execution / history rows

## Purpose

Implement deterministic local command execution below host execution.

## Allowed files

```text
brain/development/repl.py
brain/development/fixtures/repl_execution.py
brain/development/fixtures/repl_history.py
brain/invariants.py
```

## Expected behavior

```text
valid-effective command changes only ProtoBasicHistory
valid-ineffective command receives weak/non-strong feedback
syntax-invalid and semantic-invalid are bounded
resource-limit and sandbox-fault are bounded and local
no shell, no host process, no file I/O, no network I/O
```

Commit/push when targeted checks pass.

---

# Step 9 — Implement anti-Goodhart / local evidence rows if authorized

## Purpose

Represent anti-Goodhart constraints only if the accepted catalog plan includes them.

## Stop logic

If the accepted plan defers anti-Goodhart to a later phase, skip this step and proceed to full gate.

If included, keep it deterministic and local.

Allowed behavior:

```text
diminishing returns for repeated no-op / repeated identical command
strong positive feedback requires effect, not syntax alone
history summaries are local evidence only
no PerceptEvent promotion unless explicitly authorized by the accepted plan
```

Commit/push when targeted checks pass.

---

# Step 10 — Full gate

## Purpose

Verify the whole repo after Phase 3.4 rows are implemented.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit/push any final sync docs if needed.

---

# Step 11 — Post-completion audit

## Purpose

Audit Phase 3.4 after implementation.

## Output file

```text
PHASE3_4_PROTO_BASIC_REPL_AUDIT.md
```

## Required verdict

```text
PASS
PASS WITH PATCHES
BLOCKED
```

Audit:

```text
scope creep
row-family registration
syntax vs language distinction
execution vs host execution distinction
bounded feedback / valence
anti-Goodhart behavior
kernel boundary
full gate
recommended next mission
```

Commit/push the audit.

---

## Stop conditions requiring user review

Stop and report if:

```text
a fix requires editing brain/tlica/
a fix requires changing tick() semantics
a fix requires changing scenario schema
a fix requires real LLM execution
a test failure suggests the campaign plan itself is wrong
real host execution becomes necessary
open-ended process execution becomes necessary
arbitrary Python/shell/file/network execution becomes necessary
expression/readability semantics become necessary
social-language semantics become necessary
Mode B reflective planning becomes necessary
there are uncommitted external changes
```

---

## Campaign complete output

When complete, report:

```text
Phase 3.4 Proto-BASIC REPL campaign complete.
Catalog: <version>
Counts: <actual>
Full gate: pass
Commits: <list>
Remaining deferred work: expression/readability, social/language harness, Mode B, and later phases
```
