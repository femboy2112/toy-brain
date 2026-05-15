# CURRENT_CAMPAIGN.md - Operator TUI Input/Switch Repair Campaign

## Purpose

Fix the Operator TUI behavior that made the agent-style UI feel unreliable in
real use:

```text
--print-once did not show the agent layout
valid commands after a parse error showed stale ERROR transcript/footer state
Backspace keycode 263 did not edit the composer
```

This campaign is a focused repair branch, not a new developmental phase.

## Branch

All implementation work belongs on:

```text
codex/operator-tui-input-switch-fixes
```

If an agent is on another branch, stop and switch to the branch above before
editing.

## Scope

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md
brain/ui/__main__.py
brain/ui/session.py
brain/ui/tui.py
brain/ui/fixtures/tui_smoke.py
brain/ui/fixtures/agent_tui_smoke.py
```

Do not touch:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

## Findings

### Finding 1 - `--print-once` rendered the wrong UI

Reproduction:

```bash
python3 -m brain.ui --print-once --width 60 --height 12
```

Before repair, the output began with:

```text
[ core state ]----------------------------------------------
```

That meant the command used the retained legacy single-pane renderer. The
campaign corrigenda expected the non-interactive entrypoint to render an
`AgentTuiViewModel` so operators can inspect the bottom composer without a
real TTY.

Fix:

```text
brain/ui/__main__.py now builds ComposerState.empty(),
OperatorTranscript.empty(), AgentTuiViewModel, and render_agent() for
--print-once and _render_once_to_string().
```

### Finding 2 - stale errors survived later valid commands

Reproduction:

```text
type /bad + Enter
type /queue beta hello-world + Enter
type /step + Enter
```

Before repair, `/queue` and `/step` dispatched successfully but transcript
entries after those submissions were still `ERROR unknown command: /bad`.

Fix:

```text
OperatorSession.dispatch() clears error_message at the start of each valid
Command dispatch. Failure handlers set a fresh error; success paths no longer
inherit stale local UI errors.
```

### Finding 3 - Backspace code 263 was ignored

Reproduction:

```text
ComposerState(buffer="abc", cursor=3)
send raw keycode 263
```

Before repair, the route kind was `none` and the buffer stayed `abc`.

Fix:

```text
build_agent_keystroke_router() maps literal curses KEY_BACKSPACE code 263 to
AgentKeyKind.BACKSPACE.
```

## Implementation Steps

1. Preflight:

```bash
git status --short --branch
python3 -m tools.catalog counts
python3 -m brain.ui --print-once --width 60 --height 12
```

2. Runtime repair:

```text
brain/ui/__main__.py
brain/ui/session.py
brain/ui/tui.py
```

3. Regression coverage:

```text
brain/ui/fixtures/tui_smoke.py
brain/ui/fixtures/agent_tui_smoke.py
```

4. Documentation and mission handoff:

```text
README.md
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
```

5. Validation:

```bash
python3 -m brain.ui --print-once --width 60 --height 12
python3 -m brain.invariants run --id I-UI-12
python3 -m brain.invariants run --id I-UI-17
python3 -m brain.invariants run --id I-UI-18
python3 -m brain.invariants run --id I-UI-21
python3 -m brain.invariants run --id I-UI-23
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

## Current Repair Status

```text
Branch                : codex/operator-tui-input-switch-fixes
Runtime fixes         : implemented
Regression fixtures   : implemented
Docs/mission handoff  : implemented
Full validation       : pass
Commit/push           : pending commit
```

## Final Validation Results

Validated on branch `codex/operator-tui-input-switch-fixes`:

```text
python3 -m brain.ui --print-once --width 60 --height 12
  PASS - output includes agent header, transcript pane, bottom composer,
  mode=local-cmd meta row, and footer.

python3 -m brain.invariants run --id I-UI-12
  PASS - entrypoint fixture covers agent --print-once output.

python3 -m brain.invariants run --id I-UI-17
  PASS - composer edit model remains green.

python3 -m brain.invariants run --id I-UI-18
  PASS - local command parser remains green.

python3 -m brain.invariants run --id I-UI-21
  PASS - wrapper delegation fixture covers stale-error recovery and
  Backspace keycode 263.

python3 -m brain.invariants run --id I-UI-23
  OBS-PASS - scripted agent walk remains inspectable.

python3 -m tools.catalog counts
  PASS - 127 REQUIRED / 44 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED /
  7 OBSERVED.

python3 -m tools.citations verify
  PASS - 100 citations verified.

python3 -m tools.import_audit
  PASS - I-PCE-05 clean.

python3 -m brain.invariants run
  PASS - 178 rows checked; REQUIRED 127 green / 0 red; STRUCTURAL
  44 green / 0 red; OBSERVED 7 pass / 0 fail; gate failures 0.

bash tools/check_all.sh
  PASS - All checks passed.
```

## Expected Fixed Behavior

`python3 -m brain.ui --print-once --width 60 --height 12` should include:

```text
toy-brain operator
[ transcript ]
> _
mode=local-cmd
keys: enter submit
```

The scripted input sequence:

```text
/bad
/queue beta hello-world
/step
Backspace keycode 263 over "abc"
```

should yield:

```text
ERROR for /bad only
QUEUED for /queue
STEP for /step
empty final error_message
buffer "ab" after keycode 263
```

## Stop Conditions

Stop and report if:

```text
any full-gate command fails after one repair pass
the fix requires changing guarded files
the fix requires weakening an I-UI row
the fix would add shell/network/host execution or a new dependency
```

## Completion Output

When complete, report:

```text
Operator TUI input/switch repair complete.
Branch: codex/operator-tui-input-switch-fixes
Entrypoint: python3 -m brain.ui
Fixed: --print-once agent layout, stale error recovery, Backspace 263
Full gate: <pass/fail>
Commit: <sha>
Push: <status>
```
