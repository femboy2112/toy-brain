Spawn the `chatgpt-codex-writer` agent to run a bounded limited-write Codex worker.

Stage B is explicit, sequential, and allowlist-based.

Usage shape:

```text
/ask-chatgpt-write --model gpt-5.5 --effort high --allowed-file <path> [--allowed-file <path> ...] --apply <prompt>
```

Rules:

- Use only the wrapper:

```bash
python3 tools/claude_helpers/codex_chatgpt_write_worker.py ...
```

- Do not invoke raw `codex` or `codex exec`.
- Do not run parallel Codex calls.
- Do not retry automatically.
- Respect the wrapper's minimum interval between real Codex calls.
- Require exact `--allowed-file` entries.
- Require `--apply` for real repo mutation.
- The wrapper runs Codex inside a temp git worktree and copies back only allowed files.
- If out-of-scope changes are detected, stop and report.
- Parent Claude validates and commits; Codex never stages or commits.

Recommended defaults:

```text
model: gpt-5.5
effort: high
timeout: 1200 seconds
min interval: 180 seconds
```
