# PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md

## 1. Purpose

This document designs the future catalog patch for Phase 3.5 Expression +
ReadabilityPredictor rows.

It is a planning artifact only. It does not apply catalog rows, edit
`tools/catalog.py`, add runtime modules, add fixtures, change generated
catalog IDs, alter `INVARIANT_CATALOG.md`, change `brain/invariants.py`, or
change the TLICA runtime boundary. It does not authorize a UI integration
pane (per corrigenda C10-AMEND-01).

Verdict:

```text
COHERENT - READY FOR REVIEW GATE
```

No unresolved blocker prevents a later accepted catalog patch. The plan
keeps Expression strictly below language, below truth scoring, below
social communication, below agency / planning, below LLM reach, below
host / shell / network / file execution, below `PerceptEvent` / `tick()`
promotion, and below TLICA runtime mutation. It also defers UI integration
to a future campaign.

This plan adopts the corrigenda's status mapping (C8) and amendments
(C1-AMEND-01, C4-AMEND-01, C5-AMEND-01, C5-AMEND-02, C6-AMEND-01,
C6-AMEND-02, C7-AMEND-01, C7-AMEND-02, C9-AMEND-01, C10-AMEND-01).

## 2. Baseline

Current catalog baseline is v0.11:

```text
REQUIRED:       127
STRUCTURAL:      44
NOT-EXERCISED:    4
DEFERRED:        12
OBSERVED:         7
```

Total tabular entries: `194`.

`python3 -m tools.catalog counts` reports `ok` for every banner row under
v0.11.

Operator TUI audits are PASS:

```text
OPERATOR_TUI_AUDIT.md                           — PASS
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md          — PASS
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md              — PASS
```

Phase 3.4 Proto-BASIC REPL rows (`I-REPL-*`) are landed and green. The
ProtoBasicHistory / OutputHistory / WorldletHistory / OperatorTranscript
surfaces are frozen-dataclass-based and have public read accessors, so
Phase 3.5 bridges have a stable inspection surface.

## 3. Patch Impact

The next-version patch proposed here adds:

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

Fixture roster delta (planned for Steps 7-9, not landed by Step 6):

```text
+1 expression_source_enum_closed.py
+1 expression_item_bounded.py
+1 expression_feature_vector_exact.py
+1 readability_score_fraction_bounded.py
+1 readability_prediction_tagged.py
+1 expression_history_cow_bounded.py
+1 expression_no_brainstate_mutation.py
+1 expression_no_source_history_mutation.py
+1 readability_predictor_empty_item.py
+1 readability_predictor_repetition_only.py
+1 readability_predictor_length_cap.py
+1 readability_predictor_determinism.py
```

Total: `+12` Phase 3.5 fixtures. These are pinned by the REQUIRED rows.
STRUCTURAL rows are covered by import-audit / static-grep checks and do
not add fixtures.

## 4. Row Family Thesis

The patch row family uses `I-EXP-*` IDs.

Core commitments inherited from the synthesis, kickoff, and corrigenda:

```text
Expression is a bounded local representation of how an existing local-
  history item is shaped for inspection. It is not language, not a
  generated utterance, not a chat / message / dialogue.

ReadabilityScore is a Fraction in [0, 1] computed by a deterministic
  Fraction-only combinator over an ExpressionFeatureVector. It is not
  truth, not validity, not language quality, not social success, not
  intelligence, not agency.

Anti-Goodhart rules A-J hold by construction of the combinator and
  feature definitions. Each REQUIRED anti-Goodhart row has a fixture.

ExpressionHistory is bounded, copy-on-write, process-local, and not
  serialized. It does not feed back into the kernel, traces, scenarios,
  or any source history.

The bridge from OutputHistory / WorldletHistory / ProtoBasicHistory /
  OperatorTranscript to ExpressionRecord is one-way: source histories
  are read through public accessors only and are not mutated.

UI integration is deferred. No brain/ui/* file is touched by Phase 3.5.
```

## 5. Row Table

All rows use the `I-EXP-*` family. Each row's status follows the
corrigenda's C8 mapping. Owning module is `brain/development/expression.py`
unless noted.

### 5.1 REQUIRED rows (+12)

```text
I-EXP-01  ExpressionSource is a finite closed enumeration
          Owner:  brain/development/expression.py
          Check:  enumeration membership equals locked variant set;
                  no UNKNOWN / OTHER / ANY variant exists
          Fixture: expression_source_enum_closed.py

I-EXP-02  ExpressionItem.text is bounded printable
          Owner:  brain/development/expression.py
          Check:  text length <= EXPRESSION_TEXT_MAX_LEN;
                  every char is in the printable-with-replacement policy;
                  content_id length <= EXPRESSION_CONTENT_ID_MAX_LEN;
                  content_id has no reserved prefix
          Fixture: expression_item_bounded.py

I-EXP-03  ExpressionFeatureVector is deterministic and exact
          Owner:  brain/development/expression.py
          Check:  every field is int or fractions.Fraction;
                  no float occurs anywhere on the construction path;
                  identical ExpressionItem produces identical vector
          Fixture: expression_feature_vector_exact.py

I-EXP-04  ReadabilityScore is Fraction in [0, 1]
          Owner:  brain/development/expression.py
          Check:  ReadabilityScore.value is fractions.Fraction;
                  0 <= value <= 1;
                  constructor rejects float / Decimal / str
          Fixture: readability_score_fraction_bounded.py

I-EXP-05  ReadabilityPrediction is source-tagged and predictor-tagged
          Owner:  brain/development/expression.py
          Check:  prediction.source equals expression.source;
                  prediction.predictor_tag equals the module-frozen
                  predictor tag constant;
                  prediction.expression_id equals item.item_id
          Fixture: readability_prediction_tagged.py

I-EXP-06  ExpressionHistory is copy-on-write and bounded
          Owner:  brain/development/expression.py
          Check:  append returns a NEW ExpressionHistory;
                  input ExpressionHistory is unchanged;
                  len(history.entries) <= EXPRESSION_HISTORY_MAX_ENTRIES
                  for any append sequence;
                  capacity overflow drops the oldest entry (FIFO)
          Fixture: expression_history_cow_bounded.py

I-EXP-07  No mutation of BrainState / MSI / PtCns / registry
          Owner:  brain/development/expression.py
          Check:  bridge constructors and predictor do not import
                  BrainState mutators, MSI mutators, PtCns mutators,
                  or registry mutators;
                  predict() and bridge constructors return without
                  side effects on any kernel object
          Fixture: expression_no_brainstate_mutation.py

I-EXP-08  No mutation of OutputHistory / WorldletHistory /
          ProtoBasicHistory / OperatorTranscript
          Owner:  brain/development/expression.py
          Check:  bridge constructors read only public accessors of
                  the source records;
                  source records before and after the bridge call are
                  bitwise equal (frozen dataclass equality);
                  no append / register / promote method is invoked
          Fixture: expression_no_source_history_mutation.py

I-EXP-09  Anti-Goodhart: empty / whitespace-only items score Fraction(0)
          Owner:  brain/development/expression.py
          Check:  text == "" yields score == Fraction(0);
                  text consisting only of whitespace yields
                  score == Fraction(0)
          Fixture: readability_predictor_empty_item.py

I-EXP-10  Anti-Goodhart: repetition alone never increases the score
          Owner:  brain/development/expression.py
          Check:  for token T, score(N copies of T) <= score(1 copy of T)
                  for all N >= 1 (strict inequality holds for N > 1 in
                  the locked combinator; the row asserts non-increase as
                  the public contract)
          Fixture: readability_predictor_repetition_only.py

I-EXP-11  Anti-Goodhart: length alone is capped
          Owner:  brain/development/expression.py
          Check:  for length_chars > LENGTH_CAP_THRESHOLD, score is
                  capped at LENGTH_CAP;
                  for items differing only in length above the
                  threshold, the longer item has score <= the shorter
          Fixture: readability_predictor_length_cap.py

I-EXP-12  Predictor determinism
          Owner:  brain/development/expression.py
          Check:  for identical (ExpressionItem, predictor_tag),
                  ReadabilityPrediction.features and
                  ReadabilityPrediction.score are equal across
                  repeated calls;
                  predictor_tag is a module constant (not a parameter,
                  not env-derived)
          Fixture: readability_predictor_determinism.py
```

### 5.2 STRUCTURAL rows (+4)

```text
I-EXP-13  ExpressionHistory has no I/O / network / file / shell import
          Owner:  brain/development/expression.py
          Check:  import-audit: no import of os, subprocess, socket,
                  urllib, http, requests, asyncio, threading.run, or
                  pathlib-as-writer within the expression module(s)
          Fixture: covered by tools.import_audit (no separate fixture)

I-EXP-14  ExpressionRecord is a frozen dataclass
          Owner:  brain/development/expression.py
          Check:  dataclasses.fields(ExpressionRecord) is non-empty;
                  ExpressionRecord.__setattr__ on any field raises
                  FrozenInstanceError;
                  same for ExpressionItem, ExpressionShape,
                  ExpressionProvenance, ExpressionFeatureVector,
                  ReadabilityPrediction
          Fixture: covered by I-EXP-03 / I-EXP-05 fixtures (no separate
                   fixture; the structural assertion is reusable)

I-EXP-15  Bridge constructors are pure and do not register callbacks
          Owner:  brain/development/expression.py
          Check:  static-grep: no occurrence of register_callback,
                  on_append, observe, subscribe, watch, or similar
                  hook names within the expression module(s);
                  bridge constructor signatures take a source record
                  and a tick int and return an ExpressionRecord with
                  no other parameters
          Fixture: covered by tools.import_audit + static-grep
                   (no separate fixture)

I-EXP-16  Predictor module has no float / math / round on the score path
          Owner:  brain/development/expression.py
          Check:  static-grep within the predictor section of the
                  module: no occurrence of float(, math., round(,
                  Decimal, complex(;
                  the score function returns a ReadabilityScore whose
                  factory rejects non-Fraction inputs
          Fixture: covered by static-grep + I-EXP-04 fixture
```

### 5.3 OBSERVED rows (+1)

```text
I-EXP-17  Aggregate ExpressionHistory summary view is OBSERVED only
          Owner:  brain/development/expression.py
          Description: expression_history_view exposes count, mean
                  score, max score, and count by source for the
                  current local ExpressionHistory. These aggregates
                  are observation-only diagnostic outputs; they
                  carry no entitlement claim, are not consumed by
                  any developmental layer, are not written to any
                  external sink, and are not visible to
                  tick / PerceptEvent / scenarios / traces / TLICA.
          Note:   OBSERVED rows are descriptive; they do not require
                  a fixture but must be cited from the audit
```

### 5.4 NOT-EXERCISED rows (+1)

```text
I-EXP-18  ExpressionHistory write-to-disk path is NOT-EXERCISED
          Owner:  brain/development/expression.py
          Description: no public helper exists to serialize
                  ExpressionHistory to disk, traces, scenarios, or
                  any external sink. The absence of a write path is
                  an intentional safety property of Phase 3.5. Adding
                  any write path requires a new campaign with its own
                  synthesis / kickoff / corrigenda / catalog patch
                  plan (per corrigenda C9-AMEND-01).
          Note:   NOT-EXERCISED rows assert the explicit absence of a
                  code path; they do not require a runtime fixture
                  but are cited from the audit
```

## 6. Owning Modules and File Budget

New production files (Step 7):

```text
brain/development/expression.py                  (new)
brain/development/fixtures/__init__.py           (already exists; appended)
```

Fixture files (Steps 7-9), each one a single fixture per file in the
project's standard fixture layout:

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
```

Modified files for the Step 6 catalog patch:

```text
INVARIANT_CATALOG.md           (row rows + banners updated)
tools/catalog.py               (expected counts + family entries)
brain/_catalog_ids.py          (generated IDs for I-EXP-01..18)
brain/invariants.py            (pending-registration entries; no
                                runtime invariant code lands in Step 6;
                                runtime registration happens in Steps
                                7-9 with the fixtures)
```

File budget for Phase 3.5 explicitly **excludes**:

```text
brain/ui/*                     (deferred per C10-AMEND-01)
brain/tick.py                  (guarded; no semantic change)
brain/llm/*                    (guarded; no LLM reach)
brain/tlica/*                  (guarded; no runtime promotion)
traces/, scenarios/            (guarded; no schema or content change)
lean_reference/                (guarded; no Lean-bound row added)
```

## 7. Fixture Roster

REQUIRED rows are pinned by fixtures (12 fixtures, one per REQUIRED row).
Some STRUCTURAL rows reuse the dataclass-frozen / static-grep / import-
audit infrastructure and do not need a separate fixture. OBSERVED and
NOT-EXERCISED rows do not require fixtures.

Mapping rows -> fixtures:

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
I-EXP-13  (no fixture; tools.import_audit covers)
I-EXP-14  (no fixture; reuses I-EXP-03 / I-EXP-05 frozen assertions)
I-EXP-15  (no fixture; tools.import_audit + static-grep)
I-EXP-16  (no fixture; static-grep + I-EXP-04)
I-EXP-17  (OBSERVED; no fixture)
I-EXP-18  (NOT-EXERCISED; no fixture)
```

## 8. Count Impact From v0.11

Banner deltas (re-statement from Section 3):

```text
REQUIRED      : +12   (127 -> 139)
STRUCTURAL    :  +4   ( 44 ->  48)
NOT-EXERCISED :  +1   (  4 ->   5)
DEFERRED      :  +0   ( 12 ->  12)
OBSERVED      :  +1   (  7 ->   8)
TOTAL         : +18   (194 -> 212)
```

The patch updates:

```text
- INVARIANT_CATALOG.md: row table additions, banner counters, family
  index
- tools/catalog.py: expected count tuple per category, family entry for
  I-EXP-*
- brain/_catalog_ids.py: generated IDs for I-EXP-01..18 (run
  `python3 -m tools.catalog generate-ids` after row additions land in
  INVARIANT_CATALOG.md)
- brain/invariants.py: pending-registration entries that note each
  row's expected fixture file; runtime registration is added in
  Steps 7-9 with the fixtures themselves
```

The patch does not change banner counts for categories that gain no row.

## 9. Catalog Patch Mechanics

Step 6 (`Apply accepted catalog patch`) sequence:

```text
1. Add the 18 new row entries to INVARIANT_CATALOG.md under a
   "I-EXP-*  Phase 3.5 Expression + ReadabilityPredictor" section.
   Each entry includes ID, status, title, owning module, fixture file
   (or "covered by import-audit" / "OBSERVED" / "NOT-EXERCISED"),
   and a one-paragraph description that:
   - does NOT use the words "correct", "true", "valid", "accurate",
     "good", "quality" to describe what the score asserts
     (per C2-NOTE-01)
   - does NOT use agency-implying language (per C4-AMEND-01)
   - does include the C1-AMEND-01 sentence for the predictor row
     ("This module computes a bounded structural score over a local
     expression item. It does NOT model language. ...")

2. Update INVARIANT_CATALOG.md banner counts to:
   REQUIRED: 139, STRUCTURAL: 48, NOT-EXERCISED: 5, DEFERRED: 12,
   OBSERVED: 8.

3. Update tools/catalog.py expected counts to match.

4. Add pending-registration entries to brain/invariants.py for each
   new row, with `fixture=None` (or the planned fixture filename as a
   string) and `registered=False`. Runtime registration happens in
   Steps 7-9.

5. Run:
       python3 -m tools.catalog counts
   The expected output should report:
       REQUIRED ... ok
       STRUCTURAL ... ok
       NOT-EXERCISED ... ok
       DEFERRED ... ok
       OBSERVED ... ok
   with banners and actuals matching the new totals.

6. Run:
       python3 -m tools.catalog generate-ids
   to generate IDs for I-EXP-01..18 in brain/_catalog_ids.py.

7. Run:
       python3 -m tools.catalog counts
   again to confirm no drift after generate-ids.

8. Commit and push the Step 6 patch with all four modified files in a
   single commit. No fixture file is included in the Step 6 commit;
   fixtures land in Steps 7-9.
```

## 10. Pending Registration Plan

Pending registrations recorded in `brain/invariants.py` at Step 6:

```text
I-EXP-01 ... I-EXP-12        REQUIRED       fixture filename pending
I-EXP-13                     STRUCTURAL     covered by import-audit
I-EXP-14                     STRUCTURAL     covered by frozen-dataclass
                                            assertion (reuses I-EXP-03
                                            / I-EXP-05)
I-EXP-15                     STRUCTURAL     covered by import-audit +
                                            static-grep
I-EXP-16                     STRUCTURAL     covered by static-grep +
                                            I-EXP-04
I-EXP-17                     OBSERVED       documented; no fixture
I-EXP-18                     NOT-EXERCISED  documented; no fixture
```

Registration into the runner happens incrementally in Steps 7-9 as the
implementing modules and fixtures land. Step 11 (`Full gate`) verifies
that all REQUIRED rows are registered and exercised.

## 11. Strict Implementation Order

```text
Step 5   Review gate (this plan accepted by the user / stopper)
Step 6   Apply accepted catalog patch
            -> INVARIANT_CATALOG.md, tools/catalog.py,
               brain/_catalog_ids.py, brain/invariants.py
Step 7   Implement expression core
            -> brain/development/expression.py (frozen dataclasses,
               ExpressionSource, ExpressionItem, ExpressionShape,
               ExpressionProvenance, ExpressionFeatureVector,
               ExpressionRecord, bridge constructors)
            -> fixtures for I-EXP-01, I-EXP-02, I-EXP-03, I-EXP-07,
               I-EXP-08
Step 8   Implement ReadabilityPredictor
            -> brain/development/expression.py (ReadabilityScore,
               ReadabilityPrediction, ReadabilityPredictor)
            -> fixtures for I-EXP-04, I-EXP-05, I-EXP-09,
               I-EXP-10, I-EXP-11, I-EXP-12
Step 9   Implement ExpressionHistory and local summaries
            -> brain/development/expression.py (ExpressionHistory,
               append_expression_record, expression_history_view)
            -> fixtures for I-EXP-06
            -> OBSERVED row I-EXP-17 cited from view docstring
Step 10  SKIPPED  (UI integration deferred per C10-AMEND-01)
Step 11  Full gate (catalog counts, citations verify, import audit,
                    invariants run, check_all.sh)
Step 12  Post-completion audit
            -> PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
            -> verdict PASS / PASS WITH PATCHES / BLOCKED
```

## 12. Open Decisions

The plan records no blocking open decisions. The following are
**recorded** non-blocking decisions (the implementation may proceed
without re-opening the corrigenda):

```text
D1  EXPRESSION_TEXT_MAX_LEN value:
        proposed 1024; final value selected at Step 7 within the range
        [256, 4096]. Any value in that range is consistent with
        I-EXP-02 and the bounded-printable invariant.

D2  EXPRESSION_TOKEN_MAX_COUNT value:
        proposed 256; final value selected at Step 7 within the range
        [64, 1024]. Any value in that range is consistent with
        I-EXP-02.

D3  EXPRESSION_HISTORY_MAX_ENTRIES value:
        proposed 128; final value selected at Step 9 within the range
        [16, 1024]. Any value in that range is consistent with
        I-EXP-06.

D4  SHAPE_BALANCE_TARGET value:
        proposed Fraction(1, 5); final value selected at Step 7 from
        {Fraction(1, 8), Fraction(1, 6), Fraction(1, 5), Fraction(1, 4)}.

D5  W_PRINTABLE, W_SHAPE, W_DISTINCT, W_REPEAT weights:
        proposed Fraction(1, 2), Fraction(1, 4), Fraction(1, 4),
        Fraction(1, 4) respectively; final values selected at Step 8.
        Constraint: W_PRINTABLE + W_SHAPE + W_DISTINCT == Fraction(1)
        and W_REPEAT in [0, Fraction(1, 2)].

D6  LENGTH_CAP_THRESHOLD value:
        proposed half of EXPRESSION_TEXT_MAX_LEN; final value selected
        at Step 8.

D7  PRINTABLE_FLOOR / PRINTABLE_CAP / LENGTH_CAP / RESERVED_CAP:
        all module-frozen Fractions, final values selected at Step 8
        within ranges that preserve the anti-Goodhart rules. Any
        choice satisfying the rules is acceptable.
```

None of these decisions changes a row's status, a row's title, or the
count delta in Section 3. They are implementation parameter choices.

## 13. Stop Conditions

Stop and escalate (do not proceed past Step 5) if any of the following
become true:

```text
- the plan is asked to add a row that uses agency-implying language
  (violates C4-AMEND-01)
- the plan is asked to add a row whose description claims the score
  asserts "correctness", "truth", or "validity" of the expressed
  content (violates C2-NOTE-01)
- the plan is asked to authorize a UI inspection pane in this
  campaign (violates C10-AMEND-01)
- the plan is asked to authorize a serialization path for
  ExpressionHistory (violates C9-AMEND-01)
- the plan is asked to weaken any existing I-* row (violates the
  campaign-level guardrail)
- the plan is asked to add an external dependency, an LLM call, a
  shell / subprocess / network call, or a file write path (violates
  the campaign hard boundaries)
- the plan is asked to add scenario / trace schema changes or
  PerceptEvent / tick() promotion from expression evidence (violates
  the campaign hard boundaries)
- the plan is asked to promote a row from OBSERVED / STRUCTURAL to
  REQUIRED without a new corrigenda revision (violates C8)
```

If any stop condition triggers, the plan is **not** accepted by Step 5,
and the corrigenda must be re-opened before Step 6 may run.

## 14. Acceptance Criteria

The plan is accepted by Step 5 when:

```text
- all 18 rows in Section 5 are reviewed and their statuses and titles
  are acceptable to the user
- the count delta in Section 3 is reconciled (REQUIRED +12,
  STRUCTURAL +4, NOT-EXERCISED +1, OBSERVED +1)
- the file budget in Section 6 is acceptable (no brain/ui/* files;
  no LLM / scenario / trace / TLICA files)
- the strict implementation order in Section 11 is acceptable
  (Step 10 SKIPPED)
- no stop condition in Section 13 has triggered
- the open decisions in Section 12 are deferred to their implementing
  steps and do not require pre-implementation resolution
```

When accepted, Step 6 may run with the four modified files exactly as
listed in Section 6. The implementation steps (7-9) follow with the
fixture roster in Section 7. Step 11 runs the full gate and Step 12
produces the post-completion audit.
