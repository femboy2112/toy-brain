# PHASE3_16_REAL_MODEL_TUNING_RUN.md

## Purpose

Step 4 of Phase 3.16: execute a **real model-backed operational walk**
of ToyI through the existing public dispatch path, while keeping
within the 30-call campaign budget. This step performs the actual
model calls; Steps 1-3 set up routing, synthesis, and a deterministic
baseline.

The harness scripts live under `/tmp` (intentionally non-committed).
Raw prompts and raw model responses are NOT included in this report
(only hash prefixes / byte counts / parsed enums).

---

## 1. Real model call accounting (cumulative)

```text
prior steps (Step 1, 2, 3)                           : 0 calls
Step 4 probe A — `codex exec "...PRESERVE"`          : 1 call  (cumulative 1)
Step 4 factory-built CodexCLIClient through dispatch : 1 call  (cumulative 2)
Step 4 probe B — `claude -p ...PRESERVE`             : 1 call  (cumulative 3)
Step 4 first claude-cli walk (tick 1 + tick 2)       : 2 calls (cumulative 5)
Step 4 second claude-cli walk (L2 demo, tick 1+2)    : 1 call  (cumulative 6)
                                                       ---------
Total real model calls in Step 4                     : 6  / 30
```

All six attempts are counted as model-backed attempts per the
campaign accounting policy ("Count every model-backed attempt,
including retries, timeouts, parse failures, and nonzero exits").

---

## 2. First real-model attempt: codex-cli through the factory

### Setup

```text
LlmRuntimeConfig(mode=codex-cli, enable_cache=True, timeout_seconds=30.0)
build_llm_client_from_config(...)
  -> outer: CachedClient
  -> inner: CodexCLIClient(command=('/usr/local/bin/codex', 'exec'),
                          cwd='/tmp')
```

The factory wrapped the codex client in `CachedClient` (the
post-Phase-3.14 default for explicit model-backed modes).

### Result

Tick failed before reaching the model. The codex subprocess exited
non-zero with stderr:

```text
Reading additional input from stdin...
Not inside a trusted directory and --skip-git-repo-check was not
specified.
```

Bounded fields:

```text
tick_counter                   = 0
session.error_message          = "tick failure: RuntimeError:
                                  CodexCLIClient: subprocess returned
                                  non-zero exit 1. stderr: ..."
session.state                  = unchanged
CachedClient.miss_count        = 1     (the miss was recorded before
                                        the inner call raised)
CachedClient.hit_count         = 0
CachedClient.skip_count        = 0
brain/.llm_cache               = absent (no entry written; inner raised
                                         before the write step)
real model attempts used       = 1     (cumulative 2)
```

### Diagnosis

`CodexCLIClient` defaults `cwd='/tmp'` so the subprocess does not
auto-discover the parent repo's `CLAUDE.md` / hooks (see comments in
`brain/llm/client.py`). The current local `codex-cli 0.130.0` enforces
a trusted-directory check unless `--skip-git-repo-check` is passed,
and `/tmp` is not on its trusted list.

The fix would be a small adjustment to `CodexCLIClient.command` (add
`--skip-git-repo-check`) or to `CodexCLIClient.cwd` (run inside the
trusted repo). Either is a runtime-code change to
`brain/llm/client.py` and is **forbidden** without a Step 6 review
gate.

Phase 3.16 Step 4 instead uses the next preferred mode (claude-cli)
to demonstrate the operational walk, and records the codex-cli
finding for the Step 5 / Step 6 patch-required classification.

---

## 3. Probe — `claude -p`

```text
$ timeout 60 claude -p --no-session-persistence \
                      --permission-mode default \
                      'Respond with exactly one word: PRESERVE'
PRESERVE
```

Clean single-token response. Confirms the claude CLI shape is
parser-compatible.

Cumulative model calls after this probe: **3 / 30**.

---

## 4. Route A — OperatorSession dispatch with claude-cli (first walk)

### Setup

```text
LlmRuntimeConfig(mode=claude-cli, enable_cache=True, timeout_seconds=120.0)
build_llm_client_from_config(...)
  -> outer: CachedClient(cache_dir=brain/.llm_cache)
  -> inner: ClaudeCLIClient(command=
                ('claude', '-p',
                 '--no-session-persistence',
                 '--permission-mode', 'default'),
                cwd='/tmp')
```

Harness wraps the factory client in a `BudgetGuardClient` on the
OUTSIDE for accounting:

```text
BudgetGuardClient(CachedClient(ClaudeCLIClient))
```

This shape gives a faithful real-model run, but it hides the
`CachedClient` from `LLMBackedPtCns._derive_l2_metadata`, so L2 is
not enabled in this first walk. The L2 demonstration runs in
section 5 with the guard placed BELOW the cache.

### Walk

Two ticks executed through the public `OperatorSession.dispatch(...)`
surface.

**Tick #1**:

```text
QUEUE_PERCEPT  content_id='probe-real-1'
               text='a short, neutral observation about the test'
               content_state=ContentState(True, True, True, True)
               initial_rho=Fraction(1, 2)
STEP_TICK      client=guard
```

Result:

```text
tick_counter                       = 1
status_message                     = 'tick 1 ok (NEUTRAL)'
error_message                      = ''
latest_tick.tick_index             = 1
latest_tick.triggered_mode         = NEUTRAL
profile.domain                     = ['__cogito__', 'alpha',
                                      'probe-real-1']
msi.contents                       = ['__cogito__', 'alpha']
event_queue size                   = 0
CachedClient.hit_count             = 0
CachedClient.miss_count            = 1
CachedClient.skip_count            = 0
guard.run_calls                    = 1
prompt chars                       = 916
response chars                     = 8
response_prefix_hash               = 29c5888b2605
duration_ms                        = 3986
cumulative budget used             = 4 / 30
brain/.llm_cache *.json count      = 1   (L1 wrote the miss)
brain/.llm_cache/eval_v1/*.json    = 0   (L2 disabled by harness shape)
```

ConsistencyEval `NEUTRAL` parsed cleanly on the first attempt. Tick
completed. Inspectable kernel state mutated.

**Tick #2** — same text, different `content_id`:

```text
QUEUE_PERCEPT  content_id='probe-real-2'
               text='a short, neutral observation about the test'
               (same text, same ContentState, same rho)
STEP_TICK      client=guard
```

Result:

```text
tick_counter                       = 2
status_message                     = 'tick 2 ok (NEUTRAL)'
profile.domain                     = ['__cogito__', 'alpha',
                                      'probe-real-1', 'probe-real-2']
msi.contents                       = ['__cogito__', 'alpha']
CachedClient.hit_count             = 0
CachedClient.miss_count            = 2
CachedClient.skip_count            = 0
guard.run_calls                    = 2
cumulative budget used             = 5 / 30
response_prefix_hash               = 29c5888b2605
                                     (identical to tick #1's NEUTRAL)
```

L1 missed because the rendered prompt differed: `PROMPT_TEMPLATE`
embeds the existing MSI context, which now includes `probe-real-1`
in the profile's domain. The hashed prompt key is therefore
different.

(L2 would have hit in production because the L2 canonicalization
excludes the evaluated content_id and the new_text is identical
to tick #1. In this harness L2 is disabled by the
`BudgetGuard` placement; the second walk in section 5 covers L2.)

---

## 5. Route A — claude-cli with BudgetGuard INSIDE the cache

### Setup

```text
shape: CachedClient(BudgetGuardClient(ClaudeCLIClient))
```

This is the cache-discipline-faithful shape:

```text
- LLMBackedPtCns sees CachedClient at the outer position via
  isinstance() and enables L2.
- CachedClient absorbs identical-prompt repeats at L1 without
  consulting the budget guard.
- BudgetGuardClient sits between the cache and the real model;
  every real attempt increments the budget exactly once.
```

The pre-existing `brain/.llm_cache` (from section 4) was wiped
before the run so the counters start clean. The wipe is safe because
`brain/.llm_cache/` is gitignored; nothing committed was touched.

### Walk

**Tick #1**:

```text
QUEUE_PERCEPT  content_id='probe-A'
               text='another short, neutral test observation'
               content_state=ContentState(True, True, True, True)
STEP_TICK      client=CachedClient(...)
```

Result:

```text
tick_counter        = 1
status              = 'tick 1 ok (NEUTRAL)'
profile.domain      = ['__cogito__', 'alpha', 'probe-A']
msi.contents        = ['__cogito__', 'alpha']
L1.hit_count        = 0
L1.miss_count       = 1
L1.skip_count       = 0
guard.run_calls     = 1
cumulative budget   = 6 / 30
brain/.llm_cache *.json count        = 1   (L1 wrote)
brain/.llm_cache/eval_v1/*.json count = 1   (L2 wrote)
```

**Tick #2** — different `content_id`, IDENTICAL text:

```text
QUEUE_PERCEPT  content_id='probe-B'
               text='another short, neutral test observation'  # same
STEP_TICK      client=CachedClient(...)
```

Result:

```text
tick_counter         = 2
status               = 'tick 2 ok (NEUTRAL)'
profile.domain       = ['__cogito__', 'alpha', 'probe-A', 'probe-B']
msi.contents         = ['__cogito__', 'alpha']
L1.hit_count         = 0
L1.miss_count        = 1     # unchanged
L1.skip_count        = 0
guard.run_calls      = 1     # unchanged → no model call
tick #2 model calls  = 0     # CONFIRMED L2 hit
cumulative budget    = 6 / 30
brain/.llm_cache *.json count        = 1
brain/.llm_cache/eval_v1/*.json count = 1
```

**This is the cache-aware repeat probe the campaign demands**:
identical evaluated text under a different content_id, with the same
MSI context, hit the L2 canonical eval cache and produced **zero
extra model calls**.

L1 missed because the rendered prompt's content_id field differed
(probe-A vs probe-B), so the SHA-256 prompt hash differed. L2 hit
because L2 canonicalization excludes the evaluated content_id and
keys on (backend_family, model_identity, existing_msi_context,
new_text).

---

## 6. Cache file inventory after Step 4

```text
brain/.llm_cache/                       : present
brain/.llm_cache/*.json (L1)            : 1 file
brain/.llm_cache/eval_v1/*.json (L2)    : 1 file
brain/.llm_cache/eval_v1/<hash>.json    : payload restricted to
                                          {"key_prefix", "parsed"}
                                          (LOCK L / I-LLMCACHE-12;
                                           no raw prompt, no raw
                                           response, no provider
                                           metadata)
```

`brain/.llm_cache/` is gitignored. None of these files are committed.

The L1 cap (`L1_CACHE_MAX_ENTRIES = 1024`) and L2 cap
(`SEMANTIC_CACHE_MAX_ENTRIES = 1024`) are honored trivially: 1 entry
each, well below both caps. Write-skip-at-cap admission was not
exercised because the run did not approach the cap.

---

## 7. Trace event observability

The `OperatorSession` dispatch path does not currently install a
`CognitionTracer` on the kernel client. The L1 / L2 events
(`llm.cache_hit` / `llm.cache_miss` / `llm.cache_skip` /
`llm.semantic_cache_hit` / `_miss` / `_store` / `_skip` /
`parse.success` / `parse.failure`) are emitted to the default
`NullTracer()` and therefore not externally observable from this
harness without a tracer wiring change.

The counters on `CachedClient` (`hit_count` / `miss_count` /
`skip_count`) and the presence of L2 entries on disk are the
inspectable equivalents and were captured above.

Wiring a tracer through `OperatorSession.dispatch` is a runtime
behavior change and is out of scope for Phase 3.16; it could be a
deferred follow-up.

---

## 8. Constraint sanity

```text
brain/tick.py                    : not modified
brain/llm/client.py              : not modified
brain/llm/ptcns_backed.py        : not modified
brain/llm/parse.py               : not modified
brain/llm/prompts.py             : not modified
brain/ui/llm_runtime.py          : not modified
brain/ui/session.py              : not modified
brain/ui/__main__.py             : not modified
INVARIANT_CATALOG.md             : not modified
README.md                        : not modified
brain/.llm_cache contents        : not committed (gitignored)
raw prompts / responses          : not committed; only hash prefixes
                                   and parsed enums in this doc
secrets                          : not present in repo, not printed
gate_runner                      : will be re-run before commit
catalog v0.25                    : unchanged
counts                           : 281 / 88 / 14 / 15 / 16 unchanged
real model calls used            : 6 / 30
```

---

## 9. Tuning levers used and not used

Allowed levers EXERCISED:

```text
- switching from codex-cli to claude-cli after codex-cli failed at
  construction (different available model-backed mode)
- timeout extension from default 30s to 120s for claude-cli to
  accommodate longer subprocess startup
```

Allowed levers NOT NEEDED:

```text
- shorter input text (the default short observation parsed cleanly
  on the first attempt with claude-cli)
- clearer input text
- cache on/off diagnostic
- direct LLMBackedPtCns harness (Route A worked)
```

Forbidden runtime changes considered but NOT applied:

```text
- adding --skip-git-repo-check to CodexCLIClient.command (would fix
  codex-cli, but is a brain/llm/client.py edit — requires Step 6
  review gate)
- changing CodexCLIClient.cwd from '/tmp' to the repo root (same
  category: brain/llm/client.py edit)
- changing the prompt template, parser, or any cache semantics
```

These changes are recorded as candidates for the Step 6 patch plan
should the reviewer decide codex-cli compatibility is in-scope.

---

## 10. Stop conditions check

```text
budget reaches 30                    : NO (6 / 30 used)
10 consecutive parse failures        : NO (0 parse failures observed
                                          for claude-cli)
real model unavailable               : codex-cli failed at process
                                       construction; claude-cli
                                       fully functional
runtime code change seems needed     : YES — for codex-cli only.
                                       claude-cli does NOT need a
                                       runtime change.
```

Step 4 ended on a clean claude-cli walk plus a codex-cli
construction-failure observation. The overall result is "works under
claude-cli; codex-cli requires a small runtime patch."

---

## 11. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- mode / model / effort: n/a
- wrapper command: n/a
- question file / answer file: n/a
- wrapper status: n/a
- accepted advice: none
- rejected advice: none
- reason: Step 4 ran in-process; no external review needed for a
  clean run plus one mode-specific construction failure.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer of this report.

Stage C.1 flow orchestration:
- used: no
- reason: a single well-bounded report; bridge overhead exceeds the
  cost of writing directly.
```

Real-model call accounting (this step):

```text
mode tested: claude-cli (PRIMARY, succeeded)
             codex-cli  (SECONDARY, failed at construction)
calls used in Step 4 : 6
cumulative           : 6 / 30
```

---

## 12. Next artifact

Step 5: `docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_FINDINGS.md`
— classify the result (claude-cli WORKS; codex-cli BLOCKED by trusted-dir refusal) and decide whether to proceed to behavior report or open a Step 6 patch plan.
