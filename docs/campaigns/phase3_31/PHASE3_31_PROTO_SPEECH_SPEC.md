# PHASE3_31_PROTO_SPEECH_SPEC.md — Phase 3.31

## Module

`brain/development/proto_speech_acquisition.py`.

## Closed bounded constants

```text
PROTO_SPEECH_BATTERY_VERSION       = "phase3.31.v1"
PROTO_SPEECH_TURN_ID_MAX_LEN       = 64
PROTO_SPEECH_CONTEXT_LABEL_MAX_LEN = 64
PROTO_SPEECH_TEXT_MAX_LEN          = 64
PROTO_SPEECH_EXPLAIN_MAX_LEN       = 240
PROTO_SPEECH_DIGEST_HEX_LEN        = 16
PROTO_SPEECH_MAX_TURNS_PER_CONDITION = 12
PROTO_SPEECH_MAX_TURNS_PER_REPORT  = 96
PROTO_SPEECH_MAX_FRAMES_PER_STREAM = 12
PROTO_SPEECH_SUGGESTED_SET_MAX     = 8
PROTO_SPEECH_WEIGHT_HINT_MAX       = 16
PROTO_SPEECH_WEIGHT_MIN            = -8
PROTO_SPEECH_WEIGHT_MAX            = 16
PROTO_SPEECH_EVIDENCE_TABLE_MAX    = 64
STABLE_SINGLE_THRESHOLD            = 6
STABLE_COMBINATION_THRESHOLD       = 8
SUPPRESS_THRESHOLD                 = -3
```

## Closed enums

```text
ProtoVocalToken           = BA, MA, DA, NA, LA, SAME, MORE, AGAIN,
                            NO, YES, LOOK, THIS, THAT, HELP, DONE
CaregiverFeedbackKind     = ACCEPTED, IGNORED, ECHO, CORRECTED,
                            EXPANDED, AMBIENT_ONLY
ProtoSpeechContextKind    = ABSTRACT_PATTERN, WORLDLET, REPL,
                            DISPATCH_TRACE, REASONING_TRACE,
                            LEARNING_EVIDENCE, ACTIVE_HYPOTHESIS,
                            CURRICULUM, UNKNOWN
ProtoUtteranceDisposition = BABBLE, CANDIDATE, REINFORCED,
                            SUPPRESSED, STABLE_SINGLE,
                            STABLE_COMBINATION, TRANSFERRED,
                            REJECTED
ProtoSpeechDriveKind      = LOW_EVIDENCE, RECURRENCE_PRESSURE,
                            NOVELTY_PRESSURE, TRANSFER_PRESSURE,
                            UNRESOLVED_HYPOTHESIS,
                            WORLDLET_FEEDBACK_PRESENT,
                            REPL_FEEDBACK_PRESENT,
                            CAREGIVER_AMBIENT_PRIME,
                            CAREGIVER_FEEDBACK_PRIME,
                            SUPPRESSION_PRESSURE,
                            COMBINATION_PRESSURE,
                            REFUSAL_GUARD
ProtoSpeechStatus         = PASS, WARN, FAIL, NOT_APPLICABLE
ProtoSpeechCondition      = BABBLE_BASELINE, AMBIENT_IMPRINTING,
                            FEEDBACK_REINFORCEMENT,
                            CORRECTION_SHAPING, HOLOPHRASE_TRANSFER,
                            TWO_TOKEN_COMBINATION, SUPPRESSION,
                            TURN_TAKING, REFUSAL_PRESERVED,
                            DRIVE_STREAM_PRESSURE
```

## Closed evidence-update rules

| Feedback kind | Effect on attempted form | Effect on offered form |
| --- | --- | --- |
| `ACCEPTED` | +3 | (n/a) |
| `ECHO` | +3 | (n/a) |
| `EXPANDED` | +1 | +4 |
| `CORRECTED` | -2 | +3 |
| `IGNORED` | -1 | (n/a) |
| `AMBIENT_ONLY` | (n/a) | +1 (to ambient token in current context) |

Disposition transitions:

- `weight >= STABLE_COMBINATION_THRESHOLD` AND `token_count == 2`
  → `STABLE_COMBINATION`.
- `weight >= STABLE_SINGLE_THRESHOLD` AND `token_count == 1`
  → `STABLE_SINGLE`.
- `weight <= SUPPRESS_THRESHOLD` → `SUPPRESSED`.
- Otherwise, retain prior disposition (default `CANDIDATE`).

## Conditions (battery)

Ten closed conditions: C0..C9 named in
`ProtoSpeechCondition`. Each condition runs a bounded ordered
tuple of `ProtoSpeechTurn` records. Per-turn ordering:

```text
context -> drive stream -> ToyI utterance -> caregiver feedback
        -> evidence update
```

## Verdict rule

Each condition emits a `ProtoSpeechStatus`:

- `PASS` iff every expected predicate for the condition is true
  AND `false_positive_count == 0` AND `false_negative_count == 0`.
- `FAIL` otherwise.
- `WARN` and `NOT_APPLICABLE` reserved (not used in v1 plan).

## Top-level functions

```text
build_proto_utterance(tokens, *, context_label) -> ProtoUtterance
build_proto_speech_context(...)                -> ProtoSpeechContext
build_proto_speech_drive_stream(...)           -> ProtoSpeechDriveStream
update_drive_stream_after_feedback(...)        -> ProtoSpeechDriveStream
select_babble_from_drive_stream(...)           -> ProtoUtterance
update_proto_speech_evidence(...)              -> ProtoSpeechEvidenceTable
select_proto_utterance(...)                    -> ProtoUtterance
run_proto_speech_turn(state, condition,
                      turn_index, ambient,
                      feedback_plan) -> (state, ProtoSpeechTurn)
run_proto_speech_live_test()                   -> ProtoSpeechAcquisitionReport
format_proto_speech_report(report)             -> str
proto_speech_report_digest(report)             -> str
main(argv) -> int  (CLI entry, exit 0 PASS, 1 FAIL, 2 WARN)
```

## CLI

```text
python3 -m brain.development.proto_speech_acquisition
python3 -m brain.development.proto_speech_acquisition --quiet
```

Prints:

```text
proto_speech version=<v> turns=<n> pass=<p> warn=<w> fail=<f>
  stable_single=<s> stable_combination=<c> suppressed=<sup>
  transfer_success=<tr> fp=<fp> fn=<fn>
  drive_stream_count=<ds> drive_stream_digest=<dd>
  report_digest=<rd>
  real_model_calls=0 cache_writes=0 forbidden_term_hits=0
```
