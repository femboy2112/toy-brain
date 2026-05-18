# CURRENT_MISSION.md — Phase 3.20 Coherence Feedback Bridge

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read
this file, read `CURRENT_CAMPAIGN.md`, create or continue the active
campaign branch, run the next eligible campaign step, commit successful
results, push the branch, and stop exactly where the campaign says to
stop.

---

## Current mission

Execute the **Phase 3.20 Coherence Feedback Bridge Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.20 follows the completed Phase 3.19 Internal Feedback Loop
Prototype campaign (PR #24, open against `main` at campaign start).
Phase 3.19 demonstrated:

- a new `FeedbackMode` `(str, Enum)` on
  `brain/development/processing_window.py` with members `OFF` and
  `PATTERN_LEDGER`;
- a pure deterministic helper `build_pledger_summary_text` that
  produces the bounded printable template
  `"pledger_summary pattern_id=<id> recurrence=<n>/256 sat=<state>"`;
- a widened `_V1_EMITTED_SOURCES` set that includes
  `InternalEventSource.PLEDGER_SUMMARY`;
- a new optional `OperatorSession.feedback_mode` field that, when
  set to `PATTERN_LEDGER`, drives `_run_processing_window` to emit
  exactly `1 + 2 * N` stream chunks (one operator + N rehearsal + N
  pledger_summary) and produces a second-order Pattern Ledger entry
  whose recurrence climbs independently;
- catalog v0.27 with `I-IFBK-01` / `I-IFBK-02`;
- zero real model calls; `brain/tick.py` untouched.

The third `InternalEventSource` member, `COHMON_SUMMARY`, was
reserved by Phase 3.18 and explicitly **deferred** by Phase 3.19
LOCK F: it remained reserved and continued to raise from
`build_rehearsal_provenance`. Phase 3.20 takes the next bounded
operational question:

> Can ToyI's runtime route a **bounded Coherence Monitor summary
> feedback event**, derived from the live Coherence Monitor report
> observed after a rehearsal, back into the same Pattern Ledger /
> Growth Ledger substrate — without touching `brain/tick.py`, the
> LLM, the parser, the cache, the schema, or any
> consciousness-adjacent boundary, and without breaking the closed
> import discipline that keeps
> `brain/development/processing_window.py` decoupled from
> `brain/development/coherence_monitor.py`?

Phase 3.20 takes ToyI from:

```text
external input -> rehearsal -> pattern-ledger summary feedback
              -> second-order pattern entry
```

toward:

```text
external input -> rehearsal -> pattern-ledger summary feedback
              -> coherence-monitor summary feedback
              -> structural self-monitoring approximation
              -> additional inspectable second-order pattern entries
```

This is an operational architecture campaign for a bounded
**conflict-monitoring-like** loop. It is **NOT** a claim of
consciousness, sentience, subjective experience, true agency, true
selfhood, semantic understanding, truth access, desire/will/intent,
or self-modification in the strong sense.

Allowed claim shape:

```text
"ToyI approximates a coherence-feedback architecture: bounded
deterministic coherence summaries (PASS/WARN/FAIL/NOT_APPLICABLE
structural statuses) can re-enter Pattern Ledger evidence through
the existing STREAM_APPEND helper, producing additional second-order
pattern recurrence without invoking the LLM, the kernel, the cache,
or the schema."
```

Forbidden claim shape:

```text
"ToyI is conscious / sentient / understands / has a self / has
agency / has desires / introspects / knows truth / self-modifies."
```

Campaign target:

```text
Phase 3.20 Step 1   Mission sync + roadmap
Phase 3.20 Step 2   Coherence feedback synthesis
Phase 3.20 Step 3   Coherence feedback probe matrix
Phase 3.20 Step 4   Corrigenda / design locks
Phase 3.20 Step 5   Catalog patch plan
Phase 3.20 Step 6   Review Gate A
Phase 3.20 Step 7   Apply implementation (if gated through)
Phase 3.20 Step 8   Behavior report
Phase 3.20 Step 9   Findings / triage
Phase 3.20 Step 10  Final audit
Phase 3.20 Step 11  PR preparation
```

Intended result:

```text
A small, reviewed runtime extension to
brain/development/processing_window.py and brain/ui/session.py that
emits bounded coherence-summary feedback chunks whose text is a
deterministic summary of the live Coherence Monitor report observed
after the rehearsal. Each accepted feedback chunk is itself a
STREAM_APPEND chunk that drives Pattern Ledger.observe and Growth
Ledger.observe through the existing call sites; no kernel change, no
LLM call, no schema change, no autosave change, no aggregate scalar,
no new GrowthEventType. Coherence Monitor remains read-only and
continues to import OperatorSession; the new bounded-printable
summary helper lives on processing_window.py and accepts only
primitive counts + status values, so processing_window.py still
satisfies the I-PWND-02 import audit (no brain.development.
coherence_monitor import added there). Coherence feedback re-enters
later internal processing via the previously reserved closed-enum
InternalEventSource member COHMON_SUMMARY, which Phase 3.18 set aside
for exactly this expansion.
```

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-20-coherence-feedback-bridge
```

If Phase 3.19 PR #24 has not yet merged at campaign start, the
Phase 3.20 branch is **stacked** on the current Phase 3.19 HEAD and
the final PR targets `campaign/phase3-19-internal-feedback-loop`. If
PR #24 merges during the campaign, the final PR retargets to `main`
before final PR preparation.

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into the correct base at campaign completion
never merge the PR without explicit user approval
never edit brain/tick.py in Phase 3.20
```

---

## Baseline to verify

Expected current baseline (must match before any step runs):

```text
Catalog: v0.28 (Phase 3.20 Step 7 landed)
Counts:
  REQUIRED:        284
  STRUCTURAL:       91
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.19 Internal Feedback Loop
                              Prototype (PR #24 open at campaign
                              start; phase 3.20 branch stacked on
                              its head)
Available advisory bridge:    Stage A /ask-chatgpt (PR #13)
Available limited-write bridge: Stage B /ask-chatgpt-write (PR #15)
Available orchestration bridge: Stage C.1 /orchestrate-flow-with-codex
                              (PR #19)
Available workflow helpers:   tools/claude_helpers/campaign_state.py,
                              tools/claude_helpers/gate_runner.py,
                              tools/claude_helpers/flow_manifest.py
                              (PR #20)
Current mission:              Phase 3.20 Coherence Feedback Bridge
Next eligible step:           Step 2 coherence feedback synthesis
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
PHASE3_20_COHERENCE_FEEDBACK_BRIDGE_ROADMAP.md
docs/campaigns/phase3_18/PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md
docs/campaigns/phase3_18/PHASE3_18_PATTERN_RECOGNITION_DEMO.md
docs/campaigns/phase3_18/PHASE3_18_AUDIT.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_SYNTHESIS.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_BEHAVIOR_REPORT.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_FINDINGS.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_AUDIT.md
brain/development/processing_window.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/ui/session.py
brain/ui/snapshot.py
brain/tick.py
brain/llm/client.py
brain/llm/ptcns_backed.py
tools/claude_helpers/campaign_state.py
tools/claude_helpers/gate_runner.py
tools/claude_helpers/flow_manifest.py
tools/claude_helpers/codex_chatgpt_flow_orchestrator.py
.claude/agents/brain-current-mission.md
.claude/agents/chatgpt-codex-flow-orchestrator.md
.claude/commands/orchestrate-flow-with-codex.md
.claude/commands/go.md
tools/check_all.sh
```

Then read whichever files the next campaign step names.

---

## Phase 3.20 architectural guardrails

Preserve these constraints throughout Phase 3.20:

```text
no consciousness claim
no sentience claim
no subjective-experience claim
no semantic-understanding claim
no truth-adjudication claim
no agency claim
no self-modification claim
no aggregate consciousness / sentience / awareness / I-ness / growth
  score
no SelfModel implementation
no Growth Ledger semantic change (no new GrowthEventType, no new
  GrowthEventSource)
no Pattern Ledger semantic change (no new SourceKind, no new
  saturation state, no signature shape change)
no Coherence Monitor semantic change (the monitor stays read-only;
  no new check; no new status; no new source label; no mutation of
  any kernel container)
no model-backed default behavior; offline remains the default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no silent repair calls
no DB schema change
no SCHEMA_VERSION bump
no persistence / autosave runtime change
no tick semantic change (brain/tick.py untouched)
no L1 cache semantic change
no L2 (eval_v1) semantic change
no parser change
no prompt change
no UI verb addition unless explicitly review-gated
no /save-session / /load-session / autosave extension
no raw prompts committed to the repo
no raw model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation outside the sanctioned bridges
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
no unbounded loops
no unbounded state growth
50 internal ticks remains the recommended high-window default for
  meaningful internalization tests; the runtime bound stays at
  PROCESSING_WINDOW_SIZE_MAX = 255
PASS / WARN / FAIL / NOT_APPLICABLE remain treated as structural
  statuses; they are not truth claims about the running system
```

Real model-call budget for the entire campaign:

```text
Max 20 real external model-backed calls total.
Phase 3.20 expects to consume ZERO real model calls on the
  STREAM_APPEND-only coherence-feedback path.
Stop before exceeding 20.
```

Allowed real model-backed modes (only if a probe needs one):

```text
1. codex-cli
2. claude-cli
3. anthropic-api
```

---

## ChatGPT/Codex consultation (Stage A, Stage B, and Stage C.1)

Same as Phase 3.19:

- Stage A (PR #13) read-only, advisory.
- Stage B (PR #15) limited-write, allowlist-based, sequential.
- Stage C.1 (PR #19) dynamic-flow, allowlist-based, max two active
  Codex nodes, isolated nodes may run in parallel, chained nodes
  require `depends_on`, no automatic retry, hard cap 8 nodes.
  **For Phase 3.20, max total Stage C.1 real Codex nodes = 5
  unless operator approves more.**

Stage C.1 may be used in this campaign for:

- drafting Phase 3.20 synthesis / probe / corrigenda docs;
- drafting bounded fixture / module shards after Step 6 review gate;
- drafting bounded doc shards.

Stage C.1 is forbidden for:

- real model route execution;
- touching secrets;
- committing cache files;
- broad runtime changes;
- editing `brain/tick.py`;
- final catalog reconciliation;
- staging / commit / push.

Before every Stage C.1 flow:

```bash
python3 -m tools.claude_helpers.flow_manifest validate <manifest> --strict
python3 -m tools.claude_helpers.flow_manifest summary <manifest>
```

Stop on `CODEX_NETWORK_TRANSIENT`; do not retry automatically.

---

## Workflow tools (PR #20)

Prefer the helper wrappers:

```text
python3 -m tools.claude_helpers.campaign_state summary
python3 -m tools.claude_helpers.campaign_state json
python3 -m tools.claude_helpers.gate_runner
python3 -m tools.claude_helpers.gate_runner --json
python3 -m tools.claude_helpers.flow_manifest validate <path> --strict
python3 -m tools.claude_helpers.flow_manifest summary <path>
```

The gate runner must still cover the five canonical gates:

```text
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

---

## Command rule

Use `python3 -m ...` for Python module commands. Do not run real LLM
scenario commands unless the user explicitly asks.

---

## Final report format (per step)

```text
Campaign step executed:
- <step name>

Created/updated:
- <files>

Validation:
- <commands and results>

Git:
- branch: <campaign branch>
- commit: <sha or none>
- push: success / not needed

Real model call accounting:
- mode tested: <codex-cli / claude-cli / anthropic-api / n/a>
- calls used in this step: <count>
- cumulative calls used: <count> / 20

Stage A ChatGPT/Codex consultation: <disclosure>
Stage B limited-write collaboration: <disclosure>
Stage C.1 flow orchestration: <disclosure>

Next:
- <next campaign step or stop condition>
```

Stop according to `CURRENT_CAMPAIGN.md` and do not pass a review gate
without a fresh instruction.
