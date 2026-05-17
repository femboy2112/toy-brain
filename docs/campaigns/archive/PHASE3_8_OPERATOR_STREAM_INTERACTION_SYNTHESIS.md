# PHASE3_8_OPERATOR_STREAM_INTERACTION_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.8 Operator Stream Interaction step before any
catalog or runtime work. This is a planning artifact only. It does not
edit the catalog, add rows, modify `brain/ui/`, change `brain/invariants.py`,
or connect text-stream evidence to `tick()`.

Phase 3.8 follows the Phase 3.7 Text Stream Ingress audit because the
bounded local substrate now exists:

```text
TextStreamChunk
TextStreamHistory
StreamFeatureVector
SegmentCandidate
StreamPattern
StreamPromotionCandidate
```

The Phase 3.8 task is to expose that substrate through finite typed
operator commands while preserving the existing `PerceptEvent` and
`tick()` boundary.

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
Current branch:   campaign/fast-safe-text-interaction
```

Phase 3.7 established that text-stream evidence is bounded, local,
copy-on-write, deterministic, and below the promotion boundary. It also
left UI integration explicitly deferred to Phase 3.8. Therefore this
phase owns the typed operator route from raw stream text to explicit
promotion candidates.

## 2. Thesis

Operator Stream Interaction is a finite local command extension for the
existing Operator TUI. It lets an operator append bounded raw text,
inspect text-stream summaries and candidates, and explicitly promote one
validated candidate into the existing event queue.

It is not a chat layer, not a language understanding layer, not Mode B,
not a model-backed path, and not a second runtime transition route.

The governing route remains:

```text
/stream <text>
  -> append TextStreamChunk to local TextStreamHistory only
  -> no BrainState mutation
  -> no PerceptEvent construction
  -> no tick() call

/stream-summary
  -> read-only view over TextStreamHistory / StreamFeatureVector data
  -> no score, truth value, social value, or agency value

/stream-candidates
  -> read-only view over SegmentCandidate / StreamPattern /
     StreamPromotionCandidate structures
  -> candidates are inspectable, not events

/stream-promote <candidate_id>
  -> validate one explicit StreamPromotionCandidate
  -> construct and enqueue the corresponding QueuePerceptPayload /
     PerceptEvent candidate through the existing public boundary
  -> no tick() call

/step
  -> remains the only route that calls tick()
```

## 3. Command Commitments

Phase 3.8 should extend the existing finite typed parser rather than add
a free-form command channel. Candidate verbs:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
```

Parser commitments:

```text
closed verb set
bounded text length aligned with the accepted Phase 3.8 catalog plan
bounded candidate identifiers
no shell expansion
no JSON / YAML / TOML parser
no eval / exec / compile
no subprocess / socket / network / filesystem mutation
invalid input becomes local UI status only
```

Session commitments:

```text
TextStreamHistory is local session state
/stream appends only through the session router
/stream-summary and /stream-candidates are read-only
/stream-promote enqueues exactly one validated candidate
/stream-promote does not consume the candidate by calling tick()
/step remains the only tick route
failure isolation remains local UI status / error text only
```

Render commitments:

```text
the stream view is deterministic
the renderer reads view-model data only
the renderer does not mutate stream history or event queues
the renderer does not import or call tick()
```

## 4. Promotion Boundary

Phase 3.7 deliberately made `StreamPromotionCandidate` not a
`PerceptEvent`. Phase 3.8 should keep that distinction visible:

```text
StreamPromotionCandidate
  = explicit local candidate with source / provenance / chunk evidence

QueuePerceptPayload
  = existing UI payload bounded by the PerceptEvent constructor

PerceptEvent
  = existing public event boundary accepted by tick()
```

The only authorized bridge is the explicit operator command:

```text
/stream-promote <candidate_id>
```

That command may enqueue a validated payload. It must not call `tick()`;
the operator still advances the runtime with `/step`.

## 5. Non-Goals

Phase 3.8 does not authorize:

```text
raw text mutating BrainState directly
raw text mapping to COGITO_ID
raw text bypassing PerceptEvent construction
text-stream evidence mutating source histories
automatic promotion of any candidate
direct tick calls from /stream, /stream-summary, /stream-candidates, or
  /stream-promote
language parsing or semantic understanding
truth scoring
social / conversational modeling
Mode B planning
self-modification
host execution, shell, subprocess, network, or filesystem save/export
real LLM calls below the explicit Phase 3.8b toggle
```

## 6. Likely File Surface

The kickoff should refine the file budget before any code change. The
likely implementation surface, subject to the later catalog patch plan,
is:

```text
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/snapshot.py
brain/ui/render.py
brain/ui/fixtures/...
brain/invariants.py
README.md
```

The text-stream substrate in `brain/development/text_stream.py` should be
consumed as an existing local development layer. The Phase 3.8 work
should not move text-stream code into `brain/tlica/`, `brain/tick.py`,
`brain/llm/`, scenarios, or traces.

## 7. Risks

```text
parser drift: adding free-form behavior instead of a closed verb set
boundary drift: promotion directly creating runtime effects
state drift: storing stream history in BrainState instead of session-local
render drift: making summaries compute side effects
scope drift: treating raw text as language, truth, agency, or Mode B
future-toggle drift: mixing Phase 3.8b model-backed behavior into
  Phase 3.8 command implementation
```

The catalog patch plan should turn these risks into testable rows before
runtime code lands.

## 8. Next Artifact

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md
```

The kickoff should define the proposed command records, session-local
stream state, summary / candidate view-models, promotion routing, parser
bounds, renderer view, fixture roster, and the exact point where the
later catalog patch plan must stop for review.
