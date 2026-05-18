# PHASE3_13_GROWTH_LEDGER_SYNTHESIS.md

## Purpose

Phase 3.13 follows the completed Phase 3.12 Coherent I-Loop Observatory
campaign. Phase 3.12 shipped two bounded substrates that did not exist
when this campaign series opened:

- **Pattern Ledger** (`brain/development/pattern_ledger.py`, catalog
  v0.21, `I-PLEDGER-01..18`). A bounded session-local copy-on-write
  developmental record of recurring *structural* patterns observed in
  stream histories, with deterministic ids, exact `Fraction`
  confidence, recurrence saturation at
  `STREAM_PATTERN_RECURRENCE_MAX`, evidence-list caps at
  `PATTERN_LEDGER_EVIDENCE_MAX`, max-entry refusal at
  `PATTERN_LEDGER_MAX_ENTRIES`, and integration through a single
  `observe(...)` call site at the end of the successful path of
  `_dispatch_stream_append`.
- **Coherence Monitor** (`brain/development/coherence_monitor.py`,
  catalog v0.22, `I-COHMON-01..14`). A bounded *read-only* structural
  diagnostic that consumes the existing kernel, operator session,
  stream, Pattern Ledger, persistence-config, and autosave-config
  records and produces a bounded printable `CoherenceReport`
  describing whether those substrates remain mutually consistent at
  a single point in time. The monitor is Option A (pure read-only
  helper API): no `OperatorSession` slot, no new `OperatorCommand`,
  no new view, no DB open, no autosave / persistence call.

Pattern Ledger gives *what has been seen, how often, with what
evidence ids*. Coherence Monitor gives *whether the substrates still
agree at one point in time*. Neither layer records the bounded
historical signal of *what successfully happened over time*.

The job of this synthesis is to define the **Growth Ledger** concept
that closes that historical-signal gap *without* adding semantic
truth, agency, `PtCns` evaluation, MSI mutation, raw-text →
`COGITO_ID` mapping, hidden LLM calls, hidden persistence, or any
aggregate growth / I-ness / awareness scalar. The synthesis is
**documentation only**. It does not implement, fixture, or
catalog-row the ledger; those steps remain behind Step 6
Review Gate A (`CURRENT_CAMPAIGN.md`).

Growth Ledger must count **accepted, constructor-validated events**,
never raw quantity, model verbosity, or text length. The Phase 3.10c
autosave outcome-detection contract is the canonical filter: an
event is recorded *iff* its source dispatcher returned a positive
outcome through the same return value the dispatcher already exposes
for autosave. Status / error string parsing is forbidden.

Phase 3.13 implements **Growth Ledger only**. Operational SelfModel
remains explicitly out of scope and is reconsidered only in a
separate follow-up campaign, per the Phase 3.12 Step 15 roadmap
(`docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md`).

This document does not edit `brain/**`, `tools/**`, `.claude/**`,
`INVARIANT_CATALOG.md`, `README.md`, `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**`. It introduces no fixture, no committed helper, and no
runtime behavior change.

## Baseline

```text
Catalog version:                  v0.22
Counts:
  REQUIRED:                       240
  STRUCTURAL:                      85
  NOT-EXERCISED:                   11
  DEFERRED:                        14
  OBSERVED:                        16
Branch:                           campaign/phase3-13-growth-ledger
Phase 3.12 status:                complete; PR #11 merged
Docs cleanup status:              complete; PR #12 merged
ChatGPT/Codex Stage A bridge:     complete; PR #13 merged
Phase 3.13 Step 1 status:         complete (commit 56e448e
                                  "phase3.13 step1: growth ledger
                                  mission sync"); pushed
Canonical Phase 3.13 design seed:
  docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
Existing bounded substrates already shipped:
  Pattern Ledger    brain/development/pattern_ledger.py
                    I-PLEDGER-01..18  (catalog v0.21)
  Coherence Monitor brain/development/coherence_monitor.py
                    I-COHMON-01..14   (catalog v0.22)
Active Stage A advisory bridge:
  /ask-chatgpt   .claude/commands/ask-chatgpt.md
  wrapper        tools/claude_helpers/codex_chatgpt_subagent.py
  bridge audit   CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md
  audit JSONL    .claude/codex_bridge_logs/ (gitignored)
Preflight (verified at the start of Step 2):
  python3 -m tools.catalog counts     PASS  (240/85/11/14/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (333 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Operational Definition

```text
Growth Ledger:
  A bounded developmental record of accepted, constructor-validated
  growth events produced by explicit successful runtime /
  developmental transitions. The ledger is session-local in v1,
  copy-on-write, capped at GROWTH_LEDGER_MAX_EVENTS, deduplicated
  against the obvious anti-Goodhart attacks, and never inflates
  under spam. The ledger does not call tick(), does not call any
  LLM client, does not open any DB, and does not extend
  /save-session / /load-session / autosave.

Growth event:
  A bounded record with six required fields:
    - event_id       (bounded printable, != COGITO_ID)
    - event_type     (closed enum)
    - tick           (non-negative int, session.tick_counter at
                      observe time)
    - source         (closed enum naming the dispatcher / builder
                      that produced the event)
    - references     (tuple of bounded printable record ids;
                      no element equals COGITO_ID; no raw text
                      payload)
    - provenance     (bounded printable str describing the local
                      route that produced the event)

Accepted:
  Emitted only after an existing dispatcher / builder reports
  successful mutation or successful construction through the
  Phase 3.10c outcome-detection contract that already powers
  autosave. Failed parse, failed dispatch, failed tick, and
  read-only command do not count. Status / error string parsing
  is forbidden. The ledger is append-only for accepted events
  and does not validate, reinterpret, repair, rank, or summarize
  the events it records.

References:
  Bounded printable ids pointing to existing bounded records:
  chunk_id (TextStreamChunk), candidate_id
  (StreamPromotionCandidate), pattern_id (PatternLedgerEntry),
  content_id (ContentRegistry), snapshot_id
  (CoherenceSnapshot.snapshot_id), or session operation id
  (autosave status snapshot id). Events never carry raw chunk
  text; text already lives in the source histories. References
  are immutable at observe time; no post-observe mutation is
  permitted.

Provenance:
  Bounded printable source label explaining the local route that
  produced the event (e.g. "stream_append:_dispatch_stream_append",
  "pattern_ledger:observe", "tick:_dispatch_step"). Provenance is
  fixed at observe time; it is not enriched after acceptance.

Saturation:
  The ledger must remain bounded. Repeated / spam / duplicate
  events either deduplicate (same (event_type, references, tick)
  triple is a no-op) or saturate at a per-event-type or global
  cap, but they never inflate the ledger unboundedly. The
  behavior at GROWTH_LEDGER_MAX_EVENTS is hard refusal of new
  events (mirroring Pattern Ledger LOCK E). Step 4 corrigenda
  picks a saturation cap explicitly.
```

## Proposed Record Shape

Pseudocode — not implementation. Field names, defaults, and bounds
are illustrative and may be refined in Step 3 kickoff / Step 4
corrigenda.

```python
class GrowthEventType(str, Enum):
    STREAM_CHUNK_ACCEPTED      = "stream_chunk_accepted"
    PATTERN_ENTRY_CREATED      = "pattern_entry_created"
    PATTERN_ENTRY_UPDATED      = "pattern_entry_updated"
    STREAM_PROMOTION_QUEUED    = "stream_promotion_queued"
    TICK_SUCCEEDED             = "tick_succeeded"
    PROFILE_DOMAIN_ADDED       = "profile_domain_added"
    MSI_MEMBER_ADDED           = "msi_member_added"
    SESSION_SAVED              = "session_saved"
    SESSION_LOADED             = "session_loaded"
    COHERENCE_REPORT_BUILT     = "coherence_report_built"


class GrowthEventSource(str, Enum):
    STREAM_APPEND              = "stream_append"
    PATTERN_LEDGER_OBSERVE     = "pattern_ledger_observe"
    STREAM_PROMOTE             = "stream_promote"
    STEP_DISPATCH              = "step_dispatch"
    PERSISTENCE_SAVE           = "persistence_save"
    PERSISTENCE_LOAD           = "persistence_load"
    COHERENCE_MONITOR          = "coherence_monitor"


@dataclass(frozen=True, slots=True)
class GrowthEvent:
    event_id:    str                       # bounded printable, != COGITO_ID,
                                           #   len <= GROWTH_LEDGER_ID_MAX
    event_type:  GrowthEventType
    tick:        int                       # >= 0
    source:      GrowthEventSource
    references:  tuple[str, ...]           # bounded printable; no element
                                           #   equals COGITO_ID;
                                           #   0 <= len <= GROWTH_LEDGER_REFERENCE_MAX
    provenance:  str                       # bounded printable, non-empty,
                                           #   len <= GROWTH_LEDGER_PROVENANCE_MAX


@dataclass(frozen=True, slots=True)
class GrowthLedger:
    events:      tuple[GrowthEvent, ...] = ()
    max_events:  int = GROWTH_LEDGER_MAX_EVENTS

    def observe(
        self,
        *,
        event_type: GrowthEventType,
        tick: int,
        source: GrowthEventSource,
        references: tuple[str, ...],
        provenance: str,
    ) -> "GrowthLedger":
        """Return a NEW GrowthLedger with one event appended
        (copy-on-write). Idempotent: if an event with the same
        (event_type, references, tick) triple is already present,
        return self unchanged. Hard-refuse at max_events
        (LOCK E precedent). Never mutates self. Never calls
        tick(). Never touches BrainState / MSI / PtCns / registry
        / agency / LLM."""
        ...

    def counts_by_type(self) -> tuple[tuple[str, int], ...]:
        """Return a deterministic ordered tuple of
        (event_type.value, count) pairs over the closed
        GrowthEventType enum. This is a factual summary, NOT a
        growth score; no scalar field summarizes the ledger."""
        ...

    def snapshot(self) -> "GrowthLedgerSnapshot":
        """Return a bounded printable read-only summary view,
        suitable for /growth-ledger dispatch status text and the
        renderer if a UI is later authorized."""
        ...
```

Every field is a bounded primitive, a closed-enum member, or a
tuple of bounded primitives. No field is a callable, file handle,
socket, subprocess handle, `pathlib.Path`,
`sqlite3.Connection` / `Cursor`, curses object, or LLM client.
`GrowthLedger.observe(...)` is **the sole non-construction entry
point**. It does not take a `BrainState`, it does not take an
`LLMClient`, it does not take a callable. It is pure over its
inputs and emits a new `GrowthLedger`.

## Event Vocabulary Classification

Each candidate event is classified `v1` / `deferred` / `rejected`.
"Recommendation locked in this synthesis" means the candidate is
treated as Synthesis-LOCK; the Step 4 corrigenda may amend it only
with an explicit reason.

| Event type                | Class    | Reason                                                                                                                                                       |
|---------------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `STREAM_CHUNK_ACCEPTED`   | v1       | Already gated by the existing successful path of `_dispatch_stream_append`; pure reference to `chunk_id`; matches Pattern Ledger observe site.               |
| `PATTERN_ENTRY_CREATED`   | v1       | Emitted when `PatternLedger.observe(...)` returns a ledger with a new entry not present before; reference is `pattern_id`; outcome-detected by entry delta.  |
| `PATTERN_ENTRY_UPDATED`   | v1       | Emitted when `PatternLedger.observe(...)` returns a ledger whose matching entry's `recurrence_count` strictly increased; reference is `pattern_id`.          |
| `STREAM_PROMOTION_QUEUED` | v1       | Gated by the existing successful path of `_dispatch_stream_promote` (one `QueuePerceptPayload` enqueued); reference is `candidate_id`.                       |
| `TICK_SUCCEEDED`          | v1       | Gated by the existing successful path of `_dispatch_step` (TickRecord returned without exception); reference is the TickRecord identifier (e.g. tick index). |
| `PROFILE_DOMAIN_ADDED`    | v1       | Derived only from the TickRecord / state delta after a successful tick. Recorded as an accepted addition only — never as evidence of identity, selfhood, agency, preference, truth, or durable self-model state. |
| `MSI_MEMBER_ADDED`        | v1       | Derived only from the TickRecord / state delta after a successful tick. Same wording-care as `PROFILE_DOMAIN_ADDED`.                                         |
| `SESSION_SAVED`           | deferred | Tension: v1 Growth Ledger is session-local, so `SESSION_SAVED` records a substrate-level accepted event whose ledger value is lost if the session ends before save. Defer to Step 4 LOCK F. |
| `SESSION_LOADED`          | deferred | Tension: a session-local Growth Ledger loses its `SESSION_LOADED` event on the very session that loads. Defer to Step 4 LOCK F.                              |
| `COHERENCE_REPORT_BUILT`  | deferred | Risk: framing "coherence report built" as a growth event invites a semantic / quality / correctness reading. Defer until the behavior report shows demand.   |

No event type is `rejected` in this synthesis. The deferred set may
be promoted only by an explicit Step 4 corrigenda LOCK F that fixes
the persistence-vs-loss-of-event tension and the
semantic-reading risk for `COHERENCE_REPORT_BUILT`.

**Important tension to address.** A narrower v1 is safer. The
deferred trio (`SESSION_SAVED` / `SESSION_LOADED` /
`COHERENCE_REPORT_BUILT`) interacts with persistence and with the
Coherence Monitor's diagnostic surface. Including them in v1 risks
either (a) implicit persistence semantics on a session-local ledger
or (b) implying that a coherence-report build is itself "growth",
which it is not — it is a read-only diagnostic. The recommended
position is the narrow v1 set above; the deferred trio is opened
only behind a fresh review-gate decision after the v1 behavior
report shows whether the absence is load-bearing for the future
SelfModel design (which itself remains out of Phase 3.13 scope).

## Integration Points

The likely v1 observe call sites, discussed without implementation,
all sit *at the end of the successful path* of an existing
dispatcher / builder:

```text
successful _dispatch_stream_append
  -> GrowthLedger.observe(STREAM_CHUNK_ACCEPTED,
                          references=(chunk_id,))
     and (if the same dispatcher's PatternLedger.observe(...)
          returned a created-or-updated entry delta)
     -> GrowthLedger.observe(PATTERN_ENTRY_CREATED,
                             references=(pattern_id,))
        or PATTERN_ENTRY_UPDATED with the same reference.
     The created/updated distinction is observed by comparing the
     pre-observe ledger entry tuple to the post-observe one; this
     is a pure tuple comparison, not status-string parsing.

successful _dispatch_stream_promote
  -> GrowthLedger.observe(STREAM_PROMOTION_QUEUED,
                          references=(candidate_id,))

successful _dispatch_step
  -> GrowthLedger.observe(TICK_SUCCEEDED,
                          references=(tick_record_id,))
     and (from the TickRecord / state-delta surface):
     -> GrowthLedger.observe(PROFILE_DOMAIN_ADDED,
                             references=(content_id,))     (per addition)
     -> GrowthLedger.observe(MSI_MEMBER_ADDED,
                             references=(content_id,))     (per addition)

DEFERRED — not in v1 unless Step 4 LOCK F promotes them:
  successful _dispatch_save_session -> SESSION_SAVED
  successful _dispatch_load_session -> SESSION_LOADED
  successful build_full_coherence_report -> COHERENCE_REPORT_BUILT
```

Rules — every one of these is structurally enforced by the
existing `I-AUTOSAVE-14` outcome-detection discipline and by the
Pattern Ledger `I-PLEDGER-13` / `I-PLEDGER-14` / `I-PLEDGER-15`
guardrails:

- **no observe on read-only commands.** `/state`, `/tick`,
  `/stream-summary`, `/stream-candidates`, `/session-status`,
  `/db-status`, `/db-summary`, `/profile-summary`,
  `/stream-db-summary`, `/db-diff`, `/db-verify`, `/db-backup`,
  `/autosave-status`, and any future `/coherence-summary` /
  `/growth-ledger` UI command never trigger an observe call.
- **no observe on parse failure.** `LocalCommandError` never
  reaches the observe path.
- **no observe on dispatch failure.** A dispatcher that returns
  the existing outcome-detection contract's negative signal does
  not observe.
- **no observe on tick failure.** A `tick()` exception, an empty
  queue, or a `PerceptEvent` validation failure leaves the
  Growth Ledger unchanged.
- **no status / error string parsing.** The outcome-detection
  contract reads a typed return value (`Optional[bool]` or
  equivalent), never a status / error string.
- **no direct tick call from Growth Ledger.** The module does not
  import `brain.tick` at runtime callable level; the `BrainState`
  typed record may be imported as a type only.
- **no LLM call.** No field stores or accepts an object with
  `eval_consistency`. The static AST audit must reject
  `brain.llm` imports.
- **no observe call inside `tick()`.** Observe is always
  post-dispatch from the operator session layer, mirroring how
  Phase 3.10c autosave triggers after `OperatorSession.dispatch`
  returns successfully.

## Event ID Scheme

**Locked in this synthesis (LOCK to be re-affirmed by Step 4
corrigenda).** Use deterministic SHA-256 event ids derived from
the immutable acceptance payload:

```text
event_id = "growth:" + sha256(
    repr((
        event_type.value,    # str
        tick,                # int
        source.value,        # str
        references,          # tuple[str, ...]
        provenance,          # str
    )).encode("utf-8")
).hexdigest()[:16]
```

Rationale:

- **Stable across runs.** Every input is a bounded primitive or a
  tuple of bounded printable strings. CPython's `repr()` over the
  closed input shape `(str, int, str, tuple[str, ...], str)` is
  deterministic; no dict / set ordering can vary because no dict /
  set participates.
- **Deduplicates repeated same event.** Two observe calls with
  the same payload yield the same `event_id`, so the
  `(event_type, references, tick)` triple idempotency rule
  collapses to a `event_id`-equality check in the constructor /
  observe path.
- **No monotone counter field added to `OperatorSession` v1.**
  The Step 11 Pattern Ledger precedent already opened
  `_PHASE_3_12C_SESSION_ATTRS` for one new optional session
  attribute; an additional monotone counter would open the same
  audit-tier surface a second time. The deterministic scheme
  avoids it.
- **Mirrors `I-PLEDGER-12`** (`pattern_id = "pledger:" +
  sha256(repr(signature).encode("utf-8")).hexdigest()[:16]`).
  Using the same prefix-discriminated 16-hex-char convention
  keeps the id scheme uniform across the Phase 3.12 / Phase 3.13
  developmental substrates.

Canonicalization caveats (explicit; raised under Stage A advisory
review and adopted here):

- **Inputs must be the immutable acceptance payload.** Every input
  field used in `event_id` is fixed at observe time; the
  GrowthEvent record is frozen / slotted, so no field can be
  enriched after acceptance. Mutable metadata is therefore
  excluded from identity by construction (there is no mutable
  metadata).
- **The closed input shape is part of the id contract.** Any
  Step 4 corrigenda amendment that widens the input set (e.g.
  by adding a new identity-relevant field) is a
  catalog-version-bump operation, not an in-place edit, because
  the existing `event_id` values would no longer match.
- **No raw `repr()` over arbitrary objects.** The id derivation
  only ever takes the five fixed inputs above. Other objects
  (e.g. a TickRecord) are referenced only by their bounded
  printable identifier strings.
- **No `dict` / `set` ever participates in the id input.** The
  CPython `repr()` of a `dict` is insertion-ordered, but a future
  refactor that placed a `dict` into the id input would be
  re-ordering-sensitive. The locked scheme forbids it.

Step 4 corrigenda **may revisit only with explicit reason** (the
Phase 3.12 Pattern Ledger Step 8 corrigenda discipline applies).

## Bounds

Initial bounds — final values locked at Step 4 corrigenda:

```text
GROWTH_LEDGER_MAX_EVENTS         = 256
GROWTH_LEDGER_REFERENCE_MAX      = 8
GROWTH_LEDGER_ID_MAX             = 64
GROWTH_LEDGER_PROVENANCE_MAX     = 64
```

Reasoning:

- `GROWTH_LEDGER_MAX_EVENTS = 256` is conservative against the
  existing `STREAM_HISTORY_MAX_CHUNKS = 256` chunk cap. A
  worst-case session that fills the stream-history slot, generates
  one PatternLedger entry per chunk, and ticks every chunk would
  still saturate close to but not below the cap; the spam test in
  Step 8 behavior report will confirm.
- `GROWTH_LEDGER_REFERENCE_MAX = 8` is small. Every v1 event has
  exactly one reference today; the slack accommodates a future
  event type (e.g. `STREAM_PROMOTION_QUEUED` carrying both
  `candidate_id` and `chunk_id`) without re-shaping the record.
- `GROWTH_LEDGER_ID_MAX = 64` matches `PATTERN_LEDGER_ID_MAX`.
- `GROWTH_LEDGER_PROVENANCE_MAX = 64` matches Pattern Ledger /
  Coherence Monitor `MAX_SOURCE_LEN = 32` extended for
  human-readable provenance labels.

**Per-event-type caps.** Synthesis-recommended position: use
**global `max_events` plus deterministic dedup in v1**. Per-event-type
caps add complexity without clear v1 benefit. If the Step 8
behavior report shows that one event type (e.g.
`STREAM_CHUNK_ACCEPTED` under saturation spam) crowds out other
event types under the global cap, Step 4 corrigenda may add a
per-event-type cap then. The global cap + dedup keeps Step 5
catalog patch surface minimal.

## Copy-on-write Discipline

The Growth Ledger inherits the Pattern Ledger's copy-on-write
contract verbatim. Specifically:

- `GrowthLedger` is `@dataclass(frozen=True, slots=True)`.
- `events` is a `tuple[GrowthEvent, ...]`. The whole record is
  frozen.
- `GrowthLedger.observe(...)` returns a **new** `GrowthLedger`.
  The original record is unchanged: `id(old_ledger) !=
  id(new_ledger)`, `old_ledger.events is unchanged` after the
  call.
- Direct constructors reject malformed records (bounded
  printable, `COGITO_ID` rejection, closed-enum membership,
  non-negative int, bounded tuple, bounded provenance).
- `observe(...)` filters duplicate `event_id` idempotently: a
  second observe with an identical payload returns `self`
  unchanged. The duplicate is detected as `event_id`-equality
  (the SHA-256 scheme guarantees this collapses to the
  `(event_type, references, tick)` triple).
- No field of `GrowthEvent` or `GrowthLedger` is a callable,
  file handle, socket, subprocess handle, `pathlib.Path`,
  `sqlite3.Connection` / `Cursor`, curses object, or LLM client.

## Anti-Goodhart Policy

- **Repeated identical event references do not double-count.**
  Re-observing the same `(event_type, references, tick)` triple
  yields the same `event_id` and returns `self` unchanged.
- **Read-only commands do not count as growth.** Every
  read-only verb listed in the Integration Points section is
  banned from triggering observe.
- **Failures do not count.** A failed parse, dispatch, or tick
  leaves the Growth Ledger unchanged.
- **Long text does not create stronger growth.** The Growth
  Ledger stores references only; chunk-text length never reaches
  the ledger and cannot influence the event count.
- **Raw LLM proposals do not count.** A future model-backed
  layer that proposes content would have to feed through an
  existing accepted-construction path; the model's verbosity
  does not become a growth signal.
- **Event count is not a growth score.** No
  `growth_total`, `growth_index`, `growth_rate`,
  `intelligence_score`, `awareness_score`, `iness_score`,
  `coherence_quality`, `capability_score`, `maturity_score`, or
  similar scalar exists in `GrowthEvent` / `GrowthLedger` /
  `GrowthLedgerSnapshot`.
- **No aggregate growth scalar in v1.** Behavior-at-cap is hard
  refusal of new events, not "the growth signal increased by a
  bounded delta". The cap itself is not a metric.
- **`counts_by_type` is a factual summary, not a score.** It
  returns a deterministic ordered tuple of
  `(event_type.value, count)` pairs over the closed enum,
  mirroring Coherence Monitor's `counts_by_status`. It is allowed
  precisely because it is a tuple of labelled counts, not a
  scalar.

## Persistence Policy

**Recommended v1 — session-local only.** The Pattern Ledger
LOCK B precedent applies:

- No DB schema change in v1.
- No `SCHEMA_VERSION_V*` bump.
- No `growth_events` table.
- `/save-session` does **not** serialize the Growth Ledger.
- `/load-session` does **not** restore the Growth Ledger.
- `_maybe_autosave_after_dispatch` is **not** extended.
- Cold start begins empty (`GrowthLedger() == GrowthLedger(events=())`).
- A session loaded from disk has an empty Growth Ledger; the
  loaded session's `OperatorSession.tick_counter`,
  `stream_history`, `stream_candidates`, Pattern Ledger, profile,
  MSI, and registry are restored as before, but the loaded
  session begins growth-event-empty.

This choice keeps the Step 5 catalog patch surface minimal and
honors the existing `I-PERSIST-*` / `I-AUTOSAVE-*` /
`I-PLEDGER-*` discipline.

**Persistence may be revisited only after the initial behavior
report (Step 8).** If Step 8 shows that cross-session continuity
is load-bearing — for example, because the future SelfModel
campaign needs a stable historical surface — a follow-up reviewed
catalog patch can introduce a `growth_events` table and the
corresponding `I-PERSIST-*`-style discipline. Until then,
persistence stays out.

## Relationship to Pattern Ledger

- Pattern Ledger records bounded *structural recurrence state*:
  what patterns have been seen, how often, with what evidence
  chunk / candidate ids.
- Growth Ledger records bounded *historical accepted events*
  involving Pattern Ledger creation / update: which
  `PatternLedger.observe(...)` calls produced new entries
  (`PATTERN_ENTRY_CREATED`) or strictly increased recurrence
  counts (`PATTERN_ENTRY_UPDATED`).
- The Growth Ledger **must not mutate** the Pattern Ledger. The
  observe call site is downstream of `PatternLedger.observe(...)`
  and only *reads* the entry delta (a tuple comparison between
  the pre- and post-observe entry tuples).
- The Growth Ledger **may reference** `pattern_id` (bounded
  printable identifier), but never raw text from the underlying
  chunks. Text already lives in `TextStreamChunk`; the Growth
  Ledger is a referencing layer.

## Relationship to Coherence Monitor

- The Coherence Monitor may **later** inspect the Growth Ledger
  through a bounded read-only check family (e.g.
  `growth.entries_bounded`, `growth.event_ids_deterministic`,
  `growth.session_local_only`). This is out of Phase 3.13 scope;
  any such check is a future catalog patch.
- The Growth Ledger **may defer** `COHERENCE_REPORT_BUILT` in
  v1. The deferred classification reflects two risks: (a) framing
  a report build as "growth" risks a semantic / quality / truth
  reading, and (b) the Coherence Monitor build is itself a
  read-only diagnostic, not an accepted runtime mutation.
- The Growth Ledger **must not** call DB / tick / LLM **through**
  the Coherence Monitor or directly. The bounded read-only
  Coherence Monitor surface that the Growth Ledger would reference
  is `CoherenceReport.snapshot.snapshot_id`, not the build call
  itself.
- The Growth Ledger **must not mutate** Coherence Monitor records.
  Both records are frozen / slotted by design.

## Relationship to SelfModel

- **SelfModel remains deferred.** Phase 3.13 does not implement
  SelfModel. SelfModel is reconsidered only in a separate
  follow-up campaign that explicitly accepts a SelfModel plan,
  per the Phase 3.12 Step 15 roadmap.
- A future SelfModel should later **quote** Growth Ledger counts
  / events and Coherence Monitor status, **not** invent self-
  claims. The Phase 3.12 Step 15 roadmap captures the proposed
  SelfModel field shape; nothing in Phase 3.13 commits to it.
- The Growth Ledger **must not** generate self-claims. No event
  type, no source, no provenance, and no bounded printable string
  produced by the Growth Ledger may contain a self-claim
  ("I am ...", "I understand ...", "I believe ...",
  "I intend ...", etc.). The Coherence Monitor's
  `_FORBIDDEN_NON_CLAIM_TERMS` set (`I-COHMON-11`) is the
  canonical forbidden list; the Growth Ledger module inherits it.

## Static Safety / Forbidden Surfaces

The Growth Ledger module, when implemented under the Step 6 review
gate, must structurally forbid the imports and calls below. The
exact allowed import list is finalized at Step 3 kickoff / Step 4
corrigenda; this section fixes the prohibitions.

Forbidden imports (static AST audit must reject):

```text
os
subprocess
socket
urllib
http
requests
pathlib
tempfile
shutil
curses
brain.llm
brain.tick                 (raw tick callable; the BrainState typed
                             record may be imported as a type only)
threading
asyncio
atexit
signal
importlib
math                       (Pattern Ledger precedent; no float / round
                             / math.* on the count / statistic path)
```

Forbidden calls / dynamic execution (static AST audit must reject):

```text
eval
exec
compile
__import__
importlib.import_module
atexit.register
signal.signal
signal.setitimer
threading.*
asyncio.*
open                       (no filesystem mutation; no read either —
                             references are passed in, not loaded)
tick                       (no call to brain.tick.tick from the module)
save_session
load_session
db_backup
db_verify
maybe_autosave_after_mutation
```

Allowed imports — read-only, for bounded types / constants only,
to be finalized in kickoff / corrigenda — likely subset of:

```text
dataclasses
enum
fractions                  (only if exact arithmetic appears; v1 has
                             no statistic that needs it, so this may
                             be dropped at kickoff)
hashlib                    (for the SHA-256 event_id derivation)
typing
brain.development.pattern_ledger  (for PatternLedgerEntry typed
                                     record / pattern_id type, NOT for
                                     PatternLedger.observe)
brain.development.text_stream     (for TextStreamChunk typed record /
                                     chunk_id type, NOT for any
                                     observe call)
brain.io_types
brain.tlica.profile               (for COGITO_ID only)
brain.tick                        (for BrainState typed record only,
                                     never the tick callable)
brain.ui.session                  (for OperatorSession typed record
                                     only, never any dispatcher)
```

Module-level statements must be limited to imports, constants,
function defs, class defs, and a module docstring (mirroring the
Pattern Ledger / Coherence Monitor static AST audits).

## Non-claims

The Growth Ledger work, at every step from Step 3 through the
eventual Step 7 implementation, must **not**:

- claim consciousness, sentience, subjective experience, or
  qualia,
- claim semantic understanding, language understanding, or
  comprehension,
- claim truth adjudication or assign PRESERVE / DAMAGE values to
  raw text or to anything else,
- claim agency, intent, will, or desire,
- claim self-modification of code, fixtures, the catalog, or the
  runtime,
- claim personhood,
- introduce an aggregate consciousness score, "I-ness" score,
  awareness score, "growth score", "intelligence score",
  "maturity score", "capability score", "coherence quality
  score", or any single scalar purporting to summarize interior
  state,
- introduce SelfModel in any form,
- emit any hidden LLM call,
- emit any hidden filesystem write, network call, subprocess
  spawn, or shell command,
- introduce hidden persistence outside the explicit
  `/save-session` / `/load-session` route (and that route is not
  extended in v1),
- be reachable through `tick()` — the kernel runtime transition
  route remains untouched,
- mutate `BrainState`, `MSI`, `PtCns`, `ContentRegistry`,
  `OperatorSession.event_queue`, `stream_history`,
  `stream_candidates`, `stream_chunk_serial`, the Pattern
  Ledger, the Coherence Monitor records, `latest_tick`, or
  `tick_counter`,
- map any raw text to `COGITO_ID`,
- alter `/step`, `/stream`, `/stream-promote`, `/save-session`,
  `/load-session`, `/db-*`, `/autosave-*`, or any existing
  dispatcher beyond appending the post-success observe call.

These prohibitions inherit from `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, `PHASE3_13_GROWTH_LEDGER_ROADMAP.md`, the
Phase 3.12 Step 15 roadmap, the Phase 3.12 final audit, and the
existing `I-STRM-*` / `I-UISTRM-*` / `I-PERSIST-*` /
`I-OPSHARDEN-*` / `I-OBSERVE-*` / `I-AUTOSAVE-*` / `I-PLEDGER-*` /
`I-COHMON-*` discipline. Step 4 corrigenda will restate the
relevant ones in the language of the Growth Ledger record shape.

## ChatGPT/Codex Consultation

A Stage A advisory review was run against the synthesis question
file (`/tmp/toyi_chatgpt_step2_question.md`). The wrapper output
landed at `/tmp/toyi_chatgpt_step2_answer.md`.

```text
ChatGPT/Codex consultation:
- used:           yes
- mode:           review
- model:          gpt-5.5
- effort:         medium
- wrapper command: python3 tools/claude_helpers/codex_chatgpt_subagent.py
                     --mode review --model gpt-5.5 --effort medium
                     --timeout 180
                     --prompt-file /tmp/toyi_chatgpt_step2_question.md
- question file:   /tmp/toyi_chatgpt_step2_question.md
- answer file:     /tmp/toyi_chatgpt_step2_answer.md
- wrapper status:  exit 0; error_class null; codex_returncode 0;
                   duration_ms 55895; stdout 5489 bytes; full Stage A
                   review template returned with sections Mode / Answer /
                   Suggested edits / Risks / Validation / Disagreement
                   (minor) / Confidence (medium). Audit JSONL appended
                   at .claude/codex_bridge_logs/ (gitignored).
- accepted advice:
   - Choose Option A: narrow v1 (stream append, pattern created/updated,
     promotion queued, tick succeeded, profile/MSI additions); defer
     save/load and coherence-report-built events.
   - Append-only for accepted events; the ledger does NOT validate,
     reinterpret, repair, rank, or summarize the events it records.
   - Every v1 event tied to an accepted constructor-validated object
     or operation.
   - Add explicit canonicalization caveats for the SHA-256 event_id
     scheme: inputs are the immutable acceptance payload only; no
     dict / set ever participates; the closed input shape is part of
     the id contract; any widening is a catalog-version bump.
   - Mark provenance / references as immutable at observe time
     (already true by frozen / slotted construction; stated explicitly
     in this synthesis).
   - Ban every aggregate scalar: growth score, capability score,
     maturity score, intelligence score, coherence-quality score,
     I-ness score, awareness score.
   - Keep PROFILE_DOMAIN_ADDED / MSI_MEMBER_ADDED wording narrow:
     "accepted additions only, not evidence of identity, selfhood,
     agency, preference, truth, or durable self-model state".
   - Mark save/load, coherence reports, persistence, and SelfModel as
     deferred candidates requiring their own future invariants.
- rejected advice:
   - None substantive. The advisor noted that repo-local evidence
     should be reconciled against the recommendation; this synthesis
     reconciles by treating the operator's mandated SHA-256 scheme
     (per the Phase 3.13 roadmap Section 6 guardrail and the Pattern
     Ledger I-PLEDGER-12 precedent) as the canonical lock, while
     incorporating the canonicalization caveats above. The advisor's
     "consider canonical serialization instead of raw repr" framing
     is honored by the LOCK-restricted input shape and the
     no-dict-no-set rule, not by replacing the locked scheme with
     a different serialization.
- reason:          Advisor's Option-A recommendation matched the
                   planned narrow v1; the canonicalization caveats and
                   wording-care notes for PROFILE_DOMAIN_ADDED /
                   MSI_MEMBER_ADDED were adopted verbatim. No
                   substantive disagreement remains.
```

Treat the bridge output as advisory. Repo-local files, gates, and
invariants override ChatGPT advice. The advisor's "minor
disagreement, medium confidence" verdict is consistent with the
synthesis choices.

## Recommended Next Artifact

Step 3:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_KICKOFF.md
```

The kickoff fixes the record shape (resolves all "Step 4
corrigenda picks one and locks it" notes above), enumerates the
proposed implementation surface (likely
`brain/development/growth_ledger.py`), nominates the proposed
observe call sites by dispatcher name, and sketches the import
boundary (probable: read-only over Pattern Ledger /
`text_stream` / `BrainState` typed records; no `brain.tick`
callable; no `brain.llm`; no `OperatorSession` dispatcher).

The Step 4 corrigenda will resolve every open design decision
still open at kickoff time and emit LOCK statements (mirroring
Phase 3.12c Pattern Ledger LOCK A..F precedent) for
session-local-only, dispatch-time observe, event id scheme,
deduplication / saturation rule, behavior at
`GROWTH_LEDGER_MAX_EVENTS`, and the
`SESSION_SAVED` / `SESSION_LOADED` / `COHERENCE_REPORT_BUILT`
inclusion decision (LOCK F).

**Implementation remains blocked.** Step 5 produces a catalog
patch plan only. Step 6 is Review Gate A. Step 7 applies the
implementation **only if** the operator explicitly accepts the
catalog patch plan at Review Gate A. Nothing in this synthesis
authorizes a code change under `brain/**`, `tools/**`,
`.claude/**`, `INVARIANT_CATALOG.md`, `README.md`,
`lean_reference/**`, `scenarios/**`, or `traces/**`.

## Validation

Re-ran after writing this synthesis (no source under `brain/**`,
`tools/**`, `.claude/**`, `lean_reference/**`, `scenarios/**`, or
`traces/**` was touched; no edit to `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, or
`PHASE3_13_GROWTH_LEDGER_ROADMAP.md`; only this new documentation
file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
