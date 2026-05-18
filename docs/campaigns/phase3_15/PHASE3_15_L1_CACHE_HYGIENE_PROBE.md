# Phase 3.15 L1 Cache Hygiene Behavior Probe

## Purpose

Step 3 produces a deterministic, repo-local reproduction of L1
transport-cache behavior as it exists on `main` at catalog `v0.24`,
covering the measurement matrix the Step 2 synthesis enumerated. The
report grounds Step 4 LOCK A..L decisions in observed numbers rather
than by-eye intuition. No real external LLM calls. No raw prompt or
response contents are recorded.

## Reproduction harness

A throwaway harness lives at `/tmp/phase3_15_probe.py` (not
committed). It uses `brain.llm.client.MockClient`, the existing
`CachedClient`, and the existing `brain.ui.llm_runtime` parser /
factory. Every cache directory is a fresh `tempfile.mkdtemp(...)`
under `/tmp`; no measurement writes to `brain/.llm_cache`. The
harness loads `brain.llm.parse.parse_consistency_eval` and a local
`RecordingTracer` that satisfies the `CognitionTracer` event shape.

Invocation:

```
python3 /tmp/phase3_15_probe.py > /tmp/phase3_15_probe_results.json
```

Exit code was `0`. Raw JSON output lives at
`/tmp/phase3_15_probe_results.json` and is reproduced selectively in
the tables below; no raw prompt / response values appear.

## M1. Baseline (no cache wrapper)

Using `MockClient` directly with canned responses
`["PRESERVE", "DAMAGE", "NEUTRAL"]` and three calls to
`eval_consistency("prompt-a")`:

| field             | value                                |
| ----------------- | ------------------------------------ |
| inner_calls       | 3                                    |
| distinct_responses| `["DAMAGE", "NEUTRAL", "PRESERVE"]`  |

Each call advances the canned-response iterator; identical prompts
do not short-circuit because there is no cache. This is the control.

## M2. Cached hit/miss with `CachedClient`

Same client wrapped in `CachedClient(inner, cache_dir=<tmp>)`; three
calls to `eval_consistency("prompt-x")`:

| field        | value |
| ------------ | ----- |
| miss_count   | 1     |
| hit_count    | 2     |
| inner_calls  | 1     |
| responses_match | true |

`llm.cache_miss` fires once with payload keys `["cache_key_prefix"]`;
`llm.cache_hit` fires twice with the same payload key. Identical
prompts collapse to one inner call.

## M3. File / byte growth across a synthetic prompt stream

`n` unique prompts written into a fresh cache directory; one
`CachedClient` instance per row; canned response stream is
`["PRESERVE"] * n` so every prompt is a miss:

| n unique prompts | files at end | total bytes | min / median / max per file |
| ---------------- | ------------ | ----------- | --------------------------- |
| 1                | 1            | 52          | 52 / 52 / 52                |
| 100              | 100          | 5,290       | 52 / 53 / 53                |
| 1,024            | 1,024        | 55,210      | 52 / 54 / 55                |
| 1,025            | 1,025        | 55,265      | 52 / 54 / 55                |
| 2,048            | 2,048        | 111,530     | 52 / 55 / 55                |

Observations:

- File count grows linearly with unique-prompt count. No bound is
  enforced. Crossing `1024` produces a `1025`-th file with no skip
  and no warning.
- Total bytes grows linearly. The trivial harness prompts (`prompt-0`
  through `prompt-2047`) produce 52..55-byte entries each because
  both prompt and response are short canonical tokens. Production
  prompts are far larger (`PROMPT_TEMPLATE` includes MSI context),
  so the per-entry size in production will be considerably greater
  than the harness numbers. Step 4 LOCK A must NOT use the harness
  per-entry byte numbers as a basis for cap selection; the
  measurement here grounds the choice of `L1_CACHE_MAX_ENTRIES` by
  symmetry argument (entries are unbounded today) and explicitly
  defers byte-cap selection (Option B) to a future campaign.
- `hit_count` is zero on every row because each prompt is unique.

## M4. Raw payload shape

Single miss writes a single JSON file. The file's top-level shape
is:

| field          | value                  |
| -------------- | ---------------------- |
| field_count    | 2                      |
| field_names    | `["prompt", "response"]` |
| key_prefix     | `d05a82a4` (8-char digest prefix) |

The on-disk payload is exactly `{"prompt", "response"}`. The
synthesis claim that L1 stores raw prompt + raw response is
confirmed; no other keys are written. Raw values are deliberately
not reproduced here.

## M5. Bad-response replay

Canned response stream `["not a valid eval token", "PRESERVE"]`;
three calls to `eval_consistency("bad-prompt")` through
`CachedClient`:

| field                | value |
| -------------------- | ----- |
| first_response_parses| false |
| responses_identical  | true  |
| inner_calls          | 1     |
| miss_count           | 1     |
| hit_count            | 2     |

The first call misses; `inner` returns the parse-failing string; the
string is written to disk. Subsequent calls hit and return the same
parse-failing string verbatim. `parse_consistency_eval` raises
`ParseError` against the recovered string, confirming the cached
response is truly malformed. **Raw bad-response replay is durable
today.** Phase 3.15 explicitly defers Option E and does not fix this;
Step 9 findings must record this risk as a future-campaign concern.

## M6. Corrupt entry fail-loud

After a successful miss writes a valid entry, the file's contents
are overwritten with non-JSON text. A fresh `CachedClient` over the
same `cache_dir` calls `eval_consistency` for the same prompt:

| field                              | value          |
| ---------------------------------- | -------------- |
| raised                             | `RuntimeError` |
| inner2_calls_after_corrupt_read    | 0              |

Corrupt entries continue to fail loud. The inner client is **not**
called as a silent fall-back. The Phase 3.15 implementation must
preserve this behavior unchanged.

## M7. Simulated count-cap behavior (write-skip-at-cap)

The harness simulates write-skip-at-cap by short-circuiting
`CachedClient.eval_consistency` once `len(cache_dir.glob("*.json")) >= cap`.
At cap, the simulation still calls `inner.eval_consistency` (so the
inner remains the source of truth in explicit model-backed mode) but
does not write a new entry.

| cap   | stream | files at end | simulated_skip_count | simulated_inner_calls_during_skip |
| ----- | ------ | ------------ | -------------------- | --------------------------------- |
| 128   | 200    | 128          | 72                   | 72                                |
| 1,024 | 1,100  | 1,024        | 76                   | 76                                |

Observations:

- The hard bound holds at the chosen cap.
- The number of inner calls during the skip phase equals the number
  of skipped writes, which is consistent with the synthesis acceptance
  criterion "at cap: inner is still called; cache write is skipped".
- No existing entry is removed. Write-skip-at-cap is a bounded
  **admission** policy, not eviction; the Step 4 LOCK B selection
  rule recommendation is supported by the measured behavior.

## M8. Offline / mock isolation

The `build_llm_client_from_config` factory is exercised through
`parse_llm_runtime_args` for three configurations:

| config                                              | mode    | enable_cache | is `CachedClient` |
| --------------------------------------------------- | ------- | ------------ | ----------------- |
| `[]` (default)                                      | offline | false        | no                |
| `--llm-mode mock --llm-mock-response PRESERVE`      | mock    | false        | no                |
| `--llm-mode mock --llm-mock-response PRESERVE --llm-disable-cache` | mock | false | no |

OFFLINE / MOCK never produce a `CachedClient`. `--llm-disable-cache`
is a no-op for MOCK and does not change the factory's behavior. The
factory rejects `--llm-enable-cache` for OFFLINE / MOCK (verified
elsewhere by `I-LLMTOG-08`). Phase 3.15 must preserve this rejection
unchanged.

## M9. Model-backed default-on (Phase 3.14 contract)

Parser-level checks against ANTHROPIC_API / CLAUDE_CLI / CODEX_CLI:

| field                                  | value |
| -------------------------------------- | ----- |
| anthropic_api_default_enable_cache     | true  |
| anthropic_api_disable_wins             | false |
| claude_cli_default_enable_cache        | true  |
| codex_cli_default_enable_cache         | true  |
| conflicting_flags_raise                | true  |

The Phase 3.14 contract holds. `--llm-disable-cache` wins; supplying
both `--llm-enable-cache` and `--llm-disable-cache` raises
`LlmRuntimeError`. Phase 3.15 implementation must not regress this
contract.

## M10. L2 (`eval_v1`) untouched evidence

Direct inspection of constants in `brain/llm/ptcns_backed`:

| field                                | value                            |
| ------------------------------------ | -------------------------------- |
| L2_SEMANTIC_CACHE_MAX_ENTRIES        | 1024                             |
| L2_SEMANTIC_CACHE_DIR                | `brain/.llm_cache/eval_v1`       |
| L2_SEMANTIC_CACHE_SCHEMA_VERSION     | `llm-semantic-cache-v1`          |

These remain the Phase 3.14 values. Phase 3.15 must not touch any of
them.

## M11. Trace event taxonomy

Single miss + single hit through `CachedClient` with a recording
tracer:

| event           | count | payload keys              |
| --------------- | ----- | ------------------------- |
| `llm.cache_hit` | 1     | `["cache_key_prefix"]`    |
| `llm.cache_miss`| 1     | `["cache_key_prefix"]`    |

The current event surface carries only the 8-character
`cache_key_prefix`. Phase 3.15's proposed new event
(`llm.cache_skip` with `reason="capacity"`) is consistent with this
taxonomy: payload limited to bounded identifiers plus a reason
string. No raw prompt or response will leak through the new event.

## Coverage of Step 2 measurement requirements

| Step 2 requirement                                  | covered by         |
| --------------------------------------------------- | ------------------ |
| baseline hit/miss --llm-enable-cache=False          | M1, M8 (OFFLINE)   |
| baseline hit/miss --llm-enable-cache=True           | M2, M9             |
| file count growth                                   | M3                 |
| byte growth                                         | M3                 |
| L1 entry size distribution                          | M3 (min/median/max)|
| raw payload shape (no raw values)                   | M4                 |
| bad-response replay                                 | M5                 |
| corrupt-entry fail-loud                             | M6                 |
| candidate count-cap behavior                        | M7                 |
| candidate write-skip-at-cap                         | M7                 |
| candidate mtime / lexicographic selection           | M7 (deferred; not selected) |
| offline / mock isolation                            | M8                 |
| L2 untouched evidence                               | M10                |
| trace observability                                 | M11                |

## Design-question implications

The probe surfaces and confirms the four design questions the Step 2
synthesis flagged. Each requires an explicit Step 4 LOCK:

1. **Bound shape (Option A vs B vs C).** M3 confirms unbounded
   growth in entry count. Byte-per-entry varies but is small under
   the harness; production entries will be larger. Recommend
   locking on entry-count cap; defer byte cap (Option B) and TTL
   (Option C). Step 4 LOCK A.
2. **Selection rule.** M7 confirms write-skip-at-cap is bounded,
   deterministic, and observable, and that the inner client is
   still called at cap. Step 4 LOCK B.
3. **Bad-response replay.** M5 confirms the existing replay
   behavior is durable. Phase 3.15 defers Option E and must
   document this in Step 9. Step 4 LOCK C.
4. **Observability surface.** M11 confirms current payload shape
   (`cache_key_prefix` only). The proposed new event respects the
   existing taxonomy. Step 4 LOCK E.

## Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: no
- reason: Step 3 is a measurement-first probe; Stage A review is not
  required by `CURRENT_CAMPAIGN.md` for this step.

Stage B limited-write collaboration:
- used: no
- reason: report drafted directly by parent Claude over the JSON
  results from `/tmp/phase3_15_probe.py`; no doc shard was sharded
  out.

Stage C orchestration:
- used: no
- reason: report draft authored directly by parent Claude after
  measurements were produced. Two Stage C transport hiccups in Step 2
  already consumed real-call budget; the operator approved
  auto-retry, but parent Claude declined to spend another budget
  slot on a Step 3 doc shard when the inputs (the harness JSON
  results) were already in context. The remaining Stage C budget is
  reserved for Step 7 implementation.

## Next artifact

Step 4 produces
`docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_CORRIGENDA.md`.
