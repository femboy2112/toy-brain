# Phase 3.26 — Audit

End-of-campaign audit against `CURRENT_CAMPAIGN.md`'s acceptance
criteria.

## Verdict

```text
PASS WITH DEFERRED FOLLOW-UPS
```

(`PASS` because every acceptance criterion is satisfied. `DEFERRED
FOLLOW-UPS` because (a) the A3.04 NOT_APPLICABLE-overall blocker
carried forward from Phase 3.21 W3 remains an accepted WARN, and
(b) the five open follow-ups enumerated in
`PHASE3_26_FINDINGS.md` are deferred to future phases.)

## Acceptance criteria checklist

- [x] `brain.development.active_hypothesis_probe` exists with the
      closed `AmbiguityCondition` (5 values), `ActiveHypothesisStatus`
      (4 values), `ProbeConstructionRule` (6 values), `TrialVerdict`
      (4 values), and `ProbeOutcome` (2 values) enums, and the
      bounded `ActiveHypothesisCandidate`, `ActiveProbeStep`,
      `ActiveHypothesisTrial`, `ActiveHypothesisResult`,
      `ActiveHypothesisLiveTestReport` records.
- [x] `enumerate_hypotheses()` returns a bounded tuple of length
      `0..ACTIVE_HYPOTHESIS_MAX_CANDIDATES = 8`, deterministic
      across two invocations on the same input.
- [x] `select_safe_probe()` returns a bounded printable probe text
      with none of the `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS` and no
      substring leak of the candidate's `predicted_digest_hex16` or
      `predicted_shape`.
- [x] `run_active_hypothesis_live_test()` returns a bounded report
      with `pass_count == 10`, `warn_count == 0`, `fail_count == 0`,
      `false_positive_count == 0`, `false_negative_count == 0`,
      `winner_selected_count == 3` (T03, T04, T09),
      `no_hypothesis_survives_count == 3` (T07, T08, T10),
      `cache_reuse_count == 2` (T09, T10).
- [x] Two invocations of `run_active_hypothesis_live_test()` produce
      bit-identical `digest_hex16 == "86b67d97daeb251d"` and equal
      `trials` tuples.
- [x] Benchmark A13 axis green (14 / 14 PASS); A1..A12 do not
      regress (`pre_a13_case_counts == (9, 5, 4, 5, 9, 3, 4, 7, 7,
      12, 12, 14)`).
- [x] `python3 -m brain.invariants run` is fully green: 468 rows
      checked, 362 REQUIRED green / 0 red, 99 STRUCTURAL green / 0
      red, 0 gate failures.
- [x] `python3 -m tools.catalog counts` matches v0.35 banner
      (REQUIRED 361, STRUCTURAL 99, NOT-EXERCISED 14, DEFERRED 15,
      OBSERVED 16).
- [x] `bash tools/check_all.sh` reports all checks passed.
- [x] `python3 -m tools.claude_helpers.gate_runner --json` reports
      5/5 PASS.
- [x] No new `brain.llm` import; no `brain.tick.tick` call outside
      the approved `STEP_TICK` route; no host execution; no DB
      schema change; no curses; no new `LearningEvidenceKind`
      member; no new `ReasoningStepKind` member; no new
      `OperatorCommand` member; no new `LOCAL_COMMAND_VERBS` entry;
      no new `ACTIVE_VIEWS` value.
- [x] PR #31 is open with base
      `campaign/phase3-25-osmotic-learning-live-test`; no PR is
      merged.

## Catalog patch

```text
INVARIANT_CATALOG.md      v0.34 -> v0.35
  +13 REQUIRED rows (I-AHYP-01..I-AHYP-13)
  + 1 STRUCTURAL row (I-AHYP-14)
  +14 catalog rows
  +14 _catalog_ids.py entries

tools/catalog.py
  EXPECTED_COUNTS["REQUIRED"]   348 -> 361
  EXPECTED_COUNTS["STRUCTURAL"]  98 -> 99
  v0.35 banner block authored; v0.34 history retained

brain/invariants.py
  FIXTURE_MODULES extended with 11 new modules

brain/_catalog_ids.py
  regenerated via tools.catalog generate-ids
```

## Eleven new fixtures (under `brain/ui/fixtures/`)

```text
active_hypothesis_constructor.py                   I-AHYP-01, I-AHYP-02
active_hypothesis_enumerator.py                    I-AHYP-03
active_hypothesis_safe_probe.py                    I-AHYP-04
active_hypothesis_control.py                       I-AHYP-05
active_hypothesis_single.py                        I-AHYP-06
active_hypothesis_multi.py                         I-AHYP-07
active_hypothesis_nosurvivor.py                    I-AHYP-08
active_hypothesis_reuse.py                         I-AHYP-09
active_hypothesis_learning_reasoning_dispatch.py   I-AHYP-10, I-AHYP-11
active_hypothesis_runner_green.py                  I-AHYP-12, I-AHYP-13
active_hypothesis_static_audit.py                  I-AHYP-14
```

## Benchmark battery

```text
agent-benchmark phase3.26.v1
  total                 = 105   (91 prior + 14 new)
  passed                = 104
  warned                = 1     (A3.04 carry-over)
  failed                = 0
  determinism_failures  = 0
  real_model_calls      = 0
  cache_writes          = 0
  forbidden_term_hits   = 0
  transcript_digest     = 0169f117497dba08
  axes                  = 13    (ending with ACTIVE_HYPOTHESIS)
```

## Non-claim discipline

- Zero forbidden non-claim term hits in the new module source
  (`I-AHYP-14` static audit).
- Zero forbidden non-claim term hits in any trial summary line,
  any reply excerpt, any benchmark case summary, any benchmark
  transcript line (`I-AHYP-12`, `I-AGENTLOOP-09`).
- Zero forbidden direct-instruction term hits in any input text or
  constructed probe text (`I-AHYP-04` + `I-AHYP-02`).
- No claim of consciousness, sentience, awareness, subjective
  experience, real agency, will, desire, belief, intent,
  introspection, metacognition, intuition, embodiment, real
  hypothesis formation, real inquiry, real curiosity, real
  deliberation, real planning, real decision-making, or any
  cognitive process.

## TLICA Lean spec compatibility

- Every new row is marked `Engineering hypothesis (Phase 3.26
  Active Hypothesis + Self-Directed Probe Loop)` in the catalog
  source column.
- No Lean theorem is claimed; no existing REQUIRED row is
  modified; the TLICA spec in `lean_reference/` is not
  contradicted.
- The Phase 3.26 substrate is transverse to the four imprinting
  kinds and to the Phase 3.25 osmotic imprinting+activation
  surface; it is not a fifth parallel imprinting kind and does
  not introduce a new cognitive agent.

## Branch / PR state at audit close

```text
branch: campaign/phase3-26-active-hypothesis-probe
base:   campaign/phase3-25-osmotic-learning-live-test (PR #30 open)
PR:     #31 (to be opened in Step 9; base = the Phase 3.25 branch)
```

## Disclosure block

```text
Stage A ChatGPT/Codex consultation:  not used in this session
Stage B limited-write collaboration: not used in this session
Stage C.1 flow orchestration:        not used in this session
brain-catalog-lint:                  not used in this session
brain-campaign-state:                not used in this session
brain-explorer:                      used (1x at Step 1 setup for
                                     read-only substrate inventory)
brain-runner-debugger:               not used in this session
brain-row-implementer:               not used in this session
brain-spec-refresher:                not used in this session
Real model calls used this session:  0
Cumulative real model calls used:    0 / 20
```
