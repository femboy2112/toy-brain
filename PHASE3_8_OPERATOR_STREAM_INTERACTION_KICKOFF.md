# PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md

## Purpose

Define the Phase 3.8 Operator Stream Interaction build shape before any
catalog or runtime change. This is a planning artifact only. It does not
edit `INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, or any `brain/ui/` module.

Phase 3.8 connects the accepted Phase 3.7 text-stream substrate to the
existing operator-facing typed command line:

```text
operator typed command
  -> finite parser
  -> OperatorSession router
  -> local TextStreamHistory and read-only stream views
  -> explicit /stream-promote queues one candidate
  -> /step remains the only tick() route
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
Prior artifact:   PHASE3_8_OPERATOR_STREAM_INTERACTION_SYNTHESIS.md
```

Existing surfaces to preserve:

```text
LocalCommandLine       finite typed command parser
OperatorCommand        closed command enumeration
QueuePerceptPayload    public PerceptEvent-constructor-bounded payload
OperatorSession        resource-free command router
OperatorEventQueue     bounded queue of future tick candidates
BrainSnapshot          read-only kernel display projection
DevelopmentSnapshot    read-only developmental display projection
TuiViewModel           terminal-agnostic renderer input
render(...)            pure deterministic renderer
```

Existing Phase 3.7 surfaces to consume:

```text
TextStreamSource
TextStreamChunk
TextStreamHistory
StreamFeatureVector
SegmentCandidate
StreamPattern
StreamPromotionCandidate
```

## 2. Proposed Operator Commands

Candidate typed verbs:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
```

Command meanings:

```text
/stream <text>
  Parse bounded raw text, construct a TextStreamChunk with
  TextStreamSource.OPERATOR, and append it to session-local
  TextStreamHistory. This command does not construct a PerceptEvent,
  does not enqueue an event, and does not call tick().

/stream-summary
  Select a read-only stream summary view. It may compute or display
  StreamFeatureVector-derived counts over TextStreamHistory, but it
  must not score truth, language quality, social success, or agency.

/stream-candidates
  Select a read-only candidate view. It may display SegmentCandidate,
  StreamPattern, and StreamPromotionCandidate records derived from the
  local stream, but candidates remain local inspectable records.

/stream-promote <candidate_id>
  Validate one explicit StreamPromotionCandidate by ID and enqueue one
  corresponding QueuePerceptPayload through the existing event queue.
  This command does not call tick(); the operator must still type
  /step to advance the runtime.
```

The parser should continue to reject every unknown verb as local UI
status only. No command accepts shell syntax, file paths as execution
targets, network endpoints, JSON/YAML/TOML payloads, or Python
expressions.

## 3. Proposed Command Records

The later catalog patch plan should decide exact row IDs and accepted
field bounds. The likely typed payload records are:

```text
StreamTextPayload
  text: str

StreamPromotePayload
  candidate_id: str

Command(kind=STREAM_APPEND, payload=StreamTextPayload)
Command(kind=INSPECT_STREAM_SUMMARY, payload=None)
Command(kind=INSPECT_STREAM_CANDIDATES, payload=None)
Command(kind=STREAM_PROMOTE, payload=StreamPromotePayload)
```

Payload rules:

```text
text is bounded, non-empty, and acceptable under the same raw-text
  policy accepted for TextStreamChunk
candidate_id is bounded printable text
payload constructors are pure and frozen
payload constructors carry no callable, file handle, socket, path
  object, subprocess handle, LLM client, or arbitrary expression
```

## 4. Session-Local Stream State

`TextStreamHistory` should live on `OperatorSession` or an immediately
owned session-local record. It must not be stored in `BrainState`, MSI,
PtCns, the content registry, source histories, traces, or scenarios.

Likely session fields:

```text
text_stream_history: TextStreamHistory
stream_candidate_cache: tuple[StreamPromotionCandidate, ...]
```

The catalog plan should decide whether the candidate cache is stored or
rebuilt deterministically from history on demand. Either route must
preserve:

```text
no BrainState mutation
no source-history mutation
no direct tick route
bounded candidate count
bounded status / error text on failure
session remains resource-free
```

If storing a candidate cache widens the `OperatorSession` surface too
much, prefer a small immutable `StreamInteractionState` owned by the
session:

```text
StreamInteractionState
  history: TextStreamHistory
  promotion_candidates: tuple[StreamPromotionCandidate, ...]
```

This state would remain local UI/session state, not kernel state.

## 5. Summary And Candidate Views

The read-only display path should add a stream-specific snapshot rather
than letting the renderer inspect mutable session internals.

Likely display structures:

```text
StreamSummarySnapshot
  chunk_count: int
  latest_chunk_id: str | None
  total_text_length: int
  total_line_count: int
  total_whitespace_run_count: int
  latest_repeat_ratio: str | None

StreamCandidateSnapshot
  segment_count: int
  pattern_count: int
  promotion_candidate_count: int
  candidate_rows: tuple[tuple[str, str, str], ...]
```

Rules:

```text
snapshot construction is read-only
exact Fraction values render as strings
renderer receives immutable display values only
renderer does not import brain.development.text_stream if a snapshot
  layer can avoid it
renderer does not import brain.tick, brain.tlica, brain.llm, curses,
  subprocess, socket, network, or filesystem APIs
```

The active view enumeration likely needs two additional views:

```text
stream-summary
stream-candidates
```

The exact names should be locked in the catalog patch plan before code
changes.

## 6. Promotion Route

The accepted promotion route should be explicit and one-way:

```text
StreamPromotionCandidate
  -> /stream-promote <candidate_id>
  -> QueuePerceptPayload
  -> OperatorEventQueue.enqueue(...)
  -> /step
  -> PerceptEvent
  -> tick(...)
```

Required behavior:

```text
unknown candidate_id surfaces as local error only
reserved COGITO_ID remains rejected by the candidate and PerceptEvent
  constructors
event_queue full surfaces as local error only
successful promotion enqueues exactly one payload
successful promotion does not dequeue, tick, or mutate BrainState
candidate text and target_content_id come from the validated
  StreamPromotionCandidate, not from a second free-form parser path
```

`/stream-promote` should call the same `OperatorEventQueue.enqueue`
surface used by `/queue`; it must not append to the private queue list
directly.

## 7. Parser Bounds

The later catalog patch plan should lock exact constants. Initial
planning recommendation:

```text
/stream text bound: reuse STREAM_TEXT_MAX_LEN from text_stream.py
/stream-promote candidate_id bound: reuse STREAM_PROVENANCE_MAX_LEN
parser error bound: keep LOCAL_CMD_MAX_ERROR_LEN
session status bound: keep MAX_STATUS_TEXT_LEN
promotion candidate view bound: reuse STREAM_PROMOTION_MAX
```

If the parser imports text-stream constants, the static audit must
confirm it still avoids `brain.tick`, `brain.tlica`, `brain.llm`,
`curses`, shell, network, subprocess, and filesystem mutation. If that
import would make the parser too coupled, duplicate constants only with
a fixture that proves parity against the text-stream module.

## 8. Likely File Budget

The later catalog patch plan should make the file budget exact. The
likely implementation surface is:

```text
brain/ui/commands.py          add stream command kinds and payload records
brain/ui/command_line.py      parse /stream* verbs into typed commands
brain/ui/session.py           own local stream state and route commands
brain/ui/snapshot.py          add read-only stream display snapshots
brain/ui/render.py            render stream summary / candidate views
brain/ui/fixtures/...         add parser, router, snapshot, render fixtures
brain/invariants.py           register accepted Phase 3.8 rows
README.md                     document final accepted commands after code lands
```

Do not touch these guarded paths for Phase 3.8 unless a later accepted
catalog plan explicitly authorizes it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

## 9. Fixture Roster Sketch

The catalog patch plan should turn this sketch into exact rows:

```text
stream command parser accepts exactly /stream, /stream-summary,
  /stream-candidates, /stream-promote and rejects malformed forms

/stream appends one TextStreamChunk to session-local TextStreamHistory
  without mutating BrainState or event_queue

/stream-summary and /stream-candidates select read-only views and do
  not mutate history, candidates, BrainState, or event_queue

/stream-promote queues exactly one validated QueuePerceptPayload and
  does not call tick()

/step remains the only command that calls tick()

session resource-free audit still passes after adding stream state

snapshot records are frozen and read-only over text-stream state

renderer is deterministic for stream views and performs no I/O

failure paths are local status/error only
```

## 10. Phase 3.8b Boundary

Phase 3.8 must leave model-backed behavior for the later LLM Runtime
Toggle subcampaign:

```text
offline remains default
model-backed modes are explicit opt-in
selected client enters only through the existing tick client argument
standard fixtures remain deterministic
no second classification path is introduced through stream commands
```

Do not add `--llm-mode`, client factories, Anthropic/API clients, Claude
CLI clients, or model-backed smoke checks in Phase 3.8 command work.

## 11. Stop Point

Next artifact:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_CORRIGENDA.md
```

The corrigenda should audit this kickoff for parser closure, bounded
input, local stream-state ownership, promotion boundary discipline,
read-only views, failure isolation, resource-free session shape, and
Phase 3.8b separation.

After the corrigenda, the catalog patch plan must stop at the Step 22
review gate before any catalog or runtime implementation begins.
