# CURRENT_MISSION.md — Phase 3.32 Mainline Reconciliation

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, run the next eligible
campaign step, commit successful results, push the branch, and stop
exactly where the campaign says to stop.

---

## Current mission

Execute the **Phase 3.32 Mainline Reconciliation** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.32 takes the repo from:

```text
main is stale at Phase 3.19 / catalog v0.27, while the completed
campaign stack (Phases 3.20 .. 3.31) has landed via stacked PRs
that merged into prior campaign branches instead of into main.
The latest stack tip is campaign/phase3-30-curriculum-consolidation
which, after PR #33 was merged on 2026-05-19, contains the full
Phase 3.31 caregiver-scaffolded proto-speech work and catalog
v0.37.
```

toward:

```text
main contains everything through Phase 3.31 / catalog v0.37, via
a single reconciliation PR opened from
campaign/phase3-32-mainline-reconciliation. The reconciliation
branch is cut from main and merges
origin/campaign/phase3-30-curriculum-consolidation. All canonical
gates pass; benchmark is 137 total / 136 PASS / 1 WARN (A3.04
carry-over) / 0 FAIL; proto-speech live-test is 10/10 PASS;
invariants are fully green; gate_runner reports 5/5 PASS; real
model calls are 0; cache writes are 0; forbidden-term hits are 0.
README / INVARIANT_CATALOG / tools/catalog.py / brain/_catalog_ids.py
align on v0.37; PHASE3_HANDOFF_STATE.md and the current mission /
campaign docs no longer point future work at stale branch
assumptions.
```

Allowed claim shape:

```text
"Phase 3.32 is a reconciliation / stabilization campaign. It
brings main current with the completed campaign stack through
Phase 3.31. It introduces no new runtime features, no new
catalog rows, no new fixtures, and no theory-semantics changes.
Non-claim discipline is preserved: every prior cognitive-claim
guardrail (no consciousness, sentience, awareness, subjective
experience, language understanding, inner speech, private
thought, agency, will, desire, belief, intent, introspection,
metacognition, curiosity, or deliberation claims) carries forward
unchanged."
```

Forbidden claim shape:

```text
"Phase 3.32 starts new behavioral feature work / modifies theory
semantics / weakens any cognitive-claim guardrail / merges the
reconciliation PR automatically."
```

If asked whether ToyI is conscious / sentient / aware / understands
language / talks / has inner speech / has private thought, the
runtime's deterministic reply must DENY the cognitive claim and
describe itself as a bounded structural runtime — unchanged from
Phase 3.31.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md
docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_PROOF_REPORT.md
docs/campaigns/phase3_31/PHASE3_31_AUDIT.md
brain/development/proto_speech_acquisition.py
brain/_catalog_ids.py
tools/catalog.py
tools/check_all.sh
```

---

## Local command rule

Use `python3 -m ...` for Python module commands. Do not run real LLM
scenario commands unless the user explicitly asks.

---

## Stop conditions

Stop and report if:

- worktree is dirty before changes;
- main does not exist or cannot be fast-forwarded;
- the campaign source branch
  `campaign/phase3-30-curriculum-consolidation` does not contain
  Phase 3.31 artifacts (proto_speech_acquisition.py,
  docs/campaigns/phase3_31/, catalog v0.37);
- merge produces conflicts the campaign rules do not authorize
  resolving;
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.37 expectations;
- any new behavioral feature would be required to make a gate pass.

Stop at Phase 3.32 acceptance (every criterion in
`CURRENT_CAMPAIGN.md` is satisfied), open the reconciliation PR
(head `campaign/phase3-32-mainline-reconciliation`, base `main`),
update `PHASE3_HANDOFF_STATE.md`, and wait for the operator to
merge the PR manually.
