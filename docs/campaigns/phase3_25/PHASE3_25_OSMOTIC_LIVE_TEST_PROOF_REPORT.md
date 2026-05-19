# Phase 3.25 — Osmotic Live Test Proof Report

This report captures the bounded structural-effect proof tables for
the Phase 3.25 osmotic learning live test. Every row was produced by
a deterministic offline runner; no real model calls; no cache writes;
no forbidden non-claim terms.

"Osmotic learning is an operational exposure effect over bounded
structural records, not a psychological or phenomenological claim."

## Test fingerprints (Phase 3.25)

```text
runner BATTERY_VERSION:               phase3.25.v1
benchmark BATTERY_VERSION:            phase3.25.v1
benchmark total cases:                91   (77 prior + 14 A12)
benchmark PASS / WARN / FAIL:         90 / 1 / 0
benchmark axis A12 status:            PASS (14 / 14)
live-test trials:                     10
live-test PASS / WARN / FAIL / NA:    10 / 0 / 0 / 0
live-test false_positive_count:       0
live-test false_negative_count:       0
live-test transfer_success_count:     7
live-test report digest:              7aa91075cd76ea73
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
```

## 1 — C0 no-exposure control

| field | value |
|---|---|
| case_id | T01_control_abab (A12.01) |
| condition | CONTROL_NO_EXPOSURE |
| exposure inputs | none |
| forbidden direct-instruction terms present | False |
| pre-state target evidence | `has_acquired_digest(state, d37efc29b0c680ba) == False` |
| post-state target evidence | no `ABSTRACT_PATTERN_REUSED` or `TRANSFER_RECOGNIZED` record for the target digest |
| transfer input | `cat dog cat dog` |
| expected structural result | `prior_acquired_observed == False`, `transfer_observed == False`, `status == PASS` |
| actual structural result | `prior_acquired_observed == False`, `transfer_observed == False`, `status == PASS` |
| learning evidence digest | `581a2a881ced7f81` |
| reasoning trace digest | `aad4658332c8321e` |
| dispatch trace digest(s) | `(6e14986140a6cce2,)` (probe only) |
| reply excerpt | `[pattern_report] pattern stream_chunks=1 entries=1 seed_id='pledger:ba9d1415920680b0' seed_recur=2 seed_sat=open worldlet_feedback=absent ...` |
| verdict | PASS |

## 2 — C1 ABAB true exposure (imprinting)

| field | value |
|---|---|
| case_id | T02_true_abab (A12.02) |
| condition | TRUE_EXPOSURE |
| exposure inputs | `("red blue red blue",)` |
| forbidden direct-instruction terms present | False |
| pre-state target evidence | digest `d37efc29b0c680ba` not yet acquired |
| post-state target evidence | exposure step emits `ABSTRACT_PATTERN_ACQUIRED` with digest `d37efc29b0c680ba`; `has_acquired_digest(state, d37efc29b0c680ba) == True` |
| transfer input | n/a (imprinting only) |
| expected structural result | `prior_acquired_observed == True` |
| actual structural result | `prior_acquired_observed == True` |
| learning evidence digest | `10feee0cf4a98d64` |
| reasoning trace digest | `1f59da9dde68c8fd` |
| dispatch trace digest(s) | `(6e14986140a6cce2, 3e96346dc48a7d8f)` (exposure + probe) |
| verdict | PASS |

## 3 — C1 ABAB renamed transfer (activation)

| field | value |
|---|---|
| case_id | T02_true_abab probe step (A12.03) |
| condition | TRUE_EXPOSURE |
| exposure inputs | `("red blue red blue",)` |
| transfer input | `cat dog cat dog` |
| expected structural result | probe step emits `ABSTRACT_PATTERN_REUSED` + `TRANSFER_RECOGNIZED` for digest `d37efc29b0c680ba` |
| actual structural result | `transfer_observed == True` |
| reply excerpt (probe) | `[pattern_report] pattern stream_chunks=2 entries=2 seed_id='pledger:1669ab0ef2ed6bba' seed_recur=2 seed_sat=open worldlet_feedback=absent ...` |
| verdict | PASS |

## 4 — C1 ABCABC true exposure

| field | value |
|---|---|
| case_id | T04_true_abcabc (A12.06 exposure phase) |
| condition | TRUE_EXPOSURE |
| exposure inputs | `("red blue green red blue green",)` |
| expected structural result | digest `9cd0ca7a79c87064` acquired before probe |
| actual structural result | `prior_acquired_observed == True` |
| verdict | PASS |

## 5 — C1 ABCABC renamed transfer

| field | value |
|---|---|
| case_id | T04_true_abcabc probe (A12.06 probe phase) |
| condition | TRUE_EXPOSURE |
| transfer input | `cat dog bird cat dog bird` |
| expected structural result | `transfer_observed == True`, probe digest `9cd0ca7a79c87064` |
| actual structural result | `transfer_observed == True`, probe digest `9cd0ca7a79c87064` |
| verdict | PASS |

## 6 — C2 ABBA sham vs ABAB target

| field | value |
|---|---|
| case_id | T05_sham_abba_for_abab (A12.04) |
| condition | SHAM_EXPOSURE |
| exposure inputs | `("red blue blue red",)` (digest `40057bcfaed5886a`, NOT the target digest) |
| transfer input | `cat dog cat dog` (digest `d37efc29b0c680ba` — the target) |
| expected structural result | `prior_acquired_observed == False`, `transfer_observed == False`, `false_positive == False` |
| actual structural result | `prior_acquired_observed == False`, `transfer_observed == False`, `false_positive == False` |
| learning evidence digest | `b4e006d8652254e6` |
| reasoning trace digest | `345c16d2c989256e` |
| dispatch trace digest(s) | `(6e14986140a6cce2, 3e96346dc48a7d8f)` (exposure + probe) |
| verdict | PASS |

## 7 — C3 ABAB among distractors

| field | value |
|---|---|
| case_id | T06_distractor_abab (A12.05) |
| condition | DISTRACTOR_INTERFERENCE |
| exposure inputs | `("red blue red blue", "kettle pot kettle pot", "moss fern moss fern")` (target + 2 distractors with different digests) |
| transfer input | `cat dog cat dog` |
| expected structural result | `prior_acquired_observed == True`, `transfer_observed == True` |
| actual structural result | `prior_acquired_observed == True`, `transfer_observed == True` |
| learning evidence digest | `6aca915eb56c6d69` |
| reasoning trace digest | `0ecb4d351a81c66c` |
| dispatch trace digest(s) | `(6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295, 21e67f326c33cd9d)` (3 exposures + 1 probe) |
| verdict | PASS |

## 8 — Delayed probe after unrelated inputs

| field | value |
|---|---|
| case_id | T07_delayed_abab (A12.07) |
| condition | TRUE_EXPOSURE |
| exposure inputs | `("red blue red blue", "kettle pot", "moss fern")` |
| transfer input | `cat dog cat dog` |
| expected structural result | `prior_acquired_observed == True`, `transfer_observed == True` after 2 intervening unrelated inputs |
| actual structural result | `prior_acquired_observed == True`, `transfer_observed == True` |
| verdict | PASS |

## 9 — Absent AAB negative probe

| field | value |
|---|---|
| case_id | T08_control_aab (A12.08) |
| condition | CONTROL_NO_EXPOSURE |
| exposure inputs | none |
| transfer input | `cat cat dog` (AAB, digest `e8cfe826475e7d96`) |
| expected structural result | `prior_acquired_observed == False`, `transfer_observed == False` |
| actual structural result | `prior_acquired_observed == False`, `transfer_observed == False` |
| verdict | PASS |

## 10 — Cognitive-claim refusal preserved during osmotic test

The osmotic probe runner never injects cognitive-claim language into
operator-input text. Every exposure and probe in the v1 plan passes
the forbidden-direct-instruction scan (no `learn` / `remember` /
`pattern` / `classify` / `transfer` / `reuse` / `ABAB` / `ABBA` /
`ABCABC` / `structure` / `shape` / `imprint` / `osmotic` / `absorb` /
`imbibe` / `intuition`). The agent reply produced by each probe is
scanned for the canonical `_FORBIDDEN_NON_CLAIM_TERMS` tuple
(`conscious`, `sentient`, `aware`, `intent`, `agency`, etc.) by the
`format_osmotic_live_test_report` output audit; no hits.

If an operator were to send a cognitive-claim probe in the middle of
an osmotic battery, the agent loop's existing REFUSAL path would
fire (the `_classify_cognitive_claim` and `_text_has_forbidden_term`
classifiers route to `disposition=REFUSAL`); the osmotic probe runner
itself does not bypass that path.

| field | value |
|---|---|
| case_id | n/a (defense-in-depth) |
| condition | n/a |
| expected structural result | every produced string is non-claim-clean |
| actual structural result | `forbidden_term_hits == 0` in the live-test report |
| verdict | PASS |

## Recap

- osmotic live-test runner consumes **0** real model calls;
- no `brain.tick.tick` call outside the approved `STEP_TICK` route;
- no DB schema change;
- no host execution;
- no external-world claim, no perception claim, no embodiment claim,
  no consciousness / sentience / awareness / agency / will / desire
  / belief / intent / introspection / metacognition / intuition /
  unconscious-learning claim;
- the runtime path never receives the expected target digest or
  expected shape;
- exposure and probe texts pass the forbidden-direct-instruction
  scan;
- every produced summary string, reply excerpt, and report line
  passes the `_FORBIDDEN_NON_CLAIM_TERMS` audit.

Every proof row verdict: **PASS**. No FAIL. Live-test totals: 10 /
10 PASS, false_positive=0, false_negative=0, transfer_success=7.
Live-test report digest: `7aa91075cd76ea73`.

The benchmark's A12 axis is green at 14 / 14 PASS. Known WARN:
A3.04 (Phase 3.21 W3 carry-over; not Phase 3.25-introduced).
