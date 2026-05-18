# CURRENT_CAMPAIGN.md — Phase 3.17 Codex Runtime Fix + Processing Window Research

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.17 follows the completed Phase 3.16 Real Model Operational
Tuning campaign (PR #21). Phase 3.16 shipped:

```text
- A complete real-model-backed operational walk through
  OperatorSession.dispatch under claude-cli.
- L1 (CachedClient) miss / hit / skip counters exercised end-to-end.
- L2 (eval_v1) canonical semantic cache hit verified for identical
  text under a different content_id.
- 6 / 30 real model calls used.
- An explicit, deferred follow-up: codex-cli 0.130.0 refuses to run
  from cwd=/tmp without --skip-git-repo-check; the campaign recorded
  the blocker but did not patch the runtime.
- catalog v0.25 unchanged (281 REQUIRED / 88 STRUCTURAL /
  14 NOT-EXERCISED / 15 DEFERRED / 16 OBSERVED).
```

Phase 3.17 asks two bounded questions in series:

```text
1. Does adding "--skip-git-repo-check" to CodexCLIClient.command
   unblock the codex-cli runtime through the public
   OperatorSession.dispatch + brain.tick.tick path, with no other
   runtime change, no L1 / L2 cache semantic change, no parser /
   prompt / tick change, and (expected) no catalog count change?

2. What is the smallest, safest, inspectable architecture for a
   bounded post-input processing window of N internal ticks
   following an external input? The campaign uses N = 50 as the
   initial experimental default and proves the design out using
   the existing public surfaces (no kernel patch shipped in v1).
```

This is a **research** campaign toward an operationally learning /
growing "I" approximation. It is **not** a proof of consciousness.

Phase 3.17 does **not** implement SelfModel, does **not** modify
Growth Ledger / Pattern Ledger / Coherence Monitor semantics, does
**not** modify L2 (eval_v1) semantics, does **not** modify L1 cache
semantics, does **not** modify `brain/tick.py`, the parser, or the
prompt, and does **not** modify persistence / autosave / observability /
the SQLite schema. The single runtime touch is to
`CodexCLIClient.command` and the codex-cli factory in
`brain/llm/client.py` + `brain/ui/llm_runtime.py`. Catalog rows for
`I-LLMTOG-16` / `I-LLMTOG-17` may need their fixture-side
expectations refreshed to mention the new flag; the **count** is
expected to remain `281 / 88 / 14 / 15 / 16`.

Preferred campaign branch:

```text
campaign/phase3-17-codex-processing-window
```

Preferred final PR title:

```text
phase3.17: codex runtime and processing window research
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
never edit brain/tick.py in Phase 3.17
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
Latest completed campaign:    Phase 3.16 Real Model Operational
                              Tuning (PR #21)
Current campaign:             Phase 3.17 Codex Runtime Fix +
                              Processing Window Research
Next eligible step:           Step 1 mission sync and roadmap
                              install (this file's first step)
Canonical design seed:        PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md
```

Inherited follow-ups deliberately deferred:

```text
- SelfModel implementation remains OUT OF SCOPE.
- /pattern-ledger / /coherence-summary / /growth-ledger UIs remain
  DEFERRED at catalog level.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- Tracer wiring through OperatorSession.dispatch (F2 from Phase
  3.16) remains DEFERRED.
- Parser ambiguity hardening (F3 from Phase 3.16) remains DEFERRED.
- Runtime processing-window implementation is DEFERRED behind the
  Step 7 review gate.
```

---

## Operational target

Phase 3.17 uses this operational definition:

```text
codex-cli compatibility WORKS iff:
  - LlmRuntimeConfig(mode=CODEX_CLI, ...) factory-builds a real
    CodexCLIClient whose .command contains "--skip-git-repo-check"
  - OperatorSession.dispatch(QUEUE_PERCEPT ...) +
    OperatorSession.dispatch(STEP_TICK, client=cached_codex)
    completes one tick end-to-end with a parseable ConsistencyEval
  - L1 (CachedClient) hit / miss / skip counters and L2 entry
    presence reflect the result
  - no raw prompts, raw responses, secrets, or cache files are
    committed
  - final report classifies the codex result as
      CODEX RUNTIME PASS    /
      CODEX RUNTIME PARTIAL /
      CODEX RUNTIME BLOCKED BY ENV /
      CODEX RUNTIME FAIL

processing window research SHIPS iff:
  - Step 5 produces a synthesis distinguishing external / internal /
    reflective / future-REPL/worldlet tick sources, the 50-tick
    initial default, candidate architectures A–F, and the negative
    control (window 0).
  - Step 6 produces a probe plan with window sizes
    {0, 1, 5, 10, 50}, mode set {mock, claude-cli, codex-cli (if
    fixed)}, input types (motif / contradiction / self-reference /
    valenced / neutral factual), and per-output measurements
    (cache counters, profile / MSI / PtCns deltas, Pattern Ledger /
    Growth Ledger / Coherence Monitor surfaces, status / error
    events), with explicit failure limits.
  - Step 7 produces a v1 implementation plan that the campaign does
    NOT auto-implement; runtime code lands only behind an explicit
    operator-approved review gate.
  - Step 8 ships at least one negative-control experiment using
    only existing public surfaces, with bounded mock-mode evidence
    or a documented blocker.
```

---

## Real model call budget

```text
Max 20 real external model-backed calls total across the campaign.
Count every model-backed attempt, including retries, timeouts,
  parse failures, and nonzero exits.
Stop before exceeding 20.
If call count cannot be proven from logs, assume the higher number.
Use cache-aware repeated probes after the first miss.
No unbounded loops; no "keep trying forever."
```

---

## Non-goals

```text
no SelfModel implementation in Phase 3.17
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no L2 (eval_v1) semantic change
no L1 cache semantic change beyond the codex-cli command tuple fix
no parser change
no prompt change
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
no DB schema change in v1
no SCHEMA_VERSION bump
no /save-session / /load-session / autosave extension in v1
no tick semantic change (brain/tick.py untouched)
no raw prompts or model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no UI expansion unless explicitly reviewed
no raw codex invocation outside the sanctioned bridges
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
no runtime "internal tick" or "processing window" implementation
  in v1 unless Step 7 review gate authorizes it explicitly
```

---

## Macro sequence

```text
Step 1   Mission sync and research roadmap
Step 2   Codex-cli compatibility patch plan
Step 3   Apply codex-cli compatibility fix
Step 4   Codex-cli real model smoke
Step 5   Processing window research synthesis
Step 6   Processing window behavior probe design
Step 7   Optional reviewed implementation plan
Step 8   Mock processing-window initial test
Step 9   Findings / triage
Step 10  Final audit
Step 11  PR preparation
```

If Step 4 produces a clean codex-cli result, Steps 5+ proceed without
further runtime change. If Step 4 reveals a deeper blocker, Steps
5–8 still proceed using mock / claude-cli where appropriate, and
Step 9 records the blocker.

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

Stage A is allowed at: synthesis / patch plan / behavior report /
final audit adversarial review.

Stage B is allowed at: bounded single-file doc drafts whose exact
path is on the allowlist.

Stage C.1 is allowed at:

```text
Step 1   roadmap draft (optional; parent Claude writes directly)
Step 2   patch plan draft (optional)
Step 3   never for the runtime fix itself; the patch lands by parent
         Claude direct edit so the diff and constraints are auditable
Step 4   never for running the real codex-cli loop itself
Step 5   synthesis doc draft (single or multi-node disjoint shards)
Step 6   probe plan doc draft
Step 7   implementation plan doc draft only
Step 8   docs around the test; not the test itself if a runtime
         change would be needed
Step 9   findings doc draft after measurements exist
Step 10  audit doc draft after measurements exist
Step 11  PR body draft only
```

Stage C.1 is **forbidden** at:

```text
never    raw codex / codex exec invocation
never    running the real codex-cli model loop itself
never    touching secrets
never    committing cache files
never    broad runtime changes
never    brain/tick.py edits
never    final catalog reconciliation
never    overlapping write sets among active nodes
never    declared read/write collisions among active nodes
never    staging / commit / push
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

# Step 1 — Mission sync and research roadmap

Purpose: replace the Phase 3.16 mission/campaign prose with
Phase 3.17 as current, and land the Phase 3.17 roadmap at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md
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
  campaign/phase3-17-codex-processing-window
run gate_runner --json green
write Phase 3.17 CURRENT_MISSION.md (parent Claude)
write Phase 3.17 CURRENT_CAMPAIGN.md (parent Claude)
write PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md
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
  PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md
```

Commit message:

```text
phase3.17 step1: codex processing window mission sync
```

Push.

---

# Step 2 — Codex-cli compatibility patch plan

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_CODEX_CLI_COMPAT_PATCH_PLAN.md
```

Required content:

```text
- current CodexCLIClient.command is ("codex", "exec")
- current cwd is "/tmp"
- failure reason: codex-cli 0.130.0 refuses cwd=/tmp without
  --skip-git-repo-check
- preferred fix: command = ("codex", "exec", "--skip-git-repo-check")
- rejected alternative: cwd = repo root (would let codex auto-discover
  the parent repo's CLAUDE.md / hooks)
- exact files to edit:
    brain/llm/client.py
    brain/ui/llm_runtime.py
- whether any fixture under brain/ui/fixtures/ needs a constant or
  command-tuple update (yes if it asserts the exact tuple shape)
- INVARIANT_CATALOG.md status: expected count change = zero;
  bodies of I-LLMTOG-16 / I-LLMTOG-17 may need a one-line
  refresh to mention the new flag without bumping the catalog
  version
- tools/catalog.py: expected no change
- validation plan: gate_runner --json, fixture smoke, manual
  command construction probe
- smoke plan: codex --version / codex exec --help (no real call),
  then construct the client through the factory and run
  CodexCLIClient.eval_consistency on a single short prompt
- raw prompt / response / secret secrecy constraints
- disclosure block
```

Stage A review is allowed but optional.

Commit message:

```text
phase3.17 step2: codex-cli compatibility patch plan
```

Push.

---

# Step 3 — Apply codex-cli compatibility fix

Implement only the accepted small fix unless Step 2 proves more is
needed.

Likely patch:

```text
In brain/llm/client.py:
    CodexCLIClient.command = ("codex", "exec", "--skip-git-repo-check")

In brain/ui/llm_runtime.py::_build_codex_cli_client:
    CodexCLIClient(
        command=(resolved_executable, "exec", "--skip-git-repo-check"),
        timeout_seconds=config.timeout_seconds,
    )
```

Do not change cwd unless the command fix fails.

Add or update at least one fixture under `brain/ui/fixtures/` (or a
catalog-bound fixture) proving:

```text
- CodexCLIClient.command contains "exec"
- CodexCLIClient.command contains "--skip-git-repo-check"
- command is still a bounded tuple of strings
- subprocess is not invoked with shell=True
- no raw broad codex mode is reachable from the factory
- cwd remains "/tmp"
- missing executable still fails early (existing behavior preserved)
```

Run gates.

Forbidden in Step 3:

```text
brain/tick.py
brain/llm/parse.py
brain/llm/prompts.py
brain/llm/ptcns_backed.py
INVARIANT_CATALOG.md beyond a fixture-side body refresh, if at all
tools/catalog.py
schema files
persistence files
autosave files
```

Commit message:

```text
phase3.17 step3: fix codex-cli git repo check
```

Push.

---

# Step 4 — Codex-cli real model smoke

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_CODEX_CLI_REAL_MODEL_SMOKE.md
```

Run actual codex-cli model-backed ToyI route if the environment
permits.

Use call budget <= 10 for this step.

Route:

```text
- build LlmRuntimeConfig(mode=CODEX_CLI, ...)
- build client via build_llm_client_from_config
- queue one short input through OperatorSession.dispatch
- run STEP_TICK
- inspect state / tick / growth ledger / cache
- repeat equivalent input once to test L2 cache if budget allows
```

Record:

```text
- codex --version
- codex login status (presence only; never the token)
- command shape (no secrets)
- calls used (count every attempt incl. failures)
- parse result
- tick result
- cache hit / miss / skip
- L2 behavior
- state changes
- whether route works
```

If codex-cli still fails, stop and report exact blocker.

Commit message:

```text
phase3.17 step4: codex-cli real model smoke
```

Push.

---

# Step 5 — Processing window research synthesis

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_SYNTHESIS.md
```

The synthesis must analyze, per the campaign mission:

```text
- current system limits (one external percept per tick; session
  refuses empty /step; no post-input processing window; ledger /
  pattern / coherence read-only)
- proposed processing-window model: bounded internalization period
  of N internal ticks following an external input; initial N = 50;
  bounded and interruptible; audit-trailed; bounded state
- distinction between external input ticks, internal processing
  ticks, reflective feedback ticks, future REPL/worldlet ticks
- why current session route cannot process an empty queue
- why kernel empty-event ticks are not enough for learning / growth
- candidate architectures:
    A. session-level post-input tick loop using generated internal
       events
    B. new internal event type / internal percept source
    C. reflective REPL feedback generating queued internal events
    D. worldlet / working-memory feedback later
    E. no-op empty tick window as a negative control
    F. delayed consolidation queue
- human analogy used carefully (perception / working memory /
  consolidation / rehearsal / self-monitoring / action selection)
  with explicit "this is an architectural analogy, not a
  consciousness claim"
- testable hypotheses (0 vs 5 vs 10 vs 50 ticks; cache absorbs
  repeats; pattern recurrence becomes more inspectable; coherence
  PASS / WARN but never a scalar I-score)
- minimal v1: do not implement full self-model; do not change tick
  kernel; design an experimental controller / harness first; use
  mock / claude-cli / codex-cli under budgets; report evidence
- success criteria
- non-claims and safety boundaries
- disclosure block
```

Stage C.1 may draft the synthesis as a single-node doc shard.

Commit message:

```text
phase3.17 step5: processing window synthesis
```

Push.

---

# Step 6 — Processing window behavior probe design

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_PROBE_PLAN.md
```

Design experiment matrix:

```text
- window sizes: 0, 1, 5, 10, 50
- modes: mock, claude-cli, codex-cli if fixed
- input types:
    - repeated motif
    - contradiction pair
    - self-reference statement
    - emotionally valenced text
    - neutral factual text
- outputs:
    - tick count
    - model call count
    - cache hit / miss / skip
    - profile domain delta
    - MSI content delta
    - PtCns eval map delta
    - Pattern Ledger entries
    - Growth Ledger entries
    - Coherence Monitor report
    - status / error events
- failure limits:
    - call budget cap
    - cache cap
    - parse failure threshold
    - invariant failure threshold
```

Commit message:

```text
phase3.17 step6: processing window probe plan
```

Push.

---

# Step 7 — Optional implementation plan

Only create implementation plan; do not implement until a fresh
review-gate instruction is issued.

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_IMPLEMENTATION_PLAN.md
```

Plan must specify exact review gate before code.

Potential first implementation (DESIGN ONLY):

```text
- no kernel tick.py change
- new experimental harness under tools/ or
  docs/campaigns/phase3_17/tmp/ (script may NOT be committed unless
  reviewed)
- session-level controller that:
    - accepts one external input
    - runs the normal external tick
    - then runs bounded internal processing candidates generated
      from existing ledgers / coherence summaries
- internal events clearly marked provenance="internal_processing_window"
- bounded max 50
- call budget enforced
- explicit review gate before any of the above is implemented
```

Commit message:

```text
phase3.17 step7: processing window implementation plan
```

Push.

---

# Step 8 — Start actual controlled testing

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_INITIAL_TEST.md
```

Run negative-control tests first using only the existing public
surfaces:

```text
- window 0 control: queue one external input, run STEP_TICK, report
  inspectable state. This is the existing single-tick route.
- window 1 control: optionally queue a second internal-looking event
  whose target_content_id and provenance encode "internal_processing"
  for AUDIT ONLY (no kernel change).
- window N small (e.g. 5) via mock client: queue then promote N
  bounded synthetic events drawn from the live Pattern Ledger /
  Coherence summary, and run STEP_TICK each time, only when this
  can be done WITHOUT touching the kernel.
```

If runtime support is insufficient to do anything beyond the
window-0 control, document exactly why. Do not fake success.

Allowed file scope:

```text
docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_INITIAL_TEST.md
```

Forbidden in Step 8:

```text
brain/tick.py
brain/ui/session.py
brain/ui/__main__.py
INVARIANT_CATALOG.md
tools/catalog.py
schema files
persistence files
```

Commit message:

```text
phase3.17 step8: processing window initial test
```

Push.

---

# Step 9 — Findings / triage

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_FINDINGS.md
```

Classify:

```text
- codex fix success / fail
- codex model route works / partial / fail
- processing window feasible now?
- processing window requires runtime design?
- what exact next implementation campaign is needed?
- blockers
- deferred work
```

Commit message:

```text
phase3.17 step9: findings
```

Push.

---

# Step 10 — Final audit

Create:

```text
docs/campaigns/phase3_17/PHASE3_17_CODEX_PROCESSING_WINDOW_AUDIT.md
```

Verdict options:

```text
PASS                           : codex fixed AND processing-window
                                 initial test started
PASS WITH DEFERRED IMPLEMENTATION: codex fixed, design ready,
                                 runtime implementation deferred
PARTIAL                        : codex fixed but processing-window
                                 blocked
BLOCKED                        : codex unavailable or required
                                 config missing
FAIL                           : invariant / runtime regression
```

Validation (canonical preflight):

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

Required content:

```text
- verdict
- files changed across the campaign
- gate results
- cumulative real model call count
- mode tested
- explicit "no SelfModel implementation" confirmation
- explicit "no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim" confirmation
- explicit "no aggregate awareness / I-ness / growth score"
  confirmation
- explicit "no hidden LLM call / hidden persistence / DB schema
  change in v1" confirmation
- explicit "no L2 (eval_v1) semantic change" confirmation
- explicit "no tick semantic change (brain/tick.py untouched)"
  confirmation
- explicit "no raw prompts / responses / cache files / secrets
  committed" confirmation
- explicit "OFFLINE remains default; model-backed remains explicit
  opt-in" confirmation
- explicit "50 ticks is an experimental default, not a runtime
  constant in v1" confirmation
- Stage A / Stage B / Stage C.1 bridge usage disclosure across
  the campaign
- next-campaign note
```

Commit message:

```text
phase3.17 step10: final audit
```

Push.

---

# Step 11 — PR preparation

Open a PR to main with title:

```text
phase3.17: codex runtime and processing window research
```

PR body must include:

```text
- PR URL
- codex issue fixed yes/no
- codex real model route result
- processing-window design status
- whether 50 ticks is still recommended as initial default
- what actual testing was started
- validation results
- next campaign recommendation
- confirmation main was not pushed directly during campaign execution
- confirmation PR is not merged
- Stage A / Stage B / Stage C.1 bridge usage summary
```

Do not merge.
