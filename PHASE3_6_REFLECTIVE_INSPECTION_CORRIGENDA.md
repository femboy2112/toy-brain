# PHASE3_6_REFLECTIVE_INSPECTION_CORRIGENDA.md

## Purpose

Audit `PHASE3_6_REFLECTIVE_INSPECTION_KICKOFF.md` against the
non-negotiable boundaries in `CURRENT_CAMPAIGN.md` §2 and the synthesis
in `PHASE3_6_REFLECTIVE_INSPECTION_SYNTHESIS.md`. Lock the open
questions enumerated in the kickoff §12 so the catalog patch plan can
bind row IDs and statuses without ambiguity. This is a planning
artifact only. It does not introduce catalog rows, edit
`tools/catalog.py`, change `brain/invariants.py`, add runtime modules,
add fixtures, or change the TLICA runtime boundary.

## 1. Verdict

```text
KICKOFF READY FOR CATALOG PATCH PLAN — subject to the rulings below.
```

The kickoff stays inside every Phase 3.6 boundary. The corrigenda
rulings below resolve the open questions and constrain a few
field-shape details so the catalog patch plan can be written without
re-opening them.

## 2. Reflection vs Mode B (audit of kickoff §1, §5)

```text
PASS
```

The reflective layer:

- exposes no planning surface
- selects no `Act`
- constructs no `AgencyWitness`
- does not call `tick()`
- does not emit a `PerceptEvent`
- does not modify any source record

Reflective Inspection is a read-only *view*. Mode B is parallel
*action*. The kickoff distinguishes them correctly; the catalog rows
must keep this distinction in their proposition text.

## 3. Inspection vs agency (audit of kickoff §5, §11)

```text
PASS
```

The kickoff's constructor surface (`construct_reflective_summary_item`,
`construct_reflective_inspection_snapshot`) is purely functional. No
agency-implying language appears (no "choose", "select", "decide",
"prefer"). The catalog rows must continue to use observational
vocabulary only ("record", "count", "expose", "summarize", "inspect").

## 4. Summary vs truth (audit of kickoff §3, §8, §9)

```text
PASS — with a binding clarification below.
```

The kickoff explicitly forbids aggregate "quality" or "intelligence"
numbers and forbids recomputing source-derived scores. The catalog
patch plan must enforce this through a row that says approximately:

```text
ReflectiveInspectionSummary does not aggregate per-source scores.
score_min / score_max / score_mean are surfaced per source item
only when the source itself supplies a documented exact Fraction
score (Phase 3.5 ExpressionHistory). The aggregate summary exposes
counts only.
```

## 5. Read-only locality (audit of kickoff §7, §10)

```text
PASS
```

The constructor surface accepts source objects as inputs and returns a
new frozen record. The kickoff's forbidden-operations list (§10)
covers source-history mutation, BrainState mutation, callback
registration, file I/O, network I/O, subprocess spawn, real LLM
invocation, and `float` / `round` / `math` arithmetic. The static
audit fixture from the catalog patch plan will AST-check the runtime
module against the same forbidden-operations list.

## 6. Bounded exact counts / statistics (audit of kickoff §3, §4, §8)

```text
PASS — with the following lockings.
```

```text
entry_count                          int >= 0
distinct_id_count                    int, 0 <= distinct <= entry_count
counts_by_category                   sum(values) == entry_count;
                                     keys are bounded printable strings
                                     copied from source vocabulary
score_min / score_max / score_mean   either all None or all Fraction in
                                     the source's documented range
                                     ([0, 1] for ExpressionHistory)
constructed_at_tick                  int >= 0
notes                                see §11 ruling — bounded labels only
```

The catalog patch plan must lock these constraints as separate I-REF-*
rows.

## 7. Source-history non-mutation (audit of kickoff §7, §10)

```text
PASS
```

The reflective module reads `len(...)`, iterates over already-frozen
tuples, and reads documented exact `Fraction` fields. It never calls a
source-history mutator (`append_*`, `with_frame`, etc.). The static
audit fixture must explicitly forbid calls of the form
`<source>.append(...)` or `with_*(...)` from inside any reflective
function reachable from the public constructors.

## 8. UI integration deferral (audit of kickoff §11, §12 Q4)

```text
LOCKED: UI integration is DEFERRED to Phase 3.8.
```

Reasoning: the campaign already commits Phase 3.8 to operator-stream
commands. Adding a `/state` enhancement in Phase 3.6 would entangle
the read-only layer with the UI surface before the text-stream layer
exists. Phase 3.6 must not modify `brain/ui/*`.

The catalog patch plan must include a row (analog of `C10-AMEND-01`
from Phase 3.5) that explicitly defers `brain/ui/*` integration of
Reflective Inspection to a later authorized campaign.

## 9. Catalog row statuses (audit of kickoff §11; ruling for catalog plan)

```text
LOCKED row partitioning (the catalog plan will refine names/IDs):

REQUIRED  ReflectiveSource finite closed enumeration
REQUIRED  ReflectiveSummaryItem is bounded
REQUIRED  ReflectiveSummaryItem.counts_by_category sums to entry_count
REQUIRED  ReflectiveSummaryItem.distinct_id_count <= entry_count
REQUIRED  ReflectiveInspectionSnapshot is constructed deterministically
          from source records; same inputs -> equal snapshot
REQUIRED  Reflective operations do not mutate
          BrainState / MSI / PtCns / ContentRegistry
REQUIRED  Reflective operations do not mutate source histories
          (Output / Worldlet / ProtoBasic / Expression / Transcript)
REQUIRED  Reflective scores surface only from sources that supply them;
          no aggregate score is produced
STRUCTURAL  Reflective module has no I/O / network / file / shell / LLM
            / TLICA / tick imports
STRUCTURAL  Reflective records are frozen dataclasses
STRUCTURAL  No float / round / math on the count/statistic path
STRUCTURAL  Constructors are pure and register no callbacks
OBSERVED   Aggregate ReflectiveInspectionSummary walk is inspectable
NOT-EXERCISED  Reflective save / export placeholder
```

Approximate count delta from the v0.12 baseline:

```text
+ 8 REQUIRED
+ 4 STRUCTURAL
+ 1 OBSERVED
+ 1 NOT-EXERCISED
+ 0 DEFERRED
```

The catalog patch plan will resolve final IDs, exact proposition text,
exact count delta, and the fixture roster.

## 10. InspectionHistory ruling (audit of kickoff §6, §12 Q1)

```text
LOCKED: InspectionHistory is DEFERRED to a later campaign.
```

Reasoning: an `InspectionHistory` adds runtime behavior (append, ring
bounds) that is not required by the Phase 3.6 read-only thesis. The
synthesis target is a *view*, not a *log*. A future campaign can add
`InspectionHistory` (with its own rows for copy-on-write append,
bounded ring, and write-to-disk placeholder) when there is a concrete
consumer.

Phase 3.6 ships `ReflectiveInspectionSnapshot` + `…Summary` only.

## 11. notes field ruling (audit of kickoff §3, §12 Q3)

```text
LOCKED: notes is a tuple of source-vocabulary labels only.
```

`notes` is a tuple of bounded printable strings, each a member of the
source's *existing* labeling vocabulary (e.g., `ExpressionSource`
member name, `TranscriptKind` member name, Proto-BASIC parse-category
name). Free-form natural-language labels are forbidden. The tuple
length is capped at 8.

The catalog patch plan must include this constraint in the
`ReflectiveSummaryItem` row's proposition.

## 12. score field ruling (audit of kickoff §3, §12 Q2)

```text
LOCKED: score_* fields are populated ONLY for sources that supply a
        documented exact Fraction score.

Phase 3.6 v0.13: only ExpressionHistory supplies score statistics
through Phase 3.5 ReadabilityScore. All other sources have
score_min / score_max / score_mean == None.
```

## 13. Aggregate inspection walk ruling (audit of kickoff §12 Q5)

```text
LOCKED: Aggregate inspection walk is a Python frozen dataclass only.
        No serialization, no JSON, no write-to-disk. The OBSERVED row
        records the structure for inspection only.
```

## 14. Hard-boundary file list for Phase 3.6 steps 6-8

```text
INVARIANT_CATALOG.md                    Step 6 only
tools/catalog.py                        Step 6 only
brain/_catalog_ids.py                   Step 6 only (regenerated)
brain/invariants.py                     Steps 6, 7 only
brain/development/reflective.py         Step 7 only
brain/development/fixtures/reflective_*.py
                                        Step 7 only
PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md Step 8 only
```

Phase 3.6 must NOT modify:

```text
brain/tlica/
brain/tick.py
brain/llm/
brain/ui/                               (Phase 3.8 owns)
traces/                                 (no schema change)
scenarios/                              (no schema change)
lean_reference/                         (read-only spec snapshot)
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
brain/development/expression.py
brain/ui/transcript.py
```

These boundaries are the same as Phase 3.5's plus the Operator TUI
files for which `C10-AMEND-01` already deferred integration.

## 15. Stop conditions for the catalog patch plan

Stop and reopen corrigenda if any future ruling would:

```text
allow Mode B planning surface
allow self-modification
authorize a UI integration pane in Phase 3.6
authorize InspectionHistory serialization / weaving into traces or
  scenarios
authorize aggregate "quality" / "intelligence" / "social-success"
  scoring
weaken any existing I-* row
add an external dependency, LLM call, shell/subprocess/network call,
  or file write path
change scenario / trace schema
promote reflective evidence into PerceptEvent / tick() / TLICA runtime
promote an OBSERVED row to REQUIRED without new corrigenda
```

## 16. Open decisions remaining for the catalog patch plan

```text
exact I-REF-* row IDs and titles
exact proposition text per row
exact fixture roster (count and grouping)
exact field names and constants in the runtime module
exact count delta confirmation against the strict counts gate
```

These are mechanical follow-throughs of the rulings above; no new
policy questions remain.

## 17. Next artifact

```text
PHASE3_6_REFLECTIVE_INSPECTION_CATALOG_PATCH_PLAN.md
```

The catalog patch plan binds these rulings to row IDs, statuses, and a
file budget, and stops at the Step 9 review gate.
