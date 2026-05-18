"""Selftest for gate_runner.py using temporary shell gates only."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile


sys.dont_write_bytecode = True

REQUIRED_TOP_LEVEL_KEYS = {
    "repo",
    "started_at_utc",
    "finished_at_utc",
    "total_duration_s",
    "gates",
    "summary",
}


def load_gate_runner():
    here = pathlib.Path(__file__).resolve().parent
    module_path = here / "gate_runner.py"
    spec = importlib.util.spec_from_file_location("gate_runner_under_test", module_path)
    assert spec is not None, "failed to create module spec"
    assert spec.loader is not None, "failed to create module loader"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_script(path: pathlib.Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def run_main(module, repo: pathlib.Path, gates, extra_args: list[str]):
    previous_gates = module.GATES
    module.GATES = tuple(gates)
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = module.main(["--repo", str(repo), *extra_args])
    finally:
        module.GATES = previous_gates
    return code, stdout.getvalue(), stderr.getvalue()


def parse_json_output(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"JSON output did not parse: {exc}: {text!r}") from exc


def assert_duration_bounds(report: dict) -> None:
    for gate in report["gates"]:
        duration = gate["duration_s"]
        assert duration >= 0.0, f"negative duration for {gate['name']}: {duration}"
        assert duration < 60.0, f"unreasonable duration for {gate['name']}: {duration}"


def main() -> int:
    module = load_gate_runner()
    with tempfile.TemporaryDirectory(prefix="gate-runner-selftest-") as tmp:
        repo = pathlib.Path(tmp)
        pass_script = repo / "pass.sh"
        fail_script = repo / "fail.sh"
        sleep_script = repo / "sleep.sh"

        write_script(
            pass_script,
            "#!/usr/bin/env bash\nprintf 'ok\\n'\nexit 0\n",
        )
        write_script(
            fail_script,
            "#!/usr/bin/env bash\nprintf 'broken\\n' >&2\nexit 7\n",
        )
        write_script(
            sleep_script,
            "#!/usr/bin/env bash\nexec sleep 5\n",
        )

        pass_gate = ("pass", ["bash", str(pass_script)])
        pass_gate_2 = ("pass_two", ["bash", str(pass_script)])
        pass_gate_3 = ("pass_three", ["bash", str(pass_script)])
        fail_gate = ("fail", ["bash", str(fail_script)])
        sleep_gate = ("sleep", ["bash", str(sleep_script)])

        code, stdout, stderr = run_main(
            module,
            repo,
            [pass_gate, pass_gate_2, pass_gate_3],
            ["--json"],
        )
        assert code == 0, f"all-pass returned {code}, stderr={stderr!r}"
        report = parse_json_output(stdout)
        assert REQUIRED_TOP_LEVEL_KEYS <= set(report), "missing top-level JSON keys"
        assert report["summary"]["passed"] == 3, report
        assert report["summary"]["failed"] == 0, report
        assert_duration_bounds(report)

        code, stdout, stderr = run_main(
            module,
            repo,
            [pass_gate, fail_gate],
            ["--json"],
        )
        assert code == 1, f"mixed returned {code}, stderr={stderr!r}"
        report = parse_json_output(stdout)
        assert report["summary"]["passed"] == 1, report
        assert report["summary"]["failed"] == 1, report
        assert_duration_bounds(report)

        code, stdout, stderr = run_main(
            module,
            repo,
            [fail_gate, pass_gate],
            ["--json", "--bail"],
        )
        assert code == 1, f"bail returned {code}, stderr={stderr!r}"
        report = parse_json_output(stdout)
        assert len(report["gates"]) == 1, report
        assert report["gates"][0]["name"] == "fail", report
        assert_duration_bounds(report)

        code, stdout, stderr = run_main(
            module,
            repo,
            [sleep_gate],
            ["--json", "--timeout", "1"],
        )
        assert code == 1, f"timeout returned {code}, stderr={stderr!r}"
        report = parse_json_output(stdout)
        assert report["gates"][0]["status"] == "TIMEOUT", report
        assert report["summary"]["timed_out"] == 1, report
        assert_duration_bounds(report)

        code, stdout, stderr = run_main(
            module,
            repo,
            [pass_gate],
            ["--gates", "missing"],
        )
        assert code == 2, f"unknown gate returned {code}"
        assert "missing" in stderr, f"unknown gate stderr omitted name: {stderr!r}"
        assert stdout == "", f"unknown gate unexpectedly wrote stdout: {stdout!r}"

        code, stdout, stderr = run_main(
            module,
            repo,
            [pass_gate],
            ["--json", "--gates", "pass"],
        )
        assert code == 0, f"filtered JSON returned {code}, stderr={stderr!r}"
        report = parse_json_output(stdout)
        assert REQUIRED_TOP_LEVEL_KEYS <= set(report), "missing filtered JSON keys"
        assert [gate["name"] for gate in report["gates"]] == ["pass"], report
        assert_duration_bounds(report)

    print("gate_runner_selftest: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"gate_runner_selftest: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
