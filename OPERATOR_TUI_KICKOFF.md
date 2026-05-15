# OPERATOR_TUI_KICKOFF.md

## 1. Purpose

This kickoff defines the Operator TUI planning surface for `toy-brain`.

It is a planning artifact only. It does not apply catalog rows, create runtime
modules, add fixtures, modify `tick()` semantics, change developmental
histories, write traces or scenarios, add dependencies, or authorize host
execution.

Implementation target:

```text
OperatorSession
BrainSnapshot / StateSnapshot
DevelopmentSnapshot
TuiViewModel
pure renderer
thin curses wrapper
OperatorCommand
OperatorEventQueue
approved command router
bottom-up PerceptEvent injection through tick()
read-only inspection of OutputHistory / WorldletHistory / ProtoBasicHistory
keyboard map
status/error pane
```

Core rule:

```text
The Operator TUI is an operator console over existing public APIs. It may
inspect state and route validated bottom-up PerceptEvent inputs through tick().
It must not become a cognitive layer, a runtime mutation shortcut, a language
harness, a Mode B surface, or a host-execution interface.
```

## 2. Inherited Baseline

The inherited saved state is catalog v0.9:

```text
116 REQUIRED
35 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
5 OBSERVED
```

Completed developmental layers:

```text
Phase 3.1 - Osmotic Chamber
Phase 3.2 - Output Ladder
Phase 3.3 - Minimal Worldlet
Phase 3.4 - Proto-BASIC REPL
```

The Phase 3.4 audit reports PASS. The full gate is green. Proto-BASIC remains
local developmental evidence: it does not emit `PerceptEvent`, call `tick()`,
mutate TLICA runtime state, write scenario or trace files, invoke host
execution, or claim language / agency / Mode B behavior.

The Operator TUI inherits that boundary. It may display Phase 3.1-3.4 data,
but display is not promotion. A view of an output, worldlet, or Proto-BASIC
history entry is not language, external reality, reflective agency, or a new
runtime state.

## 3. OperatorSession

`OperatorSession` is the local object that holds the current operator-console
state. It is not a cognitive state object and not a replacement for
`BrainState`.

It may hold:

```text
current BrainState
latest TickRecord | None
local OutputHistory | None
local WorldletHistory | None
local ProtoBasicHistory | None
queued OperatorEventQueue
current view selection
local status/error pane state
quit flag
```

It should not hold:

```text
mutable profile/MSI/PtCns internals
private dataclass-field handles
real LLM client state
non-deterministic tick clients
subprocess handles
file descriptors
network sockets
shell commands
host-execution callbacks
```

Session updates should be copy-oriented and explicit. A command router may
return a new `OperatorSession` or a clearly defined updated session record, but
the only approved runtime kernel state transition is the existing
`tick(state, events, client)` call.

## 4. BrainSnapshot / StateSnapshot

`BrainSnapshot` or `StateSnapshot` is the read-only display representation of
the current kernel state.

It should capture only serializable or string-renderable values:

```text
profile domain
profile rho values as exact strings
MSI contents
MSI threshold as an exact string
PtCns eval partition
content registry entries
boundary contents
latest tick index
latest mode trace
latest triggered mode
latest TickRecord notes
```

Snapshot construction must not mutate:

```text
BrainState
ScalarProfile
MSI
PtCns
ContentRegistry
TickRecord
trace backends
scenario files
catalog files
```

The snapshot layer should not expose mutable containers from the live runtime.
Maps, sets, and sequences should be copied into tuples or plain display
records. Exact `Fraction` values should be rendered as strings for display;
the UI must not introduce raw float arithmetic into invariant-bearing paths.

## 5. DevelopmentSnapshot

`DevelopmentSnapshot` is the read-only display representation of local
developmental histories.

It may summarize:

```text
OutputHistory impulse / echo / pattern / token counts
WorldletHistory latest state, attempt count, response count, local reasons
ProtoBasicHistory parse / command / execution / feedback counts
ProtoBasicHistory emit counts by canonical command form
OBSERVED row summaries when already available from public helper APIs
```

It must not append to or rewrite:

```text
OutputHistory
WorldletHistory
ProtoBasicHistory
trace files
scenario files
catalog files
```

Missing histories should render as empty or unavailable panes, not as errors
that imply a broken kernel state. Inspection is optional and read-only.

## 6. TuiViewModel

`TuiViewModel` is the pure renderer's input/output boundary. It should be
small, deterministic, and terminal-agnostic.

Expected data:

```text
active view
state snapshot
development snapshot
queued event summary
latest status message
latest error message
keyboard help rows
pane title rows
body lines
```

For the same snapshots, selected view, width, and height, rendering should
produce the same view model or strings. The pure renderer should not read the
terminal, call curses, perform I/O, call `tick()`, invoke LLM behavior, mutate
session state, or inspect private dataclass fields.

## 7. Pure Renderer

The pure renderer is the testable display engine. It should accept a
`TuiViewModel` or snapshot bundle and return deterministic strings or display
rows.

It should support panes for:

```text
core state
latest tick
output history
worldlet history
Proto-BASIC history
queued event
status / errors
help
```

Renderer behavior:

```text
deterministic over input data
bounded line lengths from supplied width
graceful handling of missing histories
no curses dependency
no file/network/shell I/O
no runtime mutation
no real LLM calls
```

The renderer should not make semantic claims. It displays values already
present in snapshots or records.

## 8. Thin Curses Wrapper

The curses wrapper is an adapter around the pure renderer and command router.
It should do only terminal work:

```text
initialize curses screen
read keypresses
translate keys into OperatorCommand values
paint rendered rows
handle terminal resize by re-rendering
exit cleanly on quit
```

It should not contain kernel semantics, developmental semantics, catalog row
logic, direct state mutation, `PerceptEvent` construction rules beyond routing
input to the command parser, or any host-execution behavior.

If launched without a usable terminal, the entrypoint should fail closed with a
helpful local message. It should not attempt to run alternate shells, spawn
external programs, open files, call a browser, or mutate the filesystem.

## 9. OperatorCommand

`OperatorCommand` is the finite typed command surface for the UI.

Initial command families:

```text
INSPECT_STATE
INSPECT_TICK
INSPECT_OUTPUT
INSPECT_WORLDLET
INSPECT_REPL
QUEUE_PERCEPT
STEP_TICK
CLEAR_STATUS
HELP
QUIT
NOOP
```

Command payloads should be bounded and explicit. `QUEUE_PERCEPT` may carry
only the data needed to construct a `PerceptEvent` through the public
constructor:

```text
content_id
text
ContentState flags
initial_rho
```

Invalid command payloads should update local UI status/error state only. They
must not partially mutate the kernel, developmental histories, trace files, or
scenario files.

## 10. OperatorEventQueue

`OperatorEventQueue` stores bottom-up event candidates before a tick step.

Because v1 `tick()` semantics accept at most one `PerceptEvent`, the initial
queue should be conservative:

```text
zero or one queued PerceptEvent candidate
candidate validation before step
visible queued-event summary
explicit clear / replace behavior
```

The queue should store operator-provided data or a constructed `PerceptEvent`.
It should not store arbitrary callables, host commands, file paths to execute,
network endpoints, Python expressions, or mutable references into `BrainState`.

## 11. Approved Command Router

The router is the only place where commands change the operator session.

Approved routes:

```text
inspect command -> update active view only
queue command -> validate and store a bounded PerceptEvent candidate
step command -> call tick(current_state, [queued_event], client)
help command -> update active view/status only
clear command -> clear local status/error only
quit command -> set local quit flag
```

The bottom-up state transition must be:

```text
OperatorCommand
-> OperatorEventQueue
-> PerceptEvent public constructor
-> tick(current_state, [event], client)
-> new BrainState + TickRecord
-> updated OperatorSession
```

Router prohibitions:

```text
no direct profile/MSI/PtCns mutation
no content-registry mutation outside tick()
no developmental-history mutation by UI command
no trace/scenario/catalog writes
no private dataclass-field writes
no real LLM calls
deterministic injected tick clients only for future tests
no subprocess/shell/network/file execution
no arbitrary Python eval / exec
```

A failed validation or failed tick should be captured as local UI status/error
unless the caller explicitly chooses to abort the application. Failure display
does not become trace evidence, scenario evidence, or developmental evidence.

## 12. Keyboard Map

The keyboard map should be finite and documented in the UI help pane.

Initial map:

```text
1 - inspect core state
2 - inspect latest tick
3 - inspect output history
4 - inspect worldlet history
5 - inspect Proto-BASIC history
q - quit
h or ? - help
c - clear status/error
n - queue new bottom-up percept
s - step one tick with queued percept
```

The map is operator convenience only. Keypresses become `OperatorCommand`
values. They do not directly call kernel functions or mutate state.

## 13. Status / Error Pane

The status/error pane is local UI state. It may show:

```text
last command accepted
queued event summary
validation error
tick error
missing history notice
help text
terminal capability notice
```

It must not be treated as:

```text
trace output
scenario output
developmental history
catalog validation
PtCns evaluation
ModeOp dispatch
language feedback
```

Status text should be bounded and printable. It should not contain hidden
control commands, shell snippets to execute, or file/network side effects.

## 14. Non-Goals

This kickoff does not authorize:

```text
Phase 3.5 Expression + ReadabilityPredictor
social/language harness
natural-language teacher or corrector
Mode B reflective planning
real LLM calls
real host execution
open-ended process execution
shell execution
network I/O
arbitrary Python execution
scenario generation or mutation
trace-file writes by default
catalog edits before an accepted catalog patch
direct TLICA runtime mutation
new output/worldlet/repl semantics
save/export paths before policy review
non-standard dependencies
```

The Operator TUI should remain a small terminal adapter over public kernel and
developmental APIs.

## 15. Implementation Order

After corrigenda and catalog patch planning, the safe implementation order is:

1. Draft corrigenda for view-vs-cognitive-layer, read-only snapshots, approved
   public API routes, bottom-up input representation, curses/test split, row
   status choices, save/export policy, and trace/scenario write policy.
2. Draft the catalog patch plan with exact `I-UI-*` rows, statuses, owning
   modules, fixtures, count impact, and stop conditions.
3. After acceptance, apply catalog rows and pending registry coverage only.
4. Implement read-only snapshots and pure renderer.
5. Implement command types, event queue, and router through `tick()`.
6. Implement the thin curses wrapper and `python3 -m brain.ui` entrypoint.
7. Run targeted UI rows from the accepted plan.
8. Run the full gate.
9. Draft the post-completion audit.

This kickoff does not apply catalog rows or start implementation.

## 16. Next Artifact

The next artifact is:

```text
OPERATOR_TUI_CORRIGENDA.md
```

That corrigenda should check:

```text
UI view vs cognitive layer
snapshot read-only discipline
allowed public API routes
bottom-up input representation
interactive curses vs testable pure renderer split
I-UI-* row status choices
save/export policy
trace/scenario write prohibition by default
```
