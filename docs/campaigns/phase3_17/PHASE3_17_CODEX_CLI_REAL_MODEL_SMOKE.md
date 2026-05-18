# PHASE3_17_CODEX_CLI_REAL_MODEL_SMOKE.md

## Verdict

```text
CODEX RUNTIME PASS
```

After the Phase 3.17 Step 3 patch (`--skip-git-repo-check` added to
`CodexCLIClient.command` and to `_build_codex_cli_client`), the
codex-cli mode now drives a **complete model-backed tick** through
the public `OperatorSession.dispatch` path with `codex-cli 0.130.0`
and the existing factory wiring. The Phase 3.16 Step 4 trusted-dir
blocker is resolved.

---

## 1. Environment probe (no secrets, presence only)

```text
codex binary path : /usr/local/bin/codex
codex version     : codex-cli 0.130.0
codex auth        : "Logged in using ChatGPT" (token NOT shown)
flag presence     : --skip-git-repo-check is documented in
                    "codex exec --help"

BRAIN_LLM_MODE          : not set
BRAIN_ANTHROPIC_API_KEY : not set
ANTHROPIC_API_KEY       : not set
```

No environment variable bumps the runtime out of OFFLINE on its
own; CODEX_CLI was selected explicitly through the harness using
`LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI, ...)`.

---

## 2. Patched factory build (no real call)

The harness verified the post-Step-3 factory output before any model
call:

```text
factory_built:
  outer class                : CachedClient
  inner class                : CodexCLIClient
  inner.command shape        : ["<codex-path>", "exec",
                                "--skip-git-repo-check"]
  inner.cwd                  : "/tmp"
```

`<codex-path>` is the resolved absolute path returned by `_which`
inside the factory. The three-element tuple shape matches the Step
3 patch exactly; `cwd` remains `/tmp` per the Phase 3.11 corrigenda
Section 7 lock.

---

## 3. Smoke walk through OperatorSession.dispatch

The harness lives at `/tmp/phase3_17_codex_smoke.py` (intentionally
NOT committed). It assembles:

```text
shape: CachedClient(BudgetGuardClient(CodexCLIClient))
       - CachedClient at the outer position so LLMBackedPtCns can
         detect cache wrapping (Phase 3.14 L2 surface is reachable).
       - BudgetGuardClient inserted between cache and inner codex
         so every real model attempt is counted exactly once and
         hard-capped at 5 for the step.
       - CodexCLIClient is the production factory output (with
         --skip-git-repo-check in command[2]).
```

The hard cap is **5 real model attempts inside the harness**; the
campaign-level cap is **20**.

### 3.1 Route walked

```text
build initial cogito-only BrainState
build OperatorSession(state=state)
dispatch(Command(QUEUE_PERCEPT, payload=QueuePerceptPayload(
    content_id="phase317-codex-1",
    text="a short neutral observation about codex compatibility",
    content_state=ContentState(True, True, True, True),
    initial_rho=Fraction(1, 2),
)))
dispatch(Command(STEP_TICK), client=CachedClient(BudgetGuard(CodexCLIClient)))
```

### 3.2 Result (tick #1)

```text
dispatch_outcome              = ok
session.status_message        = "tick 1 ok (NEUTRAL)"
session.error_message         = ""
session.tick_counter          = 1
latest_tick.tick_index        = 1
latest_tick.triggered_mode    = NEUTRAL
profile.domain                = ["__cogito__", "phase317-codex-1"]
msi.contents                  = ["__cogito__"]
queue_size                    = 0   (the queued payload was consumed)
growth_ledger.event_count     = 2
growth_ledger.counts_by_type  :
    tick_succeeded            = 1
    profile_domain_added      = 1
    (all other event types    = 0)
tick_duration_ms              = 12_487
```

ConsistencyEval `NEUTRAL` parsed cleanly on the first attempt. The
codex `exec` output with `--skip-git-repo-check` did **not** prepend
the verbose trusted-dir warning headers that Phase 3.16 Step 5
flagged as a future parse-ambiguity risk, so the strict parser
accepted the response as-is.

### 3.3 Cache behavior

```text
CachedClient.hit_count       = 0
CachedClient.miss_count      = 1
CachedClient.skip_count      = 0
guard.run_calls              = 1
guard.successes              = 1
guard.failures               = 0
guard.attempt_1.duration_ms  = 12486

brain/.llm_cache  *.json pre  = 1 (existing Phase 3.16 L1 entry)
brain/.llm_cache  *.json post = 2 (new L1 entry written on miss)
brain/.llm_cache/eval_v1/*.json pre  = 1 (existing Phase 3.16 L2)
brain/.llm_cache/eval_v1/*.json post = 2 (new L2 entry written)
```

The new L1 and L2 entries are in a Codex-isolated namespace
(`_derive_l2_metadata` picks up the inner BudgetGuardClient class
name as the namespace key, isolating these entries from the prior
claude-cli entries already on disk). All cache files remain under
the gitignored `brain/.llm_cache/` directory; none are committed.

### 3.4 Prompt / response sizes (no body content shown)

```text
prompt  chars       = 954
prompt  hash prefix = dfd33f80674d
response chars      = 8       (e.g. "NEUTRAL\n")
response hash prefix = 29c5888b2605
```

No raw prompt body or raw model response appears anywhere in this
report. The response hash prefix `29c5888b2605` matches the
Phase 3.16 Step 4 hash prefix for the same parsed enum, which is
the sha256 of the model's bare `"NEUTRAL\n"` token; it leaks no
prompt-specific or session-specific data.

---

## 4. Constraint sanity

```text
brain/tick.py                       : not modified
brain/llm/parse.py                  : not modified
brain/llm/prompts.py                : not modified
brain/llm/ptcns_backed.py           : not modified
brain/ui/session.py                 : not modified
brain/ui/__main__.py                : not modified
INVARIANT_CATALOG.md                : not modified
tools/catalog.py                    : not modified
README.md                           : not modified
brain/.llm_cache contents           : not committed (gitignored)
raw prompts / responses             : not committed (only hashes,
                                      char counts, parsed enum)
secrets                             : not present in repo, not
                                      printed
gate_runner                         : ran green BEFORE this smoke
                                      (Step 3 commit 2239b7f)
catalog v0.25                       : unchanged
counts                              : 281/88/14/15/16 unchanged
real model calls used               : 1 / 20
```

---

## 5. Real model call accounting

```text
Step 1 (mission sync)               : 0
Step 2 (patch plan)                 : 0
Step 3 (apply codex fix)            : 0
Step 4 (this smoke)                 : 1   (single successful tick)

Cumulative campaign calls           : 1 / 20
Remaining budget                    : 19
```

Step 4's local hard cap is 5; we consumed 1. The smoke ends here;
the codex-cli compatibility question is answered.

---

## 6. Stop conditions check

```text
budget reaches 20                    : NO (1 / 20 used)
3 consecutive parse failures         : NO (0 parse failures)
real model unavailable               : NO (codex 0.130.0 + ChatGPT
                                       login + --skip-git-repo-check
                                       path produced a clean tick)
runtime code change beyond Step 3    : NO (the Step 3 patch was
                                       sufficient)
network transient                    : NO (1 call returned cleanly
                                       in 12.5s)
```

No stop condition fired. The smoke ran to completion as designed.

---

## 7. What this smoke does NOT prove

```text
- Codex's parse-failure behavior under verbose model output is not
  exercised. The first attempt with a short, clearly-instructed
  prompt produced a clean single-token response.
- Larger or more contentious prompts may still hit parser
  ambiguity (Phase 3.16 Step 5 F3 follow-up). That risk is
  deferred to a parser-hardening campaign.
- Long-running / multi-tick codex workloads are not exercised.
- Tracer wiring through OperatorSession.dispatch is still NOT in
  place (Phase 3.16 F2 follow-up). We rely on inspectable counters
  on the CachedClient and BudgetGuard instances.
- The Phase 3.16 anthropic-api smoke remains BLOCKED BY ENV
  (no ANTHROPIC_API_KEY in this checkout). That is unrelated to
  the codex-cli compatibility question.
- No L1 / L2 cache cap behavior is exercised here (one entry each;
  far below the 1024-entry caps).
```

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the result of the smoke is a single bounded measurement;
  the rationale and the patch shape are unambiguous from Step 2's
  plan; no external review was required to interpret the run.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer of the harness and
  this report; both are bounded and self-contained.

Stage C.1 flow orchestration:
- used: no
- reason: the campaign-level Phase 3.17 policy explicitly
  forbids Stage C.1 for the real codex-cli loop.
```

Stage A / B / C.1 transport fields (all not-applicable):

```text
mode / model / effort           : n/a
wrapper command                 : n/a
question/answer files           : n/a
allowed files / prompt file     : n/a
manifest path / validation      : n/a
wrapper status / exit code      : n/a
files changed                   : none beyond this report
accepted / rejected advice      : none
```

---

## 9. Next artifact

Step 5: `docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_SYNTHESIS.md`
— the core processing-window research synthesis. The codex-cli
runtime is now available for any future processing-window probe
that wants a real model-backed mode (subject to the campaign-level
20-call budget; remaining = 19).
