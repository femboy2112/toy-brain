# PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md

## Purpose

This is a roadmap artifact. It does not authorize implementation of
either Operational SelfModel or Growth Ledger. It does not edit
`brain/**`, `tools/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, `lean_reference/**`,
`scenarios/**`, or `traces/**`, and it does not change runtime
behavior.

Phase 3.12c has now landed two bounded substrates that did not exist
when the Phase 3.12 mission was first opened:

- **Pattern Ledger** (`brain/development/pattern_ledger.py`,
  catalog v0.21, `I-PLEDGER-01..18`). A bounded session-local,
  copy-on-write developmental record of recurring structural
  patterns observed in stream histories, with deterministic ids,
  exact `Fraction` confidence, recurrence saturation at
  `STREAM_PATTERN_RECURRENCE_MAX`, evidence-list caps at
  `PATTERN_LEDGER_EVIDENCE_MAX`, max-entry refusal at
  `PATTERN_LEDGER_MAX_ENTRIES`, and integration through a single
  `observe(...)` call site at the end of the successful path of
  `_dispatch_stream_append`.
- **Coherence Monitor** (`brain/development/coherence_monitor.py`,
  catalog v0.22, `I-COHMON-01..14`). A bounded read-only
  structural diagnostic that consumes the existing kernel,
  operator session, stream, Pattern Ledger, persistence-config,
  and autosave-config records and produces a bounded printable
  `CoherenceReport` describing whether those substrates remain
  mutually consistent at a single point in time. The monitor is
  Option A (pure read-only helper API): no `OperatorSession` slot,
  no new `OperatorCommand`, no new view, no DB open, no autosave
  / persistence call.

The next two design layers in the Phase 3.12 vocabulary —
**Operational SelfModel** and **Growth Ledger** — are still
unimplemented and must come after these two substrates because:

- Pattern Ledger provides bounded structural recurrence evidence;
  without it SelfModel would have no inspectable record of
  recurring exposure, and Growth Ledger would have no clean
  "pattern strengthened" event.
- Coherence Monitor provides bounded read-only state consistency
  reporting; SelfModel should *reference facts from those
  substrates rather than invent self-claims*. A SelfModel that
  has no Coherence Monitor available has to compute its own
  consistency report — which is exactly the cognitive-layer
  scope creep this campaign is designed to avoid.
- Growth Ledger should count *accepted, constructor-validated
  growth events*, not raw quantity or model verbosity. The
  outcome-detection contract that Step 11 (Pattern Ledger
  `observe(...)`) and the existing Phase 3.10c autosave trigger
  set both depend on is the natural shape for the Growth Ledger's
  event semantics.

The roadmap below describes what these layers should be, what
guardrails they must respect, and how the campaign should
sequence them — but it stops at Step 16 Review Gate D.
Implementation is not authorized by this file alone.

## Baseline

```text
Catalog version:                  v0.22
Counts:
  REQUIRED:                       240
  STRUCTURAL:                      85
  NOT-EXERCISED:                   11
  DEFERRED:                        14
  OBSERVED:                        16
Branch:                           campaign/phase3-12-coherent-i-loop-observatory
Phase 3.11:                       complete; PR #10 merged at 98b55ab
Phase 3.12 steps complete (in commit order on this branch):
  Step 1  566b109  coherent i-loop mission sync
  Step 2  631ae5a  coherent i-loop synthesis
  Step 3  c395989  coherent i-loop kickoff
  Step 4  10a93ee  coherent i-loop matrix
  Step 5  (Review Gate A — passed implicitly by Step 6 execution)
  Step 6  c65d37b  coherent i-loop observatory report
  Step 7  013585e  pattern ledger synthesis
  Step 8  7839f7d  pattern ledger kickoff + corrigenda
  Step 9  ffbe4d9  pattern ledger catalog patch plan
  Step 10 (Review Gate B — ACCEPT PLAN AS WRITTEN)
  Step 11 05e214c  implement pattern ledger option A
  Step 12 cfb43dc  coherence monitor synthesis + catalog patch plan
  Step 13 (Review Gate C — ACCEPT PLAN AS WRITTEN)
  Step 14 95f3057  implement coherence monitor option A
Pattern Ledger status:
  Option A implemented as accepted at Review Gate B.
  I-PLEDGER-01..15 REQUIRED (15) — live and green.
  I-PLEDGER-16 STRUCTURAL (1) — live and green.
  I-PLEDGER-17 DEFERRED — /pattern-ledger UI not in v1.
  I-PLEDGER-18 NOT-EXERCISED — end-to-end dry run not in v1.
Coherence Monitor status:
  Option A implemented as accepted at Review Gate C.
  I-COHMON-01..11 REQUIRED (11) — live and green.
  I-COHMON-12 STRUCTURAL (1) — live and green.
  I-COHMON-13 DEFERRED — /coherence-summary UI not in v1.
  I-COHMON-14 NOT-EXERCISED — end-to-end dry run not in v1.
Step 11 deviation note (still in effect):
  brain/ui/fixtures/persistence_observe_resource_audit.py and
  brain/ui/fixtures/persistence_ops_resource_audit.py each carry
  a _PHASE_3_12C_SESSION_ATTRS = frozenset({"pattern_ledger"})
  tier that authorizes the Pattern Ledger field's presence in
  OperatorSession.__slots__. The operator ACCEPTED this deviation
  AS JUSTIFIED at the start of Step 12. Step 14 added no
  OperatorSession field and required no new audit tier; both
  Coherence Monitor records live entirely outside OperatorSession.
Step 15 stop condition:
  Step 16 Review Gate D (no implementation in this step).
Preflight (verified at the start of Step 15):
  python3 -m tools.catalog counts     PASS  (240/85/11/14/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (333 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Operating Definition

The Phase 3.12 mission anchors a strict operational use of "I":

```text
Operational I means a bounded self-description record anchored to
repo-local state and constraints. It is exactly what the running
system can quote about itself by reading existing bounded records
(BrainState, OperatorSession, TextStreamHistory, PatternLedger,
CoherenceReport, the future Growth Ledger) without inventing
anything.
```

Operational I does **not** mean:

- consciousness
- sentience
- subjective experience
- semantic understanding
- truth authority over raw text
- agency
- self-modification of code, fixtures, the catalog, or the
  runtime
- personhood

These exclusions are not merely aspirational. They are enforced
structurally:

- The existing `I-STRM-08` / `I-STRM-09` / `I-STRM-10` /
  `I-UISTRM-*` discipline keeps raw text from mutating
  `BrainState`, MSI, PtCns, ContentRegistry, source histories,
  or `OperatorSession.event_queue`.
- The Step-11 Pattern Ledger discipline (`I-PLEDGER-13` /
  `I-PLEDGER-14` / `I-PLEDGER-15`) keeps recurrence evidence away
  from `tick()` and away from any LLM client.
- The Step-14 Coherence Monitor discipline (`I-COHMON-08` /
  `I-COHMON-10` / `I-COHMON-11` / `I-COHMON-12`) keeps the
  diagnostic substrate away from DB / autosave / `tick()` / LLM
  and forbids disallowed non-claim terms in module source and
  in generated bounded printable strings.

Any Operational SelfModel / Growth Ledger work must inherit those
constraints and add no new claim language.

## Operational SelfModel Concept

**SelfModel** is a future bounded read-only or constructor-only
record that *summarizes selected facts already recorded by the
existing substrates*. The record exists so the running system can
quote a single bounded printable description of itself without
re-deriving the underlying agreements.

Proposed record shape (illustrative; final names locked at
synthesis time):

```python
@dataclass(frozen=True, slots=True)
class SelfModel:
    self_model_id:                str             # not COGITO_ID
    anchor_id:                    str             # must equal COGITO_ID
    catalog_version:              str             # e.g. "v0.22"
    tick_counter:                 int
    profile_domain_size:          int
    msi_size:                     int
    registry_size:                int
    stream_chunk_count:           int
    stream_candidate_count:       int
    pattern_ledger_entry_count:   int
    latest_coherence_status:      str             # CoherenceCheckStatus.value
    known_constraints:            tuple[str, ...]
    known_capabilities:           tuple[str, ...]
    known_non_claims:             tuple[str, ...]
    provenance:                   str
```

Field semantics:

- ``self_model_id``. Bounded printable identifier for the model
  instance. Must not equal ``COGITO_ID``. The deterministic id
  scheme should follow the Pattern Ledger precedent (e.g.
  ``"selfmodel:" + sha256(...)[:16]``) once the input fields are
  locked.
- ``anchor_id``. **Must equal** ``COGITO_ID``. The SelfModel is
  anchored to the cogito sentinel; it does not replace it.
- ``catalog_version``. A bounded printable quote of the catalog
  banner at the time the SelfModel was built. The SelfModel does
  **not** invent or assert a catalog version; it quotes what is
  on disk.
- ``tick_counter``, ``profile_domain_size``, ``msi_size``,
  ``registry_size``, ``stream_chunk_count``,
  ``stream_candidate_count``, ``pattern_ledger_entry_count``.
  Non-negative int counts pulled verbatim from the live records.
  No arithmetic, no aggregation, no scoring.
- ``latest_coherence_status``. The ``value`` of the most recent
  :class:`CoherenceCheckStatus` returned by
  ``build_coherence_report(...)``. The SelfModel does not run the
  monitor; the caller passes a fresh report or its overall status.
- ``known_constraints`` / ``known_capabilities`` /
  ``known_non_claims``. Bounded printable tuples of catalog-row
  quotations or design-doc quotations, written as factual short
  phrases. None are claims about interior state.
- ``provenance``. A bounded printable string describing how this
  SelfModel was built (e.g. ``"build_self_model(session)"``).

SelfModel **must**:

- Be a frozen / slotted dataclass.
- Be constructor-validated against the same bounds the Pattern
  Ledger and Coherence Monitor records use (printable, non-empty,
  size-capped, non-`COGITO_ID` on every id-bearing field except
  `anchor_id`, exact int counts).
- Reference Coherence Monitor output where possible: in v1 the
  caller should pass the latest `CoherenceReport.overall_status`
  rather than have the SelfModel re-derive consistency.

SelfModel **must not**:

- Be ``COGITO_ID``. The SelfModel is a *summary record* anchored
  to the cogito; it does not replace it.
- Overwrite ``COGITO_ID`` in any other record.
- Mutate ``BrainState``, ``MSI``, ``PtCns``, ``ContentRegistry``,
  source histories, ``OperatorSession``, the Pattern Ledger, the
  Coherence Monitor records, the persistence configuration, or
  the autosave configuration.
- Call ``tick(...)``.
- Call any LLM client, open any DB, perform any I/O, network,
  shell, subprocess, or filesystem operation.
- Contain or emit any forbidden non-claim term (the same closed
  set the Coherence Monitor's `I-COHMON-11` audit enforces).
- Contain any scalar that purports to summarize interior state
  ("I-ness score", "awareness level", "growth score",
  "intelligence quotient", "personality vector", etc.).
- Be implicitly persisted or autosaved. v1 SelfModel is
  build-on-demand only.

## Growth Ledger Concept

**Growth Ledger** is a future bounded developmental record of
*accepted growth events*. It is built incrementally as the system
runs and exposes the bounded historical signal that SelfModel and
any later behavior audit can quote.

Candidate event types (final names locked at synthesis time):

```text
STREAM_CHUNK_ACCEPTED
PATTERN_ENTRY_CREATED
PATTERN_ENTRY_UPDATED
STREAM_PROMOTION_QUEUED
TICK_SUCCEEDED
PROFILE_DOMAIN_ADDED
MSI_MEMBER_ADDED
SESSION_SAVED
SESSION_LOADED
COHERENCE_REPORT_BUILT
```

Each event is a frozen / slotted record with:

```text
event_id          bounded printable, not COGITO_ID
event_type        finite closed enum (one of the values above)
tick              non-negative int (the session.tick_counter at
                  the time the event was recorded)
source            closed-enum label naming the dispatcher /
                  builder that produced the event
references        tuple of bounded printable record ids the event
                  refers to (chunk_id, candidate_id, pattern_id,
                  snapshot_id, autosave status snapshot id, etc.)
provenance        bounded printable str
```

The Growth Ledger itself is a bounded copy-on-write collection:

```text
GrowthLedger.events    tuple[GrowthEvent, ...]
GrowthLedger.observe   pure copy-on-write entry point that records
                       one event; saturates / deduplicates by
                       event_type + references + tick when
                       appropriate
GrowthLedger.snapshot  read-only printable summary view (counts
                       per event_type)
```

Growth Ledger **must**:

- Record *only successful, constructor-validated events*. The
  Phase 3.10c autosave outcome-detection contract is the
  canonical precedent: an event is recorded iff its source
  dispatcher returned a positive outcome through the same return
  value the dispatcher already exposes for autosave.
- Deduplicate / saturate against the obvious anti-Goodhart
  attacks (the same `STREAM_CHUNK_ACCEPTED` event delivered twice
  for the same chunk_id is a no-op; an unbounded run of
  `STREAM_PROMOTION_QUEUED` saturates at a configured cap).
- Stay bounded (`GROWTH_LEDGER_MAX_EVENTS` constant; behavior at
  cap is "hard refusal of new events" mirroring the
  Pattern Ledger LOCK E pattern unless the synthesis explicitly
  picks a different rule and the operator accepts it at the
  review gate).
- Use deterministic event ids when possible (e.g.
  ``"grow:" + sha256(repr((event_type, references, tick))).hexdigest()[:16]``)
  or monotone bounded local ids (e.g. ``"grow-N"``).

Growth Ledger **must not**:

- Be a reward function. No event has a numeric reward value, and
  no aggregate "reward" / "score" / "fitness" / "happiness"
  scalar appears anywhere in the surface.
- Be an intelligence score, an "I-ness" score, a consciousness
  score, an awareness score, or any other scalar purporting to
  summarize interior state.
- Count failed parse, failed dispatch, failed tick, read-only
  command, or raw LLM proposals as growth. The
  outcome-detection contract is the canonical filter.
- Inflate growth on repeated spam: the same input must
  saturate or deduplicate (see anti-Goodhart bullet above).
- Mutate `BrainState`, `MSI`, `PtCns`, `ContentRegistry`, source
  histories, `OperatorSession.event_queue`, `stream_history`,
  `stream_candidates`, `stream_chunk_serial`, the Pattern Ledger,
  the Coherence Monitor records, the persistence configuration,
  or the autosave configuration.
- Call `tick(...)`, any LLM client, or any DB / autosave /
  filesystem / network / shell / subprocess.
- Persist itself in v1 unless explicitly reviewed (see Open
  Design Decisions below).

## Relationship Between SelfModel and Growth Ledger

The four substrates compose cleanly:

```text
                +-------------------+
                |  Pattern Ledger   |    bounded structural recurrence
                |  (Step 11)        |    evidence over /stream history
                +-------------------+
                          |
                          | recurrence evidence
                          v
+--------------------+    |    +---------------------+
| Coherence Monitor  | <--+--> | Growth Ledger       |
| (Step 14)          |         | (proposed; deferred)|
| read-only struct.  |         | accepted-event log  |
| consistency report |         | over time           |
+--------------------+         +---------------------+
          ^                              ^
          |                              |
          | latest_coherence_status      | event counts and quotations
          |                              |
          +--------------+---------------+
                         |
                         v
                +-------------------+
                |  SelfModel        |   bounded read-only quotation
                |  (proposed;       |   record built from the
                |   deferred)       |   substrates above
                +-------------------+
```

Specifically:

- **Pattern Ledger** records bounded structural exposure — what
  has been seen, how often, with what evidence ids.
- **Coherence Monitor** reports current consistency — whether
  the kernel, the session, the stream, the Pattern Ledger, the
  persistence config, and the autosave config still agree.
- **Growth Ledger** records bounded historical accepted events —
  what successfully happened, when, on which records.
- **SelfModel** summarizes selected facts from these sources.
  It does **not** infer beyond those facts. The catalog rows
  for SelfModel (when proposed at a later synthesis) must lock
  this read-only quotation discipline structurally, the same way
  `I-COHMON-11` locks the non-claim discipline for the Coherence
  Monitor.

The dependency arrow points only one way: SelfModel → Growth
Ledger → (Pattern Ledger, Coherence Monitor, kernel records).
None of the upstream substrates may depend on SelfModel.

## Recommended Sequencing

Implementing Growth Ledger **before** SelfModel is the
recommended order, because SelfModel should consume a bounded
growth record rather than invent "growth" from current state
alone. Concretely:

```text
1. Growth Ledger synthesis
     - Define record shape, event enum, anti-Goodhart rules,
       persistence policy, integration points, non-claims.
     - Documentation only.

2. Growth Ledger kickoff + corrigenda
     - Resolve every open design decision (persistence, observe
       trigger set, event id scheme, saturation rule, UI policy).
     - Documentation only.

3. Growth Ledger catalog patch plan
     - Propose I-GROW-* (or equivalent) row family with exact
       status assignments (REQUIRED / STRUCTURAL / DEFERRED /
       NOT-EXERCISED / OBSERVED).
     - Stop at the next review gate.

4. Review gate
     - Operator chooses ACCEPT PLAN AS WRITTEN / ACCEPT WITH
       AMENDMENTS / REJECT-REVISE.

5. Growth Ledger implementation
     - Apply the accepted plan within the declared file surface.
     - Validate every gate green; commit and push.

6. SelfModel synthesis
     - Now that Growth Ledger exists, the SelfModel record shape
       can include accepted-growth-event counts as facts rather
       than derive them.

7. SelfModel kickoff + corrigenda
     - Resolve every open SelfModel design decision (anchor_id
       check shape, deterministic self_model_id, on-demand vs
       session-local lifecycle, constraints list source).

8. SelfModel catalog patch plan
     - Propose I-SELF-* (or equivalent) row family with exact
       status assignments.
     - Stop at the next review gate.

9. Review gate
     - Operator chooses ACCEPT PLAN AS WRITTEN / ACCEPT WITH
       AMENDMENTS / REJECT-REVISE.

10. SelfModel implementation
     - Apply the accepted plan within the declared file surface.
     - Validate every gate green; commit and push.
```

Why Growth Ledger first:

- A SelfModel that summarizes "growth" in terms of current state
  only (e.g. "tick_counter is 42") is unstable: tick_counter
  resets on a fresh session, and there is no way to distinguish
  "42 ticks of meaningful growth" from "42 empty-step ticks". A
  Growth Ledger that records accepted growth events with
  outcome-detected provenance gives SelfModel a stable factual
  surface to quote.
- The Growth Ledger's event types map cleanly to existing
  dispatchers (`_dispatch_stream_append`,
  `_dispatch_stream_promote`, `_dispatch_step`,
  `_dispatch_save_session`, `_dispatch_load_session`, and the
  monitor's `build_full_coherence_report(...)`), which means the
  v1 implementation can lean on the same outcome-detection
  contract that already powers Phase 3.10c autosave.
- The Growth Ledger does not require SelfModel to ship.
  Conversely, SelfModel shipping before Growth Ledger would
  either force SelfModel to invent its own growth signal (scope
  creep into a cognitive layer) or force SelfModel to be
  re-shaped a second time when Growth Ledger lands. One
  re-shape is better than two.

## Proposed Growth Ledger Guardrails

Locked-shape proposals for the Growth Ledger synthesis to honor.
Final values may be amended at the review gate, but the
substantive content of each guardrail must survive any amendment
that purports to "open up" the Growth Ledger surface.

- **Bounded max events.** The ledger holds at most
  `GROWTH_LEDGER_MAX_EVENTS` events (proposed `1024`). Behavior
  at cap is hard refusal of new events (mirrors LOCK E from the
  Pattern Ledger corrigenda) unless the synthesis explicitly
  picks a different rule and the operator accepts it at the
  review gate.
- **Exact event enum.** `GrowthEventType` is a finite closed
  `(str, Enum)`-shaped class. Adding or removing a member is a
  catalog-version-bump operation, not an in-place edit.
- **No raw text payload except references.** Events store
  bounded printable record ids (`chunk_id`, `candidate_id`,
  `pattern_id`, `snapshot_id`, autosave-status snapshot id) but
  not the raw chunk text. The text already lives in the source
  histories; the ledger is a referencing layer.
- **No `COGITO_ID` as event id.** `event_id` must not equal
  `COGITO_ID`. Every `references` element must not equal
  `COGITO_ID`. `provenance` must not equal `COGITO_ID`.
- **No `BrainState` mutation.** Across every `observe(...)`
  call, `BrainState`, `MSI`, `PtCns`, `ContentRegistry`,
  `latest_tick`, `tick_counter`, source histories,
  `OperatorSession.event_queue`, `stream_history`,
  `stream_candidates`, `stream_chunk_serial`, the Pattern
  Ledger, and the Coherence Monitor records are identity-stable.
- **No `tick(...)` call.** The Growth Ledger does not import
  `brain.tick` at runtime callable level; the `BrainState` typed
  record may be imported as a type only.
- **No LLM client.** No field stores or accepts an object with
  `eval_consistency`. The static AST audit must reject
  `brain.llm` imports.
- **No persistence in first version unless explicitly
  reviewed.** v1 Growth Ledger is session-local (mirrors LOCK B
  from the Pattern Ledger corrigenda). `/save-session` does not
  serialize the ledger; `/load-session` does not restore it;
  `_maybe_autosave_after_dispatch` is not extended. Any future
  persistence requires its own reviewed catalog patch.
- **No aggregate growth score in first version.** No field,
  method, or output is a scalar in `[0, 1]` / `[0, n]`
  purporting to summarize total growth. Per-event-type counts
  (deterministic tuple of `(event_type.value, count)` pairs,
  mirroring the Coherence Monitor's `counts_by_status`) are
  allowed; aggregate scalars are not.
- **Deterministic event ids or monotone bounded local ids.**
  Either `"grow:" + sha256(repr((event_type, references,
  tick))).hexdigest()[:16]` (defensive against id collisions)
  or `"grow-N"` (monotone session-local). The synthesis picks
  one and locks it.
- **Anti-Goodhart saturation / deduplication.** Re-recording the
  same `(event_type, references, tick)` triple is a no-op; the
  ledger does not double-count. Long runs of legitimate but
  low-information events (e.g. a thousand
  `STREAM_CHUNK_ACCEPTED` events from a single repeated input)
  must either be bounded by `GROWTH_LEDGER_MAX_EVENTS` (hard
  refusal at cap) or saturate at a per-event-type cap that the
  synthesis fixes explicitly.
- **Copy-on-write if modeled as a developmental history.**
  `GrowthLedger.observe(...)` returns a NEW ledger; the
  original `events` tuple is unchanged.

## Proposed SelfModel Guardrails

Locked-shape proposals for the SelfModel synthesis to honor.
Same amendment discipline as the Growth Ledger guardrails above.

- **Bounded fields only.** Every field is a bounded primitive, a
  tuple of bounded primitives, an int count, or a closed-enum
  value. No field is a callable, file handle, socket, subprocess
  handle, `pathlib.Path`, `sqlite3.Connection`/`Cursor`, curses
  object, or LLM client.
- **Constructor-enforced values.** Mirror the Pattern Ledger and
  Coherence Monitor record constructors: bounded printable
  identifiers, non-negative int counts, frozen / slotted
  dataclass, no silent normalization.
- **`anchor_id` must equal `COGITO_ID`; `self_model_id` must
  not.** `anchor_id != COGITO_ID` raises at construction time;
  `self_model_id == COGITO_ID` raises at construction time.
  This is the structural form of the "SelfModel is anchored to
  the cogito but is not the cogito" rule.
- **No claim strings using forbidden experiential / subjective /
  semantic / truth / agency / self-modification language.** The
  closed forbidden-terms list is the same one Coherence Monitor
  already locks (`I-COHMON-11`); the SelfModel module
  inherits it. Static AST audit + runtime audit over the
  bounded printable summary string.
- **No "I am conscious" / "I understand" / "I believe" / "I
  intend" / "I want" / "I feel" / "I know" / "I will" strings.**
  Defensive duplication against the forbidden-terms list. The
  audit treats first-person + verb of subjective experience or
  intent as an outright fail.
- **No autonomous action selection.** SelfModel does not call
  `tick(...)`, does not enqueue percepts, does not promote
  candidates, does not save / load / back up the session, and
  does not enable / disable autosave.
- **No mutation of kernel or developmental state.**
  Identity-stable across every SelfModel build call.
- **No LLM call.** No `brain.llm` import. No object with
  `eval_consistency` is stored or accepted.
- **No hidden persistence.** v1 SelfModel is build-on-demand
  only. `/save-session` does not serialize it; `/load-session`
  does not restore it; autosave is not extended.
- **No score of "I-ness".** No scalar field purports to
  summarize selfhood, awareness, growth, or any interior state.
  Counts and bounded printable tuples are allowed; scalars
  purporting to summarize "I" are not.
- **Read-only over Coherence Monitor / Pattern Ledger / Growth
  Ledger.** SelfModel reads existing records and returns a new
  bounded record. It never mutates the substrates it quotes.

## Open Design Decisions

The synthesis steps below must resolve each of these questions
before the corresponding catalog patch plan is written.

- **Should Growth Ledger be session-local first or persist
  through the existing session DB?** v1 default proposal is
  *session-local first* (LOCK B precedent). A future reviewed
  patch could add a `growth_events` table and the corresponding
  `I-PERSIST-*`-style discipline. Persisting in v1 doubles the
  implementation surface and risks `SCHEMA_VERSION_V*` churn.
- **Should Growth Ledger observe events in `OperatorSession`
  dispatch, or be built from reports after the fact?** v1
  default proposal is *dispatch-time observe*, gated by the
  Phase 3.10c outcome-detection contract (the same boolean
  return value the autosave trigger reads). Building from
  reports after the fact would require parsing status / error
  strings, which violates the existing `I-AUTOSAVE-14`
  outcome-detection discipline.
- **Should SelfModel be session-local only or generated on
  demand?** v1 default proposal is *generated on demand*, the
  same way `build_full_coherence_report(...)` works. A
  session-local SelfModel field would add a new
  `_PHASE_3_13_SESSION_ATTRS` tier to the persistence resource-
  audit fixtures (the Step 11 deviation precedent); on-demand
  generation avoids that.
- **Should SelfModel include current catalog counts as facts?**
  Probable yes: the catalog version + counts are factual quotes
  from `INVARIANT_CATALOG.md`. The synthesis must lock the read
  path so the SelfModel never invents a catalog version or
  count.
- **Should SelfModel include latest `CoherenceReport` or only
  summary status?** Probable answer: only the
  `overall_status.value` and `counts_by_status` should be
  embedded. Embedding the full report risks bloating the
  SelfModel record and re-exposing the Coherence Monitor's
  check_id / detail strings inside a record that has its own
  audit surface.
- **How should forbidden self-claim terms be audited without
  blocking legitimate "non-claim" documentation?** The
  Coherence Monitor precedent works: keep the canonical
  forbidden-terms list in a single constant and exempt that
  constant's line range from the source-text scan. Apply the
  same scheme to the SelfModel and Growth Ledger static audits.
- **Should Growth Ledger include `SESSION_SAVED` /
  `SESSION_LOADED` events if v1 is session-local and not
  persisted?** Open. Arguments for: `/save-session` /
  `/load-session` are accepted, constructor-validated growth
  events at the substrate level even if the Growth Ledger
  itself does not persist. Arguments against: a Growth Ledger
  that is not persisted will lose its `SESSION_LOADED` events
  on the very session that loads, which is confusing. The
  synthesis must decide and lock the choice.

## Non-goals

The Step 15 roadmap must **not**:

- implement Operational SelfModel or Growth Ledger in any form,
- propose catalog rows or fixtures,
- claim consciousness,
- claim sentience,
- claim subjective experience,
- claim semantic understanding,
- claim truth adjudication or assign `PRESERVE` / `DAMAGE` values
  to raw text,
- claim agency, intent, will, or desire,
- claim self-modification of code, fixtures, the catalog, or the
  runtime,
- introduce an aggregate consciousness score, "I-ness" score,
  awareness score, or any single scalar purporting to summarize
  interior state,
- emit any hidden LLM call,
- emit any hidden filesystem write, network call, subprocess
  spawn, or shell command,
- introduce hidden persistence outside the explicit
  `/save-session` / `/load-session` route,
- propose default model-backed behavior. Offline remains the
  default.

The above prohibitions are inherited from the Phase 3.12
mission, the Phase 3.11 audit, the `I-STRM-*` / `I-UISTRM-*` /
`I-PERSIST-*` / `I-OPSHARDEN-*` / `I-OBSERVE-*` / `I-AUTOSAVE-*`
/ `I-PLEDGER-*` / `I-COHMON-*` discipline, and the locks of the
two corrigenda already on the branch.

## Recommendation

Recommended outcome at Step 16 Review Gate D:

- **Stop for Review Gate D.** No SelfModel / Growth Ledger
  implementation should land inside Phase 3.12 unless the
  operator explicitly chooses to extend the campaign.
- **Prefer closing Phase 3.12 after the final audit / PR**
  (Step 17 + Step 18 as listed in `CURRENT_CAMPAIGN.md`), then
  starting a **Phase 3.13 Growth Ledger campaign**. A clean
  Phase 3.12 audit shipping a measurement-first observatory +
  bounded Pattern Ledger + bounded Coherence Monitor is a
  natural release boundary; bolting two more substrates on
  inside the same campaign would extend the branch further
  past its accepted scope and would couple the SelfModel /
  Growth Ledger design discussion to the audit that closes
  Phase 3.12.
- **If the operator wants to continue inside Phase 3.12**,
  implement Growth Ledger first and SelfModel second per the
  sequencing above. Both implementations must respect the
  guardrails sections in this document; any amendment must
  cite the guardrail it overrides.
- **If the operator wants to ship Phase 3.12 first and then
  start Phase 3.13**, this roadmap should be referenced from
  the new campaign's `CURRENT_CAMPAIGN.md` as the canonical
  design source for Growth Ledger and SelfModel.

## Step 16 Review Gate D Decision Request

Step 15 stops here. Step 16 is Review Gate D. The operator must
explicitly choose exactly one:

```text
[ ] ACCEPT ROADMAP AND DEFER IMPLEMENTATION TO FUTURE CAMPAIGN
    Close Phase 3.12 after the final audit / PR (Step 17 + Step 18)
    and start a follow-up Phase 3.13 Growth Ledger campaign that
    references this roadmap as its canonical design source.
    Recommended.

[ ] ACCEPT ROADMAP AND EXTEND PHASE 3.12 WITH GROWTH LEDGER ONLY
    Extend the campaign with Growth Ledger synthesis → kickoff /
    corrigenda → catalog patch plan → review gate →
    implementation. Defer SelfModel to a separate follow-up
    campaign. Final audit / PR shifts accordingly.

[ ] ACCEPT ROADMAP AND EXTEND PHASE 3.12 WITH GROWTH LEDGER THEN
    SELFMODEL
    Extend the campaign with both Growth Ledger and SelfModel,
    in that order, each through its own synthesis → kickoff /
    corrigenda → catalog patch plan → review gate →
    implementation. Final audit / PR shifts accordingly.

[ ] REJECT / REVISE ROADMAP
    Step 15 must be revised before any review-gate-D decision.
    Provide the revision direction.
```

Until Step 16 explicitly chooses one of the above, no file
under `brain/**`, `tools/**`, `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`lean_reference/**`, `scenarios/**`, or `traces/**` may be
modified in pursuit of either layer.

## Validation

Re-ran after writing this roadmap (no source under `brain/**`,
`tools/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, `lean_reference/**`,
`scenarios/**`, or `traces/**` was touched; only this new
documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
