# PHASE3_11_CODEX_CLI_RUNTIME_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.11 Codex CLI runtime option track before the
kickoff, the corrigenda, or any catalog/runtime change. This is a
planning artifact only. It does not edit `INVARIANT_CATALOG.md`,
`tools/catalog.py`, `brain/_catalog_ids.py`, `brain/invariants.py`,
`brain/ui/llm_runtime.py`, `brain/llm/client.py`, `brain/ui/__main__.py`,
or any guarded kernel path.

Phase 3.11 must add `codex-cli` as an explicit `--llm-mode` option.
The closest existing analog is `claude-cli`, which already proves
the design pattern (closed enum member, dataclass field for
executable, shared `timeout_seconds`, `LLMClient` protocol method,
factory branch with `_which`-based availability check,
`OBSERVED` real-smoke row, no second classification path).

```text
Status: DRAFT / REVIEW-GATED / IMPLEMENT-OR-DEFER
```

The track is review-gated at Step 7 (Review gate A). The Step 4
kickoff names design targets; the Step 5 corrigenda locks every
choice (including the `implement-now` vs `defer-as-follow-up`
decision); the Step 6 catalog patch plan binds the row family.
Implementation does NOT begin until Step 7 accepts the plan.

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

Latest LLM runtime row family: I-LLMTOG-01..15 (Phase 3.8B)
  REQUIRED:   I-LLMTOG-01..10        (10 rows)
  STRUCTURAL: I-LLMTOG-11..13        ( 3 rows)
  OBSERVED:   I-LLMTOG-14            ( 1 row)
  NOT-EXER:   I-LLMTOG-15            ( 1 row)

Preflight gates at HEAD of campaign branch:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  bash tools/check_all.sh                    All checks passed
```

---

## 2. Currently accepted `--llm-mode` values

`brain/ui/llm_runtime.py:56-62` defines the closed enum:

```python
class LlmRuntimeMode(str, Enum):
    """Finite closed enumeration of accepted LLM runtime modes."""

    OFFLINE = "offline"
    MOCK = "mock"
    ANTHROPIC_API = "anthropic-api"
    CLAUDE_CLI = "claude-cli"
```

`_ACCEPTED_MODE_VALUES` at `brain/ui/llm_runtime.py:128` is the
tuple of those values, used by `parse_llm_runtime_args` for
validation. The closed-enum property is audited by
`brain/ui/fixtures/llm_runtime_mode_closed.py` against rows
`I-LLMTOG-02` (REQUIRED) and `I-LLMTOG-12` (STRUCTURAL: exact
member set).

The factory `build_llm_client_from_config(config) -> object` at
`brain/ui/llm_runtime.py:390-463` dispatches per mode:

```text
OFFLINE        -> OfflineStandInClient (defined in brain/ui/__main__.py:143)
MOCK           -> MockClient(responses=...)
ANTHROPIC_API  -> AnthropicAPIClient(api_key=..., timeout_seconds=...)
CLAUDE_CLI     -> ClaudeCLIClient(command=(exe, ...), timeout_seconds=..., cwd=...)
```

All four backends conform to the `LLMClient` Protocol at
`brain/llm/client.py:34-46`:

```python
@runtime_checkable
class LLMClient(Protocol):
    """Minimal LLM transport seam."""

    def eval_consistency(self, prompt: str) -> str:
        ...
```

The selected client enters TLICA exactly once per dispatch via the
seam:

```text
brain/ui/__main__.py:506-524     build_llm_client_from_config(llm_config)
brain/ui/__main__.py:638         run_curses(..., client=client, ...)
brain/ui/session.py:455-460      OperatorSession.dispatch(self, command, *, client=None)
brain/ui/session.py:495          self._dispatch_step(client) within router
brain/ui/session.py:633          tick(prior_state, [event], client, tick_id=...)
brain/tick.py:94-100             def tick(state, events, client, tracer=None, tick_id=0)
```

The session **does not store** the client (audited via
`_ALLOWED_SESSION_ATTRS` at `brain/ui/session.py:188-206` and the
`I-UI-10` resource audit). This is load-bearing for Codex CLI:
adding the new mode must not put a long-lived subprocess handle
or executor on `OperatorSession`.

The argparse layer at `brain/ui/__main__.py:285-326` already
exposes the surrounding flags Codex CLI will need to mirror:

```text
--llm-mode {offline,mock,anthropic-api,claude-cli}
--llm-anthropic-api-key STR
--llm-claude-cli-executable PATH        (default: claude)
--llm-timeout SECONDS                   (shared timeout_seconds)
--llm-enable-cache                      (CachedClient wrapping)
--llm-mock-response STR                 (repeatable)
```

The mode is parsed through `parse_llm_runtime_args(argv, env)` at
`brain/ui/llm_runtime.py:157-326`, which never reads
`os.environ` outside that function. The closed-env-read property
is part of the Phase 3.8B audit and must not regress.

---

## 3. Proposed `codex-cli` mode

Proposed enum member (corrigenda locks the final spelling):

```text
LlmRuntimeMode.CODEX_CLI = "codex-cli"
```

The string value `"codex-cli"` matches the existing convention
(`anthropic-api`, `claude-cli` — lowercase, hyphen-separated). The
Python member name `CODEX_CLI` matches the existing `CLAUDE_CLI`
sibling.

Proposed dataclass fields on `LlmRuntimeConfig`:

```text
codex_cli_executable: str = "codex"     (default executable name)
```

Timeout is **reused**, not duplicated:

```text
timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS   (shared with claude-cli)
```

The shared `timeout_seconds` field is the locked Phase 3.8B
choice; the corrigenda must not introduce a parallel
`codex_cli_timeout_seconds` field unless a concrete need is
demonstrated. The synthesis's default position is reuse.

Proposed CLI flag (mirroring `--llm-claude-cli-executable`):

```text
--llm-codex-cli-executable PATH         (default: codex)
```

Proposed factory branch:

```text
CODEX_CLI  -> CodexCLIClient(command=(exe, ...), timeout_seconds=..., cwd=...)
```

The kickoff decides whether `CodexCLIClient` is:

```text
Option K-A: a new dedicated class in brain/llm/client.py with the
            same dataclass shape as ClaudeCLIClient (__post_init__
            calls shutil.which(exe); RuntimeError on missing).
Option K-B: a generic SubprocessLLMClient that both ClaudeCLIClient
            and CodexCLIClient delegate to (refactor of the
            existing claude-cli backend).
Option K-C: implement-as-follow-up; Phase 3.11 only catalogs the
            enum member and an OBSERVED row, deferring the
            backend class to a later campaign.
```

The corrigenda picks one of K-A / K-B / K-C. The default
recommendation is **K-A** because it is the smallest diff from
the proven claude-cli pattern and does not refactor an audited
module. K-B is tempting but risks reopening the Phase 3.8B audit
surface. K-C is acceptable only if the executable / argument
contract cannot be locked in the corrigenda.

---

## 4. Security and availability assumptions

`codex-cli` shares the security envelope of `claude-cli`:

```text
- The executable is an opaque local binary chosen by the operator;
  the runtime resolves it via shutil.which(...) at construction
  time, not at parse time.
- Missing executable fails closed BEFORE session launch with a
  bounded local error (LlmRuntimeError at factory, RuntimeError
  at backend __post_init__).
- The runtime makes no network call to "discover" the executable.
- The runtime does not read CODEX_API_KEY / OPENAI_API_KEY / any
  Codex-related env var at factory time. Auth is the executable's
  responsibility. If the executable's own auth fails, the
  subprocess returns non-zero and the LLMClient call surfaces a
  bounded RuntimeError. The runtime layer does not interpret the
  failure beyond "non-zero return code, surfaced as a bounded
  message".
- No long-lived subprocess handle is stored anywhere; each
  eval_consistency call is its own subprocess.run with the locked
  timeout_seconds. The session and the runtime config carry no
  subprocess state.
- The runtime layer makes no HTTP call. If a hypothetical Codex
  CLI variant requires a network round-trip, that responsibility
  lives inside the executable, not in our runtime.
- The cwd default is "/tmp" (matching claude-cli; corrigenda may
  pick a different default if the codex executable is sensitive
  to cwd).
- The selected client enters tick() via the existing client=
  argument; there is no second path.
```

The Phase 3.8B audit explicitly stated that the factory
`build_llm_client_from_config` does **not** consult `os.environ`.
The corrigenda must preserve this: codex-cli environment lookups
(if any) happen inside `parse_llm_runtime_args`, never inside
the factory.

---

## 5. Executable / auth failure behavior

Failure modes and bounded local errors:

```text
A. Missing --llm-codex-cli-executable (or default "codex" not on PATH):
     parse-time:    accepted (the value is a string; existence is
                    not checked at parse).
     factory-time:  build_llm_client_from_config raises
                    LlmRuntimeError("codex-cli executable '<x>' not
                    on PATH") BEFORE the session launches.
     UI-time:       __main__.py prints the bounded error and exits
                    non-zero; the curses surface never initializes.

B. Executable present but exits non-zero on eval_consistency:
     dispatch-time: subprocess.run returns CompletedProcess with
                    returncode != 0; CodexCLIClient.eval_consistency
                    raises RuntimeError("codex-cli returned <n>:
                    <stderr-bounded>"); the dispatch records the
                    failure in status_message via the existing
                    bounded-error pipeline.
     live state:    BrainState is not mutated; tick() never enters
                    the LLM-backed PtCns path if the client call
                    fails before the candidate evaluation.

C. Executable present but exceeds timeout_seconds:
     dispatch-time: subprocess.run raises TimeoutExpired;
                    CodexCLIClient.eval_consistency converts to
                    RuntimeError("codex-cli timed out after
                    <seconds>s"); status_message reflects the
                    bounded error.

D. Executable's own auth fails (e.g., login expired):
     same as B. The runtime does not distinguish "auth failed"
     from "any other non-zero exit". The operator inspects the
     bounded stderr fragment surfaced in status_message and
     re-authenticates the executable out of band.

E. Network unreachable inside the executable:
     same as B (non-zero exit). The runtime layer does NOT retry,
     fall back to a different backend, or surface partial output.

F. Operator omits --llm-mode codex-cli but sets a codex env var:
     factory-time: codex-cli is NOT auto-selected. Phase 3.8B's
     "explicit opt-in" rule (I-LLMTOG-04) extends to codex-cli;
     the corrigenda must rule out auto-selection via environment.
```

All of these are bounded local errors. None of them mutate
`BrainState`, none of them write to the session DB, none of them
trigger autosave (autosave fires only after a successful
mutating dispatch per `I-AUTOSAVE-*` family).

---

## 6. Manual smoke vs gating fixture distinction

Standard fixtures **must not** require real `codex` access. The
distinction mirrors `claude-cli`:

```text
REQUIRED gating fixtures (deterministic, run in CI without any
real codex binary):
  - codex-cli is in the closed enum (mode_closed audit)
  - factory returns the documented backend type (factory_per_mode
    audit; uses sys.executable as a guaranteed-present executable
    to construct the backend without invoking it)
  - missing executable raises a bounded LlmRuntimeError before
    launch (codex_cli_requires_executable audit; uses an obviously-
    nonexistent path like "/nonexistent/codex-binary-...")
  - selected client enters tick() via the existing client= arg
    (tick_seam audit covers all modes including the new one)
  - --print-once is independent of the selected client
    (print_once_independent audit extends to codex-cli)
  - cache wrapping is opt-in and mode-gated; codex-cli + cache
    returns a CachedClient wrapping CodexCLIClient
    (cache_gated audit extends)
  - explicit opt-in: env vars alone do not flip the mode to codex-cli
    (explicit_opt_in audit extends)
  - static AST audit rejects forbidden imports in the new module
    or in the extended brain/ui/llm_runtime.py (static_audit
    extends; new module may be added to the audited file set)

STRUCTURAL fixtures (closed-shape audits):
  - LlmRuntimeConfig still frozen/slots (config_frozen extends)
  - LlmRuntimeMode is (str, Enum) with the new exact member set
    of 5 (mode_closed STRUCTURAL row updates: 4 -> 5 members)

OBSERVED rows (real-smoke, OBSERVED-only, cannot fail the runner):
  - real codex-cli smoke walk: documents how an operator can run
    --llm-mode codex-cli with a real codex binary present and
    observe a single eval_consistency call. The OBSERVED row
    follows the I-LLMTOG-14 pattern: optional, out-of-band, no
    CI gating.

NOT-EXERCISED rows:
  - I-LLMTOG-15 ("no LLM runtime save/export path outside
    CachedClient cache") is shared across all modes and does NOT
    need a per-codex-cli mirror.
```

The corrigenda decides whether the existing fixtures get extended
in place or whether codex-cli gets dedicated fixture files. The
default recommendation is **dedicated fixture files** for the
codex-cli-specific REQUIRED rows (missing executable, factory
return type) and **in-place extension** for the cross-mode
audits (mode_closed, factory_per_mode, cache_gated,
explicit_opt_in, tick_seam, print_once_independent,
config_frozen, static_audit).

---

## 7. Why Codex CLI must not become default

`OFFLINE` is the locked default. The audit at
`PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md` and `I-LLMTOG-01`
(REQUIRED) pin "default config builds `OfflineStandInClient`",
with the factory never consulting `os.environ`. Codex CLI must
preserve this property because:

```text
1. The default must remain deterministic and reproducible
   without any external dependency. A user who clones the repo
   and runs `python3 -m brain.ui` must not be blocked on the
   presence or absence of a codex binary, network access, or
   credentials.

2. The catalog and the fixture suite must remain runnable in
   pure-Python CI without any external tool. Defaulting to
   codex-cli would either fail closed for every contributor or
   make CI dependent on a third-party binary.

3. The "explicit opt-in" property (I-LLMTOG-04) protects against
   accidental real-LLM use. A user who types `python3 -m brain.ui`
   without `--llm-mode` should not silently call a real LLM. This
   is a privacy / cost / surprise guarantee.

4. The autosave + persistence layers are designed against a
   deterministic LLM client. Tests that exercise persistence and
   autosave end-to-end use OFFLINE or MOCK. Changing the default
   would invalidate those tests' assumptions about determinism.

5. The architectural guardrails inherited from CURRENT_MISSION.md
   explicitly state "offline remains the default LLM mode" and
   "model-backed modes remain explicit opt-in" and "Codex CLI
   mode must be explicit opt-in".
```

The corrigenda must lock the default at `OFFLINE` and reaffirm
the explicit-opt-in invariant for codex-cli.

---

## 8. Why Codex CLI must not bypass the tick / client seam

The tick seam is the ONLY TLICA runtime transition route, and
the selected client is the ONLY way LLM-backed reasoning enters
the kernel. Codex CLI must conform:

```text
1. There is exactly one tick() function (brain/tick.py:94-100)
   and exactly one client argument. The audit at I-LLMTOG-09
   asserts the selected client enters tick() via the existing
   run_curses(..., client=...) -> session.dispatch(client=...)
   -> tick(client=...) path. Codex CLI MUST go through this
   path and not introduce a new route.

2. The session never stores the client (audited by
   _ALLOWED_SESSION_ATTRS and I-UI-10). A codex-specific cache,
   warmer, or pool would be tempting; it is forbidden. Each
   dispatch resolves the active client fresh from the
   constructed instance in __main__.py.

3. There is no second classification path. The classification
   pipeline lives inside tick() and uses LLMBackedPtCns
   (brain/tick.py:195-199) which calls
   client.eval_consistency(prompt). Codex CLI must implement
   exactly that interface; it must not introduce a parallel
   classifier entry point.

4. The LLMClient Protocol has exactly one method
   (eval_consistency). Codex CLI must NOT extend the protocol,
   add new methods, or expose alternate call sites. Methods
   like "streaming response", "tool-use round-trip",
   "multimodal input" are out of scope for Phase 3.11.

5. The autosave trigger set is closed (I-AUTOSAVE-*); codex-cli
   results must not create a new autosave trigger. A successful
   mutating dispatch that happened to use codex-cli triggers
   autosave the same way as one that used offline.

6. The persistence schema is closed (Phase 3.9); codex-cli
   results must not introduce a new column, table, or
   serialized field. The cached-response file format
   (CachedClient at brain/llm/client.py:165-218) is the only
   LLM-touching persistent surface and is shared across all
   model-backed modes.
```

The corrigenda must lock every one of these constraints into
the catalog row family.

---

## 9. Hard constraints (restated, locked at Step 5 corrigenda)

```text
offline remains default.
codex-cli is explicit opt-in (CLI flag or BRAIN_LLM_MODE env).
missing executable / auth fails before session launch with a
  bounded local error.
deterministic tests do not require real Codex access.
real Codex CLI smoke is OBSERVED/manual.
selected client enters through the existing tick(..., client, ...)
  seam.
no second classification path.
no hidden network/API path in standard fixtures.
no second save_session helper, no new persistence column.
no codex-specific autosave trigger.
no long-lived subprocess handle on OperatorSession.
no new LLM-protocol method.
no broadening of the closed parser verb set beyond the existing
  --llm-mode flag and a sibling --llm-codex-cli-executable flag.
no environment-based auto-selection (env vars alone do not flip
  mode to codex-cli).
the factory does not consult os.environ.
```

---

## 10. Implementation vs deferral criteria

The Step 5 corrigenda picks A (implement now) or B (defer as
follow-up) based on these criteria:

```text
Pick A (implement now) if ALL of the following hold:
  1. The exact codex executable invocation (binary name +
     argument tuple) can be locked in the corrigenda. The
     synthesis's default candidate is:
       command = (
         "codex",
         "exec",
         "--full-auto",   (or the locked equivalent)
       )
     The corrigenda either confirms this or names a different
     locked tuple.
  2. The codex CLI accepts a prompt via stdin or via a positional
     argument with a deterministic stdout response.
  3. The codex CLI's stderr surface is small and bounded; the
     RuntimeError text can be a single-line excerpt.
  4. The codex CLI's exit code is reliable enough to drive
     bounded RuntimeError on failure.
  5. The fixture pattern from claude-cli ports cleanly:
     - missing-executable test using an obviously-nonexistent
       path
     - factory-return-type test using sys.executable
     - mode_closed test asserting "codex-cli" is in the enum and
       member count is 5

Pick B (defer as follow-up) if ANY of the following hold:
  1. The invocation contract is uncertain enough that locking it
     in the corrigenda would create a fixture that does not
     match the real CLI.
  2. The codex CLI requires an interactive auth step that the
     test environment cannot exercise even as OBSERVED.
  3. The fixture pattern cannot port without modifying the
     Phase 3.8B audit surface (which would reopen a prior
     review).
  4. The work would exceed the campaign's file budget when
     combined with the live-test track (Steps 10-17).

Either outcome is acceptable. The campaign's name is "live
behavior test"; the Codex CLI work is a precondition for the
LLM runtime behavior report (Step 17). What is NOT acceptable is
shipping a half-implemented codex-cli mode or leaving the
catalog row family undefined.
```

The synthesis's default recommendation is **A (implement now)**
with the K-A backend class (a dedicated `CodexCLIClient`
dataclass mirroring `ClaudeCLIClient`), pending corrigenda
confirmation of the invocation contract.

---

## 11. Likely catalog row family

The Step 6 catalog patch plan is canonical. The synthesis's
estimate:

```text
Option F-A: extend the existing I-LLMTOG-* family
  - Add new REQUIRED rows for codex-cli-specific behavior:
      I-LLMTOG-16  codex-cli without executable raises
      I-LLMTOG-17  CODEX_CLI factory returns expected backend
  - Update STRUCTURAL row I-LLMTOG-12 to assert 5 members
    (not 4), and update its fixture's expected member tuple.
  - Update REQUIRED rows that already audit cross-mode behavior
    (I-LLMTOG-04, I-LLMTOG-08, I-LLMTOG-09, I-LLMTOG-10) to
    include codex-cli in the audited set; this is fixture-level,
    not a new row.
  - Add an OBSERVED row I-LLMTOG-18 for real codex-cli smoke.
  - I-LLMTOG-15 (no save/export) is shared; no new mirror.

Option F-B: open a new I-CODEXCLI-* family
  - Mirror the entire I-LLMTOG family for codex-cli specifically.
  - This is heavier and duplicates the cross-mode rows that are
    already audited generically.

Default recommendation: F-A (extend I-LLMTOG-*). It is the
smaller diff, preserves the Phase 3.8B audit surface, and uses
the existing fixture pattern.

Likely count delta under F-A:
  + 2 REQUIRED       (I-LLMTOG-16, I-LLMTOG-17)
  + 1 OBSERVED       (I-LLMTOG-18; real codex-cli smoke)
  + 0 STRUCTURAL     (I-LLMTOG-12 updates its assertion, no new row)
  + 0 NOT-EXERCISED  (I-LLMTOG-15 remains shared)
  + 0 DEFERRED

Estimated v0.20 baseline (Step 8 catalog patch):
  REQUIRED:    214   (212 + 2)
  STRUCTURAL:   83   (unchanged)
  NOT-EXERCISED: 9   (unchanged)
  DEFERRED:    12   (unchanged)
  OBSERVED:    16   (15 + 1)

These numbers are estimates; the Step 6 plan pins them.
```

---

## 12. Likely file budget

For Step 8 (catalog patch under option F-A):

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
README.md
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
```

For Step 9 (runtime implementation under option K-A + F-A):

```text
brain/ui/llm_runtime.py          add CODEX_CLI member, codex_cli_executable
                                 field, factory branch, _which check
brain/llm/client.py              add CodexCLIClient dataclass + __post_init__
                                 + eval_consistency
brain/ui/__main__.py             add --llm-codex-cli-executable arg;
                                 update --llm-mode help text
brain/ui/fixtures/
  llm_runtime_codex_cli_requires_executable.py
  llm_runtime_codex_cli_factory.py        (or extended in-place)
brain/invariants.py              FIXTURE_MODULES extension
README.md                        --llm-mode docs update
```

Excluded unless an accepted plan reopens them:

```text
brain/tlica/
lean_reference/
brain/tick.py
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
brain/ui/session.py        (no new session attr for codex-cli)
brain/development/
```

The Step 6 plan binds the actual paths. This section is a
planning estimate only.

---

## 13. Next artifact

```text
PHASE3_11_CODEX_CLI_RUNTIME_KICKOFF.md
```

The kickoff (Step 4) should define:

```text
- the locked-or-proposed enum member spelling (CODEX_CLI =
  "codex-cli");
- the locked-or-proposed dataclass field name
  (codex_cli_executable) and the default value ("codex");
- whether timeout_seconds is reused (default) or a parallel
  codex_cli_timeout_seconds is needed;
- the locked-or-proposed CLI flag (--llm-codex-cli-executable);
- the locked-or-proposed K-A / K-B / K-C choice and the
  rationale;
- a candidate executable invocation tuple (subject to corrigenda
  lock);
- the proposed fixture roster (REQUIRED + STRUCTURAL + OBSERVED);
- the disposition of cross-mode rows (extend in place vs new
  per-mode fixture);
- the stop point before the corrigenda (no implementation, no
  catalog edits).
```

After the kickoff, the corrigenda (Step 5) audits and locks the
design. The catalog patch plan (Step 6) binds the rows. The
campaign stops at the Step 7 review gate A. Implementation
(Step 9) does NOT begin until that gate is accepted.
