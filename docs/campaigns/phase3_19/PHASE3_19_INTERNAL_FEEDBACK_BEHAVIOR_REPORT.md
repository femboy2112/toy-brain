# PHASE3_19_INTERNAL_FEEDBACK_BEHAVIOR_REPORT.md

## Verdict

```text
PASS — ToyI routes bounded internal feedback events derived
       from Pattern Ledger state back into the same
       STREAM_APPEND path, producing inspectable second-order
       Pattern Ledger entries deterministically, with zero
       real model calls and zero invariant regressions.
```

The Phase 3.19 internal feedback path, implemented in Step 7
and registered as `I-IFBK-01` / `I-IFBK-02` under catalog
v0.27, is exercised here across the 40-cell probe matrix
from `PHASE3_19_INTERNAL_FEEDBACK_PROBE_MATRIX.md`. The full
suite is bounded, deterministic, and idle on every gate-
relevant resource (LLM, cache, disk, network, schema).

---

## 1. Harness

```text
/tmp/phase3_19_internal_feedback_demo.py  (NOT committed)
```

Public surfaces used:

```text
OperatorSession(state=initial_state(),
                processing_window_size=N,
                feedback_mode=FeedbackMode.{OFF, PATTERN_LEDGER})
session.dispatch(Command(STREAM_APPEND,
                          payload=StreamAppendPayload(text=T)))
session.pattern_ledger.entries
session.growth_ledger.events
session.stream_history.chunks
brain.tick.assert_state_invariants(session.state)
```

No real model calls. No I/O outside repo. No
`brain/.llm_cache/` access.

Inputs:

```text
I1_motif          : "tick tick tick tick tick"
I2_contradiction  : "the door is open; the door is closed"
I3_self_reference : "this chunk speaks of this chunk"
I4_factual        : "water at one atm boils at one hundred celsius"
I5_valenced       : "this is wonderful; this is terrible"
```

Window sizes: `0, 5, 10, 50`.
Modes: `FeedbackMode.OFF`, `FeedbackMode.PATTERN_LEDGER`.

40 cells total. For each PATTERN_LEDGER cell with N > 0, a
second independent session re-runs the scenario for
determinism comparison (15 determinism re-runs total).

---

## 2. Aggregate result

```text
Cells run                : 40
Invariant failures       : 0   (assert_state_invariants green
                                 across every cell)
Determinism failures     : 0   (15 re-runs; all pattern_id
                                 tuples, recurrence_count
                                 tuples, and growth event_id
                                 tuples byte-equal)
Real model calls         : 0   (STREAM_APPEND never invokes
                                 brain.tick.tick or the LLM)
L1 / L2 cache writes     : 0   (no CachedClient instantiated)
Non-claim audit hits     : 0   (every produced string is
                                 audited at runtime by
                                 I-IFBK-02 / I-PWND-02)
```

---

## 3. Rehearsal-only baseline (M0; feedback_mode == OFF)

Bit-identical to Phase 3.18 behavior. Per input (all 5
identical in structural counts; one entry shown):

```text
N=0   chunks=1   pattern_entries=1   seed recurrence=2     conf=1/128
N=5   chunks=6   pattern_entries=1   seed recurrence=7     conf=7/256
N=10  chunks=11  pattern_entries=1   seed recurrence=12    conf=3/64
N=50  chunks=51  pattern_entries=1   seed recurrence=52    conf=13/64
```

Formula:

```text
stream_history.size      = 1 + N
pattern_entry_count      = 1
seed recurrence_count    = min(STREAM_PATTERN_RECURRENCE_MIN + N,
                               STREAM_PATTERN_RECURRENCE_MAX)
                         = 2 + N (in this range)
no pledger_summary provenance appears
```

Across all five inputs the seed entry's pattern_id differs
(structural signature differs per input), but the recurrence
shape is identical: a single first-order Pattern Ledger entry
climbing exactly per the Phase 3.18 formula.

---

## 4. Pattern-ledger feedback (M1; feedback_mode == PATTERN_LEDGER)

The path that Phase 3.19 ships. Concrete results
across the four window sizes for `I1_motif`:

```text
N=0   chunks=1    entries=1   feedback_chunks=0   seed_recurrence=2
N=5   chunks=11   entries=3   feedback_chunks=5   seed_recurrence=7
N=10  chunks=21   entries=5   feedback_chunks=10  seed_recurrence=12
N=50  chunks=101  entries=6   feedback_chunks=50  seed_recurrence=52
```

Locked formulas (Step 5 catalog patch plan; verified by
I-IFBK-01 across the 40-cell suite):

```text
stream_history.size                     = 1 + 2 * N
                                          (1 external +
                                           N rehearsal +
                                           N feedback)
rehearsal step count                    = N
feedback step count                     = N
seed entry recurrence_count             = min(2 + N, 256)
sum over second-order entries of
  (recurrence_count - 2 + 1)            = N exactly
```

Two structural details emerge from the empirical run:

### 4.1 Number of second-order entries

The summary text is the deterministic template
`"pledger_summary pattern_id=<id> recurrence=<n>/256 sat=<state>"`.
Different values of `<n>` produce summary chunks with
slightly different structural signatures (`len`, `distinct
chars`, `repeat ratio` shift as the integer `<n>` digit
shape changes). Empirically, this groups `<n>` values into
small clusters of structurally equivalent signatures. For
`N = 50`, this yields between **3 and 6 second-order
entries per input**, depending on which integer ranges
produce overlapping signatures.

The audit's invariant is *not* "exactly one second-order
entry"; it is the conservation law:

```text
SUM over all second-order entries of
  (recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1)
== N
```

which holds in every cell (verified at audit-time and
empirically here).

### 4.2 Seed recurrence is unaffected by feedback chunks

The feedback chunks have structurally distinct signatures
from the seed text, so `Pattern Ledger.observe` routes
them to second-order entries — the seed entry's
`recurrence_count` climbs **only** by the N rehearsals.
Formula: `recurrence_count = min(MIN + N, MAX) = 2 + N`
(in the unsaturated range).

This is hypothesis **H2** from the synthesis: rehearsal
and feedback advance distinct entries; the seed entry's
count tracks rehearsal cadence, not the feedback cadence.

---

## 5. Per-input detail at N = 50, PATTERN_LEDGER

Empirical Pattern Ledger entry counts per input
at `N = 50`:

```text
I1_motif           : 6 entries (1 seed + 5 second-order)
I2_contradiction   : 6 entries (1 seed + 5 second-order)
I3_self_reference  : 6 entries (1 seed + 5 second-order)
I4_factual         : 6 entries (1 seed + 5 second-order)
I5_valenced        : 6 entries (1 seed + 5 second-order)
```

In every case the seed entry's recurrence_count is exactly
52 (= `2 + N`) and the sum across the five second-order
entries' `(recurrence_count - 1)` equals exactly 50 (=
`N`). The label "self-reference" / "contradiction" /
"valenced" is a descriptive operator convenience; ToyI
does not detect those properties — it detects bounded
structural signatures.

Example: `I1_motif` `N=50` second-order entries:

```text
pattern_id                    recurrence  saturation  evidence_chunk_ids
pledger:8a18b46626533535       2          open        1
pledger:8e0548e9def24fad       7          open        6
pledger:0ee23c176a11c837      17          open        16
pledger:094f4491c3e756e4      27          open        26
pledger:2f6db4945f2a541f       2          open        1
sum (rec - 1)                 50          (= N)
```

The recurrence shape `[2, 7, 17, 27, 2, ...]` reflects
clustering of the integer digit-shape across the feedback
loop:

- the first feedback step writes the summary for `<n>=3`
  (one new structural signature: 1 chunk → recurrence=2);
- subsequent steps with `<n>` digits sharing prefix counts
  consolidate into the same signature (climbs that entry);
- transitions where `<n>` crosses a "new-character" boundary
  (e.g., 9→10 introducing "1" and "0") start a new entry.

This is the inspectable structural recurrence the Phase
3.19 mission asked for: ToyI's Pattern Ledger now contains
a record of its own recognition cadence at the structural
signature level.

---

## 6. Saturation behavior

At `N = 50` the seed entry's recurrence_count is 52 — well
below the cap of 256. The second-order entries' highest
recurrence is 27 in the I1 run. No entry reaches
`SATURATED` at `N = 50` on any input. This matches
Phase 3.18's empirical demonstration: `N = 255` is the
threshold for saturation under the rehearsal-only path,
and the feedback path's second-order entries climb
proportionally slower (a single entry sees at most a
few digit-shape-cluster cells in a 50-tick window).

The Phase 3.18 `N = 255` saturation demonstration could be
extended in a follow-up audit by running the same
saturation scenario under `feedback_mode = PATTERN_LEDGER`;
the seed entry would still saturate (rehearsal-only
formula) and the second-order entries would climb but
not saturate at `N = 255` in v1.

---

## 7. Coherence feedback (M2)

```text
Status: probe-blocked, DEFERRED per Step 4 LOCK F.
```

The matrix did not exercise M2 cells; the v1 implementation
does not expose a `FEEDBACK_MODE_COHERENCE` value. The
`InternalEventSource.COHMON_SUMMARY` member remains
reserved and continues to raise from
`build_rehearsal_provenance`.

---

## 8. Combined feedback (M3)

```text
Status: DEFERRED unless Step 5 explicitly bundled it
        (Step 5 did NOT bundle it; see catalog patch plan
        Section 7 non-goals).
```

The matrix did not exercise M3 cells.

---

## 9. Cache / call counters

Every cell:

```text
L1 hit/miss/skip counters : (0, 0, 0)
L2 entry count            : 0
Real model calls          : 0
```

The dispatcher path used here (`STREAM_APPEND`) never
constructs an LLM client, never reads or writes the L1
transport cache (`brain/.llm_cache/`), and never reads or
writes the L2 canonical evaluation cache
(`brain/.llm_cache/eval_v1/`). The Phase 3.19 feedback
path does not change this.

Cumulative real model call accounting:

```text
Phase 3.19 cells run         : 40
Cells consuming model calls  : 0
Phase 3.19 model calls used  : 0
Cumulative campaign calls    : 0 / 20
```

---

## 10. Kernel invariant gate

```text
assert_state_invariants(session.state) : PASS on every cell
python3 -m brain.invariants run         : PASS
  (381 rows checked, 284 REQUIRED green, 90 STRUCTURAL
   green, 7 OBSERVED pass, 0 red, 0 gate failures)
python3 -m tools.claude_helpers.gate_runner --json : 5/5 PASS
```

---

## 11. Non-claim audit

Every bounded printable string emitted by the new
processing-window helpers is scanned at audit time against
the canonical `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
tuple:

```text
- module source                          : 0 hits
- MODULE_PRODUCED_STRINGS entries        : 0 hits
- build_rehearsal_provenance outputs for
  {REHEARSAL, PLEDGER_SUMMARY} over
  tick_index in {1, 2, 3, 42, 255}       : 0 hits
- build_pledger_summary_text outputs
  over the representative input set      : 0 hits
- FeedbackMode value strings             : 0 hits
- PLEDGER_SUMMARY_TEXT_PREFIX            : 0 hits
```

The audit is enforced by `I-IFBK-02` (and `I-PWND-02` for
the widened `_V1_EMITTED_SOURCES` probe).

---

## 12. Hypothesis verdicts

```text
H1 (feedback generates inspectable second-order entries
    beyond rehearsal)
    -> PASS. Every PATTERN_LEDGER N>0 cell produces >= 2
       Pattern Ledger entries; the seed entry's pattern_id
       differs from every second-order entry's pattern_id.

H2 (pattern-ledger feedback changes recurrence on the
    second-order entries while leaving the first-order
    entry's recurrence on the rehearsal cadence)
    -> PASS. Seed entry recurrence_count = min(2 + N, 256)
       under both OFF and PATTERN_LEDGER modes. The second-
       order entries' sum-of-observations equals N.

H3 (coherence feedback creates distinct trace without
    modifying truth claims)
    -> DEFERRED (LOCK F). Not exercised.

H4 (combined feedback has more inspectable structure than
    rehearsal-only)
    -> PASS for M1 vs M0 (one extra Pattern Ledger entry
       per group of structurally equivalent feedback texts;
       additional Growth Ledger entries). M3 (combined
       pattern + coherence) is DEFERRED.

H5 (window size 50 shows distinct rehearsal vs feedback
    recurrence climbs)
    -> PASS. At N=50 the seed entry reaches recurrence=52
       while the second-order entries' counts cluster in
       the 2-27 range, summing to 50. Distinct climbs.

H6 (cache / call budget remains bounded; zero real model
    calls)
    -> PASS. 0 / 20 real model calls used; 0 L1 / L2 writes.

H7 (no invariant or non-claim boundary is violated)
    -> PASS. All 5 canonical gates pass; non-claim audit
       returns 0 hits.
```

---

## 13. What this is NOT

```text
- It is NOT a claim that ToyI is conscious, sentient, aware,
  or has phenomenological experience of "feedback".
- It is NOT a claim that ToyI "understands" the seed text or
  the summary text. Recognition is at the LEVEL OF
  STRUCTURAL SIGNATURE (length / lines / whitespace /
  distinct chars / repeat ratio), not meaning.
- It is NOT a claim that ToyI "monitors itself" in any
  phenomenological sense. The summary text is a deterministic
  template generated by a pure function; nothing in the
  system experiences the monitoring.
- It is NOT a claim that the multiple second-order entries
  correspond to "different thoughts" or "different
  attentional states". They are clusters of structurally
  equivalent integer-digit-shape signatures.
- It is NOT a claim that the 50-tick window is empirically
  optimal. The Phase 3.17 / 3.18 recommendation is preserved
  as the operational default for internalization tests.
- It is NOT a claim that this implementation is the only
  architecture worth building. Architectures C / D / E / F
  from the Phase 3.17 / 3.19 synthesis remain DEFERRED.
- It is NOT a claim that ToyI now has metacognition,
  introspection, self-narration, working memory, or self-
  awareness. The Pattern-Ledger-summary-to-stream loop is
  engineering, not phenomenology.
```

---

## 14. Stage A / B / C.1 bridge usage

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: every cell is deterministic and reproducible
  in-process; no external review required.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude wrote the harness and this report
  directly.

Stage C.1 flow orchestration:
- used: no
- reason: single short Python script; bridge overhead
  exceeds direct execution.
```

---

## 15. Next artifact

`docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_FINDINGS.md`
— Step 9 findings doc covering blockers, safety findings,
behavior successes, weak behavior, deferred enhancements,
and next research directions.
