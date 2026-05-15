# PHASE3_4_PROTO_BASIC_REPL_CORRIGENDA.md

## 1. Purpose

This corrigenda reviews `PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md` before any
catalog patch or runtime implementation.

Verdict: the kickoff is coherent, but the future catalog patch plan should
make the Proto-BASIC boundary stricter in the places listed below. None of
the issues identified is a blocker for drafting the catalog patch plan.

This document does not apply catalog rows, create modules, add fixtures,
change `tick()`, change scenarios, modify TLICA Lean reference files, or
introduce any host-side execution.

## 2. Corrigenda Summary

Phase 3.4 should proceed with these tightened rules:

```text
Proto-BASIC consequence is local deterministic harness evidence, not real
interpreter behavior, not host execution, not language understanding, not
Mode B agency.

ProtoBasicCommand construction requires both a valid ProtoBasicParseResult
and current registered learned-output support, not parse-validity alone.

ProtoBasicValence is exact, bounded, source-tagged, and local to
ProtoBasicHistory.

Valid syntax alone never grants strong positive feedback. Strong positive
feedback requires execution_result.effective == True under deterministic
local rules.

No Proto-BASIC evidence enters PerceptEvent, tick(), profile, MSI, PtCns,
content registry, trace files, scenario schemas, or the affect taxonomy in
Phase 3.4.
```

## 3. Consequence vs Agency

The kickoff treats a Proto-BASIC attempt as consequence-bearing only inside
a deterministic local harness. The catalog patch plan should make this
distinction row-level rather than prose-only.

Required tightening:

```text
ProtoBasicCommand is not Act.
ProtoBasicCommand is not ModeOp.
ProtoBasicCommand is not AgencyWitness.
ProtoBasicCommand does not select an action.
ProtoBasicCommand does not carry feasibleProjectedPCE.
ProtoBasicExecutionResult is not an agency outcome.
ProtoBasicHistory is not a runtime trajectory.
ProtoBasicFeedback is not affect, not reward signal, not policy update.
```

The key semantic split is:

```text
agency: selects among feasible Act values by projected-PCE criteria
worldlet: submits a learned-token-backed attempt to a finite deterministic
          rule (Phase 3.3)
proto-basic: submits a finite-grammar one-line input to a finite
             deterministic local harness with bounded local feedback
             (Phase 3.4)
```

The Proto-BASIC harness may record that a local parse classifier accepted,
near-missed, syntax-rejected, semantically-rejected, or sandbox-faulted an
attempt. It must not claim the system chose a TLICA action, formed a
reflective plan, acquired free-will branch evidence, or performed real
interpreter execution.

## 4. Syntax vs Language

The kickoff says explicitly that Proto-BASIC syntax is not language. The
catalog patch plan should bind this to row mechanics rather than leaving it
as prose.

Required tightening:

```text
ProtoBasicToken is a finite enumerated lexical unit, not a word.
ProtoBasicLine.raw_text is a bounded printable surface, not natural
  language.
ProtoBasicParseResult is a deterministic classifier, not a comprehension
  predicate.
near-miss correction hints are deterministic edit records, not teacher
  utterances.
valid is "grammar accepts and local semantics permit", not "the system
  understood the input".
```

The hint generator must be enumerable from a valid form by a bounded local
edit (substitute, insert, delete, case-fold). It must not call any external
corrector, language model, social channel, or LLM-style teacher.

## 5. Intentionally Tiny Deterministic Grammar

The kickoff sketches a one-line command surface with a finite token set.
The catalog patch plan should make smallness and determinism row-level
properties, not informal preferences.

Required tightening:

```text
The legal ProtoBasicToken set is fixed at build time for a given
  ProtoBasicGrammar.
tokenize is total over bounded raw_text: same input yields same token
  sequence.
parse_line is total over ProtoBasicLine: every line maps to exactly one
  ProtoBasicParseResult category.
The seven parse categories partition outcomes deterministically without
  overlap (valid, near-miss, syntax-invalid, semantic-invalid,
  tool-unavailable, resource-limit, sandbox-fault).
There is no multi-line program, no GOTO / GOSUB, no loop construct, no
  stored-program memory beyond ProtoBasicHistory.
ProtoBasicProgram, if it exists at all, is a thin one-line wrapper kept
  only for symmetry with later phases.
```

Intentional smallness is the main defense against scope creep into a real
interpreter. The plan should reject any field whose only purpose is to
look like a real interpreter.

## 6. Valid Syntax Is Not Sufficient

The kickoff already states that valid syntax alone does not earn strong
positive feedback. This corrigenda upgrades that to a hard requirement
that the catalog patch plan must express as REQUIRED rows.

Required tightening:

```text
valid parse alone -> never strong positive feedback
strong positive feedback requires:
  parse_result.category == valid
  execution_result.category == valid-effective
  execution_result.effective == True
  diminishing returns factor not fully decayed
valid-ineffective execution -> weak or zero bounded valence
no feedback path bypasses execution_result.effective for strong positive
  valence
```

This rule is the structural form of "effect-required reward" and the main
defense against syntactic conformance becoming a reward-hacking surface.

## 7. Bounded Invalid / Near-Miss / Fault Feedback

The kickoff lists bounded negative valence for the non-valid categories.
The catalog patch plan should make boundedness exact, not approximate.

Required tightening:

```text
ProtoBasicValence is a Fraction.
ProtoBasicValence range: -1 <= value <= 1.
Out-of-range construction: raise. No silent clamp.
syntax-invalid     -> bounded negative valence
semantic-invalid   -> bounded negative valence
tool-unavailable   -> bounded negative valence
resource-limit     -> bounded negative valence
sandbox-fault      -> bounded negative valence
near-miss          -> small negative or neutral bounded valence
```

Negative response evidence must remain bounded and descriptive. It must not
introduce:

```text
fear
avoidance pathology
named affect taxonomy
substrate affect pathway
free-will branch semantics
policy learning
runtime self-model mutation
PerceptEvent emission
trace seam emission
profile / MSI / PtCns mutation
```

Each category's exact valence value should be fixed by the catalog patch
plan, not by the implementation. Fixing the values in the plan prevents
drift between fixtures and the documented contract.

## 8. Anti-Goodhart: Diminishing Returns and Effect-Required Reward

The kickoff already names diminishing returns and effect-required reward.
The catalog patch plan should bind both to deterministic mechanics.

Required tightening:

```text
emit_counts is incremented per canonical command form on each execution.
diminishing_returns_factor is a Fraction in [0, 1].
strong positive valence is multiplied by diminishing_returns_factor and
  remains inside [-1, 1].
the decay is deterministic (same emit_counts -> same factor).
the decay is exact (Fraction arithmetic, no floats).
the decay is not reset by interleaving other commands.
the decay does not silently clamp out-of-range values.
```

Combined with effect-required reward, repeated identical no-op spam cannot
dominate ProtoBasicHistory's feedback distribution. The plan should keep
diminishing returns local: it must not be exported into the profile, MSI,
PtCns, content registry, scenario schema, or trace seam.

If the accepted catalog patch plan defers full anti-Goodhart mechanics to
a later phase, Step 9 may be skipped per the campaign's stop logic. The
corrigenda recommendation is to keep diminishing returns and
effect-required reward together in Phase 3.4 because skipping one weakens
the other.

## 9. Row Status Guidance

The catalog patch plan should use conservative statuses for the
`I-REPL-*` family.

Recommended REQUIRED rows:

```text
ProtoBasicValence is a Fraction in [-1, 1] and never silently clamps.
ProtoBasicHistory appends parse results, commands, execution results, and
  feedback copy-on-write.
ProtoBasicParseResult is total over ProtoBasicLine.
parse categories partition outcomes deterministically without overlap.
ProtoBasicCommand construction requires a valid parse result plus
  registered token / learned-output support.
valid syntax alone does not grant strong positive feedback.
strong positive feedback requires execution_result.effective == True.
syntax-invalid, semantic-invalid, tool-unavailable, resource-limit, and
  sandbox-fault produce bounded negative valence.
near-miss correction hints respect bounded edit distance.
repeated identical no-op commands receive diminishing returns.
Proto-BASIC operations do not call tick(), emit PerceptEvent, mutate
  TLICA runtime state, mutate profile, MSI, PtCns, or content registry.
```

Recommended STRUCTURAL rows:

```text
ProtoBasicToken is a finite enumeration with bounded text.
ProtoBasicLine has bounded length and bounded token count.
ProtoBasicCommand carries no Act, ModeOp, AgencyWitness, PerceptEvent,
  selected-action, feasibleProjectedPCE, tick callback, real interpreter
  handle, subprocess handle, file descriptor, or network socket.
ProtoBasicExecutionResult exposes the declared category set
  (valid-effective, valid-ineffective, tool-unavailable, resource-limit,
  sandbox-fault).
ProtoBasicFeedback reuses the existing source / provenance discipline or a
  parallel validation discipline of equivalent strictness.
ProtoBasicProgram, if present, is a one-line wrapper with no control flow.
```

Recommended OBSERVED rows:

```text
Aggregate Proto-BASIC history summaries can be inspected for diminishing
  returns behavior.
Qualitative anti-Goodhart behavior under repeated emissions can be
  reported as local harness evidence.
```

Do not make qualitative anti-Goodhart summaries REQUIRED unless they have
an exact deterministic assertion. Do not use OBSERVED rows to smuggle in
runtime promotion, affect taxonomy growth, or external-world claims.

## 10. Expression / Readability / Social / Mode B Leakage

The kickoff lists these as non-goals. The corrigenda affirms they remain
non-goals and adds row-level guards.

The catalog patch plan should reject any field, fixture, or row that
implies:

```text
expression layer
readability predictor
naturalness scoring
social register
language model corrector
teacher utterance
listener feedback
audience model
Mode B reflective planning
free-will branch tracking via REPL
prompt-tuning to force scenario outcomes
seeded-MSI shortcuts
```

Proto-BASIC's local feedback is structural, not communicative. A near-miss
hint says only that observed tokens differ from a valid form by a specific
local edit. It does not phrase a correction in natural language, does not
address a listener, and does not score readability.

If a row would only be coherent under a social, expressive, or Mode B
reading, the plan should reject it for Phase 3.4 and defer to a later
campaign.

## 11. PerceptEvent / Tick / Trace Boundary

Proto-BASIC evidence must remain local in Phase 3.4.

The catalog patch plan should explicitly state:

```text
ProtoBasicCommand does not emit PerceptEvent.
ProtoBasicExecutionResult does not emit PerceptEvent.
ProtoBasicFeedback does not emit PerceptEvent.
ProtoBasicHistory does not call tick().
Proto-BASIC operations do not modify profile, MSI, PtCns, or content
  registry.
Proto-BASIC evidence does not enter trace files or scenario schemas in
  Phase 3.4.
Proto-BASIC evidence does not feed back into OutputHistory or
  WorldletHistory in Phase 3.4.
```

Any future path that promotes Proto-BASIC evidence into `PerceptEvent`,
`tick()`, traces, or scenarios requires a later accepted campaign step. It
is not authorized by Phase 3.4 planning.

The Phase 3.3 worldlet boundary remains the inherited rule:

```text
Worldlet consequence evidence is local deterministic harness evidence;
it is not external reality, reflective agency, language, Mode B, or
runtime promotion.
```

Phase 3.4 inherits this and adds:

```text
Proto-BASIC consequence evidence is local deterministic harness evidence;
it is not real interpreter behavior, not host execution, not language,
not Mode B, and not runtime promotion.
```

## 12. Bridge from Worldlet / Output

The kickoff's one-way bridge from learned-output / worldlet evidence into
Proto-BASIC command construction is correct. The catalog patch plan should
state the bridge direction as a row-level invariant.

Required tightening:

```text
A ProtoBasicCommand may be constructed only when:
  parse_result.category == valid
  every ProtoBasicToken in the line is enumerated
  learned-output support (LearnedOutputToken / OutputHistory) exists for
    tokens that depend on it
  optional supporting WorldletHistory evidence is present when required
    by the command kind
  source/provenance metadata is supplied

ProtoBasicHistory entries do not flow back into OutputHistory.
ProtoBasicHistory entries do not flow back into WorldletHistory.
ProtoBasicHistory entries do not flow back into PerceptEvent, tick(), or
  TLICA runtime state.
```

This avoids a weak path where Proto-BASIC accepts a command based purely
on string shape without underlying output / worldlet support, and it
prevents Proto-BASIC consequence evidence from quietly upgrading earlier
phases' state.

## 13. Source and Provenance Discipline

The kickoff preference to reuse existing source discipline should become
a hard requirement.

Required tightening:

```text
ProtoBasicParseResult, ProtoBasicCommand, ProtoBasicExecutionResult, and
  ProtoBasicFeedback should reuse the existing FrameSourceKind and
  Fraction-confidence discipline, or a parallel validation discipline of
  equivalent strictness.
No new source-kind enum member is added unless the catalog patch plan
  documents a specific justification.
trace_event_ids referenced by Proto-BASIC provenance must be printable
  local identifiers; they do not introduce real trace seam entries in
  Phase 3.4.
```

This keeps Proto-BASIC evidence aligned with the existing source-tag audit
and prevents a Proto-BASIC-specific source category from bypassing
established constructor checks.

## 14. Catalog Patch Plan Requirements

The next artifact, `PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md`,
should turn this corrigenda into exact row mechanics:

```text
I-REPL-* row IDs
statuses (REQUIRED / STRUCTURAL / OBSERVED)
owning modules
fixture files (repl_grammar.py, repl_feedback.py, repl_execution.py,
  repl_history.py)
count impact from current v0.8 to projected v0.9
implementation order
pending-registration strategy if needed
validation commands
open decisions
stop condition for the review gate
```

The plan should not apply the patch. It should be coherent enough that
Step 5's review gate can decide whether implementation is unblocked.

## 15. Final Decision

No blocker prevents drafting the catalog patch plan.

Proceed to:

```text
PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md
```

The next step should remain planning-only and should not touch runtime
modules, fixtures, catalog rows, generated IDs, `tick()`, `brain/llm/`,
`brain/tlica/`, `lean_reference/`, `scenarios/`, `traces/`, or LLM
behavior.
