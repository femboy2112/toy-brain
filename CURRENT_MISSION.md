# CURRENT_MISSION.md — Phase 3.22 Agent Communication Loop

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read
this file, read `CURRENT_CAMPAIGN.md`, create or continue the active
campaign branch, run the next eligible campaign step, commit successful
results, push the branch, and stop exactly where the campaign says to
stop.

---

## Current mission

Execute the **Phase 3.22 Agent Communication Loop + Behavioral
Indistinguishability Harness** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.22 follows the completed Phase 3.21 Developmental Trajectory
campaign (PR #26 open against `campaign/phase3-20-coherence-feedback-bridge`
at campaign start; stacked on PR #24 / #25). Phase 3.21 shipped:

- `brain/development/milestone_harness.py` (closed harness over
  Phase 3.18-3.20 surfaces),
- `DevelopmentalMilestone` / `MilestoneStatus` / `MilestoneResult`
  closed enums + record,
- ten deterministic per-milestone helpers plus `run_all_milestones()`,
- catalog v0.28 -> v0.29 with `I-DEVMILE-01..11`,
- zero real model calls; `brain/tick.py` untouched.

Phase 3.22 takes the next bounded operational question:

> Can ToyI's runtime exhibit a coherent, deterministic, operator-
> facing **agent communication loop** -- where operator input routes
> through the existing stream / pattern / coherence / growth / REPL
> substrates and emits bounded operator-facing replies that, under a
> closed deterministic benchmark battery, satisfy a "mild-agent-like
> at the bounded behavior level" criterion -- WITHOUT touching
> `brain/tick.py`, the LLM, the parser, the cache, the schema, or
> any consciousness-adjacent boundary, and WITHOUT claiming actual
> consciousness, sentience, agency, or understanding?

Phase 3.22 takes ToyI from:

```text
ten-milestone deterministic developmental trajectory (Phases 3.0-3.21)
```

toward:

```text
operator-facing agent communication loop:
  operator input ->
    STREAM_APPEND / Pattern Ledger / Coherence Monitor /
      Growth Ledger / Proto-BASIC REPL routing ->
        bounded operator-facing reply (deterministic, non-claim-clean)
```

Allowed claim shape:

```text
"ToyI's runtime supports a bounded deterministic agent communication
loop: operator input routes through the existing public surfaces and
emits bounded operator-facing replies that carry pattern observation,
REPL result, coherence status, limitation disclosure, and next-action
suggestion. Under the Phase 3.22 closed deterministic benchmark
battery the loop is 'mild-agent-like at the bounded behavior level'
(deterministic, pattern-recognizing, near-miss-correcting,
session-continuity-preserving, consciousness-claim-refusing). This is
a behavioral property of the substrate -- never a claim of actual
cognition, semantic understanding, agency, or selfhood."
```

Forbidden claim shape:

```text
"ToyI is conscious / sentient / aware / understands / has a self /
has agency / has desires / has intent / introspects / has metacognition
/ has subjective experience / has qualia / experiences / matures /
adjudicates truth."
```

The word "agent" is used throughout in the **engineering** sense
("operator-facing agent loop", "bounded agent reply") -- never in
the cognitive-agent or moral-agent sense. If asked "are you
conscious / sentient / aware?", the runtime's deterministic reply
must DENY actual consciousness and describe itself as a bounded
structural runtime.

Campaign target:

```text
Phase 3.22 Step 1   Mission sync + roadmap + handoff state
Phase 3.22 Step 2   Benchmark spec + design locks
Phase 3.22 Step 3   REPL bridge pure helpers
Phase 3.22 Step 4   Agent loop / communication module
Phase 3.22 Step 5   Pattern recognition benchmark battery
Phase 3.22 Step 6   Coherence variation probe (Phase 3.21 W3 follow-up)
Phase 3.22 Step 7   Benchmark runner + transcript generator
Phase 3.22 Step 8   Run + iterate until PASS or documented blocker
Phase 3.22 Step 9   Catalog reconciliation + canonical gates
Phase 3.22 Step 10  Behavior report + findings + final audit
Phase 3.22 Step 11  PR preparation
```

Intended result:

```text
A small reviewed runtime addition:
  - brain/development/agent_repl_bridge.py (pure REPL-bridge helpers
    over brain/development/repl.py; no UI command added)
  - brain/development/agent_loop.py (closed bounded agent-input ->
    agent-reply integration over existing public surfaces; no LLM
    import; no tick import beyond BrainState / initial_state /
    assert_state_invariants)
  - brain/development/agent_benchmark.py (closed deterministic
    benchmark battery + runner module)
A new catalog row family I-AGENTLOOP-01..11 (9 REQUIRED + 2
STRUCTURAL) at catalog v0.29 -> v0.30. Eleven new fixtures driving
the row family. brain/tick.py untouched; LLM unused; cache untouched;
OFFLINE default preserved; no consciousness-adjacent claim. The
deterministic benchmark passes every axis OR documents the exact safe
subset and blocker for the coherence-status-variation axis (Phase 3.21
W3 follow-up).
```

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-22-agent-communication-loop
```

If Phase 3.21 PR #26 has not yet merged at campaign start, the
Phase 3.22 branch is **stacked** on the current Phase 3.21 HEAD and
the final PR targets `campaign/phase3-21-developmental-trajectory`.
If PR #24 + PR #25 + PR #26 all merge during the campaign, the final
PR retargets to `main` before final PR preparation.

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into the correct base at campaign completion
never merge the PR without explicit user approval
never edit brain/tick.py in Phase 3.22
never edit brain/llm/** in Phase 3.22
```

---

## Baseline to verify

Expected current baseline (must match before any step runs):

```text
Catalog: v0.29 (Phase 3.21 Step 6 landed)
Counts:
  REQUIRED:        294
  STRUCTURAL:       92
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.21 Developmental Trajectory
                              (PR #26 open against Phase 3.20 branch)
Current mission:              Phase 3.22 Agent Communication Loop
Next eligible step:           Step 2 benchmark spec + design locks
                              (after Step 1 commits/pushes)
```

Stop if catalog counts disagree.

---

## Required source files to read first

Read these before doing campaign work:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
PHASE3_22_AGENT_COMMUNICATION_LOOP_ROADMAP.md
PHASE3_HANDOFF_STATE.md
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_AUDIT.md
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_FINDINGS.md
docs/campaigns/phase3_21/PHASE3_21_MILESTONE_LOG.md
docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_BEHAVIOR_REPORT.md
brain/development/milestone_harness.py
brain/development/processing_window.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/development/repl.py
brain/ui/session.py
brain/ui/commands.py
brain/tick.py
brain/llm/client.py
brain/llm/ptcns_backed.py
tools/claude_helpers/gate_runner.py
tools/catalog.py
tools/check_all.sh
lean_reference/TLICA.lean
lean_reference/TLICA/
```

Then read whichever files the next campaign step names.

---

## Phase 3.22 architectural guardrails

Preserve these constraints throughout Phase 3.22:

```text
no consciousness / sentience / subjective / semantic / truth /
  agency / self-modification / introspection / metacognition /
  desire / will / belief / understanding claim
no claim that ToyI is an "agent" in the cognitive / moral sense
  (operational use only -- "agent loop" is engineering shorthand)
no aggregate consciousness / sentience / awareness / I-ness /
  growth / maturity / capability / mild-agent / score
no SelfModel implementation
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no model-backed default behavior; OFFLINE remains the default
no hidden LLM calls
no silent network/model calls
no silent repair calls
no DB schema change
no SCHEMA_VERSION bump
no persistence / autosave runtime change
no tick semantic change (brain/tick.py untouched)
no L1 cache semantic change
no L2 (eval_v1) semantic change
no parser change
no prompt change
no UI verb addition; no OperatorCommand member added; no
  ACTIVE_VIEWS member added
no /save-session / /load-session / autosave extension
no raw prompts / responses / cache files / secrets committed
no Stage C.1 broad repo edits
no unbounded loops; no unbounded state growth
no new GrowthEventType or GrowthEventSource
the deterministic agent benchmark consumes 0 real model calls
the agent communication module must NOT import brain.llm.*
the agent communication module must NOT import or call
  brain.tick.tick (only BrainState / initial_state /
  assert_state_invariants are allowed)
PASS / WARN / FAIL / NOT_APPLICABLE remain structural statuses
the TLICA Lean spec in lean_reference/ remains authoritative;
  any new catalog row is Engineering hypothesis and must not
  contradict any existing REQUIRED row
```

Real model-call budget for the entire campaign:

```text
Max 20 real external model-backed calls total.
Phase 3.22 expects to consume ZERO real model calls because every
  benchmark case uses STREAM_APPEND + pure REPL helpers only.
Stop before exceeding 20.
```

---

## ChatGPT/Codex consultation (Stage A, Stage B, and Stage C.1)

Same as Phase 3.21:

- Stage A (PR #13) read-only, advisory.
- Stage B (PR #15) limited-write, allowlist-based, sequential.
- Stage C.1 (PR #19) dynamic-flow, allowlist-based, max two active
  Codex nodes, no automatic retry, hard cap 8 nodes.
  **For Phase 3.22, max total Stage C.1 real Codex nodes = 5
  unless operator approves more.**

Good candidates for parallel shards (when efficiency clearly wins):

```text
- agent_repl_bridge.py + its fixture
- agent_benchmark.py runner + transcript report
- docs synthesis + benchmark spec
```

Keep write sets disjoint. Parent Claude owns design, integration,
validation, commits, pushes, PR.

---

## Workflow tools

Same as Phase 3.21.

---

## Command rule

Use `python3 -m ...` for Python module commands. Do not run real
LLM scenario commands unless the user explicitly asks.

---

## Final report format (per step)

Same as Phase 3.21 (preserved unchanged).
