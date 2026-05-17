# PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md

## 1. Purpose

Phase 3.3 introduces the Minimal Worldlet planning surface.

This kickoff is a planning artifact. It does not apply catalog rows, create
runtime modules, add fixtures, or change the TLICA runtime boundary.

The implementation target is narrow:

```text
WorldletState
WorldletObject
WorldletAttempt
WorldletResponse
WorldletValence
WorldletHistory
```

The core rule is:

```text
A worldlet attempt may become consequence-bearing inside a finite deterministic
harness, but it remains below language, below reflective agency, below Mode B,
and below real-world action.
```

## 2. Inherited Baseline

The inherited baseline is catalog v0.7 from Phase 3.2:

```text
99 REQUIRED
24 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
3 OBSERVED
```

Phase 3.2 provides the local output-history bridge:

```text
OutputHistory
OutputPattern
OutputTokenCandidate
LearnedOutputToken
ProtoOutputActionReadiness
```

The inherited boundary is still active:

```text
Output readiness is local history evidence only.
It is not agency, language, or world consequence.
```

Phase 3.3 should consume that readiness only as support for constructing a
bounded worldlet attempt. It must not retrofit Phase 3.2 output rows into
world causality.

## 3. Minimal Worldlet Scope

The Minimal Worldlet is a finite deterministic harness with a small object
surface and a local response history.

The surface should support:

```text
finite WorldletState
optional finite WorldletObject targets
WorldletAttempt from learned output support
WorldletResponse from deterministic rules
WorldletValence bounded in [-1, 1]
WorldletHistory as the only mutation target
```

The surface should not require changes to:

```text
brain/tlica/
lean_reference/
brain/tick.py
brain/llm/
scenarios/
traces/
```

Worldlet evidence belongs in local developmental history only. It should not
enter `PerceptEvent`, `tick()`, profile, MSI, PtCns, or content registry in
Phase 3.3.

## 4. Proposed Object Model

### WorldletState

`WorldletState` is the immutable snapshot of the deterministic harness.

It should carry only finite data:

```text
state_id
objects
step_index
```

The state must be inspectable and deterministic. Any object lookup or rule
application should produce the same result for the same state and attempt.

### WorldletObject

`WorldletObject` is a bounded target surface if the catalog patch plan keeps a
target layer.

It should carry finite target facts such as:

```text
object_id
label
available
accepted_token_ids
```

`accepted_token_ids` are not grammar. They are exact learned-token identifiers
that the deterministic harness may accept for a specific object.

### WorldletAttempt

`WorldletAttempt` is a below-agency attempt record.

It should be constructed only from:

```text
ready ProtoOutputActionReadiness
registered LearnedOutputToken support
optional target_id
source/provenance metadata
```

Construction should reject incomplete readiness, missing learned-token support,
reserved identifiers, and non-printable attempt IDs.

The attempt must not expose or carry:

```text
Act
ModeOp
AgencyWitness
PerceptEvent
selected action
feasibleProjectedPCE
tick callback
```

### WorldletResponse

`WorldletResponse` records what the deterministic harness returned.

It should carry:

```text
response_id
attempt_id
accepted
reason
valence
source/provenance metadata
```

The response is consequence evidence only inside the minimal harness. It is not
a truth claim about an external world and not a runtime self-model update.

### WorldletValence

`WorldletValence` should be exact and bounded:

```text
Fraction
-1 <= value <= 1
```

There is no silent clamping. Out-of-bound values should raise at construction.

The initial deterministic convention should be simple:

```text
accepted valid attempt: positive or neutral bounded valence
rejected invalid attempt: negative bounded valence
unavailable target: negative bounded valence
```

The exact values can be fixed in the catalog patch plan, but every value must
remain local to worldlet response history.

### WorldletHistory

`WorldletHistory` is the append-only / copy-on-write store for attempts and
responses.

It should carry:

```text
attempts
responses
latest_state
```

Appending an attempt or response should return a new history object and preserve
prior history. No worldlet operation should mutate existing history in place.

## 5. Not-I Pushback

The not-I signal is the response rule, not an external reality claim.

An attempt proposes a token-backed operation to the harness. The harness returns
a response that is determined by `WorldletState` and local rules, not by the
attempt's desired outcome.

The minimal pushback cases are:

```text
target accepts token -> bounded accepted response
target rejects token -> bounded negative response
target unavailable -> bounded negative response
target missing -> bounded negative response
```

These cases are enough to make the attempt consequence-bearing while preserving
the below-agency boundary.

## 6. Readiness to Attempt Bridge

The bridge from Phase 3.2 should be explicit:

```text
OutputTokenCandidate
LearnedOutputToken
ProtoOutputActionReadiness(ready=True)
WorldletAttempt
```

Readiness alone should not be treated as a command. The kickoff preference is
that a `WorldletAttempt` requires both a ready readiness observation and the
registered learned token that made that observation true.

This avoids a weak path where an observed readiness record is copied without
checking the current `OutputHistory` / learned-token support.

## 7. Deterministic Consequence Rules

The first implementation should use total deterministic rules:

```text
respond(state, attempt) -> (next_state, response)
append_worldlet_attempt(history, attempt) -> WorldletHistory
append_worldlet_response(history, response, next_state) -> WorldletHistory
```

The rule may update only local worldlet state and worldlet history. If an
attempt is invalid, unavailable, or unsupported, it should still produce a
bounded response record rather than raising after construction, unless the
attempt object itself violates constructor invariants.

Constructor invalidity and consequence failure are different:

```text
constructor invalidity -> raise
valid attempt rejected by harness -> bounded negative response
```

## 8. Source and Provenance Discipline

Worldlet attempts and responses should reuse the existing Phase 3.1 / Phase 3.2
source discipline where possible.

The initial preference is:

```text
FrameSourceKind values only
Fraction confidence in [0, 1]
trace_event_ids as printable local provenance IDs
no new source-kind enum member unless the catalog patch plan justifies it
```

This keeps worldlet evidence aligned with the existing source-tag audit and
prevents a new worldlet-specific source category from bypassing established
constructor checks.

## 9. Row Status Guidance

The future catalog patch plan should classify rows conservatively.

Likely REQUIRED rows:

```text
bounded valence
copy-on-write worldlet history
attempt construction requires learned-token/readiness support
responses cannot mutate TLICA runtime state
invalid/unavailable attempts produce bounded negative responses
```

Likely STRUCTURAL rows:

```text
finite state/object shape
worldlet attempt is not Act / AgencyWitness / PerceptEvent
response source/provenance shape
```

Likely OBSERVED rows:

```text
aggregate local consequence history
qualitative not-I pushback summaries
```

The next catalog patch plan should decide exact row IDs, counts, fixtures, and
status impact. This kickoff does not apply those rows.

## 10. Fixture Direction

Initial fixture families should stay small:

```text
worldlet_state.py
worldlet_response.py
worldlet_attempt.py
worldlet_consequence.py
```

Expected fixture coverage:

```text
finite state construction
bounded valence rejection on out-of-range values
copy-on-write history append
attempt construction from ready learned-token support
attempt rejection without agency fields
valid accepted response
valid rejected response
unavailable target response
no profile/MSI/PtCns/registry mutation
```

The fixtures should not run real LLM commands and should not invoke real
scenario execution.

## 11. Implementation Order

After corrigenda and catalog patch planning, the safe implementation order is:

1. Add catalog rows and generated IDs.
2. Add pending registry coverage only if needed for catalog coherence.
3. Implement `WorldletValence`, `WorldletState`, `WorldletObject`, and
   `WorldletHistory`.
4. Add state/response fixtures and targeted invariant checks.
5. Implement `WorldletAttempt` construction from learned output support.
6. Add consequence rules and attempt/consequence fixtures.
7. Run targeted `I-WLD-*` checks.
8. Run the full catalog/count/citation/import/invariant gate.

No step should require `brain/tick.py` or TLICA Lean-reference edits.

## 12. Validation for This Kickoff

This kickoff should be validated only as a planning artifact:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

The next artifact is:

```text
PHASE3_3_MINIMAL_WORLDLET_CORRIGENDA.md
```

The corrigenda should tighten this kickoff before any catalog patch or runtime
implementation begins.
