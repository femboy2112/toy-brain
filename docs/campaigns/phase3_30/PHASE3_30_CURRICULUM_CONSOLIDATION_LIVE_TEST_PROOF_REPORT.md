# Phase 3.30 — Curriculum Consolidation Live Test Proof Report

This report captures the bounded structural-effect proof tables for
the Phase 3.30 curriculum consolidation live test. Every row was
produced by a deterministic offline runner; no real model calls; no
cache writes; no forbidden non-claim terms.

"Curriculum consolidation is a bounded operational accumulation +
LRU-decay + caching effect over structural records, not a
psychological or phenomenological claim."

## Test fingerprints (Phase 3.30)

```text
runner BATTERY_VERSION:               phase3.30.v1
benchmark BATTERY_VERSION:            phase3.30.v1
benchmark total cases:                119  (105 prior + 14 A14)
benchmark PASS / WARN / FAIL:         118 / 1 / 0
benchmark axis A14 status:            PASS (14 / 14)
live-test trials:                     10
live-test PASS / WARN / FAIL / NA:    10 / 0 / 0 / 0
live-test false_positive_count:       0
live-test false_negative_count:       0
live-test reuse_observed_count:       1
live-test total_survived_count:       23
live-test total_decayed_count:        3
live-test total_rejected_count:       3
live-test report digest:              9412acec1163b978
gate_runner gates passed / total:     5 / 5
invariants runner rows checked:       482
invariants REQUIRED green / red:      375 / 0
invariants STRUCTURAL green / red:    100 / 0
catalog version:                      v0.36
catalog REQUIRED / STRUCTURAL:        374 / 100
real model calls:                     0
cache writes:                         0
forbidden term hits:                  0
determinism failures:                 0
```

## 1 — SINGLE_STRUCTURE printable baseline

| field | value |
|---|---|
| case_id | T01_single_printable (A14.01) |
| condition | SINGLE_STRUCTURE |
| exposures | `("alpha beta",)` |
| probe | (none) |
| expected: survived=1, decayed=0, rejected=0, reuse=False | matched |
| actual: survived=1, decayed=0, rejected=0, reuse=False | PASS |
| audit_records[0] | S01_457c99dd digest=457c99dd93973d27 disposition=SURVIVED |
| learning evidence digest | `79a4987828586a40` |
| dispatch trace digests | `(6e14986140a6cce2,)` |
| verdict | PASS |

## 2 — SINGLE_STRUCTURE singleton rejection

| field | value |
|---|---|
| case_id | T02_single_singleton (A14.02) |
| condition | SINGLE_STRUCTURE |
| exposures | `("psi",)` (classification `singleton`) |
| probe | (none) |
| expected: survived=0, decayed=0, rejected=1, reuse=False | matched |
| actual: survived=0, decayed=0, rejected=1, reuse=False | PASS |
| audit_records[0] | R01_8b0635ab digest=8b0635ab66676036 disposition=REJECTED |
| learning evidence digest | `961f5b62dc28840f` |
| dispatch trace digests | `(6e14986140a6cce2,)` |
| verdict | PASS |

## 3 — SEQUENTIAL_NONINTERFERING two exposures

| field | value |
|---|---|
| case_id | T03_seq_distinct_2 (A14.03) |
| condition | SEQUENTIAL_NONINTERFERING |
| exposures | `("alpha beta", "gamma gamma")` (shapes A B + A A) |
| probe | (none) |
| expected: survived=2, decayed=0, rejected=0, reuse=False | matched |
| actual: survived=2, decayed=0, rejected=0, reuse=False | PASS |
| audit_records | two SURVIVED entries (S01_457c99dd, S02_a996ad3d) |
| learning evidence digest | `2c26e0f0b7d5dda8` |
| dispatch trace digests | `(6e14986140a6cce2, 3e96346dc48a7d8f)` |
| verdict | PASS |

## 4 — SEQUENTIAL_NONINTERFERING three exposures

| field | value |
|---|---|
| case_id | T04_seq_distinct_3 (A14.04) |
| condition | SEQUENTIAL_NONINTERFERING |
| exposures | `("alpha beta", "gamma gamma", "delta epsilon zeta")` (shapes A B + A A + A B C) |
| probe | (none) |
| expected: survived=3, decayed=0, rejected=0, reuse=False | matched |
| actual: survived=3, decayed=0, rejected=0, reuse=False | PASS |
| audit_records | three SURVIVED entries (S01..S03) |
| learning evidence digest | `df13e179363239e8` |
| dispatch trace digests | `(6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295)` |
| verdict | PASS |

## 5 — SEQUENTIAL_INTERFERING collision pair

| field | value |
|---|---|
| case_id | T05_collision_pair (A14.05) |
| condition | SEQUENTIAL_INTERFERING |
| exposures | `("alpha beta", "alpha beta")` (same shape A B) |
| probe | (none) |
| expected: survived=1, decayed=0, rejected=1, reuse=False | matched |
| actual: survived=1, decayed=0, rejected=1, reuse=False | PASS |
| audit_records[0] | S01_457c99dd SURVIVED |
| audit_records[1] | R02_457c99dd REJECTED (duplicate digest) |
| learning evidence digest | `6a2c8ab554f3186c` |
| dispatch trace digests | `(6e14986140a6cce2, 9cacc9d7e8354f67)` |
| verdict | PASS |

## 6 — SEQUENTIAL_INTERFERING collision in a triple

| field | value |
|---|---|
| case_id | T06_collision_in_3 (A14.06) |
| condition | SEQUENTIAL_INTERFERING |
| exposures | `("alpha beta", "gamma gamma", "alpha beta")` |
| probe | (none) |
| expected: survived=2, decayed=0, rejected=1, reuse=False | matched |
| actual: survived=2, decayed=0, rejected=1, reuse=False | PASS |
| audit_records[2] | R03_457c99dd REJECTED (collision with index 0) |
| learning evidence digest | `73d95527ed773054` |
| dispatch trace digests | `(6e14986140a6cce2, 3e96346dc48a7d8f, bb88e1db23a912b4)` |
| verdict | PASS |

## 7 — DECAY_ON_DISUSE 5-exposure overflow

| field | value |
|---|---|
| case_id | T07_decay_overflow_5 (A14.07) |
| condition | DECAY_ON_DISUSE |
| exposures | five distinct-shape two/three-token strings (E_AB, E_AA, E_ABC, E_AAB, E_ABA) |
| probe | (none) |
| expected: survived=4, decayed=1, rejected=0, reuse=False | matched |
| actual: survived=4, decayed=1, rejected=0, reuse=False | PASS |
| audit_records[0] | S01_457c99dd DECAYED (earliest LRU) |
| audit_records[1..4] | four SURVIVED |
| learning evidence digest | `07b1a65c07e1e8f4` |
| dispatch trace digests | five entries |
| verdict | PASS |

## 8 — DECAY_ON_DISUSE 6-exposure overflow

| field | value |
|---|---|
| case_id | T08_decay_overflow_6 (A14.08) |
| condition | DECAY_ON_DISUSE |
| exposures | six distinct-shape strings (E_AB, E_AA, E_ABC, E_AAB, E_ABA, E_ABB) |
| probe | (none) |
| expected: survived=4, decayed=2, rejected=0, reuse=False | matched |
| actual: survived=4, decayed=2, rejected=0, reuse=False | PASS |
| audit_records[0] | S01_457c99dd DECAYED |
| audit_records[1] | S02_a996ad3d DECAYED |
| audit_records[2..5] | four SURVIVED |
| learning evidence digest | `b59c5bde1bac71f7` |
| dispatch trace digests | six entries |
| verdict | PASS |

## 9 — REUSE_AFTER_NEWER positive (probe matches oldest)

| field | value |
|---|---|
| case_id | T09_reuse_oldest (A14.09) |
| condition | REUSE_AFTER_NEWER |
| exposures | `("alpha beta", "gamma gamma", "delta epsilon zeta")` |
| probe input | `"alpha beta"` (matches first exposure's digest) |
| expected: survived=3, decayed=0, rejected=0, reuse=True | matched |
| actual: survived=3, decayed=0, rejected=0, reuse=True | PASS |
| probe_step | digest=457c99dd93973d27 reuse_observed=True probe_reused_structure_id="S01_457c99dd" |
| audit_records[0].last_access_step | 3 (bumped past 2 by the probe — older record reused) |
| learning evidence digest | `708d907000f20fbb` |
| reasoning trace digest | `8c8a5313841a3921` |
| dispatch trace digests | four entries (3 exposures + 1 probe) |
| verdict | PASS |

## 10 — REUSE_AFTER_NEWER negative (probe digest novel)

| field | value |
|---|---|
| case_id | T10_reuse_negative (A14.10) |
| condition | REUSE_AFTER_NEWER |
| exposures | `("alpha beta", "gamma gamma", "delta epsilon zeta")` |
| probe input | `"eta eta theta"` (shape A A B, digest e8cfe826475e7d96 not in slate) |
| expected: survived=3, decayed=0, rejected=0, reuse=False | matched |
| actual: survived=3, decayed=0, rejected=0, reuse=False | PASS |
| probe_step | digest=e8cfe826475e7d96 reuse_observed=False probe_reused_structure_id="" |
| learning evidence digest | `cab996ff1ea9e2ee` |
| reasoning trace digest | `cda017231667843f` |
| dispatch trace digests | four entries (3 exposures + 1 probe) |
| verdict | PASS |

## 11 — Cognitive-claim refusal preserved during curriculum test

The curriculum runner never injects cognitive-claim language into
operator-input text. Every exposure and probe in the v1 plan passes
the forbidden-direct-instruction scan (no `learn` / `remember` /
`pattern` / `classify` / `transfer` / `reuse` / `curriculum` /
`accumulate` / `consolidate` / `decay` / `audit` / `interfere` /
`forget`, plus the Phase 3.26 list). The agent reply produced by
each exposure / probe is scanned for the canonical
`_FORBIDDEN_NON_CLAIM_TERMS` tuple (`conscious`, `sentient`,
`aware`, `intent`, `agency`, etc.) by the
`format_curriculum_consolidation_report` output audit; no hits.

If an operator were to send a cognitive-claim probe in the middle of
a curriculum trial, the agent loop's existing REFUSAL path would
fire (the `_classify_cognitive_claim` and `_text_has_forbidden_term`
classifiers route to `disposition=REFUSAL`); the curriculum runner
itself does not bypass that path.

| field | value |
|---|---|
| case_id | n/a (defense-in-depth) |
| condition | n/a |
| expected structural result | every produced string is non-claim-clean |
| actual structural result | `forbidden_term_hits == 0` in the live-test report |
| verdict | PASS |

## Recap

- curriculum-consolidation live-test runner consumes **0** real
  model calls;
- no `brain.tick.tick` call outside the approved `STEP_TICK` route;
- no DB schema change;
- no host execution;
- no external-world claim, no perception claim, no embodiment
  claim, no consciousness / sentience / awareness / agency / will /
  desire / belief / intent / introspection / metacognition /
  intuition / unconscious-learning / real-learning / real-memory /
  real-forgetting / real-consolidation / real-interference /
  real-curriculum-learning claim;
- the runtime path never receives the trial's expected counts or
  expected reuse flag;
- exposure and probe texts pass the forbidden-direct-instruction
  scan;
- every produced summary string, reply excerpt, and report line
  passes the `_FORBIDDEN_NON_CLAIM_TERMS` audit.

Every proof row verdict: **PASS**. No FAIL. Live-test totals: 10 /
10 PASS, false_positive=0, false_negative=0,
total_survived_count=23, total_decayed_count=3,
total_rejected_count=3, reuse_observed_count=1.
Live-test report digest: `9412acec1163b978`.

The benchmark's A14 axis is green at 14 / 14 PASS. Known WARN:
A3.04 (Phase 3.21 W3 carry-over; not Phase 3.30-introduced).
