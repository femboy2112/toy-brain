# PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md

## 1. Purpose

Define the thesis, motivation, and boundary for the Phase 3.8b LLM
Runtime Toggle subcampaign. This document is a planning artifact only:
it does not add modes, edit `brain/ui/__main__.py`, register catalog
rows, change `tools/catalog.py`, regenerate `brain/_catalog_ids.py`, or
modify `brain/invariants.py`.

```text
Verdict for Step 24A: COHERENT - READY FOR KICKOFF
```

## 2. Baseline

```text
Catalog version:        v0.15
REQUIRED:              168
STRUCTURAL:             61
NOT-EXERCISED:           8
DEFERRED:               12
OBSERVED:               11
Latest landed campaign step: Step 24 - Operator Stream Interaction
                              commands implemented and green.
Default LLM stand-in:   brain.ui.__main__.OfflineStandInClient
                        (returns the literal "PRESERVE" deterministically).
LLM Protocol seam:      brain.llm.client.LLMClient (runtime_checkable).
LLM v1 backends:        AnthropicAPIClient, MockClient, CachedClient,
                        ClaudeCLIClient (in brain/llm/client.py).
Existing tick seam:     brain.tick.tick(..., client, ...).
Existing entrypoint:    python3 -m brain.ui --print-once / --check-terminal
                        currently constructs OfflineStandInClient
                        unconditionally before handing off to run_curses.
```

Required source artifacts:

```text
PHASE3_8B_LLM_TOGGLE_AMENDMENT.md (mandatory context)
CURRENT_CAMPAIGN.md sections 24A-24G
brain/llm/client.py (LLMClient Protocol + four shipped backends)
brain/ui/__main__.py (current offline-only entrypoint)
```

## 3. Why Phase 3.8b follows Phase 3.8

Phase 3.8 lands the typed `/stream`, `/stream-summary`,
`/stream-candidates`, and `/stream-promote` operator routes over the
Phase 3.7 substrate. Every Phase 3.8 row preserves the existing
`OfflineStandInClient` default and never widens the kernel's
real-LLM surface. The final Phase 3.8 audit (Step 25) must still be
able to certify that no real LLM call is required by any Phase 3.8
REQUIRED or STRUCTURAL row.

Phase 3.8b extends that audit-clean baseline with one explicit
operator-facing toggle that selects between a closed set of
`LLMClient`-compatible backends. The toggle never adds a second
classification path, never introduces a model-backed `tick()` route
alongside the existing one, and never makes any REQUIRED or
STRUCTURAL row depend on a real model. It is the smallest possible
opt-in surface that satisfies the amendment's requirement: "the
completed text interaction loop should support two testing modes —
offline (default) and model (explicit opt-in)."

## 4. Phase 3.8b LLM Runtime Toggle thesis

```text
1.  Offline mode remains the default. The operator-facing CLI
    constructs an OfflineStandInClient unless an explicit opt-in
    flag is supplied.

2.  Model-backed mode is explicit opt-in. The operator must request
    a non-offline mode by CLI flag or environment variable; no
    auto-detection of API keys, no auto-fallback when a key is
    present.

3.  Client selection reuses the existing LLMClient protocol. The
    selected client is one of the brain.llm.client backends, or the
    OfflineStandInClient. No new protocol surface is introduced.

4.  The selected client enters the kernel through the existing
    tick(..., client, ...) seam. brain/tick.py is not modified.
    No second classification path appears alongside _dispatch_step.

5.  Fixtures remain deterministic unless explicitly OBSERVED or
    manual. The runner never reaches a real LLM. REQUIRED and
    STRUCTURAL rows are driven exclusively by MockClient,
    OfflineStandInClient, or no client at all. Any model-backed
    smoke check is OBSERVED/manual and cannot fail the runner.
```

## 5. Modes (closed enumeration target)

```text
offline       - default; OfflineStandInClient. No network, no shell.
mock          - deterministic canned-response client. Fixture-style
                stand-in built from a frozen response list. No network,
                no shell.
anthropic-api - AnthropicAPIClient. Reads ANTHROPIC_API_KEY from env or
                an explicit CLI argument. Uses urllib.request only;
                rejects launch when the key is unavailable.
claude-cli    - ClaudeCLIClient. Requires the `claude` executable on
                PATH; rejects launch when it is missing.
```

Mode parsing is intentionally narrow: the only accepted CLI argument
is `--llm-mode <value>` (or the equivalent env override), and the only
accepted values are the four strings above. Unknown strings produce a
local error message and exit before any client is constructed.

## 6. Why this is not a second classification path

The existing `tick()` path already accepts an `LLMClient` argument
which the Phase 2 v1 `LLMBackedPtCns` shell consumes. The toggle
changes only which concrete `LLMClient` implementation reaches
`run_curses(..., client=...)`. It does not:

```text
- introduce a separate consistency-evaluation surface
- add an alternate "language" or "social" classification step
- bypass _dispatch_step or invent a model-backed promotion route
- attach a model-backed scoring path to /stream-summary,
  /stream-candidates, or /stream-promote
```

`/stream-promote` continues to construct a `QueuePerceptPayload`
through the existing constructor-bounded path and enqueue it through
`OperatorEventQueue.enqueue`. Only `/step` reaches `tick()`. The
selected client argument is whatever the toggle resolved at launch.

## 7. Why this is not Mode B / agency / language

The toggle does not authorize:

```text
- Mode B reflective planning
- self-modification
- a natural-language teacher / corrector
- a social model
- model-backed scoring of /stream-summary or /stream-candidates
- real LLM calls below Phase 3.8b
- arbitrary subprocess spawn or shell execution
- network I/O outside the AnthropicAPIClient HTTP transport
- writing model output to traces, scenarios, source histories,
  catalog files, or any developmental history
```

Real LLM behavior, when activated, runs only inside the existing
`tick()` retry shell. The retry shell is itself bounded by Phase 2 v1
invariants (`I-LLM-01..04`). The toggle adds no new claim about what
the model says or what its output means.

## 8. Why this is not truth scoring or readability scoring

```text
- The toggle does not introduce a truth flag, a PRESERVE / DAMAGE
  judgment, or a readability score on stream evidence.
- /stream-summary remains exact int / Fraction counts.
- /stream-candidates remains structural segments / patterns /
  promotion candidates.
- The toggle does not let model output bypass /stream-promote.
- The toggle does not let model output mutate BrainState directly.
```

The model, when consulted via the existing `tick()` seam, only
evaluates consistency of one already-validated `PerceptEvent`. Its
output is parsed through the Phase 2 v1 `parse_consistency_response`
contract and is bounded by `I-LLM-01..04`.

## 9. Non-goals

```text
- new LLMClient implementations beyond the four shipped backends
- non-offline mode as the default in any scenario
- automatic API-key detection or implicit credential pickup
- model-backed scoring of stream evidence
- model output written to traces, scenarios, or source histories
- new tick() argument signatures
- new public PerceptEvent constructor behavior
- catalog rows that require a real model to pass
- a curses key binding that flips modes mid-session
- runtime mode switching without restart
```

## 10. Risks

```text
- A model-backed mode that gets default-on by accident would silently
  widen the kernel's real-LLM surface during normal operation.
  Mitigation: the closed mode enumeration plus explicit-opt-in policy
  must be the only path into a model-backed client. The implementation
  step must include a fixture that exercises the default-offline
  property against the runtime mode parser.

- A model-backed smoke check that ends up REQUIRED would tie the
  runner to network / credentials / a local CLI. Mitigation: the
  catalog patch plan must classify the model-backed smoke as
  OBSERVED/manual. The runner must continue to pass with no
  ANTHROPIC_API_KEY and no `claude` executable installed.

- Cached client behavior that silently fills the disk under
  brain/.llm_cache during operator sessions could leak prompts.
  Mitigation: the implementation must document the cache directory,
  must default to writing under brain/.llm_cache only when caching is
  enabled by config, and must not enable caching when the mode is
  offline / mock.

- Launch-time errors (missing API key, missing `claude`) that surface
  late could leave the operator with a half-initialized session.
  Mitigation: client factory must fail before any session is
  constructed; the existing OperatorSession.__post_init__ contract
  must not run on a partial state.

- A future contributor could expose a second model-backed surface
  through a different module than brain/llm/. Mitigation: the catalog
  patch plan should add a STRUCTURAL row that audits "selected client
  enters through the existing tick client argument" and "client
  factory returns an LLMClient-compatible object" so a drift becomes
  a runner failure.
```

## 11. Next artifact

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md
```

The kickoff document defines:

```text
LlmRuntimeMode enumeration
LlmRuntimeConfig record
build_llm_client_from_config(...) factory signature
CLI / env precedence rules
cache policy (default off)
startup failure behavior
fixture policy (deterministic only; model-backed smoke is OBSERVED/manual)
```

It does not register catalog rows, does not edit
`brain/ui/__main__.py`, and does not change `brain/invariants.py`.
