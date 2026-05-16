# PHASE3_7_TEXT_STREAM_INGRESS_SYNTHESIS.md

## Purpose

This document is the Phase 3.7 Text Stream Ingress synthesis. It is a
planning artifact only. It does not introduce catalog rows, edit
`tools/catalog.py`, change `brain/invariants.py`, add runtime modules or
fixtures, change the TLICA runtime boundary, or authorize any operator
command surface (operator commands are Phase 3.8's job).

## 1. v0.13 baseline

```text
Catalog version:  v0.13
Counts:           147 REQUIRED / 52 STRUCTURAL / 6 NOT-EXERCISED /
                  12 DEFERRED / 9 OBSERVED
Full gate:        green
Latest audit:     PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md  (PASS)
Mission:          Fast Safe Text Interaction (this campaign)
Entrypoint:       python3 -m brain.ui
```

Phase 3.6 landed a bounded local Reflective Inspection layer over the
existing Phase 3.1–3.5 developmental histories and the Operator TUI
transcript. Phase 3.7 is the next step in the macro-campaign that
culminates in Phase 3.8 Operator Stream Interaction.

## 2. Why Phase 3.7 follows the Phase 3.6 audit recommendation

The Phase 3.6 audit (§15, recommended next mission) explicitly calls
for *Phase 3.7 Text Stream Ingress* — bounded local raw text chunks
below the `PerceptEvent` / `tick()` promotion boundary. The campaign in
`CURRENT_CAMPAIGN.md` confirms the same sequence:

```text
3.6 Reflective Inspection      -> 3.7 Text Stream Ingress
3.7 Text Stream Ingress        -> 3.8 Operator Stream Interaction
3.8 Operator Stream Interaction -> 3.8b LLM Runtime Toggle
```

Phase 3.7 is the cheapest safe step that:

```text
introduces a bounded local substrate for raw operator/system text
preserves every existing I-* row
introduces no operator command surface (Phase 3.8 owns /stream commands)
introduces no real LLM call (Phase 3.8b owns the LLM runtime toggle)
introduces no new TLICA runtime mutation route
keeps any promotion candidate strictly below PerceptEvent / tick()
```

## 3. Text Stream Ingress thesis

The Phase 3.7 layer introduces five bounded local records below the
existing kernel boundary:

```text
TextStreamChunk = bounded local raw/operator text evidence
TextStreamHistory = copy-on-write bounded local history
SegmentCandidate = structural span/delimiter candidate, not a language parse
StreamPattern = recurrence-backed structural pattern, not truth/PRESERVE
StreamPromotionCandidate = explicit candidate, not yet a PerceptEvent
```

Each of these is a frozen developmental record with bounded printable
fields and exact `int` / `Fraction` arithmetic. None of them is a
`PerceptEvent`, an `Act`, an `AgencyWitness`, a `feasibleProjectedPCE`,
or any TLICA runtime object.

## 4. Sources covered

The Phase 3.7 layer ingests bounded raw text from a finite closed set of
source kinds:

```text
OPERATOR        operator-typed text (later fed by Phase 3.8 /stream)
SYSTEM          deterministic local-system text (e.g. fixture-injected)
PROBE_ECHO      echo of an existing operator/system chunk
GENERATED       deterministic local generation tag (fixture-injected)
```

`OPERATOR` here means the wrapper operator, *not* a model-backed agent.
A real LLM source is *not* introduced in Phase 3.7; the explicit
LLM Runtime Toggle is Phase 3.8b and uses the existing `LLMClient` /
`tick(..., client, ...)` seam, never a second classification path.

`COGITO_ID` cannot appear as a chunk text, a chunk source, or a
promotion-candidate target. The chunk validators reject any field that
collides with the reserved sentinel.

## 5. Local evidence boundaries

The Phase 3.7 layer is strictly downstream of operator/system text. The
data flow is one-way:

```text
operator / system / fixture-injected raw text
    -> TextStreamChunk
    -> TextStreamHistory
    -> SegmentCandidate / StreamPattern (recurrence-backed)
    -> StreamPromotionCandidate (explicit, not yet a PerceptEvent)
    -> Phase 3.8 /stream-promote -> existing PerceptEvent + tick() route
```

The reverse path is closed:

```text
TextStreamHistory -> BrainState / MSI / PtCns / registry / tick /
                     PerceptEvent / traces / scenarios / source histories
                                                              NOT ALLOWED
```

## 6. Why this is not language

Phase 3.7 introduces no parser, lexicon, grammar, syntax tree, dialogue
state, utterance synthesizer, speaker model, intent classifier,
translator, or natural-language teacher / corrector. It introduces:

```text
bounded raw text bytes / printable strings
deterministic structural segmentation (e.g. delimiter spans, line
  splits, whitespace runs)
recurrence-backed structural patterns (no parse)
```

No part of Phase 3.7 claims meaning, semantic equivalence, or
truth-of-utterance. A `SegmentCandidate` is a *span*, not a parse tree;
a `StreamPattern` is a *recurrence-backed structural shape*, not a
grammar production.

## 7. Why this is not truth or PRESERVE

A `StreamPattern` is *not* a TLICA `PRESERVE` claim. It does not enter
`PtCns.evaluate`, does not appear in `MSI.contents`, does not affect any
`ScalarProfile.values`, and does not contribute to mode dispatch. It is
local recurrence evidence below the kernel.

A `StreamPromotionCandidate` is explicitly *not* a `PerceptEvent`. It
carries the structural span / pattern provenance, the source kind, a
non-reserved candidate ID, and the bounded text payload, but it is *not*
a runtime event until Phase 3.8 `/stream-promote` validates it and
constructs a real `PerceptEvent` for `tick()`.

## 8. Why this is not agency

Phase 3.7 cannot:

```text
choose an Act
construct an AgencyWitness
mutate BrainState / MSI / PtCns / ContentRegistry
emit a PerceptEvent
schedule a tick
register a callback
invoke any side-effecting host capability
weight an existing PCE / ProjectedPCE / mode dispatch decision
```

Phase 3.7 is a strictly observational substrate. The
`StreamPromotionCandidate` is a *candidate*, not an agency witness; it
is queued for explicit operator action in Phase 3.8 only.

## 9. Anti-growth and boundedness

Raw text inputs are unbounded by nature; Phase 3.7 is *not*. The layer
locks bounded ranges (the binding artifact is the catalog patch plan,
Step 13):

```text
TextStreamChunk.text                 bounded printable, length capped
TextStreamChunk metadata             bounded printable IDs / tags
TextStreamHistory                    copy-on-write, bounded ring
SegmentCandidate count               capped per chunk
StreamPattern recurrence threshold   exact non-trivial recurrence count
StreamPromotionCandidate count       capped per history
```

Repeated identical chunks must not inflate `StreamPattern` strength
beyond the recurrence cap. Huge chunks are rejected at construction;
silent truncation is forbidden on the chunk text path. The exact
constants are locked in the corrigenda and bound in the catalog patch
plan.

## 10. COGITO_ID defenses

```text
TextStreamChunk.text        cannot equal COGITO_ID (sentinel collision)
TextStreamChunk.chunk_id    cannot equal COGITO_ID
StreamPromotionCandidate.target_content_id cannot equal COGITO_ID
StreamPromotionCandidate construction rejects any reserved-id collision
                                                  before queueing
```

The constructor validators reuse the existing
`brain/_catalog_ids.py` reserved sentinel and the existing
`require_printable_id` discipline.

## 11. Non-goals

```text
no operator command surface for the new layer (Phase 3.8)
no LLM-backed substrate (Phase 3.8b explicit toggle)
no Mode B planning / replay / future-state simulation
no language understanding / parser / grammar / chat
no natural-language teacher / corrector
no real LLM calls
no host execution / subprocess / shell / network I/O
no filesystem save / export path
no scenario or trace schema change
no PerceptEvent / tick() promotion route from inside the substrate
no TLICA runtime mutation
no new permission to weaken any existing I-* row
no implicit serialization of source histories
no cross-invocation persistence
no aggregate "quality" / "intelligence" / "social-success" stream score
```

## 12. Risks

```text
Scope creep — TextStream could be misread as a chat/dialogue surface.
              The catalog rows must phrase the layer as bounded raw
              text evidence, not language.

Truth drift — StreamPattern could be misread as a TLICA PRESERVE
              claim. The catalog rows must explicitly disclaim
              truth/PRESERVE/agency on StreamPattern.

Boundary erosion — A future contributor could want the substrate to
                   call tick() directly. The catalog rows must forbid
                   this; promotion is /stream-promote (Phase 3.8) only.

Anti-growth failure — Repeated identical chunks could be misread as
                      proof of a stable PRESERVE claim. The catalog
                      rows must cap the recurrence-backed pattern
                      strength and forbid promotion-by-recurrence-alone.

LLM temptation — A live LLM-backed stream is tempting; Phase 3.7 must
                 defer LLM-backed behavior to the explicit Phase 3.8b
                 toggle.

UI temptation — Operator commands are tempting; Phase 3.7 must defer
                them to Phase 3.8.

COGITO collision — A future contributor could try to map a stream
                   chunk text to COGITO_ID for "harmless" testing.
                   The catalog rows must hard-reject any COGITO_ID
                   appearance on chunk text, chunk_id, or
                   promotion-candidate target_content_id.
```

## 13. Anticipated catalog impact

This is a working sketch only; the binding artifact is the catalog patch
plan (Step 13). Likely shape:

```text
+ N REQUIRED rows for bounded TextStreamChunk construction,
  copy-on-write bounded TextStreamHistory, deterministic exact stream
  feature extraction, structural-only SegmentCandidate, recurrence-
  backed StreamPattern, explicit StreamPromotionCandidate provenance,
  COGITO_ID defenses, anti-growth behavior under repeated/huge chunks,
  no-direct-tick discipline, and no-source-history mutation
+ a small number of STRUCTURAL rows for frozen records and a static
  audit of the text_stream module (no I/O / shell / network / LLM /
  TLICA / tick / curses imports)
+ 1 OBSERVED row for the aggregate stream-history walk
+ optionally 1 NOT-EXERCISED row for a stream save / export placeholder
```

The exact counts, IDs, and statuses are decided in
`PHASE3_7_TEXT_STREAM_INGRESS_CATALOG_PATCH_PLAN.md`, after the kickoff
and corrigenda. Likely row family: `I-STRM-*`.

## 14. Relation to Phase 3.6 Reflective Inspection

Phase 3.6 produced read-only summaries over the existing developmental
histories. Phase 3.7 introduces a *new* developmental history
(`TextStreamHistory`) below the kernel. After Phase 3.7 lands, the
existing Reflective Inspection layer can be extended in a future
campaign to summarize the new history; that extension is *not* in scope
here. Phase 3.7 leaves `brain/development/reflective.py` unchanged.

## 15. Next artifact

```text
PHASE3_7_TEXT_STREAM_INGRESS_KICKOFF.md
```

The kickoff will commit to the concrete record shapes, the finite source
enumeration, the bounded fields, the construction discipline
(deterministic, exact, source-non-mutating, no direct tick), and the
relationship of `StreamPromotionCandidate` to the existing
`PerceptEvent` / `tick()` route (without authorizing the operator
command surface, which is Phase 3.8). The corrigenda will audit the
kickoff. The catalog patch plan (Step 13) will bind the audited result
to row IDs and statuses, stopping at the review gate.
