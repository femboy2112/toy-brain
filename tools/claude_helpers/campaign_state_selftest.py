#!/usr/bin/env python3
"""Selftest for campaign_state.py using temporary git repositories."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def load_module():
    sys.dont_write_bytecode = True
    path = Path(__file__).resolve().with_name("campaign_state.py")
    spec = importlib.util.spec_from_file_location("campaign_state_under_test", path)
    if spec is None or spec.loader is None:
        raise AssertionError("failed to construct import spec for campaign_state.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_git(repo: Path, *args: str) -> None:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr or proc.stdout}")


def commit_empty(repo: Path, subject: str) -> None:
    run_git(repo, "commit", "--allow-empty", "-m", subject)


def init_repo(repo: Path) -> None:
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "test@example.invalid")
    run_git(repo, "config", "user.name", "Campaign State Test")
    commit_empty(repo, "phase3.14 step1: foo")
    commit_empty(repo, "phase3.14 step2: bar")
    commit_empty(repo, "Merge pull request #16 from femboy2112/campaign/phase3-14-llm-cache-discipline")
    commit_empty(repo, "phase3.15 step1: baz")
    commit_empty(repo, "phase3.15 step2: qux")


def call_state(module, argv: list[str]) -> tuple[int, dict]:
    args = module.parse_args(argv)
    exit_code, state, error = module.collect_state(args)
    if error:
        raise AssertionError(f"collect_state returned unexpected error: {error}")
    return exit_code, state


def write_mission(repo: Path, phase: str, next_step: int) -> None:
    (repo / "CURRENT_MISSION.md").write_text(
        "\n".join(
            [
                f"Next eligible step: {phase} Step {next_step}",
                f"Phase {phase} Step {next_step} status: READY",
                "Catalog: v0.test",
                "",
            ]
        ),
        encoding="utf-8",
    )


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_tests() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        init_repo(repo)

        code, state = call_state(module, ["summary", "--repo", str(repo), "--no-mission"])
        summary = module.format_summary(state)
        assert_true(code == 0, f"summary returned exit code {code}")
        assert_true(summary.strip(), "summary output is empty")
        assert_true("phase3.15" in summary, "summary does not mention latest phase")
        assert_true("highest step 2" in summary, "summary does not mention highest step")

        code, state = call_state(module, ["json", "--repo", str(repo), "--no-mission"])
        payload = json.loads(json.dumps(state))
        assert_true(code == 0, f"json returned exit code {code}")
        assert_true(payload["current_campaign"]["phase"] == "phase3.15", "wrong current phase")
        assert_true(payload["current_campaign"]["highest_step"] == 2, "wrong highest step")
        assert_true(
            any(
                merge["pr_number"] == 16
                and merge["branch"].startswith("femboy2112/campaign/phase3-14")
                for merge in payload["recent_merges"]
            ),
            "recent_merges does not contain PR #16 campaign branch",
        )

        write_mission(repo, "phase3.14", 3)
        code, state = call_state(module, ["json", "--repo", str(repo)])
        names = {signal["name"] for signal in state["drift_signals"]}
        assert_true(code == 2, f"mismatch drift should return 2, got {code}")
        assert_true("mission-phase-mismatch" in names, "missing mission-phase-mismatch")

        write_mission(repo, "phase3.15", 3)
        code, state = call_state(module, ["json", "--repo", str(repo)])
        names = {signal["name"] for signal in state["drift_signals"]}
        assert_true("mission-phase-mismatch" not in names, "unexpected mission-phase-mismatch")

        write_mission(repo, "phase3.15", 2)
        code, state = call_state(module, ["json", "--repo", str(repo)])
        names = {signal["name"] for signal in state["drift_signals"]}
        assert_true(code == 2, f"already-committed drift should return 2, got {code}")
        assert_true("next-step-already-committed" in names, "missing next-step-already-committed")

        code, state = call_state(module, ["json", "--repo", str(repo), "--git-log-limit", "1", "--no-mission"])
        assert_true(code == 0, f"limited log returned exit code {code}")
        assert_true(len(state["recent_steps"]) == 1, "git-log-limit 1 should show one recent step")
        assert_true(state["recent_steps"][0]["slug"] == "qux", "git-log-limit 1 did not show latest commit")

        non_git = Path(tmp) / "not-git"
        non_git.mkdir()
        args = module.parse_args(["json", "--repo", str(non_git)])
        code, state, error = module.collect_state(args)
        assert_true(code == 1, f"non-git repo should return 1, got {code}")
        assert_true(bool(error), "non-git repo should produce an error")


def main() -> int:
    try:
        run_tests()
    except Exception as exc:
        print(f"campaign_state_selftest: FAIL: {exc}", file=sys.stderr)
        return 1
    print("campaign_state_selftest: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
