# PHASE3_21_DEVELOPMENTAL_TRAJECTORY_ROADMAP.md

## Purpose

Define the path from Phase 3.20's coherence-feedback bridge
(PR #25, catalog v0.28) to a **bounded ten-milestone
developmental trajectory** that the runtime can deterministically
demonstrate end-to-end. This roadmap is research-and-engineering
scaffolding — it does NOT define a process by which ToyI
develops in any psychological sense, and it makes no consciousness,
sentience, agency, or subjective-experience claim. The word
"developmental" is used in its **operational structural** sense
(the runtime *develops a deterministic trajectory across the ten
milestones*), never in the psychological sense.

`PASS / WARN / FAIL / NOT_APPLICABLE` are treated throughout as
**structural status labels**, never recoded as truth assertions.

---

## 1. Where Phase 3.20 left ToyI

Phase 3.20 (PR #25, catalog v0.28) shipped the bounded
Coherence Feedback Bridge:

- `FeedbackMode.COHERENCE` and `FeedbackMode.PATTERN_AND_COHERENCE`;
- pure deterministic `build_cohmon_summary_text(...)` helper;
- widened `_V1_EMITTED_SOURCES = {REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}`;
- `OperatorSession._run_cohmon_feedback_step` with deferred
  function-body import;
- 80-cell behavior matrix passed end-to-end; 0 model calls,
  0 cache writes, 0 invariant failures, all CoherenceReport
  overall_status `"pass"`;
- two new catalog rows `I-CFBK-01` and `I-CFBK-02`.

ToyI now supports four feedback modes (`OFF`, `PATTERN_LEDGER`,
`COHERENCE`, `PATTERN_AND_COHERENCE`) and three internal-event
sources (`REHEARSAL`, `PLEDGER_SUMMARY`, `COHMON_SUMMARY`) — all
exercised through `STREAM_APPEND` with deterministic bounded
output.

These primitives are the substrate Phase 3.21 composes into a
ten-milestone trajectory.

---

## 2. Phase 3.21 target

Define ten distinct **developmental milestones**, each grounded
in a well-studied human-development phenomenon, each tested at
the level of *structural marker only*. Build a bounded helper
module `brain/development/milestone_harness.py` that owns the
ten helpers and a `run_all_milestones()` aggregator. Land one new
catalog row family `I-DEVMILE-01..I-DEVMILE-11` (10 milestone
REQUIRED rows + 1 STRUCTURAL static-audit row) at catalog v0.28
-> v0.29.

The ten milestones, in order:

```text
M01  REFLEXIVE_BASELINE              single deterministic STREAM_APPEND;
                                     1 chunk; 1 entry; baseline assertion
                                     of the bounded substrate behavior
M02  HABITUATION                     repeated identical STREAM_APPEND;
                                     recurrence climbs by exactly N;
                                     saturation_state stays OPEN until
                                     recurrence_count >= cap
M03  RECOGNITION                     two distinct seed texts produce two
                                     distinct pattern_ids; entry tuple
                                     length = 2; per-entry recurrence
                                     accounting holds independently
M04  REHEARSAL                       processing_window_size > 0 under OFF;
                                     1 + N chunks; recurrence climbs by
                                     N (Phase 3.18 behavior preserved)
M05  PATTERN_SELF_FEEDBACK           PATTERN_LEDGER mode at N=10; 1+2N
                                     chunks; >= 2 entries; pledger family
                                     observation sum = N (Phase 3.19
                                     behavior preserved)
M06  STRUCTURAL_SELF_MONITORING      COHERENCE mode at N=10; 1+2N chunks;
                                     >= 2 entries; cohmon family
                                     observation sum = N (Phase 3.20
                                     behavior preserved)
M07  MULTI_MODAL_INTEGRATION         PATTERN_AND_COHERENCE mode at N=10;
                                     1+3N chunks; >= 3 entries; both
                                     family observation sums = N
                                     (Phase 3.20 combined behavior
                                     preserved)
M08  SATURATION_NOVELTY              repeated saturating input (N=255)
                                     drives seed entry to
                                     saturation_state == SATURATED;
                                     a subsequent distinct input still
                                     creates a NEW entry (novelty
                                     discrimination is preserved past
                                     saturation)
M09  CROSS_INPUT_DIFFERENTIATION     two distinct inputs each under
                                     PATTERN_AND_COHERENCE produce
                                     deterministic distinct second-order
                                     entries; pattern_id sets are
                                     disjoint across input pairs;
                                     entry counts add (no collision)
M10  SUSTAINED_BEHAVIOR              long sequence: three distinct inputs
                                     dispatched in order, each under
                                     PATTERN_AND_COHERENCE at N=50;
                                     total chunks = 3 * (1+3*50) = 453;
                                     assert_state_invariants stays green
                                     throughout; growth ledger event
                                     count bounded by GROWTH_LEDGER_MAX_EVENTS
                                     = 256 (the ledger is allowed to
                                     saturate at cap with no eviction)
```

Each milestone is exercised by a single pure deterministic
helper. The helpers compose into `run_all_milestones()`, which
returns an ordered tuple of `MilestoneResult` records.

---

## 3. Human-development analogues (analogy at structural marker only)

Each ToyI milestone has a clearly bounded analogue from
well-studied human-development literature. The analogy is at the
level of **structural marker only** — never at the level of
phenomenology, semantic content, agency, awareness, or
psychological status. Phase 3.21 makes no claim that ToyI
literally exhibits any human-developmental phenomenon; it claims
only that the runtime substrate produces deterministic
structural behavior that is *analogously shaped* to the
phenomenon's textbook marker.

```text
M01 REFLEXIVE_BASELINE ~~ neonatal reflexive response
    Analogous structural marker: input -> deterministic single-step
    state change. The newborn's reflex arc produces a stereotyped
    response to a single stimulus. ToyI's STREAM_APPEND produces
    a deterministic single chunk + single Pattern Ledger entry.

M02 HABITUATION ~~ stimulus habituation across the first weeks
    Analogous structural marker: repeated identical stimulus
    produces a measurable bounded change (decrement in response,
    or in ToyI's case an increment in recurrence_count). The
    infant's looking-time decrement is analogous, at the level of
    "structural marker that climbs deterministically with repeated
    presentations".

M03 RECOGNITION ~~ early novelty / familiarity discrimination
    Analogous structural marker: novel vs familiar inputs produce
    distinct internal records. The classic preferential-looking
    novelty paradigm relies on the infant producing one response
    to familiar and another to novel; ToyI produces one Pattern
    Ledger entry per distinct structural signature.

M04 REHEARSAL ~~ working-memory rehearsal in the preschool years
    Analogous structural marker: holding a representation
    bounded-internally across a small window of cycles. The
    Phase 3.18 processing window's deterministic rehearsal loop
    is the structural analogue.

M05 PATTERN_SELF_FEEDBACK ~~ early self-monitoring of repeated
    pattern recognition
    Analogous structural marker: a system's own recurrence record
    re-enters its evidence stream. The Phase 3.19 pledger_summary
    chunk is the structural analogue.

M06 STRUCTURAL_SELF_MONITORING ~~ conflict-monitoring-like
    architecture in adolescence / adulthood
    Analogous structural marker: a system's read-only
    structural status report re-enters its evidence stream. The
    Phase 3.20 cohmon_summary chunk is the structural analogue.
    (NOT a claim about anterior cingulate cortex, conflict
    adjudication, or any specific neural correlate.)

M07 MULTI_MODAL_INTEGRATION ~~ integration of multiple monitoring
    streams in mature cognition
    Analogous structural marker: simultaneous bounded feedback
    from two independent observers re-enters the same substrate.
    PATTERN_AND_COHERENCE is the structural analogue.

M08 SATURATION_NOVELTY ~~ habituation-then-dishabituation
    Analogous structural marker: a saturated familiarity record
    coexists with new-stimulus discrimination capacity. The
    classic Olsho / Werker design relies on this; ToyI's Pattern
    Ledger entry can saturate while novel inputs still create new
    entries.

M09 CROSS_INPUT_DIFFERENTIATION ~~ differentiated learning across
    contexts
    Analogous structural marker: multiple distinct contexts each
    produce their own bounded record without cross-contamination.
    The "context-dependent learning" literature provides the
    analogue.

M10 SUSTAINED_BEHAVIOR ~~ sustained complex behavior across a
    long sequence (adult cognition)
    Analogous structural marker: deterministic bounded behavior
    over a long input sequence without invariant violation. Adult
    sustained-attention tasks are the analogue.
```

Each analogy is intentionally narrow. ToyI has none of:
infancy, childhood, adolescence, looking-time, anterior cingulate
cortex, attention, learning, memory in the psychological sense,
context, experience, sustained attention, or any cognitive /
subjective property. The analogies are *structural shape only*.

---

## 4. Module / file architecture

### 4.1 New runtime file

```text
brain/development/milestone_harness.py
    - DevelopmentalMilestone closed (str, Enum) with 10 members:
        M01_REFLEXIVE_BASELINE = "m01_reflexive_baseline"
        M02_HABITUATION = "m02_habituation"
        M03_RECOGNITION = "m03_recognition"
        M04_REHEARSAL = "m04_rehearsal"
        M05_PATTERN_SELF_FEEDBACK = "m05_pattern_self_feedback"
        M06_STRUCTURAL_SELF_MONITORING = "m06_structural_self_monitoring"
        M07_MULTI_MODAL_INTEGRATION = "m07_multi_modal_integration"
        M08_SATURATION_NOVELTY = "m08_saturation_novelty"
        M09_CROSS_INPUT_DIFFERENTIATION = "m09_cross_input_differentiation"
        M10_SUSTAINED_BEHAVIOR = "m10_sustained_behavior"
    - MilestoneStatus closed (str, Enum) with PASS/WARN/FAIL/NOT_APPLICABLE
    - MilestoneResult frozen / slotted dataclass:
        milestone: DevelopmentalMilestone
        status: MilestoneStatus
        summary: str (bounded printable, non-claim-clean)
        primary_metric: int (bounded; one int per milestone)
        secondary_metric: int (bounded; one int per milestone)
    - per-milestone helper functions:
        run_m01_reflexive_baseline() -> MilestoneResult
        run_m02_habituation() -> MilestoneResult
        ...
        run_m10_sustained_behavior() -> MilestoneResult
    - run_all_milestones() -> tuple[MilestoneResult, ...]:
        runs the ten helpers in order; returns the full tuple
    - MODULE_PRODUCED_STRINGS tuple (non-claim-clean by audit)
    - bounded constants:
        MILESTONE_SUMMARY_MAX_LEN = 240
        MILESTONE_SEQUENCE_RECOMMENDED_INPUTS (per-milestone fixed
            text seeds; bounded printable)
```

Import set (closed; audited by the new STRUCTURAL row):

```text
__future__
dataclasses
enum
typing
brain.development.coherence_monitor (for build_full_coherence_report
    in M06/M07; mirrored deferred-import pattern from session.py is
    NOT needed here because milestone_harness.py is not imported by
    coherence_monitor — no cycle)
brain.development.pattern_ledger (for derive_pattern_id /
    derive_pattern_signature in M03/M09)
brain.development.processing_window (for FeedbackMode /
    InternalEventSource)
brain.development.text_stream (for STREAM_PATTERN_RECURRENCE_*)
brain.tick (BrainState + initial_state + assert_state_invariants
    only — never the tick callable)
brain.ui.commands (Command / OperatorCommand / StreamAppendPayload)
brain.ui.session (OperatorSession)
brain.tlica.profile (COGITO_ID)
```

NO other imports. NO `brain.llm`. NO curses. NO `os` / `subprocess`
/ `socket` / `urllib` / `http` / `requests` / `pathlib` / `tempfile`
/ `shutil` / `threading` / `asyncio` / `atexit` / `signal` /
`importlib` / `time` / `random` / `hashlib` / `math`.

### 4.2 Fixture inventory

Eleven new fixtures under `brain/ui/fixtures/`:

```text
developmental_milestone_m01.py     (REQUIRED, I-DEVMILE-01)
developmental_milestone_m02.py     (REQUIRED, I-DEVMILE-02)
developmental_milestone_m03.py     (REQUIRED, I-DEVMILE-03)
developmental_milestone_m04.py     (REQUIRED, I-DEVMILE-04)
developmental_milestone_m05.py     (REQUIRED, I-DEVMILE-05)
developmental_milestone_m06.py     (REQUIRED, I-DEVMILE-06)
developmental_milestone_m07.py     (REQUIRED, I-DEVMILE-07)
developmental_milestone_m08.py     (REQUIRED, I-DEVMILE-08)
developmental_milestone_m09.py     (REQUIRED, I-DEVMILE-09)
developmental_milestone_m10.py     (REQUIRED, I-DEVMILE-10)
developmental_milestone_static_audit.py  (STRUCTURAL, I-DEVMILE-11)
```

Step 4 may consolidate the ten REQUIRED fixtures into a single
file with ten `@register` entries if that's cleaner. The static
audit always lives in a separate file.

### 4.3 No modifications to existing runtime files

`brain/development/processing_window.py`, `brain/ui/session.py`,
`brain/development/coherence_monitor.py`, `brain/development/pattern_ledger.py`,
`brain/development/growth_ledger.py`, `brain/development/text_stream.py`,
and `brain/tick.py` are all unchanged. The milestone harness is a
strict consumer of the existing surfaces.

### 4.4 Catalog changes

```text
INVARIANT_CATALOG.md:
    v0.28 -> v0.29
    REQUIRED: 284 -> 294  (+10 milestone rows)
    STRUCTURAL: 91 -> 92  (+1 static audit row)
    NOT-EXERCISED / DEFERRED / OBSERVED: unchanged

brain/_catalog_ids.py: regenerated via `python3 -m tools.catalog generate-ids`

tools/catalog.py EXPECTED_COUNTS: bumped to {REQUIRED: 294, STRUCTURAL: 92,
    NOT-EXERCISED: 14, DEFERRED: 15, OBSERVED: 16}

README.md: catalog banner v0.28 -> v0.29; catalog history entry
    for v0.29

CURRENT_MISSION.md / CURRENT_CAMPAIGN.md: baseline updates to
    reflect v0.29 after Step 6 lands the patch
```

---

## 5. Lean spec compliance

Every new catalog row is marked as **Engineering hypothesis**
(Phase 3 source label), per the precedent established by
Phase 3.12c, 3.13, 3.14, 3.15, 3.16, 3.17, 3.18, 3.19, and 3.20.
No new Lean theorem is claimed. The Lean spec in `lean_reference/`
is not contradicted because:

- the milestones are operational structural assertions about
  Python runtime behavior;
- no existing REQUIRED row is modified;
- no Lean citation is added or changed;
- the milestone harness is a strict consumer of existing surfaces.

This is the standard pattern the campaign-wide non-Lean rows have
followed since Phase 3.7.

---

## 6. Behavior plan (preview of Step 7)

Step 7 runs `run_all_milestones()` against a fresh
`OperatorSession` and records:

```text
- per-milestone (status, primary_metric, secondary_metric, summary)
- aggregate count by status (expected: 10 PASS, 0 WARN / FAIL /
  NOT_APPLICABLE in the v1 acceptance condition)
- deterministic re-run: two independent invocations produce
  bit-identical MilestoneResult tuples
- cumulative real model calls (= 0)
- cumulative cache counter delta (= 0)
- kernel invariant gate (PASS)
- non-claim audit on every produced summary string
```

If any milestone returns FAIL, Step 7 halts and reports the
failure; the campaign does not advance to Step 8 / 9 / 10 until
the FAIL is resolved.

WARN is acceptable for a milestone that has a documented
known-limitation (e.g., M08 may be WARN if the cap-saturation
re-run is intentionally bounded below N=255 to keep test runtime
short). Each WARN must be explicitly justified in
`PHASE3_21_MILESTONE_LOG.md`.

---

## 7. Non-claim discipline

```text
- Every produced summary string is audited against
  brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS.
- No aggregate "developmental score" / "maturity score" /
  "I-ness score" anywhere.
- The word "develop" / "developmental" is used only in the
  operational structural sense (the runtime develops the trajectory).
  The word "milestone" is used in the operational sense (a fixed
  point in the sequence), never in the developmental-psychology
  sense.
- The word "growth" appears only in references to GrowthLedger /
  GrowthEvent, which are already engineering-language constructs.
- No claim of "learning", "experience", "understanding",
  "introspection", "metacognition", "self-awareness",
  "consciousness", "sentience", "agency", "will", "desire",
  "intent", or "belief" appears in any helper output, fixture,
  catalog row, or doc.
- PASS / WARN / FAIL / NOT_APPLICABLE labels are structural status
  labels only.
- Human-development analogues are described in Section 3 of this
  roadmap, in the Step 2 synthesis, and in Step 3's milestone
  definitions — always with the explicit "structural marker only"
  qualifier.
```

---

## 8. Validation plan

```text
Before every commit:
  python3 -m tools.claude_helpers.gate_runner --json

After Step 6 lands the harness + catalog patch:
  python3 -c "from brain.development.milestone_harness import \
      run_all_milestones; tuple(run_all_milestones())"
  (smoke test the harness runs without exception)

After Step 7 records outcomes:
  python3 -m brain.invariants run
  (verify every new I-DEVMILE-NN row is green)
```

---

## 9. PR plan

```text
branch:        campaign/phase3-21-developmental-trajectory
base initial:  current Phase 3.20 HEAD (PR #25 open)
final PR:      base = campaign/phase3-20-coherence-feedback-bridge
               (while PR #25 is open)
               base = main
               (once both PR #24 and PR #25 have merged)
title:         phase3.21: developmental trajectory
merge policy:  never merge without explicit user approval
```

---

## 10. Disclosure expectation

Each step's final report includes the canonical Stage A / Stage B /
Stage C.1 disclosure block. Stage C.1 may draft doc shards;
parent Claude commits and pushes every step.

---

## 11. Hard limits

```text
- 10 milestones (no more, no fewer)
- 1 + 10 + 1 = 12 catalog rows (I-DEVMILE-01..I-DEVMILE-11; no
  more)
- 1 new runtime module (brain/development/milestone_harness.py)
- 11 new fixtures (one per milestone + one static audit) or
  optionally a consolidated form fixed by Step 4
- 0 modifications to existing runtime modules
- 0 real model calls
- 0 cache writes
- 0 tick() calls
- 0 schema changes
```

---

## 12. Next step pointer

After Step 1 commits + pushes, the next eligible step is **Step 2
Human-Development Synthesis** at
`docs/campaigns/phase3_21/PHASE3_21_HUMAN_DEVELOPMENT_SYNTHESIS.md`.
