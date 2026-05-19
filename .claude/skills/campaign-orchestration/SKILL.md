---
name: campaign-orchestration
description: Reason about the sequence of Phase 3.32 through Phase 3.35+ campaigns - what each campaign accomplishes, what locked decisions D1-D8 apply, how to dynamically choose the next campaign based on test results, when to start a new conversation vs continue. Use this skill whenever planning or executing a campaign in the developmental progression track, switching between campaigns, or deciding what campaign to run next. Triggered by "phase 3.32", "phase 3.33", "phase 3.34", "phase 3.35", "next campaign", "campaign sequence", "drop in bundle", "ADR-001", "locked decision", "TARGET_AXES", or any reference to campaign-level planning.
---

# campaign-orchestration

## What this skill is for

Orchestrating the sequence of campaigns in the developmental
progression track. Each campaign has a specific role; the role
constrains what can be done in that campaign; mixing roles across
campaigns is forbidden.

## The four-campaign sequence

```text
Phase 3.32  Mainline Reconciliation + ProbeReport protocol
            Role: clean up the PR stack; freeze a probe-report contract.
            No probe behavior changes. No measurement changes.

Phase 3.33  Proto-Speech Strict Combination Corrigendum + Strictness Audit
            Role: surface masked capability gaps via strict counters.
            No probe behavior changes. Only report-layer additions.
            Diagnostic only.

Phase 3.34  Developmental Progression Profile + Consolidation Ladder
            Role: build the projector that consumes probe reports.
            No probe behavior changes. The profile is a pure consumer.

Phase 3.35  First Targeted Consolidation
            Role: actually change the substrate. Mechanism chosen by
            the ladder. Other axes must not regress.
            BEHAVIOR CHANGE permitted, scoped to a single axis.
```

## Why this sequence and not another

The instrument-then-measurement-then-intervention discipline:

1. **Phase 3.32** establishes a common protocol for reading reports.
   Without it, Phase 3.34's projector would have to import every
   probe module directly.

2. **Phase 3.33** makes the reports themselves honest. Adding strict
   counters where graceful-pass masking exists ensures Phase 3.34
   reads a true baseline.

3. **Phase 3.34** builds the measurement instrument (the projector).
   It cannot run before 3.33 because it would inflate band
   assignments by reading graceful counters as if they were strict.

4. **Phase 3.35+** intervenes on the substrate. Each intervention is
   scoped to a single axis; the projector verifies no other axis
   regressed.

Any reordering breaks the dependency chain.

## Locked decisions (D1–D8)

See `ADR-001-locked-decisions-D1-D8.md` for full text. The summary:

```text
D1  Phase 3.33 is diagnostic-only.
D2  Bands are generic (B00-B07), not per-axis.
D3  Strict counter pattern is project-wide discipline.
D4  Phase 3.32 lands ProbeReport protocol.
D5  Regression gate uses TARGET_AXES / NON_TARGET_AXES scoping.
D6  Predicate monotonicity is a checked invariant.
D7  NextProgressionTarget is a structured roadmap stub.
D8  Benchmark axis A16 lands with Phase 3.34.
```

Do not relitigate these inside a campaign. If new evidence demands
revisiting, open a successor ADR.

## How to start a campaign

```text
1. cd into the bundle directory.
2. Read this skill, the relevant phase's roadmap, and ADR-001.
3. Drop in the campaign's files per DROP-IN-MANIFEST.md.
4. Read PHASE3_NN_*_ROADMAP.md.
5. Read CURRENT_MISSION_phase3_NN.md (if pre-authored) or update
   CURRENT_MISSION.md / CURRENT_CAMPAIGN.md manually.
6. Run /go.
```

## How to respond to test results dynamically

The bundle's `workflow/DYNAMIC_RESPONSE_TO_TEST_RESULTS.md`
documents the decision trees. Brief summary:

- **A non-target axis dropped a band:** STOP. Investigate the
  regression. Either revert the campaign step or revise the
  campaign's TARGET_AXES (this requires re-authorizing the campaign
  via ADR amendment).

- **A target axis dropped a band:** if expected per the campaign's
  acceptance criteria, OK. If unexpected, STOP.

- **The strict counter audit found a probe with non-disposition-based
  graceful pass:** escalate to operator. Phase 3.33's scope is
  disposition-based; non-disposition-based gracefulness may need a
  follow-up campaign.

- **The predicate monotonicity check failed at import time:** STOP.
  The predicate authoring has a bug. Fix the predicate before
  proceeding.

- **The Phase 3.34 projector's two-run determinism check failed:** STOP.
  Either the projector reads mutable state, or a probe is
  non-deterministic. Investigate the probe first.

## When to start a fresh conversation

Each campaign should run in its own conversation, ideally. The
context required for Phase 3.34 is large (the predicate template
alone is substantial); mixing it with Phase 3.33 context wastes
tokens.

A rough rule:

- One campaign = one conversation, started fresh.
- Within a campaign, each major step that doesn't depend on
  in-context reasoning from a prior step can also be a fresh
  conversation (e.g., the Codex fan-out for predicate authoring).
- See `workflow/CONTEXT_MANAGEMENT_GUIDE.md` for the per-phase seed
  set.

## Bundle drop-in discipline

Don't drop in all four campaigns' files at once. Drop in phase-by-
phase:

```text
NOW:        Permanent files (ADRs, agents, commands, skills, tools)
            + Phase 3.32 files only.
After 3.32: + Phase 3.33 files.
After 3.33: + Phase 3.34 files.
After 3.34: + Phase 3.35 files.
```

The "permanent" files include the ADRs because those are referenced
by every campaign and should not be deleted between campaigns.

## Common mistakes to avoid

- **Trying to "fix" the proto-speech combination gap in Phase 3.33.**
  D1 forbids this. The fix is in Phase 3.35.
- **Trying to combine Phase 3.33 and 3.34 into one campaign.** The
  strict counters must land before the projector reads them. Mixing
  them produces a profile that retroactively re-rates the baseline.
- **Trying to use per-axis bands.** D2 forbids this. Bands are generic.
- **Trying to remove the graceful counter.** D3 says strict counters
  are *additional*; the graceful counter stays.

## Cross-references

- `README.md` — bundle overview.
- `ADR-001-locked-decisions-D1-D8.md` — locked decisions.
- `PHASE3_NN_*_ROADMAP.md` files — campaign specs.
- `workflow/*` — efficiency, parallelization, dynamic response,
  context management, Codex offload.
