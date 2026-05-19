# Phase 3.25 — Osmotic Learning Test Design

Osmotic learning is an operational exposure effect over bounded
structural records, not a psychological or phenomenological claim.

## Operational definition

For the ToyI runtime, *osmotic structural imprinting* means:

> Unlabeled ambient input that matches an abstract structural digest
> (as derived by `derive_abstract_pattern_signature`) creates a
> session-local `ABSTRACT_PATTERN_ACQUIRED` record on first exposure
> (imprinting), and a later input whose tokens differ but whose
> abstract digest matches the same record triggers
> `ABSTRACT_PATTERN_REUSED` plus, when the prior pattern_id differs
> from the current input's pattern_id, `TRANSFER_RECOGNIZED`
> (activation).

The two phases — imprinting and activation — are distinct.

## Positive evidence

- After CONTROL_NO_EXPOSURE, the target digest is **not** in
  `has_acquired_digest(state.learning_trace, target_digest)`.
- After TRUE_EXPOSURE, the target digest **is** in
  `has_acquired_digest(state.learning_trace, target_digest)`.
- After TRUE_EXPOSURE followed by a renamed probe with the same
  abstract digest, the post-probe step's
  `learning_evidence_trace.records` contains both
  `ABSTRACT_PATTERN_REUSED` and `TRANSFER_RECOGNIZED` records for the
  matching digest.

## Negative evidence

- After SHAM_EXPOSURE (different abstract digest), the target digest
  is **not** acquired, **no transfer is detected** on the probe.
- After NO_EXPOSURE, the probe with the target digest emits an
  `ABSTRACT_PATTERN_ACQUIRED` record (first exposure) but **no**
  `TRANSFER_RECOGNIZED`.

## Falsification

The osmotic-learning claim is falsified if:

- TRUE_EXPOSURE fails to produce `ABSTRACT_PATTERN_ACQUIRED`;
- TRUE_EXPOSURE produces a record but a later renamed probe fails to
  produce `TRANSFER_RECOGNIZED`;
- SHAM_EXPOSURE produces a false `TRANSFER_RECOGNIZED` for the target
  digest;
- CONTROL_NO_EXPOSURE produces a false acquisition or transfer claim
  before the probe;
- the live-test runner's `digest_hex16` is not deterministic across
  two fresh runs of `run_osmotic_live_test()`.

## Out of scope

- Real-time external-world signals (no perception, no embodiment).
- Affect, valence, motivation, attention, awareness.
- Persistence across sessions (Phase 3.25 is session-local only).
- Model-backed osmotic probes (deterministic OFFLINE only; the
  optional model-backed smoke is deferred to a separate OBSERVED row
  if approved).
- Multi-digit / multi-symbol abstract patterns beyond what
  `derive_abstract_pattern_signature` already supports.

## Anti-cheating discipline

- The **runtime path** (the agent loop's `OperatorSession.dispatch`
  call) never receives the expected target digest or expected shape
  as an input.
- The OsmoticProbeTrial record carries `expected_target_digest` and
  `expected_target_shape`, but these are **only used by the
  benchmark assertion layer** after `run_osmotic_probe_trial()`
  returns.
- The exposure text **does not contain** any of the forbidden
  direct-instruction terms: `learn`, `remember`, `pattern`,
  `classify`, `transfer`, `reuse`, `ABAB`, `structure`, `shape`,
  `imprint`, `osmotic`, `absorb`, `imbibe`. (Note: `pattern` etc. may
  legitimately appear in the **trial id** or the **summary line**;
  the exclusion applies to the operator-input text only.)
- The probe text similarly avoids the forbidden direct-instruction
  terms.

## Targets and shapes (closed set used in the runner)

| target id | abstract shape | exposure example | probe example | digest |
|---|---|---|---|---|
| `T_ABAB` | `A B A B` | `red blue red blue` | `cat dog cat dog` | `d37efc29b0c680ba` |
| `T_ABBA` | `A B B A` | `copper tin tin copper` | `moon sun sun moon` | `40057bcfaed5886a` |
| `T_AAB` | `A A B` | `red red blue` | `cat cat dog` | `e8cfe826475e7d96` |
| `T_ABCABC` | `A B C A B C` | `red blue green red blue green` | `cat dog bird cat dog bird` | `9cd0ca7a79c87064` |
| `T_ABA` | `A B A` | `red blue red` | `cat dog cat` | `9dfde01c9a4cfc38` |

The digests are deterministic outputs of `derive_abstract_pattern_signature`
and are stable across runs (this is the Phase 3.22b invariant the
campaign builds on).

## Trial battery (10 trials)

| trial_id | condition | exposure texts | probe text | expected target | expected acquired pre-probe | expected transfer |
|---|---|---|---|---|---|---|
| `T01_control_abab` | CONTROL_NO_EXPOSURE | `()` | `cat dog cat dog` | `T_ABAB` | False | False |
| `T02_true_abab` | TRUE_EXPOSURE | `("red blue red blue",)` | `cat dog cat dog` | `T_ABAB` | True | True |
| `T03_true_abba` | TRUE_EXPOSURE | `("copper tin tin copper",)` | `moon sun sun moon` | `T_ABBA` | True | True |
| `T04_true_abcabc` | TRUE_EXPOSURE | `("red blue green red blue green",)` | `cat dog bird cat dog bird` | `T_ABCABC` | True | True |
| `T05_sham_abba_for_abab` | SHAM_EXPOSURE | `("red blue blue red",)` | `cat dog cat dog` | `T_ABAB` | False | False |
| `T06_distractor_abab` | DISTRACTOR_INTERFERENCE | `("red blue red blue", "kettle pot kettle pot", "moss fern moss fern")` | `cat dog cat dog` | `T_ABAB` | True | True |
| `T07_delayed_abab` | TRUE_EXPOSURE | `("red blue red blue", "kettle pot", "moss fern")` | `cat dog cat dog` | `T_ABAB` | True | True |
| `T08_control_aab` | CONTROL_NO_EXPOSURE | `()` | `cat cat dog` | `T_AAB` | False | False |
| `T09_renamed_aab` | TRUE_EXPOSURE | `("red red blue",)` | `cat cat dog` | `T_AAB` | True | True |
| `T10_renamed_ababc_combined` | DISTRACTOR_INTERFERENCE | `("red blue green red blue green", "kettle pot kettle pot", "moss fern moss fern")` | `cat dog bird cat dog bird` | `T_ABCABC` | True | True |

## Verdict mapping

For each trial:

- `PASS` iff every observed predicate matches the expected predicate:
  - `prior_acquired_observed == prior_acquired_expected`;
  - `transfer_observed == transfer_expected`;
  - no forbidden non-claim term in the probe's reply or any of the
    bounded summaries;
  - bounded structural records were emitted as the design predicts.
- `FAIL` if any observed predicate disagrees with the expected
  predicate.
- `WARN` if the trial cannot be evaluated due to a runtime structural
  refusal that is not a campaign-recoverable error (in practice, the
  v1 trial set is designed so this never fires).
- `NOT_APPLICABLE` only if the trial is skipped by design (none in
  v1).

## Aggregate counters

The `OsmoticLiveTestReport` exposes:

- `pass_count`, `warn_count`, `fail_count`, `not_applicable_count`,
- `false_positive_count` (transfers claimed but expected False),
- `false_negative_count` (transfers expected but not observed),
- `transfer_success_count` (transfers observed AND expected).

For the v1 trial set the spec requires: `false_positive_count == 0`,
`false_negative_count == 0`, `transfer_success_count == 6` (the six
TRUE_EXPOSURE + DISTRACTOR_INTERFERENCE trials that expect transfer).

## Determinism

Two invocations of `run_osmotic_live_test()` produce equal
`OsmoticLiveTestReport.digest_hex16` and bit-identical trial result
tuples. The digest is computed as the SHA-256 of the canonical
serialization of each `OsmoticProbeResult` in order.

## Resource discipline

- Zero real model calls.
- Zero cache writes.
- Zero forbidden-term hits in any produced string (the live-test
  report's `format_osmotic_live_test_report` output, all probe
  results' `summary_line` fields, and all reply excerpts).
- Zero invariant failures.
- No `brain.tick.tick` call outside the approved `STEP_TICK` route
  (the osmotic probe runs through `run_agent_interaction_step`, which
  does not invoke `tick` for the non-`STEP_TICK` paths).

## Citation pipeline

Each trial's `OsmoticProbeResult` includes the bounded reasoning trace
digest, the bounded learning evidence trace digest, and the bounded
dispatch trace digests for the exposure and the probe. These are
captured directly from the `AgentLoopResult` records.
