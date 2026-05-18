# PHASE3_22B_REASONING_TRACE_SPEC.md

## What "reasoning trace" means here

"Reasoning trace" in Phase 3.22b means an **explicit audit trail of
deterministic structural operations**, not private subjective
reasoning. The trace is externally inspectable, bounded, printable,
and non-claim-clean. It is NOT private chain-of-thought. It is NOT a
metacognitive description of the system's "inner experience". It is
NOT a claim that the runtime "thinks".

A `ReasoningTrace` is a tuple of `ReasoningTraceStep` records. Each
step is a bounded printable description of one deterministic
operation the loop performed on its way from `operator_text` to
`AgentReply`.

## Closed enum: ReasoningStepKind

```
OBSERVE_INPUT
CLASSIFY_REFUSAL
DERIVE_PATTERN
LOOKUP_PRIOR_STRUCTURE
COMPARE_STRUCTURE
CHECK_COHERENCE
CHECK_REPL
SELECT_REPLY_INTENT
CHECK_LIMITATION
EMIT_REPLY
```

### Step semantics

- **OBSERVE_INPUT** — record bounded facts about the operator text
  (length, first 32 chars, first-token category). Always step 1.
- **CLASSIFY_REFUSAL** — run the bounded cognitive-claim classifier;
  record `matched=true` or `matched=false` plus the matched phrase
  index when matched.
- **DERIVE_PATTERN** — call `derive_abstract_pattern_signature`;
  record token count, distinct count, shape string, digest fragment.
- **LOOKUP_PRIOR_STRUCTURE** — consult session-local trace for prior
  records keyed by abstract digest or concrete pattern_id; record
  `hits=<count>` and the first matched digest fragment.
- **COMPARE_STRUCTURE** — compare derived pattern against prior;
  record `transfer=true|false`, `reused=true|false`.
- **CHECK_COHERENCE** — read the cached `coherence_overall_status`
  from the post-dispatch observation; record the value.
- **CHECK_REPL** — read the bridge result (if any); record
  `parse=<value> exec=<value>`.
- **SELECT_REPLY_INTENT** — record the chosen
  `AgentReplyDisposition`.
- **CHECK_LIMITATION** — record whether refusal / warn / fail
  preempts other intents.
- **EMIT_REPLY** — record reply digest fragment and section count.

## Trace properties

- **Deterministic.** Two identical agent calls produce equal traces.
- **Bounded.** `REASONING_TRACE_MAX_STEPS = 32`. Each step's strings
  are bounded under `REASONING_STEP_FIELD_MAX_LEN = 160`.
- **Printable.** Every field is printable; no control characters.
- **Externally inspectable.** A `ReasoningTrace` can be projected to
  a printable table via `format_reasoning_trace_table`.
- **Safe to expose.** Every step's text passes
  `_FORBIDDEN_NON_CLAIM_TERMS` audit.
- **Not hidden chain-of-thought.** The trace is the entire reasoning
  surface; no private state is summarized or hidden.
- **Not a cognitive claim.** The standard disclaimer at the top of
  this document is repeated verbatim in module docstrings and in the
  trace-report header.

## Standard disclaimer (recurring text)

> "Reasoning trace" means an explicit audit trail of deterministic
> structural operations, not private subjective reasoning.

## Embedding in `AgentReply`

Each call to `run_agent_interaction_step` populates
`AgentLoopResult.reasoning_trace`. The reply's
`NEXT_ACTION_SUGGESTION` section may end with a compact trace
reference such as `trace=<digest_hex16>` so an operator can locate
the trace in the run-level transcript.

## Benchmark obligations

A9 axis cases (7 cases):

- A9.01 every agent reply has a non-empty reasoning trace
- A9.02 refusal reply trace shows CLASSIFY_REFUSAL match path
- A9.03 pattern reply trace shows DERIVE_PATTERN ->
  LOOKUP_PRIOR_STRUCTURE -> SELECT_REPLY_INTENT path
- A9.04 REPL reply trace shows the parse/build/execute/feedback
  path (CHECK_REPL step records non-empty parse/exec values)
- A9.05 limitation reply trace documents `not_applicable` blocker
  without invalid state (CHECK_COHERENCE step records the status)
- A9.06 two runs produce equal `trace_digest_hex16`
- A9.07 trace source scan has zero forbidden-term hits

## Determinism witness

`trace_digest_hex16` is the first 16 hex chars of the SHA-256 over
the canonical serialization of all steps in the trace. Two
equivalent agent calls produce equal digests.

## Bounded constants

- `REASONING_TRACE_MAX_STEPS = 32`
- `REASONING_STEP_FIELD_MAX_LEN = 160`
- `REASONING_TRACE_DIGEST_HEX_LEN = 16`
