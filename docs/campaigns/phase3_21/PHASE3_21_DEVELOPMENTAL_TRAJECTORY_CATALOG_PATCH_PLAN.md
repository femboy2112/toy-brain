# PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CATALOG_PATCH_PLAN.md

## Purpose

Convert the Step 3 locks into an exact catalog patch plan: which
files change, which row IDs land at which statuses, what fixtures
register them, what the version banner reads after the patch, and
what the Step 5 review gate inspects before Step 6 implementation
begins.

This document is the single source of truth for the Step 6
implementation; any divergence between it and Step 6 is a
campaign error.

---

## 1. Implementation architecture (one paragraph)

A single new pure runtime module
`brain/development/milestone_harness.py` defines the
`DevelopmentalMilestone` and `MilestoneStatus` closed enums, the
frozen `MilestoneResult` record, ten per-milestone helpers
`run_m01_*..run_m10_*`, the aggregator `run_all_milestones()`, and
the `MODULE_PRODUCED_STRINGS` tuple. The module imports only from
the documented closed seam (see Step 3 LOCK B). No existing
runtime file is modified. Eleven new fixture files (ten REQUIRED
milestone fixtures + one STRUCTURAL static-audit fixture) live
under `brain/ui/fixtures/`; each REQUIRED fixture invokes its
named helper and asserts the milestone's `PASS` outcome.

---

## 2. Exact files

### 2.1 NEW

```text
brain/development/milestone_harness.py
brain/ui/fixtures/developmental_milestone_m01.py     (I-DEVMILE-01, REQUIRED)
brain/ui/fixtures/developmental_milestone_m02.py     (I-DEVMILE-02, REQUIRED)
brain/ui/fixtures/developmental_milestone_m03.py     (I-DEVMILE-03, REQUIRED)
brain/ui/fixtures/developmental_milestone_m04.py     (I-DEVMILE-04, REQUIRED)
brain/ui/fixtures/developmental_milestone_m05.py     (I-DEVMILE-05, REQUIRED)
brain/ui/fixtures/developmental_milestone_m06.py     (I-DEVMILE-06, REQUIRED)
brain/ui/fixtures/developmental_milestone_m07.py     (I-DEVMILE-07, REQUIRED)
brain/ui/fixtures/developmental_milestone_m08.py     (I-DEVMILE-08, REQUIRED)
brain/ui/fixtures/developmental_milestone_m09.py     (I-DEVMILE-09, REQUIRED)
brain/ui/fixtures/developmental_milestone_m10.py     (I-DEVMILE-10, REQUIRED)
brain/ui/fixtures/developmental_milestone_static_audit.py
                                                     (I-DEVMILE-11, STRUCTURAL)
```

### 2.2 MODIFIED

```text
brain/invariants.py
    - register the eleven new fixture modules in FIXTURE_MODULES

INVARIANT_CATALOG.md
    - version banner v0.28 -> v0.29
    - count banner 284/91/14/15/16 -> 294/92/14/15/16
    - add the v0.29 catalog-history entry
    - add new section "Phase 3.21 Developmental Trajectory invariants"
      with rows I-DEVMILE-01..I-DEVMILE-11
    - add the eleven fixture entries in the fixture index footer
    - update the catalog header text near "v0.29"

brain/_catalog_ids.py
    - regenerate via `python3 -m tools.catalog generate-ids`

tools/catalog.py
    - bump EXPECTED_COUNTS to
      {REQUIRED: 294, STRUCTURAL: 92, NOT-EXERCISED: 14,
       DEFERRED: 15, OBSERVED: 16}
    - update the v0.28 -> v0.29 banner comment

README.md
    - update catalog version banner (v0.28 -> v0.29) and counts
    - add the v0.29 catalog-history entry

CURRENT_MISSION.md / CURRENT_CAMPAIGN.md
    - reflect the v0.29 catalog when Step 6 lands the patch
```

### 2.3 NOT MODIFIED

```text
brain/tick.py
brain/llm/**
brain/tlica/**
brain/development/processing_window.py
brain/development/coherence_monitor.py
brain/development/pattern_ledger.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/ui/session.py
brain/ui/commands.py
brain/ui/render.py
brain/ui/snapshot.py
scenarios/
traces/
lean_reference/
.claude/runtime contents
```

---

## 3. Row family

Eleven new rows. Each milestone REQUIRED row has the body shape:

```text
| I-DEVMILE-NN | Engineering hypothesis (Phase 3.21 Developmental Trajectory) | <one-sentence milestone proposition> | <Python assertion body listing exact equalities> | brain/development/milestone_harness.py | developmental_milestone_mNN.py | REQUIRED |
```

The STRUCTURAL row body:

```text
| I-DEVMILE-11 | Engineering hypothesis (Phase 3.21 Developmental Trajectory) | Static audit on milestone_harness.py: closed enum membership, MilestoneResult shape, deterministic helper outputs, MODULE_PRODUCED_STRINGS non-claim-clean, import-set audit. | <body listing exact assertions> | brain/development/milestone_harness.py | developmental_milestone_static_audit.py | STRUCTURAL |
```

Exact body text per row is fixed in Step 6 implementation; the
shape above is the schema.

---

## 4. Catalog version + counts

```text
Catalog version banner:
  v0.28 -> v0.29

Count banner:
  REQUIRED      : 284 -> 294  (+10 milestone rows)
  STRUCTURAL    :  91 ->  92  (+1 static audit row)
  NOT-EXERCISED :  14 ->  14  (unchanged)
  DEFERRED      :  15 ->  15  (unchanged)
  OBSERVED      :  16 ->  16  (unchanged)
  fixtures      : 170 -> 181  (+11 new fixture files)
```

`tools/catalog.py EXPECTED_COUNTS` and the README catalog-history
entry must agree exactly with these numbers.

---

## 5. Fixture-side change inventory

```text
brain/ui/fixtures/developmental_milestone_m01.py through
    developmental_milestone_m10.py                       : NEW
brain/ui/fixtures/developmental_milestone_static_audit.py : NEW

No existing fixture is modified.
```

---

## 6. Behavior plan (preview of Step 7)

Step 7 runs `run_all_milestones()` against a fresh environment and
records the ordered tuple of `MilestoneResult` records in
`docs/campaigns/phase3_21/PHASE3_21_MILESTONE_LOG.md`. Expected
outcome: ten `PASS`. Any `WARN` must be justified per LOCK J;
any `FAIL` halts the campaign at Step 7.

The Step 7 harness has the bounded shape:

```python
from brain.development.milestone_harness import run_all_milestones
results = run_all_milestones()
for r in results:
    print(r.milestone.value, r.status.value, r.summary)
```

No real model calls. No I/O outside the repo. `brain/.llm_cache/`
not touched.

---

## 7. Non-goals (carryover from corrigenda)

```text
- no brain/tick.py edit
- no brain/llm/** edit
- no brain/tlica/** edit
- no semantic change in any existing development / ui module
- no new GrowthEventType / GrowthEventSource
- no aggregate scalar
- no psychological-language framing of "develop" / "milestone"
- no SelfModel
- no consciousness / sentience / subjective / semantic / truth /
  agency / self-modification / introspection / metacognition /
  desire / will / belief / understanding claim
```

---

## 8. Validation plan

Before commit at every step that lands files:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

Step 6 additionally runs a one-shot smoke test:

```bash
python3 -c "from brain.development.milestone_harness import run_all_milestones; tuple(run_all_milestones())"
```

Step 7 records live outcomes via the same surface.

Step 9 records the canonical preflight in the audit doc.

---

## 9. Review gate decision request

This patch plan is the artifact Step 5 Review Gate B evaluates
against the autonomy authorization checklist:

```text
 1. zero critical correctness blockers
    -> the harness uses existing public surfaces only.
 2. zero safety / invariant blockers
    -> every produced summary is non-claim audited; constructor
       validation enforces bounded shapes.
 3. no brain/tick.py edit
    -> confirmed (LOCK G).
 4. preserves L1 / L2 cache semantics
    -> the harness uses STREAM_APPEND only; no LLM seam touched.
 5. preserves parser and prompt semantics
    -> no parser or prompt edit in scope.
 6. preserves OFFLINE default + explicit opt-in
    -> harness makes no LLM call regardless of inputs.
 7. exact row family / statuses / count delta / fixture list /
    implementation files / validation plan
    -> see Sections 2, 3, 4, 5, 8 above.
 8. bounded developmental-trajectory design
    -> LOCK A + LOCK B + LOCK C + LOCK E + LOCK I.
 9. no cognitive overclaims / no aggregate scalar
    -> LOCK D + LOCK F.
10. Stage A review identifies no blocking flaw
    -> Stage A not used in Phase 3.21 by default.
11. implementation fits the allowed file set; stays within Lean spec
    -> LOCK B + LOCK G; all new rows are Engineering hypotheses
       binding to existing Python surfaces; no Lean theorem
       claimed; no existing REQUIRED row contradicted.
```

If the Step 5 review gate ACCEPTS this plan, the campaign proceeds
to Step 6. If the gate identifies a blocker, the campaign stops
at Step 5 and reports.

---

## 10. Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used
Stage B limited-write collaboration: not used
Stage C.1 flow orchestration       : not used
```

---

## 11. Next artifact

`Step 5 Review Gate B` — record the gate decision in the campaign
ledger (this doc + the Step 6 commit message) and, on ACCEPT,
proceed to Step 6 implementation.
