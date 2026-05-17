# OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md — Operator TUI Live Input Patch Audit

## Verdict

```text
PASS
```

The Operator TUI live input patch campaign added a real curses input
prompt for queuing a bottom-up `PerceptEvent` and wired it into the
`python3 -m brain.ui` CLI entrypoint. The `e` key now opens a bounded
in-TUI prompt instead of surfacing `queue percept: no input prompt
configured`. The full gate remains green at v0.10. No guarded files were
mutated. No catalog rows or counts changed.

---

## Problem fixed

Before this campaign:

```text
python3 -m brain.ui opened the Operator TUI and rendered state, but
the entrypoint called run_curses(session, client=client) with no
percept_factory. The e key was mapped to OperatorCommand.QUEUE_PERCEPT
in KEYMAP, but step_loop() had no factory to invoke, so the only thing
that happened on e was the local UI error "queue percept: no input
prompt configured". The operator could not type a bottom-up
content_id / text payload from inside the TUI; the visible state was
effectively static, driven only by the default offline session.
```

After this campaign:

```text
Pressing e opens a bounded in-TUI curses prompt. The operator types a
content_id, presses Enter, types a short text payload, and presses
Enter again. The prompt builds a QueuePerceptPayload through the
public PerceptEvent constructor (no kernel internals are touched) and
returns a Command(OperatorCommand.QUEUE_PERCEPT, payload). The
OperatorSession.dispatch() path validates and enqueues the event.
Pressing space routes the queued PerceptEvent through tick() via the
public OperatorSession.step_tick() boundary. BrainState replacement
goes through the returned TickRecord only.
```

The patch is a focused UI usability fix. It introduces no new cognitive
layer, no Phase 3.5 Expression / ReadabilityPredictor, no Mode B, no
real LLM client, no shell / file / network / host execution surface,
and no new external dependency.

---

## Files changed

Step 1 — `e0a185d` `operator-tui(live-input step1): add curses percept prompt helper`:

```text
brain/ui/tui.py
  + PROMPT_MAX_INPUT_LEN constant (bounded field read budget)
  + PROMPT_DEFAULT_CONTENT_STATE (safe ContentState default)
  + PROMPT_DEFAULT_RHO (safe initial_rho default, string-encoded)
  + _decode_getstr(raw) helper (bytes / str -> stripped str)
  + _prompt_read_field(stdscr, label, row, *, width) helper
  + prompt_queue_percept(stdscr, session, *, width, height) -> Command
      paints a bounded two-field prompt, builds QueuePerceptPayload
      via the public constructor, and returns a QUEUE_PERCEPT Command
      Never calls tick(); never mutates session; never writes a file,
      scenario, trace, history, or catalog row. Empty input cancels
      via ValueError so step_loop's percept_factory boundary surfaces
      a local UI error.
  + make_curses_percept_factory(stdscr, *, width, height) -> factory
      step_loop-compatible per-iteration factory.

brain/ui/fixtures/tui_smoke.py
  + fake-curses coverage exercising the new prompt helpers without
    attaching to a real terminal. Drives I-UI-11 and I-UI-12 plus the
    new Branch 9 / Branch 10 cases (good prompt -> QUEUE_PERCEPT
    Command; cancelled / invalid prompt -> local UI error, no
    session mutation, no tick() call).
```

Step 2 — `c4b8c07` `operator-tui(live-input step2): wire curses prompt factory into CLI entrypoint`:

```text
brain/ui/tui.py
  + percept_factory_builder parameter on run_curses(...) so the
    live wrapper can construct the per-iteration prompt against the
    real stdscr that curses.wrapper provides. The wrapper accepts
    at most one of percept_factory / percept_factory_builder, and
    defaults to make_curses_percept_factory when neither is given.

brain/ui/__main__.py
  + main() now passes percept_factory_builder=make_curses_percept_factory
    into run_curses(session, client=client, ...) on the usable-terminal
    path. The factory is built inside curses.wrapper so the window
    reference is scoped to that lifecycle.

brain/ui/fixtures/tui_smoke.py
  + extended fake-curses coverage proving the entrypoint wires the
    factory through (Branch 9 / 10), invalid factory shapes are
    rejected, and the default fallback resolves to
    make_curses_percept_factory when no factory is supplied.

README.md
  + Operator TUI section updated to document the actual interactive
    flow: `e -> content_id / text -> Enter -> space -> tick()`.
    Lists --print-once and --check-terminal as the non-interactive
    entrypoints.
```

No other files were modified. No file under `brain/tlica/`, `brain/llm/`,
`brain/tick.py`, `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `lean_reference/`, `scenarios/`, or
`traces/` was touched.

---

## Operator flow

Key sequence after this patch:

```text
e            open the bounded in-TUI percept prompt
<text>       type content_id (printable, bounded to 64 chars)
<Enter>      finish the content_id field
<text>       type text payload (printable, bounded to 64 chars)
<Enter>      finish the text field -> QueuePerceptPayload built
             via public PerceptEvent constructor, queued through
             OperatorSession.dispatch() with kind=QUEUE_PERCEPT
space        OperatorSession.dispatch(make_command(STEP_TICK)) ->
             OperatorSession.step_tick() -> tick(current_state,
             [queued_event], client) once; new state is the
             returned TickRecord.new_state via the public boundary
s / t / o / w / r   switch the active view (state, tick, output,
             worldlet, repl)
c            clear local UI status / error
? or h       show the help pane
q            quit the wrapper cleanly
```

Cancellation: empty content_id or empty text raises
`ValueError("prompt cancelled ...")` inside `prompt_queue_percept`. The
surrounding `step_loop` catches `ValueError` / `TypeError` from the
factory and stores the message as a local UI error via
`OperatorSession.set_error(...)`. BrainState, MSI, PtCns, profile,
registry, OutputHistory, WorldletHistory, ProtoBasicHistory, traces,
scenarios, and catalog files are unchanged on cancel.

---

## Validation commands and results

The campaign-required commands were executed at Step 3 audit time.

```text
$ python3 -m tools.catalog counts
Category            Banner    Actual  Expected
REQUIRED               123       123       123  ok
STRUCTURAL              41        41        41  ok
NOT-EXERCISED            4         4         4  ok
DEFERRED                12        12        12  ok
OBSERVED                 6         6         6  ok
```

```text
$ python3 -m brain.invariants run --id I-UI-14
[brain.ui.fixtures.tui_smoke]
  OBS-PASS  I-UI-14      OBSERVED
I-PCE-05: agency.py is clean of pce imports.
1 rows checked  ·  REQUIRED green: 0 ·  REQUIRED red: 0
                ·  STRUCTURAL green: 0 ·  STRUCTURAL red: 0
                ·  OBSERVED: 1 pass / 0 fail
                ·  gate failures: 0
```

```text
$ bash tools/check_all.sh
=== 0/5 generated catalog IDs freshness ===
=== 1/5 catalog counts (strict) ===           all ok
=== 2/5 citation verification ===             Verified 100 citations.
=== 3/5 import audit (I-PCE-05) ===           agency.py clean.
=== 4/5 invariant runner (includes I-CAT-01) ===
170 rows checked  ·  REQUIRED green: 123  ·  REQUIRED red: 0
                  ·  STRUCTURAL green: 41 ·  STRUCTURAL red: 0
                  ·  OBSERVED: 6 pass / 0 fail
                  ·  gate failures: 0
All checks passed.
```

I-UI-* row family is green at v0.10:

```text
I-UI-01   PASS       REQUIRED       brain/ui/snapshot.py
I-UI-02   PASS       REQUIRED       brain/ui/render.py
I-UI-03   PASS       REQUIRED       brain/ui/commands.py
I-UI-04   PASS       REQUIRED       brain/ui/commands.py
I-UI-05   PASS       REQUIRED       brain/ui/session.py
I-UI-06   PASS       REQUIRED       brain/ui/session.py
I-UI-07   PASS       REQUIRED       brain/ui/__init__.py
I-UI-08   PASS       STRUCTURAL     brain/ui/snapshot.py
I-UI-09   PASS       STRUCTURAL     brain/ui/render.py
I-UI-10   PASS       STRUCTURAL     brain/ui/session.py
I-UI-11   PASS       STRUCTURAL     brain/ui/tui.py
I-UI-12   PASS       STRUCTURAL     brain/ui/__main__.py
I-UI-13   PASS       STRUCTURAL     brain/ui/session.py
I-UI-14   OBS-PASS   OBSERVED       brain/ui/session.py
I-UI-15   (not exercised)            registered chokepoint, no fixture
```

Counts remain: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED /
12 DEFERRED / 6 OBSERVED. Catalog remains v0.10.

---

## Safety boundaries preserved

```text
Guarded surfaces NOT touched by this patch:
  brain/tlica/                       untouched
  brain/tick.py                      untouched
  brain/llm/                         untouched
  INVARIANT_CATALOG.md               untouched
  tools/catalog.py                   untouched
  brain/_catalog_ids.py              untouched (regenerated only by
                                     tools/check_all.sh; content is
                                     unchanged because no catalog
                                     rows were added)
  lean_reference/                    untouched
  scenarios/                         untouched
  traces/first_scenario_real.jsonl   untouched
  traces/RUN_SUMMARY.md              untouched

No new catalog rows. No catalog count changes.
No new external dependency. Standard library curses only.
No real LLM call site. No subprocess, no shell, no socket, no
  urllib / http / requests, no arbitrary Python evaluation, no
  filesystem write outside the UI module tree, the README, and the
  audit markdown files.
No Phase 3.5 Expression + ReadabilityPredictor work, no
  social/language harness, no Mode B, no real host execution.

State mutation routes (UI side):
  QUEUE_PERCEPT:
    curses prompt
      -> QueuePerceptPayload (public PerceptEvent constructor)
      -> Command(OperatorCommand.QUEUE_PERCEPT, payload)
      -> OperatorSession.dispatch(cmd, client=client)
  STEP_TICK:
    space key
      -> Command(OperatorCommand.STEP_TICK)
      -> OperatorSession.dispatch(...)
      -> OperatorSession.step_tick()
      -> tick(current_state, [queued_event], client)
      -> TickRecord -> session state replaced via public path

Failure isolation:
  ValueError / TypeError from the percept factory is caught by
  step_loop and stored as a local UI error via
  OperatorSession.set_error(...). BrainState, MSI, PtCns, profile,
  ContentRegistry, OutputHistory, WorldletHistory,
  ProtoBasicHistory, traces, scenario files, and catalog files are
  unchanged on failure (I-UI-05, I-UI-06, I-UI-13).

brain/ui/tui.py import roots after Step 1 / Step 2:
  __future__ annotations
  curses                         (stdlib)
  dataclasses.dataclass
  typing.TYPE_CHECKING / Callable / Optional
  brain.ui.commands
  brain.ui.render
  brain.ui.session
  brain.ui.snapshot
  (TYPE_CHECKING-only)  brain.llm.client.LLMClient

  No new forbidden import was introduced. The I-UI-11 static AST
  audit in brain/ui/fixtures/tui_smoke.py still rejects os.system,
  subprocess, socket, urllib, http, requests, and brain.llm at
  runtime import depth, and still passes.
```

---

## Manual test instructions

Run these in a usable interactive terminal. The first two are
non-interactive and do not require curses; the third requires a
TTY-attached terminal.

```bash
python3 -m brain.ui --check-terminal
python3 -m brain.ui --print-once
python3 -m brain.ui
```

Expected behaviour for each:

```text
python3 -m brain.ui --check-terminal
  Prints "usable=<True|False>, reason=..." and exits.
  Exit code 0 when usable, 1 otherwise. Never touches curses.

python3 -m brain.ui --print-once
  Renders one deterministic frame of the default operator view to
  stdout and exits 0. Static, non-interactive. Does not consume the
  terminal and does not open curses.

python3 -m brain.ui
  Opens the curses wrapper against the default offline session and
  the OfflineStandInClient. Use the interactive flow below to drive
  a bottom-up PerceptEvent through tick().
```

Interactive key sequence to exercise the patch:

```text
e -> type content_id/text -> space -> inspect tick/state

Concretely:
  e                                 open the bounded percept prompt
  beta<Enter>                        content_id (or any printable
                                     id that does not collide with
                                     COGITO_ID)
  hello operator<Enter>              text payload
  (the prompt closes; the queued
   summary appears in the view)
  space                              run one tick() with the queued
                                     PerceptEvent; the returned
                                     TickRecord replaces session
                                     state via the public path
  t                                  switch to the tick view to
                                     inspect the TickRecord
  s                                  switch to the state view to
                                     inspect the new BrainState
                                     (profile / MSI / PtCns)
  o / w / r                          inspect OutputHistory /
                                     WorldletHistory / ProtoBasic
                                     REPL history
  c                                  clear local UI status / error
  ? or h                             show the help pane
  q                                  quit cleanly
```

Empty content_id or empty text at the prompt cancels via a clean
local UI error and leaves session state unchanged.

---

## Remaining limitations

```text
--print-once stays static and non-interactive. It renders one
  deterministic frame of the default offline session and exits.
  This is intentional: the flag exists for inspection without a
  curses-capable terminal and is not in scope for interactive
  percept queuing.

Phase 3.5 Expression + ReadabilityPredictor remains deferred. The
  Operator TUI live input patch is a UI usability fix, not a new
  cognitive layer. Expression / ReadabilityPredictor work is the
  next eligible cognitive campaign and is not authorized by this
  campaign's scope.

No real LLM scenario commands run. The entrypoint ships an
  OfflineStandInClient that returns "PRESERVE" for every prompt.
  This is the same deterministic local stand-in used by the
  Operator TUI campaign. A real LLM client is explicitly out of
  scope for this campaign and would require an explicit upstream
  authorization.

Save / export to the filesystem from the UI remains
  NOT-EXERCISED (I-UI-15 placeholder). The current campaign does
  not add any save / export surface. The placeholder is the
  registered chokepoint that prevents a future campaign from
  quietly adding filesystem writes from the UI without registered
  coverage.

The prompt is keystroke-driven and bounded to PROMPT_MAX_INPUT_LEN
  (64 chars per field). Multi-line payloads, ContentState
  customisation at prompt time, and operator-driven initial_rho
  adjustment are intentionally not exposed by the prompt; safe
  defaults (PROMPT_DEFAULT_CONTENT_STATE, PROMPT_DEFAULT_RHO) are
  used. Operators that need to customise these fields can build a
  Command in code and dispatch it via the existing OperatorSession
  API.
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
