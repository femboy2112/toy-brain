# Phase 3.15 L1 Cache Hygiene Findings

## Purpose

Step 9 classifies the post-implementation state into three buckets:
**pass evidence** (what works), **deferred follow-ups** (known
limitations that do not block this campaign), and **blockers**
(items that would prevent Step 10 from issuing a PASS verdict).
Phase 3.15 has zero blockers.

## Pass evidence

- `L1_CACHE_MAX_ENTRIES == 1024` (LOCK A).
- The L1 entry count never exceeds the cap under the synthetic
  prompt stream exercised in Step 8.
- Below-cap behavior matches Phase 3.14 exactly: hits read, misses
  call inner once, no `llm.cache_skip` emission.
- At-cap miss: inner is still called; the response is still
  returned; the cache write is skipped; `skip_count` increments;
  `llm.cache_skip` is emitted with payload exactly
  `{cache_key_prefix, reason}` and `reason="capacity"`.
- Existing entries are never removed or rewritten. Bounded
  admission, not eviction.
- Corrupt entries still raise `RuntimeError` on read; the inner
  client is not called as a silent fall-back.
- L2 (`eval_v1`) semantics unchanged
  (`SEMANTIC_CACHE_MAX_ENTRIES=1024`, schema version, directory
  layout, event names all unchanged).
- OFFLINE / MOCK still reject `--llm-enable-cache` at the factory
  boundary; `--llm-disable-cache` is still a no-op for those modes.
- Phase 3.14 flag contract preserved unchanged: model-backed
  default-on; `--llm-disable-cache` wins; conflicting flags raise
  `LlmRuntimeError`.
- `brain/tick.py` not edited. No Growth / Pattern / Coherence
  semantic change. No persistence / autosave change. No
  `SCHEMA_VERSION` bump. No DB schema change. No UI expansion.
- Catalog patch `v0.24 -> v0.25`; counts `281/88/14/15/16` exactly
  as planned. `I-LLMCACHE-20` promoted from DEFERRED to REQUIRED.
  `I-LLMCACHE-23..26` added.
- Static AST audit `I-LLMCACHE-26` rejects new forbidden imports
  and confirms `llm.cache_skip` payload uses only
  `cache_key_prefix` and `reason`.
- All canonical gates green: `tools.catalog counts`,
  `tools.citations verify`, `tools.import_audit`,
  `brain.invariants run`, `tools/check_all.sh`.
- No raw prompt / response / cache files / secrets committed.

## Deferred follow-ups (do not block this campaign)

These items are explicitly out of scope for Phase 3.15. Each is
recorded with a pointer so a future campaign can pick it up
without re-deriving the design.

- **Option B (byte cap).** The Step 3 probe noted that per-entry
  size is bounded only by the model's response length. Production
  prompts (which include MSI context) are larger than the harness
  prompts. A future campaign may add a byte cap; the
  count-cap-only choice was deliberate per Step 2 synthesis and
  Step 4 LOCK A.
- **Option C (TTL).** Time-based eviction was deferred because
  clock injection adds test complexity. A future campaign may add
  TTL alongside the count cap; eviction policy interactions
  must be re-LOCKed.
- **Option E (parse-failure-aware bypass / eviction).** Phase 3.15
  explicitly preserves the existing raw bad-response replay
  behavior. The Step 3 M5 probe and the Step 8 measurement both
  confirm replay is durable today. A future campaign that wants
  to retire this risk should:
  - decide whether parse classification rides alongside the
    cache lookup or whether `CachedClient` exposes an explicit
    invalidation API;
  - LOCK a no-silent-repair policy (no auto-rewrite of cache
    contents);
  - add a row to the I-LLMCACHE-* family covering the new
    behavior and its event surface.
- **Option F (manual `inspect` / `clear` CLI helpers).** No new
  operator surface was added in Phase 3.15. A future campaign
  that wants helpers should bound them by safety prompts /
  dry-run defaults and respect the sensitive-artifact policy
  (no raw prompt / response output).
- **`I-LLMCACHE-21`** (real external model-backed cache smoke)
  remains NOT-EXERCISED. Promotion requires explicit reviewed
  policy, a dedicated catalog row update, and stop conditions
  for failure modes.
- **`I-LLMCACHE-22`** (end-to-end Phase 3.14 behavior probe)
  remains NOT-EXERCISED. Promotion is at the discretion of a
  future campaign.
- **SelfModel implementation** remains deferred (inherited from
  Phase 3.12 Step 15 roadmap).
- **`/pattern-ledger` UI** (`I-PLEDGER-17`),
  **`/coherence-summary` UI** (`I-COHMON-13`),
  **`/growth-ledger` UI** (`I-GROW-21`) remain DEFERRED.
- **End-to-end Pattern Ledger / Coherence Monitor / Growth
  Ledger dry-run helpers** (`I-PLEDGER-18`, `I-COHMON-14`,
  `I-GROW-22`) remain NOT-EXERCISED.

## Operator UX surprises

None substantive. Two minor observations:

- **Cap-count check is filesystem-glob-based.** Each at-cap miss
  performs an `iterdir()` scan of the cache directory short-circuited
  by the cap. For 1024 entries this is fast; for very large operator
  cache directories accumulated before Phase 3.15 (i.e., when an
  operator upgrades) the first cap check may include a one-shot
  larger scan. The check is correct and bounded; the cap will
  short-circuit once the limit is reached. Documenting here so a
  future campaign that adds a byte cap or TTL knows the existing
  check path.
- **No new operator-facing CLI flag was added.** Operators that
  want to control the cap must edit
  `L1_CACHE_MAX_ENTRIES` directly (a module-level constant).
  This is a deliberate Step 4 LOCK F choice; a future campaign
  may add `--llm-cache-max-entries`.

## No-block triage

Phase 3.15 has **no blockers** for Step 10. The final audit may
proceed.

## Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: no
- reason: `CURRENT_CAMPAIGN.md` does not require Stage A review at
  Step 9; the findings are triage of the Step 8 review which
  already had Stage A coverage.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude wrote the findings directly.

Stage C orchestration:
- used: no
- reason: findings are decision recording; remaining Stage C budget
  reserved for emergencies.

## Next artifact

Step 10 produces
`docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_AUDIT.md`.
