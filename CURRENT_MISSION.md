# CURRENT_MISSION.md — Codex Smart Subagent `/go` Harness Bootstrap

## One-line instruction

When current Codex receives `/go` or `go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, execute the single bootstrap campaign step, commit and push the resulting Codex prompt/config upgrade on a dedicated branch, and **restore this temporary mission/campaign pair from `HEAD` before staging** so the active repo mission is not overwritten.

This file is intentionally compatible with the repo's current serial Codex agent. Do not assume the upgraded subagent harness already exists.

---

## Current mission

Execute the **Codex Smart Subagent `/go` Harness Upgrade Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Target outcome:

```text
After the upgrade, the user can say:

/go and spawn subagents

and Codex will:
- read CURRENT_MISSION.md first,
- run a parallel preflight with read-only diagnostic subagents,
- decompose the selected campaign step into a dependency DAG,
- spawn subagents only where efficient and safe,
- generate small helper tools for repetitive deterministic work when that reduces token use or error risk,
- preserve rigor, validation, allowed-file discipline, commit/push discipline, and review gates.
```

This is a **prompt/config harness upgrade**, not a ToyI runtime feature campaign.

---

## Branch / push / PR rule

Use a branch-first workflow.

Preferred branch:

```text
campaign/codex-smart-subagent-go-harness
```

Rules:

```text
never commit directly to main
create or switch to the preferred branch unless already on an appropriate campaign branch
commit successful upgrade results
push the branch
do not open or merge a PR unless the user explicitly asks in a later step
```

---

## Temporary bootstrap-file rule

This mission/campaign pair is a temporary bootstrap overlay.

Before staging or committing, restore the repo's prior active mission files from `HEAD`:

```bash
git restore --source=HEAD -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md
```

Then verify they are no longer in the final diff:

```bash
git diff --name-only
```

`CURRENT_MISSION.md` and `CURRENT_CAMPAIGN.md` must **not** be staged or committed by this bootstrap campaign.

If `git restore --source=HEAD -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md` would preserve this same bootstrap mission because it is already committed at `HEAD`, stop and report:

```text
STOP: bootstrap mission files appear committed at HEAD; restore the prior active mission/campaign before running this upgrade.
```

---

## Required source files to read first

Read these before doing any work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
.codex/config.toml
.codex/agents/brain_current_mission.toml
.codex/agents/brain_explorer.toml
.codex/agents/brain_row_implementer.toml
.codex/agents/brain_runner_debugger.toml
.codex/agents/brain_spec_refresher.toml
.claude/agents/brain-current-mission.md
.claude/agents/brain-campaign-state.md
.claude/agents/brain-catalog-lint.md
.claude/skills/brain-invariants/SKILL.md
```

If any of the Claude files are absent, continue using the target file contracts in `CURRENT_CAMPAIGN.md`; do not fail the mission solely because the Claude source material is missing.

---

## Allowed final changed files

The final commit may change only:

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

No ToyI runtime, catalog, fixture, Lean, trace, scenario, or active Phase 3.11 implementation file is in scope.

---

## Architectural guardrails

Preserve these constraints:

```text
/go workflow remains repo-local and CURRENT_MISSION.md-first
CURRENT_MISSION.md and CURRENT_CAMPAIGN.md remain the source of task truth
subagents are advisory unless explicitly delegated a bounded shard
read-only diagnostic agents never edit
parallelism may reorder only dependency-free work
validation -> diff guard -> stage -> commit -> push remains serial
no overlapping write agents
no recursive agent fan-out beyond direct children
helper tools must be deterministic, local, stdlib-only by default, and dry-run unless explicitly write-scoped
no network requirement
no real LLM/backend invocation
no ToyI runtime semantic changes
```

---

## Command rule

Use `python3 -m ...` for Python module commands. Convert historical `python -m ...` examples to `python3 -m ...` unless the user explicitly confirms a `python` alias.

---

## Validation

Run at minimum:

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

Do **not** run real LLM commands.

---

## Final report format

After completion, report:

```text
Campaign executed:
- Codex Smart Subagent /go Harness Upgrade

Created/updated:
- <files>

Validation:
- <commands and results>

Git:
- commit: <sha or none>
- branch: campaign/codex-smart-subagent-go-harness
- push: success / not needed / failed with reason

Post-upgrade usage:
- User can now say: /go and spawn subagents

Next:
- Restore or continue the repo's prior active mission as needed.
```
