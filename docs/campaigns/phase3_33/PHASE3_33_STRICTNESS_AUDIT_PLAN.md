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

## Findings table (POPULATED at Phase 3.33 Step 4)

```text
Probe module                       Condition                                  Graceful set                                              Canonical disposition           Proposed strict counter name
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
proto_speech_acquisition           TWO_TOKEN_COMBINATION                      {CANDIDATE, REINFORCED, STABLE_COMBINATION}               STABLE_COMBINATION              stable_combination_count_strict
proto_speech_acquisition           HOLOPHRASE_TRANSFER                        (none — runner is strict; see F-2)                        n/a                             n/a (hypothesis falsified)
curriculum_consolidation_probe     (none affected — _evaluate_verdict is exact-equality on all four metrics)
active_hypothesis_probe            (none affected — _evaluate_verdict is exact-equality on all five metrics)
osmotic_learning_probe             (none affected — verdict combines three strict checks via AND)
worldlet_feedback_bridge           (no probe runner exists; bridge logic lives in processing_window.py, no PASS/FAIL semantics to audit)
```

Net result: **1 graceful-pass finding** across the five candidate probes (proto-speech TWO_TOKEN_COMBINATION only). Three of four candidate strict-counter catalog rows are dropped at Step 8 per ADR-001 D1: their probes are already strict-only. See "Catalog patch impact" section below.

The mechanical audit tool (`tools/developmental_profile_audit --audit-only`) found this same singleton candidate. Manual review of every `Status.PASS` / `TrialVerdict.PASS` / `OsmoticProbeStatus.PASS` assignment in the four runners confirmed the audit tool's coverage was complete for disposition-based gracefulness.

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

#### Finding F-1: proto_speech_acquisition.TWO_TOKEN_COMBINATION (AFFECTED — CONFIRMED)

**Location:** `brain/development/proto_speech_acquisition.py:3258`

**Graceful pattern:**

```python
elif condition is ProtoSpeechCondition.TWO_TOKEN_COMBINATION:
    last = turns[-1]
    if last.selected_utterance.token_count != 2:
        status = ProtoSpeechStatus.FAIL
    else:
        combo_rec = final_table.select(
            context_signature=ctx_sig,
            utterance_digest=last.selected_utterance.digest_hex16,
        )
        if combo_rec is None or combo_rec.disposition is not (
            ProtoUtteranceDisposition.STABLE_COMBINATION
        ):
            # Acceptable if combination not yet "stable" by the
            # final turn but still emerged; require at least
            # CANDIDATE / REINFORCED disposition.
            if combo_rec is None or combo_rec.disposition not in (
                ProtoUtteranceDisposition.CANDIDATE,
                ProtoUtteranceDisposition.REINFORCED,
                ProtoUtteranceDisposition.STABLE_COMBINATION,
            ):
                status = ProtoSpeechStatus.FAIL
```

**Acceptance interpretation:** PASS if `combo_rec.disposition` is one of `CANDIDATE`, `REINFORCED`, or `STABLE_COMBINATION` (provided `token_count == 2` on the final turn). The comment "Acceptable if combination not yet 'stable' by the final turn but still emerged" explicitly documents the graceful relaxation.

**Canonical disposition:** `STABLE_COMBINATION`. `CANDIDATE` and `REINFORCED` are "in-progress" intermediate dispositions; the substrate has not yet stabilized the 2-token combination by the time the runner finishes. The Phase 3.31 baseline has `stable_combination_count == 0` despite the condition passing 10/10 — this is the documented motivating gap of Phase 3.33.

**Proposed strict counter:** `stable_combination_count_strict` on `ProtoSpeechAcquisitionReport`.

**Strict computation rule:**

```python
def _compute_strict_combination_count(
    final_table: ProtoSpeechEvidenceTable,
) -> int:
    return sum(
        1 for rec in final_table.entries
        if rec.disposition is ProtoUtteranceDisposition.STABLE_COMBINATION
    )
```

(The existing `stable_combination_count` field is already strictly disposition-filtered to `STABLE_COMBINATION` at lines 3112-3116 of the runner — see "Note on existing field" below. The new strict counter computes the same thing but is added explicitly for projector consumption and for symmetry with the graceful-pass acceptance documented at line 3258.)

**Note on existing field:** The currently-emitted `stable_combination_count = sum(... if e.disposition is STABLE_COMBINATION)` at runner line 3112 is dispositionally strict. The "graceful" behavior at line 3258 is at the runner's *acceptance* layer (which conditions get marked PASS), not at the *counting* layer. The Phase 3.33 design's `stable_combination_count_strict` therefore tracks the *same disposition* but with explicit campaign provenance + the `strict_count_warnings` mismatch trigger that compares strict-count against the graceful-acceptance evidence (turns where `token_count == 2 AND combo_rec.disposition is CANDIDATE/REINFORCED`).

**Expected effect on Phase 3.31 baseline:**

- `stable_combination_count` (existing): `0` (no 2-token utterance reached `STABLE_COMBINATION`).
- `stable_combination_count_strict` (new): `0` (same disposition count).
- The graceful-pass evidence at the *acceptance* layer: the final turn's `combo_rec.disposition` is `CANDIDATE` or `REINFORCED`, so a `strict_count_warnings` entry of the form `"C5_TWO_TOKEN_COMBINATION strict_count=0 graceful_acceptance=<disposition>"` IS emitted. This is the honest surfacing the campaign exists to produce.
- The `digest_hex16` remains `f6a83b9caef0ac17` because the new strict counter and the warnings tuple are outside the digest input by design.

**Catalog rows:** `I-PSPEECH-20` (the strict counter field itself, STRUCTURAL) and `I-PROBE-02` (the cross-probe WARN-emission discipline that this finding triggers, STRUCTURAL).

#### Finding F-2: proto_speech_acquisition.HOLOPHRASE_TRANSFER (NOT AFFECTED — HYPOTHESIS FALSIFIED)

**Location:** `brain/development/proto_speech_acquisition.py:3223-3239`

**Runner code:**

```python
elif condition is ProtoSpeechCondition.HOLOPHRASE_TRANSFER:
    # Exactly one transfer must occur to the positive target.
    if transfers != 1:
        status = ProtoSpeechStatus.FAIL
    # The negative-target context must NOT have a TRANSFERRED
    # record for THIS.
    neg_ctx = turns[-1].context
    this_utt = build_proto_utterance((ProtoVocalToken.THIS,))
    neg_rec = final_table.select(
        context_signature=neg_ctx.context_signature,
        utterance_digest=this_utt.digest_hex16,
    )
    if neg_rec is not None and neg_rec.disposition is (
        ProtoUtteranceDisposition.TRANSFERRED
    ):
        fp = 1
        status = ProtoSpeechStatus.FAIL
```

**Acceptance interpretation:** STRICT. `transfers != 1` → FAIL (exactly one transfer required); negative-context having `disposition is TRANSFERRED` → FAIL (false positive). Both checks are exact-equality / strict-disposition tests. No graceful set.

**Status:** The bundle's `transfer_success_count_strict` hypothesis is **falsified**. The runner's acceptance is already strict; there is no graceful-set masking to surface.

**Note on the `transfer_success_count` report field:** The field is `transfers = sum(1 for t in turns if t.transfer_taken)`, a turn-level flag count — not a disposition count. A "strict variant" with semantics `sum(... if rec.disposition is TRANSFERRED)` would be a *different* measurement, not a narrowed version of the same one. The Phase 3.33 strict-counter pattern targets disposition-based graceful-pass acceptance; this isn't that.

**Catalog row:** none. The mapping table's `I-PSPEECH-20` covers the single proto-speech finding F-1 alone; no additional I-PSPEECH-NN slot is allocated for this hypothesis.

### curriculum_consolidation_probe

#### Finding F-3: curriculum_consolidation_probe._evaluate_verdict (NOT AFFECTED — HYPOTHESIS FALSIFIED)

**Location:** `brain/development/curriculum_consolidation_probe.py:934-951`

**Runner code:**

```python
def _evaluate_verdict(
    trial: CurriculumTrial,
    *,
    survived_count: int,
    decayed_count: int,
    rejected_count: int,
    reuse_observed: bool,
) -> tuple[TrialVerdict, bool, bool]:
    survived_ok = survived_count == trial.expected_survived_count
    decayed_ok = decayed_count == trial.expected_decayed_count
    rejected_ok = rejected_count == trial.expected_rejected_count
    reuse_ok = reuse_observed == trial.expected_reuse_observed
    ...
    if survived_ok and decayed_ok and rejected_ok and reuse_ok:
        return TrialVerdict.PASS, false_positive, false_negative
    return TrialVerdict.FAIL, false_positive, false_negative
```

**Acceptance interpretation:** STRICT. Every metric is an exact-equality check (`survived_count == trial.expected_survived_count`, etc.); all four must hold to return PASS. No graceful set.

The underlying disposition counts (`survived_count`, `decayed_count`, `rejected_count` at runner lines 1137-1148) are themselves strict disposition filters (`r.disposition is AuditDisposition.SURVIVED` / `.DECAYED` / `.REJECTED`). The mechanical audit confirmed this.

**Status:** The bundle's "SURVIVED conditions may accept marginal survivors" hypothesis is **falsified**. The runner uses exact-equality verdict-evaluation on strict disposition counts.

**Catalog row:** `I-CURR-15` is **DROPPED** at Step 8 per ADR-001 D1. The mapping table at the top of `PHASE3_33_DESIGN.md` will be updated with a "dropped: curriculum_consolidation_probe runner found strict-only at audit, no strict counter needed" line to preserve the row-number → audit-finding trace.

### active_hypothesis_probe

#### Finding F-4: active_hypothesis_probe._evaluate_verdict (NOT AFFECTED — HYPOTHESIS FALSIFIED)

**Location:** `brain/development/active_hypothesis_probe.py:1172-1203`

**Runner code:**

```python
def _evaluate_verdict(
    trial: ActiveHypothesisTrial,
    *,
    survivors_count: int,
    winner_id: str,
    no_hypothesis_survives: bool,
    second_visit_cache_hit: bool,
    second_visit_probe_count: int,
) -> tuple[TrialVerdict, bool, bool]:
    survivors_ok = survivors_count == trial.expected_survivors_count
    winner_ok = winner_id == trial.expected_winner_id
    no_surv_ok = no_hypothesis_survives == trial.expected_no_hypothesis_survives
    cache_hit_ok = second_visit_cache_hit == trial.expected_second_visit_cache_hit
    probe_count_ok = True
    if trial.expected_second_visit_cache_hit:
        probe_count_ok = second_visit_probe_count == 0
    ...
    if survivors_ok and winner_ok and no_surv_ok and cache_hit_ok and probe_count_ok:
        return TrialVerdict.PASS, false_positive, false_negative
    return TrialVerdict.FAIL, false_positive, false_negative
```

**Acceptance interpretation:** STRICT. Five exact-equality checks AND-combined. `winner_id == trial.expected_winner_id` rejects any "winner unexpectedly emerged" or "no winner where one was expected" case; `no_hypothesis_survives == trial.expected_no_hypothesis_survives` rejects "no-winner accepted as graceful pass when winner expected." The bundle's hypothesized graceful-pass pattern does not exist in this runner.

**Status:** The bundle's "WINNER_SELECTED conditions may accept 'no hypothesis survived' as a graceful pass" hypothesis is **falsified**. The runner explicitly disambiguates winner-expected from no-survivor-expected via separate equality checks.

**Catalog row:** `I-AHYP-15` is **DROPPED** at Step 8.

### osmotic_learning_probe

#### Finding F-5: osmotic_learning_probe.run_osmotic_probe_trial (NOT AFFECTED — HYPOTHESIS FALSIFIED)

**Location:** `brain/development/osmotic_learning_probe.py:760-770`

**Runner code:**

```python
false_positive = transfer_observed and not trial.expected_transfer
false_negative = (not transfer_observed) and trial.expected_transfer
prior_acquired_match = (
    prior_acquired_observed == trial.expected_prior_acquired
)
status = (
    OsmoticProbeStatus.PASS
    if (not false_positive and not false_negative and prior_acquired_match)
    else OsmoticProbeStatus.FAIL
)
```

**Acceptance interpretation:** STRICT. PASS requires three independent strict checks (`transfer_observed == trial.expected_transfer` reduced via the FP/FN composite, AND `prior_acquired_observed == trial.expected_prior_acquired`). `transfer_observed` is itself defined strictly: `any(r.kind is LearningEvidenceKind.TRANSFER_RECOGNIZED and r.abstract_pattern_digest == trial.expected_target_digest for r in new_records)`. No graceful set.

**Status:** The bundle's "TRANSFER conditions may accept transfer-attempt without successful transfer" hypothesis is **falsified**. The runner requires actual `TRANSFER_RECOGNIZED` evidence with matching `abstract_pattern_digest`; transfer-attempt without success would set `transfer_observed = False` and produce `false_negative = True` → FAIL.

**Catalog row:** `I-OSMO-15` is **DROPPED** at Step 8.

### worldlet_feedback_bridge

**Status: NOT APPLICABLE.** No standalone probe module exists at `brain/development/worldlet_feedback_bridge.py` or any analogous path. The Phase 3.24 worldlet feedback bridge work lives inside `brain/development/processing_window.py` as helper functions (`build_worldlet_summary_text`, `_run_worldlet_feedback_step`) with no `run_*_live_test` entry point and no `Status.PASS` / `Status.FAIL` emission. Worldlet feedback's effects are observed via the existing benchmark axis A11 cases (A11.01..A11.12) which read derived facts off the dispatch trace — those benchmark cases have their own assertion layer that is already strict (case-by-case).

The bundle's hypothesis "no canonical live-test runner exists; if so, no strict counter needed" is **confirmed**. No catalog row was allocated for worldlet in the mapping table; no row is dropped.

## Note on non-disposition gracefulness (Decision rule 6 sweep — clear)

Manual review specifically looked for non-disposition-based gracefulness that the mechanical audit tool would not catch — threshold checks, count-range acceptance, "any token_count >= 1", etc. Findings:

- **proto_speech_acquisition.FEEDBACK_REINFORCEMENT** (line 3182-3187): the runner accepts `rec.weight_after >= 3`, which is a *threshold* check (not a disposition set). In proto-speech evidence semantics, `weight_after in [3, 6)` corresponds to disposition `REINFORCED`, and `weight_after >= STABLE_SINGLE_THRESHOLD = 6` corresponds to `STABLE_SINGLE`. The threshold is therefore disposition-correlated (`weight_after >= 3` ↔ `disposition in {REINFORCED, STABLE_SINGLE}`), but it does NOT mask a report counter: the existing `stable_single_count` field is computed strictly as `sum(... if e.disposition is STABLE_SINGLE)` (runner line 3107) and is already strict. The graceful internal-acceptance threshold could be tightened in a future Phase 3.35+ *targeted-consolidation* campaign (raising the threshold to `STABLE_SINGLE_THRESHOLD`), but it is NOT a Phase 3.33 strict-counter pattern issue. **Not escalated to Decision rule 6** because no report counter is masked.
- All other inspected conditions: no threshold-based, count-range, or text-match gracefulness identified.

**Decision rule 6 status: not triggered.** No non-disposition graceful patterns surfaced that would warrant a separate follow-up campaign in lieu of folding into Phase 3.33's disposition-based scope.

## Catalog patch impact (input for Step 8)

Of the five row IDs allocated in the Phase 3.33 mapping table:

```text
Row             Source-of-truth at end of audit                  Step 8 action
─────────────────────────────────────────────────────────────────────────────
I-PSPEECH-20    F-1 confirmed                                    LAND
I-CURR-15       F-3 hypothesis falsified                         DROP
I-AHYP-15       F-4 hypothesis falsified                         DROP
I-OSMO-15       F-5 hypothesis falsified                         DROP
I-PROBE-02      WARN discipline applies to F-1's affected probe  LAND
```

Net catalog v0.38 → v0.39 patch: **+2 STRUCTURAL rows** (`I-PSPEECH-20`, `I-PROBE-02`), not +5. The mapping table at the top of `PHASE3_33_DESIGN.md` will be updated at Step 8 with the "dropped" annotations preserving the row-number → audit-finding trace per the operator's clarification.

The strict-counter authoring scope (Steps 5a–5d) collapses to **Step 5a only** (proto-speech: `stable_combination_count_strict` field per F-1, plus the `strict_count_warnings: tuple[str, ...]` field per the I-PROBE-02 WARN discipline). Steps 5b/5c/5d are NOT executed.

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
