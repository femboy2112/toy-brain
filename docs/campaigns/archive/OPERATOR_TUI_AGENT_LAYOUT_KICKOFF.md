# OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md

Step 2 kickoff for the Operator TUI Agent-Style Layout campaign
(`CURRENT_CAMPAIGN.md`). This kickoff locks the concrete planning
contracts named in `OPERATOR_TUI_AGENT_LAYOUT_SYNTHESIS.md` so the
remaining campaign steps (corrigenda, catalog patch plan, review gate,
implementation, drive, audit) have a single source of truth.

It is a **planning artifact only**. It does not:

```text
modify runtime code
add or amend catalog rows
create fixtures
change tick() semantics
change developmental histories
write traces or scenarios
add dependencies
authorize host execution, shell, network, or LLM calls
```

Baseline at the time of writing (preflight green):

```text
Catalog: v0.10
Counts: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 6 OBSERVED
Operator TUI campaign: PASS
Operator TUI live input patch: PASS and merged (commit 084f545)
Synthesis (Step 1): present (commit 0a9d3d4)
Full gate (bash tools/check_all.sh): green (170 rows checked)
Entrypoint: python3 -m brain.ui
```

---

## 1. Purpose

The synthesis established the UX deficit (single inspector + status pane
at the bottom) and the agent-style target (persistent panes plus a bottom
composer typing surface). This kickoff converts that brief into a list of
**named contracts** with concrete field surfaces, invariants, and
mappings to existing public APIs.

Every contract below is engineering-hypothesis material for new
`I-UI-*` rows in the catalog patch plan (Step 4). None of these
contracts modifies kernel state, developmental histories, traces, or
scenario files. Each is a **local UI** record or pure function.

The kickoff is intentionally explicit about what **not** to build:
real LLM chat, shell command execution, filesystem save/export, network
I/O, Mode B planning, Expression + ReadabilityPredictor, social/language
harness, and any new theory semantics are out of scope here and remain
out of scope through the campaign.

---

## 2. AgentLayout

`AgentLayout` is the terminal-agnostic geometry record produced from a
`(width, height)` pair. It is the input contract to the pure renderer's
new layout-aware path.

Shape:

```text
AgentLayout (frozen dataclass)
  width        : int           # >= MIN_WIDTH
  height       : int           # >= MIN_HEIGHT
  panes        : tuple[PaneSpec, ...]
  collapsed    : bool          # True when state+inspector collapsed vertically
  transcript_rows : int        # remaining body rows; >= MIN_TRANSCRIPT_ROWS
```

Construction:

```text
AgentLayout.from_size(width: int, height: int) -> AgentLayout
```

Rules (deterministic; pure function of `(width, height)`):

```text
width  < MIN_WIDTH  -> raise ValueError (matches existing render contract)
height < MIN_HEIGHT -> raise ValueError (matches existing render contract)
header is exactly 1 row, always present
footer is exactly 1 row, always present
composer is exactly 2 rows (one edit row + one meta row), always present
state and inspector share the body's top section
  default: side-by-side, split at width // 2 with a 1-column gutter
  collapsed (width < MIN_SIDE_BY_SIDE_WIDTH or panes don't fit MIN_PANE_WIDTH):
    state on top, inspector below, transcript still beneath
transcript occupies the rows between state/inspector and composer
  transcript_rows == max(MIN_TRANSCRIPT_ROWS, residual_body_rows)
```

Floors (locked in this kickoff; catalog patch plan may rename, not lower):

```text
MIN_WIDTH            = existing brain.ui.render.MIN_WIDTH (20)
MIN_HEIGHT           = existing brain.ui.render.MIN_HEIGHT (6)
MIN_PANE_WIDTH       = 18    # minimum columns for a side-by-side pane
MIN_SIDE_BY_SIDE_WIDTH = 2 * MIN_PANE_WIDTH + 1   # gutter
MIN_TRANSCRIPT_ROWS  = 2     # newest two transcript rows survive on small terminals
```

Invariants `AgentLayout` enforces:

```text
header row count          == 1
footer row count          == 1
composer row count        == 2
sum(pane.height for pane in panes) == height
every pane.width          <= width
every pane.width          >= MIN_PANE_WIDTH (when side-by-side)
panes are ordered top-to-bottom, left-to-right
no overlap between panes (row-major + column-major addressing is unique)
the composer pane is present in every layout
```

The geometry never reads a real terminal. It never imports `curses`. It
is a pure function and therefore trivially testable from a fixture that
sweeps `(width, height)` over a deterministic grid.

---

## 3. PaneSpec

`PaneSpec` is the per-pane record carried inside `AgentLayout.panes`. It
names a pane, declares its rectangular bounds, and points at the
renderer hook that produces its rows.

Shape:

```text
PaneSpec (frozen dataclass)
  name        : PaneName     # closed enumeration (see below)
  row         : int          # top row index, 0-based, inclusive
  col         : int          # left column index, 0-based, inclusive
  height      : int          # row count (1..AgentLayout.height)
  width       : int          # column count (1..AgentLayout.width)
  renderer    : str          # function key into the renderer dispatch table
```

`PaneName` is a closed enumeration:

```text
HEADER
STATE          # left pane (BrainState / profile / MSI / PtCns / registry)
INSPECTOR      # right pane (the active inspector view)
TRANSCRIPT     # center/bottom pane (event log)
COMPOSER       # bottom composer (1 edit row + 1 meta row, treated as one pane)
FOOTER
```

The `renderer` field is a **string key** into a finite dispatch table
in `brain/ui/render.py`. It is not a callable on the record — keeping
the field plain str preserves the "no callables on UI records" rule
that contributes to the existing `I-UI-10` audit (`OperatorSession`
holds no unsafe resources). The dispatch table maps a renderer key to a
pure function `(view, pane) -> tuple[str, ...]`.

Allowed renderer keys (initial set):

```text
"header"
"state"
"inspector"
"transcript"
"composer"
"footer"
```

`PaneSpec` is frozen, slots-based, and has no callables, file handles,
sockets, or LLM-client-shaped objects.

---

## 4. PaneRenderResult

`PaneRenderResult` is the pure renderer's per-pane output. The
top-level renderer composes these into the final rendered rows.

Shape:

```text
PaneRenderResult (frozen dataclass)
  name        : PaneName
  rows        : tuple[str, ...]   # length == pane.height
                                  # every row truncated/padded to pane.width
```

Construction rules:

```text
len(rows) == pane.height                 (renderer pads short bodies with "")
every row passes _truncate(row, pane.width)
every row is bounded printable text (matches I-UI-13 policy)
no row contains terminal control sequences
no row contains a callable / file path / network endpoint
```

Composition rule:

```text
render(view) -> tuple[str, ...]:
  layout = view.layout
  acc = [""] * layout.height
  for pane in layout.panes:
      result = dispatch(pane.renderer)(view, pane)
      for i, row in enumerate(result.rows):
          place row at (pane.row + i, pane.col .. pane.col + pane.width)
  return tuple(acc)
```

The composer pane's `rows` always have exactly 2 entries: the editor
row (`> <buffer>` with a visible cursor marker truncated to pane width)
and the meta row (`mode=local-cmd  cursor=N  history=M`). This holds
even when the buffer is empty.

---

## 5. BottomComposer

`BottomComposer` is the editor model for the bottom typing surface. It
is a pure record + a small set of transition functions; the curses
wrapper owns input and paints the rendered rows but does not own the
state machine.

Shape:

```text
BottomComposer (module-level, not a class instance)
  - exports ComposerState
  - exports ComposerAction (closed enumeration)
  - exports apply(state, action) -> ComposerState | ComposerSubmission
```

The composer is **not** a class with hidden state; it is a pure
state-transition function over `ComposerState`. This matches the rest
of the UI surface (`OperatorSession` is dataclass-shaped,
`BrainSnapshot` is frozen, `TuiViewModel` is frozen) and keeps the
audit story simple.

---

## 6. ComposerState

Shape:

```text
ComposerState (frozen dataclass, slots)
  buffer       : str                  # printable, len <= MAX_COMPOSER_BUFFER
  cursor       : int                  # 0 <= cursor <= len(buffer)
  history      : tuple[str, ...]      # bounded ring of submitted lines
  history_idx  : Optional[int]        # None == not browsing history
  mode         : str                  # "local-cmd" only in this campaign
  status_line  : str                  # bounded printable; mirrors session.status_message
```

Bounds (locked here):

```text
MAX_COMPOSER_BUFFER  = MAX_STATUS_TEXT_LEN   # 240, same bound as status pane
MAX_HISTORY_ENTRIES  = 32                    # bounded ring; oldest entries fall off
MODE_LOCAL_CMD       = "local-cmd"           # only mode this campaign defines
```

Invariants enforced at `__post_init__`:

```text
isinstance(buffer, str) and (buffer == "" or buffer.isprintable())
len(buffer) <= MAX_COMPOSER_BUFFER
0 <= cursor <= len(buffer)
every history entry is bounded printable text (same _bound_printable policy)
len(history) <= MAX_HISTORY_ENTRIES
history_idx is None or (0 <= history_idx < len(history))
mode in {MODE_LOCAL_CMD}
status_line is bounded printable text
```

Initial state:

```text
ComposerState.empty() -> ComposerState(
    buffer="",
    cursor=0,
    history=(),
    history_idx=None,
    mode=MODE_LOCAL_CMD,
    status_line="",
)
```

The composer state is **never** stored on `OperatorSession`. It lives
in the layout-aware `TuiViewModel` and on the curses wrapper's local
stack. Storing it on the session would require `I-UI-10` to be widened
to permit a new field; we explicitly avoid that.

---

## 7. ComposerAction

Closed enumeration of input events the composer accepts. The curses
wrapper translates a single keypress (or a small key sequence) into one
of these actions before calling `apply(...)`.

```text
ComposerAction (closed enumeration)
  INSERT_CHAR        # payload: single printable char
  BACKSPACE          # delete char before cursor
  DELETE             # delete char at cursor (optional; default DELETE_NOOP)
  CURSOR_LEFT
  CURSOR_RIGHT
  CURSOR_HOME
  CURSOR_END
  HISTORY_PREV       # ^P / KEY_UP
  HISTORY_NEXT       # ^N / KEY_DOWN
  CLEAR_BUFFER       # ^C (or ^U); clears buffer and history_idx
  SUBMIT             # Enter; emits ComposerSubmission
```

`apply(state, action)` is a pure function:

```text
apply(state: ComposerState, action: ComposerAction, *, char: Optional[str] = None)
  -> Union[ComposerState, ComposerSubmission]
```

Rules:

```text
INSERT_CHAR  -> char must be a single printable char; buffer inserted at cursor
               (cursor += 1); rejects non-printable, NUL, control, or
               multi-codepoint input as a no-op returning the same state
BACKSPACE    -> if cursor > 0, remove buffer[cursor-1]; cursor -= 1; else no-op
DELETE       -> if cursor < len(buffer), remove buffer[cursor]; else no-op
CURSOR_LEFT  -> if cursor > 0, cursor -= 1
CURSOR_RIGHT -> if cursor < len(buffer), cursor += 1
CURSOR_HOME  -> cursor = 0
CURSOR_END   -> cursor = len(buffer)
HISTORY_PREV -> if history is non-empty:
                  next_idx = (len(history) - 1) if history_idx is None
                            else max(0, history_idx - 1)
                  buffer = history[next_idx]; cursor = len(buffer)
HISTORY_NEXT -> if history_idx is not None:
                  next_idx = history_idx + 1
                  if next_idx >= len(history): clear back to ""; history_idx = None
                  else: buffer = history[next_idx]; cursor = len(buffer)
CLEAR_BUFFER -> buffer = ""; cursor = 0; history_idx = None
SUBMIT       -> if buffer.strip() == "": return state with status_line set
                  ("empty composer submission") and buffer unchanged
                else: return ComposerSubmission(
                  line=buffer,
                  next_state=ComposerState with buffer="", cursor=0,
                             history=push(history, buffer, MAX_HISTORY_ENTRIES),
                             history_idx=None,
                             mode=mode,
                             status_line=state.status_line,
                )
```

`ComposerSubmission` is a frozen dataclass with two fields:

```text
ComposerSubmission (frozen dataclass)
  line       : str               # the submitted text, exactly as typed
  next_state : ComposerState     # the composer state to adopt
```

The wrapper hands `ComposerSubmission.line` to `LocalCommandLine.parse`
and adopts `next_state` as the new composer state regardless of parse
outcome (so a bad command does not eat the operator's history).

---

## 8. LocalCommandLine parser

`LocalCommandLine` is a finite grammar that maps a submitted composer
line to either a `Command` or a `LocalCommandError`. It lives in a new
module `brain/ui/command_line.py` and is a pure function.

Public surface:

```text
brain.ui.command_line.parse(line: str) -> ParseResult
ParseResult = Union[Command, LocalCommandError]

LocalCommandError (frozen dataclass)
  message : str   # bounded printable text, suitable for session.set_error
```

Grammar (locked here; corrigenda may tighten, not loosen):

```text
line = optional_whitespace, "/", verb, [SP, args], optional_whitespace
verb = one of:
   "help" | "state" | "tick" | "output" | "worldlet" | "repl"
   | "queue" | "step" | "clear" | "quit"
args :
   for "queue": <content_id> SP <text...>
       content_id := one printable non-whitespace token; must not equal COGITO_ID
                     (rejection is delegated to PerceptEvent; parser only checks
                      "no whitespace" and "non-empty")
       text       := the remainder of the line (after the first whitespace gap)
   for every other verb: no args; any args yield LocalCommandError
```

Mapping table:

```text
/help     -> Command(HELP)
/state    -> Command(INSPECT_STATE)
/tick     -> Command(INSPECT_TICK)
/output   -> Command(INSPECT_OUTPUT)
/worldlet -> Command(INSPECT_WORLDLET)
/repl     -> Command(INSPECT_REPL)
/queue <content_id> <text...>
          -> make_command(QUEUE_PERCEPT,
                          content_id=<content_id>,
                          text=<text>,
                          content_state=PROMPT_DEFAULT_CONTENT_STATE,
                          initial_rho=PROMPT_DEFAULT_RHO)
/step     -> Command(STEP_TICK)
/clear    -> Command(CLEAR_STATUS)
/quit     -> Command(QUIT)
```

Rejection cases (each returns a `LocalCommandError` with bounded text):

```text
"" or whitespace-only          -> "empty command"
no leading "/"                 -> "expected leading '/'"
unknown verb                   -> "unknown command: '{verb}'"
/queue without content_id      -> "/queue requires <content_id> <text>"
/queue without text            -> "/queue requires <content_id> <text>"
/queue content_id with whitespace -> never reachable (tokenizer splits on first SP)
/queue payload rejected by PerceptEvent (COGITO_ID collision, non-printable text,
   out-of-range rho) -> "/queue rejected: {ValueError message}"
any other verb with args       -> "/{verb} does not accept arguments"
```

What the parser **does not** do:

```text
no shell expansion           (no $VAR, no `cmd`, no globbing)
no JSON / YAML / TOML / XML  parsing
no eval / exec / compile
no os.system / subprocess / socket / urllib / http / requests imports
no kernel-state mutation     (only builds Command records)
no PerceptEvent construction outside QueuePerceptPayload's constructor
no natural-language interpretation of non-"/" input
no fuzzy match / autocomplete / suggestions
no multi-command lines (one verb per submission)
```

Tokenizer is `str.split(None, 1)` applied to the post-`/` body, so
exactly two tokens at most. `content_id` and `text` are bounded by the
existing `MAX_STATUS_TEXT_LEN` policy through `_bound_printable`.

---

## 9. OperatorTranscript / TranscriptEntry

The transcript is a bounded copy-on-write log of operator-visible
events. It lives entirely in local UI state.

Shape:

```text
TranscriptEntry (frozen dataclass)
  kind            : TranscriptKind   # closed enumeration
  tick_at_event   : int              # session.tick_counter at append time
  text            : str              # bounded printable text

TranscriptKind (closed enumeration)
  SUBMIT       # operator submitted a parsed line
  QUEUED       # a percept was successfully queued
  STEP         # a tick step completed
  ERROR        # a local UI error occurred
  VIEW         # the active view changed
  QUIT         # operator asked to quit

OperatorTranscript (frozen dataclass)
  entries : tuple[TranscriptEntry, ...]   # newest entries last
  limit   : int                           # default TRANSCRIPT_MAX_ENTRIES
```

Bounds (locked here):

```text
TRANSCRIPT_MAX_ENTRIES = 64
```

Operations (all copy-on-write; return a new `OperatorTranscript`):

```text
OperatorTranscript.empty(limit: int = TRANSCRIPT_MAX_ENTRIES) -> OperatorTranscript
OperatorTranscript.append(entry: TranscriptEntry) -> OperatorTranscript
   - if len(entries) >= limit, drop the oldest before appending
OperatorTranscript.tail(n: int) -> tuple[TranscriptEntry, ...]
   - newest n entries, in order; used by the transcript pane renderer
```

Invariants:

```text
every entry's text passes _bound_printable
len(entries) <= limit at all times
limit > 0
appending an entry returns a NEW OperatorTranscript (frozen tuple)
no entry is a callable, file handle, socket, or LLM-client-shaped object
transcript is never written to disk, JSONL, trace, scenario, or external sink
transcript is never appended to OutputHistory / WorldletHistory / ProtoBasicHistory
transcript is never read by tick() or any kernel function
```

Where the transcript lives:

```text
On the layout-aware TuiViewModel (see section 10).
NOT on OperatorSession (avoids widening the I-UI-10 attribute surface).
The curses wrapper owns the canonical OperatorTranscript value and threads
it into the TuiViewModel each frame.
```

---

## 10. Layout-aware TuiViewModel

The existing `TuiViewModel` (in `brain/ui/render.py`) carries the
snapshots, queue summary, status/error, keyboard help, width/height, and
active view. The agent layout extends — does not replace — that record.

Extended shape (the new record is named `AgentTuiViewModel` to avoid
breaking the existing renderer; both records may coexist for the
duration of the campaign and the old one is retired in Step 10 once
the wrapper switches over):

```text
AgentTuiViewModel (frozen dataclass)
  # Fields inherited from TuiViewModel:
  active_view          : str                   # one of ACTIVE_VIEWS
  state_snapshot       : BrainSnapshot
  development_snapshot : DevelopmentSnapshot
  queue_summary        : tuple[str, ...]
  status_message       : str
  error_message        : str
  keyboard_help        : tuple[tuple[str, str], ...]
  width                : int
  height               : int

  # New fields:
  layout               : AgentLayout
  composer             : ComposerState
  transcript           : OperatorTranscript
  tick_counter         : int    # mirrors session.tick_counter for the header pane
```

Construction:

```text
AgentTuiViewModel.from_session(
    session: OperatorSession,
    *,
    width: int,
    height: int,
    composer: ComposerState,
    transcript: OperatorTranscript,
) -> AgentTuiViewModel
```

The from_session factory reads the session through its existing
read-only helpers (snapshot builders, `queued_event_summary`,
`keyboard_help`, `active_view`, `status_message`, `error_message`,
`tick_counter`). It never mutates the session.

Determinism rule:

```text
For the same (session-derived snapshot bundle, width, height, composer,
transcript) the from_session factory returns equal AgentTuiViewModel
records. Equality is structural (frozen dataclass + tuple fields).
```

The renderer signature on the agent path:

```text
render(view: AgentTuiViewModel) -> tuple[str, ...]
```

Returns exactly `view.height` rows, each bounded to `view.width`.
Implementation walks `view.layout.panes` and dispatches per-pane
renderers as described in section 4.

---

## 11. Responsive pane sizing

Concrete derivation (used by `AgentLayout.from_size`):

```text
INPUTS:  width (int >= MIN_WIDTH), height (int >= MIN_HEIGHT)

STEP A. header row:
    HEADER pane: row=0, col=0, height=1, width=width
STEP B. footer row:
    FOOTER pane: row=height-1, col=0, height=1, width=width
STEP C. composer rows (2):
    COMPOSER pane: row=height-3, col=0, height=2, width=width
STEP D. body region:
    body_top = 1
    body_bottom = height - 3       # exclusive; composer starts here
    body_rows = body_bottom - body_top
    if body_rows < (1 + MIN_TRANSCRIPT_ROWS):
        # Degenerate: collapse transcript to 0 rows; state/inspector share body.
        # Composer and footer always survive.
        transcript_rows = 0
    else:
        transcript_rows = max(MIN_TRANSCRIPT_ROWS, body_rows // 3)
    inspector_rows = body_rows - transcript_rows
STEP E. inspector split:
    if width >= MIN_SIDE_BY_SIDE_WIDTH:
        # Side-by-side
        collapsed = False
        left_width  = width // 2
        right_width = width - left_width
        STATE pane:     row=body_top, col=0,           height=inspector_rows, width=left_width
        INSPECTOR pane: row=body_top, col=left_width,  height=inspector_rows, width=right_width
    else:
        # Collapsed (single-column)
        collapsed = True
        state_rows     = inspector_rows // 2
        inspector_rows2 = inspector_rows - state_rows
        STATE pane:     row=body_top,                col=0, height=state_rows,     width=width
        INSPECTOR pane: row=body_top+state_rows,     col=0, height=inspector_rows2, width=width
STEP F. transcript pane (if transcript_rows > 0):
    TRANSCRIPT pane: row=body_bottom - transcript_rows, col=0,
                     height=transcript_rows, width=width
```

Edge cases (deterministic and locked here):

```text
height == MIN_HEIGHT (6):
    rows are: header(1), state(1), inspector(1), composer(2), footer(1)
    transcript is omitted (transcript_rows == 0)
    composer and footer are present
width  == MIN_WIDTH (20):
    side-by-side requires 2*MIN_PANE_WIDTH+1 = 37, so width=20 always collapses
    state on top, inspector below, transcript (if present) beneath
```

`AgentLayout` always satisfies:

```text
sum(p.height for p in panes) == height
each p.height >= 1
the COMPOSER pane is present (height == 2)
the FOOTER pane is present (height == 1)
the HEADER pane is present (height == 1)
```

This is the surface `I-UI-22` (STRUCTURAL, planned) asserts on
arbitrary grid-sweep inputs.

---

## 12. Typed command flow

End-to-end path for a typed line:

```text
1. curses wrapper reads a keystroke
2. wrapper maps keystroke -> ComposerAction (+ optional char)
3. wrapper calls BottomComposer.apply(state, action[, char=...])
4. if the return value is ComposerState: replace local composer state; redraw
5. if the return value is ComposerSubmission:
      adopt next_state as the new composer state
      transcript = transcript.append(TranscriptEntry(SUBMIT, tick, line))
      parse_result = LocalCommandLine.parse(submission.line)
      if parse_result is LocalCommandError:
          session.set_error(parse_result.message)
          transcript = transcript.append(TranscriptEntry(ERROR, tick, message))
      else:
          # parse_result is a Command record
          before = (session.state, session.latest_tick, len(session.event_queue))
          session.dispatch(parse_result, client=client)   # client kept on wrapper
          if session.error_message and was_set_by_this_dispatch:
              transcript = transcript.append(TranscriptEntry(ERROR, tick, error_message))
          elif parse_result.kind is QUEUE_PERCEPT:
              transcript = transcript.append(TranscriptEntry(QUEUED, tick, status_message))
          elif parse_result.kind is STEP_TICK:
              transcript = transcript.append(TranscriptEntry(STEP, tick, status_message))
          elif parse_result.kind is QUIT:
              transcript = transcript.append(TranscriptEntry(QUIT, tick, status_message))
          else:
              # an INSPECT_* / HELP / CLEAR_STATUS branch
              transcript = transcript.append(TranscriptEntry(VIEW, tick, status_message))
6. wrapper rebuilds AgentTuiViewModel from session + composer + transcript
7. wrapper calls render(view) and paints the rows
```

This path holds the campaign's kernel boundary exactly where it already
is. Every Command record still flows through `OperatorSession.dispatch`,
and every `STEP_TICK` still flows through `tick()` (drives existing
`I-UI-05`).

The LLM client used for `STEP_TICK` is **not** stored on the session
(drives existing `I-UI-10`); the curses wrapper passes it to `dispatch`
as the `client=` keyword, identical to today's behavior.

---

## 13. Keyboard flow

The existing single-letter accelerators stay; they coexist with the
bottom composer. A keystroke is interpreted as a composer action **only
when the composer has focus** (the default after startup). A small
escape table preserves the existing shortcuts:

```text
Default focus: composer.

Reserved keystrokes that bypass the composer (matches existing keyboard map):
  q              -> Command(QUIT)
  ?              -> Command(HELP) ; sets active_view="help"
  c              -> Command(CLEAR_STATUS)
  space          -> Command(STEP_TICK)  (when not editing — see rule below)
  s              -> Command(INSPECT_STATE)
  t              -> Command(INSPECT_TICK)
  o              -> Command(INSPECT_OUTPUT)
  w              -> Command(INSPECT_WORLDLET)
  r              -> Command(INSPECT_REPL)
  n              -> open the existing curses percept prompt
                    (preserves the live-input patch entrypoint; this is a
                     wrapper concession, not a composer feature)
```

Coexistence rule (locked here):

```text
The reserved keystrokes above ONLY fire when the composer's buffer is
empty AND the keystroke is not "/". Once the composer has any input or
the operator types "/", every printable keystroke (including space and
the reserved letters) goes to ComposerAction.INSERT_CHAR until the
composer is submitted, cleared, or explicitly emptied.
```

This rule is the kickoff's answer to the "typed text vs. accelerator"
ambiguity and the corrigenda may tighten the rule but may not loosen
it (the bottom composer must always be the primary surface once any
text is entered).

Composer-specific keys (always interpreted as composer actions,
regardless of buffer state):

```text
Enter          -> ComposerAction.SUBMIT
Backspace      -> ComposerAction.BACKSPACE
KEY_LEFT       -> ComposerAction.CURSOR_LEFT
KEY_RIGHT      -> ComposerAction.CURSOR_RIGHT
KEY_HOME / ^A  -> ComposerAction.CURSOR_HOME
KEY_END  / ^E  -> ComposerAction.CURSOR_END
KEY_UP   / ^P  -> ComposerAction.HISTORY_PREV
KEY_DOWN / ^N  -> ComposerAction.HISTORY_NEXT
^U / ^C        -> ComposerAction.CLEAR_BUFFER
```

If a keystroke is not in the table and is not a printable char, the
wrapper treats it as a no-op (no error, no state change).

---

## 14. Scrollback / log discipline

The transcript pane renders the newest `transcript_rows` entries of
`OperatorTranscript`, where `transcript_rows` comes from
`AgentLayout.transcript_rows`. Older entries fall off the front of the
ring once `TRANSCRIPT_MAX_ENTRIES` is reached.

Locked rules:

```text
The transcript is local UI state. It is never written to disk.
The transcript never enters OutputHistory / WorldletHistory / ProtoBasicHistory.
The transcript is destroyed when the wrapper exits.
The transcript is bounded: at most TRANSCRIPT_MAX_ENTRIES (64) entries are retained.
Each TranscriptEntry.text is bounded printable text (same _bound_printable policy).
Each TranscriptEntry is frozen; OperatorTranscript is frozen; appends are
  copy-on-write (return a new record).
The transcript renderer truncates rows to the transcript pane's width;
  it does not introduce wrapping or scroll commands.
There is no "scroll" interaction in this campaign; the newest entries
  are always visible. A future campaign may add page-up / page-down,
  but it is out of scope here.
```

The transcript is **not** the status pane and is **not** the error
pane. Those continue to live on `OperatorSession.status_message` and
`OperatorSession.error_message` (drives existing `I-UI-13`); the
transcript records the **sequence** of events while the status pane
shows the **latest** event.

---

## 15. Non-interactive fixture strategy

The agent layout introduces no new fixture **directories**. New
fixtures land in `brain/ui/fixtures/` alongside the existing ones and
follow the same shape:

```text
brain/ui/fixtures/agent_layout.py
    drives I-UI-16, I-UI-20, I-UI-22
    sweeps (width, height) across a deterministic grid and asserts:
      - AgentLayout.from_size returns valid layouts
      - each pane's bounds are non-overlapping and sum to (width, height)
      - the composer + footer + header panes are always present
      - the collapsed/side-by-side switch happens at MIN_SIDE_BY_SIDE_WIDTH
      - the renderer returns exactly height rows, each <= width
brain/ui/fixtures/composer_input.py
    drives I-UI-17, I-UI-18
    scripted ComposerAction sequences:
      - basic typing inserts characters at the cursor
      - backspace empties the buffer correctly
      - cursor home/end/left/right reposition without resizing the buffer
      - history prev/next walks a non-empty ring
      - clear_buffer resets buffer and history_idx
      - submit returns ComposerSubmission with the typed line and pushes history
      - non-printable INSERT_CHAR payloads are rejected as no-ops
    plus LocalCommandLine.parse table-driven assertions:
      - every approved verb maps to its Command
      - /queue with valid args builds a QueuePerceptPayload via PerceptEvent
      - /queue with COGITO_ID-colliding content_id is rejected as LocalCommandError
      - /queue with non-printable text is rejected as LocalCommandError
      - unknown verbs / missing args / args-on-no-arg verbs are LocalCommandError
brain/ui/fixtures/transcript_log.py
    drives I-UI-19
    scripted append sequences:
      - empty().append(...).append(...) returns the correct ordered tail
      - len(entries) <= TRANSCRIPT_MAX_ENTRIES after a long append run
      - each appended entry's text is bounded printable
      - append is copy-on-write (the old record is unchanged after .append)
      - tail(n) returns the newest n entries in order
      - transcript is not equal to OutputHistory / WorldletHistory / ProtoBasicHistory
        (a duck-type guard; the renderer never confuses these record types)
brain/ui/fixtures/agent_tui_smoke.py
    drives I-UI-23 (OBSERVED, non-gating)
    scripted operator-style walk:
      1. start session with the OfflineStandInClient
      2. submit "/queue beta hello-world" -> expect QUEUED transcript entry,
         queue size == 1, status_message echoes the queue summary
      3. submit "/step" -> expect STEP transcript entry, tick_counter == 1,
         active_view == "tick"
      4. submit "/state" -> expect VIEW transcript entry, active_view == "state"
      5. submit "/help" -> expect VIEW transcript entry, active_view == "help"
      6. submit "/quit" -> expect QUIT transcript entry, session.quit_flag is True
       (this fixture is OBSERVED only; it is informative, not a gate)
```

Fixture rules (the same as today):

```text
fixtures import only public UI / kernel APIs (matches existing I-UI-07)
fixtures use the OfflineStandInClient — no real LLM, no network, no shell
fixtures perform no file I/O outside the in-memory record types
fixtures perform no real curses calls (no os.system, no subprocess)
fixtures are deterministic: the same script yields the same final records
fixtures are non-interactive and can run under bash tools/check_all.sh
```

The OBSERVED row (`I-UI-23`) is non-gating; the rest are REQUIRED /
STRUCTURAL and gate the full check (mirrors the existing campaign's
pattern, where `I-UI-14` is the only OBSERVED UI row).

---

## 16. Non-goals (re-stated, binding)

The following are **explicitly out of scope** for this campaign and any
proposal that requires them must escalate rather than be folded in:

```text
real LLM chat surface in the composer
shell command execution
filesystem save / export of any kind
network I/O (sockets, HTTP, DNS, anything)
Mode B planning
Expression + ReadabilityPredictor
social/language harness
natural-language understanding of composer input
LLM-backed autocomplete or suggestions
new theory semantics (no TLICA / TOCE / Lean-bound row)
direct BrainState mutation
tick() semantics changes
scenario / trace schema changes
OutputHistory / WorldletHistory / ProtoBasicHistory writes from the UI
weakening any existing I-UI-* safety row
multi-session multiplexing
mouse handling, color attributes, true-color rendering, emoji rendering
terminal automation outside the curses UI (no tmux, screen, expect)
external dependencies
arbitrary Python execution from the composer
```

Each non-goal is enforced by an existing or planned `I-UI-*` row:

```text
I-UI-07 (REQUIRED)   import audit — no curses / kernel / LLM / shell / network
                                    imports leak into composer / parser / transcript modules
I-UI-10 (REQUIRED)   OperatorSession holds no unsafe resources
I-UI-11 (STRUCTURAL) curses wrapper imports no kernel / LLM / shell / network /
                                    file surfaces
I-UI-13 (STRUCTURAL) status / error / transcript text is bounded printable
I-UI-18 (REQUIRED, planned)  parser is finite and maps only to approved
                              OperatorCommand / QueuePerceptPayload routes
I-UI-21 (STRUCTURAL, planned) curses wrapper delegates input to composer/router
                              and does not mutate kernel state directly
```

---

## 17. Open decisions

The corrigenda (Step 3) and the catalog patch plan (Step 4) must close
the following points before implementation begins:

```text
A. Should ComposerState.status_line be a separate field or rendered
   directly from session.status_message at frame time?
   Recommendation: keep the field; the composer pane shows the most
   recent local-cmd status without depending on session state.

B. Should HISTORY_PREV / HISTORY_NEXT remap to the live curses prompt
   for /queue arguments?
   Recommendation: no. The live-input prompt remains the `n` shortcut
   only; the composer's /queue typing surface is the primary path.

C. Should /clear also clear the composer buffer?
   Recommendation: no. /clear only clears session status/error fields
   so the operator does not lose typed input. CLEAR_BUFFER (^U / ^C)
   remains the explicit composer-clear path.

D. Should transcript history persist across `python3 -m brain.ui`
   invocations?
   Recommendation: no. The transcript is process-local. Persistence
   would require filesystem writes, which is explicitly out of scope.

E. Should the existing TuiViewModel be retired now or kept until Step 10?
   Recommendation: keep both during the implementation phase. Retire
   the legacy view model only at Step 10 when the curses wrapper
   switches over.

F. Should the agent-style entrypoint share `python3 -m brain.ui` or
   register a new submodule?
   Recommendation: share `python3 -m brain.ui`. The wrapper picks the
   layout at startup; the legacy renderer remains importable for
   fixtures during the campaign and is removed at Step 10.

G. Does any new module require its own import-audit row, or does
   `I-UI-07` cover them transitively?
   Recommendation: `I-UI-07` covers `brain/ui/*.py` already; add the
   new modules' import-clean assertions to the existing fixture rather
   than a new row.
```

---

## 18. Stop conditions

Stop and escalate to the operator (do not silently fold in) if any of
the following arise during corrigenda, catalog patch planning, or
implementation:

```text
the composer requires storing a callable / file handle / socket / LLM
   client on OperatorSession (would weaken I-UI-10)
the parser requires shell expansion, subprocess, or eval/exec
the transcript requires filesystem writes or JSONL trace output
the layout requires curses calls inside the pure renderer
the agent layout requires changes to tick() semantics, trace schema,
   scenario schema, developmental-history shapes, or TLICA contracts
the catalog patch requires weakening an existing I-UI-* row
the small-terminal degraded path drops the COMPOSER or FOOTER pane
the typed command flow needs natural-language interpretation
```

---

## 19. Next artifact

The next campaign step (Step 3) produces:

```text
OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md
```

That corrigenda must check:

```text
bottom composer vs natural-language chat distinction
typed UI command parser vs shell / Proto-BASIC distinction
pane layout determinism on small terminals
transcript/log as local UI state only (no trace/scenario writes)
how typed /queue maps to existing QueuePerceptPayload
how typed /step maps to existing STEP_TICK route
whether new I-UI-* rows are needed (I-UI-16..I-UI-23 candidates)
which row statuses are REQUIRED / STRUCTURAL / OBSERVED
the open decisions enumerated in section 17 above
```

After the corrigenda, Step 4 is the catalog patch plan, Step 5 is the
review gate, and Steps 6-10 land the catalog rows and runtime code.
Step 11 runs the full gate; Step 12 records the
`OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md` verdict.

Stop condition for the campaign as a whole is in `CURRENT_CAMPAIGN.md`
Step 12: a post-completion audit verdict of PASS / PASS WITH PATCHES /
BLOCKED.
