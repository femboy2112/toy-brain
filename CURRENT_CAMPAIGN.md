# CURRENT_CAMPAIGN.md — Phase 3.26 Active Hypothesis + Self-Directed Probe Loop

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.26 stacks on the completed Phase 3.25 work
(`campaign/phase3-25-osmotic-learning-live-test`, PR #30 open). Phase
3.26 asks one bounded operational question:

```text
Under bounded live-test conditions, can the existing substrate
(abstract_pattern signature + learning evidence + reasoning trace +
dispatch trace + worldlet feedback + the Phase 3.25 osmotic
imprinting+activation surface) realize the operational analogue of
"active hypothesis + self-directed probe"? That is: given a
deliberately ambiguous structural input, can the runtime enumerate a
bounded candidate set, derive one safe internal probe per candidate
(without leaking expected outcomes), execute each probe through the
existing `run_agent_interaction_step` route, prune candidates whose
probe outcomes do not match the candidate's predictions, decline to
nominate a winner when zero survive, and on a second visit to the
same ambiguous input reuse the surviving record without re-probing
-- while control / no-survivor / multi-survivor / reuse conditions
correctly avoid false positives and false negatives?
```

This is a **research / integration / behavioral-benchmark** campaign.
It is **NOT** a proof of consciousness, sentience, subjective
experience, agency, semantic understanding, real reasoning, real
inquiry, real curiosity, real deliberation, intentionality, awareness,
intuition, embodiment, psychological development, or any cognitive
process. "Active hypothesis" / "self-directed probe" is a controlled
technical metaphor for *bounded structural candidate enumeration +
falsification + caching at the substrate level*; it is engineering
shorthand and does NOT claim psychological hypothesis formation,
inquiry, deliberation, decision-making, planning, introspection, or
metacognition.

Phase 3.26 does **not** implement SelfModel; does **not** add any new
`OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS`
value, `GrowthEventType`, `GrowthEventSource`, persistence schema
column, autosave trigger, `LearningEvidenceKind` member, or
`ReasoningStepKind` member; does **not** change L1 / L2 / parser /
prompt / tick / persistence / autosave / DB schema semantics. The
runtime touches are limited to:

- **One new closed module**
  `brain/development/active_hypothesis_probe.py`
  (pure / deterministic / bounded). Closed import set: `__future__`,
  `argparse`, `dataclasses`, `enum`, `hashlib`, `sys`, `typing`,
  `brain.development.abstract_pattern`,
  `brain.development.agent_loop`,
  `brain.development.coherence_monitor` (only for
  `_FORBIDDEN_NON_CLAIM_TERMS`),
  `brain.development.learning_evidence`,
  `brain.development.reasoning_trace`. No `brain.llm.*`, no
  `brain.tick`, no `brain.ui.session`, no curses, no I/O, no host
  execution, no `time`, no `random`.
- **One new benchmark axis** `BenchmarkAxis.ACTIVE_HYPOTHESIS` with
  the fourteen cases `A13.01..A13.14`. The full battery now runs
  A1..A13 (103 cases total = 89 from Phase 3.22 / 3.22b / 3.23 / 3.24
  / 3.25 + 14 from Phase 3.26).

Catalog patch: v0.34 → v0.35 with the bounded `I-AHYP-01..14` row
family (Engineering hypothesis, Phase 3 source label). Split: 13
REQUIRED (I-AHYP-01..13) + 1 STRUCTURAL (I-AHYP-14). New fixtures
live under `brain/ui/fixtures/`.

Branch:

```text
campaign/phase3-26-active-hypothesis-probe
```

Base: `campaign/phase3-25-osmotic-learning-live-test` (PR #30).
Final PR (likely #31):
`phase3.26: active hypothesis + self-directed probe loop`.

---

## Step ledger

```text
Step 1  Mission + design + roadmap docs                       commit phase3.26 step1
Step 2  Active hypothesis probe substrate                     commit phase3.26 step2
        (brain/development/active_hypothesis_probe.py)
Step 3  Hypothesis enumeration + probe selection trials       commit phase3.26 step3
Step 4  Probe execution + no-survivor + reuse trials          commit phase3.26 step4
Step 5  Learning / reasoning / dispatch / worldlet wiring     commit phase3.26 step5
Step 6  Benchmark A13 active_hypothesis axis                  commit phase3.26 step6
Step 7  Catalog v0.35 + I-AHYP-01..14 fixtures                commit phase3.26 step7
Step 8  Live test proof + transcripts + behavior +
        findings reports                                      commit phase3.26 step8
Step 9  Final audit + handoff + open PR #31                   commit phase3.26 step9
```

Push after every successful step.

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, intuition, embodiment,
  perception, unconscious learning, real hypothesis formation, real
  inquiry, real curiosity, real deliberation, real decision-making, or
  real planning.
- No new aggregate scalar field (no "consciousness score", no
  "hypothesis confidence score", no "active inquiry score", no
  "I-ness score").
- No reply text uses the language of wondering, deciding, choosing,
  investigating, inquiring, deliberating, planning (in the cognitive
  sense), introspecting, being curious, wanting to know, or any
  subjective-access language.
- The active-hypothesis runner is deterministic and OFFLINE; zero
  real model calls, zero cache writes, zero forbidden-term hits.
- The runtime path NEVER receives the candidate hypothesis's
  predicted digest or predicted shape as an input. Expected-outcome
  fields on the trial record are used ONLY by the benchmark assertion
  layer after the runtime path emits its result.
- No selected probe text may contain any
  `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS` (the same exclusion list used
  in Phase 3.25 plus `hypothesis`, `candidate`, `probe`, `predict`,
  `falsify`, `survive`, `decide`, `infer`).

---

## Acceptance criteria

Phase 3.26 succeeds only when:

- `brain.development.active_hypothesis_probe` exists with the closed
  `AmbiguityCondition` and `ActiveHypothesisStatus` enums and the
  bounded `ActiveHypothesisCandidate`, `ActiveProbeStep`,
  `ActiveHypothesisTrial`, `ActiveHypothesisResult`,
  `ActiveHypothesisLiveTestReport` records.
- `enumerate_hypotheses()` returns a bounded tuple sized
  `0..ACTIVE_HYPOTHESIS_MAX_CANDIDATES`, deterministic across two
  invocations on the same input.
- `select_safe_probe()` returns a bounded printable probe text
  whose body contains none of the
  `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS` and whose construction does
  not consume the candidate's `predicted_digest_hex16` or
  `predicted_shape` as a token.
- `run_active_hypothesis_live_test()` returns a bounded report whose
  verdict meets the design predicates: every CONTROL_NO_AMBIGUITY
  trial PASS with `survivors_count == 0` and `probe_steps == ()`;
  every SINGLE_HYPOTHESIS_CONVERGES trial PASS with
  `winner_id != ""` and `survivors_count == 1`; every
  MULTI_HYPOTHESIS_NARROWS trial PASS with
  `survivors_count >= 1`; every NO_HYPOTHESIS_SURVIVES trial PASS
  with `winner_id == ""` and `survivors_count == 0`; every
  REUSE_CACHED_HYPOTHESIS trial PASS with `second_visit_cache_hit`
  True and `second_visit_probe_count == 0`.
- `false_positive_count == 0`, `false_negative_count == 0`,
  `winner_selected_count` equals the design's expected value.
- Two invocations of `run_active_hypothesis_live_test()` produce
  equal `digest_hex16` and bit-identical trial result tuples.
- Benchmark A13 is green; existing A1..A12 axes do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.35 banner.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5
  PASS.
- No new `brain.llm` import; no `brain.tick.tick` call outside the
  approved `STEP_TICK` route; no host execution; no DB schema
  change; no curses; no new `LearningEvidenceKind` member; no new
  `ReasoningStepKind` member.
- PR #31 is open with base
  `campaign/phase3-25-osmotic-learning-live-test`; no PR is merged.
