# PHASE3_20_COHERENCE_FEEDBACK_PROBE_MATRIX.md

## Purpose

Enumerate the 80 probe cells the Phase 3.20 behavior report
exercises after Step 7 lands the implementation, plus the
non-runtime probes Step 3 can complete now against the v0.27
runtime. Each cell records the bounded measurements Pattern
Ledger, Coherence Monitor, Growth Ledger, and the new feedback
helpers produce. Cells whose modes do not yet exist at v0.27 are
marked `runtime-blocked` and state exactly what surface is
missing.

The matrix follows the same axes Phase 3.19 used; the only new
axis is the new mode set `{OFF, PATTERN_LEDGER, COHERENCE,
PATTERN_AND_COHERENCE}` instead of `{OFF, PATTERN_LEDGER}`.

---

## 1. Axes

```text
window sizes (N) : 0, 5, 10, 50               (4 values)
modes            : OFF
                   PATTERN_LEDGER
                   COHERENCE                  (Phase 3.20 v1 target)
                   PATTERN_AND_COHERENCE      (Phase 3.20 v1 if LOCK D
                                              bundles; else planned)
                                              (4 values)
inputs           : repeated motif
                   contradiction pair
                   self-reference phrase
                   neutral factual text
                   emotionally valenced text  (5 values)
total cells      : 4 * 4 * 5 = 80
```

### 1.1 Input family canonical seed texts

The Step 8 harness uses fixed deterministic seeds:

```text
repeated motif         : "the kettle whistled at exactly noon today again"
contradiction pair     : "the lamp is both on and off at exactly the same time"
self-reference phrase  : "this sentence has six words"
neutral factual text   : "water boils at 100 degrees celsius at standard pressure"
emotionally valenced   : "the room was warm and quiet and felt safe to stay in"
```

These seeds are bounded printable, well under
`STREAM_TEXT_MAX_LEN = 1024`, contain no `COGITO_ID`, and contain
no `_FORBIDDEN_NON_CLAIM_TERMS` term. They are not committed to
the repo as fixtures; the harness embeds them at runtime.

### 1.2 Per-mode chunk-count formula (deterministic, locked)

```text
OFF                      : 1 + N           (chunks per dispatch)
PATTERN_LEDGER           : 1 + 2N
COHERENCE                : 1 + 2N
PATTERN_AND_COHERENCE    : 1 + 3N
```

### 1.3 Per-mode minimum Pattern Ledger entry count

```text
OFF                      : 1               (seed only)
PATTERN_LEDGER           : >= 2            (seed + pledger_summary family)
COHERENCE                : >= 2            (seed + cohmon_summary family)
PATTERN_AND_COHERENCE    : >= 3            (seed + both families)
```

The actual entry count under `COHERENCE` and
`PATTERN_AND_COHERENCE` may be larger than 2 / 3 because the
coherence-summary text varies as counts shift (so each step can
produce a distinct second-order signature). The matrix records
the actual observed count.

---

## 2. Measurements per cell

For every cell the Step 8 harness records:

```text
m01 stream_chunk_count                 : len(session.stream_history.chunks)
m02 rehearsal_chunk_count              : count chunks whose provenance ends in ":rehearsal"
m03 pledger_summary_chunk_count        : count chunks whose provenance ends in ":pledger_summary"
m04 cohmon_summary_chunk_count         : count chunks whose provenance ends in ":cohmon_summary"
m05 pattern_ledger_entry_count         : len(session.pattern_ledger.entries)
m06 first_order_recurrence_count       : seed_entry.recurrence_count
m07 first_order_confidence             : seed_entry.confidence (Fraction)
m08 first_order_saturation_state       : seed_entry.saturation_state.value
m09 pledger_family_entry_count         : count entries whose pattern_id != seed and whose
                                         signature is derived from build_pledger_summary_text output
m10 cohmon_family_entry_count          : count entries whose pattern_id != seed and whose
                                         signature is derived from build_cohmon_summary_text output
m11 sum_pledger_family_recurrence      : sum of (recurrence_count - MIN + 1) over pledger family
m12 sum_cohmon_family_recurrence       : sum of (recurrence_count - MIN + 1) over cohmon family
m13 growth_ledger_event_count          : len(session.growth_ledger.events)
m14 growth_event_types                 : sorted unique event_type values seen
m15 coherence_report_overall_status    : build_full_coherence_report(session).overall_status.value
m16 coherence_report_counts_by_status  : tuple of (status_value, count) pairs
m17 real_model_call_count              : explicitly 0 (no LLM seam touched)
m18 l1_cache_writes                    : 0 (no LLMClient invoked)
m19 l2_cache_writes                    : 0
m20 assert_state_invariants_status     : PASS / FAIL
m21 nonclaim_audit_status              : PASS / FAIL (forbidden-term scan over all produced text)
m22 import_audit_status                : PASS / FAIL (I-PWND-02 + I-COHMON-10)
m23 invariant_runner_status            : PASS / FAIL (python3 -m brain.invariants run summary)
m24 deterministic_reproduction         : PASS iff two independent sessions with the same
                                         (N, mode, input) produce bit-identical
                                         (pattern_id tuple, recurrence_count tuple,
                                          growth_event_id tuple)
```

For `OFF` and `PATTERN_LEDGER` modes, m04 and m12 are expected to be
0 (no coherence-summary chunks). For `OFF` mode, m03 / m11 are
also 0.

---

## 3. Cell status legend

```text
DONE          measurement is computable today and the value is known
              (Step 3 of Phase 3.20 records the value or the formula)
PROBE-NOW     measurement is computable today against the v0.27 runtime
              even though the mode doesn't exist; the harness uses
              the OFF / PATTERN_LEDGER baselines and a deterministic
              call to build_full_coherence_report to predict the
              post-implementation values
RUNTIME-BLOCKED  the cell needs FeedbackMode.COHERENCE or
              FeedbackMode.PATTERN_AND_COHERENCE which is not yet
              shipped; will be measured in Step 8 after Step 7
              lands the implementation
```

Per-mode summary at Phase 3.20 Step 3:

```text
OFF                       all 20 cells DONE
PATTERN_LEDGER            all 20 cells DONE (Phase 3.19 baseline carried forward)
COHERENCE                 all 20 cells RUNTIME-BLOCKED
PATTERN_AND_COHERENCE     all 20 cells RUNTIME-BLOCKED
```

The runtime surface missing for COHERENCE and
PATTERN_AND_COHERENCE cells:

```text
- FeedbackMode.COHERENCE enum member does not exist yet
- FeedbackMode.PATTERN_AND_COHERENCE enum member does not exist yet
- build_cohmon_summary_text helper does not exist yet
- _V1_EMITTED_SOURCES does not yet include COHMON_SUMMARY
  (build_rehearsal_provenance still raises for it)
- OperatorSession._run_cohmon_feedback_step helper does not exist yet
- _run_processing_window does not yet branch on COHERENCE or
  PATTERN_AND_COHERENCE
```

Step 7 ships exactly these surfaces.

---

## 4. Cell table

The full 80-cell table is summarized per (mode, N) since
input-family variation does not change the count formulas (only
the seed signature changes and therefore the pattern_id values).

### 4.1 OFF mode (Phase 3.18 baseline; all DONE)

| N  | m01 | m02 | m03 | m04 | m05 | m06       | m13 (typ) | m15  | m20 | m24 |
|----|-----|-----|-----|-----|-----|-----------|-----------|------|-----|-----|
| 0  | 1   | 0   | 0   | 0   | 1   | MIN       | 2         | pass | PASS| PASS|
| 5  | 6   | 5   | 0   | 0   | 1   | MIN+5     | ~7        | pass | PASS| PASS|
| 10 | 11  | 10  | 0   | 0   | 1   | MIN+10    | ~12       | pass | PASS| PASS|
| 50 | 51  | 50  | 0   | 0   | 1   | MIN+50    | ~52       | pass | PASS| PASS|

`m15` is `pass` because every fresh session at OFF satisfies the
kernel / session / stream / pledger / persistence checks. `m24`
is PASS because OFF is bit-deterministic (Phase 3.18 D3 result).

### 4.2 PATTERN_LEDGER mode (Phase 3.19 baseline; all DONE)

| N  | m01  | m02 | m03 | m04 | m05 | m06       | m11 | m13 (typ) | m20 | m24 |
|----|------|-----|-----|-----|-----|-----------|-----|-----------|-----|-----|
| 0  | 1    | 0   | 0   | 0   | 1   | MIN       | 0   | 2         | PASS| PASS|
| 5  | 11   | 5   | 5   | 0   | >=2 | MIN+5     | 5   | ~12       | PASS| PASS|
| 10 | 21   | 10  | 10  | 0   | >=2 | MIN+10    | 10  | ~22       | PASS| PASS|
| 50 | 101  | 50  | 50  | 0   | >=2 | MIN+50    | 50  | ~102      | PASS| PASS|

`m24` PASS is the Phase 3.19 I-IFBK-01 integration assertion;
two independent sessions with identical inputs produce identical
`(pattern_id, recurrence_count, growth_event_id)` tuples.

### 4.3 COHERENCE mode (Phase 3.20 target; all RUNTIME-BLOCKED)

Expected values once Step 7 lands:

| N  | m01  | m02 | m03 | m04 | m05 | m06       | m12       | m13 (typ) | m20  | m24  |
|----|------|-----|-----|-----|-----|-----------|-----------|-----------|------|------|
| 0  | 1    | 0   | 0   | 0   | 1   | MIN       | 0         | 2         | PASS | PASS |
| 5  | 11   | 5   | 0   | 5   | >=2 | MIN+5     | 5         | ~12       | PASS | PASS |
| 10 | 21   | 10  | 0   | 10  | >=2 | MIN+10    | 10        | ~22       | PASS | PASS |
| 50 | 101  | 50  | 0   | 50  | >=2 | MIN+50    | 50        | ~102      | PASS | PASS |

Notes:

- `m05` is `>=2` because the cohmon_summary text varies as
  per-status counts shift across steps; the actual count may be
  larger;
- `m12` ("sum cohmon family recurrence") is expected to equal
  exactly N because each cohmon_summary chunk contributes one
  observation;
- `m13` includes the additional `STREAM_CHUNK_ACCEPTED` events
  the new chunks produce plus the usual `PATTERN_ENTRY_CREATED /
  UPDATED` events;
- `m24` PASS is asserted by the new I-CFBK-01 row.

### 4.4 PATTERN_AND_COHERENCE mode (Phase 3.20 target if LOCK D bundles; all RUNTIME-BLOCKED)

Expected values once Step 7 lands:

| N  | m01  | m02 | m03 | m04 | m05 | m06       | m11 | m12 | m13 (typ) | m20  | m24  |
|----|------|-----|-----|-----|-----|-----------|-----|-----|-----------|------|------|
| 0  | 1    | 0   | 0   | 0   | 1   | MIN       | 0   | 0   | 2         | PASS | PASS |
| 5  | 16   | 5   | 5   | 5   | >=3 | MIN+5     | 5   | 5   | ~17       | PASS | PASS |
| 10 | 31   | 10  | 10  | 10  | >=3 | MIN+10    | 10  | 10  | ~32       | PASS | PASS |
| 50 | 151  | 50  | 50  | 50  | >=3 | MIN+50    | 50  | 50  | ~152      | PASS | PASS |

Notes:

- `m01` formula is `1 + 3N` (one external + N rehearsal + N
  pledger_summary + N cohmon_summary);
- `m05` is `>=3` (seed entry + pledger family + cohmon family);
- both `m11` and `m12` equal N respectively;
- `m24` PASS is asserted by I-CFBK-01 across the combined mode.

---

## 5. Step 3 non-runtime probes (computable today)

To increase Step 6 review-gate confidence, the matrix records
three probes that can run today against the v0.27 runtime even
without the Phase 3.20 implementation:

### Probe P1 — Coherence Monitor output stability on a fresh session

Goal: confirm that the Coherence Monitor produces a bounded
deterministic report on a freshly constructed `OperatorSession`
across all five input families (after one STREAM_APPEND) and
across all four window sizes (with `feedback_mode=OFF` only).

Today this is computable via:

```python
from brain.tick import initial_state
from brain.ui.session import OperatorSession
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.development.coherence_monitor import build_full_coherence_report

for text in INPUTS:
    for N in (0, 5, 10, 50):
        session = OperatorSession(state=initial_state(),
                                  processing_window_size=N)
        session.dispatch(Command(OperatorCommand.STREAM_APPEND,
                                 payload=StreamAppendPayload(text=text)))
        report = build_full_coherence_report(session)
        record(report.overall_status.value,
               report.counts_by_status,
               len(report.snapshot.checks))
```

Expected (predicted): every cell yields `overall_status == "pass"`,
`counts_by_status` totals to `len(report.snapshot.checks)`, and
the bounded printable summary_text length is well under
`MAX_SUMMARY_LEN = 240`.

Status today: **DONE BY DESIGN** — the matching invariants
I-COHMON-04..08 are PASS on every current fixture. Step 7's
harness re-confirms the same behavior holds inside
`_run_cohmon_feedback_step`.

### Probe P2 — bounded primitive ranges for build_cohmon_summary_text inputs

Goal: confirm the bounded ranges the new helper must accept
match the actual ranges the Coherence Monitor produces today.

From `build_full_coherence_report(...)` over any fresh
`OperatorSession`:

```text
overall_status_value  : in {"pass", "warn", "fail", "not_applicable"}
counts_by_status      : tuple of 4 (str, int) pairs whose ints sum
                        to len(snapshot.checks)
len(snapshot.checks)  : in [0, COHERENCE_MAX_CHECKS = 64]
```

Predicted maximum total summary text length:

```text
prefix      "cohmon_summary"                                          15
overall=    " overall=" + max("not_applicable")                      24
pass=       " pass=" + max("64")                                      8
warn=       " warn=" + max("64")                                      8
fail=       " fail=" + max("64")                                      8
na=         " na=" + max("64")                                        6
checks=     " checks=" + max("64")                                   10
sum                                                                  79
```

79 chars << `STREAM_TEXT_MAX_LEN = 1024` and well under the
new `COHMON_SUMMARY_TEXT_MAX_LEN = 160` cap the Step 5 patch plan
locks. PASS by construction.

Status today: **DONE BY DESIGN** — the Coherence Monitor's own
bounded constants enforce the ranges already.

### Probe P3 — non-claim audit on every helper input projection

Goal: confirm that every bounded primitive the helper accepts is
already non-claim-clean, so the produced text cannot contain a
forbidden term.

The four allowed `overall_status_value` strings are
`{"pass", "warn", "fail", "not_applicable"}`. None of these
contains any term in `_FORBIDDEN_NON_CLAIM_TERMS`. The bounded
small-integer counts contribute only ASCII digits. The fixed
constant strings the helper composes (`"cohmon_summary "`,
`" overall="`, `" pass="`, `" warn="`, `" fail="`, `" na="`,
`" checks="`) contain no forbidden term.

The I-CFBK-02 static-audit fixture replays the helper over a
representative input set and asserts the non-claim scan returns
zero hits.

Status today: **DONE BY DESIGN** — every primitive in the input
set is itself non-claim-clean.

---

## 6. Determinism predictions

For every cell, two independent fresh `OperatorSession` instances
constructed with the same `(N, mode, input)` triple are expected
to produce:

```text
- identical session.pattern_ledger.entries pattern_id tuple
- identical session.pattern_ledger.entries recurrence_count tuple
- identical session.pattern_ledger.entries saturation_state tuple
- identical session.growth_ledger.events event_id tuple
- identical session.stream_history.chunks (chunk_id, provenance) tuples
- identical build_full_coherence_report(session).overall_status
- identical build_full_coherence_report(session).counts_by_status
```

This follows from:

- the kernel state derivation is pure (Phase 3.18 D3);
- `build_pledger_summary_text` is pure (Phase 3.19 I-IFBK-02);
- `build_cohmon_summary_text` will be pure (Phase 3.20 I-CFBK-02
  locks this);
- `build_full_coherence_report` is pure over its `OperatorSession`
  input (Phase 3.12c I-COHMON-04..09 lock the determinism).

Cumulative real model calls = 0. L1 / L2 cache writes = 0.
`assert_state_invariants` PASS across all cells.

---

## 7. Saturation behavior (carryover note)

The Phase 3.18 saturation demonstration (`N = 255` reaches
`STREAM_PATTERN_RECURRENCE_MAX = 256`) is preserved for the seed
entry regardless of `feedback_mode`. The second-order entries
(pledger_summary and cohmon_summary families) each follow the
same saturation discipline because they go through the same
`PatternLedger.observe` call site.

At `N = 50`, no entry is at saturation
(`MIN + 50 = 52 << 256`). The 50-window matrix exercises the
loop without triggering saturation; saturation is exercised by
the Phase 3.18 N=255 demonstration which Phase 3.20's behavior
report does not re-run.

If Step 5 LOCK B authorizes it, a one-cell `N = 255` re-run can
be added to the Step 8 harness under COHERENCE mode to confirm
saturation behavior is preserved; otherwise this is deferred.

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the matrix is derivable from the synthesis +
  Phase 3.19 behavior report + Coherence Monitor bounds.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard.
```

---

## 9. Next artifact

`docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_CORRIGENDA.md`
— the Step 4 design locks (LOCK A through LOCK K) that bind the
Phase 3.20 v1 implementation choices in advance of Step 5's
catalog patch plan.
