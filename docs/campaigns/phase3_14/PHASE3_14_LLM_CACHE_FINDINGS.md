# PHASE3_14_LLM_CACHE_FINDINGS.md

## Purpose

This document triages the Step 8 LLM cache behavior report findings
(F-01..F-10) and assigns each one a campaign disposition: blocker,
non-blocking follow-up, or pass evidence.

It is documentation only. It does not change code, catalog rows,
fixtures, runtime behavior, cache behavior, tick semantics, bridge
behavior, or any gate. No scope expansion is authorized. The
next artifact is the Step 10 final Phase 3.14 audit.

## Baseline

- Catalog version: v0.24.
- Counts: REQUIRED 277 / STRUCTURAL 87 / NOT-EXERCISED 14 /
  DEFERRED 16 / OBSERVED 16.
- Step 7 implementation commit: `366bf95`
  (`phase3.14 step7: implement llm cache discipline`).
- Step 8 behavior report commit: `8db679f`
  (`phase3.14 step8: llm cache behavior report`).
- Step 8 verdict: PASS WITH DEFERRED FOLLOW-UPS (zero blocking
  findings; all twelve measurement families landed their expected
  results).
- Branch: `campaign/phase3-14-llm-cache-discipline`.

## Source Findings

The ten findings below are imported verbatim from
`docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_REPORT.md` and
triaged here.

| Finding ID | Step 8 severity / category | Triage disposition | Blocker? | Action | Target campaign / step |
| --- | --- | --- | --- | --- | --- |
| F-01 — L1 still caches raw bad responses under the original-prompt hash because L1 is a transport-layer cache. A future identical-input run would replay the bad response and re-trigger the retry shell until the parser succeeds or exhausts. | Low / deferred enhancement. | Non-blocking deferred enhancement. L1 is the existing v0.16 transport cache; LOCK F preserves its raw prompt-hash semantics on purpose. L2 already excludes parse-failures from the success cache (LOCK H / I-LLMCACHE-09), so the L2 surface does not poison. The remaining L1 replay risk is a pre-Phase-3.14 property surfaced for documentation completeness. | No. | Defer to a future L1 bounding / eviction / parse-failure-aware transport-cache policy campaign. Document only; no code patch in Phase 3.14. | Bundled with the eventual I-LLMCACHE-20 follow-up campaign. |
| F-02 — I-LLMCACHE-20 (L1 cache bounding / eviction policy) remains DEFERRED in v1. L1 disk growth is therefore unbounded over long-running model-backed sessions. | Low / deferred enhancement. | Planned deferred row. Phase 3.14 introduces no new L1 cache surface — flipping `enable_cache=True` by default for model-backed modes activates the existing v0.16 `CachedClient`; the "no unbounded new cache" Phase 3.14 guardrail is satisfied because the only new persistent surface (L2) is bounded under I-LLMCACHE-11. | No. | Carry forward as a future campaign candidate. The deferred status is already cataloged. | Future campaign (post-3.14) under a dedicated row family. |
| F-03 — I-LLMCACHE-21 (real external model-backed ORS smoke with cache enabled) and I-LLMCACHE-22 (end-to-end Phase 3.14 behavior runner) remain NOT-EXERCISED in v1. Step 8 exercised the end-to-end property along the deterministic local-client route only. | Low / deferred enhancement. | Planned NOT-EXERCISED placeholders. Step 8's deterministic local-client route is the v1 evidence. | No. | Leave both statuses as planned. Promote either row only with explicit operator sponsorship and a follow-up campaign artifact. | Optional future campaign with explicit operator approval. |
| F-04 — Cache-default policy lives in two surfaces: the parser flips `enable_cache=True` for explicit model-backed modes; the bare `LlmRuntimeConfig(...)` constructor still defaults `enable_cache=False`. The parser also preserves `--llm-enable-cache` for OFFLINE/MOCK so the factory can cleanly reject it. | Low / UX/readability. | Non-blocking readability nuance. Catalog row I-LLMCACHE-02's description explicitly cites `parse_llm_runtime_args(...)` and `build_llm_client_from_config(...)`, so the catalog row already encodes the correct surface. | No. | Optional documentation clarification in a future maintenance pass on `brain/ui/llm_runtime.py` or the row description. No code patch in Phase 3.14. | Optional future maintenance pass; not on the Phase 3.14 critical path. |
| F-05 — The Step 5 observability plan enumerated `semantic_cache_skip` reasons `{"parse_failure", "capacity", "disabled", "offline_or_mock"}`. The v1 implementation only emits `"parse_failure"` and `"capacity"`; `"disabled"` and `"offline_or_mock"` are unreachable because the L2 surface is gated at `_l2_metadata is None`. | Low / documentation. | Non-blocking plan-vs-implementation note. Catalog row I-LLMCACHE-13 constrains the payload to include a `reason` field; it does not require all plan-enumerated values be emitted. The "unreachable values" property is a strictly-stronger guarantee (the L2 surface is short-circuited before those reasons would apply), not a regression. | No. | Carry into Step 10 final audit as a known plan-vs-implementation reconciliation. No code patch. | Step 10 final audit narrative. |
| F-06 — Two fixture carve-outs were necessary at Step 7: (a) `brain/ui/fixtures/tui_smoke.py` narrowed the `I-UI-07` forbidden-builtin-call audit to `ast.Name` calls only (so `LLMBackedPtCns.eval(content_id)` is not false-flagged) and extended the persistence-fixture `tempfile` exemption to cover `llm_cache_*.py`; (b) `brain/ui/fixtures/llm_runtime_tick_seam.py` added an `_unwrap_for_test()` helper that peels `CachedClient` before the `I-LLMTOG-09` `isinstance(...)` assertions so the "mode selection drives transport type" contract survives the new cache default. | Low / UX/readability (resolved blocking-contradiction). | Accepted narrow fixture-only changes. Both carve-outs are inline-documented in the touched files, are justified (false-positive correction in (a); contract preservation in (b)), and have no runtime impact. | No. | Record as resolved Step 7 blocking-contradiction fixes. Future cache work that adds fixtures using method names matching Python builtins should re-audit (a); no other follow-up required. | Future cache fixture authors should re-read the carve-out rationale before adding methods named like Python builtins. |
| F-07 — `brain/tick.py` is unchanged. For the measured identical-event scenario, cached vs uncached `tick(...)` produced field-for-field equal `(new_state, TickRecord)` for the same client responses (M-FAM12-TICK). The runner-level property over the full event space is gated by `brain/ui/fixtures/llm_cache_no_tick_change.py` (I-LLMCACHE-16), not by the Step 8 probe. | Low / safety / invariant (confirmed). | Pass evidence. Confirms LOCK N along the measured route; the catalog-level guarantee is gated by I-LLMCACHE-16 at every runner pass. | No. | None. | n/a |
| F-08 — L2 entries on disk have payload exactly `{"key_prefix", "parsed"}`. `brain/.llm_cache/` (line 28 of `.gitignore`) covers `brain/.llm_cache/eval_v1/`. No file under `brain/.llm_cache/**` is tracked. No raw prompt / response body, no error text, no provider metadata is persisted to L2. | Low / safety / invariant (confirmed). | Pass evidence. Confirms LOCK L / I-LLMCACHE-12. | No. | None. | n/a |
| F-09 — Corrupt L2 entries (invalid JSON, wrong key set) fail loud with `RuntimeError` containing `"corrupt"` and never silently call the inner client. | Low / safety / invariant (confirmed). | Pass evidence. Confirms LOCK G / I-LLMCACHE-10 for L2. L1's pre-Phase-3.14 corrupt-cache fail-loud is unchanged. | No. | None. | n/a |
| F-10 — L2 capacity behavior: hits still read at cap; misses may call inner in explicit model-backed mode; no new entry is written at cap; `llm.semantic_cache_skip` with `reason="capacity"` is emitted. No eviction / pruning fires in v1. | Low / safety / invariant (confirmed). | Pass evidence. Confirms LOCK I / I-LLMCACHE-11. The probe used a monkeypatched cap of 2; production cap is 1024 (`SEMANTIC_CACHE_MAX_ENTRIES`). | No. | None. | n/a |

## Blocker Assessment

- No blocker findings.
- No critical correctness finding.
- No safety / invariant blocker.
- No catalog-count mismatch (counts 277/87/14/16/16 match across
  `tools/catalog.py` EXPECTED_COUNTS, `INVARIANT_CATALOG.md` banner,
  `README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`).
- No hidden model-call blocker (M-FAM8-CORRUPT shows corrupt L2 fails
  loud without inner; M-FAM4..6 show L1/L2 hit paths never call inner;
  M-FAM3-E/F show OFFLINE/MOCK factory-rejection holds).
- No tick semantic blocker (`git diff origin/main -- brain/tick.py` is
  empty; M-FAM12-TICK confirms parity along the measured route;
  I-LLMCACHE-16 fixture gates the runner-level property).
- No sensitive artifact blocker (F-08; gitignore line 28 covers
  `brain/.llm_cache/`; L2 payload is exactly `{key_prefix, parsed}`).
- No bridge policy blocker (Stage A and Stage B usage in Step 7 / Step
  8 matched the cataloged policy; hash-only audit JSONL under
  `.claude/codex_bridge_logs/` is gitignored).
- No out-of-scope runtime edit blocker (the Step 7 diff vs main hit
  the planned implementation surface plus the two narrow audited
  fixture carve-outs; `brain/tick.py`, `brain/development/*`,
  `brain/ui/session.py`, persistence / autosave, `scenarios/`,
  `traces/`, `lean_reference/`, `.claude/` are all untouched).

## Non-blocking Follow-ups

1. **Future L1 bounding / eviction campaign.** I-LLMCACHE-20 remains
   DEFERRED. A future campaign may add a bounded L1 cache surface with
   explicit eviction / TTL / byte-cap policy. Phase 3.14 introduces no
   new L1 surface, so the "no unbounded new cache" guardrail is
   already satisfied for the campaign.
2. **Future real external ORS smoke.** I-LLMCACHE-21 remains
   NOT-EXERCISED. Promote only with explicit operator sponsorship and
   a dedicated campaign artifact (key-management, rate-limit policy,
   trace policy, failure-mode policy).
3. **Future end-to-end behavior runner.** I-LLMCACHE-22 remains
   NOT-EXERCISED. Step 8's deterministic local-client route is the v1
   evidence; a future campaign may promote this if a real-LLM walk is
   sponsored.
4. **Optional runtime-policy documentation clarification.** The
   parser owns the model-backed default-on cache policy; the bare
   `LlmRuntimeConfig(...)` constructor still defaults
   `enable_cache=False`. A future maintenance pass could surface this
   inline in `brain/ui/llm_runtime.py` and / or in the I-LLMCACHE-02
   row description. Not required for Phase 3.14.
5. **Optional observability wording cleanup.** The
   `semantic_cache_skip` `reason` values `"disabled"` and
   `"offline_or_mock"` from the Step 5 plan are unreachable in v1
   because the L2 surface is gated at `_l2_metadata is None`. A
   future audit-doc pass may either prune the plan enumeration or add
   an explicit note that the v1 implementation strictly tightens the
   plan. Not required for Phase 3.14.
6. **Optional future fixture audit cleanup.** If more fixtures use
   methods named after Python builtins (`eval`, `compile`, etc.),
   keep the I-UI-07 `ast.Name`-only narrowing under review and
   re-audit if any such method ever becomes a real arbitrary-code
   surface. The two existing carve-outs are inline-documented.

## Items That Do NOT Block Phase 3.14

- F-01 L1 raw bad response transport-cache behavior.
- F-02 L1 bounding deferred (I-LLMCACHE-20).
- F-03 ORS smoke and end-to-end runner placeholders NOT-EXERCISED
  (I-LLMCACHE-21, I-LLMCACHE-22).
- F-04 parser-vs-constructor readability nuance.
- F-05 unreachable `semantic_cache_skip` `reason` values.
- F-06 the two narrow fixture carve-outs.
- Lack of real external model smoke (Phase 3.14 is offline-default;
  Stage A / Stage B bridges are advisory / limited-write, not runtime
  LLM seams).
- Lack of L1 eviction / bounding.
- Lack of UI work (`/pattern-ledger`, `/coherence-summary`,
  `/growth-ledger` UIs remain DEFERRED under their respective rows;
  no Phase 3.14 UI expansion was authorized).
- Lack of SelfModel (explicitly out of scope; deferred until a
  follow-up campaign explicitly sponsors it).
- Lack of changes to Growth Ledger / Pattern Ledger / Coherence
  Monitor (Phase 3.14 made no semantic edits to any of these).

## Campaign Verdict After Triage

**PASS WITH DEFERRED FOLLOW-UPS.**

Reason:

- All five canonical gates green
  (`python3 -m tools.catalog counts`, `python3 -m tools.citations
  verify`, `python3 -m tools.import_audit`,
  `python3 -m brain.invariants run`, `bash tools/check_all.sh`).
- Step 8 behavior report passed with zero blocking findings.
- No Step 8 finding triages to a blocker here.
- All deferred / NOT-EXERCISED rows are planned, cataloged, and
  unchanged from the Step 5 accepted plan.
- Implementation matches the Step 5 plan as amended at Step 6 (no
  amendment was required; the plan was accepted as written).
- No unauthorized scope expansion (the Step 7 diff respected the
  catalog patch plan's allowed-file list; the two fixture carve-outs
  are within the inherited audit scope and are inline-documented).
- Bridge usage in Steps 1, 2, 4, 5, 7, 8, and 9 matched the cataloged
  Stage A / Stage B policy; hash-only audit JSONL is gitignored.

## Stage A ChatGPT/Codex Consultation

Stage A was used to adversarially review the Step 9 triage before
final draft.

- used: yes
- mode: review
- model: gpt-5.5
- effort: low
- wrapper command:
  `python3 tools/claude_helpers/codex_chatgpt_subagent.py --mode review
  --model gpt-5.5 --effort low --timeout 120 --prompt-file
  /tmp/toyi_phase314_step9_advisor_question.md
  > /tmp/toyi_phase314_step9_advisor_answer.md`
- question file: `/tmp/toyi_phase314_step9_advisor_question.md`
- answer file: `/tmp/toyi_phase314_step9_advisor_answer.md`
- wrapper status: exit_code=0, status="success", codex_returncode=0,
  error_class=null, duration_ms≈27704, truncated=false; hash-only
  audit JSONL under `.claude/codex_bridge_logs/` (gitignored).
- accepted advice (confirmatory; Stage A agreed PASS WITH DEFERRED
  FOLLOW-UPS, disagreement "minor", confidence "medium"):
  - kept the triage strictly inside the Step 8 finding scope; made no
    code / catalog / fixture / runtime / tick-semantic / model-call
    changes inside Step 9 (the advisor's required wording guardrail);
  - preserved the exact status labels `DEFERRED` for I-LLMCACHE-20
    and `NOT-EXERCISED` for I-LLMCACHE-21 / I-LLMCACHE-22;
  - held the verdict at PASS WITH DEFERRED FOLLOW-UPS rather than the
    stronger plain PASS;
  - kept the F-07 tick-boundary wording scoped to "the measured
    identical-event scenario" and "fixture-gated by
    `llm_cache_no_tick_change.py`", not a universal claim;
  - kept F-06..F-10 framed as "pass evidence within tested scope",
    not as universal correctness statements;
  - F-04 explicitly distinguishes parser-owned default-on policy from
    the bare `LlmRuntimeConfig(...)` constructor default of
    `enable_cache=False`;
  - F-05 frames the unreachable `semantic_cache_skip` reasons as
    plan-vs-implementation reconciliation, not as currently validated
    behavior.
- rejected advice: did not change code, catalog rows, fixtures, gate
  commands, or runtime behavior inside Step 9; did not promote any
  deferred / NOT-EXERCISED row; did not introduce new measurements
  (the Step 8 measurement pass remains the evidence base); did not
  treat F-01 as a blocker (the local Step 9 brief is triage-only and
  Step 8 reports the L1-transport-cache behavior "remains" by design
  under LOCK F).
- reason: Stage A is the required adversarial reviewer for Step 9
  triage. Step 9 is documentation-only.

## Stage B Limited-Write Collaboration

- used: no
- mode: n/a
- model: n/a
- effort: n/a
- wrapper command: n/a
- allowed files: n/a
- prompt file: n/a
- answer file: n/a
- wrapper status: n/a
- files changed: none
- accepted edits: none
- rejected edits: none
- reason: the Step 9 brief explicitly discourages Stage B for this
  triage. Parent Claude drafted the file directly. The cross-reference
  density (10 findings × 6 disposition fields, multiple LOCK / row
  citations, plus blocker / non-blocker / verdict sections) is well
  inside what a manual draft can deliver accurately.

## Next Artifact

Step 10:

`docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_AUDIT.md`

Step 10 is the final Phase 3.14 audit. It must record the PASS verdict
with the canonical confirmations (no SelfModel, no aggregate
awareness / I-ness / growth score, no hidden LLM calls, no DB schema
change, no unbounded cache growth, no tick semantic change beyond what
Review Gate A authorized — which was none —, and per-step Stage A /
Stage B disclosure links). After Step 10, Step 11 opens the final PR
into main.
