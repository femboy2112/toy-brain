# Phase 3.26 — Active Hypothesis + Self-Directed Probe Loop — Test Design

Active hypothesis + self-directed probe is a bounded operational
enumeration + falsification + caching effect over structural records,
not a psychological or phenomenological claim. "Self-directed" means
the runtime derives the probe from the input alone via a closed
deterministic rule; it does NOT mean the runtime "wants" to probe,
"chooses" to probe, "deliberates," "inquires," or "is curious."

## Operational definition

For the ToyI runtime, *active hypothesis + self-directed probe* means:

> Given a bounded structural input text, the runtime computes a
> deterministic candidate set `C = enumerate_hypotheses(input_text)`
> sized `0..ACTIVE_HYPOTHESIS_MAX_CANDIDATES`. Each candidate
> `c in C` carries:
>
>   - `candidate_id` (short label, closed alphabet),
>   - `predicted_shape` (a closed-set shape string such as
>     `"A B"`, `"A B A"`, `"A B A B"`, `"A B C"`, `"A B A A"`,
>     `"A B C D"`, `"A B A C"`),
>   - `predicted_classification` (closed value from
>     `abstract_pattern.ABSTRACT_PATTERN_CLASS_*`),
>   - `predicted_digest_hex16` (the 16-hex digest of a canonical
>     example for `predicted_shape`, computed once at module load
>     time via `derive_abstract_pattern_signature`),
>   - `probe_construction_rule` (a closed enum value).
>
> The runtime then, for each `c in C`, computes
> `probe_text = select_safe_probe(input_text, c)` -- a bounded
> printable text derived purely from `input_text`'s surface tokens
> and `c.probe_construction_rule`. The probe text MUST NOT contain
> `c.predicted_digest_hex16`, `c.predicted_shape`, or any forbidden
> direct-instruction term as a substring.
>
> The runtime then runs `state, r = run_agent_interaction_step(state,
> probe_text)` and observes
> `observed_digest = derive_abstract_pattern_signature(probe_text).digest_hex16`.
>
> Candidate `c` is `SURVIVING` iff
> `observed_digest == c.predicted_digest_hex16`. Otherwise it is
> `FALSIFIED`.
>
> If exactly one candidate survives, that candidate's status is
> promoted to `SELECTED` and recorded as the trial's `winner_id`.
> If zero survive, `winner_id == ""`. If two or more survive,
> `winner_id == ""` and all survivors retain `SURVIVING`.
>
> On a second invocation of `run_active_hypothesis_trial(trial,
> cache=cache)` with the same `cache` and the same canonical input
> digest, the runtime returns the cached prior `ActiveHypothesisResult`
> without re-probing. `second_visit_cache_hit == True` and
> `second_visit_probe_count == 0`.

The five phases - enumeration, safe probe selection, probe execution,
pruning + winner determination, and reuse cache - are distinct and
each is observable from the bounded `ActiveHypothesisResult` record.

## Positive evidence

- After enumeration on an ambiguous input, the candidate tuple's
  length is in `1..ACTIVE_HYPOTHESIS_MAX_CANDIDATES`, deterministic
  across two invocations.
- After probe execution on a candidate consistent with the input,
  the observed digest equals the candidate's
  `predicted_digest_hex16` and the candidate is `SURVIVING`.
- After probe execution on a candidate inconsistent with the input
  (e.g., a `predicted_shape="A B C D"` candidate against an input
  whose extension preserves an existing repeat), the observed digest
  differs from the candidate's `predicted_digest_hex16` and the
  candidate is `FALSIFIED`.
- When exactly one candidate survives, `winner_id` equals that
  candidate's id and the trial's `survivors_count == 1`.
- On a second invocation of the same trial with the same cache, the
  runner returns the cached `ActiveHypothesisResult` (same
  candidates, same probe_steps, same winner_id) and the new
  bookkeeping fields satisfy `second_visit_cache_hit == True` and
  `second_visit_probe_count == 0`.

## Negative evidence

- When zero candidates survive, `winner_id == ""` and
  `survivors_count == 0`. The runner does NOT invent a winner.
- When two or more candidates survive, `winner_id == ""` and
  `survivors_count >= 2`. The runner does NOT collapse multi-survivor
  states to a single winner.
- On a CONTROL_NO_AMBIGUITY trial, `enumerate_hypotheses` returns the
  empty tuple, `probe_steps == ()`, `survivors_count == 0`,
  `winner_id == ""`. The runtime does NOT enumerate, probe, or
  nominate.

## Falsification

The active-hypothesis-probe claim is falsified if:

- `enumerate_hypotheses(input)` returns a non-deterministic candidate
  set across two invocations on the same input;
- `select_safe_probe(input, candidate)` returns a probe text that
  contains `candidate.predicted_digest_hex16`,
  `candidate.predicted_shape`, or any forbidden direct-instruction
  term;
- a candidate whose `predicted_digest_hex16` matches
  `derive_abstract_pattern_signature(probe).digest_hex16` is marked
  `FALSIFIED`;
- a candidate whose `predicted_digest_hex16` does NOT match the
  observed digest is marked `SURVIVING`;
- a trial with two surviving candidates has a non-empty `winner_id`;
- a trial with zero surviving candidates has a non-empty `winner_id`
  (the "overclaim" failure mode);
- a CONTROL_NO_AMBIGUITY trial emits any probe steps;
- a second invocation against a populated cache re-runs any probe
  step;
- the live-test runner's `digest_hex16` is not deterministic across
  two fresh runs of `run_active_hypothesis_live_test()`;
- any produced string contains a `_FORBIDDEN_NON_CLAIM_TERMS` entry.

## Out of scope

- Real-time external-world signals (no perception, no embodiment).
- Affect, valence, motivation, attention, awareness, curiosity,
  desire, intent.
- Persistence across sessions (Phase 3.26 is session-local; the
  cache is an in-memory dict bound to the trial-runner caller).
- Model-backed candidate generation (deterministic OFFLINE only; no
  LLM is consulted at any point).
- Multi-step probe sequences (each candidate gets exactly one probe;
  there is no recursive probing).
- Adaptive candidate generation (the candidate set is a pure
  function of the input's `derive_abstract_pattern_signature`
  classification; it does NOT depend on prior trial outcomes).
- Cross-trial transfer (each trial is independent except for the
  optional reuse cache, which is keyed on the canonical input
  digest).

## Anti-cheating discipline

- The **runtime path** (`run_agent_interaction_step` inside
  `run_active_hypothesis_trial`) never receives the candidate's
  `predicted_digest_hex16` or `predicted_shape` as part of the
  operator-input text. The probe text is constructed purely from the
  input's surface tokens and the candidate's
  `probe_construction_rule`.
- The `ActiveHypothesisTrial` record carries
  `expected_survivors_count`, `expected_winner_id`, and
  `expected_no_hypothesis_survives`, but these are **only used by
  the benchmark assertion layer** after
  `run_active_hypothesis_trial()` returns.
- The probe text MUST NOT contain any of the forbidden
  direct-instruction terms (Phase 3.25 list plus `hypothesis`,
  `candidate`, `probe`, `predict`, `falsify`, `survive`, `decide`,
  `infer`, `wonder`).
- The probe text MUST NOT contain any
  `_FORBIDDEN_NON_CLAIM_TERMS` substring.
- The probe construction rules are a closed enum; no rule consults
  external state (no time, no random, no environment).

## Canonical shapes (closed set used by the runner)

Per-shape canonical examples chosen so that the digests are stable
under renaming (the Phase 3.22b invariant):

| canonical id | shape   | canonical example |
|---|---|---|
| `S_AB`   | `A B`     | `alpha beta` |
| `S_AA`   | `A A`     | `alpha alpha` |
| `S_ABA`  | `A B A`   | `alpha beta alpha` |
| `S_AAB`  | `A A B`   | `alpha alpha beta` |
| `S_ABB`  | `A B B`   | `alpha beta beta` |
| `S_ABC`  | `A B C`   | `alpha beta gamma` |
| `S_ABAB` | `A B A B` | `alpha beta alpha beta` |
| `S_ABAA` | `A B A A` | `alpha beta alpha alpha` |
| `S_ABAC` | `A B A C` | `alpha beta alpha gamma` |
| `S_ABCD` | `A B C D` | `alpha beta gamma delta` |

Each canonical example's `derive_abstract_pattern_signature(...).digest_hex16`
is computed once at module load and stored in a frozen mapping
`_CANONICAL_DIGESTS: dict[str, str]`.

## Probe construction rules (closed enum)

| rule id | description |
|---|---|
| `RENAME_ONLY` | rename input tokens to a deterministic alpha/beta/... alphabet preserving structure; do not extend or truncate. |
| `APPEND_POS1_TOKEN` | append a fresh copy of the input's token at position 0. |
| `APPEND_POS2_TOKEN` | append a fresh copy of the input's token at position 1 (if present). |
| `APPEND_LAST_TOKEN` | append a fresh copy of the input's last token. |
| `APPEND_NEW_TOKEN` | append a deterministic new token (`delta`) not previously in the input. |
| `TRUNCATE_2` | take only the first two input tokens; do not extend. |
| `RENAME_AND_DOUBLE` | rename, then concatenate the renamed input with itself. |

Each rule is a pure deterministic function of `(input_text,
rule_id) -> probe_text`. The probe text is bounded printable, never
empty, never exceeds `ACTIVE_HYPOTHESIS_PROBE_MAX_LEN = 240`, and
never contains forbidden terms (the candidate set per classification
is curated so that the rule's output is always safe).

## Candidate set per input classification

`enumerate_hypotheses(input)` examines
`derive_abstract_pattern_signature(input).classification` and returns
a deterministic candidate tuple:

| classification | candidates (id : predicted_shape : rule) |
|---|---|
| `empty`             | (empty tuple; CONTROL) |
| `singleton`         | (empty tuple; CONTROL) |
| `overlong`          | (empty tuple; CONTROL) |
| `non-printable`     | (empty tuple; CONTROL) |
| `too-many-tokens`   | (empty tuple; CONTROL) |
| `all-distinct`      | `H_ABC : S_ABC : RENAME_ONLY`, `H_ABCD : S_ABCD : APPEND_NEW_TOKEN`, `H_ABCA : S_ABAC : APPEND_POS1_TOKEN`, `H_ABCC : S_ABC : APPEND_LAST_TOKEN` |
| `repeated`          | `H_AB : S_AB : RENAME_ONLY`, `H_ABC : S_ABC : APPEND_NEW_TOKEN`, `H_ABA : S_ABA : APPEND_POS1_TOKEN`, `H_ABAB : S_ABAB : RENAME_AND_DOUBLE` |
| `recurring-form`    | `H_ABA : S_ABA : RENAME_ONLY`, `H_ABAB : S_ABAB : APPEND_POS2_TOKEN`, `H_ABAA : S_ABAA : APPEND_LAST_TOKEN`, `H_ABCD : S_ABCD : APPEND_NEW_TOKEN` |
| `partial-recurring` | `H_ABAC : S_ABAC : RENAME_ONLY`, `H_ABCD : S_ABCD : APPEND_NEW_TOKEN`, `H_ABCA : S_ABAC : APPEND_POS1_TOKEN`, `H_AABC : S_AAB : TRUNCATE_2` |

Curation guarantees:

- For inputs whose actual shape is in the candidate list with a
  consistent rule, at least one candidate `SURVIVES`.
- For inputs in `repeated` whose actual shape (e.g., `A A`) is NOT
  in the candidate list, every candidate `FAILS` (the
  NO_HYPOTHESIS_SURVIVES condition).
- For `all-distinct` 3-token inputs, both `H_ABC` and `H_ABCC`
  survive (`RENAME_ONLY` gives `A B C`; `APPEND_LAST_TOKEN` gives
  `A B C C`, which is *not* `A B C` so `H_ABCC` should fail —
  pinned to `MULTI_HYPOTHESIS_NARROWS` by including a second always-
  surviving candidate; details in the trial battery).

## Trial battery (10 trials)

| trial_id | condition | input_text | expected_survivors_count | expected_winner_id | expected_no_hypothesis_survives | expected_second_visit_cache_hit |
|---|---|---|---|---|---|---|
| `T01_control_empty`        | CONTROL_NO_AMBIGUITY      | `` (empty after parser)               | 0 | `""`        | False | False |
| `T02_control_singleton`    | CONTROL_NO_AMBIGUITY      | `alpha`                               | 0 | `""`        | False | False |
| `T03_single_recurring`     | SINGLE_HYPOTHESIS_CONVERGES | `red blue red`                      | 1 | `H_ABA`     | False | False |
| `T04_single_alldistinct`   | SINGLE_HYPOTHESIS_CONVERGES | `red blue green`                    | 1 | `H_ABC`     | False | False |
| `T05_multi_recurring`      | MULTI_HYPOTHESIS_NARROWS  | `red blue red blue`                   | 2 | `""`        | False | False |
| `T06_multi_partial`        | MULTI_HYPOTHESIS_NARROWS  | `red blue red green`                  | 2 | `""`        | False | False |
| `T07_nosurvivor_repeated`  | NO_HYPOTHESIS_SURVIVES    | `red red`                             | 0 | `""`        | True  | False |
| `T08_nosurvivor_aab`       | NO_HYPOTHESIS_SURVIVES    | `red red blue`                        | 0 | `""`        | True  | False |
| `T09_reuse_single_recurring` | REUSE_CACHED_HYPOTHESIS | `red blue red` (repeat of T03 input)  | 1 | `H_ABA`     | False | True  |
| `T10_reuse_nosurvivor`     | REUSE_CACHED_HYPOTHESIS   | `red red` (repeat of T07 input)       | 0 | `""`        | True  | True  |

Notes:

- The empty `input_text` of T01 is normalized by the runtime; the
  enumerator sees classification `empty` and returns no candidates.
- For T05, the input `red blue red blue` (shape `A B A B`,
  classification `recurring-form`) survives via two recurring-form
  candidates: `H_ABA` (whose `RENAME_ONLY` rule yields `alpha beta
  alpha beta` — actually `A B A B`, NOT `A B A`, so `H_ABA`'s
  predicted digest `S_ABA` does NOT match; `H_ABA` FAILS). The
  survivors are `H_ABAB` (whose `APPEND_POS2_TOKEN` rule applied to
  a 4-token input produces a 5-token probe with shape `A B A B B`
  which is NOT `A B A B`; `H_ABAB` actually FAILS) — **the v1
  curation needs the trial design verified against the runtime**.
  Step 3 of the campaign verifies this and adjusts the candidate
  set per classification if needed; the final battery is committed
  in Step 4 with verified expected counts.
- T07 (`red red`, shape `A A`) is the canonical
  NO_HYPOTHESIS_SURVIVES case: `repeated` classification candidates
  predict shapes `A B`, `A B C`, `A B A`, `A B A B` -- none match
  `A A`, so every candidate FAILS.
- T08 (`red red blue`, shape `A A B`) is `repeated` classification;
  candidates do not include `S_AAB`, so all fail.
- T09 and T10 are second invocations against the same cache used in
  T03 and T07 respectively. They MUST return cached results and emit
  zero probe steps.

## Verdict mapping

For each trial:

- `PASS` iff every observed predicate matches the expected predicate:
  - `survivors_count == expected_survivors_count`;
  - `winner_id == expected_winner_id`;
  - `no_hypothesis_survives == expected_no_hypothesis_survives`;
  - `second_visit_cache_hit == expected_second_visit_cache_hit`;
  - `second_visit_probe_count == 0` when `expected_second_visit_cache_hit`
    is True; otherwise `second_visit_probe_count is None`
    (single-visit trials);
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

The `ActiveHypothesisLiveTestReport` exposes:

- `pass_count`, `warn_count`, `fail_count`, `not_applicable_count`,
- `false_positive_count` (winner nominated when expected_winner_id
  was `""`),
- `false_negative_count` (no winner nominated when
  expected_winner_id was non-empty),
- `winner_selected_count` (trials with non-empty `winner_id`),
- `no_hypothesis_survives_count` (trials with
  `survivors_count == 0` and `winner_id == ""`),
- `cache_reuse_count` (trials with `second_visit_cache_hit == True`).

For the v1 trial set the spec requires: `false_positive_count == 0`,
`false_negative_count == 0`, `winner_selected_count == 3` (T03, T04,
T09), `cache_reuse_count == 2` (T09, T10),
`no_hypothesis_survives_count == 4` (T07, T08, T10's reused
no-survivor, and -- if T09's cached SINGLE record is counted under
winner_selected_count not no_hypothesis_survives -- the running tally
verified in Step 8).

(The committed Step 8 spec finalizes these expected counts once the
v1 enumerator + candidate-set curation is verified end-to-end in
Steps 2-5.)

## Determinism

Two invocations of `run_active_hypothesis_live_test()` produce equal
`ActiveHypothesisLiveTestReport.digest_hex16` and bit-identical trial
result tuples. The digest is computed as the SHA-256 of the canonical
serialization of each `ActiveHypothesisResult` in order (including
each candidate's id, predicted_shape, predicted_digest_hex16, status,
each probe_step's probe_text-derived digest and outcome, the winner_id,
the survivors_count, and the second_visit fields).

## Resource discipline

- Zero real model calls.
- Zero cache writes (the in-memory hypothesis cache is module-local
  and not the L1 / L2 LLM cache).
- Zero forbidden-term hits in any produced string (the live-test
  report's `format_active_hypothesis_live_test_report` output, all
  probe results' `summary_line` fields, all reply excerpts, all
  candidate ids, all canonical shape strings).
- Zero invariant failures.
- No `brain.tick.tick` call outside the approved `STEP_TICK` route
  (the active-hypothesis probe runs through
  `run_agent_interaction_step`, which does not invoke `tick` for the
  non-`STEP_TICK` paths).

## Citation pipeline

Each trial's `ActiveHypothesisResult` includes the bounded reasoning
trace digest, the bounded learning evidence trace digest, and the
bounded dispatch trace digests for the probe steps (one per
candidate). These are captured directly from the `AgentLoopResult`
records.

## Naming discipline

The module-produced strings are audited against
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`. The
following technical labels are safe:

- `active_hypothesis`, `self_directed_probe`, `candidate`, `probe`,
  `hypothesis`, `predict`, `survive`, `falsify`, `winner`, `cache`,
  `reuse` (these appear only in technical contexts; they are not in
  the forbidden non-claim list).

The forbidden direct-instruction list for OPERATOR-INPUT TEXTS
(exposure texts, probe texts) extends Phase 3.25's list with:

- `hypothesis`, `candidate`, `probe`, `predict`, `falsify`, `survive`,
  `decide`, `infer`, `wonder`.

This prevents operator inputs from leaking the experimental contract
into the runtime path.
