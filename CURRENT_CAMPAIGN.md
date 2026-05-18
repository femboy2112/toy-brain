# CURRENT_CAMPAIGN.md — Phase 3.16 Real Model Operational Tuning

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.16 follows the completed Phase 3.15 L1 Cache Hygiene campaign
(PR #18). Phase 3.15 shipped:

```text
L1 CachedClient bounded at L1_CACHE_MAX_ENTRIES = 1024 (write-skip-
  at-cap admission; no eviction; corrupt entries still fail loud)
I-LLMCACHE-23..28 (new) + I-LLMCACHE-20 promotion to REQUIRED
Catalog v0.25
Counts:
  REQUIRED:        281
  STRUCTURAL:       88
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
```

Subsequent merges on main:

```text
PR #19  Stage C.1 dynamic Codex flow orchestrator
        (.claude/agents/chatgpt-codex-flow-orchestrator.md;
         .claude/commands/orchestrate-flow-with-codex.md;
         tools/claude_helpers/codex_chatgpt_flow_orchestrator.py)
PR #20  Stage C.1 workflow helper tools
        (tools/claude_helpers/campaign_state.py;
         tools/claude_helpers/gate_runner.py;
         tools/claude_helpers/flow_manifest.py)
```

Phase 3.16 asks the next bounded question:

```text
Does ToyI's runtime actually perform a model-backed operational walk
end-to-end against a real model-backed client - accepting stream/text
input, promoting candidate/input into the event path, executing a
/step or equivalent tick path through the real LLM transport,
receiving a parseable consistency eval, updating bounded inspectable
state, and exposing cache + call-count behavior - or is a precise
environment / runtime blocker provable?

This is not a proof of consciousness. It is an operational tuning
campaign.
```

Phase 3.16 does **not** implement SelfModel, and does **not** modify
brain/tick.py, Growth Ledger semantics, Pattern Ledger semantics,
Coherence Monitor semantics, L2 (eval_v1) semantics, persistence /
autosave, observability, scenarios, traces, the SQLite schema, or any
guarded kernel path before the Phase 3.16 review gate.

Preferred campaign branch:

```text
campaign/phase3-16-real-model-operational-tuning
```

Preferred final PR title:

```text
phase3.16: real model operational tuning
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
never edit brain/tick.py in Phase 3.16
```

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

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

## Baseline

Expected current state:

```text
Catalog: v0.25
Counts:
  REQUIRED:        281
  STRUCTURAL:       88
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:  Phase 3.15 L1 Cache Hygiene (PR #18)
Latest merged PRs:          PR #18 (Phase 3.15 L1 Cache Hygiene),
                            PR #19 (Stage C.1 flow orchestrator),
                            PR #20 (Stage C.1 workflow tools)
Current campaign:           Phase 3.16 Real Model Operational Tuning
Next eligible step:         Step 1 repo-state sync and Phase 3.16
                            mission install (this file's first step)
Canonical design seed:      PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md
```

Inherited follow-ups deliberately deferred:

```text
- SelfModel implementation remains OUT OF SCOPE.
- /pattern-ledger UI is DEFERRED (I-PLEDGER-17).
- /coherence-summary UI is DEFERRED (I-COHMON-13).
- /growth-ledger UI is DEFERRED (I-GROW-21).
- end-to-end Pattern Ledger / Coherence Monitor / Growth Ledger dry-run
  helpers remain NOT-EXERCISED.
- Real external model-backed cache smoke (I-LLMCACHE-21) remains
  NOT-EXERCISED unless a future review gate authorizes a promotion.
  Phase 3.16 may produce observation evidence toward I-LLMCACHE-21
  without committing to a catalog status change.
- End-to-end Phase 3.14 behavior probe (I-LLMCACHE-22) remains
  NOT-EXERCISED.
```

---

## Operational target

Phase 3.16 uses this operational definition:

```text
real model-backed operational walk:
  one or more complete tick routes where
    - a real model-backed client (codex-cli OR claude-cli OR
      anthropic-api) is constructed via the repo runtime factory
      (build_llm_client_from_config) and used through the public
      session dispatch or a direct tick harness
    - operator input enters via the public stream/percept path
      (QUEUE_PERCEPT and/or STREAM_APPEND + STREAM_PROMOTE +
      STEP_TICK in OperatorSession.dispatch) or via a direct
      LLMBackedPtCns route constructed from public surfaces
    - the model output parses into ConsistencyEval (PRESERVE /
      DAMAGE / NEUTRAL) without permanent retry failure
    - tick completes through brain.tick.tick (read-only invocation;
      brain/tick.py is not edited)
    - inspectable state (profile / MSI / PtCns / registry / tick
      counter / ledger events as available) reflects the result
    - L1 (CachedClient) hit/miss/skip counters are recorded
    - L2 (LLMBackedPtCns) hit/miss/store/skip counters are recorded
    - repeated equivalent work does not spam the model
    - no raw prompts, raw responses, secrets, or cache files are
      committed
    - final report classifies the result as
        REAL MODEL TEST PASS    /
        REAL MODEL TEST PARTIAL /
        REAL MODEL TEST BLOCKED BY ENV /
        REAL MODEL TEST FAIL
```

---

## Real model call budget

```text
Max 30 real external model-backed calls total across the campaign.
Count every model-backed attempt, including retries, timeouts, parse
  failures, and nonzero exits.
Stop before exceeding 30.
If call count cannot be proven from logs, assume the higher number.
Use cache-aware repeated probes after the first miss.
No unbounded loops; no "keep trying forever."
```

---

## Non-goals

```text
no SelfModel implementation in Phase 3.16
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no L2 (eval_v1) semantic change
no L1 cache semantic change without a new review gate
no proof or claim of consciousness
no claim of sentience
no claim of subjective experience
no claim of semantic understanding
no truth adjudication or PRESERVE / DAMAGE judgment from raw text
no claim of agency / intent / will / desire
no claim of self-modification
no aggregate consciousness / sentience / awareness / I-ness / growth
  score
no model-backed behavior as default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no silent repair calls
no hidden autosave behavior
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
no DB schema change in v1 unless explicitly planned and accepted
no SCHEMA_VERSION bump
no /save-session / /load-session / autosave extension in v1
no tick semantic change (brain/tick.py is not edited in Phase 3.16)
no raw prompts or model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
```

---

## Macro sequence

```text
Step 1   Repo-state sync and Phase 3.16 mission install
Step 2   Real model tuning synthesis
Step 3   Model availability and deterministic baseline report
Step 4   Real model smoke and tuning run
Step 5   Findings / blocker triage
Step 6   Optional reviewed patch plan if runtime changes are needed
Step 7   Apply accepted patch only if Step 6 authorizes it
Step 8   Post-patch or final behavior report
Step 9   Final audit
Step 10  PR preparation
```

If Step 4 produces a clean useful result and no patch is required,
Steps 6-7 are skipped and the campaign proceeds to Step 8.

Every step that lands files must pass the standard preflight gates
before commit and must push the campaign branch on success:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

(or, if `gate_runner` itself fails, fall back to:)

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

---

## ChatGPT/Codex consultation policy

The repository ships three explicit, sanctioned Claude → Codex CLI →
ChatGPT bridges. Use them at high-leverage points only. The full
bridge policy lives in `CURRENT_MISSION.md`. This file restates only
what each step must do.

```text
Stage A wrapper:  python3 tools/claude_helpers/codex_chatgpt_subagent.py
Stage A modes:    plan / review / summarize / debug
Stage A slash:    /ask-chatgpt
Stage B wrapper:  python3 tools/claude_helpers/codex_chatgpt_write_worker.py
Stage B modes:    write
Stage B slash:    /ask-chatgpt-write
Stage C.1 wrapper: python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py
Stage C.1 shape:  dynamic DAG; max 2 active nodes; isolated nodes may
                   run in parallel; chained nodes require depends_on;
                   no automatic retry; hard cap 8 nodes;
                   campaign cap 5 nodes unless operator approves more
Stage C.1 slash:  /orchestrate-flow-with-codex
```

Stage A is allowed at: synthesis / catalog patch plan / behavior report
/ final audit adversarial review.

Stage B is allowed at: bounded single-file doc drafts whose exact path
is on the allowlist.

Stage C.1 is allowed for:

```text
Step 1   roadmap draft (optional; parent Claude may write directly)
Step 2   synthesis doc draft (single-node or multi-node disjoint shards)
Step 3   not used for the live deterministic baseline; allowed only
         for mechanical document drafting after measurements exist
Step 4   never used for running the real model loop itself
Step 5   findings doc draft only after measurements exist
Step 6   patch plan draft only
Step 7   limited implementation shards only if Step 6 authorizes it,
         never touching brain/tick.py
Step 8   post-patch behavior report doc draft only after measurements
Step 9   final audit doc draft only after measurements
Step 10  PR body draft only
```

Stage C.1 is **forbidden** at:

```text
never    raw codex / codex exec invocation
never    running the real model loop itself
never    touching secrets
never    committing cache files
never    broad runtime changes
never    brain/tick.py edits
never    final catalog reconciliation (parent Claude owns the catalog
         and counter reconciliation directly)
never    overlapping write sets among active nodes
never    declared read/write collisions among active nodes
never    staging / commit / push (parent Claude does that after
         inspecting the diff)
```

Before every Stage C.1 wave:

```bash
python3 -m tools.claude_helpers.flow_manifest validate \
  /tmp/<manifest>.json --strict
python3 -m tools.claude_helpers.flow_manifest summary \
  /tmp/<manifest>.json
```

Every step report must include the Stage A / Stage B / Stage C.1
disclosure block defined in `CURRENT_MISSION.md`.

---

# Step 1 — Repo-state sync and Phase 3.16 mission install

Purpose: replace the Phase 3.15 mission/campaign routing prose with
Phase 3.16 Real Model Operational Tuning as current, and land the
Phase 3.16 roadmap at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md
```

Forbidden in Step 1:

```text
brain/**
tools/**
.claude/**
INVARIANT_CATALOG.md
README.md
docs/campaigns/**
lean_reference/**
scenarios/**
traces/**
no fixtures
no code
```

Required work:

```text
sync fresh main and create branch
  campaign/phase3-16-real-model-operational-tuning
run gate_runner --json green
write Phase 3.16 CURRENT_MISSION.md (parent Claude)
write Phase 3.16 CURRENT_CAMPAIGN.md (parent Claude)
write PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md
  (parent Claude direct write; Stage C.1 optional)
inspect git status / git diff to confirm only the three allowed
  files changed
```

Validation:

```bash
python3 -m tools.claude_helpers.gate_runner --json
python3 -m tools.claude_helpers.campaign_state summary
git status --short
git diff -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md \
  PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md
```

Commit message:

```text
phase3.16 step1: real model tuning mission sync
```

Push.

---

# Step 2 — Real model tuning synthesis

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_SYNTHESIS.md
```

Required content:

```text
what "actual testing" means for ToyI in operational terms
available model-backed modes and their preference order
why --print-once is NOT a model test (returns before LLM client
  construction in brain/ui/__main__.py)
why an in-process harness or interactive TUI route is needed
real model-call budget (30) and accounting policy
route candidates:
  A. in-process OperatorSession dispatch route through public
     QUEUE_PERCEPT / STEP_TICK and/or STREAM_APPEND / STREAM_PROMOTE
     /STEP_TICK using build_default_session +
     build_llm_client_from_config
  B. interactive TUI route if a usable TTY is available
  C. direct tick harness using LLMBackedPtCns over a public
     LLMClient, exercising eval() / eval_map without touching
     brain/tick.py
success criteria
stop conditions (budget reached / 10 consecutive parse failures /
  real model unavailable / runtime code change seems needed)
raw prompt / response / secret secrecy constraints
cache discipline constraints (L1 bounded at 1024; L2 bounded at
  1024; no commit of cache files)
disclosure blocks
next artifact: model availability + deterministic baseline (Step 3)
```

Stage A review is allowed but optional given the bounded scope.

Commit message:

```text
phase3.16 step2: real model tuning synthesis
```

Push.

---

# Step 3 — Model availability + deterministic baseline

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_MODEL_AVAILABILITY_BASELINE.md
```

Probe (secrets redacted in the report):

```text
command -v codex; codex --version; codex login status
command -v claude; claude --version
env keys (presence only, never values):
  BRAIN_LLM_MODE
  BRAIN_ANTHROPIC_API_KEY
  ANTHROPIC_API_KEY
```

Use repo surfaces:

```text
parse_llm_runtime_args
build_llm_client_from_config
```

Run deterministic baseline using mock / offline only:

```text
build_default_session
OperatorSession.dispatch with QUEUE_PERCEPT + STEP_TICK (or the
  STREAM_APPEND + STREAM_PROMOTE + STEP_TICK path) under
  OfflineStandInClient or MockClient
verify inspectable state change (tick counter, ptcns eval map)
verify no real model calls happened
```

If in-process command parsing is required, inspect
`brain/ui/command_line.py` and `brain/ui/session.py`. Do not invent
commands.

Stage C.1 may draft the document only after measurements exist.

Commit message:

```text
phase3.16 step3: model availability + deterministic baseline
```

Push.

---

# Step 4 — Real model smoke and tuning run

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_RUN.md
```

Pick first available real model-backed mode in this preference order:

```text
1. codex-cli
2. claude-cli
3. anthropic-api
```

Use the model-backed client through the repo runtime factory
(`build_llm_client_from_config`), not ad-hoc subprocesses, unless
testing CLI availability.

Run minimal route:

```text
short input 1
short input 2 if budget permits
promote / queue candidate through public route (QUEUE_PERCEPT or
  STREAM_APPEND + STREAM_PROMOTE)
run STEP_TICK or direct LLMBackedPtCns.eval path
inspect state
```

Measure and report:

```text
call count (real model attempts)
parse success / failure
retry count
L1 cache hits / misses / skips
L2 hits / misses / stores / skips
tick result
state changes (profile / MSI / PtCns / registry / tick_counter)
ledger events if observable
cache file count under brain/.llm_cache (counts only, not contents)
```

Allowed tuning levers on a failed first attempt:

```text
shorter input text
clearer input text
different available model-backed mode
timeout increase
cache on / off diagnostic ONCE only (final route uses normal
  cache-on behavior)
direct tick harness vs session dispatch if one path is blocked
```

Forbidden without review gate:

```text
changing prompt template (brain/llm/prompts.py)
changing parser (brain/llm/parse.py)
changing tick (brain/tick.py)
changing cache semantics
changing invariants
```

Stop conditions:

```text
budget reaches 30 (or projected to exceed 30)
10 consecutive parse failures
real model unavailable
runtime code change seems needed
```

If any stop condition fires, commit the partial report and proceed to
Step 5 triage.

Commit message:

```text
phase3.16 step4: real model smoke and tuning run
```

Push.

---

# Step 5 — Findings / blocker triage

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_FINDINGS.md
```

Classify result as one of:

```text
works
partial
blocked by env
parse blocker
runtime bug
model-behavior weak
patch required
deferred enhancement
```

Decision:

```text
- If works / partial and no runtime patch required:
    proceed to Step 8/final report.
- If blocked by env:
    proceed to final audit with BLOCKED BY ENV.
- If patch required:
    create Step 6 patch plan and stop for review gate.
```

Commit message:

```text
phase3.16 step5: real model tuning findings
```

Push.

---

# Step 6 — Optional reviewed patch plan

Only if Step 5 classifies the result as patch required.

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_PATCH_PLAN.md
```

Must specify:

```text
exact files
exact behavior change
exact risks
whether catalog rows needed
whether review gate allows implementation
```

Do not implement until explicit review gate clears the plan.

Commit message:

```text
phase3.16 step6: real model tuning patch plan
```

Push.

---

# Step 7 — Apply accepted patch

Only if Step 6 was accepted.

Allowed files depend on the accepted plan. `brain/tick.py` MAY NOT be
touched in Phase 3.16. L2 (eval_v1) semantics MAY NOT be changed. L1
cache semantics MAY NOT be changed without a new review gate.

Run every preflight gate green. Commit and push.

Commit message:

```text
phase3.16 step7: real model tuning patch
```

---

# Step 8 — Post-patch / final behavior report

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_BEHAVIOR_REPORT.md
```

Summarize the final model-backed behavior result with concrete
evidence (call counts, cache counts, state changes).

Commit message:

```text
phase3.16 step8: real model tuning behavior report
```

Push.

---

# Step 9 — Final audit

Create:

```text
docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_AUDIT.md
```

Validation (canonical preflight):

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

Verdict must be exactly one of:

```text
REAL MODEL TEST PASS
REAL MODEL TEST PARTIAL
REAL MODEL TEST BLOCKED BY ENV
REAL MODEL TEST FAIL
```

Required content:

```text
verdict
files changed across the campaign
gate results
cumulative real model call count
mode tested
explicit "no SelfModel implementation" confirmation
explicit "no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim" confirmation
explicit "no aggregate awareness / I-ness / growth score" confirmation
explicit "no hidden LLM call / hidden persistence / DB schema change
  in v1" confirmation
explicit "no L2 (eval_v1) semantic change" confirmation
explicit "no tick semantic change (brain/tick.py untouched)"
  confirmation
explicit "no raw prompts / responses / cache files / secrets
  committed" confirmation
explicit "OFFLINE remains default; model-backed remains explicit
  opt-in" confirmation
Stage A / Stage B / Stage C.1 bridge usage disclosure across the
  campaign
next-campaign note
```

Commit message:

```text
phase3.16 step9: real model tuning final audit
```

Push.

---

# Step 10 — PR preparation

Open a PR to main with title:

```text
phase3.16: real model operational tuning
```

PR body must include:

```text
completed steps
validation results
real model mode tested
total real model calls used
result verdict
whether ToyI produced a complete model-backed tick route
cache behavior summary (L1 + L2)
whether a patch was needed
behavior findings summary
review gates reached
remaining deferred work
confirmation main was not pushed directly during campaign execution
confirmation PR is not merged
Stage A / Stage B / Stage C.1 bridge usage summary
```

Do not merge.
