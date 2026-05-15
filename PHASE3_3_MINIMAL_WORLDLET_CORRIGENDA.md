# PHASE3_3_MINIMAL_WORLDLET_CORRIGENDA.md

## 1. Purpose

This corrigenda reviews `PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md` before any
catalog patch or runtime implementation.

Verdict: the kickoff is coherent, but the future catalog patch plan should make
the worldlet boundary stricter in the places listed below.

This document does not apply catalog rows, create modules, add fixtures, change
`tick()`, change scenarios, or modify any TLICA Lean reference.

## 2. Corrigenda Summary

Phase 3.3 should proceed with these tightened rules:

```text
WorldletAttempt construction requires both ready proto-output-action readiness
and current registered LearnedOutputToken support.

Worldlet consequence is deterministic local response evidence, not Act
selection, AgencyWitness construction, Mode B planning, or external-world
truth.

WorldletResponse valence must be exact, bounded, source-tagged, and local to
WorldletHistory.

Failed valid attempts produce negative-but-bounded response evidence; invalid
attempt objects still raise at construction.

No worldlet evidence enters PerceptEvent, tick(), profile, MSI, PtCns, content
registry, trace files, or scenario schemas during Phase 3.3.
```

## 3. Consequence vs Agency

The kickoff correctly says a worldlet attempt is consequence-bearing only inside
a deterministic harness. The catalog patch plan should make this distinction
row-level rather than prose-only.

Required tightening:

```text
WorldletAttempt is not Act.
WorldletAttempt is not ModeOp.
WorldletAttempt is not AgencyWitness.
WorldletAttempt does not select an action.
WorldletAttempt does not carry feasibleProjectedPCE.
WorldletResponse is not an agency outcome.
WorldletHistory is not a runtime trajectory.
```

The key semantic split is:

```text
agency: selects among feasible Act values by projected-PCE criteria
worldlet: submits a learned-token-backed attempt to a finite deterministic rule
```

The worldlet may record that a local harness accepted, rejected, blocked, or
penalized an attempt. It must not claim the system chose a TLICA action, formed
a reflective plan, or acquired free-will branch evidence.

## 4. Attempt Construction Support

The kickoff preference should become a hard requirement.

`WorldletAttempt` must not be constructible from a copied
`ProtoOutputActionReadiness(ready=True)` object alone. Readiness is an observed
summary and can become stale or detached from the `OutputHistory` that made it
true.

Construction should require:

```text
ready ProtoOutputActionReadiness
registered OutputTokenCandidate or equivalent support reference
registered LearnedOutputToken for the same token_id
matching token_id and pattern_id across readiness and learned token support
optional printable target_id
source/provenance metadata
```

The future implementation may choose the exact API shape, but the invariant
should be that both facts are checked together:

```text
readiness.ready is True
learned_token.token_id == readiness.token_id
learned_token.pattern_id == readiness.pattern_id
learned_token exists in the supplied/current OutputHistory support
```

If any of those facts is missing, attempt construction should raise. A valid
constructed attempt can still be rejected later by the harness with a bounded
negative response.

## 5. Valence and Provenance

`WorldletValence` should be exact and bounded:

```text
type: Fraction
range: -1 <= value <= 1
out of range: raise
clamping: forbidden
```

`WorldletResponse` should be source-tagged. The catalog patch plan should
prefer reusing the existing source discipline:

```text
FrameSourceKind
Fraction confidence in [0, 1]
tuple of printable trace_event_ids
```

The plan may either reuse `OutputProvenance` directly or define a parallel
worldlet provenance dataclass with the same validation discipline. It should not
add a worldlet-specific source enum member unless the patch plan gives a
specific reason.

Response provenance should identify the response as local harness evidence, not
as external-world observation. The response can be deterministic and
source-tagged without becoming a `PerceptEvent`.

## 6. Failed Attempts

The kickoff's constructor-failure vs consequence-failure distinction should be
preserved:

```text
constructor invalidity -> raise
valid attempt rejected by harness -> WorldletResponse with negative bounded valence
valid attempt against unavailable target -> WorldletResponse with negative bounded valence
valid attempt against missing target -> WorldletResponse with negative bounded valence
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
```

The response reason should be finite and inspectable, for example:

```text
accepted
token-rejected
target-unavailable
target-missing
unsupported-attempt
```

Those reason strings are local harness outcomes, not psychological states.

## 7. Not-I Pushback

The not-I pushback language is acceptable if it remains local and operational.

The future rows should define not-I pushback as:

```text
the deterministic harness can return a response that differs from the
attempt's implicit success condition
```

It should not be defined as contact with external reality.

Safe wording:

```text
local harness pushback
deterministic response evidence
bounded consequence evidence
not chosen by the attempt object
```

Unsafe wording:

```text
real environment feedback
external-world truth
teacher correction
social response
understanding the token
```

`WorldletState` may change only by deterministic worldlet rules. Any state
change remains local to `WorldletHistory.latest_state`.

## 8. Row Status Guidance

The catalog patch plan should use conservative statuses.

Recommended REQUIRED rows:

```text
WorldletValence is a Fraction in [-1, 1] and never silently clamps.
WorldletHistory appends attempts/responses copy-on-write.
WorldletAttempt requires ready readiness plus registered learned-token support.
WorldletResponse and worldlet operations do not mutate TLICA runtime state.
Valid rejected/unavailable/missing-target attempts produce bounded negative responses.
```

Recommended STRUCTURAL rows:

```text
WorldletState and WorldletObject are finite deterministic records.
WorldletAttempt exposes no Act, ModeOp, AgencyWitness, PerceptEvent,
selected-action, feasibleProjectedPCE, or tick callback.
WorldletResponse carries bounded valence and source/provenance metadata.
Worldlet response provenance reuses the existing source discipline or an exact
parallel validation discipline.
```

Recommended OBSERVED rows:

```text
Aggregate local consequence history can be summarized for inspection.
Qualitative not-I pushback can be reported as local harness evidence.
```

Do not make qualitative not-I summaries REQUIRED unless they have an exact,
deterministic assertion. Do not use OBSERVED rows to smuggle in runtime
promotion or external-world claims.

## 9. Proto-BASIC and REPL Leakage

No Proto-BASIC or REPL semantics appear necessary for the Minimal Worldlet.

The future plan should reject fields or fixtures that imply:

```text
grammar
parser
command syntax
prompt loop
host execution
open-ended sandbox execution
natural-language teacher
readability predictor
social/language exchange
```

An accepted token ID is only an exact learned-token identifier used by a finite
deterministic rule. It is not a word, command, expression, or instruction.

## 10. PerceptEvent and Tick Boundary

Worldlet evidence must remain local in Phase 3.3.

The catalog patch plan should explicitly state:

```text
WorldletAttempt does not emit PerceptEvent.
WorldletResponse does not emit PerceptEvent.
WorldletHistory does not call tick().
Worldlet operations do not modify profile, MSI, PtCns, or content registry.
Worldlet evidence does not enter traces or scenarios except through later
explicitly accepted phase work.
```

Any future path that promotes worldlet evidence into `PerceptEvent` or `tick()`
requires a later accepted campaign step. It is not authorized by Phase 3.3
planning.

## 11. Catalog Patch Plan Requirements

The next artifact, `PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md`, should
turn this corrigenda into exact row mechanics:

```text
I-WLD-* row IDs
statuses
owning modules
fixture files
count impact from v0.7
implementation order
pending-registration strategy if needed
validation commands
open decisions
```

The plan should not apply the patch. It should be coherent enough that Step 5
can decide whether implementation is unblocked.

## 12. Final Decision

No blocker prevents drafting the catalog patch plan.

Proceed to:

```text
PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md
```

The next step should remain planning-only and should not touch runtime modules,
fixtures, catalog rows, generated IDs, `tick()`, TLICA Lean reference files,
scenario files, trace files, or LLM behavior.
