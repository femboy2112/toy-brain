# PHASE3_21_DEVELOPMENTAL_TRAJECTORY_BEHAVIOR_REPORT.md

## Purpose

Aggregate the cross-milestone behavior observed by Step 7 into a
single review-ready document. The detailed per-milestone
narrative lives in `PHASE3_21_MILESTONE_LOG.md`; this doc
summarizes the cross-cutting properties.

---

## 1. Run configuration

```text
Catalog version on disk        : v0.29
Branch                         : campaign/phase3-21-developmental-trajectory
HEAD at run time               : c25d726 (Step 6 implementation)
                                 + f035836 (Step 7 log) on disk
Python                         : 3.12
Real model mode                : not used (OFFLINE default preserved)
LLM client                     : never constructed
Stage A / B / C.1 bridges      : not used
```

---

## 2. Cross-milestone aggregate

```text
total milestones                              : 10
PASS                                          : 10
WARN                                          : 0
FAIL                                          : 0
NOT_APPLICABLE                                : 0
determinism failures (across two invocations) : 0
assert_state_invariants failures              : 0
cumulative real model calls                   : 0
cumulative L1 / L2 cache writes               : 0
canonical _FORBIDDEN_NON_CLAIM_TERMS hits     : 0 across
  - harness module source
  - MODULE_PRODUCED_STRINGS entries
  - every produced summary string
  - every fixture file
  - this behavior report doc
```

---

## 3. Substrate-usage map

```text
milestone                       | uses    | uses    | uses    | LLM | cache | tick |
                                | P3.18   | P3.19   | P3.20   |     | write |      |
m01_reflexive_baseline          |   -     |   -     |   -     |  -  |   -   |  -   |
m02_habituation                 | window  |   -     |   -     |  -  |   -   |  -   |
m03_recognition                 |   -     |   -     |   -     |  -  |   -   |  -   |
m04_rehearsal                   | window  |   -     |   -     |  -  |   -   |  -   |
m05_pattern_self_feedback       | window  | PLEDGER |   -     |  -  |   -   |  -   |
m06_structural_self_monitoring  | window  |   -     | COH     |  -  |   -   |  -   |
m07_multi_modal_integration     | window  | PLEDGER | COH/P&C |  -  |   -   |  -   |
m08_saturation_novelty          | window  |   -     |   -     |  -  |   -   |  -   |
m09_cross_input_differentiation | window  | PLEDGER | COH/P&C |  -  |   -   |  -   |
m10_sustained_behavior          | window  | PLEDGER | COH/P&C |  -  |   -   |  -   |
```

Every milestone uses only the public surfaces shipped by prior
Phase 3 campaigns. No new core runtime code was needed. The
harness is a strict consumer; the Lean spec is not contradicted
(every new row is Engineering hypothesis).

---

## 4. Chunk-count formula table

```text
milestone                       | dispatched chunks  | observed stored chunks
m01_reflexive_baseline          |   1                |   1
m02_habituation                 |  11                |  11
m03_recognition                 |   2                |   2
m04_rehearsal                   |  11                |  11
m05_pattern_self_feedback       |  21                |  21
m06_structural_self_monitoring  |  21                |  21
m07_multi_modal_integration     |  31                |  31
m08_saturation_novelty          | 256                | 256 (saturated)
m09_cross_input_differentiation |  62                |  62
m10_sustained_behavior          | 453                | 256 (saturated)
```

M08 and M10 deliberately exercise the bounded-saturation
behavior. The Pattern Ledger and Growth Ledger continue to
correctly bound their entries at their respective caps under
sustained load; no eviction occurs (the documented Phase 3.13
Growth Ledger behavior, and the documented Phase 3.7
stream-history bounded behavior).

---

## 5. Pattern Ledger entry shape table

```text
milestone                       | entries | distinct ids | family decomposition
m01_reflexive_baseline          |   1     |     1        | seed
m02_habituation                 |   1     |     1        | seed (recurrence=12)
m03_recognition                 |   2     |     2        | two seeds
m04_rehearsal                   |   1     |     1        | seed (recurrence=12)
m05_pattern_self_feedback       |   5     |     5        | seed + pledger family (1..4 entries)
m06_structural_self_monitoring  |   2     |     2        | seed + 1 cohmon entry
m07_multi_modal_integration     |   5     |     5        | seed + pledger family + cohmon family
m08_saturation_novelty          |   2     |     2        | saturated seed + 1 novel seed
m09_cross_input_differentiation |   8     |     8        | 2 seeds + their feedback families
m10_sustained_behavior          |   9     |     9        | 3 seeds + their feedback families
```

Pattern entry counts are deterministic per (mode, input) but
vary across input families because the structural signature
function differentiates inputs at the chunk-shape level.

---

## 6. Determinism

The static-audit fixture (`I-DEVMILE-11`) confirms:

- each per-milestone helper produces bit-identical
  `MilestoneResult` when invoked twice with the same
  `seed_offset` (default 0 and probe 7);
- `run_all_milestones()` produces bit-identical 10-tuples across
  two invocations.

Step 7's log run was reproducible on demand.

---

## 7. Cross-campaign integrity

- catalog v0.28 -> v0.29: REQUIRED 284 -> 294; STRUCTURAL 91 -> 92.
- `tools/catalog.py EXPECTED_COUNTS` matches; `brain/_catalog_ids.py`
  is in sync; `tools/check_all.sh` exits clean.
- No existing runtime file was modified.
- `brain/tick.py` untouched.
- L1 / L2 caches untouched.
- Parser / prompt / schema / autosave untouched.
- All Phase 3.18 / 3.19 / 3.20 invariants remain green
  (`I-PWND-01..02`, `I-IFBK-01..02`, `I-CFBK-01..02` continue
  to pass).

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used
Stage B limited-write collaboration: not used
Stage C.1 flow orchestration       : not used
Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```

---

## 9. Verdict

```text
Phase 3.21 behavior report : PASS.
```

The ten-milestone trajectory completes end-to-end on a fresh
runtime substrate. Determinism, invariant safety, non-claim
discipline, and zero-model-call discipline all hold.

---

## 10. Next artifact

`docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_FINDINGS.md`
— the campaign findings / triage.
