# CURRENT_MISSION.md — Phase 3.17 Codex Runtime Fix + Processing Window Research

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read
this file, read `CURRENT_CAMPAIGN.md`, create or continue the active
campaign branch, run the next eligible campaign step, commit successful
results, push the branch, and stop exactly where the campaign says to
stop.

---

## Current mission

Execute the **Phase 3.17 Codex Runtime Fix + Processing Window Research
Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.17 follows the completed Phase 3.16 Real Model Operational
Tuning (PR #21), which demonstrated a complete real-model-backed
operational walk under claude-cli and recorded codex-cli as
construction-blocked by codex 0.130.0's trusted-directory check.
Phase 3.17 takes two bounded operational questions in series:

1. **Codex-cli compatibility.** Does the single-line addition of
   `--skip-git-repo-check` to `CodexCLIClient.command` unblock the
   codex-cli mode end-to-end against a real codex binary, without
   touching `brain/tick.py`, the L1 / L2 cache semantics, the parser,
   the prompt, or the catalog row count?
2. **Bounded post-input processing window.** What is the smallest,
   safest, inspectable architecture for an operational
   *internalization window* of N internal ticks following each
   external input — starting with **N = 50** as the experimental
   default — so we can begin measuring whether bounded reflective
   processing produces inspectable structural recurrence and growth
   ledger evidence beyond what raw external input alone produces?

Phase 3.17 is a **research-and-engineering** campaign toward an
operationally learning/growing "I" approximation. It is **not** a
claim of consciousness, sentience, subjective experience, true
selfhood, true agency, semantic understanding, truth access,
desires / will / intent, or self-modification in the strong sense.

Allowed claim shape:

```text
"ToyI approximates some functional properties associated with a
learning/growing I: persistent state, bounded memory, pattern
recurrence, model-backed evaluations, growth events, cache
discipline, and inspectable post-input processing."
```

Forbidden claim shape:

```text
"ToyI is conscious / sentient / understands / has a self / has
agency."
```

Campaign target:

```text
Phase 3.17 Step 1   Mission sync and research roadmap
Phase 3.17 Step 2   Codex-cli compatibility patch plan
Phase 3.17 Step 3   Apply codex-cli compatibility fix
Phase 3.17 Step 4   Codex-cli real model smoke
Phase 3.17 Step 5   Processing window research synthesis
Phase 3.17 Step 6   Processing window behavior probe plan
Phase 3.17 Step 7   Optional reviewed implementation plan
Phase 3.17 Step 8   Start mock processing-window test
Phase 3.17 Step 9   Findings / triage
Phase 3.17 Step 10  Final audit
Phase 3.17 Step 11  PR preparation
```

Intended result:

```text
A small, reviewed runtime patch that unblocks codex-cli for the
Phase 3.16 operational route, evidence that the patch produces a
complete model-backed tick (or a precise blocker if it doesn't),
plus a rigorous research artifact set describing a bounded
post-input processing window architecture, an experimental probe
plan, and a first controlled test using only existing surfaces.
The mission ships no SelfModel, no consciousness claim, no
aggregate I-ness score, no tick-kernel change, no L1 / L2 cache
semantic change, no prompt / parser change, no growth / pattern /
coherence semantic change, no schema bump, and no implicit network
behavior.
```

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-17-codex-processing-window
```

Rules:

```text
never commit directly to main during campaign execution
commit every successful step that changes files
push every successful step commit to the campaign branch
open a PR into main at campaign completion
never merge the PR without explicit user approval
```

---

## Baseline to verify

Expected current baseline (must match before any step runs):

```text
Catalog: v0.25
Counts:
  REQUIRED:        281
  STRUCTURAL:       88
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.16 Real Model Operational
                              Tuning (PR #21)
Available advisory bridge:    Stage A /ask-chatgpt (PR #13)
Available limited-write bridge: Stage B /ask-chatgpt-write (PR #15)
Available orchestration bridge: Stage C.1 /orchestrate-flow-with-codex
                              (PR #19)
Available workflow helpers:   tools/claude_helpers/campaign_state.py,
                              tools/claude_helpers/gate_runner.py,
                              tools/claude_helpers/flow_manifest.py
                              (PR #20)
Current mission:              Phase 3.17 Codex Runtime Fix +
                              Processing Window Research
Phase 3.17 Step 1 status:     in flight on campaign branch
Next eligible step:           Step 2 codex-cli compatibility patch
                              plan (after Step 1 commits/pushes)
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
PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_AUDIT.md
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_FINDINGS.md
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_RUN.md
brain/llm/client.py
brain/llm/ptcns_backed.py
brain/llm/prompts.py
brain/llm/parse.py
brain/ui/llm_runtime.py
brain/ui/__main__.py
brain/ui/session.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/render.py
brain/tick.py
brain/development/growth_ledger.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
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

## Phase 3.17 architectural guardrails

Preserve these constraints throughout Phase 3.17:

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
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no model-backed default behavior; offline remains the default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no silent repair calls
no DB schema change in v1
no SCHEMA_VERSION bump
no persistence / autosave runtime change
no tick semantic change (brain/tick.py untouched)
no L2 (eval_v1) semantic change
no L1 cache semantic change EXCEPT the codex-cli command tuple
  compatibility fix (single line; locked to adding
  '--skip-git-repo-check' to CodexCLIClient.command default and
  the codex-cli factory)
no /save-session / /load-session / autosave extension in v1
no raw prompts committed to the repo
no raw model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation outside the sanctioned bridges
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
no runtime "processing window" implementation in v1 unless a Step 7
  review gate explicitly authorizes it
50 internal ticks is the *initial experimental default* for the
  processing window; it is not a constant burned into the runtime
  in v1
```

Real model-call budget for the entire campaign:

```text
Max 20 real external model-backed calls total.
Count every attempt (success, retry, parse failure, timeout, nonzero
  exit) toward the budget.
Stop before exceeding 20.
If call count cannot be proven, assume the higher number.
Use cache-aware repeated probes after the first miss.
No unbounded loops; no "keep trying forever."
```

Allowed real model-backed modes (in preference order for Step 4 only):

```text
1. codex-cli (the mode under test in this campaign)
2. claude-cli (fall back if Step 4 cannot complete on codex-cli)
3. anthropic-api (fall back if neither CLI is usable)
```

---

## ChatGPT/Codex consultation (Stage A, Stage B, and Stage C.1)

This repository ships sanctioned Claude → Codex CLI → ChatGPT bridges:

- Stage A (PR #13) read-only, advisory.
- Stage B (PR #15) limited-write, allowlist-based, sequential.
- Stage C.1 (PR #19) dynamic-flow, allowlist-based, max two active
  Codex nodes, isolated nodes may run in parallel, chained nodes
  require `depends_on`, no automatic retry, hard cap 8 nodes.
  **For Phase 3.17, max total Stage C.1 real Codex nodes = 5 unless
  operator approves more.**

Use only the sanctioned paths:

```text
Stage A:  /ask-chatgpt --mode <mode> --model gpt-5.5 --effort <effort> <prompt>
Stage B:  /ask-chatgpt-write --model gpt-5.5 --effort high \
            --allowed-file <path> [--allowed-file <path> ...] --apply <prompt>
Stage C.1: /orchestrate-flow-with-codex <task>
           python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py \
             --manifest <path> --model gpt-5.5 --effort high
```

Stage C.1 may be used in this campaign for:

- drafting Phase 3.17 roadmap / synthesis docs;
- drafting bounded docs/fixtures shards;
- mechanical doc shards after measurements exist.

Stage C.1 is forbidden for:

- running the real codex-cli model loop (Step 4);
- touching secrets;
- committing cache files;
- broad runtime changes;
- editing `brain/tick.py`;
- final catalog reconciliation;
- staging / commit / push.

Before every Stage C.1 flow, validate the manifest:

```bash
python3 -m tools.claude_helpers.flow_manifest validate <manifest> --strict
python3 -m tools.claude_helpers.flow_manifest summary <manifest>
```

Stop on `CODEX_NETWORK_TRANSIENT`; do not retry automatically.

Disclose bridge usage in every step report using the disclosure block
defined in `CURRENT_CAMPAIGN.md`.

---

## Workflow tools (PR #20)

Prefer the helper wrappers over hand-rolled pipelines:

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

If `gate_runner` itself has any issue, fall back to running the
canonical commands directly.

---

## Command rule

Use `python3 -m ...` for Python module commands. Convert historical
`python -m ...` examples to `python3 -m ...` unless the user has
explicitly confirmed a `python` alias.

Do not run real LLM scenario commands unless the user explicitly asks.

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

Stage A ChatGPT/Codex consultation:
- used: yes / no
- mode / model / effort: <values or n/a>
- wrapper command: <command or n/a>
- question file / answer file: <paths or n/a>
- wrapper status: <exit code + error class or n/a>
- accepted advice: <bullets or none>
- rejected advice: <bullets or none>
- reason: <one sentence>

Stage B limited-write collaboration:
- used: yes / no
- mode / model / effort: <values or n/a>
- wrapper command: <command or n/a>
- allowed files / prompt file / answer file: <paths or n/a>
- wrapper status: <exit code + error class or n/a>
- files changed: <paths or none>
- accepted/rejected edits: <bullets or none>
- reason: <one sentence>

Stage C.1 flow orchestration:
- used: yes / no
- manifest path: <path or n/a>
- manifest validation: <pass / fail / n/a>
- wrapper command: <command or n/a>
- wrapper status: <exit code + error class or n/a>
- nodes: <node ids or n/a>
- changed files: <paths or none>
- accepted/rejected edits: <bullets or none>
- reason: <one sentence>

Next:
- <next campaign step or stop condition>
```

Stop according to `CURRENT_CAMPAIGN.md` and do not pass a review gate
without a fresh instruction.
