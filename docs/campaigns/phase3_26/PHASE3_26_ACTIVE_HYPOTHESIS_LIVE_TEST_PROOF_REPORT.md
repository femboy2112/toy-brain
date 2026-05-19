# Phase 3.26 — Active Hypothesis + Self-Directed Probe Loop — Live Test Proof Report

> Active hypothesis + self-directed probe in ToyI is a bounded
> operational enumeration + falsification + caching effect over
> structural records, not a psychological or phenomenological claim.

## Headline result

```text
active_hypothesis_live_test
  version             = phase3.26.v1
  trials              = 10
  pass_count          = 10
  warn_count          = 0
  fail_count          = 0
  not_applicable_count = 0
  false_positive_count = 0
  false_negative_count = 0
  winner_selected_count = 3   (T03, T04, T09)
  no_hypothesis_survives_count = 3   (T07, T08, T10)
  cache_reuse_count   = 2     (T09, T10)
  real_model_calls    = 0
  cache_writes        = 0
  forbidden_term_hits = 0
  digest_hex16        = 86b67d97daeb251d
```

Two invocations of `run_active_hypothesis_live_test()` produced
bit-identical `digest_hex16` and bit-identical `trials` tuples.

## Per-trial table

| trial_id | condition | input | survivors | winner | no_surv | cache_hit | verdict |
|---|---|---|---|---|---|---|---|
| T01_control_empty        | CONTROL_NO_AMBIGUITY        | `""`              | 0 | `""`              | False | False | PASS |
| T02_control_singleton    | CONTROL_NO_AMBIGUITY        | `alpha`           | 0 | `""`              | False | False | PASS |
| T03_single_aba           | SINGLE_HYPOTHESIS_CONVERGES | `red blue red`    | 1 | `H_RENAME_S_ABA`  | False | False | PASS |
| T04_single_abb           | SINGLE_HYPOTHESIS_CONVERGES | `red blue blue`   | 1 | `H_RENAME_S_ABB`  | False | False | PASS |
| T05_multi_abc            | MULTI_HYPOTHESIS_NARROWS    | `red blue green`  | 3 | `""`              | False | False | PASS |
| T06_multi_abab           | MULTI_HYPOTHESIS_NARROWS    | `red blue red blue` | 3 | `""`            | False | False | PASS |
| T07_nosurv_aa            | NO_HYPOTHESIS_SURVIVES      | `red red`         | 0 | `""`              | True  | False | PASS |
| T08_nosurv_aab           | NO_HYPOTHESIS_SURVIVES      | `red red blue`    | 0 | `""`              | True  | False | PASS |
| T09_reuse_aba            | REUSE_CACHED_HYPOTHESIS     | `red blue red`    | 1 | `H_RENAME_S_ABA`  | False | True  | PASS |
| T10_reuse_aa             | REUSE_CACHED_HYPOTHESIS     | `red red`         | 0 | `""`              | True  | True  | PASS |

## What the runner observed (operational claim)

For each trial the runner:

1. Computed `enumerate_hypotheses(input_text)` — a bounded
   deterministic tuple of `ActiveHypothesisCandidate` records
   (0..4 in the v1 battery), keyed on the input's
   `(abstract_pattern_classification, token_count)`.
2. For each candidate, computed
   `select_safe_probe(input_text, candidate)` — a bounded printable
   probe text derived purely from input surface tokens and the
   candidate's `probe_construction_rule`. The probe never contains
   the candidate's `predicted_digest_hex16` or `predicted_shape`,
   never contains any forbidden direct-instruction term, never
   exceeds `ACTIVE_HYPOTHESIS_PROBE_MAX_LEN = 240`.
3. Executed the probe through `run_agent_interaction_step`. The
   resulting `AgentLoopResult` carried the learning evidence trace,
   the reasoning trace, and the dispatch trace as for any ordinary
   operator input.
4. Computed `observed_digest = derive_abstract_pattern_signature(
   probe_text).digest_hex16`.
5. Marked the candidate `SURVIVING` iff
   `observed_digest == candidate.predicted_digest_hex16`; otherwise
   `FALSIFIED`.
6. If exactly one candidate survived, promoted it to `SELECTED` and
   recorded its id as `winner_id`. If zero survived, left
   `winner_id == ""` and set `no_hypothesis_survives = True`. If two
   or more survived, left `winner_id == ""` and left every survivor
   at `SURVIVING`.
7. Stored the result under the input's canonical digest in a
   session-local cache. For `REUSE_CACHED_HYPOTHESIS` trials whose
   input's canonical digest matched a prior entry, returned the
   cached prior result with `second_visit_cache_hit = True` and
   `second_visit_probe_count = 0`.

## What the runner did NOT do (anti-overclaim)

- It did NOT introduce a new `LearningEvidenceKind`,
  `ReasoningStepKind`, `GrowthEventType`, `GrowthEventSource`,
  `OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, or
  `ACTIVE_VIEWS` value.
- It did NOT call `brain.tick.tick` outside the `STEP_TICK` route
  used by `run_agent_interaction_step`.
- It did NOT import `brain.llm`.
- It did NOT consume the candidate's `predicted_digest_hex16` or
  `predicted_shape` in any operator-input text (the runtime path
  never sees the expected outcome).
- It did NOT add a `hypothesis confidence score`, an
  `active inquiry score`, or any aggregate scalar field.
- It did NOT make any real model call (`real_model_calls == 0`).
- It did NOT write to the L1 / L2 LLM cache (`cache_writes == 0`).
- It did NOT emit any forbidden non-claim term in any produced
  string (`forbidden_term_hits == 0`).

## Citation pipeline

Every non-control trial result carries:

- `learning_evidence_digest` — a 16-hex digest computed from the
  post-trial `LearningEvidenceTrace.records` tuple.
- `reasoning_trace_digest` — the 16-hex digest of the last probe
  step's reasoning trace report.
- `dispatch_trace_digests` — a tuple whose length equals
  `len(probe_steps)`; each entry is a 16-hex
  `DispatchTraceReport.trace_digest_hex16`.

Two invocations of `run_active_hypothesis_live_test()` produce equal
citations for every trial id (verified by I-AHYP-10 and I-AHYP-11).

## Bounded operational claim (allowed)

ToyI's runtime can exhibit operational active hypothesis +
self-directed probe behavior: given a deliberately ambiguous
structural input, the runtime enumerates a bounded candidate set,
derives one safe internal probe per candidate from the input itself
(no expected-outcome leak), executes each probe through the existing
agent interaction path, prunes candidates whose probe outcome does
not match the candidate's prediction, declines to nominate a winner
when zero candidates survive, and on a second visit to the same
ambiguous input reuses the surviving record without re-probing.

Under bounded live-test conditions (CONTROL_NO_AMBIGUITY,
SINGLE_HYPOTHESIS_CONVERGES, MULTI_HYPOTHESIS_NARROWS,
NO_HYPOTHESIS_SURVIVES, REUSE_CACHED_HYPOTHESIS), the runtime
correctly maps every trial input to its expected verdict with
`false_positive_count == 0` and `false_negative_count == 0`.

## Non-claim recap (forbidden)

This proof report does NOT claim consciousness, sentience, awareness,
subjective experience, human-like understanding, real agency, will,
desire, belief, intent, introspection, metacognition, intuition,
embodiment, real hypothesis formation, real inquiry, real curiosity,
real deliberation, real planning, or real decision-making.
"Self-directed" means the probe text is derived from the input by a
closed deterministic rule. The runtime is a bounded structural state
machine.

## Reproduction

```bash
python3 -m brain.development.active_hypothesis_probe
# active_hypothesis_live_test version=phase3.26.v1 trials=10 pass=10 ...
# digest=86b67d97daeb251d
# real_model_calls=0 cache_writes=0 forbidden_term_hits=0
```

```bash
python3 -m brain.invariants run | tail -2
# 468 rows checked  ·  REQUIRED green: 362  ·  REQUIRED red: 0  ·
#                       STRUCTURAL green: 99  ·  STRUCTURAL red: 0  ·
#                       OBSERVED: 7 pass / 0 fail  ·  gate failures: 0
```

```bash
python3 -m brain.development.agent_benchmark --quiet
# (exits 2 due to the documented A3.04 WARN carry-over; 104 PASS + 0 FAIL)
```

```bash
bash tools/check_all.sh
# All checks passed.
```
