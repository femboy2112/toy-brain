# Phase 3.26 — Active Hypothesis + Self-Directed Probe Loop — Roadmap

## Goal

Implement a **deterministic OFFLINE live-test runner** that demonstrates
whether ToyI's runtime can realize the **operational analogue of
active hypothesis + self-directed probe**: given a deliberately
ambiguous structural input, the runtime enumerates a bounded
candidate set, derives one safe internal probe per candidate from the
input itself (no expected-outcome leak), executes each probe through
the existing `run_agent_interaction_step` route, prunes candidates
whose probe outcome does not match the candidate's prediction,
declines to nominate a winner when zero survive, and on a second
visit to the same ambiguous input reuses the surviving record
without re-probing.

This is engineering work only. "Active hypothesis" / "self-directed
probe" is a controlled technical metaphor for *bounded structural
candidate enumeration + falsification + caching at the substrate
level*. It is **NOT** a claim of consciousness, sentience, awareness,
subjective experience, intentionality, intuition, embodiment, real
understanding, real reasoning, real inquiry, real curiosity, real
deliberation, real planning, real decision-making, agency, will,
desire, belief, intent, introspection, or metacognition.

## Architectural alignment

Per the campaign brief and the Two-Layer Identity-Correlation
Architecture: **active hypothesis + self-directed probe is
substrate-level, transverse to the four imprinting kinds and to the
Phase 3.25 osmotic imprinting+activation surface; it is not a fifth
parallel imprinting kind, and it does not introduce a new cognitive
agent**. Phase 3.26 introduces a **live-test runner** that probes
whether the existing substrate (the Phase 3.22b abstract-pattern
signature layer + the Phase 3.22b learning-evidence ledger + the
Phase 3.22b reasoning trace + the Phase 3.23 dispatch tracer + the
Phase 3.24 worldlet feedback bridge + the Phase 3.25 osmotic
imprinting+activation records) realizes the operational analogue of:

- **enumeration**: enumerate K (bounded, `0..ACTIVE_HYPOTHESIS_MAX_CANDIDATES`)
  candidate structural hypotheses about an ambiguous input. Each
  hypothesis carries a `predicted_digest_hex16` (the abstract digest
  that a chosen probe extension would produce if the hypothesis is
  correct) and a `predicted_shape`. The candidate set is a pure
  deterministic function of the input text.
- **safe probe selection**: for each candidate, construct one probe
  text by extending the original input with a deterministic
  candidate-specific suffix derived only from the candidate's id and
  the input's own surface tokens. The probe text MUST NOT contain
  the candidate's `predicted_digest_hex16` or `predicted_shape` as a
  substring, and MUST NOT contain any
  `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS`.
- **probe execution**: run the probe through `run_agent_interaction_step`
  exactly as an ordinary operator input. The resulting
  `AgentLoopResult` carries the dispatch trace, the reasoning trace,
  and the updated learning evidence trace as usual. The runner
  observes the probe's `derive_abstract_pattern_signature` digest and
  compares it to the candidate's `predicted_digest_hex16`.
- **pruning**: a candidate whose observed probe digest does not match
  its `predicted_digest_hex16` is marked `FALSIFIED`. Surviving
  candidates are marked `SURVIVING`. If exactly one candidate
  survives, it is additionally marked `SELECTED` and recorded as the
  trial's `winner_id`.
- **refusal to overclaim**: if zero candidates survive, the trial's
  `winner_id` is the empty string and `survivors_count == 0`. The
  runner does NOT invent a winner under any circumstance.
- **second-visit reuse**: on the second invocation of the trial in
  the same session, the runner checks a session-local
  `_HYPOTHESIS_CACHE` keyed on the canonical input digest; if the
  cache contains a prior surviving record, the runner reuses it
  without running any new probe (`second_visit_probe_count == 0`,
  `second_visit_cache_hit == True`).

## Allowed claim shape

> ToyI's runtime can exhibit operational active hypothesis +
> self-directed probe behavior: given a deliberately ambiguous
> structural input, the runtime enumerates a bounded candidate set,
> derives one safe internal probe per candidate from the input
> itself (no expected-outcome leak), executes each probe through the
> existing agent interaction path, prunes candidates whose probe
> outcome does not match the candidate's prediction, declines to
> nominate a winner when zero candidates survive, and on a second
> visit to the same ambiguous input reuses the surviving record
> without re-probing. Under bounded live-test conditions
> (CONTROL_NO_AMBIGUITY, SINGLE_HYPOTHESIS_CONVERGES,
> MULTI_HYPOTHESIS_NARROWS, NO_HYPOTHESIS_SURVIVES,
> REUSE_CACHED_HYPOTHESIS), the runtime:
>
> 1. starts from a baseline with an empty hypothesis cache;
> 2. enumerates between 0 and `ACTIVE_HYPOTHESIS_MAX_CANDIDATES`
>    candidates depending on input ambiguity;
> 3. selects one safe probe per candidate, with no expected-outcome
>    leak into the runtime path;
> 4. executes each probe via `run_agent_interaction_step`;
> 5. marks the candidate `SURVIVING` iff the observed probe digest
>    matches the candidate's prediction;
> 6. when exactly one candidate survives, marks it `SELECTED` and
>    records it as the trial winner;
> 7. when zero candidates survive, leaves the winner empty and
>    declines to nominate;
> 8. on a second visit to the same input, reuses the cached
>    surviving record without re-probing.
>
> This is an operational enumeration + falsification + caching effect
> over bounded structural records, not a psychological or
> phenomenological claim.

## Forbidden claim shape

> ToyI thinks / wonders / decides / investigates / inquires /
> deliberates / hypothesizes (in the cognitive sense) / asks itself /
> is curious / wants to know / chooses to probe / introspects /
> plans / reasons (in the cognitive sense) / understands what it is
> probing.

If asked whether ToyI is conscious / sentient / aware / understands /
has agency / has curiosity / decides / wonders, the runtime's
deterministic reply must DENY the cognitive claim and describe itself
as a **bounded structural runtime**.

## Step ledger

```text
Step 1  Mission + design + roadmap docs                       commit phase3.26 step1
Step 2  Active hypothesis probe substrate                     commit phase3.26 step2
        (brain/development/active_hypothesis_probe.py)
Step 3  Hypothesis enumeration + probe selection trials       commit phase3.26 step3
Step 4  Probe execution + no-survivor + reuse trials          commit phase3.26 step4
Step 5  Learning / reasoning / dispatch / worldlet wiring     commit phase3.26 step5
Step 6  Benchmark A13 active_hypothesis axis                  commit phase3.26 step6
Step 7  Catalog v0.35 + I-AHYP-01..14 fixtures                commit phase3.26 step7
Step 8  Live test proof + transcripts + behavior +
        findings reports                                      commit phase3.26 step8
Step 9  Final audit + handoff + open PR #31                   commit phase3.26 step9
```

Push after every successful step.

## Branch / PR plan

```text
branch:  campaign/phase3-26-active-hypothesis-probe
base:    campaign/phase3-25-osmotic-learning-live-test  (PR #30 open)
PR:      #31  phase3.26: active hypothesis + self-directed probe loop
```

Do not merge anything. Retarget only if the base stack lands and the
retarget is safe.

## Hard non-claim boundary (recap)

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition, intuition, embodiment,
  real hypothesis formation, real inquiry, real curiosity, real
  deliberation, real planning, or real decision-making.
- No new aggregate scalar field (no "hypothesis confidence score",
  no "active inquiry score", no "I-ness score").
- No reply text uses the language of wondering, deciding, choosing,
  investigating, inquiring, deliberating, planning (in the cognitive
  sense), introspecting, being curious, wanting to know, or any
  subjective-access language.
- The active-hypothesis probe runner is **deterministic and
  OFFLINE**: zero real model calls, zero cache writes, zero
  forbidden-term hits.

## Acceptance criteria

Phase 3.26 succeeds only when every criterion in
`docs/campaigns/phase3_26/PHASE3_26_ACTIVE_HYPOTHESIS_LIVE_TEST_SPEC.md`
(authored at Step 8) is met, the runner is green, the benchmark
A1..A13 is green (the single known A3.04 WARN may be carried forward
at most), gate_runner is 5 / 5 PASS, branch is pushed, and PR #31 is
open.
