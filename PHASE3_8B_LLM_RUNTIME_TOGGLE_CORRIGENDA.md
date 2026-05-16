# PHASE3_8B_LLM_RUNTIME_TOGGLE_CORRIGENDA.md

## 1. Purpose

Audit the rulings in `PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md`, lock
the LLM runtime toggle's mode parsing, default behavior, opt-in
semantics, credential / tool availability handling, cache behavior,
trace / summary wording, fixture status mapping, and UI import-audit
implications. This document is a planning artifact only: it does not
edit `brain/ui/__main__.py`, add `brain/ui/llm_runtime.py`, register
catalog rows, or modify `brain/invariants.py`.

```text
Verdict for Step 24C: COHERENT - READY FOR CATALOG PATCH PLAN
```

## 2. Baseline

```text
Catalog version:     v0.15
REQUIRED / STRUCTURAL: 168 / 61
Accepted artifacts:
  PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md
  PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md
LLM Protocol seam:   brain.llm.client.LLMClient
Shipped backends:    AnthropicAPIClient, MockClient, CachedClient,
                     ClaudeCLIClient.
Default stand-in:    brain.ui.__main__.OfflineStandInClient.
Existing tick seam:  brain.tick.tick(..., client, ...).
```

## 3. Rulings

### 3.1 Finite mode parsing

```text
Ruling A: Mode strings are matched against the closed enumeration
          ("offline", "mock", "anthropic-api", "claude-cli") by exact
          string equality, case-sensitive, after a single .strip()
          on the operator-supplied value. Anything else is a hard
          local error.

Why:      Loose matching invites silent mode drift (e.g. "Offline",
          "ANTHROPIC", "claude_cli"). The CLI is a typed surface;
          fuzzy matching is a category of bug.

Edge cases:
  - empty string after strip()      -> LlmRuntimeError("--llm-mode
                                       requires a non-empty value")
  - whitespace-only input           -> same
  - any other string                -> LlmRuntimeError("unknown
                                       --llm-mode: <value>; expected
                                       one of {offline, mock,
                                       anthropic-api, claude-cli}")

Implementation note: prefer LlmRuntimeMode(value) (the str-Enum
constructor) inside a try / except ValueError to centralize the
match. Do not implement an aliases table.
```

### 3.2 Default deterministic behavior

```text
Ruling B: A fresh LlmRuntimeConfig() (no CLI / env input) must
          produce an OfflineStandInClient via
          build_llm_client_from_config(...). The factory must not
          consult the environment when no explicit mode is supplied.

Why:      The amendment is explicit: offline is the default. Reading
          ANTHROPIC_API_KEY when the operator did not opt in would
          silently widen the runtime surface in the presence of a
          stale env var.

Edge cases:
  - ANTHROPIC_API_KEY set but no --llm-mode -> still offline.
  - BRAIN_ANTHROPIC_API_KEY set but no
    --llm-mode                              -> still offline.
  - BRAIN_LLM_MODE explicitly set to
    "offline"                                -> offline (logged).
  - BRAIN_LLM_MODE set to an unknown value   -> error before launch.

Implementation note: the env override layer is a separate function
parse_llm_runtime_args(args, env) -> LlmRuntimeConfig. The factory
itself never reads os.environ.
```

### 3.3 Explicit opt-in semantics

```text
Ruling C: Each non-offline mode requires either:
            * the explicit CLI flag --llm-mode <mode>, or
            * the explicit env override BRAIN_LLM_MODE=<mode>.

          No other state (presence of an API key, presence of
          `claude` on PATH, presence of cache files) is sufficient
          to select a non-offline mode.

Why:      Implicit opt-in defeats the audit story: a reader of the
          repo must be able to grep one variable (BRAIN_LLM_MODE)
          or one CLI flag (--llm-mode) to know whether a real model
          will be reached.

Conflicts:
  - if both BRAIN_LLM_MODE and --llm-mode are set with different
    values, the CLI flag wins. Log the override in the local
    startup message.
  - if both are set with the same value, the launch proceeds
    silently (no warning needed).

Implementation note: parse_llm_runtime_args returns a
LlmRuntimeConfig whose mode is the resolved value. The factory
never sees the raw env / argv.
```

### 3.4 Credential / tool availability

```text
Ruling D: Credential / tool checks happen at factory time, before
          any session is constructed.

For anthropic-api:
  - If config.api_key is None AND ANTHROPIC_API_KEY is unset,
    raise LlmRuntimeError("anthropic-api requires ANTHROPIC_API_KEY
    or --llm-anthropic-api-key").
  - Do not perform an HTTP probe at factory time: the user pays for
    real calls only when the kernel reaches eval_consistency via
    tick().

For claude-cli:
  - shutil.which(config.claude_cli_executable) must return non-None.
    Otherwise raise LlmRuntimeError naming the missing executable.
  - Do not invoke the CLI at factory time.

For mock:
  - len(config.mock_responses) must be >= 1. Otherwise raise
    LlmRuntimeError("mock requires at least one --llm-mock-response").

Why: late failures (mid-tick, mid-session) leave the operator with
half-initialized state. Pushing the check to factory time keeps the
failure local to startup.
```

### 3.5 Cache behavior

```text
Ruling E: The cache is opt-in (--llm-enable-cache) AND mode-gated.
          It is only honored for anthropic-api and claude-cli.

  - --llm-enable-cache with mode == OFFLINE  -> LlmRuntimeError
                                                ("caching offline is
                                                 meaningless").
  - --llm-enable-cache with mode == MOCK     -> LlmRuntimeError
                                                ("caching mock is
                                                 meaningless").
  - Cache directory:  brain/.llm_cache  (the existing CachedClient
                       default; do not reroute writes elsewhere).
  - Cache writes happen only during eval_consistency, never at
    factory time.

Why: caching a deterministic stand-in masks the operator's intent
("did I run offline or did I replay a cache?"). Caching mock makes
the test response order ambiguous.

README must call out the cache directory and the opt-in semantics
in the implementation step (24F).
```

### 3.6 Trace / summary wording

```text
Ruling F: The Phase 2 v1 trace taxonomy (`llm.request`,
          `llm.response`, `llm.cache_hit`, `llm.cache_miss`,
          `llm.error`) already exists. The toggle does not add new
          trace event types.

          The local startup message (printed once on launch when not
          --print-once / --check-terminal) must include:

            "brain.ui: llm runtime mode = <mode> "
            "(<explanation>)"

          where <explanation> is one of:

            "default offline stand-in; no network, no shell"
            "deterministic mock; no network, no shell"
            "anthropic-api; cache=<on|off>"
            "claude-cli; executable=<path>; cache=<on|off>"

Why: the launch line is the operator's tactile feedback that the
mode they requested is the mode they got. It also surfaces the
cache state, which the audit may otherwise need to infer.

Implementation note: the message is printed to stdout (not stderr)
because it is informational, not an error. Avoid printing it when
--print-once or --check-terminal is supplied; those branches must
remain quiet.
```

### 3.7 Fixture status mapping

```text
Ruling G: Each I-LLMTOG-* row's status is determined by the
          mechanism the row asserts, not by the mode it discusses:

  - REQUIRED:
      * default offline behavior
      * closed mode enumeration
      * factory return type per mode (constructed but not invoked)
      * explicit opt-in semantics
      * credential / tool absence raises before launch
      * mock with empty responses raises before launch
      * cache rejection for offline / mock
      * --print-once independence from the selected client
      * AST audit: selected client enters tick() through the existing
        argument (no second classification path)

  - STRUCTURAL:
      * LlmRuntimeMode is a closed str-Enum
      * LlmRuntimeConfig is a frozen / slots-bearing dataclass with
        bounded fields
      * brain/ui/llm_runtime.py imports a forbidden-import-free list

  - OBSERVED:
      * any real model-backed walk that hits the Anthropic API or
        invokes the local `claude` CLI; the row records what was
        observed but cannot fail the runner.

  - NOT-EXERCISED:
      * LLM runtime save / export (no such path exists in 3.8b).
```

### 3.8 UI import-audit implications

```text
Ruling H: brain/ui/llm_runtime.py is allowed to import from
          brain.llm.client (it is the seam owner). brain/ui/__main__.py
          may import brain.ui.llm_runtime symbols; the existing
          OfflineStandInClient should either:

            (a) stay defined in brain/ui/__main__.py and be exported
                so brain.ui.llm_runtime can import it, OR
            (b) move to brain.ui.llm_runtime entirely, with
                brain.ui.__main__ re-exporting the name for backward
                compatibility.

          The implementation step chooses one; the corrigenda's
          mandate is that neither file imports brain.tlica, curses,
          os.system, subprocess (beyond the already-shipped
          ClaudeCLIClient encapsulation inside brain/llm/client.py),
          socket, urllib (beyond the already-shipped AnthropicAPIClient
          encapsulation), or http.

          The Phase 3.8 stream UI static audit (I-UISTRM-13) already
          rejects brain.llm imports in commands.py / command_line.py /
          session.py / snapshot.py / render.py. That audit does not
          extend to llm_runtime.py because the seam exists precisely
          to import brain.llm.client. The Phase 3.8b catalog patch
          plan will register an analogous I-LLMTOG-* static audit
          scoped to brain/ui/llm_runtime.py and brain/ui/__main__.py
          that allows brain.llm.client + brain.ui.commands /
          brain.ui.session imports but rejects everything else.
```

## 4. Resolution of likely-row sketch (kickoff section 12)

After the rulings above, the likely-row sketch refines to:

```text
REQUIRED:
  - Default LlmRuntimeConfig() builds OfflineStandInClient.
  - LlmRuntimeMode enumeration is closed; unknown strings raise.
  - Each accepted mode constructs the expected concrete class.
  - Explicit opt-in semantics: factory never reads env unless the
    parse layer wired it in.
  - anthropic-api without key raises LlmRuntimeError.
  - claude-cli without executable raises LlmRuntimeError.
  - mock with empty responses raises LlmRuntimeError.
  - Cache rejection for offline / mock.
  - --print-once independence from selected client.
  - Selected client enters tick() through the existing argument
    (AST audit / behavioral fixture).

STRUCTURAL:
  - LlmRuntimeConfig frozen / slots / bounded.
  - LlmRuntimeMode finite closed str-Enum.
  - Static audit over brain/ui/llm_runtime.py and the toggle path
    in brain/ui/__main__.py rejects forbidden imports.

OBSERVED:
  - Optional real model-backed smoke walk; documented, not gating.

NOT-EXERCISED:
  - LLM runtime save / export path placeholder.
```

The catalog patch plan (Step 24D) will determine the exact row count
(probably ~10 REQUIRED, ~3 STRUCTURAL, 1 OBSERVED, 1 NOT-EXERCISED)
and the fixture roster.

## 5. Risks reconsidered

```text
- Risk: a future contributor wires a curses key binding to flip
  modes mid-session. The corrigenda forbids it; the catalog patch
  plan should add a STRUCTURAL row that the parser exposes no
  mid-session mode transition function in brain/ui/llm_runtime.py.

- Risk: an env override is set with the right name but the wrong
  case (BRAIN_LLM_Mode). The parser does not consult arbitrary case
  variations; only the exact env var BRAIN_LLM_MODE is honored. A
  typo silently produces the default mode, which is offline — fail
  closed.

- Risk: the cache directory accumulates across runs and outlives
  the toggle. The implementation step must document that the cache
  is operator-owned (gitignored under brain/.llm_cache); the audit
  step (24G) must note that no automated wipe occurs.

- Risk: parse_llm_runtime_args becomes complex and starts importing
  brain.tlica or invoking subprocess. The corrigenda forbids both.
  The catalog patch plan should add an AST audit row that
  brain/ui/llm_runtime.py imports only the documented seam set.
```

## 6. Non-goals (still locked)

```text
- new LLMClient implementations
- non-offline mode as the default
- automatic credential / tool detection without opt-in
- model-backed scoring of stream evidence
- model output written to traces / scenarios / source histories
- new tick() argument signatures
- catalog rows that require a real model to pass
- mid-session mode flips
- model-backed `tick()` path alongside the existing one
```

## 7. Next artifact

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_CATALOG_PATCH_PLAN.md
```

The catalog patch plan sizes the I-LLMTOG-* row family, lists the
fixture roster, and stops at the Step 24D review gate.
