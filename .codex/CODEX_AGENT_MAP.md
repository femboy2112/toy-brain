# Codex Agent Map

This file maps the Claude Code prompt surface in `.claude/` to the Codex
prompt/config surface in this repository.

## Source To Codex Mapping

| Claude source | Codex analog | Notes |
|---|---|---|
| `CLAUDE.md` | `.codex/agents/brain_current_mission.toml` plus `CURRENT_MISSION.md` | Claude Code repo entry point for natural `go` triggers. |
| `.claude/agents/brain-current-mission.md` | `.codex/agents/brain_current_mission.toml` | Current mission/campaign runner for `go` and equivalent trigger phrases. |
| `.claude/agents/brain-explorer.md` | `.codex/agents/brain_explorer.toml` | Read-only catalog and Lean navigator. |
| `.claude/agents/brain-row-implementer.md` | `.codex/agents/brain_row_implementer.toml` | Bounded implementation role for explicit row IDs. |
| `.claude/agents/brain-runner-debugger.md` | `.codex/agents/brain_runner_debugger.toml` | Red-row diagnosis and smallest-fix role. |
| `.claude/agents/brain-spec-refresher.md` | `.codex/agents/brain_spec_refresher.toml` | SPEC_UPDATES and upstream Lean drift role. |
| `.claude/commands/go.md` | `.codex/agents/brain_current_mission.toml` | Slash-command prompt that routes to the same current mission contract. |
| `.claude/skills/brain-invariants/SKILL.md` | `.agents/skills/brain-invariants/SKILL.md` | Codex-readable project skill. |

## Translation Choices

- Claude frontmatter became Codex `config.toml` agent registrations plus
  role-local `developer_instructions`.
- Claude natural-language `go` routing lives in `CLAUDE.md`; Codex routing
  lives in `brain_current_mission.toml`. Both read `CURRENT_MISSION.md` at run
  time rather than storing a stale campaign in agent config.
- Claude tool lists were translated into explicit allowed command families and
  workflow boundaries.
- The Codex agent files intentionally use TOML multi-line strings and avoid
  `[model_context]`, which is not supported by the local Codex agent loader
  convention used in this environment.
- The skill analog lives in `.agents/skills/` rather than `.codex/skills/`
  because this environment exposes repo-local skills from `.agents/skills`.

## Non-Goals

These prompt files do not alter the kernel, catalog, runtime, fixture, trace,
scenario, or Lean snapshot implementation. They also do not start Phase 3.

Future agents may plan or implement later phases only when the user explicitly
requests that work or when `CURRENT_MISSION.md` authorizes the current campaign
step. This prompt pack does not authorize Proto-BASIC REPL, expression layer,
or language harness work by itself.
