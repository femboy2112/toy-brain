# Phase 3.24 — Worldlet Feedback Synthesis

## Architectural placement

Phase 3.24 extends the existing **processing-window feedback bridge**
by exactly one bounded path. Today, after each rehearsal in
`OperatorSession._run_processing_window`, the loop optionally fires
one or two follow-up chunks:

- `pledger_summary` (Phase 3.19) under
  `feedback_mode=PATTERN_LEDGER` or `PATTERN_AND_COHERENCE`;
- `cohmon_summary` (Phase 3.20) under
  `feedback_mode=COHERENCE` or `PATTERN_AND_COHERENCE`.

Phase 3.24 adds a third optional follow-up:

- `worldlet_summary` (Phase 3.24) under
  `feedback_mode=WORLDLET` or `PATTERN_COHERENCE_WORLDLET`.

The new mode `PATTERN_COHERENCE_WORLDLET` is the combined three-path
mode and fires `pledger_summary`, `cohmon_summary`, and
`worldlet_summary` in that fixed order. The existing
`PATTERN_AND_COHERENCE` mode is preserved bit-identically so every
existing fixture and benchmark case retains its observed digest.

## Design synthesis: why "bounded summary, not raw payload"

The Minimal Worldlet substrate carries a *finite* deterministic
harness. The bounded summary the feedback path replays must:

- be **deterministic** (same inputs ⇒ same output across runs / OSes);
- be **bounded printable text** under `STREAM_TEXT_MAX_LEN = 1024`;
- contain no raw worldlet payload (no token labels, no accepted-set,
  no full attempt-id list);
- be **stable under repeated feedback** so the Pattern Ledger
  records a *second-order entry* (the summary's signature differs
  structurally from the seed chunk's signature, the
  `pledger_summary` signature, and the `cohmon_summary` signature);
- be **non-claim-clean** (audited against
  `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`);
- be **session-local** (no persistence, no filesystem, no network).

The locked shape:

```text
worldlet_summary state=<state_id_or_absent> step=<int> objects=<int>
attempts=<int> responses=<int> accepted=<int> pushback=<int>
last_reason=<closed_set_member>
```

(The same line; line breaks here are documentation-only.)

## Closed-set validation table

| field | closed set / bound |
|---|---|
| `state` | printable str ≤ 64 chars OR sentinel `"absent"` |
| `step` | int in `[0, 65535]` |
| `objects` | int in `[0, 256]` |
| `attempts` | int in `[0, 256]` |
| `responses` | int in `[0, 256]` |
| `accepted` | int in `[0, 256]` |
| `pushback` | int in `[0, 256]` |
| `last_reason` | one of `{accepted, missing-target, rejected, target-unavailable, absent}` |

`accepted + pushback ≤ responses` is enforced by the helper as a
consistency cross-check (mirroring the
`pass + warn + fail + na == checks` cross-check in
`build_cohmon_summary_text`).

## Provenance design

After each rehearsal, the worldlet-feedback chunk carries the bounded
printable provenance string

```text
internal_processing_window:<k>:worldlet_summary
```

produced by

```python
build_rehearsal_provenance(
    tick_index=k,
    source=InternalEventSource.WORLDLET_SUMMARY,
)
```

The audit checks:

- the provenance is printable;
- the provenance is under `STREAM_PROVENANCE_MAX_LEN`;
- the provenance is non-claim-clean
  (`_FORBIDDEN_NON_CLAIM_TERMS` scan);
- the provenance appears in the dispatch trace's `before_facts` /
  `derived_facts` for the worldlet-feedback route;
- the provenance appears in the Pattern Ledger entry's `evidence_chunk_ids`
  trace via the chunk's normal `chunks_by_provenance` lookup.

## Feedback enabling truth table

| feedback_mode | rehearsal | pledger_summary | cohmon_summary | worldlet_summary |
|---|---|---|---|---|
| `OFF` | n | — | — | — |
| `PATTERN_LEDGER` | n | n | — | — |
| `COHERENCE` | n | — | n | — |
| `PATTERN_AND_COHERENCE` | n | n | n | — |
| `WORLDLET` | n | — | — | n |
| `PATTERN_COHERENCE_WORLDLET` | n | n | n | n |

`n = processing_window_size`. Existing rows are preserved bit-identically.

## Integration with the agent communication loop

`AgentObservationSummary` gains two new bounded fields:

```python
worldlet_feedback_present: bool   # True if any internal stream chunk
                                  # provenance ends in ":worldlet_summary"
worldlet_summary_count: int       # count of such chunks; <= STREAM_HISTORY_MAX_CHUNKS
```

`AgentReply` is allowed (but not required) to cite the bounded fact:

```text
worldlet_feedback=present route=internal_worldlet_summary
```

when the summary is present and the reply disposition is `PASS`. The
sentence is bounded printable text and non-claim-clean.

## Dispatch trace integration

`DispatchTrace` already records `feedback_mode` in the pre-state facts.
Phase 3.24 simply broadens the validated enum range; no new
`DispatchTraceKind` or `DispatchMutationKind` member is added (the
worldlet-feedback chunks ride the existing
`STREAM_WINDOW_INTERNAL` mutation classification, just like
`pledger_summary` and `cohmon_summary` chunks today).

A new bounded derived-fact is appended for worldlet-feedback runs:

```text
(worldlet_summary_chunks, <int 0..STREAM_HISTORY_MAX_CHUNKS>)
```

## Reasoning trace integration

One new `ReasoningStepKind` value is added:

```python
CHECK_WORLDLET_FEEDBACK = "check_worldlet_feedback"
```

It is inserted immediately before `CHECK_DISPATCH_TRACE` in every
trace; its body lists the bounded facts the summary helper produced
plus the dispatch trace digest.

## Learning evidence integration

One new `LearningEvidenceKind` value is added:

```python
WORLDLET_FEEDBACK_RECORDED = "worldlet_feedback_recorded"
```

The record is appended when a worldlet-summary chunk lands in the
session stream within the agent interaction step. Its facts cite the
bounded summary counts and the dispatch trace digest.

## Determinism + bounds proof outline

- The helper takes only bounded primitives ⇒ deterministic.
- `STREAM_TEXT_MAX_LEN = 1024` and the locked composed string is at
  most ~ 200 chars ⇒ bounded.
- The session-stream / Pattern Ledger / Growth Ledger caps already
  enforce upper bounds on the feedback throughput.
- The Pattern Ledger / Coherence Monitor / Growth Ledger semantics
  do not change. The new chunks are exactly *one more variety* of
  internal-source chunk and are observed by the existing
  Pattern-Ledger `observe()` path.

## Non-claim discipline

`worldlet_summary`, the new `WORLDLET_SUMMARY` source value, the new
`WORLDLET` / `PATTERN_COHERENCE_WORLDLET` feedback-mode values, and the
locked `last_reason` closed set are all non-claim-clean. The
static-audit fixture (`worldlet_feedback_static_audit.py`) imports
`_FORBIDDEN_NON_CLAIM_TERMS` and exhaustively scans:

- the new module-source / new helper / new enum members;
- the composed worldlet-summary text over a representative input set;
- the composed worldlet-summary provenance over the v1 source set;
- the reasoning trace / learning evidence labels.

If any term in `_FORBIDDEN_NON_CLAIM_TERMS` appears, the fixture fails
and the campaign is blocked.

## Why this does not move the cognitive baseline

The new feedback path:

- consumes **0** real model calls;
- does **not** call `brain.tick.tick`;
- does **not** mutate `OperatorSession.worldlet_history`;
- does **not** widen the existing cognitive-claim refusal classifier;
- adds two enum members and one summary helper, all bounded;
- preserves OFFLINE default;
- preserves the I-UI-10 self-audit (no callable / handle / client
  field appears on any session field or trace record).

ToyI's bounded structural runtime gains exactly one more bounded
audit-loop step. No claim of cognition is implied.
