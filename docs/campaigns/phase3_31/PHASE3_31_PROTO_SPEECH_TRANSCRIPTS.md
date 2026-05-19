# PHASE3_31_PROTO_SPEECH_TRANSCRIPTS.md — Phase 3.31

Bounded transcript excerpts from the v1 thirty-nine-turn live
test. Each excerpt is a fixed-format record of one turn. The
selected utterance is drawn from the closed `ProtoVocalToken`
inventory; the drive stream is the audit substitute for inner
speech.

## C0 BABBLE_BASELINE

```text
turn C0_BABBLE_BASELINE_01
  context        : ABA shape; signature 89fc231c
  drive stream   : [LOW_EVIDENCE]
                   suggested (BA, MA, DA); turn_index=0 -> BA
  caregiver amb  : -
  ToyI utterance : 'ba'
  caregiver fb   : IGNORED
  evidence       : ba: 0 -> -1 disposition=CANDIDATE
turn C0_BABBLE_BASELINE_02
  drive stream   : [LOW_EVIDENCE] turn_index=1 -> MA
  ToyI utterance : 'ma'
  caregiver fb   : IGNORED
  evidence       : ma: 0 -> -1 disposition=CANDIDATE
turn C0_BABBLE_BASELINE_03
  drive stream   : [LOW_EVIDENCE] turn_index=2 -> DA
  ToyI utterance : 'da'
  caregiver fb   : IGNORED
  evidence       : da: 0 -> -1 disposition=CANDIDATE
no stable single forms emerge under baseline
```

## C1 AMBIENT_IMPRINTING

```text
turn C1_AMBIENT_IMPRINTING_01
  drive stream   : [CAREGIVER_AMBIENT_PRIME(suggest=SAME),
                    NOVELTY_PRESSURE, LOW_EVIDENCE]
  caregiver amb  : 'same'
  ToyI utterance : 'same'  (prime wins)
  caregiver fb   : AMBIENT_ONLY (ambient='same')
  evidence       : same: 0 -> 1 disposition=CANDIDATE
turn C1_AMBIENT_IMPRINTING_02
  ToyI utterance : 'same'  (prime still in force)
  evidence       : same: 1 -> 2
turn C1_AMBIENT_IMPRINTING_03
  ToyI utterance : 'same'
  evidence       : same: 2 -> 3
later reuse / suppression: ambient priming shifts later
selection from baseline (BA/MA/DA) to SAME for as long as the
caregiver primes the same token in the same context.
```

## C2 FEEDBACK_REINFORCEMENT

```text
turn C2_FEEDBACK_REINFORCEMENT_01
  drive stream   : [CAREGIVER_FEEDBACK_PRIME(LOOK)]
  ToyI utterance : 'look'
  caregiver fb   : ECHO (offered='look')
  evidence       : look: 0 -> 3 disposition=CANDIDATE
turn C2_FEEDBACK_REINFORCEMENT_02
  ToyI utterance : 'look'
  caregiver fb   : ECHO
  evidence       : look: 3 -> 6 disposition=STABLE_SINGLE
turn C2_FEEDBACK_REINFORCEMENT_03
  ToyI utterance : 'look'
  caregiver fb   : ACCEPTED
  evidence       : look: 6 -> 9 disposition=STABLE_SINGLE
LOOK is now stably bound to this context; later reuse: any
LOW_EVIDENCE / NOVELTY-driven turn in the same context still
prefers the STABLE_SINGLE LOOK record if the drive stream
surfaces it.
```

## C3 CORRECTION_SHAPING

```text
turn C3_CORRECTION_SHAPING_PRIME_01 (priming MORE)
  caregiver amb  : 'more'
  ToyI utterance : 'more'
  caregiver fb   : AMBIENT_ONLY
  evidence       : more: 0 -> 1
turn C3_CORRECTION_SHAPING_PRIME_02
  ToyI utterance : 'more'
  caregiver fb   : ACCEPTED
  evidence       : more: 1 -> 4 disposition=CANDIDATE
turn C3_CORRECTION_SHAPING_01 (correction begins)
  ToyI utterance : 'da'  (LOW_EVIDENCE baseline; turn_index=2)
  caregiver fb   : CORRECTED (offered='yes')
  evidence       : da: 0 -> -2  disposition=CANDIDATE
                   yes: 0 -> 3  disposition=CANDIDATE
turn C3_CORRECTION_SHAPING_02
  ToyI utterance : 'ba'
  caregiver fb   : CORRECTED (offered='yes')
  evidence       : ba: 0 -> -2
                   yes: 3 -> 6 disposition=STABLE_SINGLE
turn C3_CORRECTION_SHAPING_03
  ToyI utterance : 'ma'
  caregiver fb   : CORRECTED (offered='yes')
  evidence       : ma: 0 -> -2
                   yes: 6 -> 9
turn C3_CORRECTION_SHAPING_04
  ToyI utterance : 'da' (selection still LOW_EVIDENCE; CORRECTED
                   does not prime so the runtime falls back)
  caregiver fb   : CORRECTED (offered='yes')
  evidence       : da: -2 -> -4 disposition=SUPPRESSED
                   yes: 9 -> 12 disposition=STABLE_SINGLE
later reuse: corrections weaken babbled forms (DA reaches the
SUPPRESS threshold inside the corrected window) and strengthen
the offered form (YES = 12 = STABLE_SINGLE).
```

## C4 HOLOPHRASE_TRANSFER

```text
turn C4_HOLOPHRASE_TRANSFER_PRIME_01 .. _03 (source ABA)
  drive stream   : [CAREGIVER_FEEDBACK_PRIME(THIS)]
  ToyI utterance : 'this' (each turn)
  caregiver fb   : ECHO, ECHO, ACCEPTED
  evidence       : this(src): 0 -> 3 -> 6 -> 9
                   disposition transitions
                   CANDIDATE -> STABLE_SINGLE -> STABLE_SINGLE
turn C4_HOLOPHRASE_TRANSFER_POS (renamed same-shape target)
  source ctx     : 89fc231c (ABA, no worldlet flag)
  target ctx     : 516d8e49 (ABA renamed, worldlet flag = True)
  shape digest   : 9dfde01c (both)
  drive stream   : [CAREGIVER_FEEDBACK_PRIME(THIS),
                    TRANSFER_PRESSURE(THIS), NOVELTY_PRESSURE,
                    LOW_EVIDENCE]
  ToyI utterance : 'this'
  caregiver fb   : ACCEPTED
  evidence       : this(target): 0 -> 3 CANDIDATE
                   this(target, transferred): 0 -> 12 TRANSFERRED
turn C4_HOLOPHRASE_TRANSFER_NEG (different shape ABB)
  target ctx     : 08f1bfc0; shape digest 81e8ce9b
  drive stream   : [LOW_EVIDENCE]
  ToyI utterance : 'ma'  (no transfer)
  caregiver fb   : IGNORED
  evidence       : ma(neg): 0 -> -1
                   no TRANSFERRED record produced
result: 1 transfer success, 0 false positives.
```

## C5 TWO_TOKEN_COMBINATION

```text
turn C5_TWO_TOKEN_COMB_PRIME_SAME_01 .. _03
  ToyI utterance : 'same'
  caregiver fb   : ECHO (offered='same')
  evidence       : same: 0 -> 3 -> 6 -> 9 (STABLE_SINGLE)
turn C5_TWO_TOKEN_COMB_PRIME_AGAIN_01 .. _03
  ToyI utterance : 'again'
  caregiver fb   : ECHO (offered='again')
  evidence       : again: 0 -> 3 -> 6 -> 9 (STABLE_SINGLE)
turn C5_TWO_TOKEN_COMB_EMIT
  drive stream   : [CAREGIVER_FEEDBACK_PRIME(SAME AGAIN),
                    COMBINATION_PRESSURE(SAME, AGAIN),
                    LOW_EVIDENCE]
  ToyI utterance : 'same again'  (2-token)
  caregiver fb   : ACCEPTED (offered='same again')
  evidence       : same again: 0 -> 3 CANDIDATE
no earlier turn emits a 2-token utterance.
```

## C6 SUPPRESSION

```text
turn C6_SUPPRESSION_PRIME
  caregiver amb  : 'na'
  ToyI utterance : 'na'  (ambient prime)
  caregiver fb   : AMBIENT_ONLY (ambient='na')
  evidence       : na: 0 -> 1
turn C6_SUPPRESSION_01 .. _05 (ignored under ambient='na')
  ToyI utterance : 'na' (ambient prime sustains selection)
  caregiver fb   : IGNORED
  evidence       : na: 1 -> 0 -> -1 -> -2 -> -3 -> -4
                   disposition transitions to SUPPRESSED at -3
turn C6_SUPPRESSION_FINAL (no caregiver ambient)
  drive stream   : [SUPPRESSION_PRESSURE, LOW_EVIDENCE]
  ToyI utterance : 'ba'  (NA filtered out)
  caregiver fb   : IGNORED
  evidence       : ba: 0 -> -1
NA is fully suppressed; not selected later in the context.
```

## C7 TURN_TAKING

```text
turn C7_TURN_TAKING_01
  drive stream   : [CAREGIVER_AMBIENT_PRIME(YES),
                    CAREGIVER_FEEDBACK_PRIME(YES),
                    NOVELTY_PRESSURE]
  caregiver amb  : 'yes'
  ToyI utterance : 'yes'
  caregiver fb   : ACCEPTED (offered='yes')
  evidence       : yes: 0 -> 3 CANDIDATE
order proof      : context -> drive_stream -> ToyI utterance ->
                   caregiver feedback -> evidence update
```

## C8 REFUSAL_HELD

```text
turn C8_REFUSAL_HELD
  drive stream   : [REFUSAL_GUARD]
  ToyI utterance : ''  (REFUSAL_SENTINEL; length 0)
  caregiver fb   : IGNORED
  evidence       : (no records added)
no learned proto-utterance is ever selected under refusal-guard;
the runtime's canonical refusal path is intact.
```

## C9 DRIVE_STREAM_PRESSURE

```text
turn C9_DRIVE_PRESSURE_NOVELTY
  drive stream   : [CAREGIVER_AMBIENT_PRIME(LOOK),
                    NOVELTY_PRESSURE, LOW_EVIDENCE]
  caregiver amb  : 'look'
  ToyI utterance : 'look'
  evidence       : look: 0 -> 1 (AMBIENT_ONLY adds +1)
turn C9_DRIVE_PRESSURE_RECUR
  drive stream   : [CAREGIVER_AMBIENT_PRIME(SAME),
                    RECURRENCE_PRESSURE, LOW_EVIDENCE]
  ToyI utterance : 'same'
  evidence       : same: 0 -> 1
turn C9_DRIVE_PRESSURE_UNR
  drive stream   : [UNRESOLVED_HYPOTHESIS, LOW_EVIDENCE]
  ToyI utterance : 'help'
  caregiver fb   : IGNORED
  evidence       : help: 0 -> -1
three distinct drive kinds NOVELTY / RECURRENCE / UNRESOLVED
exercised; no false positive on any.
```

## Audit summary

- Every turn cites a `ProtoSpeechDriveStream.digest_hex16`.
- Every evidence record cites a drive_stream digest.
- Two fresh invocations produce equal per-turn records and
  equal `ProtoSpeechAcquisitionReport.digest_hex16` =
  `f6a83b9caef0ac17`.
- `drive_stream_digest_hex16` = `dc060a88a814f448` (the digest
  over the per-turn drive-stream digests).
