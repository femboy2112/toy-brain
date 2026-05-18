# PHASE3_14_LLM_CACHE_DISCIPLINE_SYNTHESIS.md

## Purpose

Phase 3.14 follows Phase 3.13 because the Stage A and Stage B bridge substrate is now available, and the next bounded substrate question is whether model-backed LLM evaluation can avoid repeated calls without changing ToyI runtime semantics or making model-backed execution the default.

The cache discipline question is narrow: identify where repeated calls can still occur, classify which causes are intended behavior versus avoidable churn, and set up review-gated implementation criteria before touching tick behavior.

## Baseline

- Catalog: v0.23
- Counts: REQUIRED 259 / STRUCTURAL 86 / NOT-EXERCISED 12 / DEFERRED 15 / OBSERVED 16
- Phase 3.13 is complete and merged.
- Stage A and Stage B bridges are available.
- Current branch: `campaign/phase3-14-llm-cache-discipline`

## Evidence Chain

### 1. `brain/tick.py`

`tick.py` constructs a fresh `LLMBackedPtCns` for each tick. That means no across-tick `LLMBackedPtCns` instance state is retained there. Any per-instance cache inside that object can only help during the lifetime of that tick-local instance.

Do not patch `tick.py` before the Phase 3.14 review gate. The first required result is measurement and design clarity, not a runtime semantic change.

### 2. `brain/llm/ptcns_backed.py`

`LLMBackedPtCns` has a per-instance cache only. The cache begins with `COGITO_ID -> PRESERVE`, which gives the object a local invariant-preserving baseline for Cogito.

Cross-tick reuse is not owned by this object. It is delegated to the transport/client layer, specifically `CachedClient`, when that wrapper is enabled by runtime configuration.

### 3. `brain/llm/client.py`

`CachedClient` uses a SHA-256 prompt-keyed disk cache under `brain/.llm_cache`. On a cache hit, it returns the stored response without calling the inner client. On a miss, it calls the inner client and writes the response.

The cache stores both prompt and response today. That means raw prompts are present in cache files, and those files must not be committed. The cache is an execution artifact, not campaign evidence.

`AnthropicAPIClient`, `ClaudeCLIClient`, and `CodexCLIClient` are transport clients. They are the model-backed call surfaces that can be wrapped by `CachedClient` when policy allows.

### 4. `brain/ui/llm_runtime.py`

`enable_cache` defaults to `false`. The runtime factory wraps model-backed modes in `CachedClient` only when `config.enable_cache` is true.

Offline and mock modes reject caching, which keeps cache policy scoped to model-backed transports. Model-backed execution remains explicit opt-in, and cache discipline must preserve that boundary.

### 5. `brain/llm/prompts.py`

`PROMPT_TEMPLATE` includes both `new_id` and `new_text`. As a result, repeated identical text under different content IDs likely produces different prompt strings and therefore different SHA-256 prompt-cache keys.

This is a plausible source of repeated model calls even when transport caching is enabled.

## Repeated-Call Cause Classification

### A. L0 lifetime too short

`LLMBackedPtCns` has only per-instance cache state. Because `tick.py` constructs a fresh instance per tick, that L0 cache helps only inside one tick instance and cannot by itself prevent across-tick repeated calls.

### B. L1 transport cache disabled

Model-backed clients are uncached unless `--llm-enable-cache` is used. Repeated calls are expected under the current default because `enable_cache` is false.

### C. L1 prompt cache key too volatile

The prompt includes `new_id`. If the same semantic content is evaluated with different content IDs, the prompt string can differ, so the prompt-hash cache can miss even though the requested semantic evaluation is equivalent.

### D. Legitimate context change

Existing MSI contents can change across ticks. Different existing content can be semantically relevant, so not every across-tick request should hit cache.

### E. Retry / parse failure behavior

Retry prompts differ from the original prompt and may need separate policy. A retry is not necessarily the same cache event as the original transport call.

### F. Explicit operator choice

Model-backed modes are opt-in. Cache policy should not make model-backed execution the default or hide model calls behind an implicit runtime path.

## Fix Strategy Comparison

### Option A - enable `CachedClient` by default for model-backed modes

This option should survive to measurement. It is minimal and uses existing code.

Benefits:
- Uses the current transport cache implementation.
- Preserves model-backed mode as an explicit operator choice.
- Makes repeated identical prompts avoid inner client calls without adding a new cache surface.

Risks:
- It can still miss if prompts include volatile IDs.
- It requires a clear config policy: either explicit opt-out for model-backed cache, or strong documentation that model-backed modes are cached by default once the operator has opted into model-backed execution.
- It does not answer semantic-equivalence caching when prompt strings differ.

### Option B - add canonical evaluation cache keyed by semantic evaluation payload

This option should survive to measurement and design. It addresses the case where prompt strings are too volatile for semantic reuse.

Candidate key fields:
- prompt template version
- model/runtime identity if output behavior differs
- existing MSI semantic context
- `new_text`
- exclude `content_id` unless proven semantically necessary

Risks:
- Adds a new surface and likely new catalog rows.
- Requires cache invalidation policy.
- Requires context canonicalization.
- Must be precise about what counts as semantic context.

### Option C - remove or de-emphasize `new_id` from prompt/cache identity

This should survive as a possible sub-option. The risk is that `new_id` may help prompt readability, diagnostics, or trace interpretation.

An alternative is to keep `new_id` in the prompt sent to the model, but use a canonical cache key that excludes it when it is not semantically relevant.

### Option D - session-local eval cache only

This should be deprioritized or rejected as the primary fix. A session-local cache may reduce calls inside a single process, but it does not solve across-run or CLI restart spam.

## Proposed Synthesis Position

Step 3 should measure A against current behavior and confirm C's cache-key volatility. Do not patch `tick.py` first.

The preferred likely direction is A+B:

- model-backed modes should use cache by default or strongly by policy, while still requiring explicit model-backed mode opt-in;
- a canonical evaluation cache may be needed to avoid content-id cache misses.

Step 4 corrigenda should decide the exact cache layer and key. Step 5 catalog planning should make this an explicit row family rather than leaving cache discipline as implicit transport behavior.

## Cache Key Semantics

Semantic candidates:

- `new_text`
- existing MSI text context
- prompt template/version
- model/backend identity if outputs differ
- maybe normalized evaluation mode

Non-semantic or volatile candidates:

- fresh `content_id`
- runtime-generated candidate IDs
- tick index
- trace id
- timestamps
- ordering artifacts not semantically relevant

Caveat: existing MSI membership and text may be semantically relevant, so not every across-tick request should hit cache. Cache discipline must distinguish repeated semantic evaluation from legitimately changed context.

## Corrupt Cache Policy

The final corrupt-cache policy should not be decided in this synthesis. Step 4 should compare and lock one of these policies:

- fail loud on corrupt entry;
- ignore corrupt and refresh;
- quarantine corrupt entry.

The chosen policy must preserve debuggability without silently committing the runtime to stale or malformed execution artifacts.

## Parse Failure / Retry Policy

The current cache should store only the raw transport response, not the parsed enum, unless a new parsed-result cache is explicitly designed.

Retry prompts are different prompts and may be cached separately under L1. If a canonical evaluation cache is introduced, it must decide whether parse failures are cached, skipped, or tagged.

Avoid locking persistent bad responses in a way that causes permanent parse failures without operator control. Any persistent parse-failure behavior should be observable and recoverable.

## Acceptance Criteria for Eventual Implementation

- Offline default unchanged.
- Model-backed explicit opt-in unchanged.
- Cache hit does not call inner client.
- Cache miss calls inner only in explicit model-backed mode.
- Repeated same semantic evaluation across ticks calls inner at most once under enabled/default cache policy.
- Different semantic context still evaluates separately.
- Same text under different content IDs is addressed explicitly.
- Cache hit/miss is observable through tracer or counters.
- Cache files are not committed.
- No raw prompt/model output is committed.
- Cache growth is bounded or policy is documented.
- All gates are green.

## Stage A and Stage B Bridge Usage

Stage B drafted this synthesis file as an exact allowed-file shard. The parent Claude agent owns inspection, acceptance, revision, final validation, staging, commit, and push.

## Non-goals

- No tick semantic change before review.
- No model-backed default.
- No hidden LLM calls.
- No unbounded cache.
- No SelfModel.
- No consciousness, sentience, subjective, semantic, truth, agency, or self-modification claims.

## Recommended Next Artifact

Step 3 should produce:

`docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_PROBE.md`
