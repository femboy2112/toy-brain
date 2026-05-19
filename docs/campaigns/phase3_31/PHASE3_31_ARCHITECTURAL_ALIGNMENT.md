# PHASE3_31_ARCHITECTURAL_ALIGNMENT.md — Phase 3.31 architectural alignment

## Purpose

Document how Phase 3.31's caregiver-scaffolded proto-speech runner
fits the existing two-layer identity-correlation architecture
(four imprinting kinds + transverse osmotic substrate-level
imprinting) without inventing a new mechanism or making
psychological claims.

## Where it lives in the architecture

Phase 3.31 lives entirely at the **substrate level**. It does NOT
introduce a fifth imprinting kind. It does NOT introduce a new
verification-pathway tool at formation. It does NOT introduce
a SelfModel or a new aggregate scalar.

## Osmotic imprinting alignment

The phase brief reiterates the architectural rule:

- Osmotic imprinting is **transverse** to the four imprinting
  kinds, not a fifth kind.
- Osmotic imprinting is **substrate-level** pattern formation
  through repeated co-occurrence.
- It does **not** initially require explicit focus,
  verification-pathway construction, or deliberate learning.
- Imprinting and activation are **distinct**:
  imprinting forms the substrate association; activation later
  triggers its operational use.

Caregiver-scaffolded proto-speech in Phase 3.31 is modelled as
**substrate-level proto-form imprinting**, not explicit
verification-tool imprinting. The
`ProtoSpeechEvidenceTable.update` rule changes only a bounded
integer weight per `(context_signature, utterance_digest)` cell;
no `brain.affect`, `brain.tlica`, or `brain.identity` surface is
touched.

## Ignored babble is non-retention, not Mode A

A babble form that receives `IGNORED` feedback has its weight
decremented by `1`. If the weight crosses
`SUPPRESS_THRESHOLD = -3`, the form is marked `SUPPRESSED` and
the drive stream no longer surfaces it. This is **non-retention
/ suppression**, NOT Mode A boundary violation. The runner does
NOT generate Mode A events for ignored babble. The runner only
generates a Mode A boundary-violation event if a fixture
specifically proves a consistency-boundary violation (none of
the Phase 3.31 fixtures do).

## Mode C / positive identification is reserved

Repeated reinforcement raises the weight; passing
`STABLE_SINGLE_THRESHOLD = 6` flips the disposition to
`STABLE_SINGLE`. "Stable" means weight-threshold-passed; it does
NOT mean Mode C positive identification. Mode C is reserved for
explicit cases where a stable form becomes structurally
integrated into ToyI's profile / operational pattern, and Phase
3.31 explicitly does NOT cross that threshold. The future
campaign that promotes stable proto-forms to explicit
verification-pathway tools may invoke Mode C; this campaign
does not.

## Caregiver feedback is substrate-level

`ACCEPTED` (+3), `ECHO` (+3), `EXPANDED` (+4 / +1),
`CORRECTED` (-2 / +3), `IGNORED` (-1), `AMBIENT_ONLY` (+1 in
ambient slot) all act on the bounded integer weight in the
`ProtoSpeechEvidenceTable`. None of them write to the L1 / L2
caches; none of them generate a `GrowthEventType` or
`GrowthEventSource`; none of them call `tick`; none of them
register a new `ReasoningStepKind` or `LearningEvidenceKind`
member. They are pure deterministic updates to a session-local
bounded record.

## Proto-speech drive stream is explicit/auditable

`ProtoSpeechDriveStream` is a bounded ordered tuple of
`ProtoSpeechDriveFrame` records. Each frame has:

- `drive_kind` (closed enum),
- `source_surface` (bounded printable string naming the public
  substrate the frame is derived from),
- `context_signature` (closed digest of the active context),
- `input_digest_hex16` (canonical 16-hex digest of the input),
- optional digests for the evidence trace, reasoning trace,
  dispatch trace, and caregiver utterance,
- a bounded integer `weight_hint`,
- a bounded `suggested_token_set` from the closed
  `ProtoVocalToken` inventory,
- a bounded printable `explanation` (audited against the
  forbidden non-claim terms).

The drive stream is the bounded explicit substitute for inner
speech / hidden chain-of-thought. Every entry is audit-visible
in the proof report. The drive stream does NOT carry private
mutable state; it is constructed fresh per turn from public
substrate snapshots and is included in the bounded report.

## Biological-development alignment

The ToyI proto-speech analogue follows the rough developmental
shape:

```text
ambient exposure
  -> vocal play / babbling
  -> social feedback
  -> turn-taking
  -> single-form use
  -> two-form combinations
```

ToyI lacks biology, motor speech, auditory perception, human
semantics, consciousness, subjective thought, and intent. The
analogue is bounded, structural, deterministic, and operational
only. The shape is borrowed for engineering convenience; the
substrate is closed, integer-weighted, and audit-visible at
every step.

## Future-bounded threshold (out of scope)

Stable proto-forms may eventually be candidates for explicit
verification-pathway tools (Mode C imprinting). That step would
require:

- explicit construction of a verification-pathway tool for the
  form,
- an explicit `GrowthEventType` / `GrowthEventSource` extension,
- explicit alignment with the four imprinting kinds,
- explicit non-claim audit for the new surface,
- a separate campaign with its own roadmap.

Phase 3.31 does NOT cross that threshold. The future campaign
may; this one does not.

## Closed import discipline

`brain/development/proto_speech_acquisition.py` imports only:

- `__future__`,
- `argparse`,
- `dataclasses`,
- `enum`,
- `hashlib` (only at the digest-construction boundary),
- `sys`,
- `typing`,
- `brain.development.abstract_pattern`,
- `brain.development.agent_loop`,
- `brain.development.coherence_monitor` (only for
  `_FORBIDDEN_NON_CLAIM_TERMS`),
- `brain.development.learning_evidence`,
- `brain.development.reasoning_trace`.

No `brain.llm.*`, no `brain.tick`, no `brain.ui`, no `curses`,
no I/O, no host execution, no `time`, no `random`, no
threading / asyncio / atexit / signal / importlib / pathlib /
math / os.
