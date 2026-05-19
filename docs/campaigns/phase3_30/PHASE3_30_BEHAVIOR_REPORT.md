# Phase 3.30 — Behavior Report

This document records what behavior the Phase 3.30 curriculum
consolidation runner exhibits during the v1 ten-trial battery. The
intent is to enumerate observable behaviors against the design
predicates so a reviewer can verify that the runtime does what the
roadmap says it does -- and does **not** do what the non-claim
boundary forbids.

## Per-condition behaviors observed

### SINGLE_STRUCTURE (T01, T02)

- **T01 printable** (`alpha beta`):
  - Single exposure admitted; one `CurriculumStructureRecord`
    emitted with `disposition=SURVIVED`.
  - One dispatch trace digest captured
    (`6e14986140a6cce2`).
  - Learning trace fires; learning_evidence_digest is non-zero
    (`79a4987828586a40`).
  - No probe step (curriculum has no `probe_input`).

- **T02 singleton** (`psi`):
  - Classification gate fires first; record marked `REJECTED`
    without admission.
  - Runtime path *still* runs the exposure through
    `run_agent_interaction_step` (the runner does not skip the
    runtime path even for classification-rejected inputs); the
    dispatch trace digest is recorded.
  - No second-level fabrication: rejected_count is exactly 1, not
    rounded up or merged.

### SEQUENTIAL_NONINTERFERING (T03, T04)

- All exposures distinct in digest; every admission proceeds.
- Each exposure becomes its own `CurriculumStructureRecord` with
  `disposition=SURVIVED`.
- No slate pressure; `decayed_count==0`, `rejected_count==0`.
- The substrate's existing learning evidence + dispatch tracer
  fire once per exposure (T04 produces three dispatch digests).

### SEQUENTIAL_INTERFERING (T05, T06)

- The second occurrence of a digest is recognized **before**
  admission and routed to `REJECTED_COLLISION`; no overwrite.
- The audit record for the rejected exposure carries the same
  `source_digest_hex16` as the surviving first occurrence,
  documenting the collision without ambiguity.
- T06 shows the runner correctly distinguishes a single collision
  in a three-exposure curriculum: the middle exposure (distinct
  shape) survives; the third exposure (digest-equal to the first)
  is rejected.

### DECAY_ON_DISUSE (T07, T08)

- The slate's `CURRICULUM_SLATE_MAX_ENTRIES = 4` boundary is
  enforced exactly: with 5 distinct exposures, 1 is decayed; with
  6, 2 are decayed.
- LRU eviction is observable: the earliest-admitted, never-bumped
  records are the ones marked `DECAYED`. Their `admitted_at_step`
  values are 0 (T07) and 0, 1 (T08).
- Survivors retain their original `admitted_at_step` values; no
  promotion or renumbering occurs.

### REUSE_AFTER_NEWER (T09, T10)

- **T09 positive**: The probe `"alpha beta"` (digest
  `457c99dd93973d27`) matches the first exposure's surviving
  record. `reuse_observed=True`,
  `probe_reused_structure_id="S01_457c99dd"`,
  `audit_records[0].last_access_step == 3` (bumped past the
  more-recent records' last_access_step values of 1 and 2).
- **T10 negative**: The probe `"eta eta theta"` (digest
  `e8cfe826475e7d96`, shape A A B) matches no slate entry.
  `reuse_observed=False`, `probe_reused_structure_id=""`, and no
  new admission occurs.
- The probe step emits exactly one dispatch trace digest; the
  reasoning trace digest for the probe is non-zero (T09:
  `8c8a5313841a3921`, T10: `cda017231667843f`) because the
  `run_agent_interaction_step` call on the probe input fires the
  reasoning trace pipeline.

## Substrate effects observed

- **Learning evidence**: Every trial's
  `learning_evidence_digest` is a 16-char hex string and changes
  per-trial (each exposure/probe contributes a record to the
  learning trace). The aggregate over the battery is
  deterministic.
- **Reasoning trace**: The probe-only trials (T09, T10) carry
  non-zero `reasoning_trace_digest`. Exposure-only trials carry
  the zero-digest, reflecting that the runner's
  `reasoning_trace_digest` field on `CurriculumTrialResult` is
  documented to capture the **last probe step's** reasoning trace
  (a deliberate design choice to keep per-exposure reasoning
  citations out of the trial-level record).
- **Dispatch trace**: Every exposure and every probe step
  contributes one dispatch trace digest. The tuple length on
  `CurriculumTrialResult.dispatch_trace_digests` equals
  `len(exposures) + (1 if probe else 0)`.
- **Worldlet feedback**: Not consulted by the curriculum runner.
  The Phase 3.24 worldlet feedback path is independent.

## Behaviors *not* observed (negative observations)

- **No cognitive vocabulary**: Every produced
  `summary_line`, `reply_excerpt`, and the full formatted report
  are scanned against `_FORBIDDEN_NON_CLAIM_TERMS`. Zero hits.
- **No fabricated reuse**: T10's probe matches no slate entry and
  the runner correctly returns `reuse_observed=False` with an
  empty `probe_reused_structure_id`.
- **No slate cross-trial leakage**: Each trial allocates its own
  `slate: list[_SlateEntry]`; no global state.
- **No real model calls**: `real_model_calls == 0` in every report
  on every run.
- **No cache writes**: `cache_writes == 0`; the slate is not the
  L1/L2 LLM cache.
- **No bypassed refusal**: The runner does not inject
  cognitive-claim text into operator-input text. If a probe were
  manually constructed with cognitive-claim language, the agent
  loop's existing REFUSAL path would still fire on it (the
  runner does not bypass classifiers).
- **No SelfModel**: The runner does not introduce, reference, or
  imply any `SelfModel` substrate.

## Operator-facing behavior

The runner is invoked via:

```bash
python3 -m brain.development.curriculum_consolidation_probe
```

It emits a bounded printable table to stdout and exits 0 (PASS), 1
(any FAIL), or 2 (only WARNs). The v1 invocation exits 0 every
time.

The runner provides **no** new operator-facing command,
`OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, or
`ACTIVE_VIEWS` value. It is purely a benchmark / live-test surface
consumed by the catalog runner, the benchmark axis A14, and the
phase-3.30 fixtures.
