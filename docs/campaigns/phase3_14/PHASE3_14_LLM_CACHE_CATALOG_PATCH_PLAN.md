# PHASE3_14_LLM_CACHE_CATALOG_PATCH_PLAN.md

## Purpose

This plan converts the Step 4 LOCK A through LOCK S corrigenda into an exact catalog / version / fixture / implementation plan for Phase 3.14 LLM Cache Discipline.

- Step 5 does not authorize implementation.
- Step 6 Review Gate A must explicitly accept, amend, or reject this plan.
- Step 7 may implement only after Step 6 acceptance.

## Baseline

- Catalog v0.23
- Counts: REQUIRED 259 / STRUCTURAL 86 / NOT-EXERCISED 12 / DEFERRED 15 / OBSERVED 16
- Phase 3.14 Steps 1-4 complete (commits 870a0ce, 0a150f8, cc24cca, 5f23b1b on campaign/phase3-14-llm-cache-discipline).
- Step 3 reproduced M1-M9.
- Step 4 LOCK A through LOCK S bind this plan.
- Stage A and Stage B bridges available.

## Locks Imported from Corrigenda

LOCK A - Cache layer scope: Phase 3.14 uses L0 + L1 + L2 architecture. L0 is the existing per-instance `LLMBackedPtCns._cache`; L1 is the existing raw rendered-prompt SHA-256 `CachedClient` transport cache; L2 is a new canonical semantic evaluation cache for repeated equivalent evaluations whose rendered prompt strings differ because of volatile IDs.

LOCK B - Model-backed cache default policy: once a model-backed mode is explicitly selected, L1 is on by default. Add `--llm-disable-cache` as the model-backed opt-out flag. Keep `--llm-enable-cache` as accepted explicit affirmation / compatibility. If both flags are supplied, the runtime must fail with a bounded `LlmRuntimeError`.

LOCK C - L2 required: L1 alone is insufficient because Step 3 M4 reproduced prompt-hash misses for same `new_text` with different content IDs. Step 5 must enumerate the L2 canonicalization function before Step 7 may implement it.

LOCK D - L2 semantic key fields: L2 key identity must include cache schema version, prompt template version, parse schema version, backend family, model identity, existing MSI context, and new text. It must exclude volatile runtime fields such as evaluated content ID / `new_id`, chunk IDs, candidate IDs, tick index, trace ID, timestamp, object ID, process ID, hostname, environment variables, and retry attempt number.

LOCK E - Keep `new_id` in prompt, exclude from L2 key: `new_id` remains in the rendered prompt for diagnostics and trace readability, but is excluded from the L2 key. Step 7 fixtures must provide repo-local evidence that this does not change semantic result selection, provenance, or replay expectations for the v1 prompt template.

LOCK F - L1 prompt cache remains raw prompt-hash: keep `CachedClient` as the raw rendered-prompt SHA-256 transport cache with hit / no-inner-call and miss / inner-call semantics. Do not mutate L1 into the semantic cache.

LOCK G - Corrupt cache policy: corrupt cache fails loud at both L1 and L2. Do not silently refresh, quarantine, or call the inner model path to repair corrupt entries in v1.

LOCK H - Parse failure / retry policy: parse failures are excluded from L2 success cache. Failure classes remain distinct: parse failure, provider failure, timeout, refusal / empty output, schema mismatch, and corrupt entry must not collapse into a single L2 cache state.

LOCK I - Cache size / lifecycle policy: Phase 3.14 v1 must include bounded growth for new L2 cache surface. This plan sets the L2 cap at 1024 entries and defers L1 bounding.

LOCK J - Offline / mock isolation: offline and mock modes never access L1 or L2 cache files. `--llm-enable-cache` rejects for offline / mock; `--llm-disable-cache` may be accepted as a no-op but must not unlock any cache reads or writes.

LOCK K - Cache observability: preserve existing L1 `llm.cache_hit` and `llm.cache_miss` events. Add bounded L2 events for semantic hit, miss, store, and skip / write skipped. Payloads may include short key prefixes and bounded reasons, but no raw prompt, raw response, secret, or full key.

LOCK L - Sensitive local artifact rules: L1 / L2 cache files are local sensitive artifacts. They must remain gitignored, must not be committed, and must not appear as raw prompt / response content in docs, fixtures, logs, PR text, or test output.

LOCK M - L2 namespace versioning: L2 keys must be namespaced by `cache_schema_version`, `prompt_template_version`, `parse_schema_version`, `backend_family`, and `model_identity`, so stale entries cannot silently cross model, prompt, parser, or backend boundaries.

LOCK N - Tick boundary: `brain/tick.py` remains untouched unless explicitly authorized. Step 7 must prove cached and uncached evaluation preserve the same `(new_state, TickRecord)` for the same client responses.

LOCK O - Offline remains default: model-backed mode remains explicit opt-in. Cache defaults only change after the operator explicitly selects model-backed mode.

LOCK P - No hidden LLM calls: cache misses may call the inner model-backed path only when explicit model-backed mode is selected. Cache hit / corrupt / repair / offline / mock paths must not hide model calls.

LOCK Q - Stage A/B collaboration policy: Stage B may be used only for bounded allowed-file shards. Parent Claude owns inspection, acceptance, validation, staging, commit, and push. Stage B never edits `brain/tick.py`.

LOCK R - No cognitive / claim-boundary drift: "semantic cache key" is engineering cache identity only. It does not assert ToyI understanding, meaning, truth, or any cognitive upgrade.

LOCK S - Step 5 planning obligations: Step 5 must produce this exact catalog / version / fixture / implementation plan and stop before implementation. Review Gate A decides whether the plan is accepted, amended, or rejected.

## Cache Architecture Decision for Step 7

If Review Gate A accepts this plan, Step 7 should implement the following architecture.

L0:
- Keep `LLMBackedPtCns._cache` unchanged.
- No `brain/tick.py` changes.

L1:
- Keep `CachedClient` as raw rendered-prompt SHA-256 transport cache.
- Keep L1 file format as existing `{prompt, response}` JSON.
- Preserve `llm.cache_hit` / `llm.cache_miss` tracer events.
- Add model-backed default cache-on policy in `brain/ui/llm_runtime.py`.

L2:
- Add a canonical semantic evaluation cache helper inside `brain/llm/ptcns_backed.py` or as a small helper module imported by `ptcns_backed.py`.
- Position L2 around `_build_prompt` / `parse_consistency_eval`, so L2 derives structured key fields directly from MSI / `content_texts` / config rather than reverse-engineering them from the rendered prompt.
- It must not mutate `brain/tick.py`.
- It must not import `brain.ui`.
- It must not call a real model directly; on miss it routes through the existing client, which may itself be wrapped in `CachedClient` at L1.
- It must store only parse-success entries.
- It must have bounded cap behavior under LOCK I.

Critical design question: `LLMClient.eval_consistency(prompt: str)` only receives a rendered prompt. L2 cannot derive semantic key fields from prompt alone safely. Step 5 chooses among:

- Option 1: Add a cache-aware PtCns layer or modify `LLMBackedPtCns` so it builds the semantic cache key before rendering prompt, then checks L2 before calling client.
- Option 2: Add a new `LLMClient` method / protocol extension that accepts a structured cache key payload.
- Option 3: Keep L2 out of `client.py` and implement semantic cache in `ptcns_backed.py` around `_build_prompt` / `parse_consistency_eval`.

Recommended: Option 3. Implement L2 inside `brain/llm/ptcns_backed.py`. This avoids `tick.py` changes, avoids `LLMClient` Protocol churn, and matches the natural layer where the semantic inputs (MSI context, `content_texts`, `content_id`, config) are already in scope. Step 7 may edit `brain/llm/ptcns_backed.py` only because Review Gate A would explicitly authorize that file for implementation.

## Cache Layer Order of Operations

To remove L1/L2 precedence ambiguity, the implementation must follow this order for every `LLMBackedPtCns.eval(content_id)` call once the operator has explicitly selected a model-backed mode:

1. L0 check: if `content_id` is already in `LLMBackedPtCns._cache`, return that value (unchanged from today; covers cogito short-circuit and intra-tick reuse).
2. Build the rendered prompt via `_build_prompt(content_id)` (unchanged; still includes `new_id` per LOCK E).
3. Derive the L2 canonical key tuple from `(cache_schema_version, prompt_template_version, parse_schema_version, backend_family, model_identity, existing_msi_context, new_text)` (LOCK D / canonicalization function below).
4. L2 lookup: if the L2 entry exists and is well-formed, parse its `parsed` field back into `ConsistencyEval`, emit `llm.semantic_cache_hit` with `key_prefix` and `content_id`, store in L0, and return the value without calling the inner client.
5. L2 miss path: emit `llm.semantic_cache_miss`, then call `self._client.eval_consistency(prompt)` exactly as today. If the client is wrapped in `CachedClient` (L1), L1 handles its own hit/miss and emits its existing tracer events; L2 makes no assumption about whether the inner call was satisfied by L1 or by the underlying transport.
6. Parse the returned raw response via `parse_consistency_eval`. On parse failure, follow the existing retry loop unchanged; do not write an L2 entry; emit `llm.semantic_cache_skip` with `reason="parse_failure"` when retries are exhausted.
7. On parse success: write a new L2 entry (subject to capacity check) and emit `llm.semantic_cache_store`. If the L2 cache is at cap, do not write; emit `llm.semantic_cache_skip` with `reason="capacity"`.

Failure paths (provider error, timeout, refusal, schema mismatch, corrupt L2 entry) follow LOCK G / LOCK H and never produce an L2 success hit. Corrupt L2 entries raise a bounded error rather than triggering a silent inner call.

OFFLINE / MOCK never enter steps 3-7; the factory ensures `LLMBackedPtCns` constructed for those modes does not expose an L2 surface at all (see I-LLMCACHE-04).

## Cache Flags vs Mode Selection

Cache flags (`--llm-enable-cache` / `--llm-disable-cache`) modulate cache behavior for an *already-selected* model-backed mode; they do not select a mode and they cannot promote OFFLINE / MOCK into a model-backed mode. Mode selection is and remains exclusively governed by `--llm-mode` / `BRAIN_LLM_MODE` (the existing I-LLMTOG-* family).

## L2 Canonicalization Function

Step 4 LOCK C requires Step 5 to enumerate the canonicalization function. The canonical L2 key is the SHA-256 hex of the deterministic UTF-8 encoding of the following ordered tuple:

```python
(
    cache_schema_version,
    prompt_template_version,
    parse_schema_version,
    backend_family,
    model_identity,
    existing_msi_context,
    new_text,
)
```

Constant values for v1:
- `cache_schema_version = "llm-semantic-cache-v1"`
- `prompt_template_version = "prompt-template-v1"` introduced as a new module-level constant in `brain/llm/prompts.py` at Step 7.
- `parse_schema_version = "consistency-eval-v1"` introduced as a new module-level constant in `brain/llm/parse.py` or `brain/llm/prompts.py` at Step 7.

`backend_family` resolved at L2 construction time:
- `AnthropicAPIClient` -> `"anthropic-api"`
- `ClaudeCLIClient` -> `"claude-cli"`
- `CodexCLIClient` -> `"codex-cli"`
- `MockClient` / `OfflineStandInClient` -> L2 disabled; these never reach the L2 branch because the factory enforces I-LLMCACHE-04.

`model_identity`:
- for `"anthropic-api"`: `config.model`, for example `"claude-sonnet-4-6"`.
- for `"claude-cli"`: tuple `("claude-cli", config.claude_cli_executable)`.
- for `"codex-cli"`: tuple `("codex-cli", config.codex_cli_executable)`.

`existing_msi_context`:
- tuple of `(content_id, text)` pairs for non-cogito MSI contents, sorted by `content_id` ascending.
- `text` is taken from `content_texts`.
- include the existing MSI content IDs, not the evaluated `new_id`, so two semantically distinct MSI members with identical text but different IDs do not collide.

Canonical serialization: the seven-tuple above is a Python `tuple` of immutable values where every leaf is either a `str` or a nested `tuple` of `str`. The serialization is `repr(seven_tuple).encode("utf-8")`; the L2 key is `sha256(...).hexdigest()`. Python's `repr()` is deterministic across runs for the closed value space used here (sorted tuples of strings, no `dict` / `set` / floats / `MappingProxyType` / objects with custom `__repr__`). Step 7 fixtures must assert that two calls with identical seven-tuple values produce identical keys, including across process boundaries.

`new_text`:
- exact string from `content_texts[content_id]` for the evaluated `content_id`.

Excluded:
- evaluated `content_id` / `new_id`
- stream chunk ID, candidate ID
- tick index, trace ID, timestamp, Python object ID
- process ID, hostname, environment variables
- retry attempt number, which remains outside the success key as retry metadata

## new_id Exclusion Evidence Plan

Step 4 LOCK E requires repo-local evidence that excluding `new_id` from the L2 key cannot change semantic result selection, provenance, or replay expectations for the v1 prompt template. Step 7 fixtures must prove:

- Same existing MSI context + same `new_text` + different `new_id` maps to the same L2 key.
- The returned result is a parsed `ConsistencyEval` only; its value is independent of `new_id` at the v1 prompt template contract.
- Provenance / trace records (`llm.request`, `llm.response`, `llm.semantic_cache_hit`, `llm.semantic_cache_miss`) still include the actual `new_id` as event metadata, not as part of cache key identity.
- The rendered prompt sent on the first miss still includes the actual `new_id`.
- A second call with a different `new_id` can hit L2 and the trace records the actual `new_id` and a key prefix only.
- No source writes the old `new_id` as the new event's content ID.

Wording bound: claim only that for the v1 prompt template contract, result selection is intended to be over `existing_msi_context + new_text`, while `new_id` is diagnostic / provenance. Do not claim that `new_id` is universally non-semantic across all possible future prompt templates.

## L1 Default Cache Policy

Plan implementation surface: `brain/ui/llm_runtime.py`.

- Add CLI flag `--llm-disable-cache` parsing alongside the existing `--llm-enable-cache`.
- Add a config field `disable_cache: bool = False` on `LlmRuntimeConfig` or equivalent.
- For model-backed modes (`anthropic-api`, `claude-cli`, `codex-cli`), L1 cache is on by default unless `disable_cache` is true. Implementation: `build_llm_client_from_config` wraps the backend in `CachedClient` unless `config.disable_cache`.
- `--llm-enable-cache` remains accepted and compatible; for model-backed modes it is an explicit affirmation that does not change the new default.
- If both `--llm-enable-cache` and `--llm-disable-cache` are supplied, raise `LlmRuntimeError` with a bounded message naming both flags.
- For OFFLINE / MOCK: `--llm-enable-cache` continues to raise `LlmRuntimeError` under existing I-LLMTOG-08 behavior. `--llm-disable-cache` is accepted as a no-op for OFFLINE / MOCK so scripts can pass the flag uniformly. The flag does not unlock cache access; OFFLINE / MOCK never read or write cache files regardless of the flag.

## L2 Storage / Bound Policy

- L2 cache directory: `brain/.llm_cache/eval_v1/`, a subdirectory under the existing `brain/.llm_cache` gitignored root. Step 7 must verify `.gitignore` covers this path.
- Entry format is a bounded JSON schema with exactly the keys `key_prefix` and `parsed`.
- `key_prefix`: 8-char hex prefix of the full L2 key.
- `parsed`: string `ConsistencyEval` name.
- `created_at` is omitted in v1 to keep entries deterministic.
- Raw response is not persisted in L2 entries to reduce sensitivity. L1 may persist raw responses under its own `brain/.llm_cache/<sha256>.json` files.
- Cap: max 1024 entries (`PHASE3_14_L2_CACHE_MAX_ENTRIES = 1024`).
- At cap behavior: hits still read; misses may call the inner path in explicit model-backed mode but do not write a new entry. Emit `llm.semantic_cache_skip` or `llm.semantic_cache_write_skipped` with `reason="capacity"`.
- No hidden model call is made solely to repair capacity.
- No eviction / pruning in v1; defer LRU / TTL to a follow-up.

## L1 Bound Policy

L1 bounding is DEFERRED in Phase 3.14.

Rationale:
- L1 is pre-existing behavior.
- Bounding it safely requires migration and eviction policy.
- Step 3 measurements did not flag L1 unbounded growth as the primary spam cause.
- The v1 priority is bounded L2.
- Phase 3.14 introduces no new L1 cache surface; flipping `enable_cache=True` by default for model-backed modes activates the *existing* `CachedClient` already shipped in v0.16. Therefore "no unbounded new cache" (a Phase 3.14 guardrail) is satisfied: the only new persistent cache surface is L2, which is bounded by I-LLMCACHE-11.

Phase 3.14 documents L1 as a sensitive local artifact under LOCK L and marks I-LLMCACHE-20 DEFERRED. A future campaign may add explicit L1 bounding.

## Version Bump Rules

The three version constants (`cache_schema_version`, `prompt_template_version`, `parse_schema_version`) have the following bump rules. The rules bind any future campaign that edits `brain/llm/prompts.py`, `brain/llm/parse.py`, or the L2 entry format:

- Any change to `PROMPT_TEMPLATE` (body or interpolated fields) requires bumping `prompt_template_version` (e.g. `"prompt-template-v1"` → `"prompt-template-v2"`). Old L2 entries become unreachable rather than ambiguous, because the new key namespace differs.
- Any change to `parse_consistency_eval` grammar, the `ConsistencyEval` enum membership, or the parse-failure classification requires bumping `parse_schema_version`.
- Any change to the L2 entry JSON schema (e.g. adding a field, changing `parsed` representation) requires bumping `cache_schema_version`.
- Any change to the L2 canonicalization function (field order, encoding, included / excluded fields) requires bumping `cache_schema_version`.
- A version bump invalidates older L2 entries by key namespace separation; the implementation must not migrate, rewrite, or silently consume entries that match only the old namespace.

Step 7 must encode these rules as comments next to each constant; Step 5 / 6 reserves the right to make these rules invariant rows in a follow-up if drift is observed.

## L2 Entry Payload Discipline

To prevent raw prompt or raw response text from leaking into committed artifacts via L2 cache files, the implementation must enforce:

- An L2 entry JSON object has exactly two keys: `key_prefix` (8-char hex) and `parsed` (a string from the `ConsistencyEval` enum's `.name` value: `"PRESERVE"`, `"DAMAGE"`, or `"NEUTRAL"`).
- No raw prompt text, no raw model response text, no error message body, no provider metadata (HTTP headers, request IDs, timing), no key beyond the 8-char prefix, and no other field appears in the on-disk entry.
- The L2 file name is derived from the full SHA-256 hex key (e.g. `<hex>.json`); the 64-char file name is the only place the full key is materialized.
- Step 7's `llm_cache_bounds_artifacts.py` fixture writes a sample L2 entry, parses it back, and asserts that the JSON keys are exactly `{"key_prefix", "parsed"}`.
- The static AST audit in `llm_cache_static_audit.py` rejects any module that writes a JSON dict containing `"prompt"`, `"response"`, `"raw"`, `"error"`, `"trace"`, or `"headers"` into a path under `brain/.llm_cache/eval_v1/`.

This discipline is covered by the I-LLMCACHE-09 (only parse-success entries), I-LLMCACHE-12 (sensitive artifact), and I-LLMCACHE-17 (static audit) rows; no new catalog row is added.

## Corrupt Cache Policy

- L1: existing `CachedClient` already raises `RuntimeError` on corrupt entries; preserve.
- L2: fail loud on corrupt entry, including truncated JSON, schema mismatch, digest mismatch, and partial write. The error must be bounded and must not include raw prompt or raw response text.
- No silent refresh.
- No hidden model call to repair corrupt cache.
- A later campaign may add explicit repair / quarantine behavior.

## Parse Failure / Retry Policy

- L2 only stores parse-success entries.
- L2 miss calls the underlying normal evaluation path, which may itself hit L1 for the rendered prompt.
- If the underlying path raises parse failure after exhausting retries, no L2 entry is written. Emit `llm.semantic_cache_skip` or `llm.semantic_cache_write_skipped` with `reason="parse_failure"` and no raw response.
- L1 may still cache raw bad responses under its own prompt hash; this is documented but not changed in v1.
- Failure classes are kept distinct and never collapse into one L2 cache state: parse failure, provider failure, timeout, refusal / empty, schema mismatch, and corrupt entry.

## Observability Plan

L1 existing tracer events preserved:
- `llm.cache_hit`
- `llm.cache_miss`

L2 new tracer events:
- `llm.semantic_cache_hit`
- `llm.semantic_cache_miss`
- `llm.semantic_cache_store`
- `llm.semantic_cache_skip`

`llm.semantic_cache_skip` carries `reason`, for example `"parse_failure"`, `"capacity"`, `"disabled"`, or `"offline_or_mock"`.

Payload rules:
- `key_prefix` only, 8 hex chars; no full key if the full key could reveal text.
- `reason` field as bounded enum-like string where applicable.
- `content_id` is allowed in trace payload because `llm.request` / `llm.response` already use it; it is not part of the cache key under LOCK E.
- No raw prompt, raw response, or secret.

## Proposed Row Family

Use row family `I-LLMCACHE-01` through `I-LLMCACHE-22` with these statuses:

| Row | Status | Requirement |
| --- | --- | --- |
| I-LLMCACHE-01 | REQUIRED | L0 remains per-instance/per-tick and `brain/tick.py` remains unchanged. |
| I-LLMCACHE-02 | REQUIRED | Model-backed modes enable L1 transport cache by default after explicit model-backed opt-in; offline remains default. |
| I-LLMCACHE-03 | REQUIRED | `--llm-disable-cache` disables cache for model-backed modes; `--llm-enable-cache` remains compatible affirmation; conflicting flags raise `LlmRuntimeError`. |
| I-LLMCACHE-04 | REQUIRED | OFFLINE / MOCK never read or write L1 / L2 cache files; `--llm-enable-cache` rejects; `--llm-disable-cache` is accepted as a no-op without unlocking cache access. |
| I-LLMCACHE-05 | REQUIRED | L1 `CachedClient` semantics remain prompt-hash transport cache with hit/no-inner-call and miss/inner-call. |
| I-LLMCACHE-06 | REQUIRED | L2 canonical evaluation cache is keyed by the locked semantic payload and excludes the evaluated `new_id`. |
| I-LLMCACHE-07 | REQUIRED | L2 key namespace includes `cache_schema_version`, `prompt_template_version`, `parse_schema_version`, `backend_family`, `model_identity`. |
| I-LLMCACHE-08 | REQUIRED | L2 canonicalization preserves legitimate existing MSI context differences and reuses same-`new_text`/different-`new_id` under the same context. |
| I-LLMCACHE-09 | REQUIRED | L2 stores only parse-success entries; parse failures, provider failures, timeouts, refusals, schema mismatches, and corrupt entries do not become success hits. |
| I-LLMCACHE-10 | REQUIRED | Corrupt L1 / L2 cache entries fail loud with bounded error and do not silently call inner client. |
| I-LLMCACHE-11 | REQUIRED | L2 cache growth is bounded: max 1024 entries; at cap, hits still read, misses may call explicit model-backed inner path but do not write new entries; emit `llm.semantic_cache_skip` with `reason="capacity"`. |
| I-LLMCACHE-12 | REQUIRED | L1 / L2 cache files are sensitive local artifacts; gitignored; no raw prompt / response appears in committed docs / fixtures / test outputs. |
| I-LLMCACHE-13 | REQUIRED | L1 / L2 observability emits bounded tracer events for disabled / miss / hit / bypass / invalid / corrupt / write_skipped / write_success without raw prompt / response / secret / full key. |
| I-LLMCACHE-14 | REQUIRED | Cache hit path does not call inner client; cache miss path calls inner only when explicit model-backed mode is selected. |
| I-LLMCACHE-15 | REQUIRED | Different semantic contexts evaluate separately; no false hit across different existing MSI contexts, prompt_template_version, parse_schema_version, backend_family, or model_identity. |
| I-LLMCACHE-16 | REQUIRED | No `brain/tick.py` semantic change; cached and uncached evaluation preserve same `(new_state, TickRecord)` for the same client responses. |
| I-LLMCACHE-17 | REQUIRED | Static AST audit rejects hidden model-call, network, subprocess, filesystem mutation, raw prompt leakage, and disallowed imports in the new cache module(s). |
| I-LLMCACHE-18 | REQUIRED | No cognitive / claim-boundary drift: "semantic cache key" is engineering cache identity only, not ToyI understanding / meaning / truth. |
| I-LLMCACHE-19 | STRUCTURAL | Cache dependency direction is one-way; no `brain.ui` imports inside `brain.llm` modules. |
| I-LLMCACHE-20 | DEFERRED | L1 cache bounding / eviction policy remains deferred; documented as a future-campaign follow-up. |
| I-LLMCACHE-21 | NOT-EXERCISED | Real external model-backed ORS smoke with cache enabled remains optional / manual unless explicitly authorized. |
| I-LLMCACHE-22 | NOT-EXERCISED | End-to-end Phase 3.14 behavior probe placeholder; Step 8 produces a behavior report rather than an executed runner check. |

Status summary:
- REQUIRED: 18 (I-LLMCACHE-01 through I-LLMCACHE-18)
- STRUCTURAL: 1 (I-LLMCACHE-19)
- DEFERRED: 1 (I-LLMCACHE-20)
- NOT-EXERCISED: 2 (I-LLMCACHE-21, I-LLMCACHE-22)
- OBSERVED: 0

## v0.23 -> v0.24 Count Delta

Apply the row family above to the existing v0.23 totals:

- REQUIRED: 259 -> 277 (+18)
- STRUCTURAL: 86 -> 87 (+1)
- NOT-EXERCISED: 12 -> 14 (+2)
- DEFERRED: 15 -> 16 (+1)
- OBSERVED: 16 -> 16 (unchanged)

Total rows: 388 -> 410.

Step 7 must update:
- `tools/catalog.py` `EXPECTED_COUNTS` dict.
- `INVARIANT_CATALOG.md` banner block and per-row entries.
- `brain/_catalog_ids.py` regenerated via `python3 -m tools.catalog generate-ids`.
- `README.md` "Catalog version" string.
- `CURRENT_MISSION.md` baseline counts.
- `CURRENT_CAMPAIGN.md` baseline counts.

## Proposed Implementation Files

Authorized for Step 7 if accepted at Review Gate A:

- `brain/llm/client.py` - preserve `CachedClient`; no semantic-cache shape change at the client layer.
- `brain/llm/ptcns_backed.py` - implement L2 inside `LLMBackedPtCns` (Option 3); add L2 storage helper if needed.
- `brain/llm/prompts.py` - add `PROMPT_TEMPLATE_VERSION = "prompt-template-v1"` constant; no template body changes.
- `brain/llm/parse.py` - add `PARSE_SCHEMA_VERSION = "consistency-eval-v1"` constant; no parser logic changes.
- `brain/ui/llm_runtime.py` - add `--llm-disable-cache` flag and `disable_cache` config field; flip default to on for model-backed modes; raise on conflicting flags.
- `brain/ui/fixtures/llm_cache_runtime_policy.py` - new fixture.
- `brain/ui/fixtures/llm_cache_transport.py` - new fixture.
- `brain/ui/fixtures/llm_cache_semantic_key.py` - new fixture.
- `brain/ui/fixtures/llm_cache_parse_failure.py` - new fixture.
- `brain/ui/fixtures/llm_cache_bounds_artifacts.py` - new fixture.
- `brain/ui/fixtures/llm_cache_observability.py` - new fixture.
- `brain/ui/fixtures/llm_cache_no_tick_change.py` - new fixture.
- `brain/ui/fixtures/llm_cache_static_audit.py` - new fixture.
- `brain/invariants.py` - extend `FIXTURE_MODULES` with the eight new fixture modules.
- `tools/catalog.py` - bump `EXPECTED_COUNTS` to `{REQUIRED: 277, STRUCTURAL: 87, NOT-EXERCISED: 14, DEFERRED: 16, OBSERVED: 16}`.
- `INVARIANT_CATALOG.md` - new banner v0.24 plus the I-LLMCACHE-01..22 row block.
- `brain/_catalog_ids.py` - regenerated.
- `README.md` - catalog version + counts string.
- `CURRENT_MISSION.md` - catalog version + counts string.
- `CURRENT_CAMPAIGN.md` - catalog version + counts string.
- `.gitignore` - verify `brain/.llm_cache/**` covers the new `eval_v1/` subdirectory.

Explicitly excluded unless Review Gate A amends:
- `brain/tick.py`
- `brain/development/growth_ledger.py`
- `brain/development/pattern_ledger.py`
- `brain/development/coherence_monitor.py`
- `brain/ui/session.py` unless runtime config plumbing proves needed and Step 6 authorizes it.
- persistence / autosave runtime files
- DB schema / `SCHEMA_VERSION`
- `scenarios/**`
- `traces/**`
- `lean_reference/**`
- `.claude/**`

## Proposed Fixture Plan

Row-to-fixture mapping:

1. `brain/ui/fixtures/llm_cache_runtime_policy.py` covers I-LLMCACHE-02, I-LLMCACHE-03, I-LLMCACHE-04.
2. `brain/ui/fixtures/llm_cache_transport.py` covers I-LLMCACHE-05, I-LLMCACHE-10 L1 corrupt path, I-LLMCACHE-14 L1 hit/miss inner-call discipline.
3. `brain/ui/fixtures/llm_cache_semantic_key.py` covers I-LLMCACHE-06, I-LLMCACHE-07, I-LLMCACHE-08, I-LLMCACHE-15.
4. `brain/ui/fixtures/llm_cache_parse_failure.py` covers I-LLMCACHE-09 and the L2 corrupt path of I-LLMCACHE-10.
5. `brain/ui/fixtures/llm_cache_bounds_artifacts.py` covers I-LLMCACHE-11, I-LLMCACHE-12.
6. `brain/ui/fixtures/llm_cache_observability.py` covers I-LLMCACHE-13.
7. `brain/ui/fixtures/llm_cache_no_tick_change.py` covers I-LLMCACHE-01, I-LLMCACHE-16.
8. `brain/ui/fixtures/llm_cache_static_audit.py` covers I-LLMCACHE-17, I-LLMCACHE-18, I-LLMCACHE-19.

Deferred / placeholder rows:
- I-LLMCACHE-20: no fixture (DEFERRED).
- I-LLMCACHE-21: no fixture (NOT-EXERCISED real-LLM smoke).
- I-LLMCACHE-22: no fixture (NOT-EXERCISED; Step 8 behavior report).

## Stage B Usage Plan for Step 7

Because Step 7 is cross-file and coupled, Stage B is allowed only for bounded single-file shards after Step 6 acceptance.

Recommended Stage B shards, one allowed file per call:

1. Fixture shard: one fixture file per Stage B call.
2. Runtime shard A: `brain/llm/ptcns_backed.py` only.
3. Runtime shard B: `brain/llm/client.py` only, if a touch is needed beyond preserving `CachedClient`; likely no-op or minor.
4. Runtime config shard: `brain/ui/llm_runtime.py` only.
5. Catalog / version shard: parent Claude writes `INVARIANT_CATALOG.md`, `tools/catalog.py`, `README.md`, `CURRENT_MISSION.md`, and `CURRENT_CAMPAIGN.md` directly. Stage B may be used for `INVARIANT_CATALOG.md` single-file draft if exact row text is supplied.

Hard rules:
- No more than 3 real Stage B calls in Step 7 without fresh operator approval.
- Parent Claude validates, stages, commits, and pushes.
- Stage B never edits `brain/tick.py`.

## Risks and Mitigations

- Hidden model calls: prevented by LOCK P + I-LLMCACHE-14 fixture; static audit (I-LLMCACHE-17) rejects new network / subprocess calls in cache modules.
- Accidental model-backed default: prevented by LOCK B / LOCK O; offline remains default; only explicit `--llm-mode` flips to model-backed.
- Cache poisoning through parse failure: prevented by LOCK H + I-LLMCACHE-09 fixture.
- Prompt / raw response leakage: prevented by LOCK L + I-LLMCACHE-12 + I-LLMCACHE-13 fixtures + Step 5/7 gitignore check.
- Unbounded cache growth: prevented by LOCK I + I-LLMCACHE-11 fixture for L2; L1 bounding tracked as DEFERRED under I-LLMCACHE-20.
- Stale cache across model / template / parser versions: prevented by LOCK M + I-LLMCACHE-07 + I-LLMCACHE-15 fixtures.
- False semantic cache hits if key too coarse: mitigated by including existing MSI context in the L2 key, including existing MSI content IDs + texts.
- Cache miss if key too fine: mitigated by excluding evaluated `new_id` from key under LOCK E; proof obligation discharged by I-LLMCACHE-08.
- Tick semantic drift: prevented by LOCK N + I-LLMCACHE-01 + I-LLMCACHE-16 fixtures.
- Fixture overreach: prevented by per-fixture row mapping above; static audit rejects out-of-scope imports.
- Stage B out-of-scope edits: prevented by exact `--allowed-file` lists and parent Claude inspection per LOCK Q.

## Review Gate A Decision Request

Step 5 stops here. Step 6 Review Gate A must choose one:

- [ ] ACCEPT PLAN AS WRITTEN
- [ ] ACCEPT WITH AMENDMENTS (operator lists the amendments)
- [ ] REJECT / REVISE (no implementation; return to Step 5)

No implementation is authorized before Step 6 acceptance.

## Stage A and Stage B Disclosure

Stage B disclosure:
Stage B drafted this catalog patch plan as an exact allowed-file shard (`/ask-chatgpt-write --mode write --model gpt-5.5 --effort high --allowed-file docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_CATALOG_PATCH_PLAN.md --apply`). Wrapper exit 0, `out_of_scope_paths` empty, `changed_paths` exactly the allowed file.

Stage A disclosure:
Stage A reviewed the draft at high effort for row-family and implementation-surface risks before Review Gate A (`/ask-chatgpt --mode review --model gpt-5.5 --effort high`). Confidence: medium. Disagreement: substantive. Accepted advice incorporated into this plan:
- Added the "Cache Layer Order of Operations" section enumerating the L0 → L2 lookup → L2 miss → inner client → parse → L2 write sequence so L1/L2 precedence and failure paths are no longer ambiguous.
- Added the "Cache Flags vs Mode Selection" section asserting that `--llm-enable-cache` / `--llm-disable-cache` cannot promote OFFLINE / MOCK into a model-backed mode; mode selection remains exclusively governed by `--llm-mode` / `BRAIN_LLM_MODE` (existing I-LLMTOG-* family).
- Sharpened the canonical serialization wording: the seven-tuple is restricted to immutable `str` / nested `tuple[str]` leaves so Python `repr()` is deterministic across processes; Step 7 fixtures must assert cross-process key equality.
- Added the "Version Bump Rules" section codifying when each of `cache_schema_version`, `prompt_template_version`, and `parse_schema_version` must be bumped, and that bumping invalidates old L2 entries by namespace separation (no migration / silent reuse).
- Added the "L2 Entry Payload Discipline" section enumerating the exact JSON key set (`{"key_prefix", "parsed"}` only) and listing the field names that the static audit must reject from any module writing under `brain/.llm_cache/eval_v1/`. No new catalog row is needed; this is covered by I-LLMCACHE-09 / I-LLMCACHE-12 / I-LLMCACHE-17.
- Extended the L1 Bound Policy rationale to make explicit that Phase 3.14 introduces no new L1 cache surface — flipping `enable_cache=True` by default activates the existing v0.16 `CachedClient` — so the "no unbounded new cache" Phase 3.14 guardrail is satisfied even with L1 bounding deferred.

Rejected advice (deferred or already addressed):
- Did not expand the row family beyond I-LLMCACHE-01..22 to add a "no raw response persistence" row: the new "L2 Entry Payload Discipline" section maps the discipline onto existing rows I-LLMCACHE-09 / I-LLMCACHE-12 / I-LLMCACHE-17 with explicit fixture and static-audit coverage. Expanding the row count would have required a corresponding fixture without strengthening the invariant.
- Did not change the count of REQUIRED rows on the suspicion that 18 may be too many; every REQUIRED row in I-LLMCACHE-01..18 is mapped to a fixture or static audit in the Fixture Plan section, so the catalog-debt concern is preempted.
- Did not add a separate "executable fixture availability" gate row for I-LLMCACHE-21 / I-LLMCACHE-22: these are NOT-EXERCISED by design and the runner already excludes NOT-EXERCISED rows from gates.

Parent Claude owns inspection, acceptance, revision, validation, staging, commit, and push.
