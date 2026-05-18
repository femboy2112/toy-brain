# PHASE3_17_CODEX_CLI_COMPAT_PATCH_PLAN.md

## Purpose

Step 2 of Phase 3.17: specify the smallest possible runtime patch to
make the `codex-cli` mode usable end-to-end through the public
`OperatorSession.dispatch` route, given the Phase 3.16 Step 5
finding that `codex-cli 0.130.0` refuses `cwd=/tmp` without
`--skip-git-repo-check`.

This document does **not** apply the patch. Step 3 applies it.

---

## 1. Current state (frozen at this commit)

### 1.1 `CodexCLIClient` default

`brain/llm/client.py`:

```python
@dataclass(frozen=True, slots=True)
class CodexCLIClient:
    command: tuple[str, ...] = ("codex", "exec")
    timeout_seconds: float = 60.0
    tracer: CognitionTracer = field(default_factory=NullTracer)
    cwd: str = "/tmp"
```

`cwd="/tmp"` is intentional: it prevents the nested CLI from
auto-discovering the parent repo's `CLAUDE.md` / hooks / config (see
the comment block immediately above the `cwd` field).

### 1.2 Factory wiring

`brain/ui/llm_runtime.py::_build_codex_cli_client`:

```python
return CodexCLIClient(
    command=(resolved_executable, "exec"),
    timeout_seconds=config.timeout_seconds,
)
```

`resolved_executable` is the absolute path returned by `_which`. The
tuple is built positionally; only the resolved executable substitutes
into position 0.

### 1.3 Observed failure (Phase 3.16, Step 4)

`docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_RUN.md`
Section 2 records:

```text
Reading additional input from stdin...
Not inside a trusted directory and --skip-git-repo-check was not
specified.
```

`subprocess.run` exits non-zero before any prompt is forwarded to
the model. The `CachedClient` miss was recorded but no JSON entry
was written (the inner client raised before the write step).

---

## 2. Preferred fix

Add the documented `--skip-git-repo-check` flag to the default
command tuple in `brain/llm/client.py`:

```python
command: tuple[str, ...] = ("codex", "exec", "--skip-git-repo-check")
```

and to the factory in `brain/ui/llm_runtime.py`:

```python
return CodexCLIClient(
    command=(resolved_executable, "exec", "--skip-git-repo-check"),
    timeout_seconds=config.timeout_seconds,
)
```

That's the entire runtime patch. No other source under `brain/**`,
`tools/**`, or `.claude/**` is touched.

`cwd` stays `"/tmp"`. The constraint that the nested CLI must not
auto-discover this repo's `CLAUDE.md` / hooks / config is the
**reason** we keep `cwd="/tmp"`; if we let `cwd` resolve to the
repo root we re-open that discovery surface, which was previously
rejected.

### 2.1 Rationale

`--skip-git-repo-check` is documented and stable on
`codex-cli >= 0.x` (the `codex exec --help` output in Phase 3.16
Step 3 enumerates it). It does not change prompt handling, tool
invocation, sandboxing, or workspace policy. It is strictly an
"opt out of trusted-directory enforcement" flag.

This is strictly smaller than the rejected alternative of changing
`cwd` to the repo root, which would:

- let the nested CLI auto-load `./CLAUDE.md` / `./AGENTS.md`;
- inherit any local Codex config;
- collide with the explicit Phase 3.11 corrigenda Section 7 lock on
  "neutral cwd to keep the nested CLI from discovering this repo's
  configuration."

### 2.2 Rejected alternatives

```text
R1. cwd = repo_root
    REJECTED: violates the documented Phase 3.11 corrigenda
    Section 7 lock; widens the nested CLI's discovery surface.

R2. command = ("codex", "exec", "--cd", "/tmp",
                "--skip-git-repo-check")
    REJECTED: --cd is already specified implicitly by the
    subprocess.run cwd argument; adding it twice is redundant and
    risks divergence if codex-cli's --cd flag semantics change.

R3. command = ("codex", "--skip-git-repo-check", "exec")
    REJECTED: the codex-cli help text places subcommand flags AFTER
    "exec"; placing the flag before the subcommand is not
    documented and risks a future codex-cli version rejecting the
    ordering.

R4. silent fallback to claude-cli when codex-cli fails
    REJECTED: hides a runtime issue and breaks explicit
    opt-in (I-LLMTOG-04).

R5. import codex's Python SDK and bypass the subprocess seam
    REJECTED: would add a third-party runtime dependency (currently
    we only use stdlib for transport); also breaks the SubprocessClient
    pattern locked by Phase 2 v1 / Phase 3.11.
```

---

## 3. Exact files to edit

```text
Step 3 runtime files:

  brain/llm/client.py
    - CodexCLIClient.command default value (~line 369)

  brain/ui/llm_runtime.py
    - _build_codex_cli_client(...) tuple build (~lines 587-606)

Step 3 fixture files:

  brain/ui/fixtures/llm_runtime_codex_cli_factory.py
    - extend the existing I-LLMTOG-17 check to assert that
      "--skip-git-repo-check" appears in client.command and that
      command remains a bounded tuple[str, ...]

Step 3 catalog files:

  INVARIANT_CATALOG.md
    - NO change required to ship the fix. The textual row bodies
      for I-LLMTOG-16 / I-LLMTOG-17 / I-LLMTOG-18 describe the
      command tuple as `("codex", "exec")`; the new tuple is
      strictly an EXTENSION of that prefix. Recommended: leave
      INVARIANT_CATALOG.md untouched in Phase 3.17 to keep the
      catalog version banner at v0.25 and the count line
      281 / 88 / 14 / 15 / 16. Any body-text refresh is recorded
      as a deferred follow-up.

  tools/catalog.py
    - NO change.
```

---

## 4. Expected catalog impact

```text
REQUIRED        281 -> 281 (no change)
STRUCTURAL       88 ->  88 (no change)
NOT-EXERCISED    14 ->  14 (no change)
DEFERRED         15 ->  15 (no change)
OBSERVED         16 ->  16 (no change)

catalog version v0.25 -> v0.25 (no change)
```

No new row family; no row promotion / demotion; no fixture file
add (the new assertion goes into the existing
`llm_runtime_codex_cli_factory.py`); no `tools/catalog.py` banner
update.

If during Step 3 implementation a new fixture file proves necessary
(e.g., because extending the existing fixture exceeds a row-binding
boundary), Phase 3.17 stops and asks the operator before adding the
file — a fixture add is a structurally larger change than the
campaign authorizes here.

---

## 5. Fixture refresh (specific assertions to add)

The existing fixture at `brain/ui/fixtures/llm_runtime_codex_cli_factory.py`
already covers:

```text
- I-LLMTOG-17: build_llm_client_from_config returns CodexCLIClient
- client.command[0] == sys.executable (resolved exe)
- client.command[1] == "exec"
```

Step 3 extends this fixture with the following additional
assertions inside the same `check_I_LLMTOG_17_codex_cli_factory`
function (no new register call, no new row binding):

```python
# Phase 3.17: --skip-git-repo-check must be present so codex-cli
# >= 0.130 does not refuse cwd=/tmp before sending the prompt.
assert "--skip-git-repo-check" in client.command, (
    "I-LLMTOG-17 violated (Phase 3.17 extension): "
    "CodexCLIClient.command lacks --skip-git-repo-check "
    f"(got {client.command!r})"
)
# Tuple shape audit: bounded tuple of plain strings; no shell=True
# hooks; no callable smuggled in.
assert isinstance(client.command, tuple), (
    "I-LLMTOG-17 violated: CodexCLIClient.command is not a tuple "
    f"(got {type(client.command).__name__})"
)
assert all(isinstance(part, str) for part in client.command), (
    "I-LLMTOG-17 violated: CodexCLIClient.command contains a non-str "
    f"entry (got {client.command!r})"
)
# Locked positional ordering: <exe>, "exec", "--skip-git-repo-check"
# in positions 0, 1, 2.
assert client.command[2] == "--skip-git-repo-check", (
    "I-LLMTOG-17 violated: CodexCLIClient.command[2] is not "
    f"--skip-git-repo-check (got {client.command[2]!r})"
)
# Neutral cwd preserved (Phase 3.11 corrigenda Section 7).
assert client.cwd == "/tmp", (
    "I-LLMTOG-17 violated: CodexCLIClient.cwd drifted from /tmp "
    f"(got {client.cwd!r})"
)
```

If the existing fixture file already imports anything beyond what
the new assertions need, the imports stay; no new module is added.

---

## 6. Forbidden touches in Step 3

```text
brain/tick.py
brain/llm/parse.py
brain/llm/prompts.py
brain/llm/ptcns_backed.py
brain/development/growth_ledger.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/ui/session.py
brain/ui/__main__.py beyond what is required for the patch (NOT
  required for the documented patch)
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
INVARIANT_CATALOG.md (per Section 4 above)
tools/catalog.py
scenarios/**
traces/**
lean_reference/**
```

If during Step 3 a touch to any of the above seems necessary, Step 3
stops and escalates.

---

## 7. Validation and smoke plan

### 7.1 Step 3 validation (no real model call)

After applying the patch, run the canonical preflight:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

All five gates must remain PASS:

```text
catalog_counts
citations_verify
import_audit
invariants_run
check_all
```

Then run the unit-fixture-equivalent invariant on its own:

```bash
python3 -m brain.invariants run
```

Expect: REQUIRED green 282, OBSERVED 7/0 (unchanged).

### 7.2 Step 4 smoke (real codex model call, budget ≤ 10)

`docs/campaigns/phase3_17/PHASE3_17_CODEX_CLI_REAL_MODEL_SMOKE.md`
runs the actual codex-cli model loop. Step 4 walks this route:

```text
1. Probe codex availability without invoking the model:
     codex --version
     codex exec --help
2. Probe codex auth status (presence only):
     codex login status
3. Construct LlmRuntimeConfig(mode=CODEX_CLI, ...) and call
   build_llm_client_from_config. The returned client must be
   CachedClient(CodexCLIClient) (Phase 3.14 default-on for
   model-backed modes).
4. Queue one short PerceptEvent through OperatorSession.dispatch
   (QUEUE_PERCEPT) and run STEP_TICK with the cached codex client.
5. If budget allows, repeat with a different content_id but
   identical text to exercise the Phase 3.14 L2 cache path
   (canonicalization should hit).
6. Record (no secrets, no raw prompts, no raw responses):
     codex --version output
     codex login status (boolean + class only)
     CachedClient.miss_count / hit_count / skip_count
     L1 *.json file count under brain/.llm_cache (count only)
     L2 *.json file count under brain/.llm_cache/eval_v1/
     parsed ConsistencyEval
     latest_tick.tick_index / triggered_mode
     profile.domain / msi.contents deltas
     real model calls used in this step
     cumulative campaign calls used / 20
```

Step 4 stops immediately on:

```text
- 10 calls reached in Step 4 alone
- 3 consecutive parse failures
- non-zero exit unrelated to the trusted-dir check (escalates to Step 9)
- any indication a runtime code change beyond Step 3 is needed
```

### 7.3 Real model call accounting policy for Step 4

Every codex invocation that consumes a real model call counts toward
the campaign budget, including:

```text
- successful single tick
- parse failure followed by retry
- timeout
- subprocess nonzero exit
- network transient
```

If the call count cannot be proven (e.g., a wrapper inflates the
counter incorrectly), the larger figure is recorded.

---

## 8. Raw-prompt / response / secret discipline

```text
- no raw prompt body is committed; only its char count and SHA-256
  prefix may appear in Step 4's report
- no raw model response is committed; only its char count, parsed
  enum, and a short hash prefix may appear
- no value of ANTHROPIC_API_KEY / BRAIN_ANTHROPIC_API_KEY / any
  codex auth token may appear anywhere in the campaign artifacts
- brain/.llm_cache/ remains gitignored; cache file CONTENTS are
  never quoted in any doc, only counts and gitignored-status
- no .env, .secrets, ~/.config/codex/*, or similar file is read or
  printed
```

---

## 9. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the patch is a documented one-line flag addition; the
  rationale, alternatives, and validation plan are derivable
  directly from Phase 3.16 Step 5 findings and the existing
  fixture surface.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer of this plan; the plan
  is doc-only and well-bounded.

Stage C.1 flow orchestration:
- used: no
- reason: a single, self-contained patch plan; Stage C.1 overhead
  exceeds the cost of writing directly.
```

---

## 10. Real model call accounting (this step)

```text
mode tested:    n/a (this step is documentation only)
calls used in this step:  0
cumulative campaign calls: 0 / 20
```

---

## 11. Next artifact

Step 3:
`brain/llm/client.py`, `brain/ui/llm_runtime.py`, and
`brain/ui/fixtures/llm_runtime_codex_cli_factory.py` — apply the
patch and the fixture refresh, run the gates, commit.
