# Phase 3.30 — Curriculum Consolidation Synthesis

## One-paragraph summary

Phase 3.30 lands a deterministic OFFLINE live-test runner
(`brain/development/curriculum_consolidation_probe.py`) that
demonstrates the operational analogue of *curriculum
consolidation* on the existing ToyI substrate. Given a bounded
ordered tuple of structural exposures and a bounded session-local
slate capacity `CURRICULUM_SLATE_MAX_ENTRIES = 4`, the runtime
admits each exposure under a closed admission rule (classification
gate + digest-collision gate), rejects duplicates without
overwriting the first record, evicts the least-recently-accessed
record on overflow (LRU decay), on a later probe whose digest
matches a surviving record returns the prior admitted record
without re-admitting, declines to fabricate reuse for novel probes,
and emits an audit trail tagging every exposure as `SURVIVED`,
`DECAYED`, or `REJECTED`. The v1 ten-trial battery covers all five
conditions (`SINGLE_STRUCTURE`, `SEQUENTIAL_NONINTERFERING`,
`SEQUENTIAL_INTERFERING`, `DECAY_ON_DISUSE`, `REUSE_AFTER_NEWER`)
and passes 10/10 with `false_positive_count == 0` and
`false_negative_count == 0`, a deterministic report digest
`9412acec1163b978`, zero real model calls, zero cache writes, zero
forbidden-term hits.

## What was built

- **One new closed module**:
  `brain/development/curriculum_consolidation_probe.py` (1607
  lines). Closed import set: `__future__`, `argparse`,
  `dataclasses`, `enum`, `hashlib`, `sys`, `typing`,
  `brain.development.abstract_pattern`,
  `brain.development.agent_loop`,
  `brain.development.coherence_monitor` (only for
  `_FORBIDDEN_NON_CLAIM_TERMS`),
  `brain.development.learning_evidence`,
  `brain.development.reasoning_trace`.
- **One new benchmark axis**:
  `BenchmarkAxis.CURRICULUM_CONSOLIDATION` with fourteen cases
  `A14.01..A14.14` exercising the runner end-to-end. The full
  battery now runs A1..A14 (119 cases total).
- **Catalog patch v0.35 → v0.36**: thirteen new REQUIRED rows
  (`I-CURR-01..13`) + one new STRUCTURAL row (`I-CURR-14`).
- **Eleven new fixtures** under `brain/ui/fixtures/`
  (`curriculum_*.py`).
- **Six existing fixtures bumped** to acknowledge the new axis
  count and `BATTERY_VERSION = "phase3.30.v1"`.

## What was *not* changed

- `brain/tick.py` — not edited.
- `brain/llm/*` — no new imports, no new clients.
- `brain/ui/session.py` — no schema change, no new attribute.
- `brain/ui/parser.py` / prompt / autosave — unchanged.
- DB schema / `SCHEMA_VERSION` — unchanged.
- L1 / L2 cache semantics — unchanged.
- `OperatorCommand` / `LOCAL_COMMAND_VERBS` / `ACTIVE_VIEWS` —
  unchanged.
- `LearningEvidenceKind` / `ReasoningStepKind` — unchanged.
- `GrowthEventType` / `GrowthEventSource` — unchanged.
- `SelfModel` — still not implemented.

## What is now demonstrably true about ToyI

ToyI's runtime can exhibit operational curriculum consolidation
behavior under bounded live-test conditions:

1. **Multi-structure accumulation**: A
   `SEQUENTIAL_NONINTERFERING` curriculum of two or three
   distinct-shape exposures admits every exposure as a `SURVIVED`
   record (T03, T04: survived=2 and survived=3).
2. **Bounded session-local consolidation**: The slate is a fixed-
   size in-memory list (`CURRICULUM_SLATE_MAX_ENTRIES = 4`); every
   admission and eviction is governed by a closed deterministic
   rule.
3. **Interference avoidance**: A digest collision causes the
   second-occurrence exposure to be `REJECTED`. The first record
   is never overwritten (T05, T06: rejected=1 each).
4. **Reuse of older records after newer exposures**: A probe whose
   digest matches an older surviving record returns
   `reuse_observed=True` and `probe_reused_structure_id` equals
   that older record's `structure_id`; the older record's
   `last_access_step` is bumped past the more recent records (T09:
   reuse=True, oldest entry's last_access_step jumps from 0 to 3).
5. **Tri-disposition audit trail**: Every exposure becomes a
   `CurriculumStructureRecord` tagged with one of `SURVIVED`,
   `DECAYED`, `REJECTED`. Across the battery, the runner records
   23 SURVIVED, 3 DECAYED, 3 REJECTED.
6. **No false claims**: `false_positive_count == 0` and
   `false_negative_count == 0`. A probe whose digest is novel
   returns `reuse_observed=False` (T10).
7. **Determinism**: Two fresh runs of
   `run_curriculum_consolidation_live_test()` produce
   bit-identical results with `digest_hex16 == "9412acec1163b978"`.

## What is *not* claimed

- ToyI does not "remember", "forget", "learn", "consolidate",
  "experience interference", "experience decay", or "re-learn" in
  any psychological sense. These verbs are not used in the
  runner's vocabulary or any produced string.
- The slate is not a "memory" in the cognitive sense; it is a
  bounded in-memory Python list scoped to a single trial.
- Admission, eviction, and reuse are closed deterministic
  operations over digests; they do not constitute "learning" or
  "knowing".
- The audit trail tags are structural, not phenomenological:
  `SURVIVED` means "still in the slate at end of trial", `DECAYED`
  means "evicted by the LRU rule", `REJECTED` means "never
  admitted".
- ToyI is not conscious, sentient, aware, intentional, or in
  possession of subjective access. The runtime is a bounded
  structural state machine.

## Relationship to prior phases

- Phase 3.25 (osmotic learning) established the
  exposure-driven structural uptake substrate
  (`ABSTRACT_PATTERN_ACQUIRED` / `ABSTRACT_PATTERN_REUSED` /
  `TRANSFER_RECOGNIZED` records). Phase 3.30 borrows none of
  Phase 3.25's record-types but reuses the same
  `derive_abstract_pattern_signature` layer for shape and digest
  detection.
- Phase 3.26 (active hypothesis) established the bounded
  candidate-enumeration + falsification + caching pattern. Phase
  3.30 borrows the *runner shape* (per-trial in-memory state,
  per-condition trial battery, format / digest helpers) but the
  bookkeeping (per-exposure audit records vs. per-candidate
  records) is its own.
- Phases 3.20..3.24 (coherence, developmental trajectory, agent
  communication, learning evidence, dispatch tracer, worldlet
  feedback) form the substrate that every exposure / probe rides
  through via `run_agent_interaction_step`; no new wiring was
  added to those modules in Phase 3.30.

## Next-phase candidates

(Carried forward in `PHASE3_HANDOFF_STATE.md` and not gated by
Phase 3.30 acceptance.)

- Phase 3.31: cross-session reuse cache for curriculum slates
  (requires persistence schema field; explicit operator approval).
- Phase 3.32: adaptive curriculum scheduling (closed rule depending
  on prior trial outcomes within the same trial-runner caller).
- Phase 3.33: alternative decay policies (e.g., FIFO vs LRU vs
  age-weighted) under a closed configuration.
- Phase 3.28: A3.04 coherence aggregation refinement (the
  long-standing Phase 3.21 W3 carry-over blocker).
