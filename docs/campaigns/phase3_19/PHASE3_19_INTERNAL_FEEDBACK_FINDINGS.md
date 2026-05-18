# PHASE3_19_INTERNAL_FEEDBACK_FINDINGS.md

## Purpose

Classify the empirical and engineering findings from Phase
3.19 Steps 1–8 by category, naming each follow-up
explicitly so the next campaign can pick up the trail. This
doc is the audit trail for Step 10's verdict.

---

## 1. Blockers

```text
None.
```

Every Phase 3.19 step landed cleanly. Steps 1–5 produced the
required doc artifacts; Step 6 Review Gate A accepted the
plan as written; Step 7 implementation passed all five
canonical gates with `gate_runner --json` reporting 5/5
PASS; Step 8 behavior report showed 0 invariant failures and
0 determinism failures across the 40-cell probe matrix.

---

## 2. Safety / invariant findings

```text
None.
```

Explicit verifications:

```text
- I-CAT-01 coverage audit               : PASS
- I-PCE-05 import audit                 : PASS
- All Phase 3.18 rows (I-PWND-01..02)   : PASS
- All Phase 3.13 rows (I-GROW-01..22)   : PASS
  (I-GROW-14 updated to cover the new Phase 3.19 attr tier)
- All Phase 3.12c rows (I-PLEDGER-* /
  I-COHMON-*)                           : PASS
- All persistence resource-audit rows
  (I-OBSERVE-08 / I-OPSHARDEN-13)       : PASS
  (folded the new _PHASE_3_19_SESSION_ATTRS frozenset
  into the allowed union)
- New Phase 3.19 rows
  I-IFBK-01 / I-IFBK-02                 : PASS
- Non-claim discipline                  : PASS (0 hits
  across 8 representative summary-text inputs and the
  widened build_rehearsal_provenance probe set)
- Kernel invariant gate
  (assert_state_invariants(state))      : PASS on every
  cell
```

No regression in any prior catalog row.

---

## 3. Behavior successes

```text
S1. The feedback path produces inspectable second-order
    Pattern Ledger entries deterministically. Every
    PATTERN_LEDGER N>0 cell creates >= 2 entries.

S2. Seed entry recurrence is unaffected by feedback chunks.
    The hypothesis that rehearsal and feedback advance
    distinct entries (H2 in the synthesis) holds exactly:
    seed recurrence_count = min(2 + N, 256) in every cell
    of both M0 and M1 modes.

S3. The conservation law on second-order observations holds
    invariantly:
        SUM over second-order entries of
          (recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1)
        == N
    across all 20 PATTERN_LEDGER cells. No off-by-one drift.

S4. The 1 + 2*N stream-chunk count is exact in every
    PATTERN_LEDGER cell with N > 0.

S5. Determinism is byte-equal across two independent
    sessions for every PATTERN_LEDGER N>0 cell. pattern_id
    tuples, recurrence_count tuples, and Growth Ledger
    event_id tuples all match exactly (15 re-runs).

S6. Zero real model calls across the full 40-cell suite.
    0 / 20 budget consumed.

S7. Zero L1 / L2 cache writes across the full 40-cell suite.
    brain/.llm_cache/ remains gitignored and untouched.

S8. Kernel invariants remain green on every cell, including
    N = 50 cells with 6 Pattern Ledger entries and 113
    Growth Ledger events.

S9. The default FeedbackMode.OFF preserves Phase 3.18
    rehearsal-only behavior bit-for-bit, confirmed against
    every M0 cell.

S10. Catalog upgrade landed cleanly: v0.26 -> v0.27 with
     282/89 -> 283/90 counts; tools/catalog.py
     EXPECTED_COUNTS strict-gate PASS; brain/_catalog_ids.py
     regenerated cleanly; README.md / mission / campaign
     baselines updated.
```

---

## 4. Weak behavior / observations

```text
W1. The number of distinct second-order entries depends on
    the integer digit-shape of <recurrence_count> in the
    summary text. At N = 50, this clusters into 3-6
    entries per input rather than a single second-order
    entry. This is structurally correct (Pattern Ledger
    keys on the chunk's structural signature, not the
    semantic content), but it is a research-level
    consideration: a deterministic single-entry shape
    would require a fixed-width integer representation
    in the summary template.

    Mitigation: explicitly noted in the Step 3 probe
    matrix Section 3.2 (Resolution paragraph). The
    behavior report records the actual entry count per
    input rather than asserting a fixed count. A future
    campaign can re-engineer the template (e.g., zero-
    padded integers) to collapse to one second-order
    entry without modifying the invariants.

W2. At N = 50 with feedback ON, none of the second-order
    entries reach SATURATED. The highest observed
    recurrence on a second-order entry was 27 (in I1
    motif). This is expected: a 50-tick window spreads
    50 observations across multiple structural clusters,
    so no single cluster sees enough observations to
    saturate. Saturation under the feedback path would
    require either a much larger N or a single-second-
    order-entry template (W1).

W3. Growth Ledger event count under PATTERN_LEDGER at
    N = 50 ranges 111-113 per input — well under the
    GROWTH_LEDGER_MAX_EVENTS = 256 cap, but a longer
    feedback chain would eventually saturate the Growth
    Ledger. This is the same hard-cap discipline Phase
    3.18 noted; at N = 255 with feedback ON, the Growth
    Ledger would reach its cap and subsequent observe
    calls would return self unchanged (Phase 3.13
    behavior preserved).

W4. The behavior report harness lives at /tmp and is not
    committed (mission policy). Reproducing the table
    requires re-running it; the audit fixture
    (internal_feedback_integration.py) does the same
    checks programmatically inside the runner. Drift
    between harness and fixture is avoided because both
    use the same public surfaces.
```

None of W1-W4 is a regression or a blocker. All are
follow-up considerations for the next campaign.

---

## 5. Deferred enhancements

```text
D1. Coherence Monitor feedback (architecture C / LOCK F).
    Reserved enum value InternalEventSource.COHMON_SUMMARY
    continues to raise. Re-opening this lock requires a
    bounded design that resolves the
    brain.development.coherence_monitor ->
    brain.ui.session circular import without breaking
    the I-PWND-02 audit boundary.

D2. Combined feedback (architecture D). Pattern + coherence
    feedback in a single window step. DEFERRED until D1
    ships.

D3. REPL feedback (architecture E). Proto-BASIC REPL-driven
    internal observation. DEFERRED.

D4. Worldlet feedback (architecture F). WorldletHistory-
    driven internal observation. DEFERRED.

D5. Model-generated reflection over feedback events.
    Currently the feedback text is template-driven.
    Allowing the LLM to produce the summary text (or
    evaluate the feedback chunk) would consume real model
    calls and require an explicit budget; DEFERRED.

D6. Single-second-order-entry summary-text template.
    Re-engineer build_pledger_summary_text to use fixed-
    width integers (e.g., %03d) so every <n> produces
    the same structural signature. Would collapse the
    feedback chain to one second-order entry whose
    recurrence_count climbs linearly with N. Useful for
    saturation experiments at large N. DEFERRED (W1).

D7. Saturation experiment at N = 255 under
    feedback_mode = PATTERN_LEDGER. Phase 3.18's N = 255
    demonstration saturates the seed entry; under the
    feedback path with the current template, second-order
    entries climb but do not saturate. A bundled demo
    would extend the Phase 3.18 demonstration with the
    feedback ON variant. DEFERRED.

D8. SelfModel. The whole-campaign mission keeps this OUT
    OF SCOPE. The Phase 3.19 second-order Pattern Ledger
    entry is structurally close to "a record about the
    system's own activity" but does not implement a
    SelfModel. A future campaign would need an explicit
    review gate.

D9. Persistence of feedback state across /save-session /
    /load-session. Phase 3.19's feedback_mode is a
    session field; like growth_ledger and pattern_ledger,
    it is NOT serialized. A future campaign could add
    feedback-state persistence behind its own catalog
    patch. DEFERRED.

D10. UI surfaces for feedback mode. No new
     OperatorCommand, no new typed verb, no /feedback-*
     UI. Operators set feedback_mode at session
     construction time only. DEFERRED.

D11. Aggregate scalar over feedback state. Explicitly
     forbidden in the mission and the synthesis. Will
     remain DEFERRED indefinitely under the current
     non-claim discipline.
```

---

## 6. Next research directions

```text
R1. Operationally close LOCK F. Design a bounded
    Coherence-Monitor-summary feedback path that does not
    break the I-PWND-02 audit boundary. Two viable shapes:
    (a) extract the Coherence summary computation into a
    leaf module callable from processing_window.py without
    importing brain.ui.session; (b) compute the summary
    inside session.py before the window starts and pass it
    to the helper as a bounded primitive. Either choice
    requires a new catalog patch and Stage A review.

R2. Single-second-order-entry summary template variant
    (D6). The simplest research question is whether
    collapsing to one entry produces a CLEANER inspection
    surface than the current digit-shape clustering. A
    parallel template variant audit could compare.

R3. Feedback-driven Growth Ledger saturation. At what
    cumulative N does GROWTH_LEDGER_MAX_EVENTS = 256
    plateau under the feedback path? Phase 3.13 already
    proves Growth Ledger saturation is a hard-cap no-op;
    Phase 3.19 strengthens the observation that this is
    operationally reachable from a single external input.

R4. Two-input feedback interaction. The current matrix
    uses a single seed per session. A two-input scenario
    (sequential STREAM_APPEND of two different texts each
    with their own window) would test whether second-
    order entries from input A and B compose deterministic-
    ally. Should be a small extension to the harness;
    catalog-row-bearing only if a new invariant emerges.

R5. Model-backed reflection. Once R1 ships and the
    behavior report is rich enough, a future campaign can
    introduce LLM-generated summaries behind an explicit
    budget. Strictly DEFERRED until D1 / D5 are unlocked.

R6. Behavior under the Phase 3.17 real-codex-cli /
    claude-cli routes. The Phase 3.19 feedback path makes
    zero model calls, so its behavior is independent of
    the model-backed routes. A combined audit confirming
    that a real-model /step preceding a STREAM_APPEND +
    window remains bit-identical between OFF and ON
    feedback modes would close the operational story.
```

---

## 7. Cross-campaign accounting

```text
Phase 3.17 + 3.18 + 3.19 cumulative real model calls : 2 / 20
  (Phase 3.18 used 0; Phase 3.17 used 2 against claude-cli
   per its audit. Phase 3.19 uses 0.)
Budget remaining                                     : 18
Operator approvals consumed                          : 0
Stage A / B / C.1 bridge invocations in Phase 3.19    : 0
```

---

## 8. Files changed across Phase 3.19

```text
Added:
  PHASE3_19_INTERNAL_FEEDBACK_LOOP_ROADMAP.md
  docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_SYNTHESIS.md
  docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_PROBE_MATRIX.md
  docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_CORRIGENDA.md
  docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_CATALOG_PATCH_PLAN.md
  docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_BEHAVIOR_REPORT.md
  docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_FINDINGS.md
  brain/ui/fixtures/internal_feedback_integration.py
  brain/ui/fixtures/internal_feedback_static_audit.py

Modified:
  CURRENT_MISSION.md
  CURRENT_CAMPAIGN.md
  README.md
  INVARIANT_CATALOG.md
  brain/_catalog_ids.py
  brain/development/processing_window.py
  brain/development/fixtures/growth_ledger_session_integration.py
  brain/ui/session.py
  brain/ui/fixtures/persistence_observe_resource_audit.py
  brain/ui/fixtures/persistence_ops_resource_audit.py
  brain/ui/fixtures/processing_window_static_audit.py
  brain/invariants.py
  tools/catalog.py
```

---

## 9. Stage A / B / C.1 disclosure

```text
Stage A ChatGPT/Codex consultation : not used in Phase 3.19
Stage B limited-write collaboration: not used in Phase 3.19
Stage C.1 flow orchestration       : not used in Phase 3.19
```

Reason in every case: the campaign's bounded scope made
parent-Claude direct edits cheaper than bridge overhead;
the gates and behavior report ran deterministically with
no external review required.

---

## 10. Next artifact

`docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_AUDIT.md`
— Step 10 final audit with explicit verdict and the canonical
disclosure block per the campaign mission's Step 10 contract.
