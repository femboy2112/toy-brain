# PHASE3_20_COHERENCE_FEEDBACK_CATALOG_PATCH_PLAN.md

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
2. **if** `self.feedback_mode in {FeedbackMode.PATTERN_LEDGER,
   FeedbackMode.PATTERN_AND_COHERENCE}`, one **pledger_summary**
   chunk (Phase 3.19 behavior, unchanged);
3. **if** `self.feedback_mode in {FeedbackMode.COHERENCE,
   FeedbackMode.PATTERN_AND_COHERENCE}`, one **cohmon_summary**
   chunk — `_append_stream_chunk(
   text=build_cohmon_summary_text(<bounded primitives from
   build_full_coherence_report>),
   chunk_provenance="internal_processing_window:<k>:cohmon_summary",
   ...)`.

`build_cohmon_summary_text` is a new pure function on
`brain/development/processing_window.py` whose deterministic
output is `"cohmon_summary overall=<status> pass=<np> warn=<nw>
fail=<nf> na=<nna> checks=<nc>"` (LOCK C). `FeedbackMode` gains
two new members `COHERENCE` and `PATTERN_AND_COHERENCE` (LOCK
D). `_V1_EMITTED_SOURCES` widens to include
`InternalEventSource.COHMON_SUMMARY` so
`build_rehearsal_provenance(..., source=COHMON_SUMMARY)` no
longer raises and instead composes a bounded printable
non-claim-clean provenance.

The cohmon_summary step calls `build_full_coherence_report(self,
snapshot_id=f"coh-snap-{tick_index}")` via a **deferred
function-body import** inside `_run_cohmon_feedback_step`. The
import lives inside the function body to avoid a circular load
with `brain.development.coherence_monitor` (which already imports
`brain.ui.session.OperatorSession` at module load). The bounded
primitives extracted from the live `CoherenceReport` are passed
into `build_cohmon_summary_text` — `processing_window.py` itself
never imports `coherence_monitor`.

---

## 2. Exact files

### 2.1 Modified

```text
brain/development/processing_window.py
    - widen _V1_EMITTED_SOURCES to
      {REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}
    - extend FeedbackMode with COHERENCE = "coherence" and
      PATTERN_AND_COHERENCE = "pattern_and_coherence"
    - extend _FEEDBACK_MODE_VALID accordingly
    - add COHMON_SUMMARY_TEXT_PREFIX = "cohmon_summary"
    - add COHMON_SUMMARY_TEXT_MAX_LEN = 160
    - add the closed-set constant
      _COHMON_SUMMARY_VALID_OVERALL_STATUS_VALUES =
      frozenset({"pass", "warn", "fail", "not_applicable"})
    - add build_cohmon_summary_text(*, overall_status_value,
      pass_count, warn_count, fail_count, na_count, check_count)
      -> str
        validation order (mirrors build_pledger_summary_text):
          1. overall_status_value is str, non-empty, printable,
             in the valid set, not equal to COGITO_ID
          2-5. each count is int (not bool), 0 <= count <= 64
          6. check_count == pass_count + warn_count + fail_count + na_count
          7. composed text length <= COHMON_SUMMARY_TEXT_MAX_LEN
          8. composed text length <= STREAM_TEXT_MAX_LEN
          9. composed text bounded printable and not equal to COGITO_ID
    - extend MODULE_PRODUCED_STRINGS with
      COHMON_SUMMARY_TEXT_PREFIX,
      InternalEventSource.COHMON_SUMMARY.value (already present),
      FeedbackMode.COHERENCE.value,
      FeedbackMode.PATTERN_AND_COHERENCE.value
    - extend __all__ with build_cohmon_summary_text,
      COHMON_SUMMARY_TEXT_MAX_LEN, COHMON_SUMMARY_TEXT_PREFIX
    - update module docstring to reference Phase 3.20 + I-CFBK-01
      / I-CFBK-02

brain/ui/session.py
    - import is unchanged at module level (no new top-level
      import of coherence_monitor)
    - extend _run_processing_window:
        compute pledger_feedback_enabled = (feedback_mode in
            {PATTERN_LEDGER, PATTERN_AND_COHERENCE})
        compute cohmon_feedback_enabled  = (feedback_mode in
            {COHERENCE, PATTERN_AND_COHERENCE})
        compute seed_pattern_id only if pledger_feedback_enabled
        for each rehearsal step:
          if pledger_feedback_enabled:
            _run_feedback_step(...) (existing helper)
          if cohmon_feedback_enabled:
            _run_cohmon_feedback_step(tick_index=step.tick_index)
    - add _run_cohmon_feedback_step(*, tick_index: int) -> bool:
        from brain.development.coherence_monitor import (
            build_full_coherence_report,
        )  # deferred to avoid module-load cycle
        report = build_full_coherence_report(self,
                   snapshot_id=f"coh-snap-{tick_index}")
        # tally per-status counts deterministically
        counts = {status_value: 0 for status_value in
                    ("pass", "warn", "fail", "not_applicable")}
        for label, count in report.counts_by_status:
          counts[label] = count
        try:
          summary_text = build_cohmon_summary_text(
            overall_status_value=report.overall_status.value,
            pass_count=counts["pass"],
            warn_count=counts["warn"],
            fail_count=counts["fail"],
            na_count=counts["not_applicable"],
            check_count=len(report.snapshot.checks),
          )
          summary_provenance = build_rehearsal_provenance(
            tick_index=tick_index,
            source=InternalEventSource.COHMON_SUMMARY,
          )
        except (TypeError, ValueError) as exc:
          self.set_error(f"processing window cohmon feedback rejected: {exc}")
          return False
        chunk = self._append_stream_chunk(
          text=summary_text,
          chunk_provenance=summary_provenance,
          growth_provenance="stream_append:_run_processing_window",
        )
        return chunk is not None

brain/invariants.py
    - register two new fixture modules:
        brain.ui.fixtures.coherence_feedback_integration       (REQUIRED)
        brain.ui.fixtures.coherence_feedback_static_audit      (STRUCTURAL)

INVARIANT_CATALOG.md
    - version banner v0.27 -> v0.28
    - count banner 283/90/14/15/16 -> 284/91/14/15/16
    - add the v0.28 catalog-history entry
    - update I-PWND-02 body: v1-emitted source set widens to
      include COHMON_SUMMARY; build_rehearsal_provenance over
      COHMON_SUMMARY produces a non-claim-clean bounded
      provenance; COHMON_SUMMARY is no longer reserved
    - update I-IFBK-02 body: replace the COHMON_SUMMARY-raises
      assertion with a COHMON_SUMMARY-emits-non-claim-clean
      assertion; widen the build_rehearsal_provenance probe set
      to include COHMON_SUMMARY; widen the FeedbackMode value
      set to {"off", "pattern_ledger", "coherence",
      "pattern_and_coherence"}; widen the MODULE_PRODUCED_STRINGS
      expected subset to include COHMON_SUMMARY_TEXT_PREFIX and
      the two new FeedbackMode values
    - add I-CFBK-01 row (REQUIRED) covering the integration
      behavior across the four modes
    - add I-CFBK-02 row (STRUCTURAL) covering FeedbackMode
      widened membership, build_cohmon_summary_text constructor
      + non-claim + determinism audit, _V1_EMITTED_SOURCES
      widened, and MODULE_PRODUCED_STRINGS extension
    - add the two fixtures' rows in the fixture index footer
    - update the catalog header text near "v0.28"

brain/_catalog_ids.py
    - regenerate via `python3 -m tools.catalog generate-ids`
      after the catalog edit

tools/catalog.py
    - bump EXPECTED_COUNTS to {REQUIRED: 284, STRUCTURAL: 91,
      NOT-EXERCISED: 14, DEFERRED: 15, OBSERVED: 16}
    - update the v0.27 -> v0.28 banner comment

README.md
    - update catalog version banner (v0.27 -> v0.28) and counts
    - add the v0.28 catalog-history entry summarizing the
      Phase 3.20 Coherence Feedback Bridge addition

CURRENT_MISSION.md / CURRENT_CAMPAIGN.md
    - reflect the v0.28 catalog when Step 7 lands the patch
      (mission/campaign baseline updates)
```

### 2.2 New fixtures

```text
brain/ui/fixtures/coherence_feedback_static_audit.py    (NEW; I-CFBK-02; STRUCTURAL)
    - asserts FeedbackMode value set is exactly
      {"off", "pattern_ledger", "coherence", "pattern_and_coherence"}
    - asserts validate_feedback_mode accepts every member and
      rejects non-FeedbackMode input (bool, int, str, None,
      object())
    - asserts InternalEventSource value set is unchanged
      {"rehearsal", "pledger_summary", "cohmon_summary"}
    - asserts build_rehearsal_provenance(tick_index=k,
      source=InternalEventSource.COHMON_SUMMARY) for
      k in {1, 2, 3, 42, 255} produces strings that are bounded
      printable, under STREAM_PROVENANCE_MAX_LEN, contain no
      COGITO_ID, contain no forbidden non-claim term
    - asserts build_cohmon_summary_text is pure deterministic:
        * returns a bounded printable str of len <
          COHMON_SUMMARY_TEXT_MAX_LEN for a representative
          input set;
        * output starts with "cohmon_summary ";
        * output contains no COGITO_ID;
        * output contains no _FORBIDDEN_NON_CLAIM_TERMS term
          (case-insensitive);
        * same input -> same output across two invocations.
    - asserts bounded-shape rejections on
      build_cohmon_summary_text:
        * non-str / empty / non-printable / COGITO_ID
          overall_status_value;
        * unknown overall_status_value;
        * non-int / bool / negative / over-cap counts;
        * check_count != sum of per-status counts.
    - asserts MODULE_PRODUCED_STRINGS now contains
      COHMON_SUMMARY_TEXT_PREFIX, FeedbackMode.COHERENCE.value,
      FeedbackMode.PATTERN_AND_COHERENCE.value; every entry is
      non-claim-clean.

brain/ui/fixtures/coherence_feedback_integration.py     (NEW; I-CFBK-01; REQUIRED)
    - runs full integration scenarios:
        N = 0   feedback_mode = COHERENCE
                  -> strict no-op (1 chunk, 1 entry);
        N = 0   feedback_mode = PATTERN_AND_COHERENCE
                  -> strict no-op (1 chunk, 1 entry);
        N = 5/10/50  feedback_mode = OFF
                  -> bit-identical to Phase 3.18 baseline
                     (1 + N chunks, 1 entry, no pledger_summary
                     or cohmon_summary provenance);
        N = 5/10/50  feedback_mode = PATTERN_LEDGER
                  -> bit-identical to Phase 3.19 baseline
                     (1 + 2N chunks, no cohmon_summary
                     provenance);
        N = 5/10/50  feedback_mode = COHERENCE
                  -> exactly 1 + 2N chunks (1 op + N rehearsal +
                     N cohmon_summary); >= 2 pattern entries;
                     sum over cohmon-family entries of
                     (recurrence_count - MIN + 1) == N; no
                     pledger_summary provenance;
        N = 5/10/50  feedback_mode = PATTERN_AND_COHERENCE
                  -> exactly 1 + 3N chunks (1 op + N rehearsal +
                     N pledger_summary + N cohmon_summary);
                     >= 3 pattern entries; pledger-family sum
                     == N and cohmon-family sum == N
                     separately.
    - asserts assert_state_invariants(state) remains green.
    - asserts no L1 / L2 cache write occurs.
    - asserts cumulative real model calls = 0.
    - asserts two independent sessions with identical inputs +
      mode produce identical Pattern Ledger entry pattern_id
      tuples, identical per-entry recurrence_count tuples, and
      identical Growth Ledger event_id tuples (determinism).
    - asserts COHMON_SUMMARY no longer raises from
      build_rehearsal_provenance.
```

---

## 3. Row family

### 3.1 I-CFBK-01 (REQUIRED)

```text
Source: Engineering hypothesis (Phase 3.20 Coherence Feedback Bridge)
Status: REQUIRED
Module: brain/development/processing_window.py, brain/ui/session.py
Fixture: brain/ui/fixtures/coherence_feedback_integration.py

Proposition (one sentence): When OperatorSession is constructed
with feedback_mode in {FeedbackMode.COHERENCE,
FeedbackMode.PATTERN_AND_COHERENCE} and processing_window_size=N,
a successful external STREAM_APPEND followed by the processing
window produces, respectively, 1 + 2 * N or 1 + 3 * N stream
chunks; the Pattern Ledger ends with at least 2 entries
(COHERENCE) or at least 3 entries (PATTERN_AND_COHERENCE), each
second-order entry's pattern_id differs from the seed pattern_id,
every entry's constructor invariants hold, the seed entry's
recurrence_count equals min(STREAM_PATTERN_RECURRENCE_MIN + N,
STREAM_PATTERN_RECURRENCE_MAX), the sum over cohmon-family
entries of (recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1)
equals exactly N (one observation per cohmon_summary chunk), the
same sum over pledger-family entries equals exactly N under
PATTERN_AND_COHERENCE, assert_state_invariants(state) remains
green, cumulative real model calls remain 0, and two independent
fresh OperatorSession instances with identical inputs / config
produce identical Pattern Ledger entry sets and identical Growth
Ledger event id tuples (determinism).

At processing_window_size == 0, every feedback mode is a strict
no-op (one operator chunk; one Pattern Ledger entry at MIN). At
feedback_mode == FeedbackMode.OFF, the path is bit-identical to
the Phase 3.18 rehearsal-only baseline. At feedback_mode ==
FeedbackMode.PATTERN_LEDGER, the path is bit-identical to the
Phase 3.19 baseline (no cohmon_summary provenance appears).
```

### 3.2 I-CFBK-02 (STRUCTURAL)

```text
Source: Engineering hypothesis (Phase 3.20 Coherence Feedback Bridge)
Status: STRUCTURAL
Module: brain/development/processing_window.py
Fixture: brain/ui/fixtures/coherence_feedback_static_audit.py

Proposition (one sentence): FeedbackMode is a closed
(str, Enum) with exactly the members {OFF, PATTERN_LEDGER,
COHERENCE, PATTERN_AND_COHERENCE}; validate_feedback_mode
rejects every non-FeedbackMode value including bool and str;
build_cohmon_summary_text is a pure deterministic function
returning bounded printable strings under
COHMON_SUMMARY_TEXT_MAX_LEN == 160 (and under STREAM_TEXT_MAX_LEN)
that begin with "cohmon_summary " and contain no COGITO_ID and
no _FORBIDDEN_NON_CLAIM_TERMS term (case-insensitive); the
helper rejects non-str / empty / non-printable / COGITO_ID
overall_status_value, unknown overall_status_value,
non-int / bool / negative / over-cap counts, and any input
whose check_count differs from the sum of per-status counts; the
v1-emit set for build_rehearsal_provenance is exactly
{REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY} and
build_rehearsal_provenance(..., source=COHMON_SUMMARY) for
representative tick indices produces non-claim-clean bounded
provenances; MODULE_PRODUCED_STRINGS extends to include
COHMON_SUMMARY_TEXT_PREFIX, FeedbackMode.COHERENCE.value, and
FeedbackMode.PATTERN_AND_COHERENCE.value; the static AST audit
(carried by I-PWND-02) still passes against the widened module
without introducing any forbidden import or dynamic-execution
call.
```

### 3.3 Row body updates

`I-PWND-02` — widen the v1-emit set body from
`{REHEARSAL, PLEDGER_SUMMARY}` to
`{REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}`; update the probe
set to assert
`build_rehearsal_provenance(..., source=COHMON_SUMMARY)` for
`k in {1, 2, 3, 42, 255}` produces non-claim-clean bounded
strings. The audit's other clauses (import set, dynamic-execution
denylist, module-level statement restriction, COGITO_ID
exclusion, etc.) are unchanged. Status remains STRUCTURAL.

`I-IFBK-02` — replace the assertion
`build_rehearsal_provenance(..., source=COHMON_SUMMARY) raises
ValueError` with the new assertion that the same call now
produces a non-claim-clean bounded provenance. Widen the
FeedbackMode value-set assertion to
`{"off", "pattern_ledger", "coherence", "pattern_and_coherence"}`.
Widen the MODULE_PRODUCED_STRINGS expected-subset assertion to
include `COHMON_SUMMARY_TEXT_PREFIX` and the two new FeedbackMode
values. Status remains STRUCTURAL.

Both updates are **body-text updates** to existing rows; no
status change, no row-count change attributable to them.

---

## 4. Catalog version + counts

```text
Catalog version banner:
  v0.27 -> v0.28

Count banner:
  REQUIRED      : 283 -> 284  (+I-CFBK-01)
  STRUCTURAL    :  90 ->  91  (+I-CFBK-02)
  NOT-EXERCISED :  14 ->  14  (unchanged)
  DEFERRED      :  15 ->  15  (unchanged)
  OBSERVED      :  16 ->  16  (unchanged)
  fixtures      : 168 -> 170  (+coherence_feedback_static_audit.py,
                               +coherence_feedback_integration.py)
```

`tools/catalog.py EXPECTED_COUNTS` and the README catalog-history
entry must agree exactly with these numbers.

---

## 5. Fixture-side change inventory

```text
brain/ui/fixtures/coherence_feedback_static_audit.py  : NEW
brain/ui/fixtures/coherence_feedback_integration.py   : NEW
brain/ui/fixtures/internal_feedback_static_audit.py   : MODIFIED
  (widen the FeedbackMode value-set assertion to four members;
   replace the COHMON_SUMMARY-raises assertion with the
   non-claim-clean emit assertion; widen the
   MODULE_PRODUCED_STRINGS expected subset)
brain/ui/fixtures/processing_window_static_audit.py  : MODIFIED
  (widen the v1-emit-set assertion to include COHMON_SUMMARY;
   widen the build_rehearsal_provenance probe set; remove the
   COHMON_SUMMARY-raises assertion)
brain/ui/fixtures/persistence_observe_resource_audit.py : NOT MODIFIED
  (feedback_mode is already in the Phase 3.19 attribute tier;
   no new session attribute is added in Phase 3.20)
brain/ui/fixtures/persistence_ops_resource_audit.py  : NOT MODIFIED
  (same reason)
brain/ui/fixtures/processing_window_integration.py   : NOT MODIFIED
  (default feedback_mode remains OFF; existing integration
   fixture's behavior is preserved bit-for-bit)
brain/ui/fixtures/internal_feedback_integration.py   : NOT MODIFIED
  (default feedback_mode argument paths in the helper remain
   bit-identical for OFF and PATTERN_LEDGER; no Phase 3.19
   integration check needs to widen)
```

---

## 6. Behavior report plan (preview of Step 8)

The Step 8 harness exercises the 80-cell probe matrix from Step 3
plus a determinism re-run. The harness lives at
`/tmp/phase3_20_coherence_feedback_demo.py` and is NOT committed.
The behavior report doc records:

```text
- the 80 cells' measurements (m01..m24);
- the determinism re-run results;
- the cumulative real model call count (= 0);
- the cumulative cache counter delta (= 0);
- the kernel invariant gate result (PASS expected);
- a per-mode verdict (OFF PASS / PATTERN_LEDGER PASS /
  COHERENCE PASS / PATTERN_AND_COHERENCE PASS).
```

The harness uses only the public surfaces:

```text
OperatorSession(state=initial_state(),
                processing_window_size=N,
                feedback_mode=<mode>)
session.dispatch(Command(STREAM_APPEND, payload=StreamAppendPayload(text=T)))
session.pattern_ledger
session.growth_ledger
session.stream_history
brain.tick.assert_state_invariants
brain.development.coherence_monitor.build_full_coherence_report
brain.development.processing_window.build_cohmon_summary_text
brain.development.processing_window.build_rehearsal_provenance
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
- no SelfModel
- no aggregate consciousness / sentience / awareness / I-ness /
  coherence-feedback / growth score
- no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim
- no module-level import of coherence_monitor in
  brain/ui/session.py (deferred function-body import only)
- no import of coherence_monitor or session in
  brain/development/processing_window.py
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
       constructor enforces bounded shapes; check_count ==
       sum-of-counts cross-check is enforced.
 3. no brain/tick.py edit
    -> confirmed (LOCK H).
 4. preserves L1 / L2 cache semantics
    -> the feedback path uses STREAM_APPEND which is non-LLM
       and non-cached; both L1 and L2 caches are untouched.
 5. preserves parser and prompt semantics
    -> no parser or prompt edit is in scope.
 6. preserves OFFLINE default + explicit opt-in
    -> the feedback path makes no LLM call regardless of mode;
       LOCK I confirmed.
 7. exact row family / statuses / count delta / fixture list /
    implementation files / validation plan
    -> see Sections 2, 3, 4, 5, 8 above.
 8. bounded coherence-feedback design
    -> LOCK A + LOCK B + LOCK C + LOCK D; one new pure helper
       with deterministic bounded output; new closed enum
       members; deferred-import-only session helper.
 9. no cognitive overclaims
    -> LOCK J + the non-claim audit on every produced string;
       PASS/WARN/FAIL/NOT_APPLICABLE labels are structural
       statuses only.
10. Stage A review identifies no blocking flaw
    -> Stage A not used in Phase 3.20 by default; operator may
       escalate before Step 6 if desired.
11. implementation fits the allowed file set
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
