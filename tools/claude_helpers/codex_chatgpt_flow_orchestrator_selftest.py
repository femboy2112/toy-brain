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
                print(json.dumps({"type": "thread.started", "thread_id": "fake"}))
                print(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "fake edit", "status": "completed"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "file_change", "path": target, "status": "completed"}}))
                print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "codex dynamic flow node report for " + target}}))
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


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fake = make_fake_codex(tmp)
        case_in_process_rejections(tmp)
        case_dynamic_sequential_noise_flow(tmp, fake)
        case_network_transient_failure(tmp, fake)
    print("codex_chatgpt_flow_orchestrator_selftest: PASS")
    return 0


if __name__ == "__main__":
    _code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_code)
