# PHASE3_16_REAL_MODEL_TUNING_FINDINGS.md

## Purpose

Step 5 of Phase 3.16: classify the Step 4 results, identify
follow-ups, and decide the path forward (Step 6 patch plan vs.
Step 8 behavior report).

---

## 1. Classification

```text
Overall campaign verdict candidate: REAL MODEL TEST PASS

Per-mode classification:

  claude-cli      : WORKS
                    - 2 ticks through OperatorSession.dispatch
                      completed (tick 1 + tick 2)
                    - ConsistencyEval (NEUTRAL) parsed on the first
                      attempt
                    - profile.domain grew with each tick
                    - L1 (CachedClient) counters observable
                    - L2 (canonical eval cache) hit verified — same
                      text under different content_id returned via
                      L2 with 0 model calls
                    - cache files contained no raw prompt / response;
                      L2 payload restricted to {"key_prefix", "parsed"}
                    - cache directory remains gitignored
                    - 5 model calls consumed (1 standalone probe + 2
                      tick #1+#2 in walk A + 1 standalone +
                      1 walk-B tick #1)
                      (walk B's tick #2 hit L2 and consumed 0 calls)

  codex-cli       : PATCH REQUIRED (deferred to Phase 3.17 or later)
                    - codex-cli 0.130.0 refuses to run from cwd=/tmp
                      without --skip-git-repo-check
                    - 1 call consumed at factory invocation
                      (the CachedClient miss was recorded; the inner
                      subprocess exited non-zero)
                    - this is a CLI-version incompatibility, not a
                      runtime semantics issue
                    - the fix is a single-line adjustment to
                      brain/llm/client.py::CodexCLIClient.command
                      OR cwd; either touch requires a Step 6 review
                      gate

  anthropic-api   : BLOCKED BY ENV
                    - no ANTHROPIC_API_KEY / BRAIN_ANTHROPIC_API_KEY
                      in env
                    - not attempted; no calls consumed
```

---

## 2. Bugs / regressions

```text
none observed in the kernel runtime
the runtime cache stack (L1 + L2) behaves as designed under real
  model load
the public OperatorSession dispatch path accepts a real
  CachedClient(ClaudeCLIClient) and executes a complete tick()
brain/tick.py was not touched and was not exercised in a way that
  exposed any new failure mode
```

---

## 3. Operator UX surprises

```text
1. CodexCLIClient default cwd='/tmp' (intended to avoid auto-
   discovering the parent repo's hooks / CLAUDE.md) collides with
   codex-cli 0.130.0's trusted-directory check. The failure mode is
   clean (CachedClient miss recorded but no entry written; session
   error_message set; no kernel mutation), but the message is opaque
   for a first-time operator. A small one-line fix would resolve it
   without changing any semantic behavior.

2. The cache trace events (llm.cache_hit / llm.cache_miss /
   llm.cache_skip / llm.semantic_cache_*) are emitted to the
   NullTracer by default through OperatorSession.dispatch. Counters
   on the CachedClient instance ARE observable, but trace-stream
   observers (if any) get nothing. Wiring a tracer through dispatch
   would require a runtime behavior change and is out of scope.

3. The PROMPT_TEMPLATE asks for "exactly one word: PRESERVE, DAMAGE,
   or NEUTRAL" — but the parser is strict and lists all three valid
   tokens in the template, which means a verbose model that echoes
   the prompt will appear ambiguous to the parser. claude-cli
   returns single-token "PRESERVE" / "NEUTRAL" / "DAMAGE" cleanly;
   codex-cli's `codex exec` non-interactive output prepends headers
   that contain the prompt echo, which would have caused a parse
   failure if codex-cli had not failed earlier at the trusted-dir
   check. This is recorded for awareness; the v0.25 baseline is not
   threatened.
```

---

## 4. Proposed deferred follow-ups (NOT in flight)

```text
F1. codex-cli compatibility patch (single-line)
    - file:    brain/llm/client.py
    - change:  add '--skip-git-repo-check' to CodexCLIClient.command
               default, OR adjust cwd to the resolved repo root
    - risk:    low (the flag is documented and stable on
               codex-cli >= 0.x; cwd change has wider implications
               because it allows codex to discover the parent repo's
               CLAUDE.md / hooks)
    - catalog: no new row family expected; one fixture refresh
               may be needed for I-LLMTOG-16 / I-LLMTOG-17 if any
               counter / shape audit references the exact command
               tuple
    - dependency: a future campaign that authorizes the brain/llm
                  edit

F2. OperatorSession.dispatch tracer wiring
    - file:    brain/ui/session.py + brain/tick.py
    - change:  thread an operator-supplied CognitionTracer down to
               the LLMBackedPtCns retry shell so trace events
               (llm.cache_*, llm.semantic_cache_*, parse.*) are
               observable from outside the cache instance
    - risk:    medium — touches brain/tick.py (out of scope for
               Phase 3.16; tick semantic surface)
    - catalog: at least one I-LLM* row may need to be promoted from
               OBSERVED to REQUIRED for the new observability
    - dependency: requires its own review-gated mini-campaign

F3. parser ambiguity hardening (optional)
    - file:    brain/llm/parse.py and/or brain/llm/prompts.py
    - change:  either tolerate verbose tools that echo the prompt
               (e.g., parse only the LAST whitespace-separated
               token that matches one of {PRESERVE, DAMAGE, NEUTRAL})
               OR add a "strip-echo" pre-step that drops the leading
               header block before parsing
    - risk:    medium — changes parsing semantics, requires
               PARSE_SCHEMA_VERSION bump, invalidates all L2 entries
    - catalog: bump PARSE_SCHEMA_VERSION; touches L2 keying
    - dependency: own review-gated campaign (NOT in Phase 3.16)

F4. anthropic-api smoke (if a budget is available)
    - file:    /tmp harness only
    - change:  none in the repo
    - dependency: ANTHROPIC_API_KEY or BRAIN_ANTHROPIC_API_KEY must
                  be available; absent in this checkout
```

None of F1-F4 are required to deliver the Phase 3.16 campaign target,
which has been met: ToyI produced a concrete inspectable model-backed
operational walk through claude-cli.

---

## 5. Items that do NOT block the campaign

```text
- codex-cli construction failure — claude-cli covers the campaign
  target
- anthropic-api absence — claude-cli covers the campaign target
- tracer-not-wired-through-dispatch — CachedClient counters and L2
  on-disk presence cover the observability requirement
- prompt-echo parse-ambiguity risk — does not manifest with
  claude-cli's clean single-token output
- existing brain/.llm_cache contents (gitignored) — not committed
```

---

## 6. Decision

```text
Step 4 produced a "works" result for claude-cli and did not require
any runtime code change to deliver the campaign target.

Per the macro sequence in CURRENT_CAMPAIGN.md Step 5:

  "If works/partial and no runtime patch required:
       proceed to Step 8/final report."

DECISION: skip Step 6 (patch plan) and Step 7 (patch implementation);
          proceed to Step 8 (behavior report) and Step 9 (final
          audit).

The codex-cli patch (F1) is recorded as a deferred follow-up for a
future campaign that explicitly authorizes a brain/llm edit. Phase
3.16 ships with the observation that codex-cli is locally available
but not compatible with the current CodexCLIClient defaults.
```

---

## 7. Real model call accounting (cumulative)

```text
Step 4 total                      : 6 / 30
Step 5 (this doc, no real calls)  : 0
                                    --
Cumulative after Step 5           : 6 / 30
Remaining budget                  : 24
```

Steps 8 + 9 are documentation-only and expected to consume 0
additional model calls. The campaign will close with **6 / 30** real
model calls used.

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
no raw prompts / responses / secrets / cache files committed
gate_runner                      : will run before commit
catalog v0.25                    : unchanged
counts                           : 281 / 88 / 14 / 15 / 16 unchanged
real model calls used            : 6 / 30
```

---

## 9. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: findings are derivable from Step 4 measurements; no
  adversarial review needed for the documented classification.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: a single self-contained findings doc; bridge overhead
  exceeds the cost of writing directly.
```

---

## 10. Next artifact

Step 8: `docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_BEHAVIOR_REPORT.md`
— consolidate the final model-backed behavior summary with the
concrete evidence required by the campaign macro (calls, cache
counters, state changes, mode, route).
