# PHASE3_33_STRICTNESS_AUDIT_PLAN.md

## Purpose

Audit protocol for Phase 3.33 Step 4: identify which probe runners
use graceful-pass acceptance that masks substrate capability gaps,
so that Steps 5a–5d can author strict counters for the affected probes.

## Audit protocol

For each probe runner module:

1. Locate the runner entry point
   (`run_<probe>_live_test`).
2. Identify every `ProbeStatus.PASS` / `Status.PASS` assignment in
   the runner.
3. For each PASS assignment, identify the **disposition set** it
   accepts.
4. If the disposition set has more than one element, **the runner has
   graceful-pass acceptance**. Otherwise, strict-only.
5. For every graceful-pass acceptance, document:
   - The condition / case constant (e.g.,
     `ProtoSpeechCondition.TWO_TOKEN_COMBINATION`).
   - The graceful set (the set of accepted dispositions).
   - The canonical disposition (the strict-only one).
   - The proposed strict counter name (snake_case).
6. Add an entry to the findings table below.

## Audit method: code search

```bash
# Find every PASS assignment in the probe runners.
grep -rn "Status\.PASS\|status = .*PASS\|disposition not in" \
  brain/development/proto_speech_acquisition.py \
  brain/development/curriculum_consolidation_probe.py \
  brain/development/active_hypothesis_probe.py \
  brain/development/osmotic_learning_probe.py \
  brain/development/worldlet_feedback_bridge.py 2>/dev/null \
  | head -80

# Find every "acceptable if" / "graceful" / "fallback" comment.
grep -rn "graceful\|acceptable if\|fallback\|disposition not in (\|disposition in (" \
  brain/development/proto_speech_acquisition.py \
  brain/development/curriculum_consolidation_probe.py \
  brain/development/active_hypothesis_probe.py \
  brain/development/osmotic_learning_probe.py \
  brain/development/worldlet_feedback_bridge.py 2>/dev/null

# Look for explicit graceful-acceptance patterns:
#   `if disposition not in (A, B, C):` (graceful, accepts {A,B,C})
#   `if disposition is not X:` (strict, accepts {X} only)
grep -rEn "disposition (is|in) (not )?\(" brain/development/*.py
```

## Findings template (FILL IN at Phase 3.33 Step 4)

For each affected condition, fill in one row of the table below.

```text
Probe module                       Condition                                  Graceful set                                              Canonical disposition           Proposed strict counter name
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
proto_speech_acquisition           TWO_TOKEN_COMBINATION                      {STABLE_COMBINATION, REINFORCED, CANDIDATE}               STABLE_COMBINATION              stable_combination_count_strict
proto_speech_acquisition           HOLOPHRASE_TRANSFER                        <FILL IN>                                                 TRANSFERRED                     transfer_success_count_strict
proto_speech_acquisition           <other conditions>                         <FILL IN>                                                 <FILL IN>                       <FILL IN>
curriculum_consolidation_probe     <FILL IN>                                  <FILL IN>                                                 <FILL IN>                       <FILL IN>
active_hypothesis_probe            <FILL IN>                                  <FILL IN>                                                 <FILL IN>                       <FILL IN>
osmotic_learning_probe             <FILL IN>                                  <FILL IN>                                                 <FILL IN>                       <FILL IN>
worldlet_feedback_bridge           <FILL IN>                                  <FILL IN>                                                 <FILL IN>                       <FILL IN>
```

## Per-probe finding entry format

For each affected probe, write a structured finding under the probe's
heading below. Use this format:

```markdown
### Finding F-N: <probe>.<condition>

**Location:** `brain/development/<probe>.py:<line>`

**Graceful pattern:**

```python
# Quote the relevant 3-10 lines.
if combo_rec.disposition not in (
    ProtoUtteranceDisposition.CANDIDATE,
    ProtoUtteranceDisposition.REINFORCED,
    ProtoUtteranceDisposition.STABLE_COMBINATION,
):
    status = ProtoSpeechStatus.FAIL
```

**Acceptance interpretation:** PASS if disposition is one of CANDIDATE,
REINFORCED, or STABLE_COMBINATION.

**Canonical disposition:** STABLE_COMBINATION. The CANDIDATE and
REINFORCED dispositions are "in-progress" forms; the substrate has
not yet stabilized a 2-token combination by the time the runner
finishes.

**Proposed strict counter:** `stable_combination_count_strict`.

**Strict computation rule:**

```python
strict_count = sum(
    1 for rec in final_table.records()
    if rec.disposition is ProtoUtteranceDisposition.STABLE_COMBINATION
    and rec.token_count == 2
)
```

**Expected effect on Phase 3.31 baseline:**

- `stable_combination_count` (graceful) is currently 0 (per the
  Phase 3.31 report).
- `stable_combination_count_strict` will also be 0.
- No WARN will be emitted (graceful is 0, so the masking condition
  isn't triggered).
- Phase 3.34's projector will read both counters as 0 and assign
  PROTO_SPEECH_COMBINATION to B01_EMERGENT or B02_REPEATABLE based on
  earlier-band predicates (whether 2-token utterances appeared at
  all, etc.).

**Catalog row:** `I-PSPEECH-20` (STRUCTURAL).
```

## Probe sections

### proto_speech_acquisition

Pre-known findings (from planning):

- **F-1**: TWO_TOKEN_COMBINATION accepts {CANDIDATE, REINFORCED,
  STABLE_COMBINATION}; strict counter `stable_combination_count_strict`.
- **F-2**: HOLOPHRASE_TRANSFER accepts {... fill in from audit ...};
  strict counter `transfer_success_count_strict`.

Run the audit to confirm and identify any additional findings.

### curriculum_consolidation_probe

Hypothesis: SURVIVED conditions may accept marginal survivors.
Confirm via audit.

### active_hypothesis_probe

Hypothesis: WINNER_SELECTED conditions may accept "no hypothesis
survived" as a graceful pass. Confirm via audit.

### osmotic_learning_probe

Hypothesis: TRANSFER conditions may accept transfer-attempt without
successful transfer. Confirm via audit.

### worldlet_feedback_bridge

Hypothesis: no canonical live-test runner exists (the module is a
bridge, not a probe with PASS/FAIL semantics). If so, no strict
counter needed. Confirm via audit.

## Decision rules during audit

If audit finds a graceful set with exactly one element: **NOT
affected**. The runner is already strict on this condition. No
strict counter needed.

If audit finds a graceful set with multiple elements: **AFFECTED**.
Add a strict counter. Document the canonical disposition.

If audit finds a probe where the runner emits PASS unconditionally
(no disposition check): **special case**. Likely a smoke-test
condition. Document as "unconditional PASS, no strictness applies"
and skip the strict counter.

If audit finds a probe where the runner is graceful in a way that
isn't disposition-based (e.g., accepts "any token_count >= 1"):
**document and discuss with operator**. Possibly out of scope for
3.33 — the strict counter pattern is disposition-based.

## Automation

`tools/developmental_profile_audit.py --audit-only` does most of
this mechanically:

```bash
python3 -m tools.developmental_profile_audit \
    --audit-only \
    --probes proto_speech_acquisition,curriculum_consolidation_probe,active_hypothesis_probe,osmotic_learning_probe \
    --format markdown \
    > /tmp/audit-raw.md
```

Output is a draft fill-in for this document. Review every finding
manually before committing; the audit script identifies graceful-pass
candidates but a human (or planner agent) decides the canonical
disposition for each one.

## Acceptance for Step 4

Step 4 of the campaign is complete when:

- Every probe module has been audited.
- Every graceful-pass finding has a per-probe finding entry above.
- The findings table is fully populated (no `<FILL IN>` placeholders).
- The set of strict counters to add in Steps 5a–5d is final.

## Cross-references

- `PHASE3_33_PROTO_SPEECH_STRICT_CORRIGENDUM_ROADMAP.md` Step 4.
- `PHASE3_33_DESIGN.md` for the strict-counter design.
- `ADR-003-strict-counter-pattern.md` for the project-wide rule.
- `.claude/agents/brain-probe-strictness-auditor.md` — the agent
  that automates this audit.
