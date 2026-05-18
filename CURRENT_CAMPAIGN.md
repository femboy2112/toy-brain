# CURRENT_CAMPAIGN.md — Phase 3.25 Osmotic Learning Live Test

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.25 stacks on the completed Phase 3.24 work
(`campaign/phase3-24-worldlet-feedback-bridge`, PR #29 open). Phase
3.25 asks one bounded operational question:

```text
Under bounded live-test conditions, does the existing substrate
(abstract_pattern signature + learning evidence + reasoning trace +
dispatch trace + worldlet feedback) realize the operational analogue
of osmotic imprinting -- that is, does ambient unlabeled exposure to
a structural form create a session-local structural record
(imprinting) such that a later renamed / transformed probe with the
same abstract digest re-activates that record (activation), while
control / sham / distractor conditions correctly avoid false
positives and false negatives?
```

This is a **research / integration / behavioral-benchmark** campaign.
It is **NOT** a proof of consciousness, sentience, subjective
experience, agency, semantic understanding, real learning,
intentionality, awareness, intuition, embodiment, or psychological
development.

Phase 3.25 does **not** implement SelfModel; does **not** add any new
`OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS`
value, `GrowthEventType`, `GrowthEventSource`, persistence schema
column, or autosave trigger; does **not** change L1 / L2 / parser /
prompt / tick / persistence / autosave / DB schema semantics. The
runtime touches are limited to:

- **One new closed module** `brain/development/osmotic_learning_probe.py`
  (pure / deterministic / bounded). Closed import set: `__future__`,
  `dataclasses`, `enum`, `hashlib`, `typing`,
  `brain.development.abstract_pattern`, `brain.development.agent_loop`,
  `brain.development.coherence_monitor` (only for
  `_FORBIDDEN_NON_CLAIM_TERMS`), `brain.development.learning_evidence`,
  `brain.development.reasoning_trace`. No `brain.llm.*`, no
  `brain.tick`, no curses, no I/O, no host execution.
- **One new benchmark axis** `BenchmarkAxis.OSMOTIC_LEARNING` with the
  fourteen cases `A12.01..A12.14`. The full battery now runs A1..A12
  (89 cases total = 65 from Phase 3.22 / 3.22b / 3.23 + 12 from Phase
  3.24 + 14 from Phase 3.25).

Catalog patch: v0.33 → v0.34 with the bounded `I-OSMO-01..14` row
family (Engineering hypothesis, Phase 3 source label). Split: 13
REQUIRED (I-OSMO-01..13) + 1 STRUCTURAL (I-OSMO-14). New fixtures
live under `brain/ui/fixtures/`.

Branch:

```text
campaign/phase3-25-osmotic-learning-live-test
```

Base: `campaign/phase3-24-worldlet-feedback-bridge` (PR #29).
Final PR (likely #30): `phase3.25: osmotic learning live test`.

---

## Step ledger

```text
Step 1  Mission + design + roadmap docs                   commit phase3.25 step1
Step 2  Osmotic probe substrate                           commit phase3.25 step2
        (brain/development/osmotic_learning_probe.py)
Step 3  Control + sham + true-exposure trials             commit phase3.25 step3
Step 4  Transfer + delayed-probe + distractor trials      commit phase3.25 step4
Step 5  Learning / reasoning / dispatch integration       commit phase3.25 step5
Step 6  Benchmark A12 osmotic_learning axis               commit phase3.25 step6
Step 7  Catalog v0.34 + I-OSMO-01..14 fixtures            commit phase3.25 step7
Step 8  Live test proof + transcripts + behavior +
        findings reports                                  commit phase3.25 step8
Step 9  Final audit + handoff + open PR #30               commit phase3.25 step9
```

Push after every successful step.

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, intuition, embodiment,
  perception, or unconscious learning.
- No new aggregate scalar field (no "consciousness score", no
  "learning score", no "osmotic absorption score", no "I-ness
  score").
- No reply text uses the language of imbibing, soaking, absorption,
  intuition, insight, awareness, or subjective access.
- The osmotic probe runner is deterministic and OFFLINE; zero real
  model calls, zero cache writes, zero forbidden-term hits.
- The runtime path NEVER receives the expected target digest or
  expected shape as an input. Expected-shape labels are only used by
  the benchmark assertion layer after the runtime emits its result.

---

## Acceptance criteria

Phase 3.25 succeeds only when:

- `brain.development.osmotic_learning_probe` exists with the closed
  `OsmoticCondition` and `OsmoticProbeStatus` enums and the bounded
  `OsmoticExposureEvent`, `OsmoticProbeTrial`, `OsmoticProbeResult`,
  `OsmoticLiveTestReport` records.
- `run_osmotic_live_test()` returns a bounded report whose verdict
  meets the design predicates: every CONTROL_NO_EXPOSURE trial PASS;
  every TRUE_EXPOSURE trial PASS with `transfer_observed == True`;
  every SHAM_EXPOSURE trial PASS with `transfer_observed == False`;
  every DISTRACTOR_INTERFERENCE trial PASS.
- `false_positive_count == 0`, `false_negative_count == 0`,
  `transfer_success_count` equals the design's expected six.
- Two invocations of `run_osmotic_live_test()` produce equal
  `digest_hex16` and bit-identical trial result tuples.
- Benchmark A12 is green; existing A1..A11 axes do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.34 banner.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5
  PASS.
- No new `brain.llm` import; no `brain.tick.tick` call outside the
  approved `STEP_TICK` route; no host execution; no DB schema
  change; no curses.
- PR #30 is open with base `campaign/phase3-24-worldlet-feedback-bridge`;
  no PR is merged.
