# PHASE3_16_MODEL_AVAILABILITY_BASELINE.md

## Purpose

Step 3 of Phase 3.16: probe local model-backed mode availability and
exercise a deterministic mock / offline tick route through the public
`OperatorSession.dispatch(...)` path. **Zero real model calls.**

Confirms that the runtime factory + dispatch + tick stack is healthy
before Step 4 burns any of the 30-call budget on a real model.

---

## 1. Model availability probe

Secrets redacted; presence-only reporting for env keys.

```text
=== codex ===
which:   /usr/local/bin/codex
version: codex-cli 0.130.0
login:   Logged in using ChatGPT

=== claude ===
which:   /home/leah/.local/bin/claude
version: 2.1.143 (Claude Code)

=== env keys (presence only) ===
BRAIN_LLM_MODE          = [absent]
BRAIN_ANTHROPIC_API_KEY = [absent]
ANTHROPIC_API_KEY       = [absent]
```

Mode availability matrix:

```text
Mode               PATH found     Configured / authenticated     Eligible
codex-cli          yes (codex)    yes (Logged in using ChatGPT)  YES (preferred)
claude-cli         yes (claude)   trusted local Claude Code      YES
anthropic-api      n/a            no API key in env              NO
```

Phase 3.16 preference order is `codex-cli > claude-cli > anthropic-api`.
The first eligible mode for Step 4 is **codex-cli**.

---

## 2. Runtime factory shape check

`build_llm_client_from_config(LlmRuntimeConfig(mode=...))` was
exercised under three shapes. The probe script lives at
`/tmp/phase3_16_baseline_probe.py` (intentionally not committed; cache
files and harness scripts stay out of the repo per the Phase 3.16
constraints).

```text
parse_llm_runtime_args(["--llm-mode", "mock", "--llm-mock-response", "PRESERVE",
                        "--llm-mock-response", "NEUTRAL"], env={}):
  resolved mode       = mock
  enable_cache        = False
  mock_responses len  = 2
  startup line        = "brain.ui: llm runtime mode = mock
                         (deterministic mock; no network, no shell)"
  factory client cls  = MockClient

parse_llm_runtime_args([], env={}):
  resolved mode       = offline
  factory client cls  = OfflineStandInClient

parse_llm_runtime_args(["--llm-mode", "codex-cli"], env={}):
  resolved mode             = codex-cli
  enable_cache              = True       # default-on for model-backed
                                         #   (Phase 3.14 LOCK B / I-LLMCACHE-02)
  codex_cli_executable      = codex
  (factory NOT called; Step 4 owns the real construction)
```

Observations:

```text
- The factory accepts the three mode shapes Phase 3.16 cares about
  (mock, offline, codex-cli).
- The model-backed shape (codex-cli) defaults enable_cache=True. The
  Phase 3.14 cache discipline (L1 default-on for model-backed modes,
  L1 bounded at 1024 from Phase 3.15) is engaged automatically when
  Step 4 builds the real codex client.
- No environment side effects: parse_llm_runtime_args reads only the
  supplied env dict; build_llm_client_from_config only does a PATH
  lookup for CLI modes (not exercised here).
```

---

## 3. Deterministic baseline tick — OfflineStandInClient

The full public dispatch path was exercised once under
`OfflineStandInClient` (the default `--llm-mode offline` client).

Pre-tick:

```text
tick_counter            = 0
state.profile.domain    = ['__cogito__', 'alpha']
state.msi.contents      = ['__cogito__', 'alpha']
event_queue size        = 0
```

Commands issued:

```text
session.dispatch(make_command(OperatorCommand.QUEUE_PERCEPT,
    content_id="probe-baseline",
    text="a short, neutral observation about the baseline probe",
    content_state=ContentState(True, True, True, True),
    initial_rho=Fraction(1, 2),
))
session.dispatch(make_command(OperatorCommand.STEP_TICK),
                 client=OfflineStandInClient())
```

Post-tick:

```text
tick_counter                       = 1
status_message                     = "tick 1 ok (MODE_C)"
error_message                      = ""
OfflineStandInClient.calls         = 1
state.profile.domain               = ['__cogito__', 'alpha', 'probe-baseline']
state.msi.contents                 = ['__cogito__', 'alpha', 'probe-baseline']
latest_tick.triggered_mode         = MODE_C
latest_tick.tick_index             = 1
event_queue size                   = 0      (dequeued after success)
```

Verification:

```text
- One client call observed (offline_client.calls == 1). The
  retry shell did not invoke max_attempts.
- BrainState mutated: profile and MSI now include the new
  content. The Phase 3.14 / 3.15 L1 + L2 caches were not exercised
  because OfflineStandInClient is not wrapped in CachedClient.
- triggered_mode = MODE_C: a normal positive-bias tick result.
- No real model calls.
```

---

## 4. Deterministic baseline tick — MockClient(["PRESERVE", "NEUTRAL"])

Run again with the explicit `MockClient` constructed via the runtime
factory.

```text
session2.dispatch(make_command(OperatorCommand.QUEUE_PERCEPT,
    content_id="probe-mock",
    text="another short neutral observation",
    content_state=ContentState(True, True, True, True),
    initial_rho=Fraction(1, 2),
))
session2.dispatch(make_command(OperatorCommand.STEP_TICK),
                 client=mock_client)
```

Result:

```text
tick_counter                  = 1
status_message                = "tick 1 ok (MODE_C)"
MockClient.calls len          = 1                # one prompt consumed
latest_tick.tick_index        = 1
```

Verification:

```text
- MockClient consumed exactly 1 of its 2 canned responses.
- The first response (PRESERVE) parsed cleanly into
  ConsistencyEval.PRESERVE; no retry attempt was needed.
- No real model calls.
```

---

## 5. Cache state

```text
brain/.llm_cache/                : not present (no model-backed run yet)
brain/.llm_cache/*.json count    : 0
brain/.llm_cache/eval_v1/*.json  : 0
```

This is the expected pre-Step-4 baseline. The directory only appears
once the L1 `CachedClient` writes its first miss-write entry, which
requires a model-backed mode.

---

## 6. Constraint sanity check

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
Gate runner                      : all 5 gates PASS
Catalog                          : v0.25 banner intact
Counts                           : 281 / 88 / 14 / 15 / 16
Real model calls used so far     : 0 / 30
```

---

## 7. Step 4 plan

```text
Mode to test first       : codex-cli (via build_llm_client_from_config)
Backup mode              : claude-cli (only if codex-cli fails on
                           construction or first call)
Tertiary mode            : anthropic-api (NOT available; no env key)
Route                    : Route A (OperatorSession dispatch), with
                           Route C (direct LLMBackedPtCns harness)
                           as the immediate fallback if Route A
                           cannot be exercised through the public
                           public surface in /tmp.
Initial input            : a single short, neutral observation
                           ("a short, neutral observation about the
                            test environment")
Initial call accounting  : 1 real call expected, 0 retries
Second probe             : repeat the same prompt and confirm the L1
                           CachedClient returns a hit (0 model calls).
Cache hygiene check      : confirm L1 entry count and L1 file size,
                           and that the directory remains gitignored.
Stop trigger             : cumulative model calls >= 30; or 10
                           consecutive parse failures; or stop
                           condition documented in synthesis Step 8.
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
- reason: baseline probe is mechanical and self-contained.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the only writer for the baseline report.

Stage C.1 flow orchestration:
- used: no
- reason: single self-contained doc; bridge overhead exceeds the
  cost of writing directly.
```

---

## 9. Next artifact

Step 4: `docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_RUN.md` —
construct a real `codex-cli` client via `build_llm_client_from_config`
and run a minimal model-backed tick route, recording call counts,
parse outcomes, L1 + L2 counter movement, and state changes.
