# OPERATOR_TUI_AGENT_LAYOUT_SYNTHESIS.md

Step 1 synthesis for the Operator TUI Agent-Style Layout campaign
(`CURRENT_CAMPAIGN.md`). This document is the human-readable UX brief that
seeds the campaign; it does not change runtime behavior, the catalog, or any
fixture. It is a planning artifact only.

Baseline at the time of writing (preflight green):

```text
Catalog: v0.10
Counts: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 6 OBSERVED
Operator TUI campaign: PASS
Operator TUI live input patch: PASS and merged (commit 084f545)
Full gate (bash tools/check_all.sh): green (170 rows checked)
Entrypoint: python3 -m brain.ui
```

---

## 1. Problem statement

The Operator TUI shipped at v0.10 plus the live-input patch is **safe** but
not **ergonomic**. Every guardrail the campaign cares about is already in
place:

- read-only `BrainSnapshot` / `DevelopmentSnapshot` over kernel state;
- pure deterministic renderer (`brain.ui.render.render`);
- finite closed `OperatorCommand` enumeration with typed `Command` wrapper;
- `QUEUE_PERCEPT` is bounded by the public `PerceptEvent` constructor;
- `STEP_TICK` goes through the public `tick()` path only;
- validation / tick failures surface as local UI status, never trace writes;
- the curses wrapper imports no kernel / LLM / shell / network / file surface.

What the operator actually sees on the screen, however, is a **single
active inspector view** plus a help pane and a status/error line. Interaction
is a small set of single-letter keystrokes (`s`, `t`, `o`, `w`, `r`, `e`,
`space`, `c`, `?`, `q`). The `e` key opens a two-field bounded prompt for a
`content_id` and `text` payload, but only after the screen has been replaced
with the prompt; there is no persistent typing surface, no transcript of
what just happened, and no visible "what's queued" pane next to the live
state. The operator must rebuild context after every action.

In agent-style CLIs (Codex / Claude Code in a terminal) the operator expects:

- a stable header that summarizes the agent's state;
- a multi-pane body where the most relevant inspector is always visible;
- a transcript / event log that records what the operator typed and what
  the agent responded with;
- a persistent bottom composer where the operator types the next command,
  with a visible cursor and prompt mode;
- a footer that lists the keystroke contract.

The current TUI is structurally close to this layout — the data is already
available through `BrainSnapshot` and `DevelopmentSnapshot`, and the
`OperatorSession` already records the inputs it accepts — but the renderer
draws **one inspector at a time** and the bottom of the screen is owned by
the status / error pane rather than by a typed input surface.

This is a UI/UX deficit, not a kernel deficit. The campaign exists to fix it
without adding cognition, language, social behavior, Mode B, real LLM calls,
shell execution, network I/O, or host execution.

---

## 2. Agent-style target layout

The target layout is a deterministic rectangular composition. Sizes are
derived from the terminal `(width, height)` and stay deterministic for any
fixed geometry. The renderer remains terminal-agnostic; it returns a tuple
of bounded printable rows that the curses wrapper paints unchanged.

Schematic for a default 80×24 terminal (boundaries are illustrative; the
real renderer will use the existing `_truncate` / `_frame_header` helpers
plus a small `AgentLayout` geometry module to derive each pane):

```text
+----------------------------------------------------------------------------+
| brain.ui  tick=12  view=tick  queue=1/4  status=tick 12 ok (modeC)         |  <- header (1 row)
+--------------------------------+-------------------------------------------+
| [ core state ]                 | [ tick 12 ]                               |
|   profile size     : 2         |   mode trace    : modeC                   |
|   msi contents     : COGITO_ID,|   triggered     : MODE_C                  |
|                      alpha     |   notes         : (none)                  |  <- left pane: BrainState
|   eval positive    : COGITO_ID,|                                            |     right pane: selected
|                      alpha     |                                            |     inspector
|   boundary         : (none)    |                                            |
|   queued event     : alpha     |                                            |
+--------------------------------+-------------------------------------------+
| [ transcript ]                                                              |
|  t-3   /queue beta hello                                                    |
|  t-3   queued percept 'beta' (queue size = 1)                               |
|  t-2   /step                                                                |
|  t-2   tick 12 ok (modeC)                                                   |  <- transcript / event log
|  t-1   /tick                                                                |     (bounded, copy-on-write)
+----------------------------------------------------------------------------+
| > /queue beta hello-world_                                                  |  <- bottom composer
|   mode=local-cmd   cursor=22   history=2                                    |     (one row composer + one row meta)
+----------------------------------------------------------------------------+
| keys: enter submit  ^c clear  ^p prev  ^n next  /help full keymap          |  <- footer (1 row)
+----------------------------------------------------------------------------+
```

The composition holds the following stable contracts:

- **header** — exactly one row, always present, summarizing tick, active
  view, queue depth, and the latest status line; never empty.
- **left pane** — the BrainState / profile / MSI / PtCns / registry digest;
  always visible.
- **right pane** — the inspector the operator selected (state / tick /
  output / worldlet / repl / queue / status / help); always visible.
- **center/bottom pane: transcript** — a bounded, copy-on-write log of
  operator submissions and session responses; always visible.
- **bottom composer** — a one-row typing surface plus a one-row meta line
  (mode / cursor / history); always visible while the wrapper is alive.
- **footer** — a one-row key-hint strip; always visible.

The layout is "persistent": every pane is on screen at all times, regardless
of which inspector the operator is currently looking at. The active view
selects what the **right pane** shows; the left pane and the transcript do
not disappear.

---

## 3. Bottom composer thesis

The bottom composer is the campaign's primary ergonomic move. It is a
typed-input surface anchored at the bottom of the screen that the operator
uses to submit local UI commands. Three rules define what it is and what it
is not:

1. **It is a local UI command line, not a chat surface.** What the operator
   types is parsed by a finite `LocalCommandLine` grammar and mapped to an
   existing `OperatorCommand` (or rejected with a local error). Free text
   that does not start with `/` is not interpreted as natural language; it
   is either treated as a local-command argument (after a `/queue`-style
   prefix) or rejected as "unknown command".

2. **It is not a shell, REPL, or Proto-BASIC surface.** The composer does
   not call `os.system`, `subprocess`, `eval`, or `exec`. It does not call
   `brain.development.repl` either — the "repl" view is a Phase 3.4
   developmental history inspector, not a Python REPL.

3. **It does not mutate kernel state directly.** Every accepted command is
   converted to a `Command` and dispatched through
   `OperatorSession.dispatch(...)`. The composer is upstream of
   `make_command`; the existing routing guarantees the kernel boundary is
   intact.

The composer state is small and deterministic:

```text
ComposerState
  buffer       : str (printable, bounded length)
  cursor       : int (0..len(buffer))
  history      : tuple[str, ...] (bounded ring of submitted lines)
  history_idx  : Optional[int]
  mode         : "local-cmd" (only mode this campaign defines)
  status_line  : str (printable, bounded; mirrors session.status_message)
```

Every keystroke produces a `ComposerAction` that yields the next
`ComposerState`. Enter produces a `submit` event which the curses wrapper
hands to a `LocalCommandLine.parse(...)` call. The parse result is either
a `Command` (dispatched normally) or a `LocalCommandError` (recorded as a
local UI status; no session mutation beyond `set_error`).

The composer is **not** required to support multi-line input, syntax
highlighting, autocomplete, or fuzzy match in this campaign. Those would
duplicate the planning surface or hint at cognitive features.

---

## 4. Pane / window requirements

The agent-style layout introduces a small geometry primitive plus a renderer
that walks panes deterministically. Concretely:

- a `PaneSpec` record names a pane (`header`, `state`, `inspector`,
  `transcript`, `composer`, `footer`), gives its row/column bounds, and
  carries the renderer hook that produces its rows;
- an `AgentLayout` record holds the ordered tuple of `PaneSpec` values
  derived from the supplied `(width, height)`; layout derivation is a pure
  function of geometry;
- `render(view)` walks `view.layout.panes` in order, calls each pane's
  renderer, truncates each row to its pane width, pads short rows, and
  returns the concatenated rows ready for `paint_rows`.

The geometry is deterministic and bounded:

- `header` is exactly 1 row (always);
- `footer` is exactly 1 row (always);
- `composer` is exactly 2 rows (one editor row, one meta row);
- `state` and `inspector` share the body's top section, split horizontally
  at the layout's midline; both have at least `MIN_PANE_WIDTH` columns;
- `transcript` occupies the remaining body rows between the inspectors and
  the composer; it has at least `MIN_TRANSCRIPT_ROWS` rows on any terminal
  that satisfies the existing `MIN_WIDTH` / `MIN_HEIGHT` floor.

Small-terminal behavior is **degraded but stable**: if the terminal is too
narrow to keep the two inspectors side-by-side, the layout collapses to a
single column with `state` on top and `inspector` below; if the terminal is
too short to keep the transcript, the transcript is reduced to its newest
two rows. The composer and footer are **never** sacrificed; the layout
contract guarantees that typing remains possible on any terminal that meets
the existing `MIN_WIDTH` / `MIN_HEIGHT` floor.

The renderer remains pure: no curses, no file I/O, no network, no
subprocess. The wrapper paints whatever the renderer returns.

---

## 5. Typed local command requirements

The campaign defines a finite set of local UI commands that the bottom
composer accepts. Each command maps to an existing `OperatorCommand` or to
a parameterized `QueuePerceptPayload`. The grammar is total: anything that
does not match is rejected as `LocalCommandError`.

Approved local commands and their mappings:

```text
/help                            -> Command(HELP)
/state                           -> Command(INSPECT_STATE)
/tick                            -> Command(INSPECT_TICK)
/output                          -> Command(INSPECT_OUTPUT)
/worldlet                        -> Command(INSPECT_WORLDLET)
/repl                            -> Command(INSPECT_REPL)
/queue <content_id> <text...>    -> Command(QUEUE_PERCEPT, QueuePerceptPayload(...))
/step                            -> Command(STEP_TICK)
/clear                           -> Command(CLEAR_STATUS)
/quit                            -> Command(QUIT)
```

Notes on each:

- `/queue` accepts exactly two positional arguments: a `content_id` (single
  printable token, no whitespace) and the remainder of the line as `text`.
  The composer builds a `QueuePerceptPayload` with the same defaults the
  existing curses prompt uses (`PROMPT_DEFAULT_CONTENT_STATE`,
  `PROMPT_DEFAULT_RHO`), so the public `PerceptEvent` constructor is the
  validation point. Out-of-range or `COGITO_ID`-colliding inputs raise
  `ValueError`; the composer converts that to a local UI error.
- `/step` is keystroke-equivalent to the existing `space` shortcut. The
  short keys are retained as accelerators; typed commands are the primary
  surface.
- `/clear` clears only the local status / error fields (and may also clear
  the composer buffer; the kickoff document will lock this).
- `/quit` is keystroke-equivalent to `q`; the wrapper exits cleanly.
- Anything else, including `/foo`, plain text without a `/` prefix, or a
  `/queue` line missing one of its arguments, is rejected as
  `LocalCommandError` and surfaced through `session.set_error(...)`.

The parser is implemented as a pure function in a new
`brain/ui/command_line.py` module. It performs no shell expansion, no glob
expansion, no environment variable substitution, no JSON / YAML / TOML
parsing, and does not call any kernel function directly.

---

## 6. Transcript / event log requirements

The transcript is a bounded, copy-on-write record of operator-visible
events. It lives entirely in local UI state and is destroyed when the
wrapper exits.

Required entry kinds:

```text
SUBMIT     - the operator submitted a parsed line (echoes the line)
QUEUED     - a percept was successfully queued (echoes the summary)
STEP       - a tick step completed (echoes the new tick index + mode)
ERROR      - a local UI error occurred (echoes the bounded printable text)
VIEW       - the active view changed (echoes the new view name)
QUIT       - the operator asked to quit (echoes the local message)
```

Each `TranscriptEntry` is a frozen dataclass with `kind`, `tick_at_event`,
and a bounded printable `text` field. The transcript itself is a frozen
tuple wrapped in an `OperatorTranscript` record; new entries are appended
by returning a new transcript record (copy-on-write), matching the
`ProtoBasicHistory` / `WorldletHistory` style.

The transcript:

- **is not** a `OutputHistory` / `WorldletHistory` / `ProtoBasicHistory`
  record. It does not feed back into developmental layers; it is a local
  UI log only;
- **is not** a trace surface. It is never written to a file, JSONL stream,
  trace seam, scenario, or external sink;
- **is bounded**: at most `TRANSCRIPT_MAX_ENTRIES` rows are retained
  (kickoff to lock the exact number; suggested `64`). Older entries fall
  off the front;
- **is printable**: every entry's text passes the same
  `_bound_printable(...)` policy that `OperatorSession` already uses for
  status / error;
- **is non-causal**: it does not change kernel state, does not trigger
  ticks, does not influence `PtCns.eval`, and does not enter the
  developmental layers.

The transcript is the visible memory of the session. It is the operator's
"what just happened" surface, in contrast to the inspector panes which are
"what is true right now".

---

## 7. How it remains an operator UI, not cognition

The campaign is **engineering UX work**, not a cognitive expansion. The
following properties are non-negotiable:

- **No Phase 3.5 work.** The campaign does not introduce
  `ExpressionImpulse`, `ReadabilityPredictor`, social/language harness,
  or Mode B. The composer is a UI surface, not an expression channel.
- **No real LLM calls.** The kernel's `tick()` continues to take an
  `LLMClient`; the entrypoint continues to pass the `OfflineStandInClient`
  that returns `"PRESERVE"`. The composer cannot reach a real model.
- **No shell, subprocess, network, or file I/O.** The composer's parser
  imports nothing from `os.system` / `subprocess` / `socket` / `urllib` /
  `http` / `requests`. The transcript is not written to disk. The
  `tools.import_audit` row continues to enforce this.
- **No direct BrainState mutation.** Every command flows through
  `OperatorSession.dispatch(...)` and (for `STEP_TICK`) through the public
  `tick()` entrypoint. The session's `_assert_no_unsafe_resources` audit
  remains in force; no new attribute is added to the session that could
  carry a callable, file handle, socket, or LLM client.
- **No scenario / trace writes.** The transcript and composer state are
  process-local. They never enter `traces/`, `scenarios/`, or any
  developmental history file.
- **No new theory semantics.** The campaign does not add to TLICA, TOCE,
  or any Lean-bound row. New `I-UI-*` rows are engineering-hypothesis
  rows in the existing UI family, not Lean-theorem rows.
- **Catalog discipline preserved.** New rows go through the standard
  catalog patch process (kickoff -> corrigenda -> patch plan -> review
  gate -> apply -> implement -> drive -> audit). No row is added that
  weakens an existing `I-UI-*` row.

The kernel boundary stays exactly where it is. The composer changes how
the operator types, not what the kernel does.

---

## 8. Non-goals

The following are explicitly out of scope for this campaign, and any
proposal that requires them should escalate rather than be folded in:

- natural-language understanding of composer input;
- LLM-backed autocompletion or suggestions;
- a Proto-BASIC editor / runner in the composer (Phase 3.4 already exists
  as a developmental history layer; the composer's `/repl` command is an
  *inspector* into that history, not a way to edit it);
- expression generation (Phase 3.5 Expression + ReadabilityPredictor) or
  any social/language harness;
- writing the transcript to a file, JSONL trace, scenario, or external
  sink;
- spawning a subprocess, shell, browser, or external editor;
- network I/O of any kind;
- multi-session multiplexing (one curses wrapper drives one session);
- mouse handling, color attributes, true-color rendering, Unicode
  emoji rendering, or any feature outside `addnstr` + `getstr`;
- terminal automation outside the curses UI (no `tmux`, no `screen`, no
  `expect` integration);
- save / export of `BrainState` or developmental histories;
- arbitrary Python execution.

The non-goals list is enforced by the same audit surfaces the existing
campaign uses: `I-UI-07` (import audit), `I-UI-10` (no unsafe resources
on the session), and `I-UI-11` (curses wrapper has no kernel / LLM /
shell / network / file imports).

---

## 9. Risks

- **Layout determinism on small terminals.** A buggy responsive geometry
  could let one pane "eat" the composer. Mitigation: explicit
  `MIN_PANE_WIDTH` / `MIN_TRANSCRIPT_ROWS` floors in `brain/ui/layout.py`,
  with `I-UI-22` (STRUCTURAL) asserting the composer is always present in
  the rendered rows when geometry meets `MIN_WIDTH` / `MIN_HEIGHT`.
- **Transcript growth.** Without a bound, the transcript could leak
  memory or blow past the renderer's truncation budget. Mitigation:
  fixed `TRANSCRIPT_MAX_ENTRIES`, copy-on-write semantics, frozen
  dataclasses, and `I-UI-19` (REQUIRED) asserting the bound holds across
  any sequence of submissions.
- **Composer parser surface creep.** A free-form composer is tempting to
  extend with shell-like features. Mitigation: `I-UI-18` (REQUIRED)
  asserts the parser is finite and maps only to the approved
  `OperatorCommand` set; the import-audit surface is extended to cover
  the new `command_line.py` module.
- **Confusion between `/repl` (inspector) and a Python REPL.** A user
  may expect `/repl` to execute Python. Mitigation: `/help` documents
  the distinction; the corrigenda calls it out; the kickoff specifies
  the inspector contract.
- **Chat-surface drift.** A bottom composer can be read as a chat box.
  Mitigation: the prompt prefix (`> `) and meta line (`mode=local-cmd`)
  signal the local-command surface; the corrigenda enumerates the
  distinction between composer and chat.
- **Catalog row weakening.** Adding new rows shouldn't water down
  existing ones. Mitigation: the catalog patch plan must restate each
  existing `I-UI-*` row's status and explicitly say "unchanged" for
  each row this campaign does not amend.

---

## 10. Next artifact

The next campaign step (Step 2) produces:

```text
OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md
```

That document will lock the concrete contracts named in this synthesis:

- `AgentLayout`, `PaneSpec`, `PaneRenderResult` (terminal-agnostic
  geometry primitives);
- `BottomComposer`, `ComposerState`, `ComposerAction` (editor model);
- `LocalCommandLine` parser (finite grammar; pure function);
- `OperatorTranscript`, `TranscriptEntry` (bounded copy-on-write log);
- layout-aware `TuiViewModel` (extension, not replacement);
- responsive pane sizing rules;
- typed command flow end-to-end;
- keyboard flow (preserving the existing single-letter accelerators);
- scrollback / log discipline;
- non-interactive fixture strategy.

The kickoff explicitly excludes real LLM chat, shell command execution,
filesystem save / export, network I/O, Mode B planning, Expression +
ReadabilityPredictor, social/language harness, and any new theory
semantics. After the kickoff, Step 3 is a corrigenda pass; Step 4 is the
catalog patch plan; Step 5 is the review gate before any code lands.

Stop condition for the campaign as a whole is in `CURRENT_CAMPAIGN.md`
Step 12: a post-completion audit verdict of PASS / PASS WITH PATCHES /
BLOCKED, recorded in `OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md`.
