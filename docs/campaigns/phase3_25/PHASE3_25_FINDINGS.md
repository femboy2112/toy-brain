# Phase 3.25 — Findings

## Demonstrated

- Under the bounded v1 trial battery, the existing substrate
  (abstract-pattern signature layer + learning evidence ledger)
  realizes the operational analogue of osmotic imprinting and
  activation:
  - 5 / 5 TRUE_EXPOSURE trials produce `ABSTRACT_PATTERN_ACQUIRED`
    on first exposure and `ABSTRACT_PATTERN_REUSED +
    TRANSFER_RECOGNIZED` on the renamed probe.
  - 2 / 2 CONTROL_NO_EXPOSURE trials correctly avoid false
    acquisition / false transfer.
  - 1 / 1 SHAM_EXPOSURE trial correctly distinguishes a different
    abstract digest from the target.
  - 2 / 2 DISTRACTOR_INTERFERENCE trials recover the target digest
    despite intervening distractors.
- The live-test runner's report digest is bit-identical across two
  fresh invocations (`7aa91075cd76ea73`).
- No cognitive-claim probe is needed to demonstrate the effect; the
  forbidden-direct-instruction scan blocks any leak of the
  experimental contract into operator-input text.

## What did NOT land (deferred)

The campaign did not (and was not asked to):

- Add new `LearningEvidenceKind` / `ReasoningStepKind` values. The
  v1 design reuses the existing `ABSTRACT_PATTERN_ACQUIRED`,
  `ABSTRACT_PATTERN_REUSED`, `TRANSFER_RECOGNIZED`, `DERIVE_PATTERN`,
  `LOOKUP_PRIOR_STRUCTURE`, `COMPARE_STRUCTURE` records / steps;
  the closed enums are sufficient.
- Run a model-backed live smoke. The deterministic OFFLINE runner
  is the only path that gates. A separate OBSERVED row for a
  model-backed smoke is deferred to a future campaign and would
  require explicit operator approval.
- Add cross-session retention tests. The trial state is session-
  local only.
- Add a 'mutated runtime' fail-state demonstrating that a buggy
  agent loop emits false positives. The campaign uses only the
  green agent loop and confirms it correctly distinguishes the
  conditions.

## Defects observed during implementation

- F1 (resolved). Initial draft of `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS`
  did not include `ABBA`, `ABCABC`, `imprint`, `osmotic`, `absorb`,
  `imbibe`, `intuition`. These were added before any trial was
  written so that no v1 exposure or probe text smuggles experimental
  contract language into the runtime path.

- F2 (resolved). The original benchmark fixture for A11 / A10
  (`agent_benchmark_runner_green.py`, `dispatch_tracer_benchmark_axis.py`,
  `worldlet_feedback_benchmark_axis.py`) locked the prior 11-axis
  shape and the case_total of 77. Phase 3.25 widens both to 12 / 91.

- F3 (resolved). Adding the `OsmoticLearning` axis re-bases the
  benchmark transcript digest from `b91c4ece90c8706f` (Phase 3.24)
  to `50d1a0ffefcf5ce4` (Phase 3.25). A10.10's "digest stable
  across two runs" assertion still passes because both runs see the
  new digest.

## What stayed weak

- W1. A3.04 remains a WARN: overall-status `NOT_APPLICABLE` is not
  publicly reachable. This is a Phase 3.21 W3 follow-up blocker, not
  Phase 3.25-introduced. Phase 3.27 (coherence aggregation refinement)
  is the recommended next campaign.
- W2. The v1 trial battery uses 10 trials drawn from 5 target shapes
  (ABAB, ABBA, AAB, ABCABC, ABA-as-distractor-only). Extending to
  more target shapes (e.g. ABCDABCD, ABCDD, etc.) is a future
  refinement, not a defect.

## Next campaign suggestions (ranked)

1. **Phase 3.26 — Worldlet UI Construction** (Phase 3.24 W2
   follow-up). Add a bounded operator command to populate
   `OperatorSession.worldlet_history` end-to-end so the "populated
   worldlet" branch of the Phase 3.24 helper is exercised through
   the public dispatcher.
2. **Phase 3.27 — Coherence Aggregation Refinement** (A3.04
   follow-up).
3. **Phase 3.28 — Dispatch Trace Ring Buffer** (Phase 3.23
   backlog).
4. **Phase 3.29 — Osmotic Live-Test Multi-Session Retention** (a
   future extension to test imprinting persistence across `STEP_TICK`
   boundaries, if the substrate ever supports cross-session
   persistence). Currently not in scope.

## Resource discipline (final)

```text
real_model_calls used this campaign:  0
cumulative real_model_calls used:     0 / 20
cache_writes:                         0
forbidden_term_hits:                  0
determinism_failures:                 0
invariant_failures:                   0
gate_runner verdict:                  5 / 5 PASS
catalog version:                      v0.34
benchmark verdict:                    91 cases, 90 PASS + 1 WARN + 0 FAIL
osmotic live-test verdict:            10 / 10 PASS, fp=0, fn=0, transfer=7
osmotic live-test digest:             7aa91075cd76ea73
```
