# PHASE3_19_INTERNAL_FEEDBACK_CATALOG_PATCH_PLAN.md

## Purpose

Convert the Step 4 locks into an exact catalog patch plan: which
files change, which row IDs land at which statuses, what fixtures
register them, what the version banner reads after the patch, and
what the Step 6 review gate inspects before Step 7 implementation
begins.

This document is the single source of truth for the Step 7
implementation; any divergence between it and Step 7 is a
campaign error.

---

## 1. Implementation architecture (one paragraph)

After a successful external `STREAM_APPEND`,
`OperatorSession._run_processing_window(seed_chunk)` interleaves,
for each `k` in `1..processing_window_size`:

1. one **rehearsal** chunk (Phase 3.18 behavior, unchanged) —
   `_append_stream_chunk(text=seed_chunk.text,
   chunk_provenance="internal_processing_window:<k>:rehearsal",
   ...)`;
2. **only if** `self.feedback_mode == FeedbackMode.PATTERN_LEDGER`,
   one **feedback** chunk — `_append_stream_chunk(
   text=build_pledger_summary_text(<seed_entry_after_rehearsal>),
   chunk_provenance="internal_processing_window:<k>:pledger_summary",
   ...)`.

`build_pledger_summary_text` is a new pure function on
`brain/development/processing_window.py` whose deterministic
output is `"pledger_summary pattern_id=<id> recurrence=<n>/256
sat=<state>"` (LOCK C). `FeedbackMode` is a new closed
`(str, Enum)` on the same module with members `OFF` and
`PATTERN_LEDGER`. `OperatorSession.feedback_mode` is a new
optional field defaulting to `FeedbackMode.OFF`, constructor-
validated by `validate_feedback_mode`. The Phase 3.18
`_V1_EMITTED_SOURCES` frozenset widens to include
`InternalEventSource.PLEDGER_SUMMARY`; `COHMON_SUMMARY` remains
reserved and continues to raise from `build_rehearsal_provenance`
(LOCK F).

The feedback step looks up the just-updated Pattern Ledger entry
by reading `self.pattern_ledger.find(seed_pattern_id)` where
`seed_pattern_id = derive_pattern_id(derive_pattern_signature(
seed_chunk))`. This is a pure read; no mutation occurs outside
the standard `_append_stream_chunk` call site.

---

## 2. Exact files

### 2.1 Modified

```text
brain/development/processing_window.py
    - widen _V1_EMITTED_SOURCES to {REHEARSAL, PLEDGER_SUMMARY}
    - add FeedbackMode (str, Enum) with members OFF, PATTERN_LEDGER
    - add validate_feedback_mode(value) -> FeedbackMode
    - add build_pledger_summary_text(entry) -> str (deterministic
      template per LOCK C)
    - extend MODULE_PRODUCED_STRINGS with the new bounded printable
      constants the helper produces
    - update module docstring + __all__

brain/ui/session.py
    - import FeedbackMode, validate_feedback_mode,
      build_pledger_summary_text
    - add OperatorSession.feedback_mode: FeedbackMode = FeedbackMode.OFF
    - add feedback_mode to _ALLOWED_SESSION_ATTRS
    - call validate_feedback_mode(self.feedback_mode) in __post_init__
    - extend _run_processing_window to interleave a feedback chunk
      after each rehearsal when feedback_mode == PATTERN_LEDGER
    - look up the just-updated Pattern Ledger entry by pattern_id
      and pass it to build_pledger_summary_text
    - on a None return from the feedback _append_stream_chunk call,
      abort the window cleanly (mirrors the existing rehearsal
      failure semantics)

brain/ui/fixtures/persistence_observe_resource_audit.py
    - add _PHASE_3_19_SESSION_ATTRS = frozenset({"feedback_mode"})
    - fold into the allowed union compared against _ALLOWED_SESSION_ATTRS

brain/ui/fixtures/persistence_ops_resource_audit.py
    - mirror the same _PHASE_3_19_SESSION_ATTRS tier

brain/invariants.py
    - register two new fixture modules:
        brain.ui.fixtures.internal_feedback_integration       (REQUIRED)
        brain.ui.fixtures.internal_feedback_static_audit      (STRUCTURAL)

INVARIANT_CATALOG.md
    - version banner v0.26 -> v0.27
    - count banner 282/89/14/15/16 -> 283/90/14/15/16
    - add the v0.27 catalog-history entry
    - update I-PWND-02 body: v1-emitted source set widens to
      include PLEDGER_SUMMARY; COHMON_SUMMARY remains reserved
      and continues to raise; build_rehearsal_provenance over the
      new emit set must still produce non-claim-clean bounded
      printable strings
    - add I-IFBK-01 row (REQUIRED) covering the integration
      behavior
    - add I-IFBK-02 row (STRUCTURAL) covering FeedbackMode +
      build_pledger_summary_text + non-claim audit
    - add the two fixtures' rows in the fixture index footer
    - update the catalog header text near "v0.27"

brain/_catalog_ids.py
    - regenerate via `python3 -m tools.catalog generate-ids`
      after the catalog edit

tools/catalog.py
    - bump EXPECTED_COUNTS to {REQUIRED: 283, STRUCTURAL: 90,
      NOT-EXERCISED: 14, DEFERRED: 15, OBSERVED: 16}
    - update the v0.26 -> v0.27 banner comment

README.md
    - update catalog version banner (v0.26 -> v0.27) and counts
    - add the v0.27 catalog-history entry summarizing the
      Phase 3.19 Internal Feedback Loop addition

CURRENT_MISSION.md / CURRENT_CAMPAIGN.md
    - reflect the v0.27 catalog when Step 7 lands the patch
      (mission/campaign baseline updates)
```

### 2.2 New fixtures

```text
brain/ui/fixtures/internal_feedback_static_audit.py
    - asserts FeedbackMode is a closed (str, Enum) with exactly
      {OFF, PATTERN_LEDGER}
    - asserts validate_feedback_mode rejects non-FeedbackMode
      input, accepts FeedbackMode members
    - asserts build_pledger_summary_text is a pure function:
        * returns a bounded printable str of len <
          STREAM_TEXT_MAX_LEN for a representative input set;
        * output contains no COGITO_ID;
        * output contains no _FORBIDDEN_NON_CLAIM_TERMS term
          (case-insensitive);
        * same input -> same output across two invocations.
    - asserts InternalEventSource._V1_EMITTED_SOURCES (read via
      the public module-level set if exposed, else inferred from
      build_rehearsal_provenance behavior) includes REHEARSAL and
      PLEDGER_SUMMARY; COHMON_SUMMARY remains reserved (raises).
    - asserts MODULE_PRODUCED_STRINGS still contains every
      InternalEventSource value and the new constants introduced
      by build_pledger_summary_text.
    - asserts the canonical _FORBIDDEN_NON_CLAIM_TERMS audit
      passes on every produced string at the helper level.

brain/ui/fixtures/internal_feedback_integration.py
    - runs full integration scenarios:
        N = 0   feedback_mode = PATTERN_LEDGER
                  -> strict no-op (window OFF);
        N = 5   feedback_mode = PATTERN_LEDGER
                  -> 1 + 5 rehearsal + 5 feedback = 11 chunks;
                     2 Pattern Ledger entries; recurrence on each
                     bounded;
        N = 10  feedback_mode = PATTERN_LEDGER
                  -> 1 + 10 + 10 = 21 chunks; 2+ entries (the
                     summary text may produce multiple
                     structurally distinct signatures across
                     feedback steps; assert >= 2 entries and that
                     every entry's invariants hold);
        N = 50  feedback_mode = PATTERN_LEDGER
                  -> 1 + 50 + 50 = 101 chunks; same invariants;
        N = 5   feedback_mode = OFF
                  -> exactly the Phase 3.18 behavior (1 entry,
                     1 + 5 chunks, no pledger_summary provenance
                     appears).
    - asserts assert_state_invariants(state) remains green.
    - asserts cache counters are unchanged (no L1 / L2 writes).
    - asserts cumulative real model calls = 0.
    - asserts two independent sessions with identical inputs
      produce identical Pattern Ledger entry sets, per-entry
      recurrence counts, and per-entry pattern_id values.
```

---

## 3. Row family

### 3.1 I-IFBK-01 (REQUIRED)

```text
Source: Engineering hypothesis (Phase 3.19 Internal Feedback Loop)
Status: REQUIRED
Module: brain/development/processing_window.py, brain/ui/session.py
Fixture: brain/ui/fixtures/internal_feedback_integration.py

Proposition (one sentence): When OperatorSession is constructed
with feedback_mode=FeedbackMode.PATTERN_LEDGER and
processing_window_size=N, a successful external STREAM_APPEND
followed by the processing window produces exactly 1 + 2 * N
stream chunks (one operator chunk + N rehearsal chunks + N
pledger_summary chunks), the Pattern Ledger ends with at least
one second-order entry whose pattern_id differs from the seed
pattern_id, every entry's constructor invariants hold, the seed
entry's recurrence_count equals min(STREAM_PATTERN_RECURRENCE_MIN
+ N, STREAM_PATTERN_RECURRENCE_MAX), the summary entry's combined
recurrence accounting equals N (split across however many distinct
signatures the deterministic template produced), cumulative real
model calls remain 0, and two independent sessions with identical
inputs / config produce identical Pattern Ledger entry sets.

At N = 0, the feedback path is a strict no-op (the loop returns 0)
and Pattern Ledger behavior is bit-identical to Phase 3.18's
N = 0 baseline.

At feedback_mode = FeedbackMode.OFF, the path is bit-identical
to the Phase 3.18 rehearsal-only baseline.
```

### 3.2 I-IFBK-02 (STRUCTURAL)

```text
Source: Engineering hypothesis (Phase 3.19 Internal Feedback Loop)
Status: STRUCTURAL
Module: brain/development/processing_window.py
Fixture: brain/ui/fixtures/internal_feedback_static_audit.py

Proposition (one sentence): FeedbackMode is a closed
(str, Enum) with exactly the members {OFF, PATTERN_LEDGER};
validate_feedback_mode rejects every non-FeedbackMode value
including bool and str; build_pledger_summary_text is a pure
deterministic function returning bounded printable strings under
STREAM_TEXT_MAX_LEN that contain no COGITO_ID and no
_FORBIDDEN_NON_CLAIM_TERMS term (case-insensitive); the v1
emit set for build_rehearsal_provenance widens to include
PLEDGER_SUMMARY (the previously reserved member); COHMON_SUMMARY
remains reserved and continues to raise ValueError;
MODULE_PRODUCED_STRINGS extends to include every new bounded
printable constant the helper produces; the static AST audit
(carried by I-PWND-02) still passes against the widened module
without introducing any forbidden import or dynamic-execution
call.
```

### 3.3 Row body update: I-PWND-02

Phase 3.18's I-PWND-02 body locks `InternalEventSource` value set
to `{"rehearsal", "pledger_summary", "cohmon_summary"}` (unchanged)
and locks the v1-emit set to `{REHEARSAL}`. Phase 3.19 updates the
second clause: the v1-emit set widens to
`{REHEARSAL, PLEDGER_SUMMARY}`; `COHMON_SUMMARY` still raises.

The widened audit also asserts that
`build_rehearsal_provenance(..., source=InternalEventSource.PLEDGER_SUMMARY)`
produces bounded printable strings under
`STREAM_PROVENANCE_MAX_LEN` that contain no
`_FORBIDDEN_NON_CLAIM_TERMS` term, for the representative
`tick_index` set `{1, 2, 3, 42, 255}`.

`build_rehearsal_provenance(..., source=InternalEventSource.COHMON_SUMMARY)`
must still raise `ValueError`.

This is a **body-text update** to an existing row, not a re-
classification (status remains STRUCTURAL).

---

## 4. Catalog version + counts

```text
Catalog version banner:
  v0.26 -> v0.27

Count banner:
  REQUIRED      : 282 -> 283  (+I-IFBK-01)
  STRUCTURAL    :  89 ->  90  (+I-IFBK-02)
  NOT-EXERCISED :  14 ->  14  (unchanged)
  DEFERRED      :  15 ->  15  (unchanged)
  OBSERVED      :  16 ->  16  (unchanged)
  fixtures      : 166 -> 168  (+internal_feedback_static_audit.py,
                               +internal_feedback_integration.py)
```

`tools/catalog.py EXPECTED_COUNTS` and the README catalog-history
entry must agree exactly with these numbers.

---

## 5. Fixture-side change inventory

```text
brain/ui/fixtures/internal_feedback_static_audit.py  : NEW
brain/ui/fixtures/internal_feedback_integration.py   : NEW
brain/ui/fixtures/persistence_observe_resource_audit.py : MODIFIED
  (+ _PHASE_3_19_SESSION_ATTRS = frozenset({"feedback_mode"}))
brain/ui/fixtures/persistence_ops_resource_audit.py  : MODIFIED
  (+ mirrored _PHASE_3_19_SESSION_ATTRS tier)
brain/ui/fixtures/processing_window_static_audit.py  : MODIFIED
  (widen the v1-emit-set assertion to include PLEDGER_SUMMARY;
   widen the build_rehearsal_provenance probe set; keep
   COHMON_SUMMARY raising)
brain/ui/fixtures/processing_window_integration.py   : OPTIONALLY
                                                       MODIFIED if
                                                       a regression
                                                       fix is
                                                       required;
                                                       expected:
                                                       unchanged
                                                       because the
                                                       default
                                                       feedback_mode
                                                       is OFF so
                                                       the existing
                                                       integration
                                                       fixture's
                                                       behavior is
                                                       preserved
                                                       bit-for-bit.
```

---

## 6. Behavior report plan (preview of Step 8)

The Step 8 harness exercises the 40-cell probe matrix from Step 3
plus a determinism re-run. The harness lives at
`/tmp/phase3_19_internal_feedback_demo.py` and is NOT committed.
The behavior report doc records:

```text
- the 40 cells' measurements (m01..m20);
- the determinism re-run results;
- the cumulative real model call count (= 0);
- the cumulative cache counter delta (= 0);
- the kernel invariant gate result (PASS expected);
- a per-mode verdict (M0 PASS / M1 PASS / M2 DEFERRED / M3 DEFERRED).
```

The harness uses only the public surfaces:

```text
OperatorSession(state=initial_state(),
                processing_window_size=N,
                feedback_mode=FeedbackMode.PATTERN_LEDGER)
session.dispatch(Command(STREAM_APPEND, payload=StreamAppendPayload(text=T)))
session.pattern_ledger
session.growth_ledger
session.stream_history
brain.tick.assert_state_invariants
build_coherence_report  (post-window inspection only)
```

No real model calls. No I/O outside the repo. `brain/.llm_cache`
not touched.

---

## 7. Non-goals (carryover from corrigenda)

```text
- no brain/tick.py edit
- no brain/llm/** edit
- no brain/tlica/** edit
- no Pattern / Coherence / Growth Ledger module semantic change
- no schema change / SCHEMA_VERSION bump
- no autosave change
- no parser / prompt change
- no L1 / L2 cache semantic change
- no UI verb / OperatorCommand / ACTIVE_VIEWS change
- no new GrowthEventType
- no new GrowthEventSource
- no FEEDBACK_MODE_COHERENCE in v1
- no SelfModel
- no aggregate consciousness / sentience / awareness / I-ness /
  growth score
- no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim
```

---

## 8. Validation plan

Before commit at every step that lands files:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

If `gate_runner` itself errors:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Step 7 additionally runs the new behavior harness once
(see Section 6) to confirm the integration fixture's assertions
match observed runtime behavior before commit.

Step 8 re-runs the harness for the report.

Step 10 runs the canonical preflight one more time and records
the result in the audit doc.

---

## 9. Review gate decision request

This patch plan is the artifact Step 6 Review Gate A evaluates
against the autonomy authorization checklist:

```text
1. zero critical correctness blockers
   -> the patch reuses existing helpers; no semantic change in
      Pattern / Coherence / Growth Ledger; no kernel touch.
2. zero safety / invariant blockers
   -> every produced string is non-claim audited; every
      constructor enforces bounded shapes.
3. no brain/tick.py edit
   -> confirmed (LOCK H).
4. preserves L1 / L2 cache semantics
   -> the feedback path uses STREAM_APPEND which is non-LLM
      and non-cached; both L1 and L2 caches are untouched.
5. preserves OFFLINE default + explicit opt-in
   -> the feedback path makes no LLM call regardless of mode.
6. exact row family / statuses / count delta / fixture list /
   implementation files / validation plan
   -> see Sections 2, 3, 4, 5, 8 above.
7. bounded internal-feedback design
   -> LOCK A + LOCK B + LOCK C; one new closed enum, one new
      pure helper, one new optional session field.
8. no cognitive overclaims
   -> LOCK I + the non-claim audit on every produced string.
9. Stage A review identifies no blocking flaw
   -> Stage A not used in Phase 3.19 by default; operator may
      escalate before Step 6 if desired.
10. implementation fits the allowed file set
   -> see Section 2.1; no file outside the named set is
      touched.
```

If the Step 6 review gate ACCEPTS this plan, the campaign proceeds
to Step 7. If the gate identifies a blocker, the campaign stops
at Step 6 and reports.

---

## 10. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the patch plan is derivable from the synthesis +
  probe matrix + corrigenda + existing repo state; no external
  review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard; bridge overhead exceeds direct
  write cost.
```

---

## 11. Next artifact

`Step 6 Review Gate A` — record the gate decision in the campaign
ledger (this doc + the Step 6 commit message) and, on ACCEPT,
proceed to Step 7 implementation.
