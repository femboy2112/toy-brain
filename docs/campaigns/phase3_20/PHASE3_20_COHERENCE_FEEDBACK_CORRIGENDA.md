# PHASE3_20_COHERENCE_FEEDBACK_CORRIGENDA.md

## Purpose

Lock the Phase 3.20 design decisions in advance of the Step 5
catalog patch plan. Each LOCK below names a single tightly scoped
choice; the body says **what** is locked, **why**, and **what
falls outside this lock for v1**.

Locks bind the v1 implementation. A future campaign may revisit
them via the standard catalog-patch protocol.

---

## LOCK A — v1 feedback source

**Locked:** Phase 3.20 v1 ships **Coherence Monitor summary
feedback** (architecture C from the Phase 3.19 synthesis, now
the Phase 3.20 main path; equivalently Architecture A from the
Phase 3.20 synthesis). REPL feedback, worldlet feedback, and
model-generated reflection are DEFERRED.

**Reason:** Coherence is the next bounded feedback source that
re-enters the substrate the monitor is observing. It exploits the
previously reserved `InternalEventSource.COHMON_SUMMARY` member.
It adds no new `GrowthEventType`, no new `GrowthEventSource`, no
new dispatcher kind, no kernel surface, no LLM call, no parser
change, no schema change. The new helper accepts only bounded
primitives, so `brain/development/processing_window.py` continues
to satisfy I-PWND-02.

**Out of v1 scope:**

- REPL-generated internal observations;
- worldlet-simulation feedback;
- model-generated reflection over feedback events;
- any change to the Coherence Monitor's check set, status enum,
  or source labels (the monitor stays read-only and unchanged).

---

## LOCK B — Feedback event shape

**Locked:** every coherence-feedback event is a normal
`TextStreamChunk` constructed by `make_text_stream_chunk` and
appended through the existing
`OperatorSession._append_stream_chunk` helper. Specifically:

```text
field          shape
---------------+----------------------------------------------------
chunk_id       provided by OperatorSession._next_stream_chunk_id()
text           build_cohmon_summary_text(...) output, bounded
               printable, len <= COHMON_SUMMARY_TEXT_MAX_LEN = 160,
               len <= STREAM_TEXT_MAX_LEN = 1024, no COGITO_ID,
               no _FORBIDDEN_NON_CLAIM_TERMS substring
source         TextStreamSource.OPERATOR
                 (existing helper paths produce only OPERATOR;
                  no new source value)
provenance     "internal_processing_window:<k>:cohmon_summary"
                 (composed by build_rehearsal_provenance(
                   tick_index=k, source=InternalEventSource.COHMON_SUMMARY))
```

The feedback event carries no raw text from the original seed
chunk, no `CoherenceReport` instance, no `CoherenceCheck`
instance, no `OperatorSession` reference. Only the deterministic
summary template strings appear, built from bounded primitives.

**Reason:** reusing the existing chunk shape preserves the
Phase 3.7 / 3.12c / 3.13 / 3.18 / 3.19 row families unchanged.
No new provenance prefix, no new source kind, no new growth event
type.

**Out of v1 scope:**

- attaching the report or any check object to the feedback event;
- adding a new bounded printable field to `TextStreamChunk`;
- introducing a new `TextStreamSource` value (e.g.,
  `"INTERNAL_FEEDBACK"`);
- attaching the seed chunk text to the feedback event.

---

## LOCK C — Feedback target path and summary template

**Locked:** the feedback chunk is dispatched through the
**stream/internal chunk path** (existing
`_append_stream_chunk`), NOT through an event queue, NOT through
a new dispatcher kind, and NOT through `tick(...)`. The pure
helper `build_cohmon_summary_text` returns the summary text;
`_run_cohmon_feedback_step` calls `_append_stream_chunk` with that
text under the `cohmon_summary` provenance.

The summary text template is:

```text
"cohmon_summary overall=<status> pass=<np> warn=<nw> fail=<nf> na=<nna> checks=<nc>"
```

where:

- `<status>` is `CoherenceReport.overall_status.value`, in the
  closed set `{"pass", "warn", "fail", "not_applicable"}`;
- `<np>` / `<nw>` / `<nf>` / `<nna>` are the per-status counts
  pulled from `CoherenceReport.counts_by_status`, each a base-10
  ASCII integer in `[0, COHERENCE_MAX_CHECKS = 64]`;
- `<nc>` is the total check count, a base-10 ASCII integer in
  `[0, COHERENCE_MAX_CHECKS = 64]` that equals `np + nw + nf + nna`.

Constraints:

- output length is `< STREAM_TEXT_MAX_LEN` for every legal
  primitive combination at v0.27 caps (predicted max ~ 79 chars,
  well under the locked cap `COHMON_SUMMARY_TEXT_MAX_LEN = 160`);
- output is bounded printable;
- output does not contain `COGITO_ID`;
- output does not contain any `_FORBIDDEN_NON_CLAIM_TERMS`
  term (case-insensitive);
- byte-identical for the same inputs across runs / processes /
  OSes (no time / random / PID / hostname / id() input);
- helper accepts only bounded primitives; never accepts a
  `CoherenceReport`, `CoherenceCheck`, or `OperatorSession`
  reference.

**Reason:** the stream/internal chunk path already routes Pattern
Ledger and Growth Ledger updates correctly; adding a new
dispatcher kind would widen the runtime surface beyond what v1
needs. Restricting the helper to primitives keeps the
I-PWND-02 import audit intact.

**Out of v1 scope:**

- enqueueing feedback as a `PerceptEvent` for `tick(...)`
  consumption;
- introducing a deferred-consolidation queue;
- introducing a feedback-event-specific provenance string beyond
  the `cohmon_summary` suffix;
- including individual check ids or summaries inside the text
  (only aggregate counts appear).

---

## LOCK D — Feedback mode enum membership

**Locked:** Phase 3.20 v1 ships **three new members** of
`FeedbackMode`:

```text
FeedbackMode.COHERENCE                = "coherence"
FeedbackMode.PATTERN_AND_COHERENCE    = "pattern_and_coherence"
```

(In addition to the existing `OFF` and `PATTERN_LEDGER`.) The
combined mode `PATTERN_AND_COHERENCE` is included because:

- it is a pure composition of the Phase 3.19 `_run_feedback_step`
  and the new `_run_cohmon_feedback_step`;
- it adds no extra runtime file beyond the COHERENCE path;
- it lets the synthesis hypothesis H3 (combined feedback creates
  more inspectable structure than single-mode feedback) be tested
  in v1;
- the chunk-count formula stays a deterministic `1 + alpha * N`
  with `alpha in {1, 2, 2, 3}` for OFF / PATTERN_LEDGER /
  COHERENCE / PATTERN_AND_COHERENCE respectively.

`validate_feedback_mode` is updated to accept the new members.

**Reason:** the combined mode is cheap and provides a direct
test of the layering claim. If Step 5 turns up a correctness
blocker, the patch plan may downgrade to COHERENCE only and
defer PATTERN_AND_COHERENCE to Phase 3.21.

**Out of v1 scope:**

- any `FEEDBACK_MODE_REPL` / `FEEDBACK_MODE_WORLDLET` member;
- any per-mode runtime configuration beyond `feedback_mode`
  itself;
- any mode-specific cap separate from
  `PROCESSING_WINDOW_SIZE_MAX = 255`.

---

## LOCK E — Coherence Monitor semantics

**Locked:** the Coherence Monitor module
(`brain/development/coherence_monitor.py`) is **not modified** in
v1. Specifically:

- no new check is added;
- no existing check is removed or reordered;
- the `CoherenceCheckStatus` enum (`PASS`, `WARN`, `FAIL`,
  `NOT_APPLICABLE`) is unchanged;
- the `CHECK_SOURCES` frozenset is unchanged;
- the `COHERENCE_MAX_CHECKS = 64` cap is unchanged;
- `_FORBIDDEN_NON_CLAIM_TERMS` is unchanged;
- no mutation of any kernel container is introduced;
- `build_full_coherence_report` retains its existing signature
  and read-only contract.

`PASS / WARN / FAIL / NOT_APPLICABLE` labels are treated as
**structural statuses** about whether bounded invariants
currently hold across kernel / session / stream / pattern-ledger /
persistence-autosave records. They are NOT recoded as truth
claims, value judgments, or recommendations.

**Reason:** mission constraint. Touching the monitor would widen
the catalog row family and require updating I-COHMON-04..11 plus
the persistence resource-audit fixtures.

**Out of v1 scope:**

- adding a new check;
- adding a new `CoherenceCheckStatus` value;
- adding a new check `source` label;
- mutating any kernel container from inside the monitor.

---

## LOCK F — Growth Ledger event types

**Locked:** Phase 3.20 introduces **no new `GrowthEventType`**
and **no new `GrowthEventSource`**. Coherence-feedback chunks emit
the existing `STREAM_CHUNK_ACCEPTED` and (when the second-order
entry is created or updated) `PATTERN_ENTRY_CREATED` /
`PATTERN_ENTRY_UPDATED` events through the existing
`_append_stream_chunk` emission code.

**Reason:** the Phase 3.13 Growth Ledger semantics are stable and
rely on the closed enum being a small fixed set. Adding a new
event type would require updating the Growth Ledger fixture suite
plus the persistence resource-audit fixtures.

**Out of v1 scope:**

- a `COHMON_FEEDBACK_EMITTED` event type;
- a `PROCESSING_WINDOW` or `COHERENCE_MONITOR` event source.

---

## LOCK G — Processing window cap

**Locked:** `PROCESSING_WINDOW_SIZE_MAX = 255` is retained.
Phase 3.20 adds no runtime constant that would relax or replace
this cap. The behavior report tests `N = 0 / 5 / 10 / 50`; the
audit may additionally re-run Phase 3.18's `N = 255`
demonstration with COHERENCE feedback ON/OFF to confirm
saturation behavior under the new path, but the v1 cap stays at
255.

The Phase 3.17 / 3.18 recommendation that `50` is the
"meaningful internalization" default is preserved.

**Reason:** changing the cap would invalidate Phase 3.18's
saturation demonstration without buying new behavior; the cap is
the structural ceiling for both rehearsal and feedback chunks per
dispatch.

**Out of v1 scope:**

- raising or lowering `PROCESSING_WINDOW_SIZE_MAX`;
- introducing a separate `FEEDBACK_WINDOW_SIZE_MAX`;
- making the cap configurable per `OperatorSession`.

---

## LOCK H — No `brain/tick.py` change

**Locked:** Phase 3.20 does **not** modify `brain/tick.py`,
`brain/tlica/**`, or any kernel surface. The feedback path fires
inside `_run_processing_window`, which is itself called from
`OperatorSession.dispatch` after a successful external
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

## LOCK I — Model-call policy

**Locked:** the v1 feedback path is **deterministic and offline
by default**. No `brain/llm/**` client is constructed,
configured, or invoked from inside the coherence-feedback path.
The `brain/development/processing_window.py` module continues to
satisfy the I-PWND-02 import audit (no `brain.llm`, no
`brain.tick`, no `brain.ui`, no `brain.development.coherence_monitor`).
`brain/ui/session.py` is allowed to import
`brain.development.coherence_monitor.build_full_coherence_report`,
but only via a **deferred function-body import** inside
`_run_cohmon_feedback_step` to avoid a circular module load with
`coherence_monitor` (which already imports `OperatorSession`).

Real-model reflection over feedback events is **DEFERRED**.

**Reason:** v1 must consume zero real model calls (mission
constraint). The feedback path produces inspectable structural
recurrence without semantic content; LLM evaluation is orthogonal
and can be added in a future campaign behind its own review gate.

**Out of v1 scope:**

- LLM-generated summary text;
- LLM evaluation of the seed text alongside the feedback chunk;
- any `brain.llm.*` import anywhere in the coherence-feedback
  path;
- any module-level (top-of-file) import of `coherence_monitor` in
  `brain/ui/session.py`.

---

## LOCK J — Non-claim discipline

**Locked:** every bounded printable string Phase 3.20 produces is
audited against the canonical
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
tuple. The audit covers:

- the `brain/development/processing_window.py` module source
  (already covered by I-PWND-02; the widened audit re-runs after
  the helper lands);
- the `build_cohmon_summary_text` output across a fixed set of
  representative `(overall_status_value, np, nw, nf, nna, nc)`
  inputs;
- the new `FeedbackMode` member values (`"coherence"`,
  `"pattern_and_coherence"`);
- the new `MODULE_PRODUCED_STRINGS` extension entries
  (`COHMON_SUMMARY_TEXT_PREFIX = "cohmon_summary"` plus the
  new FeedbackMode values);
- every fixture file produced for I-CFBK-NN rows.

The audit MUST produce zero hits on the term tuple.

`PASS / WARN / FAIL / NOT_APPLICABLE` are **structural statuses**;
they are never recoded as truth claims, value judgments, or
recommendations. The text "overall=fail" inside a coherence
summary chunk means "the bounded structural-status aggregation
returned `CoherenceCheckStatus.FAIL`", not "the system is wrong"
or "the system has failed".

**Reason:** Phase 3.20 sits structurally close to "metacognition"
language. Active discipline prevents drift.

**Out of v1 scope:**

- relaxing or amending `_FORBIDDEN_NON_CLAIM_TERMS`;
- introducing a per-row exception list;
- introducing any aggregate scalar (no "coherence-feedback I-ness
  score", no rolled-up index).

---

## LOCK K — Stage C.1 implementation policy

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

**Reason:** Phase 3.20 follows the campaign-wide Stage C.1
policy. The locks above ensure no bridge invocation drifts the
campaign past v1 scope.

**Out of v1 scope:**

- raising the 5-node Stage C.1 cap;
- using Stage C.1 to run the behavior report.

---

## Lock cross-check vs the autonomy-authorization checklist

The Step 6 autonomy authorization checks eleven conditions. Per
this corrigenda:

```text
 1. Step 5 has zero critical correctness blockers.
    -> Determined in Step 5 (catalog patch plan).
 2. Step 5 has zero safety/invariant blockers.
    -> Determined in Step 5.
 3. Step 5 does not require brain/tick.py edits.
    -> Locked here (LOCK H).
 4. Step 5 preserves L1/L2 cache semantics.
    -> Locked here (LOCK I; coherence-feedback path makes no LLM
       call, so cache is untouched).
 5. Step 5 preserves parser and prompt semantics.
    -> No parser or prompt edit is in scope; campaign non-goals
       enforce this.
 6. Step 5 preserves OFFLINE default + explicit opt-in.
    -> Locked here (LOCK I).
 7. Step 5 has exact row family, statuses, count delta, fixture
    list, implementation files, and validation plan.
    -> Step 5 output.
 8. Step 5 has a bounded coherence-feedback design.
    -> Locked here (LOCK A + LOCK B + LOCK C + LOCK D).
 9. Step 5 does not introduce cognitive overclaims.
    -> Locked here (LOCK J).
10. Stage A review identifies no blocking flaw.
    -> Stage A not used in Phase 3.20 unless an operator
       escalates; default is no Stage A.
11. Implementation fits the allowed file set.
    -> Locked here (LOCK A + LOCK C + LOCK F + LOCK H + LOCK I).
```

---

## Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the locks are derivable from the synthesis + probe
  matrix + existing repo state + Phase 3.19 LOCK F precedent;
  no external review needed.

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

`docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_CATALOG_PATCH_PLAN.md`
— the Step 5 catalog patch plan, which converts these locks
into exact rows, fixtures, files, counts, and validation steps.
