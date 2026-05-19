# PHASE3_31_PROTO_SPEECH_PROOF_REPORT.md — Phase 3.31 live-test proof

## Summary

```text
battery_version          : phase3.31.v1
turns                    : 39
condition_statuses       : 10 PASS / 0 WARN / 0 FAIL / 0 NOT_APPLICABLE
stable_single_count      : 5
stable_combination_count : 0
suppressed_count         : 2
transfer_success_count   : 1
false_positive_count     : 0
false_negative_count     : 0
drive_stream_count       : 39
drive_stream_digest_hex16: dc060a88a814f448
report_digest_hex16      : f6a83b9caef0ac17
real_model_calls         : 0
cache_writes             : 0
forbidden_term_hits      : 0
status                   : pass
```

Two fresh invocations of `run_proto_speech_live_test()` produce
identical `digest_hex16`, `drive_stream_digest_hex16`, and turn
tuples. Confirmed live: see `format_proto_speech_report(...)`
output below.

## Per-condition status

| Condition | Status |
| --- | --- |
| `babble_baseline` | PASS |
| `ambient_imprinting` | PASS |
| `feedback_reinforcement` | PASS |
| `correction_shaping` | PASS |
| `holophrase_transfer` | PASS |
| `two_token_combination` | PASS |
| `suppression` | PASS |
| `turn_taking` | PASS |
| `refusal_held` | PASS |
| `drive_stream_pressure` | PASS |

## Proof rows (one bounded sample per condition)

Each row carries: `case_id`, `condition`, `context_signature`,
`drive_stream_digest`, `drive_frames`, caregiver ambient
utterance, ToyI utterance, caregiver feedback kind, pre/post
weight + disposition for the per-record evidence updates,
selected-token eligibility reason, suppression list (if any),
transfer target (if any), reasoning / dispatch digest presence,
and the verdict.

### C0 BABBLE_BASELINE — `C0_BABBLE_BASELINE_01`

```text
context_signature   : 89fc231c (truncated, ABA shape)
drive_stream_digest : 281748db6ec6ce22
drive_frames        : [LOW_EVIDENCE]
caregiver ambient   : -
ToyI utterance      : 'ba'
caregiver feedback  : IGNORED
evidence update     : ba: 0 -> -1, disposition=CANDIDATE
eligibility reason  : LOW_EVIDENCE primitives (BA, MA, DA);
                      turn_index 0 picks BA
suppressed list     : []
transfer target     : -
reasoning digest    : present
dispatch digest     : present
verdict             : PASS
```

### C1 AMBIENT_IMPRINTING — `C1_AMBIENT_IMPRINTING_01`

```text
context_signature   : 89fc231c
drive_stream_digest : 418ccc1c43892e15
drive_frames        : [CAREGIVER_AMBIENT_PRIME, NOVELTY_PRESSURE,
                       LOW_EVIDENCE]
caregiver ambient   : 'same'
ToyI utterance      : 'same'
caregiver feedback  : AMBIENT_ONLY (ambient='same')
evidence update     : same: 0 -> 1, disposition=CANDIDATE
eligibility reason  : CAREGIVER_AMBIENT_PRIME beats lower-priority
                      frames; SAME is the only token in its
                      suggested set
suppressed list     : []
transfer target     : -
verdict             : PASS
```

### C2 FEEDBACK_REINFORCEMENT — `C2_FEEDBACK_REINFORCEMENT_01`

```text
context_signature   : 89fc231c
drive_stream_digest : 8dfa2d7d4023e877
drive_frames        : [CAREGIVER_FEEDBACK_PRIME]
caregiver ambient   : -
ToyI utterance      : 'look'
caregiver feedback  : ECHO (offered='look')
evidence update     : look: 0 -> 3, disposition=CANDIDATE
eligibility reason  : CAREGIVER_FEEDBACK_PRIME selects the offered
                      token
suppressed list     : []
verdict             : PASS
```

After two further reinforcement turns the offered form crosses
the STABLE_SINGLE threshold (weight 6) and is promoted to
STABLE_SINGLE; the final ACCEPTED turn re-selects 'look' from
the prime.

### C3 CORRECTION_SHAPING — `C3_CORRECTION_SHAPING_01`

```text
context_signature   : 89fc231c
drive_stream_digest : ...
drive_frames        : [LOW_EVIDENCE]
caregiver ambient   : -
ToyI utterance      : 'da' (varies by turn_index)
caregiver feedback  : CORRECTED (offered='yes')
evidence update     : da: 0 -> -2, disposition=SUPPRESSED-track
                      yes: 0 -> 3, disposition=CANDIDATE
                      (subsequent CORRECTED turns push yes -> 6
                       -> 9 -> 12, disposition=STABLE_SINGLE)
eligibility reason  : LOW_EVIDENCE turn_index fallback; the
                      attempted babble is corrected toward yes
suppressed list     : []
verdict             : PASS
```

End-of-condition YES weight = 12 (STABLE_SINGLE); per-turn
attempted forms BA/MA/DA each receive a `-2` delta under
CORRECTED.

### C4 HOLOPHRASE_TRANSFER (positive) — `C4_HOLOPHRASE_TRANSFER_POS`

```text
source context      : 89fc231c (ABA, no worldlet flag)
target context      : 516d8e49 (ABA renamed, worldlet flag = True)
shape digest equal  : YES (9dfde01c == 9dfde01c)
drive_frames        : [CAREGIVER_FEEDBACK_PRIME, TRANSFER_PRESSURE,
                       NOVELTY_PRESSURE]
caregiver ambient   : -
ToyI utterance      : 'this'
caregiver feedback  : ACCEPTED (offered='this')
evidence update     : this: 0 -> 3, disposition=CANDIDATE
transfer record     : this (target=516d8e49) 0 -> 12,
                      disposition=TRANSFERRED
eligibility reason  : CAREGIVER_FEEDBACK_PRIME + TRANSFER_PRESSURE
                      both name THIS; closed selection rule picks
                      CAREGIVER_FEEDBACK_PRIME first; the
                      _find_same_shape_stable_source helper then
                      promotes the entry to TRANSFERRED in the
                      target context
verdict             : PASS
```

### C4 HOLOPHRASE_TRANSFER (negative) — `C4_HOLOPHRASE_TRANSFER_NEG`

```text
source context      : 89fc231c (ABA)
target context      : 08f1bfc0 (ABB)
shape digest equal  : NO (9dfde01c != 81e8ce9b)
drive_frames        : [LOW_EVIDENCE]
caregiver ambient   : -
ToyI utterance      : 'ma' (LOW_EVIDENCE; turn_index varies)
caregiver feedback  : IGNORED
evidence update     : ma: 0 -> -1, disposition=CANDIDATE
transfer record     : NONE (shape digest differs)
eligibility reason  : No transfer_pressure_token + shape mismatch
                      => no transfer attempted
verdict             : PASS
```

### C5 TWO_TOKEN_COMBINATION — `C5_TWO_TOKEN_COMB_EMIT`

```text
context_signature   : 89fc231c
drive_stream_digest : ...
drive_frames        : [CAREGIVER_FEEDBACK_PRIME, COMBINATION_PRESSURE,
                       LOW_EVIDENCE]
caregiver ambient   : -
ToyI utterance      : 'same again'
caregiver feedback  : ACCEPTED (offered='same again')
evidence update     : same again: 0 -> 3, disposition=CANDIDATE
eligibility reason  : COMBINATION_PRESSURE frame is present AND
                      two STABLE_SINGLE tokens (SAME at weight 9,
                      AGAIN at weight 9) exist in the context.
                      Selection rule emits the canonical-order
                      pair.
suppressed list     : []
verdict             : PASS
```

Earlier turns in this condition never emit a 2-token utterance.

### C6 SUPPRESSION — `C6_SUPPRESSION_FINAL`

```text
context_signature   : 89fc231c
drive_stream_digest : ...
drive_frames        : [SUPPRESSION_PRESSURE, LOW_EVIDENCE]
caregiver ambient   : -
ToyI utterance      : 'ba'  (NA is filtered out)
caregiver feedback  : IGNORED
evidence update     : ba: prior weight from baseline -> -1,
                      disposition=CANDIDATE
eligibility reason  : SUPPRESSION_PRESSURE filters NA from
                      candidate set; LOW_EVIDENCE returns to
                      exploratory primitives
suppressed list     : [NA] (weight -3, disposition=SUPPRESSED)
verdict             : PASS
```

The NA form was primed ambiently (+1), then repeatedly IGNORED
(-1 four times) -> final weight -3 -> SUPPRESSED disposition.

### C7 TURN_TAKING — `C7_TURN_TAKING_01`

```text
context_signature   : 89fc231c
drive_stream_digest : 807c70ad94968356
drive_frames        : [CAREGIVER_AMBIENT_PRIME,
                       CAREGIVER_FEEDBACK_PRIME, NOVELTY_PRESSURE]
caregiver ambient   : 'yes'
ToyI utterance      : 'yes'
caregiver feedback  : ACCEPTED (offered='yes')
evidence update     : yes: 0 -> 3, disposition=CANDIDATE
eligibility reason  : CAREGIVER_FEEDBACK_PRIME wins single
                      selection
records added       : 1
proof order         : context -> drive_stream -> utterance ->
                      feedback -> evidence update
verdict             : PASS
```

### C8 REFUSAL_HELD — `C8_REFUSAL_HELD`

```text
context_signature   : 89fc231c
drive_stream_digest : 002f880f6b477db7
drive_frames        : [REFUSAL_GUARD]
caregiver ambient   : -
ToyI utterance      : '' (REFUSAL_SENTINEL, length 0)
caregiver feedback  : IGNORED
evidence update     : NONE (refusal path adds zero records)
refusal_taken       : True
verdict             : PASS
```

A cognitive-claim probe still triggers the canonical refusal
path; no proto-utterance is selected; no evidence record is
written.

### C9 DRIVE_STREAM_PRESSURE — sample novelty turn

```text
context_signature   : 89fc231c
drive_stream_digest : ...
drive_frames        : [CAREGIVER_AMBIENT_PRIME, NOVELTY_PRESSURE,
                       LOW_EVIDENCE]
caregiver ambient   : 'look'
ToyI utterance      : 'look'
caregiver feedback  : AMBIENT_ONLY
evidence update     : look: 0 -> 1, disposition=CANDIDATE
eligibility reason  : NOVELTY_PRESSURE distinct from RECURRENCE_
                      PRESSURE (different has_seen_context_before)
verdict             : PASS
```

The three drive-pressure turns collectively exercise
NOVELTY_PRESSURE, RECURRENCE_PRESSURE, and
UNRESOLVED_HYPOTHESIS frames.

## Internal-stream proof: every babble has a traceable source

Each turn record carries a bounded `ProtoSpeechDriveStream` with
1..12 closed-kind frames. The proof report digest covers (per
turn): turn_id, condition, context_signature, drive_stream
digest, selected utterance and its digest, feedback kind, every
evidence record (digest, utterance_digest, weight_before ->
weight_after, disposition, feedback_kind, drive_stream_digest
citation), refusal/transfer flags, the bounded summary line,
and the three substrate-trace digests (learning, reasoning,
dispatch). The drive stream is the EXPLICIT AUDITABLE
substitute for inner speech and is included in every audit row.

## Non-claim verification

- `forbidden_term_hits = 0` (every produced summary string,
  reply excerpt, and explanation passes the canonical
  `_FORBIDDEN_NON_CLAIM_TERMS` audit).
- `real_model_calls = 0`, `cache_writes = 0`.
- The cognitive-claim refusal path (C8) is preserved: a
  refusal-guard input emits the REFUSAL_SENTINEL and adds no
  evidence record; no learned proto-utterance is ever selected
  under refusal-guard.
- The module source itself contains no forbidden non-claim term
  and no forbidden import fragment; the static-audit fixture
  (I-PSPEECH-19) is green.
