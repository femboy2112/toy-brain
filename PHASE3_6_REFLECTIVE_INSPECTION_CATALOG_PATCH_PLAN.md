# PHASE3_6_REFLECTIVE_INSPECTION_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in `PHASE3_6_REFLECTIVE_INSPECTION_CORRIGENDA.md` to
concrete catalog rows, statuses, file budget, count delta, fixture
roster, and pending-registration mechanics. This is a planning artifact
only. It does not apply catalog rows, edit `tools/catalog.py`, add
runtime modules, add fixtures, change generated catalog IDs, alter
`INVARIANT_CATALOG.md`, or change `brain/invariants.py`.

Verdict for the Step 9 review gate:

```text
COHERENT — READY FOR REVIEW GATE
```

## 2. Baseline

```text
Catalog version:  v0.12
REQUIRED:        139
STRUCTURAL:       48
NOT-EXERCISED:     5
DEFERRED:         12
OBSERVED:          8
Total tabular:   212
```

Required latest audit:

```text
PHASE3_5_EXPRESSION_READABILITY_AUDIT.md   PASS
```

## 3. Patch impact

```text
+ 8 REQUIRED
+ 4 STRUCTURAL
+ 1 NOT-EXERCISED
+ 0 DEFERRED
+ 1 OBSERVED
```

Expected counts after the accepted patch:

```text
Catalog version:  v0.13
REQUIRED:        147
STRUCTURAL:       52
NOT-EXERCISED:     6
DEFERRED:         12
OBSERVED:          9
Total tabular:   226
```

## 4. Row family thesis

Row family:

```text
I-REF-*
```

Core commitments:

```text
Reflective Inspection is a bounded local read-only summary layer
  over OutputHistory / WorldletHistory / ProtoBasicHistory /
  ExpressionHistory / OperatorTranscript.

Reflective Inspection is not Mode B, not language, not truth, not
  agency, not a UI surface in Phase 3.6.

ReflectiveSummaryItem fields are exact counts and (when supplied
  by the source) exact Fraction statistics; no aggregate score is
  produced.

ReflectiveInspectionSnapshot is a frozen record; construction does
  not mutate any source history, BrainState, MSI, PtCns, registry,
  or TLICA runtime object.

Aggregate inspection walk is OBSERVED only; the walk is a Python
  frozen dataclass; no serialization.

InspectionHistory is DEFERRED to a later campaign.

brain/ui/* integration is DEFERRED to Phase 3.8 (per C10-AMEND-01
  analog `C13-AMEND-01`).

Reflective write-to-disk is NOT-EXERCISED placeholder.
```

## 5. Row table

All rows use the `I-REF-*` family. Owning module is
`brain/development/reflective.py` unless noted.

### 5.1 REQUIRED rows

```text
I-REF-01  ReflectiveSource is a finite closed enumeration
          Fixture: reflective_source_enum_closed.py

I-REF-02  ReflectiveSummaryItem is bounded
          Fixture: reflective_summary_item_bounded.py

I-REF-03  counts_by_category sums exactly to entry_count
          Fixture: reflective_summary_item_bounded.py

I-REF-04  distinct_id_count <= entry_count
          Fixture: reflective_summary_item_bounded.py

I-REF-05  ReflectiveInspectionSnapshot construction is deterministic
          Fixture: reflective_snapshot_deterministic.py

I-REF-06  Reflective ops do not mutate BrainState / MSI / PtCns / registry
          Fixture: reflective_no_brainstate_mutation.py

I-REF-07  Reflective ops do not mutate source histories
          Fixture: reflective_no_source_history_mutation.py

I-REF-08  Reflective summary surfaces source-supplied scores only; no
          aggregate score is produced
          Fixture: reflective_no_aggregate_score.py
```

### 5.2 STRUCTURAL rows

```text
I-REF-09  Reflective module has no I/O / network / file / shell / LLM /
          TLICA / tick / curses import
          Fixture: reflective_static_audit.py

I-REF-10  Reflective records are frozen dataclasses
          Fixture: reflective_summary_item_bounded.py and
                   reflective_snapshot_deterministic.py

I-REF-11  Reflective module has no float / round / math on the
          count / statistic path
          Fixture: reflective_static_audit.py

I-REF-12  Reflective constructors are pure and register no callbacks
          Fixture: reflective_static_audit.py
```

### 5.3 OBSERVED row

```text
I-REF-13  Aggregate ReflectiveInspectionSummary walk is inspectable
          Fixture: none; cited from the Phase 3.6 audit.
```

### 5.4 NOT-EXERCISED row

```text
I-REF-14  Reflective save / export path is NOT-EXERCISED
          Fixture: none.
```

## 6. Fixture roster

```text
I-REF-01  reflective_source_enum_closed.py
I-REF-02  reflective_summary_item_bounded.py
I-REF-03  reflective_summary_item_bounded.py
I-REF-04  reflective_summary_item_bounded.py
I-REF-05  reflective_snapshot_deterministic.py
I-REF-06  reflective_no_brainstate_mutation.py
I-REF-07  reflective_no_source_history_mutation.py
I-REF-08  reflective_no_aggregate_score.py
I-REF-09  reflective_static_audit.py
I-REF-10  reflective_summary_item_bounded.py +
          reflective_snapshot_deterministic.py
I-REF-11  reflective_static_audit.py
I-REF-12  reflective_static_audit.py
I-REF-13  OBSERVED; no fixture
I-REF-14  NOT-EXERCISED; no fixture
```

Fixture file delta: `+6` files.

```text
brain/development/fixtures/reflective_source_enum_closed.py
brain/development/fixtures/reflective_summary_item_bounded.py
brain/development/fixtures/reflective_snapshot_deterministic.py
brain/development/fixtures/reflective_no_brainstate_mutation.py
brain/development/fixtures/reflective_no_source_history_mutation.py
brain/development/fixtures/reflective_no_aggregate_score.py
brain/development/fixtures/reflective_static_audit.py
```

Wait — counting:

```text
reflective_source_enum_closed.py
reflective_summary_item_bounded.py
reflective_snapshot_deterministic.py
reflective_no_brainstate_mutation.py
reflective_no_source_history_mutation.py
reflective_no_aggregate_score.py
reflective_static_audit.py
```

That is **7** new fixture files. The fixture roster total moves from
`50` to `57`.

## 7. File budget

New production file:

```text
brain/development/reflective.py
```

New fixture files (7):

```text
brain/development/fixtures/reflective_source_enum_closed.py
brain/development/fixtures/reflective_summary_item_bounded.py
brain/development/fixtures/reflective_snapshot_deterministic.py
brain/development/fixtures/reflective_no_brainstate_mutation.py
brain/development/fixtures/reflective_no_source_history_mutation.py
brain/development/fixtures/reflective_no_aggregate_score.py
brain/development/fixtures/reflective_static_audit.py
```

Modified files for Step 6 catalog patch:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Explicitly excluded (no Step in Phase 3.6 touches these):

```text
brain/ui/*
brain/tick.py
brain/llm/*
brain/tlica/*
traces/
scenarios/
lean_reference/
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
brain/development/expression.py
brain/ui/transcript.py
```

## 8. Catalog patch mechanics (Step 6)

```text
1. Add the 14 new I-REF-* row entries to INVARIANT_CATALOG.md under
   a new "### Phase 3.6 Reflective Inspection developmental
   invariants" section.
2. Update the INVARIANT_CATALOG.md banner with a v0.13 entry.
3. Update INVARIANT_CATALOG.md banner counts to REQUIRED 147,
   STRUCTURAL 52, NOT-EXERCISED 6, DEFERRED 12, OBSERVED 9.
4. Update the fixture roster table with the 7 new fixture files.
5. Update the summary counts section to v0.13.
6. Update tools/catalog.py EXPECTED_COUNTS to match.
7. Add _PHASE3_6_PENDING_ROWS to brain/invariants.py using the
   existing pending-row pattern.
8. Run python3 -m tools.catalog counts.
9. Run python3 -m tools.catalog generate-ids.
10. Run python3 -m tools.catalog counts again.
11. Commit and push.
```

Row descriptions must not claim Reflective Inspection asserts truth,
validity, accuracy, quality, social success, intelligence, agency,
language understanding, or Mode B planning capability.

Required disclaimer to appear in the I-REF-08 row description:

```text
The reflective layer surfaces counts and source-supplied exact
statistics; it does NOT produce an aggregate score, quality
estimate, intelligence measure, social-success measure, or truth
claim.
```

## 9. Pending registration mechanics (Step 6)

Step 6 must use the established `brain/invariants.py` pending-row
pattern (same shape as `_PHASE3_5_PENDING_ROWS`):

```python
_PHASE3_6_PENDING_ROWS: dict[str, str] = {
    "I-REF-01": "REQUIRED",
    "I-REF-02": "REQUIRED",
    "I-REF-03": "REQUIRED",
    "I-REF-04": "REQUIRED",
    "I-REF-05": "REQUIRED",
    "I-REF-06": "REQUIRED",
    "I-REF-07": "REQUIRED",
    "I-REF-08": "REQUIRED",
    "I-REF-09": "STRUCTURAL",
    "I-REF-10": "STRUCTURAL",
    "I-REF-11": "STRUCTURAL",
    "I-REF-12": "STRUCTURAL",
}

def _make_phase3_6_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.6 catalog coverage "
            "but its runtime implementation has not landed yet"
        )
    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check

for _row_id, _status in _PHASE3_6_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_6_pending_check(_row_id))
```

I-REF-13 (OBSERVED) and I-REF-14 (NOT-EXERCISED) do not participate in
I-CAT-01 coverage and are not pending entries.

## 10. Strict implementation order

```text
Step 5   Review gate (this artifact must be accepted before Step 6)
Step 6   Apply accepted catalog patch
Step 7   Implement Phase 3.6 core
            -> brain/development/reflective.py
            -> brain/development/fixtures/reflective_source_enum_closed.py
            -> brain/development/fixtures/reflective_summary_item_bounded.py
            -> brain/development/fixtures/reflective_snapshot_deterministic.py
            -> brain/development/fixtures/reflective_no_brainstate_mutation.py
            -> brain/development/fixtures/reflective_no_source_history_mutation.py
            -> brain/development/fixtures/reflective_no_aggregate_score.py
            -> brain/development/fixtures/reflective_static_audit.py
            -> drain _PHASE3_6_PENDING_ROWS in brain/invariants.py
            -> add the 7 fixture modules to FIXTURE_MODULES
Step 8   Phase 3.6 full gate + audit
            -> PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md
Step 9   Review gate before Phase 3.7 begins
```

The catalog plan grants Step 7 the option to bundle all 7 fixture
files in a single commit, mirroring the Phase 3.5 Step 7 allowance.

## 11. Open decisions

```text
None blocking. Implementation parameters may be selected inside the
ranges locked by the corrigenda:

REFLECTIVE_NOTES_MAX_NOTES:        small fixed cap, plan locks 8
REFLECTIVE_NOTES_MAX_LEN:          bounded printable length, plan
                                   locks <= 64 characters per note
INSPECTION_HISTORY_MAX_SNAPSHOTS:  not applicable (InspectionHistory
                                   deferred)
```

## 12. Stop conditions

Stop and reopen corrigenda if any request would:

```text
allow Mode B planning surface
allow self-modification
authorize a UI integration pane in Phase 3.6
authorize InspectionHistory in Phase 3.6
authorize reflective serialization / weaving into traces or scenarios
authorize aggregate "quality" / "intelligence" / "social-success"
  scoring
weaken any existing I-* row
add an external dependency, LLM call, shell/subprocess/network call,
  or file write path
change scenario / trace schema
promote reflective evidence into PerceptEvent / tick() / TLICA runtime
promote an OBSERVED / STRUCTURAL row to REQUIRED without new
  corrigenda
```

## 13. Acceptance criteria for the Step 9 review gate

The plan is accepted when:

```text
all 14 rows are acceptable
the count delta is reconciled: +8 REQUIRED, +4 STRUCTURAL,
  +1 NOT-EXERCISED, +1 OBSERVED
the +7 fixture roster (one shared reflective_static_audit.py
  handling I-REF-09, I-REF-11, I-REF-12) is acceptable
the file budget excludes brain/ui/*, LLM, scenario, trace, TLICA,
  and the other developmental modules
Step 6 pending mechanics match the established
  _PHASE3_6_PENDING_ROWS pattern
brain/ui/* integration remains deferred to Phase 3.8
InspectionHistory remains deferred
no stop condition has triggered
```

When accepted, Step 6 may run. The patch remains a catalog/planning
patch; runtime and fixtures land only in Step 7.
