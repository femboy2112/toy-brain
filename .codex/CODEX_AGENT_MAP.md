# Codex Agent Map

This file maps the Claude Code prompt surface in `.claude/` to the Codex
prompt/config surface in this repository.

## Source To Codex Mapping

| Claude source | Codex analog | Notes |
|---|---|---|
| `.claude/agents/brain-explorer.md` | `.codex/agents/brain_explorer.toml` | Read-only catalog and Lean navigator. |
| `.claude/agents/brain-row-implementer.md` | `.codex/agents/brain_row_implementer.toml` | Bounded implementation role for explicit row IDs. |
| `.claude/agents/brain-runner-debugger.md` | `.codex/agents/brain_runner_debugger.toml` | Red-row diagnosis and smallest-fix role. |
| `.claude/agents/brain-spec-refresher.md` | `.codex/agents/brain_spec_refresher.toml` | SPEC_UPDATES and upstream Lean drift role. |
| `.claude/skills/brain-invariants/SKILL.md` | `.agents/skills/brain-invariants/SKILL.md` | Codex-readable project skill. |

## Translation Choices

- Claude frontmatter became Codex `config.toml` agent registrations plus
  role-local `developer_instructions`.
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

Future agents may plan Phase 3 only when the user explicitly requests planning;
they must not implement the Osmotic Chamber, developmental substrate, output
ladder, worldlet, Proto-BASIC REPL, expression layer, or language harness from
this porting work.
