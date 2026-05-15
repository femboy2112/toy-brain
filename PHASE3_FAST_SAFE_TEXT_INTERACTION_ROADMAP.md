# PHASE3_FAST_SAFE_TEXT_INTERACTION_ROADMAP.md

## Purpose

Top-level roadmap for the Fast Safe Text Interaction macro-campaign that
follows the completed Phase 3.5 Expression + ReadabilityPredictor work.
This document is a navigation aid for the detailed sequence in
`CURRENT_CAMPAIGN.md`.

## Current status

```text
Phase 3.5 Expression + ReadabilityPredictor   COMPLETE
  Latest audit:   PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
  Audit verdict:  PASS
  Catalog:        v0.12
  Counts:         139 REQUIRED / 48 STRUCTURAL / 5 NOT-EXERCISED /
                  12 DEFERRED / 8 OBSERVED
  Full gate:      green

Phase 3.6 Reflective Inspection               NEXT (active)
Phase 3.7 Text Stream Ingress                 PLANNED
Phase 3.8 Operator Stream Interaction         PLANNED
```

## Macro-campaign target

```text
operator submits bounded text chunks
  -> chunks enter local TextStreamHistory
  -> deterministic stream summaries and candidates become inspectable
  -> operator explicitly promotes a validated candidate into the queue
  -> existing /step route remains the only tick() route
```

Final operator-facing commands after Phase 3.8 lands:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
/step
/tick
/state
```

## Phase sequence

```text
Phase 3.6 Reflective Inspection
  Minimal read-only developmental summary layer over the
  existing OutputHistory, WorldletHistory, ProtoBasicHistory,
  ExpressionHistory, and OperatorTranscript.
  Likely row family: I-REF-*
  Stops at a review gate after the catalog patch plan and again
  after the Phase 3.6 audit.

Phase 3.7 Text Stream Ingress
  Raw text chunks below the promotion boundary. Introduces a
  bounded TextStreamHistory and structural segment / pattern /
  promotion-candidate primitives.
  Likely row family: I-STRM-*
  Stops at a review gate after the catalog patch plan and again
  after the Phase 3.7 audit.

Phase 3.8 Operator Stream Interaction
  Operator TUI surface that exposes the Phase 3.7 layer through a
  finite typed command set. Promotion candidates queue only
  through the existing PerceptEvent constructor and only via the
  explicit /stream-promote command.
  Likely row family: I-UI-STRM-* (or I-UI-* continuation)
  Stops at a review gate after the catalog patch plan; the
  Phase 3.8 audit precedes the final campaign PR.
```

## Non-negotiable boundaries

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
developmental histories remain local until explicit promotion
tick() remains the only TLICA runtime transition route
single-event tick discipline remains intact
Expression remains local evidence only
Readability remains local readability evidence only
Reflective Inspection remains read-only and below Mode B
operator commands remain finite, typed, bounded, and inspectable
```

Hard-boundary paths may be touched only when a specific campaign
step explicitly allows them:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

## Git workflow

```text
campaign branch:  campaign/fast-safe-text-interaction
step commits:     after every successful step that changes files
branch pushes:    after every step commit
final PR:         phase3: fast safe text interaction campaign
direct main push: never
auto-merge:       never (explicit user approval required)
```

## Cross-references

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
FAST_SAFE_APPLY_INSTRUCTIONS.md
FAST_SAFE_CROSSREFERENCE_NOTES.md
PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
INVARIANT_CATALOG.md
```

## What this is not

- not a chat layer
- not a language-model integration
- not a Mode B reflective planning campaign
- not a self-modification surface
- not a real-host execution surface
- not a serialization or persistence campaign
- not a UI redesign campaign

## What this is

A bounded, deterministic, read-then-promote text interaction loop
that keeps the existing TLICA kernel boundary, the existing
`PerceptEvent` constructor, and the existing `tick()` route in place
while expanding what an operator can inspect and how text evidence
enters the candidate queue.
