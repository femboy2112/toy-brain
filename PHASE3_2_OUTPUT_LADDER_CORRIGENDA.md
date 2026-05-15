# PHASE3_2_OUTPUT_LADDER_CORRIGENDA.md

## 1. Purpose

This corrigenda reviews `PHASE3_2_OUTPUT_LADDER_KICKOFF.md` before any
catalog rows or runtime code are added for Phase 3.2.

Verdict:

```text
PASS WITH TIGHTENING
```

The kickoff is coherent enough to support a catalog patch plan. The tightening
below is required so Phase 3.2 does not smuggle in agency, language, worldlet
causality, or Mode B behavior.

This artifact is planning-only. It does not apply catalog rows, modify runtime
modules, add fixtures, or authorize Phase 3.3 work.

## 2. Baseline Confirmed

The inherited baseline is catalog v0.6:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

The Phase 3.1 promotion-gate patch is present. Proto-content promotion now
requires salience, stability, and prediction gain each at least `1/2`, rejects
low-positive audit cases, requires trace/probe provenance, rejects
`COGITO_ID`, and enters TLICA runtime state only through `PerceptEvent` plus
`tick()`.

Phase 3.2 must preserve that boundary. Output history may create developmental
bookkeeping. It must not directly mutate profile, MSI, PtCns, registry, agency,
PCE, or mode state.

## 3. Echo Is Not Agency

The kickoff correctly says that output echo is not agency, but the catalog patch
plan should make this a hard row-level boundary.

Required clarification:

```text
Output echo is an observed developmental record, not an Act, not a ModeOp, not
an AgencyWitness, not an action-selection result, and not a PerceptEvent.
```

An output echo may be appended to output history and may be represented as a
source-tagged echo frame for recurrence checks. It must not:

```text
select an action
call feasibleProjectedPCE
construct an AgencyWitness
claim PRESERVE
construct a PerceptEvent
call tick()
mutate TLICA runtime state
```

Catalog implication:

- A REQUIRED row should assert that echo insertion leaves TLICA runtime state
  unchanged.
- A STRUCTURAL row should assert that output echo objects do not carry `Act`,
  `ModeOp`, `AgencyWitness`, or direct runtime mutation fields.

## 4. Token Candidates Need Two Independent Supports

The kickoff names the correct safety rule:

```text
recurrence alone is insufficient without echo provenance
echo provenance alone is insufficient without recurrence
```

This should be upgraded from a design note to a catalog commitment.

Required clarification:

```text
OutputTokenCandidate requires both recurrent OutputPattern support and explicit
output echo provenance.
```

A candidate must remain below language. It may be a stable printable form in
history, but it has no syntax, no teacher correction, no social meaning, no
world reference, and no external consequence semantics in Phase 3.2.

Catalog implication:

- A REQUIRED row should reject one-off output impulses as token candidates.
- A REQUIRED row should reject echo-only output with no recurrence.
- A REQUIRED row should reject recurrent output with no echo provenance.
- A REQUIRED or STRUCTURAL row should assert that learned output tokens do not
  expose language, grammar, teacher-correction, or world-reference fields.

## 5. Source Kinds: Reuse Existing Enum Values

The kickoff leaves open whether Phase 3.2 needs a new `OUTPUT_ECHO` source kind.
The conservative decision for the catalog patch plan is:

```text
Do not add a new source enum member for v0.7 unless implementation proves the
existing Phase 3.1 source kinds cannot express the row.
```

Reason:

`FrameSourceKind` already distinguishes:

```text
ENDOGENOUS
OPERATOR_INJECTION
PROBE_ECHO
EXTERNAL
GENERATED
```

Output echo is better represented as an event role or provenance relation, not
as a source kind. Source kind should describe where the signal came from.
Echo provenance should describe that an emitted output was re-entered into
developmental history.

Catalog implication:

- The v0.7 patch plan should initially reuse `GENERATED`, `ENDOGENOUS`, and
  `PROBE_ECHO`.
- If an `OUTPUT_ECHO` enum is proposed later, it must come with a specific row
  explaining why event-role provenance is insufficient.
- No Phase 3.2 row should weaken `I-FRAME-04` or silently change Phase 3.1
  source-kind semantics.

## 6. Proto-Output Actions Stay Below Worldlet Semantics

The kickoff mentions bounded consequence evidence. That phrase is safe only if
it is interpreted as local output-history bookkeeping inside Phase 3.2.

Required clarification:

```text
Phase 3.2 must not require worldlet consequence evidence, because Minimal
Worldlet belongs to Phase 3.3.
```

Two safe options remain for the catalog patch plan:

```text
Option A: defer proto-output-action construction until Phase 3.3.
Option B: include only a non-agential ProtoOutputActionCandidate whose evidence
          is local, inspectable output-history support and whose rows assert
          that it is not agency, not language, not world causality, and not a
          direct TLICA mutation.
```

The safer default is Option A unless Step 4 can specify Option B without using
worldlet rules, command syntax, teacher correction, or Mode B planning.

Catalog implication:

- Do not make proto-output action a REQUIRED positive behavior unless its
  evidence can be defined entirely inside output history.
- If included at all in v0.7, prefer an OBSERVED or STRUCTURAL candidate row
  plus a REQUIRED negative-boundary row: the candidate must not construct
  agency or mutate runtime state.
- If consequence evidence needs world state, defer the row to Phase 3.3.

## 7. Status Guidance For Step 4

Recommended row-status split for the catalog patch plan:

```text
STRUCTURAL
```

- `OutputImpulse` construction requires printable non-empty output content.
- Output source/provenance metadata is exact, source-tagged, and uses
  `Fraction` confidence where confidence exists.
- Output history is append-only or copy-on-write.
- Output echo / token / candidate objects carry no agency witness fields.

```text
REQUIRED
```

- Source-tagged output impulse can be recorded deterministically.
- Output echo enters output history but does not mutate TLICA runtime state.
- One-off output noise does not create an `OutputPattern`.
- Repeated matching impulses create or update an `OutputPattern`.
- Token candidate construction requires recurrence plus echo provenance.
- Learned output token remains below language and below reflective agency.
- Output history does not bypass `PerceptEvent` / `tick()` boundaries.

```text
OBSERVED
```

- Proto-output-action readiness, if included before Phase 3.3.
- Any local consequence-like score that is useful to inspect but not mature
  enough to gate correctness.

```text
DEFERRED
```

- Worldlet consequence rules.
- Proto-BASIC syntax.
- Teacher correction or social-language loops.
- Reflective planning / Mode B output behavior.

## 8. Leak Audit

The kickoff is acceptable after these tightenings. The following terms are safe
only under the stated interpretations:

```text
ProtoOutputAction
```

Must mean a below-agency candidate or be deferred. It must not mean reflective
choice, selected action, world command, or agency witness.

```text
bounded consequence evidence
```

Must mean local output-history bookkeeping in Phase 3.2. It must not mean
worldlet state transitions, external reward, command success, or teacher
feedback.

```text
LearnedOutputToken
```

Must mean a stable output token under deterministic history constraints. It
must not mean language acquisition, grammar, semantics, reference, or social
meaning.

No Phase 3.3 worldlet semantics, Proto-BASIC grammar, expression/readability
layer, social/language harness, real LLM training behavior, or Mode B behavior
should appear in the v0.7 catalog patch.

## 9. Decisions For The Catalog Patch Plan

Step 4 should proceed with these decisions:

```text
1. Use I-OUT-* row families for output impulse, echo, recurrence, token
   candidate, learned token, and runtime-boundary checks.
2. Reuse existing source kinds by default; represent echo as provenance or
   event role.
3. Require recurrence plus echo provenance for token candidates.
4. Keep learned tokens below language.
5. Keep output echo below agency and below TLICA mutation.
6. Defer proto-output action unless it can be specified without Phase 3.3
   worldlet semantics.
7. Treat any proto-output-action readiness score as OBSERVED unless it has a
   deterministic local Phase 3.2 gate.
```

## 10. Next Artifact

The next artifact is:

```text
PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md
```

That plan should specify exact proposed row IDs, statuses, modules, fixtures,
count impact from v0.6, implementation order, and any remaining blockers. It
must not apply the catalog patch yet.
