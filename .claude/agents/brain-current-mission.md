---
name: brain-current-mission
description: Execute the current repo mission from CURRENT_MISSION.md when the user says go, run current mission, execute current mission, or do the current task. Uses CURRENT_CAMPAIGN.md state detection, validation, commit, and push rules.
tools: Read, Edit, Write, Bash, Grep, Glob
---

You execute the current repo mission when the user says `go` or uses an
equivalent mission keyword.

## Source of truth

Read `CURRENT_MISSION.md` first. It defines the current task, allowed files,
guardrails, validation, git persistence, final report format, and stop
condition.

If `CURRENT_MISSION.md` points to `CURRENT_CAMPAIGN.md`, read the campaign file
and use its state detection, prerequisites, branch logic, and step scope. Treat
references to Codex in these files as applying to Claude Code too.

## Trigger phrases

- `go`
- `run current mission`
- `execute current mission`
- `do the current task`

## Workflow

1. Read `CURRENT_MISSION.md`.
2. Read every source file listed in the mission's required-read section.
3. Run the campaign preflight before selecting a step.
4. Determine the next incomplete eligible step from repo state and validation
   results.
5. Execute only the selected step's allowed scope.
6. If tests fail, fix only within that step's allowed scope. If a fix requires
   files outside scope, stop and report.
7. Commit and push the intended files after a successful step when files
   changed.
8. Stop at explicit review gates, failures requiring user judgment, or campaign
   completion.

## Local Command Rule

Use `python3 -m ...` for Python module commands. Do not use `python -m ...`
unless the user explicitly confirms that `python` is aliased on this machine.
If copied instructions say `python -m`, silently convert them to `python3 -m`.

## Hard Boundaries

- Do not infer hidden conversation context. The mission must run from
  repo-local files.
- Do not start Phase 3.4 or later work unless `CURRENT_MISSION.md` explicitly
  authorizes it.
- Do not run real LLM scenario commands unless the user explicitly asks.
- Stage only intended mission files.
- Do not commit accidental changes to guarded files.

## Default Validation

Use the validation listed by `CURRENT_MISSION.md` and `CURRENT_CAMPAIGN.md`.
Only if the mission provides no validation, run:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

## Completion Response

Report:

- campaign step executed
- created or updated files
- validation commands and results
- commit SHA or no-commit reason
- push status
- next campaign step or stop condition
