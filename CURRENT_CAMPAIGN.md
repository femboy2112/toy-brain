# CURRENT_CAMPAIGN.md — Operator TUI Live Input Patch Campaign

## Purpose

Patch the existing Operator TUI so it is actually usable for bottom-up interaction.

Current problem:

```text
python3 -m brain.ui opens / renders the Operator TUI, but the entrypoint passes no percept_factory into run_curses().
The e key maps to QUEUE_PERCEPT, but without a percept_factory it only reports "queue percept: no input prompt configured".
The UI therefore mostly shows static state from a default offline session instead of letting the operator type bottom-up content and step it.
```

This campaign adds a real terminal input prompt for queuing a bottom-up PerceptEvent through the existing public UI command path.

This is a **focused UI usability patch**, not a new theory/cognitive phase.

---

## Saved project state / baseline

Current saved state at campaign creation:

```text
Catalog: v0.10
Operator TUI campaign: PASS
Counts: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 6 OBSERVED
Full gate: green
Entrypoint: python3 -m brain.ui
Known usability gap: no interactive percept input factory is wired into the curses entrypoint
Next cognitive campaign still deferred: Phase 3.5 Expression + ReadabilityPredictor
```

---

## Model-agnostic execution rule

When the user says `go`, the active repo-capable agent should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
run preflight
find the next eligible step from repo state
execute only that step's allowed scope
validate as specified
commit and push after successful steps
stop at explicit gates, failures requiring user judgment, or campaign completion
```

This applies to Codex, Claude Code, or any future agent with equivalent repo, shell, validation, commit, and push capability.

---

## Command rule

Use `python3 -m ...` for all Python module commands. Convert copied `python -m ...` examples to `python3 -m ...`.

---

## Accepted inputs

Read these as current state references unless the user says otherwise:

```text
OPERATOR_TUI_AUDIT.md
INVARIANT_CATALOG.md
README.md
brain/ui/tui.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/session.py
brain/ui/render.py
brain/ui/fixtures/tui_smoke.py
brain/ui/fixtures/command_router.py
brain/ui/fixtures/bottom_up_tick.py
brain/tick.py
brain/io_types.py
```

---

## Hard boundaries

Do not modify unless a step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
```

Do not implement:

```text
Phase 3.5 Expression + ReadabilityPredictor
social/language harness
Mode B
real LLM calls
real host execution
shell execution
network I/O
arbitrary Python execution
save/export filesystem writes
new catalog rows
catalog count changes
```

No external dependencies. Use only standard library curses and existing project APIs.

---

## Patch thesis

```text
The TUI should let the operator press e, type a bounded content_id and text payload, queue that payload through the existing QueuePerceptPayload / Command path, then press space to route the queued PerceptEvent through tick().
```

The patch must keep all state mutation through existing public boundaries:

```text
curses prompt -> QueuePerceptPayload -> Command(QUEUE_PERCEPT) -> OperatorSession.dispatch()
space key -> Command(STEP_TICK) -> OperatorSession.step_tick() -> tick(current_state, [queued_event], client)
```

No UI code may directly mutate BrainState internals, profile, MSI, PtCns, registry, developmental histories, traces, scenario files, or catalog files.

---

# Step 0 — Preflight

## Required reads

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
OPERATOR_TUI_AUDIT.md
brain/ui/tui.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/session.py
brain/ui/fixtures/tui_smoke.py
```

## Commands

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-UI-14
bash tools/check_all.sh
```

Stop if the tree is dirty, the full gate fails, or Operator TUI audit is absent/not PASS.

---

# Step 1 — Implement curses percept input prompt

## Purpose

Add a real interactive percept input path to the curses wrapper.

## Allowed files

```text
brain/ui/tui.py
brain/ui/fixtures/tui_smoke.py
```

## Required behavior

Add a helper in `brain/ui/tui.py`, for example:

```text
prompt_queue_percept(stdscr, session) -> Command
```

The helper should:

```text
1. temporarily show a bounded prompt area in the terminal
2. collect a printable content_id
3. collect printable text/content
4. optionally use safe defaults for any required ContentState / rho fields
5. build QueuePerceptPayload using the existing public constructor/API
6. return Command(OperatorCommand.QUEUE_PERCEPT, payload)
7. never mutate session directly
8. never call tick()
9. never write files, traces, scenarios, catalog rows, or developmental histories
10. fail closed as local UI status/error through the existing step_loop/percept_factory path
```

If the current `QueuePerceptPayload` requires additional fields, use conservative defaults already accepted by existing fixtures. Do not broaden the payload model unless absolutely necessary.

## Test requirement

Update `tui_smoke.py` to test the prompt without a real terminal by using a fake curses window with deterministic `getstr` / `getkey` / equivalent input methods.

The test must prove:

```text
prompt helper returns QUEUE_PERCEPT Command
returned payload validates through existing QueuePerceptPayload / Command machinery
prompt does not call tick()
prompt does not mutate BrainState/session directly
invalid input becomes local error/status path, not an exception that kills the loop
```

## Validation

```bash
python3 -m brain.invariants run --id I-UI-11
python3 -m brain.invariants run --id I-UI-12
python3 -m brain.invariants run --id I-UI-14
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 2 — Wire prompt into CLI entrypoint

## Purpose

Make `python3 -m brain.ui` pass the real prompt factory into `run_curses()`.

## Allowed files

```text
brain/ui/__main__.py
brain/ui/tui.py
brain/ui/fixtures/tui_smoke.py
README.md
```

## Required behavior

Update the entrypoint so the usable-terminal path does not call:

```text
run_curses(session, client=client)
```

without a percept factory.

It should call something equivalent to:

```text
run_curses(session, client=client, percept_factory=<curses prompt factory>)
```

where the factory uses the curses window/session path added in Step 1.

If `run_curses()` currently lacks access to `stdscr` inside `percept_factory`, adjust the wrapper minimally so the factory can prompt safely. Keep the wrapper thin.

Expected operator flow after this step:

```text
e      open prompt
text   enter content_id and content text
enter  queue bottom-up PerceptEvent
space  run tick with queued event
s/t/o/w/r switch views
c      clear status
?      help
q      quit
```

`--print-once` may remain static and non-interactive.

## README requirement

Update the Operator TUI README section with the actual interactive flow.

Include at minimum:

```text
python3 -m brain.ui
press e to queue a percept
press space to step tick()
use --print-once for non-interactive render
use --check-terminal for terminal diagnostics
```

## Validation

```bash
python3 -m brain.invariants run --id I-UI-07
python3 -m brain.invariants run --id I-UI-11
python3 -m brain.invariants run --id I-UI-12
python3 -m brain.invariants run --id I-UI-14
python3 -m tools.catalog counts
bash tools/check_all.sh
```

Commit/push.

---

# Step 3 — Manual usability notes / patch audit

## Purpose

Create a small audit note confirming the TUI is now interactive.

## Output file

```text
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md
```

## Allowed files

```text
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md
```

## Required content

Include:

```text
problem fixed
files changed
operator flow
validation commands and results
safety boundaries preserved
manual test instructions
remaining limitations
```

Manual test instructions should include:

```bash
python3 -m brain.ui --check-terminal
python3 -m brain.ui --print-once
python3 -m brain.ui
```

and the key sequence:

```text
e -> type content_id/text -> space -> inspect tick/state
```

## Validation

```bash
python3 -m tools.catalog counts
bash tools/check_all.sh
```

Commit/push.

---

## Campaign complete criteria

Campaign complete when:

```text
the e key opens a bounded in-TUI percept prompt
the prompt returns a QUEUE_PERCEPT command through existing public constructors
space routes the queued event through tick()
README documents the interactive key flow
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md exists
bash tools/check_all.sh passes
```

---

## Stop conditions requiring user review

Stop if the patch requires:

```text
editing brain/tlica/
changing tick() semantics
changing PerceptEvent semantics
changing scenario schema
real LLM execution
new external dependency
shell/file/network execution
catalog row or count changes
direct mutation of BrainState/profile/MSI/PtCns/registry/developmental histories
```

---

## Campaign complete output

```text
Operator TUI live input patch complete.
Catalog remains: v0.10
Counts remain: 123 / 41 / 4 / 12 / 6
Full gate: pass
Entrypoint: python3 -m brain.ui
Interactive flow: e queues percept, space steps tick
Remaining deferred work: Phase 3.5 Expression + ReadabilityPredictor
```
