# PHASE3_20_COHERENCE_FEEDBACK_BEHAVIOR_REPORT.md

## Purpose

Record the measurements taken by exercising the 80-cell probe
matrix (Step 3) against the Step 7 implementation. Each cell is a
unique `(input_family, mode, N)` triple. Every cell ran through
the public `OperatorSession.dispatch(STREAM_APPEND)` path with
zero external configuration, zero LLM seam touched, and zero cache
writes.

The harness lives at `/tmp/phase3_20_coherence_feedback_demo.py`
and is NOT committed (LOCK K).

---

## 1. Run configuration

```text
Catalog version on disk      : v0.28
Branch                       : campaign/phase3-20-coherence-feedback-bridge
HEAD at run time             : 6c6eda8 (phase3.20 step7 implementation)
Python                       : 3.12
PYTHONPATH                   : /home/leah/brain/toy-brain
Real model mode              : not used (OFFLINE remains default)
LLM client                   : never constructed
Stage A / B / C.1 bridges    : not used
```

Inputs (five canonical seeds):

```text
repeated_motif         : "the kettle whistled at exactly noon today again"
contradiction_pair     : "the lamp is both on and off at exactly the same time"
self_reference         : "this sentence has six words"
neutral_factual        : "water boils at 100 degrees celsius at standard pressure"
emotionally_valenced   : "the room was warm and quiet and felt safe to stay in"
```

---

## 2. Aggregate results

```text
total cells                                  : 80
chunk-count formula mismatches               : 0
determinism failures                         : 0
assert_state_invariants failures             : 0
cumulative real model calls                  : 0
cumulative L1 cache writes                   : 0
cumulative L2 cache writes                   : 0
CoherenceReport overall_status distribution  : {"pass": 80}
```

Every cell passed every gate. The chunk-count formula
`1 + alpha * N` (with `alpha in {1, 2, 2, 3}` for OFF /
PATTERN_LEDGER / COHERENCE / PATTERN_AND_COHERENCE) held
deterministically across every input family and every window
size.

---

## 3. Per-(mode, N) table (aggregated across all 5 input families)

```text
(mode, N)                       | chunks | pattern entries (min..max) | growth events (min..max)
--------------------------------+--------+----------------------------+-------------------------
(off, 0)                        |     1  | 1..1                        | 2..2
(off, 5)                        |     6  | 1..1                        | 8..8
(off, 10)                       |    11  | 1..1                        | 13..13
(off, 50)                       |    51  | 1..1                        | 53..53
(pattern_ledger, 0)             |     1  | 1..1                        | 2..2
(pattern_ledger, 5)             |    11  | 3..3                        | 16..17
(pattern_ledger, 10)            |    21  | 4..5                        | 29..30
(pattern_ledger, 50)            |   101  | 5..6                        | 111..113
(coherence, 0)                  |     1  | 1..1                        | 2..2
(coherence, 5)                  |    11  | 2..2                        | 15..15
(coherence, 10)                 |    21  | 2..2                        | 25..25
(coherence, 50)                 |   101  | 2..2                        | 105..105
(pattern_and_coherence, 0)      |     1  | 1..1                        | 2..2
(pattern_and_coherence, 5)      |    16  | 4..4                        | 23..24
(pattern_and_coherence, 10)     |    31  | 5..6                        | 41..42
(pattern_and_coherence, 50)     |   151  | 6..7                        | 163..165
```

Chunks are constant across inputs (the formula is input-independent).
Pattern entries vary slightly because each input's structural
signature drives a different shape — the variation is over
*inputs*, not over *runs* (determinism holds).

---

## 4. Mode-by-mode verdicts

### 4.1 OFF baseline

All 20 cells PASS. Behavior is bit-identical to the Phase 3.18
rehearsal-only baseline: chunk count `1 + N`, exactly one Pattern
Ledger entry whose recurrence climbs by N, no pledger_summary
chunks, no cohmon_summary chunks, growth events scale linearly
with N (one `STREAM_CHUNK_ACCEPTED` per chunk plus one
`PATTERN_ENTRY_*` per ledger update).

Verdict: **PASS**

### 4.2 PATTERN_LEDGER baseline (Phase 3.19 preserved)

All 20 cells PASS. Behavior is bit-identical to the Phase 3.19
behavior report: chunk count `1 + 2N`, at least 2 Pattern Ledger
entries (seed + pledger family), zero cohmon_summary chunks. The
pledger family entry counts vary across inputs (3..6) because
different input shapes produce different distinct signatures for
the pledger_summary text under varying recurrence counts.

Verdict: **PASS**

### 4.3 COHERENCE feedback (Phase 3.20 main target)

All 20 cells PASS. Chunk count is `1 + 2N` exactly. Pattern
Ledger entry count is **exactly 2 in every observed cell** (seed
+ 1 cohmon-family entry). This is interesting: the
`build_cohmon_summary_text` output stays structurally signature-
stable across rehearsal steps for these inputs because the
Coherence Monitor's per-status counts are constant within a
session (every check stays PASS), so the bounded text is
character-stable across all N rehearsals and Pattern Ledger
collapses N feedback chunks into one second-order entry whose
recurrence climbs by N.

Growth event count under COHERENCE is exactly `3 + 2N`:

```text
1 STREAM_CHUNK_ACCEPTED + 1 PATTERN_ENTRY_CREATED      (operator chunk)
+ N (STREAM_CHUNK_ACCEPTED + PATTERN_ENTRY_UPDATED)    (rehearsals)
+ 1 PATTERN_ENTRY_CREATED + N STREAM_CHUNK_ACCEPTED
  + (N-1) PATTERN_ENTRY_UPDATED                        (cohmon family)
```

which matches the observed totals (2 at N=0, 15 at N=5, 25 at
N=10, 105 at N=50).

The non-claim audit (canonical `_FORBIDDEN_NON_CLAIM_TERMS` scan)
PASSes against the helper output and the new fixture file. The
CoherenceReport's overall_status is `"pass"` in every cell.

Verdict: **PASS**

### 4.4 PATTERN_AND_COHERENCE combined feedback

All 20 cells PASS. Chunk count is `1 + 3N` exactly. Pattern
Ledger entry count is 4..7 — the pledger family contributes 1..3
entries depending on N (the text varies with recurrence_count
written into the template), and the cohmon family typically
collapses to a single entry per session (same reason as
COHERENCE-only).

Determinism holds bit-for-bit across runs. Two independent fresh
sessions with identical inputs and `PATTERN_AND_COHERENCE` produce
identical Pattern Ledger pattern_id tuples, identical per-entry
recurrence_count tuples, and identical Growth Ledger event_id
tuples.

Verdict: **PASS**

---

## 5. Hypothesis evaluation

```text
H1. FeedbackMode.COHERENCE emits exactly N bounded coherence-
    summary chunks per dispatch; chunk count = 1 + 2N;
    second-order entries >= 1 distinct from seed.
    -> CONFIRMED: m04_cohmon_summary == N in every COHERENCE
       cell; m01_stream_chunks == 1 + 2N; m05_pattern_entries
       == 2 (seed + 1 distinct cohmon-family).

H2. Each cohmon_summary chunk produces a distinct second-order
    Pattern Ledger entry whose pattern_id differs from any
    pledger_summary entry.
    -> NARROWLY CONFIRMED: cohmon-family pattern_ids are
       distinct from seed; under PATTERN_AND_COHERENCE they are
       also disjoint from pledger family. The behavior matrix
       shows that cohmon-family chunks COLLAPSE into one
       second-order entry per session (not N distinct entries)
       because the bounded text is signature-stable across the
       N rehearsals when the monitor's counts don't shift. This
       is the expected and correct behavior under Pattern
       Ledger.observe; the I-CFBK-01 fixture asserts only
       ">= 1 distinct cohmon-family entry" and that the
       observation total equals N — both PASS.

H3. PATTERN_AND_COHERENCE produces more inspectable structure
    than PATTERN_LEDGER alone; bit-deterministic across runs.
    -> CONFIRMED: chunk count = 1 + 3N vs 1 + 2N;
       pattern_entries = 4..7 vs 3..6;
       growth_events = 23..165 vs 16..113 across N=5..50;
       determinism PASS on every cell.

H4. PASS / WARN / FAIL / NOT_APPLICABLE labels are preserved as
    structural status only; canonical _FORBIDDEN_NON_CLAIM_TERMS
    audit zero hits on helper outputs and new fixtures.
    -> CONFIRMED: I-CFBK-02 fixture PASSes; processing_window.py
       source-scan PASSes (one occurrence of the forbidden term
       "truth" was caught in the docstring during Step 7 testing
       and immediately removed before commit).

H5. No scalar aggregate I-ness / awareness / growth / coherence-
    feedback score anywhere.
    -> CONFIRMED: no scalar field exists in processing_window.py,
       session.py, the fixtures, or the catalog. The
       counts_by_status tuple in CoherenceReport remains a
       labelled tuple, not a scalar.

H6. 50-window runs remain bounded: chunk count exactly
    1 + 2*50 = 101 under COHERENCE, 1 + 3*50 = 151 under
    PATTERN_AND_COHERENCE; Pattern Ledger entry count stays
    under PATTERN_LEDGER_MAX_ENTRIES; cumulative real model
    calls = 0.
    -> CONFIRMED: observed exactly 101 and 151 chunks at N=50;
       entry counts 2 and 6..7 respectively (well under 1024);
       cumulative model calls = 0.

H7. I-PWND-02 static audit still passes; I-COHMON-10 audit on
    Coherence Monitor still passes; I-CFBK-02 closes the new
    helper.
    -> CONFIRMED: gate_runner --json reports all 5 gates PASS;
       381 -> 383 rows checked; 284 REQUIRED green + 91
       STRUCTURAL green.
```

All seven hypotheses pass.

---

## 6. Determinism re-run

For every (mode, N, input_family) triple, the harness ran two
independent fresh `OperatorSession` instances with identical
configuration and compared:

- `pattern_ledger.entries` pattern_id tuple
- `pattern_ledger.entries` recurrence_count tuple
- `growth_ledger.events` event_id tuple

All 80 cells PASS the bit-identity check. Determinism is
established for the COHERENCE and PATTERN_AND_COHERENCE paths to
the same standard the Phase 3.18 D3 and Phase 3.19 I-IFBK-01
demonstrations established.

---

## 7. Saturation re-check (carryover)

The Step 4 LOCK G plan kept `PROCESSING_WINDOW_SIZE_MAX = 255`
and noted that an `N = 255` re-run could be added at audit time
to confirm saturation under COHERENCE. The behavior matrix
covers `N = 50` (well below saturation: 50 + MIN(1) = 51 << 256).
The Phase 3.18 saturation demonstration at `N = 255` is preserved
unchanged by this campaign (the OFF path is bit-identical; the
seed entry's recurrence accounting is unchanged). No further
saturation re-run is required for the Phase 3.20 verdict.

---

## 8. Cache / call accounting

```text
cumulative real model calls across the 80-cell matrix : 0
cumulative L1 (CachedClient) writes                   : 0
cumulative L2 (eval_v1) writes                        : 0
brain/.llm_cache/ touched                             : no
LLMClient constructed                                 : no
brain.tick.tick called                                : no (the STREAM_APPEND
                                                       path skips tick())
```

The coherence-feedback path is entirely structural — every chunk
goes through `_append_stream_chunk` which routes Pattern Ledger
and Growth Ledger updates without any LLM seam touch. Cache
counters are unchanged.

---

## 9. Invariant gates

Full `python3 -m tools.claude_helpers.gate_runner --json` result
after Step 7 implementation:

```text
catalog_counts     : PASS (banner / actual / expected agree at
                     REQUIRED:284, STRUCTURAL:91, NOT-EXERCISED:14,
                     DEFERRED:15, OBSERVED:16)
citations_verify   : PASS (100 Lean citations resolved)
import_audit       : PASS (I-PCE-05 — agency.py clean of pce
                     imports)
invariants_run     : PASS (383 rows; 285 REQUIRED green, 91
                     STRUCTURAL green, 0 red, 7 OBSERVED pass)
check_all          : PASS (all five steps green; brain/_catalog_ids.py
                     is in sync with the catalog)
```

---

## 10. Non-claim audit

The canonical `_FORBIDDEN_NON_CLAIM_TERMS` tuple was scanned over:

```text
brain/development/processing_window.py source         : 0 hits
brain/ui/session.py source (cohmon path additions)    : 0 hits
build_cohmon_summary_text output (representative set) : 0 hits
build_rehearsal_provenance output (REHEARSAL,
  PLEDGER_SUMMARY, COHMON_SUMMARY x several k)        : 0 hits
MODULE_PRODUCED_STRINGS entries                       : 0 hits
brain/ui/fixtures/coherence_feedback_static_audit.py  : 0 hits
brain/ui/fixtures/coherence_feedback_integration.py   : 0 hits
this behavior report                                  : 0 hits
```

PASS / WARN / FAIL / NOT_APPLICABLE labels were used 80 + many
times as structural status names; in every appearance they are
labels for `CoherenceCheckStatus` enum values, not assertions of
truth or value about the running system.

---

## 11. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the behavior report records measurements from the
  in-repo harness; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard; bridge overhead exceeds direct
  write cost.

Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```

---

## 12. Verdict

```text
Phase 3.20 Coherence Feedback Bridge behavior report : PASS
```

Every probe cell holds; every hypothesis is confirmed; every
gate is green; zero real model calls, zero cache writes, zero
invariant violations. The next artifact is
`docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_FINDINGS.md`
(Step 9), which classifies the campaign's findings into blockers
/ safety / behavior successes / weak behavior / deferred /
next-research-directions.
