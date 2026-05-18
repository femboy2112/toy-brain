# PHASE3_22B_FINDINGS.md

## Findings triage

### F1 — Renamed-structure transfer works at the abstract-pattern layer

The new `derive_abstract_pattern_signature` function emits a bounded
`digest_hex16` that depends only on the structural form of the
tokens. Renamed inputs ("red blue red blue", "cat dog cat dog") map
to the same digest. The agent loop emits `TRANSFER_RECOGNIZED`
evidence when an input with a previously-acquired digest maps to a
different concrete `pattern_id`.

Severity: **resolution** of Phase 3.22 W2.

### F2 — Diminishing-returns evidence is captured per call

Repeated valid-effective REPL commands emit
`DIMINISHING_RETURNS_UPDATED` records with deterministic `(prior,
current)` pairs (1/1 -> 1/2, 1/2 -> 1/3, ...). The reasoning trace's
`check_repl` step also records the DRF on each interaction.

Severity: **resolution** of Phase 3.22 W5.

### F3 — Refusal classifier is narrower for the trace, defense-in-depth retained

The `_classify_cognitive_claim(text)` classifier identifies direct
cognitive-claim phrasing for the reasoning trace
(`classifier_match=True`). The wider `_FORBIDDEN_NON_CLAIM_TERMS`
substring scan remains as the floor that fires REFUSAL. Both are
deterministic. Harmless technical phrases that do not contain
audit-tuple terms now pass through cleanly.

Severity: **refinement** of Phase 3.22 W3. The wider scan remains
because it is the safety floor; the I-AGENTLOOP-04 fixture still
requires every audit-tuple term to trigger REFUSAL.

### F4 — Dispatch path is documented in the reasoning trace

The `OBSERVE_INPUT` step records the dispatch path label
(`repl-bridge`, `session-dispatch-stream-append`, `refusal-no-dispatch`,
`fail-no-dispatch`, `warn-no-dispatch`). The trace makes the public
surface used by each interaction externally inspectable.

Severity: **documentation** of Phase 3.22 W4. The deterministic
OFFLINE path still does not invoke `brain.tick.tick`.

### F5 — overall_status `not_applicable` remains unreachable on valid state

`compute_overall_status` returns `NOT_APPLICABLE` only when every
check is `NA`. The `kernel.*` family always returns `PASS` on a
valid `BrainState`. Public construction enforces
`assert_state_invariants(state)`, which gates `kernel.*` to PASS.
Therefore `not_applicable` overall is not reachable through public
construction. Reaching it would require fabricating invalid state,
which Phase 3.22b refuses to do.

Severity: **carry-over** of Phase 3.22 W1. The A3.04 case is a
documented WARN and the I-AGENTLOOP-09 acceptance rubric explicitly
permits this single WARN.

### F6 — Learning evidence trace is bounded and FIFO

`LearningEvidenceTrace` enforces `LEARNING_TRACE_MAX_RECORDS = 256`
via FIFO drop on append. The I-AGENTLEARN-03 fixture exercises the
overflow path: appending the 257th record drops the oldest and
retains the 256 most recent. No unbounded growth is possible.

Severity: **invariant** witness.

### F7 — Reasoning trace is bounded and printable

`ReasoningTrace` enforces `REASONING_TRACE_MAX_STEPS = 32` with
per-field bound `REASONING_STEP_FIELD_MAX_LEN = 160`. Step numbers
are sequenced 1..N. The trace's `format_reasoning_trace_table`
projection produces a multi-line printable string suitable for
operator inspection. Every produced text passes the canonical
forbidden-term audit.

Severity: **invariant** witness.

### F8 — Determinism digests are stable across runs

The learning proof digest (`df75162f93605181` for the sample 6-step
sequence) and the reasoning trace digest (e.g. `5d8feb2a3096c3ad` for
the renamed-transfer reply) are bit-identical across two fresh
sessions advanced through the same input. The benchmark cases A8.07
and A9.06 assert this property; the gate runner re-asserts it via
the full battery determinism check.

Severity: **determinism** witness.

### F9 — Zero real model calls / cache writes / forbidden hits

The deterministic battery consumes 0 real model calls, 0 cache
writes, and produces 0 forbidden-term hits. The
`I-AGENTLEARN-10` fixture asserts this for the A8 + A9 partial
runner; `I-AGENTLOOP-09` asserts the same for the full battery.

Severity: **budget** witness.

## Deferred follow-ups (not addressed in 3.22b)

- D1: Reach the `not_applicable` overall_status without violating
  kernel invariants. Likely requires a new optional public lever or
  a refactor of `compute_overall_status`. Out of scope for 3.22b.
- D2: Cross-session persistence of `LearningEvidenceTrace`. Would
  require a schema change; explicitly forbidden in 3.22b.
- D3: A future-facing model-backed agent loop that opts in to
  `brain.tick.tick`. Phase 3.22b documents the extension point in the
  `OBSERVE_INPUT` dispatch-path label set but does not implement it.
- D4: Broader natural-language coverage in the cognitive-claim
  classifier. The closed bounded phrase set is sufficient for the
  benchmark but not exhaustive over paraphrase. Out of scope for
  3.22b.
- D5: Tracer wiring through `OperatorSession.dispatch` (deferred
  since Phase 3.7). Phase 3.22b notes this as a future Phase 3.23
  candidate.

## Non-claim hygiene

- 0 forbidden-term hits in any transcript line, any reply section,
  any evidence record summary, any trace field.
- 3 new module sources are audited by I-AGENTLEARN-11; all 3 pass
  the canonical `_FORBIDDEN_NON_CLAIM_TERMS` audit.
- The cognitive-claim probe used inside the benchmark source code
  is composed at test time from the imported audit tuple, so the
  benchmark source file itself contains no literal forbidden term.
