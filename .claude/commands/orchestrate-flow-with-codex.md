Spawn the `chatgpt-codex-flow-orchestrator` agent to run a Claude-supervised dynamic Codex flow.

Stage C.1 is explicit, bounded, DAG-based, and lazy-Claude by default.

Usage shape:

```text
/orchestrate-flow-with-codex --model gpt-5.5 --effort high --max-parallel 2 <task>
```

Rules:

- Claude creates a manifest with `nodes`, not a single static `waves` list.
- Nodes may be independent or chained with `depends_on`.
- The wrapper may run at most two Codex nodes concurrently.
- When a slot opens, a dependency-ready non-colliding node may launch, subject to pacing.
- Parallel active nodes require disjoint write sets and no active read/write collision.
- Same-file sequential work requires an explicit dependency path.
- Invoke only:

```bash
python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py ...
```

- Do not invoke raw `codex` or `codex exec`.
- Do not retry automatically.
- Network transient output is filtered by the wrapper and reported as retryable metadata.
- Parent Claude validates and commits; Codex never stages or commits.

Recommended defaults:

```text
model: gpt-5.5
effort: high
timeout: 1200 seconds
max_parallel: 2
max_total_calls: 3 without operator approval
max_total_calls: up to 8 only with explicit operator approval
min flow interval: 180 seconds
min start gap: 30 seconds
```
