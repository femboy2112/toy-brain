"""Run the standard toy-brain validation gates with per-gate reporting.

CLI:
    python3 -m tools.claude_helpers.gate_runner --help
    python3 -m tools.claude_helpers.gate_runner [--repo PATH] [--gates LIST]
        [--bail] [--json] [--quiet] [--timeout SECONDS]

Exit codes:
    0 if every selected gate passes.
    1 if any selected gate fails, times out, or errors.
    2 for argument or configuration errors, such as an unknown gate name.

The default gate order is defined by the module-level ``GATES`` constant:
    catalog_counts     -> python3 -m tools.catalog counts
    citations_verify   -> python3 -m tools.citations verify
    import_audit       -> python3 -m tools.import_audit
    invariants_run     -> python3 -m brain.invariants run
    check_all          -> bash tools/check_all.sh

Selftests may replace ``GATES`` with another ordered sequence of
``(name, argv)`` pairs to exercise the runner without touching the live repo.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import pathlib
import subprocess
import sys
import time


GATES = (
    ("catalog_counts", ["python3", "-m", "tools.catalog", "counts"]),
    ("citations_verify", ["python3", "-m", "tools.citations", "verify"]),
    ("import_audit", ["python3", "-m", "tools.import_audit"]),
    ("invariants_run", ["python3", "-m", "brain.invariants", "run"]),
    ("check_all", ["bash", "tools/check_all.sh"]),
)

TAIL_LINES = 40
JSON_TAIL_CHARS = 800
NOTE_CHARS = 80


@dataclasses.dataclass(frozen=True)
class GateResult:
    name: str
    argv: list[str]
    status: str
    returncode: int | None
    duration_s: float
    stdout: str
    stderr: str

    @property
    def stdout_tail(self) -> str:
        return tail_chars(self.stdout, JSON_TAIL_CHARS)

    @property
    def stderr_tail(self) -> str:
        return tail_chars(self.stderr, JSON_TAIL_CHARS)

    def to_json_obj(self) -> dict[str, object]:
        return {
            "name": self.name,
            "argv": list(self.argv),
            "status": self.status,
            "returncode": self.returncode,
            "duration_s": self.duration_s,
            "stdout_len": len(self.stdout),
            "stderr_len": len(self.stderr),
            "stderr_tail": self.stderr_tail,
            "stdout_tail": self.stdout_tail,
        }


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def iso_utc(value: datetime.datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def tail_chars(text: str, limit: int) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[-limit:]


def tail_lines(text: str, limit: int) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    lines = stripped.splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:NOTE_CHARS]
    return ""


def normalize_gates(gates: object) -> list[tuple[str, list[str]]]:
    normalized: list[tuple[str, list[str]]] = []
    for item in gates:  # type: ignore[union-attr]
        try:
            name, argv = item
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid gate definition: {item!r}") from exc
        if not isinstance(name, str) or not name:
            raise ValueError(f"invalid gate name: {name!r}")
        if not isinstance(argv, (list, tuple)) or not argv:
            raise ValueError(f"invalid argv for gate {name!r}: {argv!r}")
        argv_list = [str(part) for part in argv]
        normalized.append((name, argv_list))
    return normalized


def select_gates(
    gate_defs: list[tuple[str, list[str]]], gate_list: str | None
) -> list[tuple[str, list[str]]]:
    if not gate_list:
        return gate_defs

    by_name = {name: argv for name, argv in gate_defs}
    selected: list[tuple[str, list[str]]] = []
    for raw_name in gate_list.split(","):
        name = raw_name.strip()
        if not name:
            continue
        if name not in by_name:
            known = ", ".join(name for name, _argv in gate_defs)
            raise ValueError(f"unknown gate {name!r}; known gates: {known}")
        selected.append((name, list(by_name[name])))

    if not selected:
        raise ValueError("--gates did not name any gates")
    return selected


def run_one_gate(
    repo: pathlib.Path, name: str, argv: list[str], timeout: float
) -> GateResult:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        stdout = coerce_text(exc.stdout)
        stderr = coerce_text(exc.stderr)
        timeout_note = f"timed out after {timeout:g} seconds"
        if stderr.strip():
            stderr = f"{stderr.rstrip()}\n{timeout_note}\n"
        else:
            stderr = f"{timeout_note}\n"
        return GateResult(
            name=name,
            argv=list(argv),
            status="TIMEOUT",
            returncode=None,
            duration_s=round(duration, 3),
            stdout=stdout,
            stderr=stderr,
        )
    except OSError as exc:
        duration = time.monotonic() - start
        return GateResult(
            name=name,
            argv=list(argv),
            status="ERROR",
            returncode=None,
            duration_s=round(duration, 3),
            stdout="",
            stderr=str(exc),
        )

    duration = time.monotonic() - start
    status = "PASS" if completed.returncode == 0 else "FAIL"
    return GateResult(
        name=name,
        argv=list(argv),
        status=status,
        returncode=completed.returncode,
        duration_s=round(duration, 3),
        stdout=coerce_text(completed.stdout),
        stderr=coerce_text(completed.stderr),
    )


def run_gates(
    repo: pathlib.Path,
    gates: list[tuple[str, list[str]]],
    timeout: float,
    bail: bool,
    quiet: bool,
) -> list[GateResult]:
    results: list[GateResult] = []
    for name, argv in gates:
        if not quiet:
            print(f"=== {name} ===", flush=True)

        result = run_one_gate(repo=repo, name=name, argv=argv, timeout=timeout)
        results.append(result)

        if not quiet:
            stdout_tail = tail_lines(result.stdout, TAIL_LINES)
            if stdout_tail:
                print(stdout_tail)
            print(
                f"{result.status} {result.name} "
                f"duration_s={result.duration_s:.3f}"
            )

        if bail and result.status != "PASS":
            break

    return results


def summarize(results: list[GateResult]) -> dict[str, int]:
    passed = sum(1 for result in results if result.status == "PASS")
    failed = sum(1 for result in results if result.status == "FAIL")
    timed_out = sum(1 for result in results if result.status == "TIMEOUT")
    errors = sum(1 for result in results if result.status == "ERROR")
    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "timed_out": timed_out,
        "errors": errors,
    }


def build_report(
    repo: pathlib.Path,
    started_at: datetime.datetime,
    finished_at: datetime.datetime,
    results: list[GateResult],
) -> dict[str, object]:
    return {
        "repo": str(repo),
        "started_at_utc": iso_utc(started_at),
        "finished_at_utc": iso_utc(finished_at),
        "total_duration_s": round(
            (finished_at - started_at).total_seconds(), 3
        ),
        "gates": [result.to_json_obj() for result in results],
        "summary": summarize(results),
    }


def print_summary_table(results: list[GateResult]) -> None:
    print("name | status | duration_s | notes")
    print("--- | --- | ---: | ---")
    for result in results:
        note = ""
        if result.status != "PASS":
            note = first_non_empty_line(result.stderr_tail)
        print(
            f"{result.name} | {result.status} | "
            f"{result.duration_s:.3f} | {note}"
        )


def failure_count(summary: dict[str, int]) -> int:
    return summary["failed"] + summary["timed_out"] + summary["errors"]


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run toy-brain validation gates with timing and summaries."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="repository path to run gates in (default: current directory)",
    )
    parser.add_argument(
        "--gates",
        help="comma-separated gate names to run; default is all gates",
    )
    parser.add_argument(
        "--bail",
        action="store_true",
        help="stop after the first failing, timed-out, or errored gate",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of text output",
    )
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="suppress per-gate live headers; still print final text summary",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="per-gate timeout in seconds (default: 600)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.timeout <= 0:
        print("--timeout must be greater than zero", file=sys.stderr)
        return 2

    repo = pathlib.Path(args.repo).expanduser().resolve()
    if not repo.exists():
        print(f"--repo path does not exist: {repo}", file=sys.stderr)
        return 2
    if not repo.is_dir():
        print(f"--repo path is not a directory: {repo}", file=sys.stderr)
        return 2

    try:
        gate_defs = normalize_gates(GATES)
        selected_gates = select_gates(gate_defs, args.gates)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    started_at = utc_now()
    results = run_gates(
        repo=repo,
        gates=selected_gates,
        timeout=args.timeout,
        bail=args.bail,
        quiet=args.quiet or args.json,
    )
    finished_at = utc_now()
    report = build_report(repo, started_at, finished_at, results)
    summary = report["summary"]
    failures = failure_count(summary)  # type: ignore[arg-type]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_summary_table(results)
        if failures:
            print(f"gate_runner: FAIL ({failures}/{summary['total']} failed)")  # type: ignore[index]
        else:
            print("gate_runner: PASS")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
