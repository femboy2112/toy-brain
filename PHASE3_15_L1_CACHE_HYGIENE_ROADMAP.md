# PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md

## Purpose

- Phase 3.15 bounds and hygienizes the L1 transport cache after Phase
  3.14 made L1 default-on for explicit model-backed modes.
- This is a planning artifact only. It does not authorize runtime
  behavior changes before Review Gate A.

## Baseline

- Catalog v0.24
- Counts: REQUIRED 277 / STRUCTURAL 87 / NOT-EXERCISED 14 / DEFERRED 16 / OBSERVED 16
- PR #16 Phase 3.14 LLM Cache Discipline merged
- PR #17 Stage C Claude -> Codex CLI -> ChatGPT orchestration mode merged
- I-LLMCACHE-20 remains DEFERRED (L1 cache bounding / eviction policy)
- I-LLMCACHE-21 remains NOT-EXERCISED (real external model-backed cache smoke)
- I-LLMCACHE-22 remains NOT-EXERCISED (end-to-end behavior probe)
- Offline remains default, model-backed modes remain explicit opt-in

## Problem Statement

Phase 3.14 intentionally left the pre-existing L1 transport cache
semantics intact while adding cache discipline around model-backed
runtime selection and a separate bounded L2 semantic cache. The follow-up
problem is that L1 is now reached by default once an operator explicitly
chooses a model-backed mode, but L1 still has no hygiene policy of its
own.

- CachedClient (L1) still stores raw prompt/response JSON files under
  `brain/.llm_cache/<sha256>.json` (gitignored)
- L1 is unbounded -- no file-count cap, no byte cap, no TTL, no
  eviction policy
- L1 can replay raw bad responses (a cached parse failure remains a hit
  forever)
- Phase 3.14 made L1 default-on for explicit model-backed modes, so the
  unbounded surface is now reached without an `--llm-enable-cache`
  opt-in
- This is not a new model-backed default; offline remains default. Mode
  selection still requires explicit opt-in through the I-LLMTOG-*
  family.

## Current L1 Behavior

- `CachedClient` uses a prompt-hash cache: SHA-256 of the prompt string
  maps to a `{prompt, response}` JSON file.
- A cache hit returns the cached response without calling the inner
  client and records `llm.cache_hit`.
- A cache miss calls the inner client, writes the response file, and
  records `llm.cache_miss`.
- The stored JSON file contains both the raw prompt and the raw response.
- The cache directory defaults to `brain/.llm_cache`; the directory is
  gitignored.
- Corrupt cache files raise a bounded `RuntimeError` and never silently
  call the inner client.
- L2 (`eval_v1` canonical semantic evaluation cache) exists separately
  inside `brain/llm/ptcns_backed.py`, is capped at
  `SEMANTIC_CACHE_MAX_ENTRIES = 1024`, and is out of scope for Phase
  3.15.

## Candidate Hygiene Policies

### A. Max entry count cap on L1

#### Benefits

- Bounds the number of raw L1 transport files.
- Keeps the policy easy to reason about and easy to validate with local
  fixtures.
- Matches the existing L2 style of count-based capacity, while keeping
  L1 separate.

#### Risks/Open questions

- Requires a deterministic selection rule for which entry is removed or
  skipped at cap.
- File count alone does not bound disk use if a small number of prompts
  or responses are very large.
- Eviction can change replay behavior for long-running model-backed
  sessions.

### B. Max byte cap on L1

#### Benefits

- Bounds the disk footprint of raw prompt/response persistence directly.
- Addresses the failure mode where a few large entries dominate storage.
- Can be reported without exposing raw prompt or response contents.

#### Risks/Open questions

- Requires careful accounting across existing files, corrupt files, and
  partially written entries.
- Byte caps may be more complex to test deterministically than entry
  caps.
- Eviction or write-skip behavior must be specified before
  implementation.

### C. TTL (time-to-live) eviction on L1 files

#### Benefits

- Limits stale transport replay over time.
- Reduces the chance that old raw bad responses remain effective
  forever.
- Provides a policy that is intuitive for operator-managed cache
  hygiene.

#### Risks/Open questions

- Time-dependent behavior can make fixtures more brittle unless clocks
  are injected or file mtimes are controlled.
- TTL does not bound growth during high-volume use inside the live
  window.
- The policy must define whether expiration is checked on read, write,
  explicit helper invocation, or some combination.

### D. Explicit no-auto-evict with warning/report only (status quo + observability)

#### Benefits

- Preserves current L1 transport behavior.
- Avoids silent cache mutation during runtime.
- Gives operators visibility into L1 risk without changing cache hits,
  misses, or replay semantics.

#### Risks/Open questions

- Does not actually bound file count or disk bytes.
- Leaves raw bad response replay unchanged.
- May be insufficient to retire I-LLMCACHE-20 if the campaign expects
  a real bounding policy.

### E. Parse-failure-aware bypass/eviction for bad raw L1 responses

#### Benefits

- Targets the highest-risk L1 replay behavior surfaced by Phase 3.14:
  cached raw responses that are known to fail parsing.
- Could reduce repeat retry-shell churn for identical prompts.
- Keeps successful transport cache hits available while treating bad
  raw responses differently.

#### Risks/Open questions

- Requires re-deriving L1 hit/miss behavior using parse classification
  carried from the caller, or invalidating an entry on a flagged parse
  failure.
- Risks mixing transport-layer caching with parser-layer knowledge.
- Must avoid silent repair calls or inferred rewrites of cache contents.
- Needs Review Gate A authorization because it can change L1 replay
  semantics.

### F. Manual cache inspect/clear helper commands, deferred unless reviewed

#### Benefits

- Gives operators a CLI-level way to inspect or clear L1 cache state
  without changing runtime behavior.
- Can report counts, byte totals, age bands, and corrupt-entry status
  without printing raw cache contents.
- Helps validate future policy choices before automatic eviction exists.

#### Risks/Open questions

- Deferred unless reviewed; adding helper commands still expands the
  operator surface.
- Clear operations need explicit safety prompts or dry-run defaults.
- CLI-level helpers do not by themselves change runtime L1 behavior or
  retire bad-response replay risk.

## Recommended Initial Posture

- Step 1 does not decide the v1 hygiene subset.
- Synthesis (Step 2) must decide whether v1 should:
  - add a max entry cap
  - add a max byte cap
  - add an explicit inspect/clear helper
  - alter bad-response replay behavior (Option E)
  - leave L1 raw response persistence unchanged but bounded
  - keep L2 untouched
- Combinations are allowed, but Step 5 must lock the exact subset
  before Review Gate A.

## Guardrails

- no brain/tick.py edit (no tick semantic change)
- no hidden LLM calls
- no silent repair calls (e.g., no auto-rewrite of cache contents based
  on inferred fixes)
- no raw cache contents printed in docs
- no cache files committed; brain/.llm_cache stays ignored
- no model-backed default; offline remains default
- preserve L1 transport semantics unless Review Gate A authorizes a
  change
- preserve L2 (eval_v1) semantics; Phase 3.15 does not touch L2
- no SelfModel implementation
- no Growth Ledger / Pattern Ledger / Coherence Monitor semantic change
- no DB schema change, no SCHEMA_VERSION bump
- no persistence / autosave runtime change
- no UI expansion unless explicitly reviewed
- no consciousness / sentience / subjective / semantic-truth / agency /
  self-modification claim
- no aggregate growth / awareness / I-ness score
- no real external LLM call unless an explicit later review step
  authorizes one

## Stage C Orchestration Policy

- Claude plans, validates, and integrates; Codex executes bounded shards.
- One wave at a time, max two shards per wave, `max_parallel = 2`,
  `max_real_calls = 2` per wave.
- Shards must have disjoint `allowed_files`.
- A shard's `read_files` must not intersect another same-wave shard's
  `allowed_files`.
- No automatic retry; no recursive orchestration.
- Claude commits and pushes only; Codex never stages, commits, pushes,
  restores, or merges.
- More than three real Codex calls for one task requires fresh operator
  approval.
- Raw `codex` / `codex exec` invocation is forbidden; only
  `python3 tools/claude_helpers/codex_chatgpt_orchestrator.py` is
  allowed.

## Next Artifact

- Step 2 produces
  `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_SYNTHESIS.md`
