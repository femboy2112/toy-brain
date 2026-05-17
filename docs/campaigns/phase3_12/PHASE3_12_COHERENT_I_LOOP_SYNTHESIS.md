# PHASE3_12_COHERENT_I_LOOP_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.12 Coherent I-Loop target from the current repo architecture and the completed Phase 3.11 behavior campaign.

This is a planning artifact. It does not edit source code, fixtures, catalog rows, scenarios, traces, or runtime semantics.

## Why this follows Phase 3.11

Phase 3.11 verified that ToyI can be launched and used through the operator-facing path. It exercised launch, offline interaction, persistence/cold-start, autosave, DB observability/backup, and deterministic LLM runtime behavior. The aggregate behavior findings reported no critical correctness failures and no safety/invariant findings.

The next question is not whether the UI launches. The next question is whether the system can show bounded developmental behavior that looks like:

```text
coherent behavior
pattern recognition
persistent growth
operational self-reference
```

without widening the runtime boundary.

## Operational definitions

### Coherent

A behavior is coherent when:

```text
catalog gates remain green
COGITO_ID remains reserved
state transitions happen through accepted routes
latest tick/record/status can be explained from prior state + input
data persists and reloads without contradiction
operator-facing reports match actual stored state
```

Coherence does not mean subjective awareness.

### Pattern-recognizing

A behavior is pattern-recognizing when:

```text
recurring structural motifs in stream/developmental history are detected
patterns have stable bounded identifiers
repeated identical evidence saturates
novel evidence is distinguished from recurrence
pattern evidence is inspectable and persistent when persistence is added
```

Pattern recognition does not imply semantic truth, language understanding, agency, or PtCns evaluation.

### Growing

A behavior is growing when:

```text
bounded accepted evidence accumulates over time
growth survives save/load
success/failure/duplicate/spam are distinguished
repeated low-information input does not inflate growth indefinitely
```

Growth does not mean unbounded self-modification.

### I

"I" means an operational self-model:

```text
stable anchor to COGITO_ID
knowledge of current tick/state/pattern/growth summaries
knowledge of constraints and prohibited actions
self-report that matches actual repo-local state
```

"I" does not mean proof of consciousness, sentience, subjective experience, or human-like interiority.

## Existing safe path

The accepted path already exists:

```text
/stream <text>
  -> TextStreamChunk
  -> StreamPromotionCandidate

/stream-promote <candidate_id>
  -> QueuePerceptPayload

/step
  -> PerceptEvent
  -> tick()
  -> BrainState + TickRecord
```

The first Phase 3.12 observatory should measure this path before adding new code.

## Candidate future layers

### Pattern Ledger

A bounded developmental ledger of recurring structural patterns.

Requirements:

```text
copy-on-write
bounded entries
bounded evidence lists
exact Fraction confidence if scoring exists
no COGITO_ID in pattern identifiers/signatures/evidence ids
no tick() call
no BrainState mutation
no PtCns eval
no agency field
no LLM call
```

### Coherence Monitor

A read-only snapshot over:

```text
BrainState / MSI / PtCns / registry
latest TickRecord
stream state
pattern/growth state if added
persistence status
known constraints
```

It should report checks, not a consciousness score.

### SelfModel

A later operational self-model could report:

```text
self_id
COGITO anchor
tick count
active constraints
recognized pattern IDs
latest coherence report
```

It must remain read-only over kernel state and never claim subjective experience.

### Growth Ledger

A bounded ledger of accepted growth events such as:

```text
stream chunk accepted
pattern strengthened
candidate promoted
tick succeeded
content entered profile
content entered MSI
session saved/loaded
coherence report passed
```

Growth must saturate and reject Goodhart inflation.

## Non-goals

```text
no new semantic truth layer in Phase 3.12a/b
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
no hidden LLM call
no real LLM default
no self-modifying code
no consciousness score
no sentience claim
```

## Next artifact

```text
PHASE3_12_COHERENT_I_LOOP_KICKOFF.md
```
