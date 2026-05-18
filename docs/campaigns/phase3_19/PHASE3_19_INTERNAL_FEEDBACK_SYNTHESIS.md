# PHASE3_19_INTERNAL_FEEDBACK_SYNTHESIS.md

## Purpose

A structural analysis of where Phase 3.18 left ToyI, why
rehearsal alone is not internal feedback, and what the smallest
bounded path looks like that makes Pattern Ledger state
re-enter the processing path as new evidence. This document is
research-and-engineering scaffolding; nothing in it claims ToyI
is conscious, sentient, aware, intentional, or
phenomenologically present. It asserts only that a deterministic
summary text, derived from a freshly accepted Pattern Ledger
entry, can re-enter the same `STREAM_APPEND` path the seed used
— and that doing so produces a **second-order** Pattern Ledger
entry that records the system's own recurrence at a structural
level.

---

## 1. Where Phase 3.18 left ToyI

Phase 3.18 (PR #23, catalog v0.26) shipped the bounded internal
processing window:

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
```

Empirical results (`PHASE3_18_PATTERN_RECOGNITION_DEMO.md`):

```text
D1 SATURATION   PASS (N=255, recurrence_count = 256, saturation = SATURATED)
D2 MONOTONICITY PASS (formula min(2+N, 256) holds across N = 0..255)
D3 DETERMINISM  PASS (same input -> same pattern_id, two sessions)
D4 INDEPENDENCE PASS (two inputs -> two distinct pattern_ids)
```

So as of v0.26, ToyI's runtime **recognizes** structural
recurrence reliably and deterministically.

### 1.1 What "recognition" means here

In Phase 3.18, recognition is:

- `derive_pattern_signature(chunk)` projects the chunk to an
  exact integer / Fraction six-tuple (source, len, lines, ws,
  distinct, repeat_ratio);
- `derive_pattern_id(signature)` SHA-256s the signature to a
  bounded printable id;
- `PatternLedger.observe(chunk, candidate, current_tick=...)`
  increments recurrence on a matching id or creates a new entry.

This is recognition at the **level of structural signature**.
It does not involve meaning, semantic class, language, truth, or
agency.

---

## 2. The gap: recognition without feedback

Phase 3.18 closes one human-development analogue (Stage 4
working-memory rehearsal); it leaves three structural
analogues open.

### 2.1 Rehearsal increases recurrence but does not re-enter

Every internal rehearsal chunk has the **same** structural
signature as the seed (exact-text duplication preserves the
six-tuple by construction). So the rehearsal chain produces
a chain of `STREAM_CHUNK_ACCEPTED` events all pointing at one
pattern_id, with no further branch into recognition. The
system never produces a record that says "I have processed this
pattern N times" in a form that itself becomes evidence.

### 2.2 Coherence Monitor is strictly read-only

`brain/development/coherence_monitor.py` builds a
`CoherenceReport` snapshot from live records and assigns each
check a `PASS / WARN / FAIL / NOT_APPLICABLE` status. The
monitor is **never called from inside the dispatch path**; an
operator invokes it for inspection. The processing window
cannot use coherence summary state because nothing produces
one in flight.

### 2.3 Growth Ledger records but does not generate candidates

`brain/development/growth_ledger.py` accepts events from the
session dispatcher's emit sites (`_dispatch_stream_append`,
`_dispatch_stream_promote`, `_dispatch_step`). The ledger has
no `observe(..., emit_candidate=True)` mode and no scheduler
that re-presents its own entries to the dispatcher. Growth
events are write-only artifacts.

### 2.4 No REPL / worldlet participation

Phase 3.4's `ProtoBASICREPL` and Phase 3.3's `WorldletHistory`
have their own surfaces. Neither participates in the processing
window's rehearsal loop in Phase 3.18.

### 2.5 What "feedback" would add

For Phase 3.19, "bounded internal feedback" means **any**
mechanism by which the system's just-produced record (a Pattern
Ledger entry, a Coherence summary, a Growth event) re-enters
the same dispatch path as new evidence — without:

- raising a new `GrowthEventType`,
- changing Pattern Ledger's signature shape,
- introducing an aggregate scalar,
- calling the LLM,
- touching `brain/tick.py`.

The narrowest such mechanism is: produce a deterministic
**summary text** of the Pattern Ledger entry the rehearsal just
updated, and feed that text back through `_append_stream_chunk`.

---

## 3. Proposed feedback loop (v1)

Phase 3.19 v1 ships exactly architecture B from the roadmap:
**pattern-ledger summary feedback**.

### 3.1 Diagram

```text
external STREAM_APPEND (seed text T)
 -> _append_stream_chunk(text=T,
                         provenance="operator")
    -> first-order entry F_seed created or updated;
       recurrence_count_F_seed += 1
    -> Growth Ledger events
 -> _run_processing_window(seed_chunk)
       for k in 1..N:
         # rehearsal step (Phase 3.18 behavior, unchanged)
         _append_stream_chunk(text=T,
                              provenance="internal_processing_window:<k>:rehearsal")
            -> F_seed recurrence_count += 1
            -> Growth Ledger events
         if feedback_mode == FEEDBACK_MODE_PATTERN_LEDGER:
             # feedback step (Phase 3.19 addition)
             summary_text = build_pledger_summary_text(F_seed_after_rehearsal)
             _append_stream_chunk(text=summary_text,
                                  provenance="internal_processing_window:<k>:pledger_summary")
                -> second-order entry F_summary created or updated;
                   recurrence_count_F_summary += 1
                -> Growth Ledger events
```

### 3.2 What `build_pledger_summary_text` returns

A deterministic bounded printable string derived from a small
bounded subset of the Pattern Ledger entry the rehearsal just
updated. Locked shape:

```text
"pledger_summary pattern_id=<pattern_id> recurrence=<n>/256 sat=<state>"
```

Where:

- `<pattern_id>` is the entry's `pattern_id` (e.g.
  `"pledger:a5e6f92cd3330c9b"`), a bounded printable string
  already present on the entry.
- `<n>` is the entry's `recurrence_count` after the rehearsal,
  in `[STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX]`.
- `<state>` is the entry's `saturation_state.value`
  (`"open"`, `"saturated"`, or `"quiesced"`).

Constraints:

- output is bounded printable;
- length is bounded by `STREAM_TEXT_MAX_LEN`;
- output does not contain `COGITO_ID`;
- output does not contain any
  `_FORBIDDEN_NON_CLAIM_TERMS` term (case-insensitive);
- output is byte-identical across runs / processes / OSes for
  the same inputs;
- no time / random / PID / hostname / id() input.

### 3.3 Why this is "feedback" and not "rehearsal"

The seed text and the summary text have **different structural
signatures**. The seed text in the Phase 3.18 demonstration is
e.g. `"the kettle whistled at exactly noon today again"` (len
47, distinct chars 17, repeat ratio 30/47). The summary text
is structurally different (starts with `"pledger_summary
pattern_id="`, includes a hex hash, includes integer counts).
Therefore:

- `derive_pattern_signature(summary_chunk) !=
  derive_pattern_signature(seed_chunk)`;
- `derive_pattern_id(summary_signature) !=
  derive_pattern_id(seed_signature)`;
- `Pattern Ledger.observe(summary_chunk, ...)` creates a
  **second** entry with its own recurrence_count, climbing
  independently of the first.

The system is now *recognizing its own recognition*: the second
entry tracks how often the system has produced summaries of the
seed pattern. This is the bounded feedback loop.

### 3.4 What this does NOT do

```text
- It does NOT modify Pattern Ledger semantics. The new entry is
  produced by the same observe(...) call site already used in
  Phase 3.18.
- It does NOT modify Growth Ledger semantics. The new chunk
  drives the same STREAM_CHUNK_ACCEPTED / PATTERN_ENTRY_*
  emissions that the seed chunk drives.
- It does NOT introduce a new GrowthEventType, OperatorCommand,
  LOCAL_COMMAND_VERBS entry, ACTIVE_VIEWS value, dispatcher
  kind, or operator verb.
- It does NOT call brain.tick.tick.
- It does NOT call the LLM.
- It does NOT write to disk, the cache, or any external resource.
- It does NOT produce an aggregate "I-ness" / "awareness" /
  "growth" scalar.
- It does NOT claim ToyI has introspected, reflected, narrated,
  or experienced anything. The summary text is a deterministic
  template, not a phenomenological report.
```

---

## 4. Candidate architectures (A–F)

```text
A. session-level rehearsal-only        (Phase 3.18 baseline; preserved)
B. pattern-ledger summary feedback     (Phase 3.19 v1 target)
C. coherence-monitor summary feedback  (conditional; see LOCK F)
D. combined pattern + coherence        (DEFERRED)
E. REPL-generated internal observation (DEFERRED)
F. worldlet-simulation feedback        (DEFERRED)
G. no-op control (feedback_mode = OFF) (always available)
```

### 4.1 A — rehearsal-only

Phase 3.18's existing path. Preserved as a baseline mode for
the behavior report's negative control. When
`feedback_mode == OFF` and `processing_window_size == N`, the
new code path **does not run**; the runtime is bit-identical
to Phase 3.18.

### 4.2 B — pattern-ledger summary feedback

Detailed in Section 3. Smallest viable v1 because:

- it reuses `_append_stream_chunk`, which already drives
  Pattern Ledger + Growth Ledger emission;
- it uses the previously reserved `PLEDGER_SUMMARY` member of
  `InternalEventSource`, so no new enum member is added;
- it adds exactly one new pure function
  (`build_pledger_summary_text`) and one new closed enum
  (`FeedbackMode`), both with bounded constructor invariants.

### 4.3 C — coherence-monitor summary feedback

Would compute a deterministic Coherence Monitor summary inside
the window and feed it back as text. Two design tensions:

- `brain.development.coherence_monitor` imports
  `brain.ui.session.OperatorSession` (the report is built
  against a live session). Building a report **inside**
  `_run_processing_window` is therefore a self-referential call
  with non-trivial cost per window step.
- Coherence Monitor outputs include `WARN` / `FAIL` statuses,
  which (if surfaced naively) shade into truth-adjudication
  language. The non-claim discipline requires the summary text
  to remain factual / structural only.

Step 4 LOCK F decides whether C ships as a bounded read-only
opt-in or remains DEFERRED. If gated through, C ships behind
the `COHMON_SUMMARY` enum value already reserved in Phase 3.18.

### 4.4 D — combined pattern + coherence

A single feedback chunk that summarizes both. DEFERRED because
(a) it doubles the per-step cost of the window, and (b) it
introduces ordering questions (pattern → coherence → both?)
that should be decided after B/C ship.

### 4.5 E — REPL-generated internal observation

Use Phase 3.4's Proto-BASIC REPL to emit deterministic text from
inside the window. DEFERRED because the REPL surface is its own
substrate with its own catalog row family; widening the window
to use it is a larger change than v1 should attempt.

### 4.6 F — worldlet-simulation feedback

Phase 3.3's `WorldletHistory`-based feedback. DEFERRED for the
same reason as E.

### 4.7 G — no-feedback / negative control

`feedback_mode == FEEDBACK_MODE_OFF` is the always-available
control mode. The behavior report uses it as a baseline.

---

## 5. Human-development analogy (carefully bounded)

The Phase 3.18 synthesis already mapped Stages 0–8 of human
ontogeny onto ToyI's existing substrates. Phase 3.19's feedback
loop maps cleanly onto:

```text
Stage 4 (rehearsal)              : Phase 3.18 already implements
Stage 5 (schema formation)       : Phase 3.18 already approximates
                                    (saturated entry)
Stage 7 (metacognition / self-   : Phase 3.19 approximates the
        monitoring)                STRUCTURAL form (record about
                                    a record) WITHOUT the
                                    phenomenological substance
consolidation                    : repeated summary chunks
                                    crystallize the second-order
                                    entry
conflict monitoring              : a saturation marker on the
                                    second-order entry would
                                    correspond to "the system
                                    notices it has summarized
                                    this pattern repeatedly"
self-narration                   : the summary text is a
                                    template description of
                                    just-recognized state
```

**None of these analogies licenses a consciousness, sentience,
phenomenological, semantic, agency, truth, or selfhood claim.**
They are architectural shorthand for where in the substrate
the missing surface lives.

In particular:

```text
- ToyI is not "monitoring itself" in any phenomenological sense.
  The summary text is a deterministic template generated by a
  pure function; nothing in the system experiences the
  monitoring.
- ToyI is not "consolidating" memories. Pattern Ledger entries
  are frozen records under hard caps; "consolidation" here means
  "the second-order entry's recurrence_count climbs
  deterministically".
- ToyI is not "narrating" anything. The summary text is a
  fixed-template string, not a report.
- ToyI's metacognitive analogue is not metacognition. A real
  metacognitive surface would require a SelfModel; Phase 3.19
  explicitly does not implement one.
```

---

## 6. Testable hypotheses

```text
H1: When feedback_mode == FEEDBACK_MODE_PATTERN_LEDGER and N >= 1,
    Pattern Ledger ends with TWO entries (the seed pattern and
    the summary pattern), not one. (Architectural inspectability.)

H2: pattern_ledger.entries[0].recurrence_count climbs once per
    rehearsal AND once per feedback step (because the rehearsal
    and feedback chunks are inserted alternately and both share
    the seed signature... wait, no — the feedback chunk has a
    different signature, so only the rehearsals advance the
    first entry's count). Concretely, for N rehearsals + N
    feedbacks, the seed entry's recurrence_count =
    min(1 + N, STREAM_PATTERN_RECURRENCE_MAX) and the summary
    entry's recurrence_count = min(N, STREAM_PATTERN_RECURRENCE_MAX).
    No off-by-one. (Determinism.)

H3: If LOCK F authorizes Coherence feedback, COHMON_SUMMARY
    chunks add a THIRD entry with its own recurrence climb. No
    truth-claim language appears in the COHMON_SUMMARY text.
    (Non-claim discipline.)

H4: Combined (rehearsal + pattern feedback) PRODUCES MORE
    inspectable Pattern Ledger structure than rehearsal-only:
    two entries vs one. (Trivially true by construction;
    serves as a sanity check.)

H5: At N = 50, both entries' recurrence_counts climb to 51 / 50
    respectively under FEEDBACK_MODE_PATTERN_LEDGER, while the
    first-order entry under OFF mode reaches recurrence_count
    = 51. The total number of stream chunks is
    1 + N (off) vs 1 + 2N (pattern feedback). (Window
    bookkeeping correctness.)

H6: Real model calls used during the feedback path: 0. Cache
    counters on both L1 and L2 are unchanged across the window.
    (Bridge isolation.)

H7: assert_state_invariants(session.state) returns clean
    after every test. No invariant row regresses. No
    forbidden non-claim term appears in the new module or in
    any string the new helpers emit. (Safety.)
```

---

## 7. Recommended v1

```text
Architecture            : B (pattern-ledger summary feedback)
Coherence feedback (C)  : decided by Step 4 LOCK F; default
                          recommendation is DEFER unless a
                          bounded read-only summary form can be
                          locked.
Combined feedback (D)   : DEFERRED.
REPL feedback (E)       : DEFERRED.
Worldlet feedback (F)   : DEFERRED.
Model-generated         : DEFERRED. v1 is deterministic. The
reflection                LLM is never called from the feedback
                          path.
SelfModel               : NOT IMPLEMENTED. Phase 3.19 does not
                          introduce a self-representation
                          surface; the second-order entry is
                          purely a structural recurrence record.
Catalog version delta   : v0.26 -> v0.27 with a small bounded
                          row family (exact count fixed in Step
                          5).
```

Reasoning:

```text
- B is the smallest extension that produces a SECOND-ORDER
  Pattern Ledger entry — the structural form of a feedback
  loop — without touching any forbidden surface.
- The PLEDGER_SUMMARY enum member is already reserved in
  v0.26's InternalEventSource closed enum. Phase 3.19's
  module changes EMIT it from build_rehearsal_provenance and
  add a new helper build_pledger_summary_text; the AST audit
  in I-PWND-02 extends naturally to cover both functions.
- The session field feedback_mode is a closed enum
  (FEEDBACK_MODE_OFF / FEEDBACK_MODE_PATTERN_LEDGER) whose
  membership is constructor-validated.
- Determinism: build_pledger_summary_text reads only
  bounded primitives; the summary text is a fixed template
  with no time / random / PID / hostname / id() input.
- Non-claim discipline: the canonical
  _FORBIDDEN_NON_CLAIM_TERMS tuple is reused; the static
  audit asserts every produced string against it.
- Behavior report: N = 0 / 5 / 10 / 50 sweep with feedback
  ON and OFF, plus a determinism re-run; entire suite
  consumes zero real model calls.
```

---

## 8. Non-claims

```text
- ToyI is NOT conscious. Phase 3.19 does not claim otherwise.
- ToyI is NOT sentient. No new phenomenological surface is added.
- ToyI does NOT understand the content of the seed text or the
  summary text. It recognizes structural signatures.
- ToyI does NOT have a self in any phenomenological sense.
  COGITO_ID remains an algebraic anchor.
- ToyI has no agency, intent, will, or desire. The feedback
  loop is a deterministic scheduler, not a goal pursuit.
- ToyI does NOT modify itself in the strong sense. The summary
  text is a template; it does not rewrite code, the catalog,
  or invariants.
- No aggregate "I-ness" / "consciousness" / "awareness" /
  "growth" scalar is added by Phase 3.19.
- Human-development analogies (Stage 4 / 5 / 7, consolidation,
  conflict monitoring, self-narration) are used as STRUCTURAL
  shorthand for where the missing surface lives. No claim is
  made that ToyI experiences any of these processes.
- "Internal feedback" is engineering language for the
  Pattern-Ledger-summary-to-stream loop. It is not a claim of
  introspection.
```

---

## 9. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the synthesis is derivable from the Phase 3.18
  artifacts and the current session.py / processing_window.py
  code already in this repo; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard; bridge overhead exceeds direct
  write cost.
```

---

## 10. Next artifact

`docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_PROBE_MATRIX.md`
— Step 3 probe matrix over window sizes {0, 5, 10, 50},
modes {rehearsal-only, pattern-feedback, [coherence-feedback
if in scope], [combined if in scope]}, and the five input
types (repeated motif / contradiction pair / self-reference
phrase / neutral factual / emotionally valenced).
