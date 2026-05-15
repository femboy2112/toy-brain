# PHASE3_2_OUTPUT_LADDER_KICKOFF.md

## 1. Purpose

Phase 3.2 builds the Output Ladder planning surface above the Phase 3.1
Osmotic Chamber substrate.

This document is a kickoff plan only. It does not apply catalog rows, add
runtime modules, add fixtures, or implement output behavior.

The Phase 3.2 principle is:

```text
Output should become action-like only through echo, recurrence, source-tagged
history, and bounded consequence evidence; it is not reflective agency yet.
```

The inherited bridge principle remains:

```text
PRESERVE should be earned, not labeled.
```

Phase 3.2 applies that principle to output. A printable emission is not
language, not agency, and not a preservation claim. It first has to become
source-tagged history. Only repeated, inspectable, provenance-bearing output can
move up the ladder.

## 2. Current Baseline

The starting baseline is catalog v0.6:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

The inherited Phase 3.1 substrate already provides:

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

The output ladder must build on that substrate. It must not mutate TLICA state
directly, bypass `PerceptEvent`, bypass `tick()`, or treat output history as a
new action-selection system.

## 3. Scope

Phase 3.2 covers only these surfaces:

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

The implementation should be deterministic, inspectable, and catalog-driven.
Any stochastic behavior, real LLM training behavior, social teaching behavior,
or natural-language correction loop is out of scope.

## 4. Non-Goals

Phase 3.2 explicitly excludes:

```text
later-phase external-environment semantics
symbolic command syntax
social correction loops
expression systems
reflective planning
real LLM training behavior
prompt tuning to force scenario outcomes
seeded-MSI shortcuts
```

These exclusions are active design boundaries. In particular:

- Output echo is not agency.
- A stable output token is not language yet.
- A proto-output action is not reflective choice.
- No Phase 3.2 object should encode external-environment rules or symbolic
  command syntax.

## 5. OutputImpulse

`OutputImpulse` is the first bounded output event.

Expected role:

```text
capture one attempted emission
carry printable output content
carry exact source/provenance metadata
remain below action selection
remain below language
remain below TLICA runtime mutation
```

An impulse should be rejected if it cannot be source-tagged, if it has empty or
non-printable content, or if it attempts to target reserved runtime identifiers
such as `COGITO_ID`.

The initial source-kind decision should prefer reusing the existing Phase 3.1
source discipline unless the corrigenda or catalog patch plan proves that a new
output-specific source kind is necessary. Likely starting kinds are:

```text
GENERATED
ENDOGENOUS
PROBE_ECHO
OPERATOR_INJECTION
```

The kickoff does not decide whether a future catalog patch should add an
`OUTPUT_ECHO` source kind. That is a Step 3 / Step 4 decision.

## 6. OutputEchoFrame

`OutputEchoFrame` records that an output impulse occurred and places the output
back into substrate history as an inspectable frame.

Expected behavior:

```text
an emitted output can be echoed into history
the echo carries source/provenance
the echo does not assert truth
the echo does not assert PRESERVE
the echo does not construct agency
the echo does not mutate TLICA state
```

The frame should make later recurrence checks possible. It should not by itself
create `ProtoContent`, `PerceptEvent`, learned tokens, or action candidates.

Output echo should reuse `PhenomenalFrame`-style source discipline where
possible. If a separate output frame type is introduced later, it should keep
the same construction standards: exact source coverage, exact `Fraction`
confidence, non-empty printable keys, and explicit rejection of mismatches.

## 7. Output History Storage

Phase 3.2 needs a history store parallel to, or intentionally integrated with,
`SubstrateHistory`.

The initial design should support:

```text
append-only output impulse history
echo-frame history
output pattern registry
token candidate registry
learned token registry
proto-output-action candidate registry if authorized
```

The storage boundary should be immutable or copy-on-write, matching the Phase
3.1 `SubstrateHistory` style. Stored output history must be inspectable without
requiring a real LLM call or a real scenario run.

Open design choice for corrigenda:

```text
Should output history extend SubstrateHistory directly, or should it be a
separate OutputHistory object linked to SubstrateHistory by echo frame IDs?
```

The conservative default is a separate `OutputHistory` with explicit conversion
or echo insertion into substrate history. That avoids changing Phase 3.1
history semantics before the catalog patch is reviewed.

## 8. OutputPattern

`OutputPattern` is the recurrence layer for output impulses.

Expected behavior:

```text
repeated matching output impulses create or update an OutputPattern
one-off output noise does not become a pattern
pattern identity is deterministic
pattern support records recurrence evidence
pattern source kinds remain inspectable
```

This mirrors the Phase 3.1 rule that recurrence is the first deterministic
condition for earned content. A repeated output form is still not language. It
is only a recurrent emission pattern.

Similarity rules should be deterministic and narrow at first. Exact match or a
small normalized signature is preferable to semantic matching, external
correction, or natural-language interpretation.

## 9. OutputTokenCandidate

`OutputTokenCandidate` is the first stable-token layer.

A candidate should require at least:

```text
recurrent OutputPattern support
echo provenance
non-empty source-tagged history
absence of reserved identifiers
no direct TLICA mutation
```

A candidate may represent a repeatable output form, but it is not a word in a
language. It has no syntax, no externally corrected meaning, no social meaning,
and no external reference in Phase 3.2.

The likely safety rule is:

```text
recurrence alone is insufficient without echo provenance
echo provenance alone is insufficient without recurrence
```

This should be reviewed in the kickoff corrigenda before catalog rows are
assigned.

## 10. LearnedOutputToken

`LearnedOutputToken` is a stable output token that has passed the deterministic
Phase 3.2 support gates.

Expected commitments:

```text
it is reproducible
it has recurrence support
it has output echo provenance
it is source-tagged
it is inspectable
it is below language
it is below reflective agency
```

It should not imply:

```text
natural-language meaning
syntax
correction-loop meaning
external reference
reflective planning
```

The name "learned" is developmental bookkeeping. It means the runtime has a
stable output token under deterministic history constraints, not that it has
learned a language.

## 11. ProtoOutputAction

`ProtoOutputAction` is the first action-like candidate in the Output Ladder.

It should be included only if the catalog patch plan can keep it below later
phases. It must not require external-environment rules, symbolic command
syntax, correction feedback, or reflective planning.

Minimum conceptual support:

```text
recurrent output pattern
echo history
learned output token support
explicit record that this is not agency
no direct TLICA mutation
```

The campaign-level principle also names bounded consequence evidence. Phase 3.2
may define a placeholder or bookkeeping slot for such evidence, but it must not
define later-phase external-environment rules. If this evidence cannot be
specified within output history alone, proto-output actions should be deferred
or marked as a non-gating planning item.

## 12. Promotion And Substrate Interaction

Output ladder objects should interact with the existing substrate through
history and explicit promotion boundaries.

Allowed interaction:

```text
OutputImpulse can create output echo history
OutputEchoFrame can enter substrate history as inspectable developmental data
recurrence over output history can create OutputPattern
stable output history can create OutputTokenCandidate
learned output tokens can remain below PerceptEvent promotion
```

Disallowed interaction:

```text
direct profile mutation
direct MSI mutation
direct PtCns mutation
direct registry mutation
bypassing tick()
claiming PRESERVE from output text alone
claiming agency from output echo alone
```

If a later accepted catalog patch allows any output-derived `PerceptEvent`,
it must use the same boundary discipline as Phase 3.1: deterministic support,
reserved-ID rejection, valid event construction, and runtime entry only through
`tick()`.

## 13. Implementation Order

The recommended order after kickoff/corrigenda/catalog planning is:

```text
1. Catalog patch plan for I-OUT-* row families.
2. Accepted v0.7 catalog patch and generated ID sync.
3. OutputImpulse and OutputEchoFrame structure.
4. Output history storage.
5. Output echo fixture proving echo is not agency and does not mutate TLICA.
6. OutputPattern recurrence behavior.
7. OutputTokenCandidate behavior.
8. LearnedOutputToken behavior.
9. ProtoOutputAction only if accepted and still below later phases.
10. Full gate and Phase 3.2 audit.
```

No code should be written from this kickoff alone. Catalog patch planning and
corrigenda must decide row IDs, statuses, fixture split, and whether
`ProtoOutputAction` belongs in v0.7 or stays deferred.

## 14. Expected Future Row Families

This kickoff expects the catalog patch plan to consider `I-OUT-*` families for:

```text
source-tagged output impulses
output echo enters history but is not agency
one-off output noise does not become a pattern
repeated output impulses create output patterns
token candidates require recurrence plus echo provenance
learned output token is not language
proto-output action remains below reflective agency if included
no direct TLICA state mutation from output history
```

Exact IDs, statuses, fixtures, owning modules, and count impact belong to
`PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md`, not this kickoff.

## 15. Validation Plan

For planning artifacts:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

For any later accepted implementation steps:

```bash
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-OUT
bash tools/check_all.sh
```

Real LLM commands and real scenario commands remain out of scope unless the
user explicitly asks for them.

## 16. Next Artifact

The next artifact is:

```text
PHASE3_2_OUTPUT_LADDER_CORRIGENDA.md
```

The corrigenda should review:

```text
output echo vs agency distinction
whether output token candidates require recurrence plus echo provenance
whether output source kinds require new enum values or existing kinds suffice
whether output action candidates can be defined from output history alone
whether rows should be REQUIRED, STRUCTURAL, or OBSERVED
whether any later-phase semantics leaked in
```
