# PHASE3_17_PROCESSING_WINDOW_PROBE_PLAN.md

## Purpose

Step 6 of Phase 3.17: convert the seven hypotheses from
`PHASE3_17_PROCESSING_WINDOW_SYNTHESIS.md` (H1–H7) into a
concrete measurement matrix. This plan defines what to measure,
how, with which inputs, and which observations would falsify
the synthesis.

The probes themselves run during Step 8 (and any future
implementation campaign). This Step-6 document is the
specification.

---

## 1. Experiment matrix

### 1.1 Window-size axis

```text
N = 0      external tick only (negative control)
N = 1      one internal tick after the external tick
N = 5      five internal ticks
N = 10     ten internal ticks
N = 50     the experimental default proposed in the synthesis
```

### 1.2 Mode axis

```text
mock         in-process MockClient; no real model call.
             Use for hypothesis testing where call count is the
             dependent variable.

claude-cli   real model-backed via the local `claude` CLI.
             Available in this checkout per Phase 3.16.
             Use sparingly; this is the production-shaped path.

codex-cli    real model-backed via the local `codex` CLI;
             unblocked by the Phase 3.17 Step 3 patch.
             Use sparingly; this is the production-shaped path.
```

`anthropic-api` is **not** in the matrix because the checkout
lacks `ANTHROPIC_API_KEY` / `BRAIN_ANTHROPIC_API_KEY` and adding
one is out of scope.

### 1.3 Input-type axis

The same five canonical inputs from the Step 5 synthesis:

```text
I1. Repeated motif
    Example: "a short neutral note about traffic patterns."
    Then queue a second external percept with similar text and
    a different content_id. Pattern Ledger should observe
    recurrence on the structural signature.

I2. Contradiction pair
    Example A: "Two and two make four."
    Example B: "Two and two make five."
    Both go through the public QueuePerceptPayload route. The
    probe is whether the system carries the pair through
    consolidation without producing an aggregate truth/agency
    claim.

I3. Self-reference statement
    Example: "This system has a profile domain of finite size."
    Important: the text is a description; ToyI does not
    "self-recognize." The probe is whether the parser / model
    handles a self-referential phrasing without parse failure.

I4. Emotionally valenced text
    Example: "I felt joy when the program completed."
    The probe is whether the parser remains strict and the
    Coherence Monitor's `_FORBIDDEN_NON_CLAIM_TERMS` audit
    rejects any new code path that leaks the forbidden vocabulary
    (Coherence Monitor source strings).

I5. Neutral factual text
    Example: "Snow is composed of crystalline water."
    Baseline; closest to the Step 4 codex smoke input.
```

### 1.4 Per-output measurements

For every (N, mode, input-type) cell:

```text
M01. tick count actually executed inside the window (<= N).
M02. external tick count (always 1 in this matrix).
M03. internal tick count (M01 - M02).
M04. real model call count (counted via BudgetGuardClient).
M05. CachedClient L1 hit / miss / skip counters.
M06. LLMBackedPtCns L2 hit / miss / store / skip (best-effort;
     today these counters only surface via trace events under
     NullTracer; M06 may be reported as "trace-only" in v1).
M07. profile.domain — set BEFORE and AFTER the window, plus the
     delta (added/removed; "removed" should always be empty for
     v1 since the kernel never removes profile entries).
M08. msi.contents — set BEFORE and AFTER, plus the delta.
M09. PtCns eval_map — keys BEFORE and AFTER (each value is a
     ConsistencyEval enum; counts per enum are reported, NOT raw
     text).
M10. Pattern Ledger entries — count BEFORE and AFTER; per
     surviving entry, the (signature, recurrence_count,
     confidence, saturation_state) tuple.
M11. Growth Ledger event count BEFORE and AFTER; counts_by_type
     BEFORE and AFTER; the count delta per event_type.
M12. Coherence Monitor report counts_by_status BEFORE and AFTER;
     overall_status BEFORE and AFTER; any new FAIL detail.
M13. session.status_message and session.error_message at end.
M14. session.tick_counter BEFORE and AFTER (sanity: AFTER == BEFORE
     + M01).
M15. wall-clock duration of the window (ms).
M16. peak number of cache files (count only, never content) under
     brain/.llm_cache and brain/.llm_cache/eval_v1 — counts only,
     and the cache directory remains gitignored.
M17. fingerprint hash prefix of internal events: for each internal
     PerceptEvent the window emits, the SHA-256 prefix of
     (content_id, text, provenance), reported as an 8-char prefix.
     Body text is NEVER quoted.
```

### 1.5 Cell count

```text
window sizes   × modes        × input types  = cells
        5      ×    3         ×    5         =  75
```

Step 8 does NOT run all 75 cells. Step 8 only runs the
**negative-control row** (N=0 across all modes and input types),
plus, if mock implementation can be assembled WITHOUT a runtime
change, a small bounded slice (e.g. mock × {N=1, N=5} × {I1, I5}).

Any expansion beyond Step 8's negative-control + mock-light slice
requires an operator-approved follow-up campaign (Step 7 review
gate).

---

## 2. Mapping hypotheses → cells

```text
H1 (at N=0, only external deltas appear):
    cells           : every (N=0, mode, I*).
    pass criterion  : every internal-source Growth Ledger event
                      count is exactly 0 in EVERY N=0 cell;
                      provenance=internal_processing_window
                      appears nowhere.
    fail criterion  : any internal-source event present at N=0.

H2 (L2 absorbs identical internal repeats):
    cells           : N=50, mode in {claude-cli, codex-cli},
                      input=I1 (repeated motif).
    pass criterion  : M04 (real call count) <<  M01 (internal
                      ticks), e.g. M04 <= ceil(M01 / 5).
    fail criterion  : M04 ~= M01 (no absorption).

H3 (mock at N=50 has zero real calls, sub-second wall clock):
    cells           : N=50, mode=mock, all input types.
    pass criterion  : M04 == 0 and M15 < 1000 ms.
    fail criterion  : M04 > 0 or M15 >= 1000 ms.

H4 (real-mode call count tracks distinct canonical keys):
    cells           : N=50, mode in {claude-cli, codex-cli},
                      input ∈ {I1 (repeats), I5 (neutral)}.
    pass criterion  : M04 ~= number of distinct
                      (msi_context, new_text) keys produced;
                      strictly less than M01.
    fail criterion  : M04 == M01 (no L2 absorption).

H5 (no new FAIL under any window):
    cells           : every cell.
    pass criterion  : M12 overall_status AFTER is never FAIL when
                      it was not FAIL BEFORE.
    fail criterion  : a new FAIL emerges under N > 0 that did not
                      exist under N = 0.

H6 (no aggregate scalar appears):
    cells           : every cell.
    pass criterion  : the new code path produces no
                      `consciousness_score`, `i_ness`, `awareness`,
                      `growth_score`, or any other scalar
                      summary; only labeled tuples (Coherence
                      counts_by_status, Growth counts_by_type)
                      appear.
    fail criterion  : any such scalar appears in any new field
                      or any report string.

H7 (N=5 vs N=50 differ in saturation):
    cells           : N=5 and N=50, mode=mock, input=I1.
    pass criterion  : at N=50 the Pattern Ledger for the
                      synthesized internal entries reaches
                      SATURATED (recurrence_count ==
                      STREAM_PATTERN_RECURRENCE_MAX) at least
                      once; at N=5 it does NOT.
    fail criterion  : both N=5 and N=50 reach the same
                      saturation state (i.e., 50 is too large or
                      5 is already enough).
```

---

## 3. Failure limits and stop conditions

```text
F1. Call-budget cap.
    Stop the whole campaign before total real model calls
    reach 20.
    Per probe step: stop the probe before its declared local
    cap is reached.
    Recorded budget consumed so far: 1 / 20.

F2. Cache cap.
    Stop the probe if L1 *.json count or L2 *.json count
    exceeds 90% of the configured cap (920 of 1024) in any
    cell. The window is then aborted and the report records
    the cap interaction.

F3. Parse failure threshold.
    Stop the probe if more than 3 consecutive internal ticks
    record `parse.failure` (the strict parser is locked; one or
    two are tolerable, three in a row indicates a deeper issue).

F4. Invariant failure threshold.
    Any new FAIL from `assert_state_invariants` aborts the
    probe immediately. The campaign considers an invariant
    failure under N > 0 (that was green under N = 0) a
    blocking finding for Step 9.

F5. Wall-clock cap.
    Any single window run that exceeds 5 minutes wall-clock
    aborts. (Step 4 measured ~12.5 s per codex-cli real call;
    N=50 under codex-cli would project to ~10 minutes, which
    is already above this cap; that is the intended forcing
    function for L2 absorption.)

F6. Out-of-scope diff.
    Any probe that produces a non-empty diff outside the
    declared write set (e.g., docs/campaigns/phase3_17/) aborts
    and the diff is preserved for inspection.

F7. Bridge non-retry.
    If any Stage A / Stage B / Stage C.1 bridge used during the
    campaign returns `CODEX_NETWORK_TRANSIENT`, the campaign
    stops; no automatic retry.
```

---

## 4. Probe runners (DESIGN ONLY)

The runner shapes below are **specifications**, not v1 code.

### 4.1 Runner R1 — Window=0 negative control

```text
1. session = OperatorSession(state=initial_state())
2. dispatch(Command(QUEUE_PERCEPT, payload=<I*>))
3. dispatch(Command(STEP_TICK), client=<mode-specific>)
4. record M01..M16 with N=0 (i.e., no internal ticks fired)
5. final state, ledger, report -> CSV row
```

R1 runs entirely on **existing public surfaces**. No runtime
change. Step 8 ships R1.

### 4.2 Runner R2 — Window>0 with synthesized internal events

```text
1. as in R1, then:
2. for k in 1..N:
   2a. consult Pattern Ledger + Coherence Monitor + (optionally)
       prior PtCns evals to choose a source (S1 / S2 / S3) per
       the synthesis Section 4.
   2b. construct a deterministic content_id (e.g.
       "int:pledger:<pattern_id>:<tick>") that is NOT in
       state.profile.domain and is NOT COGITO_ID.
   2c. construct bounded printable text; provenance =
       "internal_processing_window:<tick>:<source>".
   2d. dispatch(Command(QUEUE_PERCEPT, payload=<internal>))
       and dispatch(Command(STEP_TICK), client=<mode-specific>)
   2e. if any failure occurs, break out of the loop and record
       the abort cause.
3. record M01..M16 with the final N actually executed.
```

R2 needs a deterministic generator and a strict bounded text
discipline. It is **DESIGN ONLY** in Phase 3.17; the actual code
ships in a follow-up campaign behind the Step 7 review gate.

---

## 5. What Step 8 actually runs

Per the synthesis Section 8 and the Step 8 acceptance criteria,
Step 8 of Phase 3.17 **only** runs:

```text
S8.1  R1 on  N=0, mode=mock,        I=I5   (mock baseline)
S8.2  R1 on  N=0, mode=mock,        I=I1   (mock motif)
S8.3  R1 on  N=0, mode=claude-cli,  I=I5   (real baseline)
      [optional, budget permitting]
S8.4  R1 on  N=0, mode=codex-cli,   I=I5   (real baseline)
      [optional, budget permitting]
```

Each of these uses only the existing public surfaces. The 75-cell
matrix above is the specification for a future operator-approved
campaign; Step 8 demonstrates the methodology on the safest cells
plus, optionally, a couple of real-model baseline cells if the
campaign budget permits.

Step 8 may also include a **counterfactual measurement**: at N=0,
deliberately attempt to synthesize an internal event by calling
`dispatch(Command(QUEUE_PERCEPT, payload=<internal>))` AFTER the
external tick succeeds — but without running STEP_TICK on it.
This proves the negative control: an internal event queued but
NOT stepped does NOT produce any Growth Ledger /
Pattern Ledger / Coherence Monitor delta beyond the queue size.

---

## 6. Reporting format (per cell)

Each cell's row is a JSON-safe dict with these keys:

```text
cell_id            : "N{N}-mode{mode}-input{I}"
N                  : int
mode               : "mock" | "claude-cli" | "codex-cli"
input_type         : "I1" .. "I5"
M01_tick_count     : int
M02_external       : int
M03_internal       : int
M04_real_calls     : int
M05_l1             : {hit, miss, skip}
M06_l2             : {hit, miss, store, skip} or
                     "trace-only" if not externally observable
M07_profile_delta  : {added, removed}
M08_msi_delta      : {added, removed}
M09_eval_counts    : {pre: {PRESERVE: n, DAMAGE: n, NEUTRAL: n},
                      post: {...}}
M10_pledger        : {pre_count, post_count, signatures: [...]}
M11_growth         : {pre, post, counts_by_type_delta: {...}}
M12_coherence      : {pre_overall, post_overall,
                      counts_by_status_delta: {...},
                      new_fail_details: [...]}
M13_status         : "<bounded printable>"
M13_error          : "<bounded printable>"
M14_tick_counter   : {pre, post}
M15_duration_ms    : int
M16_cache_files    : {l1_pre, l1_post, l2_pre, l2_post}
M17_event_fingerprints : ["8-char-hex prefix", ...]
abort_cause        : null | "F1" | "F2" | ... | "F7"
```

No raw text body of any input / prompt / response appears in any
row. Only counts, deltas, enum names, and short hash prefixes.

---

## 7. Constraint sanity

```text
brain/tick.py                       : not modified by this plan
brain/llm/parse.py                  : not modified
brain/llm/prompts.py                : not modified
brain/llm/ptcns_backed.py           : not modified
brain/ui/session.py                 : not modified by this plan
INVARIANT_CATALOG.md                : not modified
tools/catalog.py                    : not modified
brain/.llm_cache contents           : never quoted
raw prompts / responses             : never quoted
secrets                             : never present, never printed
catalog v0.25 / 281/88/14/15/16     : unchanged
```

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: this is a measurement specification derivable from the
  Step 5 synthesis; no external review required.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer of this plan.

Stage C.1 flow orchestration:
- used: no
- reason: a single self-contained doc; bridge overhead exceeds
  the cost of writing directly.
```

---

## 9. Real model call accounting

```text
mode tested:                       n/a (doc only)
calls used in this step:           0
cumulative campaign calls:         1 / 20
```

---

## 10. Next artifact

Step 7:
`docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_IMPLEMENTATION_PLAN.md`
— the design-only, review-gated implementation plan for the
processing-window prototype.
