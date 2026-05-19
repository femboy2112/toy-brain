"""tools/propose_next_campaign.py — ladder selector + roadmap-stub emitter.

Phase 3.34+ tool. Runs the developmental progression profile projector
on the current probe outputs, picks the next consolidation target via
the ladder, and emits a roadmap stub the operator can use to author a
Phase 3.35+ consolidation campaign.

Pure stdlib. Deterministic. No I/O beyond stdout and (optional)
exclusion-flag parsing.

Usage:
    python3 -m tools.propose_next_campaign
    python3 -m tools.propose_next_campaign --format roadmap-stub
    python3 -m tools.propose_next_campaign --format json
    python3 -m tools.propose_next_campaign --exclude-axis AXIS_NAME
    python3 -m tools.propose_next_campaign --exclude-mechanism MECH_NAME

The roadmap-stub output is a Markdown document with the
NextProgressionTarget rendered as fillable fields. Pipe it into a
file and use it with docs/campaigns/phase3_35/PHASE3_35_TEMPLATE_INSTRUCTIONS.md
to author a Phase 3.35+ roadmap.

This module imports brain.development.developmental_progression_profile
and brain.development.probe_report_protocol at runtime; it does NOT
import them at module load time, so the tool can be run in repo states
where those modules don't yet exist (Phase 3.32 / 3.33).
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Propose the next developmental consolidation campaign."
    )
    parser.add_argument(
        "--format",
        choices=("roadmap-stub", "json"),
        default="roadmap-stub",
        help="Output format.",
    )
    parser.add_argument(
        "--exclude-axis",
        action="append",
        default=[],
        help="Exclude an axis from consideration (may be specified "
             "multiple times). Used when the proposer's first choice "
             "is unsuitable for non-deterministic reasons (e.g., the "
             "operator wants to consolidate a different axis first).",
    )
    parser.add_argument(
        "--exclude-mechanism",
        action="append",
        default=[],
        help="Exclude a recommended mechanism (may be specified "
             "multiple times). Useful if a mechanism is infeasible "
             "(e.g., the operator wants to avoid threshold adjustments).",
    )
    args = parser.parse_args(argv)

    try:
        from brain.development.probe_report_protocol import (
            collect_probe_reports,
        )
        from brain.development.developmental_progression_profile import (
            DevelopmentalAxis,
            DevelopmentalBand,
            ProgressionMechanism,
            project_developmental_progression_profile,
            select_next_progression_target,
        )
    except ImportError as exc:
        print(
            "ERROR: brain.development.developmental_progression_profile "
            "is not importable. This tool requires Phase 3.34 to have "
            "landed. Details:",
            file=sys.stderr,
        )
        print(f"  {exc}", file=sys.stderr)
        return 1

    excluded_axes = {
        DevelopmentalAxis(name) for name in args.exclude_axis
    }
    excluded_mechanisms = {
        ProgressionMechanism(name) for name in args.exclude_mechanism
    }

    reports = collect_probe_reports()
    profile = project_developmental_progression_profile(reports)
    target = select_next_progression_target(profile)

    # Apply exclusion rules: if the recommended target is excluded,
    # re-select by simulating a higher band on the excluded axis.
    while (
        target.axis in excluded_axes
        or target.recommended_mechanism in excluded_mechanisms
    ):
        target = _reselect_with_exclusions(
            profile, target, excluded_axes, excluded_mechanisms,
            DevelopmentalAxis, DevelopmentalBand, ProgressionMechanism,
        )
        if target is None:
            print(
                "No eligible axis remains after applying exclusions.",
                file=sys.stderr,
            )
            return 2

    if args.format == "json":
        out = {
            "profile_digest": profile.profile_digest_hex16,
            "forbidden_audit_clean": profile.forbidden_audit_clean,
            "assignments": [
                {
                    "axis": a.axis.value,
                    "band": a.band.value,
                    "rationale": a.rationale_summary,
                    "cited_rows": list(a.cited_evidence_rows),
                }
                for a in profile.assignments
            ],
            "next_target": {
                "axis": target.axis.value,
                "current_band": target.current_band.value,
                "target_band": target.target_band.value,
                "prerequisites_satisfied": [
                    a.value for a in target.prerequisites_satisfied
                ],
                "prerequisites_missing": [
                    a.value for a in target.prerequisites_missing
                ],
                "recommended_mechanism": target.recommended_mechanism.value,
                "rationale": target.rationale_summary,
                "cited_rows": list(target.cited_evidence_rows),
            },
        }
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(_render_roadmap_stub(profile, target))
    return 0


def _reselect_with_exclusions(
    profile, current_target,
    excluded_axes, excluded_mechanisms,
    DevelopmentalAxis, DevelopmentalBand, ProgressionMechanism,
):
    """Re-select a target excluding the current one.

    Implementation: walk the remaining axes in order of (band, name),
    constructing a NextProgressionTarget for each, until one passes
    the exclusion filter. Returns None if none qualify.
    """
    from brain.development.developmental_progression_profile import (
        select_next_progression_target,
    )

    # Build a fake profile where the excluded axes are at the top band
    # (B07_GENERALIZES), so the selector will skip them.
    from dataclasses import replace
    masked_assignments = []
    for a in profile.assignments:
        if a.axis in excluded_axes:
            masked_assignments.append(
                replace(a, band=DevelopmentalBand.B07_GENERALIZES)
            )
        else:
            masked_assignments.append(a)
    masked_profile = replace(profile, assignments=tuple(masked_assignments))
    new_target = select_next_progression_target(masked_profile)
    if new_target.recommended_mechanism in excluded_mechanisms:
        # Could not satisfy exclusion-mechanism; give up.
        return None
    if new_target.axis == current_target.axis:
        # Selector ignored our masking somehow; give up.
        return None
    return new_target


def _render_roadmap_stub(profile, target) -> str:
    """Render a NextProgressionTarget as a Markdown roadmap stub.

    The format matches what
    docs/campaigns/phase3_35/PHASE3_35_TEMPLATE_INSTRUCTIONS.md
    expects.
    """
    lines = []
    lines.append("# NextProgressionTarget proposal (auto-generated)")
    lines.append("")
    lines.append(f"profile_digest:             {profile.profile_digest_hex16}")
    lines.append(f"forbidden_audit_clean:      {profile.forbidden_audit_clean}")
    lines.append("")
    lines.append("## Current profile")
    lines.append("")
    for a in profile.assignments:
        lines.append(f"  {a.axis.value:<32}  {a.band.value}")
    lines.append("")
    lines.append("## Recommended target")
    lines.append("")
    lines.append(f"axis:                       {target.axis.value}")
    lines.append(f"current_band:               {target.current_band.value}")
    lines.append(f"target_band:                {target.target_band.value}")
    if target.prerequisites_satisfied:
        sat = ", ".join(a.value for a in target.prerequisites_satisfied)
        lines.append(f"prerequisites_satisfied:    {sat}")
    else:
        lines.append("prerequisites_satisfied:    (none)")
    if target.prerequisites_missing:
        miss = ", ".join(a.value for a in target.prerequisites_missing)
        lines.append(f"prerequisites_missing:      {miss}")
    else:
        lines.append("prerequisites_missing:      (none)")
    lines.append(f"recommended_mechanism:      "
                 f"{target.recommended_mechanism.value}")
    lines.append("")
    lines.append("## Rationale")
    lines.append("")
    lines.append(target.rationale_summary)
    lines.append("")
    lines.append("## Cited evidence rows")
    lines.append("")
    for row in target.cited_evidence_rows:
        lines.append(f"  - {row}")
    lines.append("")
    lines.append("## Suggested next steps")
    lines.append("")
    lines.append(
        "1. Read docs/campaigns/phase3_35/PHASE3_35_TEMPLATE_INSTRUCTIONS.md"
    )
    lines.append("2. Copy PHASE3_35_FIRST_CONSOLIDATION_TEMPLATE.md to:")
    lines.append(
        f"   PHASE3_<NN>_{target.axis.value}_CONSOLIDATION_ROADMAP.md"
    )
    lines.append("3. Fill in the <<<...>>> placeholders using this proposal.")
    lines.append("4. Author the mechanism-specific design section.")
    lines.append("5. Drop in the roadmap; update CURRENT_MISSION.md and")
    lines.append("   CURRENT_CAMPAIGN.md; run /go.")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
