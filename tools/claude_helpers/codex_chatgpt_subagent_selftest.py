#!/usr/bin/env python3
"""Deterministic fake-codex selftest for codex_chatgpt_subagent.py.

Run from repo root after installing payload files:

    python3 tools/claude_helpers/codex_chatgpt_subagent_selftest.py

No real Codex call occurs. The test injects a fake `codex` executable via PATH.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = Path(__file__).resolve().parent / "codex_chatgpt_subagent.py"

FAKE_CODEX = r'''#!/bin/sh
if [ -n "$FAKE_CODEX_LOG" ]; then
  printf '%s\n' "$*" >> "$FAKE_CODEX_LOG"
fi

if [ "$1" = "--version" ]; then
  echo "codex fake-9.9.9"
  exit 0
fi

if [ "$1" = "login" ] && [ "$2" = "status" ]; then
  if [ "$FAKE_CODEX_MODE" = "auth" ]; then
    echo "not logged in; run codex login" >&2
    exit 1
  fi
  echo "Logged in as fake-user"
  exit 0
fi

if [ "$1" = "exec" ] && [ "$2" = "--help" ]; then
  if [ "$FAKE_NO_CONFIG" = "1" ]; then
    cat <<'HELP'
Usage: codex exec [OPTIONS] [PROMPT]
  -m, --model <MODEL>
      --sandbox <MODE>
      --ephemeral
      --skip-git-repo-check
      --cd <DIR>
HELP
  else
    cat <<'HELP'
Usage: codex exec [OPTIONS] [PROMPT]
  -m, --model <MODEL>
  -c, --config <key=value>
      --sandbox <MODE>
      --ephemeral
      --skip-git-repo-check
      --cd <DIR>
HELP
  fi
  exit 0
fi

if [ "$1" = "exec" ]; then
  prompt=$(cat)
  if [ "$FAKE_CODEX_MODE" = "timeout" ]; then
    sleep 5
  fi
  if [ "$FAKE_CODEX_MODE" = "nonzero" ]; then
    echo "fake nonzero failure" >&2
    exit 7
  fi
  if [ "$FAKE_CODEX_MODE" = "auth" ]; then
    echo "not logged in; run codex login" >&2
    exit 1
  fi
  if [ "$FAKE_CODEX_MODE" = "large" ]; then
    yes X | head -c 20000
    echo
    exit 0
  fi
  echo "chatgpt-codex-subagent report"
  echo "Mode:"
  echo "- fake"
  echo "Answer:"
  echo "- fake success; prompt_chars=${#prompt}"
  exit 0
fi

echo "unknown fake codex invocation: $*" >&2
exit 2
'''


def run_case(tmp: Path, name: str, args: list[str], *, env_extra: dict[str, str] | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = str(tmp / "bin") + os.pathsep + env.get("PATH", "")
    env["FAKE_CODEX_LOG"] = str(tmp / f"{name}.argv.txt")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(WRAPPER), *args],
        input=input_text,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


def assert_contains(haystack: str, needle: str) -> None:
    if needle not in haystack:
        raise AssertionError(f"expected {needle!r} in output:\n{haystack}")


def load_last_argv(tmp: Path, name: str) -> list[str]:
    path = tmp / f"{name}.argv.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[-1].split()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="codex_bridge_selftest_") as d:
        tmp = Path(d)
        bindir = tmp / "bin"
        bindir.mkdir()
        fake = bindir / "codex"
        fake.write_text(FAKE_CODEX, encoding="utf-8")
        fake.chmod(0o755)
        audit_dir = tmp / "audit"

        common = [
            "--mode", "plan",
            "--model", "gpt-test_1:/ok",
            "--effort", "low",
            "--audit-dir", str(audit_dir),
            "--max-output-chars", "16000",
        ]

        probe = run_case(tmp, "probe", ["--probe-only", "--audit-dir", str(audit_dir)])
        assert probe.returncode == 0, probe.stdout + probe.stderr
        assert_contains(probe.stdout, "codex capability probe passed")

        ok = run_case(tmp, "ok", common, input_text="Plan this fake task.")
        assert ok.returncode == 0, ok.stdout + ok.stderr
        assert_contains(ok.stdout, "fake success")
        argv = load_last_argv(tmp, "ok")
        joined = " ".join(argv)
        assert "--sandbox" in argv and "read-only" in argv, joined
        assert "--ephemeral" in argv, joined
        assert "--skip-git-repo-check" in argv, joined
        assert "-m" in argv and "gpt-test_1:/ok" in argv, joined
        assert "-c" in argv and "model_reasoning_effort=low" in argv, joined
        assert argv[-1] == "-", joined

        bad_model = run_case(tmp, "bad_model", ["--mode", "plan", "--model", "bad model!", "--audit-dir", str(audit_dir)], input_text="x")
        assert bad_model.returncode == 13, bad_model.stdout + bad_model.stderr
        assert_contains(bad_model.stdout, "CODEX_MODEL_INVALID")

        no_config = run_case(tmp, "no_config", ["--probe-only", "--audit-dir", str(audit_dir)], env_extra={"FAKE_NO_CONFIG": "1"})
        assert no_config.returncode == 12, no_config.stdout + no_config.stderr
        assert_contains(no_config.stdout, "CODEX_UNSUPPORTED_FLAG")

        auth = run_case(tmp, "auth", common, env_extra={"FAKE_CODEX_MODE": "auth"}, input_text="x")
        assert auth.returncode == 11, auth.stdout + auth.stderr
        assert_contains(auth.stdout, "CODEX_AUTH_MISSING_OR_INVALID")

        large = run_case(tmp, "large", common + ["--max-output-chars", "100"], env_extra={"FAKE_CODEX_MODE": "large"}, input_text="x")
        assert large.returncode == 22, large.stdout + large.stderr
        assert_contains(large.stdout, "CODEX_OUTPUT_TOO_LARGE")

        timeout = run_case(tmp, "timeout", common + ["--timeout", "1"], env_extra={"FAKE_CODEX_MODE": "timeout"}, input_text="x")
        assert timeout.returncode == 20, timeout.stdout + timeout.stderr
        assert_contains(timeout.stdout, "CODEX_TIMEOUT")

        audit_files = list(audit_dir.glob("*.jsonl"))
        assert audit_files, "expected audit jsonl file"
        audit_lines = audit_files[0].read_text(encoding="utf-8").splitlines()
        assert audit_lines, "expected audit records"
        record = json.loads(audit_lines[0])
        assert "prompt_sha256" in record
        assert "prompt_template_sha256" in record
        assert "prompt_chars" in record
        assert "Plan this fake task" not in audit_files[0].read_text(encoding="utf-8")

    print("codex_chatgpt_subagent_selftest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
