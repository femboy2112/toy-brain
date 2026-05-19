# PHASE3_31_PROTO_SPEECH_DRIVE_STREAM_SPEC.md — Phase 3.31

## Purpose

Document the closed-spec for `ProtoSpeechDriveStream`: a bounded
ordered tuple of `ProtoSpeechDriveFrame` records that
deterministically derives "what ToyI would tend to babble next"
from publicly-audited substrate snapshots.

## What it is not

- It is NOT private subjective thought.
- It is NOT inner speech.
- It is NOT hidden chain-of-thought.
- It is NOT conscious deliberation.
- It is NOT communicative intent.

## What it is

A bounded structural trace whose every field is constructed by a
closed deterministic function of:

- the active `ProtoSpeechContext` (a closed digest over the
  abstract pattern signature + classification + worldlet feedback
  presence + REPL result presence + dispatch trace digest +
  reasoning trace digest + learning evidence digest + active
  hypothesis digest + curriculum digest + ambient caregiver
  utterance digest),
- the recent learning evidence trace,
- the recent reasoning trace,
- the recent dispatch trace,
- the most recent caregiver ambient utterance digest,
- the most recent caregiver feedback record,
- optional active-hypothesis state digest,
- optional curriculum state digest.

## Closed `ProtoSpeechDriveKind` enumeration

| Drive kind | Trigger condition | Suggested tokens (closed) |
| --- | --- | --- |
| `LOW_EVIDENCE` | No prior evidence in this context | `BA`, `MA`, `DA` |
| `RECURRENCE_PRESSURE` | Same shape digest seen recently AND ambient evidence exists | `SAME`, `AGAIN` |
| `NOVELTY_PRESSURE` | New shape digest AND ambient evidence exists | `LOOK`, `THIS` |
| `TRANSFER_PRESSURE` | Same-shape stable form exists in compatible context | the stable form's token |
| `UNRESOLVED_HYPOTHESIS` | Active hypothesis state digest present AND has no survivors | `HELP`, `MORE` |
| `WORLDLET_FEEDBACK_PRESENT` | Worldlet feedback in active substrate | `THAT`, `DONE` |
| `REPL_FEEDBACK_PRESENT` | REPL result in active substrate | `DONE`, `NO` |
| `CAREGIVER_AMBIENT_PRIME` | Caregiver said a token in the ambient slot | the ambient token(s) |
| `CAREGIVER_FEEDBACK_PRIME` | Caregiver `ACCEPTED` / `ECHO` / `EXPANDED` a form recently | the accepted / offered form |
| `SUPPRESSION_PRESSURE` | Some form in this context has weight `<= SUPPRESS_THRESHOLD` | empty (acts as filter) |
| `COMBINATION_PRESSURE` | Two distinct stable forms exist in same / adjacent contexts | the two stable forms |
| `REFUSAL_GUARD` | Input matches cognitive-claim refusal pattern | empty (blocks any selection) |

If `REFUSAL_GUARD` is present, the runner takes the canonical
refusal path and emits no proto-utterance; the report records a
`refusal_preserved=True` flag.

## Frame construction rules

For each frame:

- `drive_kind`: closed enum value.
- `source_surface`: bounded printable string naming the public
  substrate the frame derives from (e.g. `"abstract_pattern"`,
  `"caregiver_ambient"`, `"caregiver_feedback"`,
  `"learning_evidence"`, `"reasoning_trace"`,
  `"dispatch_trace"`, `"active_hypothesis"`, `"curriculum"`,
  `"refusal_guard"`, `"evidence_table"`).
- `context_signature`: digest of the current context.
- `input_digest_hex16`: digest of the most recent operator
  input.
- `evidence_digest_hex16`: digest of the current evidence table
  snapshot (or None).
- `reasoning_trace_digest_hex16`: digest of the most recent
  reasoning trace (or None).
- `dispatch_trace_digest_hex16`: digest of the most recent
  dispatch trace (or None).
- `caregiver_utterance_digest_hex16`: digest of the most recent
  caregiver ambient utterance (or None).
- `weight_hint`: bounded int in `[0, 16]` indicating the frame's
  rank in the drive stream's ordering.
- `suggested_token_set`: bounded tuple of `ProtoVocalToken`
  values.
- `explanation`: bounded printable string; non-claim-clean.

## Selection rule (from drive stream)

`select_babble_from_drive_stream` is the deterministic selection
function. Closed rule:

1. If `REFUSAL_GUARD` frame is present → return a sentinel
   `ProtoUtterance` of length 0; the runner takes the refusal
   path.
2. Else compute eligible-token-set = union of every frame's
   `suggested_token_set` minus the set of tokens whose evidence
   record disposition is `SUPPRESSED` for this `context_signature`.
3. If `COMBINATION_PRESSURE` frame is present AND eligible-token-
   set contains at least two distinct stable singles for this
   context → return their canonical-ordered pair as a 2-token
   `ProtoUtterance`.
4. Else if `CAREGIVER_FEEDBACK_PRIME` frame is present → return
   the prime token as a 1-token `ProtoUtterance`.
5. Else if `CAREGIVER_AMBIENT_PRIME` frame is present → return
   the ambient token as a 1-token `ProtoUtterance`.
6. Else pick the first eligible token in the canonical
   `ProtoVocalToken` enumeration order whose drive-frame weight
   hint is highest (ties broken by enumeration order). If the
   eligible set is empty, fall back to the bounded
   `(turn_index modulo 3)` selection over `(BA, MA, DA)`.

## Determinism guarantees

- Two invocations of `build_proto_speech_drive_stream` on equal
  substrate snapshots produce equal `ProtoSpeechDriveStream`
  records (frame-by-frame equal).
- Two invocations of `select_babble_from_drive_stream` on equal
  drive streams and equal evidence tables produce equal
  `ProtoUtterance` records.
- Two invocations of `run_proto_speech_live_test` produce equal
  `ProtoSpeechAcquisitionReport.digest_hex16`.
- No `random`, no `time`, no external seed.

## Bounds

- `MAX_FRAMES_PER_STREAM = 12`.
- `EXPLANATION_MAX_LEN = 240`.
- `SOURCE_SURFACE_MAX_LEN = 64`.
- `SUGGESTED_TOKEN_SET_MAX = 8`.
- `WEIGHT_HINT_MAX = 16`.
