# PHASE3_7_TEXT_STREAM_INGRESS_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in `PHASE3_7_TEXT_STREAM_INGRESS_CORRIGENDA.md` to
concrete catalog rows, statuses, file budget, count delta, fixture
roster, and pending-registration mechanics. This is a planning artifact
only. It does not apply catalog rows, edit `tools/catalog.py`, add
runtime modules, add fixtures, change generated catalog IDs, alter
`INVARIANT_CATALOG.md`, or change `brain/invariants.py`.

Verdict for the Step 13 review gate:

```text
COHERENT — READY FOR REVIEW GATE
```

## 2. Baseline

```text
Catalog version:  v0.13
REQUIRED:        147
STRUCTURAL:       52
NOT-EXERCISED:     6
DEFERRED:         12
OBSERVED:          9
Total tabular:   226
```

Required latest audit:

```text
PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md   PASS
```

## 3. Patch impact

```text
+ 11 REQUIRED
+  4 STRUCTURAL
+  1 NOT-EXERCISED
+  0 DEFERRED
+  1 OBSERVED
```

Expected counts after the accepted patch:

```text
Catalog version:  v0.14
REQUIRED:        158
STRUCTURAL:       56
NOT-EXERCISED:     7
DEFERRED:         12
OBSERVED:         10
Total tabular:   243
```

## 4. Row family thesis

Row family:

```text
I-STRM-*
```

Core commitments:

```text
Text Stream Ingress is a bounded local substrate over operator/system/
  probe-echo/generated raw text, deterministic and exact, with copy-on-
  write history bounds and structural-only feature extraction.

Text Stream Ingress is not language, not truth, not agency, not Mode B,
  not a UI surface in Phase 3.7, and not a model-backed surface (the
  explicit Phase 3.8b LLM Runtime Toggle owns the model-backed seam).

TextStreamChunk fields are bounded printable text and metadata; over-
  bound text raises (no silent truncation on the chunk text path);
  COGITO_ID is hard-rejected on every identifier and on text.

TextStreamHistory is a frozen record with copy-on-write append and a
  bounded ring (oldest dropped on full append).

StreamFeatureVector is a frozen record of exact int counts; no float,
  no round, no math.

SegmentCandidate is a (start, end, segment_kind) span with a closed
  vocabulary {"line", "delimited_span", "whitespace_run"}; it carries
  no payload text and is not a parse tree.

StreamPattern is recurrence-backed structural evidence; it carries no
  PRESERVE / DAMAGE / PCE / Act / ModeOp / AgencyWitness field; the
  recurrence_count saturates at STREAM_PATTERN_RECURRENCE_MAX.

StreamPromotionCandidate carries non-reserved target_content_id, source,
  chunk_id (caller contract), bounded text, optional pattern_id, and
  bounded provenance; it is not a PerceptEvent; the substrate
  constructor never calls tick(), never appends to
  OperatorSession.event_queue, and never mutates BrainState or any
  source history.

Aggregate text-stream history walk is OBSERVED only; the walk is a
  Python frozen dataclass; no serialization.

brain/ui/* integration is DEFERRED to Phase 3.8 (analog of
  C10-AMEND-01 / C13-AMEND-01).

Text-stream save / export is NOT-EXERCISED placeholder.
```

## 5. Row table

All rows use the `I-STRM-*` family. Owning module is
`brain/development/text_stream.py` unless noted.

### 5.1 REQUIRED rows

```text
I-STRM-01  TextStreamSource is a finite closed enumeration
           Fixture: text_stream_source_enum_closed.py

I-STRM-02  TextStreamChunk is bounded printable + COGITO_ID rejected
           Fixture: text_stream_chunk_bounded.py

I-STRM-03  TextStreamHistory is copy-on-write and bounded
           Fixture: text_stream_history_cow_bounded.py

I-STRM-04  StreamFeatureVector is deterministic and exact
           Fixture: text_stream_feature_vector_exact.py

I-STRM-05  SegmentCandidate is structural (closed-vocabulary kind +
           bounded span)
           Fixture: text_stream_segment_candidate.py

I-STRM-06  StreamPattern requires recurrence_count >= MIN; carries no
           truth/PRESERVE/agency field
           Fixture: text_stream_pattern_recurrence.py

I-STRM-07  StreamPromotionCandidate requires explicit non-reserved
           target_content_id and explicit source/provenance/chunk_id;
           is not a PerceptEvent
           Fixture: text_stream_promotion_candidate.py

I-STRM-08  Stream operations do not mutate
           BrainState / MSI / PtCns / ContentRegistry
           Fixture: text_stream_no_brainstate_mutation.py

I-STRM-09  Stream operations do not mutate any existing source history
           (Output / Worldlet / ProtoBasic / Expression / Transcript)
           Fixture: text_stream_no_source_history_mutation.py

I-STRM-10  Stream operations do not call tick() and do not append to
           OperatorSession.event_queue; promotion is /stream-promote
           only (Phase 3.8)
           Fixture: text_stream_no_tick.py

I-STRM-11  Anti-growth: repeated/huge chunks do not inflate
           recurrence_count above STREAM_PATTERN_RECURRENCE_MAX; no
           silent truncation on the chunk text path
           Fixture: text_stream_anti_growth.py
```

### 5.2 STRUCTURAL rows

```text
I-STRM-12  Text stream module has no I/O / network / file / shell /
           LLM / TLICA / tick / curses import
           Fixture: text_stream_static_audit.py

I-STRM-13  Stream records are frozen dataclasses
           Fixture: text_stream_chunk_bounded.py and
                    text_stream_feature_vector_exact.py

I-STRM-14  Text stream module has no float / round / math on the
           count / statistic path
           Fixture: text_stream_static_audit.py

I-STRM-15  Stream constructors are pure and register no callbacks
           Fixture: text_stream_static_audit.py
```

### 5.3 OBSERVED row

```text
I-STRM-16  Aggregate text-stream history walk is inspectable
           Fixture: none; cited from the Phase 3.7 audit.
```

### 5.4 NOT-EXERCISED row

```text
I-STRM-17  Text-stream save / export path is NOT-EXERCISED
           Fixture: none.
```

## 6. Fixture roster

```text
I-STRM-01  text_stream_source_enum_closed.py
I-STRM-02  text_stream_chunk_bounded.py
I-STRM-03  text_stream_history_cow_bounded.py
I-STRM-04  text_stream_feature_vector_exact.py
I-STRM-05  text_stream_segment_candidate.py
I-STRM-06  text_stream_pattern_recurrence.py
I-STRM-07  text_stream_promotion_candidate.py
I-STRM-08  text_stream_no_brainstate_mutation.py
I-STRM-09  text_stream_no_source_history_mutation.py
I-STRM-10  text_stream_no_tick.py
I-STRM-11  text_stream_anti_growth.py
I-STRM-12  text_stream_static_audit.py
I-STRM-13  text_stream_chunk_bounded.py +
           text_stream_feature_vector_exact.py
I-STRM-14  text_stream_static_audit.py
I-STRM-15  text_stream_static_audit.py
I-STRM-16  OBSERVED; no fixture
I-STRM-17  NOT-EXERCISED; no fixture
```

Fixture file delta: **+12** files. The fixture roster total moves from
`57` to `69`.

```text
brain/development/fixtures/text_stream_source_enum_closed.py
brain/development/fixtures/text_stream_chunk_bounded.py
brain/development/fixtures/text_stream_history_cow_bounded.py
brain/development/fixtures/text_stream_feature_vector_exact.py
brain/development/fixtures/text_stream_segment_candidate.py
brain/development/fixtures/text_stream_pattern_recurrence.py
brain/development/fixtures/text_stream_promotion_candidate.py
brain/development/fixtures/text_stream_no_brainstate_mutation.py
brain/development/fixtures/text_stream_no_source_history_mutation.py
brain/development/fixtures/text_stream_no_tick.py
brain/development/fixtures/text_stream_anti_growth.py
brain/development/fixtures/text_stream_static_audit.py
```

## 7. File budget

New production file:

```text
brain/development/text_stream.py
```

New fixture files (12): see §6.

Modified files for Step 14 catalog patch:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Explicitly excluded (no Step in Phase 3.7 touches these):

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
brain/development/reflective.py
brain/ui/transcript.py
```

## 8. Catalog patch mechanics (Step 14)

```text
1. Add the 17 new I-STRM-* row entries to INVARIANT_CATALOG.md under
   a new "### Phase 3.7 Text Stream Ingress developmental
   invariants" section, placed after the Phase 3.6 Reflective
   Inspection section and before "### Meta / runner integrity".
2. Update the INVARIANT_CATALOG.md banner with a v0.14 entry.
3. Update INVARIANT_CATALOG.md banner counts to REQUIRED 158,
   STRUCTURAL 56, NOT-EXERCISED 7, DEFERRED 12, OBSERVED 10.
4. Update the fixture roster table with the 12 new fixture files;
   bump "57 fixtures total" to "69 fixtures total" and extend the
   incremental-introduction sentence with ", and Phase 3.7".
5. Update the "Summary counts" section to v0.14.
6. Update tools/catalog.py EXPECTED_COUNTS to match.
7. Add _PHASE3_7_PENDING_ROWS to brain/invariants.py using the
   existing pending-row pattern.
8. Run python3 -m tools.catalog counts.
9. Run python3 -m tools.catalog generate-ids.
10. Run python3 -m tools.catalog counts again.
11. Commit and push.
```

Row descriptions must not claim Text Stream Ingress asserts truth,
validity, accuracy, quality, social success, intelligence, agency,
language understanding, parse-tree semantics, or Mode B planning
capability.

Required disclaimer to appear in the I-STRM-06 row description:

```text
StreamPattern is recurrence-backed structural evidence. It does NOT
enter PtCns.evaluate, does NOT contribute to MSI.contents, and does
NOT carry PRESERVE / DAMAGE / PCE / ProjectedPCE / Act / ModeOp /
AgencyWitness fields.
```

Required disclaimer to appear in the I-STRM-07 row description:

```text
StreamPromotionCandidate is not a PerceptEvent. The substrate never
appends candidates to OperatorSession.event_queue and never calls
tick(). The Phase 3.8 /stream-promote route owns event-queue append.
```

## 9. Pending registration mechanics (Step 14)

Step 14 must use the established `brain/invariants.py` pending-row
pattern (same shape as `_PHASE3_5_PENDING_ROWS` /
`_PHASE3_6_PENDING_ROWS`):

```python
_PHASE3_7_PENDING_ROWS: dict[str, str] = {
    "I-STRM-01": "REQUIRED",
    "I-STRM-02": "REQUIRED",
    "I-STRM-03": "REQUIRED",
    "I-STRM-04": "REQUIRED",
    "I-STRM-05": "REQUIRED",
    "I-STRM-06": "REQUIRED",
    "I-STRM-07": "REQUIRED",
    "I-STRM-08": "REQUIRED",
    "I-STRM-09": "REQUIRED",
    "I-STRM-10": "REQUIRED",
    "I-STRM-11": "REQUIRED",
    "I-STRM-12": "STRUCTURAL",
    "I-STRM-13": "STRUCTURAL",
    "I-STRM-14": "STRUCTURAL",
    "I-STRM-15": "STRUCTURAL",
}

def _make_phase3_7_pending_check(row_id: str) -> Callable[[], None]:
    def _check() -> None:
        raise NotImplementedError(
            f"{row_id} is registered for Phase 3.7 catalog coverage "
            "but its runtime implementation has not landed yet"
        )
    _check.__name__ = f"check_{row_id.replace('-', '_')}_pending"
    return _check

for _row_id, _status in _PHASE3_7_PENDING_ROWS.items():
    register(_row_id, status=_status)(_make_phase3_7_pending_check(_row_id))
```

I-STRM-16 (OBSERVED) and I-STRM-17 (NOT-EXERCISED) do not participate in
I-CAT-01 coverage and are not pending entries.

## 10. Strict implementation order

```text
Step 13  Review gate (this artifact must be accepted before Step 14)
Step 14  Apply accepted catalog patch
Step 15  Implement text stream core
            -> brain/development/text_stream.py
            -> text_stream_source_enum_closed.py
            -> text_stream_chunk_bounded.py
            -> text_stream_history_cow_bounded.py
            -> text_stream_feature_vector_exact.py
            -> text_stream_no_brainstate_mutation.py
            -> text_stream_no_source_history_mutation.py
            -> text_stream_no_tick.py
            -> text_stream_static_audit.py
            -> text_stream_anti_growth.py
            -> drain pending I-STRM-01..04, 08..15 in brain/invariants.py
            -> add the corresponding fixture modules to FIXTURE_MODULES
Step 16  Implement segment / pattern / promotion-candidate layer
            -> extend brain/development/text_stream.py
            -> text_stream_segment_candidate.py
            -> text_stream_pattern_recurrence.py
            -> text_stream_promotion_candidate.py
            -> drain pending I-STRM-05, 06, 07 in brain/invariants.py
            -> add the three remaining fixture modules to
               FIXTURE_MODULES
Step 17  Phase 3.7 full audit
            -> PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md
Step 18  Review gate before Phase 3.8 begins
```

The catalog plan grants Steps 15 and 16 the option to bundle their
respective fixture files in a single commit, mirroring the Phase 3.5
Step 7 / Phase 3.6 Step 7 allowances.

## 11. Locked module-level constants

The following constants will be module-level in
`brain/development/text_stream.py` and not re-derivable at call time:

```text
STREAM_TEXT_MAX_LEN              = 1024
STREAM_PROVENANCE_MAX_LEN        = 64
STREAM_HISTORY_MAX_CHUNKS        = 256
STREAM_SEGMENTS_MAX              = 32
STREAM_PATTERN_RECURRENCE_MIN    = 2
STREAM_PATTERN_RECURRENCE_MAX    = 256
STREAM_PATTERN_SIG_MAX           = 16
STREAM_PROMOTION_MAX             = 64
ALLOWED_SEGMENT_KINDS            = ("line", "delimited_span",
                                    "whitespace_run")
```

Implementation parameters may be selected inside the ranges locked by
the corrigenda. Changing any of these values after Step 14 lands
requires a fresh corrigenda update.

## 12. Stop conditions

Stop and reopen corrigenda if any request would:

```text
allow Mode B planning surface
allow self-modification
authorize a UI integration pane in Phase 3.7
authorize TextStreamHistory serialization / weaving into traces or
  scenarios
authorize aggregate "quality" / "intelligence" / "social-success"
  stream score
authorize a real LLM-backed source kind (Phase 3.8b reuses the
  existing LLMClient seam, not a new TextStreamSource)
weaken any existing I-* row
add an external dependency, LLM call, shell/subprocess/network call,
  or file write path
change scenario / trace schema
promote stream evidence into PerceptEvent / tick() / TLICA runtime
  outside the explicit Phase 3.8 /stream-promote route
promote an OBSERVED / STRUCTURAL row to REQUIRED without new
  corrigenda
add a MODEL TextStreamSource without an authorized future campaign
allow the substrate to append to OperatorSession.event_queue
```

## 13. Acceptance criteria for the Step 13 review gate

The plan is accepted when:

```text
all 17 rows are acceptable
the count delta is reconciled: +11 REQUIRED, +4 STRUCTURAL,
  +1 NOT-EXERCISED, +1 OBSERVED
the +12 fixture roster (one shared text_stream_static_audit.py
  handling I-STRM-12, I-STRM-14, I-STRM-15; one shared bounded /
  feature-vector pair handling I-STRM-13) is acceptable
the file budget excludes brain/ui/*, LLM, scenario, trace, TLICA,
  brain/development/reflective.py, and the other developmental
  modules
Step 14 pending mechanics match the established
  _PHASE3_7_PENDING_ROWS pattern
brain/ui/* integration remains deferred to Phase 3.8
the locked module-level constants in §11 are acceptable
no stop condition has triggered
```

When accepted, Step 14 may run. The patch remains a catalog/planning
patch; runtime and fixtures land only in Steps 15 and 16.
