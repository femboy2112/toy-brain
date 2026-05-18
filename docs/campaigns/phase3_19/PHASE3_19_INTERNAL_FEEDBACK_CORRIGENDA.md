# PHASE3_19_INTERNAL_FEEDBACK_CORRIGENDA.md

## Purpose

Lock the Phase 3.19 design decisions in advance of the Step 5
catalog patch plan. Each LOCK below names a single tightly
scoped choice; the body says **what** is locked, **why**, and
**what falls outside this lock for v1**.

Locks bind the v1 implementation. A future campaign may revisit
them via the standard catalog-patch protocol.

---

## LOCK A — v1 feedback source

**Locked:** Phase 3.19 v1 ships **pattern-ledger summary
feedback only** (architecture B in the synthesis). Coherence
feedback (architecture C) is governed by LOCK F. All other
feedback architectures (D combined / E REPL / F worldlet) are
DEFERRED.

**Reason:** B is the smallest extension that produces a
**second-order** Pattern Ledger entry through the existing
`_append_stream_chunk` call site. It reuses the previously
reserved `InternalEventSource.PLEDGER_SUMMARY` member; it adds
no new `GrowthEventType`; it does not touch `brain/tick.py`,
the LLM, the cache, the parser, or the schema.

**Out of v1 scope:**

- combined pattern + coherence feedback;
- REPL-generated internal observations;
- worldlet-simulation feedback;
- model-generated reflection over feedback events.

---

## LOCK B — Feedback event shape

**Locked:** every feedback event is a normal `TextStreamChunk`
constructed by `make_text_stream_chunk` and appended through
the existing `OperatorSession._append_stream_chunk` helper.
Specifically:

```text
field          shape
---------------+----------------------------------------------------
chunk_id       provided by OperatorSession._next_stream_chunk_id()
text           build_pledger_summary_text(entry) output, bounded
               printable, len <= STREAM_TEXT_MAX_LEN, no COGITO_ID,
               no _FORBIDDEN_NON_CLAIM_TERMS substring
source         TextStreamSource.OPERATOR
                 (the only TextStreamSource value the existing
                  helper paths produce; no new source value)
provenance     "internal_processing_window:<k>:pledger_summary"
                 (composed by build_rehearsal_provenance(
                   tick_index=k, source=InternalEventSource.PLEDGER_SUMMARY))
```

The feedback event carries no raw text from the original seed
chunk; only the deterministic summary template strings appear.

**Reason:** reusing the existing chunk shape preserves the
Phase 3.7 / 3.12c / 3.13 / 3.18 row family unchanged. No new
provenance prefix, no new source kind, no new growth event
type.

**Out of v1 scope:**

- attaching the seed text to the feedback event;
- adding a new bounded printable field to `TextStreamChunk`;
- introducing a new `TextStreamSource` value (e.g.,
  `"INTERNAL_FEEDBACK"`).

---

## LOCK C — Feedback target path

**Locked:** the feedback chunk is dispatched through the
**stream/internal chunk path** (existing
`_append_stream_chunk`), NOT through an event queue, NOT through
a new dispatcher kind, and NOT through `tick(...)`. The pure
helper `build_pledger_summary_text` returns the summary text;
`_run_processing_window` calls `_append_stream_chunk` with that
text under the `pledger_summary` provenance.

The summary text template is:

```text
"pledger_summary pattern_id=<entry.pattern_id> recurrence=<n>/256 sat=<state>"
```

where:

- `<entry.pattern_id>` is the bounded printable id from the
  Pattern Ledger entry the rehearsal just updated (typically
  `"pledger:<16hex>"`);
- `<n>` is the entry's `recurrence_count` after the rehearsal,
  written as a base-10 ASCII integer;
- `<state>` is the entry's `saturation_state.value`
  (`"open"`, `"saturated"`, or `"quiesced"`).

Constraints:

- output length is `< STREAM_TEXT_MAX_LEN` for every legal
  `(pattern_id, n, state)` combination at v0.26 caps;
- output is bounded printable;
- output does not contain `COGITO_ID`;
- output does not contain any `_FORBIDDEN_NON_CLAIM_TERMS`
  term (case-insensitive);
- byte-identical for the same inputs across runs / processes /
  OSes (no time / random / PID / hostname / id() input).

**Reason:** the stream/internal chunk path already routes Pattern
Ledger and Growth Ledger updates correctly; adding a new
dispatcher kind would widen the runtime surface beyond what v1
needs.

**Out of v1 scope:**

- enqueueing feedback as a `PerceptEvent` for `tick(...)`
  consumption;
- introducing a deferred-consolidation queue;
- introducing a feedback-event-specific provenance string
  beyond the `pledger_summary` suffix.

---

## LOCK D — Model-call policy

**Locked:** the v1 feedback path is **deterministic and offline
by default**. No `brain/llm/**` client is constructed,
configured, or invoked from inside the feedback path. The
`brain.development.processing_window` module continues to
satisfy the I-PWND-02 import audit (no `brain.llm`, no
`brain.tick`, no `brain.ui`).

Real-model reflection over feedback events is **DEFERRED**.

**Reason:** v1 must consume zero real model calls (mission
constraint). The feedback path produces inspectable structural
recurrence without semantic content; LLM evaluation is
orthogonal and can be added in a future campaign behind its own
review gate.

**Out of v1 scope:**

- LLM-generated summary text;
- LLM evaluation of the seed text alongside the feedback
  chunk;
- any `brain.llm.*` import in `brain/development/processing_window.py`.

---

## LOCK E — Processing window cap

**Locked:** `PROCESSING_WINDOW_SIZE_MAX = 255` is retained.
Phase 3.19 adds no runtime constant that would relax or replace
this cap. The behavior report tests `N = 0 / 5 / 10 / 50`; the
audit may additionally re-run Phase 3.18's `N = 255`
demonstration with feedback ON/OFF to confirm saturation
behavior under the new path.

The Phase 3.17 / 3.18 recommendation that `50` is the
"meaningful internalization" default is preserved.

**Reason:** changing the cap would invalidate Phase 3.18's
saturation demonstration without buying new behavior; the cap
is the structural ceiling for both rehearsal and feedback
chunks per dispatch.

**Out of v1 scope:**

- raising or lowering `PROCESSING_WINDOW_SIZE_MAX`;
- introducing a separate `FEEDBACK_WINDOW_SIZE_MAX`;
- making the cap configurable per `OperatorSession`.

---

## LOCK F — Coherence Monitor feedback

**Locked:** Coherence Monitor feedback (architecture C) is
**DEFERRED** in v1.

**Reason:** the Coherence Monitor module (`brain/development/
coherence_monitor.py`) imports `brain.ui.session.OperatorSession`
to build its report. Calling the monitor **from inside**
`_run_processing_window` requires either:

1. an inter-module import that breaks the current one-way
   `processing_window -> text_stream / profile` discipline
   (I-PWND-02 audit forbids `brain.ui` and any wider TLICA
   submodule); or
2. a parallel summary helper that reads bounded Pattern Ledger
   / stream / autosave fields directly without invoking the
   monitor, which duplicates monitor logic and risks drift; or
3. emitting Coherence summary text from the session helper
   (`brain/ui/session.py`) rather than the processing-window
   module — this would put the summary template inside the
   session module instead of the bounded helper, breaking the
   audit boundary.

All three options widen v1 beyond the bounded-extension target.
The synthesis hypothesis H3 cannot be tested in v1 without one
of them.

**Therefore:**

- the Phase 3.19 v1 implementation **does not** add a
  `FEEDBACK_MODE_COHERENCE` enum value;
- the existing `InternalEventSource.COHMON_SUMMARY` member
  remains **reserved** and continues to raise from
  `build_rehearsal_provenance`;
- a future campaign may revisit this lock with explicit
  resolution of options 1–3 above.

**Out of v1 scope:**

- coherence summary feedback;
- combined pattern + coherence feedback;
- any direct call to `build_coherence_report` from inside
  the processing window.

---

## LOCK G — Growth Ledger event types

**Locked:** Phase 3.19 introduces **no new `GrowthEventType`**
and **no new `GrowthEventSource`**. Feedback chunks emit the
existing `STREAM_CHUNK_ACCEPTED` and (when the second-order
entry is created or updated) `PATTERN_ENTRY_CREATED` /
`PATTERN_ENTRY_UPDATED` events through the existing
`_append_stream_chunk` emission code.

**Reason:** the Phase 3.13 Growth Ledger semantics are stable
and rely on the closed enum being a small fixed set. Adding a
new event type would require updating the Growth Ledger fixture
suite plus the persistence resource-audit fixtures.

**Out of v1 scope:**

- a `FEEDBACK_CHUNK_EMITTED` event type;
- a `PROCESSING_WINDOW` event source.

---

## LOCK H — No `brain/tick.py` change

**Locked:** Phase 3.19 does **not** modify `brain/tick.py`,
`brain/tlica/**`, or any kernel surface. The feedback path
fires inside `_run_processing_window`, which is itself called
from `OperatorSession.dispatch` after a successful external
`STREAM_APPEND`. The session dispatcher's tick path (`STEP_TICK`,
`tick(...)`, the LLM seam) is untouched.

**Reason:** mission constraint. The kernel boundary is
load-bearing for every prior catalog row.

**Out of v1 scope:**

- any edit to `brain/tick.py`, `brain/tlica/**`, or
  `brain/llm/**`;
- any change to the `(new_state, TickRecord)` return shape;
- any change to the existing dispatcher kinds.

---

## LOCK I — Non-claim discipline

**Locked:** every bounded printable string Phase 3.19 produces
is audited against the canonical
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
tuple. The audit covers:

- the `brain/development/processing_window.py` module source
  (already covered by I-PWND-02);
- the `build_pledger_summary_text` output across a fixed set of
  representative `(pattern_id, n, state)` inputs;
- the new `FeedbackMode` enum member values;
- the new `MODULE_PRODUCED_STRINGS` extension (if the existing
  tuple is widened);
- every fixture file produced for I-IFBK-NN rows.

The audit MUST produce zero hits on the term tuple.

**Reason:** Phase 3.19 sits structurally close to "metacognition"
language. Active discipline prevents drift.

**Out of v1 scope:**

- relaxing or amending `_FORBIDDEN_NON_CLAIM_TERMS`;
- introducing a per-row exception list.

---

## LOCK J — Stage C.1 implementation policy

**Locked:** Stage C.1 may be used for bounded doc shards
(synthesis, probe matrix, corrigenda, catalog patch plan, PR
body) when the operator believes a shard is large enough to
justify bridge overhead. Stage C.1 may also be used for bounded
fixture / module shards **after** Step 6 review gate, subject to:

- a validated manifest under the canonical
  `python3 -m tools.claude_helpers.flow_manifest validate`
  command;
- `max_parallel = 2`;
- at most 5 total Codex nodes across the campaign;
- no automatic retry;
- no overlap in declared write sets;
- no Codex staging / commit / push.

Stage C.1 is **forbidden** for:

- raw codex / codex exec invocation;
- secrets, raw prompts, raw model responses;
- broad runtime changes;
- `brain/tick.py` edits;
- final catalog reconciliation;
- the final invariant runner gate.

Parent Claude commits and pushes every step.

**Reason:** Phase 3.19 follows the campaign-wide Stage C.1
policy. The locks above ensure no bridge invocation drifts the
campaign past v1 scope.

**Out of v1 scope:**

- raising the 5-node Stage C.1 cap;
- using Stage C.1 to run the behavior report.

---

## Lock cross-check vs the autonomy-authorization checklist

The Step 6 autonomy authorization checks ten conditions. Per
this corrigenda:

```text
1. Step 5 has zero critical correctness blockers.
   -> Determined in Step 5 (catalog patch plan).
2. Step 5 has zero safety/invariant blockers.
   -> Determined in Step 5.
3. Step 5 does not require brain/tick.py edits.
   -> Locked here (LOCK H).
4. Step 5 preserves L1/L2 cache semantics.
   -> Locked here (LOCK D + the synthesis section 3.4).
5. Step 5 preserves OFFLINE default + explicit opt-in.
   -> Locked here (LOCK D).
6. Step 5 has exact row family, statuses, count delta, fixture
   list, implementation files, validation plan.
   -> Step 5 output.
7. Step 5 has a bounded internal-feedback design.
   -> Locked here (LOCK A + LOCK B + LOCK C).
8. Step 5 does not introduce cognitive overclaims.
   -> Locked here (LOCK I).
9. Stage A review identifies no blocking flaw.
   -> Stage A not used in Phase 3.19 unless an operator
      escalates; default is no Stage A.
10. Implementation fits the allowed file set.
    -> Locked here (LOCK A + LOCK C + LOCK G + LOCK H).
```

---

## Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the locks are derivable from the synthesis + probe
  matrix + existing repo state; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard; bridge overhead exceeds direct
  write cost.
```

---

## Next artifact

`docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_CATALOG_PATCH_PLAN.md`
— the Step 5 catalog patch plan, which converts these locks
into exact rows, fixtures, files, counts, and validation steps.
