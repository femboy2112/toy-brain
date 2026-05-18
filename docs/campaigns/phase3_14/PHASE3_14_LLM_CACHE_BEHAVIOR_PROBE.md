# PHASE3_14_LLM_CACHE_BEHAVIOR_PROBE.md

## Purpose

This report measures current LLM cache behavior and repeated-call behavior before any implementation. It is documentation only. It records deterministic in-process probe results and does not change ToyI runtime semantics, cache policy, catalog rows, fixtures, or code.

## Baseline

- Catalog v0.23
- Counts: REQUIRED 259 / STRUCTURAL 86 / NOT-EXERCISED 12 / DEFERRED 15 / OBSERVED 16
- Branch: campaign/phase3-14-llm-cache-discipline
- Step 1 mission sync complete
- Step 2 synthesis complete
- No cache implementation yet

## Method

- Temporary helper path: `/tmp/phase3_14_llm_cache_probe.py`
- Command: `PYTHONPATH=/home/leah/brain/toy-brain python3 /tmp/phase3_14_llm_cache_probe.py`
- Clients used: `CountingClient` local fake, `MockClient` from `brain.llm.client`, `CachedClient` from `brain.llm.client`, `LLMBackedPtCns` from `brain.llm.ptcns_backed` over `make_msi` / `make_profile_with_cogito`, `build_llm_client_from_config` from `brain.ui.llm_runtime` for offline/mock isolation, and `MemoryTracer` for trace capture.
- Cache directory: ephemeral `tempfile.TemporaryDirectory()` under `/tmp`; `brain/.llm_cache` was not touched.
- No real LLM calls were made. The probe did not use `AnthropicAPIClient`, `ClaudeCLIClient`, or `CodexCLIClient`.
- No repo file mutation occurred during measurement, and no cache files were committed.

## Measurement Table

| Measurement ID | Question | Setup | Observed result | Interpretation | Design implication | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Does the L0 per-instance cache survive instance teardown? | Two separate `LLMBackedPtCns` instances over the same MSI/text/client. Each instance evaluated content_id `new_x` once. | `inner_calls = 2` across the two instances. | L0 cache does not survive instance teardown, confirming L0 alone cannot prevent across-tick repeated calls. | Across-tick repeated-call control needs a longer-lived cache layer than `LLMBackedPtCns` instance state. | reproduced |
| M2 | What happens when L1 transport cache is disabled? | Bare `CountingClient` with no `CachedClient`; two identical `eval_consistency("identical prompt please")` calls. | `inner_calls = 2`. | Without `CachedClient`, identical prompts always call the inner client. | Current repeated-call behavior is expected when cache is not enabled; policy must decide whether model-backed selected modes should cache by default or remain opt-in. | reproduced |
| M3 | Does L1 cache avoid an inner call for an identical prompt? | `CachedClient(CountingClient, cache_dir=/tmp/.../m3_cache)` with two identical `eval_consistency` calls. | `inner_calls = 1`; `hit_count = 1`; `miss_count = 1`; one JSON file written. | `CachedClient` correctly avoids the inner call on the second identical prompt. | The existing transport cache works for byte-identical prompt strings. | reproduced |
| M4 | Does same `new_text` under different `content_id` produce different prompt keys? | Two `LLMBackedPtCns` evals with identical `new_text` but content_id `new_x` vs `new_y`. | Two prompts captured by `CountingClient`; `prompts_equal = False`; `new_x` appears in prompt0, `new_y` appears in prompt1; the shared substring `the new content under evaluation` is present in both. | `PROMPT_TEMPLATE`'s `- ID: {new_id}` line forces semantically equivalent evaluations to produce distinct prompt strings; SHA-256 prompt-hash cache misses on the second call even though `new_text` is identical. | L1 prompt hashing alone is not enough if volatile diagnostic IDs remain in the prompt string and semantic reuse is required. | reproduced |
| M5 | Do legitimate context changes alter prompt identity? | Two `LLMBackedPtCns` evals with the same `new_text`/`new_id` but different existing MSI texts, `anchor a description` vs `anchor a DIFFERENT description`. | `prompts_equal = False`; the differing line shows up in the prompt body. | MSI context changes do change prompt identity for a semantically relevant reason. | Any canonical cache key must preserve MSI semantic context. | reproduced |
| M6 | What cache footprint is produced by retry / parse-failure behavior? | `MockClient` sequence `["nonsense", "PRESERVE"]`, wrapped in `CachedClient`; one `LLMBackedPtCns` eval triggers exactly one retry. | `inner_calls = 2` original + retry; `cache_file_count = 2`; `distinct_prompts_cached = 2`; `responses_seen = ["PRESERVE", "nonsense"]`. | The bad `nonsense` response was cached under the original prompt's hash. The retry prompt was cached under its own hash. If those exact prompts recur in a future run, the cache will replay the `nonsense` response and the parse failure will recur. | Phase 3.14 must lock parse-failure / retry cache policy before implementation. | reproduced |
| M7 | Does factory policy isolate offline/mock deterministic clients from cache wrapping? | `build_llm_client_from_config(LlmRuntimeConfig(mode=OFFLINE, enable_cache=True))`; same for `MOCK` with `mock_responses=("PRESERVE",)`. | Both raise `LlmRuntimeError` with `--llm-enable-cache is not supported for mode 'offline'; caching deterministic clients adds no value`. | Factory refuses to wrap deterministic clients in `CachedClient`. | Offline / mock isolation currently happens at factory construction time; Step 4 must decide whether that remains the policy. | reproduced |
| M8 | Is cache hit/miss observable through tracing? | `CachedClient(CountingClient, cache_dir=/tmp/.../m8_cache, tracer=MemoryTracer())`; two identical `eval_consistency` calls. | `tracer.events = [{"type": "llm.cache_miss", ...}, {"type": "llm.cache_hit", ...}]`. | Cache hit/miss is observable through `CognitionTracer` when one is supplied. | Implementation criteria can require trace visibility for cache events. | reproduced |
| M9 | What is persisted in cache files? | `CachedClient(CountingClient, cache_dir=/tmp/.../m9_cache)` with one `eval_consistency` call. | One JSON file named `<sha256_hex>.json` with keys `["prompt", "response"]`; both prompt text and response text persisted verbatim. | Cache files contain raw prompts and raw responses. | Cache files must remain gitignored and uncommitted; campaign docs must not commit raw prompt or raw response bodies. | reproduced |

## Measured vs Policy Decision

This report measures the *currently observed* behavior of the existing
`LLMBackedPtCns` / `CachedClient` / `build_llm_client_from_config` stack
under deterministic local clients. It does not declare what the cache
*should* do. M1-M9 are evidence inputs for Step 4 corrigenda; the
corrigenda are where policy is locked. In particular, none of the
following are concluded by this report:

- Whether SHA-256-of-rendered-prompt should remain the stable cache
  key contract.
- Whether parse-failure caching is correct, a bug, or
  policy-dependent.
- Whether L1 (transport prompt-hash cache) alone is sufficient or
  whether L2 (canonical semantic evaluation cache) is required.
- Whether `new_id` should be excluded from a future cache key.
- Whether offline / mock isolation should remain enforced at factory
  construction time or be re-checked at runtime as well.

## Repeated-Call Cause Classification Update

- A. L0 lifetime too short -> confirmed (M1). Behavioral observation:
  per-instance cache state does not survive instance teardown.
- B. L1 disabled by policy -> confirmed (M2). The cache wrapper is
  opt-in via `enable_cache` and is not constructed by default for
  model-backed modes.
- C. L1 prompt key volatile due to `new_id` -> confirmed at the
  prompt-string level (M4). The prompt string differs when `new_id`
  changes, so SHA-256-of-prompt cache misses. Whether `new_id` should
  remain in the prompt and/or in the cache key is a Step 4 decision.
- D. Legitimate semantic context changes -> confirmed (M5). The
  prompts differ for a semantically relevant reason; this is not
  cache key "volatility" so much as evidence that MSI context is
  part of the semantic identity of an evaluation.
- E. Retry / parse failure behavior -> currently cached and
  replayable (M6). The "nonsense" raw response is persisted under the
  original prompt's hash; on a future run with the same inputs the
  cache would replay the failure. Whether this is desirable
  determinism or undesirable lock-in is a Step 4 policy decision.
- F. Explicit operator choice -> the one measured factory path raises
  `LlmRuntimeError` when `--llm-enable-cache` is set for OFFLINE or
  MOCK (M7). The probe did not exercise every possible path that
  could read an existing cache file from offline/mock; that broader
  isolation check is a Step 4 open question.

## Cache Key Unknowns Before Step 4

The current behavior on disk is "SHA-256 hex of the rendered prompt
string". The probe did not measure whether the following dimensions
*should* be part of the cache key, nor whether they are isolated today:

- Model / provider identity (e.g. `claude-sonnet-4-6` vs another
  model under `AnthropicAPIClient`; `claude-cli` vs `codex-cli`). Two
  configurations sharing identical prompt text could collide under
  the same key today.
- Runtime options that change model output (max_tokens, temperature,
  system message contents, etc.) are not part of the on-disk key
  today.
- Parser / schema version. The cache stores raw responses; if the
  parser changes its grammar (Phase 2 v1.2 tightened parsing), an
  older cached raw response could parse differently under a newer
  parser.
- Prompt template version. `PROMPT_TEMPLATE` is currently a
  module-level constant with no version field; a change to the
  template would silently invalidate semantic equivalence but not
  the prompt-hash key, so old cache entries could still be served.
- Corrupt cache file behavior. The probe did not measure how
  `CachedClient` behaves on a truncated / malformed JSON file. Step 4
  should pick fail-loud / ignore-and-refresh / quarantine.
- Disabled-cache-with-existing-files behavior. The probe did not
  exercise running with `enable_cache=False` while
  `brain/.llm_cache/` already contains entries from a prior session.
- Offline / mock paths with existing files. M7 only covers factory
  rejection at construction; whether a runtime path could ever read
  an existing cache file in offline/mock mode is unmeasured.
- Concurrency / atomicity. Simultaneous writes to the same cache
  key, partial writes, and read-after-failed-write are unmeasured.
- Retry replay determinism. A second run after M6 with the same
  inputs is expected to reproduce the failure-then-success sequence,
  but that exact replay was not executed.

Step 4 must decide which of these dimensions become explicit parts of
the cache key contract, which become structural rules elsewhere
(e.g. factory invariants), and which remain documented as known
limitations.

## Sensitive Local Artifact Warning

`brain/.llm_cache/<sha256>.json` files contain raw prompt text and raw
model response text. They must be treated as sensitive *local*
artifacts:

- Already gitignored under `brain/.llm_cache`; do not commit.
- Do not paste cache file contents into PR descriptions, commit
  messages, audit reports, or campaign docs.
- Do not upload cache files as build artifacts, test snapshots, or
  CI logs.
- Trace events `llm.cache_hit` / `llm.cache_miss` currently include
  an 8-char key prefix only; Step 4 must keep raw prompt and raw
  response text out of trace payloads.
- If a sample cache file ever needs to be referenced for design
  evidence, the example must use synthetic prompts and synthetic
  responses, not captured production text.

## Design Question Resolution for Step 4

Step 4 corrigenda must lock the following:

- Should model-backed modes cache by default once explicitly selected?
- Should there be an opt-out flag, for example `--llm-disable-cache`?
- Is a canonical semantic evaluation cache required, or is L1 alone enough?
- What fields go into the canonical key? Candidates: `new_text`, existing MSI semantic context as ordered text tuples, prompt template version, model/backend identity. Excludes: `new_id`, candidate IDs, tick index, trace IDs, timestamps.
- Should `new_id` be excluded from cache key?
- Should `new_id` remain in the prompt text for diagnostics, even if excluded from cache key?
- Corrupt cache policy: fail-loud / ignore-and-refresh / quarantine.
- Parse-failure / retry policy: skip caching parse failures / tag parse failures so they are bypassed on hit / cache them but require explicit eviction.
- Cache size / lifecycle policy: file count cap / byte-size cap / TTL / explicit invalidation.
- Offline / mock isolation policy: factory rejects vs runtime no-write (today: factory rejects -- M7).

## Safety / Non-goal Verification

- No real external LLM call: M1-M9 used only deterministic local clients.
- No model-backed default change.
- No hidden LLM call.
- No tick semantic change.
- No code/catalog/fixture change.
- No cache files committed; cache directory was a tempfile.
- No raw prompts committed.
- No secrets committed.
- No SelfModel.
- No Growth Ledger semantic change.

## Stage A and Stage B Disclosure

Stage B disclosure: Stage B drafted this file as an exact allowed-file shard. The bounded worker was allowed to edit only `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_PROBE.md`.

Stage A disclosure: Stage A reviewed the draft after measurements
(`/ask-chatgpt --mode review --model gpt-5.5 --effort medium`).
Confidence: high. Disagreement: minor. Accepted advice incorporated
into this report: added "Measured vs Policy Decision", added "Cache
Key Unknowns Before Step 4", added "Sensitive Local Artifact
Warning", softened M5/M7/M8 framing to distinguish measured behavior
from intended policy, and rewrote the Cause Classification Update to
avoid overclaim. Rejected advice: did not add a fresh round of probe
measurements for model/provider namespace, corrupt-cache behavior,
disabled-cache-with-existing-files, and retry-replay determinism in
this step; those are listed under "Cache Key Unknowns Before Step
4" as open questions for the Step 4 corrigenda and / or a Step 7
implementation probe. The parent Claude agent owns final validation,
staging, commit, and push.
