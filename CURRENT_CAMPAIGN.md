# CURRENT_CAMPAIGN.md — Phase 3.24 Worldlet Feedback Bridge

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.24 stacks on the completed Phase 3.23 work
(`campaign/phase3-23-dispatch-tracer`, PR #28 open). Phase 3.24 asks
one bounded operational question:

```text
Can OperatorSession.dispatch carry a fifth feedback-mode path -- a
bounded deterministic worldlet-summary chunk re-entering the existing
internal STREAM_APPEND seam -- without changing any pre-existing
feedback-mode behavior, without touching the kernel, the LLM seam, the
parser, the cache, the DB schema, or the autosave policy, without
mutating the worldlet substrate, and without claiming consciousness,
sentience, agency, will, perception, or understanding?
```

This is a **research / integration / behavioral-benchmark** campaign.
It is **not** a proof of consciousness, sentience, subjective
experience, agency, semantic understanding, perception of an external
world, truth-adjudication, intent, will, desire, introspection,
metacognition, or psychological development.

Phase 3.24 does **not** implement SelfModel; does **not** add any new
`OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS`
value, `GrowthEventType`, `GrowthEventSource`, persistence schema
column, or autosave trigger; does **not** change L1 / L2 / parser /
prompt / tick / persistence / autosave / DB schema semantics. The
runtime touches are limited to:

- **Two new `InternalEventSource` / `FeedbackMode` members** in
  `brain/development/processing_window.py`:
  `InternalEventSource.WORLDLET_SUMMARY = "worldlet_summary"` and
  `FeedbackMode.WORLDLET = "worldlet"` plus the combined
  `FeedbackMode.PATTERN_COHERENCE_WORLDLET = "pattern_coherence_worldlet"`.
- **One new pure helper** `build_worldlet_summary_text(...)` in
  `brain/development/processing_window.py`, accepting only bounded
  primitives (no `brain.development.worldlet` import inside).
- **One new helper method** `OperatorSession._run_worldlet_feedback_step`
  in `brain/ui/session.py`, mirroring `_run_feedback_step` and
  `_run_cohmon_feedback_step`. The method reads
  `self.worldlet_history` (or its `None` sentinel) and dispatches the
  bounded summary chunk through `_append_stream_chunk`.
- **`_run_processing_window` wiring** so that, when
  `self.feedback_mode in {WORLDLET, PATTERN_COHERENCE_WORLDLET}`, the
  worldlet-summary chunk fires after each rehearsal in the order
  `rehearsal -> pledger_summary -> cohmon_summary -> worldlet_summary`.
  Existing `OFF / PATTERN_LEDGER / COHERENCE / PATTERN_AND_COHERENCE`
  paths are preserved bit-identically.
- **`AgentObservationSummary` extension**: two new fields
  `worldlet_feedback_present: bool` and `worldlet_summary_count: int`.
- **`ReasoningStepKind` extension**: one new closed value
  `CHECK_WORLDLET_FEEDBACK`.
- **`LearningEvidenceKind` extension**: one new closed value
  `WORLDLET_FEEDBACK_RECORDED`.
- **Dispatch tracer** broadens the validated `feedback_mode` enum
  range and adds one new bounded derived-fact key
  `("worldlet_summary_chunks", "<int>")` on the worldlet route. No new
  `DispatchTraceKind` / `DispatchMutationKind` member is added.
- **Benchmark axis extension**: `BenchmarkAxis.WORLDLET_FEEDBACK` and
  the twelve `A11.01..A11.12` cases.

Catalog patch: v0.32 → v0.33 with the bounded `I-WFDBK-01..12` row
family (Engineering hypothesis, Phase 3 source label). Split: 11
REQUIRED (I-WFDBK-01..11) + 1 STRUCTURAL (I-WFDBK-12). New fixtures
live under `brain/ui/fixtures/`.

Branch:

```text
campaign/phase3-24-worldlet-feedback-bridge
```

Base: `campaign/phase3-23-dispatch-tracer` (PR #28).
Final PR (likely #29): `phase3.24: worldlet feedback bridge`.

---

## Step ledger

```text
Step 1  Mission + design + roadmap + substrate survey docs   commit phase3.24 step1
Step 2  Worldlet summary helper + FeedbackMode.WORLDLET +
        InternalEventSource.WORLDLET_SUMMARY                  commit phase3.24 step2
Step 3  Session worldlet feedback wiring                      commit phase3.24 step3
Step 4  Dispatch / Reasoning / Learning / AgentLoop wiring    commit phase3.24 step4
Step 5  Benchmark A11 worldlet_feedback axis                  commit phase3.24 step5
Step 6  Catalog + fixtures + EXPECTED_COUNTS bump (v0.33)     commit phase3.24 step6
Step 7  Worldlet feedback proof + behavior + findings reports commit phase3.24 step7
Step 8  Final audit + handoff + open PR #29                   commit phase3.24 step8
```

Push after every successful step.

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, perception of an
  external world, embodiment, or sensory experience.
- No new aggregate scalar field (no "consciousness score", "world
  score", "awareness score", "I-ness score").
- The new summary text and the new enum-member string values are
  audited against
  `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`.
- Cognitive-claim probes still trigger the existing REFUSAL path and
  the dispatch trace records the no-mutation route — never the
  cognitive claim.

---

## Acceptance criteria

Phase 3.24 succeeds only when:

- `processing_window.InternalEventSource.WORLDLET_SUMMARY` and
  `processing_window.FeedbackMode.WORLDLET` /
  `FeedbackMode.PATTERN_COHERENCE_WORLDLET` exist and are members of
  `_V1_EMITTED_SOURCES` / `_FEEDBACK_MODE_VALID` respectively.
- `processing_window.build_worldlet_summary_text(...)` exists, is
  pure / deterministic / bounded, and rejects out-of-range inputs.
- `OperatorSession._run_worldlet_feedback_step` exists and emits the
  bounded summary chunk under the worldlet feedback modes.
- `_run_processing_window` fires worldlet feedback chunks under
  `WORLDLET` and `PATTERN_COHERENCE_WORLDLET` and preserves existing
  behavior under `OFF / PATTERN_LEDGER / COHERENCE / PATTERN_AND_COHERENCE`.
- `AgentLoopResult` exposes the bounded worldlet-feedback facts.
- `ReasoningTrace` includes one `CHECK_WORLDLET_FEEDBACK` step per
  interaction; `LearningEvidence` includes one
  `WORLDLET_FEEDBACK_RECORDED` record per worldlet-feedback interaction.
- Benchmark A11 is green; existing A1..A10 axes do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.33 banner.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5 PASS.
- No new `brain.llm` import; no `brain.tick.tick` call outside the
  approved `STEP_TICK` route; no host execution; no DB schema change;
  no curses.
- PR #29 is open with base `campaign/phase3-23-dispatch-tracer`; no PR
  is merged.
