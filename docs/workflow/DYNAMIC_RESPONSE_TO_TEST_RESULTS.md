# DYNAMIC_RESPONSE_TO_TEST_RESULTS.md

## Purpose

Decision trees for what to do when a test or check fails during a
campaign. The intent is to make the response **mechanical** so that
the operator doesn't have to re-derive the decision every time.

## Decision tree 1: Non-target axis regression

**Symptom:** the benchmark battery reports that a NON-TARGET axis
(per the campaign's `TARGET_AXES`) has dropped a band, or has
flipped a previously-green case to red.

**Decision:**

```text
A non-target axis regressed → STOP.

  Is the regression in a case that's structurally connected to the
  target axis (e.g., target = PROTO_SPEECH_COMBINATION, regressed
  case = PROTO_SPEECH_STABLE_SINGLE)?
    YES → the mechanism's parameter change has cross-axis side
          effects. REVERT the change and re-author with a more
          surgical scope.
    NO  → the mechanism's parameter change has unexpected cross-axis
          side effects. REVERT the change. Open an investigation:
          why did this axis change? Possibilities:
          a) Shared probe state was perturbed.
          b) A test fixture was implicitly relying on the old
             behavior.
          c) A non-deterministic test that flipped on the new run.
          Investigate (a)–(c) before retrying.

  Do NOT proceed by widening TARGET_AXES to include the regressed
  axis. Widening would amount to relitigating ADR-004. If a
  campaign wants to target multiple axes, that requires an ADR
  amendment.
```

## Decision tree 2: Expected target-axis change

**Symptom:** the benchmark battery reports that a TARGET axis's case
changed (PASS → PASS-with-warning, or PASS → FAIL on a different
condition).

**Decision:**

```text
Is the change in the case the campaign's acceptance criteria
explicitly require?
  YES → expected. Confirm the change matches the acceptance criteria
        exactly (e.g., the stable_combination_count_strict became
        >= 1 as predicted). PROCEED.

  NO  → the campaign moved the axis in a direction not described by
        the acceptance criteria. STOP. Either:
        a) Revise the acceptance criteria (with operator approval).
        b) Revert the mechanism's parameter change and try a more
           surgical change.
```

## Decision tree 3: Predicate monotonicity failure

**Symptom:** import of `brain.development.predicate_table` raises
`PredicateMonotonicityError`.

**Decision:**

```text
The predicate table has a non-monotonic predicate. STOP.

  Read the error message. It identifies the (axis, band) pair where
  cert is True at band B_n but False at some lower band B_i (i < n),
  OR fals is True at band B_n but False at some lower band B_i.

  For a cert violation:
    - The cert predicate for B_n is too permissive (it should require
      MORE evidence than B_{n-1}'s cert predicate, not less).
    - Re-author B_n's cert predicate to require B_{n-1}'s precondition
      AND a higher-band-specific requirement.

  For a fals violation:
    - The fals predicate for B_i is too lenient (it should rule out
      B_i with at most the same evidence that rules out B_n, not
      less).
    - Re-author B_i's fals predicate.

  Do NOT relax the monotonicity check. Monotonicity is per ADR-005;
  relaxing it breaks the projector's correctness.
```

## Decision tree 4: Projector determinism failure

**Symptom:** the static-audit fixture's two-run check fails:
`assert profile_a.profile_digest_hex16 == profile_b.profile_digest_hex16`.

**Decision:**

```text
The projector or one of its inputs is non-deterministic. STOP.

  Likely causes (in decreasing order of likelihood):
  1. A probe report contains a field whose value depends on dict
     iteration order, time, or another nondeterministic source.
  2. The projector's _collect_evidence_row_ids or
     _summarize_assignment reads mutable module state that changes
     between runs.
  3. The probe's record-collection has a set-based ordering bug.

  Diagnostic:
    Run the projector twice and diff the assignments:

        reports = collect_probe_reports()
        a = project_developmental_progression_profile(reports)
        # Cache reports, ensure same input.
        b = project_developmental_progression_profile(reports)
        for ax, bx in zip(a.assignments, b.assignments):
            if ax != bx:
                print(f'DIFF: {ax.axis}\n  a={ax}\n  b={bx}')

    If `reports` itself differs between calls, the probe is
    non-deterministic. Fix the probe first.

  Do NOT relax the determinism check. Determinism is a REQUIRED
  catalog row per ADR-001 D7 + ADR-006.
```

## Decision tree 5: Audit hit (forbidden vocabulary)

**Symptom:** the static-audit fixture raises with a forbidden term
in a `rationale_summary`.

**Decision:**

```text
A produced string contains forbidden vocabulary. STOP.

  Identify the offending string: which assignment's rationale_summary
  is the violator?

  Re-author the rationale_summary string to remove the forbidden term:
  - "infant babbling" → "early proto-vocal emission"
  - "first words" → "stable single-token emission"
  - "toddler-stage combination" → "two-token utterance composition"
  - "year-old" → (delete; replace with substrate-condition language)
  - "training" → "consolidation" or "progression"

  Re-run the audit. Iterate until clean.

  Do NOT add the forbidden term to an exception list. The forbidden
  vocabulary list is per ADR-006 and is closed.
```

## Decision tree 6: Strictness audit found non-disposition-based gracefulness

**Symptom:** during the Phase 3.33 audit, a probe runner's PASS
acceptance is graceful in a way that isn't disposition-based (e.g.,
accepts "any token_count >= 1" or "any utterance is non-empty").

**Decision:**

```text
The audit found a graceful pattern not addressable by the
disposition-based strict counter pattern.

  ESCALATE to the operator. Phase 3.33's scope is disposition-based
  gracefulness. A non-disposition-based finding may need either:

  a) A follow-up campaign that defines a strict counter for the
     non-disposition acceptance (with its own ADR).
  b) Documentation that this gracefulness is intentional and not
     masking capability (with citation of the design reason).

  Do NOT add a strict counter for non-disposition gracefulness in
  Phase 3.33; doing so widens 3.33's scope past its ADR-001 D1
  bound.
```

## Decision tree 7: Tools failed to import

**Symptom:** `tools.propose_next_campaign` or
`tools.verify_predicate_monotonicity` fails with ImportError.

**Decision:**

```text
The required modules aren't yet present. CHECK PHASE STATUS.

  propose_next_campaign requires Phase 3.34 to have landed.
  verify_predicate_monotonicity requires Phase 3.34 to have landed.
  developmental_profile_audit requires only Phase 3.31 (pre-3.32).

  If running these tools before the required phase has landed, the
  tools should fail with a clear error message. Re-run the campaign
  in the correct phase sequence.
```

## Decision tree 8: A prerequisite axis is at B00

**Symptom:** the next-target proposer recommends
`DEFER_PENDING_PREREQUISITES` because a prerequisite axis is at B00.

**Decision:**

```text
A prerequisite axis hasn't activated at all. INVESTIGATE.

  Is the prerequisite axis tested by any probe?
    NO  → the prerequisite is structurally invisible. Either:
          a) Author a probe extension campaign to test the axis.
          b) Remove the prerequisite from the DAG (this requires an
             ADR amendment; very unlikely to be the right action).
    YES → the probe is testing the axis but the substrate isn't
          activating. The right action is a probe-extension campaign
          that adds more conditions designed to elicit the axis, or a
          mechanism-driven consolidation campaign that targets the
          prerequisite axis directly.

  Do NOT proceed with the deferred consolidation. The DAG is there
  for a reason.
```

## Decision tree 9: Benchmark digest changed unexpectedly

**Symptom:** the benchmark battery's digest changed but no campaign
step modified anything that should affect the digest.

**Decision:**

```text
A digest changed without a recorded reason. STOP.

  Diagnostic:
    git log --oneline --since='1 week ago' brain/development/
    git diff <previous-baseline-sha> HEAD -- brain/development/

  Possible causes:
    a) A docstring change in a digest-input field (shouldn't happen;
       docstrings aren't digest inputs).
    b) An import-order change that altered enum ordering.
    c) A non-deterministic probe run (see Decision tree 4).
    d) The digest's canonical-repr function changed (e.g., separator
       changed).

  Do NOT update the baseline silently. Either:
    a) Find the source of the change and revert.
    b) Document the change in an ADR amendment with the new digest.
```

## Meta-rule

When in doubt, STOP. The cost of continuing past a violation is
much higher than the cost of pausing and investigating. The
campaign sequence is designed to surface violations early, while
the affected code is still small and the cause is still tractable.
