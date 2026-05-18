# PHASE3_17_PROCESSING_WINDOW_INITIAL_TEST.md

## Purpose

Step 8 of Phase 3.17: execute the **negative-control row** of the
Step 6 probe matrix using only existing public surfaces, plus a
**counterfactual** demonstrating that an internal-looking event
queued without `/step` produces no downstream change. No runtime
patch was applied for this step.

This step is the only Phase 3.17 step that **runs**, post-Step-4,
on the probe-plan methodology. It uses harness scripts under
`/tmp/` (not committed); the results below are the only artifacts.

---

## 1. What ran

Four cells, plus one counterfactual. Each cell is `N=0`
(the negative control), which is exactly the existing
single-tick path through `OperatorSession.dispatch`:

```text
S8.1  N=0, mode=mock,       input=I5  (neutral factual)
S8.2  N=0, mode=mock,       input=I1  (repeated motif text)
S8.4  N=0, mode=codex-cli,  input=I5  (real model baseline)
CF    counterfactual: queue an internal-shaped event,
      do NOT call /step
```

`S8.3` (claude-cli) was not run; Phase 3.16 already demonstrated
that route. Mock runs use `MockClient(["NEUTRAL"])`; the codex
run uses the patched factory (`CachedClient(BudgetGuard(CodexCLIClient))`).

Harness path (not committed): `/tmp/phase3_17_initial_probe.py`.

---

## 2. Cell-level results

### 2.1 S8.1 — N=0, mock, I=I5

```text
M01_tick_count            : 1
M02_external              : 1
M03_internal              : 0
M04_real_calls            : 0
M05_l1                    : n/a (mock has no cache wrapper here)
M07_profile_delta.added   : ["probe-S8.1-mock-I5"]
M07_profile_delta.removed : []
M08_msi_delta.added       : []
M09_eval_counts.pre       : {PRESERVE: 1}
M09_eval_counts.post      : {PRESERVE: 1, NEUTRAL: 1}
M10_pledger.pre_count     : 0
M10_pledger.post_count    : 0
M11_growth.pre            : 0
M11_growth.post           : 2
M11_growth.delta          : 2
M11_growth.internal_src   : 0
M12_coherence.pre_overall : pass
M12_coherence.post_overall: pass
M12_coherence.pre_counts  : pass=21, warn=0, fail=0, na=8
M12_coherence.post_counts : pass=22, warn=0, fail=0, na=7
M13_status                : "tick 1 ok (NEUTRAL)"
M13_error                 : ""
M14_tick_counter          : 0 -> 1
M15_duration_ms           : <1 ms
M16_cache_files           : L1 pre=2 post=2; L2 pre=2 post=2
M17_event_fingerprints    : ["c5400cc9"]
outcome                   : ok
```

Observation: the single external NEUTRAL tick added one
`content_id` to the profile domain. The MSI did NOT grow because
NEUTRAL maps via `ModeOp.from_eval` to a mode that does not
integrate into MSI. Two Growth Ledger events were emitted — both
from the external `STEP_DISPATCH` (`TICK_SUCCEEDED` +
`PROFILE_DOMAIN_ADDED`); **zero** events carry an
`internal_processing_window` provenance. Pattern Ledger is
untouched because `/stream` was not called. Coherence stayed PASS;
one `NOT_APPLICABLE` flipped to PASS because
`kernel.latest_tick_index_agrees` became applicable after the
first tick.

### 2.2 S8.2 — N=0, mock, I=I1

Structurally identical to S8.1:

```text
M01_tick_count            : 1
M03_internal              : 0
M04_real_calls            : 0
M07_profile_delta.added   : ["probe-S8.2-mock-I1"]
M11_growth.delta          : 2
M11_growth.internal_src   : 0
M12_coherence.pre/post_overall : pass / pass
M13_status                : "tick 1 ok (NEUTRAL)"
M16_cache_files           : L1 2/2; L2 2/2
M17_event_fingerprints    : ["c72a0602"]
outcome                   : ok
```

The repeated-motif input still produces exactly one tick at N=0;
without internal ticks, the Pattern Ledger has nothing to compare
the motif against. This is the H1 evidence: at N=0, only the
external delta appears.

### 2.3 S8.4 — N=0, codex-cli, I=I5

```text
M01_tick_count            : 1
M03_internal              : 0
M04_real_calls            : 1   (consumed by codex-cli)
M05_l1                    : hit=0 miss=1 skip=0
M07_profile_delta.added   : ["probe-S8.4-codex-I5"]
M07_profile_delta.removed : []
M08_msi_delta             : added=[] removed=[]
M09_eval_counts.post      : {PRESERVE: 1, NEUTRAL: 1}
M10_pledger.post_count    : 0
M11_growth.delta          : 2
M11_growth.internal_src   : 0
M12_coherence.pre/post_overall : pass / pass
M13_status                : "tick 1 ok (NEUTRAL)"
M14_tick_counter          : 0 -> 1
M15_duration_ms           : 7_724   (one real codex call)
M16_cache_files           : L1 pre=2 post=3 (+1); L2 pre=2 post=3 (+1)
M17_event_fingerprints    : ["6181b9a1"]
outcome                   : ok
```

The codex-cli baseline at N=0 produced exactly the same
**structural** result as the mock baselines: one external tick,
one PROFILE_DOMAIN_ADDED, no internal-source events, coherence
PASS. The wall-clock cost is real (7.7 s; one model call); the L1
+ L2 cache directories each grew by one entry (the codex-cli L2
namespace; isolated from the prior claude-cli entries on disk).

### 2.4 CF — counterfactual queue without step

```text
queued content_id     : "int:pledger:probe-counterfactual-1:0"
queued provenance     : "internal_processing_window:0:pledger"
fingerprint           : "cb4ce3a7"

pre.queue_size        : 0
post.queue_size       : 1   (the only changed field)

delta.tick_counter             : 0
delta.profile_domain_added     : []
delta.msi_contents_added       : []
delta.growth_event_delta       : 0
delta.pledger_entry_delta      : 0
delta.coherence_overall_change : None
delta.queue_size_delta         : 1
```

Even with a well-shaped internal-style payload sitting in the
queue, **none** of profile / MSI / PtCns / Growth Ledger /
Pattern Ledger / Coherence Monitor changed. The queue grew by 1
and the status_message reports the queued percept; that is the
only observable session-level effect.

This is the direct demonstration that an `internal_processing_window`
provenance string by itself does nothing — the bounded effects we
attribute to "internal processing" come from `_dispatch_step`
running, which Phase 3.17 has not authorized for internal events
in v1.

---

## 3. Hypothesis evaluation from N=0 evidence

```text
H1. At window=0, only external deltas appear.
    Result: PASS for every cell (S8.1, S8.2, S8.4, CF).
            internal_source_count = 0 in every case.
            No GrowthEvent.provenance contains
            "internal_processing_window".

H2. L2 absorbs identical internal repeats.
    Result: UNTESTABLE at N=0 by construction; deferred to a
            future implementation campaign behind GATE-PW-1..5.

H3. Mock at N=50 has 0 real calls, sub-second wall clock.
    Result: UNTESTABLE at N=0 (need an N>0 internal loop). What
            we CAN observe at N=0 mock: zero real calls,
            sub-millisecond wall clock per tick. This is
            consistent with H3 holding under any future
            mock-loop implementation, but does not prove it.

H4. Real-mode call count tracks distinct canonical keys.
    Result: UNTESTABLE at N=0 (one tick = one canonical key by
            definition). The Phase 3.16 Step 5 walk B already
            demonstrated L2 absorption (same text, different
            content_id, 0 model calls on the second tick) under
            claude-cli; the Phase 3.17 codex run did not exercise
            that path because we only ran one tick.

H5. No new FAIL under any window.
    Result: PASS for every cell. Coherence overall stayed PASS
            across S8.1, S8.2, S8.4. No new FAIL emerged.

H6. No aggregate scalar appears.
    Result: PASS. Every observable count is a labeled tuple
            (Coherence counts_by_status, Growth counts_by_type).
            No new scalar field was emitted by any code path in
            this probe.

H7. N=5 vs N=50 differ in saturation.
    Result: UNTESTABLE at N=0 by construction; deferred.
```

Two hypotheses pass on the N=0 evidence (H1, H5, H6). Four
hypotheses (H2, H3, H4, H7) require an internal-tick loop that
Phase 3.17 does not implement; they remain open for the future
campaign authorized through GATE-PW-1..5.

---

## 4. Why this is the right scope for Step 8

Per the synthesis Section 8 and the implementation plan Section 1:

```text
- Phase 3.17 deliberately does not ship a runtime processing-
  window loop.
- Step 8's purpose is to demonstrate the methodology on the
  safest cells (negative control + counterfactual) and confirm
  the inspection surface produces meaningful data.
- The 75-cell matrix from the Step 6 plan is the specification
  for a future operator-approved campaign.
```

The data above shows the methodology works:

```text
- Every Step-6 measurement (M01..M17) is reportable from the
  existing public surfaces, except M06 (L2 hit/miss/store/skip)
  which is currently only observable via trace events under the
  default NullTracer (Phase 3.16 follow-up F2).
- M11_growth.internal_src is a clean, falsifiable signal that
  would flip from 0 to nonzero the moment a runtime
  processing-window loop emits its first internal-provenance
  event.
- The counterfactual confirms that the bounded effects we care
  about flow from /step, not from queue contents alone.
```

---

## 5. What this step does NOT do

```text
- Does not implement the architecture-A processing window.
- Does not modify brain/tick.py, brain/ui/session.py,
  brain/llm/*, brain/development/*, or any catalog file.
- Does not produce per-cell measurements for N > 0.
- Does not test parser ambiguity under verbose model output
  (Phase 3.16 F3).
- Does not exercise L1 / L2 cache caps (the run used 2-3 entries;
  the caps are 1024 each).
- Does not test the contradiction-pair input (I2), the
  self-reference input (I3), or the valenced input (I4). Those
  are reserved for the future operator-approved campaign.
```

---

## 6. Real model call accounting

```text
S8.1 mock baseline               : 0
S8.2 mock motif                  : 0
S8.4 codex-cli baseline          : 1     (7.7 s)
CF   counterfactual              : 0
Step 8 subtotal                  : 1

Cumulative across the campaign   : 2 / 20
Remaining budget                 : 18
```

---

## 7. Constraint sanity

```text
brain/tick.py                       : not modified
brain/ui/session.py                 : not modified
brain/llm/*                         : not modified beyond Step 3
brain/development/*                 : not modified
INVARIANT_CATALOG.md                : not modified
tools/catalog.py                    : not modified
brain/.llm_cache contents           : not committed (gitignored;
                                      counts only above)
raw prompts / responses             : not committed; only hash
                                      prefixes and parsed enum
secrets                             : not present, not printed
gate_runner                         : will re-run before commit
catalog v0.25                       : unchanged
counts                              : 281 / 88 / 14 / 15 / 16
                                      unchanged
real model calls used               : 2 / 20
```

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the probe is a direct measurement over existing
  surfaces; no external review was required to interpret
  M01..M17.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer; the harness lives
  under /tmp and is not committed.

Stage C.1 flow orchestration:
- used: no
- reason: the runner is a single in-process Python harness; the
  campaign-level Phase 3.17 policy forbids Stage C.1 for the
  real codex-cli loop.
```

---

## 9. Next artifact

Step 9:
`docs/campaigns/phase3_17/PHASE3_17_FINDINGS.md` — classify the
codex fix, the codex model route result, the processing-window
feasibility, the runtime-design need, the next implementation
campaign recommendation, and any blockers / deferred work.
