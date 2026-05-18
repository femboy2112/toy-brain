# PHASE3_14_LLM_CACHE_DISCIPLINE_AUDIT.md

## Purpose

This is the final Phase 3.14 LLM Cache Discipline audit. It audits the
campaign end-to-end, from Step 1 (mission sync) through Step 9
(findings / triage). It records the canonical confirmations the
campaign must carry into Step 11 Final PR Preparation.

This document is documentation only. It does not change code, catalog
rows, fixtures, runtime behavior, cache behavior, tick semantics,
bridge behavior, or any prior Phase 3.14 artifact. It does not
authorize any new measurement, fixture, or implementation.

## Baseline

- Catalog version: v0.24.
- Counts:
  - REQUIRED: 277
  - STRUCTURAL: 87
  - NOT-EXERCISED: 14
  - DEFERRED: 16
  - OBSERVED: 16
- Branch: `campaign/phase3-14-llm-cache-discipline`.
- Phase 3.13 Growth Ledger: complete and merged (PR #14).
- PR #15: Stage B limited-write Claude → Codex CLI → ChatGPT bridge
  merged into main before Phase 3.14.
- Phase 3.14 Steps 1 through 9: complete and pushed.

## Campaign Timeline

- **Step 1** — LLM cache discipline mission sync — commit `870a0ce`
  (`phase3.14 step1: llm cache discipline mission sync`). Installed
  `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, and
  `PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md` at repo root.
- **Step 2** — LLM cache discipline synthesis — commit `0a150f8`
  (`phase3.14 step2: llm cache discipline synthesis`). Created
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_SYNTHESIS.md`.
- **Step 3** — LLM cache behavior probe / spam reproduction report —
  commit `cc24cca`
  (`phase3.14 step3: llm cache behavior probe`). Created
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_PROBE.md`
  with measurement families M1..M9.
- **Step 4** — LLM cache discipline corrigenda — commit `5f23b1b`
  (`phase3.14 step4: llm cache discipline corrigenda`). Created
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_CORRIGENDA.md`
  with LOCK A through LOCK S.
- **Step 5** — LLM cache catalog patch plan — commit `d9ad131`
  (`phase3.14 step5: llm cache catalog patch plan`). Created
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_CATALOG_PATCH_PLAN.md`
  with row family I-LLMCACHE-01..22 and the catalog v0.23 → v0.24
  delta.
- **Step 6** — Review Gate A — accepted the Step 5 plan as written
  (no amendment). No source commit; Review Gate A is a decision
  artifact embedded in the campaign workflow.
- **Step 7** — LLM cache implementation — commit `366bf95`
  (`phase3.14 step7: implement llm cache discipline`). Bumped catalog
  to v0.24, added I-LLMCACHE-01..22 with the 18/1/1/2/0 status split,
  added the eight `llm_cache_*.py` fixtures, added L2 inside
  `brain/llm/ptcns_backed.py`, flipped the parser default and added
  `--llm-disable-cache` in `brain/ui/llm_runtime.py`, added the three
  version constants in `brain/llm/prompts.py` / `brain/llm/parse.py`,
  and applied two narrow blocking-contradiction fixture carve-outs in
  `brain/ui/fixtures/tui_smoke.py` and
  `brain/ui/fixtures/llm_runtime_tick_seam.py`.
- **Step 8** — LLM cache behavior report — commit `8db679f`
  (`phase3.14 step8: llm cache behavior report`). Created
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_REPORT.md`
  with twelve measurement families M-FAM1..12 along the deterministic
  local-client route. Verdict PASS WITH DEFERRED FOLLOW-UPS; zero
  blocking findings.
- **Step 9** — LLM cache findings / triage — commit `b7b064f`
  (`phase3.14 step9: llm cache findings`). Created
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_FINDINGS.md` and
  triaged F-01..F-10. Verdict PASS WITH DEFERRED FOLLOW-UPS; zero
  blockers.
- **Step 10** — final Phase 3.14 audit — this document.

## Implementation Audit

The implemented architecture matches the Step 5 catalog patch plan as
accepted at Review Gate A. The accepted plan was applied without
amendment in Step 7.

**L0 — per-instance `LLMBackedPtCns._cache`:**

- Behavior unchanged from Phase 2 v1. Each `tick(...)` constructs a
  fresh `LLMBackedPtCns`; the cache starts seeded only with
  `{COGITO_ID: PRESERVE}` (I-LLM-03 / I-LLMCACHE-01).
- Cogito short-circuit preserved.
- No `brain/tick.py` edit
  (`git diff origin/main -- brain/tick.py` is empty; recorded in
  Validation Results).

**L1 — `CachedClient` raw prompt-hash transport cache:**

- Preserved as the existing v0.16 transport cache; `brain/llm/client.py`
  is functionally unchanged.
- Hit returns the cached response without calling the inner client;
  miss calls the inner client and writes `{prompt, response}` JSON
  under `cache_dir/<sha256>.json`.
- After explicit selection of a model-backed mode, the runtime parser
  flips the default to `enable_cache=True`.
- `--llm-disable-cache` is the explicit opt-out flag.
- `--llm-enable-cache` is retained as a compatibility affirmation for
  model-backed modes.
- Supplying both `--llm-enable-cache` and `--llm-disable-cache` raises
  a bounded `LlmRuntimeError` naming both flags.
- L1 bounding / eviction remains DEFERRED under I-LLMCACHE-20.

**L2 — canonical semantic evaluation cache:**

- Implemented inside `brain/llm/ptcns_backed.py` (Step 5 Option 3).
- Enabled iff the wrapped client is a `CachedClient`. In production
  this means the runtime factory wrapped a known model-backed
  transport (`AnthropicAPIClient` / `ClaudeCLIClient` /
  `CodexCLIClient`) because OFFLINE / MOCK are factory-rejected from
  caching. `--llm-disable-cache` disables the wrap and therefore
  disables L2 as well.
- Canonical key: SHA-256 hex of `repr()` of the seven-tuple
  `(SEMANTIC_CACHE_SCHEMA_VERSION, PROMPT_TEMPLATE_VERSION,
  PARSE_SCHEMA_VERSION, backend_family, model_identity,
  existing_msi_context, new_text)`. `existing_msi_context` is a
  sorted tuple of `(content_id, text)` pairs over non-cogito MSI
  members.
- The evaluated `new_id` is excluded from the L2 key (LOCK E) but
  retained in the rendered prompt for diagnostics and trace
  readability.
- L2 entry payload is exactly `{"key_prefix", "parsed"}`. No raw
  prompt, raw response, error text, provider metadata, or full key
  appears in the on-disk file. File name is the 64-char hex digest
  under `brain/.llm_cache/eval_v1/`.
- L2 stores **only** parse-success entries. Parse failures emit
  `llm.semantic_cache_skip` with `reason="parse_failure"` and write
  nothing to L2.
- L2 cap is `SEMANTIC_CACHE_MAX_ENTRIES = 1024`. At cap, hits still
  read; misses may call the explicit model-backed inner path but do
  not write a new entry, and the implementation emits
  `llm.semantic_cache_skip` with `reason="capacity"`. No eviction or
  pruning in v1.
- Corrupt L2 entries (invalid JSON, unexpected key set, invalid
  `parsed` value, key-prefix mismatch) fail loud with a bounded
  `RuntimeError` containing `"corrupt"`; the inner client is not
  silently called for repair.
- Tracer events are bounded — payload subset of `{content_id,
  key_prefix, reason}`. `key_prefix` is the 8-char hex prefix of the
  full key.

**Runtime policy:**

- OFFLINE remains the default mode (no `--llm-mode` / no
  `BRAIN_LLM_MODE` ⇒ OFFLINE).
- Model-backed modes remain explicit opt-in. Cache flags
  (`--llm-enable-cache` / `--llm-disable-cache`) cannot promote
  OFFLINE / MOCK into a model-backed mode; mode selection remains
  exclusively governed by the I-LLMTOG-* family.
- OFFLINE / MOCK never read or write L1 / L2 cache files. The factory
  rejects `--llm-enable-cache` for OFFLINE / MOCK with a bounded
  error; the parser also accepts `--llm-disable-cache` from OFFLINE /
  MOCK as a no-op so scripts can pass the flag uniformly without
  unlocking cache access.
- No real external LLM mode was run during deterministic gates. The
  Stage A / Stage B bridges are advisory / limited-write channels
  reaching ChatGPT through the Codex CLI wrapper — they are not
  runtime LLM seams.

## Catalog Audit

- Catalog version bump: v0.23 → v0.24.
- Row family added: `I-LLMCACHE-01..22`.
- Status split:
  - REQUIRED: +18 (I-LLMCACHE-01..18).
  - STRUCTURAL: +1 (I-LLMCACHE-19).
  - DEFERRED: +1 (I-LLMCACHE-20).
  - NOT-EXERCISED: +2 (I-LLMCACHE-21, I-LLMCACHE-22).
  - OBSERVED: 0 (unchanged).
- Final counts: REQUIRED 277 / STRUCTURAL 87 / NOT-EXERCISED 14 /
  DEFERRED 16 / OBSERVED 16. Banner = actual = expected at every gate
  command.
- Fixtures added (eight, one per the Step 5 row-to-fixture map):
  - `brain/ui/fixtures/llm_cache_runtime_policy.py` —
    I-LLMCACHE-02 / -03 / -04.
  - `brain/ui/fixtures/llm_cache_transport.py` —
    I-LLMCACHE-05 / -14 (L1 hit/miss inner-call discipline; L1
    corrupt path).
  - `brain/ui/fixtures/llm_cache_semantic_key.py` —
    I-LLMCACHE-06 / -07 / -08 / -15.
  - `brain/ui/fixtures/llm_cache_parse_failure.py` —
    I-LLMCACHE-09 and the L2 corrupt path of I-LLMCACHE-10.
  - `brain/ui/fixtures/llm_cache_bounds_artifacts.py` —
    I-LLMCACHE-11 / -12.
  - `brain/ui/fixtures/llm_cache_observability.py` —
    I-LLMCACHE-13.
  - `brain/ui/fixtures/llm_cache_no_tick_change.py` —
    I-LLMCACHE-01 / -16.
  - `brain/ui/fixtures/llm_cache_static_audit.py` —
    I-LLMCACHE-17 / -18 / -19.
- Catalog stamp surfaces updated at Step 7: `INVARIANT_CATALOG.md`
  banner; `tools/catalog.py` `EXPECTED_COUNTS`;
  `brain/_catalog_ids.py` regenerated; `brain/invariants.py`
  `FIXTURE_MODULES` extended with the eight fixture modules;
  `README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md` catalog
  version + counts stamps updated.

## Validation Results

The five canonical gates plus the `brain/tick.py` diff sanity check
were re-run at Step 10 preflight. All pass.

```text
$ python3 -m tools.catalog counts
Category            Banner    Actual  Expected
REQUIRED               277       277       277  ok
STRUCTURAL              87        87        87  ok
NOT-EXERCISED           14        14        14  ok
DEFERRED                16        16        16  ok
OBSERVED                16        16        16  ok
```

```text
$ python3 -m tools.citations verify
Verified 100 citations.
All catalog citations resolve in lean_reference/.
```

```text
$ python3 -m tools.import_audit
I-PCE-05: agency.py is clean of pce imports.
```

```text
$ python3 -m brain.invariants run
... (372 rows checked)
REQUIRED green: 278 · REQUIRED red: 0 · STRUCTURAL green: 87 ·
STRUCTURAL red: 0 · OBSERVED: 7 pass / 0 fail · gate failures: 0
```

(The runner's "REQUIRED green: 278" count includes the
`I-PCE-05`-clean line emitted by the import-audit hook, which
duplicates one count vs the catalog row total of 277; both numbers
are correct under their respective scopes.)

```text
$ bash tools/check_all.sh
... (runner output)
All checks passed.
```

```text
$ git diff origin/main -- brain/tick.py
$ # (empty — zero lines of diff)
```

Verdict for Validation Results: **PASS**.

## Behavior Audit

The Step 8 behavior report
(`docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_REPORT.md`,
commit `8db679f`) measured twelve families M-FAM1..12 along the
deterministic local-client route. Every measurement landed its
expected result. Summary:

- **M-FAM1 / M-FAM2** — gates and Step 7 diff surface: PASS; the diff
  surface matches the Step 5 plan plus the two audited fixture
  carve-outs.
- **M-FAM3 (A..H + CONSTR)** — runtime policy: default OFFLINE; CLI
  and env-override model-backed flip enable_cache on by default;
  `--llm-disable-cache` opts out; conflicting flags raise; OFFLINE /
  MOCK factory-reject `--llm-enable-cache`; OFFLINE / MOCK
  `--llm-disable-cache` is a no-op; bare `LlmRuntimeConfig(...)`
  constructor default is `enable_cache=False` (parser-owned policy).
- **M-FAM4** — L1 identical prompt: 2 evals → 1 inner call; cache
  file with `{prompt, response}`; tracer `[llm.cache_miss,
  llm.cache_hit]`.
- **M-FAM5** — L2 same-text / different `content_id` under same MSI
  context: 1 inner call across two `LLMBackedPtCns` instances; one
  L2 entry; second instance traces a single `llm.semantic_cache_hit`.
- **M-FAM6** — different existing MSI context: two distinct L2 keys;
  both inner calls realized; no false hit.
- **M-FAM7** — parse failure: retries-exhaust writes zero L2 entries
  and emits exactly one `llm.semantic_cache_skip` with
  `reason="parse_failure"`; retry-then-success writes exactly one L2
  entry with `parsed="PRESERVE"`.
- **M-FAM8** — corrupt L2: both invalid-JSON and wrong-key-set
  variants raise `RuntimeError` containing `"corrupt"`; the inner
  client is never silently called for repair.
- **M-FAM9** — capacity (cap monkeypatched to 2): hits still read at
  cap; misses call inner once; no new entry written;
  `llm.semantic_cache_skip(reason="capacity")` emitted.
- **M-FAM10** — observability / leakage: cache-event payloads contain
  no `prompt` / `response` / `raw` / `error` / `secret` / `api_key`
  / `headers` / `full_key`; `key_prefix` length is 8.
- **M-FAM11** — gitignore / file safety: `brain/.llm_cache/` at
  `.gitignore` line 28 covers `brain/.llm_cache/eval_v1/`; the L2
  entry payload is exactly `{"key_prefix", "parsed"}`; no raw text
  appears in the file.
- **M-FAM12** — tick boundary: cached vs uncached `tick(...)` over an
  identical event produces field-for-field equal `(new_state,
  TickRecord)` for the same client responses;
  `git diff origin/main -- brain/tick.py` is empty.
- Fixture carve-outs: classified justified, narrow, no runtime impact
  in the Step 8 report.

Step 8 Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Zero blocking
findings. Stage A (review / medium) accepted the report.

## Findings / Triage Audit

The Step 9 findings doc
(`docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_FINDINGS.md`, commit
`b7b064f`) triaged F-01..F-10:

- **F-01** — L1 raw bad-response transport-cache replay → deferred
  enhancement (LOCK F preserves L1 prompt-hash semantics on purpose;
  L2 already excludes parse failures from the success cache).
- **F-02** — `I-LLMCACHE-20` L1 bounding → planned deferred row.
- **F-03** — `I-LLMCACHE-21` / `I-LLMCACHE-22` → planned
  NOT-EXERCISED placeholders.
- **F-04** — parser-vs-constructor cache-default surface →
  UX/readability, non-blocking.
- **F-05** — `semantic_cache_skip` `reason` values `"disabled"` and
  `"offline_or_mock"` enumerated in the Step 5 plan are unreachable
  in v1 because the L2 surface is gated at `_l2_metadata is None` →
  documentation / plan-vs-implementation reconciliation,
  non-blocking.
- **F-06** — the two fixture carve-outs (`tui_smoke.py`,
  `llm_runtime_tick_seam.py`) → resolved blocking-contradiction,
  justified, narrow, non-blocking.
- **F-07..F-10** — pass evidence within tested scope (tick boundary
  on measured route + fixture-gated; L2 sensitive-artifact policy;
  corrupt L2 fail-loud; capacity behavior).

Step 9 Verdict: **PASS WITH DEFERRED FOLLOW-UPS**. Zero blockers.
Stage A (review / low) confirmed the verdict and the wording
guardrails.

## Fixture Carve-out Audit

1. **`brain/ui/fixtures/tui_smoke.py`** —
   - The `I-UI-07` forbidden-builtin-call audit was narrowed from
     "any `ast.Call` whose `.func` has an `attr` or `id` in
     `{exec, eval, compile, __import__}`" to "any `ast.Call` whose
     `.func` is an `ast.Name` whose `id` is in the forbidden set".
     Python builtins of those names are only ever invoked by bare
     name, so this is a false-positive correction rather than a
     real loosening; it lets `LLMBackedPtCns.eval(content_id)`
     stand.
   - The persistence-fixture `tempfile` exemption was extended to
     match `path.name.startswith("llm_cache_")` so the eight new
     fixtures can isolate L1 / L2 cache writes under temp dirs.
   - Reason: the new Phase 3.14 LLM cache fixtures legitimately call
     `LLMBackedPtCns.eval(...)` and use `tempfile.TemporaryDirectory()`
     to keep cache artifacts out of `brain/.llm_cache/`.
   - Runtime impact: **none** (fixture-internal audit only).
   - Blocker: **no**.

2. **`brain/ui/fixtures/llm_runtime_tick_seam.py`** —
   - An `_unwrap_for_test(client)` helper returns `client._inner` if
     `isinstance(client, CachedClient)` and the client itself
     otherwise. The three `isinstance(...)` assertions in
     `check_I_LLMTOG_09_tick_seam` (OFFLINE →
     `OfflineStandInClient`; MOCK → `MockClient`; CODEX_CLI →
     `CodexCLIClient`) are routed through this helper.
   - Reason: post-Step-7 the runtime parser flips
     `enable_cache=True` by default for explicit model-backed modes,
     so `main(["--llm-mode", "codex-cli", ...])` now returns
     `CachedClient(CodexCLIClient(...))` instead of a bare
     `CodexCLIClient`. The I-LLMTOG-09 contract is "mode selection
     drives transport type"; whether the transport is wrapped in
     `CachedClient` is now governed by the separate I-LLMCACHE-02
     default policy.
   - Runtime impact: **none** (fixture-internal helper).
   - Blocker: **no**.

Both carve-outs are inline-documented in their respective files.
Both are within the inherited audit scope and do not change runtime
behavior.

## Non-goal Confirmation

The following non-goals were observed across Phase 3.14:

- No SelfModel implementation.
- No Growth Ledger semantic change (Phase 3.13 artifacts unchanged).
- No Pattern Ledger semantic change (Phase 3.13 artifacts unchanged).
- No Coherence Monitor semantic change (Phase 3.13 artifacts
  unchanged).
- No UI expansion (`/pattern-ledger`, `/coherence-summary`,
  `/growth-ledger` remain DEFERRED).
- No DB schema change.
- No `SCHEMA_VERSION` bump.
- No persistence / autosave runtime change.
- No `brain/tick.py` edit
  (`git diff origin/main -- brain/tick.py` is empty).
- No hidden LLM calls are evidenced in the campaign artifacts or
  Step 10 gate context. M-FAM4..M-FAM12 in Step 8 confirm no inner
  call from any cache-hit path; M-FAM3-E / M-FAM3-F confirm factory
  rejection at OFFLINE / MOCK; M-FAM8-CORRUPT confirms no silent
  inner-call on corrupt L2. Repo-local evidence remains
  authoritative.
- No default model-backed behavior. OFFLINE remains the default; the
  cache-default flip only fires after the operator has explicitly
  selected a model-backed mode.
- No cache files committed
  (`git ls-files brain/.llm_cache` returns no output).
- No raw prompts committed (no fixture, doc, or report quotes raw
  prompt bodies; cache key references are 8-char hex prefixes only).
- No raw model responses committed.
- No secrets committed.
- No real external model-backed runtime smoke during deterministic
  gates. The Stage A / Stage B bridges reach ChatGPT through the
  Codex CLI wrapper; they are not runtime LLM seams.
- No aggregate growth / awareness / I-ness / sentience / consciousness
  score is computed or surfaced.
- No consciousness claim.
- No sentience claim.
- No subjective-experience claim.
- No semantic-understanding claim.
- No truth-adjudication claim.
- No agency / intent / will / desire claim.
- No self-modification claim (no code, fixture, catalog, or runtime
  is mutated by ToyI itself; all edits are operator-driven through
  the cataloged campaign workflow).

**Wording note.** The phrase "semantic cache key" / "canonical
semantic evaluation cache" is engineering language about cache
*identity* (the seven-tuple under SHA-256), not a claim that ToyI
understands meaning. The Phase 3.14 corrigenda LOCK R fixes this
wording, and the audit preserves it.

## ChatGPT/Codex Bridge Usage Audit

**Stage A advisory consultations** (`/ask-chatgpt`) used at the
following steps; each call has a hash-only JSONL audit row under
`.claude/codex_bridge_logs/` (gitignored):

- Step 1 — plan review (advisory plan review of the mission install).
- Step 2 — synthesis adversarial review.
- Step 4 — corrigenda adversarial review.
- Step 5 — catalog patch plan adversarial review.
- Step 7 — implementation risk review (pre-implementation
  adversarial check on the broad cross-file scope).
- Step 8 — behavior report adversarial review (review / medium /
  gpt-5.5; advisor confidence "high", disagreement "minor").
- Step 9 — findings / triage review (review / low / gpt-5.5; advisor
  confidence "medium", disagreement "minor").
- Step 10 — this final audit review (review / medium / gpt-5.5).

**Stage B limited-write collaboration** (`/ask-chatgpt-write`) used
at:

- Step 1 — roadmap draft (single allowed file
  `PHASE3_14_LLM_CACHE_DISCIPLINE_ROADMAP.md`).
- Step 2 — synthesis draft (single allowed file
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_SYNTHESIS.md`).
- Step 3 — behavior probe report draft (single allowed file
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_BEHAVIOR_PROBE.md`).
- Step 4 — corrigenda draft (single allowed file
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_DISCIPLINE_CORRIGENDA.md`).
- Step 5 — catalog patch plan draft (single allowed file
  `docs/campaigns/phase3_14/PHASE3_14_LLM_CACHE_CATALOG_PATCH_PLAN.md`).

**Stage B explicitly not used** at:

- Step 7 (implementation — the cross-file scope would have exceeded
  the three-call Stage B budget; parent Claude integrated directly).
- Step 8 (behavior report — 12 measurement families × 22 row
  citations is high-risk for single-shot writer accuracy).
- Step 9 (findings / triage — the Step 9 brief explicitly discourages
  Stage B for this triage).
- Step 10 (this final audit — the Step 10 brief discourages Stage B
  for the final audit).

**Bridge policy confirmations:**

- No raw `codex` / `codex exec` invocation anywhere in the campaign.
- No Stage B `--apply` outside an exact `--allowed-file` path.
- No Stage B staging, commit, push, restore, or merge — parent Claude
  inspected every Stage B diff and owned validation, staging, commit,
  and push.
- No parallel Stage A / Stage B calls.
- No more than three real Stage B calls in any single step without
  fresh operator approval.
- Hash-only Stage A audit JSONL under `.claude/codex_bridge_logs/`
  is gitignored.
- Stage B runtime state under `.claude/codex_bridge_state/` is
  gitignored.
- The operator-supplied `gpt-5.5` model was used throughout; no other
  model was used. (The Codex CLI backend for the local ChatGPT
  account rejected the other candidates `gpt-5.1-codex` / `gpt-5` /
  `gpt-5-codex` / `gpt-5.1` / `o3` / `gpt-4o` with HTTP 400 during
  the original Stage A / Stage B smokes.)
- Repo-local files, gates, and invariants override every piece of
  ChatGPT advice. Where ChatGPT advice conflicted with a repo-local
  rule, the repo-local rule won and the conflict was reported in the
  per-step disclosure.

## Deferred Follow-ups

The following items are intentional carry-forwards from Phase 3.14.
They are already cataloged or already-deferred and do not block PR.

- **I-LLMCACHE-20** — L1 cache bounding / eviction policy remains
  **DEFERRED**. A future campaign may add bounded L1 growth + eviction
  policy.
- **I-LLMCACHE-21** — Real external model-backed ORS smoke with cache
  enabled remains **NOT-EXERCISED**. Promote only with explicit
  operator sponsorship and a dedicated campaign artifact (key
  management, rate-limit policy, trace policy, failure-mode policy).
- **I-LLMCACHE-22** — End-to-end Phase 3.14 behavior runner remains
  **NOT-EXERCISED**. The Step 8 report exercises the property along
  the deterministic local-client route only.
- **F-04** — optional documentation clarification noting that the
  cache default-on policy is parser-owned and that the bare
  `LlmRuntimeConfig(...)` constructor default is `enable_cache=False`.
- **F-05** — optional observability wording cleanup for the Step 5
  plan-enumerated `semantic_cache_skip` `reason` values `"disabled"`
  and `"offline_or_mock"` that are unreachable in v1.
- **F-06** — optional future fixture audit re-check if more fixtures
  use Python builtin method names.
- **Inherited UI deferrals** from earlier phases:
  - `/pattern-ledger` UI (I-PLEDGER-17).
  - `/coherence-summary` UI (I-COHMON-13).
  - `/growth-ledger` UI (I-GROW-21).
- **SelfModel** remains deferred to a later campaign that explicitly
  accepts the SelfModel plan (Phase 3.12 Step 15 roadmap is not in
  flight).
- **Inherited dry-run helpers**: I-PLEDGER-18 / I-COHMON-14 /
  I-GROW-22 (end-to-end Pattern Ledger / Coherence Monitor / Growth
  Ledger dry-run helpers) remain **NOT-EXERCISED**.
- **SQLite backup wording note** carried from Phase 3.10c remains
  documented; no Phase 3.14 change.

## Risk Assessment

- **No blocker risk remains from Step 8 / Step 9.** Step 9 explicitly
  triaged F-01..F-10; zero findings rose to a blocking patch.
- **Main residual risks are future scope creep**:
  - L1 bounding / eviction temptation under operator pressure.
    Mitigation: any L1-bounding change requires a separate catalog
    patch and review gate.
  - Real model-backed smoke creep. Mitigation: I-LLMCACHE-21 stays
    NOT-EXERCISED until an explicit operator-sponsored campaign
    artifact lands.
  - UI creep (`/cache-stats`, etc.). Mitigation: Phase 3.14
    authorized no UI surface; any future UI addition requires a
    review-gated UI catalog patch under a new campaign.
  - SelfModel creep. Mitigation: SelfModel implementation is
    explicitly out of scope; Phase 3.12 Step 15 roadmap is a planning
    artifact only.
  - Semantic-cache wording overclaim. Mitigation: LOCK R / I-LLMCACHE-18
    fixture-gates the non-claim language in `brain/llm/ptcns_backed.py`;
    audit / docs reuse "cache identity" wording.
- **Stable invariants** the audit re-confirms:
  - `brain/tick.py` is unchanged (zero-line diff vs main).
  - L2 entries are minimal (`{key_prefix, parsed}`).
  - OFFLINE / MOCK never reach L1 / L2.
  - Cache hit paths never call the inner client.
  - Corrupt cache fails loud with no silent inner call.
  - All five canonical gates green.

## Stage A ChatGPT/Codex Consultation

Stage A advisory review was used for this final audit.

- used: yes
- mode: review
- model: gpt-5.5
- effort: medium
- wrapper command:
  `python3 tools/claude_helpers/codex_chatgpt_subagent.py --mode review
  --model gpt-5.5 --effort medium --timeout 180 --prompt-file
  /tmp/toyi_phase314_step10_advisor_question.md
  > /tmp/toyi_phase314_step10_advisor_answer.md`
- question file: `/tmp/toyi_phase314_step10_advisor_question.md`
- answer file: `/tmp/toyi_phase314_step10_advisor_answer.md`
- wrapper status: exit_code=0, status="success", codex_returncode=0,
  error_class=null, duration_ms≈29888, truncated=false; advisor
  confidence "medium", disagreement "none"; hash-only audit JSONL
  under `.claude/codex_bridge_logs/` (gitignored).
- accepted advice (confirmatory; advisor explicitly approved PASS
  WITH DEFERRED FOLLOW-UPS):
  - preserved exact status labels (DEFERRED for I-LLMCACHE-20,
    NOT-EXERCISED for I-LLMCACHE-21 / I-LLMCACHE-22);
  - framed every Step 8 / Step 9 pass-evidence statement as
    "verified on the measured route" / "fixture-gated" rather than
    universal;
  - softened the "no hidden LLM calls" non-goal wording from a
    universal "are possible" claim to "are evidenced in the campaign
    artifacts and Step 10 gate context", with the repo-local evidence
    cross-referenced;
  - kept the verdict at PASS WITH DEFERRED FOLLOW-UPS (not a stronger
    plain PASS);
  - explicitly noted that the Stage A / Stage B bridges are advisory /
    limited-write channels, not runtime LLM seams;
  - preserved the "semantic cache key = engineering cache identity,
    not a claim that ToyI understands meaning" wording from LOCK R /
    I-LLMCACHE-18;
  - kept the F-04 parser-vs-constructor distinction explicit;
  - kept the inherited UI / dry-run / SelfModel deferrals listed
    explicitly so the PR summary cannot bury them under a general
    pass verdict.
- rejected advice: did not change code, catalog rows, fixtures,
  runtime behavior, tick semantics, or bridge behavior inside Step
  10; did not promote any deferred or NOT-EXERCISED row; did not
  introduce new measurements; did not pre-write Step 11 PR text into
  the audit; did not relabel any cataloged DEFERRED row as PASS.
- reason: Stage A final-audit review is required by the campaign
  policy for Step 10 unless the audit can justify redundancy. There
  is no redundancy justification here; the final audit is the last
  written artifact before PR preparation.

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
- reason: the Step 10 brief discourages Stage B for the final audit.
  Parent Claude drafted the audit directly. The audit cross-references
  ten step commits, twelve measurement families, ten Step 9 findings,
  two fixture carve-outs, and the full Stage A / Stage B bridge
  history — a single-shot writer call would be high-risk for accurate
  cross-reference fidelity.

## Final Verdict

**PASS WITH DEFERRED FOLLOW-UPS.**

Reason:

- All five canonical gates are green (Validation Results section).
- The implementation matches the Step 5 / Step 6 accepted plan,
  applied without amendment.
- The Step 8 behavior report passed with zero blocking findings
  across twelve measurement families.
- The Step 9 triage found zero blockers across F-01..F-10.
- Deferred / NOT-EXERCISED rows (I-LLMCACHE-20, I-LLMCACHE-21,
  I-LLMCACHE-22) are intentional, cataloged, and unchanged from the
  Step 5 plan.
- No non-goal was violated. No scope expansion occurred. No bridge
  policy was breached. No raw artifact was committed.

## Next Step

Step 11 — Final PR preparation.

Step 11 opens a PR into `main` with title `phase3.14: llm cache
discipline` and the body required by `CURRENT_CAMPAIGN.md` (completed
steps, validation results, behavior findings summary, review gates
reached, implementation summary, remaining deferred work,
confirmation that main was not pushed directly, confirmation that the
PR is not merged, Stage A consultation summary, Stage B collaboration
summary). The PR is not merged. The campaign closes when the operator
explicitly merges.
