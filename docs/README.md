# docs/

This directory holds **archived planning, kickoff, synthesis, corrigenda,
catalog-patch-plan, audit, behavior-report, dry-run, roadmap, and matrix
artifacts** from past and current campaigns. It is not a runtime surface
and it is not where active mission execution starts.

## What lives where

| Path | What it is |
|---|---|
| `docs/campaigns/` | Campaign artifacts grouped by phase. Read its `README.md` for the per-phase index. |

## Where active operation starts

Active repo operation always starts from root-level files. The archive
is historical context; do not treat any document in here as a current
instruction unless an active root entrypoint explicitly points to it.

The active root files are:

| Path | What it is |
|---|---|
| `README.md` | Top-level repo entry point. |
| `CURRENT_MISSION.md` | Current mission for repo-capable agents. |
| `CURRENT_CAMPAIGN.md` | Current campaign breakdown referenced by the mission. |
| `INVARIANT_CATALOG.md` | Canonical source of truth for invariant rows, statuses, counts, and citations. |
| `CLAUDE.md` | Claude Code project instructions. |
| `AGENTS.md` | Agent operating contract. |
| `SPEC_UPDATES.md` | Lean spec refresh protocol. |
| `ARCHIVE.md` | Pointer to the v0 README history preserved in-place at root. |

If `CURRENT_MISSION.md` explicitly names a document in `docs/`, that
document is treated as a current required read for that mission step;
otherwise everything under `docs/` is historical.

## What does not live here

- Source code under `brain/` is not archived; it is the live kernel.
- Tools under `tools/` are not archived; they are live validation surfaces.
- The Lean snapshot under `lean_reference/` is not archived; it is the
  read-only spec snapshot the catalog cites.
- Scenarios under `scenarios/` and traces under `traces/` are not
  archived; they are live runtime data.

## Move rules

This directory was populated by the
`campaign/archive-completed-docs` cleanup. Files were moved with
`git mv`; their git history is preserved. Runtime behavior, catalog
semantics, fixture behavior, and catalog counts were not changed by
that cleanup.
