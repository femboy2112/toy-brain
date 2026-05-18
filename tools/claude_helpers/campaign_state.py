#!/usr/bin/env python3
"""Report campaign progress from git history and mission files.

CLI:
  python3 -m tools.claude_helpers.campaign_state --help
  python3 -m tools.claude_helpers.campaign_state summary [--repo PATH] [--git-log-limit N]
  python3 -m tools.claude_helpers.campaign_state json [--repo PATH] [--git-log-limit N]

The tool is read-only. It scans recent git commit subjects for
``phase<major>.<minor> step<N>: <slug>`` commits and campaign merge subjects,
optionally reads CURRENT_MISSION.md and CURRENT_CAMPAIGN.md, and emits drift
signals when mission files disagree with committed campaign state.

Exit codes:
  0 success
  1 repository is not a git repo or git is unavailable
  2 blocking drift signals were found
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import sys

EXIT_SUCCESS = 0
EXIT_REPO_OR_GIT_ERROR = 1
EXIT_BLOCKING_DRIFT = 2

STEP_RE = re.compile(r"^phase(\d+)\.(\d+)\s+step(\d+):\s+(.*)$")
MERGE_RE = re.compile(r"^Merge pull request #(\d+) from (\S+)$")
NEXT_STEP_RE = re.compile(r"Next eligible step:\s*(.*)", re.IGNORECASE)
STATUS_RE = re.compile(r"Phase\s+\S+\s+Step\s+\d+\s+status:\s*.*", re.IGNORECASE)
CATALOG_RE = re.compile(r"Catalog:\s*v\S+", re.IGNORECASE)
PHASE_RE = re.compile(r"\bphase(\d+)\.(\d+)\b", re.IGNORECASE)
STEP_NUM_RE = re.compile(r"\bStep\s+(\d+)\b", re.IGNORECASE)
PREFERRED_BRANCH_RE = re.compile(r"^campaign/\S+", re.MULTILINE)


@dataclass(frozen=True)
class StepCommit:
    commit: str
    subject: str
    major: int
    minor: int
    step: int
    slug: str
    order: int

    @property
    def phase(self) -> str:
        return f"phase{self.major}.{self.minor}"

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "major": self.major,
            "minor": self.minor,
            "step": self.step,
            "slug": self.slug,
            "commit": self.commit,
        }


@dataclass(frozen=True)
class MergeCommit:
    commit: str
    subject: str
    pr_number: int
    branch: str
    order: int

    def to_dict(self) -> dict[str, object]:
        return {
            "pr_number": self.pr_number,
            "branch": self.branch,
            "commit": self.commit,
        }


@dataclass
class PhaseView:
    phase: str
    major: int
    minor: int
    steps: list[int]
    highest_step: int
    highest_slug: str
    highest_commit: str
    most_recent_order: int

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "major": self.major,
            "minor": self.minor,
            "steps": self.steps,
            "highest_step": self.highest_step,
            "highest_slug": self.highest_slug,
            "highest_commit": self.highest_commit,
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize toy-brain campaign state from git log and mission files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--repo", default=".", help="Repository path; must contain .git")
        subparser.add_argument(
            "--git-log-limit",
            type=int,
            default=300,
            help="Number of commits to scan",
        )
        subparser.add_argument("--phase", help="Optional phase filter, e.g. phase3.15")
        subparser.add_argument(
            "--no-mission",
            action="store_true",
            help="Skip CURRENT_MISSION.md and CURRENT_CAMPAIGN.md reads",
        )

    add_common(subparsers.add_parser("summary", help="Print a human-readable report"))
    add_common(subparsers.add_parser("json", help="Print a JSON report"))
    return parser.parse_args(argv)


def normalize_repo(repo_arg: str) -> Path:
    return Path(repo_arg).expanduser().resolve()

def validate_repo(repo: Path) -> bool:
    return repo.exists() and (repo / ".git").exists()

def run_git_log(repo: Path, limit: int) -> tuple[int, list[str], str]:
    if limit <= 0:
        return 0, [], ""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "log", "--pretty=format:%H\t%s", f"-{limit}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return EXIT_REPO_OR_GIT_ERROR, [], str(exc)
    if proc.returncode != 0:
        return EXIT_REPO_OR_GIT_ERROR, [], (proc.stderr or proc.stdout).strip()
    return EXIT_SUCCESS, proc.stdout.splitlines(), ""

def parse_git_lines(lines: list[str]) -> tuple[list[StepCommit], list[MergeCommit]]:
    steps: list[StepCommit] = []
    merges: list[MergeCommit] = []
    for order, line in enumerate(lines):
        if "\t" not in line:
            continue
        commit, subject = line.split("\t", 1)
        step_match = STEP_RE.match(subject)
        if step_match:
            major, minor, step, slug = step_match.groups()
            steps.append(
                StepCommit(
                    commit=commit,
                    subject=subject,
                    major=int(major),
                    minor=int(minor),
                    step=int(step),
                    slug=slug,
                    order=order,
                )
            )
            continue
        merge_match = MERGE_RE.match(subject)
        if merge_match:
            pr_number, branch = merge_match.groups()
            merges.append(
                MergeCommit(
                    commit=commit,
                    subject=subject,
                    pr_number=int(pr_number),
                    branch=branch,
                    order=order,
                )
            )
    return steps, merges

def build_phase_views(steps: list[StepCommit]) -> dict[str, PhaseView]:
    grouped: dict[str, list[StepCommit]] = {}
    for step in steps:
        grouped.setdefault(step.phase, []).append(step)

    views: dict[str, PhaseView] = {}
    for phase, phase_steps in grouped.items():
        highest = max(phase_steps, key=lambda item: (item.step, -item.order))
        most_recent = min(phase_steps, key=lambda item: item.order)
        views[phase] = PhaseView(
            phase=phase,
            major=highest.major,
            minor=highest.minor,
            steps=sorted({item.step for item in phase_steps}),
            highest_step=highest.step,
            highest_slug=highest.slug,
            highest_commit=highest.commit,
            most_recent_order=most_recent.order,
        )
    return views

def current_campaign(phase_views: dict[str, PhaseView]) -> PhaseView | None:
    if not phase_views:
        return None
    return min(phase_views.values(), key=lambda view: view.most_recent_order)

def is_campaign_branch(branch: str) -> bool:
    return branch.startswith("campaign/") or "/campaign/" in branch

def last_merged_campaign(merges: list[MergeCommit]) -> MergeCommit | None:
    for merge in merges:
        if is_campaign_branch(merge.branch):
            return merge
    return None

def first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0).strip() if match else None

def extract_phase(text: str | None) -> str | None:
    if not text:
        return None
    match = PHASE_RE.search(text)
    if not match:
        return None
    return f"phase{int(match.group(1))}.{int(match.group(2))}"

def extract_step_number(text: str | None) -> int | None:
    if not text:
        return None
    match = STEP_NUM_RE.search(text)
    return int(match.group(1)) if match else None

def read_mission_like(path: Path) -> dict[str, object]:
    info: dict[str, object] = {
        "path": path.name,
        "present": path.exists(),
        "next_eligible_step": None,
        "next_eligible_step_number": None,
        "status_lines": [],
        "catalog": None,
        "phase": None,
    }
    if not path.exists():
        return info
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        info["read_error"] = str(exc)
        return info

    next_match = NEXT_STEP_RE.search(text)
    if next_match:
        line = next_match.group(0).strip()
        info["next_eligible_step"] = line
        info["next_eligible_step_number"] = extract_step_number(line)
        info["phase"] = extract_phase(line)

    statuses = [match.group(0).strip() for match in STATUS_RE.finditer(text)]
    info["status_lines"] = statuses
    if not info["phase"]:
        for status in statuses:
            phase = extract_phase(status)
            if phase:
                info["phase"] = phase
                break

    catalog = first_match(CATALOG_RE, text)
    if catalog:
        info["catalog"] = catalog

    return info

def read_campaign_file(path: Path) -> dict[str, object]:
    info = read_mission_like(path)
    info["preferred_branch"] = None
    if not path.exists():
        return info
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return info
    branch = first_match(PREFERRED_BRANCH_RE, text)
    if branch:
        info["preferred_branch"] = branch
    return info

def roadmap_phase(path: Path) -> str | None:
    match = re.match(r"PHASE3_(\d+)_.*_ROADMAP\.md$", path.name)
    if not match:
        return None
    return f"phase3.{int(match.group(1))}"

def drift_signals(
    repo: Path,
    current: PhaseView | None,
    phase_views: dict[str, PhaseView],
    mission: dict[str, object],
) -> list[dict[str, object]]:
    signals: list[dict[str, object]] = []
    current_phase = current.phase if current else None
    mission_phase = mission.get("phase")

    if mission_phase and current_phase and mission_phase != current_phase:
        signals.append(
            {
                "name": "mission-phase-mismatch",
                "severity": "blocking",
                "message": f"CURRENT_MISSION.md references {mission_phase}; git current campaign is {current_phase}",
            }
        )

    next_step = mission.get("next_eligible_step_number")
    check_phase = mission_phase or current_phase
    if next_step is not None and check_phase in phase_views:
        highest = phase_views[check_phase].highest_step
        if next_step <= highest:
            signals.append(
                {
                    "name": "next-step-already-committed",
                    "severity": "blocking",
                    "message": f"{check_phase} next eligible step {next_step} is <= committed highest step {highest}",
                }
            )

    if current_phase:
        stale = sorted(
            {
                phase
                for path in repo.glob("PHASE3_*_ROADMAP.md")
                for phase in [roadmap_phase(path)]
                if phase and phase != current_phase
            }
        )
        if stale:
            signals.append(
                {
                    "name": "stale-roadmap",
                    "severity": "info",
                    "message": "Roadmap files for other phases are present: " + ", ".join(stale),
                }
            )
    return signals

def collect_state(args: argparse.Namespace) -> tuple[int, dict[str, object], str]:
    repo = normalize_repo(args.repo)
    if not validate_repo(repo):
        return EXIT_REPO_OR_GIT_ERROR, {}, f"{repo} is not a git repository"

    git_status, lines, git_error = run_git_log(repo, args.git_log_limit)
    if git_status != EXIT_SUCCESS:
        return git_status, {}, git_error or "git log failed"

    steps, merges = parse_git_lines(lines)
    phase_views = build_phase_views(steps)
    current = current_campaign(phase_views)
    last_merge = last_merged_campaign(merges)

    mission = {
        "path": "CURRENT_MISSION.md",
        "present": False,
        "next_eligible_step": None,
        "next_eligible_step_number": None,
        "status_lines": [],
        "catalog": None,
        "phase": None,
    }
    campaign = {
        "path": "CURRENT_CAMPAIGN.md",
        "present": False,
        "next_eligible_step": None,
        "next_eligible_step_number": None,
        "status_lines": [],
        "catalog": None,
        "phase": None,
        "preferred_branch": None,
    }
    if not args.no_mission:
        mission = read_mission_like(repo / "CURRENT_MISSION.md")
        campaign = read_campaign_file(repo / "CURRENT_CAMPAIGN.md")

    selected_steps = [step for step in steps if not args.phase or step.phase == args.phase]
    selected_merges = merges
    signals = drift_signals(repo, current, phase_views, mission)
    blocking = any(signal["severity"] == "blocking" for signal in signals)

    state = {
        "current_campaign": current.to_dict() if current else None,
        "last_merged_campaign": last_merge.to_dict() if last_merge else None,
        "recent_steps": [step.to_dict() for step in selected_steps[:12]],
        "recent_merges": [merge.to_dict() for merge in selected_merges[:5]],
        "mission": mission,
        "campaign_file": campaign,
        "drift_signals": signals,
    }
    return EXIT_BLOCKING_DRIFT if blocking else EXIT_SUCCESS, state, ""

def format_mission(info: dict[str, object]) -> list[str]:
    if not info.get("present"):
        return [f"{info.get('path', 'file')}: not present"]
    lines = [f"{info.get('path', 'file')}: present"]
    if info.get("phase"):
        lines.append(f"phase: {info['phase']}")
    if info.get("next_eligible_step"):
        lines.append(f"next eligible: {info['next_eligible_step']}")
    if info.get("catalog"):
        lines.append(f"catalog: {info['catalog']}")
    if info.get("preferred_branch"):
        lines.append(f"preferred branch: {info['preferred_branch']}")
    for status in info.get("status_lines", []):
        lines.append(f"status: {status}")
    if info.get("read_error"):
        lines.append(f"read error: {info['read_error']}")
    return lines

def format_summary(state: dict[str, object]) -> str:
    chunks: list[str] = []
    current = state["current_campaign"]
    chunks.append("Current campaign")
    if current:
        chunks.append(
            f"{current['phase']} highest step {current['highest_step']}: {current['highest_slug']} "
            f"({current['highest_commit'][:12]})"
        )
        chunks.append("steps seen: " + ", ".join(str(step) for step in current["steps"]))
    else:
        chunks.append("none")

    chunks.append("")
    chunks.append("Recent steps (last 12)")
    if state["recent_steps"]:
        for step in state["recent_steps"]:
            chunks.append(
                f"{step['commit'][:12]} {step['phase']} step{step['step']}: {step['slug']}"
            )
    else:
        chunks.append("none")

    chunks.append("")
    chunks.append("Recent campaign merges (last 5)")
    if state["recent_merges"]:
        for merge in state["recent_merges"]:
            chunks.append(
                f"{merge['commit'][:12]} PR #{merge['pr_number']} from {merge['branch']}"
            )
    else:
        chunks.append("none")

    chunks.append("")
    chunks.append("Mission file")
    chunks.extend(format_mission(state["mission"]))

    chunks.append("")
    chunks.append("Campaign file")
    chunks.extend(format_mission(state["campaign_file"]))

    chunks.append("")
    chunks.append("Drift signals")
    if state["drift_signals"]:
        for signal in state["drift_signals"]:
            chunks.append(f"{signal['severity']}: {signal['name']} - {signal['message']}")
    else:
        chunks.append("none")
    return "\n".join(chunks) + "\n"

def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    exit_code, state, error = collect_state(args)
    if error:
        print(f"campaign_state: {error}", file=sys.stderr)
        return exit_code
    if args.command == "json":
        print(json.dumps(state, indent=2))
    else:
        print(format_summary(state), end="")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
