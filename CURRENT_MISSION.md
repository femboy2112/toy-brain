# CURRENT_MISSION.md - Operator TUI Input/Switch Repair

## One-line instruction

When the user tells a repo-capable agent `go` in this repository, read this
file and execute the current repair campaign in `CURRENT_CAMPAIGN.md`.

## Current mission

The active mission is the Operator TUI input/switch repair campaign.

```text
Campaign file : CURRENT_CAMPAIGN.md
Working branch: codex/operator-tui-input-switch-fixes
Entrypoint    : python3 -m brain.ui
Catalog       : current INVARIANT_CATALOG.md on this branch
```

This mission is a UI repair only. It does not start Phase 3.5 and does not
change TLICA, tick semantics, LLM behavior, scenario files, trace files, or
developmental-history semantics.

## Verified problems

The following failures were reproduced on `main` before the repair:

```text
1. python3 -m brain.ui --print-once rendered the legacy single-pane frame
   instead of the agent layout with bottom composer.
2. After an invalid typed command, later valid /queue and /step commands
   dispatched successfully but inherited the stale error in transcript/footer.
3. Backspace keycode 263, the common curses KEY_BACKSPACE code, was routed as
   none and did not edit the composer buffer.
```

## Required source files to read first

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
brain/ui/__main__.py
brain/ui/session.py
brain/ui/tui.py
brain/ui/fixtures/tui_smoke.py
brain/ui/fixtures/agent_tui_smoke.py
```

Then read any file named by the current campaign step.

## Important local command rule

Use `python3 -m ...` for Python module commands.

Do not use `python -m ...` on this machine unless the user explicitly says a
`python` alias exists.

## Guardrails

Do not modify these files or directories for this repair:

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

No shell execution, network I/O, filesystem save/export feature, Mode B,
Phase 3.5 Expression + ReadabilityPredictor, or new dependency is in scope.

## Done condition

The mission is complete when:

```text
branch codex/operator-tui-input-switch-fixes exists
the three verified problems are fixed
targeted I-UI checks pass
bash tools/check_all.sh passes
CURRENT_CAMPAIGN.md records the final validation results
changes are committed on the repair branch
```

## Final report format

```text
Campaign step executed:
- Operator TUI input/switch repair

Created/updated:
- <files>

Validation:
- <commands and results>

Git:
- branch: codex/operator-tui-input-switch-fixes
- commit: <sha or none>
- push: <success / not run with reason>

Next:
- review and merge the repair branch, or continue with the campaign stop gate
```
