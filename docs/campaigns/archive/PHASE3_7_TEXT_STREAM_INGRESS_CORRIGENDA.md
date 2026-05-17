# PHASE3_7_TEXT_STREAM_INGRESS_CORRIGENDA.md

## Purpose

Audit `PHASE3_7_TEXT_STREAM_INGRESS_KICKOFF.md` against the
non-negotiable boundaries in `CURRENT_CAMPAIGN.md` §"Guardrails" and the
synthesis in `PHASE3_7_TEXT_STREAM_INGRESS_SYNTHESIS.md`. Lock the open
questions enumerated in the kickoff §15 so the catalog patch plan can
bind row IDs and statuses without ambiguity. This is a planning artifact
only. It does not introduce catalog rows, edit `tools/catalog.py`,
change `brain/invariants.py`, add runtime modules, add fixtures, or
change the TLICA runtime boundary.

## 1. Verdict

```text
KICKOFF READY FOR CATALOG PATCH PLAN — subject to the rulings below.
```

The kickoff stays inside every Phase 3.7 boundary. The corrigenda
rulings below resolve the open questions and constrain a few field-shape
details so the catalog patch plan can be written without re-opening
them.

## 2. Raw stream vs PerceptEvent (audit of kickoff §3, §8)

```text
PASS
```

`TextStreamChunk` is bounded raw printable text evidence; it is *not* a
`PerceptEvent`. The constructor never calls `tick()`, never emits a
`PerceptEvent`, and never reaches into `BrainState`. The catalog rows
must keep this distinction in their proposition text.

`StreamPromotionCandidate` carries the explicit fields needed by the
existing `PerceptEvent` constructor (a non-reserved
`target_content_id`, a bounded `text`, a closed-vocabulary `source`,
and bounded provenance), but is *not* itself a `PerceptEvent`. The
candidate must be passed through the existing
`brain/io_types.PerceptEvent` constructor by the Phase 3.8
`/stream-promote` route — the candidate constructor must never do this.

## 3. Chunk text vs language meaning (audit of kickoff §5, §6)

```text
PASS
```

`StreamFeatureVector` exposes only structural counts:

- `char_count` (length)
- `token_count` (whitespace-split count)
- `distinct_token_count` (set size)
- `line_count` (line-split count)
- `max_run_length` (consecutive identical token run)
- `whitespace_only` (bool)

No regex, no parser, no grammar, no language model, no probabilistic
step participates. `extract_stream_features` uses `str.split`,
`str.splitlines`, `set` cardinality, and printable-char counting only.
The catalog rows must phrase this as *structural* feature extraction
and explicitly disclaim language understanding.

## 4. Segment candidate vs parse (audit of kickoff §6)

```text
PASS — with a binding clarification.
```

`SegmentCandidate` is a *span* (`start`, `end`) plus a
closed-vocabulary `segment_kind` tag. It carries no payload text (the
chunk is the source of truth) and no parse tree. The corrigenda locks
the closed `segment_kind` vocabulary at:

```text
{ "line", "delimited_span", "whitespace_run" }
```

`segment_kind` outside this set is rejected at construction. New kinds
require a future campaign and a new catalog row.

## 5. Stream pattern vs truth / PRESERVE (audit of kickoff §7)

```text
PASS
```

`StreamPattern` carries:

- `pattern_id` (bounded printable, not COGITO_ID)
- `signature` (bounded tuple of bounded printable tokens)
- `recurrence_count` (int >= STREAM_PATTERN_RECURRENCE_MIN)
- `last_seen_tick` (int >= 0)

It carries no `PRESERVE` / `DAMAGE` / `PCE` / `ProjectedPCE` / `Act` /
`ModeOp` / `AgencyWitness` field. It does not enter `PtCns.evaluate`.
It does not contribute to `MSI.contents`. The catalog patch plan must
include a row that explicitly disclaims these.

## 6. Promotion candidate vs event queue (audit of kickoff §8)

```text
PASS — with a binding clarification.
```

`StreamPromotionCandidate` is a queueable record only. It is *not*
appended to `OperatorSession.event_queue` by the substrate; that is
the Phase 3.8 `/stream-promote` route's job. The candidate constructor:

- does not call `tick()`
- does not construct a `PerceptEvent`
- does not append to any event queue
- does not mutate `BrainState`, MSI, PtCns, registry, or any source
  history

The catalog patch plan must include a row that explicitly forbids the
substrate from appending candidates to `OperatorSession.event_queue`.
The `/stream-promote` route owns that append in Phase 3.8.

## 7. Bounds and anti-growth rules (audit of kickoff §11; ruling)

```text
LOCKED constants:

STREAM_TEXT_MAX_LEN              1024 chars
STREAM_PROVENANCE_MAX_LEN          64 chars
STREAM_HISTORY_MAX_CHUNKS         256 chunks
STREAM_SEGMENTS_MAX                32 segments per chunk
STREAM_PATTERN_RECURRENCE_MIN       2 (minimum threshold)
STREAM_PATTERN_RECURRENCE_MAX     256 (saturation cap)
STREAM_PATTERN_SIG_MAX             16 tokens
STREAM_PROMOTION_MAX               64 candidates per history walk
```

Repeated identical chunks must not inflate `recurrence_count` beyond
`STREAM_PATTERN_RECURRENCE_MAX`. Over-bound chunk text raises
`ValueError` tagged with the row id; silent truncation on the chunk
text path is forbidden. Over-bound history append drops the oldest
chunk before the new chunk is added (matching the Phase 3.5
`ExpressionHistory` ring discipline).

The catalog patch plan locks these constants in the runtime module.

## 8. Source / provenance rules (audit of kickoff §2, §3)

```text
PASS — with a binding clarification.
```

`TextStreamSource` is closed at v0.14:

```text
{ OPERATOR, SYSTEM, PROBE_ECHO, GENERATED }
```

A `MODEL` source kind is *not* introduced. The Phase 3.8b LLM Runtime
Toggle reuses the existing `LLMClient` / `tick(..., client, ...)` seam,
not a second classification path through the stream substrate. Adding
`MODEL` requires a future campaign and a new catalog row.

`TextStreamChunk.provenance_tag` is a closed-vocabulary tag derived
from the source record. The corrigenda recommends but does not lock the
exact tag vocabulary; the catalog patch plan can either lock a closed
set or treat it as a bounded printable label with no semantic
interpretation. The recommended floor is "bounded printable, length
<= STREAM_PROVENANCE_MAX_LEN, no COGITO_ID collision".

## 9. COGITO_ID defenses (audit of kickoff §12)

```text
PASS
```

The kickoff already lists nine COGITO_ID defenses:

```text
TextStreamChunk.chunk_id, .text
StreamPattern.pattern_id
SegmentCandidate.chunk_id
StreamPromotionCandidate.candidate_id, .target_content_id, .chunk_id,
                                  .pattern_id (when set), .text
```

The catalog patch plan must include a row that explicitly tests every
one of these by attempting construction with `COGITO_ID` in the
relevant field and asserting the construction is rejected with a
row-tagged `ValueError`.

The validators reuse the existing
`brain/_catalog_ids.COGITO_ID` reserved sentinel.

## 10. SegmentCandidate kind tag ruling (audit of kickoff §15 Q2)

```text
LOCKED: SegmentCandidate carries (start, end, segment_kind) where
        segment_kind is a member of the closed vocabulary
        { "line", "delimited_span", "whitespace_run" }.
```

Reasoning: segment vocabulary needs to be auditable and closed. A
free-form `segment_kind` invites drift toward language interpretation.
A closed vocabulary keeps the layer structural.

## 11. StreamPattern signature ruling (audit of kickoff §15 Q3)

```text
LOCKED: StreamPattern carries the actual signature tokens (bounded by
        STREAM_PATTERN_SIG_MAX = 16 tokens), not a hash.
```

Reasoning: structural transparency matters for inspection. A hash
collapses the structure and would force a future contributor to invent
a "lookup the original tokens" path that defeats the read-only
discipline.

## 12. StreamPromotionCandidate pattern requirement ruling (audit of kickoff §15 Q4)

```text
LOCKED: StreamPromotionCandidate.pattern_id is OPTIONAL.
```

Reasoning: chunk-only promotion candidates are valid for explicit
operator action. The operator carries the accountability through the
Phase 3.8 `/stream-promote` route, not the substrate. Requiring a
supporting `StreamPattern` would force the substrate to invent
patterns when the operator wants to promote a one-off chunk
explicitly.

## 13. StreamPromotionCandidate chunk_id ruling (audit of kickoff §15 Q5)

```text
LOCKED: chunk_id is a CALLER CONTRACT, not a substrate-time lookup.
```

Reasoning: the substrate constructor does not load `TextStreamHistory`
to verify chunk_id existence. The Phase 3.8 `/stream-promote` route is
responsible for passing a valid chunk_id from the displayed history.
The catalog patch plan must include a row that documents the caller
contract explicitly.

This keeps the substrate constructor pure (no side-effecting lookup)
and avoids tight coupling between candidate construction and history
presence.

## 14. Aggregate stream walk ruling (audit of kickoff §15 Q6)

```text
LOCKED: Aggregate stream walk is a Python frozen dataclass only.
        No JSON. No write-to-disk. The OBSERVED row records the
        structure for inspection only.
```

This mirrors the Phase 3.5 `I-EXP-17` and Phase 3.6 `I-REF-13` rulings.
Serialization is a future-campaign concern.

## 15. Save / export NOT-EXERCISED row ruling (audit of kickoff §15 Q7)

```text
LOCKED: Phase 3.7 includes a NOT-EXERCISED row for stream
        save / export.
```

Mirrors the existing `I-EXP-18` and `I-REF-14` placeholders. No
`TextStreamHistory` / `StreamPromotionCandidate` serialization, save,
export, or write-to-disk path lands in this campaign. Any future write
path requires reviewed policy, dedicated rows, fixtures under bounded
conditions, and a stop condition.

## 16. UI integration deferral (audit of kickoff §14)

```text
LOCKED: UI integration is DEFERRED to Phase 3.8.
```

Reasoning: Phase 3.8 owns the operator-stream commands (`/stream`,
`/stream-summary`, `/stream-candidates`, `/stream-promote`). Adding
operator commands or UI integration in Phase 3.7 would entangle the
substrate with the UI surface before the substrate exists. Phase 3.7
must not modify `brain/ui/*`.

The catalog patch plan must include a row (analog of `C10-AMEND-01`
from Phase 3.5 and the equivalent `C13-AMEND-01` analog from Phase 3.6)
that explicitly defers `brain/ui/*` integration of Text Stream Ingress
to Phase 3.8.

## 17. Catalog row statuses (ruling for catalog plan)

```text
LOCKED row partitioning (the catalog plan will refine names/IDs):

REQUIRED  TextStreamSource finite closed enumeration
REQUIRED  TextStreamChunk is bounded printable + COGITO_ID rejected
REQUIRED  TextStreamHistory is copy-on-write and bounded
REQUIRED  StreamFeatureVector is deterministic and exact
REQUIRED  SegmentCandidate is structural (closed-vocabulary kind +
          bounded span)
REQUIRED  StreamPattern requires recurrence_count >= MIN; carries no
          truth / PRESERVE / agency field
REQUIRED  StreamPromotionCandidate requires explicit non-reserved
          target_content_id and explicit source/provenance/chunk_id;
          is not a PerceptEvent
REQUIRED  Stream operations do not mutate
          BrainState / MSI / PtCns / ContentRegistry
REQUIRED  Stream operations do not mutate any existing source history
REQUIRED  Stream operations do not call tick() and do not append to
          OperatorSession.event_queue
REQUIRED  Anti-growth: repeated/huge chunks do not inflate
          recurrence_count above the saturation cap; no silent
          truncation on the chunk text path
STRUCTURAL  Text stream module has no I/O / network / file / shell /
            LLM / TLICA / tick / curses imports
STRUCTURAL  Stream records are frozen dataclasses
STRUCTURAL  No float / round / math on the count/statistic path
STRUCTURAL  Constructors are pure and register no callbacks
OBSERVED   Aggregate text-stream history walk is inspectable
NOT-EXERCISED  Stream save / export placeholder
```

Approximate count delta from the v0.13 baseline:

```text
+ 11 REQUIRED
+  4 STRUCTURAL
+  1 OBSERVED
+  1 NOT-EXERCISED
+  0 DEFERRED
```

The catalog patch plan resolves final IDs, exact proposition text,
exact count delta, and the fixture roster.

## 18. Hard-boundary file list for Phase 3.7 steps 14-17

```text
INVARIANT_CATALOG.md                       Step 14 only
tools/catalog.py                           Step 14 only
brain/_catalog_ids.py                      Step 14 only (regenerated)
brain/invariants.py                        Steps 14, 15, 16 only
brain/development/text_stream.py           Steps 15, 16 only
brain/development/fixtures/text_stream_*.py
                                           Steps 15, 16 only
PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md     Step 17 only
```

Phase 3.7 must NOT modify:

```text
brain/tlica/
brain/tick.py
brain/llm/
brain/ui/                              (Phase 3.8 owns)
traces/                                (no schema change)
scenarios/                             (no schema change)
lean_reference/                        (read-only spec snapshot)
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
brain/development/expression.py
brain/development/reflective.py
brain/ui/transcript.py
```

These boundaries are the same as Phase 3.6's plus the new
`brain/development/reflective.py` (Phase 3.6 just landed; it stays
unchanged in Phase 3.7).

## 19. Stop conditions for the catalog patch plan

Stop and reopen corrigenda if any future ruling would:

```text
allow Mode B planning surface
allow self-modification
authorize a UI integration pane in Phase 3.7
authorize TextStreamHistory serialization / weaving into traces or
  scenarios
authorize aggregate "quality" / "intelligence" / "social-success"
  stream score
authorize a real LLM-backed source kind (Phase 3.8b is the only
  authorized model-backed surface, and it does not introduce a new
  source kind)
weaken any existing I-* row
add an external dependency, LLM call, shell/subprocess/network call,
  or file write path
change scenario / trace schema
promote stream evidence into PerceptEvent / tick() / TLICA runtime
  outside the explicit Phase 3.8 /stream-promote route
promote an OBSERVED row to REQUIRED without new corrigenda
add a MODEL TextStreamSource without an authorized future campaign
```

## 20. Open decisions remaining for the catalog patch plan

```text
exact I-STRM-* row IDs and titles
exact proposition text per row
exact fixture roster (count and grouping)
exact field names and constants in the runtime module
exact count delta confirmation against the strict counts gate
exact closed segment_kind vocabulary registration in the catalog plan
                            (the corrigenda locks the set; the plan
                             must record the constant in the module)
```

These are mechanical follow-throughs of the rulings above; no new
policy questions remain.

## 21. Next artifact

```text
PHASE3_7_TEXT_STREAM_INGRESS_CATALOG_PATCH_PLAN.md
```

The catalog patch plan binds these rulings to row IDs, statuses, and a
file budget, and stops at the Step 13 review gate.
