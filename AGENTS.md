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
