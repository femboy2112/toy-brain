# CURRENT_CAMPAIGN.md — Phase 3.32 Mainline Reconciliation + ProbeReport Protocol

## Campaign status

```text
RECONCILIATION (DONE) + PROTOCOL-DECLARATION (REMAINING)
SINGLE-PR / NO-PROBE-BEHAVIOR-CHANGE / REVIEW-GATED
```

Phase 3.32 has two halves. The reconciliation half — PR-stack merge
into main and the campaign-stack merge into the reconciliation branch
— is **already landed** on HEAD of branch
`campaign/phase3-32-mainline-reconciliation` (see commits
`phase3.32: merge campaign stack through phase 3.31 into mainline
reconciliation branch` and `phase3.32: reconcile campaign stack into
main`).

The remaining half lands a thin header-only `typing.Protocol`
(`brain/development/probe_report_protocol.py`) plus a
deterministic `collect_probe_reports()` adapter, decorates each
existing probe report dataclass with `ClassVar[str] module_name`,
adds a static-audit fixture, and bumps catalog v0.37 -> v0.38 with
a single new STRUCTURAL row `I-PROBE-01`. This is the clean
interface the Phase 3.34 developmental progression profile
projector will consume.

Phase 3.32 asks one bounded operational question:

```text
Can a single header-only typing.Protocol (ProbeReport) be declared
such that every existing probe report dataclass satisfies it at
runtime via @runtime_checkable, without modifying any probe
runner behavior or changing any existing field on any probe
report (the sole allowed addition is a ClassVar[str] module_name
constant), while every canonical gate stays green, the benchmark
A1..A15 totals and digests stay identical to the v0.37 baseline,
the proto-speech live-test continues to report 10/10 PASS with
report_digest f6a83b9caef0ac17, catalog rolls cleanly v0.37 ->
v0.38 with one new STRUCTURAL row I-PROBE-01, and zero new
behavioral features are introduced?
```

This is a **reconciliation + protocol-declaration** campaign. It is
**NOT** a proof of consciousness, sentience, subjective experience,
agency, semantic understanding, real reasoning, real learning, real
memory, real language acquisition, real language understanding, real
communicative intent, real inner speech, real private thought, real
hidden chain-of-thought, real audience modelling, intentionality,
awareness, intuition, embodiment, psychological development, or any
cognitive process. No new claims are introduced; every prior
non-claim guardrail carries forward unchanged.

Phase 3.32 does **not** add any new `OperatorCommand` member,
`LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS` value, `GrowthEventType`,
`GrowthEventSource`, persistence schema column, autosave trigger,
`LearningEvidenceKind` member, `ReasoningStepKind` member, or
benchmark axis. It does **not** change L1 / L2 / parser / prompt /
tick / persistence / autosave / DB schema semantics. It does **not**
modify theory semantics. The allowed edits are strictly:

- create `brain/development/probe_report_protocol.py` containing the
  `@runtime_checkable` `ProbeReport` Protocol class and the
  `collect_probe_reports()` adapter function;
- add `module_name: ClassVar[str] = "<canonical_name>"` to each
  existing probe report dataclass (proto_speech_acquisition,
  curriculum_consolidation_probe, active_hypothesis_probe,
  osmotic_learning_probe);
- add the static-audit fixture
  `brain/development/fixtures/probe_report_protocol_static_audit.py`;
- add catalog row `I-PROBE-01` (STRUCTURAL) and update the
  catalog version banner in `README.md`, `INVARIANT_CATALOG.md`,
  `tools/catalog.py`, `CURRENT_MISSION.md`, and `CURRENT_CAMPAIGN.md`
  to v0.38;
- regenerate `brain/_catalog_ids.py` via
  `python3 -m tools.catalog generate-ids`;
- update `PHASE3_HANDOFF_STATE.md`;
- the commit messages and PR body.

---

## Source-of-truth

- Reconciliation branch: `campaign/phase3-32-mainline-reconciliation`
- Reconciliation base: `main`
- Expected new catalog version: v0.38 (was v0.37)
- Expected catalog-row delta: +1 STRUCTURAL row `I-PROBE-01`;
  REQUIRED / NOT-EXERCISED / DEFERRED / OBSERVED unchanged
- Expected benchmark A1..A15: identical totals and digests to the
  v0.37 baseline (137 total / 136 PASS / 1 WARN A3.04 carry-over /
  0 FAIL)
- Expected proto-speech live-test: 10/10 PASS, fp=0, fn=0,
  stable_single=5, stable_combination=0, suppressed=2,
  transfer_success=1, report_digest=`f6a83b9caef0ac17`,
  drive_stream_digest=`dc060a88a814f448`
- Expected isinstance checks: every existing probe report
  dataclass passes `isinstance(report, ProbeReport)`
- Expected invariants: 0 red
- Expected gate_runner: 5/5 PASS
- Expected real model calls: 0
- Expected cache writes: 0
- Expected forbidden-term hits: 0

---

## Step ledger

```text
Step 1   PR stack audit + reconciliation plan                 DONE
Step 2   Operator-controlled merge of PRs #24..#33            DONE
Step 3   Branch from reconciled main                          DONE
Step 4   brain/development/probe_report_protocol.py           NEXT
         + Protocol declaration + module_name ClassVars
Step 5   collect_probe_reports() adapter + tests
Step 6   probe_report_protocol_static_audit.py fixture
Step 7   Catalog v0.37 -> v0.38 (+I-PROBE-01)
Step 8   Verification: runtime_checkable on all probe reports
         + full gate run + benchmark + proto-speech live-test
Step 9   Open PR; update PHASE3_HANDOFF_STATE.md
```

Steps 1-3 acceptance is captured by the commits already on HEAD
(`phase3.32: merge campaign stack through phase 3.31 into mainline
reconciliation branch`, `phase3.32: reconcile campaign stack into
main`). Steps 4-9 acceptance is captured below.

---

## Step 4 detailed scope

Create `brain/development/probe_report_protocol.py` with the closed
import set `__future__, typing` and the `@runtime_checkable`
`ProbeReport` Protocol declaring:

```text
digest_hex16: str
false_positive_count: int
false_negative_count: int
module_name: str
```

Add `module_name: ClassVar[str] = "<canonical_name>"` to each
existing probe report dataclass:

```text
ProtoSpeechAcquisitionReport   "proto_speech_acquisition"
CurriculumConsolidationReport  "curriculum_consolidation_probe"
ActiveHypothesisReport         "active_hypothesis_probe"
OsmoticLearningReport          "osmotic_learning_probe"
```

These are `ClassVar`s — constant strings, no instance-field
addition, not in any digest, no constructor signature change.

## Step 5 detailed scope

Add the `collect_probe_reports()` function in
`probe_report_protocol.py` per the design in
`docs/campaigns/phase3_32/PHASE3_32_PROBE_REPORT_PROTOCOL.md`.
Function-body imports defer probe-module coupling. Returns a
deterministic fixed-order tuple of reports.

## Step 6 detailed scope

Land `brain/development/fixtures/probe_report_protocol_static_audit.py`
per the design doc. Verifies that each probe report class has
`module_name` matching the canonical constant, and that the four
required ProbeReport attributes exist as annotations or class
attributes.

## Step 7 detailed scope

```text
README.md catalog-version banner       v0.37 -> v0.38
INVARIANT_CATALOG.md title             v0.37 -> v0.38
INVARIANT_CATALOG.md explicit-version  v0.37 -> v0.38
INVARIANT_CATALOG.md add row           | I-PROBE-01 | STRUCTURAL | ... |
tools/catalog.py EXPECTED_COUNTS       bump STRUCTURAL by +1
brain/_catalog_ids.py                  regenerate via tools.catalog generate-ids
```

## Step 8 detailed scope: full verification

```bash
python3 -m brain.development.proto_speech_acquisition
python3 -m brain.development.agent_benchmark
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
python3 -m tools.claude_helpers.gate_runner --json
```

Every command must succeed at the expected verdicts above.

## Step 9 detailed scope: PR open

Commit messages follow the existing convention:

```text
phase3.32 step4: probe report protocol declaration + module_name classvars
phase3.32 step5: collect_probe_reports adapter
phase3.32 step6: probe report protocol static audit fixture
phase3.32 step7: catalog v0.37 -> v0.38 + I-PROBE-01
phase3.32 step8: full gate + benchmark + proto-speech verification
phase3.32 step9: update handoff state
```

Push the branch and open a PR with `--base main --head
campaign/phase3-32-mainline-reconciliation`. The PR body must
include catalog version (v0.38), counts, benchmark totals,
proto-speech live-test result, gate verdict, invariants result,
real-model-call count, cache-write count, forbidden-term-hit
count, an explicit non-claim disclosure, and an explicit "Merge
with merge commit only after operator approval" instruction.

Do NOT merge the PR.

---

## Acceptance criteria

Phase 3.32 succeeds only when every item below is true:

- branch `campaign/phase3-32-mainline-reconciliation` exists, cut from
  `main`, with the campaign stack through Phase 3.31 merged in (DONE);
- `brain/development/probe_report_protocol.py` exists with the
  closed `ProbeReport` `@runtime_checkable` Protocol class and the
  `collect_probe_reports()` adapter function;
- the `ProbeReport` protocol declares at minimum: `digest_hex16:
  str`, `false_positive_count: int`, `false_negative_count: int`,
  `module_name: str`;
- every existing probe report dataclass passes
  `isinstance(report, ProbeReport)` at runtime;
- every existing probe report dataclass has
  `module_name: ClassVar[str] = "<canonical_name>"` and no other
  modification;
- no probe module's runner behavior changes; no probe report's
  existing field is added, removed, or renamed;
- the static-audit fixture
  `brain/development/fixtures/probe_report_protocol_static_audit.py`
  verifies that all four probe report classes have the expected
  `module_name` constant and the four ProbeReport attributes;
- README, INVARIANT_CATALOG, tools/catalog.py, and
  brain/_catalog_ids.py agree on catalog v0.38; the only catalog
  delta vs v0.37 is +1 STRUCTURAL row `I-PROBE-01`;
- `python3 -m brain.development.proto_speech_acquisition` reports
  10/10 PASS, fp=0, fn=0, digest `f6a83b9caef0ac17`;
- `python3 -m brain.development.agent_benchmark` reports identical
  A1..A15 totals and digests to the v0.37 baseline (137 / 136 PASS /
  1 WARN / 0 FAIL);
- `python3 -m brain.invariants run` is fully green;
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report
  5/5 PASS;
- `real_model_calls == 0`; `cache_writes == 0`;
  `forbidden_term_hits == 0`;
- a single PR is opened with base `main` and head
  `campaign/phase3-32-mainline-reconciliation`;
- the PR is NOT merged automatically;
- no new behavioral feature, runtime module beyond
  `probe_report_protocol.py`, fixture beyond
  `probe_report_protocol_static_audit.py`, catalog row beyond
  `I-PROBE-01`, or benchmark axis is introduced;
- no theory semantics are changed;
- non-claim discipline is preserved.
