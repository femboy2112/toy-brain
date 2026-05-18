# PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md

## Campaign overview

Phase 3.16 is a **measurement-first operational tuning campaign**. It
asks one bounded question:

> Does ToyI's runtime actually perform a model-backed operational walk
> end-to-end against a real model-backed client — or is a precise
> environment / runtime blocker provable?

This is **not** a proof of consciousness, sentience, awareness,
subjective experience, semantic understanding, agency, or
self-modification. None of those properties are introduced, claimed,
or measured. The campaign instruments existing public surfaces, runs
bounded real model calls inside a 30-call budget, and reports
inspectable evidence.

The campaign follows Phase 3.15 L1 Cache Hygiene (PR #18), Stage C.1
dynamic Codex flow orchestrator (PR #19), and Stage C.1 workflow tools
(PR #20). The catalog baseline is v0.25.

```text
Counts:
  REQUIRED:        281
  STRUCTURAL:       88
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
```

---

## Why this campaign exists

`brain/ui/__main__.py --print-once` returns before the LLM runtime
factory is invoked (`build_llm_client_from_config` is only reached after
the terminal-detection short-circuit). So the existing
`--print-once` smoke does **not** exercise a real model-backed tick
route. The only sanctioned real-LLM seams that exist today are:

1. `OperatorSession.dispatch(...)` over an `LLMClient` constructed by
   `brain.ui.llm_runtime.build_llm_client_from_config`, fed by
   operator-queued `QUEUE_PERCEPT` events or the `STREAM_APPEND` +
   `STREAM_PROMOTE` + `STEP_TICK` path.
2. A direct `LLMBackedPtCns` harness constructed against the same
   public `LLMClient` and invoked through `eval()` /
   `eval_map`.
3. The interactive curses TUI (`python3 -m brain.ui --llm-mode ...`),
   when a usable terminal is present.

Phase 3.16 measures whether route (1) and/or route (3) actually
deliver a complete model-backed tick, and how the L1 (CachedClient)
and L2 (LLMBackedPtCns canonical eval cache) layers behave under real
load.

`brain/tick.py` is untouched in Phase 3.16. The runtime is observed,
not modified.

---

## High-level target

A successful Phase 3.16 result includes at least one complete
model-backed tick route where:

```text
- a real model-backed client (codex-cli / claude-cli / anthropic-api)
  is constructed via build_llm_client_from_config
- the model output parses into the canonical ConsistencyEval enum
  without permanent retry failure
- tick() completes (read-only invocation; tick.py is untouched)
- profile / MSI / PtCns / registry / tick_counter / ledger state
  changes are recorded
- L1 (CachedClient) hit/miss/skip behavior is measured
- L2 (LLMBackedPtCns) hit/miss/store/skip behavior is measured
- repeated equivalent work shows no uncontrolled model spam
- all raw prompts / responses / secrets / cache files remain
  uncommitted
- final report classifies as one of:
    REAL MODEL TEST PASS / PARTIAL / BLOCKED BY ENV / FAIL
```

---

## Real model call budget

```text
Max 30 real external model-backed calls TOTAL across the campaign.
Count every attempt (success, retry, parse failure, timeout, nonzero
  exit) toward the budget.
Stop before exceeding 30.
If call count cannot be proven from logs, assume the higher number.
Use cache-aware repeated probes after the first miss.
No unbounded loops; no "keep trying forever."
```

---

## Preferred model-backed mode order

```text
1. codex-cli         (local Codex CLI; reuses any existing login)
2. claude-cli        (local Claude Code CLI in non-interactive mode)
3. anthropic-api     (direct HTTP; requires ANTHROPIC_API_KEY env)
```

Phase 3.16 uses the first available mode. It is not required to
exercise all three. If no mode is available, the audit produces
**REAL MODEL TEST BLOCKED BY ENV** showing exactly what is missing
(redacted).

---

## Global hard constraints

```text
do not push to main
work on a campaign branch
commit and push each successful file-changing step
do not merge any PR
do not edit brain/tick.py
do not alter L2 eval_v1 semantics
do not alter L1 cache semantics unless a new review gate authorizes
do not alter Growth Ledger / Pattern Ledger / Coherence Monitor
  semantics
do not implement SelfModel
do not add UI unless explicitly reviewed
do not change DB schema or SCHEMA_VERSION
do not add persistence / autosave behavior
do not commit raw prompts
do not commit raw model responses
do not commit cache files (brain/.llm_cache is gitignored)
do not commit secrets
do not print secrets into reports
no hidden model calls
OFFLINE remains default
model-backed modes remain explicit opt-in
no consciousness / sentience / subjective-experience /
  semantic-understanding / truth / agency / self-modification claims
no aggregate growth / awareness / I-ness score
```

---

## Workflow tools

Use the helpers landed by PR #20.

### Campaign state

```bash
python3 -m tools.claude_helpers.campaign_state summary
python3 -m tools.claude_helpers.campaign_state json
```

Detect stale mission / campaign routing and next-step drift.

### Gate runner

```bash
python3 -m tools.claude_helpers.gate_runner
python3 -m tools.claude_helpers.gate_runner --json
```

Covers the five canonical gates:

```text
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

If `gate_runner` itself has any issue, fall back to running the five
canonical commands directly.

### Flow manifest validation

Before every Stage C.1 flow call:

```bash
python3 -m tools.claude_helpers.flow_manifest validate \
  /tmp/<manifest>.json --strict
python3 -m tools.claude_helpers.flow_manifest summary \
  /tmp/<manifest>.json
```

Fix manifest errors before invoking Codex.

---

## Stage C.1 flow orchestration

Use only:

```bash
python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py \
  --manifest <manifest path> --model gpt-5.5 --effort high
```

Or the slash form `/orchestrate-flow-with-codex <task>`. Do **not**
invoke raw `codex` or `codex exec`.

Stage C.1 constraints:

```text
manifest uses nodes, not waves
max 2 active Codex nodes
isolated nodes may run in parallel
chained nodes require explicit depends_on
same-file sequential writes require explicit dependency
no write/write collision among active nodes
no read/write collision among active nodes
no automatic retry
stop on CODEX_NETWORK_TRANSIENT unless operator authorizes retry
more than 3 Codex nodes requires --operator-approved-over-three-calls
absolute hard cap is 8 nodes
for this campaign: max total Stage C.1 real Codex nodes = 5 unless
  operator approves more
parent Claude validates, stages, commits, pushes
Codex never stages, commits, pushes, restores, rebases, or merges
```

Stage C.1 is appropriate for:

```text
drafting Phase 3.16 roadmap / synthesis docs
drafting report files after measurements exist
mechanical non-runtime helper / report shards
optionally bounded test harness files if a review gate authorizes
```

Stage C.1 is **forbidden** for:

```text
running the real model loop itself
touching secrets
committing cache files
broad runtime changes
brain/tick.py
final catalog reconciliation
```

---

## Step-by-step plan

### Step 1 — Repo-state sync and Phase 3.16 mission install

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git status --short --branch
git log --oneline -20
python3 -m tools.claude_helpers.campaign_state summary || true
python3 -m tools.claude_helpers.campaign_state json     || true
python3 -m tools.claude_helpers.gate_runner --json
git switch -c campaign/phase3-16-real-model-operational-tuning
```

Edit (parent Claude direct writes):

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md
```

Commit message:

```text
phase3.16 step1: real model tuning mission sync
```

Push.

### Step 2 — Real model tuning synthesis

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_SYNTHESIS.md
```

Must cover: what "actual testing" means for ToyI; available modes;
why `--print-once` is not a model test; why an in-process harness or
TUI route is needed; budget; route candidates A / B / C; success
criteria; stop conditions; secrecy + cache discipline; disclosure
blocks.

Stage A review allowed; Stage C.1 draft allowed.

Commit message:

```text
phase3.16 step2: real model tuning synthesis
```

### Step 3 — Model availability + deterministic baseline

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_MODEL_AVAILABILITY_BASELINE.md
```

Probe `codex` / `claude` / API key env presence (redacted). Run a
deterministic mock / offline tick through `OperatorSession.dispatch`
or a direct `LLMBackedPtCns` route. Verify no real model calls.

Commit message:

```text
phase3.16 step3: model availability + deterministic baseline
```

### Step 4 — Real model smoke and tuning run

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_RUN.md
```

Pick the first available mode. Build the client through
`build_llm_client_from_config`. Run a minimal tick route. Record call
count, parse outcomes, retries, L1 and L2 counters, state changes,
cache file count, tick result. Tune only via allowed levers.

Commit message:

```text
phase3.16 step4: real model smoke and tuning run
```

### Step 5 — Findings / blocker triage

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_FINDINGS.md
```

Classify the result. Decide path forward.

Commit message:

```text
phase3.16 step5: real model tuning findings
```

### Step 6 — Optional reviewed patch plan

Only if Step 5 says patch required.

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_PATCH_PLAN.md
```

Stop for review gate.

### Step 7 — Apply accepted patch

Only if Step 6 was accepted. Never touch `brain/tick.py`. Never alter
L2 (eval_v1). Never alter L1 cache semantics without a new review gate.

### Step 8 — Post-patch / final behavior report

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_BEHAVIOR_REPORT.md
```

Concrete evidence and counters.

Commit message:

```text
phase3.16 step8: real model tuning behavior report
```

### Step 9 — Final audit

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_AUDIT.md
```

Verdict: `REAL MODEL TEST PASS` / `PARTIAL` / `BLOCKED BY ENV` /
`FAIL`. Full constraint confirmations.

Commit message:

```text
phase3.16 step9: real model tuning final audit
```

### Step 10 — PR preparation

Open PR to main with title:

```text
phase3.16: real model operational tuning
```

PR body covers branch, calls, mode, verdict, route, cache behavior,
patch decision, deferred work, bridge usage. Do **not** merge.

---

## Success / blocked / failed criteria

```text
REAL MODEL TEST PASS
  - one or more complete model-backed tick routes recorded
  - parseable consistency eval observed
  - L1 + L2 counters observable
  - no patch required
  - cumulative call count <= 30

REAL MODEL TEST PARTIAL
  - some progress, but at least one acceptance criterion not met
    cleanly (e.g., parse failure on first try, recovered via tuning)
  - cumulative call count <= 30

REAL MODEL TEST BLOCKED BY ENV
  - no model-backed mode available locally
  - report shows exactly which mode is missing what
  - no real model calls used

REAL MODEL TEST FAIL
  - real model was reachable but the operational walk could not be
    completed within the budget
  - report shows exactly where the route broke and why
```

---

## Deferred items (not promoted in Phase 3.16)

```text
- SelfModel implementation
- /pattern-ledger UI         (I-PLEDGER-17 DEFERRED)
- /coherence-summary UI      (I-COHMON-13 DEFERRED)
- /growth-ledger UI          (I-GROW-21 DEFERRED)
- end-to-end Pattern Ledger / Coherence Monitor / Growth Ledger
  dry-run helpers
- I-LLMCACHE-21 catalog-status change (Phase 3.16 may produce
  observation evidence but does not commit to a status change)
- I-LLMCACHE-22 catalog-status change
- SQLite backup wording note carried from Phase 3.10c
```

---

## Non-goals

```text
no SelfModel implementation
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no L2 (eval_v1) semantic change
no L1 cache semantic change without a new review gate
no tick semantic change (brain/tick.py is not edited)
no proof or claim of consciousness / sentience / subjective
  experience / semantic understanding / truth / agency /
  self-modification
no aggregate consciousness / sentience / awareness / I-ness / growth
  score
no model-backed behavior as default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no hidden autosave behavior
no DB schema change in v1
no /save-session / /load-session / autosave extension in v1
no raw prompts / responses / secrets / cache files committed
no UI expansion unless reviewed
no raw codex invocation
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
```
