# CURRENT_MISSION.md — Phase 3.16 Real Model Operational Tuning Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read
this file, read `CURRENT_CAMPAIGN.md`, create or continue the active
campaign branch, run the next eligible campaign step, commit successful
results, push the branch, and stop exactly where the campaign says to
stop.

---

## Current mission

Execute the **Phase 3.16 Real Model Operational Tuning Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.16 follows the completed Phase 3.15 L1 Cache Hygiene (PR #18),
the Stage C.1 dynamic Codex flow orchestrator (PR #19), and the Stage
C.1 workflow helper tools (PR #20). Phase 3.16 takes the next bounded
operational question: **does ToyI's runtime actually perform a
model-backed operational walk end-to-end against a real model-backed
client**, observably and within a documented call budget — or is a
specific environment / runtime blocker provable?

Campaign target:

```text
Phase 3.16 Step 1   Repo-state sync and Phase 3.16 mission install
Phase 3.16 Step 2   Real model tuning synthesis
Phase 3.16 Step 3   Model availability and deterministic baseline report
Phase 3.16 Step 4   Real model smoke and tuning run
Phase 3.16 Step 5   Findings / blocker triage
Phase 3.16 Step 6   Optional reviewed patch plan if runtime changes are needed
Phase 3.16 Step 7   Apply accepted patch only if Step 6 authorizes it
Phase 3.16 Step 8   Post-patch or final behavior report
Phase 3.16 Step 9   Final audit
Phase 3.16 Step 10  PR preparation
```

If Step 4 produces a clean useful result and no patch is required,
Steps 6-7 are skipped and the campaign proceeds to Step 8.

Intended result:

```text
A concrete, inspectable model-backed operational walk of ToyI that
either demonstrates a complete model-backed tick route (real client,
parseable consistency eval, tick completion, bounded state change,
bounded cache behavior, bounded call count) or proves a precise
environment / runtime blocker. OFFLINE remains default. Model-backed
modes remain explicit opt-in. L1 (CachedClient) bounded at
L1_CACHE_MAX_ENTRIES = 1024. L2 (eval_v1) bounded at
SEMANTIC_CACHE_MAX_ENTRIES = 1024 and stores only key_prefix /
parsed. brain/tick.py is untouched. No consciousness / sentience /
subjective / semantic / truth / agency / self-modification claim is
introduced. No SelfModel implementation appears. No Growth Ledger /
Pattern Ledger / Coherence Monitor semantic change ships.
```

This mission is measurement-first. It does not implement runtime
features without an explicit Step 6 review gate.

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-16-real-model-operational-tuning
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
Latest completed campaign:    Phase 3.15 L1 Cache Hygiene (PR #18)
Latest bridge merges:         Stage C.1 dynamic Codex flow orchestrator
                              (PR #19); Stage C.1 workflow tools (PR #20)
Available advisory bridge:    Stage A /ask-chatgpt through Codex CLI wrapper
                              (PR #13)
Available limited-write bridge: Stage B /ask-chatgpt-write through Codex CLI
                              wrapper (PR #15)
Available orchestration bridge: Stage C.1 dynamic /orchestrate-flow-with-codex
                              through Codex CLI wrapper (PR #19)
Available workflow helpers:   tools/claude_helpers/campaign_state.py,
                              tools/claude_helpers/gate_runner.py,
                              tools/claude_helpers/flow_manifest.py (PR #20)
Current mission:              Phase 3.16 Real Model Operational Tuning
Phase 3.16 Step 1 status:     in flight on campaign branch
Next eligible step:           Step 2 Real model tuning synthesis
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
PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md
PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_AUDIT.md
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_FINDINGS.md
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

## Phase 3.16 architectural guardrails

Preserve these constraints throughout Phase 3.16:

```text
no consciousness claim
no sentience claim
no subjective-experience claim
no semantic-understanding claim
no truth-adjudication claim
no agency claim
no self-modification claim
no aggregate consciousness / sentience / awareness / I-ness / growth score
no SelfModel implementation
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no model-backed default behavior; offline remains the default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no silent repair calls
no DB schema change in v1 unless explicitly planned and accepted at the
  review gate
no SCHEMA_VERSION bump
no persistence / autosave runtime change
no tick semantic change (brain/tick.py untouched)
no L2 (eval_v1) semantic change
no L1 cache semantic change without a new review gate
no /save-session / /load-session / autosave extension in v1
no raw prompts committed to the repo
no raw model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
```

Real-model-call budget for the entire campaign:

```text
Max 30 real external model-backed calls total.
Count every attempt (success, retry, parse failure, timeout, nonzero
  exit) toward the budget.
Stop before exceeding 30.
If call count cannot be proven, assume the higher number.
Use cache-aware repeated probes after the first miss.
No unbounded loops; no "keep trying forever."
```

Allowed real model-backed modes (in preference order):

```text
1. codex-cli
2. claude-cli
3. anthropic-api
```

Use the first available/configured mode that can safely run. Do not
require all three. If no model-backed mode is available, produce a
BLOCKED BY ENV report showing exactly what is missing.

---

## ChatGPT/Codex consultation (Stage A, Stage B, and Stage C.1 bridges)

This repository ships sanctioned Claude → Codex CLI → ChatGPT bridges:

- Stage A (PR #13) is read-only, transport + policy bounded, and advisory only.
- Stage B (PR #15) is limited-write, allowlist-based, sequential, and bounded by a temp git worktree.
- Stage C.1 (PR #19) is dynamic-flow, allowlist-based, max two active Codex nodes, isolated nodes may run in parallel, chained nodes require explicit `depends_on`, no automatic retry, hard cap 8 nodes. For this campaign, max total Stage C.1 real Codex nodes = 5 unless operator approves more.

Use only the sanctioned paths:

```text
Stage A slash command:
  /ask-chatgpt --mode <mode> --model gpt-5.5 --effort <effort> <prompt>

Stage B slash command:
  /ask-chatgpt-write --model gpt-5.5 --effort high \
    --allowed-file <path> [--allowed-file <path> ...] --apply <prompt>

Stage C.1 slash command:
  /orchestrate-flow-with-codex <task>

Stage C.1 wrapper:
  python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py \
    --manifest <manifest path> --model gpt-5.5 --effort high
```

Stage C.1 should be used for: drafting Phase 3.16 roadmap / synthesis
docs; drafting report files after measurements exist; mechanical
non-runtime helper / report shards; optionally bounded test harness
files if a review gate authorizes them.

Stage C.1 should not be used for: running the real model loop itself;
touching secrets; committing cache files; broad runtime changes;
brain/tick.py; final catalog reconciliation.

Before every Stage C.1 flow call, validate the manifest:

```bash
python3 -m tools.claude_helpers.flow_manifest validate /tmp/<manifest>.json --strict
python3 -m tools.claude_helpers.flow_manifest summary /tmp/<manifest>.json
```

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

## Final report format

After each run, report:

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
- cumulative calls used: <count> / 30

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
