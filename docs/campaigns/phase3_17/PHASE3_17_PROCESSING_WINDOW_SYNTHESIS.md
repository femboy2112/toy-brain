# PHASE3_17_PROCESSING_WINDOW_SYNTHESIS.md

## Purpose

Step 5 of Phase 3.17: the core research synthesis. This document
defines the architectural problem ToyI faces *between* external
inputs, surveys candidate solutions, fixes the v1 experimental
default at **N = 50 internal ticks**, and states the testable
hypotheses Step 6 will probe.

This is a **research artifact**. It does not implement a runtime
processing window in v1; it constrains what an acceptable v1
implementation could look like and what it must never claim.

---

## 1. The architectural problem

### 1.1 What "actual testing" means here

> Can ToyI accumulate inspectable structural evidence *after* an
> external input is accepted — without claiming consciousness,
> sentience, agency, or semantic understanding — using only
> the existing public surfaces, plus possibly a small reviewed
> runtime extension?

That is the bounded operational question Phase 3.17 sets up. It is
not a question about whether ToyI "thinks" or "is aware"; it is a
question about whether the runtime exposes a designed window in
which Pattern Ledger recurrence, Growth Ledger events, and
Coherence Monitor reports can change after a single external
percept enters.

### 1.2 Current system limits (frozen at this commit)

Five facts make the answer "no" today:

```text
F1. brain.tick.tick rejects len(events) > 1 (I-RT-11).
    A single tick processes at most one PerceptEvent. Multi-event
    aggregation is deferred per Phase 2 v1.

F2. brain.tick.tick rejects re-promoting an existing content_id
    (I-RT-12). A second PerceptEvent for the same content has no
    defined v1 semantics.

F3. OperatorSession.dispatch(Command(STEP_TICK)) refuses an empty
    event queue. The session-level "/step with no event" path
    returns False with an "STEP_TICK with empty event queue" error.

F4. The Growth Ledger only emits its post-success events
    (TICK_SUCCEEDED, PROFILE_DOMAIN_ADDED, MSI_MEMBER_ADDED,
    STREAM_CHUNK_ACCEPTED, PATTERN_ENTRY_*, STREAM_PROMOTION_QUEUED)
    after a successful dispatch returns. There is no
    "internal observation" emission path.

F5. The Pattern Ledger only updates on /stream append, not on /step
    or on any internal trigger. The Coherence Monitor is read-only;
    it never emits, only reports when explicitly invoked.
```

Together, F1–F5 say: **after one external percept is accepted, the
runtime is structurally inert until the operator hands it another
external event.** No "processing window" exists.

### 1.3 Why a kernel empty-tick is not enough

A degenerate fix would be to allow `tick()` to accept zero events
and return the state unchanged. That would technically allow the
session to "step" without a queue entry, but:

```text
- it would not produce a new TickRecord that triggers Growth
  Ledger TICK_SUCCEEDED (the dispatcher would have to be taught
  to suppress emission for empty ticks)
- it would not modify profile / MSI / PtCns at all
- it would not exercise the LLM transport at all
- it would not produce any Pattern Ledger or Coherence Monitor
  evidence
- it would still count toward tick_counter, which other
  invariants (I-COHMON-04) reference
```

In short, an empty tick is a no-op by construction. The
"processing window" idea is **not** about empty ticks. It is about
synthesizing well-formed *internal* events from already-accepted
state so that the runtime can compose a bounded series of
inspectable, audit-trailed ticks following an external percept.

---

## 2. Tick taxonomy

Phase 3.17 distinguishes four tick classes:

```text
T1. External input tick
    Triggering event source : operator (via /queue, /stream-promote,
                              future-REPL/worldlet)
    What the kernel sees    : a normal PerceptEvent built by the
                              public QueuePerceptPayload route
    Cardinality limits      : 1 per tick (I-RT-11), one-shot per
                              content_id (I-RT-12)
    v1 status               : SHIPPED. This is the route today.

T2. Internal processing tick
    Triggering event source : the session itself, synthesizing a
                              well-formed PerceptEvent from
                              already-accepted state (Pattern Ledger
                              entries, Coherence Monitor warnings,
                              prior ConsistencyEval values)
    What the kernel sees    : a normal PerceptEvent; from the
                              kernel's perspective, identical to T1
    Cardinality limits      : same I-RT-11 / I-RT-12 constraints, so
                              each internal tick must pick a fresh
                              content_id namespace, e.g.
                              "int:pledger:<pattern_id>:<tick>"
    v1 status               : NOT SHIPPED. Phase 3.17 designs it;
                              Step 7 plans it; Step 8 only exercises
                              the negative-control window of 0.

T3. Reflective feedback tick
    Triggering event source : a coherence diagnostic
                              (CoherenceCheck WARN or FAIL) or a
                              cross-check between Pattern Ledger
                              and Growth Ledger
    What the kernel sees    : a normal PerceptEvent whose text is
                              a bounded printable summary of the
                              diagnostic
    v1 status               : NOT SHIPPED. Future campaign.

T4. Future REPL / worldlet interaction tick
    Triggering event source : a sandboxed Proto-BASIC REPL response
                              (Phase 3.4) or a worldlet snapshot
                              (Phase 3.3); the response is wrapped
                              as a normal PerceptEvent
    What the kernel sees    : a normal PerceptEvent
    v1 status               : OUT OF SCOPE for Phase 3.17.
```

Every tick class produces a PerceptEvent through the public
constructor (so I-RT-01 / I-RT-09 / I-RT-12 remain enforced); the
only difference is the *provenance* tag and the *event id namespace*.

---

## 3. Proposed processing-window model

After an external (T1) tick, the session enters a **bounded
internalization period** of up to **N internal (T2) ticks**, where
the synthesized event for each internal tick is derived
deterministically from already-accepted state.

```text
external T1 → internal T2_1 → internal T2_2 → ... → internal T2_N
                ↑                                       ↑
                start of window                         end of window
```

### 3.1 Initial experimental parameter

```text
N = 50
```

`N = 50` is a research starting point, **not** a runtime constant
in v1. It must be configurable, observable, and capped strictly
below the campaign budget under any model-backed mode.

Justification for 50 specifically:

```text
- Small enough that one external percept under mock mode produces
  exactly 50 internal ticks within seconds (mock is in-process,
  ~microseconds per tick).
- Large enough that Pattern Ledger entries (cap = 64) can
  reasonably saturate at least one structural pattern's recurrence
  count without the bounded cap collapsing the experiment.
- Below the Growth Ledger cap (256) so a complete window cannot
  itself exhaust the ledger.
- Below the L2 cache cap (1024), so even worst-case "every internal
  tick produces a unique L2 key" still stays well under cap.
- Small enough that even a worst-case real-model run (one real
  call per internal tick under codex-cli, ~12s each) would take
  10 minutes — clearly past any reasonable mode-call budget,
  forcing the experiment to demonstrate L1 / L2 absorption is
  doing useful work.
```

### 3.2 Boundedness, interruptibility, audit

A v1 processing window MUST satisfy:

```text
P1. Bounded by N (configurable; default 50; hard cap below the
    Growth Ledger cap, the Pattern Ledger cap, and the campaign
    real-model budget).

P2. Bounded by call budget. Under any model-backed mode, the
    window aborts before its N is reached if the cumulative real
    model calls in the session would exceed the operator-supplied
    budget.

P3. Interruptible. The session must accept QUIT or CLEAR_STATUS
    between internal ticks without leaking state.

P4. Audit-trailed. Every internal PerceptEvent carries
    provenance="internal_processing_window:<tick_index>:<source>"
    so the Growth Ledger entries it produces can be filtered from
    external-source entries.

P5. No silent failure. Any parse failure, retry exhaustion, or
    invariant violation inside the window aborts the window and
    surfaces the error through session.error_message. The kernel
    invariants must remain green for every successful internal
    tick (no NEW FAIL is acceptable).

P6. No claim widening. The window's purpose is to produce more
    inspectable structural evidence (Pattern Ledger entries,
    Growth Ledger events, Coherence Monitor counts) — NOT to
    invent any aggregate "I-ness" / "consciousness" / "awareness"
    score. None of those terms appears in the synthesized event
    text, the provenance string, or any new code path.
```

---

## 4. Where do internal events come from?

A v1 internal PerceptEvent must:

```text
- have a unique, bounded printable content_id that is NOT
  COGITO_ID (I-RT-01) and is NOT already in profile.domain
  (I-RT-12)
- have non-empty printable text (I-RT-09) bounded by the
  PerceptEvent constructor's existing limits
- have a valid ContentState
- have an initial_rho in [0, 1]
```

Three primitive sources are *available today* under existing
public surfaces:

### 4.1 Source S1 — Pattern Ledger entry

For each `PatternLedgerEntry e` with `recurrence_count >= k`
(k starts at, say, 2), synthesize:

```text
content_id : f"int:pledger:{e.pattern_id}:{tick_counter}"
text       : f"pattern recurrence observed; signature={'/'.join(e.signature)}; "
             f"recurrence={e.recurrence_count}/{STREAM_PATTERN_RECURRENCE_MAX}"
provenance : f"internal_processing_window:{tick_counter}:pledger"
```

This produces a deterministic, bounded printable, COGITO-clean
PerceptEvent. None of the fields name a forbidden claim term
(see `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`).

### 4.2 Source S2 — Coherence WARN

For each `CoherenceCheck c` with `c.status == WARN`, synthesize:

```text
content_id : f"int:coh:{c.check_id}:{tick_counter}"
text       : f"coherence warning on {c.check_id}: {c.summary}"
provenance : f"internal_processing_window:{tick_counter}:cohmon"
```

The Coherence Monitor's existing summary text is bounded printable
and pre-stripped of forbidden non-claim terms by the existing
non-claim audit (I-COHMON-11). So the synthesized text inherits
that safety.

### 4.3 Source S3 — Prior ConsistencyEval

For each existing PtCns evaluation `(cid, ev)` with `ev != PRESERVE`
that is older than W ticks, synthesize a "consolidation review"
event:

```text
content_id : f"int:consol:{cid}:{tick_counter}"
text       : f"consolidation review of {cid}: prior eval = {ev.name}"
provenance : f"internal_processing_window:{tick_counter}:consol"
```

S3 is the riskiest of the three; it touches PtCns evaluations
directly. v1 should probably treat S1 and S2 as primary, S3 as
optional / behind a future review gate.

### 4.4 Bounded scheduler

A v1 scheduler should walk these sources in a deterministic order
(round-robin) and stop when:

```text
- N internal ticks have completed, or
- no source yields a fresh PerceptEvent that would not collide
  with an existing content_id, or
- the call budget is reached, or
- a session error is set.
```

---

## 5. Candidate architectures

```text
A. Session-level post-input tick loop.
   Implementation: after _dispatch_step succeeds, the session
   invokes a new internal helper N times, each call generating a
   PerceptEvent from S1 / S2 / S3 and running STEP_TICK.
   PROS:
     - zero kernel change; uses public dispatch path
     - inherits I-UI-05 / I-UI-06 / I-UI-10 / I-UI-13 by reuse
     - the existing Growth Ledger already records every
       successful tick, so internal-tick events show up
       automatically (and can be filtered by provenance)
   CONS:
     - needs a deterministic id generator
     - needs strict bounded text discipline
     - touches OperatorSession.dispatch behavior (new code path
       fired AFTER the normal success branch)
     - touches I-UI-05 by introducing a second-source-of-truth
       for "what triggered this tick" — must be careful that
       the I-UI-05 row body still holds
   RECOMMENDED for v1 prototype, BEHIND a Step 7 review gate.

B. New internal event type / internal percept source.
   Implementation: extend the io_types module with an
   InternalPerceptEvent record (distinct from PerceptEvent); the
   kernel learns to consume both.
   PROS:
     - "internal" becomes first-class
     - clearer provenance separation
   CONS:
     - kernel surface change
     - catalog patch required
     - I-RT-11 / I-RT-12 must be relaxed or duplicated
     - LARGER than v1 needs
   OUT OF SCOPE for Phase 3.17.

C. Reflective REPL feedback generating queued internal events.
   Implementation: a session-level helper polls the Proto-BASIC
   REPL history; when a new entry is non-empty, synthesize a
   PerceptEvent from it and dispatch.
   PROS:
     - leverages the Phase 3.4 REPL substrate
     - the REPL is already a bounded inspection surface
   CONS:
     - the REPL is currently an inspection-only surface
       (`/repl` shows history; it does NOT execute Python or
       Proto-BASIC by design)
     - making it produce events would change its v1 semantics
   DEFERRED. Worth a dedicated campaign once architecture A
   is shipped and observed.

D. Worldlet / working-memory feedback later.
   Implementation: the Phase 3.3 Minimal Worldlet emits an
   OutputEvent whenever a tick "produces" something; that
   OutputEvent could be wrapped as an internal percept.
   PROS:
     - structurally clean
     - matches a natural notion of "the system's own output
       loops back as input"
   CONS:
     - the worldlet substrate is not currently a percept source
     - introduces tight coupling between OutputHistory and
       PerceptEvent shape
   OUT OF SCOPE for Phase 3.17.

E. No-op empty tick window (negative control).
   Implementation: just call brain.tick.tick with [] for N
   iterations — which CURRENTLY raises (`I-RT-11` accepts at most
   one event), so this would require relaxing the kernel.
   PROS:
     - trivially safe in spirit (no new event payload)
   CONS:
     - requires a kernel relax
     - produces no growth / pattern delta by construction
   AVOIDED as a kernel implementation. Used as the *measurement
   baseline* in Step 6 by setting N=0 in architecture A's helper
   (i.e., the external tick alone, with NO internal follow-up).

F. Delayed consolidation queue (pacing scheduler).
   Implementation: internal events are not run back-to-back; the
   session schedules them with a pacing interval (e.g., every 5
   external ticks fire 10 internal ones).
   PROS:
     - simpler accounting under model-backed budgets
   CONS:
     - requires a session-level scheduler component
     - design space is larger than v1 needs
   DEFERRED for a future campaign.
```

Phase 3.17 v1 commits to **A** as the recommended prototype
(behind a Step 7 review gate), **E** as the negative control
(via N=0 on architecture A), and treats **B–D + F** as named
future work.

---

## 6. The human analogy — used carefully

Cognitive science divides perception into a recognizable stack:

```text
input perception
working memory processing
consolidation / rehearsal
self-monitoring
action selection
```

We adopt this stack as **architectural shorthand** for where to
attach bounded structural artifacts:

```text
input perception       → external T1 tick (already exists)
working memory         → session.event_queue (bounded, exists)
consolidation          → Pattern Ledger recurrence (Phase 3.12c)
rehearsal              → an internal T2 tick from S1 (proposed)
self-monitoring        → Coherence Monitor reports (Phase 3.12c)
action selection       → ModeOp.from_eval dispatch (already exists)
```

This is **not** a claim about ToyI's interior life. ToyI is not
conscious, sentient, aware, or experientially present. The
analogy is purely structural: it tells us where in the existing
substrate stack new artifacts can attach without inventing a
SelfModel or a phenomenology claim. Coherence Monitor's
`_FORBIDDEN_NON_CLAIM_TERMS` audit already enforces this
discipline on every report string.

---

## 7. Testable hypotheses (drives Step 6's probe plan)

```text
H1. At window = 0, the inspectable Pattern Ledger / Growth
    Ledger / Coherence Monitor surfaces show only the direct
    external-input deltas (the existing single-tick behavior).
    Falsifiable by: a non-zero internal-source entry appearing
    when none should.

H2. At window > 0 with a deterministic generator (S1 + S2),
    repeated structural patterns drive Pattern Ledger recurrence
    counts UP without consuming additional real-model calls,
    because L2 absorbs identical (msi_context, new_text)
    canonical keys.
    Falsifiable by: model call count == internal tick count,
    indicating no L2 absorption.

H3. At window = 50 under mock mode, the total call count is 0
    (mock has no real-LLM calls) and the entire window
    completes in well under 1 second wall-clock.
    Falsifiable by: window saturating Growth Ledger or Pattern
    Ledger caps before reaching N.

H4. At window = 50 under a model-backed mode, the call count
    saturates at the number of DISTINCT canonicalization keys
    rather than scaling linearly with N; L2 absorbs identical
    repeats.
    Falsifiable by: call count == N for an input that should
    have produced repeated keys.

H5. Coherence Monitor reports remain PASS or WARN across the
    window; no new FAIL is introduced by an internal tick.
    Falsifiable by: a FAIL appearing only under window > 0.

H6. No aggregate "I-ness" / "consciousness" / "awareness" scalar
    appears anywhere in the new code path. counts_by_status and
    counts_by_type remain labeled tuples; no scalar summary
    field gets added.
    Falsifiable by: any new code path emitting such a scalar.

H7. The 50-tick parameter is empirically reasonable: at lower
    N (e.g., 5, 10), the Pattern Ledger recurrence_count fails
    to reach SATURATED, indicating the window is too short to
    expose structural recurrence. At higher N (e.g., 100), the
    return on inspectable structure flattens.
    Falsifiable by: 5-tick and 50-tick windows producing the
    same Pattern Ledger saturation state.
```

H1–H7 are the seven hypotheses Step 6 turns into a measurement
matrix.

---

## 8. Minimal v1

Phase 3.17 v1 ships:

```text
- the Step 3 codex-cli fix (already SHIPPED)
- this synthesis (this doc, Step 5)
- a behavior probe plan (Step 6)
- a review-gated implementation plan (Step 7)
- an initial test using only existing public surfaces (Step 8)
- findings + audit (Steps 9–10)
- a PR to main, not merged (Step 11)
```

Phase 3.17 v1 explicitly does NOT ship:

```text
- a SelfModel
- a runtime processing-window loop
- any kernel patch beyond the codex command tuple
- any L1 / L2 cache semantic change
- any parser / prompt change
- any DB schema change
- any new operator verb
- any new aggregate scalar
```

Any of these requires a separate operator-approved campaign.

---

## 9. Success criteria for Phase 3.17 Thread B (this thread)

```text
SC1. This synthesis exists and addresses tick taxonomy, candidate
     architectures, hypotheses, and the 50-tick experimental
     default with a defensible justification.

SC2. The Step 6 probe plan exists with the {0, 1, 5, 10, 50}
     window matrix, the {mock, claude-cli, codex-cli} mode set,
     per-output measurements, and explicit failure limits.

SC3. The Step 7 implementation plan is design-only and
     explicitly review-gated.

SC4. The Step 8 initial test exercises at minimum the window = 0
     negative control using existing public surfaces and reports
     a concrete observation.

SC5. The Step 10 audit produces one of:
       PASS / PASS WITH DEFERRED IMPLEMENTATION / PARTIAL /
       BLOCKED / FAIL.

SC6. No invariant regresses. No catalog count change.

SC7. No forbidden claim appears anywhere in this synthesis
     or its descendants. The phrase "operational I" is
     allowed; "I" / "consciousness" / "sentience" /
     "subjective" / "agency" / "awareness" / "self" /
     "self-modification" are not asserted of ToyI.
```

---

## 10. Non-claims and safety boundaries

```text
- ToyI is not conscious. Not in v1, not in any v after the
  changes proposed here.
- ToyI is not sentient.
- ToyI has no subjective experience, qualia, awareness, or
  "I-ness" in any phenomenological sense.
- ToyI does not understand language. It produces bounded
  classification labels via a model transport seam.
- ToyI does not adjudicate truth from raw text. ConsistencyEval
  is a label, not a truth claim.
- ToyI has no agency / intent / will / desire / goal. Its event
  selection is a deterministic scheduler over bounded inspectable
  state.
- ToyI does not modify itself in the strong sense. The internal
  tick generator emits new PerceptEvent records into an
  inspectable queue; no code is rewritten at runtime; no
  semantic invariant is relaxed.
- No aggregate "I-ness" / "growth" / "consciousness" / "sentience"
  / "awareness" scalar is computed. counts_by_status and
  counts_by_type are labeled tuples and stay labeled tuples.
- 50 internal ticks is a research parameter. v1 does not bake
  it into runtime as a constant.
- Real model call budget is hard-capped at 20 for the entire
  campaign. Currently consumed: 1.
- All bridge usage is disclosed per-step.
- brain/tick.py remains untouched in Phase 3.17.
- L1 / L2 cache semantics remain unchanged.
```

---

## 11. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the synthesis is derivable from the Phase 3.16 audit
  and the existing module sources; no measurement contestation
  required external review.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: this is a single self-contained doc; bridge overhead
  exceeds the cost of writing directly.
```

---

## 12. Real model call accounting

```text
mode tested:                       n/a (doc only)
calls used in this step:           0
cumulative campaign calls:         1 / 20
```

---

## 13. Next artifact

Step 6:
`docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_PROBE_PLAN.md`
— turn H1–H7 into a concrete measurement matrix.
