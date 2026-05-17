# PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md

## 1. Purpose

This document designs the future catalog patch for Phase 3.5 Expression + ReadabilityPredictor rows.

It is a planning artifact only. It does not apply catalog rows, edit `tools/catalog.py`, add runtime modules, add fixtures, change generated catalog IDs, alter `INVARIANT_CATALOG.md`, change `brain/invariants.py`, or change the TLICA runtime boundary. It does not authorize a UI integration pane, per `C10-AMEND-01`.

## 2. Review-gate corrigendum

The first Step 4 plan was blocked at review gate because it made two false assumptions:

```text
1. It claimed existing tools.import_audit covers brain/development/expression.py.
   It does not; tools.import_audit currently covers the existing agency/PCE audit only.

2. It described pending rows using fixture=None / registered=False language.
   That is not how brain/invariants.py works. The real pattern is a pending-row
   dictionary plus generated checks that raise NotImplementedError until the
   runtime fixtures replace them.
```

This revised plan fixes both blockers.

No row IDs, statuses, catalog counts, hard boundaries, or implementation order are changed.

Verdict after corrigendum:

```text
COHERENT - READY FOR REVIEW GATE
```

## 3. Baseline

Current catalog baseline is v0.11:

```text
REQUIRED:       127
STRUCTURAL:      44
NOT-EXERCISED:    4
DEFERRED:        12
OBSERVED:         7
```

Total tabular entries: `194`.

Required PASS audit artifacts:

```text
OPERATOR_TUI_AUDIT.md
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md
```

## 4. Patch impact

The accepted catalog patch adds:

```text
+12 REQUIRED
 +4 STRUCTURAL
 +1 NOT-EXERCISED
 +0 DEFERRED
 +1 OBSERVED
```

Expected counts after the accepted patch:

```text
REQUIRED:       139
STRUCTURAL:      48
NOT-EXERCISED:    5
DEFERRED:        12
OBSERVED:         8
```

Total tabular entries become `212` if no other rows are added or removed.

## 5. Row family thesis

The patch row family uses `I-EXP-*` IDs.

Core commitments:

```text
Expression is a bounded local representation of how an existing local-history item is shaped for inspection.
Expression is not language, not a generated utterance, not a chat/message/dialogue surface.
ReadabilityScore is a Fraction in [0, 1] computed by a deterministic Fraction-only combinator over an ExpressionFeatureVector.
ReadabilityScore is not truth, validity, language quality, social success, intelligence, or agency.
ExpressionHistory is bounded, copy-on-write, process-local, and not serialized.
The bridge from OutputHistory / WorldletHistory / ProtoBasicHistory / OperatorTranscript to ExpressionRecord is one-way.
No source history, BrainState, MSI, PtCns, registry, tick, trace, scenario, or TLICA runtime object may be mutated by expression/readability logic.
UI integration is deferred. No brain/ui/* file is touched by Phase 3.5.
```

## 6. Row table

All rows use the `I-EXP-*` family. Owning module is `brain/development/expression.py` unless noted.

### 6.1 REQUIRED rows

```text
I-EXP-01  ExpressionSource is a finite closed enumeration
          Fixture: expression_source_enum_closed.py

I-EXP-02  ExpressionItem.text is bounded printable
          Fixture: expression_item_bounded.py

I-EXP-03  ExpressionFeatureVector is deterministic and exact
          Fixture: expression_feature_vector_exact.py

I-EXP-04  ReadabilityScore is Fraction in [0, 1]
          Fixture: readability_score_fraction_bounded.py

I-EXP-05  ReadabilityPrediction is source-tagged and predictor-tagged
          Fixture: readability_prediction_tagged.py

I-EXP-06  ExpressionHistory is copy-on-write and bounded
          Fixture: expression_history_cow_bounded.py

I-EXP-07  No mutation of BrainState / MSI / PtCns / registry
          Fixture: expression_no_brainstate_mutation.py

I-EXP-08  No mutation of OutputHistory / WorldletHistory / ProtoBasicHistory / OperatorTranscript
          Fixture: expression_no_source_history_mutation.py

I-EXP-09  Anti-Goodhart: empty / whitespace-only items score Fraction(0)
          Fixture: readability_predictor_empty_item.py

I-EXP-10  Anti-Goodhart: repetition alone never increases the score
          Fixture: readability_predictor_repetition_only.py

I-EXP-11  Anti-Goodhart: length alone is capped
          Fixture: readability_predictor_length_cap.py

I-EXP-12  Predictor determinism
          Fixture: readability_predictor_determinism.py
```

### 6.2 STRUCTURAL rows

```text
I-EXP-13  Expression module has no I/O / network / file / shell import
          Fixture: expression_static_audit.py

I-EXP-14  Expression records are frozen dataclasses
          Fixture: expression_feature_vector_exact.py and readability_prediction_tagged.py

I-EXP-15  Bridge constructors are pure and do not register callbacks
          Fixture: expression_static_audit.py

I-EXP-16  Predictor module has no float / math / round on the score path
          Fixture: expression_static_audit.py
```

`expression_static_audit.py` must implement AST/static checks over `brain/development/expression.py`. It must not rely on existing `tools.import_audit` unless a future campaign explicitly extends that tool. For this campaign, the static expression audit lives in the fixture.

### 6.3 OBSERVED row

```text
I-EXP-17  Aggregate ExpressionHistory summary view is OBSERVED only
          Fixture: none; cited from the audit.
```

### 6.4 NOT-EXERCISED row

```text
I-EXP-18  ExpressionHistory write-to-disk path is NOT-EXERCISED
          Fixture: none.
```

## 7. Fixture roster

```text
I-EXP-01  expression_source_enum_closed.py
I-EXP-02  expression_item_bounded.py
I-EXP-03  expression_feature_vector_exact.py
I-EXP-04  readability_score_fraction_bounded.py
I-EXP-05  readability_prediction_tagged.py
I-EXP-06  expression_history_cow_bounded.py
I-EXP-07  expression_no_brainstate_mutation.py
I-EXP-08  expression_no_source_history_mutation.py
I-EXP-09  readability_predictor_empty_item.py
I-EXP-10  readability_predictor_repetition_only.py
I-EXP-11  readability_predictor_length_cap.py
I-EXP-12  readability_predictor_determinism.py
I-EXP-13  expression_static_audit.py
I-EXP-14  expression_feature_vector_exact.py + readability_prediction_tagged.py
I-EXP-15  expression_static_audit.py
I-EXP-16  expression_static_audit.py
I-EXP-17  OBSERVED; no fixture
I-EXP-18  NOT-EXERCISED; no fixture
```

Fixture delta: `+13` fixture files, including the shared `expression_static_audit.py` fixture.

## 8. File budget

New production file:

```text
brain/development/expression.py
```

New fixture files:

```text
brain/development/fixtures/expression_source_enum_closed.py
brain/development/fixtures/expression_item_bounded.py
brain/development/fixtures/expression_feature_vector_exact.py
brain/development/fixtures/readability_score_fraction_bounded.py
brain/development/fixtures/readability_prediction_tagged.py
brain/development/fixtures/expression_history_cow_bounded.py
brain/development/fixtures/expression_no_brainstate_mutation.py
brain/development/fixtures/expression_no_source_history_mutation.py
brain/development/fixtures/readability_predictor_empty_item.py
brain/development/fixtures/readability_predictor_repetition_only.py
brain/development/fixtures/readability_predictor_length_cap.py
brain/development/fixtures/readability_predictor_determinism.py
brain/development/fixtures/expression_static_audit.py
```

Modified files for Step 6 catalog patch:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Explicitly excluded:

```text
brain/ui/*
brain/tick.py
brain/llm/*
brain/tlica/*
traces/
scenarios/
lean_reference/
```

## 9. Catalog patch mechanics

Step 6 sequence:

```text
1. Add the 18 new I-EXP-* row entries to INVARIANT_CATALOG.md.
2. Update INVARIANT_CATALOG.md banner counts to REQUIRED 139, STRUCTURAL 48, NOT-EXERCISED 5, DEFERRED 12, OBSERVED 8.
3. Update tools/catalog.py expected counts to match.
4. Add _PHASE3_5_PENDING_ROWS to brain/invariants.py using the actual existing pending-row pattern.
5. Run python3 -m tools.catalog counts.
6. Run python3 -m tools.catalog generate-ids.
7. Run python3 -m tools.catalog counts again.
8. Commit and push the Step 6 patch with only the accepted Step 6 files.
```

Row descriptions must not claim the score asserts correctness, truth, validity, accuracy, quality, social success, intelligence, agency, or language understanding.

The predictor row must include this sentence:

```text
This module computes a bounded structural score over a local expression item. It does NOT model language.
```

## 10. Pending registration mechanics

Step 6 must use the actual `brain/invariants.py` pattern:

```python
_PHASE3_5_PENDING_ROWS: dict[str, str] = {
    "I-EXP-01": "REQUIRED",
    "I-EXP-02": "REQUIRED",
    "I-EXP-03": "REQUIRED",
    "I-EXP-04": "REQUIRED",
    "I-EXP-05": "REQUIRED",
    "I-EXP-06": "REQUIRED",
    "I-EXP-07": "REQUIRED",
    "I-EXP-08": "REQUIRED",
    "I-EXP-09": "REQUIRED",
    "I-EXP-10": "REQUIRED",
    "I-EXP-11": "REQUIRED",
    "I-EXP-12": "REQUIRED",
    "I-EXP-13": "STRUCTURAL",
    "I-EXP-14": "STRUCTURAL",
    "I-EXP-15": "STRUCTURAL",
    "I-EXP-16": "STRUCTURAL",
}
```

Add a helper matching the established shape:

```python
def _make_phase3_5_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.5 catalog coverage "
            "but its runtime implementation has not landed yet"
        )
    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check
```

Then register each pending row with:

```python
for _row_id, _status in _PHASE3_5_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_5_pending_check(_row_id))
```

Do not use `fixture=None`, `registered=False`, or any invented pending-row schema.

I-EXP-17 (OBSERVED) and I-EXP-18 (NOT-EXERCISED) are not pending entries and do not participate in I-CAT-01 coverage.

## 11. Strict implementation order

```text
Step 5   Review gate
Step 6   Apply accepted catalog patch
Step 7   Implement expression core
            -> expression.py
            -> fixtures for I-EXP-01, I-EXP-02, I-EXP-03,
               I-EXP-07, I-EXP-08, I-EXP-13, I-EXP-14, I-EXP-15
Step 8   Implement ReadabilityPredictor
            -> expression.py
            -> fixtures for I-EXP-04, I-EXP-05, I-EXP-09,
               I-EXP-10, I-EXP-11, I-EXP-12, I-EXP-16
Step 9   Implement ExpressionHistory and local summaries
            -> expression.py
            -> fixtures for I-EXP-06
            -> OBSERVED I-EXP-17 documented in audit
Step 10  SKIPPED  (UI integration deferred per C10-AMEND-01)
Step 11  Full gate
Step 12  Post-completion audit
```

`expression_static_audit.py` may land in Step 7 or Step 8, but all rows it drives must be real fixture-backed checks before Step 11.

## 12. Open decisions

No blocking open decisions remain. Implementation parameters may be selected inside the ranges locked by the corrigenda:

```text
EXPRESSION_TEXT_MAX_LEN:        [256, 4096]
EXPRESSION_TOKEN_MAX_COUNT:     [64, 1024]
EXPRESSION_HISTORY_MAX_ENTRIES: [16, 1024]
SHAPE_BALANCE_TARGET:           one of {1/8, 1/6, 1/5, 1/4}
W_PRINTABLE + W_SHAPE + W_DISTINCT == 1
W_REPEAT in [0, 1/2]
```

These choices do not change row IDs, statuses, titles, or catalog counts.

## 13. Stop conditions

Stop and reopen corrigenda if any request would:

```text
use agency-implying language
claim the score asserts correctness, truth, validity, accuracy, quality, social success, intelligence, or language understanding
authorize a UI inspection pane in this campaign
authorize ExpressionHistory serialization/weaving into traces or scenarios
weaken any existing I-* row
add an external dependency, LLM call, shell/subprocess/network call, or file write path
change scenario / trace schema
promote expression evidence into PerceptEvent / tick() / TLICA runtime
promote an OBSERVED / STRUCTURAL row to REQUIRED without new corrigenda
```

## 14. Acceptance criteria

The plan is accepted by Step 5 when:

```text
all 18 rows are acceptable
the count delta is reconciled: +12 REQUIRED, +4 STRUCTURAL, +1 NOT-EXERCISED, +1 OBSERVED
the +13 fixture roster is acceptable, including expression_static_audit.py
the file budget excludes brain/ui/*, LLM, scenario, trace, and TLICA files
Step 6 pending mechanics match the existing _PHASE3_5_PENDING_ROWS pattern
Step 10 remains skipped
no stop condition has triggered
```

When accepted, Step 6 may run. The patch remains a catalog/planning patch; runtime and fixtures land only in Steps 7-9.
