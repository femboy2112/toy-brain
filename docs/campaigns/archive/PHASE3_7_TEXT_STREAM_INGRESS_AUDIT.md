# PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md

## Verdict

```text
PASS
```

The Phase 3.7 Text Stream Ingress campaign landed the accepted v0.14
catalog patch (`I-STRM-01..I-STRM-17`) and the corresponding bounded
local runtime layer without scope creep or kernel-boundary breach. All
15 registered `I-STRM-*` rows are green, the full gate is green, and
the OBSERVED / NOT-EXERCISED rows are documented rather than promoted.

## Scope of audit

- v0.14 catalog patch (`I-STRM-01..I-STRM-17`) — Step 14
- `brain/development/text_stream.py` (production module) — Steps 15 + 16
- Phase 3.7 fixture files under
  `brain/development/fixtures/text_stream_*.py` (12 new fixtures)
- pending-row drain in `brain/invariants.py`
  (`_PHASE3_7_PENDING_ROWS` now empty)
- guardrails and stop conditions enumerated in
  `PHASE3_7_TEXT_STREAM_INGRESS_CATALOG_PATCH_PLAN.md` section 12

## 1. Scope creep

```text
No
```

The implementation:

- did not introduce Mode B planning or any planner / search / replay
  buffer / future-state model / action selector / goal / intention
- did not introduce self-modification of `BrainState`, `MSI`, `PtCns`,
  or the content registry
- did not introduce a natural-language teacher / corrector, parser, or
  social model
- did not call any real LLM client, subprocess, shell, or network I/O
  (the explicit Phase 3.8b LLM Runtime Toggle owns the model-backed
  seam)
- did not write any file (no save / export / serialization path landed)
- did not change scenario, trace, or catalog schemas beyond the planned
  rows
- did not authorize a Phase 3.7 UI integration pane (deferred to
  Phase 3.8 per analog `C13-AMEND-01`)
- did not promote any text-stream evidence through `PerceptEvent` or
  `tick()` (the Phase 3.8 `/stream-promote` route owns event-queue
  append)
- did not mutate `BrainState`, `ScalarProfile`, `MSI`, `PtCns`,
  `ContentRegistry`, `OutputHistory`, `WorldletHistory`,
  `ProtoBasicHistory`, `ExpressionHistory`, `OperatorTranscript`, or
  `OperatorSession.event_queue`
- did not add an external dependency (standard library plus the
  existing `brain.development.history` import only)

`brain/development/text_stream.py` imports only `dataclasses`, `enum`,
`fractions`, `typing`, and `brain.development.history`. It does not
import `brain.tlica`, `brain.ui`, `brain.llm`, `brain.tick`, or
`curses`. The reserved cogito sentinel is duplicated locally as
`_COGITO_RESERVED_ID` so that text_stream.py satisfies I-STRM-12 (no
`brain.tlica` import); the
`text_stream_chunk_bounded.py` fixture asserts parity with
`brain.tlica.profile.COGITO_ID` at fixture import time, so any
divergence fails the runner immediately rather than silently masking
the reservation.

## 2. Row registration

```text
Catalog rows added: 17 (I-STRM-01..I-STRM-17)
  +11 REQUIRED     (I-STRM-01..I-STRM-11)
  + 4 STRUCTURAL   (I-STRM-12..I-STRM-15)
  + 1 OBSERVED     (I-STRM-16 — documentation-only; no registered check)
  + 1 NOT-EXERCISED (I-STRM-17 — placeholder for save / export policy)

Registered runtime checks: 15
  I-STRM-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11 (REQUIRED)
  I-STRM-12, 13, 14, 15 (STRUCTURAL)

I-CAT-01 audit: pass (REQUIRED ∪ STRUCTURAL ⊆ registered)
_PHASE3_7_PENDING_ROWS: empty
```

`tools.catalog counts` confirms banner = actual = expected for all five
status buckets at the v0.14 expansion (`158 / 56 / 7 / 12 / 10`).

## 3. Boundedness

```text
Maintained
```

`brain/development/text_stream.py` locks bounded ranges (corrigenda-
locked, plan section 11):

```text
STREAM_TEXT_MAX_LEN              1024 chars
STREAM_PROVENANCE_MAX_LEN          64 chars
STREAM_HISTORY_MAX_CHUNKS         256 chunks
STREAM_SEGMENTS_MAX                32 segments per chunk
STREAM_PATTERN_RECURRENCE_MIN       2
STREAM_PATTERN_RECURRENCE_MAX     256
STREAM_PATTERN_SIG_MAX             16 signature entries
STREAM_PROMOTION_MAX               64
ALLOWED_SEGMENT_KINDS           ("line", "delimited_span",
                                  "whitespace_run")
```

Every text-stream record enforces these bounds at `__post_init__`. The
following are rejected at construction time:

- text over `STREAM_TEXT_MAX_LEN` (I-STRM-11; no silent truncation)
- provenance over `STREAM_PROVENANCE_MAX_LEN`
- non-printable text (allowing only `\n` and `\t` as raw separators)
- empty or non-printable identifiers (`chunk_id`, `candidate_id`,
  `pattern_id`, `target_content_id`)
- `recurrence_count` below `STREAM_PATTERN_RECURRENCE_MIN`
- `recurrence_count` above `STREAM_PATTERN_RECURRENCE_MAX` on direct
  `StreamPattern` construction; `make_stream_pattern` saturates instead
- `signature` empty, or over `STREAM_PATTERN_SIG_MAX`, or containing
  non-printable / over-length entries
- `segment_kind` outside `ALLOWED_SEGMENT_KINDS`
- `start < 0`, `end < 0`, or `end < start` on `SegmentCandidate`

The `text_stream_anti_growth.py` fixture (I-STRM-11) verifies all three
anti-growth properties: text over MAX raises, history never grows above
MAX under arbitrary append, and `make_stream_pattern` saturates while
direct over-MAX construction raises.

## 4. Copy-on-write behavior

```text
Maintained
```

`TextStreamHistory` is a frozen dataclass with a tuple of chunks. The
`append` method:

- returns a new `TextStreamHistory` rather than mutating in place
- preserves the prior chunks exactly when under the bound
- drops the oldest chunk before append when `len(chunks) >=
  STREAM_HISTORY_MAX_CHUNKS`
- never silently extends past the bound

The `text_stream_history_cow_bounded.py` fixture (I-STRM-03) constructs
a history, appends one chunk, asserts the original is unmodified,
fills to exactly `STREAM_HISTORY_MAX_CHUNKS`, performs one more append,
verifies the length is still capped and that the oldest chunk has been
dropped, and confirms construction-time rejection of an over-bound
tuple input.

## 5. COGITO_ID defenses

```text
Maintained
```

The cogito sentinel reservation holds for every text-stream identifier
and for raw text content:

- `TextStreamChunk.chunk_id == COGITO_ID` raises I-STRM-02
- `TextStreamChunk.text == COGITO_ID` raises I-STRM-02
- `TextStreamChunk.provenance == COGITO_ID` raises I-STRM-02 (via the
  bounded-printable helper)
- `StreamPattern.pattern_id == COGITO_ID` raises I-STRM-06
- `StreamPromotionCandidate.target_content_id == COGITO_ID` raises
  I-STRM-07
- `StreamPromotionCandidate.text == COGITO_ID` raises I-STRM-07

The fixture `text_stream_chunk_bounded.py` imports the real
`brain.tlica.profile.COGITO_ID` and asserts at fixture import time that
the text-stream module's local `_COGITO_RESERVED_ID` matches it. The
fixture then passes `COGITO_ID` as each identifier / text input and
asserts each constructor raises with the appropriate row tag.

## 6. No direct tick route / no event-queue append

```text
Maintained
```

`brain/development/text_stream.py`:

- does not import `brain.tick` or any `brain.tlica` module
- does not import `brain.ui.session` or any `OperatorSession` /
  `OperatorEventQueue` surface
- never calls a function literally named `tick`
- never names `event_queue.append` or any `*.tick` call target

The static portion of `text_stream_no_tick.py` (I-STRM-10) AST-checks
the production module for forbidden imports and call names. The
behavioral portion constructs an `OperatorSession`, captures
`session.event_queue` identity and `snapshot()` before any text-stream
work, runs a complete walk (chunk construction, history append, feature
extraction, segmentation, pattern construction, promotion candidate
construction), and asserts the queue identity is the same object, the
queue length is unchanged, and the snapshot tuple is equal. The
session's `tick_counter` and `latest_tick` fields are also unchanged.

`StreamPromotionCandidate` carries no `Act`, `ModeOp`,
`AgencyWitness`, `feasibleProjectedPCE`, `tick`, `event_queue_append`,
or `initial_rho` field. The `text_stream_promotion_candidate.py`
fixture (I-STRM-07) asserts absence of these fields and confirms the
candidate is not a `PerceptEvent` — promotion to the event queue is
exclusively the Phase 3.8 `/stream-promote` route.

## 7. Source-history non-mutation (positive evidence)

```text
Maintained
```

The `text_stream_no_source_history_mutation.py` fixture (I-STRM-09)
constructs `OutputHistory` and `ExpressionHistory` from existing
Phase 3.2 / Phase 3.5 surfaces, records `id(...)` and the underlying
tuples before any text-stream work, runs the full text-stream walk
(chunk construction, history append, feature extraction, segmentation,
pattern construction, promotion candidate construction), and asserts:

- `id(out)` and `id(expr)` are unchanged
- `len(out.impulses)` and `len(expr.records)` are unchanged
- the underlying tuples `out.impulses` and `expr.records` are the same
  object as before

The text-stream constructors do not call any source-history mutator;
they only read attributes via standard attribute access on existing
records.

`text_stream_no_brainstate_mutation.py` (I-STRM-08) captures kernel
identities (`profile`, `msi`, `ptcns`, `registry`), their underlying
values, and the registry texts before and after a full text-stream
walk, and confirms equality on every snapshot. No `tick()` is called
and no `PerceptEvent` is emitted.

## 8. Static-audit module discipline

```text
Maintained
```

The `text_stream_static_audit.py` fixture covers three structural
rows:

- I-STRM-12: AST-walks `text_stream.py` and rejects imports of `os`,
  `subprocess`, `socket`, `urllib`, `http`, `requests`, `pathlib`,
  `tempfile`, `shutil`, `curses`, `brain.llm`, every concrete
  `brain.tlica.*` submodule, `brain.tick`, and `brain.ui`. The
  permitted imports are exactly `dataclasses`, `enum`, `fractions`,
  `typing`, and `brain.development.history`.
- I-STRM-14: walks every count / statistic-path function
  (`extract_stream_features`, `extract_segment_candidates`,
  `make_stream_pattern`, `make_stream_promotion_candidate`,
  `make_text_stream_chunk`, `_require_int_nonneg`,
  `_require_bounded_printable`) and every record's `__post_init__`,
  and asserts no `float(...)`, `round(...)`, or `math.*` call appears.
  Also asserts `text_stream.py` does not import `math`.
- I-STRM-15: rejects disallowed module-level statements, the call set
  `{"atexit.register", "signal.signal", "open"}`, any `atexit.` or
  `signal.` module-level call, and any call name containing
  `"brain.ui"`, `"brain.tlica"`, `"brain.llm"`, or `"brain.tick"`.

## 9. Mode B / truth / language / social / agency boundary

```text
Maintained
```

The text-stream substrate:

- does not plan, replay, or set goals (no Mode B planning surface)
- does not assert truth, validity, accuracy, ground-truth, or external
  reality alignment (no truth claim)
- does not parse, generate, classify intent, model speakers, or model
  conversations (no language claim)
- does not model social register, audience, intelligence, or success
  (no social / intelligence claim)
- does not authorize self-modification or self-update of any TLICA or
  developmental store

`StreamPattern` is recurrence-backed structural evidence. It does NOT
enter `PtCns.evaluate`, does NOT contribute to `MSI.contents`, and
does NOT carry `PRESERVE` / `DAMAGE` / `PCE` / `ProjectedPCE` / `Act`
/ `ModeOp` / `AgencyWitness` fields. The
`text_stream_pattern_recurrence.py` fixture (I-STRM-06) asserts the
absence of these fields by attribute introspection.

`SegmentCandidate` is a `(start, end, segment_kind)` span over the
closed vocabulary `("line", "delimited_span", "whitespace_run")` with
no `text`, `tokens`, `payload`, `parse_tree`, `ast`, `language`,
`meaning`, `truth`, `preserve`, `damage`, `readability_score`, `act`,
`agency_witness`, or `tick_callback` field. The
`text_stream_segment_candidate.py` fixture (I-STRM-05) asserts the
absence of every such field.

`StreamPromotionCandidate` is not a `PerceptEvent`. The substrate
never appends candidates to `OperatorSession.event_queue` and never
calls `tick()`. The Phase 3.8 `/stream-promote` route owns event-queue
append.

## 10. Frozen-record contract

```text
Maintained
```

All six text-stream records are slot-using frozen dataclasses:

- `TextStreamChunk`
- `TextStreamHistory`
- `StreamFeatureVector`
- `SegmentCandidate`
- `StreamPattern`
- `StreamPromotionCandidate`

`text_stream_feature_vector_exact.py` (I-STRM-13) instantiates one of
each, asserts `is_dataclass(record)` and
`type(record).__dataclass_params__.frozen` for each, and verifies that
`FrozenInstanceError` is raised on attempted attribute mutation for
`StreamFeatureVector`, `SegmentCandidate`, `StreamPattern`, and
`StreamPromotionCandidate`. `text_stream_chunk_bounded.py` performs
the same `FrozenInstanceError` probe on `TextStreamChunk`.

## 11. Kernel boundary

```text
Maintained
```

Phase 3.7 evidence flows strictly one-way:

```text
raw text (operator / system / probe-echo / generated)
    -> TextStreamChunk
    -> TextStreamHistory
    -> StreamFeatureVector / SegmentCandidate / StreamPattern
    -> StreamPromotionCandidate (record only; not yet a PerceptEvent)
```

The reverse path is closed:

```text
StreamPromotionCandidate ->
   BrainState / MSI / PtCns / registry / tick / PerceptEvent /
   OperatorSession.event_queue / traces / scenarios / source histories
   / brain.ui / brain.llm / brain.tlica            NOT ALLOWED
```

No `brain/tick.py`, `brain/tlica/`, `brain/llm/`, `brain/ui/`,
`scenarios/`, `traces/`, `lean_reference/`,
`brain/development/expression.py`, `brain/development/reflective.py`,
`brain/development/output.py`, `brain/development/worldlet.py`, or
`brain/development/repl.py` content was modified during the Step 14,
15, or 16 commits.

## 12. OBSERVED and NOT-EXERCISED rows

`I-STRM-16` (OBSERVED) is documented here as a structural sketch of an
aggregate `TextStreamHistory` walk:

```text
chunks_total                       len(history.chunks)
distinct_chunk_id_count            len({c.chunk_id for c in chunks})
counts_by_source                   source -> chunk-count mapping
feature_aggregate                  per-chunk StreamFeatureVector list
                                   (text_length / printable_length /
                                    line_count / whitespace_run_count /
                                    distinct_char_count summed exactly)
segment_counts_by_kind             segment_kind -> int count mapping
pattern_counts                     int count of distinct patterns
promotion_counts                   int count of promotion candidates
```

The walk uses only `int` and `Fraction` arithmetic and produces no
aggregate quality / intelligence / social-success score and no truth
claim. Anti-growth sketch: an arbitrary stream of repeated identical
chunks has `chunks_total == STREAM_HISTORY_MAX_CHUNKS` after the bound
is reached (oldest dropped); `recurrence_count` saturates at
`STREAM_PATTERN_RECURRENCE_MAX`; segment counts per chunk stay at most
`STREAM_SEGMENTS_MAX`. None of these saturations inflates downstream.

`I-STRM-17` (NOT-EXERCISED) remains a policy placeholder: no
`TextStreamHistory`, `StreamPattern`, or `StreamPromotionCandidate`
serialization, save, export, or write-to-disk path exists in this
campaign. Any future write path requires reviewed policy, dedicated
catalog rows, fixtures under bounded conditions, and a stop condition.

## 13. Full gate

```text
python3 -m tools.catalog counts        ->  158 / 56 / 7 / 12 / 10  ok
python3 -m tools.citations verify      ->  100 citations resolved
python3 -m tools.import_audit          ->  I-PCE-05 clean
python3 -m brain.invariants run        ->  221 rows checked
                                          REQUIRED green:   158 / 158
                                          STRUCTURAL green:  56 /  56
                                          OBSERVED pass:      7 / 0 fail
                                          gate failures:      0
bash tools/check_all.sh                ->  All checks passed.
```

The 7-vs-10 OBSERVED count is by design: `I-EXP-17`, `I-REF-13`, and
`I-STRM-16` are documentation-only and not registered, so seven
OBSERVED rows appear in the run summary.

## 14. Hard-boundary file audit

```text
brain/tlica/                          unchanged
lean_reference/                       unchanged
traces/                               unchanged
scenarios/                            unchanged
brain/tick.py                         unchanged
brain/llm/                            unchanged
brain/ui/                             unchanged
brain/development/expression.py       unchanged
brain/development/reflective.py       unchanged
brain/development/output.py           unchanged
brain/development/worldlet.py         unchanged
brain/development/repl.py             unchanged
brain/development/proto_pattern.py    unchanged
brain/development/proto_content.py    unchanged
brain/development/promotion.py        unchanged
brain/development/probes.py           unchanged
brain/development/stream.py           unchanged
brain/development/history.py          unchanged
```

`git log` shows the Phase 3.7 commits touched only:

- `INVARIANT_CATALOG.md`
- `tools/catalog.py`
- `brain/_catalog_ids.py`
- `brain/invariants.py`
- `brain/development/text_stream.py` (new)
- `brain/development/fixtures/text_stream_*.py` (12 new files)
- `PHASE3_7_*.md` planning + audit docs

## 15. Patches landed during the campaign

Two minor probe corrections were made during the Step 15 implementation
draft and folded into the same commit before push:

```text
fix(I-STRM-02): allow "\n" and "\t" inside chunk text. Python's
                ``str.isprintable()`` excludes both, but raw text
                separators are meaningful for line / whitespace-run
                features and segment extraction; the helper
                ``_text_is_acceptable`` enforces "printable or
                allowed-whitespace" while still rejecting every other
                control character.
fix(I-STRM-07): drop the redundant ``self.text.isprintable()`` clause
                from ``StreamPromotionCandidate.__post_init__``; the
                ``_text_is_acceptable`` helper now governs that path
                so the candidate accepts the same raw text that the
                chunk constructor accepts.
```

Neither correction changed catalog rows, row IDs, statuses, count
expectations, or hard boundaries. Both align the promotion-candidate
text contract with the chunk text contract.

## 16. Recommended next mission

`Phase 3.8 Operator Stream Interaction (typed TUI commands that feed
text-stream chunks below the PerceptEvent / tick() boundary and
promote only explicit candidates through /stream-promote)`

Rationale: the macro-campaign in `CURRENT_CAMPAIGN.md` proceeds:

```text
3.7 Text Stream Ingress        -> 3.8 Operator Stream Interaction
3.8 Operator Stream Interaction -> 3.8b LLM Runtime Toggle
3.8b LLM Runtime Toggle         -> 3.9 final audit, dry run, PR
```

Phase 3.8 introduces the typed operator-facing commands
`/stream <text>`, `/stream-summary`, `/stream-candidates`, and
`/stream-promote <candidate_id>` over `brain/ui/`. The text-stream
substrate landed in Phase 3.7 is the substrate those commands read and
queue against; the `/stream-promote` route is the only authorized path
from `StreamPromotionCandidate` into `OperatorSession.event_queue` and
the existing `tick()` boundary.

Stop conditions for Phase 3.8 must continue to refuse:

```text
raw text mutating BrainState directly
raw text mapping to COGITO_ID
raw text bypassing the public PerceptEvent constructor
text-stream evidence flowing back into source histories
direct tick calls from /stream or /stream-summary or /stream-candidates
real LLM calls below the explicit Phase 3.8b toggle
social/language harness
Mode B reflective planning
host execution / shell / subprocess / network I/O
filesystem save/export outside an explicit reviewed policy
TLICA runtime mutation outside the existing tick() boundary
weakening any existing I-* safety row
```

## Conclusion

Phase 3.7 Text Stream Ingress campaign is complete. Catalog is at
v0.14 with full gate green. No outstanding patches, no blocked rows,
no scope-creep risks, and no follow-up corrigenda are required for
this campaign. Step 18 is the campaign's review gate before Phase 3.8
begins.
