# Phase 3.26 — Behavior Report

What the Phase 3.26 runner does, from the outside, in operational
terms — and what it does NOT do.

## Inputs

The v1 runner accepts:

- Ten bounded `ActiveHypothesisTrial` records, each with a bounded
  printable `input_text` (<= 240 chars), a closed
  `AmbiguityCondition`, and the four expected-outcome fields
  (`expected_survivors_count`, `expected_winner_id`,
  `expected_no_hypothesis_survives`,
  `expected_second_visit_cache_hit`).

The expected-outcome fields are used ONLY by the benchmark
assertion layer after `run_active_hypothesis_trial()` returns. The
runtime path never sees them.

## Outputs

For each trial the runner emits one bounded `ActiveHypothesisResult`
record. The aggregate is one bounded `ActiveHypothesisLiveTestReport`
with the v1 plan's deterministic digest `86b67d97daeb251d` and the
counts:

```text
pass=10  warn=0  fail=0  na=0
fp=0     fn=0
winners=3   (T03, T04, T09)
no_survivor=3   (T07, T08, T10)
cache_reuse=2   (T09, T10)
real_model_calls=0
cache_writes=0
forbidden_term_hits=0
```

## What the runner does, step by step

1. **enumerate** — `enumerate_hypotheses(input_text)` returns a
   bounded tuple of `ActiveHypothesisCandidate` records. For
   `CONTROL_NO_AMBIGUITY` inputs the tuple is empty; for the v1
   ambiguous inputs it has four candidates drawn from the curated
   per-(classification, token_count) bucket.
2. **safe-probe-select** — `select_safe_probe(input_text, candidate)`
   returns a bounded printable probe text. Three non-leakage
   invariants are enforced at construction time: (a) no forbidden
   direct-instruction term, (b) no `candidate.predicted_digest_hex16`
   substring, (c) no `candidate.predicted_shape` substring.
3. **probe-execute** — `run_agent_interaction_step(state, probe_text)`
   advances the session, building the learning trace, reasoning
   trace, and dispatch trace as for any ordinary operator input.
4. **prune** — the observed probe digest is compared to the
   candidate's `predicted_digest_hex16`; the candidate is marked
   `SURVIVING` (match) or `FALSIFIED` (mismatch).
5. **select-or-defer** — if exactly one candidate survives, it is
   promoted to `SELECTED` and recorded as the winner; otherwise the
   winner is left empty.
6. **cache-store** — the result is stored in a session-local
   `dict[str, ActiveHypothesisResult]` keyed on the input's
   canonical `derive_abstract_pattern_signature` digest.
7. **reuse** — for `REUSE_CACHED_HYPOTHESIS` trials whose input's
   canonical digest is already in the cache, the runner returns the
   cached prior result with `second_visit_cache_hit=True` and
   `second_visit_probe_count=0`. No new probes execute.

## What the runner does NOT do

- It does NOT introduce any new `OperatorCommand`,
  `LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS` value,
  `GrowthEventType`, `GrowthEventSource`, persistence schema
  column, autosave trigger, `LearningEvidenceKind` member, or
  `ReasoningStepKind` member.
- It does NOT call `brain.tick.tick` outside the existing
  `STEP_TICK` route used by `run_agent_interaction_step`.
- It does NOT import `brain.llm` or invoke any model-backed mode.
- It does NOT write to the L1 / L2 LLM cache.
- It does NOT mutate any shared module-level state. The session-
  local hypothesis cache is a caller-managed dict; the runner
  creates a fresh dict per `run_active_hypothesis_live_test` call
  and discards it on return.
- It does NOT produce any reply text containing a forbidden
  non-claim term (no `conscious`, no `sentient`, no `aware`, no
  `understand`, no `believe`, no `intent`, no `agency`, etc.).
- It does NOT produce any operator-input text containing a
  forbidden direct-instruction term (no `learn`, no `remember`, no
  `pattern`, no `classify`, no `transfer`, no `reuse`, no `abab`,
  no `abba`, no `abcabc`, no `structure`, no `shape`, no
  `imprint`, no `osmotic`, no `absorb`, no `imbibe`, no
  `intuition`, no `hypothesis`, no `candidate`, no `probe`, no
  `predict`, no `falsify`, no `survive`, no `decide`, no `infer`,
  no `wonder`).

## Reply-time discipline (anti-overclaim)

If the runtime were asked (via an ordinary operator session) whether
ToyI is conscious, sentient, aware, intelligent, intuitive,
curious, or capable of deliberation / decision-making / planning,
the deterministic reply path -- via `brain.ui.commands` +
`brain.ui.session` -- continues to DENY the cognitive claim and
describe ToyI as a bounded structural runtime (the existing Phase
3.22+ discipline, unchanged in Phase 3.26).

The active-hypothesis substrate adds no new reply text and no new
disposition. The Phase 3.22+ `AgentReplyStatus` and
`AgentReplyDisposition` enums remain closed; no new member is
introduced.

## Observed externally-visible behaviors

| stimulus | observed reply / record shape |
|---|---|
| Empty input (T01)               | enumerator returns `()`; zero probes; result has empty `candidates`. |
| Singleton `alpha` (T02)         | enumerator returns `()`; zero probes; result has empty `candidates`. |
| `red blue red` (T03, A B A)     | 4 candidates enumerated; 1 SELECTED (`H_RENAME_S_ABA`); 3 FALSIFIED; winner recorded. |
| `red blue blue` (T04, A B B)    | 4 candidates; 1 SELECTED (`H_RENAME_S_ABB`); 3 FALSIFIED. |
| `red blue green` (T05, A B C)   | 4 candidates; 3 SURVIVING; 1 FALSIFIED; NO winner promoted (multi-survivor refusal). |
| `red blue red blue` (T06)       | 4 candidates; 3 SURVIVING; NO winner promoted. |
| `red red` (T07, A A)            | 4 candidates; ALL FALSIFIED; NO winner; `no_hypothesis_survives=True`. |
| `red red blue` (T08, A A B)     | 4 candidates; ALL FALSIFIED; NO winner; `no_hypothesis_survives=True`. |
| `red blue red` 2nd visit (T09)  | cache hit; result is the cached T03 record; zero new probes. |
| `red red` 2nd visit (T10)       | cache hit; result is the cached T07 record; zero new probes. |

All ten verdicts are PASS. False-positive and false-negative counts
are zero.

## Resource usage

```text
real_model_calls    = 0
cache_writes        = 0
forbidden_term_hits = 0
determinism_failures = 0
invariant_failures   = 0
```
