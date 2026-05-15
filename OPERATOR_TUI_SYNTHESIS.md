# OPERATOR_TUI_SYNTHESIS.md

## 1. Purpose

The Operator TUI campaign defines a terminal interface for inspecting and
stepping the existing `toy-brain` kernel and developmental histories.

This document is a synthesis artifact only. It does not authorize catalog
patches, runtime modules, fixture additions, a curses implementation, save or
export behavior, Phase 3.5 Expression + ReadabilityPredictor, social/language
behavior, Mode B, real LLM calls, host execution, shell execution, network I/O,
or arbitrary code execution.

Core thesis:

```text
The Operator TUI is an operator-facing inspection and input surface over the
existing deterministic kernel. It lets a human inspect state, queue bounded
bottom-up PerceptEvent inputs, and step tick() through public APIs. It is not a
new cognitive layer, not reflective agency, and not a runtime shortcut.
```

The inherited Phase 3 bridge principle remains in force:

```text
PRESERVE should be earned, not labeled.
```

The TUI extends that principle to interaction. An operator may present a
bottom-up percept and observe the resulting state transition, but the UI must
not label content as preserved, mutate profile/MSI/PtCns directly, bypass
`tick()`, or reinterpret display state as evidence of a new cognitive phase.

## 2. v0.9 Saved-State Summary

The inherited saved state is catalog v0.9 after the Phase 3.4 Proto-BASIC REPL
campaign:

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

The full gate is green. The Phase 3.4 audit reports PASS, `I-REPL-*` rows are
registered and green, `I-REPL-18` is OBSERVED only, Proto-BASIC history remains
local evidence, and the kernel boundary remains clean: no Proto-BASIC operation
emits `PerceptEvent`, calls `tick()`, mutates TLICA runtime state, writes
scenario or trace files, or invokes host execution.

The next cognitive campaign remains deferred:

```text
Phase 3.5 - Expression + ReadabilityPredictor
```

The Operator TUI may inspect the saved state and the Phase 3.1-3.4 histories.
It must not reinterpret those histories as language, reflective agency,
external reality, Mode B planning, or automatic runtime promotion.

## 3. Why a TUI Is an Operator Tool

The TUI is a presentation and routing layer for a human operator. Its job is to
make the current kernel easier to inspect and step, not to add new semantics to
the kernel.

The distinction is:

```text
operator tool      - exposes state snapshots and public input routes
cognitive layer    - adds new representational or developmental semantics
```

The Operator TUI belongs on the operator-tool side. It may render
`BrainState`, `TickRecord`, and developmental history summaries. It may keep
local UI status such as the active view, queued input text, validation errors,
and help text. It may route a validated bottom-up input through the existing
`PerceptEvent -> tick()` path.

It must not add a new self-model, a new action-selection surface, new
developmental promotion rules, or a new proof obligation by implication. Any
new invariant rows for the UI should describe UI discipline: snapshots are
read-only, rendering is deterministic, command routing uses approved public
APIs, and the curses wrapper stays thin over testable pure modules.

## 4. Bottom-Up Interaction Thesis

The TUI should support bottom-up interaction in the narrow existing sense:

```text
operator input -> validated PerceptEvent -> tick() -> BrainState + TickRecord
```

The operator is outside the kernel. The UI may let the operator create a
bounded `PerceptEvent` candidate by supplying a content ID, printable text,
content-state flags, and an initial rho value. After validation, the only
approved path into runtime state is `tick()`.

Bottom-up interaction is therefore not a conversational layer. It is not a
teacher, not a social partner, not a language harness, and not an external
environment. It is a local operator route for injecting the same kind of
percept that existing public kernel APIs already accept.

The UI should make this route auditable:

```text
queued event visible before step
validation failures shown as local UI status
tick result displayed as state snapshot plus TickRecord
mode/action/classification displays derived from existing records
no hidden mutation between queue and step
```

## 5. State-Inspection Requirements

The TUI should make inspection dense, deterministic, and read-only. Expected
inspection surfaces:

```text
BrainState snapshot
profile domain and rho values
MSI contents and threshold
PtCns eval partition
content registry entries
latest TickRecord
mode trace and triggered mode
boundary contents
developmental OutputHistory summary
developmental WorldletHistory summary
developmental ProtoBasicHistory summary
local UI status and errors
```

Snapshots should be serializable or string-renderable without exposing mutable
internal objects. A display refresh must not change `BrainState`,
`TickRecord`, profile, MSI, PtCns, content registry, output history, worldlet
history, Proto-BASIC history, scenario files, trace files, catalog files, or
private dataclass fields.

The renderer should be pure enough to test without a terminal. Given the same
snapshot and view selection, it should return the same view model or string
output. The curses layer should only translate terminal input and paint the
already-rendered view.

## 6. Allowed Input Routes

Allowed routes for the campaign:

```text
inspect current snapshot
switch views / panes
queue a bounded PerceptEvent candidate
validate queued input using public constructors
step exactly through tick()
view the resulting TickRecord
view existing OutputHistory / WorldletHistory / ProtoBasicHistory summaries
clear local UI errors
show help / keyboard map
quit the UI
```

The approved state-transition route is:

```text
OperatorCommand -> OperatorEventQueue -> PerceptEvent -> tick()
```

Any developmental-history inspection should use public history records and
helper functions. The UI may hold references to local histories for display,
but it should not write into those histories unless a later accepted plan
explicitly adds such a route with catalog coverage.

## 7. Forbidden Mutation Routes

The TUI must not directly mutate:

```text
BrainState
ScalarProfile
MSI
PtCns
ContentRegistry
OutputHistory
WorldletHistory
ProtoBasicHistory
catalog rows
scenario files
trace files
private dataclass fields
```

The TUI must not bypass:

```text
PerceptEvent validation
tick()
SafeTracer boundaries
catalog/registry coverage
public developmental helper APIs
```

The TUI must not invoke:

```text
real LLM calls
subprocesses
shell commands
network I/O
host execution
arbitrary Python eval / exec
file-system mutation outside explicit user-approved save/export paths
```

The UI may display a local status message when a command is invalid. That
status message is UI state only. It is not an invariant row result, a trace
event, a scenario entry, a developmental-history record, or a TLICA runtime
state change.

## 8. Non-Goals

This campaign must not implement or smuggle in:

```text
Phase 3.5 Expression + ReadabilityPredictor
social/language harness
natural-language teacher or corrector
Mode B reflective planning
real LLM behavior
real host execution
open-ended process execution
shell execution
network I/O
arbitrary code execution
scenario generation or mutation
trace-file writes by default
catalog edits before an accepted catalog patch
direct TLICA runtime mutation
new output/worldlet/repl semantics
automatic promotion from UI display state
```

The TUI should be useful precisely because it is boring: a deterministic
operator console that displays current state and routes explicit bottom-up
inputs through already-approved public APIs.

## 9. Risks

Main risks:

- Treating an operator view as a new cognitive layer.
- Letting display refresh mutate state.
- Letting queued input bypass `PerceptEvent` validation.
- Letting a command router write directly into `BrainState` internals.
- Treating UI status or error text as trace, scenario, or developmental
  evidence.
- Adding save/export paths before the policy is reviewed.
- Making the curses wrapper too stateful to test without a terminal.
- Pulling in non-standard dependencies for a simple terminal surface.
- Accidentally invoking real LLM, shell, network, file, or host-execution
  behavior.
- Using Phase 3.1-3.4 histories to imply language, external reality,
  reflective agency, or Mode B.

The safe rule is to keep the UI split into read-only snapshots, pure rendering,
finite typed commands, an approved router, and a thin terminal wrapper.

## 10. Next Artifact

The next artifact is:

```text
OPERATOR_TUI_KICKOFF.md
```

That kickoff should lock only the Step 2 planning surface:

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
