# CODEX_CHATGPT_DYNAMIC_FLOW_BRIDGE_AUDIT.md

## Verdict

Stage C.1 dynamic flow handoff is READY FOR CLAUDE CODE IMPLEMENTATION.

This package upgrades the merged Stage C static wave runner into a dynamic DAG scheduler while preserving the existing safety posture:

- Claude remains controller/verifier/integrator.
- Codex executes bounded nodes only through a Python wrapper.
- Max active Codex sessions is hard-capped at 2.
- More than three total Codex nodes requires explicit operator approval.
- Nodes can be isolated or chained by `depends_on`.
- Same-file sequential edits require an explicit dependency path.
- Dependency outputs are overlaid only into nodes that depend on them.
- Live repo remains clean until final all-or-nothing apply.
- Network/retry diagnostics are separated from semantic JSONL output and do not count against semantic output caps.
- Network transient failures become `CODEX_NETWORK_TRANSIENT` / exit 45 / retryable metadata.
- No raw `codex` allowlist is introduced.
- No ToyI runtime files are intended to change.

## Deterministic validation

Run:

```bash
python3 -m py_compile tools/claude_helpers/codex_chatgpt_flow_orchestrator.py
python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py --help
python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator_selftest.py
python3 tools/claude_helpers/codex_chatgpt_orchestrator_selftest.py
python3 tools/claude_helpers/codex_chatgpt_write_worker_selftest.py
python3 tools/claude_helpers/codex_chatgpt_subagent_selftest.py
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

## Real smoke

Do not run a real dynamic Codex smoke unless the operator explicitly approves it in-session.

Suggested real smoke after deterministic tests pass:

- one isolated docs node;
- one independent docs/test node;
- one dependent follow-up node;
- harmless throwaway file or intentionally retained audit doc only;
- inspect and revert unless operator approves retention.

## Package-local validation before delivery

Performed in this environment:

```text
python3 -m py_compile codex_chatgpt_flow_orchestrator.py codex_chatgpt_flow_orchestrator_selftest.py  PASS
python3 codex_chatgpt_flow_orchestrator.py --help                                           PASS
python3 codex_chatgpt_flow_orchestrator_selftest.py                                         PASS
```
