# CURRENT_MISSION.md — Model-Agnostic `go` Entry Point

## One-line instruction

When the user tells any repo-capable agent **`go`** in this repository, the agent should read this file and execute the current campaign.

This entry point is model-agnostic. It applies to Codex, Claude Code, or any future agent with equivalent repository read/write, shell, validation, commit, and push capabilities.

---

## Current mission

Execute the next eligible step in:

```text
CURRENT_CAMPAIGN.md
```

`CURRENT_CAMPAIGN.md` is currently the Operator TUI Agent-Style Layout campaign.

The active agent must use campaign state detection, prerequisites, test results, and stop conditions to decide which step to run next.

---

## Important local command rule

Use `python3 -m ...` for all Python module commands.

Do **not** use `python -m ...` on this machine unless the user explicitly says a `python` alias exists.

If any copied command says `python -m`, convert it to `python3 -m` before running.

---

## Required source files to read first

Read these before doing anything:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
```

Then read whatever files the current campaign step requires.

Do not rely on unstated conversation context. The campaign must run from repo-local files.

---

## Campaign execution rules

1. Run the campaign preflight first.
2. Determine the next incomplete eligible campaign step from repo state.
3. Execute only that step's allowed scope.
4. Use the step's test results to decide whether to continue, fix, commit, or stop.
5. Commit and push after each successful step.
6. Stop at explicit approval gates, failing tests requiring user judgment, or campaign completion.

Do not skip ahead to Phase 3.5 Expression + ReadabilityPredictor or later cognitive campaigns.

---

## Global guardrails

Do not modify these unless `CURRENT_CAMPAIGN.md` explicitly allows the current step to touch them:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

Do not run real LLM scenario commands unless the user explicitly asks.

---

## Git persistence requirement

After each successful campaign step, the active agent must commit and push.

Rules:

```text
stage only intended files
commit with a clear message
push to current branch / main as appropriate
report the commit SHA
```

Committing and pushing completed step results is mandatory if files changed.

Do not commit accidental changes to guarded files.

If there are no changes, report that no commit was made and why.

---

## Final report

After each run, report:

```text
Campaign step executed:
- <step name>

Created/updated:
- <files>

Validation:
- <commands and results>

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- <next campaign step or stop condition>
```

---

## Stop condition

Stop according to `CURRENT_CAMPAIGN.md`.

Do not continue past a campaign stop gate without a new explicit user instruction.
