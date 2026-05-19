# Phase 3.25 — Osmotic Live Test Spec

This document is the **design contract** for Phase 3.25. Every item in
the acceptance criteria of the campaign points here.

## S.1 Module shape

`brain/development/osmotic_learning_probe.py` is a pure deterministic
OFFLINE live-test runner. Its closed import set is:

```text
__future__, dataclasses, enum, hashlib, typing, argparse, sys
brain.development.abstract_pattern
brain.development.agent_loop
brain.development.coherence_monitor (only for _FORBIDDEN_NON_CLAIM_TERMS)
brain.development.learning_evidence
brain.development.reasoning_trace
```

No `brain.llm`, no `brain.tick`, no `brain.ui`, no `os` /
`subprocess` / `socket` / `urllib` / `http` / `requests` / `pathlib`
/ `tempfile` / `shutil` / `threading` / `asyncio` / `atexit` /
`signal` / `importlib` / `time` / `random` / `math`.

## S.2 Closed enums

```python
class OsmoticCondition(str, Enum):
    CONTROL_NO_EXPOSURE = "control_no_exposure"
    TRUE_EXPOSURE = "true_exposure"
    SHAM_EXPOSURE = "sham_exposure"
    DISTRACTOR_INTERFERENCE = "distractor_interference"

class OsmoticProbeStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
```

## S.3 Records

```python
OsmoticExposureEvent(text, interaction_id, abstract_digest_hex16,
                     classification, shape)
OsmoticProbeTrial(trial_id, condition, exposure_texts, probe_text,
                   expected_target_digest, expected_target_shape,
                   expected_prior_acquired, expected_transfer)
OsmoticProbeResult(trial_id, condition, status, exposure_events,
                    probe_digest, probe_shape, probe_classification,
                    prior_acquired_observed, transfer_observed,
                    expected_prior_acquired, expected_transfer,
                    false_positive, false_negative,
                    learning_evidence_digest, reasoning_trace_digest,
                    dispatch_trace_digests, reply_excerpt,
                    summary_line)
OsmoticLiveTestReport(battery_version, trials, pass_count, warn_count,
                       fail_count, not_applicable_count,
                       false_positive_count, false_negative_count,
                       transfer_success_count, real_model_calls,
                       cache_writes, forbidden_term_hits,
                       digest_hex16, summary_line)
```

All records are frozen / slotted; every field is bounded; no
callable, no socket, no client, no path.

## S.4 Functions

```python
build_osmotic_exposure_plan() -> tuple[OsmoticProbeTrial, ...]
run_osmotic_probe_trial(trial: OsmoticProbeTrial) -> OsmoticProbeResult
run_osmotic_live_test(trials=None) -> OsmoticLiveTestReport
format_osmotic_live_test_report(report) -> str
osmotic_live_test_digest(report) -> str
main(argv) -> int
```

The v1 trial battery contains exactly the 10 trials documented in
`PHASE3_25_OSMOTIC_LEARNING_TEST_DESIGN.md`.

## S.5 Runtime path discipline

- `run_osmotic_probe_trial(trial)` constructs a **fresh**
  `AgentLoopState` per trial; trials do not leak state.
- For each exposure text, `run_agent_interaction_step(state, text)`
  is invoked; the exposure event is recorded with the bounded
  abstract digest computed from the exposure text via
  `derive_abstract_pattern_signature`.
- Before the probe, the runner records
  `prior_acquired_observed = has_acquired_digest(state.learning_trace,
  trial.expected_target_digest)`.
- The probe step is then `run_agent_interaction_step(state,
  trial.probe_text)`; the runner inspects the *new* records appended
  during this step for a `TRANSFER_RECOGNIZED` record whose
  `abstract_pattern_digest == trial.expected_target_digest`.
- The runtime path **never** sees `trial.expected_target_digest` or
  `trial.expected_target_shape` as an input.

## S.6 Verdict derivation

```text
false_positive  = transfer_observed and not expected_transfer
false_negative  = (not transfer_observed) and expected_transfer
prior_acquired_match = (prior_acquired_observed == expected_prior_acquired)
status = PASS iff (not false_positive)
                and (not false_negative)
                and prior_acquired_match
       else FAIL
```

`WARN` and `NOT_APPLICABLE` are reserved for future trials that
cannot be evaluated; the v1 battery never uses them.

## S.7 Determinism

- Two invocations of `run_osmotic_probe_trial(trial)` on the same
  trial produce bit-identical results.
- Two invocations of `run_osmotic_live_test()` produce equal
  `digest_hex16` and equal `trials` tuples.
- The digest is `sha256(canonical_serialization)[:16]` where the
  canonical serialization is the line-joined per-trial fields in a
  locked order.

## S.8 Non-claim discipline

- Every produced summary string, reply excerpt, and report line
  passes the canonical `_FORBIDDEN_NON_CLAIM_TERMS` audit.
- Operator-input texts (exposure + probe) are scanned for forbidden
  direct-instruction terms (`learn`, `remember`, `pattern`,
  `classify`, `transfer`, `reuse`, `ABAB`, `ABBA`, `ABCABC`,
  `structure`, `shape`, `imprint`, `osmotic`, `absorb`, `imbibe`,
  `intuition`); the v1 battery uses none of them in operator input
  text. The exclusion applies only to operator-input text, not to
  trial ids or summary lines.

## S.9 Benchmark axis

`BenchmarkAxis.OSMOTIC_LEARNING = "osmotic_learning"` with 14 cases
`A12.01..A12.14`. Mapping documented in
`PHASE3_25_OSMOTIC_LEARNING_TEST_DESIGN.md` § Trial battery and the
catalog rows I-OSMO-01..14.

## S.10 Catalog rows

`I-OSMO-01..14` (13 REQUIRED + 1 STRUCTURAL). Bumps the catalog to
v0.34. Ten new fixtures.

## S.11 Hard constraints

- No edit to `brain/tick.py`, `brain/llm/**`, parser, prompt, DB
  schema, autosave policy, L1 / L2 cache, Pattern Ledger / Coherence
  Monitor / Growth Ledger semantics, or curses code.
- No new `OperatorCommand` member; no new `ACTIVE_VIEWS` value; no
  new `GrowthEventType` / `GrowthEventSource`.
- No new `LearningEvidenceKind` / `ReasoningStepKind` value (Phase
  3.25 reuses the existing `ABSTRACT_PATTERN_ACQUIRED`,
  `ABSTRACT_PATTERN_REUSED`, `TRANSFER_RECOGNIZED` records and the
  existing `DERIVE_PATTERN`, `LOOKUP_PRIOR_STRUCTURE`,
  `COMPARE_STRUCTURE` reasoning steps).
- OFFLINE default preserved; model-backed paths remain explicit
  opt-in. The model-backed live smoke is **deferred** to a separate
  OBSERVED row only if approved.
- Zero real model calls expected.

## S.12 Acceptance

Pass only when:

- the runner produces a deterministic 10-trial report with 10 PASS,
  0 WARN, 0 FAIL, false_positive=0, false_negative=0,
  transfer_success=7;
- runner is fully green (`python3 -m brain.invariants run`);
- benchmark axes A1..A12 are green (A3.04 WARN may remain);
- gate_runner is 5/5 PASS;
- branch is pushed;
- PR #30 is open against
  `campaign/phase3-24-worldlet-feedback-bridge`.
