# Phase 3.26 — Active Hypothesis + Self-Directed Probe Loop — Live Test Spec

This spec freezes the acceptance contract for the v1 active-hypothesis
live-test runner.

## Module under test

`brain/development/active_hypothesis_probe.py`

## Public API contract

- `enumerate_hypotheses(input_text: str) -> tuple[ActiveHypothesisCandidate, ...]`
  — pure, deterministic, returns a tuple of length
  `0..ACTIVE_HYPOTHESIS_MAX_CANDIDATES = 8`. Returns `()` for inputs
  whose `derive_abstract_pattern_signature` classification is in
  `{empty, singleton, overlong, non-printable, too-many-tokens}`.
- `construct_probe_text(input_text: str, rule: ProbeConstructionRule) -> str`
  — pure deterministic application of one of six rules:
  `RENAME_ONLY`, `APPEND_POS0_TOKEN`, `APPEND_POS1_TOKEN`,
  `APPEND_LAST_TOKEN`, `APPEND_NEW_TOKEN`, `RENAME_AND_DOUBLE`.
- `select_safe_probe(input_text: str, candidate: ActiveHypothesisCandidate) -> str`
  — wraps `construct_probe_text` and enforces the four non-leakage
  invariants (bounded printable, no forbidden direct-instruction
  term, no `predicted_digest_hex16` substring, no `predicted_shape`
  substring).
- `run_active_hypothesis_trial(trial, *, cache=None) -> ActiveHypothesisResult`
  — runs the full enumerate / probe / prune / select cycle; for
  REUSE_CACHED_HYPOTHESIS trials with a populated cache, returns
  the cached prior result with `second_visit_cache_hit=True`,
  `second_visit_probe_count=0`.
- `run_active_hypothesis_live_test(trials=None) -> ActiveHypothesisLiveTestReport`
  — threads one cache through the v1 ten-trial battery; produces
  a deterministic `digest_hex16`.
- `build_active_hypothesis_trials() -> tuple[ActiveHypothesisTrial, ...]`
  — the v1 ten-trial battery.
- `format_active_hypothesis_live_test_report(report) -> str`
  — bounded printable table; forbidden-term-clean.
- `active_hypothesis_live_test_digest(report) -> str`
  — 16-hex SHA-256 over the canonical serialization of each result.

## Closed enums

| enum | values |
|---|---|
| `AmbiguityCondition`        | `control_no_ambiguity`, `single_hypothesis_converges`, `multi_hypothesis_narrows`, `no_hypothesis_survives`, `reuse_cached_hypothesis` |
| `ActiveHypothesisStatus`    | `pending`, `surviving`, `falsified`, `selected` |
| `ProbeConstructionRule`     | `rename_only`, `append_pos0_token`, `append_pos1_token`, `append_last_token`, `append_new_token`, `rename_and_double` |
| `TrialVerdict`              | `pass`, `warn`, `fail`, `not_applicable` |
| `ProbeOutcome`              | `confirmed`, `falsified` |

## Bounded record shapes (slot tuples)

- `ActiveHypothesisCandidate`: `(candidate_id, predicted_shape_name,
  predicted_shape, predicted_classification,
  predicted_digest_hex16, probe_construction_rule, status)`.
- `ActiveProbeStep`: `(candidate_id, probe_text,
  probe_digest_hex16, probe_shape, probe_classification,
  predicted_digest_hex16, outcome, interaction_id,
  dispatch_trace_digest, reasoning_trace_digest, reply_excerpt)`.
- `ActiveHypothesisTrial`: `(trial_id, condition, input_text,
  expected_survivors_count, expected_winner_id,
  expected_no_hypothesis_survives,
  expected_second_visit_cache_hit)`.
- `ActiveHypothesisResult`: `(trial_id, condition, verdict,
  input_digest_hex16, candidates, probe_steps, survivors_count,
  winner_id, no_hypothesis_survives, second_visit_cache_hit,
  second_visit_probe_count, false_positive, false_negative,
  learning_evidence_digest, reasoning_trace_digest,
  dispatch_trace_digests, summary_line)`.
- `ActiveHypothesisLiveTestReport`: `(battery_version, trials,
  pass_count, warn_count, fail_count, not_applicable_count,
  false_positive_count, false_negative_count,
  winner_selected_count, no_hypothesis_survives_count,
  cache_reuse_count, real_model_calls, cache_writes,
  forbidden_term_hits, digest_hex16, summary_line)`.

## Bounded constants

| constant | value |
|---|---|
| `ACTIVE_HYPOTHESIS_BATTERY_VERSION`         | `"phase3.26.v1"` |
| `ACTIVE_HYPOTHESIS_TRIAL_ID_MAX_LEN`        | 64 |
| `ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN`    | 48 |
| `ACTIVE_HYPOTHESIS_INPUT_MAX_LEN`           | 240 |
| `ACTIVE_HYPOTHESIS_PROBE_MAX_LEN`           | 240 |
| `ACTIVE_HYPOTHESIS_SHAPE_MAX_LEN`           | 64 |
| `ACTIVE_HYPOTHESIS_CLASSIFICATION_MAX_LEN`  | 32 |
| `ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN`          | 16 |
| `ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN`    | 320 |
| `ACTIVE_HYPOTHESIS_REPLY_EXCERPT_MAX_LEN`   | 320 |
| `ACTIVE_HYPOTHESIS_MAX_CANDIDATES`          | 8 |
| `ACTIVE_HYPOTHESIS_MAX_PROBE_STEPS`         | 8 |
| `ACTIVE_HYPOTHESIS_MAX_TRIALS`              | 64 |

## Acceptance criteria

- `run_active_hypothesis_live_test()` returns 10 trials, all PASS.
- `false_positive_count == 0` and `false_negative_count == 0`.
- `winner_selected_count == 3` (T03, T04, T09).
- `no_hypothesis_survives_count == 3` (T07, T08, T10).
- `cache_reuse_count == 2` (T09, T10).
- `real_model_calls == 0`, `cache_writes == 0`,
  `forbidden_term_hits == 0`.
- `digest_hex16 == "86b67d97daeb251d"` (the v1 plan signature).
- Two invocations of `run_active_hypothesis_live_test()` produce
  bit-identical `trials` tuples.
- A13 benchmark axis green (14 / 14 PASS).
- Full battery green (105 cases: 104 PASS + 1 documented A3.04 WARN
  + 0 FAIL).
- `python3 -m brain.invariants run` reports 468 rows checked, all
  REQUIRED + STRUCTURAL rows green.
- 5/5 gates PASS in `python3 -m tools.claude_helpers.gate_runner --json`.

## Falsification triggers

The spec is falsified if:

- `enumerate_hypotheses(input)` is non-deterministic for any input;
- `select_safe_probe` returns a probe text containing the
  candidate's `predicted_digest_hex16`, `predicted_shape`, or any
  forbidden direct-instruction term;
- a candidate whose `predicted_digest_hex16` matches the observed
  probe digest is marked `FALSIFIED`;
- a candidate whose `predicted_digest_hex16` does NOT match is
  marked `SURVIVING`;
- a trial with two surviving candidates has a non-empty `winner_id`;
- a trial with zero surviving candidates has a non-empty `winner_id`;
- a CONTROL_NO_AMBIGUITY trial emits any probe steps;
- a second invocation against a populated cache re-runs any probe;
- the live-test runner's `digest_hex16` is not deterministic across
  two fresh runs;
- any produced string contains a `_FORBIDDEN_NON_CLAIM_TERMS` entry.

## Non-claim discipline

The spec forbids all of: consciousness, sentience, awareness,
subjective experience, real understanding, real agency, will,
desire, belief, intent, introspection, metacognition, intuition,
embodiment, real hypothesis formation, real inquiry, real curiosity,
real deliberation, real decision-making, real planning.
"Self-directed" is operational only.
