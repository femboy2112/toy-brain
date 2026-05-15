# toy-brain Codex Prompt Pack

This directory contains repo-local Codex agent role configuration derived from
the Claude Code prompt files under `.claude/`.

Source material:

- `.claude/agents/brain-explorer.md`
- `.claude/agents/brain-row-implementer.md`
- `.claude/agents/brain-runner-debugger.md`
- `.claude/agents/brain-spec-refresher.md`
- `.claude/skills/brain-invariants/SKILL.md`

## Layout

- `config.toml` registers the project-scoped Codex agents.
- `agents/*.toml` contains role-specific developer instructions.
- `CODEX_AGENT_MAP.md` maps Claude-side prompts to Codex-side analogs.
- `.agents/skills/brain-invariants/SKILL.md` contains the Codex-readable
  project skill.

## Scope

This is a tooling/configuration prompt pack. It does not change the TLICA
kernel, catalog, runtime, scenario, trace, fixture, or Lean snapshot state.

Do not treat any role in this prompt pack as permission to start Phase 3
implementation work. Phase 3 planning may be discussed only when the user
explicitly asks for planning.

## Codex Assumptions

This environment uses project-scoped `.codex/config.toml` with agent role files
under `.codex/agents/*.toml`. Agent files use `developer_instructions`; do not
use unsupported `[model_context]` tables.

The project skill is stored under `.agents/skills/brain-invariants/SKILL.md`,
which matches the repo-local skill convention available to Codex in this
environment.
