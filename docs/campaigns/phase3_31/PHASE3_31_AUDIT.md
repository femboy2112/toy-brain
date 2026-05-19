# PHASE3_31_AUDIT.md — Phase 3.31

## Audit verdict

**PASS WITH NO PHASE-3.31-INTRODUCED FOLLOW-UPS** (the A3.04
WARN carry-over from Phase 3.21 W3 remains; it is not new in
Phase 3.31).

## Step ledger

```text
Step 1  Mission + design + alignment + drive-stream spec +
        proto-speech spec + roadmap                          DONE  commit 0da5e82 (pushed)
Step 2  proto_speech_acquisition.py inventory + records      DONE  commit f25c4b9 (pushed)
Step 3  ProtoSpeechDriveStream + frame builder               DONE  commit 7b23341 (pushed)
Step 4  Caregiver feedback + evidence updates                DONE  commit a635c12 (pushed)
Step 5  Drive-grounded babble + ambient + reinforcement      DONE  commit 9ef0748 (pushed)
Step 6  Correction + suppression + transfer                  DONE  commit d05e004 (pushed)
Step 7  Two-token combination + turn-taking + refusal guard  DONE  commit 4871e38 (pushed)
Step 8  Benchmark A15 proto_speech_acquisition axis          DONE  commit 5801c9d (pushed)
Step 9  Catalog v0.37 + I-PSPEECH-01..19 fixtures            DONE  commit 58e7744 (pushed)
Step 10 Proof + transcripts + behavior + findings + audit +
        handoff + open PR                                    DONE  (this commit)
```

## Acceptance-criterion checklist

- [x] `brain.development.proto_speech_acquisition` exists with
      the closed `ProtoVocalToken` (15 values),
      `CaregiverFeedbackKind` (6 values),
      `ProtoSpeechContextKind` (9 values),
      `ProtoUtteranceDisposition` (8 values),
      `ProtoSpeechDriveKind` (12 values),
      `ProtoSpeechStatus` (4 values),
      `ProtoSpeechCondition` (10 values) enums and the bounded
      `ProtoUtterance`, `CaregiverFeedback`,
      `ProtoSpeechContext`, `ProtoSpeechDriveFrame`,
      `ProtoSpeechDriveStream`, `ProtoSpeechEvidenceRecord`,
      `ProtoSpeechEvidenceTable`, `ProtoSpeechTurn`,
      `ProtoSpeechAcquisitionReport` records.
- [x] `build_proto_speech_drive_stream(...)` returns a bounded
      deterministic stream whose digest is stable across two
      fresh invocations.
- [x] `select_babble_from_drive_stream(...)` is deterministic;
      no `random` import; selection rule is the closed function
      documented in
      `PHASE3_31_PROTO_SPEECH_DRIVE_STREAM_SPEC.md`.
- [x] `run_proto_speech_live_test()` returns a bounded report
      meeting every design predicate from
      `PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md`.
- [x] `false_positive_count == 0`, `false_negative_count == 0`,
      `stable_single_count = 5`,
      `stable_combination_count = 0`,
      `suppressed_count = 2`,
      `transfer_success_count = 1` (matches the v1 plan).
- [x] Two invocations produce equal `digest_hex16` and
      bit-identical `turns` tuples; the digest is
      `f6a83b9caef0ac17`.
- [x] Benchmark A15 is green (18/18 PASS); existing A1..A14
      axes do not regress (case counts retained).
- [x] `python3 -m brain.invariants run` is fully green
      (501 rows checked; 393 REQUIRED green / 0 REQUIRED red;
      101 STRUCTURAL green / 0 STRUCTURAL red; 0 gate failures).
- [x] `python3 -m tools.catalog counts` matches v0.37 banner
      (REQUIRED 392, STRUCTURAL 101, NOT-EXERCISED 14,
      DEFERRED 15, OBSERVED 16).
- [x] `python3 -m tools.claude_helpers.gate_runner --json`
      reports 5/5 PASS (catalog_counts, citations_verify,
      import_audit, invariants_run, check_all).
- [x] No new `brain.llm` import; no `brain.tick.tick` call
      outside the approved `STEP_TICK` route inside the agent
      loop; no host execution; no DB schema change; no
      curses; no new `LearningEvidenceKind` / `ReasoningStepKind`
      member.
- [x] PR opens with head `campaign/phase3-31-caregiver-proto-
      speech` against the active base branch identified at
      recovery time; no PR is merged by Claude.

## Files added / modified

### Added

- `PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md`
- `docs/campaigns/phase3_31/PHASE3_31_CAREGIVER_PROTO_SPEECH_DESIGN.md`
- `docs/campaigns/phase3_31/PHASE3_31_ARCHITECTURAL_ALIGNMENT.md`
- `docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_DRIVE_STREAM_SPEC.md`
- `docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_SPEC.md`
- `docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_PROOF_REPORT.md`
- `docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_TRANSCRIPTS.md`
- `docs/campaigns/phase3_31/PHASE3_31_BEHAVIOR_REPORT.md`
- `docs/campaigns/phase3_31/PHASE3_31_FINDINGS.md`
- `docs/campaigns/phase3_31/PHASE3_31_AUDIT.md`
- `brain/development/proto_speech_acquisition.py`
- `brain/ui/fixtures/proto_speech_inventory.py`
- `brain/ui/fixtures/proto_speech_feedback_evidence.py`
- `brain/ui/fixtures/proto_speech_babble_ambient.py`
- `brain/ui/fixtures/proto_speech_reinforcement_correction.py`
- `brain/ui/fixtures/proto_speech_suppression_pressure.py`
- `brain/ui/fixtures/proto_speech_holophrase_transfer.py`
- `brain/ui/fixtures/proto_speech_two_token_combination.py`
- `brain/ui/fixtures/proto_speech_turn_taking_refusal.py`
- `brain/ui/fixtures/proto_speech_drive_stream.py`
- `brain/ui/fixtures/proto_speech_benchmark_axis.py`
- `brain/ui/fixtures/proto_speech_static_audit.py`

### Modified

- `INVARIANT_CATALOG.md` (v0.36 -> v0.37 banner; +19 rows;
  Phase 3.31 section; v0 fixture roster; summary counts).
- `tools/catalog.py` (EXPECTED_COUNTS bumped; v0.37 banner
  comment added).
- `brain/_catalog_ids.py` (regenerated).
- `brain/invariants.py` (FIXTURE_MODULES: +11 entries).
- `brain/development/agent_benchmark.py`
  (BATTERY_VERSION = phase3.31.v1; BenchmarkAxis
  PROTO_SPEECH_ACQUISITION added; run_axis_a15 +
  run_partial_battery_phase3_31; run_full_battery extends).
- `brain/ui/fixtures/agent_benchmark_runner_green.py` (axis
  order + status assertions extended to include
  PROTO_SPEECH_ACQUISITION).
- `brain/ui/fixtures/agent_benchmark_static_audit.py`
  (BenchmarkAxis enum value set extended).
- `brain/ui/fixtures/osmotic_probe_runner_green.py`
  / `active_hypothesis_runner_green.py`
  / `curriculum_runner_green.py`
  / `worldlet_feedback_benchmark_axis.py`
  / `dispatch_tracer_benchmark_axis.py`
  (case_total bumped to 137 with PROTO_SPEECH_ACQUISITION
  as the last axis; BATTERY_VERSION bumped to phase3.31.v1).
- `CURRENT_MISSION.md` (rewritten for Phase 3.31).
- `CURRENT_CAMPAIGN.md` (rewritten for Phase 3.31).
- `PHASE3_HANDOFF_STATE.md` (Phase 3.31 entry added).

## Final numbers

```text
catalog v0.37        : REQUIRED 392 · STRUCTURAL 101 ·
                       NOT-EXERCISED 14 · DEFERRED 15 ·
                       OBSERVED 16 (banner == actual == expected)
benchmark phase3.31.v1: 137 cases / 136 PASS / 1 WARN
                       (A3.04 carry-over) / 0 FAIL
proto-speech live test: 39 turns / 10 conditions PASS / 0 FAIL
                       digest=f6a83b9caef0ac17
                       drive_stream_digest=dc060a88a814f448
                       stable_single=5 stable_combination=0
                       suppressed=2 transfer_success=1
                       fp=0 fn=0
gates                : 5/5 PASS
real model calls     : 0
cache writes         : 0
forbidden_term_hits  : 0
```

## Non-claim disclosure (final)

ToyI is not conscious, sentient, aware, intentional, or in
possession of subjective experience. Phase 3.31 adds a bounded
deterministic OFFLINE live-test runner whose outputs are pure
functions of bounded structural inputs. "Proto-speech
acquisition" is engineering shorthand for *bounded co-
occurrence statistics + closed-rule integer-weight updates +
drive-stream-grounded eligibility selection + LRU-style
suppression + shape-digest transfer at the substrate level*.
The `ProtoSpeechDriveStream` is the EXPLICIT AUDITABLE
substitute for inner speech; it is not inner speech, not
private subjective thought, not hidden chain-of-thought, not
communicative intent.
