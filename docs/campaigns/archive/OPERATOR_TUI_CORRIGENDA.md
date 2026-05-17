# OPERATOR_TUI_CORRIGENDA.md

## 1. Purpose

This corrigenda reviews `OPERATOR_TUI_SYNTHESIS.md` and
`OPERATOR_TUI_KICKOFF.md` before any catalog patch plan or runtime
implementation for the Operator TUI.

Verdict: the synthesis and kickoff are coherent. The Operator TUI is an
operator-facing inspection and input surface over the existing deterministic
kernel; it is not a new cognitive layer. None of the issues identified below
is a blocker for drafting the catalog patch plan. The future
`OPERATOR_TUI_CATALOG_PATCH_PLAN.md` should turn the tightenings in this
document into row-level mechanics rather than prose-only guidance.

This document does not apply catalog rows, create modules, add fixtures,
change `tick()` semantics, modify developmental histories, write traces or
scenarios, modify TLICA Lean reference files, add dependencies, or introduce
any host execution.

## 2. Corrigenda Summary

The Operator TUI campaign should proceed with these tightened rules:

```text
The Operator TUI is a presentation and routing surface, not a cognitive layer.
Display, rendering, and view selection never mutate kernel or developmental
  state.
The only approved runtime transition is the existing
  PerceptEvent -> tick() route.
All developmental-history inspection goes through public helper APIs on
  OutputHistory / WorldletHistory / ProtoBasicHistory.
The pure renderer is deterministic over its inputs and is fully testable
  without a real terminal.
The curses wrapper is thin over the pure renderer and command router and
  contains no kernel semantics.
The status / error pane is local UI state only; it is never trace,
  scenario, developmental, or catalog evidence.
Save / export paths remain out of scope by default and require an explicit
  reviewed policy before any filesystem mutation is added.
Phase 3.5 Expression + ReadabilityPredictor, social/language, Mode B, real
  LLM, host execution, shell, network, and arbitrary code execution remain
  non-goals.
```

## 3. UI View vs Cognitive Layer

The synthesis correctly frames the TUI as an operator tool rather than a
cognitive layer. The catalog patch plan should make this distinction
row-level rather than prose-only.

Required tightening:

```text
OperatorSession is not BrainState.
OperatorSession is not a TLICA runtime container.
OperatorSession is not a developmental history.
BrainSnapshot / DevelopmentSnapshot are read-only display views.
TuiViewModel is a display contract, not a representation of cognition.
View selection and pane navigation are UI state only.
Local UI status / error text is not trace, scenario, catalog, or
  developmental evidence.
No UI surface introduces a new self-model, action-selection layer,
  developmental promotion rule, or proof obligation by implication.
```

The semantic split is:

```text
operator console - exposes state snapshots and approved public input routes
cognitive layer  - adds new representational or developmental semantics to
                   the kernel
```

The Operator TUI belongs strictly on the operator-console side. A view of
an OutputHistory, WorldletHistory, or ProtoBasicHistory entry is display,
not promotion. The plan should reject any field, fixture, or row that would
make sense only under a "the UI thinks / decides / understands" reading.

## 4. Snapshot Read-Only Discipline

The kickoff specifies that `BrainSnapshot` / `DevelopmentSnapshot` must not
mutate live state. The catalog patch plan should bind this to enforceable
row mechanics.

Required tightening:

```text
Snapshot construction is total over the inputs allowed by its constructor.
Snapshot construction does not mutate BrainState, ScalarProfile, MSI,
  PtCns, ContentRegistry, TickRecord, OutputHistory, WorldletHistory,
  ProtoBasicHistory, trace backends, scenario files, or catalog files.
Snapshot fields are immutable display records (frozen dataclasses or
  tuples).
Mutable kernel containers are copied into tuples / frozensets / plain
  display records before they appear in a snapshot.
Exact Fraction values are rendered as strings in the snapshot's display
  fields; the UI does not introduce float arithmetic into invariant-bearing
  paths.
Snapshot construction is deterministic over the same input state.
Two snapshots taken back to back without an intervening tick render the
  same display fields.
Missing histories produce empty / "unavailable" snapshot fields rather
  than raising.
```

The plan should reject snapshot fields that expose:

```text
mutable references into BrainState internals
mutable references into developmental histories
private dataclass fields (anything whose access bypasses public helpers)
live trace-backend objects
live scenario or catalog file handles
real LLM client state
non-deterministic clock or RNG state
```

## 5. Allowed Public API Routes

The kickoff already names approved routes. The catalog patch plan should
state them as enforceable invariants over the command router.

Required tightening:

```text
Bottom-up percept route:
  OperatorCommand QUEUE_PERCEPT
  -> OperatorEventQueue stores a bounded candidate
  -> PerceptEvent public constructor validates
  -> tick(current_state, [event], client) runs
  -> new BrainState + TickRecord update OperatorSession

Inspection routes:
  OperatorCommand INSPECT_* updates only active view + UI status
  OperatorCommand HELP updates only active view + UI status
  OperatorCommand CLEAR_STATUS updates only UI status / error
  OperatorCommand QUIT sets only the local quit flag
  OperatorCommand NOOP changes nothing

Developmental-history inspection:
  Snapshot construction calls only public helper APIs on
    OutputHistory / WorldletHistory / ProtoBasicHistory.
  Snapshot construction does not access private fields, does not append,
    and does not rewrite history entries.
```

Router prohibitions to state at row level:

```text
no direct profile / MSI / PtCns / content-registry mutation
no direct OutputHistory / WorldletHistory / ProtoBasicHistory mutation
no trace / scenario / catalog writes
no private dataclass-field writes
no real LLM calls
no subprocess / shell / network / file execution
no arbitrary Python eval / exec
no tick path other than tick(state, events, client) with operator-queued
  events
```

A failed `PerceptEvent` validation or failed `tick()` is captured as local
UI status / error. It does not become trace evidence, scenario evidence,
developmental evidence, or catalog evidence.

## 6. Bottom-Up Input Representation

The synthesis describes bottom-up input in the narrow existing sense. The
catalog patch plan should make the representation explicit.

Required tightening:

```text
QUEUE_PERCEPT carries only the data needed by the PerceptEvent public
  constructor:
    content_id
    text
    ContentState flags
    initial_rho
QUEUE_PERCEPT does not carry callables, shell strings, file paths to
  execute, network endpoints, Python expressions, real LLM prompts, or
  mutable references into BrainState / developmental histories.
The queue is conservative: at most one queued candidate at a time, matching
  current tick() semantics for a single PerceptEvent step.
Queued candidates are visible in the snapshot / view model before STEP_TICK.
STEP_TICK validates the candidate via the public PerceptEvent constructor
  before calling tick().
A validation failure aborts the step and updates local UI status / error
  only.
A successful tick replaces the session's current BrainState and stores the
  resulting TickRecord; it does not also write traces or scenarios by
  default.
```

The bottom-up route is not a conversational layer:

```text
not a teacher
not a social partner
not a language harness
not an external environment
not a Mode B planning surface
```

It is a local operator route for injecting the same kind of percept that
existing public kernel APIs already accept.

## 7. Interactive Curses vs Testable Pure Renderer Split

The kickoff splits the implementation into a pure renderer plus a thin
curses wrapper. The catalog patch plan should bind this split to row
mechanics rather than informal preference.

Required tightening:

```text
Pure renderer (brain/ui/render.py-equivalent):
  accepts TuiViewModel or snapshot bundle + bounded width / height
  returns deterministic strings or display rows
  same inputs -> same outputs across runs
  no curses import
  no file / network / shell I/O
  no tick() call
  no kernel or developmental mutation
  no real LLM call
  no private dataclass-field access
  graceful rendering of missing histories

Thin curses wrapper (brain/ui/tui.py-equivalent):
  initialize / tear down curses screen
  read keypresses
  translate keys into OperatorCommand values
  paint rendered rows
  handle terminal resize by re-rendering
  exit cleanly on quit
  no kernel semantics
  no developmental semantics
  no catalog row logic
  no PerceptEvent construction rules beyond passing input to a parser
  no host execution
  no subprocess / shell / network / file execution

Entrypoint (brain/ui/__main__.py-equivalent):
  on missing or unusable terminal, fails closed with a helpful local
    message
  does not spawn alternate shells, open files, call a browser, or mutate
    the filesystem
```

A non-interactive smoke test should be possible by exercising the pure
renderer and command router without initializing curses or attaching to a
real terminal.

## 8. I-UI-* Row Status Choices

The catalog patch plan should use conservative statuses for the future
`I-UI-*` family.

Recommended REQUIRED rows:

```text
Snapshot construction is read-only with respect to BrainState, profile,
  MSI, PtCns, content registry, OutputHistory, WorldletHistory,
  ProtoBasicHistory, trace files, scenario files, and catalog files.
The pure renderer is deterministic over (view model, width, height).
OperatorCommand is a finite typed surface with no callable / shell / file
  / network payloads.
QUEUE_PERCEPT carries only data accepted by the public PerceptEvent
  constructor.
The router's STEP_TICK route calls tick(state, [event], client) and
  records the resulting TickRecord without taking any other kernel route.
Validation failures and tick failures update local UI status / error only
  and do not partially mutate kernel or developmental state.
The UI does not call real LLM, subprocess, shell, network, or file-
  execution surfaces.
Snapshot construction does not write to OutputHistory, WorldletHistory,
  ProtoBasicHistory, trace files, scenario files, or catalog files.
```

Recommended STRUCTURAL rows:

```text
BrainSnapshot / DevelopmentSnapshot are frozen / immutable display
  records.
TuiViewModel is a small, terminal-agnostic data contract.
OperatorSession holds no real LLM client, no subprocess handle, no file
  descriptor, no network socket, no shell command, and no host-execution
  callback.
The curses wrapper contains only terminal-handling code and contains no
  kernel or developmental semantics.
The brain/ui/__main__.py entrypoint fails closed with a helpful local
  message when no usable terminal is available.
Local UI status / error text is bounded printable text and is not a trace
  event, scenario entry, developmental history entry, or catalog row
  result.
The keyboard map is a finite enumeration documented in the help pane.
```

Recommended OBSERVED rows:

```text
Aggregate Operator TUI session walks can be inspected for kernel-boundary
  cleanliness (no leaked mutations, no leaked tick calls outside the
  router).
Qualitative inspection coverage of Phase 3.1-3.4 histories can be reported
  as local UI evidence.
```

Do not make qualitative OBSERVED rows REQUIRED unless they have an exact
deterministic assertion. Do not use OBSERVED rows to smuggle in runtime
promotion, expression semantics, language semantics, Mode B semantics, or
external-world claims.

The plan may also list NOT-EXERCISED placeholders for future TUI rows that
intentionally have no fixture in this campaign (for example, future
save / export rows). These should remain NOT-EXERCISED until an explicit
policy authorizes them.

## 9. Save / Export Policy

The kickoff lists "save/export paths before policy review" as a non-goal.
The corrigenda upgrades this to a hard rule for the catalog patch plan.

Required tightening:

```text
The Operator TUI does not write any file by default.
The Operator TUI does not write traces, scenarios, catalog files, or
  developmental histories.
The Operator TUI does not implement a save snapshot path in this campaign.
The Operator TUI does not implement an export view path in this campaign.
The Operator TUI does not implement a transcript / session log path in
  this campaign.
Any future save / export path requires:
  an explicit reviewed policy artifact
  catalog rows that constrain the path
  fixtures that exercise the path under bounded conditions
  a stop condition for failure modes
```

If a future step adds save / export, that step is responsible for ensuring
the path does not become a covert channel for trace, scenario,
developmental, or catalog mutation. Until then, the entire campaign treats
the filesystem as read-only with respect to outputs.

## 10. Trace / Scenario Write Prohibition by Default

The Operator TUI may display existing trace and scenario information that
is already exposed via public APIs, but it must not write traces or
scenarios in this campaign.

Required tightening:

```text
No TUI command writes traces/first_scenario_real.jsonl.
No TUI command writes traces/RUN_SUMMARY.md.
No TUI command writes any file under traces/.
No TUI command writes any file under scenarios/.
No TUI command writes any file under brain/tlica/.
No TUI command writes any file under brain/llm/.
No TUI command modifies catalog files (INVARIANT_CATALOG.md,
  tools/catalog.py, brain/_catalog_ids.py, brain/invariants.py) outside an
  explicit catalog-patch step authorized by the campaign.
No TUI command appends to OutputHistory, WorldletHistory, or
  ProtoBasicHistory directly; the only path to those histories is via
  their existing public helper APIs invoked through tick() and the
  developmental modules.
```

Local UI status / error text remains local. It does not become a trace
event or scenario entry by being displayed.

## 11. Phase 3.5 / Social / Language / Mode B Leakage

The synthesis and kickoff already list these as non-goals. The corrigenda
affirms they remain non-goals and adds row-level guards.

The catalog patch plan should reject any UI field, fixture, or row that
implies:

```text
Phase 3.5 Expression + ReadabilityPredictor
social register
language harness
natural-language teacher or corrector
listener / audience modeling
Mode B reflective planning
free-will branch tracking via UI
prompt-tuning to force scenario outcomes
seeded-MSI shortcuts via UI
runtime promotion from UI display state
automatic learning from UI status / error text
```

The Operator TUI may display Phase 3.1-3.4 history summaries because those
summaries are local developmental evidence already covered by their own
catalog rows. Displaying that evidence is not promoting it. A row whose
only coherent reading is "the UI talked / decided / understood" should be
rejected and deferred to a later cognitive campaign.

## 12. Public-API Boundary

Reaffirm and tighten the public-API boundary:

```text
PerceptEvent and tick() remain the only routes that change kernel state.
OutputHistory / WorldletHistory / ProtoBasicHistory remain owned by their
  developmental modules.
The TUI imports from brain.io_types, brain.tick (or an equivalent public
  entrypoint), and the public helper APIs on the developmental history
  modules.
The TUI does not import private modules under brain/tlica/ for state
  mutation, does not import brain/llm/ to inject real LLM clients, and
  does not import brain/tick.py to alter its semantics.
The TUI does not extend brain/io_types with new public types in this
  campaign except for UI-local dataclasses placed under brain/ui/.
```

The import audit (`tools/import_audit`) should remain green after the
implementation steps. If any UI module would require an import that
crosses these lines, that requirement is a stop condition for the
campaign, not a license to relax the boundary.

## 13. Determinism and Exactness

The TUI should preserve the project-wide determinism and exactness rules.

Required tightening:

```text
No UI module introduces float arithmetic into invariant-bearing paths.
Fraction values from the kernel are rendered as exact strings for display.
Snapshot construction is deterministic over the input state.
The pure renderer is deterministic over (snapshot, view, width, height).
The keyboard map is fixed at build time for a given UI version.
OperatorCommand is a closed enumeration; the router rejects unknown
  commands with a local UI status update.
```

Determinism is the main defense against the UI silently becoming a
non-deterministic input to the kernel.

## 14. Catalog Patch Plan Requirements

The next artifact, `OPERATOR_TUI_CATALOG_PATCH_PLAN.md`, should turn this
corrigenda into exact row mechanics:

```text
I-UI-* row IDs
statuses (REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED as appropriate)
owning modules (brain/ui/ submodules)
fixture files (brain/ui/fixtures/ submodules)
count impact from current v0.9 to projected next version
fixture roster
module map
catalog patch mechanics
implementation order
open decisions
stop conditions for the review gate
validation commands
```

The plan should not apply the patch. It should be coherent enough that
Step 5's review gate can decide whether implementation is unblocked.

## 15. Final Decision

No blocker prevents drafting the catalog patch plan.

Proceed to:

```text
OPERATOR_TUI_CATALOG_PATCH_PLAN.md
```

The next step should remain planning-only and should not touch runtime
modules, fixtures, catalog rows, generated IDs, `tick()`, `brain/llm/`,
`brain/tlica/`, `lean_reference/`, `scenarios/`, `traces/`, or LLM
behavior.
