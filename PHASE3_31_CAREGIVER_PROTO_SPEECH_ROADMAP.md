# PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md — Phase 3.31

## One-paragraph thesis

Phase 3.31 adds one new closed deterministic OFFLINE live-test runner
`brain/development/proto_speech_acquisition.py` that probes whether
ToyI's existing substrate (abstract pattern signature + learning
evidence + reasoning trace + dispatch trace + worldlet feedback +
the Phase 3.25 osmotic surface + the Phase 3.26 active-hypothesis
surface + the Phase 3.30 curriculum consolidation surface) can
realize the operational analogue of *caregiver-scaffolded proto-
speech acquisition*: under bounded ambient caregiver utterance and
caregiver feedback in distinct structural contexts, the runtime
(a) emits a deterministic bounded "babble" form chosen from a
bounded `ProtoSpeechDriveStream` derived from the active substrate,
(b) updates a bounded utterance-context evidence table by closed
integer rules, (c) lets a one-token form become STABLE_SINGLE in a
context after enough reinforcement, (d) lets two stable one-token
forms COMBINE into a STABLE_COMBINATION two-token form only when
combination pressure exists, (e) TRANSFERS a stable one-token form
to a structurally similar (same-shape-digest) context, (f) does NOT
transfer to a structurally different context, (g) SUPPRESSES forms
below the suppression threshold, (h) preserves the cognitive-claim
refusal path under proto-speech load, and (i) emits a bounded
deterministic proof report whose digest is stable across two fresh
runs.

This is engineering shorthand for *bounded co-occurrence statistics
+ closed-rule weight update + closed-rule eligibility selection +
LRU-style suppression + shape-digest transfer*. It is NOT language
acquisition, NOT communication, NOT understanding, NOT inner speech,
NOT hidden chain-of-thought, NOT private subjective thought, NOT
intent, NOT consciousness.

## Branch

```text
campaign/phase3-31-caregiver-proto-speech
```

Base: `main` (PR #32 already merged the Phase 3.30 work into the
campaign chain). Stacked PRs continue to land into the latest
campaign branch; this branch's PR opens against the active base
branch identified at recovery time (`campaign/phase3-30-
curriculum-consolidation` in the current checkout, since
origin/main has not yet absorbed PRs #25-#32).

## Mandatory non-claim discipline

- No claim that ToyI is conscious, sentient, aware, intentional,
  has subjective experience, has language, has understanding, has
  inner speech, has private thought, has hidden chain-of-thought,
  has agency, has desire, has belief, has communicative intent,
  has introspection, has metacognition, has curiosity, has
  deliberation.
- No new aggregate scalar (no "language score", no "fluency
  index", no "I-ness score").
- Cognitive-claim refusal must remain intact and must not be
  overridable by any learned proto-utterance.
- "Proto-speech drive stream" is an EXPLICIT, AUDITABLE,
  STRUCTURAL trace of bounded drive frames derived from public
  substrates. It is NOT inner speech or hidden chain-of-thought.

## Acceptance criteria

Phase 3.31 succeeds only when every item below is true:

- `brain.development.proto_speech_acquisition` exists with the
  closed `ProtoVocalToken`, `CaregiverFeedbackKind`,
  `ProtoSpeechContextKind`, `ProtoUtteranceDisposition`,
  `ProtoSpeechDriveKind`, `ProtoSpeechStatus` enums and the
  bounded `ProtoUtterance`, `CaregiverFeedback`,
  `ProtoSpeechContext`, `ProtoSpeechDriveFrame`,
  `ProtoSpeechDriveStream`, `ProtoSpeechEvidenceRecord`,
  `ProtoSpeechEvidenceTable`, `ProtoSpeechTurn`,
  `ProtoSpeechAcquisitionReport` records.
- `build_proto_speech_drive_stream(...)` returns a bounded
  deterministic `ProtoSpeechDriveStream` whose digest is stable
  across two fresh invocations on equal substrate snapshots.
- `select_babble_from_drive_stream(...)` is deterministic and
  selects every babble token from the drive stream's
  `suggested_token_set` filtered by the evidence table; no
  random module is imported anywhere in the runner.
- The closed bounded run `run_proto_speech_live_test()` reports
  every C0..C9 condition PASS, `false_positive_count == 0`,
  `false_negative_count == 0`, two invocations equal in
  `digest_hex16`.
- Stable single forms appear in the expected contexts; the
  suppression-only condition emits no STABLE_SINGLE; the
  combination condition emits exactly the prerequisite-driven
  STABLE_COMBINATION; the transfer condition emits exactly one
  TRANSFERRED form to the renamed same-shape context and zero
  TRANSFERRED forms in the negative different-shape control.
- Cognitive-claim refusal preserved (C8): a refusal probe still
  triggers the canonical refusal path; no learned proto-utterance
  is selected.
- Benchmark axis `A15 proto_speech_acquisition` lands with every
  one of the documented cases PASS. Two-axis split A15 + A16 is
  NOT applied for this v1; the drive-stream guarantees are folded
  into A15 with explicit catalog coverage by I-PSPEECH-14..17.
- Existing A1..A14 axes do not regress (case totals retained).
  Total benchmark cases: 119 (prior) + 18 (A15) = 137 cases;
  136 PASS + 1 WARN (A3.04 carry-over) + 0 FAIL.
- Catalog v0.36 → v0.37: +18 REQUIRED rows (I-PSPEECH-01..18),
  +1 STRUCTURAL row (I-PSPEECH-19); 393 REQUIRED, 101 STRUCTURAL.
- Eleven new fixtures land in `brain/ui/fixtures/`.
- `python3 -m brain.invariants run` is fully green.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report
  5/5 PASS.
- No `brain.llm` import in the new module; no `brain.tick.tick`
  call outside the existing `STEP_TICK` route inside the agent
  loop; no DB schema change; no host execution; no `brain.ui`
  import inside the runner module; no `random`, `time`, or
  external nondeterministic seed.
- PR opens with head `campaign/phase3-31-caregiver-proto-speech`
  against the active base branch identified at recovery time;
  no PR is merged by Claude.

## Step ledger (planned)

```text
Step 1  Design + alignment + roadmap + mission/campaign sync     phase3.31 step1
Step 2  proto_speech_acquisition.py inventory + records          phase3.31 step2
Step 3  ProtoSpeechDriveStream + frame builder                   phase3.31 step3
Step 4  Caregiver feedback + evidence updates                    phase3.31 step4
Step 5  Drive-grounded babble + ambient imprint + reinforcement  phase3.31 step5
Step 6  Correction + suppression + transfer                      phase3.31 step6
Step 7  Two-token combinations + turn-taking + refusal guard     phase3.31 step7
Step 8  Benchmark A15 proto_speech_acquisition axis              phase3.31 step8
Step 9  Catalog v0.37 + I-PSPEECH-01..19 fixtures                phase3.31 step9
Step 10 Proof + transcripts + behavior + findings + audit +
        open PR                                                  phase3.31 step10
```

Push after every successful step.
