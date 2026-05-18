# Phase 3.15 L1 Cache Hygiene Behavior Report

## Purpose

Step 8 re-runs the Step 3 probe measurements against the
post-implementation runtime and verifies, point by point, that the
LOCKed policy is faithfully implemented in
`brain/llm/client.py::CachedClient`. No real external LLM calls; no
raw cache contents. The harness lives at
`/tmp/phase3_15_probe_post.py` and is not committed.

## Reproduction

```
python3 /tmp/phase3_15_probe_post.py > /tmp/phase3_15_probe_post_results.json
```

Exit code `0`. Raw JSON is at
`/tmp/phase3_15_probe_post_results.json`.

## Verification matrix

Each row names the LOCK from
`PHASE3_15_L1_CACHE_HYGIENE_CORRIGENDA.md` it verifies.

| LOCK | Behavior under test                                              | Implementation observation                                                                                                            |
| ---- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| A    | `L1_CACHE_MAX_ENTRIES` constant value                            | `1024` (matches LOCK A).                                                                                                              |
| A    | Below-cap miss / hit semantics preserved                         | Two unique prompts produced `miss_count=2`, the repeat of the first produced `hit_count=1`; `skip_count=0`; only `llm.cache_hit` and `llm.cache_miss` fired. Cache directory had `2` files. |
| A    | At-cap miss: cache write is skipped                              | `files_after_at_cap_miss == 1024` (no growth past cap).                                                                              |
| A    | At-cap miss: existing entries unchanged                          | `all_original_entries_present == true` over the full pre-fill set.                                                                  |
| B    | At-cap miss: inner is still called                               | With the cache directory pre-filled to `L1_CACHE_MAX_ENTRIES`, `inner.calls` grew from 0 to 1 on a new miss; the response was returned to the caller unchanged. |
| B    | At-cap miss: response is returned unchanged                      | `response_returned == "PRESERVE"` (matches the inner stub).                                                                          |
| B    | At-cap repeat: deterministic behavior                            | Five consecutive at-cap misses produced `skip_count=5`, `inner_calls=5`, `skip_event_count=5`, and `files_after == 1024` (still no growth past cap). |
| C    | Below-cap: no `llm.cache_skip` emission (no bad-response policy change) | `skip_count=0`; tracer's `event_counts` contains only `llm.cache_hit` and `llm.cache_miss`. Raw bad-response replay behavior is unchanged from Phase 3.14 (Option E remains deferred, recorded in Step 9). |
| D    | Cache directory layout unchanged; `eval_v1/` ignored by L1 cap   | `_at_capacity` counts only top-level `*.json` files; `eval_v1/` is a directory and does not match the glob. L1 dir is `brain/.llm_cache`. |
| D    | Corrupt entries still fail loud                                  | Tampering a cache file's JSON caused `RuntimeError` on the next read; `inner.calls` remained `0` (no silent fall-back).               |
| E    | At-cap miss: `skip_count` increments                             | `skip_count == 1` after the single at-cap miss.                                                                                      |
| E    | At-cap miss: `llm.cache_skip` emitted with the LOCKed payload    | One `llm.cache_skip` event with payload keys exactly `["cache_key_prefix", "reason"]` and `reason == "capacity"`.                    |
| E    | L1 hits do not call the inner client (existing observability)    | After one miss the inner was called once; the subsequent hit did not increment `inner_calls`.                                        |
| F    | Phase 3.14 flag contract preserved (no new CLI flags)            | ANTHROPIC_API defaults `enable_cache=True`; `--llm-disable-cache` wins (returns `False`); supplying both flags raises `LlmRuntimeError`. |
| G    | L2 (`eval_v1`) semantics unchanged                               | `SEMANTIC_CACHE_MAX_ENTRIES=1024`, `SEMANTIC_CACHE_DIR=brain/.llm_cache/eval_v1`, `SEMANTIC_CACHE_SCHEMA_VERSION="llm-semantic-cache-v1"` — same as Phase 3.14. |
| H    | OFFLINE / MOCK isolation preserved                               | MOCK with `--llm-mock-response` returned a non-`CachedClient`; `config.enable_cache=False`. The factory boundary is unchanged.        |
| I    | No silent repair / no hidden inner call                          | Every inner call is observable as a miss or as a skip-with-`reason="capacity"`; corrupt entries do not silently fall back to inner. |
| J    | Trace payload bound (no raw prompt / response / secret leakage)  | The new event's payload is exactly `{cache_key_prefix, reason}`. The static AST audit (`I-LLMCACHE-26`) enforces this at build time. This document also contains no raw prompt, no raw response, no cache contents, and no credentials. |
| K    | Stage C implementation policy followed                           | Step 7 was implemented by parent Claude directly (Stage C budget conserved after two Step 2 transport failures). Parent Claude owns catalog and counter reconciliation. |
| L    | No tick semantic change                                          | `brain/tick.py` was not edited in Step 7. The implementation surface is entirely inside `CachedClient`; tick still constructs a fresh `LLMBackedPtCns` per call with unchanged kernel behavior. |
| L    | No mutation of BrainState / MSI / PtCns / ledgers                | The Step 7 diff touches no kernel record, no MSI, no PtCns, and no Growth / Pattern / Coherence module. The runner reports `gate failures: 0` across all 281 REQUIRED rows. |

## Anti-growth test

The `at_cap_repeat` measurement exercised the cache directly to
verify the bound holds under repeated at-cap pressure: pre-fill to
cap, then issue five additional misses. The expected outcome is:

- 5 inner calls (each miss still calls inner);
- 5 `skip_count` increments;
- 5 `llm.cache_skip` events;
- the directory still contains exactly `L1_CACHE_MAX_ENTRIES` files
  (no growth past cap).

Observed: all five hold.

## No-mutation verification

Step 7's diff is bounded to:

- `brain/llm/client.py` (new constant, new counter, new cap-check
  branch, new event emission);
- `brain/ui/fixtures/llm_cache_l1_capacity.py` (new fixture);
- `brain/ui/fixtures/llm_cache_static_audit.py` (added the
  `I-LLMCACHE-26` check function);
- `brain/invariants.py` (added the new fixture module to
  `FIXTURE_MODULES`);
- `tools/catalog.py` (`EXPECTED_COUNTS` v0.25 + inline comment);
- `INVARIANT_CATALOG.md` (banner + `I-LLMCACHE-20` rewrite +
  `I-LLMCACHE-23..26` rows + summary block);
- `brain/_catalog_ids.py` (regenerated);
- `README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md` (version
  + counts stamps).

No file under `brain/tlica/`, `brain/development/`, `brain/ui/session.py`,
`brain/tick.py`, persistence / autosave modules, scenarios, traces, or
`lean_reference/` was modified.

Verified by direct git inspection of the Step 7 commit:

```
git diff --stat 7259535^..7259535 -- brain/tlica/ brain/development/ \
    brain/ui/session.py brain/tick.py
(empty output — no protected path changed)
```

`(new_state, TickRecord)` parity is preserved trivially: the cache
write decision occurs strictly after the inner client call and is
invisible to callers; the inner client's return value is returned
verbatim either way.

### Non-claim / sensitive-artifact sweep (LOCK J)

This document contains no raw prompt, no raw model response, no
secrets, and no cache file contents. Trace payloads emitted by the
new code path contain only `cache_key_prefix` (8 hex characters
derived from the SHA-256 digest of the prompt) and `reason` (the
closed string `"capacity"`). `brain/.llm_cache/` remains gitignored.

## Validation gates

After Step 7, the canonical gates produce:

```
python3 -m tools.catalog counts
Category            Banner    Actual  Expected
REQUIRED               281       281       281  ok
STRUCTURAL              88        88        88  ok
NOT-EXERCISED           14        14        14  ok
DEFERRED                15        15        15  ok
OBSERVED                16        16        16  ok

python3 -m tools.citations verify
Verified 100 citations.

python3 -m tools.import_audit
I-PCE-05: agency.py is clean of pce imports.

python3 -m brain.invariants run
377 rows checked  ·  REQUIRED green: 282 ·  REQUIRED red: 0  ·  STRUCTURAL green: 88 ·  STRUCTURAL red: 0  ·  OBSERVED: 7 pass / 0 fail  ·  gate failures: 0

bash tools/check_all.sh
All checks passed.
```

(`REQUIRED green: 282` exceeds the catalog's 281 by one because the
runner counts the `_meta` row for `I-CAT-01` as a passing REQUIRED
check, matching the same pattern observed in the Phase 3.14
behavior report.)

## Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: yes
- mode: review
- model: gpt-5.5
- effort: high
- wrapper command:
  `python3 tools/claude_helpers/codex_chatgpt_subagent.py --mode review --model gpt-5.5 --effort high --timeout 600 --prompt-file /tmp/toyi_phase3_15_step8_review_question.md`
- question file: `/tmp/toyi_phase3_15_step8_review_question.md`
- answer file: `/tmp/toyi_phase3_15_step8_review_answer.md`
- wrapper status: `exit_code=0`, `error_class=None`
- overall verdict: APPROVE WITH MINOR EDITS (no blockers)
- accepted advice:
  - explicitly enumerate LOCK A through LOCK L in the verification
    matrix (each row now names its LOCK)
  - add a short no-mutation evidence sentence with the actual git
    diff command (added)
  - strengthen LOCK J wording to cover both trace payloads and
    report / docs text (added)
- rejected advice: none
- reason: behavior report adversarial review required by
  `CURRENT_CAMPAIGN.md`

Stage B limited-write collaboration:
- used: no
- reason: parent Claude wrote the report directly over the
  measurement JSON.

Stage C orchestration:
- used: no
- reason: behavior report is a single doc whose inputs (the probe
  JSON and the LOCKed catalog patch) are already in context.
  Remaining Stage C budget is reserved for emergencies.

## Next artifact

Step 9 produces
`docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_FINDINGS.md`.
