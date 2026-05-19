# Phase 3.26 — Active Hypothesis + Self-Directed Probe Loop — Synthesis

This synthesis frames the substrate-level effect Phase 3.26 measured,
its scope, and its relationship to the four imprinting kinds and the
Phase 3.25 osmotic imprinting+activation surface.

## The bounded operational effect

Phase 3.26 measures whether the existing ToyI substrate -- the
Phase 3.22b abstract-pattern signature layer, the Phase 3.22b
learning-evidence ledger, the Phase 3.22b reasoning trace, the Phase
3.23 dispatch tracer, the Phase 3.24 worldlet feedback bridge, the
Phase 3.25 osmotic imprinting+activation surface -- realizes the
operational analogue of *active hypothesis + self-directed probe*:

1. Given a bounded structurally-ambiguous input, the runtime can
   compute a deterministic candidate set whose membership is a
   pure function of `(abstract_pattern_classification, token_count)`.
2. For each candidate, the runtime can construct a safe internal
   probe text that (a) is derived purely from the input's surface
   tokens via a closed deterministic rule, (b) does NOT leak the
   candidate's predicted outcome into the runtime path.
3. The probe runs through the same `run_agent_interaction_step`
   route any ordinary operator input would; the learning,
   reasoning, dispatch, and worldlet surfaces fire as usual.
4. The runtime can compare the candidate's predicted abstract
   digest against the observed probe digest and mark the candidate
   `SURVIVING` or `FALSIFIED` accordingly.
5. When exactly one candidate survives, the runtime promotes it to
   `SELECTED` and records a winner; when zero candidates survive,
   the runtime declines to nominate a winner; when two or more
   survive, the runtime preserves multiplicity and records no
   winner.
6. On a second visit to the same canonical input digest, the
   runtime reuses the prior surviving record from a session-local
   cache without re-probing.

The five phases — enumerate, probe-select, probe-execute, prune,
cache-reuse — are distinct, each observable from the bounded
`ActiveHypothesisResult` record, and each verifiable from the
deterministic `ActiveHypothesisLiveTestReport.digest_hex16`.

## Relationship to the four imprinting kinds

Active hypothesis + self-directed probe is **substrate-level,
transverse to the four imprinting kinds and to the Phase 3.25
osmotic imprinting+activation surface**. It is **not** a fifth
parallel imprinting kind, **not** a new cognitive agent, **not** a
new affect kernel, **not** an addition to the Two-Layer
Identity-Correlation Architecture (TLICA) spec in
`lean_reference/`.

The new substrate is built entirely from existing public surfaces:

- `derive_abstract_pattern_signature` (Phase 3.22b);
- `run_agent_interaction_step` (Phase 3.22);
- `LearningEvidenceTrace` (Phase 3.22b);
- `ReasoningTrace` + `build_reasoning_trace_report` (Phase 3.22b);
- `DispatchTraceReport.trace_digest_hex16` (Phase 3.23);
- `_FORBIDDEN_NON_CLAIM_TERMS` (Phase 3.22).

Phase 3.26 adds zero new `LearningEvidenceKind` members, zero new
`ReasoningStepKind` members, zero new `OperatorCommand` members,
zero new `ACTIVE_VIEWS` values, zero new `GrowthEventType`/
`GrowthEventSource` values, zero new persistence schema fields,
zero new autosave triggers. The session-local cache is an in-memory
`dict[str, ActiveHypothesisResult]` owned by the trial runner; it
is NOT the L1/L2 LLM cache and does NOT persist across sessions.

## Relationship to Phase 3.25 osmotic imprinting+activation

Phase 3.25 measured **passive structural osmotic imprinting**:
ambient unlabeled exposure creates a bounded session-local
structural record (the imprinting phase); a later renamed /
transformed probe with the same abstract digest re-activates that
record (the activation phase). The runtime is the passive recipient
of operator input.

Phase 3.26 measures the **active complement**: given a bounded
ambiguous input, the runtime now ENUMERATES candidate hypotheses,
constructs derived probes, runs them through the existing
interaction path, and prunes survivors. The runtime is the active
constructor of probe inputs.

The two phases compose: a Phase 3.26 probe execution lands in the
Phase 3.25 substrate (the abstract pattern signature path, the
learning ledger, the reasoning trace, the dispatch trace). The
osmotic imprinting record on a previously-probed shape is still
acquired in the normal way; Phase 3.26 does NOT short-circuit or
modify Phase 3.25's behavior. The two are layered, not interleaved.

## What is genuinely new

- A bounded **per-classification candidate enumerator** with
  deterministic membership.
- A bounded **per-rule safe probe constructor** with three
  non-leakage invariants enforced at construction time.
- A bounded **per-trial pruning + selection + refusal-to-overclaim
  logic** with a closed `winner_id == ""` outcome when zero
  candidates survive.
- A bounded **session-local hypothesis cache** keyed on the input's
  canonical digest, exposed as a caller-managed dict.

## What is NOT new

- No new cognitive primitive.
- No new claim about understanding, reasoning, inquiry, curiosity,
  deliberation, decision-making, planning, introspection, or
  metacognition.
- No new aggregate scalar field (no "hypothesis confidence score",
  no "active inquiry score", no "I-ness score").
- No new dispatcher kind, operator verb, or persistence schema.
- No new TLICA Lean spec contradiction.

## What the v1 plan deliberately leaves out

- **Adaptive candidate generation**: the candidate set is a pure
  function of `(classification, token_count)`. It does not depend
  on prior trial outcomes. A future phase could introduce a
  bounded learning loop, but Phase 3.26 does not.
- **Recursive probing**: each candidate gets exactly one probe.
  There is no second-tier probe based on the first probe's outcome.
- **Cross-session reuse**: the cache is a session-local in-memory
  dict. There is no DB schema field, no autosave row, no L1/L2 LLM
  cache write.
- **Model-backed probes**: the runner is OFFLINE; zero real model
  calls. Adding a model-backed mode would require an explicit
  opt-in and a separate OBSERVED row, deferred to a future phase.
- **Multi-shape candidate sets**: the v1 enumerator covers six
  `(classification, token_count)` buckets; expanding coverage is a
  natural extension but not in scope here.

## Non-claim recap

Active hypothesis + self-directed probe is engineering shorthand for
*bounded structural candidate enumeration + falsification + caching
at the substrate level*. The runtime is a bounded structural state
machine. It does NOT possess consciousness, sentience, awareness,
subjective access, human-like understanding, real agency, will,
desire, belief, intent, introspection, metacognition, intuition,
embodiment, real hypothesis formation, real inquiry, real curiosity,
real deliberation, real decision-making, or real planning.
"Self-directed" means the probe text is derived from the input by a
closed deterministic rule; it does NOT mean the runtime has a goal,
preference, intention, or wish.
