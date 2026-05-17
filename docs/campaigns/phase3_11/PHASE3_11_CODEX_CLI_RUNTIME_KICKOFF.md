# PHASE3_11_CODEX_CLI_RUNTIME_KICKOFF.md

## Purpose

Name the concrete design targets for the Phase 3.11 Codex CLI
runtime option track. This is a planning artifact only. It does
not edit `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `brain/invariants.py`,
`brain/ui/llm_runtime.py`, `brain/llm/client.py`,
`brain/ui/__main__.py`, or any guarded path.

The kickoff makes the synthesis's recommendations concrete and
prepares the Step 5 corrigenda. Every design target listed below
is a proposal subject to corrigenda lock. The corrigenda may
accept, reject, or refine each item. Implementation (Step 9) does
NOT begin until the Step 7 review gate accepts the Step 6
catalog patch plan.

```text
Status: DRAFT / REVIEW-GATED / NO-IMPLEMENTATION-YET
```

Hard rule:

```text
Do not implement until the Step 6 catalog patch plan is accepted
at the Step 7 review gate A.
```

---

## 1. Baseline

```text
Catalog version:  v0.19
REQUIRED:        212
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         15
Total fixtures:  130

Synthesis (Step 3) recommends:
  - Option A     (implement codex-cli in Phase 3.11, not deferral)
  - Option K-A   (dedicated CodexCLIClient mirroring ClaudeCLIClient)
  - Option F-A   (extend I-LLMTOG-* row family, no new family)

Preflight gates at HEAD:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  bash tools/check_all.sh                    All checks passed
```

---

## 2. Locked-or-proposed enum member

Proposed (corrigenda locks):

```python
class LlmRuntimeMode(str, Enum):
    """Finite closed enumeration of accepted LLM runtime modes."""

    OFFLINE = "offline"
    MOCK = "mock"
    ANTHROPIC_API = "anthropic-api"
    CLAUDE_CLI = "claude-cli"
    CODEX_CLI = "codex-cli"        # NEW
```

```text
Python member name:    CODEX_CLI
String value:          "codex-cli"
Position in enum:      after CLAUDE_CLI (stable order; appending
                       avoids reordering existing members)
Member count after:    5 (was 4)
```

The string value `"codex-cli"` matches Phase 3.8B convention
(lowercase, hyphen-separated, matches what an operator types
after `--llm-mode`). The Python member name `CODEX_CLI` matches
the existing `CLAUDE_CLI` sibling.

Audit consequences:

```text
- _ACCEPTED_MODE_VALUES at brain/ui/llm_runtime.py:128 grows
  from 4 to 5 entries.
- I-LLMTOG-02 (REQUIRED, mode_closed) continues to assert closed
  enumeration; the fixture's accepted-value list updates.
- I-LLMTOG-12 (STRUCTURAL, mode_closed) updates from "exact 4
  members" to "exact 5 members".
- argparse `--llm-mode` help text grows to include codex-cli.
```

---

## 3. Locked-or-proposed dataclass fields on LlmRuntimeConfig

Proposed addition to `LlmRuntimeConfig` (corrigenda locks):

```python
@dataclass(frozen=True, slots=True)
class LlmRuntimeConfig:
    mode: LlmRuntimeMode = LlmRuntimeMode.OFFLINE
    enable_cache: bool = False
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-6"
    claude_cli_executable: str = "claude"
    codex_cli_executable: str = "codex"     # NEW
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    mock_responses: tuple[str, ...] = ()
```

```text
New field:             codex_cli_executable: str = "codex"
Default value:         "codex"
Position in config:    after claude_cli_executable (stable order)
Field discipline:      bounded primitive (str), frozen dataclass
                       continues to hold; no new mutable type.
```

Timeout: **reused**, not duplicated.

```text
The synthesis recommends timeout_seconds is shared with
claude-cli, anthropic-api, and any future model-backed mode.
Adding codex_cli_timeout_seconds would:
  - duplicate state
  - widen the configurable surface for no operator benefit
  - require a new CLI flag (--llm-codex-cli-timeout) which
    widens the parser

The kickoff's default position: reuse timeout_seconds. The
corrigenda may override only if a concrete reason emerges (e.g.,
codex CLI is consistently slower than claude CLI and the
operator needs a per-mode override). The synthesis identifies no
such reason.
```

Frozen / slots: **preserved**.

```text
I-LLMTOG-11 (STRUCTURAL, config_frozen) continues to audit
LlmRuntimeConfig as frozen/slots over bounded primitives.
codex_cli_executable: str is a bounded primitive; the audit
remains green.
```

---

## 4. Locked-or-proposed CLI flag

Proposed addition to `brain/ui/__main__.py` argparse (corrigenda
locks):

```text
--llm-codex-cli-executable PATH
  Default: codex
  Help:    "Path or name of the codex executable to invoke when
           --llm-mode is codex-cli (default: codex). Resolved
           via shutil.which at session-launch time. Missing
           executable fails closed before launch."
```

Placement: after the existing `--llm-claude-cli-executable`
argument at `brain/ui/__main__.py:306`. The argument is parsed by
the same `parse_llm_runtime_args` helper at
`brain/ui/llm_runtime.py:157-326`.

Existing flags re-used unchanged:

```text
--llm-mode                {offline, mock, anthropic-api,
                           claude-cli, codex-cli}      (extends)
--llm-timeout             SECONDS                      (reused)
--llm-enable-cache                                     (reused)
```

Existing flags NOT extended:

```text
--llm-anthropic-api-key       (only ANTHROPIC_API uses it)
--llm-mock-response           (only MOCK uses it)
--llm-claude-cli-executable   (only CLAUDE_CLI uses it)
```

Environment variable extension (proposed; corrigenda locks):

```text
BRAIN_LLM_MODE=codex-cli      (existing env var; new value accepted)
BRAIN_LLM_CODEX_CLI_EXECUTABLE=<path>   (new env var;
                                         corrigenda may accept
                                         or reject)
```

The synthesis's default position is to add `BRAIN_LLM_MODE` value
recognition only and **not** add a codex-specific env var unless
the corrigenda finds a concrete reason. Phase 3.8B's pattern is
"explicit opt-in"; env vars alone do not flip the mode.

---

## 5. Locked-or-proposed backend class (Option K-A)

Proposed addition to `brain/llm/client.py` (corrigenda locks):

```python
@dataclass(frozen=True, slots=True)
class CodexCLIClient:
    """LLMClient backed by the codex CLI executable.

    The executable is resolved at __post_init__ time via
    shutil.which; missing executable raises RuntimeError. Each
    eval_consistency call is its own subprocess.run with the
    locked timeout_seconds. No long-lived subprocess handle is
    stored.
    """

    command: tuple[str, ...] = ("codex", "exec", "--full-auto")
    timeout_seconds: float = 60.0
    cwd: str = "/tmp"

    def __post_init__(self) -> None:
        # resolves self.command[0] via shutil.which; raises
        # RuntimeError("codex-cli executable '<x>' not on PATH")
        # if missing. Mirrors ClaudeCLIClient pattern.
        ...

    def eval_consistency(self, prompt: str) -> str:
        # subprocess.run(self.command, input=prompt,
        #                capture_output=True, text=True,
        #                timeout=self.timeout_seconds,
        #                cwd=self.cwd)
        # Non-zero return code -> RuntimeError("codex-cli
        # returned <n>: <stderr-bounded>"); TimeoutExpired ->
        # RuntimeError("codex-cli timed out after <s>s").
        ...
```

The dataclass shape mirrors `ClaudeCLIClient` at
`brain/llm/client.py:226-292` exactly. The only differences are:

```text
- command tuple default
- the executable name in the bounded error string
- (optionally) the cwd default if the corrigenda picks a
  different value
```

Command tuple candidates (corrigenda locks one):

```text
Candidate C-1:   ("codex", "exec", "--full-auto")
                 The OpenAI codex CLI documented invocation for
                 non-interactive use; reads prompt from stdin or
                 trailing positional argument depending on the
                 binary version.

Candidate C-2:   ("codex",)
                 Minimal; assumes the CLI reads the prompt from
                 stdin by default. Risk: depending on the
                 binary's mode-flag conventions, this may invoke
                 an interactive REPL rather than a single
                 prompt-response.

Candidate C-3:   ("codex", "exec")
                 If the codex binary has an "exec" subcommand
                 that takes a prompt and emits a response without
                 interactive flags.

Candidate C-4:   ("codex", "-p")
                 Mirrors the claude-cli "-p" (prompt) flag if
                 the codex binary uses the same convention.
```

The kickoff's working assumption is **C-1** but flags this as
the highest-uncertainty item. The Step 5 corrigenda must lock
one candidate (or pick a different one entirely) based on the
codex binary's actual invocation contract. If the contract
cannot be locked, the corrigenda must pick Option K-C (defer as
follow-up) and the Step 6 catalog patch plan reflects that
choice with only an OBSERVED row and no REQUIRED rows.

Where the class lives (Option K-A): `brain/llm/client.py`,
appended after `ClaudeCLIClient`. The static AST audit at
`I-LLMTOG-13` extends to cover the new class but does not need a
new audit row; the audit operates on the module file as a whole.

Resource discipline:

```text
- No new field on OperatorSession.
- No long-lived subprocess.Popen handle stored anywhere.
- No threading / asyncio / signal / atexit hook.
- No file handle stored on the class beyond the bounded
  dataclass fields.
- Subprocess.run is the only IPC mechanism.
- Each eval_consistency call is fully synchronous and bounded
  by timeout_seconds.
- No second classification path; this class only implements
  LLMClient.eval_consistency.
```

---

## 6. Locked-or-proposed factory branch

Proposed addition to `build_llm_client_from_config` at
`brain/ui/llm_runtime.py:390-463` (corrigenda locks):

```python
def build_llm_client_from_config(config: LlmRuntimeConfig) -> object:
    if config.mode is LlmRuntimeMode.OFFLINE:
        return _build_offline_client()
    if config.mode is LlmRuntimeMode.MOCK:
        return _build_mock_client(config)
    if config.mode is LlmRuntimeMode.ANTHROPIC_API:
        return _build_anthropic_client(config)
    if config.mode is LlmRuntimeMode.CLAUDE_CLI:
        return _build_claude_cli_client(config)
    if config.mode is LlmRuntimeMode.CODEX_CLI:        # NEW
        return _build_codex_cli_client(config)         # NEW
    raise LlmRuntimeError(f"unknown mode: {config.mode}")
```

Helper `_build_codex_cli_client(config)`:

```text
- Resolves config.codex_cli_executable via _which(...).
- If missing, raises LlmRuntimeError("codex-cli executable
  '<x>' not on PATH"). This is the LOAD-BEARING bounded local
  error; it fires BEFORE the session launches and is matched by
  the I-LLMTOG-16 REQUIRED row.
- Constructs CodexCLIClient(command=(resolved_exe, "exec",
  "--full-auto"), timeout_seconds=config.timeout_seconds,
  cwd="/tmp") (or the locked candidate from Section 5).
- If enable_cache is True, wraps in CachedClient (matching the
  claude-cli pattern).
- Never reads os.environ; the factory remains env-free.
```

---

## 7. Locked-or-proposed fixture roster

Proposed fixture files (corrigenda may extend or merge):

```text
NEW dedicated fixtures (codex-cli-specific):

  brain/ui/fixtures/llm_runtime_codex_cli_requires_executable.py
    Audits I-LLMTOG-16 (REQUIRED, NEW).
    Asserts:
      LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI,
                       codex_cli_executable="/nonexistent/codex-...")
      build_llm_client_from_config -> LlmRuntimeError
        with message naming both the path and the mode.

  brain/ui/fixtures/llm_runtime_codex_cli_factory.py
    Audits I-LLMTOG-17 (REQUIRED, NEW).
    Asserts:
      LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI,
                       codex_cli_executable=sys.executable)
      build_llm_client_from_config -> CodexCLIClient instance.
      No subprocess invocation; construction only.

EXTENDED in-place fixtures (cross-mode):

  llm_runtime_mode_closed.py
    Updates accepted-value tuple to include "codex-cli";
    asserts member count == 5 (was 4) for I-LLMTOG-12 STRUCTURAL.

  llm_runtime_factory_per_mode.py
    Extends per-mode dispatch dict to include CODEX_CLI ->
    CodexCLIClient.

  llm_runtime_explicit_opt_in.py
    Extends the audit set: env vars alone do not flip mode to
    codex-cli; CLI flag or BRAIN_LLM_MODE=codex-cli is required.

  llm_runtime_cache_gated.py
    Extends: CODEX_CLI + enable_cache -> CachedClient wrapping
    CodexCLIClient; same gating rule as claude-cli.

  llm_runtime_tick_seam.py
    Extends: selected client when mode is codex-cli enters
    tick() via the same run_curses(..., client=...) seam.

  llm_runtime_print_once_independent.py
    Extends: --print-once with --llm-mode codex-cli still exits
    0 even if codex_cli_executable is invalid.

  llm_runtime_config_frozen.py
    Extends: codex_cli_executable: str field is bounded;
    LlmRuntimeConfig remains frozen/slots.

  llm_runtime_static_audit.py
    Extends: AST audit covers the new module-level statements
    (none expected); the import set in
    brain/ui/llm_runtime.py and brain/llm/client.py remains
    bounded.

OBSERVED row (no fixture file; documentation only):

  I-LLMTOG-18 (OBSERVED, NEW)
    Real codex-cli smoke walk: documents how an operator can run
    `python3 -m brain.ui --llm-mode codex-cli
       --llm-codex-cli-executable /path/to/codex`
    with a real codex binary present and observe a single
    eval_consistency call. OBSERVED-only; cannot fail the runner.
```

Total fixture deltas:

```text
+ 2 new fixture files (codex_cli_requires_executable,
                       codex_cli_factory)
+ 0 new rows that need a dedicated fixture beyond those two
8 existing fixture files extended in place
+ 1 OBSERVED row (I-LLMTOG-18) without a fixture file
```

The Step 6 catalog patch plan binds the row numbers and the
exact fixture-row mapping.

---

## 8. Likely catalog row family (extends Step 3 estimate)

```text
NEW REQUIRED rows:
  I-LLMTOG-16   codex-cli without executable raises
                LlmRuntimeError before launch
                Fixture: llm_runtime_codex_cli_requires_executable.py
                Lean: same citation pattern as I-LLMTOG-06

  I-LLMTOG-17   CODEX_CLI factory returns CodexCLIClient
                Fixture: llm_runtime_codex_cli_factory.py
                Lean: same citation pattern as I-LLMTOG-03

NEW OBSERVED row:
  I-LLMTOG-18   Real codex-cli smoke walk (OBSERVED-only,
                no fixture, cannot fail the runner)

UPDATED row (existing):
  I-LLMTOG-12   STRUCTURAL: LlmRuntimeMode is (str, Enum) with
                EXACT 5 members (was 4)
                Fixture: llm_runtime_mode_closed.py (updated)

ROWS NOT NEEDED:
  No new STRUCTURAL row (the static audit and config_frozen
    rows already cover codex-cli implicitly when extended).
  No new NOT-EXERCISED row (I-LLMTOG-15 is shared across modes).
  No new DEFERRED row.
  No I-CODEXCLI-* family (synthesis option F-B is rejected by
    default; corrigenda may revisit).

Estimated count deltas from v0.19 to v0.20:
  + 2 REQUIRED       (I-LLMTOG-16, I-LLMTOG-17)
  + 0 STRUCTURAL     (I-LLMTOG-12 updates in place)
  + 0 NOT-EXERCISED
  + 0 DEFERRED
  + 1 OBSERVED       (I-LLMTOG-18)

Estimated v0.20 baseline:
  REQUIRED:    214   (212 + 2)
  STRUCTURAL:   83   (unchanged)
  NOT-EXERCISED: 9   (unchanged)
  DEFERRED:    12   (unchanged)
  OBSERVED:    16   (15 + 1)
```

The Step 6 plan binds the final numbers. If the corrigenda picks
Option K-C (defer), the count delta becomes:

```text
  + 0 REQUIRED
  + 0 STRUCTURAL
  + 0 NOT-EXERCISED  (no new NOT-EXERCISED placeholder)
  + 0 DEFERRED       (no new DEFERRED placeholder)
  + 1 OBSERVED       (I-LLMTOG-18 documents the deferred path)
```

Under K-C the enum is not extended either; codex-cli remains an
out-of-band documented future option until a follow-up campaign.

---

## 9. Disposition of cross-mode rows

The synthesis recommends extending in place. The kickoff
confirms:

```text
Extend in place (no new dedicated file):
  llm_runtime_mode_closed.py
  llm_runtime_factory_per_mode.py
  llm_runtime_explicit_opt_in.py
  llm_runtime_cache_gated.py
  llm_runtime_tick_seam.py
  llm_runtime_print_once_independent.py
  llm_runtime_config_frozen.py
  llm_runtime_static_audit.py

Dedicated new file:
  llm_runtime_codex_cli_requires_executable.py
  llm_runtime_codex_cli_factory.py
```

Rationale: cross-mode audits operate on the entire enum; adding
a per-mode dedicated copy would duplicate the assertion and
require a new catalog row, both of which the synthesis rejects.
codex-cli-specific REQUIRED rows get their own files (mirroring
the claude-cli pattern: a dedicated `claude_cli_requires_executable.py`
exists, not just an extension of cross-mode files).

---

## 10. Implement-vs-defer working position

Working position (corrigenda locks):

```text
Default: Option A (implement now) with Option K-A backend class.
Fallback: Option K-C (defer as follow-up) if the Step 5 corrigenda
         cannot lock the command tuple from Section 5 candidates.
```

The kickoff cannot lock the command tuple alone; that is the
corrigenda's job. The kickoff names the candidates (C-1..C-4) and
flags C-1 as the working assumption. If the corrigenda finds
that none of C-1..C-4 matches the real codex binary's invocation,
it picks K-C and the Step 6 plan reflects the deferral.

Acceptance criteria for A (re-stated from synthesis):

```text
1. Command tuple lockable in Section 5 of corrigenda.
2. Prompt-in / response-out shape deterministic enough to drive
   a bounded RuntimeError on failure.
3. Bounded stderr surface (single-line bounded excerpt).
4. Reliable non-zero exit code on failure.
5. Fixture pattern from claude-cli ports cleanly to codex-cli
   without modifying the Phase 3.8B audit surface.
```

Acceptance criteria for K-C (re-stated from synthesis):

```text
1. Command tuple uncertain.
2. Interactive auth required that the test environment cannot
   exercise even as OBSERVED.
3. Fixture pattern requires modifying Phase 3.8B audit surface.
4. File budget exceeded when combined with Steps 10-17.
```

The corrigenda must explicitly state which path is taken and
quote the criterion that drove the decision.

---

## 11. Stop point

The kickoff stops here. The next artifact is:

```text
PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md   (Step 5)
```

The corrigenda must lock:

```text
- mode spelling (final string value, member name, position)
- executable field name and default value
- whether timeout_seconds is reused (default) or a parallel
  field is introduced (with justification if so)
- whether Codex CLI gets a new backend class (K-A) or shares an
  abstract subprocess-CLI client (K-B) or is deferred (K-C)
- the command tuple (one of C-1..C-4 or a new locked tuple)
- the cwd default
- the fixture strategy (extend-in-place vs dedicated; per
  Section 9)
- the row family name (I-LLMTOG-* extension, per Section 8)
- the catalog count deltas (per Section 8)
- the file budget (per Section 12 of the synthesis)
- the OBSERVED smoke definition (I-LLMTOG-18 wording)
- the implement-vs-defer choice and the criterion that drove it
```

No catalog edits. No runtime edits. No fixture edits. No
implementation. The corrigenda is a planning artifact; the Step
6 catalog patch plan is also a planning artifact. The Step 7
review gate A is the next stopping point.
