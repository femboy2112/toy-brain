# PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md

## Purpose

Lock every Codex CLI runtime option design choice before the
Step 6 catalog patch plan binds the rows. This is the decision
document. It is a planning artifact only and does not edit
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, `brain/ui/llm_runtime.py`,
`brain/llm/client.py`, `brain/ui/__main__.py`, or any guarded
path.

The corrigenda follows the synthesis (Step 3) and the kickoff
(Step 4). Where the synthesis recommended and the kickoff
proposed, the corrigenda **locks**. Every section below records
a final decision, the rationale, and the rejected alternative if
any. The Step 6 catalog patch plan reads from this document; the
Step 7 review gate A reads from both.

```text
Status: LOCKED / IMPLEMENT (Option A) / K-A / F-A
```

Hard rule (unchanged):

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

Preflight at HEAD of campaign branch:
  check_all.sh                    All checks passed
  catalog counts                  ok / ok / ok
  citations verify                100 citations resolve
  import_audit                    agency.py clean
```

---

## 2. LOCKED: implement vs defer

**Decision: Option A (implement codex-cli in Phase 3.11).**

```text
The synthesis Section 10 acceptance criteria for A are satisfied:

1. Deterministic fixtures do NOT require the real codex binary.
   The REQUIRED rows audit factory behavior (construction only,
   no subprocess invocation) and bounded missing-exec error.
   The codex CLI's actual invocation contract is exercised only
   by the OBSERVED smoke, which is operator-driven and cannot
   fail the runner.

2. The factory's bounded-error path (LlmRuntimeError on missing
   exec) is independent of the codex binary's actual behavior;
   it depends only on shutil.which("codex") returning None.

3. The fixture pattern from claude-cli ports cleanly. Two
   dedicated fixtures + eight in-place extensions mirror the
   Phase 3.8B layout without modifying the Phase 3.8B audit
   surface itself; existing fixtures are extended, not
   replaced.

4. The file budget is bounded (~10 fixture edits + 1 new client
   class + 1 factory branch + 1 CLI flag + catalog edits).
   It fits inside the campaign's macro sequence.

5. The campaign's name is "live behavior test"; implementing
   codex-cli is a precondition for the LLM runtime behavior
   report (Step 17). Deferring would make Step 17 incomplete.

Rejected alternative: Option K-C (defer as follow-up).
Rationale for rejection: the acceptance criteria above
demonstrate that the implementation work does not depend on
locking the real codex invocation contract for deterministic
tests; only the OBSERVED smoke depends on it, and OBSERVED rows
are by definition optional. Deferring would leave the LLM
runtime behavior report (Step 17) incomplete without any
deterministic gain.
```

---

## 3. LOCKED: enum member spelling

```python
class LlmRuntimeMode(str, Enum):
    OFFLINE = "offline"
    MOCK = "mock"
    ANTHROPIC_API = "anthropic-api"
    CLAUDE_CLI = "claude-cli"
    CODEX_CLI = "codex-cli"        # LOCKED
```

```text
Python member name:    CODEX_CLI
String value:          "codex-cli"
Position in enum:      appended AFTER CLAUDE_CLI (stable order;
                       avoids reordering existing members; stable
                       repr).
Member count after:    5 (was 4)

Rejected alternative: position before CLAUDE_CLI (rejected:
reorders existing members, changes the str(LlmRuntimeMode.*)
repr order for any existing test that iterates the enum in
declaration order).
```

---

## 4. LOCKED: executable field

Added to `LlmRuntimeConfig`:

```python
codex_cli_executable: str = "codex"        # LOCKED
```

```text
Field name:        codex_cli_executable
Type:              str
Default value:     "codex"
Position:          after claude_cli_executable
Field discipline:  bounded primitive; LlmRuntimeConfig remains
                   frozen + slots over bounded primitives;
                   I-LLMTOG-11 audit holds.

Rejected alternative: codex_executable (no _cli suffix).
Rationale for rejection: the existing field is
claude_cli_executable, with _cli explicitly indicating "CLI
backend executable". codex_executable could be misread as
"anything codex-related"; codex_cli_executable matches the
sibling and the mode spelling.
```

---

## 5. LOCKED: timeout discipline

**Decision: REUSE `timeout_seconds`. Do not introduce a parallel
`codex_cli_timeout_seconds` field.**

```text
Rationale:
  - The existing timeout_seconds field is shared across
    ANTHROPIC_API, CLAUDE_CLI, and the (currently-unused for
    construction) OFFLINE/MOCK modes. Adding a per-mode timeout
    would duplicate state and widen the CLI parser surface for
    no operator benefit.
  - No concrete reason (slower binary, longer-running
    invocation) has been demonstrated for a codex-specific
    timeout.
  - The Phase 3.8B audit surface stays minimal; I-LLMTOG-11
    config_frozen audit holds without a new field.

Rejected alternative: codex_cli_timeout_seconds: float field with
its own --llm-codex-cli-timeout flag.
Rationale for rejection: stated above (no demonstrated need,
widens parser, duplicates state).
```

---

## 6. LOCKED: backend class (Option K-A)

**Decision: Option K-A — a dedicated `CodexCLIClient` dataclass
in `brain/llm/client.py`, mirroring `ClaudeCLIClient`.**

```python
@dataclass(frozen=True, slots=True)
class CodexCLIClient:
    """LLMClient backed by the codex CLI executable."""

    command: tuple[str, ...] = ("codex", "exec")     # LOCKED (see Section 7)
    timeout_seconds: float = 60.0                    # LOCKED
    cwd: str = "/tmp"                                # LOCKED

    def __post_init__(self) -> None:
        # shutil.which(self.command[0]); raise
        # RuntimeError("codex-cli executable '<x>' not on PATH")
        # if missing.
        ...

    def eval_consistency(self, prompt: str) -> str:
        # subprocess.run(self.command, input=prompt,
        #                capture_output=True, text=True,
        #                timeout=self.timeout_seconds,
        #                cwd=self.cwd)
        # Non-zero -> RuntimeError("codex-cli returned <n>:
        # <stderr-bounded>").
        # TimeoutExpired -> RuntimeError("codex-cli timed out
        # after <s>s").
        ...
```

```text
Class name:        CodexCLIClient
File:              brain/llm/client.py (appended after
                   ClaudeCLIClient)
Shape:             frozen=True, slots=True dataclass
Subprocess shape:  subprocess.run, synchronous, bounded by
                   timeout_seconds
Resource shape:    no long-lived Popen / file handle / thread /
                   asyncio / signal hook

Rejected alternative K-B: shared abstract SubprocessLLMClient
that both ClaudeCLIClient and CodexCLIClient delegate to.
Rationale for rejection: would refactor the existing
ClaudeCLIClient (audited by Phase 3.8B) and reopen the
I-LLMTOG-13 static audit surface. The two-class duplication is
~30 lines per class; the refactor saves duplication at the cost
of reopening a passed audit. The corrigenda prefers minimal
diff.

Rejected alternative K-C: defer the backend class.
See Section 2.
```

---

## 7. LOCKED: command tuple

**Decision: `("codex", "exec")` (candidate C-3 from the kickoff).**

```text
Locked command tuple:   ("codex", "exec")
Locked cwd:             "/tmp"
Locked timeout_seconds: 60.0

Rationale:
  - "exec" is a documented codex subcommand for non-interactive
    prompt-response invocation in the OpenAI codex CLI. It
    avoids triggering an interactive REPL.
  - The tuple is minimal: no flags whose semantics could shift
    between codex binary versions.
  - The deterministic REQUIRED fixtures do NOT invoke the real
    binary; they only audit factory construction and bounded
    missing-exec error. The command tuple's correctness is
    exercised only by the OBSERVED smoke.
  - If the operator's installed codex binary uses a different
    invocation, the operator overrides via
    --llm-codex-cli-executable <path-to-wrapper-script> where
    the wrapper translates "exec <prompt>" into the binary's
    actual invocation. The runtime layer remains stable.

Rejected alternative C-1: ("codex", "exec", "--full-auto").
Rationale for rejection: --full-auto is a version-specific flag
that may not exist in all codex CLI builds; locking it would
make the OBSERVED smoke fragile across binary versions. The
operator can supply this flag via a wrapper if needed; the
runtime layer does not bake it in.

Rejected alternative C-2: ("codex",).
Rationale for rejection: invokes the codex CLI in default mode,
which is typically interactive. The OBSERVED smoke would block
on terminal input.

Rejected alternative C-4: ("codex", "-p").
Rationale for rejection: -p is the claude-cli prompt flag; no
evidence it exists in the codex CLI. Adopting it speculatively
would create a fixture-vs-reality mismatch.

Future-revision note:
The corrigenda accepts that ("codex", "exec") may be revised in
a follow-up campaign if real-binary smoke under I-LLMTOG-18
reveals a different invocation contract. Revision requires a
new corrigenda artifact, not a silent code edit. The
deterministic REQUIRED rows (I-LLMTOG-16, I-LLMTOG-17) remain
stable across any such revision because they do not depend on
the command tuple's contents beyond the first element being a
PATH-resolvable executable name.
```

---

## 8. LOCKED: CLI flag

```text
Locked flag:        --llm-codex-cli-executable PATH
Default value:      "codex"
Help text:          "Path or name of the codex executable to
                    invoke when --llm-mode is codex-cli. Default:
                    codex. Resolved via shutil.which at session-
                    launch time. Missing executable fails closed
                    before launch."
Placement:          after --llm-claude-cli-executable in
                    brain/ui/__main__.py argparse
Parser binding:     parse_llm_runtime_args reads the parsed
                    value into LlmRuntimeConfig.codex_cli_executable

--llm-mode help text update:
  current: "...offline (default), mock, anthropic-api, or
           claude-cli..."
  locked:  "...offline (default), mock, anthropic-api,
           claude-cli, or codex-cli..."

BRAIN_LLM_MODE=codex-cli   accepted (existing env var, new value)
BRAIN_LLM_CODEX_CLI_EXECUTABLE   NOT added (rejected)

Rejected alternative: add a BRAIN_LLM_CODEX_CLI_EXECUTABLE env
var.
Rationale for rejection: the synthesis Section 4 notes Phase
3.8B's "explicit opt-in" pattern; the env var would widen the
auto-pickup surface without operator benefit. The CLI flag
suffices.
```

---

## 9. LOCKED: factory branch

Added to `build_llm_client_from_config`:

```python
if config.mode is LlmRuntimeMode.CODEX_CLI:
    return _build_codex_cli_client(config)
```

Helper `_build_codex_cli_client(config)` shape:

```text
1. resolved_exe = _which(config.codex_cli_executable)
2. if resolved_exe is None:
       raise LlmRuntimeError(
           f"codex-cli executable {config.codex_cli_executable!r} "
           f"not on PATH"
       )
3. client = CodexCLIClient(
       command=(resolved_exe, "exec"),
       timeout_seconds=config.timeout_seconds,
       cwd="/tmp",
   )
4. if config.enable_cache:
       client = CachedClient(inner=client, cache_dir=..., tracer=...)
5. return client
```

```text
Env-read discipline:   build_llm_client_from_config does NOT
                       read os.environ in the new branch; all
                       env reads happen in parse_llm_runtime_args.
                       This preserves the I-LLMTOG-04 explicit-
                       opt-in audit.

Cache discipline:      enable_cache=True wraps CodexCLIClient in
                       CachedClient (same as claude-cli).
                       I-LLMTOG-08 audit extends to codex-cli.

No second classification path; no new tick seam; no new
autosave trigger; no new persistence column.
```

---

## 10. LOCKED: fixture strategy

```text
Dedicated new fixtures (codex-cli-specific REQUIRED rows):

  brain/ui/fixtures/llm_runtime_codex_cli_requires_executable.py
    Audits I-LLMTOG-16 (REQUIRED, NEW).
    Asserts: missing executable raises LlmRuntimeError with
    bounded message naming both the executable path and the
    mode "codex-cli". Uses an obviously-nonexistent path like
    "/nonexistent/codex-binary-<hash>" to guarantee
    determinism in any CI environment.

  brain/ui/fixtures/llm_runtime_codex_cli_factory.py
    Audits I-LLMTOG-17 (REQUIRED, NEW).
    Asserts: build_llm_client_from_config(
        LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI,
                          codex_cli_executable=sys.executable))
    returns a CodexCLIClient instance whose command tuple
    starts with sys.executable. No subprocess invocation.

Extended in-place (cross-mode):
  llm_runtime_mode_closed.py             (LLMTOG-02 + LLMTOG-12)
    accepted-value tuple grows to include "codex-cli";
    member-count assertion updates from 4 to 5.

  llm_runtime_factory_per_mode.py        (LLMTOG-03)
    dispatch dict extends CODEX_CLI -> CodexCLIClient (using
    sys.executable to guarantee construction).

  llm_runtime_explicit_opt_in.py         (LLMTOG-04)
    asserts env vars alone do NOT flip mode to codex-cli;
    requires --llm-mode codex-cli or BRAIN_LLM_MODE=codex-cli.

  llm_runtime_cache_gated.py             (LLMTOG-08)
    CODEX_CLI + enable_cache wraps CodexCLIClient in
    CachedClient; CODEX_CLI without cache returns bare
    CodexCLIClient.

  llm_runtime_tick_seam.py               (LLMTOG-09)
    extends the per-mode iteration to confirm CODEX_CLI
    client also enters tick() via the existing seam.

  llm_runtime_print_once_independent.py  (LLMTOG-10)
    --print-once with --llm-mode codex-cli and an invalid
    codex_cli_executable still exits 0 (factory never called).

  llm_runtime_config_frozen.py           (LLMTOG-11)
    codex_cli_executable: str field is bounded; frozen+slots
    audit still holds.

  llm_runtime_static_audit.py            (LLMTOG-13)
    AST import-set audit covers
    brain/ui/llm_runtime.py and brain/llm/client.py with the
    new class present. Forbidden imports (curses, brain.tlica,
    brain.tick) remain rejected.

NO file changes for:
  llm_runtime_default_offline.py         (LLMTOG-01;
                                          default is OFFLINE,
                                          codex-cli is irrelevant)
  llm_runtime_anthropic_requires_key.py  (LLMTOG-05; anthropic-
                                          specific)
  llm_runtime_claude_cli_requires_executable.py (LLMTOG-06;
                                          claude-cli-specific)
  llm_runtime_mock_requires_responses.py (LLMTOG-07; mock-
                                          specific)

OBSERVED row (no fixture file):
  I-LLMTOG-18 (OBSERVED, NEW)
    Real codex-cli smoke walk: documented in INVARIANT_CATALOG.md
    as "Optional real model-backed smoke walk for codex-cli:
    requires a real `codex` binary on PATH and operator-supplied
    auth. Run `python3 -m brain.ui --llm-mode codex-cli
    --llm-codex-cli-executable <path> --print-once` to observe
    the factory wiring; run a full session with one /step to
    observe a single eval_consistency call. Cannot fail the
    runner."

Standard fixtures do NOT require real codex access. This is the
locked contract for the corrigenda.

Rejected alternative: copy the entire claude-cli fixture set as
codex-cli mirrors.
Rationale for rejection: cross-mode audits (LLMTOG-02 through
LLMTOG-13 minus the per-mode requires-X rows) operate on the
entire enum; mirroring them per-mode duplicates state and
inflates the catalog without new coverage.
```

---

## 11. LOCKED: OBSERVED real-codex smoke definition

```text
Row:      I-LLMTOG-18 (OBSERVED, NEW)
Subject:  Real codex-cli smoke walk
Gating:   OBSERVED-only; cannot fail the runner; no fixture file
Fixture:  none (documentation row in INVARIANT_CATALOG.md)
Trigger:  operator-driven, out-of-band
Lean cite: shares the I-LLMTOG-14 citation pattern (the existing
           OBSERVED row for real model-backed smoke); precise
           citation locked in Step 6 catalog patch plan

Smoke procedure (documented in catalog row body):
  1. Operator confirms a real codex binary is on PATH.
  2. Operator confirms codex auth is configured for the binary.
  3. Operator runs:
       python3 -m brain.ui --llm-mode codex-cli \
         --llm-codex-cli-executable <path> --print-once
     Expected: exits 0 with the startup banner; no real
     subprocess invocation (--print-once short-circuits before
     factory call).
  4. Operator runs:
       python3 -m brain.ui --llm-mode codex-cli \
         --llm-codex-cli-executable <path>
     and issues /stream <text>, /stream-promote, /step in
     sequence with at least one accepted candidate.
     Expected: a single subprocess.run invocation against the
     codex binary; bounded stderr surface; non-blocking
     timeout; status_message shows the bounded outcome of the
     LLMClient call.
  5. Operator records the observation in the Step 17 LLM
     runtime behavior report (PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md).
```

---

## 12. LOCKED: row family name and structure

**Row family: extend the existing `I-LLMTOG-*` family. No new
`I-CODEXCLI-*` family.**

```text
NEW rows (under I-LLMTOG-*):
  I-LLMTOG-16   REQUIRED   codex-cli without executable raises
                            LlmRuntimeError before launch
                            Fixture: llm_runtime_codex_cli_requires_executable.py
                            Lean citation: same as I-LLMTOG-06

  I-LLMTOG-17   REQUIRED   CODEX_CLI factory returns CodexCLIClient
                            (construction only, no invocation)
                            Fixture: llm_runtime_codex_cli_factory.py
                            Lean citation: same as I-LLMTOG-03

  I-LLMTOG-18   OBSERVED   Real codex-cli smoke walk
                            Fixture: none (documentation only)
                            Lean citation: same as I-LLMTOG-14

UPDATED rows (existing):
  I-LLMTOG-12   STRUCTURAL: enum member count assertion
                            updates from EXACT 4 to EXACT 5
                            Fixture: llm_runtime_mode_closed.py (extended)
                            No catalog row text change is
                            required if the row text reads
                            "exact closed member set"; the row
                            body MAY add the new member name
                            for clarity (Step 6 plan decides).

NO new rows for:
  - STRUCTURAL: cross-mode extensions cover codex-cli
                without new rows.
  - NOT-EXERCISED: I-LLMTOG-15 (no save/export path) is shared.
  - DEFERRED: no deferred codex-specific row.

Rejected alternative: new I-CODEXCLI-* family with 10+ rows
mirroring I-LLMTOG-*.
Rationale for rejection: duplicates cross-mode rows that
already audit the closed enum and the factory dispatch.
```

---

## 13. LOCKED: catalog count deltas

From v0.19 to v0.20:

```text
REQUIRED:        +2     212 -> 214
STRUCTURAL:      +0      83 ->  83
NOT-EXERCISED:   +0       9 ->   9
DEFERRED:        +0      12 ->  12
OBSERVED:        +1      15 ->  16

Total rows:      +3     331 -> 334

Total fixtures: +2     130 -> 132
                 (llm_runtime_codex_cli_requires_executable.py,
                  llm_runtime_codex_cli_factory.py)
```

Step 6 catalog patch plan binds these as the v0.20 target.
Step 8 patch executes them.

---

## 14. LOCKED: file budget

**Step 8 (catalog patch under F-A):**

```text
INVARIANT_CATALOG.md           add I-LLMTOG-16/17/18 rows;
                               update I-LLMTOG-12 body if
                               needed; update v0.20 banner
tools/catalog.py               EXPECTED_COUNTS banner + dict
                               update; +2 REQUIRED / +1 OBSERVED
brain/_catalog_ids.py          add I-LLMTOG-16/17/18 entries
brain/invariants.py            no FIXTURE_MODULES change yet
                               (fixtures land in Step 9)
                               OR add to FIXTURE_MODULES with
                               pending marker if the plan
                               prefers a staged drain
README.md                      v0.20 changelog entry
CURRENT_MISSION.md             v0.20 baseline counts
CURRENT_CAMPAIGN.md            v0.20 baseline counts
```

**Step 9 (runtime implementation under K-A):**

```text
brain/ui/llm_runtime.py        add CODEX_CLI enum member;
                               add codex_cli_executable field;
                               add _build_codex_cli_client
                               helper; extend factory dispatch;
                               extend _ACCEPTED_MODE_VALUES;
                               extend parse_llm_runtime_args
                               (env value + CLI flag)
brain/llm/client.py            add CodexCLIClient dataclass
brain/ui/__main__.py           add --llm-codex-cli-executable
                               argparse argument; update
                               --llm-mode help text;
                               no factory invocation change
                               (the shared factory path
                               handles the new mode)
brain/ui/fixtures/
  llm_runtime_codex_cli_requires_executable.py   NEW
  llm_runtime_codex_cli_factory.py                NEW
  llm_runtime_mode_closed.py                      EXTEND
  llm_runtime_factory_per_mode.py                 EXTEND
  llm_runtime_explicit_opt_in.py                  EXTEND
  llm_runtime_cache_gated.py                      EXTEND
  llm_runtime_tick_seam.py                        EXTEND
  llm_runtime_print_once_independent.py           EXTEND
  llm_runtime_config_frozen.py                    EXTEND
  llm_runtime_static_audit.py                     EXTEND
brain/invariants.py            FIXTURE_MODULES extension
                               (drain pending rows);
                               +2 new modules
README.md                      docs section for --llm-mode
                               codex-cli
```

**Excluded** (unchanged across Steps 8/9):

```text
brain/tlica/
lean_reference/
brain/tick.py
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
brain/ui/session.py
brain/development/
traces/
scenarios/
brain/llm/client.py existing classes (AnthropicAPIClient,
                                     ClaudeCLIClient, etc.)
                  remain UNCHANGED; only an addition is made.
```

---

## 15. LOCKED: audit consequences

```text
- I-LLMTOG-01 (REQUIRED, default offline)         unaffected
- I-LLMTOG-02 (REQUIRED, closed enum)             extended (5 values)
- I-LLMTOG-03 (REQUIRED, factory per mode)        extended (5 modes)
- I-LLMTOG-04 (REQUIRED, explicit opt-in)         extended (codex-cli)
- I-LLMTOG-05 (REQUIRED, anthropic needs key)     unaffected
- I-LLMTOG-06 (REQUIRED, claude-cli needs exec)   unaffected
- I-LLMTOG-07 (REQUIRED, mock needs responses)    unaffected
- I-LLMTOG-08 (REQUIRED, cache gated)             extended (codex-cli)
- I-LLMTOG-09 (REQUIRED, tick seam)               extended (codex-cli)
- I-LLMTOG-10 (REQUIRED, print-once independent)  extended (codex-cli)
- I-LLMTOG-11 (STRUCTURAL, config frozen)         extended (codex-cli field)
- I-LLMTOG-12 (STRUCTURAL, enum member count)     updated (4 -> 5)
- I-LLMTOG-13 (STRUCTURAL, static AST audit)      extended (new class)
- I-LLMTOG-14 (OBSERVED, real model smoke)        unaffected (claude-cli/anthropic)
- I-LLMTOG-15 (NOT-EXERCISED, no save/export)     unaffected (shared)
- I-LLMTOG-16 (REQUIRED, NEW)                     codex-cli requires-exec
- I-LLMTOG-17 (REQUIRED, NEW)                     codex-cli factory
- I-LLMTOG-18 (OBSERVED, NEW)                     real codex-cli smoke

No Phase 3.8B row is RETIRED. No Phase 3.8B row is RENAMED. No
Phase 3.8B fixture is REPLACED. All extensions are additive.
```

---

## 16. LOCKED: hard constraints (restated)

```text
offline remains default.
codex-cli is explicit opt-in (CLI flag or BRAIN_LLM_MODE env).
missing executable fails before launch with a bounded local
  LlmRuntimeError.
deterministic fixtures do not require real codex access.
real codex-cli smoke is OBSERVED-only (I-LLMTOG-18).
selected client enters through the existing
  tick(..., client, ...) seam.
no second classification path.
no hidden network/API path in standard fixtures.
no second save_session helper, no new persistence column.
no codex-specific autosave trigger.
no long-lived subprocess handle on OperatorSession.
no new LLMClient protocol method.
no new operator verb (codex-cli is selected via --llm-mode).
the factory does not consult os.environ.
no env-based auto-selection of codex-cli.
all existing I-LLMTOG-01..15 audits remain green; extensions
  are additive, not replacement.
```

---

## 17. Next artifact

```text
PHASE3_11_CODEX_CLI_RUNTIME_CATALOG_PATCH_PLAN.md   (Step 6)
```

The catalog patch plan binds:

```text
- the new row IDs (I-LLMTOG-16, I-LLMTOG-17, I-LLMTOG-18)
- the exact row body text for each
- the Lean citations for each REQUIRED and OBSERVED row
- the EXPECTED_COUNTS update in tools/catalog.py
- the brain/_catalog_ids.py entries
- the brain/invariants.py FIXTURE_MODULES status (pending vs
  drained) for the new fixtures
- the v0.20 banner text in INVARIANT_CATALOG.md, README.md,
  CURRENT_MISSION.md, CURRENT_CAMPAIGN.md
- the EXACT count assertions for the catalog gate
- the I-LLMTOG-12 row body update (4 -> 5 member assertion)
- the exact wording of the OBSERVED I-LLMTOG-18 row body
  (smoke procedure)
- the stop point: Step 7 review gate A
```

The Step 7 review gate A then stops the campaign. The Step 8
patch and the Step 9 implementation are blocked until the user
explicitly accepts the Step 6 plan.
