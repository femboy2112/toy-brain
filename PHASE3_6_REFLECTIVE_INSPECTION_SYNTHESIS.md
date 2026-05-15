# PHASE3_6_REFLECTIVE_INSPECTION_SYNTHESIS.md

## Purpose

This document is the Phase 3.6 Reflective Inspection synthesis. It is a
planning artifact only. It does not introduce catalog rows, edit
`tools/catalog.py`, change `brain/invariants.py`, add runtime modules or
fixtures, or change the TLICA runtime boundary.

## 1. v0.12 baseline

```text
Catalog version:  v0.12
Counts:           139 REQUIRED / 48 STRUCTURAL / 5 NOT-EXERCISED /
                  12 DEFERRED / 8 OBSERVED
Full gate:        green
Latest audit:     PHASE3_5_EXPRESSION_READABILITY_AUDIT.md  (PASS)
Mission:          Fast Safe Text Interaction (this campaign)
Entrypoint:       python3 -m brain.ui
```

Phase 3.5 landed a bounded local Expression + ReadabilityPredictor layer
over Phase 3.1–3.4 developmental histories. Phase 3.6 is the first step of
the macro-campaign that culminates in Phase 3.8 Operator Stream
Interaction.

## 2. Why Phase 3.6 follows the Phase 3.5 audit recommendation

The Phase 3.5 audit (§12, recommended next mission) calls for a
*Reflective Inspection* layer — an operator-facing summary view over the
local developmental histories — explicitly *without* UI integration and
*without* Mode B planning. Phase 3.6 is exactly that layer.

Reflective Inspection is the cheapest safe step that:

```text
exposes the existing developmental histories as a single inspectable
read-only surface
preserves every existing I-* row
adds no runtime behavior beyond bounded summary construction
defers UI integration until a later campaign explicitly authorizes it
defers any text-stream evidence (Phase 3.7 will introduce that)
defers any operator command surface for the new layer (Phase 3.8)
```

## 3. Reflective Inspection thesis

A **Reflective Inspection** record is a bounded local, read-only,
exact-count summary derived deterministically from the existing local
developmental histories. It is *not* reflection in any subjective sense
and *not* an introspective claim; it is a bounded data record that
re-presents existing local evidence in a single shape.

Sources covered (only these; the enumeration is finite):

```text
OutputHistory          (Phase 3.2)
WorldletHistory        (Phase 3.3)
ProtoBasicHistory      (Phase 3.4)
ExpressionHistory      (Phase 3.5)
OperatorTranscript     (Operator TUI Agent-Style Layout)
```

`BrainState`, `MSI`, `PtCns`, `ContentRegistry`, traces, scenarios,
`brain/tlica/`, `brain/tick.py`, and `brain/llm/` are *not* covered by
the Reflective Inspection layer. The layer reads only what already
exists in developmental histories.

## 4. Local evidence boundaries

The Phase 3.6 layer is strictly downstream of the existing developmental
histories. The data flow is one-way:

```text
OutputHistory / WorldletHistory / ProtoBasicHistory /
ExpressionHistory / OperatorTranscript
    -> ReflectiveSummaryItem
    -> ReflectiveInspectionSnapshot
    -> local InspectionHistory (only if accepted)
```

The reverse path is closed:

```text
ReflectiveInspectionSnapshot -> BrainState / MSI / PtCns / registry /
                                tick / PerceptEvent / traces /
                                scenarios / source histories   NOT ALLOWED
```

## 5. Why this is not Mode B

Mode B in TLICA is parallel reflective planning. Phase 3.6:

```text
does not plan
does not select an Act
does not construct an AgencyWitness
does not call tick()
does not modify any source history
does not modify any TLICA runtime object
does not introduce a "should the brain do X" surface
does not introduce a "what if" simulation surface
```

Reflective Inspection is a *view*, not a *step*. It produces a
read-only snapshot of what *already* happened.

## 6. Why this is not language or social communication

The summary is a numeric / enumerated / counted record:

```text
counts per source kind
counts per outcome category (per existing Phase 3.2–3.5 vocabularies)
exact Fraction statistics where the source supplies Fractions
bounded printable identifiers and short labels copied from source
records, never re-interpreted
```

It does not synthesize utterances, generate language, parse natural
language, address an audience, or compute any social metric. It does
not introduce a chat surface and does not authorize one.

## 7. Why this is not truth scoring

The summary does not claim truth, validity, correctness, accuracy, or
quality of any source record. It records what is *there*; it does not
score *whether* it is right. Phase 3.5's anti-Goodhart discipline for
`ReadabilityScore` carries forward: any score values surfaced by the
summary come directly from the existing source records, with no
re-weighting and no aggregation that would imply a truth claim.

## 8. Why this is not agency

The summary cannot:

```text
choose an Act
construct an AgencyWitness
mutate BrainState / MSI / PtCns / ContentRegistry
emit a PerceptEvent
schedule a tick
register a callback
invoke any side-effecting host capability
```

Reflective Inspection is a strictly observational surface. Even the
`/state` Operator TUI command (which is in scope only as a *consumer*
of snapshots later in Phase 3.8) does not gain new capabilities here.

## 9. Non-goals

```text
no Mode B planning
no self-modification
no language understanding
no natural-language teacher / corrector
no real LLM calls
no host execution / subprocess / shell / network I/O
no filesystem save / export path
no scenario or trace schema change
no PerceptEvent / tick() promotion route
no TLICA runtime mutation
no UI integration in Phase 3.6 (Phase 3.8 owns the operator surface)
no new permission to weaken any existing I-* row
no implicit serialization of source histories
no cross-invocation persistence
```

## 10. Risks

```text
Scope creep — Reflective Inspection could be misread as a stepping stone
              to Mode B. The catalog rows must phrase the layer as a
              read-only summary, not as a planning surface.

Boundary erosion — A future contributor might want the summary to mutate
                   source histories "to keep them in sync". The catalog
                   rows must explicitly forbid this.

Aggregation drift — Aggregating across sources risks producing a number
                    that looks like a truth/intelligence/quality score.
                    The corrigenda must call this out and the catalog
                    rows must constrain aggregation to per-source
                    counts and exact statistics.

UI temptation — A live inspection pane is tempting; Phase 3.6 must defer
                UI integration. The Operator TUI command surface is
                Phase 3.8's job.

OBSERVED inflation — The aggregate inspection walk will be an OBSERVED
                     row, not a REQUIRED row, so that its summary
                     contents can evolve without weakening gating.
```

## 11. Anticipated catalog impact

This is a working sketch only; the binding artifact is the catalog patch
plan (Step 5). Likely shape:

```text
+ N REQUIRED rows for bounded source enumeration, bounded item
  construction, deterministic exact aggregate counts, source-history
  non-mutation, BrainState non-mutation
+ a small number of STRUCTURAL rows for frozen records and the static
  audit of the reflective module (no I/O / shell / network / LLM)
+ 1 OBSERVED row for the aggregate inspection walk
```

The exact counts and IDs are decided in
`PHASE3_6_REFLECTIVE_INSPECTION_CATALOG_PATCH_PLAN.md`, after the
kickoff and corrigenda.

## 12. Next artifact

```text
PHASE3_6_REFLECTIVE_INSPECTION_KICKOFF.md
```

The kickoff will commit to the concrete record shape, the finite source
enumeration, the bounded fields, and the construction discipline
(deterministic, exact, source-history-non-mutating). The corrigenda
will audit the kickoff. The catalog patch plan will bind the audited
result to row IDs and statuses, stopping at the review gate.
