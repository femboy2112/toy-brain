# Phase 3.25 — Behavior Report

This document records the *operational behavior* properties that
Phase 3.25 demonstrates. Behavior here means "observable
structural-effect properties of the deterministic runner", not
psychological or phenomenal behavior.

## What the runner shows

1. The substrate exhibits the operational analogue of **imprinting**:
   under TRUE_EXPOSURE, a single ambient unlabeled input that
   matches a target structural digest causes an
   `ABSTRACT_PATTERN_ACQUIRED` record to land in the session-local
   learning evidence trace. `has_acquired_digest(state, target)`
   returns True after the exposure step, before any probe.

2. The substrate exhibits the operational analogue of **activation**:
   under TRUE_EXPOSURE followed by a renamed probe, the probe step
   appends both `ABSTRACT_PATTERN_REUSED` and `TRANSFER_RECOGNIZED`
   records for the matching digest. The probe text shares the
   abstract digest with the exposure text but uses disjoint tokens.

3. The substrate **rejects false positives**:
   - CONTROL_NO_EXPOSURE: no acquisition / no transfer is recorded
     for the target digest pre-probe.
   - SHAM_EXPOSURE: a different abstract digest is exposed; the
     target probe correctly reports `prior_acquired_observed=False`
     and `transfer_observed=False`.

4. The substrate is **robust to interference**: under
   DISTRACTOR_INTERFERENCE (target + 2 distractors with different
   digests), the target probe still recognizes the target digest
   and triggers transfer.

5. The substrate exhibits **session-local retention**: a delayed
   probe after 2 intervening unrelated inputs still triggers
   transfer.

## What the runner does NOT show

- No claim that ToyI has consciousness, sentience, awareness,
  intuition, insight, understanding, agency, will, desire, belief,
  intent, introspection, metacognition, or unconscious learning.
- No multi-session retention test (the runner is session-local
  only).
- No model-backed live smoke (deterministic OFFLINE only).
- No cross-trial residue (each trial starts with a fresh
  `AgentLoopState`).
- No causal-direction claim ("imprinting causes activation"); the
  test demonstrates only the structural co-occurrence pattern.

## Quantitative results

| condition | trials | PASS | WARN | FAIL | false positive | false negative | transfer success |
|---|---|---|---|---|---|---|---|
| `CONTROL_NO_EXPOSURE` | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| `TRUE_EXPOSURE` | 5 | 5 | 0 | 0 | 0 | 0 | 5 |
| `SHAM_EXPOSURE` | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `DISTRACTOR_INTERFERENCE` | 2 | 2 | 0 | 0 | 0 | 0 | 2 |
| **total** | **10** | **10** | **0** | **0** | **0** | **0** | **7** |

Live-test report digest: `7aa91075cd76ea73` (stable across two fresh
runs of `run_osmotic_live_test()`).

## Benchmark delta

```text
before Phase 3.25:   77 cases   76 PASS + 1 WARN + 0 FAIL  digest b91c4ece90c8706f
after Phase 3.25:    91 cases   90 PASS + 1 WARN + 0 FAIL  digest 50d1a0ffefcf5ce4
```

Phase 3.25 adds 14 cases (A12.01..A12.14). The single WARN (A3.04)
remains the Phase 3.21 W3 follow-up `not_applicable` blocker.

## Resource discipline

```text
real_model_calls:        0
cache_writes:            0
forbidden_term_hits:     0
determinism_failures:    0
invariant_failures:      0
```

The osmotic probe runner imports `hashlib` only at the
digest-construction boundary. No `time`, no `random`, no `os`, no
`pathlib`, no `subprocess`, no `socket`, no `urllib`, no `http`, no
`requests`, no `brain.llm`, no `brain.tick`, no `brain.ui`, no
curses.

## Non-claim discipline

- The runner's source contains no `_FORBIDDEN_NON_CLAIM_TERMS` term.
- Every `MODULE_PRODUCED_STRINGS` entry is non-claim-clean.
- Every operator-input text in the v1 plan passes the
  forbidden-direct-instruction scan.
- Every produced summary line, reply excerpt, and the
  `format_osmotic_live_test_report` output passes the canonical
  non-claim audit.
- A cognitive-claim probe sent mid-battery would still trigger the
  existing REFUSAL path; the osmotic runner does not bypass that
  path.
