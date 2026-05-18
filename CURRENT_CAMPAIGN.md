# CURRENT_CAMPAIGN.md — Phase 3.14 LLM Cache Discipline Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.14 follows the completed Phase 3.13 Growth Ledger. Phase 3.13 shipped:

```text
Pattern Ledger     brain/development/pattern_ledger.py     I-PLEDGER-01..18    catalog v0.21
Coherence Monitor  brain/development/coherence_monitor.py  I-COHMON-01..14     catalog v0.22
Growth Ledger      brain/development/growth_ledger.py      I-GROW-01..22       catalog v0.23
```

Subsequent merges on main:

```text
PR #14  Phase 3.13 Growth Ledger (catalog v0.23; +I-GROW-01..22)
PR #15  Stage B Claude → Codex CLI → ChatGPT limited-write bridge
        (.claude/agents/chatgpt-codex-writer.md;
         .claude/commands/ask-chatgpt-write.md;
         tools/claude_helpers/codex_chatgpt_write_worker.py)
```

Phase 3.14 asks the next bounded question:

```text
Can ToyI's model-backed LLM runtime modes evaluate repeated semantic
content without spamming the external model across ticks, while
preserving offline-as-default, explicit opt-in for model-backed modes,
no hidden LLM calls, no unbounded cache, and no tick semantic change
before review?
```

The driving evidence chain (verified from repo-local files in Step 1):

```text
brain/tick.py::tick(...) constructs a fresh LLMBackedPtCns every call.
brain/llm/ptcns_backed.py::LLMBackedPtCns caches per-instance/per-tick.
brain/llm/client.py::CachedClient exists and persists prompt-hash
  responses to brain/.llm_cache (gitignored).
brain/ui/llm_runtime.py::build_llm_client_from_config wraps
  ANTHROPIC_API / CLAUDE_CLI / CODEX_CLI in CachedClient only when
  config.enable_cache is true. OFFLINE / MOCK reject caching at the
  factory boundary.
brain/llm/prompts.py::PROMPT_TEMPLATE includes new_id and new_text, so
  repeated same text under different content IDs may miss the
  prompt-hash cache.
```

Phase 3.14 does **not** implement SelfModel, and does **not** modify Growth Ledger semantics, Pattern Ledger semantics, Coherence Monitor semantics, persistence, autosave, observability, scenarios, traces, or any guarded kernel path before the Phase 3.14 review gate.

Preferred campaign branch:

```text
campaign/phase3-14-llm-cache-discipline
```

Preferred final PR title:

```text
phase3.14: llm cache discipline
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

Then read whichever files the next campaign step names. Do not rely on chat memory.

---

## Baseline

Expected current state:

```text
Catalog: v0.23
Counts:
  REQUIRED:        259
  STRUCTURAL:       86
  NOT-EXERCISED:    12
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:  Phase 3.13 Growth Ledger
Latest merged PRs:          PR #14 (Phase 3.13 Growth Ledger),
                            PR #15 (Stage B limited-write bridge)
Current campaign:           Phase 3.14 LLM Cache Discipline
Next eligible step:         Step 1 repo-state sync and Phase 3.14
                            mission install (this file's first step)
Canonical design seed:      PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md
```

Inherited follow-ups deliberately deferred from Phase 3.13 and earlier:

```text
- SelfModel implementation (Phase 3.12 Step 15 roadmap) is OUT OF SCOPE
  for Phase 3.14. It is not in flight in any campaign.
- /pattern-ledger UI is DEFERRED (I-PLEDGER-17).
- /coherence-summary UI is DEFERRED (I-COHMON-13).
- /growth-ledger UI is DEFERRED (I-GROW-21).
- end-to-end Pattern Ledger / Coherence Monitor / Growth Ledger dry-run
  helpers are NOT-EXERCISED (I-PLEDGER-18 / I-COHMON-14 / I-GROW-22).
- SQLite backup wording note (carried from Phase 3.10c).
- optional real ORS smoke for anthropic-api / claude-cli / codex-cli
  remains deferred. The Stage A /ask-chatgpt and Stage B
  /ask-chatgpt-write bridges are sanctioned advisory / limited-write
  channels and are not runtime LLM seams.
```

---

## Operational target

Phase 3.14 uses this operational definition:

```text
LLM cache discipline:
  the cataloged, bounded, observable behavior of the model-backed LLM
  runtime that guarantees repeated semantic evaluation work across
  ticks reuses prior model responses without calling the underlying
  external model again, while preserving:
    - offline as the default runtime
    - model-backed modes as explicit opt-in
    - no hidden LLM calls
    - no unbounded cache growth
    - deterministic, documented cache keys
    - cache hits that do not call the inner client
    - cache misses that may call the inner client only in explicit
      model-backed mode
    - explicit, documented corrupt-cache and parse-failure / retry
      policy
    - explicit, documented behavior for "same evaluation, different
      content ID" cases

Cache layers under consideration:
  L0  per-instance/per-tick short-circuit (LLMBackedPtCns._cache)
  L1  prompt-hash transport cache (CachedClient on disk under
      brain/.llm_cache)
  L2  optional canonical semantic evaluation cache (Option B in the
      roadmap; not authorized for Step 1; designed in Step 2;
      decided at Review Gate A)
```

---

## Non-goals

```text
no SelfModel implementation in Phase 3.14
no Growth Ledger semantic change
no Pattern Ledger semantic change
no Coherence Monitor semantic change
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
no hidden autosave behavior
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
no DB schema change in v1 unless explicitly planned and accepted at the
  review gate
no /save-session / /load-session / autosave extension in v1 unless
  explicitly planned and accepted at the review gate
no tick semantic change before the Phase 3.14 review gate
no raw prompts or model outputs committed to the repo
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays ignored)
no real external LLM smoke beyond the sanctioned bridges and any
  explicitly approved Phase 3.14 measurement step
no UI expansion unless explicitly reviewed
no raw codex invocation
no unbounded Codex collaboration loop
```

---

## Macro sequence

```text
Step 1   Repo-state sync and Phase 3.14 mission install
Step 2   LLM cache discipline synthesis
Step 3   LLM cache behavior probe / spam reproduction report
Step 4   LLM cache corrigenda
Step 5   LLM cache catalog patch plan
Step 6   Review Gate A — LLM cache implementation
Step 7   Apply accepted LLM cache implementation, if approved
Step 8   LLM cache behavior report
Step 9   LLM cache findings / triage
Step 10  Final Phase 3.14 audit
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

## ChatGPT/Codex consultation policy (Stage A + Stage B bridges)

The repository ships two explicit, sanctioned Claude → Codex CLI → ChatGPT bridges. Use them as advisory (Stage A) or limited-write (Stage B), at high-leverage points. The full bridge policy lives in `CURRENT_MISSION.md`. This file restates only what each step must do.

```text
Stage A wrapper:  python3 tools/claude_helpers/codex_chatgpt_subagent.py
Stage A modes:    plan / review / summarize / debug
Stage A slash:    /ask-chatgpt
Stage B wrapper:  python3 tools/claude_helpers/codex_chatgpt_write_worker.py
Stage B modes:    write
Stage B slash:    /ask-chatgpt-write
```

Stage A is **required** at:

```text
Step 1   advisory plan review (this step)
Step 2   synthesis adversarial review
Step 5   catalog patch plan adversarial review
Step 8   behavior report adversarial review
Step 10  final audit adversarial review (unless explicitly redundant)
```

Stage B is **allowed**, with bounded scope, at:

```text
Step 1   roadmap draft only (PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md)
Step 2   synthesis doc draft only (exact single-file allowed path)
Step 5   catalog patch plan draft only (exact single-file allowed path)
Step 7   implementation shards only after Step 6 review gate, with
         exact allowed-file lists, one call at a time, never more than
         3 real Codex calls without fresh operator approval
never    raw broad repo edits
never    staging / commit / push
never    Stage B for CURRENT_MISSION.md / CURRENT_CAMPAIGN.md /
         INVARIANT_CATALOG.md / README.md / brain/tick.py edits
```

When a step uses a bridge:

```text
- use the wrapper or slash command, never raw codex
- use --model gpt-5.5 unless the operator approves another model
  in-session
- write the question to /tmp/toyi_<stepid>_<role>_question.md (Stage A)
  or /tmp/toyi_<stepid>_writer_prompt.md (Stage B)
- write the wrapper output to /tmp/toyi_<stepid>_<role>_answer.md
- the wrapper's hash-only audit JSONL lands under
  .claude/codex_bridge_logs/ (gitignored); do not commit those logs
- treat repo-local files, gates, and invariants as authoritative if
  they conflict with ChatGPT advice
- Stage B requires exact --allowed-file paths only; parent Claude
  inspects diff, validates, stages, commits, and pushes
- Stage B never uses --apply for paths outside the explicit allowed
  list
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
```

---

# Step 1 — Repo-state sync and Phase 3.14 mission install

Purpose: replace the stale Phase 3.13 mission/campaign routing prose with Phase 3.14 LLM Cache Discipline as current, with the Phase 3.14 roadmap landed at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md
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
sync fresh main and create branch campaign/phase3-14-llm-cache-discipline
run all preflight gates green
write Phase 3.14 CURRENT_MISSION.md
write Phase 3.14 CURRENT_CAMPAIGN.md
create PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md at repo root with the
  ten required sections enumerated in the mission spec (purpose,
  baseline, problem statement, current code diagnosis, candidate fix
  strategies, guardrails, required future measurements, bridge
  collaboration policy, non-goals, next artifact)
run a Stage A advisory plan review against gpt-5.5 / plan / medium and
  record wrapper status
use Stage B writer for the roadmap file only (one allowed file), inspect
  diff, and accept/reject — parent Claude writes CURRENT_MISSION.md and
  CURRENT_CAMPAIGN.md directly
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
git status --short
git diff -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md
```

Commit message:

```text
phase3.14 step1: llm cache discipline mission sync
```

Push.

---

# Step 2 — LLM cache discipline synthesis

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_SYNTHESIS.md
```

Required content:

```text
why Phase 3.14 follows Phase 3.13 (Growth Ledger landed; LLM cache
  discipline is the next bounded substrate question)
evidence chain (file-by-file) over brain/tick.py,
  brain/llm/ptcns_backed.py, brain/llm/client.py, brain/llm/prompts.py,
  brain/ui/llm_runtime.py
classification of repeated-call causes:
  - per-instance cache lifetime too short (L0)
  - raw prompt-hash cache misses due to volatile IDs (L1 vs new_id)
  - legitimate semantic changes between ticks
  - explicit opt-in model-backed mode usage
fix-strategy comparison (Options A / B / C / D from the roadmap):
  - decide which option(s) survive synthesis
  - state the proposed cache key shape, including which fields are
    semantic and which are non-semantic
  - state corrupt-cache and parse-failure / retry policy precisely
acceptance criteria for the eventual implementation:
  - offline default unchanged
  - no real LLM calls in tests unless explicitly injected or mocked
  - repeated semantic inputs across ticks produce at most one external
    call in model-backed mode
  - different semantic inputs still call/evaluate separately
  - cache hit/miss evidence is inspectable
  - cache files remain bounded and gitignored
phased plan to Review Gate A
Stage A and Stage B disclosure blocks
next artifact: behavior probe (Step 3)
```

Stage A is required for adversarial review of the synthesis.
Stage B is allowed for drafting the synthesis file when an exact single-file allowed path is used. Parent Claude inspects diff and accepts/rejects.

Commit message:

```text
phase3.14 step2: llm cache discipline synthesis
```

Push.

---

# Step 3 — LLM cache behavior probe / spam reproduction report

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_PROBE.md
```

Required content:

```text
deterministic, repo-local reproduction of repeated-call behavior using
  the MockClient and the existing /step path; no real external model
  call
measurement table covering each Required Future Measurement from the
  roadmap (cache disabled / enabled / same text different IDs /
  retry / file write+read / offline+mock isolation /
  llm.cache_hit + llm.cache_miss trace presence)
explicit identification of which measurements expose the design
  question that synthesis flagged
Stage A and Stage B disclosure blocks
next artifact: corrigenda (Step 4)
```

This step does **not** modify any kernel source; it is a measurement-first probe over the existing public surfaces. If measurement requires a small temporary fixture, it must live under `/tmp` or be otherwise non-committed unless Step 4/5 explicitly allows it.

Commit message:

```text
phase3.14 step3: llm cache behavior probe
```

Push.

---

# Step 4 — LLM cache corrigenda

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_CORRIGENDA.md
```

Required content:

```text
resolve every open design decision still open at synthesis/probe time
LOCK statements (mirror Phase 3.13 Growth Ledger LOCK A..F precedent):
  - LOCK A: explicit cache layer scope decision (L0 only / L0+L1 /
    L0+L1+L2)
  - LOCK B: cache-key semantic vs non-semantic field list
  - LOCK C: corrupt-cache policy (fail-loud vs fail-quiet-with-trace)
  - LOCK D: parse-failure / retry policy (cache-skip vs cache-with-tag)
  - LOCK E: cache size bound and growth policy (file-count cap /
    byte-size cap / lifecycle policy)
  - LOCK F: offline/mock isolation (factory rejects vs runtime
    no-write)
Stage A and Stage B disclosure blocks
next artifact: catalog patch plan (Step 5)
```

Commit message:

```text
phase3.14 step4: llm cache discipline corrigenda
```

Push.

---

# Step 5 — LLM cache catalog patch plan

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_CATALOG_PATCH_PLAN.md
```

Required content:

```text
proposed row family: I-LLMCACHE-* (or extension of I-LLM-* /
  I-LLMTOG-* if synthesis prefers that)
exact row-by-row status assignment
  (REQUIRED / STRUCTURAL / DEFERRED / NOT-EXERCISED / OBSERVED)
exact catalog version bump (v0.23 -> v0.24)
exact count delta (REQUIRED += n, STRUCTURAL += n, DEFERRED += n,
  NOT-EXERCISED += n, OBSERVED += n)
fixture list (one fixture per row family discipline; constructor /
  cache-hit-no-inner-call / cache-miss-calls-inner / offline+mock
  isolation / static-AST audit / no-tick-change audit /
  non-claim audit)
explicit non-rows (every cognitive-layer claim that Phase 3.14 does NOT
  authorize, inherited from the Phase 3.12 Step 15 roadmap's
  non-goals)
Stage A and Stage B disclosure blocks
next artifact: Review Gate A
```

Stop at the next review gate.

Commit message:

```text
phase3.14 step5: llm cache catalog patch plan
```

Push.

---

# Step 6 — Review Gate A — LLM cache implementation

Stop unless the operator explicitly chooses one:

```text
[ ] ACCEPT PLAN AS WRITTEN
[ ] ACCEPT WITH AMENDMENTS (operator lists the amendments)
[ ] REJECT / REVISE (no implementation; return to Step 5)
```

No source-code changes are allowed before this gate clears.

---

# Step 7 — Apply accepted LLM cache implementation, if approved

Allowed files depend on the accepted plan. Likely set:

```text
brain/llm/client.py                                           (cache layer extension)
brain/llm/ptcns_backed.py                                     (only if Option B/C requires it)
brain/llm/prompts.py                                          (only if Option C requires it)
brain/ui/llm_runtime.py                                       (cache wiring extension)
brain/ui/fixtures/<llm cache fixtures listed in Step 5>       (new)
brain/invariants.py                                           (FIXTURE_MODULES extension)
tools/catalog.py                                              (EXPECTED_COUNTS banner update)
INVARIANT_CATALOG.md                                          (new v0.24 banner + I-LLMCACHE-* rows)
README.md                                                     (catalog version + counts string)
CURRENT_MISSION.md                                            (catalog version + counts string)
CURRENT_CAMPAIGN.md                                           (catalog version + counts string)
```

No implementation is authorized by this campaign text alone. The exact file set comes from the Step 5 catalog patch plan amended by the Step 6 gate.

`brain/tick.py` MAY be touched only if Review Gate A explicitly authorizes a tick semantic change; otherwise it stays frozen.

Stage B implementation shards are permitted with exact `--allowed-file` lists, one call at a time, and never more than 3 real Codex calls without fresh operator approval. Parent Claude validates, stages, commits, and pushes.

Run every preflight gate green. Commit and push.

---

# Step 8 — LLM cache behavior report

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_REPORT.md
```

Required content:

```text
re-run of the Step 3 probe table over the post-implementation runtime
event-by-event verification that:
  - cache hits do not call the inner client
  - cache misses call the inner client only in explicit model-backed
    mode
  - offline/mock modes still produce zero cache writes (or only the
    explicitly allowed behavior)
  - same text under different content IDs collapses to one external
    call (or is explicitly documented as deferred if Option B/C
    was rejected)
  - cache file count / byte size remains within the LOCK E bound
anti-spam test (same input repeated; transport call count saturates)
no-mutation verification (BrainState / MSI / PtCns / Growth Ledger /
  Pattern Ledger / Coherence Monitor records identity-stable across
  repeated cached evaluations; tick semantics either unchanged or
  changed exactly as Review Gate A approved)
Stage A and Stage B disclosure blocks
next artifact: findings / triage (Step 9)
```

Commit message:

```text
phase3.14 step8: llm cache behavior report
```

Push.

---

# Step 9 — LLM cache findings / triage

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_FINDINGS.md
```

Required content:

```text
bugs / regressions observed in Step 8 (if any)
operator UX surprises (if any)
proposed deferred follow-ups
explicit list of items that DO NOT block this campaign
Stage A and Stage B disclosure blocks
next artifact: final audit (Step 10)
```

Commit message:

```text
phase3.14 step9: llm cache findings
```

Push.

---

# Step 10 — Final Phase 3.14 audit

Create:

```text
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_AUDIT.md
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
explicit "no unbounded cache growth" confirmation
explicit "no tick semantic change other than what Review Gate A
  approved (if any)" confirmation
explicit "Stage A and Stage B bridge usage, if any, is recorded" with
  per-step disclosure links
next-campaign note (SelfModel remains deferred; promote only after a
  follow-up campaign that explicitly accepts the SelfModel plan)
Stage A and Stage B disclosure blocks
```

Commit message:

```text
phase3.14 step10: final llm cache discipline audit
```

Push.

---

# Step 11 — Final PR preparation

Open a PR to main with title:

```text
phase3.14: llm cache discipline
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
  optional real ORS smoke)
confirmation main was not pushed directly during campaign execution
confirmation PR is not merged
Stage A /ask-chatgpt consultation summary across the campaign
Stage B /ask-chatgpt-write collaboration summary across the campaign
```

Do not merge.
