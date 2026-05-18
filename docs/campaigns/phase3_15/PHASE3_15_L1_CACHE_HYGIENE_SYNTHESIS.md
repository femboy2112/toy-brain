# Phase 3.15 L1 Cache Hygiene Synthesis

## 1. Why Phase 3.15 follows Phase 3.14

Phase 3.14 closed the higher-level LLM cache discipline question:
model-backed runtime modes (ANTHROPIC_API, CLAUDE_CLI, CODEX_CLI) now
default to L1 transport caching on, and a new bounded L2 canonical
semantic evaluation cache (`eval_v1`, capped at
`SEMANTIC_CACHE_MAX_ENTRIES = 1024`) was added inside
`brain/llm/ptcns_backed.py`. The Phase 3.14 audit explicitly recorded
`I-LLMCACHE-20` (L1 cache bounding / eviction policy) as DEFERRED, with
the note that flipping `enable_cache=True` by default activates the
existing v0.16 `CachedClient` against the same gitignored disk surface
(`brain/.llm_cache/<sha256>.json`) without altering L1 semantics. The
Phase 3.14 findings restated that the bound is a future-campaign
concern.

Phase 3.15 is that follow-up. The campaign retires `I-LLMCACHE-20` by
introducing a deterministic, observable bound on the existing L1
transport cache, and re-affirms (rather than expands) the rest of the
Phase 3.14 architecture: offline remains default, model-backed modes
remain explicit opt-in, L2 semantics are unchanged, and
`brain/tick.py` is not edited. `I-LLMCACHE-21` (real external
model-backed cache smoke) and `I-LLMCACHE-22` (end-to-end Phase 3.14
behavior probe) remain NOT-EXERCISED unless Review Gate A explicitly
promotes them.

## 2. Evidence chain

The hygiene problem is visible from the existing public surfaces of
four files. Inspect them in this order; do not include raw cache
contents anywhere in this document or any campaign artifact.

- `brain/llm/client.py :: CachedClient` is the L1 transport cache.
  - Key derivation: `digest = sha256(prompt).hexdigest()`, file path
    `cache_dir / f"{digest}.json"`, `cache_dir` defaults to
    `Path("brain/.llm_cache")`.
  - Hit path: read file, `json.loads(...)`, return `payload["response"]`
    without calling the inner client; increment `hit_count`; emit
    `llm.cache_hit` with `{"cache_key_prefix": digest[:8]}`.
  - Miss path: increment `miss_count`; emit `llm.cache_miss`; call
    `self._inner.eval_consistency(prompt)`; ensure cache dir; write
    `{"prompt": prompt, "response": response}` as JSON with
    `indent=2`; return the response.
  - Failure-loud invariant already exists: corrupt JSON / `KeyError`
    raises `RuntimeError(...)`; no silent fall-back into the inner
    client.
  - Counters: `hit_count` and `miss_count` are public ints on the
    instance.
- `brain/ui/llm_runtime.py :: build_llm_client_from_config` is the
  only seam that wraps an inner client in `CachedClient`.
  - OFFLINE / MOCK reject `--llm-enable-cache` at the factory
    boundary.
  - For ANTHROPIC_API / CLAUDE_CLI / CODEX_CLI the parser flips the
    default to `enable_cache=True`; `--llm-disable-cache` wins;
    supplying both flags raises `LlmRuntimeError`.
  - `LLM_RUNTIME_CACHE_DIR = Path("brain/.llm_cache")` is the
    canonical cache directory; do not re-route writes elsewhere.
- `brain/llm/ptcns_backed.py` owns the L2 canonical semantic
  evaluation cache (`eval_v1`). L2 keys on a seven-tuple including
  `SEMANTIC_CACHE_SCHEMA_VERSION="llm-semantic-cache-v1"`, is capped
  at `SEMANTIC_CACHE_MAX_ENTRIES = 1024`, stores only
  `{"key_prefix", "parsed"}` per entry, and is OUT OF SCOPE for Phase
  3.15.
- `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_AUDIT.md`
  and `PHASE3_14_LLM_CACHE_FINDINGS.md` record `I-LLMCACHE-20` as
  DEFERRED with the rationale that L1 bounding was deliberately not
  attempted in Phase 3.14.

## 3. Current L1 risk surfaces

The visible risks today are:

- **Unbounded file count.** `brain/.llm_cache` accumulates one JSON
  file per unique `sha256(prompt)`. There is no file-count cap. Under
  sustained model-backed use the directory grows monotonically.
- **Unbounded byte growth.** Each entry stores both raw prompt and
  raw response with `json.dumps(..., indent=2)`. There is no
  per-entry size limit and no aggregate cap.
- **Raw prompt / response sensitivity.** The on-disk payload includes
  the literal prompt and the literal model response. The directory is
  gitignored, but it is local and operator-visible.
- **Raw bad-response replay.** When a model returns a response that
  fails `parse_consistency_eval`, the response is still cached on
  disk; subsequent identical prompts will hit and re-replay the same
  parse-failing text indefinitely.
- **Corrupt entries already fail loud.** `RuntimeError` is raised on
  read; Phase 3.15 preserves this and does not weaken it.
- **Phase 3.14 raised the L1 floor.** L1 is now reached by default
  whenever an operator opts into a model-backed mode, so the
  cardinality of operator-triggered cache writes is structurally
  higher than pre-Phase-3.14.
- **L2 is already bounded and out of scope.** `eval_v1` is capped at
  1024 entries; Phase 3.15 must not touch its semantics.

## 4. Option comparison

### A. Max entry count cap on L1

**Benefits.** Bounds file count directly. Matches the L2 style of
count-based capacity. Easy to test deterministically with a synthetic
prompt stream and an injected cap.

**Risks.** Requires a deterministic selection rule for which entry is
removed or skipped at cap. File count alone does not bound disk use
if individual entries are very large. Eviction can disrupt long
model-backed sessions; write-skip-at-cap is the conservative variant
that avoids removing existing entries.

**Cost.** Small. Implementation lives entirely inside
`brain/llm/client.py::CachedClient`.

### B. Max byte cap on L1

**Benefits.** Bounds disk footprint directly. Addresses the failure
mode where a small number of large entries dominate disk use.

**Risks.** Byte accounting must handle partial writes, corrupt files,
and concurrent operators. Testing requires controlled file sizes.
Implementation is fiddlier than entry-count caps.

**Cost.** Medium.

### C. TTL eviction

**Benefits.** Limits stale replay across time. Intuitive for
operator-managed hygiene.

**Risks.** Time-dependent. Brittle under fixture clocks unless mtime
is injected or controlled. Does not bound growth during a single
high-volume window. Adds policy-dependent state to the read path.

**Cost.** Medium.

### D. No-auto-evict warning / report only (status quo + observability)

**Benefits.** Preserves current L1 semantics exactly. Gives operators
visibility into cache state without changing hits, misses, or replay
semantics. Trace event surface is cheap.

**Risks.** Does not actually bound growth. Insufficient alone to
retire `I-LLMCACHE-20` if the campaign expects a real bound.

**Cost.** Very small.

### E. Parse-failure-aware bypass / eviction

**Benefits.** Targets the highest-risk L1 behavior surfaced by Phase
3.14: cached responses that are known to fail parsing. Could reduce
retry-shell churn for known-bad prompts.

**Risks.** Mixes transport-layer caching with parser-layer
knowledge. Requires the caller (`LLMBackedPtCns`) to either carry
parse classification across the cache call or expose an explicit
invalidation API. Must avoid silent repair calls (no auto-rewrite of
cache contents based on inferred fixes).

**Cost.** Medium-large.

### F. Manual cache inspect / clear helper commands

**Benefits.** CLI-level operator UX without changing runtime
behavior. Helpers can report counts, byte totals, age bands, and
corrupt-entry status without printing raw cache contents.

**Risks.** Expands the operator-facing surface. Clear operations need
explicit safety / dry-run defaults. Helpers do not by themselves
retire `I-LLMCACHE-20`.

**Cost.** Small for inspect; small for clear.

## 5. Proposed v1 subset

Lock-in is deferred to Step 4 LOCK A. The synthesis recommendation is:

- **Adopt Option A** (max entry count cap) as the primary bounding
  lever. Propose a default constant such as
  `L1_CACHE_MAX_ENTRIES = 1024` by symmetry with the L2 cap of 1024
  entries. Note that L1 entries store raw prompt + raw response and
  may be considerably larger per-entry than L2 entries (which store
  only `{"key_prefix", "parsed"}`); Step 3 must therefore record the
  representative serialized payload size for L1 entries, and the
  final value is pinned in Step 4 LOCK A. The byte cap (Option B) is
  deferred, so the count cap is justified by measurement, not by
  by-eye parity with L2.
- **Adopt Option A's write-skip-at-cap variant** for the selection
  rule (Step 4 LOCK B). This is a **bounded admission** policy, not
  an eviction policy: existing entries are never removed. At cap:
  hits continue to read; misses may still call the inner client in
  explicit model-backed mode; no new entry is written. The catalog
  language for the eventual `I-LLMCACHE-20` retirement must speak of
  bounded admission, not eviction, to avoid overclaiming. This
  avoids the fiddly mtime / lexicographic ordering questions that an
  evict-on-write policy raises.
- **Adopt Option D's observability subset** as a companion: emit a
  new trace event (proposed name `llm.cache_skip` with
  `reason="capacity"`) whenever a miss is not written due to the cap.
  Payload limited to the 8-character `key_prefix` and `reason`.
  Counter `skip_count` exposed on `CachedClient` for fixture
  assertions.
- **Defer Option B** (byte cap). Record as a future-campaign concern.
  Step 9 findings should call this out explicitly.
- **Defer Option C** (TTL). Clock injection adds test complexity
  beyond Phase 3.15 scope. Record as a future-campaign concern.
- **Defer Option E** (parse-failure-aware bypass). Requires
  parser-layer coupling beyond Phase 3.15 scope. Phase 3.15 does NOT
  claim to solve malformed-response cache poisoning. Step 9 findings
  must explicitly record that raw bad-response replay still exists
  after Phase 3.15 and that retiring it is a future-campaign concern.
- **Defer Option F** (manual inspect / clear helpers). The runtime
  bound is the primary lever. Operator-facing helpers may follow in a
  later campaign.

Combinations remain admissible. Step 4 LOCK A must pin the exact
subset before Step 5 catalog planning.

## 6. Acceptance criteria for implementation

The eventual implementation must satisfy every item below before
Review Gate A may be cleared:

- Offline remains default; `OFFLINE` / `MOCK` still reject
  `--llm-enable-cache` at the factory boundary; `--llm-disable-cache`
  remains a no-op for those modes.
- Model-backed modes remain explicit opt-in via `--llm-mode` /
  `BRAIN_LLM_MODE`. Cache flags cannot promote OFFLINE / MOCK into a
  model-backed mode.
- Phase 3.14 flag contract preserved unchanged:
  `--llm-disable-cache` continues to win over the default-on for
  ANTHROPIC_API / CLAUDE_CLI / CODEX_CLI; `--llm-enable-cache`
  continues to be accepted as an explicit affirmation; supplying both
  flags continues to raise `LlmRuntimeError` from
  `parse_llm_runtime_args`.
- Factory-boundary preservation: `build_llm_client_from_config`
  remains the only `brain/ui/` seam that wraps an inner client in
  `CachedClient`; no new caller is added; `LLM_RUNTIME_CACHE_DIR`
  remains `Path("brain/.llm_cache")`.
- Cache directory behavior: `CachedClient` continues to create the
  cache directory on first miss; the bounded-admission policy does
  not require pre-existence of the directory and does not delete or
  rename it.
- At-cap miss behavior is explicit: when an at-cap miss occurs in
  explicit model-backed mode, the inner client is still called and
  the response is still returned to the caller; only the cache write
  is skipped. The new trace event (`llm.cache_skip` with
  `reason="capacity"`) is emitted; `skip_count` is incremented.
- `L2` (`eval_v1`) semantics unchanged; `brain/llm/ptcns_backed.py`
  is not modified for cache behavior.
- `brain/tick.py` is not edited.
- No real LLM calls in tests; all fixtures use `MockClient` or a
  similarly deterministic stand-in.
- For valid entries within the locked cap, hit semantics are
  preserved: hits read from disk and never call the inner client.
- For misses at cap: the inner client may still be called only in
  explicit model-backed mode; whether a new entry is written is
  governed by the locked write-skip / eviction rule (Step 4 LOCK B).
- Eviction or write-skip behavior is deterministic and observable
  through a new trace event (Step 4 LOCK E pins the exact names and
  payload fields).
- Corrupt entries continue to raise `RuntimeError` on read; no
  silent fall-back; no silent repair.
- Bad-response replay behavior is explicitly documented and either
  preserved or explicitly changed by Step 4 LOCK C.
- `brain/.llm_cache` remains gitignored; no cache files committed;
  no raw cache contents in docs.
- Trace event payloads contain only `key_prefix`, `reason`, and
  (where applicable) counts; never raw prompt or response.
- No `SCHEMA_VERSION` bump; no DB schema change; no
  persistence / autosave runtime change.
- No `SelfModel` implementation; no Growth / Pattern / Coherence
  semantic change.
- Catalog patch is a clean delta over `v0.24` (Step 5 pins the
  exact rows / statuses / counts).

## 7. Step 3 measurement requirements

Step 3 must produce a deterministic probe report covering at least
the following measurements. All measurements use `MockClient` and the
existing public API. No real external LLM calls. Any helper script
lives under `/tmp` unless Step 4 or Step 5 explicitly authorizes a
committed fixture.

- Baseline L1 hit / miss with `--llm-enable-cache=False`.
- Baseline L1 hit / miss with `--llm-enable-cache=True`.
- File count growth across a synthetic prompt stream at
  sample sizes 1, 100, 1024, 1025, and 2048 unique prompts; record
  `CachedClient.hit_count` and `CachedClient.miss_count`.
- Byte growth (total cache directory size) across the same prompt
  stream.
- Representative L1 entry size distribution: record min / median /
  max serialized payload size in bytes across the synthetic prompt
  stream. This grounds the Step 4 LOCK A choice of
  `L1_CACHE_MAX_ENTRIES` in measurement instead of L2-parity alone.
- Raw payload shape: confirm each file contains
  `{"prompt", "response"}`. Do not print raw values. Record only
  the field names and the 8-character key prefix.
- Bad-response replay: cache a response that fails
  `parse_consistency_eval`; verify subsequent identical-prompt
  evaluations return the same cached response unchanged.
- Corrupt-entry behavior: tamper a cache file's JSON; verify
  `CachedClient` raises `RuntimeError` and the inner client is not
  called.
- Candidate count-cap behavior (simulated): under a write-skip-at-cap
  selection rule with `L1_CACHE_MAX_ENTRIES = N`, record which
  entries survive and that the inner client is still called on miss
  at cap.
- Candidate byte-cap behavior (simulated): record what a byte cap
  would skip / preserve. Used to justify deferring Option B.
- Candidate mtime vs lexicographic selection: record determinism
  characteristics. Used to justify write-skip-at-cap over
  evict-on-write.
- Offline / mock isolation: confirm `OFFLINE` and `MOCK` produce zero
  cache writes.
- L2 untouched evidence: read `SEMANTIC_CACHE_MAX_ENTRIES` and
  inspect L2 directory state before and after the probe.
- Trace observability: count `llm.cache_hit`, `llm.cache_miss`,
  `llm.semantic_cache_hit`, `llm.semantic_cache_miss`,
  `llm.semantic_cache_store`, `llm.semantic_cache_skip` events
  emitted during a run. After implementation, the new event
  (`llm.cache_skip` with `reason="capacity"`) is added to this list.

## 8. Non-goals and guardrails

- no `brain/tick.py` edit (no tick semantic change)
- no L2 (`eval_v1`) semantic change; `brain/llm/ptcns_backed.py`
  semantic behavior unchanged
- no `SelfModel` implementation
- no Growth Ledger / Pattern Ledger / Coherence Monitor semantic
  change
- no hidden LLM calls
- no silent repair calls (no auto-rewrite of cache contents based on
  inferred fixes)
- no DB schema change; no `SCHEMA_VERSION` bump
- no persistence / autosave runtime change
- no UI expansion unless explicitly reviewed
- no raw prompts / raw model responses / raw cache files / secrets
  committed
- no raw cache contents printed in any campaign artifact
- no consciousness / sentience / subjective-experience /
  semantic-understanding / truth / agency / self-modification claim
- no aggregate growth / awareness / I-ness score
- `OFFLINE` remains the default runtime
- model-backed modes remain explicit opt-in

## 9. Stage A / Stage B / Stage C disclosure

Stage A consultation:
- used: yes
- mode: review
- model: gpt-5.5
- effort: high
- wrapper command:
  `python3 tools/claude_helpers/codex_chatgpt_subagent.py --mode review --model gpt-5.5 --effort high --timeout 600 --prompt-file /tmp/toyi_phase3_15_step2_review_question.md`
- wrapper status: `exit_code=0`, `error_class=None`
- question file: `/tmp/toyi_phase3_15_step2_review_question.md`
- answer file: `/tmp/toyi_phase3_15_step2_review_answer.md`
- overall verdict: APPROVE WITH MINOR EDITS (no blockers)
- accepted advice:
  - frame the v1 policy as bounded admission, not eviction, in the
    Step 5 catalog language to avoid overclaiming retirement of
    `I-LLMCACHE-20`
  - justify `L1_CACHE_MAX_ENTRIES` by Step 3 measurement of
    representative L1 entry size rather than L2-parity alone
  - record raw bad-response replay as a documented Step 9
    follow-up; do not claim Phase 3.15 solves malformed-response
    cache poisoning
  - make `--llm-disable-cache` precedence, conflicting-flag
    `LlmRuntimeError`, factory-boundary preservation, cache
    directory behavior, at-cap no-write behavior, and
    `skip_count` / event emission explicit acceptance criteria
  - add a Step 3 measurement for representative L1 entry size
    distribution
- rejected advice: none
- reason: synthesis adversarial review required by
  `CURRENT_CAMPAIGN.md`

Stage B limited-write collaboration:
- used: no
- reason: Stage C is the preferred bridge for bounded doc shards in
  Phase 3.15; Stage B was not invoked at Step 2

Stage C orchestration:
- used: attempted; both attempts failed before producing a shard diff
  (`SHARD_FAILED` / `CODEX_OUTPUT_TOO_LARGE`), operator approved
  auto-retry. Parent Claude wrote this synthesis directly to conserve
  the remaining Stage C call budget for Step 7 implementation.
- shards: `synthesis_draft` (single-shard wave, attempted twice; no
  files were applied)
- accepted edits: none from Codex; document authored by parent Claude
- rejected edits: none (no shard diff was produced)
- reason: transport hiccups consumed two real Codex calls without
  producing a draft; parent Claude wrote the doc to preserve the
  remaining Stage C budget for Step 7

## 10. Next artifact

Step 3 produces
`docs/campaigns/phase3_15/PHASE3_15_L1_CACHE_HYGIENE_PROBE.md`.
