# Phase 3.15 L1 Cache Hygiene Catalog Patch Plan

## Purpose

Step 5 specifies the exact catalog patch that implements the LOCKed
Phase 3.15 v1 policy. The plan covers row family, statuses, count
delta, disposition of the inherited rows (`I-LLMCACHE-20/21/22`),
implementation file set, fixture list, Stage C shard plan,
validation, and non-rows. Stop at Review Gate A.

## Row family extension

Phase 3.15 extends the existing `I-LLMCACHE-*` family by adding four
new rows (`I-LLMCACHE-23..26`) and promoting `I-LLMCACHE-20` from
`DEFERRED` to `REQUIRED`. `I-LLMCACHE-21` and `I-LLMCACHE-22` remain
`NOT-EXERCISED`.

### Status assignment

| Row             | Phase 3.14 status | Phase 3.15 status |
| --------------- | ----------------- | ----------------- |
| `I-LLMCACHE-20` | DEFERRED          | REQUIRED          |
| `I-LLMCACHE-21` | NOT-EXERCISED     | NOT-EXERCISED     |
| `I-LLMCACHE-22` | NOT-EXERCISED     | NOT-EXERCISED     |
| `I-LLMCACHE-23` | (new)             | REQUIRED          |
| `I-LLMCACHE-24` | (new)             | REQUIRED          |
| `I-LLMCACHE-25` | (new)             | REQUIRED          |
| `I-LLMCACHE-26` | (new)             | STRUCTURAL        |

### Row propositions

`I-LLMCACHE-20` (promoted to REQUIRED) — L1 cache bounding by
`L1_CACHE_MAX_ENTRIES = 1024` via write-skip-at-cap **admission**
policy. The L1 entry count never exceeds `L1_CACHE_MAX_ENTRIES`; at
cap, `CachedClient` does not write a new entry; existing entries
remain present and readable; hits continue to read. The cache itself
never evicts; only new admissions are skipped.

`I-LLMCACHE-23` (REQUIRED) — At-cap miss behavior. When a miss occurs
with `>= L1_CACHE_MAX_ENTRIES` `*.json` files already present in the
cache directory, the inner client is still called and the response
is still returned to the caller; only the cache write is skipped.

`I-LLMCACHE-24` (REQUIRED) — Observability: at-cap skip emits
`llm.cache_skip` with payload exactly `{"cache_key_prefix", "reason"}`
and `reason="capacity"`. The new `skip_count` counter is exposed as a
public `int` attribute on `CachedClient`, alongside `hit_count` and
`miss_count`. The skip event payload contains no other keys and no
raw prompt or response.

`I-LLMCACHE-25` (REQUIRED) — No silent repair / no weakening of
corrupt-entry fail-loud. The bounded admission policy does not
rewrite or delete existing entries; corrupt entries continue to
raise `RuntimeError` on read; the inner client is not called as a
silent fall-back; the policy does not introduce any code path that
calls inner without the call being observable as a miss or as a
skip-with-`reason="capacity"`.

`I-LLMCACHE-26` (STRUCTURAL) — Static AST audit over the new L1
hygiene code path inside `brain/llm/client.py` rejects new forbidden
imports (`brain.ui`, `brain.tick`, `brain.development`, `subprocess`,
`socket`, `urllib`, `http`, `requests`, `sqlite3`, `shutil`,
`tempfile`, `atexit`, `threading`, `asyncio`, `signal`); rejects
calls to `eval`, `exec`, `compile`, `__import__`; and asserts that
no raw payload-key string (`"prompt"`, `"response"`, `"raw"`,
`"error"`, `"trace"`, `"headers"`) appears as a string literal in
the new code path introduced by Phase 3.15 except where the existing
`CachedClient.eval_consistency` already uses `"prompt"` and
`"response"` (the existing literals are explicitly allowed; only
*new* literals must not be added).

## Catalog version bump

`v0.24 -> v0.25`.

The new banner sentence (drafted for the `INVARIANT_CATALOG.md`
header) reads, approximately:

> **Catalog version:** v0.25. Patches over v0.24 (Phase 3.15 L1
> Cache Hygiene): +4 REQUIRED rows, +1 STRUCTURAL row, -1 DEFERRED
> row, OBSERVED unchanged, NOT-EXERCISED unchanged. Promotes
> `I-LLMCACHE-20` from `DEFERRED` to `REQUIRED` by binding a
> deterministic write-skip-at-cap admission policy with
> `L1_CACHE_MAX_ENTRIES = 1024` to the existing `CachedClient` L1
> transport cache; adds `I-LLMCACHE-23..26` for at-cap miss
> behavior, observability (`llm.cache_skip` event with payload
> `{cache_key_prefix, reason="capacity"}` and `skip_count` counter),
> no-silent-repair guarantees, and a static AST audit over the new
> L1 hygiene code. L2 (`eval_v1`) semantics are unchanged. Offline
> remains the default; model-backed modes remain explicit opt-in.
> `brain/tick.py` is not edited. `I-LLMCACHE-21` and
> `I-LLMCACHE-22` remain `NOT-EXERCISED`.

## Count delta

| Category       | v0.24 | delta | v0.25 |
| -------------- | ----- | ----- | ----- |
| REQUIRED       | 277   | +4    | 281   |
| STRUCTURAL     | 87    | +1    | 88    |
| NOT-EXERCISED  | 14    | 0     | 14    |
| DEFERRED       | 16    | -1    | 15    |
| OBSERVED       | 16    | 0     | 16    |

Sources for the delta:

- REQUIRED +4: `I-LLMCACHE-20` promoted (+1), three new REQUIRED rows
  `I-LLMCACHE-23`, `I-LLMCACHE-24`, `I-LLMCACHE-25` (+3).
- STRUCTURAL +1: `I-LLMCACHE-26`.
- DEFERRED −1: `I-LLMCACHE-20` leaves the DEFERRED set.

## Disposition of inherited rows

- `I-LLMCACHE-20`: promoted to REQUIRED. Row text is rewritten so
  the proposition matches the implementation; the fixture column is
  updated to point to the new fixture file (see below).
- `I-LLMCACHE-21`: unchanged, NOT-EXERCISED. Phase 3.15 does not
  run a real external model-backed cache smoke. Step 9 / Step 10
  will note this explicitly.
- `I-LLMCACHE-22`: unchanged, NOT-EXERCISED. The end-to-end Phase
  3.14 behavior probe row remains a deliberate placeholder; Phase
  3.15 does not promote it.

## Implementation file set

Phase 3.15 v1 touches exactly these files in Step 7:

| File                                                   | Change                                            |
| ------------------------------------------------------ | ------------------------------------------------- |
| `brain/llm/client.py`                                  | add `L1_CACHE_MAX_ENTRIES = 1024`; add `skip_count` attribute; add cap-check + skip-emit logic in `CachedClient.eval_consistency`; emit `llm.cache_skip` with payload `{cache_key_prefix, reason}` |
| `brain/ui/fixtures/llm_cache_l1_capacity.py`           | new fixture file driving `I-LLMCACHE-20`, `-23`, `-24`, `-25` |
| `brain/ui/fixtures/llm_cache_static_audit.py`          | extend with a new check function for `I-LLMCACHE-26` |
| `brain/invariants.py`                                  | add `"brain.ui.fixtures.llm_cache_l1_capacity"` to `FIXTURE_MODULES` |
| `tools/catalog.py`                                     | update `EXPECTED_COUNTS` banner to v0.25 numbers; update inline comment with the Phase 3.15 summary |
| `INVARIANT_CATALOG.md`                                 | replace v0.24 banner with v0.25 banner; rewrite `I-LLMCACHE-20` row; append `I-LLMCACHE-23..26` rows |
| `brain/_catalog_ids.py`                                | regenerated via `python3 -m tools.catalog generate-ids` |
| `README.md`                                            | catalog version + counts string (`v0.25` and the new count line) |
| `CURRENT_MISSION.md`                                   | catalog version + counts string (`v0.25` and the new count line) |
| `CURRENT_CAMPAIGN.md`                                  | catalog version + counts string (`v0.25` and the new count line) |

Forbidden in Step 7 (re-stated from LOCK K and the campaign
guardrails):

- `brain/tick.py`
- `brain/llm/ptcns_backed.py` semantic L2 changes (read-only
  documentation tweaks NOT required; do not touch)
- `brain/llm/prompts.py` (prompt template unchanged)
- `brain/llm/parse.py` (parser unchanged)
- `brain/ui/llm_runtime.py` (flag contract preserved; no change
  needed)
- `brain/ui/session.py`
- persistence / autosave / DB schema files
- Growth Ledger / Pattern Ledger / Coherence Monitor modules
- UI expansion files

`.gitignore` is NOT touched. `brain/.llm_cache/` is already covered
by the existing rule; no new entry is required.

## Fixture list

### New: `brain/ui/fixtures/llm_cache_l1_capacity.py`

Contains four `@register(...)`-decorated functions, one per
REQUIRED row in the bound `I-LLMCACHE-20`, `-23`, `-24`, `-25`
group. All four share a single `_CountingClient` helper class and
each uses a fresh `tempfile.TemporaryDirectory` so no test write
escapes `/tmp`.

| Function                                              | Row             | Assertion                                                              |
| ----------------------------------------------------- | --------------- | ---------------------------------------------------------------------- |
| `check_I_LLMCACHE_20_l1_count_cap_admission`          | `I-LLMCACHE-20` | `L1_CACHE_MAX_ENTRIES == 1024`; pre-fill cap with synthetic entries; record the set of existing entry digests; next miss does not write a new file; `len(*.json) == cap` after the at-cap miss (no growth past cap); every original entry is still present and readable (no eviction); a second hit against an existing entry still returns its cached response. |
| `check_I_LLMCACHE_23_at_cap_miss_calls_inner`         | `I-LLMCACHE-23` | At-cap miss: `inner.calls` grows by 1; the response returned to the caller equals `inner.response`. |
| `check_I_LLMCACHE_24_at_cap_skip_event_and_counter`   | `I-LLMCACHE-24` | At-cap miss emits exactly one `llm.cache_skip` event with payload keys exactly `{"cache_key_prefix", "reason"}` and `reason="capacity"`; `cache.skip_count == 1`; `cache.hit_count` and `cache.miss_count` unchanged in shape from Phase 3.14 (still public ints). |
| `check_I_LLMCACHE_25_no_silent_repair`                | `I-LLMCACHE-25` | Existing entries are unchanged after an at-cap miss; tampering an existing entry still raises `RuntimeError` on read (no rewrite); at-cap skip does not delete or modify any existing `*.json` file; `llm.cache_skip` is the only new event emitted, and it is **not** emitted on a normal hit or a below-cap miss. |

### Extended: `brain/ui/fixtures/llm_cache_static_audit.py`

Add one new `@register("I-LLMCACHE-26", status="STRUCTURAL")`
function with the L1-specific name
`check_I_LLMCACHE_26_l1_hygiene_static_audit`. The existing
`I-LLMCACHE-17` L2 audit (`check_I_LLMCACHE_17_l2_static_audit`)
remains a distinct function over `brain/llm/ptcns_backed.py`; the
new function's label, scope, and target path are L1-specific so the
two audits cannot collapse into each other. Walks
`brain/llm/client.py` via `ast.parse`, asserts:

- Module-level imports come only from the existing allowed set plus
  the unchanged set (no new forbidden imports introduced by Phase
  3.15).
- No calls to `eval`, `exec`, `compile`, `__import__`.
- No new string literals matching `"prompt"`, `"response"`, `"raw"`,
  `"error"`, `"trace"`, `"headers"` are introduced beyond the
  existing `"prompt"` and `"response"` literals already used by
  `CachedClient.eval_consistency` (existing literals are exempt;
  only newly-added literals must respect the allowlist).
- The new `llm.cache_skip` event payload, as represented in the
  source by the `_tracer.record(...)` call, uses only the keys
  `"cache_key_prefix"` and `"reason"`.

## Stage C implementation shard plan (Step 7)

Step 7 uses Stage C with at most two real Codex calls in total. The
preferred shape is a **single-shard wave** that writes the runtime
code and the new fixture file, followed by parent-Claude direct
edits for the catalog / counter / banner / mission / campaign
files. Rationale: the catalog + banner + version-stamp edits are
load-bearing and must be reconciled exactly; parent Claude owns
them per LOCK K.

### Wave 1 — single shard `l1_hygiene_impl`

- `allowed_files`:
  - `brain/llm/client.py`
  - `brain/ui/fixtures/llm_cache_l1_capacity.py`
  - `brain/ui/fixtures/llm_cache_static_audit.py`
- `read_files`:
  - `brain/llm/client.py`
  - `brain/ui/fixtures/llm_cache_transport.py`
  - `brain/ui/fixtures/llm_cache_bounds_artifacts.py`
  - `brain/ui/fixtures/llm_cache_static_audit.py`
  - `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CORRIGENDA.md`
  - `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CATALOG_PATCH_PLAN.md`
- shard prompt: implement `L1_CACHE_MAX_ENTRIES`, `skip_count`, and
  the cap-check / skip-emit logic per the catalog patch plan; write
  the new fixture file with the four `@register` checks above; add
  the new `check_I_LLMCACHE_26_l1_hygiene_static_audit` function
  to the existing static-audit fixture.

If Wave 1 fails or operator declines to use Stage C, parent Claude
implements directly.

### Parent-Claude direct edits (no Stage C)

After Wave 1 inspect-diff, parent Claude updates:
- `brain/invariants.py` (add fixture module to `FIXTURE_MODULES`).
- `INVARIANT_CATALOG.md` (banner + rows).
- `tools/catalog.py` (`EXPECTED_COUNTS` + inline comment).
- `brain/_catalog_ids.py` (regenerated via
  `python3 -m tools.catalog generate-ids`).
- `README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`
  (version + counts strings).

## Validation commands

Run in order. Every command must exit zero before commit.

```
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Expected post-Step-7 banner output (from `python3 -m tools.catalog counts`):

```
Category            Banner    Actual  Expected
REQUIRED               281       281       281  ok
STRUCTURAL              88        88        88  ok
NOT-EXERCISED           14        14        14  ok
DEFERRED                15        15        15  ok
OBSERVED                16        16        16  ok
```

## Non-goals and non-rows

Phase 3.15 does NOT add catalog rows for:

- byte-cap policy (Option B) — explicitly deferred.
- TTL eviction (Option C) — explicitly deferred.
- parse-failure-aware bypass / eviction (Option E) — explicitly
  deferred; the existing raw bad-response replay behavior is
  preserved unchanged.
- manual `inspect` / `clear` CLI helpers (Option F) — explicitly
  deferred.
- SelfModel implementation — out of scope (Phase 3.12 deferral).
- `/pattern-ledger` UI — `I-PLEDGER-17` remains DEFERRED.
- `/coherence-summary` UI — `I-COHMON-13` remains DEFERRED.
- `/growth-ledger` UI — `I-GROW-21` remains DEFERRED.
- end-to-end Pattern / Coherence / Growth Ledger dry-run helpers —
  `I-PLEDGER-18` / `I-COHMON-14` / `I-GROW-22` remain
  NOT-EXERCISED.
- real external model-backed cache smoke — `I-LLMCACHE-21` remains
  NOT-EXERCISED.
- end-to-end Phase 3.14 behavior probe — `I-LLMCACHE-22` remains
  NOT-EXERCISED.

## Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: yes
- mode: review
- model: gpt-5.5
- effort: high
- wrapper command:
  `python3 tools/claude_helpers/codex_chatgpt_subagent.py --mode review --model gpt-5.5 --effort high --timeout 600 --prompt-file /tmp/toyi_phase3_15_step5_review_question.md`
- wrapper status: `exit_code=0`, `error_class=None`
- question file: `/tmp/toyi_phase3_15_step5_review_question.md`
- answer file: `/tmp/toyi_phase3_15_step5_review_answer.md`
- overall verdict: APPROVE WITH MINOR EDITS (no blockers)
- accepted advice:
  - strengthen the `I-LLMCACHE-20` proposition to explicitly assert
    "no growth past cap" AND "existing entries remain present and
    readable" (added)
  - strengthen the `I-LLMCACHE-20` fixture spec to record the set
    of pre-cap entry digests and verify every original entry
    remains present and readable after the at-cap miss (added)
  - keep the new I-LLMCACHE-26 L1 audit function name distinct
    from the existing I-LLMCACHE-17 L2 audit function; document
    that the two audits stay separate (added)
- rejected advice: none
- reason: catalog patch plan adversarial review required by
  `CURRENT_CAMPAIGN.md`

Stage B limited-write collaboration:
- used: no
- reason: parent Claude wrote the patch plan directly; catalog
  patch text is load-bearing and was kept under direct
  human-reviewable control.

Stage C orchestration:
- used: no (for the draft itself)
- reason: parent Claude wrote the catalog patch plan directly to
  conserve the remaining Stage C budget for Step 7 implementation.
  The Step 7 Stage C shard plan above governs Step 7's Stage C
  usage.

## Stop

Stop at Review Gate A.
