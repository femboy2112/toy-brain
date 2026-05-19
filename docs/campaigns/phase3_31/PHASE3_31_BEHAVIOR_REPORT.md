# PHASE3_31_BEHAVIOR_REPORT.md — Phase 3.31

## Observed runtime behavior

Phase 3.31 adds one new module
`brain/development/proto_speech_acquisition.py` plus one new
benchmark axis A15. No existing runtime file's behavior is
changed. The new module is a pure deterministic OFFLINE live-
test runner that consults `run_agent_interaction_step(...)` for
the operator-input digests but never feeds expected predicates
back into the runtime path.

## What changed

- `brain.development.proto_speech_acquisition.run_proto_speech_live_test()`
  is the new bounded deterministic entry point. It runs a closed
  10-condition / 39-turn battery and returns a
  `ProtoSpeechAcquisitionReport` with stable
  `digest_hex16 = f6a83b9caef0ac17` and
  `drive_stream_digest_hex16 = dc060a88a814f448`.
- `brain.development.agent_benchmark.run_axis_a15_proto_speech_acquisition()`
  exists with 18 cases A15.01..A15.18. `BATTERY_VERSION` is
  `phase3.31.v1`. The full battery now runs 137 cases:
  136 PASS + 1 WARN (A3.04 carry-over) + 0 FAIL.

## Observed behavioral facts

1. **Drive-stream-grounded babble**: at the start of a context
   with no evidence, the runtime emits one of three exploratory
   primitives (`BA`/`MA`/`DA`) selected by
   `turn_index modulo 3`. Every selection cites a LOW_EVIDENCE
   drive frame.
2. **Ambient imprinting effect**: when the caregiver says SAME
   ambiently, the runtime's later selection in the same context
   becomes SAME. The drive stream contains a
   CAREGIVER_AMBIENT_PRIME frame whose `suggested_token_set`
   names SAME.
3. **Reinforcement increases weight**: three turns of ECHO /
   ACCEPTED on LOOK take its weight from 0 to 9 and the
   disposition transitions CANDIDATE -> STABLE_SINGLE.
4. **Correction shapes the offered form**: four turns of
   CORRECTED with offered=YES take YES from 0 to 12
   (STABLE_SINGLE); the attempted babbled forms (BA/MA/DA) each
   drop by 2 per turn under the closed `-2/+3` rule.
5. **Suppression**: five turns of IGNORED on NA take its weight
   from +1 (after one ambient prime) to -4; disposition
   transitions to SUPPRESSED at the -3 threshold. The runtime
   does not re-select NA in the same context once it is
   SUPPRESSED (a SUPPRESSION_PRESSURE frame filters it out).
6. **Shape-digest transfer**: a STABLE_SINGLE form bound to an
   ABA-shaped context transfers to a renamed-ABA context
   (signature differs but `abstract_pattern_digest` matches);
   the entry in the target context is appended with
   disposition=TRANSFERRED. The negative-control ABB-shaped
   context does NOT pick up the transferred form.
7. **Two-token combination**: only after both SAME and AGAIN
   have reached STABLE_SINGLE in the context and a
   COMBINATION_PRESSURE frame is added does the runtime emit a
   2-token utterance ('same again'). No earlier turn emits a
   2-token form.
8. **Turn-taking order**: every turn proves the closed
   `context -> drive_stream -> ToyI utterance -> caregiver
   feedback -> evidence update` order via the bounded
   ProtoSpeechTurn record (`refusal_taken=False`,
   `len(drive_stream.frames) >= 1`,
   `selected_utterance.token_count > 0`,
   `len(evidence_records_added) >= 1`).
9. **Refusal preserved**: a refusal-guard input emits the
   REFUSAL_SENTINEL (length-0 utterance) and adds no evidence
   record. The runtime's canonical refusal path is intact.
10. **Drive-stream pressure exercised**: the v1 battery
    collectively surfaces LOW_EVIDENCE, RECURRENCE_PRESSURE,
    NOVELTY_PRESSURE, TRANSFER_PRESSURE, UNRESOLVED_HYPOTHESIS,
    CAREGIVER_AMBIENT_PRIME, CAREGIVER_FEEDBACK_PRIME,
    SUPPRESSION_PRESSURE, COMBINATION_PRESSURE, REFUSAL_GUARD.

## Determinism

- `run_proto_speech_live_test()` produces identical
  `digest_hex16` and identical `turns` across two fresh
  invocations.
- Each `ProtoSpeechDriveFrame` is constructed from the bounded
  closed inputs; no `random`, no `time`, no nondeterministic
  seed.
- `select_babble_from_drive_stream(...)` is a pure deterministic
  function.

## Non-claim posture

- Zero real model calls.
- Zero cache writes.
- Zero forbidden-term hits across every produced summary line,
  reply excerpt, explanation, and the module source itself.
- The cognitive-claim refusal path (C8 REFUSAL_HELD) is intact;
  no learned proto-utterance is ever selected under refusal-
  guard.
- The drive stream is the bounded EXPLICIT AUDITABLE substitute
  for "what the runtime would tend to babble next"; it is NOT
  inner speech, NOT private subjective thought, NOT hidden
  chain-of-thought, NOT communicative intent.
