# PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 17: LLM runtime behavior tests for
the Phase 3.11 comprehensive live behavior campaign.

Source: CURRENT_CAMPAIGN.md Step 17

Required artifact:

```text
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
```

This is a report-only step. It records deterministic runtime-mode
behavior and does not edit source code, fixtures, catalog rows, mission
files, or campaign files.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 17
Prior step evidence: a6d7f53 phase3.11 step16: db observability behavior report
Required Step 17 report before execution: absent
```

## Test Method

Temporary helper:

```text
/tmp/phase3_11_llm_step17/run_llm_observations.py
```

Helper policy:

```text
deterministic local Python helper
no real API calls
no real Claude CLI calls
no real Codex CLI calls
fake TTY StringIO only for fail-closed startup paths
real external CLI checks limited to shutil.which availability
```

The helper exercised:

```text
python3 -m brain.ui --llm-mode offline --print-once
python3 -m brain.ui --llm-mode mock --llm-mock-response PRESERVE --print-once
main(["--llm-mode", "anthropic-api"], fake TTY, empty credential env)
main(["--llm-mode", "claude-cli", "--llm-claude-cli-executable", missing_path], fake TTY)
main(["--llm-mode", "codex-cli", "--llm-codex-cli-executable", missing_path], fake TTY)
in-process parse_llm_runtime_args + build_llm_client_from_config cache checks
print-once mode independence for all accepted modes
```

Accepted mode enumeration observed:

```text
offline
mock
anthropic-api
claude-cli
codex-cli
```

## Observation Table

| ID | Type | Automation | Observation | Verdict |
| --- | --- | --- | --- | --- |
| 17.offline.1 | SST | yes | `python3 -m brain.ui --llm-mode offline --print-once` exited 0 and rendered the operator frame at `tick=0`, `queue=0`. | works |
| 17.mock.1 | SST | yes | `python3 -m brain.ui --llm-mode mock --llm-mock-response PRESERVE --print-once` exited 0 and rendered the same print-once frame without constructing a backend. | works |
| 17.anthropic-api.1 | SST | yes | Fake-TTY launch with `--llm-mode anthropic-api` and empty credential env exited 1 before curses with `brain.ui: llm runtime error: mode 'anthropic-api' requires --llm-anthropic-api-key, BRAIN_ANTHROPIC_API_KEY, or ANTHROPIC_API_KEY`. | works |
| 17.anthropic-api.2 | ORS | no | No API key was configured or accepted for a real API smoke in this deterministic step. | ORS skipped |
| 17.claude-cli.1 | SST | yes | Fake-TTY launch with `--llm-mode claude-cli --llm-claude-cli-executable /tmp/phase3_11_missing_claude` exited 1 before curses with a bounded missing-executable error naming `claude-cli` and the supplied path. | works |
| 17.claude-cli.2 | ORS | no | `claude` exists at `/home/leah/.local/bin/claude`, but real Claude CLI smoke was not run because Step 17 deterministic gates do not require live external model execution. | ORS skipped |
| 17.codex-cli.1 | SST | yes | Fake-TTY launch with `--llm-mode codex-cli --llm-codex-cli-executable /tmp/phase3_11_missing_codex` exited 1 before curses with a bounded missing-executable error naming `codex-cli` and the supplied path. | works |
| 17.codex-cli.2 | ORS | no | `codex` exists at `/usr/local/bin/codex`, but real Codex CLI smoke was not run because Step 17 deterministic gates do not require live external model execution. | ORS skipped |
| 17.cache.1 | SST | yes | In-process factory returned `CachedClient` for `anthropic-api` with a dummy explicit key and `--llm-enable-cache`; offline and mock modes rejected cache with bounded `LlmRuntimeError` messages. No API call was made. | works |
| 17.print-once-mode-independence.1 | SST | yes | `--print-once` exited 0 for offline, mock, anthropic-api without key, claude-cli with forced missing executable, and codex-cli with forced missing executable. This confirms print-once returns before backend construction. | works |
| 17.failure-anthropic-key.1 | SST | yes | Same evidence as `17.anthropic-api.1`: missing API key fails closed before curses and performs no network call. | works |
| 17.failure-claude-missing.1 | SST | yes | Same evidence as `17.claude-cli.1`: forced missing Claude executable fails closed before curses and performs no subprocess call. | works |
| 17.failure-codex-missing.1 | SST | yes | Same evidence as `17.codex-cli.1`: forced missing Codex executable fails closed before curses and performs no subprocess call. | works |
| 17.ux-llm-errors.1 | MOT | env | Missing key/executable messages are bounded and actionable. They name the selected mode and missing requirement directly. | works |

## Raw Evidence Summary

### Offline And Mock

```text
python3 -m brain.ui --llm-mode offline --print-once:
  exit=0
  first line: toy-brain operator . view=state . tick=0 . queue=0

python3 -m brain.ui --llm-mode mock --llm-mock-response PRESERVE --print-once:
  exit=0
  first line: toy-brain operator . view=state . tick=0 . queue=0
```

### Fail-Closed Model Modes

```text
anthropic-api without key:
  exit=1
  stderr=brain.ui: llm runtime error: mode 'anthropic-api' requires --llm-anthropic-api-key, BRAIN_ANTHROPIC_API_KEY, or ANTHROPIC_API_KEY

claude-cli with forced missing executable:
  exit=1
  stderr=brain.ui: llm runtime error: mode 'claude-cli' requires executable '/tmp/phase3_11_missing_claude' on PATH

codex-cli with forced missing executable:
  exit=1
  stderr=brain.ui: llm runtime error: mode 'codex-cli' requires executable '/tmp/phase3_11_missing_codex' on PATH
```

The fail-closed checks used fake TTY streams so they reached runtime
resolution before curses initialization. They did not call real external
LLM backends.

### Optional Real Smoke

```text
ANTHROPIC_API_KEY: not configured / not accepted for real smoke
claude executable: /home/leah/.local/bin/claude
codex executable:  /usr/local/bin/codex
```

Real CLI smoke was skipped for both `claude-cli` and `codex-cli`.
Availability is recorded, but no external model command was invoked.

### Cache

```text
anthropic-api + dummy key + --llm-enable-cache:
  client_type=CachedClient
  mode=anthropic-api
  enable_cache=True

offline + --llm-enable-cache:
  LlmRuntimeError: --llm-enable-cache is not supported for mode 'offline'

mock + --llm-enable-cache:
  LlmRuntimeError: --llm-enable-cache is not supported for mode 'mock'
```

The cache check constructed local client objects only. It did not send a
request.

### Print-Once Mode Independence

```text
--llm-mode offline --print-once                                      exit=0
--llm-mode mock --llm-mock-response PRESERVE --print-once            exit=0
--llm-mode anthropic-api --print-once                                exit=0
--llm-mode claude-cli --llm-claude-cli-executable missing --print-once exit=0
--llm-mode codex-cli --llm-codex-cli-executable missing --print-once  exit=0
```

## Findings

- Offline and mock print-once paths render deterministically.
- Model-backed modes fail closed with bounded local errors when required
  credentials or executables are unavailable.
- `codex-cli` is present in the accepted mode set and has the same
  missing-executable fail-closed behavior as `claude-cli`.
- `--print-once` is mode-independent and returns before backend
  construction for all accepted modes.
- Cache wrapping is accepted for model-backed `anthropic-api` config and
  rejected for deterministic offline/mock modes.
- Real Claude and Codex executables are available on this machine, but
  real external CLI smoke was intentionally skipped in this deterministic
  report-only step.

No Step 17 observation produced a gating failure. No behavior was
patched.

## Validation

Post-report validation:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

Scope guard after validation:

```text
git status --short                    only PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
git diff --name-only                  no tracked source/catalog/mission diff
temporary helper state                helper remains only under /tmp
```

## Next

The next campaign step after this report is Step 18:

```text
PHASE3_11_BEHAVIOR_FINDINGS.md
```
