# PHASE3_32_MAINLINE_RECONCILIATION_ROADMAP.md — Phase 3.32

## One-paragraph thesis

Phase 3.32 reconciles the stacked PR chain (PR #24–#33, currently
spanning Phase 3.19 through Phase 3.31) into mainline, and lands one
new pure-Python module `brain/development/probe_report_protocol.py`
that defines a `typing.Protocol` every existing probe report already
satisfies by name. This unblocks Phase 3.34's profile projector from
having to import five distinct probe modules just to read their
report dataclasses. No probe behavior changes. No probe module is
modified. The protocol is a header-only declaration with no runtime
effect except enabling type-checked consumers.

## Branch

```text
campaign/phase3-32-mainline-reconciliation
```

Base (at recovery time): `main`, after the stacked PR chain has been
merged. Specifically:

```text
PR #24 → main           (Phase 3.19)
PR #25 → main           (Phase 3.20, retargeted after #24 merges)
PR #26 → main           (Phase 3.21)
PR #27 → main           (Phase 3.22 + 3.22b)
PR #28 → main           (Phase 3.23)
PR #29 → main           (Phase 3.24)
PR #30 → main           (Phase 3.25)
PR #31 → main           (Phase 3.26)
PR #32 → main           (Phase 3.30)
PR #33 → main           (Phase 3.31)
```

Phase 3.32's branch is created from `main` after all ten have been
merged. If the stack is unable to merge cleanly (e.g., a conflict in
`INVARIANT_CATALOG.md` from concurrent edits), 3.32's first step is
to resolve the conflicts in a dedicated reconciliation commit on
`main` before branching.

## Mandatory non-claim discipline

No probe behavior changes in 3.32. No new cognitive claim. The
`ProbeReport` protocol is purely structural typing.

## Acceptance criteria

Phase 3.32 succeeds only when every item below is true:

- All PRs #24 through #33 are merged into `main` (operator-controlled).
- `git log --oneline -50 main` shows a clean linear or merge-commit
  history with all ten campaign branches reconciled.
- `brain.development.probe_report_protocol` exists with the closed
  `ProbeReport` Protocol class and the `collect_probe_reports()`
  adapter function.
- The `ProbeReport` protocol declares at minimum:
  - `digest_hex16: str`
  - `false_positive_count: int`
  - `false_negative_count: int`
  - `module_name: str`  (probe identifier; e.g. `"proto_speech_acquisition"`)
- Every existing probe report dataclass passes `isinstance(report, ProbeReport)`
  at runtime via `runtime_checkable` (or its `@typing.runtime_checkable`
  equivalent in 3.12).
- No existing probe module is modified. The protocol is import-only.
- The static-audit fixture `probe_report_protocol_static_audit.py`
  verifies that no probe report dataclass has been altered.
- Benchmark battery A1..A15: same case totals, same digest as before.
- `python3 -m brain.invariants run` is fully green.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report 5/5 PASS.
- Catalog v0.37 → v0.38 with +1 STRUCTURAL row `I-PROBE-01`.
  No new REQUIRED rows.
- PR opens with head `campaign/phase3-32-mainline-reconciliation`
  against `main`.

## Why this is a campaign, not a chore

The PR-stack merge is operator-controlled and could be done outside
Phase 3.32. But the **protocol declaration** is the campaign's real
work. Without it, Phase 3.34's projector has two unappealing options:

1. Import every probe module and depend on five distinct report
   dataclasses. Couples the profile to probe internals.
2. Duplicate every report's relevant fields into the profile's own
   internal struct. Stale-by-construction.

A `typing.Protocol` is the third option: the projector imports the
protocol, every probe report already satisfies it by name, and no
probe module changes. The protocol is the contract.

## Step ledger (planned)

```text
Step 1   PR stack audit + reconciliation plan                phase3.32 step1
Step 2   Operator-controlled merge of PRs #24..#33           phase3.32 step2
Step 3   Branch from reconciled main                         phase3.32 step3
Step 4   probe_report_protocol.py + Protocol declaration     phase3.32 step4
Step 5   collect_probe_reports() adapter + tests             phase3.32 step5
Step 6   probe_report_protocol_static_audit.py fixture       phase3.32 step6
Step 7   Catalog v0.37 → v0.38 (+I-PROBE-01)           phase3.32 step7
Step 8   Verification: runtime_checkable on all 5 probes     phase3.32 step8
Step 9   Open PR; update PHASE3_HANDOFF_STATE.md             phase3.32 step9
```

## Step 1 detailed scope: PR stack audit

Run:

```bash
gh pr list --state open --json number,headRefName,baseRefName,mergeable,statusCheckRollup
```

For each open PR in the stack:

- Check `mergeable == "MERGEABLE"`.
- Check `statusCheckRollup` is all green.
- Check `baseRefName` matches the prior branch in the stack (PR #25's
  base should be the campaign/phase3-19 branch, etc.).
- Note any retargeting needed when an upstream merges.

Output: `docs/campaigns/phase3_32/PHASE3_32_PR_STACK_AUDIT.md` populated
with the actual stack state (the bundle file is a template).

## Step 4 detailed scope: the Protocol

```python
# brain/development/probe_report_protocol.py
"""Phase 3.32 Probe Report Protocol.

Header-only typing.Protocol that every existing probe report
already satisfies by name. The Phase 3.34 developmental
progression profile projector consumes this protocol, so it
does not have to import five distinct probe modules.

Closed import set:
    __future__, typing
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProbeReport(Protocol):
    """Common structural shape of every probe report dataclass.

    Every probe's *Report dataclass already exposes these four
    fields by name; this protocol declares the contract. The
    profile projector calls only these four attributes.

    The protocol intentionally does NOT include probe-specific
    counters (stable_combination_count, survived_count, etc.).
    Those are accessed via getattr() with a default in the
    projector, so the protocol can stay narrow.
    """
    digest_hex16: str
    false_positive_count: int
    false_negative_count: int
    module_name: str


def collect_probe_reports() -> tuple["ProbeReport", ...]:
    """Run each probe's canonical live-test and return reports.

    Deterministic. Bit-identical across runs. The order is
    fixed: proto_speech, curriculum_consolidation,
    active_hypothesis, osmotic_learning, worldlet_feedback.
    """
    from brain.development.proto_speech_acquisition import (
        run_proto_speech_live_test,
    )
    from brain.development.curriculum_consolidation_probe import (
        run_curriculum_consolidation_live_test,
    )
    from brain.development.active_hypothesis_probe import (
        run_active_hypothesis_live_test,
    )
    from brain.development.osmotic_learning_probe import (
        run_osmotic_learning_live_test,
    )
    return (
        run_proto_speech_live_test(),
        run_curriculum_consolidation_live_test(),
        run_active_hypothesis_live_test(),
        run_osmotic_learning_live_test(),
    )
```

Note: `module_name` doesn't currently exist on every probe report. If
not present, Step 4 adds it as a `ClassVar[str]` on each existing
report dataclass — the ONLY allowed modification to existing probe
modules, and only because it's a constant string identifier (no
behavior change).

## Hard limits

```text
- No probe module's runner behavior changes.
- No probe module's report dataclass loses or renames a field.
- The only allowed addition to existing probe reports is
  ClassVar[str] module_name.
- No new OperatorCommand, LOCAL_COMMAND_VERBS, ACTIVE_VIEWS,
  GrowthEventType, GrowthEventSource, LearningEvidenceKind,
  or ReasoningStepKind member.
- No DB schema change.
- No brain.llm import.
- No brain.tick.tick call outside STEP_TICK.
- 0 real model calls.
- 0 cache writes.
```

## Cross-references

- `docs/campaigns/phase3_32/PHASE3_32_PR_STACK_AUDIT.md` — PR-stack
  state and reconciliation plan.
- `docs/campaigns/phase3_32/PHASE3_32_PROBE_REPORT_PROTOCOL.md` —
  full Protocol design including rationale, alternatives considered,
  and the explicit list of probes that satisfy it.
- `ADR-001-locked-decisions-D1-D8.md` — D4 justifies this phase.
