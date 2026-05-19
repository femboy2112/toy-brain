# Phase 3.24 — Worldlet Feedback Spec

This document is the **design contract** for Phase 3.24. Every item in
the acceptance criteria of the campaign points here. Spec items are
phrased so a fixture can directly assert them.

## S.1 Enum extensions (closed sets)

### S.1.a `processing_window.InternalEventSource`

Add member:

```python
WORLDLET_SUMMARY = "worldlet_summary"
```

Add `WORLDLET_SUMMARY` to `_V1_EMITTED_SOURCES`. Update
`MODULE_PRODUCED_STRINGS` to include the new value.

### S.1.b `processing_window.FeedbackMode`

Add members:

```python
WORLDLET = "worldlet"
PATTERN_COHERENCE_WORLDLET = "pattern_coherence_worldlet"
```

Add both to `_FEEDBACK_MODE_VALID`. Update `MODULE_PRODUCED_STRINGS` to
include both values. Validation rejects any non-member with a typed
`ValueError`.

## S.2 Helper signature

```python
def build_worldlet_summary_text(
    *,
    state_id_value: str,           # printable str <= 64; or sentinel "absent"
    step_index: int,               # in [0, 65535]
    object_count: int,             # in [0, 256]
    attempt_count: int,            # in [0, 256]
    response_count: int,           # in [0, 256]
    accepted_count: int,           # in [0, 256]
    pushback_count: int,           # in [0, 256]
    last_reason_value: str,        # closed set, see below
) -> str
```

Closed set for `last_reason_value`:

```text
{accepted, missing-target, rejected, target-unavailable, absent}
```

Validation order: type → range → printability → COGITO_ID check →
cross-check `accepted_count + pushback_count <= response_count`. The
composed string is

```text
worldlet_summary state=<state_id_value> step=<n> objects=<n> attempts=<n>
responses=<n> accepted=<n> pushback=<n> last_reason=<v>
```

Bounded by `WORLDLET_SUMMARY_TEXT_MAX_LEN = 240` and
`STREAM_TEXT_MAX_LEN = 1024`.

Pure function: no I/O, no time, no random, no PID, no hostname, no
`id()`.

## S.3 Provenance

`build_rehearsal_provenance(..., source=InternalEventSource.WORLDLET_SUMMARY)`
produces

```text
internal_processing_window:<k>:worldlet_summary
```

Validated against `STREAM_PROVENANCE_MAX_LEN`, printability, and
COGITO_ID.

## S.4 OperatorSession integration

Add (no new field on the dataclass; the helper reads the existing
`worldlet_history` field):

```python
def _run_worldlet_feedback_step(
    self, *, tick_index: int
) -> bool: ...
```

Behavior:

1. Build primitives from `self.worldlet_history`. When the history is
   `None`, use the sentinel triple
   `(state_id_value="absent", step_index=0, object_count=0,
   attempt_count=0, response_count=0, accepted_count=0,
   pushback_count=0, last_reason_value="absent")`.
2. Call `build_worldlet_summary_text(**primitives)`.
3. Call `build_rehearsal_provenance(tick_index, WORLDLET_SUMMARY)`.
4. Dispatch via `self._append_stream_chunk(text=..., chunk_provenance=...,
   growth_provenance="stream_append:_run_processing_window")`.
5. Return `True` on success, `False` on bounded substrate refusal (with
   `self.set_error(...)` already called).

`_run_processing_window` is extended: after each rehearsal, fire the
`worldlet_summary` chunk whenever
`self.feedback_mode in {WORLDLET, PATTERN_COHERENCE_WORLDLET}`. The
fixed ordering is

```text
rehearsal -> pledger_summary -> cohmon_summary -> worldlet_summary
```

`PATTERN_AND_COHERENCE` and the other pre-existing modes preserve their
exact prior behavior.

## S.5 DispatchTracer integration

No new `DispatchTraceKind` / `DispatchMutationKind` value is added.
Phase 3.24 only **broadens** the validated enum range that the dispatch
tracer is allowed to see in its `feedback_mode` fact (the value comes
from `FeedbackMode.value`). The worldlet-feedback chunks ride the
existing `STREAM_WINDOW_INTERNAL` mutation kind.

One new derived-fact key is added to the dispatch trace under the
worldlet-feedback route:

```text
("worldlet_summary_chunks", "<int 0..STREAM_HISTORY_MAX_CHUNKS>")
```

emitted by the `_DispatchTraceBuilder` after the post-state count is
known.

## S.6 ReasoningTrace integration

Add one new closed value:

```python
CHECK_WORLDLET_FEEDBACK = "check_worldlet_feedback"
```

Inserted immediately **before** `CHECK_DISPATCH_TRACE` in every trace.
Its body cites the bounded worldlet facts plus the dispatch trace
digest. The trace-report counts dict gains a new key. Trace digest
stability is preserved across fresh sessions.

## S.7 LearningEvidence integration

Add one new closed value:

```python
WORLDLET_FEEDBACK_RECORDED = "worldlet_feedback_recorded"
```

Emitted once per interaction step in which any internal
`:worldlet_summary` chunk lands in the session stream. The record's
facts include the bounded counts plus the dispatch trace digest.

## S.8 AgentLoop integration

Extend `AgentObservationSummary`:

```python
worldlet_feedback_present: bool
worldlet_summary_count: int          # 0..STREAM_HISTORY_MAX_CHUNKS
```

Both default to `False` / `0` for backwards compatibility (existing
fixtures pass them in).

`AgentReply` adds an optional bounded line citing the worldlet-feedback
state when `worldlet_feedback_present is True`:

```text
worldlet_feedback=present route=internal_worldlet_summary
```

The line is added to the `PASS` section body. Refusal / FAIL replies
are unchanged.

## S.9 Benchmark A11

`BenchmarkAxis.WORLDLET_FEEDBACK = "worldlet_feedback"` with twelve
cases:

```text
A11.01  WORLDLET feedback mode validates as a closed enum member
A11.02  build_worldlet_summary_text deterministic + bounded
A11.03  STREAM_APPEND with N>0 + WORLDLET emits worldlet_summary chunks
A11.04  worldlet_summary chunks update Pattern Ledger entries
A11.05  dispatch trace records feedback_mode=WORLDLET + internal route
A11.06  reasoning trace contains CHECK_WORLDLET_FEEDBACK
A11.07  learning evidence records WORLDLET_FEEDBACK_RECORDED
A11.08  agent reply cites bounded worldlet-feedback facts safely
A11.09  PATTERN_COHERENCE_WORLDLET combined mode works
A11.10  worldlet feedback digest stable across two fresh runs
A11.11  worldlet-feedback source scan has zero forbidden-term hits
A11.12  A1..A10 case counts retained
```

## S.10 Catalog rows

`I-WFDBK-01..12` (11 REQUIRED + 1 STRUCTURAL). Bumps the catalog to
v0.33. Twelve fixtures land in `brain/ui/fixtures/`.

## S.11 Hard constraints

- No edit to `brain/tick.py`, `brain/llm/**`, parser, prompt, DB
  schema, autosave policy, L1 / L2 cache, Pattern Ledger / Coherence
  Monitor / Growth Ledger semantics, or curses code.
- No new `OperatorCommand` member; no new `ACTIVE_VIEWS` value; no new
  `GrowthEventType` / `GrowthEventSource`.
- OFFLINE default preserved; model-backed paths remain explicit opt-in.
- Zero real model calls expected.
- Cognitive-claim refusal classifier is preserved; cognitive-claim
  probes still trigger the refusal path; the dispatch trace records the
  no-mutation route — never the cognitive claim.

## S.12 Acceptance

Pass only when:

- runner is fully green (`python3 -m brain.invariants run`);
- benchmark axes A1..A11 are green (A3.04 WARN may remain);
- gate_runner is 5/5 PASS;
- branch is pushed;
- PR #29 is open against `campaign/phase3-23-dispatch-tracer`.
