# Phase 3.25 — Final Audit

## Mission verdict

**PASS WITH DEFERRED FOLLOW-UPS.** Every acceptance criterion in
`PHASE3_25_OSMOTIC_LEARNING_LIVE_TEST_ROADMAP.md` and
`docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LIVE_TEST_SPEC.md`
section S.12 is satisfied.

## Acceptance criteria checklist

```text
[x] brain/development/osmotic_learning_probe.py exists with the
    closed OsmoticCondition + OsmoticProbeStatus enums and the
    bounded OsmoticExposureEvent / OsmoticProbeTrial /
    OsmoticProbeResult / OsmoticLiveTestReport records.
[x] run_osmotic_live_test() returns a 10-trial bounded report.
[x] Every CONTROL_NO_EXPOSURE trial PASS.
[x] Every TRUE_EXPOSURE trial PASS with transfer_observed == True.
[x] Every SHAM_EXPOSURE trial PASS with transfer_observed == False.
[x] Every DISTRACTOR_INTERFERENCE trial PASS.
[x] false_positive_count == 0, false_negative_count == 0.
[x] transfer_success_count == 7 (matches design).
[x] Two invocations of run_osmotic_live_test() produce equal
    digest_hex16 and bit-identical trial result tuples.
[x] Benchmark A12 is green (14 / 14 PASS).
[x] Existing A1..A11 axes do not regress.
[x] python3 -m brain.invariants run is fully green (454 rows, 0
    red, 0 gate failures).
[x] python3 -m tools.catalog counts matches v0.34 banner.
[x] bash tools/check_all.sh passes.
[x] python3 -m tools.claude_helpers.gate_runner --json reports
    5 / 5 PASS.
[x] No new brain.llm import; no brain.tick.tick call outside the
    approved STEP_TICK route; no host execution; no DB schema
    change; no curses.
[x] Branch campaign/phase3-25-osmotic-learning-live-test pushed.
[ ] PR #30 open (Step 9 will open it).
[x] No PR is merged.
```

## Disclosure block

```text
Stage A ChatGPT/Codex consultation:  not used in this session
Stage B limited-write collaboration: not used in this session
Stage C.1 flow orchestration:        not used in this session
brain-catalog-lint:                  not used (manual catalog
                                     edits are tightly scoped and
                                     verified by check_all.sh)
brain-campaign-state:                not used
brain-explorer:                      not used
brain-runner-debugger:               not used
brain-row-implementer:               not used
brain-spec-refresher:                not used
Real model calls used this session:  0
Cumulative real model calls used:    0 / 20
```

## Final benchmark / runner / gate signatures

```text
runner BATTERY_VERSION:               phase3.25.v1
benchmark BATTERY_VERSION:            phase3.25.v1
benchmark total cases:                91
benchmark PASS / WARN / FAIL:         90 / 1 / 0
benchmark axis A12 status:            PASS (14 / 14)
benchmark transcript digest:          50d1a0ffefcf5ce4
gate_runner gates passed / total:     5 / 5
invariants runner rows checked:       454
invariants REQUIRED green / red:      349 / 0
invariants STRUCTURAL green / red:    98 / 0
catalog version:                      v0.34
catalog REQUIRED / STRUCTURAL:        348 / 98
real model calls:                     0
cache writes:                         0
forbidden term hits:                  0
determinism failures:                 0

live-test trials:                     10
live-test PASS / WARN / FAIL / NA:    10 / 0 / 0 / 0
live-test false_positive_count:       0
live-test false_negative_count:       0
live-test transfer_success_count:     7
live-test report digest:              7aa91075cd76ea73
```

## Sample digests

```text
T01_control_abab     learning=581a2a881ced7f81  reasoning=aad4658332c8321e
T02_true_abab        learning=10feee0cf4a98d64  reasoning=1f59da9dde68c8fd
T05_sham_abba        learning=b4e006d8652254e6  reasoning=345c16d2c989256e
T06_distractor       learning=6aca915eb56c6d69  reasoning=0ecb4d351a81c66c
```

## Step ledger

```text
Step 1  Mission + design + roadmap docs                   commit c060f51 (pushed)
Step 2  Osmotic probe substrate                           commit 0fd55c2 (pushed)
        (brain/development/osmotic_learning_probe.py)
Step 3..5  Trials + integration                            (folded into Step 2 commit)
Step 6  Benchmark A12 osmotic_learning axis               commit e2a3152 (pushed)
Step 7  Catalog v0.34 + I-OSMO-01..14 fixtures            commit 266b201 (pushed)
Step 8  Live test proof + transcripts + spec + synthesis +
        behavior + findings + audit                       commit <this>     (pending)
Step 9  Final audit + handoff + open PR #30               (next step)
```

## Hard non-claim recap

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, intuition,
  unconscious learning, perception of an external world,
  embodiment, or sensory experience.
- No new aggregate scalar field.
- The runner's source, every `MODULE_PRODUCED_STRINGS` entry,
  every produced summary line / reply excerpt / report line, and
  every operator-input text passes the canonical non-claim audit.
- Cognitive-claim probes still trigger the existing REFUSAL path;
  the osmotic probe runner never bypasses that path.
