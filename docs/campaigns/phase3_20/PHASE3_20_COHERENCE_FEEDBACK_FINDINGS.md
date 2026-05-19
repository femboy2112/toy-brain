# PHASE3_20_COHERENCE_FEEDBACK_FINDINGS.md

## Purpose

Triage the Phase 3.20 Coherence Feedback Bridge campaign into
blockers, safety / invariant findings, behavior successes, weak
behavior, deferred enhancements, and next research directions.

The campaign's behavior report (Step 8) is the empirical basis for
every claim in this document.

---

## 1. Blockers

```text
NONE.
```

The campaign reached every macro step (1..10 here, 11 next) with
all gates green at every commit. The one issue encountered during
Step 7 — a docstring containing the forbidden non-claim term
`truth` — was caught by the I-PWND-02 source-scan within seconds
of the change and fixed in the same step. No blocker required
Stage A / Stage B / Stage C.1 escalation or operator intervention.

---

## 2. Safety / invariant findings

```text
- Catalog v0.27 -> v0.28 binds two new rows (I-CFBK-01 REQUIRED,
  I-CFBK-02 STRUCTURAL); both PASS in the runner. brain/_catalog_ids.py
  was regenerated and committed; tools/catalog.py EXPECTED_COUNTS
  matches; check_all.sh sees no drift.
- I-PWND-02 body update (widened emit set) PASSes the static AST
  audit against the modified module: the import set is still the
  closed {__future__, dataclasses, enum, typing,
  brain.development.text_stream, brain.tlica.profile}; no
  brain.development.coherence_monitor import was added inside
  processing_window.py.
- I-IFBK-02 body update (FeedbackMode value set widened;
  COHMON_SUMMARY-raises assertion replaced with non-claim-clean
  emit assertion) PASSes the fixture.
- The deferred function-body import in
  OperatorSession._run_cohmon_feedback_step does NOT introduce a
  module-level cycle. coherence_monitor still imports
  OperatorSession at module load; session.py imports
  build_full_coherence_report only at function-call time. The
  pattern matches the established Phase 3.9 / 3.10c precedent for
  SessionStoreConfig / AutosaveConfig / AutosaveStatusReport
  in OperatorSession.__post_init__.
- The cross-check inside build_cohmon_summary_text
  (check_count == pass + warn + fail + na) prevents the helper
  from producing inconsistent text if a future CoherenceReport
  shape ever drifts.
- The non-claim audit (canonical _FORBIDDEN_NON_CLAIM_TERMS scan)
  PASSes on the new helper output, the new module strings, both
  new fixtures, the existing fixtures' updated bodies, and the
  Phase 3.20 docs in this directory.
- The PASS / WARN / FAIL / NOT_APPLICABLE labels are used
  throughout as structural status names; the campaign deliberately
  avoids any prose that would recode them as truth assertions
  about the running system.
- No new GrowthEventType, no new GrowthEventSource, no new
  TextStreamSource value, no new OperatorCommand, no new
  ACTIVE_VIEWS value, no schema change, no SCHEMA_VERSION bump,
  no autosave change.
- L1 and L2 cache counters unchanged. brain/.llm_cache/ untouched.
- OFFLINE remains the default; model-backed modes remain explicit
  opt-in; the LLM client was never constructed during the 80-cell
  behavior matrix.
- brain/tick.py untouched (verified by repo diff against the
  Phase 3.19 branch HEAD).
```

No safety or invariant finding requires follow-up.

---

## 3. Behavior successes

```text
S1. Chunk-count determinism: every cell in the 80-cell matrix
    produced exactly the expected number of stream chunks per the
    locked formula 1 + alpha * N. Zero mismatches.

S2. Cross-process determinism: every (mode, N, input) triple
    produced bit-identical Pattern Ledger pattern_id tuples,
    bit-identical recurrence_count tuples, and bit-identical
    Growth Ledger event_id tuples across two independent fresh
    sessions. Zero determinism failures.

S3. Invariant safety: assert_state_invariants(state) remained
    green across every cell. Zero invariant failures.

S4. Zero model footprint: cumulative real model calls = 0
    across the 80-cell matrix. Cache counters unchanged.

S5. Non-claim cleanliness: the _FORBIDDEN_NON_CLAIM_TERMS scan
    returned zero hits across helper outputs, module sources,
    fixtures, and docs.

S6. Coherence Monitor stability: every cell's overall_status
    came back "pass", confirming that the deterministic
    Coherence Monitor produces consistent structural-status
    summaries on every fresh OperatorSession reachable through
    the public STREAM_APPEND path.

S7. Combined-mode composition: PATTERN_AND_COHERENCE produces
    deterministic 1 + 3N chunks, 4..7 Pattern Ledger entries,
    with per-family observation sums each equal to N. The
    pledger family and cohmon family stay disjoint and both
    disjoint from the seed entry.

S8. Saturation discipline preserved: the seed entry's
    recurrence_count formula min(MIN + N, MAX) holds regardless
    of feedback_mode. The Phase 3.18 saturation demonstration at
    N = 255 remains valid (the OFF path is bit-identical).
```

---

## 4. Weak behavior

```text
W1. cohmon-family Pattern Ledger entry collapse: under COHERENCE
    mode at N >= 5, the N cohmon_summary chunks collapse into
    EXACTLY ONE second-order Pattern Ledger entry whose recurrence
    climbs by N. The collapse happens because the bounded
    build_cohmon_summary_text output is signature-stable across
    rehearsals when the Coherence Monitor's per-status counts
    don't shift between steps (every check stays "pass"). This
    is functionally correct (recurrence accounting still totals
    N) and was anticipated by the synthesis (cohmon_summary text
    "may produce one or several distinct signatures"). It does
    mean H2's "distinct second-order entry per cohmon chunk"
    reading is NOT confirmed in the strict sense — only the
    narrower reading "at least one distinct second-order entry"
    is. The I-CFBK-01 assertion is written to the narrower
    reading and PASSes; the wider reading would be a future
    enhancement (W1 follow-up).

W2. pledger-family entry counts vary across input families:
    under PATTERN_LEDGER at N=10 and N=50, the pledger-family
    entry count is 4..5 or 5..6 depending on input (a single
    extra entry appears for some inputs). This was also true
    under Phase 3.19 and is not a regression. The variation is
    deterministic per input, so determinism still holds; the
    cross-input variation only shows up in the aggregated
    matrix view.

W3. No coherence-status SHIFT was observed in any cell because
    the Coherence Monitor always returns overall_status "pass"
    on a fresh OperatorSession. The behavior matrix therefore
    does NOT exercise the bounded printable variation across
    pass / warn / fail / not_applicable. A future probe could
    deliberately construct an OperatorSession whose monitor
    returns WARN or FAIL and assert that the cohmon_summary
    text changes accordingly (W3 follow-up).

W4. The 50-window dimension is well under saturation
    (50 + 1 = 51 << 256). Saturation behavior under COHERENCE
    and PATTERN_AND_COHERENCE was NOT exercised at N = 255 in
    this campaign (the audit may optionally re-run at N = 255;
    Step 4 LOCK G left this discretionary).
```

None of W1..W4 are runtime bugs. They are gaps in the behavior
matrix's coverage of behaviors the implementation supports.

---

## 5. Deferred enhancements

Carried over from the corrigenda + roadmap:

```text
D1. REPL / worldlet feedback (architectures from Phase 3.19
    taxonomy). Out of scope for v1; revisit in Phase 3.22 or
    later.

D2. Model-generated reflection over feedback events. Out of
    scope for v1 (LOCK I).

D3. A new GrowthEventType / GrowthEventSource specifically for
    feedback chunks. Out of scope; LOCK F deliberately reuses
    existing events.

D4. Aggregate scalar coherence / feedback / I-ness score.
    Permanently out of scope per the campaign non-claim policy.

D5. /coherence-feedback UI verb or new ACTIVE_VIEW. Out of
    scope; no UI surface added.

D6. Raising PROCESSING_WINDOW_SIZE_MAX above 255. Out of scope.

D7. A bounded "deliberately-tilted CoherenceReport" probe set
    that exercises cohmon_summary text changes across
    PASS / WARN / FAIL / NOT_APPLICABLE statuses. New (W3
    follow-up); a candidate for Phase 3.21 or a one-doc
    addendum to this campaign.

D8. A "per-cohmon-chunk distinct signature" probe matrix that
    deliberately constructs sessions where each rehearsal step
    shifts the report's per-status counts. New (W1 follow-up);
    candidate for Phase 3.21.

D9. Coherence Monitor check-set expansion (e.g., new checks for
    the new feedback chunks themselves) is OUT OF SCOPE per
    LOCK E.
```

---

## 6. Next research directions

```text
R1. Coherence Feedback Bridge bridges the Pattern Ledger and
    Coherence Monitor surfaces into one bounded feedback loop.
    The next logical extension is "developmental trajectory" —
    can ToyI exhibit recognizable structural transitions across
    a sequence of distinct behaviors that approximate a human-
    development trajectory? This is the queued Phase 3.21
    Developmental Trajectory campaign captured in
    /home/leah/brain/toy-brain/PHASE3_HANDOFF_STATE.md.

R2. The cohmon-family entry collapse (W1) suggests that the
    structural-signature granularity of Pattern Ledger may be
    too coarse for some feedback-text variations to surface
    as distinct entries. A follow-up campaign could probe the
    signature space deliberately and either accept the collapse
    as the correct behavior (current default) or refine the
    signature derivation (LOCK on Pattern Ledger semantics
    forbids this in v1).

R3. The coherence-feedback path is structurally close to a
    conflict-monitoring-like architecture from cognitive
    neuroscience. A bounded follow-up could exercise the FAIL /
    WARN paths deliberately to confirm the path produces
    distinct second-order entries when the monitor's overall
    status varies (W3 follow-up).

R4. REPL / worldlet feedback (D1) remains the next architectural
    bridge after the Coherence Feedback Bridge. A Phase 3.22 or
    later campaign could explore whether bounded REPL output or
    worldlet-simulation output can re-enter the same
    STREAM_APPEND substrate without breaking import discipline.

R5. The current Phase 3.20 implementation does not exercise
    the model-backed seam at all. A reviewed Phase 3.X campaign
    could explore whether a real LLM call ON the feedback chunk
    (not for producing it) yields useful structural signal
    while preserving the campaign budget. The LLM seam is
    untouched today.
```

---

## 7. Cross-campaign carryovers

```text
- /pattern-ledger / /coherence-summary / /growth-ledger UIs
  remain DEFERRED at catalog level.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- Tracer wiring through OperatorSession.dispatch remains
  DEFERRED.
- SelfModel implementation remains OUT OF SCOPE.
```

None of these carryovers were touched or aggravated by
Phase 3.20.

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the findings synthesize the behavior report and the
  repo state directly; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard.

Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```

---

## 9. Next artifact

`docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_AUDIT.md`
— the Step 10 final audit, which records the verdict (PASS /
PASS WITH DEFERRED FOLLOW-UPS / PARTIAL / BLOCKED / FAIL),
canonical preflight result, and the next-campaign recommendation.
