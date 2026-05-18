# CURRENT_MISSION.md — Phase 3.14 LLM Cache Discipline Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

---

## Current mission

Execute the **Phase 3.14 LLM Cache Discipline Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.14 follows the completed Phase 3.13 Growth Ledger and the Stage B Claude → Codex CLI → ChatGPT limited-write bridge that landed on main as PR #15. Phase 3.14 audits and fixes **LLM cache discipline**: the model-backed LLM modes can spam external models across ticks unless cache behavior is explicit, semantic, bounded, and observable. The likely implementation surface is the LLM runtime / client / cache layer (`brain/llm/client.py`, `brain/llm/ptcns_backed.py`, `brain/llm/prompts.py`, `brain/ui/llm_runtime.py`) and possibly the prompt / cache-key canonicalization. The kernel transition surface (`brain/tick.py`) is **not** authorized as the first edit target; tick semantics are frozen behind the Phase 3.14 review gate.

Campaign target:

```text
Phase 3.14 Step 1     Repo-state sync and Phase 3.14 mission install
Phase 3.14 Step 2     LLM cache discipline synthesis
Phase 3.14 Step 3     LLM cache behavior probe / spam reproduction report
Phase 3.14 Step 4     LLM cache corrigenda
Phase 3.14 Step 5     LLM cache catalog patch plan
Phase 3.14 Step 6     Review Gate A — LLM cache implementation
Phase 3.14 Step 7     Apply accepted LLM cache implementation, if approved
Phase 3.14 Step 8     LLM cache behavior report
Phase 3.14 Step 9     LLM cache findings / triage
Phase 3.14 Step 10    Final Phase 3.14 audit
Phase 3.14 Step 11    Final PR preparation
```

Intended result:

```text
The repo's model-backed LLM modes use a cataloged, bounded, observable
cache discipline that prevents redundant external model calls across
ticks. Offline remains default. Model-backed modes remain explicit
opt-in. No tick semantic change ships before Review Gate A. No
consciousness / sentience / subjective / semantic / truth / agency /
self-modification claim is introduced. No SelfModel implementation
appears. No Growth Ledger semantic change ships.
```

This mission is measurement-first and design-gated. The existing `CachedClient` already supplies a SHA-256 prompt-hash disk cache under `brain/.llm_cache`; the new work is to (a) measure exactly where repeated external calls occur today, (b) decide whether the fix is enable-by-default of `CachedClient`, a canonical semantic evaluation cache, prompt-identity changes, or a combination, and (c) catalog the resulting discipline so a future agent cannot silently widen the model-backed surface.

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-14-llm-cache-discipline
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
Catalog: v0.24
Counts:
  REQUIRED:        277
  STRUCTURAL:       87
  NOT-EXERCISED:    14
  DEFERRED:         16
  OBSERVED:         16
Latest completed campaign:    Phase 3.13 Growth Ledger (PR #14)
Latest bridge merge:          Stage B Claude → Codex CLI → ChatGPT
                              limited-write bridge (PR #15)
Available advisory bridge:    Stage A /ask-chatgpt through Codex CLI wrapper
                              (PR #13)
Available limited-write bridge: Stage B /ask-chatgpt-write through Codex CLI
                              wrapper (PR #15)
Canonical Phase 3.14 design seed:
  PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md
Current mission:              Phase 3.14 LLM Cache Discipline
Phase 3.14 Step 1 status:     in flight on campaign branch
Next eligible step:           Step 2 LLM cache discipline synthesis
                              (after Step 1 commits/pushes)
```

Stop if the catalog counts disagree or if the Phase 3.14 roadmap seed is missing.

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
PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md
.claude/agents/brain-current-mission.md
.claude/agents/chatgpt-codex-subagent.md
.claude/agents/chatgpt-codex-writer.md
.claude/commands/go.md
.claude/commands/ask-chatgpt.md
.claude/commands/ask-chatgpt-write.md
tools/claude_helpers/codex_chatgpt_subagent.py
tools/claude_helpers/codex_chatgpt_write_worker.py
CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md
CODEX_CHATGPT_LIMITED_WRITE_BRIDGE_AUDIT.md
brain/tick.py
brain/llm/client.py
brain/llm/ptcns_backed.py
brain/llm/prompts.py
brain/ui/llm_runtime.py
brain/ui/session.py
brain/ui/__main__.py
tools/check_all.sh
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Phase 3.14 architectural guardrails

Preserve these constraints throughout Phase 3.14:

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
no model-backed default behavior; offline remains the default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no unbounded cache growth
no DB schema change in v1 unless explicitly planned and accepted at the
  review gate
no tick semantic change before the Phase 3.14 review gate
no /save-session / /load-session / autosave extension in v1 unless
  explicitly planned and accepted at the review gate
no raw prompts or model outputs committed to the repo
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation
no unbounded Codex collaboration loop
no real external LLM smoke beyond the sanctioned Stage A /ask-chatgpt
  and Stage B /ask-chatgpt-write bridges and any explicitly approved
  Phase 3.14 measurement step
```

The permitted experimental framing is:

```text
bounded model-backed cache discipline
explicit semantic vs non-semantic cache key choices
deterministic, documented, observable cache behavior
opt-in model-backed runtime preserved
session-local first; persistent on disk only with explicit policy
references-only diagnostics; no raw prompt or response payload
```

The prohibited framing is:

```text
proof or claim of consciousness
unbounded self-modification
semantic truth authority from raw text
model-backed default behavior
hidden LLM calls
unbounded cache growth
silent persistence
aggregate awareness / sentience / I-ness / growth score
SelfModel implementation
Growth Ledger semantic change
```

---

## ChatGPT/Codex consultation (Stage A and Stage B bridges)

This repository ships two explicit Claude → Codex CLI → ChatGPT bridges:

- Stage A (PR #13) is read-only, transport + policy bounded, and advisory only.
- Stage B (PR #15) is limited-write, allowlist-based, sequential, and bounded by a temp git worktree.

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
```

The direct wrappers are the policy boundary. Do not invoke raw `codex` or `codex exec`. Do not add `Bash(codex:*)` / `Bash(codex exec:*)` allowlists. Stage A `code` mode is forbidden. Stage B requires exact `--allowed-file` entries and never stages, commits, pushes, restores, or merges.

Allowed Stage A modes: `plan` / `review` / `summarize` / `debug`.
Allowed Stage B mode: `write`.
Preferred model: `gpt-5.5` (the only model the local ChatGPT-account Codex backend accepted during the Stage A/B smokes; other candidates including `gpt-5.1-codex`, `gpt-5`, `gpt-5-codex`, `gpt-5.1`, `o3`, and `gpt-4o` were rejected with HTTP 400).
Effort guidance: `low` for quick sanity checks, `medium` for normal review critique, `high` for row-family or invariant-boundary analysis and for Stage B write work.

Use the bridges only at high-leverage points: row-family design, competing invariant choices, unresolved validation failure after local inspection, scope ambiguity, possible TLICA boundary violation, pre-review-gate adversarial check, pre-final-audit critique, and (Stage B only) bounded single-file doc drafts whose exact path is on the allowlist.

The wrappers write hash-only audit JSONL under `.claude/codex_bridge_logs/`, which is gitignored. Do not commit those logs.

More than three real Codex calls in a single step requires fresh operator approval. Stage B is never to be used for staging / committing / pushing — parent Claude does that after inspecting the diff.

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

Next:
- <next campaign step or stop condition>
```

Stop according to `CURRENT_CAMPAIGN.md` and do not pass a review gate without a fresh instruction.
