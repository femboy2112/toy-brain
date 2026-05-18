#!/usr/bin/env python3
"""Deterministic fake-codex selftest for codex_chatgpt_orchestrator.py.

Covers:
- in-process collision and symlink path rejection
- end-to-end fake-codex two-shard happy path with all-or-nothing apply
- end-to-end fake-codex partial-apply prevention via apply preflight
- hash-only audit record (no task/prompt content)
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
WRAPPER = ROOT / "codex_chatgpt_orchestrator.py"

spec = importlib.util.spec_from_file_location("orch", WRAPPER)
orch = importlib.util.module_from_spec(spec)
sys.modules["orch"] = orch
assert spec.loader is not None
spec.loader.exec_module(orch)


def run(args: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(args, cwd=str(cwd), env=merged, capture_output=True, text=True, timeout=timeout, check=False)


def make_repo(tmp: Path) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    repo = tmp / "repo"
    repo.mkdir()
    run(["git", "init"], cwd=repo)
    run(["git", "config", "user.email", "selftest@example.invalid"], cwd=repo)
    run(["git", "config", "user.name", "selftest"], cwd=repo)
    for name in ["a.txt", "b.txt", "shared.txt"]:
        (repo / name).write_text(f"before {name}\n", encoding="utf-8")
    run(["git", "add", "."], cwd=repo)
    commit = run(["git", "commit", "-m", "init"], cwd=repo)
    assert commit.returncode == 0, commit.stderr
    return repo


def make_fake_codex(tmp: Path) -> Path:
    fake = tmp / "codex"
    fake.write_text(textwrap.dedent(r'''
        #!/usr/bin/env python3
        import json, os, re, sys
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
            mm = re.search(r"WRITE_MODE=([^\s]+)", prompt)
            ml = re.search(r"SYMLINK_DEST=([^\s]+)", prompt)
            target = mt.group(1) if mt else "a.txt"
            mode = mm.group(1) if mm else "write"
            full = os.path.join(cwd, target)
            if mode == "symlink":
                if os.path.lexists(full):
                    os.unlink(full)
                dest = ml.group(1) if ml else "/tmp/codex-orch-selftest-missing"
                os.symlink(dest, full)
            else:
                with open(full, "w", encoding="utf-8") as fh:
                    fh.write("after " + target + "\n")
            print(json.dumps({"type":"thread.started","thread_id":"fake"}))
            print(json.dumps({"type":"item.completed","item":{"type":"command_execution","command":"fake edit","status":"completed"}}))
            print(json.dumps({"type":"item.completed","item":{"type":"file_change","path":target,"status":"completed"}}))
            print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"codex orchestration shard report for " + target + " (mode=" + mode + ")"}}))
            print(json.dumps({"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}))
            raise SystemExit(0)
        print("unknown fake codex args", args, file=sys.stderr)
        raise SystemExit(2)
    ''').lstrip(), encoding="utf-8")
    fake.chmod(0o755)
    return fake


def write_manifest(path: Path, shards: list[dict]) -> Path:
    path.write_text(json.dumps({
        "task": "selftest orchestration",
        "waves": [{"id": "wave1", "shards": shards}],
    }, indent=2), encoding="utf-8")
    return path


def assert_raises(fn, exc_type, msg: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(msg)


def case_in_process_checks(tmp: Path) -> None:
    repo = make_repo(tmp / "inprocess")
    s1 = orch.Shard("s1", "p", ("a.txt",), ("shared.txt",), ())
    s2 = orch.Shard("s2", "p", ("b.txt",), ("shared.txt",), ())
    orch.collision_check([s1, s2], max_parallel=2, max_real_calls=2)
    assert_raises(lambda: orch.collision_check([s1, orch.Shard("s3", "p", ("a.txt",), (), ())], max_parallel=2, max_real_calls=2), RuntimeError, "write/write collision not rejected")
    assert_raises(lambda: orch.collision_check([orch.Shard("r", "p", ("a.txt",), ("b.txt",), ()), s2], max_parallel=2, max_real_calls=2), RuntimeError, "read/write collision not rejected")
    assert_raises(lambda: orch.collision_check([s1, s2, orch.Shard("s3", "p", ("c.txt",), (), ())], max_parallel=2, max_real_calls=3), RuntimeError, "max_parallel not enforced")
    outside = tmp / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (repo / "sym.txt").symlink_to(outside)
    assert_raises(lambda: orch.validate_path("sym.txt", repo=str(repo), label="allowed file"), orch.SymlinkPathRejected, "symlink path not rejected")
    (repo / "sym.txt").unlink()


def case_happy_path(tmp: Path, fake: Path) -> None:
    repo = make_repo(tmp / "happy")
    man = write_manifest(tmp / "happy_manifest.json", [
        {"id": "s1", "prompt": "WRITE_TARGET=a.txt\nWRITE_MODE=write\nUpdate a.txt.", "allowed_files": ["a.txt"], "read_files": ["shared.txt"]},
        {"id": "s2", "prompt": "WRITE_TARGET=b.txt\nWRITE_MODE=write\nUpdate b.txt.", "allowed_files": ["b.txt"], "read_files": ["shared.txt"]},
    ])
    audit_dir = tmp / "happy_audit"
    state_dir = tmp / "happy_state"
    proc = run([
        sys.executable, str(WRAPPER),
        "--codex-executable", str(fake),
        "--cwd", str(repo),
        "--manifest", str(man),
        "--apply",
        "--model", "gpt-5.5",
        "--effort", "high",
        "--timeout", "30",
        "--max-parallel", "2",
        "--max-real-calls", "2",
        "--min-wave-interval-seconds", "0",
        "--selftest-no-pacing",
        "--audit-dir", str(audit_dir),
        "--state-dir", str(state_dir),
    ], cwd=repo)
    if proc.returncode != 0:
        raise AssertionError(f"happy orchestration failed\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}")
    if (repo / "a.txt").read_text(encoding="utf-8") != "after a.txt\n":
        raise AssertionError("a.txt not applied")
    if (repo / "b.txt").read_text(encoding="utf-8") != "after b.txt\n":
        raise AssertionError("b.txt not applied")
    logs = list(audit_dir.glob("*.jsonl"))
    if not logs:
        raise AssertionError("audit log missing")
    audit = logs[0].read_text(encoding="utf-8")
    if "task_sha256" not in audit or "selftest orchestration" in audit:
        raise AssertionError("audit should hash task without content")
    if "\"apply_preflight_failed\":false" not in audit.replace(" ", ""):
        raise AssertionError("audit must record apply_preflight_failed=false on happy path")


def case_partial_apply_prevented(tmp: Path, fake: Path) -> None:
    repo = make_repo(tmp / "preflight")
    # Shard B's source becomes a symlink in the temp worktree; preflight must
    # reject the entire apply so shard A's a.txt also stays untouched in the
    # live repo.
    symlink_dest = tmp / "outside-target.txt"
    symlink_dest.write_text("outside payload\n", encoding="utf-8")
    man = write_manifest(tmp / "preflight_manifest.json", [
        {"id": "s1", "prompt": "WRITE_TARGET=a.txt\nWRITE_MODE=write\nUpdate a.txt normally.", "allowed_files": ["a.txt"], "read_files": ["shared.txt"]},
        {"id": "s2", "prompt": f"WRITE_TARGET=b.txt\nWRITE_MODE=symlink\nSYMLINK_DEST={symlink_dest}\nReplace b.txt with a symlink.", "allowed_files": ["b.txt"], "read_files": ["shared.txt"]},
    ])
    audit_dir = tmp / "preflight_audit"
    state_dir = tmp / "preflight_state"
    before_a = (repo / "a.txt").read_text(encoding="utf-8")
    before_b = (repo / "b.txt").read_text(encoding="utf-8")
    proc = run([
        sys.executable, str(WRAPPER),
        "--codex-executable", str(fake),
        "--cwd", str(repo),
        "--manifest", str(man),
        "--apply",
        "--model", "gpt-5.5",
        "--effort", "high",
        "--timeout", "30",
        "--max-parallel", "2",
        "--max-real-calls", "2",
        "--min-wave-interval-seconds", "0",
        "--selftest-no-pacing",
        "--audit-dir", str(audit_dir),
        "--state-dir", str(state_dir),
    ], cwd=repo)
    if proc.returncode == 0:
        raise AssertionError(f"preflight should reject symlink-source apply but wrapper returned 0\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}")
    if proc.returncode != orch.EXIT_APPLY_PREFLIGHT_FAILED:
        raise AssertionError(f"expected EXIT_APPLY_PREFLIGHT_FAILED={orch.EXIT_APPLY_PREFLIGHT_FAILED}, got {proc.returncode}\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}")
    # Live repo must be unchanged: shard A's would-be write to a.txt must NOT
    # have been applied because the preflight rejected before any copy-back.
    after_a = (repo / "a.txt").read_text(encoding="utf-8")
    after_b_path = repo / "b.txt"
    after_b = after_b_path.read_text(encoding="utf-8")
    if after_a != before_a:
        raise AssertionError(f"shard A leaked into live repo despite preflight failure: a.txt={after_a!r}")
    if after_b != before_b:
        raise AssertionError(f"shard B leaked into live repo despite preflight failure: b.txt={after_b!r}")
    if after_b_path.is_symlink():
        raise AssertionError("b.txt in live repo became a symlink; preflight must prevent that copy")
    # Live repo must not contain any extra files that were never tracked.
    expected = {"a.txt", "b.txt", "shared.txt"}
    actual = {p.name for p in repo.iterdir() if p.name != ".git"}
    if actual != expected:
        raise AssertionError(f"unexpected files in live repo after preflight rejection: {actual - expected}")
    logs = list(audit_dir.glob("*.jsonl"))
    if not logs:
        raise AssertionError("preflight audit log missing")
    audit_text = logs[0].read_text(encoding="utf-8")
    audit_compact = audit_text.replace(" ", "")
    if "\"apply_preflight_failed\":true" not in audit_compact:
        raise AssertionError("audit must record apply_preflight_failed=true")
    if "\"error_class\":\"APPLY_PREFLIGHT_FAILED\"" not in audit_compact:
        raise AssertionError("audit must record error_class=APPLY_PREFLIGHT_FAILED")
    if "selftest orchestration" in audit_text:
        raise AssertionError("audit should hash task without content")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fake = make_fake_codex(tmp)
        case_in_process_checks(tmp)
        case_happy_path(tmp, fake)
        case_partial_apply_prevented(tmp, fake)
    print("codex_chatgpt_orchestrator_selftest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
