# PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md

## 1. Purpose

Phase 3.4 introduces the Proto-BASIC REPL planning surface.

This kickoff is a planning artifact. It does not apply catalog rows, create
runtime modules, add fixtures, change the TLICA runtime boundary, or authorize
host execution of any kind.

The implementation target is narrow:

```text
ProtoBasicToken
ProtoBasicLine
ProtoBasicProgram / one-line command surface
ProtoBasicParseResult
ProtoBasicCommand
ProtoBasicExecutionResult
ProtoBasicFeedback
ProtoBasicValence
ProtoBasicHistory
```

The core rule is:

```text
A Proto-BASIC attempt may carry deterministic syntactic structure and bounded
local consequence inside a finite enumerable grammar, but it remains below a
real interpreter, below host execution, below language understanding, below
reflective Mode B agency, and below social exchange.
```

## 2. Inherited Baseline

The inherited baseline is catalog v0.8 from Phase 3.3:

```text
105 REQUIRED
29 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
4 OBSERVED
```

Phase 3.3 provides the local worldlet-consequence bridge:

```text
WorldletState
WorldletObject
WorldletAttempt
WorldletResponse
WorldletValence (bounded in [-1, 1])
WorldletProvenance
WorldletHistory
respond_worldlet
WorldletConsequenceSummary
```

The inherited boundary is still active:

```text
Worldlet consequence evidence is local deterministic harness evidence;
it is not external reality, reflective agency, language, Mode B, or runtime
promotion.
```

Phase 3.4 should consume the worldlet bridge only as support for constructing
a Proto-BASIC attempt. It must not retrofit Phase 3.3 worldlet rows into
external execution, real interpreter semantics, or language understanding.

## 3. Proto-BASIC REPL Scope

The Proto-BASIC REPL is a finite deterministic grammar with a small command
surface and a local history.

The surface should support:

```text
finite ProtoBasicToken enumeration
finite one-line ProtoBasicLine grammar
deterministic ProtoBasicParseResult classifier
ProtoBasicCommand from learned-output / worldlet support
ProtoBasicExecutionResult from local deterministic rules
ProtoBasicFeedback with bounded valence and structured near-miss hints
ProtoBasicValence bounded in [-1, 1]
ProtoBasicHistory as the only mutation target
```

The surface should not require changes to:

```text
brain/tlica/
lean_reference/
brain/tick.py
brain/llm/
scenarios/
traces/
brain/development/worldlet.py runtime semantics
brain/development/output.py runtime semantics
```

Proto-BASIC evidence belongs in local developmental history only. It should
not enter `PerceptEvent`, `tick()`, profile, MSI, PtCns, content registry,
trace seam, or scenario schema in Phase 3.4.

## 4. Proposed Object Model

### ProtoBasicToken

`ProtoBasicToken` is a fixed enumeration of legal lexical units.

It should carry only finite data:

```text
token_id
kind (e.g. KEYWORD, VAR, NUMBER, PUNCT)
text (canonical printable form)
```

`ProtoBasicToken` is not a free string surface, not a tokenizer over real
source code, not a natural-language token, and not an extension point for
language semantics. The set of legal tokens is enumerable and fixed at
construction time for a given build of Proto-BASIC.

Construction should reject:

```text
unknown kinds
non-printable text
empty or whitespace-only text
text exceeding a small fixed length cap
duplicate canonical text within the enumeration
```

### ProtoBasicLine

`ProtoBasicLine` is a single one-line Proto-BASIC input.

It should carry only finite data:

```text
line_id
raw_text (printable, bounded length)
tokens (tuple[ProtoBasicToken, ...])
```

`ProtoBasicLine` is the unit of REPL submission. It is bounded in length, in
token count, and in lexical content. There is no multi-line program, no
control flow, no block structure, no nested expressions beyond the finite
grammar.

The kickoff preference is that `ProtoBasicLine` is constructed from a single
tokenization pass over `raw_text`. The tokenization is deterministic and
total: for any well-formed `raw_text`, it returns the same token sequence.

### ProtoBasicProgram / one-line command surface

Phase 3.4 should restrict the program surface to a one-line command surface.

The kickoff preference is:

```text
one ProtoBasicLine per submission
no multi-line program
no GOTO / GOSUB / loop structure
no stored program memory beyond ProtoBasicHistory entries
```

If a `ProtoBasicProgram` wrapper exists at all in Phase 3.4, it should be a
trivial one-line wrapper kept only for symmetry with later phases. It must
not introduce control flow, line-numbered storage, or stored-program
semantics.

### ProtoBasicParseResult

`ProtoBasicParseResult` is a deterministic classifier over `ProtoBasicLine`.

It should distinguish at least these categories:

```text
valid             - structurally well-formed and semantically permissible
near-miss         - within bounded local edit distance of a valid form
syntax-invalid    - not within bounded edit distance of any valid form
semantic-invalid  - structurally valid but disallowed by local rules
tool-unavailable  - references a Proto-BASIC operation not present in this build
resource-limit    - exceeds a bounded local resource cap
sandbox-fault     - a local containment guard fired during parse or eval
```

Each category is local and deterministic. None of them is a real
operating-system error, a real interpreter exception, a real sandbox alarm,
or a real resource exhaustion.

The parse result should carry:

```text
result_id
line_id
category
correction_hint (optional, only meaningful for near-miss)
source/provenance metadata
```

Near-miss is the most developmentally important non-valid category. It
should be defined by a small, deterministic local edit-distance bound (for
example, single-token substitution, single-token insertion, single-token
deletion, or single-keyword case fold). The bound should be small enough to
make near-miss enumerable from a valid form.

### ProtoBasicCommand

`ProtoBasicCommand` is the post-parse command record for a valid line.

It should be constructed only from:

```text
ProtoBasicParseResult with category == valid
registered ProtoBasicToken support for every token in the line
optional bridge support from LearnedOutputToken / WorldletHistory
source/provenance metadata
```

Construction should reject:

```text
non-valid parse results
unknown token references
reserved command identifiers
non-printable command IDs
```

`ProtoBasicCommand` must not expose or carry:

```text
Act
ModeOp
AgencyWitness
PerceptEvent
selected action
feasibleProjectedPCE
tick callback
real interpreter handle
host subprocess handle
file descriptor
network socket
```

### ProtoBasicExecutionResult

`ProtoBasicExecutionResult` records what the local deterministic harness
returned for a `ProtoBasicCommand`.

It should carry:

```text
result_id
command_id
effective (bool: did execution change ProtoBasicHistory beyond bare ack?)
category (valid-effective, valid-ineffective, tool-unavailable,
          resource-limit, sandbox-fault)
detail (optional bounded local detail string)
source/provenance metadata
```

The execution result is consequence evidence inside the Proto-BASIC harness
only. It is not a truth claim about an external world, a runtime self-model
update, or a real interpreter return value.

### ProtoBasicFeedback

`ProtoBasicFeedback` records the bounded valence and any near-miss correction
hints associated with a parse or execution result.

It should carry:

```text
feedback_id
parse_result_id or execution_result_id
valence (ProtoBasicValence)
correction_hint (optional, structured, near-miss only)
diminishing_returns_factor (Fraction in [0, 1])
source/provenance metadata
```

Hints are local feedback derived from the grammar. They are not language,
not teacher correction, and not a social exchange. A hint says only that a
near-miss differs from a specific valid form by a specific local edit.

### ProtoBasicValence

`ProtoBasicValence` should be exact and bounded:

```text
Fraction
-1 <= value <= 1
```

There is no silent clamping. Out-of-bound values should raise at construction.

The initial deterministic convention should be:

```text
valid-effective    -> positive bounded valence
valid-ineffective  -> weak / non-strong (small or zero) bounded valence
near-miss          -> small negative or neutral bounded valence
syntax-invalid     -> bounded negative valence
semantic-invalid   -> bounded negative valence
tool-unavailable   -> bounded negative valence
resource-limit     -> bounded negative valence
sandbox-fault      -> bounded negative valence
```

The exact values should be fixed in the catalog patch plan. Every value must
remain local to Proto-BASIC feedback and must not be promoted into affect
taxonomy, profile values, MSI scoring, or PtCns weights.

### ProtoBasicHistory

`ProtoBasicHistory` is the append-only / copy-on-write store for parse
results, commands, execution results, and feedback.

It should carry:

```text
parse_results
commands
execution_results
feedback
emit_counts (per canonical command form)
```

Appending any entry should return a new `ProtoBasicHistory` object and
preserve prior history. No Proto-BASIC operation should mutate existing
history in place.

`emit_counts` exists to support anti-Goodhart diminishing returns: it tracks
how many times each canonical command form has been submitted, so the
feedback layer can reduce strong positive valence for repeated identical
no-op or trivially-effective commands.

## 5. Parse Result Categories and Boundaries

The seven parse categories partition Proto-BASIC outcomes deterministically.
The boundary between each category is fixed by local rules, not by external
runtime behavior.

```text
valid             - grammar accepts; local semantics permit; effect possible
near-miss         - one bounded edit from a valid form; hint required
syntax-invalid    - no bounded edit reaches a valid form
semantic-invalid  - grammar accepts but local semantics reject
tool-unavailable  - command references an unbuilt local operation
resource-limit    - submission exceeds a small fixed local cap
sandbox-fault     - a local containment guard fired
```

Important non-claims:

```text
tool-unavailable is not a missing OS tool
resource-limit is not a real CPU/memory/disk exhaustion
sandbox-fault is not a real sandbox alarm
syntax-invalid is not a real parser exception
semantic-invalid is not a real type error
near-miss is not teacher correction
valid is not language understanding
```

## 6. Near-Miss Correction Hints

Near-miss correction hints are structured local feedback only.

A hint should carry:

```text
hint_id
parse_result_id
edit_kind (e.g. SUBSTITUTE_TOKEN, INSERT_TOKEN, DELETE_TOKEN, CASE_FOLD)
edit_position (token index, bounded)
expected_token_id (optional, must reference an enumerated ProtoBasicToken)
observed_token_text (optional, bounded, printable)
```

Hints are not natural-language explanations. They do not include free-form
strings, advice, or social phrasing. A hint is a deterministic edit record
that names the local distance from a valid form.

The hint generator must:

```text
return the same hint for the same line under the same grammar
emit at most one canonical hint per near-miss
respect the bounded edit distance defined by the grammar
not invoke any external corrector, teacher, or language model
```

## 7. Anti-Goodhart Controls

Anti-Goodhart controls keep Proto-BASIC from becoming a reward-hacking
surface. The two primary controls are diminishing returns and effect-required
reward.

Diminishing returns:

```text
the feedback layer reads emit_counts for the canonical command form
strong positive valence decays as emit_counts grows
the decay is deterministic, bounded, and exact (Fraction)
the decay does not push valence outside [-1, 1]
the decay is not reset by interleaving other commands
```

Effect-required reward:

```text
valid syntax alone does not earn strong positive feedback
strong positive feedback requires execution_result.effective == True
valid-ineffective execution receives weak / non-strong feedback
ProtoBasicHistory summaries reflect effective behavior, not emission rate
```

Combined, the controls enforce:

```text
emitting one strongly-positive command in a loop does not dominate history
syntactic conformance is necessary but not sufficient for strong positive feedback
emission rate alone does not drive the feedback distribution
```

These controls live entirely inside Proto-BASIC. They do not feed into the
affect taxonomy, the profile, the MSI, PtCns, or `tick()`.

## 8. Worldlet / Output Bridge

The bridge from Phase 3.2 and Phase 3.3 should be explicit.

```text
OutputTokenCandidate
LearnedOutputToken
ProtoOutputActionReadiness(ready=True)
WorldletAttempt (and bounded WorldletResponse history)
WorldletHistory + learned output token support
ProtoBasicCommand
```

The kickoff preference is that a `ProtoBasicCommand` may only be constructed
from a valid parse whose tokens reference enumerated `ProtoBasicToken`s, and
only when the supporting learned-output / worldlet evidence is present in
local history.

Specifically:

```text
each ProtoBasicToken used in a command should be enumerated at build time
tokens whose appearance depends on learned-output support should be gated
  on registered LearnedOutputToken records in OutputHistory
worldlet evidence should never be required for a parse result, only for a
  command record
```

This avoids a weak path where the REPL accepts a command based purely on
string shape without any output/worldlet support behind it.

The bridge is one-way:

```text
output / worldlet evidence -> ProtoBasicCommand support
ProtoBasicHistory entries -> do not flow back into OutputHistory,
                              WorldletHistory, PerceptEvent, tick(), or
                              TLICA runtime state in Phase 3.4
```

## 9. Deterministic Local Rules

Phase 3.4 implementation should use total deterministic rules:

```text
tokenize(raw_text) -> tuple[ProtoBasicToken, ...]
parse_line(line) -> ProtoBasicParseResult
build_command(parse_result, support) -> ProtoBasicCommand or rejection
execute_command(command, history) -> (ProtoBasicExecutionResult, history')
score_feedback(parse_result | execution_result, history) -> ProtoBasicFeedback
append_history(history, *entries) -> ProtoBasicHistory
```

Each rule should be:

```text
deterministic
total over its declared input domain
local (touches only Proto-BASIC state)
bounded in cost
free of host execution, subprocess, file I/O, network I/O, eval / exec
```

Constructor invalidity and parse / execution rejection are different:

```text
constructor invalidity -> raise (e.g. malformed ProtoBasicToken,
                                  out-of-range valence)
valid line rejected by parser -> ProtoBasicParseResult with non-valid category
valid command failing at execution -> ProtoBasicExecutionResult with
                                       valid-ineffective, tool-unavailable,
                                       resource-limit, or sandbox-fault
                                       category
```

## 10. Source and Provenance Discipline

Proto-BASIC parse results, commands, execution results, and feedback should
reuse the existing source discipline.

The initial preference is:

```text
FrameSourceKind values only
Fraction confidence in [0, 1]
trace_event_ids as printable local provenance IDs
no new source-kind enum member unless the catalog patch plan justifies it
```

This keeps Proto-BASIC evidence aligned with the existing source-tag audit
and prevents a new Proto-BASIC-specific source category from bypassing
established constructor checks.

## 11. Row Status Guidance

The future catalog patch plan should classify rows conservatively. Likely
row family is `I-REPL-*`.

Likely REQUIRED rows:

```text
ProtoBasicValence bounded in [-1, 1]
copy-on-write ProtoBasicHistory append
ProtoBasicCommand construction requires valid parse + token support
ProtoBasicParseResult is total over ProtoBasicLine
parse categories partition deterministically
valid syntax alone does not grant strong positive feedback
strong positive feedback requires execution_result.effective == True
repeated identical no-op commands receive diminishing returns
Proto-BASIC operations do not call tick(), do not emit PerceptEvent, and
  do not mutate TLICA runtime state
near-miss hints respect bounded edit distance
syntax-invalid / semantic-invalid / tool-unavailable / resource-limit /
  sandbox-fault produce bounded negative valence
```

Likely STRUCTURAL rows:

```text
ProtoBasicToken is a finite enumeration
ProtoBasicLine has bounded length and token count
ProtoBasicCommand carries no Act / ModeOp / AgencyWitness / PerceptEvent
ProtoBasicExecutionResult has the declared category set
ProtoBasicFeedback source/provenance shape
```

Likely OBSERVED rows:

```text
aggregate Proto-BASIC history summaries
qualitative anti-Goodhart behavior under repeated emissions
```

The next catalog patch plan should decide exact row IDs, counts, fixtures,
and status impact. This kickoff does not apply those rows.

## 12. Fixture Direction

Initial fixture families should stay small:

```text
repl_grammar.py
repl_feedback.py
repl_execution.py
repl_history.py
```

Expected fixture coverage:

```text
finite ProtoBasicToken enumeration
deterministic tokenize over bounded raw_text
parse categories partition deterministically
near-miss bounded edit distance and canonical hint
valid-effective vs valid-ineffective distinction
diminishing returns under repeated identical commands
bounded valence rejection on out-of-range values
copy-on-write history append
ProtoBasicCommand rejection without learned-output / worldlet support where
  required
ProtoBasicCommand rejection without valid parse
no profile / MSI / PtCns / registry / scenario / trace mutation
no host execution, subprocess, file I/O, network I/O, eval / exec
```

The fixtures should not run real LLM commands and should not invoke real
scenario execution.

## 13. Implementation Order

After corrigenda and catalog patch planning, the safe implementation order is:

1. Add catalog rows and generated IDs (Step 6).
2. Add pending registry coverage only if needed for catalog coherence.
3. Implement `ProtoBasicToken`, `ProtoBasicLine`, `ProtoBasicValence`, and
   `ProtoBasicHistory` (Step 7).
4. Implement `ProtoBasicParseResult` and near-miss correction hints.
5. Implement `ProtoBasicFeedback` with bounded valence.
6. Add grammar/feedback fixtures and run targeted invariant checks.
7. Implement `ProtoBasicCommand` and `ProtoBasicExecutionResult` (Step 8).
8. Add execution/history fixtures and targeted invariant checks.
9. Implement anti-Goodhart controls if the accepted catalog plan includes
   them (Step 9).
10. Run targeted `I-REPL-*` checks.
11. Run the full catalog / count / citation / import / invariant gate
    (Step 10).
12. Draft the Phase 3.4 audit (Step 11).

No step should require `brain/tick.py`, `brain/llm/`, `brain/tlica/`,
`lean_reference/`, `scenarios/`, `traces/`, or TLICA Lean-reference edits.

## 14. Non-Goals

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
multi-line programs
GOTO / GOSUB / loops / stored-program semantics
```

## 15. Validation for This Kickoff

This kickoff should be validated only as a planning artifact:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

The next artifact is:

```text
PHASE3_4_PROTO_BASIC_REPL_CORRIGENDA.md
```

The corrigenda should tighten this kickoff before any catalog patch or
runtime implementation begins.
