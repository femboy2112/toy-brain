# PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md

## 1. Purpose

Audit the Phase 3.8b LLM Runtime Toggle implementation against the
accepted synthesis, kickoff, corrigenda, and catalog patch plan. This
document is an audit artifact: it does not edit
`brain/ui/llm_runtime.py`, `brain/ui/__main__.py`, fixtures,
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
or `brain/invariants.py`.

```text
Verdict for Step 24G: PASS
```

## 2. Baseline

```text
Catalog version:  v0.16
REQUIRED:        178
STRUCTURAL:       64
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         12
Total tabular:   275
Total fixtures:   91

Landed campaign steps:
  Step 24A  synthesis        commit 7b159a5
  Step 24B  kickoff          commit 6775806
  Step 24C  corrigenda       commit 6970adb
  Step 24D  catalog patch    commit 20484a4 (patched by 5af8976)
  Step 24E  catalog landed   commit f947a69
  Step 24F  implementation   commit 5247df4
  Step 24G  this audit       this document
```

Required source artifacts:

```text
PHASE3_8B_LLM_TOGGLE_AMENDMENT.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_CORRIGENDA.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_CATALOG_PATCH_PLAN.md
brain/ui/llm_runtime.py
brain/ui/__main__.py
brain/ui/fixtures/llm_runtime_*.py
INVARIANT_CATALOG.md (v0.16)
```

## 3. Default offline behavior

```text
Audit:    Default `LlmRuntimeConfig()` builds `OfflineStandInClient`;
          the factory does not consult `os.environ`.

Evidence: brain/ui/llm_runtime.py defines LlmRuntimeConfig with
          mode=LlmRuntimeMode.OFFLINE and enable_cache=False as the
          declared dataclass defaults. build_llm_client_from_config
          dispatches mode is LlmRuntimeMode.OFFLINE to
          _build_offline_client(), which returns
          OfflineStandInClient(). The body of
          build_llm_client_from_config contains no os.environ
          reference; the only env reads in the module are inside
          parse_llm_runtime_args (BRAIN_LLM_MODE, BRAIN_ANTHROPIC_API_KEY,
          ANTHROPIC_API_KEY) and inside _which() for PATH resolution.

Row:      I-LLMTOG-01 REQUIRED.
Fixture:  brain/ui/fixtures/llm_runtime_default_offline.py — passes
          under runner. The fixture sets stale ANTHROPIC_API_KEY /
          BRAIN_ANTHROPIC_API_KEY / BRAIN_LLM_MODE in os.environ and
          confirms the factory still returns OfflineStandInClient.

Status:   PASS.
```

## 4. Explicit model-backed opt-in

```text
Audit:    Model-backed modes require explicit opt-in via --llm-mode
          or BRAIN_LLM_MODE (supplied env). No other ambient state
          (API key presence, executable on PATH, cache files) is
          sufficient.

Evidence: parse_llm_runtime_args first sets resolved_mode = OFFLINE,
          then checks env["BRAIN_LLM_MODE"] and overlays with
          --llm-mode CLI. No code path elsewhere flips the mode. The
          factory never consults os.environ to determine mode.

Rows:     I-LLMTOG-02 REQUIRED (closed enumeration),
          I-LLMTOG-04 REQUIRED (explicit opt-in),
          I-LLMTOG-12 STRUCTURAL (str-Enum shape).
Fixtures: llm_runtime_mode_closed.py, llm_runtime_explicit_opt_in.py.
          Both pass under the runner. The opt-in fixture verifies
          that ANTHROPIC_API_KEY / BRAIN_ANTHROPIC_API_KEY in env
          without --llm-mode still resolve to OFFLINE, and that CLI
          --llm-mode wins over BRAIN_LLM_MODE.

Status:   PASS.
```

## 5. Client factory behavior

```text
Audit:    build_llm_client_from_config returns the documented
          backend per mode (or CachedClient wrapping the backend
          when caching is opt-in for ANTHROPIC_API / CLAUDE_CLI),
          performs no HTTP / subprocess invocation at factory
          time, and raises LlmRuntimeError locally before launch
          on insufficient config.

Evidence: brain/ui/llm_runtime.py:
            OFFLINE       -> OfflineStandInClient()
            MOCK          -> MockClient(config.mock_responses)
            ANTHROPIC_API -> AnthropicAPIClient(api_key=,
                              model=, timeout_seconds=)
            CLAUDE_CLI    -> ClaudeCLIClient(command=(...),
                              timeout_seconds=)
          Each model-backed branch is gated by a precondition
          check: api_key truthy for ANTHROPIC_API, _which(...) not
          None for CLAUDE_CLI, mock_responses non-empty for MOCK,
          enable_cache=False for OFFLINE / MOCK.

Rows:     I-LLMTOG-03 REQUIRED (factory return type per mode),
          I-LLMTOG-05 REQUIRED (anthropic-api requires key),
          I-LLMTOG-06 REQUIRED (claude-cli requires executable),
          I-LLMTOG-07 REQUIRED (mock requires responses),
          I-LLMTOG-08 REQUIRED (cache rejection / acceptance).
Fixtures: llm_runtime_factory_per_mode.py uses sys.executable as
          the CLAUDE_CLI executable so CI does not depend on a
          real Claude CLI being installed; it asserts construction
          only and never invokes eval_consistency.
          llm_runtime_anthropic_requires_key.py confirms api_key
          precedence: CLI > BRAIN_ANTHROPIC_API_KEY > ANTHROPIC_API_KEY,
          and that the factory does not consult os.environ when
          api_key=None (it raises even with stale env keys).
          llm_runtime_claude_cli_requires_executable.py confirms a
          missing executable raises LlmRuntimeError naming the
          executable and the mode.
          llm_runtime_mock_requires_responses.py confirms empty
          mock_responses raise; a non-empty tuple succeeds.
          llm_runtime_cache_gated.py confirms OFFLINE / MOCK + cache
          raise; ANTHROPIC_API / CLAUDE_CLI + cache produce
          CachedClient wrapping the expected backend with the
          brain/.llm_cache default cache_dir.

Status:   PASS.
```

## 6. Tick seam plumbing

```text
Audit:    The selected client enters tick() through the existing
          run_curses(session, client=..., ...) argument. No second
          client surface is constructed and no alternate
          classification path is invoked.

Evidence: brain/ui/__main__.py main() constructs the client via
          build_llm_client_from_config(llm_config) and passes it
          directly into run_curses(...). An AST audit (inside the
          llm_runtime_tick_seam.py fixture) confirms every
          run_curses(...) call in __main__.py supplies
          client=<bare local name `client`>. The static audit
          fixture additionally rejects any direct construction of
          AnthropicAPIClient / ClaudeCLIClient / MockClient /
          CachedClient inside __main__.py (the factory is the
          only construction site).

Row:      I-LLMTOG-09 REQUIRED.
Fixture:  llm_runtime_tick_seam.py — substitutes a no-op
          run_curses to observe the client argument and confirms
          it is the factory output for both OFFLINE and MOCK modes.

Status:   PASS.
```

## 7. --print-once independence

```text
Audit:    --print-once and --check-terminal return before any
          factory call so a stale config (missing key, missing
          executable, empty mock responses, unknown mode-tracked
          but with --print-once still passes) does not block the
          deterministic frame render.

Evidence: main() in brain/ui/__main__.py routes the
          --check-terminal and --print-once branches before
          calling _resolve_llm_runtime_config or
          build_llm_client_from_config. The fixture exercises
          each combination of --print-once with the four
          --llm-mode values (and the additional bad-config
          variants) and confirms exit code 0 with non-empty
          stdout.

Row:      I-LLMTOG-10 REQUIRED.
Fixture:  llm_runtime_print_once_independent.py — passes.

Status:   PASS.
```

## 8. LlmRuntimeConfig shape and audit

```text
Audit:    LlmRuntimeConfig is a frozen / slots-bearing dataclass
          over bounded primitives; LlmRuntimeMode is a closed
          str-Enum; the static audit over brain/ui/llm_runtime.py
          and the toggle path additions in brain/ui/__main__.py
          rejects forbidden imports and module-level side
          effects.

Evidence: brain/ui/llm_runtime.py:
            @dataclass(frozen=True, slots=True)
            class LlmRuntimeConfig:
                mode: LlmRuntimeMode = ...
                api_key: Optional[str] = None
                model: str = "claude-sonnet-4-6"
                claude_cli_executable: str = "claude"
                timeout_seconds: float = 30.0
                enable_cache: bool = False
                mock_responses: tuple[str, ...] = ()
            class LlmRuntimeMode(str, Enum):
                OFFLINE       = "offline"
                MOCK          = "mock"
                ANTHROPIC_API = "anthropic-api"
                CLAUDE_CLI    = "claude-cli"

          The static audit fixture parses brain/ui/llm_runtime.py
          and brain/ui/__main__.py, walks the AST, and verifies:
            - imports are confined to the documented seam set
              (stdlib + brain.llm.client + brain.ui.__main__).
            - no curses / brain.tlica / brain.tick / subprocess /
              shutil / socket / urllib / http / requests /
              tempfile import in llm_runtime.py.
            - no os.<forbidden-attr> (system, popen, exec*,
              spawn*, fork, kill) call in llm_runtime.py.
            - module-level statements are limited to imports,
              constants, function defs, and class defs (plus a
              module docstring); no @atexit decorator.
            - __main__.py imports parse_llm_runtime_args and
              build_llm_client_from_config from
              brain.ui.llm_runtime, and constructs no model-backed
              client class directly.

Rows:     I-LLMTOG-11 STRUCTURAL (frozen / slots),
          I-LLMTOG-13 STRUCTURAL (static audit).
Fixtures: llm_runtime_config_frozen.py, llm_runtime_static_audit.py
          — both pass under the runner.

Status:   PASS.
```

## 9. Fixture determinism

```text
Audit:    Every Phase 3.8b REQUIRED and STRUCTURAL row passes
          with no ANTHROPIC_API_KEY, no BRAIN_ANTHROPIC_API_KEY,
          and no `claude` executable on PATH. No fixture performs
          a real HTTP call or a real subprocess invocation.

Evidence: `python3 -m brain.invariants run --id I-LLMTOG` reports
          13 PASS (10 REQUIRED + 3 STRUCTURAL) with 0 failures.
          `bash tools/check_all.sh` reports 178 REQUIRED green,
          64 STRUCTURAL green, 7 OBSERVED pass / 0 fail, 0 gate
          failures.
          The CLAUDE_CLI construction-only fixture uses
          sys.executable (a guaranteed-present executable on the
          runner) instead of the real `claude` binary, and the
          fixture asserts construction only — eval_consistency
          is never invoked.

Status:   PASS.
```

## 10. OBSERVED smoke walk

```text
Audit:    The optional real model-backed smoke walk is OBSERVED
          and out-of-band; it cannot fail the runner. The walk is
          documented here.

Documented commands:

  # Anthropic API (requires a valid ANTHROPIC_API_KEY):
  ANTHROPIC_API_KEY=<key> python3 -m brain.ui \
      --print-once \
      --llm-mode anthropic-api \
      --llm-anthropic-api-key <key>

  # Claude CLI (requires the `claude` CLI on PATH):
  python3 -m brain.ui \
      --print-once \
      --llm-mode claude-cli

Expected behavior:
  - --print-once short-circuits before factory invocation, so
    these commands exit 0 without making a real call. To exercise
    a real call, run an interactive session (drop --print-once)
    and observe the llm.request / llm.response events on the
    next /step.

Row:      I-LLMTOG-14 OBSERVED.
Status:   OBSERVED (audit-cited; not a runner gate). No real walk
          performed by the runner. The walk above is the
          campaign-documented manual smoke; this audit does not
          require it to run to pass.
```

## 11. NOT-EXERCISED guard

```text
Audit:    No Phase 3.8b LLM runtime save, export, serialization,
          trace weaving, scenario weaving, or write-to-disk path
          exists outside the existing CachedClient cache directory
          (brain/.llm_cache).

Evidence: brain/ui/llm_runtime.py has no file open / write call,
          no urllib / socket / subprocess import, and no
          LLM-result-to-disk path. The CachedClient writes live in
          brain/llm/client.py (an existing Phase 2 v1 surface)
          and remain out of scope for Phase 3.8b. The static audit
          fixture rejects the forbidden imports that would enable a
          save / export path.

Row:      I-LLMTOG-15 NOT-EXERCISED.
Status:   PASS (placeholder is in place; no path exists).
```

## 12. Interaction with the Phase 3.8 audit

```text
The final Phase 3.8 audit (Step 25) must certify that the Operator
Stream Interaction surface continues to work with the default
offline mode AND with the new --llm-mode toggle.

Compatibility properties:

  - The Phase 3.8 stream surface uses /step (and /tick) as the
    only routes that call tick(). The selected LLM client enters
    tick() through the existing run_curses(session, client=...,
    ...) argument, which Phase 3.8 already depends on.

  - The /stream-promote route queues exactly one explicit
    StreamPromotionCandidate through OperatorEventQueue.enqueue.
    Whether the next tick() consumes that event under OFFLINE,
    MOCK, ANTHROPIC_API, or CLAUDE_CLI is opaque to the toggle:
    the toggle only selects which LLMClient backs the tick path.

  - The Phase 3.8 static audit (I-UISTRM-10, I-UISTRM-13)
    rejects brain.llm imports in commands.py / command_line.py /
    session.py / snapshot.py / render.py. That audit does NOT
    extend to llm_runtime.py because llm_runtime.py is the
    documented seam owner. The Phase 3.8b static audit
    (I-LLMTOG-13) is the analogous gate scoped to
    llm_runtime.py.

  - The I-UI-07 forbidden-import audit (filesystem mutation
    surfaces: shutil, tempfile, etc.) continues to apply to
    every file under brain/ui/. brain/ui/llm_runtime.py uses
    only os.path / os.access / os.environ["PATH"] for read-only
    executable resolution and stdlib for everything else; no
    shutil import was added.

Conclusion: the Phase 3.8 audit can certify all of Phase 3.8
plus Phase 3.8b without additional carve-outs.
```

## 13. Full gate

```text
Required final validation (run on the post-Step-24F tree):

  python3 -m tools.catalog counts
    -> Banner / Actual / Expected agree on
       REQUIRED=178, STRUCTURAL=64, NOT-EXERCISED=9,
       DEFERRED=12, OBSERVED=12.

  python3 -m tools.citations verify
    -> Verified 100 citations. All catalog citations resolve in
       lean_reference/.

  python3 -m tools.import_audit
    -> I-PCE-05: agency.py is clean of pce imports.

  python3 -m brain.invariants run
    -> 249 rows checked
       REQUIRED green: 178 · REQUIRED red: 0
       STRUCTURAL green: 64 · STRUCTURAL red: 0
       OBSERVED: 7 pass / 0 fail
       gate failures: 0

  bash tools/check_all.sh
    -> All checks passed.

All gates green.
```

## 14. Recommended next mission

```text
Step 25  Phase 3.8 audit
Step 26  End-to-end dry-run documentation
Step 27  Final PR preparation
```

The Phase 3.8 audit (Step 25) should now certify that the
complete operator stream interaction loop works with both the
default offline mode and the new explicit --llm-mode toggle. The
dry-run document (Step 26) should include both a default-offline
walkthrough and an optional model-backed launch example using
the documented `--llm-mode anthropic-api` / `--llm-mode
claude-cli` flags from this audit's section 10.

## 15. Verdict

```text
PASS

Phase 3.8b LLM Runtime Toggle is implemented per the accepted
synthesis, kickoff, corrigenda, and catalog patch plan. All
I-LLMTOG-01..13 rows are green; I-LLMTOG-14 OBSERVED is
documented; I-LLMTOG-15 NOT-EXERCISED guard is in place. The
default offline behavior is preserved; model-backed modes are
explicit opt-in; the selected client enters tick() through the
existing seam; and no second classification path was introduced.
```
