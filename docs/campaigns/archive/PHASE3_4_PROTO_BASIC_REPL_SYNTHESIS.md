# PHASE3_4_PROTO_BASIC_REPL_SYNTHESIS.md

## 1. Purpose

Phase 3.4 defines the Proto-BASIC REPL that follows the Phase 3.3 Minimal
Worldlet.

This document is a synthesis artifact only. It does not authorize catalog
patches, runtime modules, fixture additions, full REPL behavior, real host
execution, an actual BASIC interpreter, expression/readability work,
social/language behavior, or Mode B implementation.

Core thesis:

```text
Proto-BASIC gives the system a deterministic rule-governed output worldlet
where syntax, near-miss correction, and bounded consequence can be learned
through local feedback. It is not a real interpreter, not host execution,
not language understanding, and not reflective agency.
```

Phase 3.4 preserves the inherited Phase 3 bridge principle:

```text
PRESERVE should be earned, not labeled.
```

The Proto-BASIC REPL extends that principle to syntax. A learned output token
should not become a command because it happens to look like one. It should
become a Proto-BASIC command only when a constrained deterministic grammar
accepts it, and even then the feedback should reward effective behavior, not
the mere appearance of syntactic form.

The Phase 3.3 boundary remains in force:

```text
Worldlet consequence evidence is local deterministic harness evidence; it is
not external reality, reflective agency, language, Mode B, or runtime
promotion.
```

## 2. Current Baseline (v0.8)

The inherited baseline is Phase 3.3 / catalog v0.8:

```text
105 REQUIRED
29 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
4 OBSERVED
```

The v0.8 gate covers the deterministic Minimal Worldlet:

```text
WorldletState
WorldletAttempt
WorldletResponse
WorldletValence (bounded in [-1, 1])
WorldletProvenance
WorldletHistory
respond_worldlet
WorldletConsequenceSummary (local-harness evidence scope)
```

The important Phase 3.3 result is not that the system has language, agency,
or world contact. It is that the system can route a learned output token into
a bounded attempt, receive a deterministic accepted / rejected / unavailable
/ missing-target response with bounded valence, and write that response into
local worldlet history without mutating profile, MSI, PtCns, registry,
trace, or `tick()` state.

The Phase 3.3 audit reports PASS. The full gate is green, `I-WLD-*` rows are
registered and green, `I-WLD-12` is OBSERVED only, worldlet responses are
local consequence evidence, valence is exact and bounded, and not-I pushback
is not an external-reality claim.

## 3. Why a Constrained REPL Follows Worldlet Consequence Evidence

The Minimal Worldlet comes before the Proto-BASIC REPL because syntactic
interaction needs a consequence-bearing surface to act against. Without local
worldlet history that records bounded accepted / rejected outcomes, REPL
syntax would just be a string predicate with no developmental meaning behind
it.

Phase 3.3 leaves exactly one bridge point into Phase 3.4:

```text
WorldletHistory + learned output token support
```

That history is local and bounded. It says the system has produced a small
set of learned output tokens that have been tested against a deterministic
harness and accumulated bounded acceptance / rejection evidence. It does not
say the tokens are commands, words, selected `Act`s, agency witnesses, or
real-world operations.

Phase 3.4 should therefore ask the next conservative question:

```text
Can a learned, recurrent, worldlet-tested output token participate in a
constrained deterministic grammar with parse-classified outcomes and bounded
feedback valence, without becoming language, host execution, free-will
agency, or Mode B planning?
```

This puts Proto-BASIC after worldlet pushback but before expression and
social language. The system should first meet bounded resistance through the
worldlet, then meet rule-governed syntactic structure through Proto-BASIC,
and only then attempt expression-layer or social-language work.

## 4. Proto-BASIC Thesis

The Proto-BASIC REPL should be a finite deterministic grammar with a narrow
surface:

```text
ProtoBasicToken
ProtoBasicLine
ProtoBasicProgram / one-line command surface
ProtoBasicParseResult (valid / near-miss / syntax-invalid / semantic-invalid
                      / tool-unavailable / resource-limit / sandbox-fault)
ProtoBasicCommand
ProtoBasicExecutionResult
ProtoBasicFeedback
ProtoBasicValence (bounded in [-1, 1])
ProtoBasicHistory
```

`ProtoBasicToken` is a fixed enumeration of legal lexical units. It is not an
extension point for natural language, not a free string surface, and not a
tokenizer over real source code.

`ProtoBasicLine` and the one-line command surface enforce a strictly finite
grammar. The grammar is small enough to enumerate completely. There is no
control flow, no I/O, no host call, no `eval`, no subprocess, no file system
mutation outside local in-memory REPL state.

`ProtoBasicParseResult` distinguishes outcomes deterministically. A valid
parse is structurally well-formed and semantically permissible. A near-miss
is structurally close to a valid form by a bounded local edit distance.
Syntax-invalid, semantic-invalid, tool-unavailable, resource-limit, and
sandbox-fault are bounded local categories; none of them is a real
operating-system error or a real interpreter exception.

`ProtoBasicCommand` and `ProtoBasicExecutionResult` describe deterministic
local effects on `ProtoBasicHistory` only. They do not call `tick()`, do not
emit `PerceptEvent`, do not mutate TLICA runtime state, and do not touch the
guarded scenario, trace, or LLM seams.

`ProtoBasicFeedback` carries bounded valence and structured near-miss
correction hints. Hints are local feedback derived from the grammar; they
are not language, not teacher correction, and not a social exchange. Hints
say only that a near-miss differs from a valid form by a specific local
edit.

`ProtoBasicHistory` is the local store for parse results, execution results,
and feedback. It is copy-on-write / append-only in the same spirit as
`OutputHistory` and `WorldletHistory`. Entries stay in Proto-BASIC history.
They do not enter the profile, MSI, PtCns, registry, scenario schema, trace
files, or `tick()` semantics.

## 5. Syntax as Bounded Worldlet Interaction, Not Language

Proto-BASIC syntax is bounded worldlet interaction. It is rule-governed
form: an attempt is well-formed when the grammar accepts it, and it is
effective when the harness produces a defined non-null change to
`ProtoBasicHistory` beyond bare acknowledgement.

Proto-BASIC syntax is not language. Specifically:

```text
no semantics over a referential world
no pragmatics
no social interlocutor
no natural-language tokens
no teacher / corrector agent
no inferential meaning beyond local grammar
no compositional understanding beyond the finite grammar
no expression-layer signal
no readability predictor
no Mode B reflective interpretation
```

The grammar should be small enough that exhaustive enumeration of legal
forms is a practical test. The system meets a constrained rule surface,
discovers which strings the surface accepts, and learns to produce
accepted-and-effective strings. That is syntactic shaping, not language.

## 6. Parse Result Categories

Phase 3.4 should treat the parse result as a deterministic classifier with
at least these categories:

```text
valid            - structurally well-formed and semantically permissible
near-miss        - within bounded local edit distance of a valid form
syntax-invalid   - not within bounded edit distance of any valid form
semantic-invalid - structurally valid but disallowed by local rules
tool-unavailable - references a Proto-BASIC operation not present in this build
resource-limit   - exceeds a bounded local resource cap (length / depth / count)
sandbox-fault    - a local containment guard fired during parse or eval
```

`tool-unavailable`, `resource-limit`, and `sandbox-fault` are local
deterministic categories. They do not mean a real operating-system tool was
missing, a real resource limit was hit, or a real sandbox alarmed.

Near-miss is the most developmentally important non-valid category. It
should be defined by a small, deterministic local edit-distance bound, and
the resulting feedback should include structured correction hints that name
the specific local edit. Hints are local feedback only; they do not
constitute language.

## 7. Bounded Valence and Anti-Goodhart Requirements

`ProtoBasicValence` must be an exact `Fraction` in `[-1, 1]`. It is never
silently clamped, never represented as a raw `float`, and never extended
beyond the unit interval.

Bounded valence by category:

```text
valid-effective    -> positive bounded valence
valid-ineffective  -> weak / non-strong (small or zero) bounded valence
near-miss          -> small negative or neutral bounded valence + correction hint
syntax-invalid     -> bounded negative valence
semantic-invalid   -> bounded negative valence
tool-unavailable   -> bounded negative valence
resource-limit     -> bounded negative valence
sandbox-fault      -> bounded negative valence
```

Anti-Goodhart requirements:

```text
valid syntax alone does not earn strong positive feedback
strong positive feedback requires an observable effect on ProtoBasicHistory
repeated identical no-op commands receive diminishing returns
repeated trivially-effective commands do not dominate history summaries
the feedback distribution is not driven by emission rate alone
```

The point is that Proto-BASIC should not become a reward-hacking surface. A
system that has learned to emit one strongly-positive command and emits it
forever should not produce a runaway positive signal. The grammar must
reward effective behavior, not emission alone, and history summaries must
reflect this through bounded diminishing returns or an explicit
effect-required gate.

## 8. Why This Remains Below Expression, Social Language, and Mode B

Proto-BASIC REPL is rule-governed and consequence-bearing, but it is still
below expression, social language, and reflective Mode B agency.

The boundary is:

```text
parse result is not language understanding
near-miss correction is not teacher correction
execution result is not Act selection
feedback is not affect taxonomy
history summary is not PerceptEvent or TLICA mutation
grammar is not real interpreter semantics
sandbox-fault is not a real sandbox alarm
resource-limit is not a real resource exhaustion
tool-unavailable is not a real missing OS tool
REPL command is not free-will branch selection
REPL history is not Mode B reflective planning material in this phase
```

Proto-BASIC may show that an output token, once tested against worldlet
pushback, can be further constrained by a deterministic local grammar and
learn to satisfy that grammar in effective ways. It does not show that the
system understands the grammar, can extend it, can compose new commands
beyond the finite enumeration, can talk about its own commands, or can plan
new commands reflectively.

Mode B and expression remain out of scope. Phase 3.4 may provide material
that a later expression layer or Mode B layer could inspect, but it must not
implement readability prediction, expression evaluation, reflective
planning, or parallel developmental reasoning.

## 9. Non-Goals

Phase 3.4 must not implement or smuggle in:

```text
real BASIC interpreter
host execution
shell access
subprocess invocation
file I/O outside in-memory REPL state
network I/O
arbitrary Python execution
eval / exec
open-ended sandbox execution
natural language teacher
expression / readability layer
readability predictor
social / language harness
Mode B reflective planning
real LLM training behavior
prompt tuning to force scenario outcomes
seeded-MSI shortcuts
direct mutation of TLICA state
Proto-BASIC history promotion into PerceptEvent
Proto-BASIC feedback promotion into the affect taxonomy
free-will branch semantics through REPL commands
```

Proto-BASIC is not a real programming language. It is not a real
interpreter. It is not a social interlocutor. It is not a real sandbox. It
is a deterministic constrained grammar with bounded local feedback.

## 10. Expected Phase Ordering

The inherited Phase 3 order remains:

```text
Phase 3.1 - Osmotic Chamber
Phase 3.2 - Output Ladder
Phase 3.3 - Minimal Worldlet
Phase 3.4 - Proto-BASIC REPL
Phase 3.5 - Expression + ReadabilityPredictor
Phase 3.6 - Social / language harness
```

Phase 3.4 belongs between worldlet pushback and expression because the
system needs rule-governed syntactic structure with bounded local feedback
before it can be evaluated for expressiveness or readability, and well
before it enters a social-language exchange.

## 11. Risks

Main risks:

- Treating Proto-BASIC syntax as language.
- Treating a valid parse as sufficient for strong positive feedback.
- Letting near-miss correction become teacher correction or a social
  exchange.
- Letting Proto-BASIC history enter `PerceptEvent` or `tick()` without an
  explicit later phase.
- Letting `sandbox-fault`, `tool-unavailable`, or `resource-limit` cross the
  local-harness boundary and look like real OS or runtime errors.
- Letting bounded negative feedback grow into affect taxonomy, fear, or
  avoidance pathology.
- Introducing real host execution, subprocess, or file/network I/O.
- Introducing arbitrary Python `eval` / `exec` as a shortcut.
- Reward hacking: emitting one strongly-positive command in a loop and
  dominating history summaries.
- Expanding the grammar beyond a small finite surface before later phases
  authorize it.
- Tuning prompts or seeded MSIs solely to force the four-tick scenario or
  any other gate to pass.

The safe rule is to keep every parse, execution, and feedback local,
deterministic, bounded, exhaustively enumerable, and auditable. If a
property needs real execution, real I/O, real semantics over an external
world, real teacher correction, reflective planning, or runtime self-model
mutation, it belongs in a later phase.

## 12. Next Artifact

The next artifact is:

```text
PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md
```

That kickoff should lock only the Phase 3.4 planning surface:

```text
ProtoBasicToken
ProtoBasicLine
ProtoBasicProgram / one-line command surface
ProtoBasicParseResult
ProtoBasicCommand
ProtoBasicExecutionResult
ProtoBasicFeedback
ProtoBasicValence bounded in [-1, 1]
ProtoBasicHistory
near-miss correction hints
valid / near-miss / syntax-invalid / semantic-invalid / tool-unavailable /
  resource-limit / sandbox-fault categories
anti-Goodhart controls (diminishing returns and effect-required reward)
connection from WorldletHistory / learned output token support to
  Proto-BASIC attempts
Proto-BASIC operations do not call tick(), do not emit PerceptEvent, and do
  not mutate TLICA runtime state
```

No catalog patch or runtime implementation should occur before kickoff,
corrigenda, and catalog patch planning are complete.
