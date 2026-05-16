# PHASE3_8_OPERATOR_STREAM_INTERACTION_CORRIGENDA.md

## Purpose

Audit `PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md` before the
catalog patch plan. This is a planning artifact only. It does not edit
the catalog, runtime modules, fixtures, README, traces, scenarios, or
guarded kernel paths.

Verdict for Step 21:

```text
COHERENT - PROCEED TO CATALOG PATCH PLAN
```

## 1. Baseline

```text
Catalog version:  v0.14
REQUIRED:         158
STRUCTURAL:        56
NOT-EXERCISED:      7
DEFERRED:          12
OBSERVED:          10
Latest audit:     PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md
Audit verdict:    PASS
Current phase:    Phase 3.8 Operator Stream Interaction
```

Accepted prior artifacts:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_SYNTHESIS.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md
```

## 2. Finite Command Parser

Kickoff proposal:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
```

Corrigendum:

```text
ACCEPTED WITH ROW COVERAGE REQUIRED
```

The current `LocalCommandLine` parser is a finite verb parser. Phase 3.8
may extend that closed verb set, but it must not add a second free-form
command channel. The catalog patch plan must require:

```text
unknown stream verbs return local parser errors
malformed stream command forms return local parser errors
stream verbs map only to typed OperatorCommand values
stream payloads are frozen typed records
parser code performs no shell expansion, subprocess call, network I/O,
  filesystem mutation, eval, exec, compile, import hook, JSON parser,
  YAML parser, TOML parser, or arbitrary expression evaluation
```

Decision:

```text
The kickoff's parser shape is coherent.
```

## 3. Bounded Input Length

Kickoff proposal:

```text
/stream text bound: reuse STREAM_TEXT_MAX_LEN
/stream-promote candidate_id bound: reuse STREAM_PROVENANCE_MAX_LEN
parser error bound: keep LOCAL_CMD_MAX_ERROR_LEN
session status bound: keep MAX_STATUS_TEXT_LEN
promotion candidate view bound: reuse STREAM_PROMOTION_MAX
```

Corrigendum:

```text
ACCEPTED WITH EXPLICIT CONSTANT PARITY CHECK
```

The plan should prefer importing Phase 3.7 constants from
`brain.development.text_stream` where that does not violate static UI
audit boundaries. If a UI module duplicates a text-stream bound, the
fixture roster must include a parity check so drift cannot silently
weaken the Phase 3.7 contract.

Required locked bounds for the plan:

```text
stream text max length: STREAM_TEXT_MAX_LEN = 1024
candidate id / provenance max length: STREAM_PROVENANCE_MAX_LEN = 64
promotion candidate display cap: STREAM_PROMOTION_MAX = 64
parser error max length: LOCAL_CMD_MAX_ERROR_LEN = 240
status/error max length: MAX_STATUS_TEXT_LEN = 240
```

Decision:

```text
The kickoff's bounded-input discipline is coherent, but the catalog
plan must pin exact constants.
```

## 4. Stream Command Does Not Tick

Kickoff proposal:

```text
/stream appends to TextStreamHistory only
/stream-summary is read-only
/stream-candidates is read-only
/stream-promote queues only
/step remains the only tick route
```

Corrigendum:

```text
ACCEPTED AS HARD BOUNDARY
```

The Step 22 row family must include both behavioral and static coverage:

```text
/stream does not call tick()
/stream-summary does not call tick()
/stream-candidates does not call tick()
/stream-promote does not call tick()
only OperatorCommand.STEP_TICK reaches OperatorSession._dispatch_step
tick_counter and latest_tick remain unchanged after stream commands
BrainState identity and kernel containers remain unchanged after stream
  commands
```

Decision:

```text
No stream command may be a runtime transition route.
```

## 5. Promotion Command Only Queues

Kickoff proposal:

```text
StreamPromotionCandidate
  -> /stream-promote <candidate_id>
  -> QueuePerceptPayload
  -> OperatorEventQueue.enqueue(...)
  -> /step
  -> PerceptEvent
  -> tick(...)
```

Corrigendum:

```text
ACCEPTED WITH ONE-WAY BRIDGE RULE
```

`/stream-promote` may bridge one explicit
`StreamPromotionCandidate` into one queued `QueuePerceptPayload`.
It must not:

```text
construct PerceptEvent directly outside QueuePerceptPayload validation
append to OperatorEventQueue._items directly
call tick()
dequeue anything
mutate TextStreamHistory
mutate BrainState, MSI, PtCns, ContentRegistry, source histories,
  traces, or scenarios
invent target_content_id or text from a second parser path
```

The candidate ID lookup must be exact. Unknown or stale IDs are local
status/errors only.

Decision:

```text
The kickoff's promotion route is coherent if the queue-only bridge is
tested directly.
```

## 6. Failure Isolation

Kickoff proposal:

```text
invalid input becomes local UI status only
event_queue full surfaces as local error only
unknown candidate_id surfaces as local error only
```

Corrigendum:

```text
ACCEPTED
```

The plan must require fixtures for:

```text
malformed /stream
over-bound /stream text
unknown /stream-promote candidate_id
event queue full during /stream-promote
constructor rejection during candidate-to-payload conversion
```

Every failure path must leave these unchanged:

```text
BrainState
latest_tick
tick_counter
TextStreamHistory, unless the failing command is rejected before append
OperatorEventQueue length, unless the command succeeds
source developmental histories
```

Decision:

```text
Failure isolation remains local UI status/error only.
```

## 7. Session Resource-Free Property

Kickoff proposal:

```text
TextStreamHistory lives on OperatorSession or a small session-owned
StreamInteractionState.
```

Corrigendum:

```text
ACCEPTED WITH RESOURCE AUDIT UPDATE REQUIRED
```

If `OperatorSession` gains new fields, `_ALLOWED_SESSION_ATTRS` and the
resource-free fixture must be updated in the same implementation step.
Allowed stream-session state:

```text
TextStreamHistory
tuple[StreamPromotionCandidate, ...]
frozen StreamInteractionState containing only bounded immutable stream
  records
```

Forbidden session state:

```text
LLM client
subprocess handle
file descriptor
socket
path object used for save/export
shell command string intended for execution
callback
mutable external history reference beyond the session-owned stream
  state
```

Decision:

```text
The session-local design is coherent, but the catalog plan must require
the resource audit to cover every new session field.
```

## 8. Read-Only Render Path

Kickoff proposal:

```text
add stream-specific immutable snapshots
render stream views from view-model data
renderer remains deterministic and side-effect-free
```

Corrigendum:

```text
ACCEPTED
```

The catalog plan must require:

```text
stream summary snapshots are frozen
stream candidate snapshots are frozen
snapshot construction does not mutate TextStreamHistory or candidate
  records
exact Fraction values render as strings
rendering stream views is deterministic for equal view models
rendering stream views performs no file, network, shell, subprocess,
  curses, tick, TLICA, or LLM operation
```

Decision:

```text
The kickoff's render route is coherent.
```

## 9. Language, Truth, Social, And Agency Boundaries

Corrigendum:

```text
RESTATE AS HARD NON-GOALS
```

Phase 3.8 stream commands must not introduce:

```text
language parsing
semantic understanding
truth scoring
readability scoring
social modeling
speaker / conversation / dialogue state
natural-language teacher or corrector
agency witness
Mode B planning
self-modification
real host execution
```

`/stream-summary` and `/stream-candidates` are structural displays over
local text-stream records only.

Decision:

```text
No Phase 3.8 row may imply language, truth, social success, or agency.
```

## 10. Phase 3.8b Separation

Kickoff proposal:

```text
Do not add --llm-mode, client factories, Anthropic/API clients, Claude
CLI clients, or model-backed smoke checks in Phase 3.8 command work.
```

Corrigendum:

```text
ACCEPTED AS REQUIRED AMENDMENT BOUNDARY
```

`PHASE3_8B_LLM_TOGGLE_AMENDMENT.md` remains mandatory context, but it
belongs after stream command implementation and before the final Phase
3.8 audit. Phase 3.8 stream-command fixtures must remain deterministic.

Decision:

```text
The catalog patch plan must explicitly defer model-backed mode selection
to Steps 24A-24G.
```

## 11. Catalog Patch Plan Requirements

Step 22 must bind the above rulings to:

```text
row family name
row statuses
count delta
exact file budget
fixture roster
pending-registration mechanics
accepted constants
review-gate stop condition
```

Likely row family:

```text
I-UI-STRM-*
```

Required row themes:

```text
finite stream command parser
bounded stream payload records
/stream appends local TextStreamHistory only
/stream-summary is read-only
/stream-candidates is read-only
/stream-promote queues exactly one candidate and does not tick
only /step calls tick
stream session state is resource-free and local
stream snapshots are immutable and read-only
stream rendering is deterministic and side-effect-free
failure paths are local status/error only
no language/truth/social/agency/Mode B/model-backed behavior
OBSERVED scripted stream interaction walk
NOT-EXERCISED save/export placeholder remains unimplemented
```

## 12. Stop Rule

After Step 22, stop at the review gate:

```text
Do not apply catalog rows.
Do not edit runtime modules.
Do not add fixtures.
Do not update README command docs as if implementation exists.
Do not proceed to Step 23 until the plan is accepted.
```

## Conclusion

The Phase 3.8 kickoff is coherent. The next artifact is:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_CATALOG_PATCH_PLAN.md
```

That plan must be committed and pushed, then the campaign must stop at
the Step 22 review gate.
