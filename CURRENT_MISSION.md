# CURRENT_MISSION.md — Phase 3.15 L1 Cache Hygiene Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

---

## Current mission

Execute the **Phase 3.15 L1 Cache Bounding & Replay Hygiene Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.15 follows the completed Phase 3.14 LLM Cache Discipline that landed on main as PR #16, and the Stage C Claude → Codex CLI → ChatGPT orchestration bridge that landed on main as PR #17. Phase 3.15 takes the next bounded substrate question: **L1 transport cache hygiene** — bounding the existing `CachedClient` prompt-hash disk cache and triaging raw bad-response replay, without weakening the Phase 3.14 L0/L1/L2 architecture and without changing tick semantics.

Campaign target:

```text
Phase 3.15 Step 1     Repo-state sync and Phase 3.15 mission install
Phase 3.15 Step 2     L1 cache hygiene synthesis
Phase 3.15 Step 3     L1 cache behavior probe / replay reproduction report
Phase 3.15 Step 4     L1 cache hygiene corrigenda
Phase 3.15 Step 5     L1 cache catalog patch plan
Phase 3.15 Step 6     Review Gate A — L1 cache hygiene implementation
Phase 3.15 Step 7     Apply accepted L1 cache hygiene implementation, if approved
Phase 3.15 Step 8     L1 cache hygiene behavior report
Phase 3.15 Step 9     L1 cache findings / triage
Phase 3.15 Step 10    Final Phase 3.15 audit
Phase 3.15 Step 11    Final PR preparation
```

Intended result:

```text
The repo's L1 transport cache (CachedClient at brain/llm/client.py) has
a cataloged, bounded, observable hygiene policy that prevents
unbounded growth of brain/.llm_cache and is explicit about raw
bad-response replay, without weakening the Phase 3.14 L0/L1/L2
architecture. Offline remains default. Model-backed modes remain
explicit opt-in. L2 (eval_v1) semantics are unchanged. No tick
semantic change ships before Review Gate A. No consciousness /
sentience / subjective / semantic / truth / agency / self-modification
claim is introduced. No SelfModel implementation appears. No Growth
Ledger / Pattern Ledger / Coherence Monitor semantic change ships.
```

This mission is measurement-first and design-gated. The Phase 3.14 catalog patch left `I-LLMCACHE-20` DEFERRED with the note that L1 bounding / eviction is a future-campaign concern; Phase 3.15 is that campaign. The Phase 3.14 audit also left `I-LLMCACHE-21` (real external model-backed cache smoke) and `I-LLMCACHE-22` (end-to-end Phase 3.14 behavior probe) NOT-EXERCISED. Phase 3.15 inherits both as deliberately deferred unless Review Gate A explicitly authorizes promoting one or both.

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-15-l1-cache-hygiene
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
Latest completed campaign:    Phase 3.14 LLM Cache Discipline (PR #16)
Latest bridge merge:          Stage C Claude → Codex CLI → ChatGPT
                              orchestration bridge (PR #17)
Available advisory bridge:    Stage A /ask-chatgpt through Codex CLI wrapper
                              (PR #13)
Available limited-write bridge: Stage B /ask-chatgpt-write through Codex CLI
                              wrapper (PR #15)
Available orchestration bridge: Stage C /orchestrate-with-codex through Codex
                              CLI wrapper (PR #17)
Canonical Phase 3.15 design seed:
  PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md
Current mission:              Phase 3.15 L1 Cache Hygiene
Phase 3.15 Step 1 status:     in flight on campaign branch
Next eligible step:           Step 2 L1 cache hygiene synthesis
                              (after Step 1 commits/pushes)
```

Stop if the catalog counts disagree or if the Phase 3.15 roadmap seed is missing.

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
PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md
PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_AUDIT.md
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_FINDINGS.md
.claude/agents/brain-current-mission.md
.claude/agents/chatgpt-codex-subagent.md
.claude/agents/chatgpt-codex-writer.md
.claude/agents/chatgpt-codex-orchestrator.md
.claude/commands/go.md
.claude/commands/ask-chatgpt.md
.claude/commands/ask-chatgpt-write.md
.claude/commands/orchestrate-with-codex.md
tools/claude_helpers/codex_chatgpt_subagent.py
tools/claude_helpers/codex_chatgpt_write_worker.py
tools/claude_helpers/codex_chatgpt_orchestrator.py
CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md
CODEX_CHATGPT_LIMITED_WRITE_BRIDGE_AUDIT.md
CODEX_CHATGPT_ORCHESTRATION_BRIDGE_AUDIT.md
brain/tick.py
brain/llm/client.py
brain/llm/ptcns_backed.py
brain/llm/prompts.py
brain/llm/parse.py
brain/ui/llm_runtime.py
brain/ui/session.py
brain/ui/__main__.py
tools/check_all.sh
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Phase 3.15 architectural guardrails

Preserve these constraints throughout Phase 3.15:

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
no silent repair calls (no auto-rewrite of cache contents based on
  inferred fixes)
no DB schema change in v1 unless explicitly planned and accepted at the
  review gate
no SCHEMA_VERSION bump
no persistence / autosave runtime change
no tick semantic change before the Phase 3.15 review gate
no /save-session / /load-session / autosave extension in v1 unless
  explicitly planned and accepted at the review gate
no raw prompts or model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation
no Stage C broad repo edits
no unbounded Codex collaboration loop
no real external LLM smoke beyond the sanctioned Stage A /ask-chatgpt,
  Stage B /ask-chatgpt-write, and Stage C /orchestrate-with-codex
  bridges, and any explicitly approved Phase 3.15 measurement step
no L2 (eval_v1) semantic change; Phase 3.15 does not touch L2
preserve L1 transport semantics unless Review Gate A authorizes a change
```

The permitted experimental framing is:

```text
bounded L1 transport cache hygiene
explicit, deterministic eviction or write-skip policy
explicit raw bad-response replay policy
deterministic, documented, observable cache behavior
opt-in model-backed runtime preserved
references-only diagnostics; no raw prompt or response payload in docs
manual inspect/clear helpers only after explicit Review Gate A approval
```

The prohibited framing is:

```text
proof or claim of consciousness
unbounded self-modification
semantic truth authority from raw text
model-backed default behavior
hidden LLM calls
unbounded cache growth (the surface this campaign exists to retire)
silent persistence
aggregate awareness / sentience / I-ness / growth score
SelfModel implementation
Growth Ledger / Pattern Ledger / Coherence Monitor semantic change
L2 (eval_v1) semantic change
```

---

## ChatGPT/Codex consultation (Stage A, Stage B, and Stage C bridges)

This repository ships three explicit Claude → Codex CLI → ChatGPT bridges:

- Stage A (PR #13) is read-only, transport + policy bounded, and advisory only.
- Stage B (PR #15) is limited-write, allowlist-based, sequential, and bounded by a temp git worktree.
- Stage C (PR #17) is orchestrated multi-shard, allowlist-based, capped at two concurrent shards per wave, and bounded by a temp git worktree per shard.

Use only the sanctioned paths:

```text
Stage A slash command:
  /ask-chatgpt --mode <mode> --model gpt-5.5 --effort <effort> <prompt>

Stage A direct wrapper:
  python3 tools/claude_helpers/codex_chatgpt_subagent.py \
    --mode <mode> --model gpt-5.5 --effort <effort> \
    --timeout <seconds> --prompt-file <path>

Stage B slash command:
  /ask-chatgpt-write --model gpt-5.5 --effort high \
    --allowed-file <path> [--allowed-file <path> ...] --apply <prompt>

Stage B direct wrapper:
  python3 tools/claude_helpers/codex_chatgpt_write_worker.py \
    --mode write --model gpt-5.5 --effort <effort> \
    --timeout <seconds> --allowed-file <path> [--apply] \
    --prompt-file <path>

Stage C slash command:
  /orchestrate-with-codex --model gpt-5.5 --effort high --max-parallel 2 <task>

Stage C direct wrapper:
  python3 tools/claude_helpers/codex_chatgpt_orchestrator.py \
    --manifest <manifest path> --model gpt-5.5 --effort <effort> \
    --timeout <seconds> --max-parallel 2 --max-real-calls 2 --apply
```

The direct wrappers are the policy boundary. Do not invoke raw `codex` or `codex exec`. Do not add `Bash(codex:*)` / `Bash(codex exec:*)` allowlists. Stage A `code` mode is forbidden. Stage B requires exact `--allowed-file` entries and never stages, commits, pushes, restores, or merges. Stage C requires a manifest with exactly one wave, at most two shards per wave, disjoint `allowed_files` sets, no declared read/write collision, no shard interdependence, and never stages, commits, pushes, restores, or merges.

Allowed Stage A modes: `plan` / `review` / `summarize` / `debug`.
Allowed Stage B mode: `write`.
Allowed Stage C shape: one wave, ≤2 shards, `max_parallel=2`, `max_real_calls=2` per wave.

Preferred model: `gpt-5.5` (the only model the local ChatGPT-account Codex backend accepted during the Stage A/B/C smokes; other candidates including `gpt-5.1-codex`, `gpt-5`, `gpt-5-codex`, `gpt-5.1`, `o3`, and `gpt-4o` were rejected with HTTP 400).
Effort guidance: `low` for quick sanity checks, `medium` for normal review critique, `high` for row-family or invariant-boundary analysis and for Stage B / Stage C write work.

Use the bridges only at high-leverage points:

```text
Stage A     adversarial review at synthesis / catalog patch plan /
            behavior report / final audit; or any unresolved validation
            failure after local inspection.
Stage B     bounded single-file doc drafts whose exact path is on the
            allowlist; rarely fixture shards after a review gate.
Stage C     bounded multi-shard doc work or implementation shards whose
            exact write sets are disjoint and whose read/write
            boundaries do not collide; one wave at a time; never for
            final catalog integration; never for CURRENT_MISSION.md or
            CURRENT_CAMPAIGN.md unless explicitly bound as the only
            file in a shard.
```

The wrappers write hash-only audit JSONL under `.claude/codex_bridge_logs/`, which is gitignored. Do not commit those logs.

More than three real Codex calls in a single step requires fresh operator approval. None of the bridges are to be used for staging / committing / pushing — parent Claude does that after inspecting the diff.

Treat ChatGPT as advisory. Claude remains the parent integrator. Repo-local files, gates, and invariants override ChatGPT advice. If ChatGPT advice conflicts with a repo-local constraint, report the conflict and follow the repo.

Disclose bridge usage in every step report using the disclosure block defined in `CURRENT_CAMPAIGN.md`.

---

## Command rule

Use `python3 -m ...` for Python module commands. Convert historical `python -m ...` examples to `python3 -m ...` unless the user has explicitly confirmed a `python` alias.

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

Stage A ChatGPT/Codex consultation:
- used: yes / no
- mode / model / effort: <values or n/a>
- wrapper command: <command or n/a>
- question file: <path or n/a>
- answer file: <path or n/a>
- wrapper status: <exit code + error class or n/a>
- accepted advice: <bullets or none>
- rejected advice: <bullets or none>
- reason: <one sentence>

Stage B limited-write collaboration:
- used: yes / no
- mode / model / effort: <values or n/a>
- wrapper command: <command or n/a>
- allowed files: <paths or n/a>
- question file / prompt file: <path or n/a>
- answer file: <path or n/a>
- wrapper status: <exit code + error class or n/a>
- files changed: <paths or none>
- accepted edits: <bullets or none>
- rejected edits: <bullets or none>
- reason: <one sentence>

Stage C orchestration:
- used: yes / no
- probe status: <pass / fail / n/a>
- manifest path: <path or n/a>
- wrapper command: <command or n/a>
- wrapper status: <exit code + error class or n/a>
- shards: <shard ids or n/a>
- changed files: <paths or none>
- accepted edits: <bullets or none>
- rejected edits: <bullets or none>
- reason: <one sentence>

Next:
- <next campaign step or stop condition>
```

Stop according to `CURRENT_CAMPAIGN.md` and do not pass a review gate without a fresh instruction.
