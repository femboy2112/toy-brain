# Phase 3.30 — Findings

## What worked

1. **The runner produced a deterministic green report on first
   end-to-end invocation.** All ten trials passed without
   adjustment to the v1 trial battery or candidate pool. The
   deterministic digest is `9412acec1163b978` and is bit-identical
   across reruns.

2. **The LRU decay rule correctly handles overflow at +1 and +2
   capacity.** T07 (5 exposures into a 4-slot slate) drops exactly
   one entry; T08 (6 exposures) drops exactly two. The dropped
   entries are the earliest-admitted, never-bumped records, which
   matches the design predicate exactly.

3. **The collision-rejection rule prefers the first occurrence.**
   A digest-equal duplicate exposure is `REJECTED` and the first
   record retains `SURVIVED` status. No silent merge, no
   overwrite, no special-case "fresher wins" exception.

4. **The probe-time reuse bump is observable in
   `last_access_step`.** T09 demonstrates that probing an older
   record updates its `last_access_step` past more recently
   admitted records, which is the substrate condition needed for
   correct LRU behavior under repeated reuse-after-newer cycles
   (Phase 3.32 territory).

5. **Per-trial slate isolation works.** Each trial allocates its
   own slate; no cross-trial state leakage. Verified by
   determinism (re-running produces identical results) and by the
   per-trial `dispatch_trace_digests` tuples (no shared state
   would manifest as differing digests).

6. **The substrate's learning evidence + dispatch tracer + reasoning
   trace pipelines fire as usual.** The curriculum runner does not
   bypass `run_agent_interaction_step`; every exposure and probe
   rides through the existing agent-loop pipeline. Per-trial
   `learning_evidence_digest` and per-step `dispatch_trace_digest`
   values are recorded and citation-stable across reruns.

7. **The Phase 3.26 anti-cheating discipline carries over
   unchanged.** Expected-outcome fields on `CurriculumTrial` are
   used only by the benchmark assertion layer after
   `run_curriculum_trial` returns; the runtime path never sees
   them. Forbidden direct-instruction terms are absent from every
   operator-input text in the v1 battery.

## What surfaced design questions for later phases

1. **Decay policy is currently LRU; alternative policies are a
   Phase 3.33 question.** The closed v1 rule is "evict
   `slate[0]`", which equals the least-recently-accessed entry by
   insertion order (the probe-bump moves the matched entry's
   `last_access_step` value but does NOT reorder the list). A more
   sophisticated policy (reorder on bump; age-weighted; FIFO)
   would require an explicit operator choice, which Phase 3.33
   carries forward.

2. **Probe step's reuse bump updates `last_access_step` but does
   not move the entry within the slate list.** This means a second
   reuse-after-newer probe in the same trial could see the
   slate's `slate[0]` evicted **even if it was recently bumped**.
   The v1 battery does not run that case, so the spec is silent
   on whether the LRU rule should consult `last_access_step` for
   eviction selection vs. insertion order. Phase 3.32 (adaptive
   curriculum) or a Phase 3.33 follow-up could refine this.

3. **The curriculum runner is session-local; cross-session
   retention is Phase 3.31's question.** As designed in the
   roadmap, the slate is bound to a single
   `run_curriculum_trial(...)` call. Phase 3.31 (cross-session
   reuse cache for curriculum slates) would require a persistence
   schema column, an autosave trigger, and corresponding
   non-claim guardrails -- which the current acceptance bar
   forbids without explicit operator approval.

4. **The reasoning trace digest is captured only for the probe
   step.** Trials without a probe (T01..T08) carry the zero-digest
   for `reasoning_trace_digest`. If a downstream consumer wants a
   per-exposure reasoning digest, Phase 3.32 would need to
   restructure `CurriculumTrialResult` to expose either a tuple of
   per-step reasoning digests (mirroring `dispatch_trace_digests`)
   or aggregate a single deterministic digest over the curriculum's
   exposures.

5. **The v1 exposure pool is bounded to 10 canonical shapes plus
   one singleton and one empty.** A larger pool would let
   `DECAY_ON_DISUSE` exercise larger overflows. The v1 design caps
   `CURRICULUM_MAX_EXPOSURES_PER_TRIAL = 8`, so even with the
   current pool a 7- or 8-exposure decay trial is in bounds for a
   future expansion.

## What did not need adjustment

- The substrate's existing `derive_abstract_pattern_signature`
  layer handles every input cleanly; the runner did not need a
  new digest helper.
- The agent loop's existing classification of empty / singleton /
  overlong / non-printable / too-many-tokens inputs is exactly
  what the curriculum runner's admission rule consumes.
- The existing Phase 3.22b learning evidence + reasoning trace
  modules expose enough public surface (no new
  `LearningEvidenceKind` member, no new `ReasoningStepKind`
  member) for the curriculum runner to capture per-trial digests.
- The Phase 3.23 dispatch tracer + Phase 3.24 worldlet feedback
  surfaces are not consulted; the curriculum runner is independent
  of those subsystems.

## Confidence call

The Phase 3.30 design is **operationally satisfied** by the v1
runner. Every acceptance criterion in
`PHASE3_30_CURRICULUM_CONSOLIDATION_ROADMAP.md` passes. The non-
claim boundary holds at every audited surface (module source,
produced strings, operator inputs, formatted report).

The phase is ready for review and PR #32 open.
