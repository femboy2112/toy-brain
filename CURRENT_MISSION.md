# CURRENT_MISSION.md — Phase 3.30 Curriculum Consolidation Live Test

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.30 Curriculum Consolidation Live Test**
campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.30 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning
evidence, reasoning trace, dispatch trace, worldlet feedback, a
deterministic OFFLINE osmotic-imprinting live-test runner, and a
deterministic OFFLINE active-hypothesis live-test runner (Phases
3.18 - 3.26)
```

toward:

```text
operator-facing agent communication loop where a deterministic
OFFLINE curriculum-consolidation live-test runner probes whether
the existing substrate can (a) accept a bounded ordered curriculum
of structural exposures, (b) admit each exposure into a bounded
session-local slate under a closed admission rule, (c) reject
admission on digest collision without overwriting the first record,
(d) evict the least-recently-accessed record once the slate
capacity is exceeded, (e) on a later probe whose digest matches a
surviving record return the prior admitted record (without
fabricating reuse for novel inputs), and (f) emit a complete
audit trail tagging every exposure as SURVIVED, DECAYED, or
REJECTED. The runner produces a bounded report whose verdict is
verifiable by a closed-criterion benchmark axis A14 and a row
family I-CURR-01..14, with zero real model calls, zero cache
writes, zero forbidden-term hits, false_positive_count == 0,
false_negative_count == 0, and a deterministic report digest.
```

Allowed claim shape:

```text
"ToyI's runtime can exhibit operational curriculum consolidation
behavior: given a bounded ordered tuple of structural exposures
and a bounded session-local slate, the runtime admits each
exposure into the slate under a closed admission rule, rejects
duplicates without overwriting the first record, evicts the
least-recently-accessed record once the slate capacity is
exceeded, on a later probe whose digest matches a surviving
record returns the prior admitted record without re-admitting,
declines to fabricate reuse for probes whose digest is novel,
and emits an audit trail tagging every exposure as SURVIVED,
DECAYED, or REJECTED. This is an operational accumulation +
slate-bounded LRU eviction + caching effect over bounded
structural records, not a claim of learning, memory,
forgetting, re-learning, consolidation, deliberation,
investigation, curiosity, motivation, agency, intent, will,
introspection, metacognition, or any cognitive process. ToyI is
not conscious, sentient, aware, intentional, or in possession of
subjective access; the runtime is a bounded structural state
machine; curriculum consolidation in ToyI is a substrate-level
engineering analogue."
```

Forbidden claim shape:

```text
"ToyI learns / remembers / forgets / re-learns / consolidates
(in the cognitive sense) / accumulates knowledge / experiences
interference / experiences decay / engages in deliberation /
deliberates which record to keep / chooses to forget / is curious
about older inputs / wants to consolidate / introspects its
slate."
```

If asked whether ToyI is conscious / sentient / aware / understands
/ has agency / has intuition / has memory / has knowledge /
remembers / forgets, the runtime's deterministic reply must DENY
the cognitive claim and describe itself as a bounded structural
runtime.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_30_CURRICULUM_CONSOLIDATION_ROADMAP.md
docs/campaigns/phase3_30/PHASE3_30_CURRICULUM_CONSOLIDATION_TEST_DESIGN.md
docs/campaigns/phase3_26/PHASE3_26_ACTIVE_HYPOTHESIS_TEST_DESIGN.md
docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LEARNING_TEST_DESIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/curriculum_consolidation_probe.py
brain/development/active_hypothesis_probe.py
brain/development/osmotic_learning_probe.py
brain/development/agent_loop.py
brain/development/agent_benchmark.py
brain/development/learning_evidence.py
brain/development/reasoning_trace.py
brain/development/dispatch_tracer.py
brain/development/abstract_pattern.py
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
- PR #31 is merged or closed before Phase 3.30 lands (then retarget
  before continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.35 expectations at start, or v0.36
  expectations after Step 7.

Stop at Phase 3.30 acceptance (every criterion in
`PHASE3_30_CURRICULUM_CONSOLIDATION_ROADMAP.md` is satisfied), open
PR #32 (base `campaign/phase3-26-active-hypothesis-probe`, head
`campaign/phase3-30-curriculum-consolidation`), and update
`PHASE3_HANDOFF_STATE.md`.
