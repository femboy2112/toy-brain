# CURRENT_MISSION.md — Phase 3.26 Active Hypothesis + Self-Directed Probe Loop

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.26 Active Hypothesis + Self-Directed Probe Loop**
campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.26 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning
evidence, reasoning trace, dispatch trace, worldlet feedback, and a
deterministic OFFLINE osmotic-imprinting live-test runner (Phases
3.18 - 3.25)
```

toward:

```text
operator-facing agent communication loop where a deterministic
OFFLINE active-hypothesis live-test runner probes whether the existing
substrate can (a) enumerate a bounded set of structural hypotheses
about a deliberately ambiguous input, (b) select a safe internal
probe per hypothesis without leaking expected outcomes into the
runtime path, (c) execute the probe via the existing
`run_agent_interaction_step` route so that learning / reasoning /
dispatch / worldlet surfaces fire as usual, (d) prune falsified
hypotheses, (e) decline to overclaim a winner when all hypotheses
are falsified, and (f) reuse a previously surviving hypothesis on a
second visit to the same ambiguous input without re-probing. The
runner produces a bounded report whose verdict is verifiable by a
closed-criterion benchmark axis A13 and a row family I-AHYP-01..14,
with zero real model calls, zero cache writes, zero forbidden-term
hits, false_positive_count == 0, false_negative_count == 0, and a
deterministic report digest.
```

Allowed claim shape:

```text
"ToyI's runtime can exhibit operational active hypothesis + probe
behavior: given a bounded ambiguous structural input, the runtime
enumerates a bounded candidate set, derives one safe internal probe
per candidate from the input itself (no expected-outcome leak),
executes each probe through the existing agent interaction path,
prunes candidates whose probe outcome does not match the candidate's
prediction, declines to nominate a winner when zero candidates
survive, and on a second visit to the same ambiguous input reuses
the surviving record without re-probing. This is an operational
enumeration + falsification + caching effect over bounded structural
records, not a claim of inquiry, deduction, deliberation,
investigation, curiosity, motivation, agency, intent, will,
introspection, metacognition, or any cognitive process. ToyI is not
conscious, sentient, aware, intentional, or in possession of
subjective access; the runtime is a bounded structural state
machine; active-hypothesis probing in ToyI is a substrate-level
engineering analogue."
```

Forbidden claim shape:

```text
"ToyI thinks / wonders / decides / investigates / inquires /
deliberates / hypothesizes (in the cognitive sense) / asks itself /
is curious / wants to know / chooses to probe / introspects /
plans / reasons (in the cognitive sense) / understands what it is
probing."
```

If asked whether ToyI is conscious / sentient / aware / understands
/ has agency / has intuition / has curiosity / decides / wonders, the
runtime's deterministic reply must DENY the cognitive claim and
describe itself as a bounded structural runtime.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_26_ACTIVE_HYPOTHESIS_PROBE_ROADMAP.md
docs/campaigns/phase3_26/PHASE3_26_ACTIVE_HYPOTHESIS_TEST_DESIGN.md
docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LEARNING_TEST_DESIGN.md
docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LIVE_TEST_PROOF_REPORT.md
docs/campaigns/phase3_25/PHASE3_25_AUDIT.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/active_hypothesis_probe.py
brain/development/osmotic_learning_probe.py
brain/development/agent_loop.py
brain/development/agent_benchmark.py
brain/development/learning_evidence.py
brain/development/reasoning_trace.py
brain/development/dispatch_tracer.py
brain/development/abstract_pattern.py
brain/development/processing_window.py
brain/development/worldlet.py
brain/development/coherence_monitor.py
brain/tick.py
brain/invariants.py
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
- branch is wrong;
- PR #30 is merged or closed before Phase 3.26 lands (then retarget
  before continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.34 expectations at start, or v0.35
  expectations after Step 7.

Stop at Phase 3.26 acceptance (every criterion in
`PHASE3_26_ACTIVE_HYPOTHESIS_PROBE_ROADMAP.md` is satisfied), open PR
#31 (base `campaign/phase3-25-osmotic-learning-live-test`, head
`campaign/phase3-26-active-hypothesis-probe`), and update
`PHASE3_HANDOFF_STATE.md`.
