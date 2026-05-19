# PHASE3_20_COHERENCE_FEEDBACK_BRIDGE_ROADMAP.md

## Purpose

Define the path from Phase 3.19's deterministic Pattern Ledger
summary feedback (PR #24, catalog v0.27) to a **bounded Coherence
Monitor summary feedback** prototype: read-only Coherence Monitor
reports — produced inside the processing window via a deferred
import that avoids the `coherence_monitor <-> session` circular
load — that re-enter ToyI's STREAM_APPEND path as deterministic
internal events, drive additional second-order Pattern Ledger
entries, and emit normal Growth Ledger records. No new kernel
surface, no LLM call, no schema change, no new GrowthEventType, no
mutation of any monitor check, and no consciousness-adjacent claim.

This roadmap is **research-and-engineering scaffolding**, not an
implementation order. The catalog patch plan in Step 5 fixes the
exact files, rows, fixtures, and version delta.

---

## 1. Where Phase 3.19 left ToyI

Phase 3.19 produced:

- two Pattern Ledger entries per dispatch under
  `feedback_mode == PATTERN_LEDGER` and `processing_window_size > 0`:
  the first-order entry (the seed text repeated under rehearsal
  provenance) and a second-order entry (the deterministic
  `pledger_summary` text);
- exactly `1 + 2 * N` stream chunks per dispatch under the same
  mode;
- the widened `_V1_EMITTED_SOURCES` set
  `{REHEARSAL, PLEDGER_SUMMARY}`;
- the third `InternalEventSource` member `COHMON_SUMMARY` still
  reserved and raising from `build_rehearsal_provenance`
  (LOCK F from Phase 3.19).

```text
external input
  -> _dispatch_stream_append
      -> Pattern Ledger.observe              (first-order entry, recurrence += 1)
      -> Growth Ledger.observe(STREAM_CHUNK_ACCEPTED)
      -> Growth Ledger.observe(PATTERN_ENTRY_CREATED / UPDATED)
  -> _run_processing_window(seed_chunk)
      for k in 1..processing_window_size:
        _append_stream_chunk(rehearsal text, "internal_processing_window:<k>:rehearsal")
        if feedback_mode == FEEDBACK_MODE_PATTERN_LEDGER:
            _append_stream_chunk(build_pledger_summary_text(seed_entry),
                                 "internal_processing_window:<k>:pledger_summary")
        -- COHERENCE / PATTERN_AND_COHERENCE not yet wired
```

Phase 3.19 thus produces inspectable second-order Pattern Ledger
entries from Pattern Ledger state itself, but the Coherence Monitor
remains a one-way read-only observer: its output never re-enters
the substrate it is observing.

This is the gap Phase 3.20 closes.

---

## 2. Phase 3.20 target

Add a **bounded Coherence Monitor summary feedback** path that runs
*inside* `_run_processing_window` after each rehearsal (and, if
combined mode ships, also after each pledger_summary feedback step),
emitting a deterministic Coherence Monitor summary chunk via the
existing `_append_stream_chunk` helper. Each summary chunk has:

```text
text       : deterministic Coherence Monitor summary string, of shape
             "cohmon_summary overall=<status> pass=<np> warn=<nw>
              fail=<nf> na=<nna> checks=<nc>"
             where <status> is the live CoherenceReport.overall_status.value,
             <np>/<nw>/<nf>/<nna> are the per-status counts from
             CoherenceReport.counts_by_status, and <nc> is the total
             check count.
provenance : "internal_processing_window:<k>:cohmon_summary"
source     : OPERATOR (existing TextStreamSource.OPERATOR; no new
             source value introduced)
```

The summary text has a **different structural signature** from the
seed chunk and from the Phase 3.19 `pledger_summary` chunk, so
Pattern Ledger observes it as additional second-order entries
distinct from both. Recurrence climbs deterministically across
those entries; saturation eventually kicks in at the same 256 cap.

Architecturally:

```text
external input
  -> _dispatch_stream_append (seed -> first-order Pattern Ledger entry)
  -> _run_processing_window(seed_chunk)
      for k in 1..N:
        rehearsal_chunk = _append_stream_chunk(text=seed_text,
                                               provenance=rehearsal_prov)
        -> updates first-order entry
        if feedback_mode in {PATTERN_LEDGER, PATTERN_AND_COHERENCE}:
            summary_chunk = _append_stream_chunk(
                text=build_pledger_summary_text(seed_entry),
                provenance=pledger_prov)
            -> creates / updates pledger_summary second-order entries
        if feedback_mode in {COHERENCE, PATTERN_AND_COHERENCE}:
            report = <deferred-import>.build_full_coherence_report(self,
                       snapshot_id="coh-snap-<k>")
            cohmon_chunk = _append_stream_chunk(
                text=build_cohmon_summary_text(
                    overall_status_value=report.overall_status.value,
                    pass_count=<count>, warn_count=<count>,
                    fail_count=<count>, na_count=<count>,
                    check_count=len(report.snapshot.checks)),
                provenance=cohmon_prov)
            -> creates / updates cohmon_summary second-order entries
```

The summary text is generated by a new pure function
`build_cohmon_summary_text(...)` on
`brain/development/processing_window.py`. Determinism:

```text
- Inputs: overall_status_value (str in {"pass","warn","fail",
  "not_applicable"}), pass_count / warn_count / fail_count /
  na_count (non-negative ints in a small bounded range), check_count
  (non-negative int up to COHERENCE_MAX_CHECKS = 64).
- Output: bounded printable string under STREAM_TEXT_MAX_LEN with
  no COGITO_ID inclusion, no raw chunk text inclusion, no time /
  PID / random / hostname / id() input, no forbidden non-claim
  term.
- Output for the same inputs is byte-identical across runs.
```

The helper lives on `processing_window.py` and accepts only
primitives, so the I-PWND-02 import audit continues to forbid
`brain.development.coherence_monitor` and `brain.ui.session`
imports inside the module. The session is the only caller that
joins the Coherence Monitor's report values to the helper.

Combined feedback (architecture E: `PATTERN_AND_COHERENCE`) is
**conditionally in scope** — see Step 4 LOCK D. The minimal v1
ships only the coherence-feedback path; combined feedback may be
bundled if Step 5 commits to a bounded composition that does not
expand the file set or duplicate helper logic.

---

## 3. Where the COHMON_SUMMARY member came from

Phase 3.18 introduced the closed `InternalEventSource` enum with
three members:

```python
class InternalEventSource(str, Enum):
    REHEARSAL = "rehearsal"
    PLEDGER_SUMMARY = "pledger_summary"   # widened in Phase 3.19
    COHMON_SUMMARY = "cohmon_summary"     # reserved; unlocked here
```

`PLEDGER_SUMMARY` was reserved in Phase 3.18 specifically for the
Phase 3.19 pattern-ledger feedback expansion, which shipped it.
`COHMON_SUMMARY` was reserved in the same enum for the next
deferred bridge — the bridge this campaign closes.

Phase 3.20 widens `_V1_EMITTED_SOURCES` to include
`COHMON_SUMMARY` so `build_rehearsal_provenance(tick_index=k,
source=InternalEventSource.COHMON_SUMMARY)` produces a bounded
printable provenance string of shape
`"internal_processing_window:<k>:cohmon_summary"` instead of
raising.

---

## 4. The import-seam problem

`brain/development/processing_window.py` is closed by its
I-PWND-02 audit: its import set is exactly
`{__future__, dataclasses, enum, typing,
brain.development.text_stream, brain.tlica.profile}`. It cannot
import `brain.development.coherence_monitor`, `brain.ui.session`,
or any wider TLICA / UI module.

`brain/development/coherence_monitor.py` already imports
`brain.ui.session.OperatorSession` to walk the live session and
build the report. A direct `processing_window -> coherence_monitor`
import would break the I-PWND-02 audit; a direct
`coherence_monitor -> processing_window` already exists (only via
the FORBIDDEN_NON_CLAIM_TERMS constant import in fixtures, not the
module itself), and a session-level call works because the session
already imports the processing window helpers.

The Phase 3.20 architecture resolves the seam with **three
disjoint moves**:

1. `processing_window.py` gains a new pure helper
   `build_cohmon_summary_text(...)` that accepts only bounded
   primitives. The helper does NOT import the Coherence Monitor;
   it composes a bounded printable string from values the caller
   already extracted.

2. `session.py` gains a new `_run_cohmon_feedback_step(*,
   tick_index)` helper that performs a **deferred import** of
   `brain.development.coherence_monitor.build_full_coherence_report`
   inside the function body (no module-level addition), extracts
   the bounded primitives from the live `CoherenceReport`, calls
   `build_cohmon_summary_text(...)` for the bounded text, calls
   `build_rehearsal_provenance(..., source=COHMON_SUMMARY)` for
   the provenance, and dispatches a chunk through
   `_append_stream_chunk`. The session already calls
   `build_full_coherence_report` from the existing
   `_dispatch_inspect_view` for the `/coherence` view; the
   processing-window helper reuses the same public surface from a
   different call site.

3. `_run_processing_window` gains a single new branch: if
   `feedback_mode in {COHERENCE, PATTERN_AND_COHERENCE}`, call
   `_run_cohmon_feedback_step` after the rehearsal (and after the
   pledger_summary feedback step, under `PATTERN_AND_COHERENCE`).
   On any bounded-substrate refusal, the existing
   abort-window-cleanly semantics apply.

Resulting graph:

```text
processing_window.py        --(pure primitives only)-->  build_cohmon_summary_text
brain.development.coherence_monitor.py   --(imports)-->  brain.ui.session.OperatorSession
brain.ui.session.py        --(deferred import in body)-> brain.development.coherence_monitor
brain.ui.session.py        --(module-level)----------->  processing_window helpers
```

No circular import at module load: `coherence_monitor` still
imports `OperatorSession`; `session` does not add a module-level
import of `coherence_monitor`. The deferred import inside
`_run_cohmon_feedback_step` mirrors the pattern session already
uses for `AutosaveConfig`, `SessionStoreConfig`, and
`AutosaveStatusReport` in `__post_init__`.

---

## 5. Three vs four vs deferred mode taxonomy

Five candidate FeedbackMode shapes considered:

```text
A. OFF / PATTERN_LEDGER                  (Phase 3.19; shipped)
B. add COHERENCE                          (minimal v1; preferred)
C. add COHERENCE and PATTERN_AND_COHERENCE (bundled v1; OK if simple)
D. add COHERENCE only and defer combined to Phase 3.21
E. defer everything to Phase 3.21         (rejected: Phase 3.20 mission)
```

Step 4 LOCK D selects between B / C / D. The roadmap's default is
**C** (bundle combined) because:

- the combined mode is a pure composition of two helpers the
  campaign already commits to (`build_pledger_summary_text` and
  `build_cohmon_summary_text`);
- the chunk-count formula remains a deterministic
  `1 + alpha * N` where `alpha in {1, 2, 2, 3}` for `OFF`,
  `PATTERN_LEDGER`, `COHERENCE`, `PATTERN_AND_COHERENCE`
  respectively;
- it lets H3 (combined feedback creates more inspectable structure
  than single-mode feedback) be tested in v1;
- it adds no extra runtime file beyond what the COHERENCE mode
  already requires.

Step 4 may downgrade to **B** or **D** if the patch plan turns up a
correctness blocker.

---

## 6. Window sizes and input set for the probe

Re-used from Phase 3.19 with one extension:

```text
window sizes:  0, 5, 10, 50
inputs:        repeated motif
               contradiction pair
               self-reference phrase
               neutral factual text
               emotionally valenced text
modes:         OFF
               PATTERN_LEDGER
               COHERENCE                              (Phase 3.20 v1)
               PATTERN_AND_COHERENCE                   (Phase 3.20 v1 if
                                                       LOCK D bundles
                                                       combined; else
                                                       planned)
recommended high-window default: N = 50
runtime cap:                     PROCESSING_WINDOW_SIZE_MAX = 255
```

Per-mode chunk-count formula:

```text
OFF                      : 1 + 0   = 1     (plus N rehearsals = 1 + N)
PATTERN_LEDGER           : 1 + 2N
COHERENCE                : 1 + 2N
PATTERN_AND_COHERENCE    : 1 + 3N
```

Per-mode minimum Pattern Ledger entry count:

```text
OFF                      : 1
PATTERN_LEDGER           : >= 2 (seed + pledger_summary family)
COHERENCE                : >= 2 (seed + cohmon_summary family)
PATTERN_AND_COHERENCE    : >= 3 (seed + pledger_summary + cohmon_summary)
```

The cohmon_summary text varies as recurrence climbs (because the
report's counts shift across rehearsals); the probe matrix in
Step 3 quantifies the resulting second-order entry growth.

---

## 7. Testable hypotheses for the synthesis (Step 2 captures)

```text
H1. FeedbackMode.COHERENCE emits exactly N bounded coherence-summary
    chunks per dispatch (one per rehearsal step). Chunk count =
    1 + 2N; second-order entries >= 1 distinct from the seed.
H2. Coherence feedback produces a distinct second-order Pattern
    Ledger entry whose pattern_id differs from any pledger_summary
    entry (different structural signature).
H3. PATTERN_AND_COHERENCE produces more inspectable structure than
    PATTERN_LEDGER alone (>= 3 distinct Pattern Ledger entries) and
    is bit-deterministic across runs.
H4. PASS/WARN/FAIL/NOT_APPLICABLE labels are preserved as
    structural status only and never recoded as truth claims in any
    bounded printable string the campaign produces.
H5. No scalar aggregate I-ness, awareness, or growth score appears
    in the runtime, the catalog, the fixtures, or the docs.
H6. 50-window runs remain bounded: chunk count exactly 1 + 2*50 =
    101 under COHERENCE, 1 + 3*50 = 151 under
    PATTERN_AND_COHERENCE; Pattern Ledger entry count stays under
    PATTERN_LEDGER_MAX_ENTRIES; cumulative real model calls = 0.
H7. The I-PWND-02 static import audit still passes; the new helper
    does not introduce any forbidden import. The I-COHMON-10 audit
    on the Coherence Monitor module still passes (the monitor is
    unchanged).
```

---

## 8. Out of scope for v1

```text
- REPL / worldlet feedback (architectures D / E from Phase 3.19's
  taxonomy);
- model-generated reflection over feedback events;
- a new GrowthEventType (FEEDBACK_CHUNK_EMITTED, etc.);
- a new GrowthEventSource (PROCESSING_WINDOW, etc.);
- aggregate scalar coherence / pattern / growth scores;
- a /coherence-feedback UI verb or a new ACTIVE_VIEW;
- promoting any DEFERRED or NOT-EXERCISED row;
- relaxing the COHERENCE_MAX_CHECKS = 64 cap;
- mutating any Coherence Monitor check;
- raising PROCESSING_WINDOW_SIZE_MAX above 255;
- L1 / L2 cache changes;
- parser / prompt / DB / autosave changes;
- SelfModel.
```

---

## 9. Catalog skeleton (informational; Step 5 binds exact text)

Anticipated catalog additions:

```text
I-CFBK-01  Engineering hypothesis (Phase 3.20 Coherence Feedback Bridge)
           REQUIRED
           Module:  brain/development/processing_window.py,
                    brain/ui/session.py
           Fixture: brain/ui/fixtures/coherence_feedback_integration.py
           Body:    bounded coherence-feedback integration across
                    modes OFF / PATTERN_LEDGER / COHERENCE
                    (and PATTERN_AND_COHERENCE if bundled), with
                    deterministic chunk counts, deterministic
                    Pattern Ledger entry IDs, and bounded growth.

I-CFBK-02  Engineering hypothesis (Phase 3.20 Coherence Feedback Bridge)
           STRUCTURAL
           Module:  brain/development/processing_window.py
           Fixture: brain/ui/fixtures/coherence_feedback_static_audit.py
           Body:    closed FeedbackMode value set, validation
                    rejections, build_cohmon_summary_text
                    determinism + bounded printable + non-claim
                    clean output, widened _V1_EMITTED_SOURCES to
                    include COHMON_SUMMARY, MODULE_PRODUCED_STRINGS
                    extension, no new forbidden import in
                    processing_window.py.

I-PWND-02   body widens: emit set becomes
            {REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY};
            build_rehearsal_provenance(..., COHMON_SUMMARY)
            now produces a non-claim-clean bounded provenance.

I-IFBK-02   body note: COHMON_SUMMARY is no longer reserved in
            v1; the static-audit assertion that it raises is
            replaced by an assertion that it produces a
            non-claim-clean bounded provenance.
```

Catalog version: v0.27 -> v0.28. Counts: REQUIRED 283 -> 284,
STRUCTURAL 90 -> 91; NOT-EXERCISED 14 unchanged; DEFERRED 15
unchanged; OBSERVED 16 unchanged.

---

## 10. Validation skeleton

Before every commit that lands files:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

On gate_runner failure:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Step 7 additionally runs the new behavior harness once before
commit. Step 8 re-runs it for the report. Step 10 records the
canonical preflight in the audit doc.

---

## 11. Branching / PR plan

```text
branch:        campaign/phase3-20-coherence-feedback-bridge
base initial:  current Phase 3.19 HEAD (PR #24 still open)
final PR:      base = campaign/phase3-19-internal-feedback-loop
               (while PR #24 is open)
               base = main
               (once PR #24 has merged; retarget before final PR
                preparation)
title:         phase3.20: coherence feedback bridge
merge policy:  never merge without explicit user approval
```

---

## 12. Disclosure expectation

Each step's final report includes the canonical Stage A / Stage B /
Stage C.1 block. Stage C.1 may draft doc shards; parent Claude
commits and pushes every step; no Stage C.1 broad runtime edits.

---

## 13. Next step pointer

After Step 1 commits + pushes, the next eligible step is **Step 2
Coherence Feedback Synthesis** at
`docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_SYNTHESIS.md`.
