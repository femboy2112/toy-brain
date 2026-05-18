# PHASE3_22B_BEHAVIOR_REPORT.md

## Verdict

```text
Phase 3.22b verdict: PASS WITH DEFERRED FOLLOW-UPS
Catalog version: v0.31 (Phase 3.22 v0.30 + I-AGENTLEARN-01..11)
Counts:
  REQUIRED        313
  STRUCTURAL       95
  NOT-EXERCISED    14
  DEFERRED         15
  OBSERVED         16
Total tabular entries: 453
Benchmark cases:        53 (39 Phase 3.22 + 14 Phase 3.22b)
Benchmark PASS:         52
Benchmark WARN:         1 (A3.04, Phase 3.21 W3 follow-up blocker)
Benchmark FAIL:         0
Real model calls:       0
Cache writes:           0
Determinism failures:   0
Invariant failures:     0
Forbidden-term hits:    0
Transcript digest:      aa4fae94b8c9a8e4
Learning proof digest:  df75162f93605181  (sample sequence)
Reasoning trace digest: 5d8feb2a3096c3ad  (renamed transfer reply)
```

## What landed

Phase 3.22b extends Phase 3.22 with three new bounded modules and one
new row family `I-AGENTLEARN-01..11`:

- `brain/development/abstract_pattern.py` —
  `derive_abstract_pattern_signature(text)` and the closed
  `AbstractPatternSignature` record. Renamed inputs sharing
  structural form (e.g. "red blue red blue" and "cat dog cat dog")
  map to the same `digest_hex16`.
- `brain/development/learning_evidence.py` — closed
  `LearningEvidenceKind` enum (8 members), bounded
  `LearningEvidenceRecord` / `LearningEvidenceTrace` /
  `LearningProofReport` records, eight per-kind builder helpers, and
  a `build_learning_proof_report` aggregator.
- `brain/development/reasoning_trace.py` — closed
  `ReasoningStepKind` enum (10 members), bounded `ReasoningTraceStep`
  / `ReasoningTrace` / `ReasoningTraceReport` records, a builder
  helper, and a `format_reasoning_trace_table` projection.
- Agent loop integration: `AgentLoopState` gains `learning_trace:
  LearningEvidenceTrace`; `AgentLoopResult` gains
  `learning_evidence_trace` and `reasoning_trace` optional fields
  populated on every interaction.
- Benchmark axes: A8 `learning_evidence` (7 cases A8.01–A8.07) +
  A9 `reasoning_trace` (7 cases A9.01–A9.07). All 14 new cases PASS.

## Phase 3.22 weak-behavior follow-ups

### W1 — overall-status `not_applicable` unreachable via public surface

**Status:** documented architectural blocker, still WARN.

Why this is unreachable on a valid `BrainState`: `compute_overall_status`
returns `NOT_APPLICABLE` only when every check is `NA`, but the
`kernel.*` check family always emits `PASS` for any valid
`BrainState` reachable via the public construction surface. Public
construction always passes `assert_state_invariants(state)`, so the
kernel checks always pass, so `compute_overall_status` cannot return
`NOT_APPLICABLE`. Reaching `NOT_APPLICABLE` overall would require
violating the kernel invariants, which is forbidden — and would
constitute fabricating evidence rather than observing it.

Phase 3.22b does NOT hack private invalid state to force the status
variation. The A3.04 case remains a documented WARN with the
above proof-style explanation in its `notes` field. The reasoning
trace's `check_coherence` step records the actual achievable
overall_status value at run time, preserving the audit trail.

### W2 — Pattern Ledger renamed-structure transfer

**Status:** RESOLVED.

`brain/development/abstract_pattern.py` provides
`derive_abstract_pattern_signature(text) -> AbstractPatternSignature`
mapping any input to a bounded `(shape, classification, digest_hex16)`
triple that depends only on the structural form of the tokens
(token-equality class, recurrence class). Renamed inputs that share
the structural form share the digest:

```text
derive_abstract_pattern_signature("red blue red blue").digest_hex16 ==
derive_abstract_pattern_signature("cat dog cat dog").digest_hex16
== "d37efc29b0c680ba"
```

This layer composes with the Pattern Ledger; it does NOT replace
ledger semantics. The agent loop emits a `TRANSFER_RECOGNIZED`
evidence record whenever an input with a previously-acquired digest
maps to a different concrete `pattern_id`.

### W3 — REFUSAL trigger overbreadth

**Status:** REFINED.

A new narrower cognitive-claim classifier
`_classify_cognitive_claim(text) -> tuple[bool, int]` operates over a
bounded tuple of phrase fragments synthesized at module load from the
imported `_FORBIDDEN_NON_CLAIM_TERMS` tuple. The reasoning trace's
`classify_refusal` step records the classifier match independently
from the wider audit-tuple match.

The wider audit-tuple scan remains the floor that fires REFUSAL: any
input containing any audit-tuple term routes to REFUSAL. This is
deliberate defense-in-depth, and is asserted by I-AGENTLOOP-04. The
narrower classifier provides finer signal for the reasoning trace
and is asserted by benchmark case A9.02.

Regression tests:

- Direct cognitive-claim probe `"are you " + _FORBIDDEN_NON_CLAIM_TERMS[0]`
  triggers REFUSAL (A9.01 covers this through the trace shape; A9.02
  asserts the classifier match path).
- Harmless structural phrases (`"red blue red blue"`, `"EMIT ALPHA"`,
  `"random text here"`) do not match the narrower classifier. They
  still PASS through the loop normally.

### W4 — Agent loop and `brain.tick.tick`

**Status:** documented; no architectural change.

The deterministic OFFLINE agent-loop tests do NOT route through
`brain.tick.tick`; doing so would violate the campaign's "0 real
model calls" budget. The reasoning trace's `OBSERVE_INPUT` step
records the actual dispatch path used on each interaction:

- `repl-bridge` — the loop routed through `agent_repl_bridge.run_repl_line`,
- `session-dispatch-stream-append` — the loop dispatched
  `OperatorCommand.STREAM_APPEND` through `OperatorSession.dispatch`,
- `refusal-no-dispatch` — the wider audit-tuple scan matched; no
  session mutation occurred,
- `fail-no-dispatch` — the input was oversize,
- `warn-no-dispatch` — the input was empty.

A future-facing model-backed opt-in could thread `brain.tick.tick`
through a separate explicit code path; Phase 3.22b documents the
extension point and stops there.

### W5 — REPL valid-effective is structural only

**Status:** RESOLVED + extended.

"Valid-effective" remains a local structural consequence; no host
execution is performed. Phase 3.22b additionally records every DRF
change as a `DIMINISHING_RETURNS_UPDATED` evidence record. Repeated
valid-effective commands lower the DRF deterministically:

```text
EMIT BETA #1: DRF = 1/1
EMIT BETA #2: DRF = 1/2  (DIMINISHING_RETURNS_UPDATED record emitted)
EMIT BETA #3: DRF = 1/3  (record emitted)
EMIT BETA #4: DRF = 1/4  (record emitted)
EMIT BETA #5: DRF = 1/5  (record emitted)
```

The benchmark case A8.06 and the I-AGENTLEARN-07 fixture both assert
the exact `(prior, current)` DRF pairs in order.

## Per-axis summary

| axis | cases | PASS | WARN | FAIL | notes |
|---|---|---|---|---|---|
| A1 pattern_recognition | 9 | 9 | 0 | 0 | unchanged from Phase 3.22 |
| A2 cross_input_structural | 5 | 5 | 0 | 0 | unchanged |
| A3 coherence_variation | 4 | 3 | 1 | 0 | A3.04 documented WARN (W1 blocker) |
| A4 repl_coherence | 5 | 5 | 0 | 0 | unchanged |
| A5 communication | 9 | 9 | 0 | 0 | unchanged |
| A6 session_continuity | 3 | 3 | 0 | 0 | unchanged |
| A7 blind_transcript | 4 | 4 | 0 | 0 | unchanged |
| **A8 learning_evidence** | **7** | **7** | 0 | 0 | **new** |
| **A9 reasoning_trace** | **7** | **7** | 0 | 0 | **new** |
| total | 53 | 52 | 1 | 0 | |

## Examples

### Example learning proof row (verbatim)

```text
abstract_pattern_acquired      abstract pattern d37efc29b0c680ba acquired shape='A B A B' class=recurring-form
```

### Example reasoning trace row (verbatim)

```text
04 lookup_prior_structure   in='digest=d37efc29b0c680ba' drv="acquired=True prior_pid='pledger:1669ab0ef2ed6bba'" nxt='compare_structure'
```

## Remaining limitations

- W1 not_applicable overall-status remains an architectural blocker.
  Captured as a documented A3.04 WARN with proof-style explanation.
- Cross-session persistence of learning evidence remains OUT OF
  SCOPE; the trace is session-local only.
- The narrower cognitive-claim classifier does not catch every
  paraphrase. It catches the closed set of starter-phrase + audit-
  tuple-term combinations, which is sufficient for benchmark
  obligations but not exhaustive over natural language.
- Real model-backed paths are not exercised; the deterministic
  OFFLINE battery consumes 0 real model calls.
