# PHASE3_22_AGENT_COMMUNICATION_LOOP_FINDINGS.md

## Purpose

Triage the Phase 3.22 Agent Communication Loop + Behavioral
Indistinguishability Harness campaign into blockers, safety /
invariant findings, behavior successes, weak behavior, deferred
enhancements, and next research directions.

---

## 1. Blockers

```text
NONE.
```

No blocker emerged during Phase 3.22. The two minor issues
encountered during Step 5 (forbidden-term literals in the benchmark
source via the hardcoded REFUSAL carrier strings; and a stray
debug attribute in a fixture) were caught at the smoke-test step,
fixed within the same step's commit window, and did not require
Stage A / Stage B / Stage C.1 escalation. No operator intervention
was needed.

---

## 2. Safety / invariant findings

```text
- Catalog v0.29 -> v0.30 binds 11 new rows (9 REQUIRED + 2
  STRUCTURAL); all PASS in the runner.
- The runner loaded 11 new fixtures via FIXTURE_MODULES; the
  invariant runner reports 0 red across REQUIRED + STRUCTURAL +
  OBSERVED.
- The static-audit fixtures (I-AGENTLOOP-10, I-AGENTLOOP-11)
  confirm: closed enum membership; slot shape on every frozen /
  slotted record; MODULE_PRODUCED_STRINGS non-claim-clean;
  module source non-claim-clean; closed import discipline
  (no brain.llm, no brain.tick.tick, no curses / subprocess /
  socket / urllib / http / requests / tempfile / shutil /
  threading / asyncio / atexit / signal in any of the three
  new modules).
- assert_state_invariants(state) remains green after every
  STREAM_APPEND dispatch the agent loop makes.
- No L1 / L2 cache write occurred; brain/.llm_cache/ untouched.
- LLM client never constructed; OFFLINE remains default.
- brain/tick.py untouched (verified by repo diff against the
  Phase 3.21 HEAD).
- The TLICA Lean spec in lean_reference/ is preserved unchanged.
  All 11 new rows are marked as Engineering hypothesis (Phase 3
  source label); no Lean theorem is claimed.
- The canonical _FORBIDDEN_NON_CLAIM_TERMS audit returned zero
  hits on the three new module sources, every new fixture file,
  every produced reply / observation / transcript string, and
  every reply section body.
- The non-claim discipline holds: the words "agent" and
  "communication loop" are used in operational / engineering
  sense only; no claim of "consciousness", "sentience",
  "awareness", "understanding", "agency", "intent", "belief",
  "selfhood", or "subjective experience" appears anywhere in
  the runtime modules, the fixtures, or the produced replies.
```

No safety or invariant finding requires follow-up.

---

## 3. Behavior successes

```text
S1. 39/39 cases reach a documented status with no FAIL: 38 PASS +
    1 WARN-with-documented-blocker (A3.04). Full battery exit code
    is 2 by design (WARN-only).

S2. Deterministic across invocations: full battery transcript
    digest b6a93e11a105edd3 is bit-identical across two runs.
    Per-case (status, summary, primary, secondary, notes) tuples
    are bit-identical.

S3. Zero model footprint: cumulative real model calls = 0 across
    the entire campaign. Cache counters unchanged.
    brain/.llm_cache/ untouched.

S4. Non-claim cleanliness: 0 forbidden-term hits across all reply
    section bodies, all transcript lines, all module sources,
    all fixture files, all MODULE_PRODUCED_STRINGS tuples, and
    all produced summaries.

S5. Substrate composition: every axis uses only existing public
    surfaces from Phase 3.4 (REPL), Phase 3.12c (Pattern Ledger,
    Coherence Monitor), Phase 3.13 (Growth Ledger), Phase 3.18
    (text stream + processing window), Phase 3.19 (FeedbackMode),
    Phase 3.20 (CoherenceReport feedback bridge), and Phase 3.21
    (milestone harness pattern). No new core runtime code was
    needed beyond the three new closed modules.

S6. REFUSAL trigger discipline: every term in
    _FORBIDDEN_NON_CLAIM_TERMS routes its carrier to a bounded
    REFUSAL reply whose text contains zero forbidden literals.
    Operator session state is never mutated under REFUSAL.

S7. Pattern Ledger semantics confirmed and documented:
    - structural-only signature (length / line / whitespace /
      distinct-char / repeat ratio); surface-equal-structure
      texts collide by design (A2.05);
    - cross-input distinct-structure texts produce distinct
      pattern_id (A2.01 / A2.02 / A2.03);
    - bounded saturation at MAX recurrence + new entry creation
      under novel input is correct (A1.05);
    - ABAB / ABBA / ABCABC discrimination works with
      structurally distinct seeds (A1.06 / A1.07 / A1.08).

S8. REPL bridge determinism: the closed bridge over
    brain/development/repl.py runs valid / near-miss / syntax-
    invalid / repeated-valid commands deterministically, with
    the 1/(n+1) diminishing-returns schedule observable in the
    feedback valence sequence (A4.04).

S9. Phase 3.21 W3 follow-up: a deliberately-tilted CoherenceReport
    probe (A3.02, A3.03) reaches the WARN and FAIL paths through
    bounded dataclass-field assignment on the (non-frozen)
    OperatorSession dataclass; the NOT_APPLICABLE-overall path is
    documented as not publicly reachable (A3.04 — the campaign's
    sole WARN, with a notes line documenting the blocker).

S10. Session continuity within one OperatorSession: cumulative
     entry-count climbs (A6.01); seed-recurrence monotonicity
     under repeats (A6.02); REPL+stream interleave reply integrity
     (A6.03).

S11. Lean-spec compliance: all 11 new rows are Engineering
     hypotheses; no Lean theorem is claimed; no existing REQUIRED
     row is contradicted.

S12. Catalog patch lands cleanly:
     - INVARIANT_CATALOG.md row family in canonical order,
     - tools/catalog.py EXPECTED_COUNTS updated,
     - brain/_catalog_ids.py regenerated,
     - brain/invariants.py FIXTURE_MODULES extended,
     - README.md banner updated.
     All five canonical gates green at v0.30.
```

---

## 4. Weak behavior

```text
W1. A3.04 (the campaign's sole WARN). Overall-status
    NOT_APPLICABLE is not publicly reachable. The blocker is
    architectural: compute_overall_status returns NOT_APPLICABLE
    only when every check is NA, but the kernel.* checks always
    emit PASS for a valid BrainState. To force overall-NA one
    would need to invalidate BrainState, which would also fail
    multiple OTHER checks. The campaign documents this as the
    accepted limit of the W3 follow-up; the WARN is not a runtime
    bug.

W2. The structural-only Pattern Ledger signature is correct by
    design but the design surface forces "renamed structure"
    cases to use structurally distinct surface tokens. Phase 3.22
    documents this in A2.05 and the BENCHMARK_SPEC corrigendum;
    no campaign claims surface-equal-structure transfer. A
    deeper "structural transfer" beyond the current signature
    semantics would require a Pattern Ledger semantic change
    (out of scope; LOCK B).

W3. The agent loop's REFUSAL trigger is conservative: any term
    in the audit tuple (including "preserve", "damage", "truth")
    triggers REFUSAL even when the operator's intent (engineering
    sense) is not a cognitive query. This is a deliberate safety
    conservatism: REFUSAL is the safe default. A future campaign
    could narrow the trigger set if the operator-surface
    experience proves too restrictive in practice, but the
    safety floor is correct.

W4. The agent loop does NOT route operator text through
    brain.tick.tick; it dispatches only STREAM_APPEND. This is
    architectural per Phase 3.18-3.21 substrate composition (the
    tick path is the kernel boundary and was not in scope for
    Phase 3.22). The reply layer is therefore bounded to the
    stream / pattern / coherence / growth / REPL substrates; no
    Mode B reflective agency, no expression layer, no readability
    score, no language understanding participates.

W5. REPL execution does NOT actually run code: execute_command
    returns a bounded deterministic ProtoBasicExecutionResult
    record; there is no host execution, no subprocess, no file
    I/O. The "valid-effective" status is a structural label only.
    This is the existing Phase 3.4 semantics; the agent loop
    reuses it without claim of real-world effect.
```

None of W1..W5 are runtime bugs. They are framing notes about
the operator-facing reply layer's bounded scope.

---

## 5. Deferred enhancements

```text
D1. Tracer wiring through OperatorSession.dispatch (deferred
    since Phase 3.7). Would enable per-step observability without
    introducing new runtime state. Candidate for Phase 3.23.

D2. A second-pass refusal trigger that narrows the carrier set
    to cognitive-property terms only (subset of
    _FORBIDDEN_NON_CLAIM_TERMS), reducing false REFUSAL on
    operator inputs containing terms like "preserve" or "damage"
    where the surrounding context is non-cognitive. Out of scope
    for v1; the conservative trigger is the safer default.

D3. A model-backed reflection layer over agent-loop outputs.
    Strictly bounded by the existing 20-call budget and explicit
    opt-in policy. Would require a new reviewed campaign with
    its own LOCK set.

D4. SelfModel implementation. Permanently OUT OF SCOPE.

D5. Cross-session persistence of AgentLoopState. Out of scope; no
    schema change is permitted by the Phase 3.22 mission.

D6. A new ACTIVE_VIEWS member exposing the agent loop in the
    operator TUI. Out of scope per the Phase 3.22 mission (no
    UI verb / view addition).

D7. Worldlet feedback bridge (Phase 3.19 / 3.20 carryover).
    Bounded extension following the FeedbackMode precedent;
    candidate for Phase 3.24.

D8. A model-backed answer-generation layer for the operator's
    natural-text input. Out of scope; the operator-facing reply
    is bounded structural data, NOT a generated answer.

D9. Aggregate scalar "mild-agent score" / "capability score" /
    "intelligence score". Permanently out of scope per LOCK D.

D10. Per-cohmon-chunk distinct-signature probe matrix for M06 +
     M07 (Phase 3.21 W2 carryover). Out of scope; not the focus
     of Phase 3.22.

D11. I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED. Out of
     scope.
```

---

## 6. Next research directions

```text
R1. Phase 3.23 candidate: tracer wiring through
    OperatorSession.dispatch. Bounded; would enable per-loop
    observability without new runtime state. Closely paired
    with the agent loop's reply layer for per-step inspection.

R2. Phase 3.24 candidate: worldlet feedback bridge (a fifth
    FeedbackMode following the OFF / PATTERN_LEDGER /
    COHERENCE / PATTERN_AND_COHERENCE precedent). Bounded
    extension; the agent loop's reply layer would absorb
    the new feedback chunks via its existing observation path.

R3. Phase 3.X candidate: a narrower REFUSAL trigger that
    distinguishes "operator-supplied query about cognition"
    from "operator-supplied non-cognitive use of a forbidden
    term". Likely requires a second closed list of
    cognitive-query-specific terms (subset of the existing
    tuple) plus an audit-clean derivation path.

R4. Phase 3.X candidate: extend the agent loop to emit a small
    bounded set of pre-built operator-facing UI verbs
    (/agent-loop, /agent-reply) once Phase 3.23 tracer
    observability is in place. Strictly opt-in.

R5. Long-term: the bounded "mild-agent-like under bounded tests"
    rubric could be extended into a periodic-style behavioral
    benchmark battery covering further structural-only
    behavioral axes (e.g., bounded long-context recall, bounded
    novelty discrimination at the substrate cap, bounded
    saturation-recovery probes). The non-claim discipline
    remains the binding constraint.
```

---

## 7. Cross-campaign carryovers

```text
- Tracer wiring through OperatorSession.dispatch remains
  DEFERRED.
- Worldlet feedback bridge remains DEFERRED.
- Real-model reflection over agent-loop outputs remains DEFERRED.
- SelfModel remains OUT OF SCOPE.
- /pattern-ledger / /coherence-summary / /growth-ledger /
  /agent-loop UI verbs remain DEFERRED.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- Phase 3.21 W2 (per-cohmon-chunk distinct signature) remains a
  DEFERRED follow-up.
- Phase 3.21 W3 (deliberately-tilted CoherenceReport probe) is
  RESOLVED by Phase 3.22 A3 axis: WARN and FAIL paths
  demonstrated; NOT_APPLICABLE-overall documented as not
  publicly reachable.
```

None of these carryovers were aggravated by Phase 3.22.

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used
Stage B limited-write collaboration: not used
Stage C.1 flow orchestration       : not used
Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```

---

## 9. Next artifact

`docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_AUDIT.md`
— the Step 10 final audit, which records the verdict (PASS / PASS
WITH DEFERRED FOLLOW-UPS / PARTIAL / BLOCKED / FAIL), canonical
preflight result, and the next-campaign recommendation.
