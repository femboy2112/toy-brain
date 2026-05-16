# PHASE3_8B_LLM_RUNTIME_TOGGLE_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in
`PHASE3_8B_LLM_RUNTIME_TOGGLE_CORRIGENDA.md` to concrete catalog
rows, statuses, file budget, count delta, fixture roster, and
pending-registration mechanics. This is a planning artifact only.
It does not apply catalog rows, edit `tools/catalog.py`, add runtime
modules, add fixtures, change generated catalog IDs, alter
`INVARIANT_CATALOG.md`, change `brain/invariants.py`, or update
README as though implementation exists.

Verdict for the Step 24D review gate after the review patch:

```text
COHERENT - READY FOR REVIEW GATE AFTER REQUIRED PATCHES
```

Review patch disposition:

```text
PATCHED: env resolution belongs only to parse_llm_runtime_args(...).
PATCHED: build_llm_client_from_config(...) never reads os.environ.
PATCHED: Anthropic key precedence is CLI > BRAIN_ANTHROPIC_API_KEY > ANTHROPIC_API_KEY.
PATCHED: CLAUDE_CLI factory-per-mode fixtures may use sys.executable and must not invoke eval_consistency.
```

## 2. Baseline

```text
Catalog version:  v0.15
REQUIRED:        168
STRUCTURAL:       61
NOT-EXERCISED:     8
DEFERRED:         12
OBSERVED:         11
Total tabular:   260
```

Required latest audit:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION (Step 24 implementation green)
```

Accepted planning artifacts:

```text
PHASE3_8B_LLM_TOGGLE_AMENDMENT.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_CORRIGENDA.md
```

## 3. Patch impact

```text
+ 10 REQUIRED
+  3 STRUCTURAL
+  1 NOT-EXERCISED
+  0 DEFERRED
+  1 OBSERVED
```

Expected counts after the accepted patch:

```text
Catalog version:  v0.16
REQUIRED:        178
STRUCTURAL:       64
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         12
Total tabular:   275
```

## 4. Row family thesis

Row family:

```text
I-LLMTOG-*
```

Family spelling rationale:

```text
Use I-LLMTOG-* rather than I-LLM-TOG-* or I-LLM-TOGGLE-* because the
current catalog parser recognizes row IDs in the I-<UPPERCASEMODULE>-NN
shape. A second hyphen inside the module token would not be parsed by
tools/catalog.py without a tooling change. The compact LLMTOG form
also avoids collision with the existing I-LLM-01..04 Phase 2 v1
LLM-Protocol rows.
```

Core commitments:

```text
The Phase 3.8b LLM Runtime Toggle introduces one operator-facing CLI
surface (`--llm-mode <mode>`) plus a small typed helper module
(`brain/ui/llm_runtime.py`). It does NOT introduce a new LLMClient
implementation, does NOT add a second classification path, and does
NOT modify `brain/tick.py` or `brain/llm/client.py`.

Default mode is offline. The factory returns `OfflineStandInClient`
for `LlmRuntimeConfig()`. Model-backed modes require explicit opt-in
via `--llm-mode` or the `BRAIN_LLM_MODE` env override.

Environment resolution happens only inside parse_llm_runtime_args(argv,
env). That parser resolves mode and per-mode config values from the
provided argv / env inputs and returns an explicit LlmRuntimeConfig.
build_llm_client_from_config(config) never reads os.environ; it only
validates and builds from the supplied config.

Credential / tool availability checks happen at factory time against
fields already present on the config. The factory raises
`LlmRuntimeError` before any session or curses initialization when the
explicit config is insufficient (for example, ANTHROPIC_API with
api_key=None, CLAUDE_CLI with a missing executable, or MOCK with no
responses).

Cache wrapping is opt-in via `--llm-enable-cache` and is honored only
for `anthropic-api` and `claude-cli`. Cache writes happen only inside
`CachedClient.eval_consistency`, never at factory time.

The selected client enters the kernel through the existing
`tick(..., client, ...)` argument. No second classification path is
introduced. `/step` remains the only route that calls `tick()`.

Standard fixtures remain deterministic. Every REQUIRED and
STRUCTURAL row passes with no `ANTHROPIC_API_KEY`, no
`BRAIN_ANTHROPIC_API_KEY`, and no `claude` executable on PATH. Any
real model-backed smoke walk is OBSERVED and cannot fail the runner.
```

## 5. Row table

All rows use the `I-LLMTOG-*` family. Owning modules are
`brain/ui/llm_runtime.py` and `brain/ui/__main__.py` unless noted.

### 5.1 REQUIRED rows

```text
I-LLMTOG-01  Default LlmRuntimeConfig() builds OfflineStandInClient.
              LlmRuntimeConfig() with no arguments produces a record
              whose `mode` is LlmRuntimeMode.OFFLINE and whose
              `enable_cache` is False;
              build_llm_client_from_config(LlmRuntimeConfig())
              returns an instance of OfflineStandInClient and does
              not consult `os.environ`.
              Fixture: llm_runtime_default_offline.py

I-LLMTOG-02  LlmRuntimeMode is a finite closed enumeration.
              LlmRuntimeMode exposes exactly OFFLINE, MOCK,
              ANTHROPIC_API, CLAUDE_CLI; construction with any other
              value raises (or the parse helper raises
              LlmRuntimeError) before a config is built.
              Fixture: llm_runtime_mode_closed.py

I-LLMTOG-03  Each accepted mode returns the expected concrete client
              type without invoking it.
              build_llm_client_from_config(<each mode>) returns an
              instance whose class is the documented backend
              (OfflineStandInClient, MockClient, AnthropicAPIClient,
              ClaudeCLIClient), or a CachedClient wrapping the
              backend when caching is enabled. No HTTP / subprocess
              call is performed at factory time.

              Fixture note: for CLAUDE_CLI construction checks,
              llm_runtime_factory_per_mode.py may pass
              claude_cli_executable=sys.executable or another
              guaranteed-present executable so CI does not require the
              real Claude CLI. The fixture asserts construction only;
              it must not invoke eval_consistency.
              Fixture: llm_runtime_factory_per_mode.py

I-LLMTOG-04  Model-backed modes require explicit opt-in.
              parse_llm_runtime_args(argv=[], env={}) returns a
              config whose mode is OFFLINE regardless of whether
              ANTHROPIC_API_KEY, BRAIN_ANTHROPIC_API_KEY, or
              `claude` is present in the ambient environment; only
              --llm-mode (or BRAIN_LLM_MODE) selects a non-offline
              mode.
              Fixture: llm_runtime_explicit_opt_in.py

I-LLMTOG-05  ANTHROPIC_API without a resolved api_key raises before
              launch.
              parse_llm_runtime_args resolves api_key in this order:
                1. CLI --llm-anthropic-api-key
                2. BRAIN_ANTHROPIC_API_KEY from the supplied env
                3. ANTHROPIC_API_KEY from the supplied env
              The returned LlmRuntimeConfig.api_key contains the
              resolved value or None. build_llm_client_from_config(
                LlmRuntimeConfig(
                  mode=LlmRuntimeMode.ANTHROPIC_API,
                  api_key=None,
                )
              ) raises LlmRuntimeError naming the missing API key.
              The factory does not consult os.environ.
              Fixture: llm_runtime_anthropic_requires_key.py

I-LLMTOG-06  CLAUDE_CLI without executable raises before launch.
              build_llm_client_from_config(LlmRuntimeConfig(
                mode=LlmRuntimeMode.CLAUDE_CLI,
                claude_cli_executable="<not-on-path>")) raises
              LlmRuntimeError naming the missing executable; no
              ClaudeCLIClient instance is returned.
              Fixture: llm_runtime_claude_cli_requires_executable.py

I-LLMTOG-07  MOCK with empty responses raises before launch.
              build_llm_client_from_config(LlmRuntimeConfig(
                mode=LlmRuntimeMode.MOCK)) raises LlmRuntimeError
              when mock_responses is empty.
              Fixture: llm_runtime_mock_requires_responses.py

I-LLMTOG-08  Cache wrapping is opt-in and mode-gated.
              build_llm_client_from_config(LlmRuntimeConfig(
                mode=LlmRuntimeMode.OFFLINE, enable_cache=True))
              raises LlmRuntimeError; same for MOCK. With
              enable_cache=True and ANTHROPIC_API / CLAUDE_CLI,
              the returned client is a CachedClient wrapping the
              expected backend, and the cache directory is the
              brain/.llm_cache default.
              Fixture: llm_runtime_cache_gated.py

I-LLMTOG-09  Selected client enters tick() through the existing
              argument.
              The `main()` entrypoint passes the
              build_llm_client_from_config(...) result through to
              `run_curses(session, client=..., ...)`; no second
              client surface is constructed and no alternate
              classification path is invoked. The fixture performs
              a behavioral check against the entrypoint plumbing
              (substituting a no-op `run_curses` to observe the
              client argument) and an AST audit that confirms
              `run_curses(` calls in brain/ui/__main__.py use the
              factory output.
              Fixture: llm_runtime_tick_seam.py

I-LLMTOG-10  --print-once remains independent of the selected client.
              `python3 -m brain.ui --print-once` succeeds with each
              of `--llm-mode offline`, `--llm-mode mock --llm-mock-
              response PRESERVE`, `--llm-mode anthropic-api` (no
              key), and `--llm-mode claude-cli` (no executable),
              because the --print-once branch returns before the
              factory is invoked. The fixture exercises each combo
              and asserts the entrypoint exits 0 without
              constructing a real backend.
              Fixture: llm_runtime_print_once_independent.py
```

### 5.2 STRUCTURAL rows

```text
I-LLMTOG-11  LlmRuntimeConfig is a frozen / slots-bearing record.
              LlmRuntimeConfig is a dataclass(frozen=True,
              slots=True); fields are bounded primitives, Optional
              bounded strings, a bounded float timeout, a bool, and
              a tuple of bounded printable strings; no field is a
              callable, file handle, socket, subprocess handle, or
              LLM client instance.
              Fixture: llm_runtime_config_frozen.py

I-LLMTOG-12  LlmRuntimeMode is a finite closed str-Enum.
              LlmRuntimeMode is a `str, Enum` subclass whose
              members are exactly the documented four values; the
              membership set is the same as the runtime audit in
              I-LLMTOG-02 but the check is STRUCTURAL because the
              enumeration shape (str-Enum, finite member list) is
              the assertion under test.
              Fixture: llm_runtime_mode_closed.py

I-LLMTOG-13  Static audit over the LLM runtime surface rejects
              forbidden imports and side effects.
              An AST audit over brain/ui/llm_runtime.py and the
              toggle path additions in brain/ui/__main__.py rejects
              imports of `curses`, `brain.tlica`, `brain.tick`, and
              anything outside the documented seam set
              (stdlib + brain.llm.client + brain.ui.commands +
              brain.ui.session + brain.ui.snapshot + brain.ui.render
              + brain.ui.transcript + brain.ui.composer +
              brain.ui.tui). Module-level statements other than
              imports, constants, function defs, and class defs
              are rejected (no @atexit registration, no module-load
              subprocess call, no module-load HTTP probe).
              Fixture: llm_runtime_static_audit.py
```

### 5.3 OBSERVED row

```text
I-LLMTOG-14  Optional real model-backed smoke walk.
              A documented out-of-band smoke walk that launches
              `python3 -m brain.ui --print-once --llm-mode
              anthropic-api` (or `--llm-mode claude-cli`) records
              successful client construction, a real
              eval_consistency call, and the resulting trace events;
              the row is OBSERVED and cannot fail the runner. The
              walk is documented in
              PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md.
              Fixture: (none — audit-cited)
```

### 5.4 NOT-EXERCISED row

```text
I-LLMTOG-15  LLM runtime save / export path is NOT-EXERCISED.
              No Phase 3.8b LLM runtime save, export, serialization,
              trace weaving, scenario weaving, or write-to-disk path
              outside the existing CachedClient cache directory
              exists in this campaign; any future write path
              requires an explicit reviewed policy artifact,
              dedicated catalog rows, fixtures, and a stop
              condition.
              Fixture: none.
```

## 6. Fixture roster

```text
I-LLMTOG-01  llm_runtime_default_offline.py
I-LLMTOG-02  llm_runtime_mode_closed.py
I-LLMTOG-03  llm_runtime_factory_per_mode.py
I-LLMTOG-04  llm_runtime_explicit_opt_in.py
I-LLMTOG-05  llm_runtime_anthropic_requires_key.py
I-LLMTOG-06  llm_runtime_claude_cli_requires_executable.py
I-LLMTOG-07  llm_runtime_mock_requires_responses.py
I-LLMTOG-08  llm_runtime_cache_gated.py
I-LLMTOG-09  llm_runtime_tick_seam.py
I-LLMTOG-10  llm_runtime_print_once_independent.py
I-LLMTOG-11  llm_runtime_config_frozen.py
I-LLMTOG-12  llm_runtime_mode_closed.py     (shared with I-LLMTOG-02)
I-LLMTOG-13  llm_runtime_static_audit.py
I-LLMTOG-14  OBSERVED; documented in audit
I-LLMTOG-15  NOT-EXERCISED; no fixture
```

Fixture file delta: **12** new files.

```text
brain/ui/fixtures/llm_runtime_default_offline.py
brain/ui/fixtures/llm_runtime_mode_closed.py
brain/ui/fixtures/llm_runtime_factory_per_mode.py
brain/ui/fixtures/llm_runtime_explicit_opt_in.py
brain/ui/fixtures/llm_runtime_anthropic_requires_key.py
brain/ui/fixtures/llm_runtime_claude_cli_requires_executable.py
brain/ui/fixtures/llm_runtime_mock_requires_responses.py
brain/ui/fixtures/llm_runtime_cache_gated.py
brain/ui/fixtures/llm_runtime_tick_seam.py
brain/ui/fixtures/llm_runtime_print_once_independent.py
brain/ui/fixtures/llm_runtime_config_frozen.py
brain/ui/fixtures/llm_runtime_static_audit.py
```

If implementation combines `llm_runtime_mode_closed.py` so that one
fixture file drives both I-LLMTOG-02 and I-LLMTOG-12, the catalog
patch must reflect the shared fixture column explicitly. Other
fixture combinations require updating this roster before landing
rows.

## 7. File budget

Modified files for Step 24E (catalog patch):

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Expected modified / new files for Step 24F (implementation):

```text
brain/ui/llm_runtime.py                          (new)
brain/ui/__main__.py                             (extends parser /
                                                  client selection)
brain/ui/fixtures/llm_runtime_default_offline.py        (new)
brain/ui/fixtures/llm_runtime_mode_closed.py            (new)
brain/ui/fixtures/llm_runtime_factory_per_mode.py       (new)
brain/ui/fixtures/llm_runtime_explicit_opt_in.py        (new)
brain/ui/fixtures/llm_runtime_anthropic_requires_key.py (new)
brain/ui/fixtures/llm_runtime_claude_cli_requires_executable.py (new)
brain/ui/fixtures/llm_runtime_mock_requires_responses.py (new)
brain/ui/fixtures/llm_runtime_cache_gated.py            (new)
brain/ui/fixtures/llm_runtime_tick_seam.py              (new)
brain/ui/fixtures/llm_runtime_print_once_independent.py (new)
brain/ui/fixtures/llm_runtime_config_frozen.py          (new)
brain/ui/fixtures/llm_runtime_static_audit.py           (new)
brain/invariants.py                                     (FIXTURE_MODULES)
README.md                                               (after impl)
```

`README.md` should be updated only after the accepted implementation
exists. Step 24E should not document `--llm-mode` as available.

Explicitly excluded unless a future accepted plan reopens them:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/client.py
brain/llm/parse.py
brain/llm/prompts.py
brain/llm/ptcns_backed.py
```

## 8. Catalog patch mechanics (Step 24E)

```text
1. Add the 15 new I-LLMTOG-* row entries to INVARIANT_CATALOG.md
   under a new "### Phase 3.8b LLM Runtime Toggle UI invariants"
   section.

2. Add a v0.16 catalog-version banner above v0.15 documenting the
   +10 REQUIRED / +3 STRUCTURAL / +1 NOT-EXERCISED / +1 OBSERVED
   expansion.

3. Update the summary counts in INVARIANT_CATALOG.md to:
   REQUIRED 178, STRUCTURAL 64, NOT-EXERCISED 9, DEFERRED 12,
   OBSERVED 12.

4. Update tools/catalog.py EXPECTED_COUNTS to the same values.

5. Run python3 -m tools.catalog generate-ids to refresh
   brain/_catalog_ids.py.

6. Add _PHASE3_8B_PENDING_ROWS in brain/invariants.py with every
   REQUIRED and STRUCTURAL row that is not yet backed by a real
   fixture. OBSERVED I-LLMTOG-14 and NOT-EXERCISED I-LLMTOG-15 do
   not participate in I-CAT-01 coverage.

7. Validate with:
   python3 -m tools.catalog counts
   python3 -m tools.catalog generate-ids
   python3 -m tools.catalog counts
```

Step 24E should commit and push after count validation only. It
should not implement the runtime toggle, the factory, the parser,
or the fixtures.

## 9. Implementation mechanics (Step 24F)

The later implementation step drains `_PHASE3_8B_PENDING_ROWS` by
landing fixture-backed checks in a controlled order:

```text
1. Add brain/ui/llm_runtime.py with LlmRuntimeMode,
   LlmRuntimeConfig, LlmRuntimeError, parse_llm_runtime_args,
   build_llm_client_from_config.
2. Extend brain/ui/__main__.py:
     - extend build_arg_parser with the new flags
     - pass argv and env into parse_llm_runtime_args
     - resolve api_key inside parse_llm_runtime_args using:
         CLI --llm-anthropic-api-key
         then BRAIN_ANTHROPIC_API_KEY
         then ANTHROPIC_API_KEY
     - build the config from CLI + env, fail before session
     - print the startup mode line on the normal launch path
     - keep --print-once / --check-terminal independent
     - pass the resolved client into run_curses(...)
3. Add fixtures in order:
     - llm_runtime_mode_closed.py (drives I-LLMTOG-02, I-LLMTOG-12)
     - llm_runtime_config_frozen.py (drives I-LLMTOG-11)
     - llm_runtime_default_offline.py (drives I-LLMTOG-01)
     - llm_runtime_factory_per_mode.py (drives I-LLMTOG-03;
       uses sys.executable or another guaranteed-present executable
       for CLAUDE_CLI construction checks and does not invoke
       eval_consistency)
     - llm_runtime_explicit_opt_in.py (drives I-LLMTOG-04)
     - llm_runtime_anthropic_requires_key.py (drives I-LLMTOG-05)
     - llm_runtime_claude_cli_requires_executable.py (I-LLMTOG-06)
     - llm_runtime_mock_requires_responses.py (drives I-LLMTOG-07)
     - llm_runtime_cache_gated.py (drives I-LLMTOG-08)
     - llm_runtime_tick_seam.py (drives I-LLMTOG-09)
     - llm_runtime_print_once_independent.py (drives I-LLMTOG-10)
     - llm_runtime_static_audit.py (drives I-LLMTOG-13)
4. Update README only after behavior exists.
```

Expected targeted validations:

```bash
python3 -m brain.invariants run --id I-LLMTOG
python3 -m brain.invariants run --id I-UI
python3 -m brain.invariants run --id I-UISTRM
python3 -m brain.invariants run --id I-LLM
bash tools/check_all.sh
```

## 10. Accepted constants

```text
LlmRuntimeMode.OFFLINE          "offline"
LlmRuntimeMode.MOCK             "mock"
LlmRuntimeMode.ANTHROPIC_API    "anthropic-api"
LlmRuntimeMode.CLAUDE_CLI       "claude-cli"
LlmRuntimeConfig.timeout_seconds (default)      30.0
LlmRuntimeConfig.model           (default)      "claude-sonnet-4-6"
LlmRuntimeConfig.claude_cli_executable (default) "claude"
LlmRuntimeConfig.enable_cache    (default)      False
LlmRuntimeConfig.mock_responses  (default)      ()
CachedClient cache_dir           (default)      Path("brain/.llm_cache")
```

These constants are owned by `brain/ui/llm_runtime.py` (toggle-side)
and `brain/llm/client.py` (backend-side). The constant-parity audit
inside the new static audit fixture asserts the toggle-side defaults
match the kickoff and corrigenda numbers.

## 11. Non-goals to preserve

```text
no new LLMClient implementations beyond the four shipped backends
no non-offline default
no automatic credential / tool detection without opt-in
no environment read inside build_llm_client_from_config
no model-backed scoring of stream evidence
no model output reaching traces / scenarios / source histories
no new tick() argument signatures
no catalog rows that require a real model to pass
no mid-session mode flips
no model-backed `tick()` path alongside the existing one
no curses key binding for mode selection
no implicit cache enable
```

## 12. Review gate

Stop after this plan is committed and pushed.

```text
Do not apply v0.16 catalog rows.
Do not edit tools/catalog.py.
Do not edit brain/_catalog_ids.py.
Do not edit brain/invariants.py.
Do not add brain/ui/llm_runtime.py.
Do not edit brain/ui/__main__.py.
Do not add llm_runtime_* fixtures.
Do not update README to advertise --llm-mode.
Do not proceed to Step 24E until this patched plan is explicitly accepted.
```

## Conclusion

This plan is coherent after the required review-gate patches. The next
campaign step, if accepted, is:

```text
Step 24E - Apply accepted LLM toggle catalog patch
```