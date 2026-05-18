#!/usr/bin/env python3
"""Deterministic fake-codex selftest for codex_chatgpt_write_worker.py."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parent
WRAPPER = ROOT / "codex_chatgpt_write_worker.py"


def run(args: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(args, cwd=str(cwd), env=merged, capture_output=True, text=True, timeout=timeout, check=False)


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    run(["git", "init"], cwd=repo)
    run(["git", "config", "user.email", "selftest@example.invalid"], cwd=repo)
    run(["git", "config", "user.name", "selftest"], cwd=repo)
    (repo / "allowed.txt").write_text("before\n", encoding="utf-8")
    run(["git", "add", "allowed.txt"], cwd=repo)
    commit = run(["git", "commit", "-m", "init"], cwd=repo)
    assert commit.returncode == 0, commit.stderr
    return repo


def make_fake_codex(tmp: Path) -> Path:
    fake = tmp / "codex"
    fake.write_text(textwrap.dedent(r'''
        #!/usr/bin/env python3
        import os, sys, time
        args = sys.argv[1:]
        if args == ["--version"]:
            print("codex-cli 0.130.0")
            raise SystemExit(0)
        if args == ["login", "status"]:
            if os.environ.get("FAKE_CODEX_AUTH_FAIL"):
                print("not logged in; run codex login", file=sys.stderr)
                raise SystemExit(1)
            print("Logged in using ChatGPT")
            raise SystemExit(0)
        if args[:2] == ["exec", "--help"]:
            if os.environ.get("FAKE_CODEX_NO_WORKSPACE_WRITE"):
                print("usage: codex exec --sandbox read-only --ephemeral --skip-git-repo-check -m MODEL -c, --config key=value --cd DIR -")
            else:
                print("usage: codex exec --sandbox read-only|workspace-write|danger-full-access --ephemeral --skip-git-repo-check -m MODEL -c, --config key=value --cd DIR -")
            raise SystemExit(0)
        if args and args[0] == "exec":
            prompt = sys.stdin.read()
            if os.environ.get("FAKE_CODEX_SLEEP"):
                time.sleep(float(os.environ["FAKE_CODEX_SLEEP"]))
            cwd = os.getcwd()
            if "--cd" in args:
                cwd = args[args.index("--cd") + 1]
            target = os.environ.get("FAKE_CODEX_WRITE_TARGET", "allowed.txt")
            with open(os.path.join(cwd, target), "w", encoding="utf-8") as fh:
                fh.write("after from fake codex\n")
            if os.environ.get("FAKE_CODEX_OUT_OF_SCOPE"):
                with open(os.path.join(cwd, "outside.txt"), "w", encoding="utf-8") as fh:
                    fh.write("out of scope\n")
            if os.environ.get("FAKE_CODEX_NONZERO"):
                print("fake nonzero", file=sys.stderr)
                raise SystemExit(7)
            if os.environ.get("FAKE_CODEX_BIG_OUTPUT"):
                print("x" * 100000)
            else:
                print("codex limited-write report\n\nChanged files:\n- allowed.txt: updated by fake codex")
            raise SystemExit(0)
        print("unknown fake codex args", args, file=sys.stderr)
        raise SystemExit(2)
    ''').lstrip(), encoding="utf-8")
    fake.chmod(0o755)
    return fake


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    if not WRAPPER.exists():
        print(f"missing wrapper: {WRAPPER}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fake = make_fake_codex(tmp)

        # Happy path: fake Codex writes allowed file inside temp worktree;
        # wrapper copies only that file back to live repo.
        repo = make_repo(tmp / "case_ok") if False else None
        case_ok = tmp / "case_ok"; case_ok.mkdir(); repo = make_repo(case_ok)
        prompt = tmp / "prompt.txt"; prompt.write_text("Update allowed.txt only.\n", encoding="utf-8")
        proc = run([
            sys.executable, str(WRAPPER),
            "--codex-executable", str(fake),
            "--cwd", str(repo),
            "--allowed-file", "allowed.txt",
            "--apply",
            "--prompt-file", str(prompt),
            "--model", "gpt-5.5",
            "--effort", "high",
            "--timeout", "30",
            "--min-interval-seconds", "0",
            "--selftest-no-pacing",
        ], cwd=repo)
        assert_true(proc.returncode == 0, f"happy path failed:\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}")
        assert_true((repo / "allowed.txt").read_text(encoding="utf-8") == "after from fake codex\n", "allowed file not copied back")
        assert_true("workspace-write" in proc.stdout, "report should mention workspace-write sandbox")
        log_dir = repo / ".claude" / "codex_bridge_logs"
        logs = list(log_dir.glob("*.jsonl"))
        assert_true(bool(logs), "audit log not written")
        audit_text = logs[0].read_text(encoding="utf-8")
        assert_true("prompt_sha256" in audit_text and "Update allowed" not in audit_text, "audit should hash prompt without content")

        # Out of scope path: live repo should remain unchanged from its committed baseline.
        case_oos = tmp / "case_oos"; case_oos.mkdir(); repo2 = make_repo(case_oos)
        prompt2 = tmp / "prompt2.txt"; prompt2.write_text("Try to write outside too.\n", encoding="utf-8")
        proc2 = run([
            sys.executable, str(WRAPPER),
            "--codex-executable", str(fake),
            "--cwd", str(repo2),
            "--allowed-file", "allowed.txt",
            "--apply",
            "--prompt-file", str(prompt2),
            "--model", "gpt-5.5",
            "--effort", "high",
            "--timeout", "30",
            "--min-interval-seconds", "0",
            "--selftest-no-pacing",
        ], cwd=repo2, env={"FAKE_CODEX_OUT_OF_SCOPE": "1"})
        assert_true(proc2.returncode == 33, f"out-of-scope should return 33, got {proc2.returncode}\n{proc2.stdout}\n{proc2.stderr}")
        assert_true((repo2 / "allowed.txt").read_text(encoding="utf-8") == "before\n", "live repo changed despite out-of-scope failure")
        assert_true(not (repo2 / "outside.txt").exists(), "out-of-scope file leaked into live repo")

        # Dirty live worktree should fail before Codex invocation.
        case_dirty = tmp / "case_dirty"; case_dirty.mkdir(); repo3 = make_repo(case_dirty)
        (repo3 / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        proc3 = run([
            sys.executable, str(WRAPPER),
            "--codex-executable", str(fake),
            "--cwd", str(repo3),
            "--allowed-file", "allowed.txt",
            "--apply",
            "--prompt-file", str(prompt),
            "--model", "gpt-5.5",
            "--effort", "high",
            "--timeout", "30",
            "--min-interval-seconds", "0",
            "--selftest-no-pacing",
        ], cwd=repo3)
        assert_true(proc3.returncode == 31, f"dirty worktree should return 31, got {proc3.returncode}")

        # Invalid model rejected before subprocess.
        case_model = tmp / "case_model"; case_model.mkdir(); repo4 = make_repo(case_model)
        proc4 = run([
            sys.executable, str(WRAPPER),
            "--codex-executable", str(fake),
            "--cwd", str(repo4),
            "--allowed-file", "allowed.txt",
            "--apply",
            "--prompt-file", str(prompt),
            "--model", "bad model with spaces",
            "--effort", "high",
            "--min-interval-seconds", "0",
            "--selftest-no-pacing",
        ], cwd=repo4)
        assert_true(proc4.returncode == 13, f"invalid model should return 13, got {proc4.returncode}")

        # Missing workspace-write support rejected.
        case_flag = tmp / "case_flag"; case_flag.mkdir(); repo5 = make_repo(case_flag)
        proc5 = run([
            sys.executable, str(WRAPPER),
            "--codex-executable", str(fake),
            "--cwd", str(repo5),
            "--allowed-file", "allowed.txt",
            "--apply",
            "--prompt-file", str(prompt),
            "--model", "gpt-5.5",
            "--effort", "high",
            "--min-interval-seconds", "0",
            "--selftest-no-pacing",
        ], cwd=repo5, env={"FAKE_CODEX_NO_WORKSPACE_WRITE": "1"})
        assert_true(proc5.returncode == 12, f"unsupported flag should return 12, got {proc5.returncode}")

    print("codex_chatgpt_write_worker_selftest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
