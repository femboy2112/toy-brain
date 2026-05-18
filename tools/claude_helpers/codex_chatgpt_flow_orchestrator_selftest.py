#!/usr/bin/env python3
"""Deterministic fake-Codex selftest for codex_chatgpt_flow_orchestrator.py.

Coverage:
- dependency cycle rejected;
- max_parallel > 2 rejected;
- more than three calls requires explicit operator approval;
- write/write conflict without dependency rejected;
- sequential same-file writes with dependency accepted;
- dynamic scheduling observes at most two active Codex processes;
- a dependency-ready node can run in the same flow after an active slot opens;
- network diagnostic noise does not count against semantic output caps and is suppressed from final reports;
- nonzero transient network failures become CODEX_NETWORK_TRANSIENT.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap


ROOT = Path(__file__).resolve().parent
WRAPPER = ROOT / "codex_chatgpt_flow_orchestrator.py"

spec = importlib.util.spec_from_file_location("flow_orch", WRAPPER)
flow_orch = importlib.util.module_from_spec(spec)
sys.modules["flow_orch"] = flow_orch
assert spec.loader is not None
spec.loader.exec_module(flow_orch)


def run(args: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(args, cwd=str(cwd), env=merged, capture_output=True, text=True, timeout=timeout, check=False)


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir(parents=True)
    run(["git", "init"], cwd=repo)
    run(["git", "config", "user.email", "selftest@example.invalid"], cwd=repo)
    run(["git", "config", "user.name", "selftest"], cwd=repo)
    for name in ["a.txt", "b.txt", "c.txt", "shared.txt", "noise.txt", "netfail.txt"]:
        (repo / name).write_text(f"before {name}\n", encoding="utf-8")
    run(["git", "add", "."], cwd=repo)
    commit = run(["git", "commit", "-m", "init"], cwd=repo)
    assert commit.returncode == 0, commit.stderr
    return repo


def make_fake_codex(tmp: Path) -> Path:
    fake = tmp / "codex"
    fake.write_text(textwrap.dedent(r'''
        #!/usr/bin/env python3
        import fcntl, json, os, re, sys, time
        from pathlib import Path

        def update_state(delta):
            state_path = os.environ.get("FLOW_FAKE_STATE")
            if not state_path:
                return
            path = Path(state_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a+", encoding="utf-8") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                fh.seek(0)
                raw = fh.read().strip()
                data = json.loads(raw) if raw else {"active": 0, "max_active": 0, "calls": []}
                data["active"] += delta
                data["max_active"] = max(data["max_active"], data["active"])
                data["calls"].append({"pid": os.getpid(), "delta": delta, "active": data["active"], "time": time.time()})
                fh.seek(0)
                fh.truncate()
                fh.write(json.dumps(data, sort_keys=True))
                fh.flush()
                fcntl.flock(fh, fcntl.LOCK_UN)

        args = sys.argv[1:]
        if args == ["--version"]:
            print("codex-cli 0.130.0")
            raise SystemExit(0)
        if args == ["login", "status"]:
            print("Logged in using ChatGPT")
            raise SystemExit(0)
        if args[:2] == ["exec", "--help"]:
            print("usage: codex exec --json --sandbox read-only|workspace-write|danger-full-access --ephemeral --skip-git-repo-check -m MODEL -c, --config key=value --cd DIR -")
            raise SystemExit(0)
        if args and args[0] == "exec":
            prompt = sys.stdin.read()
            cwd = os.getcwd()
            if "--cd" in args:
                cwd = args[args.index("--cd") + 1]
            mt = re.search(r"WRITE_TARGET=([^\s]+)", prompt)
            ms = re.search(r"SLEEP_MS=(\d+)", prompt)
            ma = re.search(r"APPEND_TEXT=([^\n]+)", prompt)
            target = mt.group(1) if mt else "a.txt"
            sleep_ms = int(ms.group(1)) if ms else 0
            append_text = ma.group(1).strip() if ma else ("after " + target)
            update_state(+1)
            try:
                if "NETWORK_FAIL" in prompt:
                    print("connection reset by peer while streaming", file=sys.stderr)
                    raise SystemExit(5)
                if sleep_ms:
                    time.sleep(sleep_ms / 1000)
                if "NETWORK_NOISE" in prompt:
                    print("websocket stream disconnected; retry later " + ("x" * 5000))
                full = os.path.join(cwd, target)
                with open(full, "a", encoding="utf-8") as fh:
                    fh.write(append_text + "\n")
                mextra = re.search(r"EXTRA_TARGET=([^\s]+)", prompt)
                if mextra:
                    extra_full = os.path.join(cwd, mextra.group(1))
                    with open(extra_full, "a", encoding="utf-8") as fh:
                        fh.write("out-of-scope\n")
                print(json.dumps({"type": "thread.started", "thread_id": "fake"}))
                print(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "fake edit", "status": "completed"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "file_change", "path": target, "status": "completed"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "codex dynamic flow node report for " + target}}))
                if "SEMANTIC_BLOAT" in prompt:
                    print(json.dumps({"type": "thread.metadata", "blob": "y" * 8000}))
                print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}))
                raise SystemExit(0)
            finally:
                update_state(-1)
        print("unknown fake codex args", args, file=sys.stderr)
        raise SystemExit(2)
    ''').lstrip(), encoding="utf-8")
    fake.chmod(0o755)
    return fake


def write_manifest(path: Path, nodes: list[dict]) -> Path:
    path.write_text(json.dumps({"task": "flow selftest", "nodes": nodes}, indent=2), encoding="utf-8")
    return path


def wrapper_cmd(repo: Path, fake: Path, manifest: Path, tmp: Path, extra: list[str] | None = None) -> list[str]:
    cmd = [
        sys.executable, str(WRAPPER),
        "--codex-executable", str(fake),
        "--cwd", str(repo),
        "--manifest", str(manifest),
        "--apply",
        "--model", "gpt-5.5",
        "--effort", "high",
        "--timeout", "30",
        "--max-parallel", "2",
        "--max-total-calls", "3",
        "--min-flow-interval-seconds", "0",
        "--min-start-gap-seconds", "0",
        "--selftest-no-pacing",
        "--audit-dir", str(tmp / "audit"),
        "--state-dir", str(tmp / "state"),
    ]
    if extra:
        cmd.extend(extra)
    return cmd


def expect_code(proc: subprocess.CompletedProcess[str], code: int, label: str) -> None:
    if proc.returncode != code:
        raise AssertionError(f"{label}: expected return {code}, got {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")


def expect_raises(fn, exc_types, label: str) -> None:
    try:
        fn()
    except exc_types:
        return
    raise AssertionError(f"{label}: expected exception")


def normalize(repo: Path, nodes: list[dict]):
    manifest = {"task": "unit", "nodes": nodes}
    return flow_orch.normalize_manifest(
        manifest,
        repo=str(repo),
        default_model="gpt-5.5",
        default_effort="high",
        default_timeout=30,
    )


def case_in_process_rejections(tmp: Path) -> None:
    repo = make_repo(tmp / "unit")
    expect_raises(
        lambda: normalize(repo, [
            {"id": "a", "prompt": "p", "allowed_files": ["a.txt"], "depends_on": ["b"]},
            {"id": "b", "prompt": "p", "allowed_files": ["b.txt"], "depends_on": ["a"]},
        ]),
        ValueError,
        "cycle rejected",
    )
    _task, nodes, _by_id, _closure = normalize(repo, [
        {"id": "a", "prompt": "p", "allowed_files": ["a.txt"]},
    ])
    expect_raises(
        lambda: flow_orch.validate_caps(nodes=nodes, max_parallel=3, max_total_calls=1, operator_approved=False),
        ValueError,
        "max_parallel rejected",
    )
    _task, nodes, _by_id, _closure = normalize(repo, [
        {"id": "a", "prompt": "p", "allowed_files": ["a.txt"]},
        {"id": "b", "prompt": "p", "allowed_files": ["b.txt"]},
        {"id": "c", "prompt": "p", "allowed_files": ["c.txt"]},
        {"id": "d", "prompt": "p", "allowed_files": ["noise.txt"]},
    ])
    expect_raises(
        lambda: flow_orch.validate_caps(nodes=nodes, max_parallel=2, max_total_calls=4, operator_approved=False),
        RuntimeError,
        "call budget rejected",
    )
    expect_raises(
        lambda: normalize(repo, [
            {"id": "a", "prompt": "p", "allowed_files": ["shared.txt"]},
            {"id": "b", "prompt": "p", "allowed_files": ["shared.txt"]},
        ]),
        RuntimeError,
        "write/write conflict rejected",
    )


def case_dynamic_sequential_noise_flow(tmp: Path, fake: Path) -> None:
    repo = make_repo(tmp / "dynamic")
    state = tmp / "dynamic_state.json"
    man = write_manifest(tmp / "dynamic.json", [
        {"id": "first", "prompt": "WRITE_TARGET=shared.txt\nSLEEP_MS=100\nAPPEND_TEXT=FIRST", "allowed_files": ["shared.txt"]},
        {"id": "noise", "prompt": "WRITE_TARGET=noise.txt\nSLEEP_MS=1500\nNETWORK_NOISE\nAPPEND_TEXT=NOISE_OK", "allowed_files": ["noise.txt"]},
        {"id": "second-after-first", "prompt": "WRITE_TARGET=shared.txt\nAPPEND_TEXT=SECOND", "allowed_files": ["shared.txt"], "read_files": ["shared.txt"], "depends_on": ["first"]},
    ])
    env = {"FLOW_FAKE_STATE": str(state)}
    proc = run(wrapper_cmd(repo, fake, man, tmp / "dynamic", ["--max-semantic-output-chars", "2000"]), cwd=repo, env=env)
    expect_code(proc, 0, "dynamic sequential/noise flow")
    data = json.loads(state.read_text(encoding="utf-8"))
    if data["max_active"] > 2:
        raise AssertionError(f"max active exceeded 2: {data}")
    if data["max_active"] != 2:
        raise AssertionError(f"dynamic flow should observe two active Codex processes: {data}")
    shared = (repo / "shared.txt").read_text(encoding="utf-8")
    noise = (repo / "noise.txt").read_text(encoding="utf-8")
    if "FIRST" not in shared or "SECOND" not in shared:
        raise AssertionError(f"sequential same-file dependency did not preserve both edits: {shared!r}")
    if "NOISE_OK" not in noise:
        raise AssertionError("network-noise node output not applied")
    if "websocket stream disconnected" in proc.stdout:
        raise AssertionError("network noise leaked into final report")
    if "network noise lines: 1" not in proc.stdout:
        raise AssertionError("network noise count missing from final report")
    if "max simultaneous observed: 2" not in proc.stdout:
        raise AssertionError("wrapper report did not show max concurrency")


def case_network_transient_failure(tmp: Path, fake: Path) -> None:
    repo = make_repo(tmp / "netfail")
    man = write_manifest(tmp / "netfail.json", [
        {"id": "netfail", "prompt": "WRITE_TARGET=netfail.txt\nNETWORK_FAIL", "allowed_files": ["netfail.txt"]},
    ])
    proc = run(wrapper_cmd(repo, fake, man, tmp / "netfail"), cwd=repo)
    expect_code(proc, flow_orch.EXIT_CODEX_NETWORK_TRANSIENT, "network transient failure")
    if "CODEX_NETWORK_TRANSIENT" not in proc.stdout:
        raise AssertionError("network transient error class missing")


def case_true_semantic_oversize(tmp: Path, fake: Path) -> None:
    repo = make_repo(tmp / "oversize")
    man = write_manifest(tmp / "oversize.json", [
        {"id": "bloat", "prompt": "WRITE_TARGET=a.txt\nSEMANTIC_BLOAT\nAPPEND_TEXT=ok", "allowed_files": ["a.txt"]},
    ])
    proc = run(
        wrapper_cmd(repo, fake, man, tmp / "oversize", ["--max-semantic-output-chars", "200"]),
        cwd=repo,
    )
    expect_code(proc, flow_orch.EXIT_CODEX_OUTPUT_TOO_LARGE, "true semantic oversize")
    if "CODEX_OUTPUT_TOO_LARGE" not in proc.stdout:
        raise AssertionError("true-semantic-oversize error class missing from report")
    if (repo / "a.txt").read_text(encoding="utf-8") != "before a.txt\n":
        raise AssertionError("live a.txt changed despite semantic-oversize failure")


def case_out_of_scope_diff(tmp: Path, fake: Path) -> None:
    repo = make_repo(tmp / "oos")
    man = write_manifest(tmp / "oos.json", [
        {"id": "oos-write", "prompt": "WRITE_TARGET=a.txt\nEXTRA_TARGET=b.txt\nAPPEND_TEXT=ok", "allowed_files": ["a.txt"]},
    ])
    proc = run(wrapper_cmd(repo, fake, man, tmp / "oos"), cwd=repo)
    expect_code(proc, flow_orch.EXIT_OUT_OF_SCOPE_DIFF, "out-of-scope diff rejection")
    if "OUT_OF_SCOPE_DIFF" not in proc.stdout:
        raise AssertionError("out-of-scope error class missing from report")
    if (repo / "a.txt").read_text(encoding="utf-8") != "before a.txt\n":
        raise AssertionError("live a.txt changed despite out-of-scope rejection")
    if (repo / "b.txt").read_text(encoding="utf-8") != "before b.txt\n":
        raise AssertionError("live b.txt changed despite out-of-scope rejection")


def case_all_or_nothing_apply(tmp: Path, fake: Path) -> None:
    """Parallel nodes: one would succeed alone, the other fails out-of-scope.
    The wrapper must reject the flow and leave the live repo entirely unchanged.
    """
    repo = make_repo(tmp / "aon")
    man = write_manifest(tmp / "aon.json", [
        {
            "id": "ok-node",
            "prompt": "WRITE_TARGET=a.txt\nSLEEP_MS=200\nAPPEND_TEXT=OK_NODE",
            "allowed_files": ["a.txt"],
        },
        {
            "id": "fail-node",
            "prompt": "WRITE_TARGET=b.txt\nEXTRA_TARGET=c.txt\nSLEEP_MS=200\nAPPEND_TEXT=FAIL_NODE",
            "allowed_files": ["b.txt"],
        },
    ])
    proc = run(wrapper_cmd(repo, fake, man, tmp / "aon"), cwd=repo)
    if proc.returncode == 0:
        raise AssertionError(
            f"all-or-nothing flow should have failed; stdout={proc.stdout!r}"
        )
    if "OUT_OF_SCOPE_DIFF" not in proc.stdout:
        raise AssertionError("expected OUT_OF_SCOPE_DIFF in failure report")
    for name in ("a.txt", "b.txt", "c.txt"):
        live_text = (repo / name).read_text(encoding="utf-8")
        if live_text != f"before {name}\n":
            raise AssertionError(
                f"all-or-nothing violated: live {name} changed to {live_text!r}"
            )
    porcelain = run(["git", "status", "--porcelain"], cwd=repo)
    if porcelain.stdout.strip() != "":
        raise AssertionError(
            f"all-or-nothing violated: live repo not clean: {porcelain.stdout!r}"
        )


def case_audit_hash_only(tmp: Path, fake: Path) -> None:
    """Audit JSONL must hash the manifest and per-node prompts. No raw prompt
    text or task description text may be persisted in audit records."""
    repo = make_repo(tmp / "audit")
    secret_marker = "SECRET_NODE_PROMPT_marker_xyz123_DONOTPERSIST"
    secret_task = "SECRET_TASK_marker_qrs789_DONOTPERSIST"
    manifest_obj = {
        "task": secret_task,
        "nodes": [
            {
                "id": "audit-ok",
                "prompt": f"WRITE_TARGET=a.txt\nAPPEND_TEXT={secret_marker}",
                "allowed_files": ["a.txt"],
            }
        ],
    }
    manifest_path = tmp / "audit.json"
    manifest_path.write_text(json.dumps(manifest_obj, indent=2), encoding="utf-8")
    proc = run(wrapper_cmd(repo, fake, manifest_path, tmp / "audit"), cwd=repo)
    expect_code(proc, 0, "audit hash-only run")

    audit_dir = tmp / "audit" / "audit"
    audit_files = sorted(audit_dir.glob("*.jsonl"))
    if not audit_files:
        raise AssertionError("no audit jsonl record was written")
    total_records = 0
    for ap in audit_files:
        raw = ap.read_text(encoding="utf-8")
        if secret_marker in raw:
            raise AssertionError(f"raw node prompt content persisted in {ap}")
        if secret_task in raw:
            raise AssertionError(f"raw task content persisted in {ap}")
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            total_records += 1
            if not rec.get("manifest_sha256"):
                raise AssertionError("audit record missing manifest_sha256")
            prompt_sha = rec.get("node_prompt_sha256")
            if not isinstance(prompt_sha, dict) or "audit-ok" not in prompt_sha:
                raise AssertionError("audit record missing node_prompt_sha256 for node")
            for key, value in rec.items():
                if isinstance(value, str):
                    if secret_marker in value or secret_task in value:
                        raise AssertionError(f"raw prompt/task content found in audit field {key!r}")
            if "prompt" in rec or "task_text" in rec or "manifest_text" in rec:
                raise AssertionError("audit record contains non-hash prompt/task/manifest text")
    if total_records < 1:
        raise AssertionError("audit jsonl had zero parseable records")

    expected_manifest_sha = flow_orch.sha256_text(
        json.dumps(manifest_obj, sort_keys=True)
    )
    expected_prompt_sha = flow_orch.sha256_text(manifest_obj["nodes"][0]["prompt"])
    last_record = json.loads(
        [ln for ln in audit_files[-1].read_text(encoding="utf-8").splitlines() if ln.strip()][-1]
    )
    if last_record["node_prompt_sha256"]["audit-ok"] != expected_prompt_sha:
        raise AssertionError("audit node_prompt_sha256 does not match sha256 of node prompt")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fake = make_fake_codex(tmp)
        case_in_process_rejections(tmp)
        case_dynamic_sequential_noise_flow(tmp, fake)
        case_network_transient_failure(tmp, fake)
        case_true_semantic_oversize(tmp, fake)
        case_out_of_scope_diff(tmp, fake)
        case_all_or_nothing_apply(tmp, fake)
        case_audit_hash_only(tmp, fake)
    print("codex_chatgpt_flow_orchestrator_selftest: PASS")
    return 0


if __name__ == "__main__":
    _code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_code)
