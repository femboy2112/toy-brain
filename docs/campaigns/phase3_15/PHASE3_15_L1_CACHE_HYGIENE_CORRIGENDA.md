# Phase 3.15 L1 Cache Hygiene Corrigenda

## Purpose

Step 4 locks every open design decision required before Step 5
catalog planning and Review Gate A. Each LOCK statement is binding
unless explicitly amended by Review Gate A. The Step 2 synthesis
recommendations and Step 3 probe measurements feed these LOCKs.

## LOCK A — v1 hygiene policy subset

Phase 3.15 v1 implements **Option A only**: a deterministic maximum
entry-count bound on the L1 transport cache.

- Constant name: `L1_CACHE_MAX_ENTRIES`.
- Constant value: `1024`. Chosen by symmetry with
  `SEMANTIC_CACHE_MAX_ENTRIES = 1024` and acknowledged in Step 3 as
  a count-cap rather than byte-cap; the byte cap (Option B) and TTL
  (Option C) remain explicit future-campaign concerns.
- Location: defined as a module-level constant in
  `brain/llm/client.py` and consumed by `CachedClient`.
- Options B (byte cap), C (TTL), E (parse-failure-aware bypass), and
  F (manual inspect/clear helpers) are **deferred** and recorded as
  future-campaign concerns in Step 9.
- Option D (observability) is partially adopted via LOCK E below.

## LOCK B — selection rule

Phase 3.15 adopts **write-skip-at-cap**, a bounded admission policy
rather than an eviction policy.

- At cap, a new miss does **not** write a new entry to disk.
- Existing entries are **never** removed or evicted by the cache
  itself.
- In explicit model-backed mode, the inner client is still called on
  a miss at cap; the response is still returned to the caller; only
  the cache write is skipped.
- Counter `skip_count` is incremented on every at-cap skip.
- The cap is checked at write time. The check is based on the count
  of `*.json` files in the cache directory at the moment of the
  write decision; this is the same surface the Step 3 probe exercised
  in M7.
- Operators retain the ability to manually clear the cache directory
  out-of-band (filesystem `rm`); no in-process clear helper ships in
  v1.

## LOCK C — bad-response replay policy

Phase 3.15 explicitly **preserves** current L1 raw bad-response
replay behavior. The Step 3 M5 probe confirms this is durable today;
Phase 3.15 does not change it.

- Phase 3.15 makes no claim to solve malformed-response cache
  poisoning.
- The Step 9 findings document must record this as a known
  future-campaign concern with an explicit pointer to Option E.
- No silent repair calls; no auto-rewrite of cache contents; no
  parse-classification piggybacked onto cache reads.

## LOCK D — cache directory layout and corruption isolation

Phase 3.15 keeps the L1 cache directory layout unchanged.

- L1 cache directory: `brain/.llm_cache` (canonical name from
  `LLM_RUNTIME_CACHE_DIR`).
- File naming: `{sha256(prompt)}.json`, as today.
- No per-backend segmentation, no namespacing subdirectory, no
  manifest file.
- L2 (`eval_v1`) subdirectory at `brain/.llm_cache/eval_v1`
  remains untouched and unaffected by L1 hygiene.
- Corrupt-entry behavior is preserved unchanged: `RuntimeError`
  raised on read; no silent fall-back to inner client. The new
  bounded-admission logic must not weaken this invariant.
- The cap counting MUST exclude the `eval_v1/` subdirectory if
  present (it is a directory, not a `*.json` file, and the
  `cache_dir.glob("*.json")` pattern already excludes it; this is
  re-asserted as a Step 7 invariant).

## LOCK E — observability events and payload limits

Phase 3.15 adds one new trace event and one new counter.

- New event name: `llm.cache_skip`.
- New event payload fields:
  - `cache_key_prefix` — the first 8 characters of the SHA-256
    digest (same shape as existing hit/miss events).
  - `reason` — bounded string. Phase 3.15 v1 only ever emits
    `reason="capacity"`. A future campaign may add
    `reason="parse_failure"` (Option E) or similar; the
    payload-bound is that `reason` is one of a closed enumeration
    of short identifiers, never raw prompt or response text.
- New counter: `skip_count` exposed as a public `int` attribute on
  `CachedClient`, alongside `hit_count` and `miss_count`.
- Existing events (`llm.cache_hit`, `llm.cache_miss`) and payload
  shape (`cache_key_prefix` only) are unchanged.
- No new event payload field may include the raw prompt, the raw
  response, raw byte counts of disk-content, or any operator
  credential.

## LOCK F — CLI / runtime flags

Phase 3.15 v1 introduces **no new CLI flags**.

- The cap is a module-level constant, not operator-tunable in v1.
  This avoids expanding the operator surface before the policy has
  field experience.
- A future campaign may add `--llm-cache-max-entries` (Option F)
  with appropriate validation; explicitly deferred.
- The existing flag contract is **preserved unchanged**:
  - `--llm-enable-cache` continues to be accepted; ANTHROPIC_API /
    CLAUDE_CLI / CODEX_CLI default `enable_cache=True` per Phase
    3.14.
  - `--llm-disable-cache` continues to win over the default for
    those modes.
  - Supplying both flags continues to raise `LlmRuntimeError` from
    `parse_llm_runtime_args`.
  - OFFLINE / MOCK still reject `--llm-enable-cache` at the
    factory boundary and continue to treat `--llm-disable-cache`
    as a no-op.

## LOCK G — L2 (`eval_v1`) untouched

Phase 3.15 makes **no semantic change** to L2.

- `brain/llm/ptcns_backed.py` is not modified for cache behavior.
- `SEMANTIC_CACHE_MAX_ENTRIES = 1024` remains.
- `SEMANTIC_CACHE_DIR = Path("brain/.llm_cache") / "eval_v1"`
  remains.
- `SEMANTIC_CACHE_SCHEMA_VERSION = "llm-semantic-cache-v1"`
  remains.
- L2 hit / miss / store / skip event names and payload shapes
  remain. The new `llm.cache_skip` event sits at L1 and does not
  shadow the existing L2 `llm.semantic_cache_skip` event.

## LOCK H — OFFLINE / MOCK isolation

Phase 3.15 **preserves** the factory-boundary rejection of caching
for OFFLINE and MOCK.

- `build_llm_client_from_config` continues to reject
  `enable_cache=True` for OFFLINE / MOCK.
- OFFLINE / MOCK never produce a `CachedClient`; therefore they
  never reach L1 hygiene logic.
- Step 3 M8 confirms this is the observed behavior today.

## LOCK I — no hidden model calls / no silent repair

Phase 3.15 must not introduce any new code path that:

- calls the inner client without the new behavior being explicitly
  observable as a miss or as a skip-with-`reason="capacity"`;
- rewrites, repairs, or re-derives an existing cache entry's
  contents based on parser-layer or model-layer knowledge;
- migrates entries between layouts.

Any silent-repair-shaped behavior is rejected at Review Gate A.

## LOCK J — sensitive artifact policy

Phase 3.15 enforces the existing sensitive-artifact policy.

- `brain/.llm_cache/` remains gitignored (already ensured by the
  Phase 3.10 / Phase 3.14 `.gitignore` rule). Step 7 must confirm
  this rule is still in place; no new entry is added.
- No raw prompt, raw response, raw cache contents, or credentials
  may appear in any campaign artifact, fixture, trace payload, or
  commit message.
- Trace event payloads are limited to `cache_key_prefix`, `reason`,
  and bounded counter values.
- Docstrings and comments inside the new code must not contain raw
  prompt or response examples.

## LOCK K — Stage C implementation policy

Phase 3.15 Step 7 may use Stage C orchestration with the following
constraints, in addition to the global Stage C policy:

- Each shard's `allowed_files` set must be disjoint from every other
  same-wave shard's set.
- The implementation code shard (`brain/llm/client.py`) must NOT
  share a wave with any catalog / counter / banner shard. Parent
  Claude owns:
  - `INVARIANT_CATALOG.md`,
  - `tools/catalog.py` `EXPECTED_COUNTS` banner,
  - `brain/_catalog_ids.py` regeneration,
  - `brain/invariants.py` `FIXTURE_MODULES` list,
  - `README.md` catalog version + counts string,
  - `CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` version stamps.
- Codex must not stage, commit, push, restore, rebase, or merge.
- Maximum two real Codex calls in Step 7 unless operator approves
  more.
- No automatic retry beyond the one already operator-authorized at
  Step 2; if a Step 7 shard fails, parent Claude stops and reports.

## LOCK L — non-claim boundary

Phase 3.15 makes none of the following claims and authors no
artifact, code comment, fixture name, trace payload, or doc string
that implies any of them:

- consciousness
- sentience
- subjective experience
- semantic understanding
- truth adjudication from raw text
- agency / intent / will / desire
- self-modification of code, fixtures, the catalog, or the runtime
- aggregate consciousness / sentience / awareness / I-ness / growth
  score
- SelfModel implementation
- Growth Ledger / Pattern Ledger / Coherence Monitor semantic
  change
- model-backed runtime as default
- hidden LLM calls

The L1 cap is an engineering hygiene measure on a disk artifact; it
is not a cognitive claim.

## Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: no
- reason: Step 4 corrigenda is decision recording, not synthesis;
  `CURRENT_CAMPAIGN.md` does not require Stage A review at Step 4.
  The Step 2 Stage A review already informed these LOCKs.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude wrote the corrigenda directly to keep the
  exact LOCK text under direct human-reviewable control.

Stage C orchestration:
- used: no
- reason: corrigenda is decision recording with consequences for
  every later step. Parent Claude wrote it directly to avoid any
  shard-introduced drift in LOCK wording. The remaining Stage C
  budget is reserved for Step 5 (optional) and Step 7
  (implementation).

## Next artifact

Step 5 produces
`docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CATALOG_PATCH_PLAN.md`.
