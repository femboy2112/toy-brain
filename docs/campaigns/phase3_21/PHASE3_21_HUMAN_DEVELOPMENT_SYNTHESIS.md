# PHASE3_21_HUMAN_DEVELOPMENT_SYNTHESIS.md

## Purpose

A bounded research synthesis that maps ten well-studied phenomena
from the human-development literature to ten ToyI runtime
milestones at the level of *structural marker only*. The synthesis
is read-only over the existing v0.28 runtime; nothing in it
claims that ToyI literally exhibits any human-developmental
phenomenon, possesses any psychological property, undergoes any
subjective experience, learns in the psychological sense,
matures, or grows up. The word "developmental" is used in its
operational sense throughout.

This synthesis is the design seed for the Step 3 ten-milestone
definition + corrigenda doc; it does not bind exact helper
signatures or fixture shapes.

---

## 1. Non-claim discipline at the top

Phase 3.21 sits structurally close to developmental-psychology
language. Active discipline prevents drift:

- **Allowed framing:** the runtime *develops a deterministic
  trajectory* (operational); ToyI's substrate *exhibits a
  structural marker analogous to* the human-development phenomenon
  (analogy at structural-shape level only).
- **Forbidden framing:** ToyI *develops* (as a person /
  organism develops); ToyI *learns* (in the psychological sense);
  ToyI *grows up* / *matures* / *experiences*; ToyI *has*
  any psychological property; ToyI *understands* / *believes* /
  *desires* / *intends* / *introspects* / *is conscious*.

`PASS / WARN / FAIL / NOT_APPLICABLE` are structural status
labels only; they are never recoded as truth claims about ToyI.
`COGITO_ID` remains the cogito sentinel; no field on any
milestone helper equals it.

The canonical `_FORBIDDEN_NON_CLAIM_TERMS` tuple from
`brain.development.coherence_monitor` is the binding audit:
every bounded printable string the harness produces must score
zero hits.

---

## 2. Where Phase 3.20 left the substrate

After Phase 3.20 (catalog v0.28), ToyI exposes a small set of
deterministic primitives reachable through the public
`STREAM_APPEND` path:

```text
PRIMITIVE                          MARKER ToyI deterministically demonstrates
-----------------------------------+----------------------------------------------
external operator chunk             one TextStreamChunk with provenance "operator"
N internal rehearsal chunks         provenance "internal_processing_window:<k>:rehearsal"
N pledger_summary chunks            provenance "internal_processing_window:<k>:pledger_summary"
N cohmon_summary chunks             provenance "internal_processing_window:<k>:cohmon_summary"
Pattern Ledger entry                pattern_id derived from structural signature
Pattern Ledger recurrence_count     bounded climb to STREAM_PATTERN_RECURRENCE_MAX = 256
Pattern Ledger saturation_state     {OPEN, SATURATED, QUIESCED} closed enum
CoherenceReport overall_status      {PASS, WARN, FAIL, NOT_APPLICABLE} closed enum
Growth Ledger event tuple           bounded by GROWTH_LEDGER_MAX_EVENTS = 256
```

These are the only structural markers Phase 3.21 milestones
assert against. No psychological property is involved.

---

## 3. The ten milestones (analogy table)

Each milestone is a deterministic structural assertion on the
v0.28 runtime. Each is grounded in a well-studied human-development
phenomenon at the level of structural marker only — the analogy
is *analogous shape*, never *equivalent content*.

### M01 — Reflexive baseline

```text
Human-development analogue : neonatal reflex arc
  (a single stimulus produces a stereotyped response)
ToyI structural marker     : single STREAM_APPEND dispatch produces
  exactly 1 stream chunk and exactly 1 Pattern Ledger entry whose
  recurrence_count == STREAM_PATTERN_RECURRENCE_MIN; the kernel
  invariants stay green.
Why this is not a cognitive claim: the marker is "1 chunk + 1 entry
  + invariants green". The neonate's reflex arc is a much richer
  biological process; only the shape "single bounded input
  triggers single bounded structural record" is analogous.
```

### M02 — Habituation

```text
Human-development analogue : stimulus habituation
  (repeated identical stimulus produces a measurable
   bounded decrement in response — looking-time, sucking-rate,
   etc.)
ToyI structural marker     : repeated identical STREAM_APPEND
  (processing_window_size=10, feedback_mode=OFF) produces
  exactly 1 entry whose recurrence_count climbs by exactly N
  to min(MIN + N, MAX). The structural change is monotonically
  bounded.
Why this is not a cognitive claim: ToyI has no attention, no
  arousal, no looking-time. The shape "repeated input -> bounded
  monotonic structural change in a single record" is the
  analogue.
```

### M03 — Recognition

```text
Human-development analogue : novelty / familiarity discrimination
  (preferential-looking; novel vs familiar produce distinct
   measurable responses)
ToyI structural marker     : two distinct seed texts under
  STREAM_APPEND produce two distinct Pattern Ledger entries
  whose pattern_ids differ; recurrence accounting holds
  independently per entry. The structural marker is "distinct
  input -> distinct record".
Why this is not a cognitive claim: ToyI has no preference, no
  looking. The analogue is the shape of differential structural
  registration.
```

### M04 — Rehearsal

```text
Human-development analogue : working-memory rehearsal in early
  childhood (verbal rehearsal extends item retention across a
  small bounded window)
ToyI structural marker     : Phase 3.18 processing window at N>0
  with feedback_mode=OFF produces 1 + N chunks; the seed entry's
  recurrence_count climbs by N. The bounded rehearsal loop is
  the analogue.
Why this is not a cognitive claim: ToyI has no working memory,
  no retention, no verbal subvocalization. The analogue is the
  shape "bounded internal loop reinforces a structural record".
```

### M05 — Pattern self-feedback

```text
Human-development analogue : early self-monitoring of repeated
  pattern recognition (the child's report "I've seen this before"
  is itself a structural observation that can re-enter the
  evidence stream)
ToyI structural marker     : Phase 3.19 PATTERN_LEDGER mode at
  N=10 produces 1 + 2*N chunks; >= 2 Pattern Ledger entries;
  the pledger-family observation sum equals N. The structural
  marker is "system's own recurrence record re-enters its evidence
  stream".
Why this is not a cognitive claim: ToyI has no self-report, no
  metacognition. The analogue is the shape "internal observation
  feeds back into observation substrate".
```

### M06 — Structural self-monitoring approximation

```text
Human-development analogue : a conflict-monitoring-like
  architecture in mature cognition (a read-only structural status
  report enters the cognitive evidence stream)
ToyI structural marker     : Phase 3.20 COHERENCE mode at N=10
  produces 1 + 2*N chunks; >= 2 entries; cohmon-family
  observation sum equals N. The CoherenceReport's overall_status
  is one of {PASS, WARN, FAIL, NOT_APPLICABLE} — structural
  status labels only, never truth claims.
Why this is not a cognitive claim: ToyI has no anterior
  cingulate cortex, no conflict adjudication, no judgment. The
  analogue is the shape "structural status report re-enters the
  substrate".
```

### M07 — Multi-modal integration

```text
Human-development analogue : integration of multiple monitoring
  streams in mature cognition (visual + auditory + proprioceptive
  feedback streams compose into a single behavioral substrate)
ToyI structural marker     : PATTERN_AND_COHERENCE mode at N=10
  produces 1 + 3*N chunks; >= 3 entries; both family observation
  sums equal N independently. The structural marker is
  "two independent bounded feedback streams compose without
  collision into one substrate".
Why this is not a cognitive claim: ToyI has no visual, auditory,
  or proprioceptive modality. The analogue is the shape "two
  independent bounded streams compose".
```

### M08 — Saturation + novelty

```text
Human-development analogue : habituation-then-dishabituation
  (the saturated familiarity record coexists with new-stimulus
   discrimination capacity)
ToyI structural marker     : a saturating input drives the seed
  entry to saturation_state == SATURATED; a subsequent distinct
  input still creates a NEW Pattern Ledger entry whose pattern_id
  differs from the seed's. Novelty discrimination is preserved
  past saturation of any single entry. Phase 3.18's saturation
  demonstration is the precedent.
Why this is not a cognitive claim: ToyI has no habituation in
  the biological sense, no arousal. The analogue is the shape
  "saturation of one record does not block creation of new
  records".
```

### M09 — Cross-input differentiation under feedback

```text
Human-development analogue : differentiated learning across
  contexts (the child shows context-dependent recall; the same
  stimulus in different contexts produces distinct records)
ToyI structural marker     : two distinct seed inputs each under
  PATTERN_AND_COHERENCE at N=10 produce pairwise-disjoint
  second-order Pattern Ledger entries (no collision across
  inputs). Entry counts add deterministically.
Why this is not a cognitive claim: ToyI has no context, no
  learning. The analogue is the shape "distinct inputs each
  drive distinct second-order records under feedback".
```

### M10 — Sustained complex behavior

```text
Human-development analogue : sustained complex behavior over a
  long sequence (adult sustained-attention / vigilance tasks)
ToyI structural marker     : three distinct inputs dispatched in
  order, each under PATTERN_AND_COHERENCE at N=50, produces
  total = 3 * (1 + 3 * 50) = 453 stream chunks; the kernel
  invariant assert_state_invariants stays green throughout; the
  Growth Ledger event count stays bounded (saturates at
  GROWTH_LEDGER_MAX_EVENTS = 256 with no eviction, which is the
  documented and correct behavior).
Why this is not a cognitive claim: ToyI has no attention, no
  vigilance, no fatigue. The analogue is the shape "long
  bounded sequence of high-throughput dispatch preserves all
  structural invariants".
```

---

## 4. Why the analogy stops where it does

Each milestone's analogue is bounded to one specific structural
shape. The human-development literature is rich with content
beyond the shape: phenomenology, semantic content, motivation,
context, social setting, neural correlates, individual variation,
developmental stage, sensitive periods, scaffolding,
intersubjectivity, language acquisition. ToyI has **none** of
these. The campaign deliberately rejects any extension of the
analogy into these domains, and every doc / fixture / catalog row
this campaign produces is audited against the canonical
`_FORBIDDEN_NON_CLAIM_TERMS` tuple to prevent drift.

This is the same discipline Phase 3.18 applied when borrowing
Stage 4 working-memory rehearsal as a structural analogue;
Phase 3.21 extends the discipline to nine more analogues without
relaxing it.

---

## 5. Substrate coverage map

```text
milestone | uses Phase 3.18 | uses Phase 3.19 | uses Phase 3.20 | new code
M01       | -               | -               | -               | helper only
M02       | yes (window>0)   | -               | -               | helper only
M03       | -               | -               | -               | helper only
M04       | yes              | -               | -               | helper only
M05       | yes              | yes             | -               | helper only
M06       | yes              | -               | yes             | helper only
M07       | yes              | yes             | yes             | helper only
M08       | yes              | -               | -               | helper only
M09       | yes              | yes             | yes             | helper only
M10       | yes              | yes             | yes             | helper only
```

No milestone requires new core runtime code. The
`milestone_harness.py` module is a strict consumer of the existing
public surfaces. The campaign therefore stays within the Lean
spec by construction: no new Lean theorem is claimed; no existing
catalog row is contradicted; the new rows are Engineering
hypotheses.

---

## 6. Determinism

Every milestone helper is pure deterministic over its inputs.
Two invocations with identical inputs produce identical
`MilestoneResult`. This follows from:

- the kernel state derivation is pure (Phase 3.18 D3 result);
- `build_pledger_summary_text` is pure (I-IFBK-02);
- `build_cohmon_summary_text` is pure (I-CFBK-02);
- `build_full_coherence_report` is pure over its `OperatorSession`
  input (I-COHMON-04..09);
- `assert_state_invariants` is pure;
- `derive_pattern_id` / `derive_pattern_signature` are pure.

No helper introduces time, random, PID, hostname, `id()`, or any
non-deterministic input.

---

## 7. Hypotheses for Step 3 to lock

```text
HH1. The closed-enum DevelopmentalMilestone with exactly 10
     members covers every analogue in this synthesis without
     gaps or duplicates.
HH2. Each milestone helper produces a single MilestoneResult
     whose status is one of {PASS, WARN, FAIL, NOT_APPLICABLE};
     the v1 acceptance condition expects 10 PASS / 0 WARN / 0
     FAIL / 0 NOT_APPLICABLE.
HH3. Every helper's primary_metric and secondary_metric are
     bounded int fields whose ranges are documented in Step 3.
HH4. The canonical _FORBIDDEN_NON_CLAIM_TERMS audit produces
     zero hits on every helper summary string and every
     module-produced constant.
HH5. The harness's import set is closed and audited (one new
     STRUCTURAL row I-DEVMILE-11).
HH6. Two independent invocations of run_all_milestones() produce
     bit-identical MilestoneResult tuples (cross-process
     determinism).
HH7. Cumulative real model calls across run_all_milestones() = 0;
     cumulative cache writes = 0; assert_state_invariants stays
     green throughout.
```

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the synthesis is derivable from the prior-campaign
  audits and the v0.28 repo state; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: single-doc shard.
```

---

## 9. Next artifact

`docs/campaigns/phase3_21/PHASE3_21_TEN_MILESTONES.md` — the
Step 3 ten-milestone definition doc, which binds each milestone's
exact helper signature, bounded inputs, success criterion,
primary metric, secondary metric, summary text shape, and failure
classification.

Paired with:
`docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CORRIGENDA.md`
— the Step 3 design locks (LOCK A through LOCK K).
