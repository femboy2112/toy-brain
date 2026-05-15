# CURRENT_CAMPAIGN.md — Operator TUI Agent-Style Layout Campaign

## Purpose

Redesign the existing Operator TUI into a usable agent-style terminal interface, closer to Codex / Claude Code style CLIs.

The current TUI is safe and now has live input, but it still lacks the interaction shape the operator wants:

```text
persistent multi-pane layout
bottom input composer
typed local commands
visible transcript / event log
status bar
state / tick / developmental-history inspectors
interactive queue + step workflow
```

This is a UI/UX campaign only. It is **not** Phase 3.5 Expression + ReadabilityPredictor and does not introduce language, social behavior, Mode B, real LLM calls, shell execution, network I/O, or host execution.

---

## Saved baseline

Expected baseline before this campaign:

```text
Catalog: v0.10
Operator TUI campaign: PASS
Operator TUI live input patch: PASS and merged
Counts: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 6 OBSERVED
Full gate: green
Entrypoint: python3 -m brain.ui
```

If `OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md` is absent or not PASS, stop and report that the live input patch must be merged/applied first.

---

## Execution rule

When the user says `go`, the active repo-capable agent should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
run preflight
infer the next eligible step from repo state
execute only that step's allowed scope
validate as specified
commit and push after successful steps
stop at review gates, failures requiring user judgment, or campaign completion
```

Use `python3 -m ...` for Python module commands. Convert copied `python -m ...` examples to `python3 -m ...`.

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
real terminal automation outside the curses UI
```

No external dependencies. Use only standard library modules and existing project APIs.

---

## Design thesis

The TUI should behave like an operator console with a stable interface contract:

```text
top/header: current state summary and tick count
left pane: BrainState / profile / MSI / PtCns / registry
right pane: selected inspector details
center/bottom pane: transcript / event log
bottom composer: typed input, cursor, prompt mode, and status
footer: key hints and safety status
```

The operator should be able to type local UI commands in the bottom composer:

```text
/help
/state
/tick
/output
/worldlet
/repl
/queue <content_id> <text>
/step
/clear
/quit
```

These are **UI commands only**. They are not shell commands, natural-language understanding, Proto-BASIC, Mode B, or a real LLM chat surface.

Allowed bottom-up path:

```text
bottom composer -> local UI command parser -> QueuePerceptPayload -> Command(QUEUE_PERCEPT) -> OperatorSession.dispatch()
/step or space -> Command(STEP_TICK) -> OperatorSession.step_tick() -> tick(current_state, [queued_event], client)
```

No direct mutation of kernel state or developmental histories is allowed.

---

# Step 0 — Preflight

Read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
OPERATOR_TUI_AUDIT.md
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md
brain/ui/tui.py
brain/ui/__main__.py
brain/ui/render.py
brain/ui/session.py
brain/ui/commands.py
```

Run:

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-UI-14
bash tools/check_all.sh
```

Stop if the tree is dirty, the full gate fails, or either required audit is absent/not PASS.

---

# Step 1 — UX synthesis

Create:

```text
OPERATOR_TUI_AGENT_LAYOUT_SYNTHESIS.md
```

Include:

```text
problem statement: current TUI is safe but not ergonomically interactive
agent-style target layout
bottom composer thesis
pane/window requirements
typed local command requirements
transcript/event-log requirements
how it remains an operator UI, not cognition
non-goals
risks
next artifact: OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md
```

Validate:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 2 — Kickoff

Create:

```text
OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md
```

Cover:

```text
AgentLayout
PaneSpec
PaneRenderResult
BottomComposer
ComposerState
ComposerAction
LocalCommandLine parser
OperatorTranscript / TranscriptEntry
layout-aware TuiViewModel
responsive pane sizing
typed command flow
keyboard flow
scrollback / log discipline
non-interactive fixture strategy
```

Do not include real LLM chat, shell command execution, filesystem save/export, network I/O, Mode B planning, Expression + ReadabilityPredictor, social/language harness, or new theory semantics.

Validate:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 3 — Corrigenda

Create:

```text
OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md
```

Check:

```text
bottom composer vs natural-language chat distinction
typed UI command parser vs shell / Proto-BASIC distinction
pane layout determinism
small terminal behavior
transcript/log as local UI state only
no trace/scenario writes
how typed /queue maps to existing QueuePerceptPayload
how typed /step maps to existing STEP_TICK route
whether new I-UI-* rows are needed
which row statuses are REQUIRED / STRUCTURAL / OBSERVED
```

Validate and commit/push.

---

# Step 4 — Catalog patch plan

Create:

```text
OPERATOR_TUI_AGENT_LAYOUT_CATALOG_PATCH_PLAN.md
```

Continue the `I-UI-*` family unless the plan proves otherwise.

Recommended rows:

```text
I-UI-16 REQUIRED    Agent-style layout exposes persistent named panes plus bottom composer.
I-UI-17 REQUIRED    BottomComposer edit model supports type/backspace/enter/history deterministically.
I-UI-18 REQUIRED    Local command-line parser is finite, typed, and maps only to approved OperatorCommand / QueuePerceptPayload routes.
I-UI-19 REQUIRED    OperatorTranscript records UI events copy-on-write and remains local UI state only.
I-UI-20 STRUCTURAL  AgentLayout / PaneSpec / TuiViewModel are terminal-agnostic immutable contracts.
I-UI-21 STRUCTURAL  Curses wrapper delegates input to composer/router and does not mutate kernel state directly.
I-UI-22 STRUCTURAL  Responsive pane geometry is deterministic and preserves a visible bottom composer on small terminals.
I-UI-23 OBSERVED    Scripted agent-style interaction walk is inspectable and non-gating.
```

Projected count impact from v0.10 if accepted:

```text
REQUIRED       123 -> 127   (+4)
STRUCTURAL      41 -> 44    (+3)
NOT-EXERCISED    4 -> 4     (+0)
DEFERRED        12 -> 12    (+0)
OBSERVED         6 -> 7     (+1)
```

Catalog version should become `v0.11` if rows are added.

Specify row table, statuses, owning modules, fixtures, count impact, catalog patch mechanics, pending registration plan, strict implementation order, open decisions, and stop conditions.

Likely modules:

```text
brain/ui/layout.py
brain/ui/composer.py
brain/ui/command_line.py
brain/ui/transcript.py
brain/ui/render.py
brain/ui/tui.py
brain/ui/session.py
```

Likely fixtures:

```text
brain/ui/fixtures/agent_layout.py
brain/ui/fixtures/composer_input.py
brain/ui/fixtures/transcript_log.py
brain/ui/fixtures/agent_tui_smoke.py
```

Validate and commit/push.

---

# Step 5 — Review gate

Do not proceed to Step 6 unless the catalog patch plan is coherent and no open decision blocks implementation.

Stop and report if the plan requires shell/network/host execution, real LLM calls, direct BrainState mutation, tick() semantic changes, scenario/trace schema changes, external dependencies, or weakening existing I-UI safety rows.

Proceed only when the user says `go` again or explicitly accepts the plan.

---

# Step 6 — Apply accepted v0.11 catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional package markers only if needed:

```text
brain/ui/layout.py
brain/ui/composer.py
brain/ui/command_line.py
brain/ui/transcript.py
brain/ui/fixtures/__init__.py
```

Apply only accepted `I-UI-16..I-UI-23` rows, expected count updates, generated IDs, and pending registrations for REQUIRED / STRUCTURAL rows.

Do not implement runtime behavior unless explicitly allowed by the accepted plan.

Run:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 7 — Layout model and pure renderer upgrade

Allowed files:

```text
brain/ui/layout.py
brain/ui/render.py
brain/ui/fixtures/agent_layout.py
brain/invariants.py
```

Implement deterministic responsive geometry, persistent panes, bottom composer area, render output for header/panes/transcript/composer/status/footer, and graceful small-terminal degradation.

Drive likely rows:

```text
I-UI-16
I-UI-20
I-UI-22
```

Run targeted checks and commit/push.

---

# Step 8 — Bottom composer and typed command parser

Allowed files:

```text
brain/ui/composer.py
brain/ui/command_line.py
brain/ui/commands.py
brain/ui/session.py
brain/ui/fixtures/composer_input.py
brain/invariants.py
```

Implement typing, backspace, enter submit, optional deterministic history recall, finite local command parser, and mappings:

```text
/queue <content_id> <text> -> QueuePerceptPayload -> Command(QUEUE_PERCEPT)
/step -> Command(STEP_TICK)
/state /tick /output /worldlet /repl /help /clear /quit -> existing OperatorCommand routes
invalid commands -> local status/error only
```

Drive likely rows:

```text
I-UI-17
I-UI-18
```

Run targeted checks and commit/push.

---

# Step 9 — Transcript/event log

Allowed files:

```text
brain/ui/transcript.py
brain/ui/session.py
brain/ui/render.py
brain/ui/fixtures/transcript_log.py
brain/invariants.py
```

Implement bounded local transcript/log records for operator command submissions, queue events, step results, validation failures, and view changes. Do not write trace/scenario files and do not enter OutputHistory / WorldletHistory / ProtoBasicHistory.

Drive likely row:

```text
I-UI-19
```

Run targeted checks and commit/push.

---

# Step 10 — Curses wrapper integration

Allowed files:

```text
brain/ui/tui.py
brain/ui/__main__.py
brain/ui/fixtures/agent_tui_smoke.py
README.md
brain/invariants.py
```

Update the wrapper so normal typing edits the bottom composer, Enter parses/submits, `/queue` queues a percept, `/step` or space steps tick, shortcut keys can remain, screen repaints in agent-style layout, status/transcript stay visible, and the curses wrapper remains thin.

Drive likely rows:

```text
I-UI-21
I-UI-23 OBSERVED
```

README must document the new interface.

Run targeted checks and commit/push.

---

# Step 11 — Full gate

Run:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit/push final sync docs if needed.

---

# Step 12 — Post-completion audit

Create:

```text
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md
```

Verdict must be PASS / PASS WITH PATCHES / BLOCKED.

Audit agent-style layout usability, bottom composer visibility, typed command parser safety, transcript/local log behavior, pane/window determinism, small terminal behavior, curses wrapper thinness, kernel boundary, full gate, manual test instructions, and remaining limitations.

Commit/push.

---

## Manual test target

After completion:

```bash
python3 -m brain.ui
```

Expected interaction:

```text
bottom input bar visible immediately
type /queue beta hello-world
press Enter
queue summary appears in transcript/status
type /step
press Enter
tick result appears in transcript
state/tick panes update
type /tick or press t
tick inspector visible
type /state or press s
state inspector visible
type /help
command help visible
type /quit or press q
clean exit
```

Shortcut keys may remain, but typed commands through the bottom composer are the primary interaction path.

---

## Campaign complete output

```text
Operator TUI agent-style layout campaign complete.
Catalog: v0.11 if rows accepted, otherwise v0.10
Counts: <actual>
Full gate: pass
Entrypoint: python3 -m brain.ui
Interactive flow: bottom composer supports /queue, /step, /state, /tick, /help, /quit
Remaining deferred work: Phase 3.5 Expression + ReadabilityPredictor
```
