# toy-brain Claude Code Entry Point

This repository has a repo-local mission runner contract. When the user tells
Claude Code any of the following:

- `go`
- `run current mission`
- `execute current mission`
- `do the current task`

Claude Code must read `CURRENT_MISSION.md` first and execute the current
mission described there. Treat references in mission and campaign files to
Codex as applying to the current Claude Code agent too; `CURRENT_MISSION.md`
and `CURRENT_CAMPAIGN.md` are tool-neutral source-of-truth files for this
checkout.

## Required Mission Workflow

1. Read `CURRENT_MISSION.md`.
2. Read every file listed in that mission's required-read section.
3. Read `CURRENT_CAMPAIGN.md` when the mission points to it.
4. Run the campaign preflight before choosing a step.
5. Determine the next incomplete eligible step from repo state and test
   results.
6. Execute only that step's allowed scope.
7. Respect the mission and campaign guardrails exactly.
8. Commit and push after each successful step when files changed.
9. Stop at explicit review gates, failures requiring user judgment, or campaign
   completion.

## Local Command Rule

Use `python3 -m ...` for Python module commands. If copied instructions say
`python -m ...`, convert them to `python3 -m ...` before running.

Do not run real LLM scenario commands unless the user explicitly asks.

## Claude Code Surfaces

- Use `.claude/agents/brain-current-mission.md` for the current mission runner.
- Use `.claude/commands/go.md` when the user wants a slash-command entry point.
- Use `.claude/skills/brain-invariants/SKILL.md` for catalog, runner,
  citation, import-audit, and invariant-row workflows.
