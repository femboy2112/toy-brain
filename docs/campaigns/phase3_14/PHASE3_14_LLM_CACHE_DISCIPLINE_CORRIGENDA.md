# PHASE3_14_LLM_CACHE_DISCIPLINE_CORRIGENDA.md

## Purpose

This corrigenda locks the Phase 3.14 LLM cache policy after the Step 2 synthesis and Step 3 behavior probe. It does not authorize implementation. Implementation remains blocked until:
- Step 5 catalog patch plan
- Step 6 Review Gate A
- Step 7 implementation, if accepted.

## Baseline

- Catalog v0.23
- Counts: REQUIRED 259 / STRUCTURAL 86 / NOT-EXERCISED 12 / DEFERRED 15 / OBSERVED 16
- Phase 3.14 Steps 1-3 complete (commits 870a0ce, 0a150f8, cc24cca on campaign/phase3-14-llm-cache-discipline).
- Step 2 synthesis favored A+B (default L1 for explicit model-backed modes + canonical semantic eval cache).
- Step 3 reproduced all nine measurement families M1-M9.
- No implementation has occurred yet.

Step 3 measurement summary:
- M1 L0 lifetime: 2 separate LLMBackedPtCns instances -> inner_calls=2; per-instance cache does not survive teardown.
- M2 L1 disabled: bare CountingClient -> 2 inner_calls.
- M3 L1 enabled identical prompt: 1 inner call; 1 miss + 1 hit; 1 cache file.
- M4 same new_text different content_id: prompts differ; SHA-256 prompt-hash misses.
- M5 same new_text/new_id different MSI texts: prompts differ for legitimate semantic reason.
- M6 retry/parse failure: 2 cache files written, including the "nonsense" raw response under the original prompt hash; replay would reproduce the parse failure.
- M7 offline/mock isolation: build_llm_client_from_config raises LlmRuntimeError on OFFLINE+enable_cache and MOCK+enable_cache.
- M8 trace observability: MemoryTracer captured llm.cache_miss then llm.cache_hit.
- M9 cache file safety: cache files are <sha256_hex>.json with keys ["prompt", "response"]; must remain gitignored.

## Corrigenda Authority

- These locks bind Step 5 and any Step 7 implementation.
- A later review gate may override a lock only by naming the lock and giving a reason.
- Repo-local invariants win over this document.

## Cache–Tick Semantic Boundary

Phase 3.14 caching is a cost / reproducibility / observability mechanism. It is not a semantic mechanism. The following invariants apply to every lock below and override any apparent conflict:

- Cache hits, cache misses, and cache writes do not change tick semantics before the Phase 3.14 review gate. Bit-for-bit `(new_state, record)` parity at the kernel boundary is preserved when the same model-backed inputs are evaluated with caching vs without.
- "Semantic" in "semantic evaluation cache" refers to cache *identity*, not to a claim that ToyI understands meaning. Cache identity equivalence must be proven by explicit inputs and versions; the cache is not a truth-adjudicator.
- A cache hit may only return a previously-recorded model-backed result. It may never substitute for a model call in offline / mock modes, and may never elevate an offline path into model-backed behavior.
- Any catalog row, fixture, or implementation that implies cache hits alter tick outcomes before the review gate is out of scope and must be rejected at Step 5 / Step 6.

## LOCK A — Cache layer scope

Lock: Use L0 + L1 + L2.

Definitions:
- L0: Existing per-instance LLMBackedPtCns._cache. Keep as-is.
- L1: Transport cache via CachedClient. Model-backed modes should use L1 by default after the operator explicitly opts into a model-backed mode.
- L2: New canonical semantic evaluation cache to handle repeated same semantic evaluation when rendered prompt strings differ because of volatile IDs.

State: Do not patch tick() for L0/L1/L2 behavior unless Step 5 proves unavoidable.

## LOCK B — Model-backed cache default policy

Lock: Once the operator explicitly selects a model-backed mode (anthropic-api, claude-cli, codex-cli), the runtime enables L1 transport caching by default. Offline remains default. Model-backed execution remains explicit opt-in.

Add an explicit opt-out flag: --llm-disable-cache.

Policy:
- enable_cache defaults to true for model-backed modes
- --llm-disable-cache forces cache off for model-backed modes
- --llm-enable-cache remains accepted for compatibility and is a no-op / explicit affirmation for model-backed modes
- offline/mock still reject both --llm-enable-cache and --llm-disable-cache if those flags are not meaningful

Step 5 may refine CLI compatibility wording if repo evidence requires it.

## LOCK C — L2 canonical evaluation cache required

Lock: L2 canonical evaluation cache is required because Step 3 M4 reproduced that same text with different content IDs produces different prompt hashes.

L2 cache must key on semantic evaluation payload, not volatile content IDs.

Candidate implementation options may be decided in Step 5, but policy is locked:
- L1 alone is insufficient.
- Synthesis Option C survives only as an implementation detail: keep new_id in prompt text for diagnostics, but exclude it from L2 canonical cache identity.

Step 5 proof obligation: L2 reuse is permitted only when key equivalence is proven by documented inputs and versions. Step 5 must enumerate the canonicalization function and the exact set of input fields that constitute "the same semantic evaluation". Without that enumeration, L2 reuse is not authorized.

## LOCK D — L2 semantic key fields

Lock L2 key fields:

Required semantic fields:
- cache_schema_version
- prompt_template_version
- parse_schema_version
- backend_family
- model_identity
- existing_msi_context
- new_text

Excluded non-semantic / volatile fields:
- content_id / new_id
- stream chunk id
- candidate id
- tick index
- trace id
- timestamp
- Python object id
- file path
- process id
- hostname
- environment variables
- retry attempt number, except as part of retry-policy metadata outside canonical success key

Existing MSI context:
Use deterministic ordered tuple of existing MSI content text pairs or content descriptors. Step 5 must define exact canonicalization. It must preserve semantically relevant differences, as Step 3 M5 confirmed.

## LOCK E — Keep new_id in model prompt, exclude from L2 key

Lock: new_id remains in the prompt text for diagnostics/trace readability in v1.

But new_id is excluded from L2 canonical cache key.

Rationale:
- Step 3 M4 shows new_id causes volatile prompt-hash misses.
- Removing new_id from prompt could reduce diagnostic clarity.
- L2 allows semantic cache reuse without changing prompt text before a deeper prompt-design review.

Step 5 proof obligation: the catalog patch plan and accompanying fixtures must produce repo-local evidence that excluding new_id from the L2 cache key cannot change semantic result selection, provenance, or replay expectations for the v1 prompt template. If that evidence cannot be produced, the L2 key must either include new_id or the lock must be reopened at Review Gate A.

## LOCK F — L1 prompt cache remains raw prompt-hash

Lock: Keep existing CachedClient prompt-hash behavior for L1.

Do not mutate L1 into semantic cache.

L1 remains transport-layer cache:
- key = rendered prompt SHA-256
- hit returns raw response
- miss calls inner client and writes raw response

If L2 is implemented, it sits above or beside L1 in a clearly documented layer, not by silently changing CachedClient semantics.

## LOCK G — Corrupt cache policy

Lock:
- L1 corrupt cache entry policy: fail loud with bounded error, as current CachedClient does for corrupt entries.
- L2 corrupt cache entry policy: fail loud in v1.

No silent refresh. No hidden network call to repair corrupt cache.

Reason: silent refresh could cause unexpected model calls and violate cache discipline. A later campaign may add explicit repair/quarantine behavior.

## LOCK H — Parse failure / retry policy

Lock:
- Do not store parse failures in L2 success cache.
- L2 success cache may store only parse-success results, or raw response + parsed enum only after parse success.

For L1:
Existing raw prompt-hash cache may cache raw bad responses because it is transport-layer cache. Step 5 must decide whether to wrap/avoid L1 for retry prompts or leave this behavior documented.

Retry prompts:
- retry prompt remains a separate transport prompt at L1
- retry attempt number is not part of L2 success key
- a parse-failed raw response must not poison the L2 success key
- any persistent parse failure behavior must be observable and evictable by deleting cache files

Failure class separation: the following classes must not collapse into a single cache state. Each class has distinct handling and may not satisfy an authoritative L2 success hit:

- parse failure (raw response could not be parsed into a ConsistencyEval)
- provider failure (transport error: HTTP non-2xx, connection error, subprocess non-zero)
- timeout (transport timeout)
- refusal / empty output (parseable but rejected by parser as ambiguous, empty, or refused)
- schema mismatch (raw response shape unexpected at the transport layer)
- corrupt cache entry (handled separately under LOCK G)

Step 5 must enumerate which of these classes are L1-cached as raw transport responses, which are bypassed at L1, and which are explicitly excluded from L2 success caching. Diagnostic recording of failures (e.g. for trace observability) is allowed only if those records cannot be read back as a cache hit.

## LOCK I — Cache size / lifecycle policy

Lock: Phase 3.14 v1 must include a bounded growth policy.

Preferred policy:
- max cache entries cap for L2, default 1024 entries
- hard refusal or deterministic pruning must be decided in Step 5
- if L1 is left as existing unbounded disk cache, Step 5 must either:
  A. add L1 bound now, or
  B. explicitly mark L1 bounding as a deferred follow-up and bound only L2

Recommended: Add a bound for any new L2 surface in v1. Do not silently leave new cache unbounded.

Step 5 must decide the exact cap and behavior at cap.

## LOCK J — Offline/mock isolation

Lock: Offline and mock modes must never read or write L1/L2 cache files.

Existing factory rejection for enable_cache=True on OFFLINE/MOCK remains.

If --llm-disable-cache is added, offline/mock must either reject it as meaningless or ignore it with no cache access. Step 5 must choose.

No cache files read under OFFLINE/MOCK even if cache files exist on disk.

## LOCK K — Cache observability

Lock: Cache hit/miss must be inspectable.

Required:
- L1 continues tracer events:
  - llm.cache_hit
  - llm.cache_miss

L2 must expose analogous bounded tracer events if implemented:
- llm.semantic_cache_hit
- llm.semantic_cache_miss
- llm.semantic_cache_store
- llm.semantic_cache_skip or equivalent for parse failure

Trace payloads:
- key prefix only
- no raw prompt
- no raw response
- no secret
- no full cache key if it may expose text

Observability minimums: at least the following cache decisions must be externally inspectable in trace output or in a structured local report, without requiring a hidden model call to surface them:

- cache disabled (operator opted out or factory rejected)
- cache miss (key not present; inner client will be called)
- cache hit (key present; inner client will not be called)
- cache bypass (mode-gated or class-gated skip, e.g. retry path)
- cache invalid (schema/version mismatch detected at read time)
- cache corrupt (file unreadable / digest mismatch / partial write)
- cache write skipped (e.g. parse failure not stored in L2 success cache)
- cache write success (entry persisted)

Step 5 must define the exact trace event names for L2 and the structured report fields, consistent with LOCK K's `llm.semantic_cache_*` naming family. The fixture suite at Step 7 must prove no hidden LLM call surfaces any of these states.

## LOCK L — Sensitive artifact policy

Lock: Cache files are sensitive local artifacts.

Rules:
- no cache files committed
- no raw prompt in campaign docs
- no raw model response in campaign docs
- no cache files uploaded as artifacts
- examples must be synthetic
- .gitignore must cover cache dirs
- Step 5/7 must verify gitignore coverage

## LOCK M — Key namespace policy

Lock: L2 key must be namespaced by:
- cache_schema_version
- prompt_template_version
- parse_schema_version
- backend_family
- model_identity

Reason: Step 3 identified model/provider, parser/schema, and template-version namespace risks. Do not let different models/providers share the same semantic cache entry unless explicitly proven equivalent.

## LOCK N — No tick semantic change

Lock: brain/tick.py must remain untouched unless Step 5 proves unavoidable and Step 6 explicitly authorizes a tick change.

Preferred implementation surface:
- brain/llm/client.py
- brain/ui/llm_runtime.py
- maybe brain/llm/prompts.py only if constants/versioning needed
- new fixtures
- catalog/version files

## LOCK O — No model-backed default

Lock: Offline remains default. Cache defaults may change only after a model-backed mode is explicitly selected. Cache policy must never cause offline launch to call a model.

## LOCK P — No hidden LLM calls

Lock:
- cache hit must not call inner client
- corrupt cache must not silently call inner client
- offline/mock must not call model
- disabled cache must behave as documented
- any model call requires explicit model-backed mode

## LOCK Q — Stage A / Stage B collaboration policy

Lock:

Stage A required for:
- Step 5 catalog patch plan review
- Step 8 behavior report review
- Step 10 audit review unless explicitly redundant

Stage B allowed for:
- Step 5 catalog plan draft, single allowed file
- Step 7 implementation shards only after Review Gate A, with exact allowed-file lists
- no more than 3 real Stage B calls during Step 7 without fresh operator approval

Stage B forbidden for:
- broad repo edits
- raw codex
- staging/commit/push
- brain/tick.py unless explicitly authorized by Step 6

## LOCK R — Non-goals / claim boundaries

Lock: No consciousness/sentience/subjective/semantic/truth/agency/self-modification claims.

Important nuance: the phrase "semantic cache key" is engineering language about cache identity, not a claim that ToyI understands semantics.

Use wording:
- "semantic evaluation payload"
- "cache identity"
- "text/context equivalence"

Avoid wording:
- "ToyI understands"
- "true meaning"
- "semantic authority"

## LOCK S — Required Step 5 planning obligations

Step 5 must produce:
docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_CATALOG_PATCH_PLAN.md

It must include:
- exact cache layer architecture
- exact row family
- exact statuses
- exact v0.24 count delta
- exact fixture list
- exact implementation files
- cache key constants/version fields
- cache bounds/cap behavior
- Stage A/Stage B usage
- stop at Review Gate A

Step 5 must not implement.

## Stage A and Stage B Disclosure

Stage B disclosure:
This corrigenda was drafted by Stage B as an exact allowed-file shard limited to docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_CORRIGENDA.md. Stage B made no implementation changes, did not stage, did not commit, and did not push.

Stage A disclosure:
Stage A reviewed the draft for under-specified locks before Step 5 catalog planning (`/ask-chatgpt --mode review --model gpt-5.5 --effort medium`). Confidence: medium. Disagreement: minor. Accepted advice incorporated into this corrigenda:
- Added the "Cache–Tick Semantic Boundary" subsection between Corrigenda Authority and LOCK A, capturing the non-tick-semantic invariant for every lock below.
- Added a Step 5 proof obligation to LOCK C requiring canonicalization-function enumeration before L2 reuse is authorized.
- Added a Step 5 proof obligation to LOCK E requiring repo-local evidence that excluding new_id from the L2 key cannot change semantic result selection, provenance, or replay expectations.
- Added explicit failure class separation to LOCK H (parse failure, provider failure, timeout, refusal/empty, schema mismatch, corrupt entry) so Step 5 cannot collapse them into a single cache state.
- Added an observability minimums list to LOCK K (disabled / miss / hit / bypass / invalid / corrupt / write_skipped / write_success).

Rejected advice (deferred to Step 5):
- Did not split LOCK A into a finer per-layer responsibility matrix in Step 4; precedence and invalidation between L1 and L2 is locked at the Cache–Tick Semantic Boundary and the per-lock policy level, with the exact architecture diagram deferred to Step 5.
- Did not pre-define the full L2 key field grammar (canonicalization function shape); LOCK D enumerates the required fields and excluded fields, and Step 5 owns the exact canonicalization function.
- Did not add a separate retention / repository-artifact policy section beyond LOCK L; Step 5/7 verifies gitignore coverage as already required.

Parent Claude owns inspection, acceptance, revision, validation, staging, commit, and push.
