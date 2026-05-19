"""Parser and query interface for INVARIANT_CATALOG.md.

Reads the catalog's markdown tables into structured rows so other tooling
(citation verifier, runner sanity checks, subagents) can query by ID,
status, module, or fixture without re-parsing the file each time.

CLI:
    python3 -m tools.catalog list [--status REQUIRED] [--module modes]
                                  [--source-kind LEAN]
    python3 -m tools.catalog show I-AGN-03
    python3 -m tools.catalog counts
    python3 -m tools.catalog generate-ids   # writes brain/_catalog_ids.py
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "INVARIANT_CATALOG.md"
GENERATED_IDS_PATH = REPO_ROOT / "brain" / "_catalog_ids.py"

# v0.38 expected counts — bumped by the Phase 3.32 Mainline
# Reconciliation + ProbeReport Protocol catalog patch
# (I-PROBE-01: +0 REQUIRED rows, +1 STRUCTURAL row; NOT-
# EXERCISED / DEFERRED / OBSERVED unchanged). Phase 3.32 adds the
# new header-only module brain/development/probe_report_protocol
# .py: a @runtime_checkable typing.Protocol named ProbeReport
# declaring the four documented attributes digest_hex16: str,
# false_positive_count: int, false_negative_count: int,
# module_name: str, plus a deterministic collect_probe_reports()
# adapter. Each existing probe report dataclass gains one
# ClassVar[str] module_name constant (excluded from __slots__,
# not in any digest input, no runtime behavior change). Benchmark
# A1..A15 digests are bit-identical to the v0.37 baseline; proto-
# speech live-test remains 10/10 PASS with digest f6a83b9caef0ac17.
# v0.37 history retained: bumped by the Phase 3.31 Caregiver-
# Scaffolded Proto-Speech Acquisition catalog patch
# (I-PSPEECH-01..19: +18 REQUIRED rows, +1 STRUCTURAL row; NOT-
# EXERCISED / DEFERRED / OBSERVED unchanged). Phase 3.31 adds the
# new module brain/development/proto_speech_acquisition.py: a
# pure bounded deterministic OFFLINE live-test runner with closed
# ProtoVocalToken (15 values), CaregiverFeedbackKind (6 values),
# ProtoSpeechContextKind (9 values), ProtoUtteranceDisposition
# (8 values), ProtoSpeechDriveKind (12 values), ProtoSpeechStatus
# (4 values), and ProtoSpeechCondition (10 values) enums and the
# bounded ProtoUtterance, CaregiverFeedback, ProtoSpeechContext,
# ProtoSpeechDriveFrame, ProtoSpeechDriveStream,
# ProtoSpeechEvidenceRecord, ProtoSpeechEvidenceTable,
# ProtoSpeechTurn, ProtoSpeechAcquisitionReport records. The
# runner probes whether the existing substrate realizes the
# operational analogue of caregiver-scaffolded proto-speech
# acquisition (drive-stream-grounded babble + closed-rule
# evidence updates + shape-digest transfer + suppression +
# combination + refusal-held) under ten bounded conditions. The
# benchmark battery adds one axis: A15 proto_speech_acquisition
# (18 cases A15.01..A15.18). Total benchmark cases: 137 (119 +
# 18); 136 PASS + 1 WARN (A3.04 carry-over) + 0 FAIL. brain/tick
# .py is not edited; no existing runtime file's behavior changes;
# OFFLINE default preserved; zero real model calls; non-claim
# discipline enforced via the canonical _FORBIDDEN_NON_CLAIM_TERMS
# tuple on every produced summary string and the new module
# source. "Proto-speech acquisition" is engineering shorthand for
# bounded co-occurrence + closed-rule weight updates + drive-
# stream-grounded selection + shape-digest transfer at the
# substrate level; the runtime is not claimed to have language,
# inner speech, hidden chain-of-thought, communicative intent,
# audience modelling, or any cognitive process.
# v0.36 history retained: bumped by the Phase 3.30 Curriculum
# Consolidation Live Test catalog patch (I-CURR-01..14: +13
# REQUIRED rows, +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED /
# OBSERVED unchanged). Phase 3.30 adds the new module
# brain/development/curriculum_consolidation_probe.py: a pure
# bounded deterministic OFFLINE live-test runner with closed
# CurriculumCondition (5 values), AuditDisposition (3 values),
# AdmissionOutcome (3 values), TrialVerdict (4 values) enums and
# the bounded CurriculumExposure, CurriculumStructureRecord,
# CurriculumProbeStep, CurriculumTrial, CurriculumTrialResult,
# CurriculumConsolidationReport records. The runner probes whether
# the existing substrate realizes the operational analogue of
# *curriculum consolidation*: bounded ordered structural exposure
# + closed admission rule + LRU decay + session-local cache reuse
# + tri-disposition audit at the substrate level. The v1
# ten-trial battery covers shapes A B / A A / A B C / A A B /
# A B A / A B B / collision pairs / five- and six-shape overflow /
# reuse positive and negative under five conditions
# (SINGLE_STRUCTURE, SEQUENTIAL_NONINTERFERING,
# SEQUENTIAL_INTERFERING, DECAY_ON_DISUSE, REUSE_AFTER_NEWER).
# Eleven new fixtures land in brain/ui/fixtures/. The benchmark
# battery adds one axis: A14 curriculum_consolidation (14 cases
# A14.01..A14.14). Total benchmark cases: 119 (105 + 14); 118 PASS
# + 1 WARN (A3.04 carry-over) + 0 FAIL. brain/tick.py is not
# edited; no existing runtime file's behavior changes; OFFLINE
# default preserved; zero real model calls; non-claim discipline
# enforced via the canonical _FORBIDDEN_NON_CLAIM_TERMS tuple on
# every produced summary string and the new module source.
# "Curriculum consolidation" is engineering shorthand for bounded
# ordered structural exposure + closed admission rule + LRU decay
# + session-local cache reuse + tri-disposition audit at the
# substrate level; the runtime is not claimed to have learning,
# memory, forgetting, consolidation, interference, deliberation,
# attention, working memory, episodic memory, or any cognitive
# process.
# v0.35 history retained: bumped by the Phase 3.26 Active
# Hypothesis + Self-Directed Probe Loop catalog patch
# (I-AHYP-01..14: +13 REQUIRED rows, +1 STRUCTURAL row;
# NOT-EXERCISED / DEFERRED / OBSERVED unchanged). Phase 3.26 adds the new module
# brain/development/active_hypothesis_probe.py: a pure bounded
# deterministic OFFLINE live-test runner with closed AmbiguityCondition
# (5 values), ActiveHypothesisStatus (4 values), ProbeConstructionRule
# (6 values), TrialVerdict (4 values), ProbeOutcome (2 values) enums
# and the bounded ActiveHypothesisCandidate, ActiveProbeStep,
# ActiveHypothesisTrial, ActiveHypothesisResult,
# ActiveHypothesisLiveTestReport records. The runner probes whether
# the existing substrate realizes the operational analogue of
# *active hypothesis + self-directed probe*: bounded structural
# candidate enumeration + falsification + caching at the substrate
# level. The v1 ten-trial battery covers shapes A B A, A B B,
# A B C, A B A B, A A, A A B under five conditions
# (CONTROL_NO_AMBIGUITY, SINGLE_HYPOTHESIS_CONVERGES,
# MULTI_HYPOTHESIS_NARROWS, NO_HYPOTHESIS_SURVIVES,
# REUSE_CACHED_HYPOTHESIS). Eleven new fixtures land in
# brain/ui/fixtures/. The benchmark battery adds one axis: A13
# active_hypothesis (14 cases A13.01..A13.14). Total benchmark
# cases: 105 (91 + 14); 104 PASS + 1 WARN (A3.04 carry-over) + 0
# FAIL. brain/tick.py is not edited; no existing runtime file's
# behavior changes; OFFLINE default preserved; zero real model
# calls; non-claim discipline enforced via the canonical
# _FORBIDDEN_NON_CLAIM_TERMS tuple on every produced summary
# string and the new module source. "Active hypothesis" /
# "self-directed probe" is engineering shorthand for bounded
# structural candidate enumeration + falsification + caching at
# the substrate level; the runtime is not claimed to have
# inquiry, curiosity, deliberation, planning, decision-making,
# introspection, or any cognitive property.
# v0.34 history retained: bumped by the Phase 3.25 Osmotic Learning
# Live Test catalog patch (I-OSMO-01..14: +13 REQUIRED rows, +1
# STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged).
# Phase 3.25 adds the new module
# brain/development/osmotic_learning_probe.py: a pure bounded
# deterministic OFFLINE live-test runner with the closed
# OsmoticCondition (4 values) and OsmoticProbeStatus (4 values)
# enums and the bounded OsmoticExposureEvent, OsmoticProbeTrial,
# OsmoticProbeResult, OsmoticLiveTestReport records. The runner
# probes whether the existing substrate realizes the operational
# analogue of osmotic imprinting + activation under four bounded
# conditions: CONTROL_NO_EXPOSURE, TRUE_EXPOSURE, SHAM_EXPOSURE,
# DISTRACTOR_INTERFERENCE. The v1 ten-trial battery covers ABAB,
# ABBA, AAB, ABCABC target shapes. Ten new fixtures land in
# brain/ui/fixtures/. The benchmark battery adds one axis: A12
# osmotic_learning (14 cases A12.01..A12.14). Total benchmark
# cases: 91 (77 + 14); 90 PASS + 1 WARN (A3.04 carry-over) + 0
# FAIL. brain/tick.py is not edited; no existing runtime file's
# behavior changes; OFFLINE default preserved; zero real model
# calls; non-claim discipline enforced via the canonical
# _FORBIDDEN_NON_CLAIM_TERMS tuple on every produced summary
# string and the new module source. "Osmotic learning" is
# engineering shorthand for unlabeled exposure-driven structural
# uptake at the substrate level; the runtime is not claimed to
# have intuition, awareness, perception, or unconscious learning.
# v0.33 history retained: bumped by the Phase 3.24 Worldlet Feedback
# Bridge catalog patch (I-WFDBK-01..12: +11 REQUIRED rows, +1
# STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged).
# Phase 3.24 adds the bounded pure helper build_worldlet_summary_text
# in brain/development/processing_window.py, the two new FeedbackMode
# members WORLDLET and PATTERN_COHERENCE_WORLDLET, the new
# InternalEventSource.WORLDLET_SUMMARY member, the OperatorSession
# helper method _run_worldlet_feedback_step in brain/ui/session.py,
# the two new closed-enum extensions ReasoningStepKind.CHECK_WORLDLET_FEEDBACK
# and LearningEvidenceKind.WORLDLET_FEEDBACK_RECORDED, the three new
# AgentObservationSummary fields, the dispatch-trace
# worldlet_summary_chunks derived fact, and benchmark axis A11
# worldlet_feedback (12 cases A11.01..A11.12). Eight new fixtures
# land in brain/ui/fixtures/. brain/tick.py is not edited; no
# existing runtime file's behavior changes; OFFLINE default
# preserved; zero real model calls; non-claim discipline enforced
# via the canonical _FORBIDDEN_NON_CLAIM_TERMS tuple on every
# produced summary string and the new helper output.
# v0.32 history retained: bumped by the Phase 3.23 Dispatch Tracer
# Wiring catalog patch (I-DTRACE-01..12: +11 REQUIRED rows, +1
# STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged).
# Phase 3.23 adds the brain/development/dispatch_tracer.py module: a
# pure deterministic audit-trail substrate with closed
# DispatchTraceKind (12 values), DispatchMutationKind (14 values),
# and DispatchTraceStatus (4 values) enums and bounded
# DispatchTraceStep / DispatchTrace / DispatchTraceReport /
# DispatchTraceDigest / DispatchTraceConfig records. The
# OperatorSession.dispatch path is wired to build a bounded trace
# inline on every dispatch and store the report on the new
# single-slot OperatorSession.latest_dispatch_trace field; existing
# semantics are kept bit-identical. AgentLoopResult exposes the
# trace report; the Phase 3.22b reasoning trace gains a
# CHECK_DISPATCH_TRACE step before EMIT_REPLY citing the digest, and
# the Phase 3.22b learning evidence ledger gains a
# DISPATCH_TRACE_RECORDED record kind citing the same digest. The
# benchmark gains one new axis A10 (12 cases). Nine new fixtures
# land in brain/ui/fixtures/ (constructor + session-stream +
# processing-window + step-tick-error + noop + agent-loop-integration
# + reasoning-learning-integration + benchmark-axis + static-audit).
# brain/tick.py is not edited; no existing runtime file's behavior
# changes; OFFLINE default preserved; zero real model calls; non-
# claim discipline enforced via the canonical
# _FORBIDDEN_NON_CLAIM_TERMS tuple on every produced summary string
# and the new module source.
# v0.29 history retained: bumped by the Phase 3.21 Developmental
# Trajectory catalog patch (I-DEVMILE-01..11: +10 REQUIRED rows,
# +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED
# unchanged). Phase 3.21 adds the brain/development/milestone_harness.py
# module: a strict consumer of existing public surfaces that
# defines a closed ten-member DevelopmentalMilestone enum, a
# closed four-member MilestoneStatus enum, a frozen / slotted
# MilestoneResult record, ten pure deterministic helpers
# run_m01_*..run_m10_*, and an aggregator run_all_milestones().
# Eleven new fixtures land in brain/ui/fixtures/ (one per
# milestone + one static audit). brain/tick.py is not edited;
# no existing runtime file is modified; OFFLINE default
# preserved; zero real model calls; non-claim discipline
# enforced via the canonical _FORBIDDEN_NON_CLAIM_TERMS tuple
# on every produced summary string and the harness module
# source. "Developmental" / "milestone" / "trajectory" are used
# in the operational sense only, never psychological.
# v0.28 history retained: Phase 3.20 extends brain/development/processing_window.py
# with two new FeedbackMode members (COHERENCE and
# PATTERN_AND_COHERENCE), a pure build_cohmon_summary_text helper
# accepting only bounded primitives, the COHMON_SUMMARY_TEXT_*
# constants, and widens the v1-emitted source set in
# InternalEventSource to include COHMON_SUMMARY (no member is
# reserved at v0.28). OperatorSession gains a new
# _run_cohmon_feedback_step helper that performs a deferred
# function-body import of build_full_coherence_report to avoid a
# circular module load. The new fixtures are
# coherence_feedback_static_audit.py (STRUCTURAL) and
# coherence_feedback_integration.py (REQUIRED). brain/tick.py is
# not edited; L1 / L2 cache semantics unchanged; parser / prompt
# unchanged; no new GrowthEventType / GrowthEventSource /
# OperatorCommand / operator verb; STREAM_APPEND consumes zero
# real model calls so the feedback path consumes zero real model
# calls regardless of size.
EXPECTED_COUNTS: dict[str, int] = {
    "REQUIRED": 392,
    "STRUCTURAL": 102,
    "NOT-EXERCISED": 14,
    "DEFERRED": 15,
    "OBSERVED": 16,
}

# Module header lines look like "### `brain/tlica/profile.py` — ..."
_MODULE_HEADER_RE = re.compile(r"^###\s+`([^`]+)`")
# Row IDs look like I-XXX-NN
_ROW_ID_RE = re.compile(r"^I-[A-Z]+-\d+[a-z]?$")
# Banner counts at the summary block
_REQUIRED_BANNER_RE = re.compile(r"\*\*REQUIRED[^*]*\*\*\s*(\d+)")
_STRUCTURAL_BANNER_RE = re.compile(r"\*\*STRUCTURAL[^*]*\*\*\s*(\d+)")
_NOT_EXERCISED_BANNER_RE = re.compile(r"\*\*NOT-EXERCISED[^*]*\*\*\s*(\d+)")
_DEFERRED_BANNER_RE = re.compile(r"\*\*DEFERRED[^*]*\*\*\s*(\d+)")
_OBSERVED_BANNER_RE = re.compile(r"\*\*OBSERVED[^*]*\*\*\s*(\d+)")


class SourceKind(Enum):
    """Phase 2 v1.2: explicit classification of each catalog row's origin.

    Inferred from the row's ``Source`` field and ``Status`` by
    :func:`infer_source_kind`. Becomes load-bearing in Phase 3 when
    developmental / engineering rows need to be enumerable separately
    from theory-derived rows.
    """

    LEAN = "lean"
    PLAN_CONVENTION = "plan_convention"
    ENGINEERING_HYPOTHESIS = "engineering_hypothesis"
    OBSERVED = "observed"
    DEFERRED = "deferred"


_ENGINEERING_MARKERS: tuple[str, ...] = (
    "phase 2 v1",
    "phase 2 v1.1",
    "phase 2 v1.2",
    "phase 3",
    "developmental layer",
    "engineering hypothesis",
)


def infer_source_kind(source: str, status: str) -> SourceKind:
    """Classify a catalog row's source/status as a :class:`SourceKind`.

    Status-driven overrides win first (OBSERVED, DEFERRED, NOT-EXERCISED);
    otherwise infer from the free-text Source field via heuristics that
    detect Lean citations and Phase 2/3 engineering markers.
    """
    if status == "OBSERVED":
        return SourceKind.OBSERVED
    if status in ("DEFERRED", "NOT-EXERCISED"):
        return SourceKind.DEFERRED
    src_low = source.lower()
    if "::" in source and ".lean" in src_low:
        return SourceKind.LEAN
    if any(marker in src_low for marker in _ENGINEERING_MARKERS):
        return SourceKind.ENGINEERING_HYPOTHESIS
    return SourceKind.PLAN_CONVENTION


@dataclass(frozen=True, slots=True)
class InvariantRow:
    id: str
    lean_source: str
    proposition: str
    py_assertion: str
    fixture: str
    status: str
    module: str  # the brain/ owning module (last seen module header)
    source_kind: SourceKind = SourceKind.PLAN_CONVENTION


def _split_pipes(line: str) -> list[str]:
    """Split markdown-table row on `|`, treating backtick-quoted spans as opaque.

    This matters because catalog rows like I-PROF-07 contain expressions like
    `f.domain | g.domain` inside backticks; a naive split mangles them.
    """
    parts: list[str] = []
    buf: list[str] = []
    in_tick = False
    for ch in line:
        if ch == "`":
            in_tick = not in_tick
            buf.append(ch)
        elif ch == "|" and not in_tick:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def load_catalog(path: Path | None = None) -> list[InvariantRow]:
    """Parse the catalog markdown into InvariantRow records."""
    p = path or CATALOG_PATH
    text = p.read_text(encoding="utf-8")
    rows: list[InvariantRow] = []
    current_module = ""
    for raw_line in text.splitlines():
        m = _MODULE_HEADER_RE.match(raw_line)
        if m:
            current_module = m.group(1)
            continue
        if not raw_line.startswith("|"):
            continue
        cells = _split_pipes(raw_line)
        if len(cells) < 6:
            continue
        first = cells[0]
        if not _ROW_ID_RE.match(first):
            continue
        # Standard catalog rows have 6 columns:
        #   ID | Lean source | Proposition | Python assertion | Fixture | Status
        # The Phase 2 v1 cross-cutting table has 7 columns:
        #   ID | Source | Proposition | Python assertion | Owning module | Fixture | Status
        # Read Status/Fixture from the right end so both shapes parse correctly;
        # when an Owning module column is present, prefer it over current_module.
        status = cells[-1]
        fixture = cells[-2]
        if len(cells) >= 7:
            module = cells[-3]
        else:
            module = current_module
        rows.append(
            InvariantRow(
                id=first,
                lean_source=cells[1],
                proposition=cells[2],
                py_assertion=cells[3],
                fixture=fixture,
                status=status,
                module=module,
                source_kind=infer_source_kind(cells[1], status),
            )
        )
    return rows


def filter_rows(
    rows: list[InvariantRow],
    *,
    status: str | None = None,
    module: str | None = None,
    fixture: str | None = None,
    id_prefix: str | None = None,
    source_kind: SourceKind | None = None,
) -> list[InvariantRow]:
    out = rows
    if status is not None:
        out = [r for r in out if r.status == status]
    if module is not None:
        out = [r for r in out if module in r.module]
    if fixture is not None:
        out = [r for r in out if fixture in r.fixture]
    if id_prefix is not None:
        out = [r for r in out if r.id.startswith(id_prefix)]
    if source_kind is not None:
        out = [r for r in out if r.source_kind == source_kind]
    return out


def banner_counts(path: Path | None = None) -> dict[str, int]:
    """Return the catalog's self-reported summary counts."""
    p = path or CATALOG_PATH
    text = p.read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for label, pattern in (
        ("REQUIRED", _REQUIRED_BANNER_RE),
        ("STRUCTURAL", _STRUCTURAL_BANNER_RE),
        ("NOT-EXERCISED", _NOT_EXERCISED_BANNER_RE),
        ("DEFERRED", _DEFERRED_BANNER_RE),
        ("OBSERVED", _OBSERVED_BANNER_RE),
    ):
        m = pattern.search(text)
        counts[label] = int(m.group(1)) if m else -1
    return counts


def actual_counts(rows: list[InvariantRow]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r.status] = out.get(r.status, 0) + 1
    return out


def _fmt_row(r: InvariantRow) -> str:
    return f"{r.id:11s}  {r.status:14s}  {r.module:42s}  fixture={r.fixture}"


def _cmd_list(args: argparse.Namespace) -> int:
    rows = load_catalog()
    kind = None
    if args.source_kind:
        try:
            kind = SourceKind[args.source_kind.upper()]
        except KeyError:
            print(
                f"unknown --source-kind {args.source_kind!r}; expected one of "
                f"{[k.name for k in SourceKind]}",
                file=sys.stderr,
            )
            return 1
    filtered = filter_rows(
        rows,
        status=args.status,
        module=args.module,
        fixture=args.fixture,
        id_prefix=args.id_prefix,
        source_kind=kind,
    )
    for r in filtered:
        print(_fmt_row(r))
    print(f"\n{len(filtered)} rows.")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    rows = load_catalog()
    matches = [r for r in rows if r.id == args.row_id]
    if not matches:
        print(f"No row with ID {args.row_id!r}.", file=sys.stderr)
        return 1
    for r in matches:
        print(f"ID:           {r.id}")
        print(f"Status:       {r.status}")
        print(f"Module:       {r.module}")
        print(f"Fixture:      {r.fixture}")
        print(f"Lean source:  {r.lean_source}")
        print(f"Proposition:  {r.proposition}")
        print(f"Py assertion: {r.py_assertion}")
    return 0


def _cmd_counts(args: argparse.Namespace) -> int:
    rows = load_catalog()
    banner = banner_counts()
    actual = actual_counts(rows)
    if args.by_source_kind:
        return _print_counts_by_source_kind(rows)
    print(f"{'Category':16s}  {'Banner':>8s}  {'Actual':>8s}  {'Expected':>8s}")
    ok = True
    # Strict gate (P6): banner ≠ actual ≠ expected ⇒ failure.
    # Previously only actual-vs-expected mismatch failed, so stale banners
    # could sneak past the gate.
    for k in ("REQUIRED", "STRUCTURAL", "NOT-EXERCISED", "DEFERRED", "OBSERVED"):
        b = banner.get(k, -1)
        a = actual.get(k, 0)
        e = EXPECTED_COUNTS[k]
        passing = b == a == e
        mark = "  ok" if passing else "  !!"
        if not passing:
            ok = False
        print(f"{k:16s}  {b:8d}  {a:8d}  {e:8d}{mark}")
    return 0 if ok else 1


def _print_counts_by_source_kind(rows: list[InvariantRow]) -> int:
    counts: dict[SourceKind, int] = {kind: 0 for kind in SourceKind}
    for r in rows:
        counts[r.source_kind] += 1
    print(f"{'Source kind':24s}  {'Count':>8s}")
    for kind in SourceKind:
        print(f"{kind.name:24s}  {counts[kind]:8d}")
    print(f"\n{sum(counts.values())} total rows.")
    return 0


def _cmd_generate_ids(args: argparse.Namespace) -> int:
    """Write ``brain/_catalog_ids.py`` from the catalog.

    Source of truth for I-CAT-01 — every REQUIRED / STRUCTURAL ID listed
    in the catalog appears in the generated frozenset; the runner audits
    its registry against these at startup.
    """
    rows = load_catalog()
    required = sorted(r.id for r in rows if r.status == "REQUIRED")
    structural = sorted(r.id for r in rows if r.status == "STRUCTURAL")
    lines = [
        '"""Auto-generated from INVARIANT_CATALOG.md by tools/catalog.py.',
        "",
        "DO NOT EDIT BY HAND. Regenerate via:",
        "",
        "    python3 -m tools.catalog generate-ids",
        "",
        "This file is the source of truth for I-CAT-01 (every REQUIRED or",
        "STRUCTURAL catalog row has a corresponding @register entry).",
        '"""',
        "from __future__ import annotations",
        "",
        "EXPECTED_REQUIRED_IDS: frozenset[str] = frozenset({",
    ]
    for rid in required:
        lines.append(f'    "{rid}",')
    lines.append("})")
    lines.append("")
    lines.append("EXPECTED_STRUCTURAL_IDS: frozenset[str] = frozenset({")
    for rid in structural:
        lines.append(f'    "{rid}",')
    lines.append("})")
    lines.append("")
    content = "\n".join(lines)
    GENERATED_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    GENERATED_IDS_PATH.write_text(content, encoding="utf-8")
    print(
        f"wrote {GENERATED_IDS_PATH}  "
        f"(REQUIRED={len(required)}, STRUCTURAL={len(structural)})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.catalog")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List rows (optionally filtered).")
    p_list.add_argument("--status")
    p_list.add_argument("--module")
    p_list.add_argument("--fixture")
    p_list.add_argument("--id-prefix")
    p_list.add_argument(
        "--source-kind",
        help="Filter by inferred SourceKind: LEAN, PLAN_CONVENTION, "
        "ENGINEERING_HYPOTHESIS, OBSERVED, DEFERRED.",
    )
    p_list.set_defaults(func=_cmd_list)

    p_show = sub.add_parser("show", help="Show a single row by ID.")
    p_show.add_argument("row_id")
    p_show.set_defaults(func=_cmd_show)

    p_counts = sub.add_parser(
        "counts",
        help="Compare banner vs actual vs expected counts (strict gate).",
    )
    p_counts.add_argument(
        "--by-source-kind",
        action="store_true",
        help="Print counts grouped by SourceKind instead of the strict gate.",
    )
    p_counts.set_defaults(func=_cmd_counts)

    p_gen = sub.add_parser(
        "generate-ids",
        help="Write brain/_catalog_ids.py for the I-CAT-01 runner audit.",
    )
    p_gen.set_defaults(func=_cmd_generate_ids)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
