# PHASE3_20_COHERENCE_FEEDBACK_SYNTHESIS.md

## Purpose

A structural analysis of where Phase 3.19 left ToyI, why
pattern-ledger feedback alone leaves the Coherence Monitor as a
one-way observer, and what the smallest bounded path looks like
that lets the monitor's own structural status re-enter the
processing path as new evidence. This document is research-and-
engineering scaffolding; nothing in it claims ToyI is conscious,
sentient, aware, intentional, introspective, metacognitive, or
phenomenologically present. It asserts only that a deterministic
summary text, derived from a freshly built `CoherenceReport`
(bounded printable `PASS / WARN / FAIL / NOT_APPLICABLE` per-check
status counts), can re-enter the same `STREAM_APPEND` path the
seed used — and that doing so produces additional **second-order**
Pattern Ledger entries that record the system's own structural
self-monitoring at a structural level only.

`PASS / WARN / FAIL / NOT_APPLICABLE` are treated throughout as
**structural statuses**, never as truth claims about the running
system.

---

## 1. Where Phase 3.19 left ToyI

Phase 3.19 (PR #24, catalog v0.27) shipped the bounded Pattern
Ledger feedback path:

```text
external STREAM_APPEND
  -> _append_stream_chunk(text=seed_text, provenance="operator")
     -> first-order Pattern Ledger entry created or updated
     -> Growth Ledger STREAM_CHUNK_ACCEPTED + PATTERN_ENTRY_*
  -> _run_processing_window(seed_chunk)
       for k in 1..N:
         _append_stream_chunk(
           text=seed_text,
           provenance="internal_processing_window:<k>:rehearsal",
         )
         -> same first-order entry, recurrence += 1
         -> more Growth Ledger events
         if feedback_mode is FeedbackMode.PATTERN_LEDGER:
             _run_feedback_step(tick_index=k, seed_pattern_id=...)
               -> _append_stream_chunk(
                    text=build_pledger_summary_text(seed_entry),
                    provenance="internal_processing_window:<k>:pledger_summary",
                  )
                  -> second-order Pattern Ledger entry created or updated
                  -> more Growth Ledger events
```

Empirical results inherited from
`docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_BEHAVIOR_REPORT.md`:

```text
OFF (N=0)                    : 1 chunk; 1 entry; recurrence = MIN
OFF (N=5/10/50)              : 1+N chunks; 1 entry
PATTERN_LEDGER (N=0)         : strict no-op; identical to OFF
PATTERN_LEDGER (N=5)         : 11 chunks; >= 2 entries; deterministic
PATTERN_LEDGER (N=10)        : 21 chunks; >= 2 entries; deterministic
PATTERN_LEDGER (N=50)        : 101 chunks; >= 2 entries; deterministic
non-claim audit              : PASS across helpers and produced strings
real model calls             : 0
cache writes                 : 0
brain/tick.py                : unchanged
```

So as of v0.27, ToyI's runtime **recognizes** structural recurrence
reliably (Phase 3.18) AND can **feed Pattern Ledger summaries back
into itself** as bounded printable text (Phase 3.19).

### 1.1 What "feedback" means here

In Phase 3.19, feedback is:

- after each rehearsal, look up the just-updated Pattern Ledger
  entry by `derive_pattern_id(derive_pattern_signature(seed_chunk))`;
- compose a deterministic summary text of shape
  `"pledger_summary pattern_id=<id> recurrence=<n>/256 sat=<state>"`;
- re-enter that text through the existing `_append_stream_chunk`
  call site under provenance
  `"internal_processing_window:<k>:pledger_summary"`;
- the summary chunk's structural signature differs from the seed
  chunk's structural signature, so Pattern Ledger.observe creates
  a second-order entry that records "ToyI's own recurrence has
  reached count N" at the structural-signature level.

This is feedback at the **level of bounded printable structural
summary**. It does not involve meaning, semantic class, language,
truth, agency, introspection, or metacognition.

---

## 2. The gap: feedback only over Pattern Ledger

Phase 3.19 closes one of the three remaining deferred bridges
identified in the Phase 3.18 synthesis. Two remain open at the
start of Phase 3.20:

### 2.1 Coherence Monitor is still strictly read-only

`brain/development/coherence_monitor.py` builds a
`CoherenceReport` from the live `OperatorSession`:

- `build_kernel_checks(session)` — six structural agreements over
  the kernel record (cogito-in-profile, cogito-in-msi, profile
  values bounded in `[0, 1]`, ptcns eval_map keys equal profile
  domain, msi contents subset of profile domain, latest_tick
  index agrees with session tick counter);
- `build_session_checks(session)` — five structural agreements
  over the operator session (no unsafe resources, active view in
  the documented view set, event queue bounded, status/error text
  bounded printable, pattern ledger field is a resource-safe
  `PatternLedger`);
- `build_stream_checks(session)` — four structural agreements
  over the stream history and candidate list;
- `build_pattern_ledger_checks(session)` — six structural
  agreements over Pattern Ledger entries;
- `build_persistence_autosave_checks(session)` — five structural
  agreements over the persistence / autosave configuration;
- `build_nonclaim_checks(checks_so_far)` — two structural
  agreements that no produced string contains a forbidden
  non-claim term and no aggregate scalar I-ness score appears.

Each check produces a `CoherenceCheck(check_id, status, summary,
detail, source)` with `status` in
`{PASS, WARN, FAIL, NOT_APPLICABLE}`. The aggregate
`CoherenceReport.overall_status` is `FAIL > WARN > PASS >
NOT_APPLICABLE`. The monitor is **never called from inside the
dispatch path**; an operator invokes it for inspection via the
`/coherence` view dispatcher. The Phase 3.19 processing window
cannot use coherence summary state because nothing produces one
in flight.

The `InternalEventSource` enum still has three members
`{REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}`, but the
`_V1_EMITTED_SOURCES` frozenset is still
`{REHEARSAL, PLEDGER_SUMMARY}`. `build_rehearsal_provenance(..., 
source=COHMON_SUMMARY)` still raises `ValueError` per LOCK F.

### 2.2 No combined-mode feedback yet

`FeedbackMode` has exactly two members
`{OFF, PATTERN_LEDGER}`. There is no
`COHERENCE` member and no `PATTERN_AND_COHERENCE` member, so
ToyI cannot today be configured to run both feedback paths in
one dispatch.

### 2.3 REPL / worldlet feedback remain DEFERRED

Architectures D and E from the Phase 3.19 synthesis remain
out-of-scope per the campaign's macro deferrals; the
`brain/development/repl.py` and `brain/development/worldlet.py`
substrates are not consulted during the processing window. They
are not Phase 3.20's target.

---

## 3. Proposed coherence feedback loop and event shape

Phase 3.20 adds a third feedback variant. Its end-to-end shape:

```text
external STREAM_APPEND
  -> _append_stream_chunk(text=seed_text, provenance="operator")
     -> first-order Pattern Ledger entry created or updated
     -> Growth Ledger STREAM_CHUNK_ACCEPTED + PATTERN_ENTRY_*
  -> _run_processing_window(seed_chunk)
       for k in 1..N:
         rehearsal_chunk = _append_stream_chunk(
           text=seed_text,
           provenance="internal_processing_window:<k>:rehearsal",
         )
         if feedback_mode in {PATTERN_LEDGER, PATTERN_AND_COHERENCE}:
             _run_feedback_step(tick_index=k, seed_pattern_id=...)
               -> appends pledger_summary chunk
         if feedback_mode in {COHERENCE, PATTERN_AND_COHERENCE}:
             _run_cohmon_feedback_step(tick_index=k)
               -> defer-imports build_full_coherence_report
               -> extracts (overall_status_value, per-status counts,
                  total check count) from the fresh CoherenceReport
               -> calls build_cohmon_summary_text(...) for the
                  bounded printable text
               -> calls build_rehearsal_provenance(...,
                  source=InternalEventSource.COHMON_SUMMARY) for the
                  bounded printable provenance
               -> _append_stream_chunk(text=summary_text,
                                       provenance="internal_processing_window:<k>:cohmon_summary")
                  -> additional second-order Pattern Ledger entries
                  -> more Growth Ledger events
```

Each coherence-feedback chunk has:

```text
text       : deterministic Coherence Monitor summary string of shape
             "cohmon_summary overall=<status> pass=<np> warn=<nw>
              fail=<nf> na=<nna> checks=<nc>"
             where <status> is the live CoherenceReport.overall_status.value,
             <np>/<nw>/<nf>/<nna> are the per-status counts pulled from
             CoherenceReport.counts_by_status, and <nc> is the total check
             count.
provenance : "internal_processing_window:<k>:cohmon_summary"
source     : OPERATOR (existing TextStreamSource.OPERATOR; no new source)
```

The summary text has a structurally distinct signature from the
seed chunk (different length, different distinct-char ratio,
different repeat ratio) AND from the Phase 3.19 `pledger_summary`
chunk (different prefix, different token set). So
`PatternLedger.observe` records additional second-order entries
distinct from both.

The bounded inputs that the helper accepts:

```text
overall_status_value : str in {"pass", "warn", "fail", "not_applicable"}
pass_count           : non-negative int (small bounded, <= COHERENCE_MAX_CHECKS = 64)
warn_count           : non-negative int (same bound)
fail_count           : non-negative int (same bound)
na_count             : non-negative int (same bound)
check_count          : non-negative int (same bound)
```

Each input is a primitive: no `CoherenceReport`, no
`CoherenceCheck`, no `OperatorSession`, no callable, no handle.
`build_cohmon_summary_text` rejects every other type with a
typed `ValueError` for the same reasons
`build_pledger_summary_text` does.

---

## 4. Candidate architectures

Five candidate architectures considered:

### Architecture A — session-level summary builder, primitives helper on processing_window.py

`brain/ui/session.py` calls `build_full_coherence_report(self)`
inside a new `_run_cohmon_feedback_step` helper (via a deferred
import to avoid a circular load with `coherence_monitor`),
extracts bounded primitives from the live report, and passes them
to a new pure helper `build_cohmon_summary_text(...)` on
`brain/development/processing_window.py`. The helper composes the
bounded printable text; the session emits the chunk through
`_append_stream_chunk` with the same provenance / growth
mechanics it already uses for the Phase 3.19 pledger_summary
chunks.

```text
+ keeps processing_window.py closed-import substrate clean
+ keeps coherence_monitor.py read-only (no mutation, no import
  of new surfaces)
+ session.py is already the only caller of build_full_coherence_report
  (existing /coherence inspect view), so reusing the same surface
  here adds no new external coupling
+ deferred import in a function body avoids the cycle without
  needing a TYPE_CHECKING guard or a module split
+ the bounded helper on processing_window.py is bit-for-bit
  symmetric with build_pledger_summary_text
+ supports trivial composition for the combined mode
- requires touching session.py (already true for Phase 3.19;
  no new file added)
```

### Architecture B — narrow coherence summary record on processing_window.py without importing coherence_monitor

processing_window.py grows a new closed record type
`CohmonSummaryRecord` that wraps the same bounded primitives, and
session.py passes the primitives through that record before
producing the text. The helper still accepts only primitives.

```text
+ adds a typed boundary at the cost of one extra class
- duplicates the dataclass shape Pattern Ledger / Coherence
  Monitor already maintain
- extra record buys little: build_cohmon_summary_text already
  validates each primitive
- net effect is a wrapper around the primitives Architecture A
  already accepts directly
```

Rejected as duplicative.

### Architecture C — processing_window.py imports coherence_monitor directly

processing_window.py imports
`brain.development.coherence_monitor.build_full_coherence_report`
at module load and calls it from inside its own helper.

```text
- breaks the I-PWND-02 import audit (allowed import set is
  exactly {__future__, dataclasses, enum, typing,
  brain.development.text_stream, brain.tlica.profile}); adding
  coherence_monitor would force the audit to widen
- coherence_monitor imports OperatorSession, so this also
  introduces a transitive brain.ui.session dependency from
  processing_window
- would require processing_window to accept an OperatorSession,
  bringing it into the UI graph
```

Rejected as boundary-breaking.

### Architecture D — defer coherence feedback to Phase 3.21

processing_window.py and session.py are unchanged; the
`InternalEventSource.COHMON_SUMMARY` member remains reserved;
`FeedbackMode` stays at `{OFF, PATTERN_LEDGER}`. The campaign
ships only documentation.

```text
- fails the Phase 3.20 mission target (no runtime coherence feedback)
- leaves the reserved enum member dangling for a third campaign
```

Rejected as scope failure.

### Architecture E — combined pattern + coherence feedback mode

Adds `FeedbackMode.PATTERN_AND_COHERENCE` on top of
Architecture A. The new mode fires both Phase 3.19's
`_run_feedback_step` and the new `_run_cohmon_feedback_step`
after each rehearsal. The chunk-count formula becomes
`1 + 3N`; Pattern Ledger entry count is `>= 3` (seed +
pledger_summary family + cohmon_summary family).

```text
+ tests H3 (combined feedback creates more inspectable structure
  than single-mode feedback) in v1
+ no extra runtime file required beyond Architecture A
+ pure composition: each fired helper is independently
  deterministic
- adds one more enum member and a small branch in
  _run_processing_window
- combined chunks per dispatch grows linearly (alpha = 3 vs 2);
  still bounded by N <= 255
- introduces a tighter cross-coupling between feedback modes that
  must be tested explicitly
```

Conditionally accepted (Step 4 LOCK D selects).

---

## 5. Preferred architecture for v1

**A + E** is preferred. A is mandatory; E is conditionally
bundled.

Rationale:

- A is the smallest extension that fires the coherence-feedback
  loop without breaking the I-PWND-02 import boundary;
- the deferred-import-in-function-body pattern is already used in
  session.py's `__post_init__` for `SessionStoreConfig`,
  `AutosaveConfig`, and `AutosaveStatusReport` — adding it for
  `build_full_coherence_report` follows the established repo
  convention;
- E is cheap because both helpers are independently pure; the new
  mode is a single new enum value plus one extra branch in
  `_run_processing_window`;
- the resulting taxonomy is symmetric: each non-OFF mode adds one
  bounded feedback chunk per rehearsal, optionally a second one
  under combined mode.

If Step 5 turns up evidence that bundling E doubles the catalog
test surface, LOCK D may downgrade to architecture A only and
defer E to Phase 3.21. The synthesis recommends A + E.

---

## 6. Testable hypotheses

```text
H1. FeedbackMode.COHERENCE emits exactly N bounded coherence-summary
    chunks per dispatch (one per rehearsal step). Chunk count
    under COHERENCE = 1 + 2N; Pattern Ledger entry count >= 2;
    second-order entries distinct from the seed entry.
H2. Each cohmon_summary chunk produces a distinct second-order
    Pattern Ledger entry whose pattern_id differs from any
    pledger_summary entry under PATTERN_LEDGER (different
    structural signature, different prefix, different token set).
H3. Under FeedbackMode.PATTERN_AND_COHERENCE, the runtime emits
    1 + 3N chunks per dispatch and produces >= 3 distinct
    Pattern Ledger entries (seed + pledger_summary family +
    cohmon_summary family); the combined run is bit-deterministic
    across processes and OSes.
H4. PASS / WARN / FAIL / NOT_APPLICABLE labels are preserved as
    structural status only and never recoded as truth claims in
    any bounded printable string the campaign produces. The
    canonical _FORBIDDEN_NON_CLAIM_TERMS audit produces zero
    hits on the new helper outputs and the new fixtures.
H5. No scalar aggregate I-ness, awareness, growth, or
    coherence-feedback score appears in the runtime, the catalog,
    the fixtures, or the docs.
H6. 50-window runs remain bounded: chunk count exactly
    1 + 2*50 = 101 under COHERENCE, 1 + 3*50 = 151 under
    PATTERN_AND_COHERENCE; Pattern Ledger entry count stays
    under PATTERN_LEDGER_MAX_ENTRIES = 1024; cumulative real
    model calls = 0; cache writes = 0.
H7. No invariant, import, or non-claim boundary violation: the
    I-PWND-02 static audit still passes; the I-COHMON-10 static
    audit on the Coherence Monitor module still passes (the
    monitor is unchanged); the new fixture's I-CFBK-02 audit
    closes the new helper.
```

---

## 7. Why this is not introspection

The architecture deliberately avoids language that would suggest
metacognition:

- the Coherence Monitor is a read-only structural diagnostic over
  the live records; its check list is fixed and audited by
  I-COHMON-04..08 at module-load time;
- the report's `PASS / WARN / FAIL / NOT_APPLICABLE` labels are
  treated as **structural statuses** about whether bounded
  invariants currently hold across kernel / session / stream /
  pattern-ledger / persistence-autosave records — not as a
  judgment about the running system's truth, value, or state;
- the feedback chunk is a bounded printable string composed from
  per-status integer counts and the overall status value; it
  contains no propositional content, no recommendation, no
  decision, no first-person language;
- the chunk re-enters Pattern Ledger via the same
  `STREAM_APPEND` substrate every other chunk uses; Pattern
  Ledger.observe treats it as a piece of structural evidence,
  not as a claim;
- no Growth Ledger event type is added; the new chunk produces
  exactly the same `STREAM_CHUNK_ACCEPTED` +
  `PATTERN_ENTRY_CREATED` / `PATTERN_ENTRY_UPDATED` events the
  pledger_summary chunk produces;
- there is no aggregate scalar: the system does NOT compute a
  "coherence I-ness score" or any other rolled-up index.

The architecture lets ToyI's structural self-monitoring approximation
re-enter Pattern Ledger as one more inspectable bounded record. It is
**not** ToyI looking at itself; it is a deterministic copy-and-re-feed
loop over already-bounded primitives. The phrase "structural
self-monitoring approximation" is engineering language for that loop,
and is the strongest claim the campaign permits.

---

## 8. Recommended v1

```text
1. Add FeedbackMode.COHERENCE in
   brain/development/processing_window.py.
2. Conditionally add FeedbackMode.PATTERN_AND_COHERENCE
   (Step 4 LOCK D); the synthesis recommends bundling.
3. Add the pure helper build_cohmon_summary_text(*,
   overall_status_value, pass_count, warn_count, fail_count,
   na_count, check_count) -> str in
   brain/development/processing_window.py. The helper accepts
   only bounded primitives; rejects every other type with a
   typed ValueError; output is bounded printable, deterministic,
   no COGITO_ID, no _FORBIDDEN_NON_CLAIM_TERMS term.
4. Widen _V1_EMITTED_SOURCES to {REHEARSAL, PLEDGER_SUMMARY,
   COHMON_SUMMARY} so build_rehearsal_provenance(...,
   source=InternalEventSource.COHMON_SUMMARY) composes a
   bounded printable provenance.
5. Extend MODULE_PRODUCED_STRINGS with COHMON_SUMMARY_TEXT_PREFIX
   (= "cohmon_summary"), FeedbackMode.COHERENCE.value
   (= "coherence"), and FeedbackMode.PATTERN_AND_COHERENCE.value
   (= "pattern_and_coherence", if bundled).
6. Update validate_feedback_mode to accept the new members.
7. In brain/ui/session.py, add a new _run_cohmon_feedback_step(*,
   tick_index) -> bool helper that performs a deferred import of
   build_full_coherence_report and extracts the bounded primitives;
   extend _run_processing_window to fire it under
   FeedbackMode.COHERENCE and FeedbackMode.PATTERN_AND_COHERENCE.
8. Add row family I-CFBK-01 (REQUIRED) + I-CFBK-02 (STRUCTURAL)
   at catalog v0.27 -> v0.28; counts REQUIRED 283 -> 284,
   STRUCTURAL 90 -> 91; OBSERVED / NOT-EXERCISED / DEFERRED
   unchanged.
9. Update I-PWND-02 body to reflect the widened emit set.
10. Update I-IFBK-02 body to replace the assertion that
    COHMON_SUMMARY raises with an assertion that it now produces
    a non-claim-clean bounded provenance.
11. Add brain/ui/fixtures/coherence_feedback_integration.py
    (REQUIRED) and brain/ui/fixtures/coherence_feedback_static_audit.py
    (STRUCTURAL).
12. No real model calls. No new GrowthEventType. No new
    GrowthEventSource. No new ACTIVE_VIEWS value. No new
    OperatorCommand verb. No brain/tick.py change. No L1 / L2
    cache change. No parser / prompt change. No DB schema /
    SCHEMA_VERSION change. No autosave change.
```

---

## 9. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the synthesis is derivable from the v0.27 repo + the
  Phase 3.19 corrigenda LOCK F + the Coherence Monitor module's
  existing public API; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard; bridge overhead exceeds direct write
  cost.
```

---

## 10. Next artifact

`docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_PROBE_MATRIX.md`
— the Step 3 probe matrix, which enumerates the 80 cells the
Step 8 behavior report exercises and marks which cells are
runtime-blocked until Step 7 lands the implementation.
