# Phase 3.24 — Worldlet Feedback Bridge — Roadmap

## Goal

Add a **bounded worldlet-summary feedback path** that composes with the
existing Phase 3.18 / 3.19 / 3.20 processing-window architecture and with
the Phase 3.22 / 3.22b / 3.23 agent communication loop. The new path is
a **fifth feedback option** that re-enters the same internal STREAM_APPEND
seam used today by `pledger_summary` and `cohmon_summary` chunks.

This campaign is research / integration / behavioral-benchmark work. It
is **not** a proof of consciousness, sentience, awareness, subjective
experience, agency, will, desire, belief, intent, introspection,
metacognition, or human-like understanding. "Worldlet feedback" is
engineering shorthand for *a bounded structural summary of the
session-local Minimal Worldlet substrate, replayed through the
processing window so the Pattern Ledger and downstream traces can
observe it*.

## Allowed claim shape

> ToyI's runtime can append a bounded deterministic worldlet-summary
> chunk to its session-local stream after each rehearsal, when the
> session's `feedback_mode` is `WORLDLET` (or a combined worldlet
> mode). The summary text encodes only bounded printable structural
> facts about the Minimal Worldlet substrate (state id, attempt /
> response counts, accepted / pushback counts, latest reason). The
> Pattern Ledger observes the chunk as any other internal chunk; the
> Dispatch Trace records `feedback_mode=worldlet` and the
> internal-source provenance; the Reasoning Trace cites a
> `CHECK_WORLDLET_FEEDBACK` step; the Learning Evidence ledger cites
> a `WORLDLET_FEEDBACK_RECORDED` record. This is a behavioral
> property of the substrate — never a claim of perception of an
> external world.

## Forbidden claim shape

> ToyI perceives the external world / has a body / has senses /
> understands meaning / is conscious / is sentient / is aware / has
> agency / has will / has desire / introspects / has metacognition.

If asked whether ToyI has a world / is conscious / is sentient /
understands, the runtime's deterministic reply must DENY the cognitive
claim and describe itself as a **bounded structural runtime that emits
a worldlet-summary chunk**.

## Step ledger

```text
Step 1  Mission + design + roadmap + substrate survey docs
Step 2  Worldlet summary helper + FeedbackMode.WORLDLET +
        InternalEventSource.WORLDLET_SUMMARY in processing_window.py
Step 3  OperatorSession._run_worldlet_feedback_step wiring
Step 4  DispatchTracer / ReasoningTrace / LearningEvidence /
        AgentLoop integration
Step 5  Benchmark A11 worldlet_feedback axis (12 cases A11.01..A11.12)
Step 6  Catalog v0.32 -> v0.33; I-WFDBK-01..12 (11 REQUIRED + 1
        STRUCTURAL); fixtures
Step 7  Proof + behavior + findings reports
Step 8  Final audit + handoff + open PR #29
```

Push after every successful step.

## Branch / PR plan

```text
branch:  campaign/phase3-24-worldlet-feedback-bridge
base:    campaign/phase3-23-dispatch-tracer  (PR #28 open)
PR:      #29  phase3.24: worldlet feedback bridge
```

Do not merge anything. Retarget only if the base stack lands and the
retarget is safe.

## Hard non-claim boundary (recap)

- No claim of consciousness / sentience / awareness / subjective
  experience / human-like understanding / real agency / will / desire /
  belief / intent / introspection / metacognition.
- No new aggregate scalar field (no "consciousness score", "world
  score", "awareness score", "I-ness score").
- The new worldlet summary text contains only bounded printable
  structural facts (state id, counts, latest reason). No raw worldlet
  payload, no external-world claim, no token semantics.
- Cognitive-claim probes still trigger the existing REFUSAL path and
  the dispatch trace records the no-mutation route.

## Acceptance criteria

Phase 3.24 succeeds only when every criterion in
`docs/campaigns/phase3_24/PHASE3_24_WORLDLET_FEEDBACK_SPEC.md` is met,
the runner is green, the benchmark A1..A11 is green (1 known WARN
A3.04 carried forward at most), gate_runner is 5 / 5 PASS, branch is
pushed, and PR #29 is open.
