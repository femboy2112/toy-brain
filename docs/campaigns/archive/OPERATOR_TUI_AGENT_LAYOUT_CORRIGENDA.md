# OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md

Step 3 corrigenda for the Operator TUI Agent-Style Layout campaign
(`CURRENT_CAMPAIGN.md`). This document closes the open decisions
enumerated in section 17 of `OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md`,
restates each campaign boundary that the kickoff's planning surface
touches, and locks the contracts that Step 4 (catalog patch plan) will
turn into row text.

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
Kickoff (Step 2): present (commit 97cb503)
Full gate (bash tools/check_all.sh): green (170 rows checked)
Entrypoint: python3 -m brain.ui
```

---

## 1. Purpose

The synthesis (Step 1) established the UX deficit, and the kickoff
(Step 2) locked the concrete contracts (`AgentLayout`, `PaneSpec`,
`PaneRenderResult`, `BottomComposer`, `ComposerState`,
`ComposerAction`, `LocalCommandLine`, `OperatorTranscript`,
`TranscriptEntry`, `AgentTuiViewModel`, responsive pane sizing, typed
command flow, keyboard flow, scrollback / log discipline,
non-interactive fixture strategy). The kickoff explicitly listed seven
open decisions (A–G in section 17) and seven "stop and escalate"
conditions in section 18.

This corrigenda does three things:

```text
1. Resolves the seven open decisions (A–G) with binding rulings the
   Step 4 catalog patch plan will quote verbatim.
2. Re-checks every campaign boundary the kickoff touches against the
   guardrails in CURRENT_CAMPAIGN.md and the existing I-UI-* rows,
   and records the result of each check.
3. Locks the I-UI-* row family for Step 4 (proposed IDs, statuses,
   and mappings to kickoff contracts) so the catalog patch plan does
   not have to re-derive them.
```

Every contract below is engineering-hypothesis material. None of it
modifies the kernel, the trace seam, developmental histories,
scenarios, or the Lean reference. All checks resolve to "consistent
with the kickoff" or "tighten the kickoff" — no resolution **loosens**
a kickoff contract or weakens an existing `I-UI-*` row.

---

## 2. Bottom composer vs natural-language chat distinction

The bottom composer is a typed local UI command line. The kickoff
already states this in sections 5 and 8, and the synthesis restates it
in section 3 ("It is a local UI command line, not a chat surface").
This corrigenda re-checks the distinction against every campaign
guardrail and records the result.

Check 2.1 — does the composer accept free-form natural language?

```text
Kickoff section 8 grammar: line = optional_whitespace, "/", verb, ...
A line without a leading "/" is rejected as LocalCommandError("expected
leading '/'"). The grammar has no production for "natural language"
input. The parser performs no LLM call, no fuzzy match, no
autocomplete, and no suggestion list.
Result: PASS. Composer cannot be coerced into a chat surface by input
content.
```

Check 2.2 — can the composer reach a real LLM?

```text
The composer hands a ComposerSubmission.line to LocalCommandLine.parse.
The parser returns either a Command (closed enumeration of UI commands)
or a LocalCommandError. Neither path constructs an LLMClient, calls
client.evaluate, or imports brain.llm.
The STEP_TICK Command continues to be dispatched by
OperatorSession.dispatch(client=...), and the client is the existing
OfflineStandInClient owned by the curses wrapper. The composer never
sees the client object.
Result: PASS. Composer is upstream of dispatch; no LLM path.
```

Check 2.3 — does the rendered surface look like a chat window?

```text
The composer pane shows two rows: an editor row "> <buffer>_" with a
cursor marker, and a meta row "mode=local-cmd  cursor=N  history=M".
The "mode=local-cmd" tag and the prompt prefix "> " (not, e.g., "agent:"
or "you:") are deliberate. The footer is a one-row key-hint strip
("keys: enter submit  ^c clear  ^p prev  ^n next  /help full keymap"),
not a chat header. The transcript renders TranscriptKind tags
(SUBMIT/QUEUED/STEP/ERROR/VIEW/QUIT), not "user" / "agent" labels.
Result: PASS. The rendered surface signals "local command line", not
"chat with an agent".
```

Check 2.4 — does the composer participate in any cognitive layer?

```text
Composer state lives on the curses wrapper's local stack and on the
AgentTuiViewModel for rendering only. It is never read by tick(),
PtCns.eval, OutputHistory, WorldletHistory, ProtoBasicHistory, the
trace seam, or any scenario writer. It is destroyed when the wrapper
exits.
Result: PASS. Composer is local UI state only.
```

Ruling: the composer is a typed local UI command line. The Step 4
catalog patch plan uses this language; the implementation steps must
not relax it. If a future user request requires natural-language input
in the composer, that is a new campaign (likely Phase 3.5 territory),
not an in-flight amendment.

---

## 3. Typed UI command parser vs shell / Proto-BASIC distinction

The parser must be a finite grammar over the approved verbs. It must
not behave like a shell, a Python REPL, or a Proto-BASIC editor.

Check 3.1 — is the grammar finite?

```text
Kickoff section 8 enumerates exactly ten verbs:
  help, state, tick, output, worldlet, repl,
  queue, step, clear, quit.
Each non-queue verb takes zero arguments; /queue takes exactly two
positional arguments (content_id and the remainder of the line as
text). The tokenizer is str.split(None, 1) applied to the post-"/"
body, so the parser produces at most two tokens.
Result: PASS. Grammar is a closed enumeration.
```

Check 3.2 — does the parser expand or interpret arguments?

```text
The parser performs no shell expansion ($VAR, command substitution,
globbing, brace expansion), no JSON/YAML/TOML parsing, no eval, no
exec, no compile, no os.system, no subprocess, no socket, no urllib,
no http, no requests. The /queue text payload is passed unchanged to
PerceptEvent's constructor through QueuePerceptPayload.
Result: PASS. Arguments are inert tokens until PerceptEvent's
constructor validates them.
```

Check 3.3 — could /repl be mistaken for a Python REPL?

```text
/repl maps to Command(INSPECT_REPL). INSPECT_REPL switches the active
view to the Proto-BASIC developmental history inspector
(brain.development.repl). It does not execute Python, does not parse
Proto-BASIC, and does not append to ProtoBasicHistory. The renderer
shows the existing history; the operator cannot edit it from the
composer.
The /help command (Step 4 catalog patch plan + Step 10 README update)
documents this distinction in a one-line description. The corrigenda
records the distinction here so it is captured before implementation.
Result: PASS. /repl is an inspector view, not a REPL.
```

Check 3.4 — can the parser reach the host?

```text
brain/ui/command_line.py (planned module) imports only:
  - typing helpers
  - brain.ui.commands (OperatorCommand enum, Command record,
    QueuePerceptPayload, make_command)
  - brain.ui.constants for PROMPT_DEFAULT_CONTENT_STATE /
    PROMPT_DEFAULT_RHO (or wherever those constants live today)
It does not import curses, brain.tick, brain.tlica, brain.llm,
brain.trace, os, subprocess, socket, urllib, http, requests, json,
yaml, ast, code, codeop. The existing I-UI-07 import-audit fixture
extends to cover the new module (kickoff section 16 + open decision G,
ruled below).
Result: PASS subject to I-UI-07 fixture extension at Step 6 and Step 8.
```

Ruling: the parser is finite, inert, and contains no shell, REPL, or
Proto-BASIC surface. Step 4 row I-UI-18 (REQUIRED, planned) carries
this assertion; Step 8 lands the runtime.

---

## 4. Pane layout determinism on small terminals

The kickoff's section 11 specifies the derivation of `AgentLayout`
from `(width, height)` and the explicit small-terminal collapse path.
This corrigenda walks the derivation for the four boundary geometries
the catalog patch plan will name in fixture inputs and confirms the
result.

Boundary cases:

```text
Case A: width=20 (MIN_WIDTH), height=6 (MIN_HEIGHT)
  STEP_A: HEADER row=0, height=1, width=20
  STEP_B: FOOTER row=5, height=1, width=20
  STEP_C: COMPOSER row=3, height=2, width=20
  STEP_D: body_top=1, body_bottom=3, body_rows=2
          body_rows < 1 + MIN_TRANSCRIPT_ROWS (= 3)
          -> transcript_rows=0, inspector_rows=2
  STEP_E: width 20 < MIN_SIDE_BY_SIDE_WIDTH (37) -> collapsed=True
          state_rows = 2 // 2 = 1
          inspector_rows2 = 2 - 1 = 1
          STATE: row=1, col=0, height=1, width=20
          INSPECTOR: row=2, col=0, height=1, width=20
  STEP_F: transcript omitted (transcript_rows==0)
  Sum of pane heights: 1 + 1 + 1 + 2 + 1 = 6 == height. PASS.
  COMPOSER present, FOOTER present, HEADER present. PASS.

Case B: width=37 (MIN_SIDE_BY_SIDE_WIDTH), height=10
  STEP_A: HEADER row=0, height=1, width=37
  STEP_B: FOOTER row=9, height=1, width=37
  STEP_C: COMPOSER row=7, height=2, width=37
  STEP_D: body_top=1, body_bottom=7, body_rows=6
          body_rows >= 1 + MIN_TRANSCRIPT_ROWS (= 3)
          transcript_rows = max(2, 6 // 3) = 2
          inspector_rows = 6 - 2 = 4
  STEP_E: width 37 >= MIN_SIDE_BY_SIDE_WIDTH (37) -> collapsed=False
          left_width = 37 // 2 = 18 (== MIN_PANE_WIDTH)
          right_width = 37 - 18 = 19
          STATE: row=1, col=0, height=4, width=18
          INSPECTOR: row=1, col=18, height=4, width=19
  STEP_F: TRANSCRIPT: row=5, col=0, height=2, width=37
  Sum of pane heights: 1 + 4 + 2 + 2 + 1 = 10 == height. PASS.
  STATE and INSPECTOR are 18 + 19 = 37 cols (full width). PASS.
  Note: when state and inspector are side-by-side they occupy the same
  rows (1..4). Their column extents are disjoint and contiguous
  (state: cols 0..17, inspector: cols 18..36), so the layout invariant
  "no overlap between panes (row-major + column-major addressing is
  unique)" still holds: each (row, col) cell belongs to exactly one
  pane.

Case C: width=80, height=24 (default)
  STEP_A: HEADER row=0, height=1, width=80
  STEP_B: FOOTER row=23, height=1, width=80
  STEP_C: COMPOSER row=21, height=2, width=80
  STEP_D: body_top=1, body_bottom=21, body_rows=20
          transcript_rows = max(2, 20 // 3) = 6
          inspector_rows = 14
  STEP_E: collapsed=False, left_width=40, right_width=40
          STATE: row=1, col=0, height=14, width=40
          INSPECTOR: row=1, col=40, height=14, width=40
  STEP_F: TRANSCRIPT: row=15, col=0, height=6, width=80
  Sum of pane heights: 1 + 14 + 6 + 2 + 1 = 24 == height. PASS.

Case D: width=200, height=60 (large terminal)
  body_rows = 56, transcript_rows = max(2, 56 // 3) = 18,
  inspector_rows = 38, left_width = 100, right_width = 100.
  Sum: 1 + 38 + 18 + 2 + 1 = 60. PASS.
```

The deterministic rule "given (width, height) >= (MIN_WIDTH,
MIN_HEIGHT), `AgentLayout.from_size` returns a layout where
HEADER + COMPOSER + FOOTER always exist, panes do not overlap, and
pane heights sum to height" is a Step 4 catalog row (I-UI-22
STRUCTURAL).

Check 4.1 — does the composer ever vanish on a valid small terminal?

```text
Case A above (20x6) keeps the COMPOSER at row 3 (height 2). The
collapse branch reduces transcript_rows to 0 and reduces inspector
rows to 1 row each, but the COMPOSER pane is constructed before the
body region is divided. The composer is fed from STEP_C, which runs
before STEP_D and STEP_E. STEP_D and STEP_E only divide the body
between body_top (=1) and body_bottom (=height-3).
Result: PASS. COMPOSER is present on every (width, height) >= (20, 6).
```

Check 4.2 — could the body collapse make inspector_rows zero?

```text
At (MIN_WIDTH, MIN_HEIGHT) = (20, 6), body_rows = 6 - 3 - 1 = 2 and
inspector_rows = 2 (transcript_rows=0). At MIN_HEIGHT exactly, the
collapsed branch splits inspector_rows into state_rows = 1 and
inspector_rows2 = 1.
At MIN_HEIGHT - 1 the existing render contract already raises
ValueError, so AgentLayout.from_size raises the same ValueError. The
collapse branch never observes inspector_rows == 0.
Result: PASS. STATE and INSPECTOR each have at least 1 row at the
floor.
```

Check 4.3 — is the geometry a pure function?

```text
AgentLayout.from_size(width, height) reads no global state, no
environment variable, no terminal, no curses, no clock. It uses only
integer arithmetic over (width, height) and module-level constants
(MIN_WIDTH, MIN_HEIGHT, MIN_PANE_WIDTH, MIN_SIDE_BY_SIDE_WIDTH,
MIN_TRANSCRIPT_ROWS).
Result: PASS. Step 4 row I-UI-20 (STRUCTURAL) asserts AgentLayout /
PaneSpec / TuiViewModel are terminal-agnostic immutable contracts.
```

Ruling: the small-terminal contract holds. The Step 4 fixture for
I-UI-16 / I-UI-20 / I-UI-22 (`brain/ui/fixtures/agent_layout.py`)
sweeps (width, height) over a deterministic grid that includes the
four boundary cases above plus a corner sweep over
(MIN_WIDTH..MIN_WIDTH+4) and (MIN_HEIGHT..MIN_HEIGHT+4).

---

## 5. Transcript / log as local UI state only

The transcript must never leave local memory. The kickoff section 9
states this; this corrigenda re-checks the boundary against the
guardrails.

Check 5.1 — does OperatorTranscript hold unsafe resources?

```text
Fields: entries (tuple of TranscriptEntry), limit (int).
TranscriptEntry fields: kind (TranscriptKind enum),
                        tick_at_event (int),
                        text (str, bounded printable).
No callable. No file handle. No socket. No LLM client. No path object.
No threading primitive. No subprocess handle.
Result: PASS. OperatorTranscript and TranscriptEntry are POD-shaped.
```

Check 5.2 — is the transcript ever serialized?

```text
The transcript is rendered into bounded printable rows by the
transcript pane renderer (PaneRenderResult). Those rows are passed to
the curses wrapper's paint_rows (existing surface). They are not
written to disk, not appended to a JSONL trace, not appended to
OutputHistory / WorldletHistory / ProtoBasicHistory, not sent over the
network, and not exported through any save/export route. The
campaign's NOT-EXERCISED save/export row (I-UI-15) remains
NOT-EXERCISED.
Result: PASS. Transcript is render-only.
```

Check 5.3 — could a /queue or /step cause the transcript to enter a
developmental history?

```text
TranscriptEntry append is triggered by the curses wrapper after
session.dispatch returns. The TranscriptEntry is constructed from the
session's status_message (which is already bounded printable text under
I-UI-13). The developmental histories are appended only by tick() (via
brain.output, brain.worldlet, brain.development.repl, etc.), which
operates on PerceptEvent / TickRecord, not on session.status_message.
The transcript and the histories share no field.
Result: PASS. Transcript is structurally disjoint from any
developmental history.
```

Check 5.4 — bound discipline.

```text
The kickoff locks TRANSCRIPT_MAX_ENTRIES = 64 and
MAX_COMPOSER_BUFFER = MAX_STATUS_TEXT_LEN (= 240). The append
operation is copy-on-write: when len(entries) >= limit, drop the
oldest entry, then append. The fixture (transcript_log.py) asserts
the bound holds after a long append run.
Result: PASS. Step 4 row I-UI-19 (REQUIRED) carries the bound.
```

Ruling: the transcript is local UI state only, with no path to a
trace, scenario, or developmental history. Step 4 row I-UI-19
(REQUIRED) is the catalog assertion.

---

## 6. No trace / scenario writes

This is an audit-level re-statement. The campaign authorizes no new
trace seams, scenario files, or fixture-driven file writes.

Check 6.1 — composer / parser / transcript modules.

```text
brain/ui/composer.py: imports typing helpers and brain.ui.constants.
                     No filesystem call. No trace seam. No scenario.
brain/ui/command_line.py: imports typing helpers and brain.ui.commands.
                          No filesystem call. No trace seam. No scenario.
brain/ui/transcript.py: imports typing helpers and brain.ui.constants.
                        No filesystem call. No trace seam. No scenario.
brain/ui/layout.py: imports typing helpers and brain.ui.render constants.
                    No filesystem call. No trace seam. No scenario.
```

Check 6.2 — the existing safety rows that protect this boundary.

```text
I-UI-07 (REQUIRED) import audit — no curses / kernel / LLM / shell /
                    network imports leak. Extended at Step 6 (fixture
                    update) to cover the four new modules.
I-UI-10 (REQUIRED) OperatorSession holds no unsafe resources.
                    OperatorTranscript and ComposerState do not live
                    on OperatorSession (kickoff section 9 + section 6),
                    so I-UI-10 is unaffected.
I-UI-11 (STRUCTURAL) curses wrapper imports no kernel / LLM / shell /
                    network / file surfaces. The wrapper update at
                    Step 10 adds composer / parser / transcript /
                    layout imports, all of which are local UI modules
                    by Check 6.1 above.
I-UI-13 (STRUCTURAL) status / error text is bounded printable. Extends
                    to transcript text by construction (TranscriptEntry
                    uses the same _bound_printable policy).
I-UI-15 (NOT-EXERCISED) save/export route — remains NOT-EXERCISED.
                    The transcript is not a save/export surface.
```

Ruling: no new trace seam, scenario file, or fixture-driven file write
is authorized or required. The Step 4 catalog patch plan must restate
I-UI-15 as NOT-EXERCISED and explicitly say "unchanged" for
I-UI-07/10/11/13.

---

## 7. How typed /queue maps to existing QueuePerceptPayload

The synthesis section 5 and the kickoff section 8 both specify this
mapping. This corrigenda traces the path step-by-step to confirm the
public PerceptEvent constructor is the only validation point.

Trace:

```text
1. Operator types: "/queue beta hello-world"
2. ComposerAction.SUBMIT fires. ComposerSubmission.line == "/queue beta
   hello-world".
3. LocalCommandLine.parse("/queue beta hello-world"):
   a. strips leading/trailing whitespace
   b. removes the leading "/"
   c. body = "queue beta hello-world"
   d. tokens = body.split(None, 1) -> ["queue", "beta hello-world"]
   e. verb = "queue"
   f. args_remainder = "beta hello-world"
   g. content_id, text = args_remainder.split(None, 1)
                          -> ("beta", "hello-world")
   h. parser returns:
        make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="beta",
            text="hello-world",
            content_state=PROMPT_DEFAULT_CONTENT_STATE,
            initial_rho=PROMPT_DEFAULT_RHO,
        )
      which calls QueuePerceptPayload(...) which calls
      PerceptEvent(...) for validation, exactly as the existing
      curses prompt does today.
4. Wrapper calls session.dispatch(command, client=client).
5. session.dispatch routes QUEUE_PERCEPT to the existing
   queue_percept handler, which appends the validated PerceptEvent
   to OperatorSession.event_queue.
6. Wrapper reads session.status_message ("queued percept 'beta' (queue
   size = 1)") and appends a TranscriptEntry(QUEUED, tick, summary).
```

Rejection paths (recorded in the parser, not introduced by the parser):

```text
Empty content_id or non-printable content_id:
  -> tokens = body.split(None, 1) only returns the verb -> parser raises
     LocalCommandError("/queue requires <content_id> <text>")
  -> never reaches PerceptEvent.
COGITO_ID-colliding content_id:
  -> parser does NOT pre-check (responsibility belongs to PerceptEvent).
  -> PerceptEvent(content_id=COGITO_ID, ...) raises ValueError.
  -> parser catches the ValueError and returns
     LocalCommandError("/queue rejected: <ValueError message>").
Out-of-range rho (would only happen if a future verb supplied rho):
  -> in this campaign /queue uses PROMPT_DEFAULT_RHO. No operator-supplied
     rho path. Future campaigns may add a rho field, but they would
     extend the parser by addition, not amendment.
Non-printable text:
  -> PerceptEvent's text field is bounded printable. PerceptEvent raises
     ValueError. Parser catches and returns LocalCommandError.
```

Check 7.1 — single validation point.

```text
PerceptEvent's constructor is the only validation step that runs
between operator input and OperatorSession.event_queue. The parser
performs cheap syntactic checks (presence of two tokens) but never
reimplements PerceptEvent's domain checks.
Result: PASS. The parser delegates all semantic validation to
PerceptEvent.
```

Check 7.2 — no direct event_queue mutation.

```text
The parser never imports OperatorSession. The parser never appends to
OperatorSession.event_queue. The only path that reaches event_queue
is OperatorSession.dispatch(Command(QUEUE_PERCEPT, payload)).
Result: PASS. Kernel boundary preserved (drives existing I-UI-04,
I-UI-06).
```

Ruling: the typed /queue path is the existing QUEUE_PERCEPT route with
a different UI surface in front. Step 4 row I-UI-18 (REQUIRED) asserts
the parser maps only to approved routes; the existing I-UI-04 and
I-UI-06 continue to assert the routing.

---

## 8. How typed /step maps to existing STEP_TICK route

Trace:

```text
1. Operator types: "/step"
2. ComposerSubmission.line == "/step"
3. LocalCommandLine.parse("/step") -> Command(OperatorCommand.STEP_TICK)
4. Wrapper calls session.dispatch(command, client=client) where client
   is the OfflineStandInClient held on the wrapper's local stack
   (matching today's wrapper).
5. session.dispatch routes STEP_TICK to session.step_tick(client).
6. session.step_tick(client) calls tick(current_state,
                                          [queued_event],
                                          client)
   exactly as today. The TickRecord and the new BrainState are
   captured on the session through the existing public hooks.
7. Wrapper reads session.status_message and appends
   TranscriptEntry(STEP, tick, summary).
```

Check 8.1 — does the typed path differ from the keystroke path?

```text
Today's path: space keystroke -> Command(STEP_TICK) -> session.dispatch
              -> session.step_tick(client) -> tick(...)
Typed path  : "/step" submission -> Command(STEP_TICK) -> session.dispatch
              -> session.step_tick(client) -> tick(...)
The two paths produce the same Command record. session.dispatch sees no
new code path. tick() sees no new arguments. The OperatorSession's
local fields (current_state, latest_tick, tick_counter,
event_queue, status_message, error_message) move through the same
transitions.
Result: PASS. Step 4 row I-UI-18 records this; Step 4 also restates
existing I-UI-05 (REQUIRED) as unchanged (STEP_TICK route through
public tick() only).
```

Check 8.2 — the LLM client surface.

```text
The wrapper keeps the LLMClient on its local stack and passes it to
session.dispatch via the client= keyword. The composer does not store
the client. The parser does not see the client. The transcript does
not store the client. I-UI-10 (REQUIRED) is unaffected.
Result: PASS.
```

Ruling: the typed /step path is identical to the existing keystroke
path at every layer below the wrapper. The Step 4 catalog patch plan
restates I-UI-05 as unchanged.

---

## 9. New I-UI-* row family for Step 4

The kickoff section 16 named eight candidate rows (I-UI-16..I-UI-23).
This corrigenda confirms the mapping from rows to kickoff contracts
and locks the statuses for Step 4 to quote.

Row table (proposed for catalog v0.11):

```text
ID         Status      Drives / Contract
---------- ----------- ------------------------------------------------
I-UI-16    REQUIRED    AgentLayout exposes persistent named panes plus
                       bottom composer. (kickoff section 2, 11)
                       Owning module: brain/ui/layout.py
                       Fixture: brain/ui/fixtures/agent_layout.py

I-UI-17    REQUIRED    BottomComposer edit model supports type /
                       backspace / enter / history deterministically.
                       (kickoff section 5-7)
                       Owning module: brain/ui/composer.py
                       Fixture: brain/ui/fixtures/composer_input.py

I-UI-18    REQUIRED    LocalCommandLine parser is finite, typed, and
                       maps only to approved OperatorCommand /
                       QueuePerceptPayload routes. (kickoff section 8,
                       this corrigenda section 7-8)
                       Owning module: brain/ui/command_line.py
                       Fixture: brain/ui/fixtures/composer_input.py

I-UI-19    REQUIRED    OperatorTranscript records UI events
                       copy-on-write and remains local UI state only.
                       (kickoff section 9, this corrigenda section 5)
                       Owning module: brain/ui/transcript.py
                       Fixture: brain/ui/fixtures/transcript_log.py

I-UI-20    STRUCTURAL  AgentLayout / PaneSpec / AgentTuiViewModel are
                       terminal-agnostic immutable contracts. (kickoff
                       sections 2, 3, 10)
                       Owning module: brain/ui/layout.py +
                                      brain/ui/render.py
                       Fixture: brain/ui/fixtures/agent_layout.py

I-UI-21    STRUCTURAL  Curses wrapper delegates input to composer /
                       router and does not mutate kernel state
                       directly. (kickoff section 12-13)
                       Owning module: brain/ui/tui.py
                       Fixture: brain/ui/fixtures/agent_tui_smoke.py
                       (plus continued reliance on I-UI-11)

I-UI-22    STRUCTURAL  Responsive pane geometry is deterministic and
                       preserves a visible bottom composer on small
                       terminals. (kickoff section 11, this corrigenda
                       section 4)
                       Owning module: brain/ui/layout.py
                       Fixture: brain/ui/fixtures/agent_layout.py

I-UI-23    OBSERVED    Scripted agent-style interaction walk is
                       inspectable and non-gating. (kickoff section 15)
                       Owning module: brain/ui/tui.py +
                                      brain/ui/session.py
                       Fixture: brain/ui/fixtures/agent_tui_smoke.py
```

Status rationale (per row):

```text
I-UI-16 REQUIRED — the layout is the campaign's primary structural
        promise. Without persistent panes plus composer the campaign
        has not shipped. Fixture asserts pane presence and ordering.

I-UI-17 REQUIRED — the composer is the campaign's primary ergonomic
        promise. The fixture exercises every ComposerAction including
        edge cases (empty submit, history wrap, non-printable
        INSERT_CHAR rejection).

I-UI-18 REQUIRED — the parser is the safety surface. Anything the
        operator types is constrained by this row. Fixture is
        table-driven over the verb enumeration.

I-UI-19 REQUIRED — bounding the transcript is the only thing that
        keeps the UI from leaking memory or violating I-UI-13. The
        row asserts both the bound and the copy-on-write contract.

I-UI-20 STRUCTURAL — the contracts are enforced at construction time
        (frozen dataclasses + __post_init__ checks). No per-tick
        assertion is needed beyond the fixtures driving the rows that
        depend on them (I-UI-16 and I-UI-22).

I-UI-21 STRUCTURAL — the wrapper-delegation property is a structural
        invariant of the codebase (the wrapper has no kernel imports,
        composer/parser handle input). I-UI-11 already covers the
        import audit; I-UI-21 captures the delegation pattern itself
        and is exercised by the OBSERVED smoke walk plus the wrapper's
        construction-time delegation table.

I-UI-22 STRUCTURAL — derives from I-UI-16's fixture sweep. The
        geometry is a pure function of (width, height); the fixture
        sweeps a deterministic grid and asserts the small-terminal
        preservation property. STRUCTURAL because it is a property of
        the AgentLayout constructor, not a runtime tick-time check.

I-UI-23 OBSERVED — like I-UI-14 today, this is an inspectable walk
        that helps operators verify the agent surface end-to-end
        without being a correctness gate. It runs under the full gate
        but does not fail the runner.
```

Projected catalog impact (from v0.10):

```text
REQUIRED       123 -> 127   (+4: I-UI-16, I-UI-17, I-UI-18, I-UI-19)
STRUCTURAL      41 -> 44    (+3: I-UI-20, I-UI-21, I-UI-22)
NOT-EXERCISED    4 -> 4     (+0)
DEFERRED        12 -> 12    (+0)
OBSERVED         6 ->  7    (+1: I-UI-23)
Total rows     186 -> 194
```

This matches the kickoff section 16 projection and the campaign's
Step 4 recommended-row table. Step 4 must restate the table verbatim;
this corrigenda is the canonical mapping.

Existing I-UI-* rows (must be restated as **unchanged** in Step 4):

```text
I-UI-01  REQUIRED    snapshot_view  unchanged
I-UI-02  REQUIRED    render_view    unchanged
I-UI-03  REQUIRED    command_router unchanged
I-UI-04  REQUIRED    command_router unchanged
I-UI-05  REQUIRED    command_router unchanged
I-UI-06  REQUIRED    command_router unchanged
I-UI-07  REQUIRED    tui_smoke      unchanged (fixture extended at
                                    Step 6 to cover new modules)
I-UI-08  STRUCTURAL  snapshot_view  unchanged
I-UI-09  STRUCTURAL  render_view    unchanged
I-UI-10  REQUIRED    command_router unchanged
I-UI-11  STRUCTURAL  tui_smoke      unchanged
I-UI-12  STRUCTURAL  tui_smoke      unchanged
I-UI-13  STRUCTURAL  command_router unchanged
I-UI-14  OBSERVED    tui_smoke      unchanged
I-UI-15  NOT-EX'D    (none)         unchanged
```

The corrigenda explicitly affirms: no existing I-UI-* row is weakened,
amended, or retired. The campaign extends; it does not modify in
place.

---

## 10. Open decisions A–G — binding rulings

The kickoff section 17 enumerated seven open decisions. Each is ruled
below. The Step 4 catalog patch plan must adopt these rulings without
further negotiation; any deviation is a stop condition under kickoff
section 18.

### A. ComposerState.status_line field

Kickoff recommendation: keep the field.

Ruling: **keep the field**. The composer pane shows the most recent
local-cmd status without re-reading `session.status_message` mid-frame.
This decouples the composer's meta row from the session's status pane
and lets the composer surface parse-time messages (for example, "empty
composer submission") that never reach `session.set_error` because they
are not session-level errors.

Implementation note for Step 8:

```text
ComposerState.status_line is set ONLY by:
  - the SUBMIT action when buffer.strip() == "" (sets "empty composer
    submission" and returns the unchanged buffer);
  - the wrapper, after a successful parse, by writing session.status_message
    into the next ComposerState via apply(state.with_status(...)).
The composer pane renderer reads ComposerState.status_line for the meta
row's third field when session.status_message is empty; otherwise it
prefers session.status_message. The "prefer session" precedence keeps
the existing I-UI-13 status-pane semantics intact.
```

Rationale: the field is bounded printable text (kickoff section 6),
costs one tuple slot, and prevents the parser from reaching across
into `OperatorSession.set_status`/`set_error` for parser-internal
messages. No safety row is weakened.

### B. HISTORY_PREV / HISTORY_NEXT and the live curses /queue prompt

Kickoff recommendation: no.

Ruling: **no**. HISTORY_PREV / HISTORY_NEXT walk the composer's own
submission ring. The live curses percept prompt (opened by the `n`
key, from the live-input patch) is a separate, single-shot bounded
prompt that does not share history with the composer.

Rationale:

```text
1. The live curses prompt is a two-field dialog over (content_id, text)
   with bounded-printable inputs. It has no notion of "previous
   submission".
2. Sharing history would require the prompt to read the composer's
   ring (cross-module coupling) and would invite the operator to
   recall a "/queue beta hello" line into the prompt's content_id
   field, which would fail validation.
3. The composer is the primary surface for /queue (this corrigenda
   section 7). The `n` key remains as a wrapper concession for users
   who prefer the dialog; new fixtures cover the composer path, not
   the dialog path.
```

Implementation note: the wrapper continues to map `n` to the existing
percept-prompt factory wired in commit c4b8c07. No history field is
threaded into the prompt.

### C. Should /clear also clear the composer buffer?

Kickoff recommendation: no.

Ruling: **no**. `/clear` maps to `Command(CLEAR_STATUS)` and clears
only the session's status/error fields. The composer buffer survives
across `/clear` so the operator does not lose typed input by clearing
status.

The explicit composer-clear path is `CLEAR_BUFFER` (ComposerAction)
which is bound to `^U` and `^C` (kickoff section 13). The operator who
wants to clear both submits `/clear` and then types `^U` (or vice
versa).

Implementation note for Step 8:

```text
Verb dispatch table (Step 8):
  /clear -> Command(OperatorCommand.CLEAR_STATUS)
  ^U / ^C (when composer has focus) -> ComposerAction.CLEAR_BUFFER

These are independent. /clear never returns a ComposerSubmission with
an empty buffer; it returns a parsed Command, and the wrapper adopts
the new ComposerState (with buffer="", because SUBMIT always returns
buffer="") only because Enter was pressed.

Note: SUBMIT does clear the buffer by design — that is the existing
ComposerState transition for SUBMIT (kickoff section 7). After SUBMIT,
the wrapper passes "/clear" to the parser, gets Command(CLEAR_STATUS),
and dispatches it. The buffer is empty after SUBMIT, which is
consistent with "buffer survives /clear" because /clear only operates
on session fields; the empty buffer is a side effect of pressing Enter.
```

Documentation note: /help must explicitly say "/clear clears status,
^U clears the composer".

### D. Transcript persistence across `python3 -m brain.ui` invocations

Kickoff recommendation: no.

Ruling: **no**. The transcript is process-local and dies with the
curses wrapper.

Rationale:

```text
1. Persistence requires filesystem writes, which kickoff section 16
   explicitly excludes.
2. Persistence would invite confusion with the trace seam (which is a
   kernel-level surface, not a UI surface).
3. Persistence would invite cross-session "agent memory" semantics that
   are out of scope for the campaign (and would smell like Phase 3.5
   without going through Phase 3.5).
4. The OperatorSession itself is also process-local under the existing
   I-UI-10 row; transcript persistence would create an asymmetry.
```

Implementation note: no read/write of `~/.brain_tui_history` or
similar. The transcript is built fresh in every wrapper startup
(`OperatorTranscript.empty()`).

### E. Retire the existing TuiViewModel now or at Step 10?

Kickoff recommendation: keep both during the implementation phase.
Retire at Step 10.

Ruling: **keep both through Step 9; retire at Step 10**. The legacy
`TuiViewModel` remains importable for the duration of Steps 6–9 so
existing fixtures (`brain/ui/fixtures/render_view.py`,
`brain/ui/fixtures/snapshot_view.py`, etc.) do not have to be rewritten
in lock-step with the new layout module.

Retirement protocol at Step 10:

```text
1. Move existing TuiViewModel fixtures that test render() with the
   legacy view model onto AgentTuiViewModel (a thin adapter is
   acceptable in fixtures).
2. Remove the legacy TuiViewModel record from brain/ui/render.py.
3. The renderer's public signature becomes
   render(view: AgentTuiViewModel) -> tuple[str, ...].
4. The "active_view" / "queue_summary" / "status_message" /
   "error_message" / "keyboard_help" / "width" / "height" fields
   continue to exist on AgentTuiViewModel (kickoff section 10), so
   nothing observable to the renderer changes.
```

This keeps Steps 6–9 from triggering a wrapper-wide refactor and
isolates the wrapper-only switch to Step 10.

### F. Should the agent-style entrypoint share `python3 -m brain.ui`?

Kickoff recommendation: yes, share.

Ruling: **share `python3 -m brain.ui`**. The wrapper picks the layout
at startup. The campaign does not register a new submodule
(no `python3 -m brain.ui.agent` or similar).

Rationale:

```text
1. The campaign is a UX upgrade, not a parallel UI. Two entrypoints
   would force users to remember which is "the new one".
2. The legacy renderer remains importable during Steps 6-9 (open
   decision E), but the wrapper switches to the agent layout at
   Step 10. After Step 10, the only callable surface is the
   layout-aware path.
3. README is updated at Step 10 to document the new interface in
   place; no separate "agent UI" section is added.
```

Implementation note: `brain/ui/__main__.py` remains the single entry
file. Its `--check-terminal` / `--print-once` flags continue to work,
with `--print-once` switching to render an `AgentTuiViewModel` of the
default operator view at Step 10.

### G. Does any new module require its own import-audit row, or does
       I-UI-07 cover them transitively?

Kickoff recommendation: I-UI-07 covers `brain/ui/*.py`; extend the
existing fixture.

Ruling: **I-UI-07 covers the new modules**; the fixture is extended.
No new import-audit row is added.

Rationale:

```text
1. I-UI-07's owning module is brain.ui.tui (the curses wrapper) and
   its fixture is brain/ui/fixtures/tui_smoke.py. The fixture walks
   the brain/ui package's modules and asserts the import allowlist.
2. Adding a per-module row would inflate the catalog without adding
   coverage; the existing audit is already package-scoped.
3. The fixture extension at Step 6 / Step 8 adds the four new modules
   (layout.py, composer.py, command_line.py, transcript.py) to the
   audited set. The audit allowlist remains:
       typing-only imports
       brain.ui.commands (where the closed enumeration lives)
       brain.ui.constants (where the bounds live)
       brain.ui.render constants (MIN_WIDTH / MIN_HEIGHT)
       brain.io_types.PerceptEvent (for QueuePerceptPayload construction)
   No new module imports curses, kernel, LLM, shell, network, or file
   surfaces.
4. The pending registration list at Step 6 lists fixture-extension
   work for I-UI-07 alongside the new I-UI-16..I-UI-23 registrations.
```

Implementation note for Step 6 / Step 8: when the fixture's audited
module list expands, the catalog row's "Fixture" cell stays
"tui_smoke.py" because that is the fixture that drives the audit.

---

## 11. Stop conditions (re-stated, binding)

The kickoff section 18 listed stop conditions. The corrigenda
re-affirms each and adds one corrigenda-specific stop condition.

Carried from the kickoff:

```text
- composer requires storing a callable / file handle / socket / LLM
  client on OperatorSession (would weaken I-UI-10)
- parser requires shell expansion, subprocess, or eval / exec
- transcript requires filesystem writes or JSONL trace output
- layout requires curses calls inside the pure renderer
- agent layout requires changes to tick() semantics, trace schema,
  scenario schema, developmental-history shapes, or TLICA contracts
- catalog patch requires weakening an existing I-UI-* row
- small-terminal degraded path drops the COMPOSER or FOOTER pane
- typed command flow needs natural-language interpretation
```

Added by this corrigenda:

```text
- any open decision A-G is re-opened mid-implementation without an
  explicit operator instruction (Steps 6-12 must follow the rulings
  in section 10 above).
```

If any stop condition trips, the active agent stops and reports rather
than folding the change in. Step 5 (review gate) is the natural
checkpoint to surface a stop-condition concern before any code is
written.

---

## 12. Validation footprint

This corrigenda is text-only. Validation is:

```text
git diff --name-only           -> OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md
python3 -m tools.catalog counts -> 123/41/4/12/6 (unchanged)
```

The catalog rows are added at Step 6, not now. The fixtures are added
at Steps 7-10. The wrapper switch happens at Step 10. The full gate is
re-run at Step 11. The post-completion audit lands at Step 12.

---

## 13. Next artifact

The next campaign step (Step 4) produces:

```text
OPERATOR_TUI_AGENT_LAYOUT_CATALOG_PATCH_PLAN.md
```

That document must:

```text
1. Quote the row table from section 9 above verbatim.
2. Quote the open-decision rulings from section 10 above verbatim.
3. Specify the catalog patch mechanics (banner update, count update,
   tools.catalog generate-ids invocation order, brain/_catalog_ids.py
   regeneration, pending-registration list).
4. Name the strict implementation order:
     Step 6  apply catalog patch (rows added; pending registrations
             open).
     Step 7  layout module + renderer upgrade (drives I-UI-16, I-UI-20,
             I-UI-22).
     Step 8  composer + command-line parser (drives I-UI-17, I-UI-18).
     Step 9  transcript + session integration (drives I-UI-19).
     Step 10 wrapper switch + README sync (drives I-UI-21, I-UI-23,
             retires legacy TuiViewModel).
5. Restate the stop conditions verbatim (section 11 above).
6. Restate the unchanged rows (section 9 above, "existing I-UI-* rows"
   block).
```

After the catalog patch plan, Step 5 is the review gate; only after
that gate does Step 6 land catalog rows. The campaign's overall stop
condition (Step 12 audit verdict of PASS / PASS WITH PATCHES /
BLOCKED) is unchanged.
