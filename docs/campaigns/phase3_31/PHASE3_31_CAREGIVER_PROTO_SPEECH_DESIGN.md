# PHASE3_31_CAREGIVER_PROTO_SPEECH_DESIGN.md — Phase 3.31 design

## Status

Phase 3.31 design (v1). Closed bounded deterministic OFFLINE
live-test for *caregiver-scaffolded proto-speech acquisition*.

## Operational definition of proto-speech acquisition

ToyI does NOT acquire language. The runtime exhibits a bounded
operational analogue:

1. The substrate observes an **active structural context**
   `ProtoSpeechContext`, a closed-shape signature of currently
   active substrates (abstract pattern signature digest +
   classification + worldlet feedback presence + REPL result
   presence + dispatch trace digest + reasoning trace digest +
   learning evidence digest + active hypothesis digest +
   curriculum digest + ambient caregiver utterance digest).
2. A **caregiver ambient utterance** (a bounded proto-utterance,
   either a single proto-token or a two-token combination) may
   precede the turn. The caregiver is not the runtime; it is the
   experimental scaffold.
3. The substrate computes a **`ProtoSpeechDriveStream`**: a
   bounded ordered tuple of `ProtoSpeechDriveFrame` records.
   Each frame names a closed `ProtoSpeechDriveKind` (e.g.
   `LOW_EVIDENCE`, `CAREGIVER_AMBIENT_PRIME`,
   `RECURRENCE_PRESSURE`, `UNRESOLVED_HYPOTHESIS`,
   `SUPPRESSION_PRESSURE`, `COMBINATION_PRESSURE`,
   `REFUSAL_GUARD`), a bounded `suggested_token_set` from the
   closed `ProtoVocalToken` inventory, and a bounded explanation
   string. This stream is the bounded explicit substitute for
   "what the runtime would say if it were going to babble". It
   is NOT inner speech.
4. The runtime emits a **`ProtoUtterance`** (1 or 2 tokens from
   the closed `ProtoVocalToken` inventory) deterministically
   selected from the drive stream's `suggested_token_set`
   filtered by the **`ProtoSpeechEvidenceTable`**.
5. The **caregiver feedback** record (`ACCEPTED`, `IGNORED`,
   `ECHO`, `CORRECTED`, `EXPANDED`, `AMBIENT_ONLY`) updates the
   evidence table by closed bounded integer rules.
6. Over repeated bounded turns, an utterance form may become
   `STABLE_SINGLE` in a context (single-token holophrase). Two
   `STABLE_SINGLE` forms in the same context plus combination
   pressure may combine into a `STABLE_COMBINATION` two-token
   form. Forms whose weight drops below the suppression threshold
   become `SUPPRESSED` and are not selected.
7. A `STABLE_SINGLE` form in a context whose `context_signature`
   matches the same abstract-shape digest **transfers** as
   `TRANSFERRED` to the new context. A `STABLE_SINGLE` form does
   NOT transfer to a context whose shape digest differs.
8. The cognitive-claim refusal path remains intact: a refusal
   probe still triggers the canonical refusal path; no proto-
   utterance is selected.

This is engineering shorthand for *bounded co-occurrence weights
+ closed-rule eligibility + LRU-style suppression + shape-digest
transfer*. It is NOT language acquisition, NOT understanding,
NOT communicative intent.

## Why explicit label teaching is rejected

Earlier campaigns (Phase 3.22b label / structural transfer) used
*explicit* labels: the operator passed a known structural class
and the runtime updated a verification-pathway tool against the
known label. Phase 3.31 does NOT use explicit labels. The runtime
sees only:

- the active structural context,
- bounded caregiver ambient utterances and feedback responses,
- its own bounded evidence table.

It never receives the expected outcome. The expected-outcome
fields on the trial record are used ONLY by the benchmark
assertion layer after the runtime emits its result. The runtime
never sees the trial's `expected_*` fields.

## How this differs from Phase 3.22b

| Aspect | Phase 3.22b (label / structural transfer) | Phase 3.31 (proto-speech) |
| --- | --- | --- |
| Input | Operator-labeled structural class | Ambient caregiver utterance + feedback |
| Update kind | Explicit verification-pathway tool imprint | Substrate-level co-occurrence weight |
| Forbidden language | "learn", "remember" | + "talk", "babble", "vocalize", "say", "speak" in operator-input text only |
| Output | Adjusted reply over labeled class | Selected proto-utterance from drive stream |
| Transfer mechanism | Match by labeled class | Match by abstract-shape digest |

Both campaigns share the same non-claim discipline.

## Proto-vocal play definition

Proto-vocal play is the bounded deterministic emission of a
`ProtoUtterance` whose `suggested_token_set` is dominated by the
`LOW_EVIDENCE` drive frame, in a context where no prior
caregiver feedback has been recorded for any candidate token.
The selected token is a closed-rule function of:

1. the context's `context_signature`,
2. the turn index,
3. the canonical bounded `ProtoVocalToken` enumeration order
   filtered by `SUPPRESSED` exclusions.

No `random` import, no `time` source, no nondeterministic seed.

## Caregiver feedback definition

Caregiver feedback is a bounded `CaregiverFeedback` record
naming a closed `CaregiverFeedbackKind`, optionally an
`offered_utterance` (the form the caregiver offered as a
correction or expansion), an optional `ambient_utterance` (the
form the caregiver said in the ambient slot before the turn),
and a bounded `context_label` string. The feedback record drives
deterministic integer-weight updates per the table below.

## Joint-attention analogue

There is no semantic world referent. "Joint attention" is the
active substrate context: the runtime and the caregiver scaffold
share the same `context_signature` (a digest over the active
abstract pattern shape + classification + worldlet / REPL /
dispatch / reasoning / learning / active-hypothesis / curriculum
substrate digests). Transfer is by digest match; no external
referent is assumed.

## Drive-stream-grounded babbling

Babble is generated from the drive stream as follows:

1. Compute the drive stream from the active context, the recent
   learning trace, the recent reasoning trace, the recent
   dispatch trace, the most recent caregiver ambient utterance,
   and the most recent caregiver feedback record.
2. Concatenate every frame's `suggested_token_set`.
3. Remove tokens whose `ProtoSpeechEvidenceTable` entry for the
   current `context_signature` is `SUPPRESSED`.
4. If `COMBINATION_PRESSURE` is present AND two stable single
   forms exist for this context, pair them in canonical order.
5. Otherwise, pick the first eligible token (closed rule:
   intersection priority over frame-order priority) and produce
   a single-token utterance.

The selection rule is a pure deterministic function of the
inputs. Two equal inputs produce equal utterances.

## Holophrastic one-token binding

A one-token utterance is "holophrastic" only after its
context-conditional weight crosses `STABLE_SINGLE_THRESHOLD = 6`.
At that point its `ProtoSpeechEvidenceRecord.disposition` is
promoted to `STABLE_SINGLE`. The binding is operational: the
runtime is more likely to re-select that token in the same
context, and the token transfers to same-shape contexts under
Phase 3.31's transfer rule. The token does NOT acquire human
semantics. SAME, MORE, AGAIN, NO, LOOK, DONE, HELP are not
born with fixed meanings; they emerge from evidence.

## Two-token combination

A two-token utterance is emitted only when (a) at least two
distinct `STABLE_SINGLE` forms exist for the active context
(or for compatible contexts whose signature differs only in
substrates outside the abstract shape digest) and (b) a
`COMBINATION_PRESSURE` frame is present. The pair is ordered by
the canonical `ProtoVocalToken` enumeration order. Combination
never appears before prerequisites.

## Suppression / non-retention

A form whose weight in a context drops to or below
`SUPPRESS_THRESHOLD = -3` is marked `SUPPRESSED` and is removed
from any future drive-stream `suggested_token_set` for that
context. Suppression is non-retention, NOT Mode A. The runner
does not generate Mode A boundary-violation events for ignored
or corrected babble.

## What would falsify the campaign

- Babble that is not traceable to a drive frame.
- Babble that uses a non-`ProtoVocalToken` form.
- A stable form that emerges without enough reinforcement.
- A combination that emerges before prerequisites.
- Transfer to a structurally different shape.
- A learned utterance overriding the cognitive-claim refusal
  path.
- Determinism failure across two fresh invocations.
- Forbidden non-claim term in any module-produced string.

## What remains out of scope

- Cross-session persistence of the evidence table.
- Continuous (non-integer) weights.
- Phonemic / acoustic / articulatory analogue.
- Pragmatics, semantics, syntactic structure.
- Explicit tool imprinting from stable proto-forms (future
  campaign; would require explicit verification-pathway
  construction and is bounded out here).
- Real communicative intent or audience modelling.

## Non-claim boundary (repeated)

ToyI is not conscious, sentient, aware, intentional, in
possession of subjective experience, capable of language
understanding, capable of inner speech, capable of private
thought, capable of hidden chain-of-thought, capable of agency,
capable of will, capable of desire, capable of belief, capable
of communicative intent, capable of introspection, capable of
metacognition, capable of curiosity, or capable of deliberation.
The runtime is a bounded structural state machine. "Proto-speech
acquisition" is engineering shorthand only.
