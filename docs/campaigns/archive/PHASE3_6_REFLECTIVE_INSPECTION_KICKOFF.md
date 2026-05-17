# PHASE3_6_REFLECTIVE_INSPECTION_KICKOFF.md

## Purpose

Concretize the read-only structures named in
`PHASE3_6_REFLECTIVE_INSPECTION_SYNTHESIS.md`. This is a planning
artifact only. It does not introduce catalog rows, edit
`tools/catalog.py`, change `brain/invariants.py`, add runtime modules,
add fixtures, or change the TLICA runtime boundary. The corrigenda
audits this artifact; the catalog patch plan binds the audited result.

## 1. Structural commitments

```text
ReflectiveSource          finite closed enumeration of source kinds
ReflectiveSummaryItem     bounded per-source summary record
ReflectiveInspectionSnapshot
                          frozen record collecting one item per source
ReflectiveInspectionSummary
                          aggregate exact counts / Fraction statistics
                          across all sources
InspectionHistory         copy-on-write bounded local snapshot history
                          (introduced only if accepted; may be deferred)
```

All records are frozen dataclasses (or equivalent immutable shapes).
Every field is a bounded primitive, an enumeration value, an exact
`Fraction`, a tuple of bounded printable strings, or a reference to
another frozen reflective record. No callable, file handle, socket,
LLM client, or path object appears on any field.

## 2. ReflectiveSource enumeration

```text
class ReflectiveSource(Enum):
    OUTPUT_HISTORY        = "output_history"
    WORLDLET_HISTORY      = "worldlet_history"
    PROTO_BASIC_HISTORY   = "proto_basic_history"
    EXPRESSION_HISTORY    = "expression_history"
    OPERATOR_TRANSCRIPT   = "operator_transcript"
```

The enumeration is closed at v0.13. New source kinds require a future
campaign and a new catalog row. `ReflectiveSource` deliberately
overlaps with `ExpressionSource` for `OUTPUT_HISTORY`,
`WORLDLET_HISTORY`, `PROTO_BASIC_HISTORY`, and `OPERATOR_TRANSCRIPT`,
but does not import or alias the Phase 3.5 enum — it is its own closed
enumeration so Phase 3.6 can evolve without coupling to Phase 3.5.

## 3. ReflectiveSummaryItem

```text
@dataclass(frozen=True, slots=True)
class ReflectiveSummaryItem:
    source: ReflectiveSource
    entry_count: int
    distinct_id_count: int
    counts_by_category: Mapping[str, int]    # source-defined category
    score_min: Fraction | None               # None when source has no score
    score_max: Fraction | None
    score_mean: Fraction | None
    notes: tuple[str, ...]                   # bounded printable labels
```

Field-level rules (the corrigenda will audit these):

```text
source                       must be a ReflectiveSource
entry_count                  int >= 0
distinct_id_count            int, 0 <= distinct_id_count <= entry_count
counts_by_category           MappingProxyType wrapping a dict[str, int];
                             keys are bounded printable category names
                             copied from the source's existing
                             vocabulary; values are int >= 0; the sum
                             of values equals entry_count
score_min / score_max /
score_mean                   either all None (source supplies no
                             scores) or all Fraction in their source's
                             documented range (Phase 3.5: [0, 1])
notes                        tuple of <= NOTES_MAX_NOTES (small fixed
                             cap, likely 8) bounded printable strings,
                             each <= NOTES_MAX_LEN characters
```

Category vocabulary per source (copied from existing rows; not
re-interpreted):

```text
OUTPUT_HISTORY        categories: { "impulses", "echoes",
                                   "output_patterns",
                                   "token_candidates",
                                   "learned_tokens" }
WORLDLET_HISTORY      categories: { "attempts", "responses",
                                   "accepted", "rejected" }
PROTO_BASIC_HISTORY   categories: per ProtoBasicParseResult.category
                                  and ProtoBasicExecutionResult.category
EXPRESSION_HISTORY    categories: per ExpressionSource member
OPERATOR_TRANSCRIPT   categories: per TranscriptKind member
```

The corrigenda must confirm that these vocabulary sets reflect the
*existing* source-record categories. The catalog plan must lock the
final vocabulary per source as a constant in the reflective module.

## 4. ReflectiveInspectionSnapshot

```text
@dataclass(frozen=True, slots=True)
class ReflectiveInspectionSnapshot:
    items: Mapping[ReflectiveSource, ReflectiveSummaryItem]
    constructed_at_tick: int                 # 0 if no tick has run
```

Snapshot rules:

```text
items keys are exactly the active subset of ReflectiveSource members
  for which the caller supplied a non-None source object;
  if a source object is None, no item appears (no synthetic zero item);
constructed_at_tick is a non-negative int captured from the caller
  (typically state.tick_index); the snapshot does not read tick state
  on its own and is not coupled to brain.tick.
```

The constructor is a pure function that copies from the supplied source
records and returns a new snapshot. It must not store a reference to
any mutable source container; only the counts and bounded labels are
extracted.

## 5. ReflectiveInspectionSummary

```text
@dataclass(frozen=True, slots=True)
class ReflectiveInspectionSummary:
    snapshot: ReflectiveInspectionSnapshot
    total_entries: int
    total_distinct_ids: int
    source_count: int                        # number of items present
```

The summary is a thin aggregation over `snapshot.items`. It does not
reach back into source histories. It does not compute a single
"quality" or "intelligence" number. Per the synthesis (§7), no
aggregate score is produced — only counts.

## 6. InspectionHistory (optional, may be deferred)

The kickoff *proposes* a copy-on-write `InspectionHistory`:

```text
@dataclass(frozen=True, slots=True)
class InspectionHistory:
    snapshots: tuple[ReflectiveInspectionSnapshot, ...] = ()

    def append(self, snapshot) -> "InspectionHistory":
        ...   # bounded by INSPECTION_HISTORY_MAX_SNAPSHOTS
```

The corrigenda will decide whether this is in-scope for Phase 3.6 or
deferred to a later campaign. Defaulting to deferred is acceptable;
the catalog plan must reflect that decision explicitly.

## 7. Constructor surface

Two public callables (final names locked by the catalog patch plan):

```text
def construct_reflective_summary_item(
    source: ReflectiveSource,
    source_object: object,
) -> ReflectiveSummaryItem: ...

def construct_reflective_inspection_snapshot(
    output_history:           OutputHistory          | None = None,
    worldlet_history:         WorldletHistory        | None = None,
    proto_basic_history:      ProtoBasicHistory      | None = None,
    expression_history:       ExpressionHistory      | None = None,
    operator_transcript:      OperatorTranscript     | None = None,
    *,
    constructed_at_tick: int = 0,
) -> ReflectiveInspectionSnapshot: ...
```

Both constructors are pure functions. They do not register callbacks,
do not call `tick()`, do not emit `PerceptEvent`, and do not mutate any
input.

## 8. Bounded feature extraction

The reflective module extracts only what the source already exposes:

```text
OutputHistory          len(impulses), len(echoes), len(output_patterns),
                       len(token_candidates), len(learned_tokens);
                       distinct impulse_id count

WorldletHistory        len(attempts), len(responses); accepted count
                       (boolean accepted == True); rejected count

ProtoBasicHistory      parse-result category counts;
                       execution-result category counts;
                       distinct command_id count

ExpressionHistory      total record count;
                       per-ExpressionSource counts;
                       readability score min / max / mean as exact
                       Fraction

OperatorTranscript     entries.len();
                       per-TranscriptKind counts;
                       distinct tick_at_event count
```

No source-derived score is recomputed. No new score is invented. All
arithmetic uses `int` and `Fraction` only — never `float`, never
`math.*`, never `round`.

## 9. Anti-Goodhart rules

```text
counts can only reflect source records that exist now; the reflective
  layer never invents or duplicates entries

aggregate statistics do not weight one source above another

no per-source "quality" or "score" is composed from category counts

ExpressionHistory readability statistics are surfaced as-is from the
  Phase 3.5 ReadabilityScore values; the reflective layer must not
  recompute, rescale, or combine them with other sources

InspectionHistory (if accepted) appends only complete snapshots; the
  layer does not mutate an in-flight snapshot
```

## 10. Non-mutating inspection contract

The reflective module is forbidden to do any of:

```text
mutate OutputHistory / WorldletHistory / ProtoBasicHistory /
       ExpressionHistory / OperatorTranscript
mutate BrainState / ScalarProfile / MSI / PtCns / ContentRegistry
call any source-history mutator (append_*, etc.)
register an atexit / signal / callback hook
call float(), round(), or math.*
import os, subprocess, socket, urllib, http, requests, pathlib,
       tempfile, shutil, curses, brain.llm, brain.tlica, brain.tick
write to disk
open a file
open a socket
spawn a subprocess
invoke a real LLM client
```

The static audit fixture (see catalog plan) AST-checks the module to
enforce these rules.

## 11. Exclusions for Phase 3.6

```text
no Mode B reflective planning
no self-modification
no natural-language teacher / corrector
no social model
no real LLM calls
no direct tick() promotion
no TLICA mutation
no UI integration (Phase 3.8 owns operator commands)
no scenario / trace schema change
no save / export path
no cross-invocation persistence
```

## 12. Open questions for the corrigenda

```text
Q1  Should InspectionHistory be in-scope for Phase 3.6 or deferred?

Q2  Are score_min / score_max / score_mean fields required for
    ExpressionHistory items only, or also for any future source that
    supplies a Fraction score? (Recommended: only when the source
    itself supplies a documented Fraction score.)

Q3  Are notes useful at all in v0.13? They risk drifting into
    natural-language descriptions. The corrigenda should either
    constrain them to a closed set of bounded labels copied from
    source enumerations, or remove the field.

Q4  Should the reflective summary call be exposed via the Operator TUI
    `/state` view in Phase 3.6 (read-only) or deferred to Phase 3.8?

Q5  Should the aggregate inspection walk produce a JSON-printable
    record, or remain a Python frozen dataclass only? (Recommended:
    Python frozen dataclass only; serialization is a future-campaign
    concern.)
```

## 13. Next artifact

```text
PHASE3_6_REFLECTIVE_INSPECTION_CORRIGENDA.md
```

The corrigenda will audit each of §1–§12 here, lock the open questions,
and produce a verdict on whether the kickoff is ready for the catalog
patch plan.
