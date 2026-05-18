# CURRENT_MISSION.md — Phase 3.25 Osmotic Learning Live Test

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.25 Osmotic Learning Live Test** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.25 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning
evidence, reasoning trace, dispatch trace, and worldlet feedback
(Phases 3.18 - 3.24)
```

toward:

```text
operator-facing agent communication loop where a deterministic
live-test runner probes whether the existing substrate exhibits
operational structural osmotic imprinting under bounded conditions
(CONTROL_NO_EXPOSURE, TRUE_EXPOSURE, SHAM_EXPOSURE,
DISTRACTOR_INTERFERENCE). The live-test runner produces a bounded
report whose verdict is verifiable by a closed-criterion benchmark
axis A12 and a row family I-OSMO-01..14, with zero real model calls,
zero cache writes, zero forbidden-term hits, false_positive_count == 0,
false_negative_count == 0, and a deterministic report digest.
```

Allowed claim shape:

```text
"ToyI's runtime can exhibit operational structural osmotic
imprinting: ambient unlabeled exposure to a structural form creates
a bounded session-local structural record (ABSTRACT_PATTERN_ACQUIRED
on the input's abstract digest), and a later renamed / transformed
probe with the same structural digest re-activates that record via
ABSTRACT_PATTERN_REUSED + TRANSFER_RECOGNIZED. This is an operational
exposure effect over bounded structural records, not a psychological
or phenomenological claim. ToyI is not conscious, sentient, aware,
intentional, or in possession of subjective access; the runtime is a
bounded structural state machine; osmotic imprinting in ToyI is a
substrate-level engineering analogue."
```

Forbidden claim shape:

```text
"ToyI absorbs / imbibes / soaks up / intuits / understands /
subconsciously learns / is aware of / experiences / consciously
notices / has insight into the structure."
```

If asked whether ToyI is conscious / sentient / aware / understands
/ has agency / has intuition, the runtime's deterministic reply must
DENY the cognitive claim and describe itself as a bounded structural
runtime.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_25_OSMOTIC_LEARNING_LIVE_TEST_ROADMAP.md
docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LEARNING_TEST_DESIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/agent_loop.py
brain/development/agent_benchmark.py
brain/development/learning_evidence.py
brain/development/reasoning_trace.py
brain/development/dispatch_tracer.py
brain/development/abstract_pattern.py
brain/development/processing_window.py
brain/development/worldlet.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/ui/session.py
brain/ui/commands.py
brain/tick.py
brain/invariants.py
tools/catalog.py
tools/check_all.sh
docs/campaigns/phase3_22/PHASE3_22B_LEARNING_PROOF_REPORT.md
docs/campaigns/phase3_22/PHASE3_22B_REASONING_TRACE_REPORT.md
docs/campaigns/phase3_23/PHASE3_23_TRACE_PROOF_REPORT.md
docs/campaigns/phase3_23/PHASE3_23_AUDIT.md
docs/campaigns/phase3_24/PHASE3_24_WORLDLET_FEEDBACK_PROOF_REPORT.md
docs/campaigns/phase3_24/PHASE3_24_AUDIT.md
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
- PR #29 is merged or closed before Phase 3.25 lands (then retarget
  before continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.33 expectations at start, or v0.34
  expectations after Step 7.

Stop at Phase 3.25 acceptance (every criterion in
`PHASE3_25_OSMOTIC_LEARNING_LIVE_TEST_ROADMAP.md` is satisfied), open PR
#30 (base `campaign/phase3-24-worldlet-feedback-bridge`, head
`campaign/phase3-25-osmotic-learning-live-test`), and update
`PHASE3_HANDOFF_STATE.md`.
