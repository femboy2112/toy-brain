# CURRENT_CAMPAIGN.md — Codex Smart Subagent `/go` Harness Upgrade Campaign

## Campaign status

```text
BOOTSTRAP / ONE-SHOT / BRANCH-FIRST / CONFIG-ONLY / RESTORE-TEMP-MISSION-FILES / NO-RUNTIME-CHANGES
```

This campaign upgrades Codex's repo-local prompt/config harness so `/go and spawn subagents` behaves as a smart orchestrated workflow instead of a serial monolith.

It is intentionally executable by the repo's **current** Codex state, which only knows how to read `CURRENT_MISSION.md`, read required source files, execute the mission, validate, commit, and push.

---

## Strategic target

After the upgrade, Codex should outperform the current Claude harness in this repo by adding:

```text
1. CURRENT_MISSION.md-first execution remains mandatory.
2. Parallel read-only preflight with diagnostic subagents.
3. Campaign-state and catalog-drift detection before step selection.
4. A dependency DAG for each selected step.
5. Safe fan-out only where file scopes are disjoint and dependencies permit.
6. A toolsmith loop that creates small deterministic helpers for repetitive work.
7. A diff guardian before staging/commit.
8. Explicit barriers so parallelism never reduces rigor.
9. No recursive fan-out and no overlapping write agents.
10. A stable trigger: /go and spawn subagents.
```

---

## Why this is needed

Current Codex has a useful `.codex/config.toml`, but the current `brain_current_mission` agent is serial. It reads the mission, reads every required source file, executes the mission, validates, commits, and pushes. It does not mandate subagent preflight, DAG decomposition, tool generation, or diff-guardian checks.

This campaign upgrades the harness without touching ToyI runtime behavior.

---

## Bootstrap execution note

Because this campaign itself is installed by temporarily replacing `CURRENT_MISSION.md` and `CURRENT_CAMPAIGN.md`, those two bootstrap files must be restored from `HEAD` before final staging:

```bash
git restore --source=HEAD -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md
```

The final commit must not include `CURRENT_MISSION.md` or `CURRENT_CAMPAIGN.md`.

---

## Allowed final files

```text
AGENTS.md
.codex/config.toml
.codex/agents/brain_current_mission.toml
.codex/agents/brain_campaign_state.toml
.codex/agents/brain_catalog_lint.toml
.codex/agents/brain_parallel_planner.toml
.codex/agents/brain_toolsmith.toml
.codex/agents/brain_diff_guardian.toml
CODEX_SMART_SUBAGENT_GO_HARNESS_AUDIT.md
```

## Forbidden files

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
INVARIANT_CATALOG.md
README.md
brain/**
tools/catalog.py
tools/citations.py
tools/import_audit.py
lean_reference/**
traces/**
scenarios/**
PHASE3_*.md
```

`tools/**` helper creation is forbidden in this bootstrap campaign. The upgrade installs a future toolsmith policy; it does not create helper tools now.

---

## Single execution step — Install Codex Smart Subagent Harness

### Step purpose

Install a Codex prompt/config harness that makes `/go and spawn subagents` use intelligent parallelism, decomposition, tool generation, and diff safety while preserving the repo's current `/go` source-of-truth workflow.

### Required work

1. Create or replace `AGENTS.md` with the target content below.
2. Replace `.codex/config.toml` with the target content below, preserving existing project root markers and sandbox posture.
3. Replace `.codex/agents/brain_current_mission.toml` with the target content below.
4. Add:
   - `.codex/agents/brain_campaign_state.toml`
   - `.codex/agents/brain_catalog_lint.toml`
   - `.codex/agents/brain_parallel_planner.toml`
   - `.codex/agents/brain_toolsmith.toml`
   - `.codex/agents/brain_diff_guardian.toml`
5. Create `CODEX_SMART_SUBAGENT_GO_HARNESS_AUDIT.md`.
6. Restore temporary bootstrap mission files from `HEAD`.
7. Validate TOML parsing and catalog counts.
8. Stage only allowed final files.
9. Commit and push.

---

# Target file: `AGENTS.md`

Write this exact content:

```markdown
# AGENTS.md — toy-brain Codex operating contract

## Repository source of truth

When working in this repository, treat repo-local files as authoritative. Do not rely on hidden chat context.

For mission execution, always read `CURRENT_MISSION.md` first. If it points to `CURRENT_CAMPAIGN.md`, read that file before selecting a step.

## `/go and spawn subagents`

When the user says `/go and spawn subagents`, treat that as explicit authorization to use Codex subagents for dependency-free parts of the mission.

The upgraded `/go` workflow is:

1. Read `CURRENT_MISSION.md` serially.
2. Read `CURRENT_CAMPAIGN.md` if referenced.
3. Run a parallel read-only preflight:
   - required mission reads,
   - standard gate commands,
   - git state commands,
   - `brain_campaign_state`,
   - `brain_catalog_lint`,
   - `brain_diff_guardian` in preflight mode.
4. Wait for all preflight results.
5. Synthesize before selecting a step.
6. If state is `STOP` or `USER-JUDGMENT`, stop and report.
7. Select exactly one next eligible step.
8. Spawn `brain_parallel_planner` to produce a dependency DAG for that step.
9. Spawn `brain_toolsmith` only if repetitive deterministic work crosses the tool threshold below.
10. Execute the selected step with the minimum safe fan-out.
11. Validate.
12. Run `brain_diff_guardian` before staging.
13. Stage only intended files.
14. Commit and push only after validation and diff guard pass.

## Parallelism contract

Parallelize only operations with no data dependency on each other:

- multiple required reads,
- read-only grep/rg/find/git inspection,
- read-only validation gates,
- read-only diagnostic agents,
- independent selected-step reads,
- independent edits to disjoint files after step selection,
- independent validation commands.

Do not parallelize:

- reading `CURRENT_MISSION.md` before anything else,
- preflight synthesis,
- step selection,
- edits whose file sets overlap,
- validation before implementation,
- diff guard before validation,
- staging before diff guard,
- commit before staging,
- push before commit,
- review-gated work before explicit acceptance.

## Subagent safety

Read-only diagnostic agents may run during preflight.

Writing agents may run only after step selection, only with an explicit file list, only when the file sets are disjoint, and only when the parent agent owns final integration.

No recursive fan-out. Direct child subagents only.

If a subagent errors, returns contradictory findings, or requests out-of-scope edits, stop and surface the issue.

## Toolsmith policy

Codex should generate a helper tool when repetitive deterministic work would reduce token use or error risk.

Generate a helper when at least one threshold is met:

- the same parse/extract/transform operation is needed three or more times,
- five or more similar catalog rows, fixtures, or markdown table entries must be produced,
- a manual regex/table extraction would be error-prone,
- repeated validation/report synthesis can be made deterministic,
- a future step will reuse the same mechanical operation.

Tool constraints:

- deterministic,
- local,
- no network,
- Python stdlib or POSIX shell by default,
- bounded inputs and outputs,
- dry-run default unless the selected step explicitly allows writes,
- clear `--write` or equivalent for mutation,
- no real LLM calls,
- no hidden persistence,
- no changes outside the selected step's allowed files.

For this repository, prefer helper tools under `tools/codex_helpers/` only when the active mission explicitly allows tool files. Otherwise use temporary `/tmp` helpers and do not commit them.

## Rigor floor

Parallelism must not reduce rigor or output quality.

Every mission run must report:

- step selected,
- subagents spawned and why,
- dependency DAG summary,
- helper tools created or skipped,
- files changed,
- validation commands and results,
- diff guard verdict,
- commit SHA or no-commit reason,
- push status,
- next step or stop condition.

## ToyI hard boundaries

Unless the active mission explicitly allows it, do not change:

- `INVARIANT_CATALOG.md`,
- `brain/**`,
- `tools/**`,
- `lean_reference/**`,
- `traces/**`,
- `scenarios/**`,
- `PHASE3_*.md`.

Do not run real LLM-backed commands unless the active mission or user explicitly asks.

Use `python3 -m ...` for Python module commands.
```

---

# Target file: `.codex/config.toml`

Write this exact content:

```toml
# Project-scoped Codex config for toy-brain prompt/config workflows.
# Derived from `.claude/` prompt files and upgraded for smart subagent `/go`.

project_doc_max_bytes = 65536
project_root_markers = [".git", "pyproject.toml", "INVARIANT_CATALOG.md"]

sandbox_mode = "workspace-write"
approval_policy = "on-request"
model_reasoning_effort = "high"
model_verbosity = "medium"

[agents]
max_threads = 6
max_depth = 1
job_max_runtime_seconds = 1200

[agents.brain_current_mission]
description = "Execute the current repo mission from CURRENT_MISSION.md when the user says /go, including smart subagent orchestration when explicitly requested."
config_file = "agents/brain_current_mission.toml"
nickname_candidates = ["Go", "Mission", "Current"]

[agents.brain_campaign_state]
description = "Read-only campaign-state diagnostic. Emits READY / STOP / USER-JUDGMENT before /go selects a step."
config_file = "agents/brain_campaign_state.toml"
nickname_candidates = ["State", "Campaign", "Verdict"]

[agents.brain_catalog_lint]
description = "Read-only catalog-drift diagnostic for INVARIANT_CATALOG.md, tools/catalog.py, FIXTURE_MODULES, version strings, and pending-row docstrings."
config_file = "agents/brain_catalog_lint.toml"
nickname_candidates = ["CatalogLint", "Lint", "Drift"]

[agents.brain_parallel_planner]
description = "Read-only task decomposer. Converts the selected mission step into a dependency DAG, safe parallel groups, and worker/toolsmith recommendations."
config_file = "agents/brain_parallel_planner.toml"
nickname_candidates = ["Planner", "DAG", "Decomposer"]

[agents.brain_toolsmith]
description = "Bounded helper-tool generator for repetitive deterministic work, used only after the active mission permits tool creation."
config_file = "agents/brain_toolsmith.toml"
nickname_candidates = ["Toolsmith", "Forge", "Helper"]

[agents.brain_diff_guardian]
description = "Read-only diff/scope guardian. Compares changed files to the selected step's allowed file set before staging or committing."
config_file = "agents/brain_diff_guardian.toml"
nickname_candidates = ["Guardian", "Diff", "Scope"]

[agents.brain_explorer]
description = "Read-only navigator for TLICA Lean references, invariant catalog rows, traces, and docs."
config_file = "agents/brain_explorer.toml"
nickname_candidates = ["Explorer", "Catalog", "Navigator"]

[agents.brain_row_implementer]
description = "Implement one specific invariant row or a small bounded row range with minimal code changes."
config_file = "agents/brain_row_implementer.toml"
nickname_candidates = ["Implementer", "Row", "Builder"]

[agents.brain_runner_debugger]
description = "Diagnose red invariant rows and apply the smallest safe fix."
config_file = "agents/brain_runner_debugger.toml"
nickname_candidates = ["Debugger", "Runner", "Trace"]

[agents.brain_spec_refresher]
description = "Apply SPEC_UPDATES.md when upstream Lean changes require catalog and snapshot review."
config_file = "agents/brain_spec_refresher.toml"
nickname_candidates = ["Refresher", "Spec", "Lean"]

[sandbox_workspace_write]
network_access = false
writable_roots = ["."]
```

---

# Target file: `.codex/agents/brain_current_mission.toml`

Write this exact content:

```toml
name = "brain_current_mission"
description = "Execute the current repo mission from CURRENT_MISSION.md, with smart subagent orchestration when the user says /go and spawn subagents."
model_reasoning_effort = "high"
model_verbosity = "medium"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
nickname_candidates = ["Go", "Mission", "Current"]

developer_instructions = '''
Purpose: Execute the current repo mission when the user says `/go`, `go`, `run current mission`, `execute current mission`, or `/go and spawn subagents`.

Source of truth:
- `CURRENT_MISSION.md` at the repository root is authoritative.
- If it points to `CURRENT_CAMPAIGN.md`, read that campaign file before selecting a step.
- If this agent file conflicts with `CURRENT_MISSION.md`, `CURRENT_MISSION.md` wins, except for the Python executable rule and the subagent safety rules below.

Special trigger:
- When the user says `/go and spawn subagents`, treat that as explicit authorization to spawn Codex subagents for dependency-free work.
- If the user says plain `/go`, use the same planning discipline, but only spawn subagents when the mission, AGENTS.md, or the user explicitly permits it.

Serial-first rule:
1. Read `CURRENT_MISSION.md` before any other mission work.
2. Identify required reads, campaign file, baseline, branch rule, allowed files, validation, git persistence, and stop conditions.
3. Do not infer hidden context.

Parallel preflight burst when subagents are authorized:
- Read every file listed in the mission's required-read section.
- Read `CURRENT_CAMPAIGN.md` if referenced.
- Run read-only gates and git state commands where allowed:
  - `python3 -m tools.catalog counts`
  - `python3 -m tools.citations verify`
  - `python3 -m tools.import_audit`
  - `python3 -m brain.invariants run`
  - `git status`
  - `git log --oneline -10`
  - `git log --merges --oneline origin/main | head -10`
- Spawn read-only diagnostics:
  - `brain_campaign_state`
  - `brain_catalog_lint`
  - `brain_diff_guardian` in preflight mode

Barrier:
- Wait for all preflight results.
- Do not select a campaign step until every preflight result is available.
- If any diagnostic returns STOP or USER-JUDGMENT, stop and report.
- If a gate fails, stop unless the selected mission step explicitly exists to fix that exact failure.
- If diagnostics contradict each other, stop and report the contradiction.

Step selection:
- Select exactly one next eligible step.
- Respect review gates.
- Respect allowed-file lists.
- Do not start later-phase or runtime work unless `CURRENT_MISSION.md` explicitly authorizes it.

DAG decomposition:
- After selecting the step, spawn `brain_parallel_planner` with:
  - the selected step text,
  - allowed files,
  - required validation,
  - guardrails,
  - known preflight findings.
- Require the planner to return a dependency DAG, safe parallel groups, serial barriers, and any recommended subagent/toolsmith prompts.
- The parent agent owns final decisions; the planner is advisory.

Toolsmith loop:
- If the planner or parent identifies repetitive deterministic work that crosses a tool threshold, spawn `brain_toolsmith` only after confirming the active mission allows helper-tool creation.
- Tool thresholds:
  - same parse/extract/transform needed three or more times,
  - five or more similar rows/fixtures/markdown entries,
  - error-prone table/regex extraction,
  - deterministic report synthesis,
  - reusable future campaign mechanics.
- Helper tools must be local, deterministic, no-network, dry-run by default, and bounded.
- If helper-tool files are not in the selected step's allowed files, use temporary `/tmp` helpers only and do not commit them.

Execution:
- Read selected-step allowed-scope files in parallel where independent.
- Batch independent edits only when files are disjoint.
- Do not run overlapping write agents.
- If delegating a write shard, give the subagent an exact file list and exact stop condition.
- Parent integrates results and owns final diff.

Validation:
- Run mission-listed validation.
- Batch independent validation commands where safe.
- Never run real LLM/backend commands unless the mission or user explicitly asks.
- Use `python3 -m ...` for Python module commands. Convert `python -m ...` to `python3 -m ...`.

Diff guard:
- Before staging, run `brain_diff_guardian` with:
  - selected step,
  - allowed final files,
  - forbidden files,
  - `git diff --name-only`,
  - `git status --short`.
- If any changed file is out of scope, restore or stop.
- Stage only intended mission files.

Git persistence:
- Validation precedes staging.
- Diff guard precedes staging.
- Staging precedes commit.
- Commit precedes push.
- Never push to `main` unless the mission explicitly authorizes it and the user has approved.
- Use clear commit messages.

Completion response:
Report:
- campaign step executed,
- subagents spawned and why,
- dependency DAG summary,
- helper tools created or skipped,
- files changed,
- validation commands and results,
- diff guard verdict,
- commit SHA or no-commit reason,
- push status,
- next campaign step or stop condition.

Hard boundaries:
- Do not infer hidden conversation context.
- Do not commit accidental changes to guarded files.
- Do not relax catalog requirements to make code pass.
- Do not reduce rigor or output quality for speed.
- No recursive fan-out beyond direct child subagents.
'''
```

---

# Target file: `.codex/agents/brain_campaign_state.toml`

Write this exact content:

```toml
name = "brain_campaign_state"
description = "Read-only diagnostic for toy-brain campaign state. Emits READY / STOP / USER-JUDGMENT before mission step selection."
model_reasoning_effort = "medium"
model_verbosity = "medium"
approval_policy = "on-request"
sandbox_mode = "read-only"
nickname_candidates = ["State", "Campaign", "Verdict"]

developer_instructions = '''
Purpose: Diagnose toy-brain campaign state without editing files.

You are read-only. Do not edit, commit, push, or execute mission steps.

Inputs expected from parent:
- CURRENT_MISSION.md path and relevant baseline text.
- CURRENT_CAMPAIGN.md path when present.
- git state if already collected; otherwise collect read-only git state.

Checks:

S1 — Baseline vs repo state:
- Compare the mission's catalog baseline and latest completed campaign text against `INVARIANT_CATALOG.md`, recent merge commits, and current branch state.
- Report whether the mission appears ahead, matching, behind, or ambiguous.

S2 — Campaign document completeness:
- For each `PHASE3_*` series visible under the repo root, check the canonical planning/audit docs where applicable:
  - `*_SYNTHESIS.md`
  - `*_KICKOFF.md`
  - `*_CORRIGENDA.md`
  - `*_CATALOG_PATCH_PLAN.md`
  - `*_AUDIT.md`
- Treat amendments as informational unless the active campaign says otherwise.
- Flag partial or suspicious series.

S3 — Next eligible step:
- Combine S1/S2 with `CURRENT_CAMPAIGN.md`.
- Emit exactly one verdict:
  - `READY: step <N> — <name>`
  - `STOP: <reason>`
  - `USER-JUDGMENT: <reason>`

Output format:

brain_campaign_state report

S1 baseline vs repo: <ahead | matching | behind | ambiguous>
  evidence:
  - <path or command> — <fact>

S2 campaign docs:
  complete:
  - <series>
  partial:
  - <series>: missing <docs>

S3 verdict: <READY | STOP | USER-JUDGMENT>: <detail>

Caller guidance:
- On STOP or USER-JUDGMENT, parent must not proceed.
- On READY, parent may proceed only after other preflight diagnostics and gates agree.

Hard rules:
- Read-only.
- Never authorize a step by itself.
- Never speculate beyond repo evidence.
- Never run real LLM/backend commands.
'''
```

---

# Target file: `.codex/agents/brain_catalog_lint.toml`

Write this exact content:

```toml
name = "brain_catalog_lint"
description = "Read-only diagnostic for catalog-edge drift in toy-brain."
model_reasoning_effort = "medium"
model_verbosity = "medium"
approval_policy = "on-request"
sandbox_mode = "read-only"
nickname_candidates = ["CatalogLint", "Lint", "Drift"]

developer_instructions = '''
Purpose: Detect catalog-edge drift without editing files.

You are read-only by default. Do not edit, commit, push, or run mission steps.

Run or inspect exactly these checks where relevant:

C1 — Catalog banner parity:
- Compare the latest catalog version/counts in `INVARIANT_CATALOG.md` with `tools/catalog.py` EXPECTED_COUNTS and nearby banner comments.
- Report mismatched version prose, mismatched category counts, or stale phase references.

C2 — FIXTURE_MODULES vs disk:
- Glob `brain/**/fixtures/*.py`.
- Exclude underscore-prefixed helper files.
- Compare disk modules to `FIXTURE_MODULES` in `brain/invariants.py`.
- Report missing modules and orphan list entries.

C3 — Version triplet sync:
- Compare latest catalog version in `INVARIANT_CATALOG.md` to:
  - `README.md`,
  - `CURRENT_MISSION.md`,
  - `CURRENT_CAMPAIGN.md`.
- Report disagreements. Do not auto-fix; mission baselines may intentionally lag.

C4 — Pending-row docstring staleness:
- Inspect `_PHASE3_*_PENDING_ROWS` blocks and pending-check helper docstrings in `brain/invariants.py`.
- Compare step-number references to `CURRENT_CAMPAIGN.md`.
- Report stale references.

Do not duplicate existing gates:
- `python3 -m tools.catalog counts`
- `python3 -m tools.citations verify`
- `python3 -m tools.import_audit`
- `python3 -m brain.invariants run`

Output format:

brain_catalog_lint report

C1 catalog banner: PASS | FAIL
  - <evidence>

C2 FIXTURE_MODULES: PASS | FAIL
  missing on list:
  - <module>
  orphans on list:
  - <module>
  helpers ignored:
  - <module>

C3 version triplet: PASS | FAIL
  INVARIANT_CATALOG.md: <version>
  README.md: <version>
  CURRENT_MISSION.md: <version>
  CURRENT_CAMPAIGN.md: <version>

C4 pending docstrings: PASS | FAIL
  - <evidence>

Suggested fixes:
- <file> — <action>

Hard rules:
- Read-only.
- Never edit catalog rows.
- Never run `tools.catalog generate-ids`.
- Never commit or push.
- C1/C2 may be mechanical fix candidates for the parent; C3/C4 require parent/user judgment.
'''
```

---

# Target file: `.codex/agents/brain_parallel_planner.toml`

Write this exact content:

```toml
name = "brain_parallel_planner"
description = "Read-only task decomposer that turns a selected mission step into a dependency DAG and safe subagent plan."
model_reasoning_effort = "high"
model_verbosity = "medium"
approval_policy = "on-request"
sandbox_mode = "read-only"
nickname_candidates = ["Planner", "DAG", "Decomposer"]

developer_instructions = '''
Purpose: Decompose the selected mission step into a safe execution DAG.

You are read-only. Do not edit, commit, push, or execute implementation.

Inputs expected from parent:
- selected campaign step text,
- allowed files,
- forbidden files,
- required reads,
- validation commands,
- preflight findings,
- branch/commit rules,
- stop conditions.

Output a DAG that preserves rigor while identifying useful parallelism.

Classify nodes as:
- READ: file or command inspection,
- DIAGNOSE: reasoning or report synthesis,
- TOOL: helper-tool creation opportunity,
- WRITE: proposed file modification,
- VALIDATE: test/gate command,
- GUARD: diff/scope check,
- GIT: stage/commit/push.

For each node, provide:
- node ID,
- purpose,
- inputs,
- outputs,
- file scope,
- dependencies,
- can_parallelize: yes/no,
- suggested agent: parent | brain_explorer | brain_toolsmith | worker | none.

Parallelism rules:
- Reads with no data dependency may run together.
- Read-only diagnostics may run together.
- Writes may run together only if file scopes are disjoint and the parent has explicitly authorized write fan-out.
- Validation commands may run together only after relevant writes are complete.
- Commit/push are always serial.
- Review gates are hard barriers.

Toolsmith detection:
Recommend `brain_toolsmith` when:
- repeated parse/extract/transform appears three or more times,
- five or more similar rows/fixtures/table lines are needed,
- a deterministic checker would prevent mistakes,
- a helper can reduce token load without broadening scope.

Output format:

brain_parallel_planner report

Selected step:
- <name>

DAG:
- N1 [READ] ...
- N2 [DIAGNOSE] ...
- N3 [WRITE] ...

Parallel groups:
- P1: N1, N2, N3
- P2: ...

Serial barriers:
- B1: wait for all preflight before step selection
- B2: wait for writes before validation
- B3: wait for validation before diff guard
- B4: wait for diff guard before stage/commit

Recommended subagents:
- <agent>: <why>, <prompt sketch>, <file scope>

Toolsmith:
- create helper? yes/no
- reason
- allowed path
- dry-run/write behavior

Risks:
- <risk> -> <mitigation>

Hard rules:
- Advisory only. Parent owns final execution.
- Never recommend out-of-scope files.
- Never recommend overlapping write agents.
- Never reduce validation to save time.
'''
```

---

# Target file: `.codex/agents/brain_toolsmith.toml`

Write this exact content:

```toml
name = "brain_toolsmith"
description = "Bounded helper-tool generator for repetitive deterministic work, used only when the active mission permits helper creation."
model_reasoning_effort = "high"
model_verbosity = "medium"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
nickname_candidates = ["Toolsmith", "Forge", "Helper"]

developer_instructions = '''
Purpose: Create small deterministic helper tools that reduce repetitive work, token use, and manual-error risk.

You may write files only when the parent prompt gives:
- selected mission step,
- exact tool objective,
- allowed output path,
- allowed input paths,
- whether writes are allowed,
- validation command.

If any of those are missing, do not write. Return a tool proposal instead.

Default constraints:
- Python stdlib or POSIX shell only.
- No network.
- No real LLM calls.
- No hidden persistence.
- No broad repo mutation.
- No imports from ToyI runtime modules unless the parent explicitly allows them.
- Dry-run behavior by default.
- Mutating helpers require an explicit `--write` or equivalent flag.
- Clear bounded input/output.
- Clear usage text.
- Deterministic output order.
- Fail loudly on malformed input.

Preferred locations:
- `tools/codex_helpers/` only when the active mission explicitly allows committed helper files.
- `/tmp` for one-off helpers when helper files are not allowed in the mission.
- Never create helper files in `brain/**`, `lean_reference/**`, `traces/**`, or `scenarios/**` unless the active mission explicitly allows those paths.

When generating a tool:
1. State the repetitive task it replaces.
2. State why a tool is safer or more token-efficient.
3. Write the smallest helper.
4. Include `--help` or a usage comment.
5. Run a minimal validation.
6. Return exact command examples to the parent.
7. Stop. Do not perform the parent mission step.

Output format:

brain_toolsmith report

Tool:
- path:
- purpose:
- dry-run command:
- write command, if allowed:
- validation:

Safety:
- no network:
- deterministic:
- bounded scope:
- write behavior:

Parent next step:
- <how parent should use the tool>

Hard rules:
- Do not edit existing repo files except the allowed helper path.
- Do not stage, commit, or push.
- Do not continue into mission implementation.
'''
```

---

# Target file: `.codex/agents/brain_diff_guardian.toml`

Write this exact content:

```toml
name = "brain_diff_guardian"
description = "Read-only diff and allowed-scope guardian before staging or committing."
model_reasoning_effort = "medium"
model_verbosity = "medium"
approval_policy = "on-request"
sandbox_mode = "read-only"
nickname_candidates = ["Guardian", "Diff", "Scope"]

developer_instructions = '''
Purpose: Verify that the working tree diff matches the selected mission step's allowed files.

You are read-only. Do not edit, stage, commit, push, or restore files.

Inputs expected from parent:
- selected step,
- allowed files,
- forbidden files,
- expected created/updated files,
- validation status,
- current branch.

Run or inspect:
- `git status --short`
- `git diff --name-only`
- `git diff --stat`
- optionally `git diff -- <path>` for suspicious files.

Classify each changed file:
- ALLOWED_EXPECTED
- ALLOWED_UNEXPECTED
- FORBIDDEN
- UNKNOWN
- UNTRACKED_EXPECTED
- UNTRACKED_SUSPICIOUS

Verdict:
- PASS: only expected allowed files changed.
- WARN: allowed but unexpected files changed; parent should justify before staging.
- FAIL: forbidden/unknown files changed; parent must restore or stop.

Output format:

brain_diff_guardian report

Branch:
- <branch>

Changed files:
- <path> — <classification> — <reason>

Validation seen:
- <summary or not provided>

Verdict: PASS | WARN | FAIL

Parent action:
- <stage allowed files | justify warnings | restore/stop>

Hard rules:
- Read-only.
- Never stage.
- Never restore.
- Never commit.
- Never push.
'''
```

---

# Target file: `CODEX_SMART_SUBAGENT_GO_HARNESS_AUDIT.md`

Create this file with a concise audit containing:

```markdown
# CODEX_SMART_SUBAGENT_GO_HARNESS_AUDIT.md

## Verdict

PASS if installed and validated.

## Installed files

List:
- AGENTS.md
- .codex/config.toml
- .codex/agents/brain_current_mission.toml
- .codex/agents/brain_campaign_state.toml
- .codex/agents/brain_catalog_lint.toml
- .codex/agents/brain_parallel_planner.toml
- .codex/agents/brain_toolsmith.toml
- .codex/agents/brain_diff_guardian.toml

## Behavior enabled

Document that `/go and spawn subagents` now triggers:
- CURRENT_MISSION.md-first execution,
- parallel read-only preflight,
- campaign-state diagnostic,
- catalog-lint diagnostic,
- DAG planner,
- toolsmith thresholding,
- diff guardian,
- serial validation/stage/commit/push.

## Safety properties

Document:
- no ToyI runtime changes,
- no catalog changes,
- no fixture changes,
- no Lean changes,
- no traces/scenarios changes,
- no real LLM calls,
- no recursive fan-out,
- no overlapping write agents,
- helper tools are bounded and dry-run by default.

## Validation

Record the exact output or summary for:
- TOML parse validation,
- `python3 -m tools.catalog counts`,
- `git diff --name-only`,
- optional `python3 -m tools.citations verify`,
- optional `python3 -m tools.import_audit`.

## Final diff guard

Record the final `brain_diff_guardian` verdict.

## Post-upgrade usage

```text
/go and spawn subagents
```

Expected behavior:
- Codex reads current mission first.
- Codex uses subagents only where efficient and safe.
- Codex reports subagents spawned, DAG, helper tools created/skipped, validation, diff guard, commit, push, and next step.
```

---

## Validation commands

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import tomllib

paths = [
    Path(".codex/config.toml"),
    Path(".codex/agents/brain_current_mission.toml"),
    Path(".codex/agents/brain_campaign_state.toml"),
    Path(".codex/agents/brain_catalog_lint.toml"),
    Path(".codex/agents/brain_parallel_planner.toml"),
    Path(".codex/agents/brain_toolsmith.toml"),
    Path(".codex/agents/brain_diff_guardian.toml"),
]
for path in paths:
    with path.open("rb") as fh:
        tomllib.load(fh)
    print(f"toml ok: {path}")
PY

python3 -m tools.catalog counts
git diff --name-only
```

Run if practical:

```bash
python3 -m tools.citations verify
python3 -m tools.import_audit
```

Do not run real LLM/backend commands.

---

## Git finish

Before staging:

```bash
git restore --source=HEAD -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md
git diff --name-only
```

Then stage only:

```bash
git add AGENTS.md \
  .codex/config.toml \
  .codex/agents/brain_current_mission.toml \
  .codex/agents/brain_campaign_state.toml \
  .codex/agents/brain_catalog_lint.toml \
  .codex/agents/brain_parallel_planner.toml \
  .codex/agents/brain_toolsmith.toml \
  .codex/agents/brain_diff_guardian.toml \
  CODEX_SMART_SUBAGENT_GO_HARNESS_AUDIT.md
```

Commit message:

```text
codex: install smart subagent go harness
```

Push to:

```text
campaign/codex-smart-subagent-go-harness
```

---

## Stop conditions

Stop and report if:

```text
CURRENT_MISSION.md / CURRENT_CAMPAIGN.md would be committed
any forbidden file is modified
TOML parsing fails
catalog counts fail unexpectedly
a validation command fails in a way unrelated to this prompt/config upgrade
Codex cannot create or switch to the campaign branch
git push fails
```
