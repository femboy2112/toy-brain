# PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md

## Purpose

Phase 3.14 exists to prevent repeated model-backed LLM calls across ticks by
making cache discipline explicit, safe, bounded, testable, and cataloged.

This roadmap is a planning artifact. It does not authorize runtime behavior
changes before the review gate.

## Baseline

- Catalog v0.23.
- Counts: REQUIRED 259 / STRUCTURAL 86 / NOT-EXERCISED 12 / DEFERRED 15 /
  OBSERVED 16.
- Phase 3.13 is complete and merged.
- Stage A read-only ChatGPT/Codex bridge is available.
- Stage B limited-write ChatGPT/Codex bridge is available.
- Existing LLM stack summary:
  - `tick(...)` constructs a fresh `LLMBackedPtCns` every tick.
  - `LLMBackedPtCns` has an internal per-instance cache.
  - `CachedClient` already exists and stores prompt-hash responses under
    `brain/.llm_cache`.
  - `build_llm_client_from_config` wraps model-backed clients in
    `CachedClient` only when `enable_cache` is true.
  - `PROMPT_TEMPLATE` includes `new_id` and `new_text`, so repeated same text
    under different IDs may miss the prompt-hash cache.
  - Offline remains the default.
  - Model-backed runtime modes remain explicit opt-in.

## Problem Statement

External model-backed modes may call the model every tick unless
`--llm-enable-cache` is used. The current per-instance `LLMBackedPtCns` cache can
avoid repeated content-ID work inside one tick instance, but it does not provide
an across-tick or across-run transport guard by itself.

Even when the prompt-hash cache is enabled, repeated same content with different
content IDs may miss if `new_id` is included in the prompt. This means the cache
key may reflect incidental runtime identity instead of the semantic evaluation
payload that should determine whether the model transport call is redundant.

Retry prompts and parse failures need careful handling. A cache policy that
locks in malformed responses, failed parses, or retry scaffolding without an
explicit rule could make bad behavior durable and hard to diagnose.

Offline and mock modes must not gain unnecessary cache behavior. The goal is to
prevent redundant transport calls in explicit model-backed modes and make cache
behavior observable without changing the default offline semantics.

## Current Code Diagnosis

1. `tick(...)` constructs a fresh `LLMBackedPtCns` each tick.
2. `LLMBackedPtCns` per-instance cache only short-circuits content IDs inside
   one tick instance.
3. `CachedClient` is the intended across-tick/across-run layer.
4. `CachedClient` is opt-in via `config.enable_cache`.
5. Model-backed runtime modes are explicit opt-in and must remain so.
6. Prompt identity includes `new_id`, which may reduce cache hits.

## Candidate Fix Strategies

### Option A - enable CachedClient by default for model-backed modes

Enable the existing `CachedClient` wrapper automatically whenever the user has
already opted into a model-backed runtime mode.

Benefits:

- Reuses the existing cache implementation.
- Keeps offline as the default.
- Keeps model-backed behavior explicit opt-in.
- Likely reduces repeated identical prompt transport calls across ticks/runs.

Risks and open questions:

- May not address repeated same text under different content IDs if `new_id`
  remains part of prompt identity.
- Requires explicit corrupt-cache and parse-failure policy.
- Requires clear cache growth bounds or maintenance policy.

### Option B - add canonical LLM evaluation cache keyed by semantic evaluation payload

Add an evaluation-level cache above prompt rendering, keyed by a documented
semantic payload such as normalized evaluation text, relevant mode/config
identity, schema/version, and retry policy.

Benefits:

- Can avoid misses caused by incidental content IDs.
- Makes the cache key easier to reason about and catalog.
- Can separate semantic evaluation identity from prompt formatting details.

Risks and open questions:

- Larger implementation surface than Option A.
- Requires careful versioning so prompt/schema changes do not reuse stale
  results.
- Must prove cache hit paths never call the inner model client.

### Option C - remove or de-emphasize new_id from LLM prompt/cache identity

Reduce the role of `new_id` in prompt identity, either by removing it from the
model prompt when not semantically necessary or by excluding it from the cache
identity while preserving it for trace/debug context.

Benefits:

- Directly targets same-text/different-ID cache misses.
- Smaller than adding a full evaluation cache if prompt identity is the main
  issue.

Risks and open questions:

- The ID may carry useful context for diagnostics or model disambiguation.
- Changing prompt text can change model behavior and must be reviewed before
  runtime semantic changes.
- Requires tests proving the intended cache behavior and trace observability.

### Option D - session-local eval cache only

Add a bounded in-memory session cache for repeated evaluations within one run,
without persistent cache writes.

Benefits:

- Avoids persistent corrupt cache files.
- Can be tightly bounded.
- Useful for repeated tick evaluations inside one process.

Risks and open questions:

- Does not prevent repeated calls across separate runs.
- Duplicates part of the existing `CachedClient` purpose.
- Still needs a documented semantic key and clear miss/hit observability.

### Recommendation

Do not decide implementation in Step 1. Step 2 synthesis should analyze whether
Option A alone is enough or whether Option A plus Option B and/or Option C is
required.

## Guardrails

- Offline remains default.
- Model-backed modes remain explicit opt-in.
- Cache does not make model-backed behavior default.
- No hidden LLM calls.
- No unbounded cache growth.
- Cache key is deterministic and documented.
- Cache hit must not call the inner client.
- Cache miss may call the inner client only in explicit model-backed mode.
- Corrupt cache policy must be explicit.
- Parse-failure/retry cache semantics must be explicit.
- No raw prompts committed.
- No secrets committed.
- No cache files committed.
- `brain/.llm_cache` remains ignored or becomes explicitly ignored if needed.
- No tick semantic change before review gate.

## Required Future Measurements

Step 3 must measure or reproduce:

- Cache disabled repeated calls.
- Cache enabled identical prompt hit.
- Same text with different content IDs behavior.
- Retry/failure behavior.
- Cache file write/read behavior.
- No cache use in offline/mock unless expected.
- Trace events `llm.cache_hit` / `llm.cache_miss` if available.

## Bridge Collaboration Policy

- Stage A is for review.
- Stage B is for bounded write shards only.
- No raw Codex.
- No parallel calls.
- No automatic retries.
- Exact allowed-file list required.
- Parent Claude validates/commits/pushes.
- Stage B may be useful for isolated docs and fixture shards after review gates,
  not for uncontrolled runtime rewrites.

## Non-goals

- No consciousness, sentience, subjective, semantic, truth, agency, or
  self-modification claims.
- No hidden LLM calls.
- No unbounded cache.
- No tick semantic change before review.
- No default model-backed behavior.
- No `SelfModel`.
- No Growth Ledger semantic change.

## Next Artifact

Step 2:
`docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_SYNTHESIS.md`
