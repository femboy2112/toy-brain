# PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md

## 1. Purpose

Sketch the concrete structure for the Phase 3.8b LLM Runtime Toggle on
top of the accepted synthesis (`PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md`).
This document is a planning artifact only: it names types, fields, and
behavior contracts but does not edit `brain/ui/__main__.py`, add
fixtures, change `tools/catalog.py`, register catalog rows, or modify
`brain/invariants.py`.

```text
Verdict for Step 24B: COHERENT - READY FOR CORRIGENDA
```

## 2. Baseline

```text
Catalog version:        v0.15
REQUIRED / STRUCTURAL:  168 / 61
Latest synthesis:       PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md
LLMClient seam:         brain.llm.client.LLMClient
Existing default:       brain.ui.__main__.OfflineStandInClient
                        constructed unconditionally before run_curses.
Existing CLI flags:     --print-once, --check-terminal, --width, --height
                        (in brain.ui.__main__.build_arg_parser).
```

## 3. Module layout

```text
brain/ui/llm_runtime.py
    LlmRuntimeMode             closed string Enum
    LlmRuntimeConfig           frozen dataclass with slots
    build_llm_client_from_config(config) -> LLMClient
    parse_llm_runtime_args(args, env) -> LlmRuntimeConfig
    LlmRuntimeError            small exception subclass for local errors

brain/ui/__main__.py           extends build_arg_parser with the new
                               flags; replaces the unconditional
                               OfflineStandInClient construction with
                               a call to build_llm_client_from_config.

brain/ui/fixtures/llm_runtime_toggle.py
                               deterministic fixtures driving the new
                               I-LLMTOG-* row family.

brain/invariants.py            extends FIXTURE_MODULES with the new
                               fixture entry and (if needed) a
                               _PHASE3_8B_PENDING_ROWS table.

INVARIANT_CATALOG.md           bumps to v0.16 with the I-LLMTOG-* row
                               family (sized in the catalog patch plan).

README.md                      adds the --llm-mode flag documentation
                               and the v0.16 banner after implementation
                               lands.
```

## 4. `LlmRuntimeMode`

```text
class LlmRuntimeMode(str, Enum):
    OFFLINE       = "offline"
    MOCK          = "mock"
    ANTHROPIC_API = "anthropic-api"
    CLAUDE_CLI    = "claude-cli"
```

```text
- The enumeration is closed. The factory accepts only these four
  string values (case-sensitive, with the explicit dash spelling for
  anthropic-api and claude-cli).
- An unknown string raises LlmRuntimeError before any client is
  constructed.
- The default mode is OFFLINE. The factory must not fall back to a
  non-offline mode when offline construction succeeds, and must not
  fall back to offline when an explicit non-offline mode fails.
```

## 5. `LlmRuntimeConfig`

```text
@dataclass(frozen=True, slots=True)
class LlmRuntimeConfig:
    mode: LlmRuntimeMode = LlmRuntimeMode.OFFLINE
    api_key: Optional[str] = None        # explicit override for
                                         # anthropic-api; if None,
                                         # AnthropicAPIClient consults
                                         # ANTHROPIC_API_KEY at first call.
    model: str = "claude-sonnet-4-6"      # only honored when mode is
                                         # anthropic-api.
    claude_cli_executable: str = "claude" # only honored when mode is
                                         # claude-cli.
    timeout_seconds: float = 30.0        # only honored for
                                         # anthropic-api / claude-cli.
    enable_cache: bool = False           # when True and mode is
                                         # anthropic-api or claude-cli,
                                         # wrap the selected client
                                         # with CachedClient under
                                         # brain/.llm_cache/.
    mock_responses: tuple[str, ...] = () # only honored when mode is
                                         # MOCK; non-empty when MOCK is
                                         # explicit.
```

```text
- All fields are bounded primitives or a closed tuple of bounded
  printable strings. No field is a callable, file handle, socket,
  subprocess handle, or LLM client instance.
- Construction raises LlmRuntimeError when the per-mode preconditions
  are violated (e.g. MOCK with empty mock_responses).
- The default LlmRuntimeConfig() yields offline mode with no cache and
  no extra config; build_llm_client_from_config(LlmRuntimeConfig())
  must return an OfflineStandInClient.
```

## 6. `build_llm_client_from_config(config) -> LLMClient`

```text
- OFFLINE       -> OfflineStandInClient()
- MOCK          -> MockClient(responses=config.mock_responses)
- ANTHROPIC_API -> AnthropicAPIClient(
                       api_key=config.api_key,
                       model=config.model,
                       timeout_seconds=config.timeout_seconds,
                   )
                   optionally wrapped in CachedClient when
                   config.enable_cache is True.
- CLAUDE_CLI    -> ClaudeCLIClient(
                       command=(config.claude_cli_executable, "-p",
                                "--no-session-persistence",
                                "--permission-mode", "default"),
                       timeout_seconds=config.timeout_seconds,
                   )
                   optionally wrapped in CachedClient when
                   config.enable_cache is True.
```

```text
- The factory raises LlmRuntimeError before returning when:
    * mode == ANTHROPIC_API and no api_key is supplied AND
      ANTHROPIC_API_KEY is absent from the environment.
    * mode == CLAUDE_CLI and shutil.which(config.claude_cli_executable)
      returns None.
    * mode == MOCK and len(config.mock_responses) == 0.
- The factory must never silently fall back across modes.
- The factory returns an object satisfying LLMClient (the runtime
  Protocol check accepts duck-typed eval_consistency methods).
- The returned object is the only thing handed to run_curses(...,
  client=...). No second classification path is constructed.
```

## 7. CLI / env precedence

```text
1. Default:     LlmRuntimeMode.OFFLINE.
2. Environment: BRAIN_LLM_MODE if set and recognized; otherwise
                ignored.
3. CLI flag:    --llm-mode <value> (or --llm-mode=<value>); when
                present, overrides BRAIN_LLM_MODE.
4. Per-mode flags:
    --llm-anthropic-api-key <value>      explicit api_key override
                                         (also via BRAIN_ANTHROPIC_API_KEY)
    --llm-anthropic-model <value>        model name override
    --llm-claude-cli-executable <value>  claude executable override
    --llm-timeout <float>                request timeout override
    --llm-enable-cache                   enable CachedClient wrapping
    --llm-mock-response <value>          repeatable; collects into
                                         mock_responses tuple (MOCK only)
5. Unknown flags / values produce a local error message and exit
   with a non-zero return code before any session is constructed.
```

```text
- The parser must accept --llm-mode offline explicitly so a CI run
  can document "the mode was selected, not defaulted."
- --print-once must remain independent of the selected client: the
  current implementation does not call the client, and that behavior
  is preserved by routing --print-once into its existing code path
  before constructing the client.
- --check-terminal also runs before client construction.
```

## 8. Cache policy

```text
- Default: enable_cache = False.
- When enable_cache is True AND mode is in (ANTHROPIC_API, CLAUDE_CLI),
  wrap the selected inner client with CachedClient(cache_dir=
  Path("brain/.llm_cache")) before returning.
- When enable_cache is True for OFFLINE or MOCK, the factory raises
  LlmRuntimeError: caching deterministic clients adds no value and
  risks confusion.
- The cache directory must be documented in README after the
  implementation step. The README must say "cache writes only happen
  when --llm-enable-cache is supplied and a model-backed mode is
  selected."
```

## 9. Startup failure behavior

```text
- All failures discovered before client return raise LlmRuntimeError.
- main() catches LlmRuntimeError, prints a bounded printable message
  to stderr, and returns a non-zero exit code.
- An LlmRuntimeError must surface before any OperatorSession or
  curses initialization; an interrupted launch must not partially
  construct the session.
- The error message must include the mode the operator requested and
  the local reason for the rejection (missing key, missing executable,
  empty mock responses, unknown mode).
```

## 10. Fixture policy

```text
- All Phase 3.8b REQUIRED and STRUCTURAL rows are driven by:
    OfflineStandInClient, MockClient,
    LlmRuntimeConfig records, build_llm_client_from_config(...),
    and AST audits.
- No REQUIRED or STRUCTURAL row makes a real HTTP call or a real
  subprocess invocation. The runner must continue to pass with
  no ANTHROPIC_API_KEY and no `claude` executable on PATH.
- A model-backed smoke walk that exercises a real AnthropicAPIClient
  or ClaudeCLIClient is OBSERVED/manual only. It runs out-of-band,
  documented in the Phase 3.8b audit, and is not registered as a
  runner check.
- Fixtures verify:
    * default LlmRuntimeConfig() builds an OfflineStandInClient.
    * each explicit mode constructs the expected concrete class
      (without invoking it).
    * each mode's failure preconditions raise LlmRuntimeError
      cleanly.
    * the AST audit confirms run_curses(..., client=...) is fed by
      build_llm_client_from_config(...) only.
```

## 11. Owning modules and import discipline

```text
brain/ui/llm_runtime.py
    may import: stdlib, brain.llm.client, brain.ui.__main__ for the
                OfflineStandInClient definition (or relocate the class
                into brain.ui.llm_runtime if cleaner — implementation
                step to decide).
    must not import: curses, brain.tlica, brain.tick.

brain/ui/__main__.py
    extends imports to include brain.ui.llm_runtime symbols.
    must remain free of brain.tlica (it already is) and must keep
    brain.llm imports lazy when possible (the AnthropicAPIClient and
    ClaudeCLIClient classes already perform HTTP / subprocess on
    eval_consistency, not at import).
```

## 12. Likely catalog row family

The accepted patch plan (Step 24D) will register rows under:

```text
I-LLMTOG-*
```

A first sketch of likely rows (sized properly in the patch plan):

```text
I-LLMTOG-01  Default LlmRuntimeConfig() produces offline mode.
I-LLMTOG-02  LlmRuntimeMode is a finite closed enumeration.
I-LLMTOG-03  build_llm_client_from_config(OFFLINE) returns
              OfflineStandInClient.
I-LLMTOG-04  Model-backed modes require explicit opt-in; the factory
              never silently selects ANTHROPIC_API / CLAUDE_CLI from a
              default config.
I-LLMTOG-05  ANTHROPIC_API without ANTHROPIC_API_KEY raises
              LlmRuntimeError before launch.
I-LLMTOG-06  CLAUDE_CLI without `claude` on PATH raises
              LlmRuntimeError before launch.
I-LLMTOG-07  MOCK with empty mock_responses raises LlmRuntimeError.
I-LLMTOG-08  Cache wrapping is opt-in and only honored for
              ANTHROPIC_API / CLAUDE_CLI.
I-LLMTOG-09  Selected client enters tick() through the existing
              client argument; no second classification path exists.
I-LLMTOG-10  Stream / TUI imports do not introduce a second
              model-backed surface; AST audit over brain/ui/.
I-LLMTOG-11  --print-once remains independent of the selected client.
I-LLMTOG-12  Model-backed smoke is OBSERVED/manual (status OBSERVED).
I-LLMTOG-13  LLM runtime save/export is NOT-EXERCISED in this campaign.
```

Final row counts, status assignments, and fixture roster are the
job of Step 24D.

## 13. Non-goals (carried forward from the synthesis)

```text
- no new LLMClient implementations beyond the four shipped backends
- no auto-detection of model-backed mode from env state alone
- no implicit cache enable
- no curses key binding to flip modes mid-session
- no model-backed tick() route alongside the existing one
- no model output reaching traces / scenarios / source histories /
  catalog files
- no REQUIRED / STRUCTURAL row that needs a real model to pass
```

## 14. Next artifact

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_CORRIGENDA.md
```

The corrigenda step audits each ruling above (finite mode parsing,
default deterministic behavior, explicit opt-in semantics,
credential / tool availability, cache behavior, trace / summary
wording, fixture status mapping, UI import-audit implications) and
locks the final row family before the catalog patch plan.
