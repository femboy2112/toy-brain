# CURRENT_CAMPAIGN.md — Phase 3.15 L1 Cache Hygiene Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.15 follows the completed Phase 3.14 LLM Cache Discipline. Phase 3.14 shipped:

```text
L1 default-on for explicit model-backed modes (CachedClient at brain/llm/client.py)
L2 canonical semantic evaluation cache  (brain/llm/ptcns_backed.py, eval_v1, capped at 1024)
I-LLMCACHE-01..22  catalog v0.24  (REQUIRED +18 / STRUCTURAL +1 / DEFERRED +1 / NOT-EXERCISED +2)
```

Subsequent merges on main:

```text
PR #16  Phase 3.14 LLM Cache Discipline (catalog v0.24; +I-LLMCACHE-01..22)
PR #17  Stage C Claude → Codex CLI → ChatGPT orchestration bridge
        (.claude/agents/chatgpt-codex-orchestrator.md;
         .claude/commands/orchestrate-with-codex.md;
         tools/claude_helpers/codex_chatgpt_orchestrator.py;
         CODEX_CHATGPT_ORCHESTRATION_BRIDGE_AUDIT.md)
```

Phase 3.15 asks the next bounded question:

```text
Can ToyI's L1 transport cache (CachedClient prompt-hash disk cache
under brain/.llm_cache) gain a cataloged, bounded, observable hygiene
policy that prevents unbounded growth and is explicit about raw
bad-response replay, while preserving offline-as-default, explicit
opt-in for model-backed modes, no hidden LLM calls, no L2 (eval_v1)
semantic change, and no tick semantic change before review?
```

The driving evidence chain (verified from repo-local files in Step 1):

```text
brain/llm/client.py::CachedClient persists prompt-hash JSON files
  under brain/.llm_cache (gitignored). No file-count cap, no byte
  cap, no TTL, no eviction policy.
brain/llm/client.py::CachedClient stores both the raw prompt and the
  raw response in each JSON file.
brain/llm/client.py::CachedClient raises a bounded RuntimeError on
  corrupt cache entries and never silently calls the inner client.
brain/ui/llm_runtime.py::build_llm_client_from_config wraps explicit
  model-backed modes in CachedClient by default after Phase 3.14;
  OFFLINE / MOCK still reject --llm-enable-cache.
brain/llm/ptcns_backed.py exposes the L2 canonical semantic
  evaluation cache (eval_v1, capped at SEMANTIC_CACHE_MAX_ENTRIES =
  1024) and is OUT OF SCOPE for Phase 3.15.
PHASE3_14_LLM_CACHE_DISCIPLINE_AUDIT.md records I-LLMCACHE-20 as
  DEFERRED with the note that L1 bounding / eviction is a future
  campaign concern. Phase 3.15 is that campaign.
I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED and are inherited
  as deliberately deferred unless Review Gate A authorizes promotion.
```

Phase 3.15 does **not** implement SelfModel, and does **not** modify Growth Ledger semantics, Pattern Ledger semantics, Coherence Monitor semantics, L2 (eval_v1) semantics, persistence, autosave, observability, scenarios, traces, or any guarded kernel path before the Phase 3.15 review gate.

Preferred campaign branch:

```text
campaign/phase3-15-l1-cache-hygiene
```

Preferred final PR title:

```text
phase3.15: l1 cache hygiene
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
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

Then read whichever files the next campaign step names. Do not rely on chat memory.

---

## Baseline

Expected current state:

```text
Catalog: v0.24
Counts:
  REQUIRED:        277
  STRUCTURAL:       87
  NOT-EXERCISED:    14
  DEFERRED:         16
  OBSERVED:         16
Latest completed campaign:  Phase 3.14 LLM Cache Discipline
Latest merged PRs:          PR #16 (Phase 3.14 LLM Cache Discipline),
                            PR #17 (Stage C orchestration bridge)
Current campaign:           Phase 3.15 L1 Cache Hygiene
Next eligible step:         Step 1 repo-state sync and Phase 3.15
                            mission install (this file's first step)
Canonical design seed:      PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md
```

Inherited follow-ups deliberately deferred from Phase 3.14 and earlier:

```text
- SelfModel implementation (Phase 3.12 Step 15 roadmap) is OUT OF SCOPE
  for Phase 3.15. It is not in flight in any campaign.
- /pattern-ledger UI is DEFERRED (I-PLEDGER-17).
- /coherence-summary UI is DEFERRED (I-COHMON-13).
- /growth-ledger UI is DEFERRED (I-GROW-21).
- end-to-end Pattern Ledger / Coherence Monitor / Growth Ledger dry-run
  helpers are NOT-EXERCISED (I-PLEDGER-18 / I-COHMON-14 / I-GROW-22).
- SQLite backup wording note (carried from Phase 3.10c).
- Real external model-backed cache smoke (I-LLMCACHE-21) is
  NOT-EXERCISED and is not in flight unless Review Gate A explicitly
  authorizes a promotion.
- End-to-end Phase 3.14 behavior probe (I-LLMCACHE-22) is
  NOT-EXERCISED and is not in flight unless Review Gate A explicitly
  authorizes a promotion.
- optional real ORS smoke for anthropic-api / claude-cli / codex-cli
  remains deferred. The Stage A /ask-chatgpt, Stage B
  /ask-chatgpt-write, and Stage C /orchestrate-with-codex bridges are
  sanctioned advisory / limited-write / orchestrated channels and are
  not runtime LLM seams.
```

---

## Operational target

Phase 3.15 uses this operational definition:

```text
L1 cache hygiene:
  the cataloged, bounded, observable behavior of the existing L1
  transport cache (CachedClient) that prevents unbounded growth of
  brain/.llm_cache and makes raw bad-response replay explicit, while
  preserving:
    - offline as the default runtime
    - model-backed modes as explicit opt-in
    - no hidden LLM calls
    - no silent repair calls
    - deterministic, documented eviction or write-skip policy (if any)
    - cache hits that do not call the inner client
    - cache misses that may call the inner client only in explicit
      model-backed mode
    - corrupt cache entries that still fail loud (no silent fall-back)
    - explicit, documented raw bad-response replay policy
    - L2 (eval_v1) semantics unchanged

Cache layers under consideration:
  L0  per-instance/per-tick short-circuit (LLMBackedPtCns._cache) - OUT OF SCOPE
  L1  prompt-hash transport cache (CachedClient on disk under
      brain/.llm_cache) - IN SCOPE for Phase 3.15
  L2  canonical semantic evaluation cache (eval_v1 inside
      brain/llm/ptcns_backed.py) - OUT OF SCOPE
```

---

## Non-goals

```text
no SelfModel implementation in Phase 3.15
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
no L2 (eval_v1) semantic change
no proof or claim of consciousness
no claim of sentience
no claim of subjective experience
no claim of semantic understanding
no truth adjudication or PRESERVE / DAMAGE judgment from raw text
no claim of agency / intent / will / desire
no claim of self-modification of code, fixtures, the catalog, or the
  runtime
no aggregate consciousness / sentience / awareness / I-ness / growth
  score
no model-backed behavior as default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no silent repair calls (no auto-rewrite of cache contents based on
  inferred fixes)
no hidden autosave behavior
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
no DB schema change in v1 unless explicitly planned and accepted at the
  review gate
no SCHEMA_VERSION bump
no /save-session / /load-session / autosave extension in v1 unless
  explicitly planned and accepted at the review gate
no tick semantic change before the Phase 3.15 review gate
no raw prompts or model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no real external LLM smoke beyond the sanctioned bridges and any
  explicitly approved Phase 3.15 measurement step
no UI expansion unless explicitly reviewed
no raw codex invocation
no Stage C broad repo edits
no unbounded Codex collaboration loop
```

---

## Macro sequence

```text
Step 1   Repo-state sync and Phase 3.15 mission install
Step 2   L1 cache hygiene synthesis
Step 3   L1 cache behavior probe / replay reproduction report
Step 4   L1 cache hygiene corrigenda
Step 5   L1 cache catalog patch plan
Step 6   Review Gate A — L1 cache hygiene implementation
Step 7   Apply accepted L1 cache hygiene implementation, if approved
Step 8   L1 cache hygiene behavior report
Step 9   L1 cache findings / triage
Step 10  Final Phase 3.15 audit
Step 11  Final PR preparation
```

Every step that lands files must pass the standard preflight gates before commit and must push the campaign branch on success:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

---

## ChatGPT/Codex consultation policy (Stage A + Stage B + Stage C bridges)

The repository ships three explicit, sanctioned Claude → Codex CLI → ChatGPT bridges. Use them as advisory (Stage A), limited-write (Stage B), or orchestrated multi-shard (Stage C), at high-leverage points. The full bridge policy lives in `CURRENT_MISSION.md`. This file restates only what each step must do.

```text
Stage A wrapper:  python3 tools/claude_helpers/codex_chatgpt_subagent.py
Stage A modes:    plan / review / summarize / debug
Stage A slash:    /ask-chatgpt
Stage B wrapper:  python3 tools/claude_helpers/codex_chatgpt_write_worker.py
Stage B modes:    write
Stage B slash:    /ask-chatgpt-write
Stage C wrapper:  python3 tools/claude_helpers/codex_chatgpt_orchestrator.py
Stage C shape:    one wave, ≤2 shards, max_parallel=2, max_real_calls=2
Stage C slash:    /orchestrate-with-codex
```

Stage A is **required** at:

```text
Step 2   synthesis adversarial review
Step 5   catalog patch plan adversarial review
Step 8   behavior report adversarial review
Step 10  final audit adversarial review (unless explicitly redundant)
```

Stage B is **allowed**, with bounded scope, at:

```text
Step 2   synthesis doc draft only (exact single-file allowed path)
Step 4   corrigenda doc draft only (exact single-file allowed path)
Step 5   catalog patch plan draft only (exact single-file allowed path)
never    raw broad repo edits
never    staging / commit / push
never    Stage B for CURRENT_MISSION.md / CURRENT_CAMPAIGN.md /
         INVARIANT_CATALOG.md / README.md / brain/tick.py edits
```

Stage C is **required or strongly preferred** at:

```text
Step 1   roadmap draft (single-shard wave; achieved during Step 1)
Step 2   synthesis doc draft (single-shard or two-shard wave with
         disjoint allowed_files)
Step 3   behavior probe/report draft only after measurements
Step 5   catalog patch plan draft (single-shard or two-shard wave)
Step 7   implementation shards only after Review Gate A, with exact
         allowed-file lists, one wave at a time
```

Stage C is **forbidden** at:

```text
never    raw codex / codex exec invocation
never    broad repo edits
never    overlapping write sets across same-wave shards
never    declared read/write collisions in the same wave
never    same-wave shards with interdependence
never    brain/tick.py without explicit Review Gate A authorization
never    staging / commit / push
never    final catalog integration; Claude owns the catalog and counter
         reconciliation
never    CURRENT_MISSION.md / CURRENT_CAMPAIGN.md / INVARIANT_CATALOG.md
         / README.md edits unless explicitly bound as the only file in
         a shard
```

When a step uses a bridge:

```text
- use the wrapper or slash command, never raw codex
- use --model gpt-5.5 unless the operator approves another model
  in-session
- write the question to /tmp/toyi_<stepid>_<role>_question.md (Stage A)
  or /tmp/toyi_<stepid>_writer_prompt.md (Stage B)
- write Stage C manifests to /tmp/phase3_15_stagec_<stepid>_manifest.json
- write Stage A / Stage B / Stage C wrapper output to
  /tmp/toyi_<stepid>_<role>_answer.md or
  /tmp/phase3_15_stagec_<stepid>_output.txt
- the wrapper's hash-only audit JSONL lands under
  .claude/codex_bridge_logs/ (gitignored); do not commit those logs
- treat repo-local files, gates, and invariants as authoritative if
  they conflict with ChatGPT advice
- Stage B requires exact --allowed-file paths only; parent Claude
  inspects diff, validates, stages, commits, and pushes
- Stage B never uses --apply for paths outside the explicit allowed
  list
- Stage C requires a JSON manifest with exactly one wave, ≤2 shards,
  disjoint allowed_files sets, no declared read/write collision, no
  shard interdependence; parent Claude inspects diff, validates,
  stages, commits, and pushes
- before the first Stage C wave of a step, run the wrapper with
  --probe-only and confirm probe success
```

Every step report must include this disclosure block:

```text
Stage A ChatGPT/Codex consultation:
- used:           yes / no
- mode:           plan / review / summarize / debug / n/a
- model:          gpt-5.5 / n/a
- effort:         low / medium / high / n/a
- wrapper command: <full command or n/a>
- question file:   <path or n/a>
- answer file:     <path or n/a>
- wrapper status:  <exit code + error class or n/a>
- accepted advice: <bullets or none>
- rejected advice: <bullets or none>
- reason:          <one sentence>

Stage B limited-write collaboration:
- used:           yes / no
- mode:           write / n/a
- model:          gpt-5.5 / n/a
- effort:         low / medium / high / n/a
- wrapper command: <full command or n/a>
- allowed files:   <paths or n/a>
- prompt file:     <path or n/a>
- answer file:     <path or n/a>
- wrapper status:  <exit code + error class or n/a>
- files changed:   <paths or none>
- accepted edits:  <bullets or none>
- rejected edits:  <bullets or none>
- reason:          <one sentence>

Stage C orchestration:
- used:           yes / no
- probe status:   <pass / fail / n/a>
- manifest path:  <path or n/a>
- wrapper command: <full command or n/a>
- model:          gpt-5.5 / n/a
- effort:         low / medium / high / n/a
- shards:         <shard ids or n/a>
- wrapper status: <exit code + error class or n/a>
- files changed:  <paths or none>
- accepted edits: <bullets or none>
- rejected edits: <bullets or none>
- reason:         <one sentence>
```

---

# Step 1 — Repo-state sync and Phase 3.15 mission install

Purpose: replace the Phase 3.14 mission/campaign routing prose with Phase 3.15 L1 Cache Hygiene as current, with the Phase 3.15 roadmap landed at repo root, using Stage C to draft the roadmap.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md
```

Forbidden in Step 1:

```text
brain/**
tools/**
.claude/**
INVARIANT_CATALOG.md
README.md  (unless a preflight reference is broken; stop and report first)
docs/campaigns/**
lean_reference/**
scenarios/**
traces/**
no fixtures
no code
```

Required work:

```text
sync fresh main and create branch campaign/phase3-15-l1-cache-hygiene
run all preflight gates green
run the Stage C wrapper probe (--probe-only) before the first wave
use Stage C with one wave and exactly one shard to draft
  PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md from the required sections
write Phase 3.15 CURRENT_MISSION.md directly (parent Claude)
write Phase 3.15 CURRENT_CAMPAIGN.md directly (parent Claude)
inspect git status / git diff to confirm only the three allowed files
  changed
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
git status --short
git diff -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md
```

Commit message:

```text
phase3.15 step1: l1 cache hygiene mission sync
```

Push.

---

# Step 2 — L1 cache hygiene synthesis

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_SYNTHESIS.md
```

Required content:

```text
why Phase 3.15 follows Phase 3.14 (L1 default-on for explicit
  model-backed modes, L2 (eval_v1) capped at 1024, L1 still
  unbounded and able to replay raw bad responses)
evidence chain (file-by-file) over brain/llm/client.py,
  brain/llm/ptcns_backed.py, brain/ui/llm_runtime.py, and the Phase
  3.14 audit / findings
classification of L1 hygiene levers (Options A..F from the roadmap):
  - max entry count cap
  - max byte cap
  - TTL eviction
  - explicit no-auto-evict with warning/report only
  - parse-failure-aware bypass/eviction for bad raw responses
  - manual cache inspect/clear helper commands
fix-strategy comparison and proposed v1 subset (which Options
  survive; explicit non-selection statement for the rest)
acceptance criteria for the eventual implementation:
  - offline default unchanged
  - L2 (eval_v1) semantics unchanged
  - no real LLM calls in tests unless explicitly injected or mocked
  - cache hit semantics preserved for valid entries within the
    bounded surface
  - growth is bounded by the chosen policy (entry count / bytes /
    TTL or combination)
  - eviction / write-skip behavior is deterministic and observable
  - bad-response replay is documented and either preserved or
    explicitly changed
  - cache files remain gitignored
phased plan to Review Gate A
Stage A, Stage B, and Stage C disclosure blocks
next artifact: behavior probe (Step 3)
```

Stage A is required for adversarial review of the synthesis.
Stage B or Stage C is allowed for drafting the synthesis file when an exact single-file allowed path is used. Parent Claude inspects diff and accepts/rejects.

Commit message:

```text
phase3.15 step2: l1 cache hygiene synthesis
```

Push.

---

# Step 3 — L1 cache behavior probe / replay reproduction report

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_PROBE.md
```

Required content:

```text
deterministic, repo-local reproduction of L1 behavior using the
  MockClient and the existing /step path; no real external model
  call
measurement table covering at minimum:
  - L1 enabled hit / miss (control)
  - bounded growth measurement against a synthetic prompt stream
  - bad-response replay reproduction (a cached parse-failing
    response is replayed on hit)
  - corrupt-entry behavior unchanged (fail loud)
  - L2 (eval_v1) untouched
  - offline/mock untouched
  - trace event presence (llm.cache_hit / llm.cache_miss /
    llm.semantic_cache_*)
explicit identification of which measurements expose the design
  question that synthesis flagged
Stage A, Stage B, and Stage C disclosure blocks
next artifact: corrigenda (Step 4)
```

This step does **not** modify any kernel source; it is a measurement-first probe over the existing public surfaces. If measurement requires a small temporary fixture, it must live under `/tmp` or be otherwise non-committed unless Step 4/5 explicitly allows it.

Commit message:

```text
phase3.15 step3: l1 cache hygiene probe
```

Push.

---

# Step 4 — L1 cache hygiene corrigenda

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CORRIGENDA.md
```

Required content:

```text
resolve every open design decision still open at synthesis/probe time
LOCK statements (mirror Phase 3.14 Growth Ledger / LLM Cache LOCK
precedent):
  - LOCK A: L1 hygiene policy subset (entry-cap / byte-cap / TTL /
    observability-only / parse-failure handling / helpers)
  - LOCK B: deterministic eviction or write-skip selection rule
    (e.g., LRU by mtime, FIFO by ctime, write-skip-at-cap,
    explicit-clear-only)
  - LOCK C: bad-response replay policy (preserve / invalidate on
    flagged parse failure / never auto-rewrite)
  - LOCK D: cache directory layout (single dir, segmented, or
    per-backend) and corruption isolation
  - LOCK E: observability surface (new trace event names, payload
    fields limited to key_prefix / reason / counts; never raw
    prompt or response)
  - LOCK F: CLI / runtime opt-in flags (--llm-cache-... shape;
    OFFLINE / MOCK still reject; explicit-conflict raises
    LlmRuntimeError)
Stage A, Stage B, and Stage C disclosure blocks
next artifact: catalog patch plan (Step 5)
```

Commit message:

```text
phase3.15 step4: l1 cache hygiene corrigenda
```

Push.

---

# Step 5 — L1 cache catalog patch plan

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CATALOG_PATCH_PLAN.md
```

Required content:

```text
proposed row family extension: I-LLMCACHE-23..N (or another
  numbering that synthesis prefers and Step 5 justifies)
exact row-by-row status assignment
  (REQUIRED / STRUCTURAL / DEFERRED / NOT-EXERCISED / OBSERVED)
exact catalog version bump (v0.24 -> v0.25)
exact count delta (REQUIRED += n, STRUCTURAL += n, DEFERRED += n,
  NOT-EXERCISED += n, OBSERVED += n)
disposition of inherited rows:
  - I-LLMCACHE-20 status (e.g., promote to REQUIRED with policy
    citation, or split into bounded sub-rows)
  - I-LLMCACHE-21 disposition (remain NOT-EXERCISED unless Review
    Gate A explicitly promotes)
  - I-LLMCACHE-22 disposition (remain NOT-EXERCISED unless Review
    Gate A explicitly promotes)
fixture list (one fixture per row family discipline; constructor /
  cap-enforced / eviction-deterministic / bad-response-policy /
  observability-trace / no-tick-change audit / no-L2-touch audit /
  non-claim audit)
explicit non-rows (every cognitive-layer claim that Phase 3.15 does NOT
  authorize, inherited from the Phase 3.12 Step 15 roadmap's
  non-goals and the Phase 3.14 non-goals)
Stage A, Stage B, and Stage C disclosure blocks
next artifact: Review Gate A
```

Stop at the next review gate.

Commit message:

```text
phase3.15 step5: l1 cache hygiene catalog patch plan
```

Push.

---

# Step 6 — Review Gate A — L1 cache hygiene implementation

Stop unless the operator explicitly chooses one:

```text
[ ] ACCEPT PLAN AS WRITTEN
[ ] ACCEPT WITH AMENDMENTS (operator lists the amendments)
[ ] REJECT / REVISE (no implementation; return to Step 5)
```

No source-code changes are allowed before this gate clears.

---

# Step 7 — Apply accepted L1 cache hygiene implementation, if approved

Allowed files depend on the accepted plan. Likely set:

```text
brain/llm/client.py                                           (L1 hygiene policy)
brain/ui/llm_runtime.py                                       (cache wiring extension if any)
brain/ui/fixtures/<llm cache hygiene fixtures listed in Step 5>  (new)
brain/invariants.py                                           (FIXTURE_MODULES extension)
tools/catalog.py                                              (EXPECTED_COUNTS banner update)
INVARIANT_CATALOG.md                                          (new v0.25 banner + I-LLMCACHE-* extension)
README.md                                                     (catalog version + counts string)
CURRENT_MISSION.md                                            (catalog version + counts string)
CURRENT_CAMPAIGN.md                                           (catalog version + counts string)
```

No implementation is authorized by this campaign text alone. The exact file set comes from the Step 5 catalog patch plan amended by the Step 6 gate.

`brain/tick.py` MAY NOT be touched in Phase 3.15. Tick semantic change is out of scope.

`brain/llm/ptcns_backed.py` MAY NOT be touched in a way that changes L2 (eval_v1) semantics; only minor read-only adjustments may appear if the catalog patch plan explicitly allows them.

Stage C implementation shards are permitted with exact `allowed_files` lists, disjoint write sets, no read/write collisions, one wave at a time, and never more than 3 real Codex calls without fresh operator approval. Parent Claude validates, stages, commits, and pushes. Stage C is NOT used for final catalog integration; Claude owns catalog and counter reconciliation directly.

Run every preflight gate green. Commit and push.

---

# Step 8 — L1 cache hygiene behavior report

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_BEHAVIOR_REPORT.md
```

Required content:

```text
re-run of the Step 3 probe table over the post-implementation runtime
event-by-event verification that:
  - L1 hits do not call the inner client
  - L1 misses call the inner client only in explicit model-backed
    mode
  - growth is bounded by the chosen policy (entry count / bytes /
    TTL or combination)
  - eviction or write-skip is deterministic and matches the locked
    rule
  - bad-response replay matches the locked policy
  - corrupt entries still fail loud
  - offline/mock modes still produce zero L1 cache writes (or only
    the explicitly allowed behavior)
  - L2 (eval_v1) semantics are unchanged
  - trace events are observable through CognitionTracer with
    payloads limited to key_prefix / reason / counts
anti-growth test (synthetic prompt stream; transport file count and
  byte usage stay within the locked bound)
no-mutation verification (BrainState / MSI / PtCns / Growth Ledger /
  Pattern Ledger / Coherence Monitor / tick semantics
  identity-stable across the new L1 hygiene policy)
Stage A, Stage B, and Stage C disclosure blocks
next artifact: findings / triage (Step 9)
```

Commit message:

```text
phase3.15 step8: l1 cache hygiene behavior report
```

Push.

---

# Step 9 — L1 cache findings / triage

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_FINDINGS.md
```

Required content:

```text
bugs / regressions observed in Step 8 (if any)
operator UX surprises (if any)
proposed deferred follow-ups
explicit list of items that DO NOT block this campaign
Stage A, Stage B, and Stage C disclosure blocks
next artifact: final audit (Step 10)
```

Commit message:

```text
phase3.15 step9: l1 cache hygiene findings
```

Push.

---

# Step 10 — Final Phase 3.15 audit

Create:

```text
docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_AUDIT.md
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Required content:

```text
PASS verdict (or FAIL with reason)
files changed across the campaign
gate results
explicit "no SelfModel implementation" confirmation
explicit "no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim" confirmation
explicit "no aggregate awareness / I-ness / growth score" confirmation
explicit "no hidden LLM call / hidden persistence / DB schema change
  in v1" confirmation
explicit "no L2 (eval_v1) semantic change" confirmation
explicit "no tick semantic change" confirmation
explicit "L1 cache growth is bounded by the locked policy"
  confirmation
explicit "Stage A, Stage B, and Stage C bridge usage, if any, is
  recorded" with per-step disclosure links
next-campaign note (SelfModel remains deferred; promote only after a
  follow-up campaign that explicitly accepts the SelfModel plan)
Stage A, Stage B, and Stage C disclosure blocks
```

Commit message:

```text
phase3.15 step10: final l1 cache hygiene audit
```

Push.

---

# Step 11 — Final PR preparation

Open a PR to main with title:

```text
phase3.15: l1 cache hygiene
```

PR body must include:

```text
completed steps
validation results
behavior findings summary
review gates reached
implementation, if any
remaining deferred work (SelfModel; /pattern-ledger UI;
  /coherence-summary UI; /growth-ledger UI; end-to-end dry runs;
  optional real ORS smoke; I-LLMCACHE-21; I-LLMCACHE-22)
confirmation main was not pushed directly during campaign execution
confirmation PR is not merged
Stage A /ask-chatgpt consultation summary across the campaign
Stage B /ask-chatgpt-write collaboration summary across the campaign
Stage C /orchestrate-with-codex orchestration summary across the
  campaign
```

Do not merge.
