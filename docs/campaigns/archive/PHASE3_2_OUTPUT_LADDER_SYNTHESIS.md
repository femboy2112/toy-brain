# PHASE3_2_OUTPUT_LADDER_SYNTHESIS.md

## 1. Purpose

Phase 3.2 defines the Output Ladder that follows the Phase 3.1 Osmotic
Chamber.

This document is a synthesis artifact only. It does not authorize catalog
patches, runtime modules, fixture additions, worldlet behavior, Proto-BASIC
syntax, language behavior, or Mode B implementation.

Core thesis:

```text
Output is not language and not reflective action at first. It begins as
source-tagged output echo and becomes action-like only after recurrence and
bounded consequence history.
```

Phase 3.2 should preserve the Phase 3 bridge principle:

```text
PRESERVE should be earned, not labeled.
```

The Output Ladder extends that principle to expression: output should become
meaningful only through substrate history, echo provenance, recurrence, and
later consequence evidence. It should not become agency merely because it is
printable text.

## 2. Current Baseline

The inherited baseline is Phase 3.1 / catalog v0.6:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

The current v0.6 gate covers the deterministic Osmotic Chamber substrate:

```text
PhenomenalFrame
FrameSource
SubstrateHistory
ProtoPattern
ProtoContent
salience_v1
stability_v1
prediction_gain_v1
ProbeUse
ProbePolicyState
promotion gate to PerceptEvent
source-tag audit
```

The important Phase 3.1 result is not that the system now has language. It is
that the system has a deterministic place for source-tagged contact, recurrence,
metric support, and bounded promotion through the existing `tick()` boundary.

The promotion gate has also been tightened before Phase 3.2 planning. Promotion
requires salience, stability, and prediction gain at or above the deterministic
threshold, rejects low-positive audit cases, requires trace/probe provenance,
rejects `COGITO_ID`, and reaches TLICA runtime state only through
`PerceptEvent` plus `tick()`.

## 3. Why Output Follows Substrate History

The Osmotic Chamber comes before output because cold text emission without
history is developmentally thin. If output appears before source-tagged history,
the system can only emit labels or strings; it cannot distinguish an echoed
contact, a recurring pattern, a stable token candidate, or an action-like
attempt.

Phase 3.1 created the needed substrate boundary:

```text
source tags distinguish endogenous, generated, external, operator, and probe
history separates recurrence from one-off noise
salience is not truth
prediction gain and stability constrain promotion
tick remains the only runtime mutation boundary
```

Phase 3.2 should use that substrate rather than bypass it. Output should first
be an observed developmental event in the substrate layer, then a repeatable
pattern, then a token candidate, then a learned token, and only later a
proto-action candidate.

This keeps expression below reflective agency. A generated output can be
source-tagged and echoed without being a free action, a language act, or a
world-changing command.

## 4. Output Ladder Thesis

The Output Ladder should advance in conservative layers:

```text
OutputImpulse
OutputEchoFrame / output source tagging
OutputPattern / recurrence
OutputTokenCandidate
LearnedOutputToken
ProtoOutputAction
```

`OutputImpulse` is the first bounded output unit. It is not language, not a
command, and not an agency witness. It is a printable or symbolic emission with
explicit source/provenance metadata.

`OutputEchoFrame` records the fact that output occurred and binds it back into
substrate history. Echo means the system can later inspect that it emitted
something; it does not mean the system understands the output.

`OutputPattern` requires recurrence. A one-off output impulse should remain
noise or transient emission, just as a one-off input frame does not become
stable proto-content.

`OutputTokenCandidate` requires recurrence plus echo provenance. A token
candidate is a stable output form under substrate constraints, not yet a word in
a language.

`LearnedOutputToken` is still below natural language. It may be reproducible and
source-tagged, but it does not by itself imply grammar, reference, readability,
teacher correction, or social meaning.

`ProtoOutputAction` is the first action-like layer, and it should remain below
Mode B and below worldlet semantics. It can only be considered after recurrence,
echo history, and bounded consequence evidence exist.

## 5. Non-Goals

Phase 3.2 must not implement or smuggle in:

```text
Minimal Worldlet
worldlet consequence rules
Proto-BASIC REPL
Proto-BASIC grammar
natural language teacher
expression/readability layer
readability predictor
social/language harness
Mode B reflective planning
real LLM training behavior
prompt tuning to force scenario outcomes
seeded-MSI shortcuts
direct mutation of TLICA state
```

Output echo is not agency. A stable output token is not language yet. A
proto-output action is not reflective choice and not world causality.

## 6. Expected Phase Ordering

The inherited Phase 3 order remains:

```text
Phase 3.1 - Osmotic Chamber
Phase 3.2 - Output Ladder
Phase 3.3 - Minimal Worldlet
Phase 3.4 - Proto-BASIC REPL
Phase 3.5 - Expression + ReadabilityPredictor
Phase 3.6 - Social/language harness
```

The Output Ladder belongs between chamber history and worldlet interaction
because the system needs constrained output before external interaction becomes
meaningful. It should be able to emit, echo, repeat, and stabilize output forms
before those forms are treated as commands in a worldlet or symbols in a REPL.

Worldlet causality should still come before Proto-BASIC syntax. The system
should encounter bounded external resistance before a symbolic command language
is introduced.

## 7. Risks

Main risks:

- Treating printable output as language too early.
- Treating output echo as agency.
- Allowing one-off output noise to become a token candidate.
- Letting output source tags create new enum values that conflict with Phase
  3.1 source discipline.
- Letting proto-output actions require worldlet evidence before the worldlet
  phase exists.
- Mutating TLICA state directly from output history instead of using the
  established promotion and tick boundaries.
- Overfitting fixtures to a desired narrative rather than cataloging bounded
  deterministic behavior.

The safe rule is to make every promotion step earn its status through explicit
history and provenance. If a layer cannot be justified without Phase 3.3
worldlet semantics, it should be deferred or marked as a future open decision.

## 8. Next Artifact

The next artifact is:

```text
PHASE3_2_OUTPUT_LADDER_KICKOFF.md
```

That kickoff should lock only the Phase 3.2 planning surface:

```text
OutputImpulse
OutputEchoFrame / output source tagging
OutputPattern / recurrence
OutputTokenCandidate
LearnedOutputToken
ProtoOutputAction
output-history storage
output echo is not agency
stable output token is not language yet
promotion/interaction with existing substrate history
```

No catalog patch or runtime implementation should occur before kickoff,
corrigenda, and catalog patch planning are complete.
