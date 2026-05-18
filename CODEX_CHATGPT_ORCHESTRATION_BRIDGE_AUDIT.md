# CODEX_CHATGPT_ORCHESTRATION_BRIDGE_AUDIT.md

## Verdict

PLANNED FOR STAGE C IMPLEMENTATION.

This artifact should be filled in by Claude Code after installing the Stage C orchestrator. The intended result is a Claude-owned orchestration mode where Codex can execute up to two independent bounded write shards in parallel through temporary worktrees.

## Intended scope

- Add `/orchestrate-with-codex` command.
- Add `chatgpt-codex-orchestrator` Claude agent.
- Add `tools/claude_helpers/codex_chatgpt_orchestrator.py`.
- Add fake-codex selftest.
- Add prompt template `orchestrate_worker.md`.
- Add narrow wrapper allowlist only.
- No raw Codex allowlist.
- No ToyI runtime changes.

## Required safety invariants

```text
max parallel Codex calls: 2
parallel unit: one orchestration wave
write collision policy: hard reject overlapping allowed_files
read/write collision policy: hard reject same-wave read_files vs other shard allowed_files
workspace-write scope: temp worktree only
apply policy: all shards pass, then all-or-nothing apply preflight, then serial copy-back of exact allowed files
no automatic retry
no recursive orchestration
Claude validates before commit
```

## All-or-nothing apply preflight

Before any live-repo write the wrapper calls `validate_all_copybacks(repo, shards, results)` which walks every changed path across every successful shard result and verifies:

- the path is in that shard's exact `allowed_files`
- the path re-passes `validate_path` (no parent traversal, no absolute path, no `.git`, no directory at the live destination, no symlink at the live destination)
- the temp-worktree source is not a symlink
- the temp-worktree source is not a directory
- a missing source (deletion) is explicitly listed in `shard.allow_delete`

If preflight fails, the wrapper exits with `EXIT_APPLY_PREFLIGHT_FAILED` (44), error class `APPLY_PREFLIGHT_FAILED`, records `apply_preflight_failed: true` in the audit record, and copies back zero files. Only when preflight passes does the manifest-order copy loop run.

## Validation to record after implementation

```text
python3 -m py_compile tools/claude_helpers/codex_chatgpt_orchestrator.py
python3 tools/claude_helpers/codex_chatgpt_orchestrator.py --help
python3 tools/claude_helpers/codex_chatgpt_orchestrator_selftest.py
python3 tools/claude_helpers/codex_chatgpt_write_worker_selftest.py
python3 tools/claude_helpers/codex_chatgpt_subagent_selftest.py
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

## Selftest coverage

`tools/claude_helpers/codex_chatgpt_orchestrator_selftest.py` exercises, with a fake-codex binary and no network:

- in-process write/write collision rejection
- in-process declared read/write collision rejection
- in-process `max_parallel` rejection
- in-process symlink allowed-path rejection
- `case_happy_path`: two independent shards, both apply, audit hashes the task without content, `apply_preflight_failed=false`
- `case_partial_apply_prevented`: two shards where shard B replaces its allowed file with a symlink in the temp worktree; preflight rejects the wave, the live repo is byte-identical to its pre-wave state (shard A's would-be write is not leaked), exit code is `EXIT_APPLY_PREFLIGHT_FAILED`, audit records `apply_preflight_failed=true` and `error_class=APPLY_PREFLIGHT_FAILED`

## Real Codex smoke

Not part of deterministic validation. Requires explicit operator approval.

Recommended smoke: two harmless files, two independent shards, gpt-5.5, high effort, timeout >= 1200s, max_parallel=2, max_real_calls=2.
