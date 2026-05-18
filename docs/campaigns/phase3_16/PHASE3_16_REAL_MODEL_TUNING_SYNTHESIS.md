# PHASE3_16_REAL_MODEL_TUNING_SYNTHESIS.md

## Purpose

Synthesize what "real model operational tuning" means for ToyI in
concrete, measurable terms. This document is Step 2 of the Phase 3.16
campaign. It does **not** run any real model calls; it defines the
routes, success criteria, budget accounting, and stop conditions that
Step 3 (baseline) and Step 4 (real model smoke + tuning) will follow.

This is **not** a proof of consciousness, sentience, awareness,
subjective experience, semantic understanding, agency, or
self-modification. None of those properties are introduced, claimed,
or measured. The campaign instruments existing public surfaces.

---

## 1. What "actual testing" means for ToyI

"Actual testing" of a real model-backed walk means: at least one
complete tick route through the existing public runtime, where the
LLM transport is **not** a mock / offline stand-in, and the
behavior is **inspectable** through public state and bounded
observability surfaces.

A complete model-backed tick route must satisfy ALL of:

```text
(a) The LLM client is constructed via the repo runtime factory:
    brain.ui.llm_runtime.build_llm_client_from_config(...)
    over an LlmRuntimeConfig whose mode is one of:
      LlmRuntimeMode.CODEX_CLI
      LlmRuntimeMode.CLAUDE_CLI
      LlmRuntimeMode.ANTHROPIC_API

(b) Operator input enters via a public surface:
      - QUEUE_PERCEPT (via OperatorSession.dispatch), OR
      - STREAM_APPEND + STREAM_PROMOTE + STEP_TICK, OR
      - A direct LLMBackedPtCns.eval(content_id) harness over the
        same factory-built client.

(c) brain.tick.tick(...) (or LLMBackedPtCns.eval over a public
    PtCns surface) completes without raising.

(d) The retry shell (LLMBackedPtCns) parses the response into one of
    ConsistencyEval.{PRESERVE, DAMAGE, NEUTRAL} without exhausting
    max_attempts.

(e) Inspectable kernel state changes are recorded:
      - BrainState.profile / msi / ptcns / registry
      - OperatorSession.tick_counter advances
      - OperatorSession.latest_tick captures the new TickRecord
      - GrowthLedger / PatternLedger / CoherenceMonitor events
        observable (where applicable; we do not modify their
        semantics)

(f) L1 (CachedClient) hit / miss / skip counters are recorded.

(g) L2 (LLMBackedPtCns canonical eval cache) hit / miss / store /
    skip counters are recorded.

(h) Repeated equivalent work does NOT spam the model. The L1 and L2
    layers should absorb a same-prompt repeat.

(i) All raw prompts, raw responses, secrets, and cache files remain
    UNCOMMITTED. brain/.llm_cache is gitignored; cache files stay
    out of the commit.

(j) Final report classifies as one of:
      REAL MODEL TEST PASS
      REAL MODEL TEST PARTIAL
      REAL MODEL TEST BLOCKED BY ENV
      REAL MODEL TEST FAIL
```

Anything less than this is **not** "actual testing" — it is either a
mock run, a UI smoke, or an unmeasured spike.

---

## 2. Available model-backed modes

The repo recognizes three real model-backed transports (defined in
`brain/ui/llm_runtime.py`'s `LlmRuntimeMode`):

```text
codex-cli       → CodexCLIClient (brain/llm/client.py)
                  Subprocess ("codex", "exec", <prompt>)
                  Authentication: whatever local codex binary has
                  (ChatGPT account or API)
                  No env-var management required
                  PATH-resolved at startup

claude-cli      → ClaudeCLIClient
                  Subprocess ("claude", "-p", ..., <prompt>)
                  Authentication: whatever local claude binary has
                  No env-var management required
                  PATH-resolved at startup

anthropic-api   → AnthropicAPIClient
                  Direct HTTPS to api.anthropic.com/v1/messages
                  Requires ANTHROPIC_API_KEY or BRAIN_ANTHROPIC_API_KEY
                  Default model: claude-sonnet-4-6
                  Default timeout: 30s
```

Phase 3.16 preference order:

```text
1. codex-cli         (CLI present + login present is the typical
                      developer-machine baseline)
2. claude-cli        (CLI present + valid Pro/Max session)
3. anthropic-api     (env API key available)
```

The first available mode is used. If none is available, the audit
ships **REAL MODEL TEST BLOCKED BY ENV** with a precise list of what
is missing.

---

## 3. Why `--print-once` is NOT a model test

`brain/ui/__main__.py::main` has the following short-circuit ordering:

```text
1. argparse.parse_args
2. autosave-mode validation
3. --check-terminal branch:        returns 0/1
4. --print-once branch:            renders one frame, returns 0
5. --db-status / --db-verify / --db-backup short-circuit
6. terminal usability check
7. _resolve_llm_runtime_config + build_llm_client_from_config
8. run_curses(session, client, ...)
```

`--print-once` returns at step 4, **before** the LLM runtime config
is resolved at step 7. The branch explicitly carries the comment:

> `--print-once remains independent of the selected LLM mode
>  (I-LLMTOG-10): we render without constructing any backend.`

So `python3 -m brain.ui --print-once` cannot exercise a real
model-backed tick route. It renders a deterministic frame of the
default session and exits. The session contains only the seed
profile (cogito + alpha) and no queued event; no `tick()` call is
made. This is why Phase 3.16 introduces in-process / TUI / direct
harness routes — `--print-once` is structurally unable to be the
test surface.

---

## 4. Why an in-process harness or interactive TUI route is needed

ToyI's real model path is exercised in exactly one place at runtime:
`brain.ui.session.OperatorSession.dispatch(STEP_TICK, client=...)`,
which calls `brain.tick.tick(...)` after popping a queued
`PerceptEvent` and passing it together with the LLM client. Two
entry shapes feed that dispatch:

```text
Route A (in-process OperatorSession dispatch):
    session = build_default_session()
    client  = build_llm_client_from_config(llm_config)
    session.dispatch(make_command(QUEUE_PERCEPT, payload), client=None)
    session.dispatch(make_command(STEP_TICK), client=client)

Route B (interactive curses TUI):
    python3 -m brain.ui --llm-mode codex-cli
    inside the TUI:
      "e" enters Composer mode, types a percept text
      "<Enter>" queues a percept
      "s" issues STEP_TICK
    requires a usable terminal (stdin + stdout TTY, TERM != dumb)
    blocks until operator quits

Route C (direct LLMBackedPtCns harness):
    client = build_llm_client_from_config(llm_config)
    ptcns  = LLMBackedPtCns(msi, content_texts, client, max_attempts=3)
    result = ptcns.eval("<content_id>")
    bypasses tick() but exercises the same retry shell, the same
    parser, and the same L0/L1/L2 cache stack.
```

Phase 3.16 prefers Route A (deterministic, scriptable, no terminal
required, captures the most ToyI surface area). Route C is a
secondary harness used when Route A is blocked by a step / dispatch
shape issue. Route B is used only if the operator explicitly opts in
to an interactive session.

---

## 5. Real model call budget

```text
Max 30 real external model-backed calls TOTAL across Phase 3.16.

Count every model-backed attempt toward the budget:
  - successful first-attempt parses                       (1 call each)
  - retry attempts after parse failure                    (1 call each)
  - timed-out attempts                                    (1 call each)
  - subprocess nonzero-exit attempts                      (1 call each)
  - HTTP errors against anthropic-api                     (1 call each)

Stop before exceeding 30.

If call count cannot be proven from observable counters / logs,
assume the higher number.

Use cache-aware repeated probes: after the first miss, repeat the
same prompt to confirm L1 hit behavior; that repeat is 0 model
calls (cache hit), not 1.

No unbounded loops; no "keep trying forever."

Counter sources:
  - CachedClient.hit_count / miss_count / skip_count
  - LLMBackedPtCns._cache size and ConsistencyEval distribution
  - CognitionTracer event stream events:
      llm.request / llm.response       (one of each per real call)
      llm.retry                        (extra retry attempt)
      llm.cache_hit / llm.cache_miss / llm.cache_skip
      llm.semantic_cache_hit / _miss / _store / _skip
      parse.success / parse.failure
  - cache file count under brain/.llm_cache (excluding eval_v1/)
```

Real model calls accumulate across steps. Step 3 should produce 0
model calls (mock / offline only). Step 4 owns most of the budget.
Step 7 (if reached) may consume a small additional reserve to
verify the patch end-to-end.

---

## 6. Route candidates

### Route A — In-process OperatorSession dispatch

```python
# pseudo-code (not executed in this doc)
from brain.ui.__main__ import build_default_session
from brain.ui.llm_runtime import (
    LlmRuntimeConfig, LlmRuntimeMode, build_llm_client_from_config,
)
from brain.ui.commands import (
    OperatorCommand, QueuePerceptPayload, make_command,
)
from brain.toce_core import ContentState
from fractions import Fraction

config  = LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI)  # or CLAUDE_CLI / ANTHROPIC_API
client  = build_llm_client_from_config(config)
session = build_default_session()

payload = QueuePerceptPayload(
    content_id="probe-1",
    text="a short, neutral observation about the system itself",
    content_state=ContentState.CANDIDATE,
    initial_rho=Fraction(1, 2),
)
session.dispatch(make_command(OperatorCommand.QUEUE_PERCEPT, payload))
session.dispatch(make_command(OperatorCommand.STEP_TICK), client=client)

# Inspect
print(session.tick_counter)
print(session.latest_tick)
print(session.state.profile)
print(client.hit_count, client.miss_count, client.skip_count)
```

Pros: scriptable, deterministic argv, captures profile/MSI/PtCns/
registry/tick_counter changes, CachedClient counters directly
inspectable.

Cons: requires correct payload shape (cogito-collision-safe
`content_id`, valid `ContentState`, in-range rho).

### Route B — Interactive curses TUI

```bash
python3 -m brain.ui --llm-mode codex-cli
# inside TUI: 'e' to enter composer, type text, Enter, 's' for tick
```

Pros: faithful operator path.

Cons: needs a TTY; not scriptable; produces fewer machine-readable
counters; operator must drive each step.

### Route C — Direct LLMBackedPtCns harness

```python
# pseudo-code (not executed in this doc)
from fractions import Fraction
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID
from brain.llm.ptcns_backed import LLMBackedPtCns

profile = make_profile_with_cogito({COGITO_ID: 1, "alpha": Fraction(3, 4)})
msi     = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 2))
ptcns   = LLMBackedPtCns(
    msi=msi,
    content_texts={"alpha": "alpha text", "probe-1": "neutral observation"},
    client=client,
    max_attempts=3,
)
parsed = ptcns.eval("probe-1")
```

Pros: smallest possible surface; bypasses dispatch shape issues;
exercises L0 / L1 / L2 directly.

Cons: skips tick() and Growth/Pattern ledger events.

---

## 7. Success criteria

```text
The operational walk SUCCEEDS for a tick route iff all of (a)-(j) in
Section 1 hold.

The campaign as a whole verdicts as:

REAL MODEL TEST PASS
  - >= 1 complete model-backed tick route via Route A or Route B
  - cumulative model calls <= 30
  - all secrecy + cache-discipline constraints hold

REAL MODEL TEST PARTIAL
  - the route demonstrates at least one real model call resulting
    in a parsed ConsistencyEval, but at least one acceptance
    criterion (a)-(j) failed cleanly (e.g., session dispatch
    couldn't accept the payload but Route C eval() worked, or
    initial parse failed but a tuning retry parsed cleanly)

REAL MODEL TEST BLOCKED BY ENV
  - no model-backed mode available locally
  - report names exactly which mode is missing what
  - no real model calls used

REAL MODEL TEST FAIL
  - real model reachable but the walk could not be completed
    within the budget
  - report names exactly where the route broke and why
```

---

## 8. Stop conditions

The real run (Step 4) stops on any of:

```text
- cumulative model call count reaches 30 (or projected next attempt
  would exceed 30)
- 10 consecutive parse failures across all attempts
- real model unavailable (subprocess failure, HTTP failure,
  authentication failure) AND fallback to next preferred mode also
  unavailable
- runtime code change seems needed to make the path work (this is
  a "patch required" classification; commit the partial report and
  proceed to Step 5/6)
```

---

## 9. Allowed tuning levers

If the first real model attempt does not parse:

```text
- shorter input text
- clearer input text (less ambiguous between PRESERVE / DAMAGE /
  NEUTRAL semantics)
- a different available model-backed mode (codex-cli ↔ claude-cli ↔
  anthropic-api)
- timeout increase (within Phase 3.15 LLM_RUNTIME_TIMEOUT defaults
  and Phase 3.14 cache discipline)
- cache on/off diagnostic exactly ONCE (final route uses
  cache-on behavior)
- switch between Route A (session dispatch) and Route C (direct
  LLMBackedPtCns harness)
```

Forbidden without a Step 6 review gate:

```text
- changing brain/llm/prompts.py (prompt template)
- changing brain/llm/parse.py (parser grammar)
- changing brain/tick.py (tick semantics)
- changing brain/llm/client.py L1 cache semantics
- changing brain/llm/ptcns_backed.py L2 cache semantics
- changing any invariant
```

---

## 10. Raw prompt / response / secret secrecy

```text
- never commit raw prompts to the repo
- never commit raw model responses to the repo
- never commit cache files; brain/.llm_cache stays gitignored
- never commit API keys or sessions
- never print API keys in reports; redact to [REDACTED] or boolean
- never reproduce a full raw response in the report; bounded
  identifiers (hash prefix, parsed enum name, byte count) only
- prompt template, parser grammar, and L2 entry schema are
  versioned (PROMPT_TEMPLATE_VERSION, PARSE_SCHEMA_VERSION,
  SEMANTIC_CACHE_SCHEMA_VERSION); record versions, not bodies
```

---

## 11. Cache discipline

```text
L1 (brain/llm/client.py::CachedClient):
  bounded at L1_CACHE_MAX_ENTRIES = 1024
  write-skip-at-cap admission (Phase 3.15); existing entries
    never removed by the cache itself
  emits llm.cache_hit / llm.cache_miss / llm.cache_skip
  corrupt entries still fail loud

L2 (brain/llm/ptcns_backed.py canonical eval cache):
  bounded at SEMANTIC_CACHE_MAX_ENTRIES = 1024
  entry payload exactly {"key_prefix", "parsed"} — no raw prompt,
    no raw response, no provider metadata, no full key
  bumped by changes to PROMPT_TEMPLATE_VERSION, PARSE_SCHEMA_VERSION,
    or SEMANTIC_CACHE_SCHEMA_VERSION
  emits llm.semantic_cache_hit / _miss / _store / _skip

Phase 3.16 does NOT modify either layer's semantics. It observes
counters and event streams to verify the locked policies hold under
real model load.
```

---

## 12. Disclosure block templates

Each step report carries the Stage A / Stage B / Stage C.1 disclosure
block defined in `CURRENT_MISSION.md`. For Step 2 (this synthesis),
the disclosures are:

```text
Stage A ChatGPT/Codex consultation:
- used: no
- mode / model / effort: n/a
- wrapper command: n/a
- question file / answer file: n/a
- wrapper status: n/a
- accepted advice: none
- rejected advice: none
- reason: synthesis is bounded and self-contained; the Step 2 scope
  is small enough that adversarial review can wait until Step 4/5
  if a result is contestable.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the only writer for synthesis files.

Stage C.1 flow orchestration:
- used: no
- reason: synthesis is a single small file; the overhead of a
  Stage C.1 manifest (validate → orchestrate → review) exceeds the
  cost of writing the doc directly.
```

---

## 13. Next artifact

Step 3: `docs/campaigns/phase3_16/PHASE3_16_MODEL_AVAILABILITY_BASELINE.md`
— probe `codex` / `claude` / ANTHROPIC_API_KEY presence (secrets
redacted) and run a deterministic mock / offline tick through the
public dispatch path. No real model calls.
