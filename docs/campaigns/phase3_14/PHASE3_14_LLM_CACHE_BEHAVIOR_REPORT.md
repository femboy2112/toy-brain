# PHASE3_14_LLM_CACHE_BEHAVIOR_REPORT.md

## Purpose

This report measures the implemented Phase 3.14 LLM Cache Discipline after
Step 7 (commit `366bf95`). It is documentation only. It does not change
code, catalog rows, fixtures, runtime behavior, tick semantics, or any
gate. It records deterministic in-process measurements against the
post-Step-7 runtime and compares the observed behavior to the Step 5
plan, the Step 4 LOCK statements, and the Step 3 baseline.

**Scope discipline.** This report is deterministic local-client only.
All measurements use a local `CountingClient`, the existing
`brain.llm.client.MockClient`, the existing `brain.llm.client.CachedClient`,
and the existing `brain.llm.ptcns_backed.LLMBackedPtCns`, with
`SEMANTIC_CACHE_DIR` and `SEMANTIC_CACHE_MAX_ENTRIES` monkeypatched in
process so that no L2 cache files land under `brain/.llm_cache/eval_v1/`
during measurement. It does not run real external model-backed LLM
modes; it does not call `AnthropicAPIClient`, `ClaudeCLIClient`, or
`CodexCLIClient` against a real service; and it does not prove
universal properties about external providers, L1 disk growth, or
every possible tick path. See the **Not Established By This Report**
section for the scope boundary.

The next artifact is the Step 9 LLM cache findings / triage doc.

## Baseline

- Catalog version: v0.24.
- Counts: REQUIRED 277 / STRUCTURAL 87 / NOT-EXERCISED 14 / DEFERRED 16
  / OBSERVED 16.
- Step 7 implementation commit: `366bf95`
  (`phase3.14 step7: implement llm cache discipline`).
- Branch: `campaign/phase3-14-llm-cache-discipline`.
- Row family in scope: `I-LLMCACHE-01..I-LLMCACHE-22`.
- `brain/tick.py` is not edited by Phase 3.14 (`git diff origin/main --
  brain/tick.py` is empty).
- No real external model call is performed by Step 8.

## Method

- Temporary helper path:
  `/tmp/phase3_14_llm_cache_behavior_report_probe.py`.
- Invocation:
  `PYTHONPATH=/home/leah/brain/toy-brain python3
  /tmp/phase3_14_llm_cache_behavior_report_probe.py`.
- Deterministic clients used:
  - `CountingClient` — a local file-private stand-in that returns a
    canned `"PRESERVE"` (or a scripted sequence) per call and tracks
    `calls`. Not committed.
  - `brain.llm.client.MockClient` — for parse-failure / retry sequences.
  - `brain.llm.client.CachedClient` — wraps a `CountingClient` /
    `MockClient` with a `cache_dir` rooted under `tempfile.TemporaryDirectory()`.
  - `brain.llm.ptcns_backed.LLMBackedPtCns` — the post-Step-7
    implementation under measurement.
- Cache directories used:
  - L1 cache dirs: per-scenario `tempfile.TemporaryDirectory()` under
    `/tmp/`.
  - L2 cache dirs: per-scenario `tempfile.TemporaryDirectory()` under
    `/tmp/`, installed by setting
    `brain.llm.ptcns_backed.SEMANTIC_CACHE_DIR` to the tempdir path for
    the duration of the scenario and restoring it afterward.
- Monkeypatches:
  - `brain.llm.ptcns_backed.SEMANTIC_CACHE_DIR` — replaced with an
    isolated temp dir per scenario (Family 5..12), then restored.
  - `brain.llm.ptcns_backed.SEMANTIC_CACHE_MAX_ENTRIES` — replaced with
    `2` for the capacity scenario (Family 9), then restored. This
    simulates the cap behavior without writing 1024 files in /tmp.
  - No other module state is patched.
- No repo file is mutated by the probe.
- No L2 file is written under `brain/.llm_cache/eval_v1/` during
  measurement.
- No `AnthropicAPIClient`, `ClaudeCLIClient`, or `CodexCLIClient` is
  ever called against a real service.
- No model-backed runtime mode is launched.
- No raw prompt body, no raw model response body, and no L2 file
  contents are quoted in this report.

## Measurement Table

| Measurement ID | Question | Setup | Observed result | Expected result | Verdict | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| M-FAM1-GATES | Do the five canonical gates pass against the post-Step-7 tree? | `python3 -m tools.catalog counts`, `python3 -m tools.citations verify`, `python3 -m tools.import_audit`, `python3 -m brain.invariants run`, `bash tools/check_all.sh`. | Catalog counts banner=actual=expected=`277 / 87 / 14 / 16 / 16` ok. `Verified 100 citations.` `I-PCE-05: agency.py is clean of pce imports.` Runner `gate failures: 0` `REQUIRED red: 0 STRUCTURAL red: 0`. `check_all.sh` ends with `All checks passed.`. | All five PASS. | works | Re-run captured in Post-Write Validation section below. Drives the I-LLMCACHE-01..22 row family green status. |
| M-FAM2-DIFF | What does the Step 7 diff surface include / exclude vs main? | `git diff origin/main --stat`. | 26 files changed: I-LLMCACHE row block in INVARIANT_CATALOG.md; catalog count files (`tools/catalog.py`, `brain/_catalog_ids.py`, `brain/invariants.py`); `brain/llm/parse.py` + `brain/llm/prompts.py` (version constants only); `brain/llm/ptcns_backed.py` (L2 implementation); `brain/ui/llm_runtime.py` (default-on policy + flag conflict); the eight `brain/ui/fixtures/llm_cache_*.py` new fixtures; `brain/ui/fixtures/tui_smoke.py` (audit narrowing + tempfile exemption); `brain/ui/fixtures/llm_runtime_tick_seam.py` (CachedClient-unwrap helper); five Phase 3.14 docs under `docs/campaigns/phase3_14/` + the root roadmap; `README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md` (catalog stamps). No `brain/tick.py` edit. No `brain/development/*.py` edit (Growth Ledger / Pattern Ledger / Coherence Monitor untouched). No `brain/ui/session.py` edit. No persistence / autosave / DB schema edits. No `.claude/` edits. No `scenarios/`, `traces/`, or `lean_reference/` edits. | All categories present, all exclusions hold. | works | Two narrow carve-outs (`tui_smoke.py`, `llm_runtime_tick_seam.py`) are audited in the Fixture Carve-out Audit section. |
| M-FAM3-A | Does default config yield OFFLINE with no cache wrap? | `parse_llm_runtime_args([], {})` then `build_llm_client_from_config(...)`. | `mode=offline`, `enable_cache=False`. Factory returns an `OfflineStandInClient` instance. | OFFLINE / `enable_cache=False` / `OfflineStandInClient`. | works | Drives I-LLMTOG-01 and I-LLMCACHE-02 default-off-for-non-model-backed. |
| M-FAM3-B | Does `--llm-mode anthropic-api` flip enable_cache on by default? | `parse_llm_runtime_args(["--llm-mode", "anthropic-api", "--llm-anthropic-api-key", "sk-FAKE"], {})` then factory. Same shape exercised with `BRAIN_LLM_MODE=claude-cli` env override. | `enable_cache=True`; factory returns `CachedClient` wrapping `AnthropicAPIClient`. Env override yields `mode=claude-cli`, `enable_cache=True`. | enable_cache flips to True for explicit model-backed; factory wraps in `CachedClient`. | works | Drives I-LLMCACHE-02. |
| M-FAM3-C | Does `--llm-disable-cache` force enable_cache off for model-backed? | `parse_llm_runtime_args(["--llm-mode","anthropic-api","--llm-anthropic-api-key","sk-FAKE","--llm-disable-cache"], {})` then factory. | `enable_cache=False`; factory returns a bare `AnthropicAPIClient` (no `CachedClient` wrap). | enable_cache False; no `CachedClient`. | works | Drives I-LLMCACHE-03. |
| M-FAM3-D | Do both `--llm-enable-cache` and `--llm-disable-cache` raise? | Pass both flags to the parser. | `LlmRuntimeError`: `--llm-enable-cache and --llm-disable-cache are mutually exclusive`. | bounded `LlmRuntimeError` naming both flags. | works | Drives I-LLMCACHE-03's conflict branch. |
| M-FAM3-E | Does `--llm-enable-cache` reject for OFFLINE? | Parser default mode is OFFLINE; pass `--llm-enable-cache`; then attempt `build_llm_client_from_config(LlmRuntimeConfig(mode=OFFLINE, enable_cache=True))`. | Parser keeps `enable_cache=True` (the parser's mode-gated branch only flips defaults for explicit model-backed modes; it does not strip the flag for OFFLINE/MOCK). Factory then raises `LlmRuntimeError: --llm-enable-cache is not supported for mode 'offline'; caching deterministic clients adds no value`. | factory rejects; parser preserves operator-supplied flag for diagnostic clarity. | awkward | Catalog row I-LLMCACHE-04 enumerates the **factory** rejection. The parser's preservation of the user-supplied `--llm-enable-cache` for OFFLINE is a documented diagnostic surface: it reaches the factory, which rejects it cleanly. See Findings F-04 (UX/readability) below; not a blocker. |
| M-FAM3-F | Does MOCK + `enable_cache=True` (direct config) reject? | `build_llm_client_from_config(LlmRuntimeConfig(mode=MOCK, enable_cache=True, mock_responses=("PRESERVE",)))`. | `LlmRuntimeError: --llm-enable-cache is not supported for mode 'mock'; ...`. | factory rejects naming MOCK. | works | Drives I-LLMCACHE-04. |
| M-FAM3-G | Is `--llm-disable-cache` accepted as a no-op for OFFLINE? | `parse_llm_runtime_args(["--llm-disable-cache"], {})` then factory. | `mode=OFFLINE`, `enable_cache=False`; factory returns `OfflineStandInClient`. | no-op; OFFLINE remains the deterministic stand-in. | works | Drives I-LLMCACHE-04. |
| M-FAM3-H | Is `--llm-disable-cache` accepted as a no-op for MOCK? | `parse_llm_runtime_args(["--llm-mode","mock","--llm-mock-response","PRESERVE","--llm-disable-cache"], {})` then factory. | `mode=MOCK`, `enable_cache=False`; factory returns `MockClient`. | no-op; MOCK remains the deterministic mock. | works | Drives I-LLMCACHE-04. |
| M-FAM3-CONSTR | What is the cache default of the bare constructor? | `LlmRuntimeConfig(mode=ANTHROPIC_API, api_key="sk-fake")` constructed directly. | `enable_cache=False`. | False — cache default is parser/runtime-entrypoint policy, not constructor policy. | works (documented) | The Step 5 plan implements LOCK B at the parser. Catalog row I-LLMCACHE-02 explicitly checks `parse_llm_runtime_args(...)` and `build_llm_client_from_config(...)`, not the bare constructor. This is consistent. See Findings F-04. |
| M-FAM4-L1 | Does L1 short-circuit a second identical prompt? | `CachedClient(CountingClient, cache_dir=/tmp/.../m4)`, `tracer=MemoryTracer()`. Two identical `eval_consistency("identical")` calls. | `inner.calls == 1`. `cache.hit_count == 1`, `cache.miss_count == 1`. Exactly one `<sha256>.json` file with keys `["prompt", "response"]`. Trace event types: `["llm.cache_miss", "llm.cache_hit"]`. Both returned strings equal `"PRESERVE"`. | one inner call; cache file present; miss then hit. | works | Drives I-LLMCACHE-05 / I-LLMCACHE-14 (L1 hit path does not call inner). |
| M-FAM5-L2REUSE | Does L2 collapse same MSI ctx + same `new_text` under different `new_id` to one inner call? | Build two `LLMBackedPtCns` over the same MSI ctx + same `new_text`. First evaluates `content_id="new_a"`, second evaluates `content_id="new_b"`. Same `CachedClient(CountingClient)` underneath. L2 dir is a tempdir. | `CountingClient.calls == 1` across both evaluations. Two L2 entries observed -> exactly one (filename hex-key shared). Tracer for the first instance records `[semantic_cache_miss, llm.request, llm.response, parse.success, semantic_cache_store]`. Tracer for the second instance records exactly `[semantic_cache_hit]`. The first rendered prompt contains `new_a` and does NOT contain `new_b` (the actual evaluated content ID is still in the prompt; LOCK E confirmed: `new_id` is in the prompt but excluded from the key). | one inner call across both; second is L2 hit; first miss carries the actual evaluated id; second hit's trace records the new content id and a key prefix only. | works | Drives I-LLMCACHE-06 / I-LLMCACHE-07 / I-LLMCACHE-08 / I-LLMCACHE-14. |
| M-FAM6-CTX | Does a different existing MSI context produce a distinct L2 entry? | Same `new_text` and `new_id="new_x"`. Anchor text `"anchor a description"` vs `"anchor a DIFFERENT description"`. Two `LLMBackedPtCns` instances. | `inner.calls == 2`. Two L2 files with distinct hex names. | distinct L2 keys; both inner calls realized. | works | Drives I-LLMCACHE-08 / I-LLMCACHE-15. Confirms that legitimate semantic-context change does not falsely collapse. |
| M-FAM7-PARSE-FAIL | Do retries-exhaust without writing an L2 success entry? | `MockClient(["xxx","yyy","zzz"])` wrapped in `CachedClient`. One `eval(content_id)`. | `ValueError` raised with the I-LLM-01 wording. Zero L2 entries after the call. Exactly one `llm.semantic_cache_skip` event whose payload keys are `{content_id, key_prefix, reason}` with `reason="parse_failure"`. | no L2 entry; bounded skip event with `reason=parse_failure`; the I-LLM-01 retry contract is intact. | works | Drives I-LLMCACHE-09. |
| M-FAM7-RETRY-OK | Does retry-then-success write exactly one L2 success entry? | `MockClient(["nonsense","PRESERVE"])` wrapped in `CachedClient`. One `eval(content_id)`. | Evaluation returns `PRESERVE`. Exactly one L2 success entry with file payload keys `{key_prefix, parsed}` and `parsed == "PRESERVE"`. No bad raw response is in the L2 file. | one entry, parse-success only, no error/raw text in L2 payload. | works | Drives I-LLMCACHE-09. L1 may still cache the raw bad response under the original-prompt hash; this is documented transport behavior and is unchanged from v0.16 (see Findings F-01). |
| M-FAM8-CORRUPT | Does a corrupt L2 entry fail loud without calling inner? | Compute the canonical L2 key for the scenario via `_canonical_l2_key(...)`. Write `{ this is not valid json` to `<key>.json` under the L2 tempdir. Then call `eval(content_id)`. Repeat with a wrong key set `{"foo":"bar"}`. | First call raises `RuntimeError` whose message contains `"corrupt"`. `CountingClient.calls` is unchanged before vs after (no silent inner repair call). The wrong-key-set variant also raises `RuntimeError` containing `"corrupt"`. | both corruption shapes raise; inner client is never called. | works | Drives I-LLMCACHE-10 for L2. L1 corrupt-cache behavior is preserved from the v0.16 `CachedClient` (raises `RuntimeError` mentioning the cache path); not re-measured because v0.16 behavior is unchanged. |
| M-FAM9-CAP | Does the L2 cap stop writes without blocking hits or hiding inner calls? | Monkeypatch `SEMANTIC_CACHE_MAX_ENTRIES = 2`. Three distinct misses (different `new_text` values), then a fourth miss, then reuse the first prompt. | After three distinct misses, L2 has 2 files (cap honored from the third miss onward). The fourth distinct miss: `CountingClient.calls` delta is 1 (inner still called in explicit model-backed mode), L2 file count stays at 2, and the tracer captures `llm.semantic_cache_skip` with `reason="capacity"`. The reuse-an-old-key call: `CountingClient.calls` delta is 0 and the tracer records `llm.semantic_cache_hit`. | at cap, hits read; misses may call inner; no new entry; bounded skip with `reason=capacity`. | works | Drives I-LLMCACHE-11. The probe uses a small cap to make the property testable in seconds; the production cap is 1024. |
| M-FAM10-TRACE | Do trace events carry only bounded, sanitized payloads? | `MemoryTracer` for both L1 (passed to `CachedClient`) and L2 (passed to `LLMBackedPtCns`). Two same-text/different-id evaluations. | Observed event types: `llm.cache_miss`, `llm.cache_hit` (L1); `llm.semantic_cache_miss`, `llm.semantic_cache_store`, `llm.semantic_cache_hit`, `llm.semantic_cache_skip` (L2). No cache-event payload contains any of `{prompt, response, raw, error, secret, api_key, headers, full_key}`. No cache-event payload string value contains the prompt template snippet `"consistency-preserving"` or the anchor text fixture. L2 `semantic_cache_hit` payload keys: `{content_id, key_prefix}`. `key_prefix` length is exactly 8. L1 `cache_hit` payload key set: `{cache_key_prefix}` per the existing v0.16 schema. | all event types present; no leakage; key_prefix length is 8. | works | Drives I-LLMCACHE-13. |
| M-FAM11-IGNORE | Is the L2 cache directory gitignored, and are L2 entries minimal? | Read `.gitignore`; inspect `SEMANTIC_CACHE_DIR`; write one parse-success and verify the file payload. | `.gitignore` line 28 contains `brain/.llm_cache/`. `SEMANTIC_CACHE_DIR == Path("brain/.llm_cache/eval_v1")`, which is under the ignored root and is therefore implicitly ignored. The probe never wrote a file under that real directory (all writes were under tempdirs). The simulated L2 entry produced by the probe has JSON keys exactly `{"key_prefix", "parsed"}` and contains no `prompt`, `response`, `raw`, `error`, `trace`, `headers`, `consistency-preserving` template snippet, or anchor-text body. Version constants present: `cache_schema='llm-semantic-cache-v1'`, `prompt='prompt-template-v1'`, `parse='consistency-eval-v1'`. | gitignored; minimal payload; no raw text. | works | Drives I-LLMCACHE-12 / I-LLMCACHE-07 / I-LLMCACHE-17. |
| M-FAM12-TICK | Does `tick(...)` produce identical `(new_state, TickRecord)` for cached vs uncached client with the same response? | Build a deterministic initial `BrainState` (cogito+alpha) and a single `PerceptEvent("beta", "beta probe", ...)`. Call `tick(state, [event], CountingClient("PRESERVE"))`. Independently call `tick(state, [event], CachedClient(CountingClient("PRESERVE"), cache_dir=/tmp/.../l1))`. Compare structured views (profile values + domain, MSI contents + threshold, ptcns eval map, registry texts, tick_index, mode_trace, triggered_mode, boundary, notes). | `state_view(new_state_u) == state_view(new_state_c)`. `record_view(record_u) == record_view(record_c)`. `git diff origin/main -- brain/tick.py` is empty. | bit-for-bit parity at the kernel boundary; `brain/tick.py` unchanged. | works | Drives I-LLMCACHE-01 / I-LLMCACHE-16 along the probe's direct call path. Catalog row I-LLMCACHE-16 also has a fixture (`brain/ui/fixtures/llm_cache_no_tick_change.py`) that gates this property in the runner. |

## Step 3 vs Step 8 Comparison

The Step 3 probe (commit `cc24cca`) characterized M1..M9 against the
pre-implementation runtime. The same shapes are re-stated against the
post-Step-7 runtime here:

- **L0 (per-instance LLMBackedPtCns._cache):** still per-instance.
  Each `tick(...)` constructs a fresh `LLMBackedPtCns` (M1 unchanged).
  Across-tick reuse is delegated to L1 + L2. M-FAM12-TICK confirms
  cached-vs-uncached tick parity.
- **L1 default policy (Step 3 M2):** previously, model-backed modes
  required explicit `--llm-enable-cache`. Post-Step-7 (M-FAM3-B), the
  parser flips `enable_cache=True` by default once the operator
  explicitly selects a model-backed mode. `--llm-disable-cache`
  (M-FAM3-C) is the explicit opt-out. Conflict (M-FAM3-D) raises a
  bounded `LlmRuntimeError`.
- **L1 same-prompt cache (Step 3 M3):** byte-identical prompts still
  hit L1 with one inner call across two evaluations (M-FAM4-L1).
  Unchanged.
- **Same-text/different-content-id (Step 3 M4):** previously caused L1
  prompt-hash misses. Post-Step-7 (M-FAM5-L2REUSE), L2 collapses both
  evaluations to one inner call by keying on the seven-tuple that
  excludes `new_id`; the rendered prompt still carries the actual
  evaluated content id.
- **Different-MSI-context (Step 3 M5):** prompts still differ for the
  legitimate semantic reason. Post-Step-7 (M-FAM6-CTX), L2 keys are
  distinct, no false hit occurs, and both inner calls are realized.
- **Retry/parse-failure (Step 3 M6):** L1 still caches raw bad
  responses under the original-prompt hash (transport-level behavior
  unchanged from v0.16). L2 (M-FAM7-PARSE-FAIL / M-FAM7-RETRY-OK) only
  stores parse-success entries; retries-exhausted emits a bounded
  `semantic_cache_skip` with `reason=parse_failure`; no L2 success
  entry is written for failures.
- **OFFLINE/MOCK isolation (Step 3 M7):** factory rejection of
  `--llm-enable-cache` for OFFLINE/MOCK is preserved (M-FAM3-E,
  M-FAM3-F). `--llm-disable-cache` is accepted as a no-op (M-FAM3-G,
  M-FAM3-H) without unlocking cache access. The construction-time L2
  metadata derivation (`_derive_l2_metadata`) returns `None` whenever
  the wrapping client is not a `CachedClient`, so OFFLINE/MOCK never
  reach the L2 lookup/write paths even if such a client is constructed
  directly.
- **L1 trace events (Step 3 M8):** `llm.cache_hit` / `llm.cache_miss`
  preserved. L2 adds `llm.semantic_cache_hit` / `_miss` / `_store` /
  `_skip` with bounded payloads (M-FAM10-TRACE).
- **L1 file format (Step 3 M9):** unchanged — `{prompt, response}` per
  v0.16 transport contract. L2 files store exactly
  `{key_prefix, parsed}` (M-FAM11-IGNORE), reducing the on-disk
  sensitivity surface vs L1.

New post-Step-7 properties not covered by Step 3:

- L2 corruption fails loud without calling inner (M-FAM8-CORRUPT).
- L2 cap is honored without hidden repair (M-FAM9-CAP).
- Cached-vs-uncached `tick(...)` produces field-for-field equal
  `(new_state, TickRecord)` for the same client responses
  (M-FAM12-TICK).

## Event / Trace Observability

Observed event names and sample sanitized payload shapes — no raw
prompt body, no raw response body, no full L2 key, no secret:

L1 (`brain.llm.client.CachedClient`):

- `llm.cache_miss` → payload `{cache_key_prefix: "<8 hex>"}` (existing
  v0.16 shape).
- `llm.cache_hit` → payload `{cache_key_prefix: "<8 hex>"}`.

L2 (`brain.llm.ptcns_backed.LLMBackedPtCns`):

- `llm.semantic_cache_miss` → payload `{content_id, key_prefix}` where
  `key_prefix` is 8 hex chars.
- `llm.semantic_cache_store` → payload `{content_id, key_prefix}`.
- `llm.semantic_cache_hit` → payload `{content_id, key_prefix}`.
- `llm.semantic_cache_skip` → payload `{content_id, key_prefix,
  reason}` where `reason` is one of `"parse_failure"` (observed,
  M-FAM7-PARSE-FAIL) or `"capacity"` (observed, M-FAM9-CAP).

Reachable `reason` values observed during the probe: `"parse_failure"`,
`"capacity"`. The Step 5 plan also lists `"disabled"` and
`"offline_or_mock"` as enumerated values; these are not emitted by the
v1 implementation because OFFLINE/MOCK and the disabled-cache path
short-circuit before reaching L2 (the L2 surface is gated by
`_l2_metadata is None`). See Findings F-05.

No cache event payload observed during the probe contained any of
`{prompt, response, raw, error, secret, api_key, headers, full_key}`.
No payload string contained the prompt template snippet
`"consistency-preserving"` or the anchor text body used in the probe
scenarios.

## Sensitive Artifact Verification

- L1 cache files (`brain/.llm_cache/<sha256>.json`) still store
  `{prompt, response}` verbatim per the existing v0.16 transport
  contract. They are sensitive local artifacts.
- L2 cache files (`brain/.llm_cache/eval_v1/<sha256>.json`) store
  exactly `{key_prefix, parsed}` per LOCK D / I-LLMCACHE-12. No prompt
  text, no response text, no error text, no provider metadata.
- All cache directories used during measurement were under
  `tempfile.TemporaryDirectory()` paths in `/tmp/`. The probe never
  wrote a file under `brain/.llm_cache/eval_v1/`.
- `.gitignore` line 28 covers `brain/.llm_cache/`, which transitively
  covers `brain/.llm_cache/eval_v1/`.
- No raw prompt body, no raw model response body, and no L2 file
  contents are quoted in this report. Cache key prefixes when shown
  are 8-char hex only.
- No file under `brain/.llm_cache/**` is tracked by git
  (`git ls-files brain/.llm_cache` returns no output).
- The Stage A advisor question file (`/tmp/toyi_phase314_step8_advisor_question.md`)
  and answer file (`/tmp/toyi_phase314_step8_advisor_answer.md`) are
  not committed; only the bounded hash-only JSONL log under
  `.claude/codex_bridge_logs/` (which itself is gitignored) records
  bridge usage.

## Fixture Carve-out Audit

Step 7 included two narrow fixture-side changes that are not new cache
implementation but unblock the existing audit fixtures against the new
default-on cache surface. Both are independently audited here.

### Carve-out 1 — `brain/ui/fixtures/tui_smoke.py`

What changed:

1. The `I-UI-07` forbidden-builtin-call audit (the AST walk that
   rejects `exec(...)`, `eval(...)`, `compile(...)`,
   `__import__(...)`) was narrowed from "any `ast.Call` whose `.func`
   has an `attr` or `id` in the forbidden set" to "any `ast.Call`
   whose `.func` is an `ast.Name` whose `id` is in the forbidden set".
   The motivation is that the Phase 3.14 LLM cache fixtures call
   `LLMBackedPtCns.eval(content_id)` (a method named `eval`), which
   would otherwise be false-flagged. The Python builtins `exec`,
   `eval`, `compile`, and `__import__` are only ever invoked by bare
   name (not via `obj.eval(...)`), so this narrowing does not loosen
   the audit's stated intent.

2. The persistence-fixture tempfile exemption — previously matching
   `path.name.startswith("persistence_")` or `"autosave_"` — now also
   matches `path.name.startswith("llm_cache_")`. The Phase 3.14 LLM
   cache fixtures use `tempfile.TemporaryDirectory()` to isolate L1 /
   L2 cache writes from `brain/.llm_cache/`.

Why it changed: blocking contradiction between the prior audit and the
new Step 7 fixtures. Without (1), `LLMBackedPtCns.eval(content_id)`
calls inside the new fixtures would trip `I-UI-07` as a
forbidden-builtin-call. Without (2), the new fixtures could not open a
temp dir to isolate their cache writes, and would have to write under
`brain/.llm_cache/eval_v1/` directly (which would violate the
sensitive-artifact policy of LOCK L / I-LLMCACHE-12).

Narrowness:

- (1) restricts the audit to `ast.Call` with `func` an `ast.Name`. Any
  attribute-style call to a forbidden function is unaffected — but no
  such call exists as a legitimate Python builtin invocation, because
  `exec`, `eval`, `compile`, and `__import__` are not methods on
  anything in the standard library. The change is therefore a
  false-positive correction, not a real loosening.
- (2) adds exactly one filename prefix (`"llm_cache_"`) to the
  pre-existing exemption shape. It does not allow `tempfile` to leak
  outside fixture files. It does not affect any runtime UI module.

Runtime-behavior impact: none. Both changes affect a fixture-internal
audit only. Runner gates remain green.

Follow-up: none required for Phase 3.14. A future tightening could
move the audit AST shape into a single declarative rule; this is a
catalog-debt note rather than a Phase 3.14 obligation.

Blocker: no.

Verdict: **justified**, narrow, no runtime impact, no follow-up
blocker.

### Carve-out 2 — `brain/ui/fixtures/llm_runtime_tick_seam.py`

What changed: an `_unwrap_for_test(client)` helper that returns
`client._inner` if `isinstance(client, CachedClient)` and the client
itself otherwise. Each of the three `isinstance(...)` assertions in
`check_I_LLMTOG_09_tick_seam` (OFFLINE → `OfflineStandInClient`,
MOCK → `MockClient`, CODEX_CLI → `CodexCLIClient`) is now passed
through `_unwrap_for_test(...)` first.

Why it changed: blocking contradiction. Post-Step-7, the runtime
parser flips `enable_cache=True` by default for the explicit
model-backed mode `codex-cli`. The factory therefore returns
`CachedClient(CodexCLIClient(...))`, not a bare `CodexCLIClient`.
Without the unwrap, the `I-LLMTOG-09` assertion `isinstance(client,
CodexCLIClient)` would fail.

Narrowness:

- The unwrap only peels one layer (`CachedClient` -> inner). It does
  not silently descend through arbitrary wrappers, only through the
  one transport-cache wrapper introduced by Phase 3.14's default-on
  policy.
- The other two branches (OFFLINE, MOCK) are unaffected because
  OFFLINE / MOCK are factory-rejected from caching; the unwrap is a
  no-op there.
- The AST-audit portion of `I-LLMTOG-09` (every `run_curses(...)` call
  passes the named local `client`) is unchanged.

Runtime-behavior impact: none. The fixture is a fixture; it makes no
runtime promises. The fixture's intent — "mode selection drives
transport type" — is preserved: the assertion still checks that the
operator-selected transport is `CodexCLIClient`; whether it is wrapped
in `CachedClient` is governed by the separate I-LLMCACHE-02 default
policy, not by I-LLMTOG-09.

Follow-up: the existing `I-LLMTOG-03` row should be re-read alongside
I-LLMCACHE-02 to confirm there is no remaining ambiguity about which
row owns the "factory returns a CachedClient wrap" property. Today
I-LLMTOG-03's catalog description already says "or CachedClient
wrapping the backend when caching is enabled", so the two rows are
consistent.

Blocker: no.

Verdict: **justified**, narrow, no runtime impact, no follow-up
blocker.

## Findings Classification

| Finding | Severity | Category | Description | Evidence | Recommendation | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| F-01 | Low | deferred enhancement | L1 still caches raw bad responses under the original-prompt hash because L1 is a transport-layer cache that stores whatever the model returned. A future identical-input run would replay the bad response and re-trigger the retry shell until the parser succeeds (or exhausts retries). | Step 3 M6, post-Step-7 unchanged by design under LOCK F. | Defer to a follow-up campaign or to I-LLMCACHE-20's eventual L1 bounding / eviction work. Documented today as a transport-cache property, not a Phase 3.14 regression. | no |
| F-02 | Low | deferred enhancement | I-LLMCACHE-20 (L1 cache bounding / eviction policy) remains DEFERRED in v1. L1 disk growth is therefore unbounded over long-running model-backed sessions. | Catalog row I-LLMCACHE-20; Step 5 L1 Bound Policy section; LOCK I rationale. | Carry forward as a Phase 3.15+ candidate row family. | no |
| F-03 | Low | deferred enhancement | I-LLMCACHE-21 (real external model-backed ORS smoke with cache enabled) and I-LLMCACHE-22 (end-to-end behavior runner) are NOT-EXERCISED in v1. Step 8 exercises the end-to-end property along the deterministic local-client route only. | Catalog rows I-LLMCACHE-21 / I-LLMCACHE-22; this report's Method section. | A future campaign may promote these from NOT-EXERCISED if real-LLM smoke gains explicit operator sponsorship; the existing Stage A / Stage B bridges are advisory / limited-write channels, not runtime LLM seams. | no |
| F-04 | Low | UX/readability | The cache-default policy lives in two surfaces: (a) the parser flips `enable_cache=True` for explicit model-backed modes; (b) the bare `LlmRuntimeConfig(...)` constructor still defaults `enable_cache=False`. A reader who builds a `LlmRuntimeConfig` by hand may be surprised. The factory does not auto-flip the default, which is also correct under LOCK B (parser owns the default). Similarly, the parser preserves `--llm-enable-cache` for OFFLINE/MOCK so the factory can reject it cleanly (M-FAM3-E); a future reader may misread this as a "silent ignore" until they see the factory error path. | M-FAM3-CONSTR, M-FAM3-E in this report. | Optionally document the "default lives in the parser" rule in the next maintenance pass on `brain/ui/llm_runtime.py` and/or in `INVARIANT_CATALOG.md` row I-LLMCACHE-02's description (already cites `parse_llm_runtime_args` explicitly). No code change required. | no |
| F-05 | Low | documentation | The Step 5 observability plan enumerates `reason` values `{"parse_failure", "capacity", "disabled", "offline_or_mock"}` for `llm.semantic_cache_skip`. The v1 implementation only emits `"parse_failure"` and `"capacity"`; `"disabled"` and `"offline_or_mock"` are unreachable because the L2 surface is short-circuited at `_l2_metadata is None`. Catalog row I-LLMCACHE-13 already constrains the payload to a `reason` field without requiring all enumerated values be emitted, so this is a planning-vs-implementation note, not a regression. | M-FAM10-TRACE; `_l2_metadata` short-circuit in `brain/llm/ptcns_backed.py`. | Carry forward as documentation in Step 9 findings; no code or catalog change required for Phase 3.14. | no |
| F-06 | Low | UX/readability | The two fixture carve-outs (`tui_smoke.py`, `llm_runtime_tick_seam.py`) were necessary to keep the runner green after Step 7's default-on policy and the new fixtures' method-name overlap with the `eval` builtin. Both are narrow and inline-documented; a less inline-documented carve-out could become invisible drift over time. | Fixture Carve-out Audit section. | Step 9 should explicitly list these as resolved blocking-contradictions and recommend that future cache work re-audits the I-UI-07 builtin-call narrowing if any new fixture introduces method names matching Python builtins. | no |
| F-07 | Low | safety/invariant (confirmed) | `brain/tick.py` is unchanged. For the measured identical-event scenario, cached vs uncached `tick(...)` produces field-for-field equal `(new_state, TickRecord)` for the same client responses (M-FAM12-TICK). The runner-level property over the full event space is gated by catalog row I-LLMCACHE-16's fixture (`llm_cache_no_tick_change.py`), not by this Step 8 probe. | M-FAM12-TICK; `git diff origin/main -- brain/tick.py` is empty. | None. Confirms LOCK N along the measured route. | no |
| F-08 | Low | safety/invariant (confirmed) | The L2 entry on-disk payload is exactly `{"key_prefix", "parsed"}`. No raw prompt, raw response, error text, full key, or provider metadata is persisted to L2. L2 cache directory is under the gitignored `brain/.llm_cache/` root. No file in `brain/.llm_cache/**` is tracked. | M-FAM11-IGNORE. | None. Confirms LOCK L / I-LLMCACHE-12. | no |
| F-09 | Low | no issue | Corrupt L2 entries (truncated JSON, wrong key set) fail loud with a bounded `RuntimeError` containing `"corrupt"` and do not call the inner client. | M-FAM8-CORRUPT. | None. Confirms LOCK G / I-LLMCACHE-10. | no |
| F-10 | Low | no issue | Capacity behavior preserves hits, allows misses to call inner in explicit model-backed mode, does not write new entries at cap, and emits a bounded `semantic_cache_skip` with `reason="capacity"`. No eviction / pruning fires in v1. | M-FAM9-CAP. | None. Confirms LOCK I / I-LLMCACHE-11. | no |

There are zero blocking-severity findings. All findings are
documentation-level or planned deferrals.

## Not Established By This Report

The following properties are **outside** what this Step 8 measurement
pass establishes. They are noted explicitly so Step 9 / Step 10 do not
overclaim from Step 8 evidence:

- Real external model-backed cache behavior against
  `AnthropicAPIClient`, `ClaudeCLIClient`, or `CodexCLIClient` is
  **not** measured. Factory selection wraps the model-backed transport
  in `CachedClient` when `enable_cache` is on (M-FAM3-B); real
  provider call paths remain NOT-EXERCISED per I-LLMCACHE-21.
- L1 disk growth bound, eviction, and concurrent-write atomicity are
  **not** established. L1 bounding is DEFERRED under I-LLMCACHE-20.
- Production L2 capacity behavior at the actual cap (1024) is **not**
  stress-measured. The probe simulates the cap branch under a
  monkeypatched value of 2; the cap branch is shown to honor the cap,
  emit `semantic_cache_skip(reason="capacity")`, and allow inner
  calls in explicit model-backed mode. Real-world 1024-entry stress
  is out of scope for v1.
- Cached-vs-uncached `tick(...)` parity is established for **one**
  identical-event scenario (M-FAM12-TICK). It is not a universal
  proof that caching cannot affect every possible tick path. The
  runner-level guarantee comes from the fixture
  `brain/ui/fixtures/llm_cache_no_tick_change.py` (I-LLMCACHE-16),
  which gates this property at every catalog runner pass; this report
  cross-references that fixture but does not re-derive its full
  property space.
- Parse-failure / retry behavior is measured for two narrow shapes:
  exhausted retries (M-FAM7-PARSE-FAIL) and retry-then-success
  (M-FAM7-RETRY-OK). Concurrent failure-and-store interleavings,
  partial-write recovery, and parser-version migration paths are not
  measured.
- Corrupt-cache recovery / operator remediation paths are not
  exercised. The implementation fails loud (M-FAM8-CORRUPT); operator
  remediation is "delete the offending file under
  `brain/.llm_cache/eval_v1/`" and is not a runtime self-heal.
- Observability leakage was checked against the **measured** cache
  events emitted in this probe. Future trace surfaces (new tracer
  back-ends, FileTracer JSONL files, raised-exception messages, log
  output) must remain bounded; the existing `MemoryTracer`-shape
  check does not transitively cover them.

## Stage A and Stage B Disclosure

Stage A ChatGPT/Codex consultation:

- used: yes
- mode: review
- model: gpt-5.5
- effort: medium
- wrapper command: `python3 tools/claude_helpers/codex_chatgpt_subagent.py
  --mode review --model gpt-5.5 --effort medium --timeout 180
  --prompt-file /tmp/toyi_phase314_step8_advisor_question.md
  > /tmp/toyi_phase314_step8_advisor_answer.md`
- question file: `/tmp/toyi_phase314_step8_advisor_question.md`
- answer file: `/tmp/toyi_phase314_step8_advisor_answer.md`
- wrapper status: exit_code=0, status="success",
  codex_returncode=0, error_class=null, duration_ms≈36019,
  truncated=false; bounded JSONL audit log under
  `.claude/codex_bridge_logs/` (gitignored).
- accepted advice: added an explicit **Not Established By This
  Report** section enumerating what the deterministic local-client
  route does **not** prove (real provider behavior, L1 disk growth,
  production-cap stress, universal tick-semantics, concurrent
  failure interleavings, future trace-surface leakage); reframed
  the report's scope discipline in the Purpose section as
  "deterministic local-client only"; softened the F-07 / M-FAM12
  wording to "measured identical-event scenario" rather than a
  universal claim, and referenced the runner-level fixture
  `llm_cache_no_tick_change.py` as the catalog-level gate; kept the
  fixture carve-out audit narrow and labeled the two changes as
  inherited Step 7 blocking-contradiction fixes; tightened F-04
  parser-vs-constructor wording; clarified that F-05's
  Step-5-plan-enumerated `reason` values `"disabled"` and
  `"offline_or_mock"` are unreachable in v1 because the L2 surface
  is gated at `_l2_metadata is None`.
- rejected advice: did not add a Step 8 catalog row change; did not
  run a real external LLM smoke (`I-LLMCACHE-21` stays NOT-EXERCISED);
  did not introduce new fixtures (Step 8 is documentation-only); did
  not adopt the advisor's literal validation command list verbatim
  (e.g., `tools/check_lean_citations`, `tools/invariant_runner --all`
  do not exist in this repo) — the canonical five gates listed in
  Step 8's Method / Post-Write Validation use the repo's actual
  commands.
- reason: Step 8 is a behavior report. Stage A is the required
  adversarial reviewer for the report draft.

Stage B limited-write collaboration:

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
- reason: this report cross-references twelve measurement families,
  twenty-two catalog rows, two fixture carve-out audits, and a Step 3
  vs Step 8 comparison. A single-shot Stage B writer call would be
  high-risk for accurate row citation. The Step 8 spec explicitly
  permits drafting manually when Stage B is judged unreliable for the
  given scope; parent Claude drafted the file directly and Stage A
  reviewed the draft.
