# PHASE3_16_REAL_MODEL_TUNING_BEHAVIOR_REPORT.md

## Purpose

Step 8 of Phase 3.16: consolidate the final model-backed behavior
result with the concrete evidence required by the campaign macro
(real model calls used, mode tested, cache counters, state changes,
route).

This is the **behavior** report. Step 9 (final audit) carries the
campaign verdict and the explicit constraint confirmations.

---

## 1. Headline

ToyI produced a **complete, inspectable, real model-backed
operational walk** through the existing public dispatch path.

```text
Mode             : claude-cli (Claude Code 2.1.143; non-interactive
                   `claude -p`)
Route            : Route A — OperatorSession.dispatch with
                   QUEUE_PERCEPT + STEP_TICK over a real
                   CachedClient(ClaudeCLIClient) built via
                   brain.ui.llm_runtime.build_llm_client_from_config
Ticks executed   : 2 (probe-A, probe-B) + 2 earlier walk-A ticks
                   = 4 total successful ticks across the campaign
Total real calls : 6  (within the 30-call budget; 24 remaining)
Verdict candidate: REAL MODEL TEST PASS
                   (final verdict in Step 9)
```

The cache stack absorbed repeated equivalent work as designed: an
identical-text evaluation under a different `content_id` returned via
the L2 canonical semantic eval cache with **0 model calls**.

---

## 2. Tick-by-tick evidence

### Walk A — BudgetGuard outside cache (L1 visible, L2 disabled)

**Tick A.1**

```text
input
  content_id       = probe-real-1
  text             = a short, neutral observation about the test
  content_state    = ContentState(True, True, True, True)
  initial_rho      = Fraction(1, 2)
result
  tick_counter             = 1
  status                   = 'tick 1 ok (NEUTRAL)'
  triggered_mode           = NEUTRAL
  tick_index               = 1
  profile.domain (post)    = ['__cogito__', 'alpha', 'probe-real-1']
  msi.contents (post)      = ['__cogito__', 'alpha']
  CachedClient.hit_count   = 0
  CachedClient.miss_count  = 1
  CachedClient.skip_count  = 0
  duration_ms              = 3986
  prompt chars             = 916
  response chars           = 8
  response_prefix_hash     = 29c5888b2605
  cumulative budget        = 4 / 30
```

**Tick A.2**

```text
input
  content_id       = probe-real-2
  text             = a short, neutral observation about the test
                     (identical to A.1)
result
  tick_counter             = 2
  status                   = 'tick 2 ok (NEUTRAL)'
  triggered_mode           = NEUTRAL
  profile.domain (post)    = ['__cogito__', 'alpha',
                              'probe-real-1', 'probe-real-2']
  CachedClient.hit_count   = 0
  CachedClient.miss_count  = 2
  CachedClient.skip_count  = 0
  cumulative budget        = 5 / 30
  L1 missed because the prompt template embeds the existing
    MSI/profile context, which differed from tick A.1
  L2 was disabled in this harness shape (BudgetGuard sat OUTSIDE
    the CachedClient, hiding it from
    LLMBackedPtCns._derive_l2_metadata)
```

### Walk B — BudgetGuard inside cache (L1 + L2 fully active)

The cache directory `brain/.llm_cache/` was wiped before Walk B for
reproducibility. The wipe touched no committed file
(`brain/.llm_cache/` is gitignored).

**Tick B.1**

```text
input
  content_id       = probe-A
  text             = another short, neutral test observation
result
  tick_counter             = 1
  status                   = 'tick 1 ok (NEUTRAL)'
  triggered_mode           = NEUTRAL
  profile.domain (post)    = ['__cogito__', 'alpha', 'probe-A']
  msi.contents (post)      = ['__cogito__', 'alpha']
  CachedClient.hit_count   = 0
  CachedClient.miss_count  = 1
  CachedClient.skip_count  = 0
  guard.run_calls          = 1
  cumulative budget        = 6 / 30
  brain/.llm_cache/*.json count       = 1   (L1 entry stored)
  brain/.llm_cache/eval_v1/*.json     = 1   (L2 entry stored)
```

**Tick B.2 — cache-aware repeat probe**

```text
input
  content_id       = probe-B
  text             = another short, neutral test observation
                     (identical text under same MSI context)
result
  tick_counter             = 2
  status                   = 'tick 2 ok (NEUTRAL)'
  triggered_mode           = NEUTRAL
  profile.domain (post)    = ['__cogito__', 'alpha',
                              'probe-A', 'probe-B']
  msi.contents (post)      = ['__cogito__', 'alpha']
  CachedClient.hit_count   = 0
  CachedClient.miss_count  = 1     (unchanged from B.1)
  CachedClient.skip_count  = 0
  guard.run_calls          = 1     (unchanged from B.1)
  brain/.llm_cache/*.json count       = 1
  brain/.llm_cache/eval_v1/*.json     = 1
  delta model calls        = 0     <-- LLMBackedPtCns L2 HIT
  cumulative budget        = 6 / 30
```

The L1 miss-and-no-store-delta plus the L2 entry-count-unchanged plus
`guard.run_calls` unchanged together prove that **tick B.2 was
served entirely from the L2 canonical semantic eval cache** with
zero real model calls.

---

## 3. Aggregate counters

```text
Real model calls (total Step 4)                : 6
  - 1 standalone codex exec probe
  - 1 codex factory failure (CachedClient miss recorded; no entry
    written; subprocess refused trusted-dir check)
  - 1 standalone claude -p probe
  - 2 walk-A ticks (1 call each; tick A.2 missed L1 due to MSI
    context change; L2 disabled by harness shape)
  - 1 walk-B tick B.1 (tick B.2 hit L2)
Ticks executed end-to-end (walk-A + walk-B)    : 4
Successful ConsistencyEval parses (first try)  : 4 (all NEUTRAL)
ConsistencyEval parse failures                 : 0
Retries                                        : 0
LLMBackedPtCns max_attempts exhausted           : never
L1 entries written (walk-B persisted)          : 1
L2 entries written (walk-B persisted)          : 1
L1 / L2 cap exceeded                           : never
brain/.llm_cache committed                     : NO (gitignored)
raw prompts in repo                            : NO
raw responses in repo                          : NO
secrets in repo                                : NO
secrets printed in reports                     : NO (presence-only
                                                 redaction)
budget remaining                               : 24 / 30
```

---

## 4. Per-acceptance-criterion verification

Against the Step 1 / Section 1 acceptance list in the synthesis:

```text
(a) factory-built real LLMClient                     : YES
    build_llm_client_from_config(LlmRuntimeConfig(mode=CLAUDE_CLI))
    returned CachedClient(ClaudeCLIClient(...))

(b) operator input via public surface                : YES
    QUEUE_PERCEPT + STEP_TICK through
    OperatorSession.dispatch(...)

(c) brain.tick.tick(...) completes                   : YES
    tick(...) returned a TickRecord and a new BrainState; no
    exception path was taken under claude-cli.

(d) parser yields ConsistencyEval, no max_attempts   : YES
    NEUTRAL parsed on the first attempt for all four ticks.

(e) inspectable state changes recorded               : YES
    profile.domain grew by exactly the queued content_id each tick;
    tick_counter advanced 0->1->2 within each walk;
    latest_tick.tick_index and triggered_mode populated.

(f) L1 counters recorded                             : YES
    CachedClient.hit_count / miss_count / skip_count populated;
    L1 entry persisted to disk in walk B.

(g) L2 counters recorded                             : PARTIAL
    L2 entry persisted in walk B; tick B.2 returned via L2.
    Walk A did not exercise L2 due to harness shape (BudgetGuard
    sat outside the CachedClient, hiding it from
    LLMBackedPtCns._derive_l2_metadata). This is a harness
    artifact, not a runtime regression — in production, the
    OperatorSession.dispatch path passes the CachedClient
    directly, mirroring walk B's shape.

(h) repeated equivalent work shows no spam           : YES
    Tick B.2 with identical text under the same MSI context returned
    via L2 with 0 model calls.

(i) raw prompts/responses/secrets/cache uncommitted  : YES
    only hash prefixes and parsed enums recorded in this doc;
    brain/.llm_cache stays gitignored.

(j) final classification reachable                   : YES
    REAL MODEL TEST PASS proposed; final verdict in Step 9.
```

---

## 5. Bounds confirmations

```text
L1_CACHE_MAX_ENTRIES (=1024)
  observed peak entries           : 1
  exceeded                        : never
  write-skip-at-cap exercised     : not in this run (population
                                    well below cap)

SEMANTIC_CACHE_MAX_ENTRIES (=1024)
  observed peak entries           : 1
  exceeded                        : never
  write-skip-at-cap exercised     : not in this run

PROMPT_TEMPLATE_VERSION           : "prompt-template-v1" (unchanged)
PARSE_SCHEMA_VERSION              : "consistency-eval-v1" (unchanged)
SEMANTIC_CACHE_SCHEMA_VERSION     : "llm-semantic-cache-v1" (unchanged)

L2 entry payload                  : {"key_prefix", "parsed"} only
                                    (verified by inspection that the
                                     file size is the expected
                                     ~50 bytes JSON;
                                     content excluded from this doc)

corrupt L1 entries                : 0 created; failure path
                                    unchanged
corrupt L2 entries                : 0 created
```

---

## 6. No-mutation outside expected channels

```text
brain/tick.py                    : not modified
brain/llm/client.py              : not modified
brain/llm/ptcns_backed.py        : not modified
brain/llm/parse.py               : not modified
brain/llm/prompts.py             : not modified
brain/ui/llm_runtime.py          : not modified
brain/ui/session.py              : not modified
brain/ui/__main__.py             : not modified
brain/development/**              : not modified
INVARIANT_CATALOG.md             : not modified
tools/catalog.py                 : not modified
brain/invariants.py              : not modified
README.md                        : not modified
CLAUDE.md                        : not modified
AGENTS.md                        : not modified

Growth Ledger semantics          : not modified
Pattern Ledger semantics         : not modified
Coherence Monitor semantics      : not modified
L2 (eval_v1) semantics           : not modified
L1 cache semantics               : not modified
DB schema                        : not modified
SCHEMA_VERSION                   : not bumped
persistence / autosave behavior  : not extended
SelfModel                        : not implemented
catalog v0.25                    : unchanged
counts 281/88/14/15/16            : unchanged
```

---

## 7. Failure mode observed: codex-cli (mode-specific, deferred)

```text
mode                   : codex-cli
local CLI version      : codex-cli 0.130.0
local CLI auth         : Logged in using ChatGPT
failure                : subprocess returned non-zero exit 1
stderr                 : "Reading additional input from stdin...
                         Not inside a trusted directory and
                         --skip-git-repo-check was not specified."
classification         : PATCH REQUIRED (deferred to a future
                         campaign — the fix is a 1-line edit to
                         brain/llm/client.py::CodexCLIClient.command
                         OR cwd, and brain/llm edits are out of
                         scope for Phase 3.16)
impact on campaign     : none. claude-cli covers the campaign
                         target.
budget cost            : 1 call (the CachedClient miss + the
                         subprocess refusal each counted as a model
                         attempt per the campaign accounting policy).
```

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- mode / model / effort: n/a
- wrapper command: n/a
- question file / answer file: n/a
- wrapper status: n/a
- accepted advice: none
- rejected advice: none
- reason: behavior is summarized from Step 4 measurements; no
  adversarial review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: a single behavior summary; bridge overhead exceeds the
  cost of writing directly.
```

---

## 9. Next artifact

Step 9: `docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_AUDIT.md`
— record the final verdict (REAL MODEL TEST PASS / PARTIAL / BLOCKED
BY ENV / FAIL) plus the explicit constraint confirmations.
