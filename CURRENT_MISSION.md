# CURRENT_MISSION.md — Phase 3.23 Dispatch Tracer Wiring (COMPLETE)

> Phase 3.23 Dispatch Tracer Wiring is COMPLETE on the
> `campaign/phase3-23-dispatch-tracer` branch. PR #28 should be
> opened with base `campaign/phase3-22-agent-communication-loop` and
> head `campaign/phase3-23-dispatch-tracer`. PR #27 and the rest of
> the upstream stack remain open. The original Phase 3.23 mission
> text follows so the runner contract stays reproducible.

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.23 Dispatch Tracer Wiring** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.23 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning evidence
+ reasoning trace (Phases 3.18 - 3.22b)
```

toward:

```text
operator-facing agent communication loop with bounded dispatch trace +
learning evidence + reasoning trace; every public OperatorSession.dispatch
route is structurally inspectable from outside the call, and the resulting
trace is cited by the reasoning trace and learning evidence without
changing existing semantics.
```

Allowed claim shape:

```text
"ToyI's runtime now produces a bounded deterministic dispatch trace for
every OperatorSession.dispatch call. The trace is a structural audit
artifact: it records command kind, route label, pre/post substrate
facts, mutation classification, autosave consideration, and resource
audit outcome. It is externally inspectable, deterministic across equal
sessions, and cite-able from the reasoning trace and learning evidence
ledger. This is a behavioral property of the substrate -- never a claim
of cognition, sentience, agency, will, intent, introspection, or
understanding."
```

Forbidden claim shape:

```text
"ToyI is conscious / sentient / aware / understands / has a self /
has agency / has desires / has intent / introspects / has metacognition
/ has subjective experience / has qualia / experiences / decides /
adjudicates truth."
```

"Dispatch trace" is engineering shorthand for "explicit bounded audit
record of the public dispatch route and structural effects". It is NOT
a claim of cognitive agency, sentience, or understanding. If asked "are
you conscious / sentient / aware?", the runtime's deterministic reply
must DENY actual consciousness and describe itself as a bounded
structural runtime that emits a dispatch trace.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_23_DISPATCH_TRACER_ROADMAP.md
docs/campaigns/phase3_23/PHASE3_23_DISPATCH_TRACER_SYNTHESIS.md
docs/campaigns/phase3_23/PHASE3_23_DISPATCH_TRACE_SPEC.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/ui/session.py
brain/ui/commands.py
brain/development/agent_loop.py
brain/development/agent_benchmark.py
brain/development/reasoning_trace.py
brain/development/learning_evidence.py
brain/development/abstract_pattern.py
brain/development/agent_repl_bridge.py
brain/tick.py
brain/invariants.py
tools/catalog.py
tools/check_all.sh
docs/campaigns/phase3_22/PHASE3_22B_LEARNING_PROOF_REPORT.md
docs/campaigns/phase3_22/PHASE3_22B_REASONING_TRACE_REPORT.md
docs/campaigns/phase3_22/PHASE3_22B_AUDIT.md
docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_AUDIT.md
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
- PR #27 is merged or closed (then retarget before continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.31 expectations at start, or v0.32
  expectations after Step 6.

Stop at Phase 3.23 acceptance (every criterion in
`PHASE3_23_DISPATCH_TRACER_ROADMAP.md` is satisfied), open PR #28
(base `campaign/phase3-22-agent-communication-loop`, head
`campaign/phase3-23-dispatch-tracer`), and update
`PHASE3_HANDOFF_STATE.md`.
