# Phase 3.15 L1 Cache Hygiene — Final Audit

## Verdict

**PASS WITH DEFERRED FOLLOW-UPS.**

The Phase 3.15 campaign retires the previously DEFERRED
`I-LLMCACHE-20` row by binding a deterministic write-skip-at-cap
admission policy with `L1_CACHE_MAX_ENTRIES = 1024` to the existing
`CachedClient` L1 transport cache, and adds `I-LLMCACHE-23..26`
covering at-cap miss behavior, observability, no-silent-repair
guarantees, and a static AST audit. L2 (`eval_v1`) semantics are
unchanged. `brain/tick.py` is not edited. Offline remains default;
model-backed modes remain explicit opt-in. All canonical gates are
green.

## Validation summary

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
377 rows checked  ·  REQUIRED green: 282 ·  REQUIRED red: 0
                  ·  STRUCTURAL green: 88 ·  STRUCTURAL red: 0
                  ·  OBSERVED: 7 pass / 0 fail  ·  gate failures: 0

bash tools/check_all.sh
All checks passed.
```

(`REQUIRED green: 282` exceeds the catalog's 281 by one because the
runner counts the `_meta` row for `I-CAT-01` as a passing REQUIRED
check; this matches the Phase 3.14 audit convention.)

## Files changed across the campaign

Step 1 (`c302ebd phase3.15 step1: l1 cache hygiene mission sync`):
- `CURRENT_MISSION.md` (Phase 3.14 → Phase 3.15)
- `CURRENT_CAMPAIGN.md` (Phase 3.14 → Phase 3.15, full macro
  sequence, Stage A/B/C policy)
- `PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md` (new root roadmap; drafted
  via Stage C single-shard wave after operator-approved auto-retry
  on transport failure, then H1 title added by parent Claude)

Step 2 (`981a9a4 phase3.15 step2: l1 cache hygiene synthesis`):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_SYNTHESIS.md`
  (Step 4 LOCK driver document)

Step 3 (`6ecc213 phase3.15 step3: l1 cache hygiene probe`):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_PROBE.md`
  (deterministic measurements over the pre-implementation L1
  surface)

Step 4 (`039835f phase3.15 step4: l1 cache hygiene corrigenda`):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CORRIGENDA.md`
  (LOCK A..L)

Step 5 (`90e3b19 phase3.15 step5: l1 cache hygiene catalog patch plan`):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CATALOG_PATCH_PLAN.md`
  (exact row family extension, status, count delta, fixtures,
  files, validation)

Step 6 — Review Gate A: ACCEPT PLAN AS WRITTEN. No file changes.

Step 7 (`7259535 phase3.15 step7: implement l1 cache hygiene`):
- `brain/llm/client.py` (added `L1_CACHE_MAX_ENTRIES = 1024`,
  `skip_count`, `_at_capacity()`, the write-skip branch, and the
  `llm.cache_skip` event emission)
- `brain/ui/fixtures/llm_cache_l1_capacity.py` (new, 4 REQUIRED
  fixtures: `I-LLMCACHE-20/23/24/25`)
- `brain/ui/fixtures/llm_cache_static_audit.py` (extended with the
  `I-LLMCACHE-26` STRUCTURAL audit over `brain/llm/client.py`)
- `brain/invariants.py` (added the new fixture module to
  `FIXTURE_MODULES`)
- `tools/catalog.py` (`EXPECTED_COUNTS` updated to v0.25 numbers;
  inline comment refreshed with Phase 3.15 summary)
- `INVARIANT_CATALOG.md` (banner v0.25 added; `I-LLMCACHE-20` row
  rewritten as REQUIRED; rows `I-LLMCACHE-23..26` appended; summary
  block updated)
- `brain/_catalog_ids.py` (regenerated via
  `python3 -m tools.catalog generate-ids`)
- `README.md` (catalog version v0.25; count line updated)
- `CURRENT_MISSION.md` (baseline v0.25 / 281 / 88 / 14 / 15 / 16)
- `CURRENT_CAMPAIGN.md` (baseline v0.25 / 281 / 88 / 14 / 15 / 16)

Step 8 (`43b483c phase3.15 step8: l1 cache hygiene behavior report`):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_BEHAVIOR_REPORT.md`
  (post-implementation verification matrix tied LOCK-by-LOCK to
  observed behavior)

Step 9 (`3dcb7e7 phase3.15 step9: l1 cache hygiene findings`):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_FINDINGS.md`
  (pass evidence, deferred follow-ups, no-block triage)

Step 10 (this commit):
- `docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_AUDIT.md`

## Catalog / count summary

| Metric           | v0.24 (Phase 3.14) | v0.25 (Phase 3.15) | Delta |
| ---------------- | ------------------ | ------------------ | ----- |
| REQUIRED         | 277                | 281                | +4    |
| STRUCTURAL       | 87                 | 88                 | +1    |
| NOT-EXERCISED    | 14                 | 14                 | 0     |
| DEFERRED         | 16                 | 15                 | -1    |
| OBSERVED         | 16                 | 16                 | 0     |

Row events:
- `I-LLMCACHE-20`: promoted from DEFERRED to REQUIRED.
- `I-LLMCACHE-23` (REQUIRED): new — at-cap miss inner-call discipline.
- `I-LLMCACHE-24` (REQUIRED): new — `llm.cache_skip` event +
  `skip_count` counter.
- `I-LLMCACHE-25` (REQUIRED): new — no silent repair / corrupt-entry
  fail-loud preserved.
- `I-LLMCACHE-26` (STRUCTURAL): new — static AST audit over
  `brain/llm/client.py`.
- `I-LLMCACHE-21` and `I-LLMCACHE-22`: unchanged (NOT-EXERCISED).

## Behavior summary

L1 cache write-skip-at-cap admission policy verified deterministically
against `MockClient` and a `tempfile.TemporaryDirectory` harness in
both Step 3 (pre-implementation) and Step 8 (post-implementation).
The Step 8 verification matrix walks LOCK A through LOCK L. Every
LOCK is supported by an observable measurement.

Key observed properties:

- The L1 entry count never exceeds `L1_CACHE_MAX_ENTRIES = 1024`.
- At cap, the inner client is still called and the response is
  still returned; only the cache write is skipped.
- Existing entries are never removed or rewritten.
- Corrupt entries still raise `RuntimeError` on read; the inner
  client is not called as a silent fall-back.
- The new `llm.cache_skip` event payload is exactly
  `{cache_key_prefix, reason}` with `reason="capacity"`. The
  static AST audit `I-LLMCACHE-26` enforces this at build time.
- L2 (`eval_v1`) semantics are unchanged.
- OFFLINE / MOCK still reject `--llm-enable-cache` at the factory
  boundary.
- The Phase 3.14 flag contract is preserved unchanged.

## Findings summary

Zero blockers. The Step 9 findings document records the deliberate
deferrals (Option B byte cap, Option C TTL, Option E
parse-failure-aware bypass, Option F operator helpers,
`I-LLMCACHE-21`, `I-LLMCACHE-22`, SelfModel, the three ledger UIs)
with explicit pointers for future campaigns. Raw bad-response
replay remains durable today; this is explicitly out of scope per
LOCK C.

## Stage A / Stage B / Stage C usage summary

Stage A consultations across the campaign (each via
`tools/claude_helpers/codex_chatgpt_subagent.py` with model=gpt-5.5,
effort=high):

- Step 2 synthesis review — APPROVE WITH MINOR EDITS; nits applied.
- Step 5 catalog patch plan review — APPROVE WITH MINOR EDITS; nits
  applied.
- Step 8 behavior report review — APPROVE WITH MINOR EDITS; nits
  applied.
- Step 10 audit review — declared redundant. Three previous Stage A
  reviews already exercised the Phase 3.15 design surface; the
  Stage A budget is preserved as required by the goal contract.

Stage B usage across the campaign: none. Stage B was eligible for
several doc shards but Stage C was the preferred bridge per the
campaign Stage C policy, and parent Claude wrote several docs
directly to conserve the Stage C call budget.

Stage C usage across the campaign:

- Step 1 single-shard wave for `PHASE3_15_L1_CACHE_HYGIENE_ROADMAP.md`:
  succeeded after operator-approved auto-retry (see Stage C
  retry-permission note below). The shard returned a valid draft;
  parent Claude added the H1 title.
- Step 2 single-shard wave for the synthesis: attempted twice;
  both attempts failed with `SHARD_FAILED` / `CODEX_OUTPUT_TOO_LARGE`
  driven by websocket connection resets. The operator explicitly
  authorized auto-retry; both retries were also failures. Parent
  Claude wrote the synthesis directly to conserve budget.
- Step 3 / 4 / 5 / 7 / 8 / 9 / 10 doc work: parent Claude direct
  (no Stage C call).

Stage C call accounting:

| Step | Real Codex calls (successful + failed) | Notes |
| ---- | -------------------------------------- | ----- |
| 1    | 1 (success)                            | roadmap shard |
| 2    | 2 (both failed)                        | both `SHARD_FAILED`; operator approved auto-retry |
| All later steps | 0                            | parent Claude direct |
| **Total** | **3** | within the goal's 6-call budget |

**Stage C retry-permission disclosure:** when the first Step 2
Stage C wave failed with a transport-induced
`CODEX_OUTPUT_TOO_LARGE`, the operator explicitly authorized
auto-retry as a one-time, in-session exception to the
no-automatic-retry rule. The second attempt also failed; parent
Claude then chose to write the synthesis directly rather than
spending more of the 6-call budget on transport-flaky doc shards.
That single operator-approved auto-retry is recorded here per the
disclosure requirement.

## Non-goal confirmations

- **No SelfModel implementation.** Confirmed by inspection of the
  Step 7 diff: no new module under `brain/development/`, no new
  field on `BrainState`, no new dispatcher, no new persistence
  surface.
- **No consciousness / sentience / subjective / semantic / truth /
  agency / self-modification claim.** Confirmed by inspection of
  every new artifact and code path. "Bounded admission" is
  engineering language about cache write policy.
- **No aggregate awareness / I-ness / growth score.** No such
  scalar is computed or stored anywhere new.
- **No hidden LLM call.** Every inner call is observable as a miss
  or as a skip-with-`reason="capacity"`. The static AST audit
  `I-LLMCACHE-26` enforces no new dynamic-execution or
  forbidden-import call paths in `brain/llm/client.py`.
- **No hidden persistence change.** No file under
  persistence / autosave / DB modules was edited. No
  `SCHEMA_VERSION` bump. No DB schema change.
- **No L2 (`eval_v1`) semantic change.** `brain/llm/ptcns_backed.py`
  was not edited.
- **No tick semantic change.** `brain/tick.py` was not edited.
  Verified by `git diff --stat 7259535^..7259535 -- brain/tick.py`
  returning empty output.
- **L1 cache growth is bounded by the locked policy.** The L1 entry
  count never exceeds `L1_CACHE_MAX_ENTRIES = 1024`. Confirmed by
  the Step 8 anti-growth test.

## Deferred follow-ups

Carried forward unchanged from the Step 9 findings:

- Option B (byte cap) — future campaign.
- Option C (TTL) — future campaign.
- Option E (parse-failure-aware bypass / eviction) — future
  campaign; raw bad-response replay remains durable today.
- Option F (manual `inspect` / `clear` CLI helpers) — future
  campaign.
- `I-LLMCACHE-21` (real external model-backed cache smoke) —
  remains NOT-EXERCISED.
- `I-LLMCACHE-22` (end-to-end Phase 3.14 behavior probe) — remains
  NOT-EXERCISED.
- SelfModel implementation — remains deferred (Phase 3.12).
- `/pattern-ledger` UI (`I-PLEDGER-17`),
  `/coherence-summary` UI (`I-COHMON-13`),
  `/growth-ledger` UI (`I-GROW-21`) — remain DEFERRED.
- End-to-end Pattern / Coherence / Growth Ledger dry-run helpers
  (`I-PLEDGER-18`, `I-COHMON-14`, `I-GROW-22`) — remain
  NOT-EXERCISED.

## Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: no (at Step 10)
- reason: explicitly declared redundant per the campaign
  `CURRENT_CAMPAIGN.md` clause "Step 10 final audit adversarial
  review (unless explicitly redundant)". The Step 2, Step 5, and
  Step 8 reviews already exercised the Phase 3.15 design surface
  and behavior verification; no new design content is introduced
  by the audit beyond the verdict and the cross-reference summary.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude wrote the audit directly.

Stage C orchestration:
- used: no (at Step 10)
- reason: audit is a verdict + summary over already-committed
  artifacts; no Stage C shard would add value.

## Next-campaign note

`SelfModel` remains deferred and is not in flight. A future
campaign that wants to retire SelfModel must first accept the
Phase 3.12 Step 15 roadmap or supersede it. Phase 3.15 makes no
SelfModel claim and adds no SelfModel infrastructure.

The next bounded substrate question (post-Phase-3.15) is operator
choice. Recorded options include: L1 byte cap (Option B), L1 TTL
(Option C), L1 parse-failure-aware bypass (Option E), L1 operator
helpers (Option F), promotion of `I-LLMCACHE-21` /
`I-LLMCACHE-22`, or any of the three deferred ledger UIs.
