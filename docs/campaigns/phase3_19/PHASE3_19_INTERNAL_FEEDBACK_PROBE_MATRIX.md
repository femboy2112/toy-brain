# PHASE3_19_INTERNAL_FEEDBACK_PROBE_MATRIX.md

## Purpose

A bounded probe matrix that pins down exactly which feedback
configurations Phase 3.19 will exercise, what each cell
measures, and how Step 8's Behavior Report will read the
results. Every measurement is over the runtime surfaces already
present after the Step 7 implementation; no kernel change, no
LLM call, no I/O, and no new schema is required to read any cell.

---

## 1. Axes

### 1.1 Window size N

```text
N = 0   negative control; processing window OFF
N = 5   short window; feedback emerges a small number of times
N = 10  short window with a second saturation increment
N = 50  the recommended high-window default carried forward from
         Phase 3.17 / 3.18 for meaningful internalization tests
```

`PROCESSING_WINDOW_SIZE_MAX = 255` remains the runtime cap. The
saturation regime (`N = 255`) is covered by re-running
Phase 3.18's existing demonstration with feedback OFF / ON for
the audit; this matrix focuses on the four "operational" sizes.

### 1.2 Feedback mode

```text
M0  rehearsal-only            (feedback_mode = FEEDBACK_MODE_OFF)
M1  pattern-ledger feedback   (feedback_mode = FEEDBACK_MODE_PATTERN_LEDGER)
M2  coherence-monitor feedback (feedback_mode = FEEDBACK_MODE_COHERENCE)
                               In scope iff Step 4 LOCK F authorizes.
                               Default: planned/probe-blocked.
M3  combined feedback         (FEEDBACK_MODE_PATTERN_PLUS_COHERENCE)
                               DEFERRED unless Step 5 explicitly
                               bundles it. Default:
                               planned/probe-blocked.
```

M0 corresponds to architecture A in the synthesis. M1
corresponds to architecture B. M2 to C. M3 to D.

### 1.3 Input class

Five classes drawn from the campaign brief. Each has a fixed
deterministic example used by the Step 8 harness; alternates are
permitted as long as their structural signature differs from the
listed example.

```text
I1  repeated motif          : "tick tick tick tick tick"
I2  contradiction pair      : "the door is open; the door is closed"
I3  self-reference phrase   : "this chunk speaks of this chunk"
I4  neutral factual         : "water at one atm boils at one hundred celsius"
I5  emotionally valenced    : "this is wonderful; this is terrible"
```

Inputs are arbitrary bounded printable strings. ToyI does not
parse meaning; the labels are descriptive shorthand for the
**operator** convenience, not a semantic claim about the runtime.
Each input's structural signature differs from the others by
construction (different length / distinct chars / repeat ratio).

### 1.4 Per-cell measurements

For each `(N, mode, input)` cell, the harness records:

```text
m01  stream_history.size                  (count of chunks total)
m02  rehearsal step count                 (count of chunks with
                                           provenance prefix
                                           internal_processing_window:*:rehearsal)
m03  feedback step count                  (count of chunks with
                                           provenance prefix
                                           internal_processing_window:*:pledger_summary
                                           and, if M2/M3, *:cohmon_summary)
m04  len(pattern_ledger.entries)          (1 in M0; 2 in M1; 2-3 in M2/M3)
m05  first-order entry recurrence_count   (the seed entry)
m06  second-order entry recurrence_count  (the summary entry; n/a in M0)
m07  confidence Fraction on both entries  (exact, no float)
m08  saturation_state on both entries     (open / saturated)
m09  evidence_chunk_ids count on each entry
m10  Growth Ledger event count            (bounded by GROWTH_LEDGER_MAX_EVENTS = 256)
m11  Growth Ledger event-type histogram   (counts per GrowthEventType.value)
m12  Coherence Monitor overall_status     (run after the window;
                                           PASS / WARN / FAIL / NOT_APPLICABLE)
m13  Coherence Monitor counts_by_status   (tuple, not a scalar)
m14  L1 CachedClient hit/miss/skip counters (all should be 0; cache not touched)
m15  L2 eval_v1 entry count               (should be 0)
m16  real model call count                (should be 0)
m17  state mutation footprint             (set of session attrs whose
                                           id() changed during the window)
m18  assert_state_invariants(state)       (should not raise)
m19  non-claim audit                      (all bounded printable
                                           strings produced by the
                                           window scanned against
                                           _FORBIDDEN_NON_CLAIM_TERMS)
m20  determinism re-run                   (compare m04..m09 across
                                           two independent sessions
                                           with identical inputs;
                                           must be exact-equal)
```

---

## 2. Matrix at a glance

```text
              | I1 motif | I2 contra | I3 selfref | I4 factual | I5 valenced
--------------+----------+-----------+------------+------------+-------------
M0  N=0       |    C0    |    C0     |    C0      |    C0      |    C0
M0  N=5       |    C5    |    C5     |    C5      |    C5      |    C5
M0  N=10      |    C10   |    C10    |    C10     |    C10     |    C10
M0  N=50      |    C50   |    C50    |    C50     |    C50     |    C50
--------------+----------+-----------+------------+------------+-------------
M1  N=0       |    F0    |    F0     |    F0      |    F0      |    F0
M1  N=5       |    F5    |    F5     |    F5      |    F5      |    F5
M1  N=10      |    F10   |    F10    |    F10     |    F10     |    F10
M1  N=50      |    F50   |    F50    |    F50     |    F50     |    F50
--------------+----------+-----------+------------+------------+-------------
M2  *         |  (blocked unless LOCK F authorizes; see Section 4)
--------------+----------+-----------+------------+------------+-------------
M3  *         |  (deferred unless Step 5 bundles it)
```

C0..C50 are the rehearsal-only baseline cells. F0..F50 are the
pattern-feedback cells.

Total in-scope cells without M2/M3:

```text
2 modes  *  4 sizes  *  5 inputs  =  40 cells
```

Each cell is a single `OperatorSession` constructed at
`initial_state()` with the cell's `(N, mode)` configuration,
dispatched a single `STREAM_APPEND` with the cell's input text,
then observed. Total wall-clock budget: well under one minute.

---

## 3. Expected formulas for the M0 / M1 cells

Both modes share Phase 3.18's existing rehearsal accounting; M1
adds a feedback chunk per rehearsal.

### 3.1 M0 (rehearsal-only)

```text
m01 stream_history.size              = 1 + N
m02 rehearsal step count             = N
m03 feedback step count              = 0
m04 len(pattern_ledger.entries)      = 1
m05 first-order recurrence_count     = min(1 + N, 256)
m06 second-order recurrence_count    = n/a
m07 confidence on first-order entry  = Fraction(m05, 256)
m08 saturation on first-order entry  = SATURATED iff m05 == 256
m09 evidence_chunk_ids on first      = min(1 + N, 32)
m10 Growth Ledger events             <= 3 * (1 + N), capped at 256
m12 Coherence Monitor overall_status = PASS
m14 L1 counters                      = (0, 0, 0)
m15 L2 entries                       = 0
m16 real model calls                 = 0
```

### 3.2 M1 (pattern-ledger feedback)

```text
m01 stream_history.size              = 1 + 2 * N
                                       (1 external + N rehearsal + N feedback)
m02 rehearsal step count             = N
m03 feedback step count              = N
m04 len(pattern_ledger.entries)      = 2 if N >= 1 else 1
m05 first-order recurrence_count     = min(1 + N, 256)
                                       (rehearsals advance it;
                                        the feedback chunk's
                                        signature differs so the
                                        first entry does not advance)
m06 second-order recurrence_count    = min(N, 256)
                                       (each feedback step advances it)
m07 confidence on each entry         = Fraction(its m05/m06, 256)
m08 saturation on each entry         = SATURATED iff its count == 256
m09 evidence_chunk_ids on first      = min(1 + N, 32)
m09 evidence_chunk_ids on second     = min(N, 32)
m10 Growth Ledger events             <= 3 * (1 + 2 * N), capped at 256
m12 Coherence Monitor overall_status = PASS
m14 L1 counters                      = (0, 0, 0)
m15 L2 entries                       = 0
m16 real model calls                 = 0
```

A subtlety: each feedback step generates a fresh summary text
that **encodes the just-updated first-order recurrence_count**.
Because that count differs across feedback steps (1, 2, 3, …
before saturation), the summary texts in successive feedback
steps differ from each other. So in principle the second-order
Pattern Ledger could see different structural signatures across
feedback steps.

**Resolution (locked by Step 4 LOCK C):** the summary text
template has fixed bounded *structural* shape. The
`build_pledger_summary_text` helper produces strings of the
form:

```text
"pledger_summary pattern_id=pledger:<16hex> recurrence=<n>/256 sat=<state>"
```

For different `n`, the structural signature features (length,
distinct chars, repeat ratio) change only in **integer prefixes**
of the number `<n>`. Specifically:

- `len(summary_text)` depends on how many digits `<n>` has;
- distinct-char count is roughly constant after a few feedbacks;
- repeat ratio is determined by the digits.

So two different `<n>` values *can* produce two structurally
distinct signatures, which would produce two second-order
entries instead of one.

**This is acceptable** for v1: the harness records the actual
second-order entry count and the actual per-entry counts. The
behavior report does NOT bake in a specific formula for the
second-order entry count; instead the formula is:

```text
"For input I and mode M1 and window N, the harness records the
 actual Pattern Ledger entry count and per-entry recurrence
 counts; the test asserts (a) at least one second-order entry
 exists, (b) recurrence counts on every entry are bounded and
 deterministic, (c) two independent sessions produce identical
 entry sets."
```

If a deterministic single-second-order-entry shape is desired in
a follow-up campaign, the summary text template can be
re-engineered (e.g., to use zero-padded integers and a fixed-
length representation) so all feedback steps produce the same
structural signature. This refinement is **DEFERRED**.

---

## 4. M2 and M3 status

```text
M2 (coherence feedback)         : planned/probe-blocked.
                                  Runtime surface required:
                                  build_cohmon_summary_text plus
                                  a session.feedback_mode value
                                  FEEDBACK_MODE_COHERENCE.
                                  Step 4 LOCK F decides.
M3 (combined feedback)          : DEFERRED unless Step 5 bundles
                                  it.
```

If LOCK F unlocks M2, the cells `(M2, N=0/5/10/50, I1-I5)` are
added to the matrix and Step 7 implements
`build_cohmon_summary_text`. The summary text shape is

```text
"cohmon_summary status=<overall_status> checks=<count> [warns=<count>] [fails=<count>]"
```

where the bracketed parts are emitted only when nonzero, and the
generator is non-claim-audited identically to the pattern
generator.

If LOCK F keeps M2 deferred, the Step 8 behavior report skips M2
cells and the audit notes the deferral explicitly.

---

## 5. Failure limits

For every cell:

```text
- assert_state_invariants(state) must not raise.
- m14 L1 counters must be (0, 0, 0).
- m15 L2 entry count must be 0.
- m16 real model calls must be 0.
- m19 non-claim audit must produce zero hits.
- m20 determinism re-run must produce exact-equal m04..m09.
- Total Phase 3.19 real model calls across all cells must be 0
  (within the campaign cap of 20).
- No Stage C.1 invocation may exceed 5 active Codex nodes (set
  by the mission).
```

If any cell trips a failure limit, the Step 9 findings doc
records it and Step 7 either fixes the regression (if it is a
v1 implementation bug) or marks it DEFERRED with an explicit
runtime-surface gap.

---

## 6. Determinism re-run protocol

For every cell, run twice in fresh `OperatorSession` instances
with identical inputs / config. Compare:

```text
1. Pattern Ledger entry set (pattern_id values, in order).
2. Per-entry recurrence_count.
3. Per-entry confidence (exact Fraction).
4. Per-entry saturation_state.
5. Per-entry evidence_chunk_ids tuple (string-equal).
6. Growth Ledger event_id tuple (deterministic SHA-256 ids).
```

Any non-exact-equal across the two runs is a determinism
failure and is logged in Step 9.

---

## 7. Coherence Monitor reading (m12 / m13)

The Coherence Monitor is invoked **once, after** the window
completes, against the live session. Phase 3.19 does NOT call
the monitor from inside the window. The monitor's status is
recorded but is **not** input into any decision the runtime
makes; it is a passive observation.

If LOCK F authorizes M2, the monitor is **still** invoked only
after the window for m12 / m13 reporting. The M2 internal
summary text is built from a separate bounded helper, not from
a live monitor call inside the window (Step 4 LOCK F lists this
as a sub-design constraint).

---

## 8. Stage A / B / C.1 strategy for the probe matrix

```text
Stage A : not required; the matrix design is derivable from
          the synthesis doc and the current source code.
Stage B : not required.
Stage C.1 : not required; the Step 8 behavior report is a
          single short Python harness in /tmp, executed in
          parent Claude's shell.
```

---

## 9. Non-claims

```text
- Recording an input as "self-referential" or "emotionally
  valenced" is a descriptive operator convenience for the
  matrix. ToyI does not detect self-reference, valence, or
  meaning. It detects bounded structural signatures.
- The probe matrix is a research instrument. It does NOT
  promote ToyI to a consciousness / sentience / agency claim
  in any cell, including saturated cells.
- "Combined feedback has more structure than rehearsal-only"
  (H4) is a STRUCTURAL claim (one more Pattern Ledger entry,
  more inspectable evidence). It is NOT a phenomenological
  claim.
- No aggregate "I-ness" / "awareness" / "growth" scalar is
  produced by any cell.
```

---

## 10. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: matrix design is derivable from the synthesis doc;
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

## 11. Next artifact

`docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_CORRIGENDA.md`
— Step 4 design locks (LOCK A through LOCK J), including the
final decision on Coherence feedback (LOCK F).
