Spawn the `chatgpt-codex-orchestrator` agent to run a Claude-supervised Codex orchestration wave.

Stage C is explicit, bounded, and wave-based.

Usage shape:

```text
/orchestrate-with-codex --model gpt-5.5 --effort high --max-parallel 2 <task>
```

Rules:

- Claude creates a manifest with one wave and one or two shards.
- The wrapper may run at most two Codex calls concurrently.
- Parallel shards require disjoint write sets and no declared read/write collision.
- Invoke only:

```bash
python3 tools/claude_helpers/codex_chatgpt_orchestrator.py ...
```

- Do not invoke raw `codex` or `codex exec`.
- Do not retry automatically.
- Respect wrapper pacing between waves.
- Parent Claude validates and commits; Codex never stages or commits.

Recommended defaults:

```text
model: gpt-5.5
effort: high
timeout: 1200 seconds
max_parallel: 2
max_real_calls per wave: 2
min wave interval: 180 seconds
```
