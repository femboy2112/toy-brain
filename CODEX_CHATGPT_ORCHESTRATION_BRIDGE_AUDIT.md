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
apply policy: all shards pass, then serial copy-back of exact allowed files
no automatic retry
no recursive orchestration
Claude validates before commit
```

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

## Real Codex smoke

Not part of deterministic validation. Requires explicit operator approval.

Recommended smoke: two harmless files, two independent shards, gpt-5.5, high effort, timeout >= 1200s, max_parallel=2, max_real_calls=2.
