# CURRENT_MISSION.md — Phase 3.19 Internal Feedback Loop Prototype

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read
this file, read `CURRENT_CAMPAIGN.md`, create or continue the active
campaign branch, run the next eligible campaign step, commit successful
results, push the branch, and stop exactly where the campaign says to
stop.

---

## Current mission

Execute the **Phase 3.19 Internal Feedback Loop Prototype Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.19 follows the completed Phase 3.18 Bounded Internal Processing
Window campaign (PR #23). Phase 3.18 demonstrated:

- deterministic post-input rehearsal via
  `brain/development/processing_window.py`
- Pattern Ledger saturation in a single dispatch at `N = 255`
- monotone, deterministic, independent pattern recognition (D1–D4 PASS)
- zero real model calls on the rehearsal path
- catalog v0.26 with `I-PWND-01` / `I-PWND-02`

Phase 3.19 takes the next bounded operational question:

> Can ToyI's runtime route a **bounded internal feedback event**,
> derived from Pattern Ledger state observed inside the processing
> window, back into the same Pattern Ledger / Growth Ledger
> substrate — without touching `brain/tick.py`, the LLM, the parser,
> the cache, or any consciousness-adjacent boundary?

Phase 3.19 takes ToyI from:

```text
external input -> deterministic rehearsal -> recurrence count
```

toward:

```text
external input -> rehearsal -> pattern-ledger summary
              -> bounded internal feedback event
              -> normal STREAM_APPEND path
              -> inspectable second-order pattern + growth
```

This is an operational approximation of some functional properties
associated with a learning/growing "I." It is **NOT** a claim of
consciousness, sentience, subjective experience, true agency, true
selfhood, semantic understanding, truth access, desire/will/intent, or
self-modification in the strong sense.

Allowed claim shape:

```text
"ToyI approximates some functional properties associated with a
learning/growing I: bounded internal feedback events, second-order
pattern recurrence, deterministic state integration, inspectable
growth-event records, and bounded coherence summaries."
```

Forbidden claim shape:

```text
"ToyI is conscious / sentient / understands / has a self / has
agency / has desires / introspects."
```

Campaign target:

```text
Phase 3.19 Step 1   Mission sync + roadmap
Phase 3.19 Step 2   Internal feedback synthesis
Phase 3.19 Step 3   Internal feedback probe matrix
Phase 3.19 Step 4   Corrigenda / design locks
Phase 3.19 Step 5   Catalog patch plan
Phase 3.19 Step 6   Review Gate A
Phase 3.19 Step 7   Apply implementation (if gated through)
Phase 3.19 Step 8   Behavior report
Phase 3.19 Step 9   Findings / triage
Phase 3.19 Step 10  Final audit
Phase 3.19 Step 11  PR preparation
```

Intended result:

```text
A small, reviewed runtime extension to
brain/development/processing_window.py and brain/ui/session.py that
emits bounded internal feedback events whose text is a deterministic
summary of the live Pattern Ledger entry created by the just-fired
rehearsal. Each accepted feedback event is itself a STREAM_APPEND
chunk that drives Pattern Ledger.observe and Growth Ledger.observe
through the existing call sites; no kernel change, no LLM call, no
schema change, no autosave change, no aggregate scalar. Pattern
recurrence now feeds back into later internal processing via the
new closed-enum InternalEventSource member PLEDGER_SUMMARY, which
was reserved in Phase 3.18 for exactly this expansion.
```

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-19-internal-feedback-loop
```

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
never edit brain/tick.py in Phase 3.19
```

---

## Baseline to verify

Expected current baseline (must match before any step runs):

```text
Catalog: v0.27
Counts:
  REQUIRED:        283
  STRUCTURAL:       90
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.18 Bounded Internal Processing
                              Window (PR #23, merged into the
                              phase3.17 branch upstream; phase3.18
                              content is brought along by the
                              phase3.19 campaign branch); Phase 3.19
                              Step 7 implementation now in flight on
                              the campaign branch
Available advisory bridge:    Stage A /ask-chatgpt (PR #13)
Available limited-write bridge: Stage B /ask-chatgpt-write (PR #15)
Available orchestration bridge: Stage C.1 /orchestrate-flow-with-codex
                              (PR #19)
Available workflow helpers:   tools/claude_helpers/campaign_state.py,
                              tools/claude_helpers/gate_runner.py,
                              tools/claude_helpers/flow_manifest.py
                              (PR #20)
Current mission:              Phase 3.19 Internal Feedback Loop
                              Prototype
Phase 3.19 Step 1 status:     in flight on campaign branch
Next eligible step:           Step 2 internal feedback synthesis
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
PHASE3_19_INTERNAL_FEEDBACK_LOOP_ROADMAP.md
docs/campaigns/phase3_18/PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md
docs/campaigns/phase3_18/PHASE3_18_PATTERN_RECOGNITION_DEMO.md
docs/campaigns/phase3_18/PHASE3_18_AUDIT.md
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

## Phase 3.19 architectural guardrails

Preserve these constraints throughout Phase 3.19:

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
no Coherence Monitor semantic change
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
50 internal ticks remains the initial high-window default for
  meaningful internalization tests; the runtime bound stays at
  PROCESSING_WINDOW_SIZE_MAX = 255
```

Real model-call budget for the entire campaign:

```text
Max 20 real external model-backed calls total.
Phase 3.19 expects to consume ZERO real model calls on the
  STREAM_APPEND-only feedback path.
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

Same as Phase 3.18:

- Stage A (PR #13) read-only, advisory.
- Stage B (PR #15) limited-write, allowlist-based, sequential.
- Stage C.1 (PR #19) dynamic-flow, allowlist-based, max two active
  Codex nodes, isolated nodes may run in parallel, chained nodes
  require `depends_on`, no automatic retry, hard cap 8 nodes.
  **For Phase 3.19, max total Stage C.1 real Codex nodes = 5
  unless operator approves more.**

Stage C.1 may be used in this campaign for:

- drafting Phase 3.19 synthesis / probe / corrigenda docs;
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
