# CURRENT_MISSION.md — Phase 3.32 Mainline Reconciliation + ProbeReport Protocol

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, run the next eligible
campaign step, commit successful results, push the branch, and stop
exactly where the campaign says to stop.

---

## Current mission

Execute the **Phase 3.32 Mainline Reconciliation + ProbeReport Protocol**
campaign per the canonical roadmap:

```text
PHASE3_32_MAINLINE_RECONCILIATION_ROADMAP.md
CURRENT_CAMPAIGN.md
```

Phase 3.32 has two halves:

```text
A. Reconciliation half (Steps 1-3, ALREADY LANDED)
   PRs #24..#33 merged into main; a reconciliation branch
   `campaign/phase3-32-mainline-reconciliation` was cut from
   main and has the campaign stack through Phase 3.31 merged
   into it. Commits `phase3.32: merge campaign stack...` and
   `phase3.32: reconcile campaign stack into main` are present
   on HEAD.

B. ProbeReport protocol half (Steps 4-9, REMAINING)
   Land `brain/development/probe_report_protocol.py` — a thin
   header-only `typing.Protocol` plus a deterministic
   `collect_probe_reports()` adapter. Add `module_name`
   `ClassVar[str]` to each existing probe report dataclass
   (the only allowed modification to existing probe modules;
   constant string, no behavior change, not in any digest).
   Land the static-audit fixture
   `probe_report_protocol_static_audit.py`. Add catalog row
   `I-PROBE-01` (STRUCTURAL) and bump catalog v0.37 -> v0.38.
   Verify all gates green. Open PR; do NOT merge.
```

Phase 3.32 (full) takes the repo from:

```text
Main contains Phase 3.31 / catalog v0.37; the reconciliation
branch `campaign/phase3-32-mainline-reconciliation` has the
campaign stack merged but the ProbeReport protocol module does
not yet exist.
```

toward:

```text
The reconciliation branch contains, additionally,
brain/development/probe_report_protocol.py with a
@runtime_checkable ProbeReport Protocol and the
collect_probe_reports() adapter; every existing probe report
dataclass has been given a ClassVar[str] module_name and is
runtime_checkable as a ProbeReport; the static-audit fixture
verifies the protocol holds; catalog is v0.38 with new
STRUCTURAL row I-PROBE-01; benchmark A1..A15 totals and
digests are unchanged from v0.37; proto-speech live-test
remains 10/10 PASS with report_digest f6a83b9caef0ac17; all
canonical gates pass; PR is opened against main and not merged.
```

Allowed claim shape:

```text
"Phase 3.32 is a reconciliation + protocol-declaration campaign.
It brings main current with the Phase 3.31 campaign stack and
adds a single header-only typing.Protocol (ProbeReport) that
every existing probe report dataclass already satisfies by
name. No probe runner behavior changes. The protocol is the
clean interface the Phase 3.34 developmental progression
profile projector will consume. Non-claim discipline is
preserved: every prior cognitive-claim guardrail (no
consciousness, sentience, awareness, subjective experience,
language understanding, inner speech, private thought, agency,
will, desire, belief, intent, introspection, metacognition,
curiosity, or deliberation claims) carries forward unchanged."
```

Forbidden claim shape:

```text
"Phase 3.32 modifies probe runner behavior / changes any probe
report's existing fields / introduces a new benchmark axis /
adds new OperatorCommand / LearningEvidenceKind / etc. members /
weakens any cognitive-claim guardrail / merges the
reconciliation PR automatically."
```

If asked whether ToyI is conscious / sentient / aware / understands
language / talks / has inner speech / has private thought, the
runtime's deterministic reply must DENY the cognitive claim and
describe itself as a bounded structural runtime — unchanged from
Phase 3.31.

---

## Locked decisions (do NOT relitigate; see ADR-001 for full text)

```text
D1  Phase 3.33 is diagnostic-only. (Not 3.32; carried for context.)
D2  Bands B00..B07 are GENERIC structural labels, shared across axes.
D3  Strict counter pattern is project-wide discipline (applies in 3.33).
D4  Phase 3.32 lands the ProbeReport protocol.  <-- THIS PHASE
D5  Regression gate uses TARGET_AXES / NON_TARGET_AXES scoping.
D6  Predicate monotonicity is a checked structural invariant (in 3.34).
D7  NextProgressionTarget is a structured roadmap stub (in 3.34).
D8  Benchmark axis A16 lands with Phase 3.34.
```

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_32_MAINLINE_RECONCILIATION_ROADMAP.md
ADR-001-locked-decisions-D1-D8.md
docs/campaigns/phase3_32/PHASE3_32_PR_STACK_AUDIT.md
docs/campaigns/phase3_32/PHASE3_32_PROBE_REPORT_PROTOCOL.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/proto_speech_acquisition.py
brain/development/curriculum_consolidation_probe.py
brain/development/active_hypothesis_probe.py
brain/development/osmotic_learning_probe.py
brain/_catalog_ids.py
tools/catalog.py
tools/check_all.sh
```

---

## Local command rule

Use `python3 -m ...` for Python module commands. Do not run real LLM
scenario commands unless the user explicitly asks.

---

## Stop conditions

Stop and report if:

- worktree is dirty in a way that conflicts with the next step;
- catalog version banner / row count / generated id file drift cannot
  be resolved by `python3 -m tools.catalog generate-ids` alone;
- any probe report dataclass cannot be given a `ClassVar[str]
  module_name` without changing layout or constructor signature;
- `isinstance(report, ProbeReport)` returns False for any existing
  probe report after the protocol lands;
- the static-audit fixture would require modifying probe runner
  behavior to pass;
- benchmark A1..A15 totals or digests change vs the v0.37 baseline
  (would indicate an accidental probe behavior change);
- proto-speech live-test no longer reports 10/10 PASS or its
  report_digest changes from `f6a83b9caef0ac17`;
- any gate command fails or reports unexpected verdicts;
- any new behavioral feature, runtime module beyond the protocol
  file, fixture beyond the static-audit, catalog row beyond
  I-PROBE-01, or benchmark axis is required.

Stop at Phase 3.32 acceptance (every criterion in
`CURRENT_CAMPAIGN.md` and the roadmap is satisfied), open the
PR (head `campaign/phase3-32-mainline-reconciliation`, base
`main`), update `PHASE3_HANDOFF_STATE.md`, and wait for the
operator to merge the PR manually.
