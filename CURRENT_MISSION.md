# CURRENT_MISSION.md — Phase 3.13 Growth Ledger Entry Point

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must read this file, read `CURRENT_CAMPAIGN.md`, create or continue the active campaign branch, run the next eligible campaign step, commit successful results, push the branch, and stop exactly where the campaign says to stop.

---

## Current mission

Execute the **Phase 3.13 Growth Ledger Campaign** in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.13 follows the completed Phase 3.12 Coherent I-Loop Observatory and the docs-archive / ChatGPT advisory bridge cleanup that landed alongside it. Phase 3.13 implements **Growth Ledger first**. It does **not** implement Operational SelfModel. The Phase 3.12 Step 15 roadmap recommends Growth Ledger before SelfModel because SelfModel should later quote bounded growth facts rather than infer growth from current state alone.

Campaign target:

```text
Phase 3.13 Step 1     repo-state sync and Phase 3.13 mission install
Phase 3.13 Step 2     Growth Ledger synthesis
Phase 3.13 Step 3     Growth Ledger kickoff
Phase 3.13 Step 4     Growth Ledger corrigenda
Phase 3.13 Step 5     Growth Ledger catalog patch plan
Phase 3.13 Step 6     Review Gate A — Growth Ledger implementation
Phase 3.13 Step 7     apply accepted Growth Ledger implementation, if approved
Phase 3.13 Step 8     Growth Ledger behavior report
Phase 3.13 Step 9     Growth Ledger findings / triage
Phase 3.13 Step 10    Final Phase 3.13 audit
Phase 3.13 Step 11    Final PR preparation
```

Intended result:

```text
The repo contains a bounded developmental record of accepted, constructor-validated growth events, behind a review gate, with no SelfModel implementation, no consciousness/sentience/subjective/semantic/truth/agency/self-modification claim, no aggregate growth score, and no hidden persistence or LLM call.
```

This mission is measurement-first and design-gated. The Pattern Ledger (`brain/development/pattern_ledger.py`, `I-PLEDGER-01..18`) and Coherence Monitor (`brain/development/coherence_monitor.py`, `I-COHMON-01..14`) already provide bounded structural-recurrence evidence and bounded read-only consistency reporting. Growth Ledger adds the third bounded substrate: bounded historical accepted-event evidence. SelfModel remains explicitly out of scope.

---

## Branch / push / PR rule

Preferred branch:

```text
campaign/phase3-13-growth-ledger
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
Catalog: v0.22
Counts:
  REQUIRED:        240
  STRUCTURAL:       85
  NOT-EXERCISED:    11
  DEFERRED:         14
  OBSERVED:         16
Latest completed campaign:    Phase 3.12 Coherent I-Loop Observatory
Latest cleanup merged:        docs archive (PR #12)
Available advisory bridge:    Stage A /ask-chatgpt through Codex CLI wrapper
                              (PR #13)
Canonical Phase 3.13 design seed:
  docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
Current mission:              Phase 3.13 Growth Ledger
Next eligible step:           Step 1 repo-state sync and Phase 3.13 mission install
```

Stop if the catalog counts disagree or if the Phase 3.12 roadmap seed is missing.

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
.claude/agents/brain-current-mission.md
.claude/agents/chatgpt-codex-subagent.md
.claude/commands/go.md
.claude/commands/ask-chatgpt.md
tools/claude_helpers/codex_chatgpt_subagent.py
CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md
docs/README.md
docs/campaigns/README.md
docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
docs/campaigns/phase3_12/PHASE3_12_COHERENT_I_LOOP_AUDIT.md
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/ui/session.py
brain/tick.py
tools/check_all.sh
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Phase 3.13 architectural guardrails

Preserve these constraints throughout Phase 3.13:

```text
no SelfModel implementation in Phase 3.13
no consciousness claim
no sentience claim
no subjective-experience claim
no semantic-understanding claim
no truth adjudication / PRESERVE / DAMAGE judgment from raw text
no agency claim
no self-modification claim
no aggregate consciousness / sentience / awareness / I-ness / growth score
no model-backed default behavior; offline remains the default
no hidden LLM calls
no hidden persistence
no DB schema changes in v1 unless explicitly planned and accepted at the review gate
no real external LLM smoke beyond the sanctioned Stage A /ask-chatgpt bridge
Growth Ledger counts accepted, constructor-validated events only
failed parse / failed dispatch / failed tick / read-only command do not count
the existing outcome-detection contract (Phase 3.10c autosave precedent)
  is the canonical filter for "successful mutation"
COGITO_ID remains reserved on every id-bearing Growth Ledger field
no Growth Ledger field equals COGITO_ID
no Growth Ledger event mutates BrainState / MSI / PtCns / ContentRegistry
  / source histories / OperatorSession.event_queue / stream history /
  stream candidates / stream_chunk_serial / Pattern Ledger / Coherence
  Monitor records / persistence config / autosave config
no tick() call inside the Growth Ledger
no LLM client field; no eval_consistency-bearing object stored or accepted
copy-on-write history discipline (observe returns a NEW ledger)
anti-Goodhart deduplication and saturation (no inflation under spam)
references-only event records — no raw text payload
session-local first; no save-session / load-session / autosave extension in v1
```

The permitted experimental framing is:

```text
bounded accepted-event accumulation
constructor-validated growth events
session-local developmental history
references-only event records
read-only quotation of upstream substrates (Pattern Ledger, Coherence Monitor)
```

The prohibited framing is:

```text
proof or claim of consciousness
unbounded self-modification
semantic truth authority from raw text
model-backed default behavior
hidden LLM calls
hidden autosave or hidden persistence
aggregate growth / I-ness / awareness score
SelfModel implementation
```

---

## ChatGPT/Codex consultation (Stage A bridge)

This repository now ships an explicit Claude → Codex CLI → ChatGPT advisory bridge (PR #13). Stage A is read-only, transport + policy bounded, and advisory only.

Use only the sanctioned Stage A path:

```text
slash command:
  /ask-chatgpt --mode <mode> --model gpt-5.5 --effort <effort> <prompt>

direct wrapper:
  python3 tools/claude_helpers/codex_chatgpt_subagent.py \
    --mode <mode> --model gpt-5.5 --effort <effort> \
    --timeout <seconds> --prompt-file <path>
```

The direct wrapper is the policy boundary. Do not invoke raw `codex` or `codex exec`. Do not add `Bash(codex:*)` / `Bash(codex exec:*)` allowlists. Do not use `code` mode. Do not ask Codex to produce patches. Do not apply Codex suggestions automatically.

Allowed Stage A modes: `plan` / `review` / `summarize` / `debug`.
Preferred model: `gpt-5.5` (the only model the local ChatGPT-account Codex backend accepted during the Stage A smoke; other candidates including `gpt-5.1-codex`, `gpt-5`, `gpt-5-codex`, `gpt-5.1`, `o3`, and `gpt-4o` were rejected with HTTP 400).
Effort guidance: `low` for quick sanity checks, `medium` for normal review critique, `high` only for row-family or invariant-boundary analysis.

Use the bridge only at high-leverage points: row-family design, competing invariant choices, unresolved validation failure after local inspection, scope ambiguity, possible TLICA boundary violation, pre-review-gate adversarial check, pre-final-audit critique.

The wrapper writes hash-only audit JSONL under `.claude/codex_bridge_logs/`, which is gitignored. Do not commit those logs.

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

ChatGPT/Codex consultation:
- used: yes / no
- mode / model / effort: <values or n/a>
- wrapper command: <command or n/a>
- question file: <path or n/a>
- answer file: <path or n/a>
- wrapper status: <exit code + error class or n/a>
- accepted advice: <bullets or none>
- rejected advice: <bullets or none>
- reason: <one sentence>

Next:
- <next campaign step or stop condition>
```

Stop according to `CURRENT_CAMPAIGN.md` and do not pass a review gate without a fresh instruction.
