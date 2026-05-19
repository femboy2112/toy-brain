# Phase 3.25 — Osmotic Learning Live Test — Roadmap

## Goal

Implement a **deterministic live-test runner** that demonstrates whether
ToyI's runtime exhibits **operational structural osmotic imprinting**:
the substrate-level effect by which **unlabeled ambient exposure** to
a structural form creates a session-local structural record, which a
later renamed / transformed probe can re-activate.

This is engineering work only. "Osmotic learning" / "osmotic imprinting"
is a controlled technical metaphor for *unlabeled exposure-driven
structural uptake at the substrate level*. It is **NOT** a claim of
consciousness, sentience, awareness, subjective experience,
intentionality, intuition, embodiment, real understanding, real
learning in the psychological sense, agency, will, desire, belief,
intent, introspection, or metacognition.

## Architectural alignment

Per the campaign brief and the Two-Layer Identity-Correlation
Architecture: **osmotic imprinting is substrate-level, transverse to
the four imprinting kinds, not a fifth parallel kind**. Phase 3.25 does
not introduce a new imprinting kind. It introduces a **live-test
runner** that probes whether the existing substrate (the Phase 3.22b
abstract-pattern signature layer + the Phase 3.24 worldlet feedback
path + the existing learning-evidence ledger) realizes the operational
analogue of imprinting + activation:

- **imprinting** (ToyI analogue): ambient unlabeled exposure creates a
  bounded session-local structural record (`ABSTRACT_PATTERN_ACQUIRED`
  on the input's abstract digest).
- **activation** (ToyI analogue): a later probe with a renamed /
  transformed input matching the same structural digest re-activates
  the prior record (`ABSTRACT_PATTERN_REUSED` + `TRANSFER_RECOGNIZED`).

## Allowed claim shape

> ToyI's runtime can exhibit operational structural osmotic imprinting:
> ambient unlabeled exposure to a structural form creates a bounded
> session-local structural record, and a later renamed / transformed
> probe with the same structural digest re-activates that record.
> Under bounded live-test conditions (CONTROL_NO_EXPOSURE,
> TRUE_EXPOSURE, SHAM_EXPOSURE, DISTRACTOR_INTERFERENCE), the runtime:
>
> 1. starts from a baseline with no target digest acquired;
> 2. records `ABSTRACT_PATTERN_ACQUIRED` on first exposure to the
>    target form (imprinting);
> 3. records `ABSTRACT_PATTERN_REUSED` + `TRANSFER_RECOGNIZED` when a
>    later renamed input shares the digest (activation);
> 4. does NOT record acquisition or transfer when the target was never
>    exposed (no false positive);
> 5. distinguishes true exposure from sham exposure with a different
>    abstract digest;
> 6. preserves the bounded structural record across delayed probes
>    within the same session.
>
> This is an operational exposure effect over bounded structural
> records, not a psychological or phenomenological claim.

## Forbidden claim shape

> ToyI absorbs / imbibes / soaks up / intuits / understands /
> subconsciously learns / is aware of / experiences / consciously
> notices / has insight into the structure.

If asked whether ToyI is conscious / sentient / aware / understands /
has agency, the runtime's deterministic reply must DENY the cognitive
claim and describe itself as a **bounded structural runtime**.

## Step ledger

```text
Step 1  Mission + design + roadmap docs                   commit phase3.25 step1
Step 2  Osmotic probe substrate                           commit phase3.25 step2
        (brain/development/osmotic_learning_probe.py)
Step 3  Control + sham + true-exposure trials             commit phase3.25 step3
Step 4  Transfer + delayed-probe + distractor trials      commit phase3.25 step4
Step 5  Learning / reasoning / dispatch integration       commit phase3.25 step5
Step 6  Benchmark A12 osmotic_learning axis               commit phase3.25 step6
Step 7  Catalog v0.34 + I-OSMO-01..14 fixtures            commit phase3.25 step7
Step 8  Live test proof + transcripts + behavior +
        findings reports                                  commit phase3.25 step8
Step 9  Final audit + handoff + open PR #30               commit phase3.25 step9
```

Push after every successful step.

## Branch / PR plan

```text
branch:  campaign/phase3-25-osmotic-learning-live-test
base:    campaign/phase3-24-worldlet-feedback-bridge  (PR #29 open)
PR:      #30  phase3.25: osmotic learning live test
```

Do not merge anything. Retarget only if the base stack lands and the
retarget is safe.

## Hard non-claim boundary (recap)

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like understanding, real agency, will, desire,
  belief, intent, introspection, metacognition.
- No new aggregate scalar field (no "consciousness score", no
  "learning score", no "osmotic absorption score", no "I-ness
  score").
- No reply text uses the language of imbibing, soaking,
  absorption, intuition, insight, awareness, or subjective access.
- The osmotic probe runner is **deterministic and OFFLINE**: zero
  real model calls, zero cache writes, zero forbidden-term hits.

## Acceptance criteria

Phase 3.25 succeeds only when every criterion in
`docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LIVE_TEST_SPEC.md` is met,
the runner is green, the benchmark A1..A12 is green (1 known WARN
A3.04 carried forward at most), gate_runner is 5 / 5 PASS, branch is
pushed, and PR #30 is open.
