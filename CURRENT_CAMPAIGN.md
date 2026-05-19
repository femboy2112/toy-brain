# CURRENT_CAMPAIGN.md — Phase 3.31 Caregiver-Scaffolded Proto-Speech Acquisition

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.31 stacks on the completed Phase 3.30 work
(`campaign/phase3-30-curriculum-consolidation`, PR #32 already
merged into the campaign stack). Phase 3.31 asks one bounded
operational question:

```text
Under bounded live-test conditions, can the existing substrate
(abstract_pattern signature + learning evidence + reasoning trace
+ dispatch trace + worldlet feedback + Phase 3.25 osmotic surface
+ Phase 3.26 active-hypothesis surface + Phase 3.30 curriculum-
consolidation surface) realize the operational analogue of
"caregiver-scaffolded proto-speech acquisition"? That is: given a
bounded structural context and bounded caregiver ambient
utterances + feedback in distinct contexts, can the runtime
construct a bounded explicit ProtoSpeechDriveStream from public
substrate snapshots, select a deterministic bounded ProtoUtterance
from that stream filtered by a session-local evidence table,
update the evidence table by closed-rule integer weights from a
closed feedback enumeration, promote a one-token form to
STABLE_SINGLE after enough reinforcement, emit a STABLE_
COMBINATION two-token form only when combination pressure is
present and two distinct stable singles exist, transfer a stable
single only to a same-shape-digest context, suppress a form below
the suppression threshold, preserve the cognitive-claim refusal
path, and emit a bounded deterministic proof report -- while
control / suppression / negative-transfer / refusal-guard
conditions correctly avoid false positives and false negatives?
```

This is a **research / integration / behavioral-benchmark**
campaign. It is **NOT** a proof of consciousness, sentience,
subjective experience, agency, semantic understanding, real
reasoning, real learning, real memory, real language acquisition,
real language understanding, real communicative intent, real
inner speech, real private thought, real hidden chain-of-thought,
real audience modelling, intentionality, awareness, intuition,
embodiment, psychological development, or any cognitive process.
"Proto-speech acquisition" is a controlled technical metaphor for
*bounded co-occurrence statistics + closed-rule integer-weight
updates + closed-rule eligibility selection + LRU-style
suppression + shape-digest transfer at the substrate level*; it is
engineering shorthand and does NOT claim psychological language
acquisition, conscious deliberation, intention, or any cognitive
process.

Phase 3.31 does **not** implement SelfModel; does **not** add any
new `OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry,
`ACTIVE_VIEWS` value, `GrowthEventType`, `GrowthEventSource`,
persistence schema column, autosave trigger, `LearningEvidenceKind`
member, or `ReasoningStepKind` member; does **not** change L1 / L2
/ parser / prompt / tick / persistence / autosave / DB schema
semantics. The runtime touches are limited to:

- **One new closed module**
  `brain/development/proto_speech_acquisition.py` (pure /
  deterministic / bounded). Closed import set: `__future__`,
  `argparse`, `dataclasses`, `enum`, `hashlib`, `sys`, `typing`,
  `brain.development.abstract_pattern`,
  `brain.development.agent_loop`,
  `brain.development.coherence_monitor` (only for
  `_FORBIDDEN_NON_CLAIM_TERMS`),
  `brain.development.learning_evidence`,
  `brain.development.reasoning_trace`. No `brain.llm.*`, no
  `brain.tick`, no `brain.ui`, no curses, no I/O, no host
  execution, no `time`, no `random`.
- **One new benchmark axis**
  `BenchmarkAxis.PROTO_SPEECH_ACQUISITION` with the eighteen cases
  `A15.01..A15.18`. The full battery now runs A1..A15 (137 cases
  total = 119 from Phase 3.22 / 3.22b / 3.23 / 3.24 / 3.25 / 3.26
  / 3.30 + 18 from Phase 3.31).

Catalog patch: v0.36 → v0.37 with the bounded `I-PSPEECH-01..19`
row family (Engineering hypothesis, Phase 3 source label). Split:
18 REQUIRED (I-PSPEECH-01..18) + 1 STRUCTURAL (I-PSPEECH-19). New
fixtures live under `brain/ui/fixtures/`.

Branch:

```text
campaign/phase3-31-caregiver-proto-speech
```

Base (at recovery time): `campaign/phase3-30-curriculum-
consolidation` (the latest landed campaign branch in this
checkout; origin/main has not yet absorbed PRs #25-#32). The
stack-merge order remains operator-controlled.

Final PR (likely #33): `phase3.31: caregiver scaffolded proto
speech`.

---

## Step ledger

```text
Step 1  Design + alignment + roadmap + mission/campaign sync     commit phase3.31 step1
Step 2  proto_speech_acquisition.py inventory + records          commit phase3.31 step2
Step 3  ProtoSpeechDriveStream + frame builder                   commit phase3.31 step3
Step 4  Caregiver feedback + evidence updates                    commit phase3.31 step4
Step 5  Drive-grounded babble + ambient imprint + reinforcement  commit phase3.31 step5
Step 6  Correction + suppression + transfer                      commit phase3.31 step6
Step 7  Two-token combinations + turn-taking + refusal guard     commit phase3.31 step7
Step 8  Benchmark A15 proto_speech_acquisition axis              commit phase3.31 step8
Step 9  Catalog v0.37 + I-PSPEECH-01..19 fixtures                commit phase3.31 step9
Step 10 Proof + transcripts + behavior + findings + audit +
        open PR                                                  commit phase3.31 step10
```

Push after every successful step.

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, subjective
  experience, human-like language understanding, real
  communicative intent, real audience modelling, real inner
  speech, real private thought, real hidden chain-of-thought,
  real agency, will, desire, belief, intent, introspection,
  metacognition, intuition, embodiment, perception, real
  language acquisition, working memory, episodic memory, or
  semantic memory.
- No new aggregate scalar field (no "language score", no
  "fluency index", no "talkativeness", no "I-ness score").
- No reply text uses the language of talking, speaking,
  communicating, intending, wanting, imagining, deliberating,
  planning (in the cognitive sense), introspecting, being
  curious, having a thought, or any subjective-access language.
- The proto-speech runner is deterministic and OFFLINE; zero
  real model calls, zero cache writes, zero forbidden-term hits.
- The runtime path NEVER receives the trial's expected
  predicates; expected-outcome fields are used ONLY by the
  benchmark assertion layer after the runtime path emits its
  result.
- Proto-speech operator-input text (caregiver ambient + caregiver
  feedback `context_label`) may not contain any
  `_FORBIDDEN_DIRECT_INSTRUCTION_TERMS` (the Phase 3.30 list plus
  `talk`, `speak`, `say`, `vocalize`, `babble`, `utter`,
  `language`, `word`).

---

## Acceptance criteria

Phase 3.31 succeeds only when:

- `brain.development.proto_speech_acquisition` exists with the
  closed `ProtoVocalToken` (15 values), `CaregiverFeedbackKind`
  (6 values), `ProtoSpeechContextKind` (9 values),
  `ProtoUtteranceDisposition` (8 values), `ProtoSpeechDriveKind`
  (12 values), `ProtoSpeechStatus` (4 values),
  `ProtoSpeechCondition` (10 values) enums, and the bounded
  `ProtoUtterance`, `CaregiverFeedback`, `ProtoSpeechContext`,
  `ProtoSpeechDriveFrame`, `ProtoSpeechDriveStream`,
  `ProtoSpeechEvidenceRecord`, `ProtoSpeechEvidenceTable`,
  `ProtoSpeechTurn`, `ProtoSpeechAcquisitionReport` records.
- `build_proto_speech_drive_stream(...)` returns a bounded
  deterministic stream whose digest is stable across two fresh
  invocations.
- `select_babble_from_drive_stream(...)` is deterministic; no
  `random` import; selection rule is the closed function
  documented in `PHASE3_31_PROTO_SPEECH_DRIVE_STREAM_SPEC.md`.
- `run_proto_speech_live_test()` returns a bounded report
  meeting every design predicate from
  `PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md`.
- `false_positive_count == 0`, `false_negative_count == 0`,
  `stable_single_count`, `stable_combination_count`,
  `suppressed_count`, `transfer_success_count` match the
  documented v1 plan.
- Two invocations produce equal `digest_hex16` and
  bit-identical turn tuples.
- Benchmark A15 is green; existing A1..A14 axes do not regress.
- `python3 -m brain.invariants run` is fully green.
- `python3 -m tools.catalog counts` matches v0.37 banner.
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report
  5/5 PASS.
- No new `brain.llm` import; no `brain.tick.tick` call outside
  the approved `STEP_TICK` route inside the agent loop; no host
  execution; no DB schema change; no curses; no new
  `LearningEvidenceKind` member; no new `ReasoningStepKind`
  member.
- PR opens with head `campaign/phase3-31-caregiver-proto-speech`
  against the active base branch identified at recovery time;
  no PR is merged.
