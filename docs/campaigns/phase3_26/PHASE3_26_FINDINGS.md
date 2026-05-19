# Phase 3.26 — Findings

What we learned from running the active-hypothesis live-test runner
end-to-end against the existing substrate.

## F1. The existing substrate is sufficient for the bounded operational claim

The bounded operational claim — *given a bounded ambiguous input,
the runtime can enumerate a bounded candidate set, derive one safe
internal probe per candidate, execute the probe through the existing
agent interaction path, prune candidates whose probe outcome does
not match the candidate's prediction, decline to overclaim a winner
when zero survive, and on a second visit reuse the cached record* —
is verified by the v1 ten-trial battery with zero false positives,
zero false negatives, and a deterministic 16-hex report digest.

No new closed-enum member, no new persistence schema, no new
operator command, no new dispatcher kind, no new aggregate score
field was required. The Phase 3.22b abstract-pattern signature
layer, the Phase 3.22b learning ledger, the Phase 3.22b reasoning
trace, the Phase 3.23 dispatch tracer, and the agent loop's
ordinary `run_agent_interaction_step` route provide every primitive
the active-hypothesis runner needs.

## F2. The non-leakage invariants are constructively enforceable

`ActiveProbeStep.__post_init__` raises if the probe text contains
the candidate's `predicted_digest_hex16`, the candidate's
`predicted_shape`, or any forbidden direct-instruction term.
`select_safe_probe` raises before that point, so the leakage
condition is unreachable at runtime; the constructor's audit is a
defense-in-depth that doubled as a fixture target (I-AHYP-04).

This is a clean instance of the *no-cheating-the-test* discipline
codified in Phase 3.25 for the osmotic-learning runner: the
expected outcome lives on the trial record, the trial record is
only consumed by the benchmark layer, and the runtime path is
mechanically prevented from observing it.

## F3. Refusal-to-overclaim is the discriminating behavior

The most operationally interesting observed behavior is the
`NO_HYPOTHESIS_SURVIVES` condition (T07, T08, T10). When the v1
candidate set is structurally incompatible with the input (e.g.,
shape `A A` falls outside the `(repeated, 2)` bucket's predicted
shapes), every candidate is `FALSIFIED` and the runner returns:

```text
survivors_count = 0
winner_id       = ""
no_hypothesis_survives = True
```

The runner does NOT invent a winner. This is the substrate-level
analogue of *refusal to overclaim under insufficient evidence*: it
is a bounded mechanical property of the comparison + selection
logic, not a cognitive judgment. The fact that this property is
testable as a closed-criterion benchmark case (A13.07, A13.08) is
the load-bearing piece — it means the discipline is verifiable
rather than asserted.

## F4. The multi-survivor case preserves multiplicity

T05 and T06 yield three surviving candidates each. The runner does
NOT collapse multiplicity to a single winner via tie-breaking or
score ranking. `winner_id` remains `""` and all three survivors
retain `SURVIVING` status. This is intentional: the v1 plan does
not introduce a tie-breaking rule because doing so would be a
designer-imposed preference rather than a substrate-level
operational property. A future phase could introduce a bounded
tie-breaker (e.g., shortest-probe-text, alphabetical-candidate-id)
explicitly tagged as a designer choice; v1 does not.

## F5. The session-local cache is necessary and sufficient

The reuse cache is keyed on the input's canonical
`derive_abstract_pattern_signature.digest_hex16`. For
`REUSE_CACHED_HYPOTHESIS` trials whose input's canonical digest is
already in the cache, the runner returns the cached prior result
with `second_visit_probe_count == 0`. The cache is a caller-managed
`dict[str, ActiveHypothesisResult]` — not the L1/L2 LLM cache, not
a persistence schema column, not a module-level mutable global.
This keeps the substrate (a) bounded, (b) per-session, (c) trivially
inspectable from the benchmark layer.

A future cross-session-persistent variant is a defensible
extension but would require a new persistence schema field, an
autosave trigger, and corresponding non-claim guardrails — all out
of scope for Phase 3.26.

## F6. Determinism is preserved end-to-end

Two invocations of `run_active_hypothesis_live_test()` produce
bit-identical `ActiveHypothesisLiveTestReport.trials` tuples and an
equal `digest_hex16 == "86b67d97daeb251d"`. Two invocations of
`run_full_battery()` produce equal `transcript_digest_hex16 ==
"0169f117497dba08"`. The Phase 3.22+ determinism discipline is
preserved without modification.

## F7. The non-claim audit catches docstring drift

The Phase 3.25 source-scan precedent (every `_FORBIDDEN_NON_CLAIM_TERMS`
substring in the module source is treated as a hit) successfully
caught a first-draft active_hypothesis_probe.py docstring that
enumerated the forbidden terms in a denial sentence. The fix was to
rewrite the disclaimer without enumerating the terms. This is the
same fix Phase 3.25 made for the same reason; it is a discipline
that scales: the audit is mechanical, the message is preserved by
careful wording, and the substrate's denial of cognitive claims is
made structurally rather than rhetorically.

## F8. The benchmark axis extension is mechanical

Adding `BenchmarkAxis.ACTIVE_HYPOTHESIS`, bumping `BATTERY_VERSION`
to `"phase3.26.v1"`, extending `run_full_battery` by one axis,
adding 14 `A13.01..A13.14` cases, and patching the five dependent
fixtures (`agent_benchmark_runner_green`,
`agent_benchmark_static_audit`, `dispatch_tracer_benchmark_axis`,
`osmotic_probe_runner_green`, `worldlet_feedback_benchmark_axis`)
was the entire mechanical cost. The full battery now covers
105 cases — 91 from Phases 3.22..3.25 plus 14 from Phase 3.26 —
with 104 PASS + 1 documented WARN (A3.04 carry-over) + 0 FAIL.

## Open follow-ups (not in scope for Phase 3.26)

- **Adaptive candidate generation** based on prior trial outcomes
  would require a bounded learning loop; defer to a future phase.
- **Recursive probing** (probe a probe's outcome) would require a
  recursion bound and a separate fixture family; defer.
- **Cross-session reuse cache** would require a persistence schema
  field, an autosave trigger, and corresponding non-claim
  guardrails; defer.
- **Wider candidate-set coverage** beyond the six v1
  `(classification, token_count)` buckets is a natural extension;
  defer pending a use case.
- **Model-backed probes** (an opt-in mode where the probe text goes
  through `brain.llm` instead of the deterministic agent loop)
  would require a separate OBSERVED row and explicit operator
  approval; defer.
- **A3.04 NOT_APPLICABLE-overall blocker** (carried forward since
  Phase 3.21 W3) remains a documented WARN; defer per the Phase
  3.21 corrigendum decision.
