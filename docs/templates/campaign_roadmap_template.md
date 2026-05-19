# PHASE3_NN_<CAMPAIGN_NAME>_ROADMAP.md

<!--
USAGE: copy this template to PHASE3_NN_<CAMPAIGN_NAME>_ROADMAP.md
where NN is the phase number and CAMPAIGN_NAME is in SCREAMING_SNAKE_CASE.

Fill in every <<<...>>> placeholder. Delete or expand sections as the
campaign's scope demands. Match the structural shape of the
PHASE3_32 .. PHASE3_35 roadmaps in this bundle.
-->

## Thesis

<<<One paragraph: what is this campaign's single thesis? What changes
in the repo as a result? What does NOT change? Keep to ~5 sentences.>>>

## Branch

```text
phase3_NN/<axis-or-feature-lowercase-hyphenated>
```

## Locked decision references

This campaign honors:

```text
ADR-001-locked-decisions-D1-D8  (D<list relevant D-numbers>)
ADR-<other relevant ADRs>
```

Do not relitigate locked decisions inside this campaign. If new
evidence demands revisiting, open a successor ADR before proceeding.

## Non-claim discipline (mandatory)

This section is REQUIRED for every campaign. The text below is
boilerplate and must appear verbatim (or near-verbatim) in every
campaign roadmap.

- ToyI is a bounded structural state machine. No claim or implication
  of consciousness, sentience, agency, intentionality, qualia, language,
  understanding, "real" cognition, or LLM-like emergence.
- No aggregate scalar across axes (no "developmental quotient",
  "I-ness score", or similar).
- The forbidden vocabulary list (ADR-006) applies to every produced
  string.
- 0 real model calls. All probes are OFFLINE and deterministic.
- The closed-rule weight table is not relaxed.
- "Training" is forbidden vocabulary; use "consolidation" or
  "progression".

## TARGET_AXES (per ADR-004)

```text
TARGET_AXES = {
    <<<list the axes this campaign targets, or empty if diagnostic-only>>>
}

NON_TARGET_AXES = (every other DevelopmentalAxis)

Regression gate: every NON_TARGET axis's band assignment must be
UNCHANGED across the campaign's baseline → post-campaign comparison.
The TARGET_AXES are permitted to move (and SHOULD move per the
acceptance criteria).
```

## Acceptance criteria

The campaign is complete and mergeable when ALL of these hold:

1. <<<Concrete acceptance condition 1. Cite a benchmark axis case if
      possible.>>>
2. <<<Concrete acceptance condition 2.>>>
3. ...
N. The regression gate passes: NON_TARGET_AXES are unchanged.
N+1. The catalog rows added by this campaign are present and the
      catalog validity check passes.
N+2. The Phase 3.NN benchmark axis (if introduced) is green.
N+3. The static-audit fixture (if introduced) passes.
N+4. Every test in `tests/` passes.

## Step ledger

Steps are sequential unless explicitly marked PARALLEL. Each step is
one commit.

### Step 1: <<<Step title>>>

<<<What this step does. ~3 sentences. What files are touched. What
the test that validates it is.>>>

```bash
<<<Concrete bash commands or test invocations>>>
```

### Step 2: <<<Step title>>>

...

### Step N: <<<final step (usually "drop in catalog rows and PR")>>>

...

## Hard limits

- <<<List campaign-specific hard limits. Examples follow:>>>
- No probe behavior change (for diagnostic-only campaigns).
- No catalog row demoted from REQUIRED to STRUCTURAL.
- No `time`, `random`, or other nondeterministic source introduced.
- No new LLM call (real or simulated).
- No widening of TARGET_AXES once the campaign has started (such
  widening requires re-authorizing the campaign).
- Catalog row count for this campaign: <<<N>>> rows
  (<<<X>>> REQUIRED, <<<Y>>> STRUCTURAL).

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| <<<Risk 1>>> | <<<Mitigation 1>>> |
| <<<Risk 2>>> | <<<Mitigation 2>>> |
| ... | ... |

## Cross-references

```text
Companion design docs:
  docs/campaigns/phase3_NN/PHASE3_NN_DESIGN.md
  docs/campaigns/phase3_NN/<other phase-specific docs>

Locked decisions:
  ADR-001-locked-decisions-D1-D8.md
  ADR-<related>.md

Predecessor campaign roadmap:
  PHASE3_<N-1>_*_ROADMAP.md

Next-step pointer:
  CURRENT_MISSION_phase3_NN.md
  CURRENT_CAMPAIGN_phase3_NN.md
```

## Next step (after merge)

<<<What is the next campaign? Reference its roadmap by filename. If
the campaign sequence is fluid, reference the
`/next-campaign` slash command + the planner agent's role.>>>
