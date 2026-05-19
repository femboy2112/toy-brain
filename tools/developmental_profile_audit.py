"""tools/developmental_profile_audit.py — probe strictness audit script.

Phase 3.33 Step 4 helper. Mechanically identifies graceful-pass
acceptance patterns in probe runner modules so the auditor (human or
agent) doesn't have to read every line.

Usage:
    python3 -m tools.developmental_profile_audit --audit-only \\
        --probes proto_speech_acquisition,curriculum_consolidation_probe,...

    python3 -m tools.developmental_profile_audit --audit-only \\
        --probes proto_speech_acquisition \\
        --format markdown

    python3 -m tools.developmental_profile_audit --audit-only \\
        --probes proto_speech_acquisition \\
        --format json

The script reads probe module source and identifies:

1. Lines matching "disposition not in (...)" or "disposition in (...)"
   — these are graceful-pass acceptance candidates.
2. Lines matching "status = ProbeStatus.PASS" preceded by such an
   acceptance — these are the PASS branches.
3. The disposition set in each acceptance.

It does NOT decide the canonical disposition or author the strict
counter. Those decisions require human (or agent) review of the
surrounding context.

The script is pure Python with no third-party dependencies. It
operates on the probe module source text, not on imported modules.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


_PROBE_MODULE_PATH = "brain/development/{module}.py"

_DISPOSITION_PATTERN = re.compile(
    r"\bdisposition\s+(?:not\s+)?in\s+\(",
    re.IGNORECASE,
)

_DISPOSITION_IS_PATTERN = re.compile(
    r"\bdisposition\s+is\s+(?:not\s+)?\b",
    re.IGNORECASE,
)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit probe modules for graceful-pass patterns."
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="Run audit only; do not modify any module.",
    )
    parser.add_argument(
        "--probes",
        required=True,
        help="Comma-separated probe module names (without .py).",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repo root (default: current dir).",
    )
    args = parser.parse_args(argv)

    if not args.audit_only:
        print(
            "ERROR: --audit-only is required (this tool is read-only).",
            file=sys.stderr,
        )
        return 2

    findings_by_probe: dict[str, list[dict]] = {}
    for probe in args.probes.split(","):
        probe = probe.strip()
        path = Path(args.repo_root) / _PROBE_MODULE_PATH.format(module=probe)
        if not path.exists():
            findings_by_probe[probe] = [{
                "kind": "module_missing",
                "path": str(path),
            }]
            continue
        findings_by_probe[probe] = audit_probe_module(path)

    if args.format == "json":
        print(json.dumps(findings_by_probe, indent=2, sort_keys=True))
    else:
        print(_render_markdown(findings_by_probe))

    return 0


def audit_probe_module(path: Path) -> list[dict]:
    """Find every graceful-pass acceptance candidate in a probe module."""
    findings: list[dict] = []
    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")

    for i, line in enumerate(lines, start=1):
        # Skip comments and docstrings (rough heuristic).
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith(('"""', "'''")):
            continue

        # Check for graceful-pass pattern.
        match = _DISPOSITION_PATTERN.search(line)
        if match:
            # Collect the disposition tuple by reading subsequent lines
            # until we hit the closing paren.
            dispositions = _collect_disposition_tuple(lines, i - 1)
            findings.append({
                "kind": "graceful_pass_candidate",
                "line": i,
                "source_line": line.rstrip(),
                "dispositions": dispositions,
                "context_before": _get_context(lines, i - 1, -5),
                "context_after": _get_context(lines, i - 1, +5),
            })

        # Check for strict pattern.
        match_is = _DISPOSITION_IS_PATTERN.search(line)
        if match_is:
            findings.append({
                "kind": "strict_pattern",
                "line": i,
                "source_line": line.rstrip(),
                "context_before": _get_context(lines, i - 1, -3),
                "context_after": _get_context(lines, i - 1, +3),
            })

    return findings


def _collect_disposition_tuple(lines: list[str], start_index: int) -> list[str]:
    """Collect dispositions from a `disposition (not) in ( ... )` tuple.

    Returns the disposition names as strings (without enum qualifier).
    """
    text_chunks: list[str] = []
    paren_depth = 0
    started = False
    for line in lines[start_index : start_index + 30]:
        for ch in line:
            if ch == "(":
                paren_depth += 1
                started = True
            elif ch == ")":
                paren_depth -= 1
                if paren_depth == 0 and started:
                    text_chunks.append(line)
                    text = " ".join(text_chunks)
                    return _parse_dispositions(text)
            elif started and paren_depth > 0:
                pass
        if started:
            text_chunks.append(line)
        if paren_depth == 0 and started:
            break
    return _parse_dispositions(" ".join(text_chunks))


def _parse_dispositions(text: str) -> list[str]:
    """Parse disposition names from a tuple-literal text fragment."""
    # Match `Foo.BAR` patterns and take BAR.
    tokens = re.findall(r"\b[A-Z][a-zA-Z_]*\.([A-Z_]+)\b", text)
    return list(dict.fromkeys(tokens))  # dedupe preserving order


def _get_context(lines: list[str], index: int, delta: int) -> list[str]:
    """Return `abs(delta)` lines before (delta<0) or after (delta>0) `index`."""
    if delta < 0:
        start = max(0, index + delta)
        return [
            f"{i+1}: {lines[i].rstrip()}"
            for i in range(start, index)
        ]
    else:
        end = min(len(lines), index + delta + 1)
        return [
            f"{i+1}: {lines[i].rstrip()}"
            for i in range(index + 1, end)
        ]


def _render_markdown(findings_by_probe: dict[str, list[dict]]) -> str:
    lines = []
    lines.append("# Probe Strictness Audit — Raw Findings")
    lines.append("")
    lines.append(
        "This is the raw output of `tools/developmental_profile_audit "
        "--audit-only`. Every entry below is a CANDIDATE; manual review "
        "is required to confirm graceful-pass status and to identify the "
        "canonical disposition."
    )
    lines.append("")

    for probe, findings in findings_by_probe.items():
        lines.append(f"## {probe}")
        lines.append("")
        if not findings:
            lines.append("(no graceful-pass candidates found)")
            lines.append("")
            continue

        for f in findings:
            if f.get("kind") == "module_missing":
                lines.append(f"⚠ module missing: `{f['path']}`")
                lines.append("")
                continue

            if f["kind"] == "graceful_pass_candidate":
                lines.append(f"### Line {f['line']} — graceful-pass candidate")
                lines.append("")
                lines.append("```python")
                for ctx in f.get("context_before", []):
                    lines.append(ctx)
                lines.append(f"{f['line']}: {f['source_line']}")
                for ctx in f.get("context_after", []):
                    lines.append(ctx)
                lines.append("```")
                lines.append("")
                lines.append(
                    f"**Dispositions detected:** {', '.join(f['dispositions']) or '(none parsed)'}"
                )
                lines.append("")
                lines.append("**Reviewer action:**")
                lines.append("")
                lines.append(
                    "- Confirm: is this an ACCEPTANCE clause (PASS path)?"
                )
                lines.append("- Identify the canonical disposition.")
                lines.append("- Author the proposed strict counter name.")
                lines.append("")
            elif f["kind"] == "strict_pattern":
                lines.append(f"### Line {f['line']} — strict pattern (no action)")
                lines.append("")
                lines.append("```python")
                for ctx in f.get("context_before", []):
                    lines.append(ctx)
                lines.append(f"{f['line']}: {f['source_line']}")
                for ctx in f.get("context_after", []):
                    lines.append(ctx)
                lines.append("```")
                lines.append("")
                lines.append(
                    "(This is a strict disposition check, not a graceful "
                    "acceptance. No action needed.)"
                )
                lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
