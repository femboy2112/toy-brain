# CURRENT_MISSION.md — Phase 3.24 Worldlet Feedback Bridge

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.24 Worldlet Feedback Bridge** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.24 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning evidence,
reasoning trace, and dispatch trace; processing-window feedback supports
OFF / PATTERN_LEDGER / COHERENCE / PATTERN_AND_COHERENCE
```

toward:

```text
operator-facing agent communication loop where the processing-window
feedback architecture has a fifth path: a bounded session-local
worldlet-summary chunk that re-enters the same internal STREAM_APPEND
seam used today by pledger_summary and cohmon_summary, with the
Dispatch Trace recording feedback_mode=worldlet and the worldlet-summary
route, the Reasoning Trace citing a CHECK_WORLDLET_FEEDBACK step before
EMIT_REPLY, and the Learning Evidence ledger citing a
WORLDLET_FEEDBACK_RECORDED record. Existing OFF / PATTERN_LEDGER /
COHERENCE / PATTERN_AND_COHERENCE behavior is preserved bit-identically.
```

Allowed claim shape:

```text
"ToyI's runtime can append a bounded deterministic worldlet-summary
chunk to its session-local stream after each rehearsal under
feedback_mode=WORLDLET (or PATTERN_COHERENCE_WORLDLET). The summary
encodes only bounded printable structural facts about the Minimal
Worldlet substrate (state id, attempt / response counts, accepted /
pushback counts, latest reason). The Pattern Ledger observes the
chunk; the Dispatch Trace records the worldlet-feedback route; the
Reasoning Trace cites a CHECK_WORLDLET_FEEDBACK step; the Learning
Evidence ledger cites a WORLDLET_FEEDBACK_RECORDED record. This is a
behavioral property of the substrate -- never a claim of perception,
understanding, consciousness, sentience, agency, will, desire, belief,
intent, introspection, or metacognition."
```

Forbidden claim shape:

```text
"ToyI perceives the external world / has a body / has senses /
understands meaning / is conscious / is sentient / is aware / has
agency / has will / has desire / introspects / has metacognition."
```

If asked whether ToyI has a world / is conscious / sentient / aware,
the runtime's deterministic reply must DENY the cognitive claim and
describe itself as a bounded structural runtime that emits a
worldlet-summary chunk.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_24_WORLDLET_FEEDBACK_BRIDGE_ROADMAP.md
docs/campaigns/phase3_24/PHASE3_24_WORLDLET_SUBSTRATE_SURVEY.md
docs/campaigns/phase3_24/PHASE3_24_WORLDLET_FEEDBACK_SYNTHESIS.md
docs/campaigns/phase3_24/PHASE3_24_WORLDLET_FEEDBACK_SPEC.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/worldlet.py
brain/development/processing_window.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/development/agent_loop.py
brain/development/agent_benchmark.py
brain/development/learning_evidence.py
brain/development/reasoning_trace.py
brain/development/dispatch_tracer.py
brain/development/abstract_pattern.py
brain/development/agent_repl_bridge.py
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
- PR #28 is merged or closed before Phase 3.24 lands (then retarget
  before continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.32 expectations at start, or v0.33
  expectations after Step 6.

Stop at Phase 3.24 acceptance (every criterion in
`PHASE3_24_WORLDLET_FEEDBACK_BRIDGE_ROADMAP.md` is satisfied), open PR
#29 (base `campaign/phase3-23-dispatch-tracer`, head
`campaign/phase3-24-worldlet-feedback-bridge`), and update
`PHASE3_HANDOFF_STATE.md`.
