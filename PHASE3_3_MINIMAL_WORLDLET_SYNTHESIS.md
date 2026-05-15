# PHASE3_3_MINIMAL_WORLDLET_SYNTHESIS.md

## 1. Purpose

Phase 3.3 defines the Minimal Worldlet that follows the Phase 3.2 Output
Ladder.

This document is a synthesis artifact only. It does not authorize catalog
patches, runtime modules, fixture additions, Proto-BASIC syntax, REPL behavior,
expression/readability work, social/language behavior, or Mode B implementation.

Core thesis:

```text
The Minimal Worldlet converts local proto-output readiness into bounded
consequence-bearing attempts, but only inside a deterministic harness. It
supplies not-I pushback; it does not create reflective agency, language, REPL
command syntax, or real-world action.
```

Phase 3.3 preserves the inherited Phase 3 bridge principle:

```text
PRESERVE should be earned, not labeled.
```

The worldlet extends that principle to consequence. A local output token should
not become action-like because it is printable, recurrent, or learned. It should
become action-like only when a bounded deterministic harness can return
consequence evidence that the system did not assign to itself.

## 2. Current Baseline

The inherited baseline is Phase 3.2 / catalog v0.7:

```text
99 REQUIRED
24 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
3 OBSERVED
```

The v0.7 gate covers the deterministic Output Ladder:

```text
OutputImpulse
OutputProvenance
OutputEcho
OutputHistory
OutputPattern
OutputTokenCandidate
LearnedOutputToken
ProtoOutputActionReadiness
```

The important Phase 3.2 result is not that the system now has language,
agency, or world contact. It is that the system can record output impulses,
echo them into local history, detect recurrent output forms, construct learned
output tokens under recurrence-plus-echo support, and observe proto-output
action readiness without mutating TLICA runtime state.

The Phase 3.2 audit reports PASS. The full gate is green, `I-OUT-*` rows are
registered and green, `I-OUT-11` is OBSERVED only, output echo remains below
agency, learned output tokens remain below language, and readiness remains
below consequence.

## 3. Why Worldlet Follows Output Readiness

The Output Ladder comes before the Minimal Worldlet because consequence-bearing
attempts need an output surface to constrain. Without source-tagged output
history, a worldlet attempt would be a direct external command surface with no
local developmental evidence behind it.

Phase 3.2 leaves exactly one bridge point:

```text
ProtoOutputActionReadiness
```

That readiness is local and non-gating in v0.7. It says the history contains a
learned output token with recurrence and echo support. It does not say the token
is a command, a word, a selected `Act`, an agency witness, or a real-world
operation.

Phase 3.3 should therefore ask the next conservative question:

```text
Can a learned, recurrent, source-tagged output token be used as a bounded
attempt inside a deterministic harness, and can the harness return local
consequence evidence without crossing into agency or language?
```

This puts the worldlet after output readiness but before Proto-BASIC. The
system should encounter constrained resistance before it receives command
syntax for manipulating that resistance.

## 4. Minimal Worldlet Thesis

The Minimal Worldlet should be a finite deterministic harness with a narrow
surface:

```text
WorldletState
WorldletObject / target surface if needed
WorldletAttempt
WorldletResponse
WorldletValence
WorldletHistory
```

`WorldletState` is bounded and inspectable. It is not an open environment, not a
host process, and not a hidden external world.

`WorldletAttempt` is constructed only from local output-readiness support. It is
not an `Act`, not an `AgencyWitness`, not a Mode B plan, and not a REPL command.

`WorldletResponse` records what the harness returned. It should include exact
source/provenance metadata and bounded valence, but it should not promote
itself into TLICA runtime state.

`WorldletHistory` is the local store for attempts and responses. It is
copy-on-write / append-only in the same spirit as `OutputHistory`. The response
enters local worldlet history, not the profile, MSI, PtCns, registry, scenario
schema, trace files, or `tick()` semantics.

## 5. Not-I Pushback and Consequence Evidence

The worldlet supplies not-I pushback by returning deterministic responses that
are not chosen by the output token itself. This pushback is bounded and local:

```text
valid attempt -> deterministic bounded response
invalid attempt -> deterministic bounded negative response
unavailable target -> deterministic bounded negative response
```

The negative side is important. Failed attempts should produce bounded
consequence evidence without becoming fear, avoidance pathology, affect
taxonomy, free-will branch semantics, or a real-world failure claim.

Worldlet valence should be exact and bounded:

```text
-1 <= WorldletValence <= 1
```

Positive valence should mean only that the deterministic harness accepted or
rewarded the attempt under its local rules. Negative valence should mean only
that the harness rejected, blocked, or penalized the attempt under its local
rules. Neither side is a truth claim about the external world.

## 6. Still Below Agency, Language, and Mode B

Minimal Worldlet evidence is consequence-bearing, but it is still below
reflective agency.

The boundary is:

```text
consequence evidence is not action selection
not-I pushback is not external reality
worldlet attempt is not Act
worldlet response is not PerceptEvent
worldlet history is not TLICA runtime mutation
learned output token is not language
bounded local valence is not affect taxonomy
```

The worldlet may show that an output token can be tested against a constrained
response surface. It does not show that the system understands the token, formed
a plan, selected a free action, used grammar, entered a social exchange, or
updated the runtime self-model.

Mode B remains out of scope. Phase 3.3 may provide material that a later Mode B
layer could inspect, but it should not implement reflective planning or parallel
developmental reasoning.

## 7. Non-Goals

Phase 3.3 must not implement or smuggle in:

```text
Proto-BASIC REPL
Proto-BASIC grammar
open-ended sandbox execution
real host execution
natural language teacher
expression/readability layer
readability predictor
social/language harness
Mode B reflective planning
real LLM training behavior
prompt tuning to force scenario outcomes
seeded-MSI shortcuts
direct mutation of TLICA state
worldlet response promotion into PerceptEvent
```

Minimal Worldlet is not a command language. It is not an operating-system
sandbox. It is not a social environment. It is not a real external world. It is
a deterministic harness for bounded consequence evidence.

## 8. Expected Phase Ordering

The inherited Phase 3 order remains:

```text
Phase 3.1 - Osmotic Chamber
Phase 3.2 - Output Ladder
Phase 3.3 - Minimal Worldlet
Phase 3.4 - Proto-BASIC REPL
Phase 3.5 - Expression + ReadabilityPredictor
Phase 3.6 - Social/language harness
```

The Minimal Worldlet belongs between output readiness and Proto-BASIC because
the system needs bounded consequence contact before symbolic command syntax.
Output history makes attempts possible; worldlet pushback makes attempts
consequence-bearing; only after that should a REPL or expression layer be
considered.

## 9. Risks

Main risks:

- Treating proto-output-action readiness as sufficient for agency.
- Treating a worldlet attempt as an `Act` or an `AgencyWitness`.
- Letting a worldlet response enter `PerceptEvent` or `tick()` without an
  explicit later phase.
- Treating deterministic harness pushback as external reality.
- Letting negative bounded responses become fear, avoidance pathology, or named
  affect taxonomy.
- Introducing Proto-BASIC syntax or REPL behavior too early.
- Making learned output tokens into language through worldlet labels.
- Adding new source kinds or runtime mutation paths without catalog review.
- Overfitting the harness so every learned token succeeds.

The safe rule is to keep every consequence local, deterministic, bounded, and
auditable. If a property needs grammar, real execution, social correction,
reflective planning, or runtime self-model mutation, it belongs in a later
phase.

## 10. Next Artifact

The next artifact is:

```text
PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md
```

That kickoff should lock only the Phase 3.3 planning surface:

```text
WorldletState
WorldletObject / target surface if needed
WorldletAttempt
WorldletResponse
WorldletValence bounded in [-1, 1]
WorldletHistory
not-I pushback
bounded deterministic consequence evidence
connection from ProtoOutputActionReadiness to WorldletAttempt
worldlet response enters local worldlet history, not TLICA state
```

No catalog patch or runtime implementation should occur before kickoff,
corrigenda, and catalog patch planning are complete.
