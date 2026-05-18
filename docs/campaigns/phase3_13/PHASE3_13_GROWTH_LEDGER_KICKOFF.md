# PHASE3_13_GROWTH_LEDGER_KICKOFF.md

## Purpose

This kickoff turns the Step 2 Growth Ledger synthesis
(`docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_SYNTHESIS.md`)
into an implementation-ready plan. It enumerates the proposed
implementation surface, proposed session integration, proposed observe
call sites, proposed allowed imports, and proposed fixture families,
and lists the open design decisions that **Step 4 corrigenda must lock
before Step 5 catalog planning**.

This kickoff **does not authorize implementation**. Implementation
remains blocked until:

```text
Step 5  catalog patch plan
Step 6  Review Gate A — explicit operator acceptance
Step 7  applied implementation, if approved
```

Every proposed surface below is therefore tagged "candidate pending
Step 5 plan and Step 6 review". No file under `brain/**`, `tools/**`,
`.claude/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, `lean_reference/**`,
`scenarios/**`, or `traces/**` may be modified in pursuit of either
substrate before that gate clears.

This document introduces no fixture, no committed helper, and no
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
Phase 3.13 Step 1 status:         complete (56e448e
                                  "phase3.13 step1: growth ledger
                                  mission sync"); pushed
Phase 3.13 Step 2 status:         complete (f3fa0c4
                                  "phase3.13 step2: growth ledger
                                  synthesis"); pushed
Narrow v1 event scope:            selected by synthesis (Option A);
                                  SESSION_SAVED / SESSION_LOADED /
                                  COHERENCE_REPORT_BUILT deferred to
                                  Step 4 LOCK F
Event id scheme:                  locked at synthesis ("growth:" +
                                  sha256-of-immutable-acceptance-payload);
                                  Step 4 LOCK C must re-affirm
ChatGPT/Codex Stage A bridge:     available and used in Step 1, Step 2,
                                  and this Step 3
Preflight (verified at start of Step 3):
  python3 -m tools.catalog counts     PASS  (240/85/11/14/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (333 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Synthesis Decisions Imported

The Step 2 synthesis already locked the following. The kickoff does
not revise them; Step 4 corrigenda may, but only with explicit reason.

```text
- Growth Ledger is session-local in v1.
- No DB schema change.
- No SCHEMA_VERSION bump.
- No /save-session / /load-session serialization in v1.
- No autosave extension in v1.
- No SelfModel in Phase 3.13.
- No aggregate growth / I-ness / awareness / capability /
  maturity / coherence-quality / intelligence scalar — anywhere.
- Event id scheme (LOCK to be re-affirmed by Step 4):
    event_id = "growth:" + sha256(
        repr((
            event_type.value,    # str
            tick,                # int
            source.value,        # str
            references,          # tuple[str, ...]
            provenance,          # str
        )).encode("utf-8")
    ).hexdigest()[:16]
- Closed v1 event scope:
    STREAM_CHUNK_ACCEPTED
    PATTERN_ENTRY_CREATED
    PATTERN_ENTRY_UPDATED
    STREAM_PROMOTION_QUEUED
    TICK_SUCCEEDED
    PROFILE_DOMAIN_ADDED        (accepted addition only; never
                                 evidence of identity, selfhood,
                                 agency, preference, truth, or
                                 durable self-model state)
    MSI_MEMBER_ADDED            (same wording-care as above)
- Deferred event types:
    SESSION_SAVED
    SESSION_LOADED
    COHERENCE_REPORT_BUILT
- Append-only over accepted events; the ledger does NOT validate,
  reinterpret, repair, rank, normalize, or summarize the events it
  records.
- counts_by_type is a labelled tuple of (event_type.value, count)
  pairs — a factual summary, not a score.
```

The synthesis ChatGPT advisory reviewer (Step 2) returned a "minor
disagreement, medium confidence" verdict and recommended Option A
verbatim; the Step 3 advisory reviewer (this step) returned the same
verdict and recommended additional explicit blocks for "non-goals and
banned interpretations" and "corrigenda must decide". Both
recommendations are adopted in this kickoff.

## Proposed Implementation Surface

**Every surface below is a candidate pending Step 5 plan and Step 6
review.** No file is touched by this kickoff.

### Likely Step 7 file set (if Review Gate A approves)

```text
brain/development/growth_ledger.py                              (new module)

brain/development/fixtures/growth_ledger_constructor.py         (new)
brain/development/fixtures/growth_ledger_event_id.py            (new)
brain/development/fixtures/growth_ledger_observe.py             (new)
brain/development/fixtures/growth_ledger_static_audit.py        (new)
brain/development/fixtures/growth_ledger_no_runtime_coupling.py (new)
brain/development/fixtures/growth_ledger_session_integration.py (new)

brain/invariants.py                                             (FIXTURE_MODULES extension)
INVARIANT_CATALOG.md                                            (v0.23 banner + I-GROW-* rows)
brain/_catalog_ids.py                                           (regenerated from catalog)
tools/catalog.py                                                (EXPECTED_COUNTS banner update)

brain/ui/session.py                                             (narrow extension only)

README.md                                                       (catalog version + counts string)
CURRENT_MISSION.md                                              (catalog version + counts string)
CURRENT_CAMPAIGN.md                                             (catalog version + counts string)
```

### Likely fixture-audit updates if an OperatorSession field is added

```text
brain/ui/fixtures/persistence_observe_resource_audit.py         (extend)
brain/ui/fixtures/persistence_ops_resource_audit.py             (extend)
```

If Growth Ledger v1 adds `OperatorSession.growth_ledger` (Step 4
must lock this — see Open Design Decisions, Section "Open Design
Decisions for Step 4"), the same phase-tier audit mechanism used for
Pattern Ledger (`_PHASE_3_12C_SESSION_ATTRS`) must be extended with a
new `_PHASE_3_13_SESSION_ATTRS = frozenset({"growth_ledger"})` tier
on both fixtures. **This is not a deviation if accepted explicitly in
Step 4 / Step 5; it should be planned, not discovered late.** The
Phase 3.12c Step 11 deviation note (about
`_PHASE_3_12C_SESSION_ATTRS` having to be added during
implementation rather than at plan time) is the cautionary precedent
the Step 4 corrigenda should explicitly avoid.

### Explicitly excluded in v1 (no change permitted)

```text
brain/tick.py
brain/llm/**
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/render.py
brain/ui/snapshot.py
DB schema files (schema is owned by I-PERSIST-*; no growth_events
  table; no SCHEMA_VERSION bump)
lean_reference/**
scenarios/**
traces/**
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
```

The Coherence Monitor module is in the excluded set: any future
read-only Coherence Monitor check that *inspects* the Growth Ledger
(e.g. `growth.entries_bounded`) is a follow-up reviewed catalog
patch and is **out of Phase 3.13 scope**. Phase 3.13 does not modify
`brain/development/coherence_monitor.py`.

## Proposed Data Model

Pseudocode — not implementation. Field names, defaults, and bounds
are illustrative and remain subject to Step 4 corrigenda LOCK
revision.

```python
class GrowthEventType(str, Enum):
    STREAM_CHUNK_ACCEPTED      = "stream_chunk_accepted"
    PATTERN_ENTRY_CREATED      = "pattern_entry_created"
    PATTERN_ENTRY_UPDATED      = "pattern_entry_updated"
    STREAM_PROMOTION_QUEUED    = "stream_promotion_queued"
    TICK_SUCCEEDED             = "tick_succeeded"
    PROFILE_DOMAIN_ADDED       = "profile_domain_added"
    MSI_MEMBER_ADDED           = "msi_member_added"
    SESSION_SAVED              = "session_saved"        # deferred
    SESSION_LOADED             = "session_loaded"       # deferred
    COHERENCE_REPORT_BUILT     = "coherence_report_built"  # deferred


class GrowthEventSource(str, Enum):
    STREAM_APPEND              = "stream_append"
    PATTERN_LEDGER_OBSERVE     = "pattern_ledger_observe"
    STREAM_PROMOTE             = "stream_promote"
    STEP_DISPATCH              = "step_dispatch"
    PERSISTENCE_SAVE           = "persistence_save"     # deferred path
    PERSISTENCE_LOAD           = "persistence_load"     # deferred path
    COHERENCE_MONITOR          = "coherence_monitor"    # deferred path


@dataclass(frozen=True, slots=True)
class GrowthEvent:
    event_id:    str                       # bounded printable; != COGITO_ID;
                                           #   len <= GROWTH_LEDGER_ID_MAX
    event_type:  GrowthEventType
    tick:        int                       # >= 0; session.tick_counter at
                                           #   observe time
    source:      GrowthEventSource
    references:  tuple[str, ...]           # bounded printable; no element
                                           #   equals COGITO_ID;
                                           #   0 <= len <= GROWTH_LEDGER_REFERENCE_MAX
    provenance:  str                       # bounded printable; non-empty;
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
        """Copy-on-write; idempotent by event_id; hard-refuses at
        max_events (LOCK E precedent). Never mutates self. Never
        calls tick(). Never touches BrainState / MSI / PtCns /
        registry / agency / LLM."""
        ...

    def counts_by_type(self) -> tuple[tuple[str, int], ...]:
        """Deterministic tuple over the closed GrowthEventType enum.
        Factual summary, NOT a growth score; no scalar field
        summarizes the ledger."""
        ...

    def snapshot(self) -> "GrowthLedgerSnapshot":
        """Bounded read-only summary view."""
        ...
```

`GrowthLedger.observe(...)` is the **sole non-construction entry
point**. It does not take a `BrainState`, it does not take an
`LLMClient`, and it does not take a callable. It is pure over its
inputs and emits a new `GrowthLedger`.

## Proposed Constants

Use Step 2 synthesis defaults unless Step 4 corrigenda revises them
with explicit reason.

```text
GROWTH_LEDGER_MAX_EVENTS         = 256
GROWTH_LEDGER_REFERENCE_MAX      = 8
GROWTH_LEDGER_ID_MAX             = 64
GROWTH_LEDGER_PROVENANCE_MAX     = 64
```

Candidate additional constants — **not locked here**; Step 4 decides:

```text
GROWTH_LEDGER_SOURCE_MAX         ~ 64   (cap on GrowthEventSource value len; the
                                          enum already bounds this, so this
                                          constant may be unnecessary)
GROWTH_LEDGER_SNAPSHOT_MAX       ~ 64   (cap on a future bounded snapshot
                                          shape; only if Step 4 adds a
                                          GrowthLedgerSnapshot record)
GROWTH_LEDGER_OBSERVE_LIMIT_PER_TYPE  (per-event-type cap; not added unless
                                          Step 8 behavior report shows
                                          one event type crowds out others
                                          under the global cap)
```

Step 4 corrigenda will either accept these defaults verbatim, replace
them, or drop the candidate additional constants entirely.

## Proposed Integration Points

Exact candidate call sites and the events each emits, drawn from
`brain/ui/session.py` (the operator dispatch surface). Every site
sits at the **end of the successful path** of an existing
dispatcher / builder.

### 1. successful `_dispatch_stream_append`

Possible events:

```text
GrowthLedger.observe(
    event_type = STREAM_CHUNK_ACCEPTED,
    tick       = self.tick_counter,
    source     = STREAM_APPEND,
    references = (chunk.chunk_id,),
    provenance = "stream_append:_dispatch_stream_append",
)

# Then, if the same dispatcher's PatternLedger.observe(...) returned
# a created-or-updated entry delta (compare pre- and post-observe
# PatternLedger.entries tuples — a pure tuple comparison, NOT
# status-string parsing):

GrowthLedger.observe(
    event_type = PATTERN_ENTRY_CREATED   # or PATTERN_ENTRY_UPDATED
                                          # by delta classification
    tick       = self.tick_counter,
    source     = PATTERN_LEDGER_OBSERVE,
    references = (pattern_id,),
    provenance = "pattern_ledger:observe",
)
```

**Important.** The Growth Ledger observe call site must occur
**after successful stream append AND after `PatternLedger.observe`**
because the created/updated distinction depends on the Pattern
Ledger delta (compare `prior_pattern_ledger.entries` to
`self.pattern_ledger.entries` — recurrence_count strictly increased
vs new entry appended).

### 2. successful `_dispatch_stream_promote`

```text
GrowthLedger.observe(
    event_type = STREAM_PROMOTION_QUEUED,
    tick       = self.tick_counter,
    source     = STREAM_PROMOTE,
    references = (candidate.candidate_id,),
    provenance = "stream_promote:_dispatch_stream_promote",
)
```

`_dispatch_stream_promote` already returns `Optional[bool]` per the
`I-AUTOSAVE-14` outcome-detection contract; the Growth Ledger
observe site uses the same `True` signal to decide whether to fire.

### 3. successful `_dispatch_step`

```text
GrowthLedger.observe(
    event_type = TICK_SUCCEEDED,
    tick       = self.tick_counter,    # already advanced by _dispatch_step
    source     = STEP_DISPATCH,
    references = (f"tick-{record.tick_index}",),
    provenance = "step_dispatch:_dispatch_step",
)

# For each content_id in the post-tick profile.domain that was NOT
# in the pre-tick profile.domain (delta derived from
# new_state.profile.domain - prior_state.profile.domain):

GrowthLedger.observe(
    event_type = PROFILE_DOMAIN_ADDED,
    tick       = self.tick_counter,
    source     = STEP_DISPATCH,
    references = (content_id,),
    provenance = "step_dispatch:profile_delta",
)

# Same shape, derived from new_state.msi.contents - prior_state.msi.contents:

GrowthLedger.observe(
    event_type = MSI_MEMBER_ADDED,
    tick       = self.tick_counter,
    source     = STEP_DISPATCH,
    references = (content_id,),
    provenance = "step_dispatch:msi_delta",
)
```

`_dispatch_step` already returns `Optional[bool]` and already records
the prior state in local variables (`prior_state`,
`prior_latest_tick`, `prior_queue_size`) for the failure-rollback
contract; the same `prior_state` is the natural delta input for the
profile / MSI observe sites.

**Important.** Profile / MSI additions are **accepted additions
only**. They are not evidence of identity, selfhood, agency,
preference, truth, or durable self-model state. The Step 4
corrigenda must restate this in the Growth Ledger module docstring
and in the catalog row text. Naming language stays narrow:
"growth event" means "a bounded observed delta", not "improvement"
or "progress".

### Deferred call sites (NOT in v1)

```text
_dispatch_save_session                  -> SESSION_SAVED       (deferred)
_dispatch_load_session                  -> SESSION_LOADED      (deferred)
build_full_coherence_report             -> COHERENCE_REPORT_BUILT (deferred)
```

Each deferred site brings risk:

- `SESSION_SAVED` / `SESSION_LOADED` interact with the
  persistence boundary, and a session-local Growth Ledger loses its
  `SESSION_LOADED` event on the very session that loads.
- `COHERENCE_REPORT_BUILT` framing risks a "growth = coherence
  quality" semantic reading. The Coherence Monitor build is a
  read-only diagnostic, not an accepted runtime mutation.

Step 4 LOCK F resolves the deferred trio.

## Outcome Detection Contract

Growth Ledger uses **typed outcome detection**, not status / error
parsing. This is the existing `I-AUTOSAVE-14` discipline applied to
a new substrate.

### Allowed

```text
- the dispatcher's existing typed return value
  (e.g. _dispatch_step returns Optional[bool]; True = success)
- the known successful path after every constructor in that path
  succeeds without raising
- comparing pre- and post-dispatch bounded record tuples
  (e.g. profile.domain delta, msi.contents delta, pattern_ledger
  entries delta)
- a TickRecord returned by tick() without exception
- the state delta after a successful tick
```

### Forbidden

```text
- parsing session.status_message
- parsing session.error_message
- parsing any UI output
- treating a read-only command as growth
- observing on parse failure, dispatch failure, or tick failure
- observing on any error path
- observing on /quit, /noop, /clear-status, /help, or any non-mutating
  verb
- using exception messages as observable signals
```

The Phase 3.12c Pattern Ledger / Phase 3.10c autosave precedents
both established that the outcome-detection contract reads typed
return values, never status strings; Growth Ledger inherits that
discipline.

## Proposed Session Integration

**Candidate pending Step 5 plan and Step 6 review.** Step 4
corrigenda must lock each item below before Step 5 catalog planning.

### Proposed (pending lock)

```text
- Add OperatorSession.growth_ledger: GrowthLedger = field(default_factory=GrowthLedger).
- Add "growth_ledger" to _ALLOWED_SESSION_ATTRS in brain/ui/session.py.
- Extend brain/ui/fixtures/persistence_observe_resource_audit.py with
  _PHASE_3_13_SESSION_ATTRS = frozenset({"growth_ledger"}); the new
  attribute joins the existing _PHASE_3_12C_SESSION_ATTRS tier as a
  parallel surface; the same applies to
  brain/ui/fixtures/persistence_ops_resource_audit.py.
- Growth Ledger remains session-local; /save-session does NOT
  serialize it; /load-session does NOT restore it; cold start creates
  an empty GrowthLedger (default_factory).
- The dispatcher's pre-observe sequence in _dispatch_stream_append /
  _dispatch_stream_promote / _dispatch_step gains exactly one
  self.growth_ledger = self.growth_ledger.observe(...) line per
  observed event. No other line in the dispatcher body changes.
```

### Why this should be explicitly locked in Step 4

The Pattern Ledger precedent (Step 11 of Phase 3.12c) is informative:
its `_PHASE_3_12C_SESSION_ATTRS` audit tier was added during
implementation, not at plan time. The operator reviewed and
**accepted** that deviation as justified, but the audit log recorded
it as a deviation. Step 4 should plan the
`_PHASE_3_13_SESSION_ATTRS` tier explicitly so Step 7
implementation does not have to declare a deviation. Avoiding the
deviation is a planning improvement, not a guarantee — Step 6 may
still amend the plan.

## Proposed Non-Integration List

v1 implementation, if approved, must **not**:

```text
- edit tick()
- call tick() from any Growth Ledger code path
- edit Pattern Ledger
- edit Coherence Monitor
- open the session DB
- save/load the Growth Ledger
- extend the autosave trigger set
  (I-AUTOSAVE-12 set remains: {STEP_TICK, STREAM_PROMOTE})
- call any LLM client
- add a UI command (no /growth-ledger verb in v1)
- add an active_view (no "growth_ledger" view in v1)
- modify brain/ui/snapshot.py, brain/ui/render.py, brain/ui/commands.py,
  brain/ui/command_line.py
- modify brain/ui/persistence.py, brain/ui/persistence_ops.py,
  brain/ui/persistence_observe.py, brain/ui/autosave.py
- parse status / error / UI output strings as observable signals
- add any aggregate scalar score (no growth score, capability score,
  maturity score, intelligence score, awareness score, I-ness score,
  coherence-quality score)
- derive persistence from session serialization, profile export,
  traces, coherence reports, or fixture snapshots
  (this is the explicit "no hidden persistence" rule restated for
  every potential indirect route)
- introduce a normalization / ranking / totalizing / summary metric
  that exposes per-event-type counts as a proxy score
- introduce SelfModel in any form
```

## Proposed Allowed Imports

For the future `brain/development/growth_ledger.py` module, propose a
closed allowed import set — narrower than the synthesis floor, and
optimized to keep `growth_ledger.py` independent of Pattern Ledger /
Coherence Monitor module runtime coupling.

### Probable allowed set

```text
dataclasses
enum
hashlib              (for the SHA-256 event_id derivation)
typing
brain.tlica.profile  (COGITO_ID only — for rejection checks)
```

### Probably NOT imported (recommendation)

```text
fractions
  v1 Growth Ledger has no statistic that needs exact Fraction
  arithmetic. counts_by_type returns int counts; event records
  carry int tick; no field is a Fraction. Drop unless Step 4 adds
  a Fraction-valued surface.

brain.development.pattern_ledger
brain.development.coherence_monitor
brain.development.text_stream
  v1 Growth Ledger accepts bounded printable references (pattern_id,
  chunk_id, candidate_id, content_id, snapshot_id) as plain strings;
  the integration layer (brain/ui/session.py) is responsible for
  passing the bounded id strings, NOT the typed records. Keeping
  growth_ledger.py independent of these modules at runtime keeps the
  module's dependency direction one-way (session.py imports
  growth_ledger.py; growth_ledger.py does NOT import other
  development substrates back). This avoids cycles and keeps the
  static AST audit tight.

brain.tick
  Only the BrainState typed record may be imported as a type hint
  (if needed at all). The tick callable must NOT be importable from
  growth_ledger.py. The Step 4 corrigenda may decide to omit even
  the typed import — the module is fully decoupled by passing
  bounded id strings only.

brain.ui.session
  Growth Ledger does NOT import OperatorSession. The OperatorSession
  field (if accepted) holds a GrowthLedger value; the integration
  call sites live IN session.py, not in growth_ledger.py.
```

### Recommendation

Keep `growth_ledger.py` **independent** of Pattern Ledger /
Coherence Monitor / `text_stream` modules in v1. Integration code in
`brain/ui/session.py` can pass bounded id strings; the ledger module
only validates bounded strings/enums/ints. This mirrors how
`brain/development/pattern_ledger.py` imports only from
`brain.development.text_stream` for typed record helpers (not back
into any session / runtime module).

The dependency direction must remain **one-way**: session.py and any
future consumer import growth_ledger.py; growth_ledger.py does not
import session.py, tick.py, llm/, ui/, or other development
substrates.

## Forbidden Imports / Calls / Runtime Resources

### Forbidden imports (static AST audit must reject)

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
sqlite3
brain.llm
brain.tick (the tick callable — the BrainState typed record may be
            imported as a type only, and even that is optional)
brain.ui                                            (any submodule)
brain.development.pattern_ledger                    (runtime — type
                                                     imports also
                                                     disallowed in
                                                     the recommendation
                                                     above)
brain.development.coherence_monitor                 (runtime call)
threading
asyncio
atexit
signal
importlib
math
```

### Forbidden calls / dynamic execution

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
open                  (no filesystem mutation; no read either)
tick                  (no call to brain.tick.tick from the module)
save_session
load_session
db_backup
db_verify
maybe_autosave_after_mutation
build_coherence_report
build_full_coherence_report
PatternLedger.observe  (the GrowthLedger module does not call
                        PatternLedger.observe; that runs in
                        session.py BEFORE the growth observe site)
```

### Forbidden runtime resource storage (constructor / runtime audit)

No `GrowthEvent` or `GrowthLedger` field may store:

```text
callable
file handle
socket
subprocess handle
pathlib.Path
sqlite3.Connection / Cursor
curses object
LLM client-shaped object
object with eval_consistency
```

The same `_value_looks_unsafe` discipline that the Coherence Monitor
applies (`brain/development/coherence_monitor.py` —
`_value_looks_unsafe`) is the canonical pattern for the runtime
resource audit.

## Proposed Fixtures

**Candidate fixture families pending Step 5 plan and Step 6
review.** Step 4 corrigenda may admit, reject, or merge any family
below; the fixture set committed at Step 7 is the Step 5 plan as
amended by Step 6, not this list.

### 1. `growth_ledger_constructor.py`

- closed `GrowthEventType` enum membership
- closed `GrowthEventSource` enum membership
- valid `GrowthEvent` constructs through every event-type / source
  combination admitted by Step 4 LOCK F
- `COGITO_ID` rejection on `event_id`, every `references` element,
  and `provenance`
- malformed bounded string rejection (non-str, empty,
  non-printable, oversized)
- `references` tuple bounds (`GROWTH_LEDGER_REFERENCE_MAX`)
- non-negative `tick`
- frozen / slotted contract (mutation raises `FrozenInstanceError`)
- duplicate references behavior — accept Step 4 LOCK D's choice;
  the synthesis position is "duplicate `(event_type, references,
  tick)` is a no-op via `event_id` collapse"; constructor allows
  duplicates in `references` tuple only if Step 4 locks that

### 2. `growth_ledger_event_id.py`

- deterministic id stable across two construction calls with the
  same payload
- different payload yields different id
- closed input shape only: the locked five inputs
  (`event_type.value`, `tick`, `source.value`, `references`,
  `provenance`)
- no `dict` / `set` ever participates in the id input
- no nondeterministic value (time, randomness, PID, hostname,
  `id(...)`, env lookup) appears on the id derivation path
- id length is exactly `len("growth:") + 16 = 23` and the
  prefix is always `"growth:"`

### 3. `growth_ledger_observe.py`

- empty ledger `observe(...)` produces a one-event ledger
- duplicate `(event_type, references, tick)` is a no-op:
  re-calling `observe(...)` with the same payload returns `self`
  unchanged (`id`-equality check)
- hard refusal at `GROWTH_LEDGER_MAX_EVENTS`: at the cap, the
  ledger returns `self` for any new event; no eviction, no FIFO
  drop, no overwrite (LOCK E precedent)
- copy-on-write: old ledger `events` tuple is unchanged after
  `observe(...)`; the result is a NEW `GrowthLedger`
- `counts_by_type` is deterministic over the closed enum: the same
  ledger always returns the same tuple of pairs
- no aggregate scalar field appears in `GrowthEvent` or
  `GrowthLedger`

### 4. `growth_ledger_static_audit.py`

- forbidden imports / calls absent (the full lists above)
- allowed imports only (the closed set above)
- module-level statements limited to imports, constants,
  function defs, class defs, and a module docstring (Pattern
  Ledger / Coherence Monitor precedent)
- no non-claim violations: the
  `_FORBIDDEN_NON_CLAIM_TERMS` audit (the canonical Coherence
  Monitor constant, possibly imported by reference) must find no
  forbidden term in the module source
- no dynamic execution
- no raw LLM / `tick` / DB call

### 5. `growth_ledger_no_runtime_coupling.py`

- records store no unsafe resources (the
  `_value_looks_unsafe`-style check applied to every
  `GrowthEvent` and `GrowthLedger` field)
- `observe(...)` does not mutate `BrainState`, `PatternLedger`,
  `CoherenceMonitor` records, `OperatorSession.event_queue`, or
  any source history (a constructed example session before /
  after `observe(...)` proves identity-stability)
- no object with `eval_consistency` is stored or accepted

### 6. `growth_ledger_session_integration.py`

- a successful `/stream` append records `STREAM_CHUNK_ACCEPTED`
- a successful `/stream` append that produces a new Pattern
  Ledger entry records `PATTERN_ENTRY_CREATED`
- a successful `/stream` append that increments an existing
  Pattern Ledger entry's `recurrence_count` records
  `PATTERN_ENTRY_UPDATED`
- a successful `/stream-promote` records `STREAM_PROMOTION_QUEUED`
- a successful `/step` records `TICK_SUCCEEDED` plus one
  `PROFILE_DOMAIN_ADDED` and one `MSI_MEMBER_ADDED` per
  newly-admitted content
- a failed parse / dispatch / tick produces **no** observe call
- every read-only verb produces **no** observe call
  (`/state`, `/tick`, `/stream-summary`, `/stream-candidates`,
  `/session-status`, `/db-status`, `/db-summary`,
  `/profile-summary`, `/stream-db-summary`, `/db-diff`,
  `/db-verify`, `/db-backup`, `/autosave-status`)
- `/save-session` / `/load-session` / `build_full_coherence_report`
  produce **no** Growth Ledger event in v1 (the deferred set is
  enforced)
- spam: repeated identical `/stream alpha` does NOT inflate the
  Growth Ledger beyond `GROWTH_LEDGER_MAX_EVENTS`; same
  `event_id` re-observation is a no-op

### 7. optional future UI fixture (DEFERRED — not in v1)

A `/growth-ledger` UI command and a `growth_ledger_ui_*` fixture
family would be a follow-up reviewed catalog patch. **Not
admitted in Phase 3.13.**

## Open Design Decisions for Step 4

Step 4 corrigenda must lock each item below before Step 5 catalog
planning. Synthesis position (where one exists) is noted; Step 4 may
amend with explicit reason.

1. **Session-local-only in v1.** Synthesis position: yes.
   *Decision:* explicit LOCK A statement.
2. **`OperatorSession.growth_ledger` accepted as a new field?**
   Synthesis position: yes (parallels Pattern Ledger). *Decision:*
   explicit accept / reject. If accepted, the audit-tier extension
   below is automatically required.
3. **`_PHASE_3_13_SESSION_ATTRS` audit tier explicitly authorized?**
   *Decision:* explicit yes (avoid the Phase 3.12c Step 11
   deviation precedent) or explicit no (omit the OperatorSession
   field).
4. **Dispatch-time observe vs report-derived observe?**
   Synthesis position: dispatch-time observe at the end of the
   existing successful path. *Decision:* explicit LOCK B statement.
5. **Event id scheme final lock.** Synthesis position: SHA-256 over
   the immutable acceptance payload as written. *Decision:* explicit
   LOCK C statement re-affirming or amending.
6. **Duplicate event handling.** Synthesis position: idempotent
   no-op when `event_id` collides; the SHA-256 collapse guarantees
   that two observe calls with the same payload yield the same id.
   *Decision:* explicit LOCK D statement.
7. **Duplicate reference handling.** Whether the constructor admits
   `references=("X", "X")` (duplicate reference within one event)
   or rejects it. Synthesis position: not locked. *Decision:* Step 4
   picks accept-only-unique vs accept-duplicates-as-distinct, with
   one-line rationale.
8. **Behavior at `GROWTH_LEDGER_MAX_EVENTS`.** Synthesis position:
   hard refusal (mirroring Pattern Ledger LOCK E). *Decision:*
   explicit LOCK E statement.
9. **Final constants.** Synthesis defaults are 256 / 8 / 64 / 64.
   *Decision:* explicit accept / amend per constant. If amended,
   one-line reason.
10. **`SESSION_SAVED` / `SESSION_LOADED` / `COHERENCE_REPORT_BUILT`
    promoted into v1 or kept deferred?** Synthesis position:
    deferred. *Decision:* explicit LOCK F statement.
11. **Profile / MSI delta derivation method.** Synthesis position:
    `new_state.profile.domain - prior_state.profile.domain` and
    `new_state.msi.contents - prior_state.msi.contents` computed in
    `_dispatch_step` AFTER tick succeeds. *Decision:* explicit
    accept; or pick an alternative (e.g. parse TickRecord delta
    fields) and justify.
12. **TICK_SUCCEEDED reference shape.** Synthesis position:
    `references=(f"tick-{record.tick_index}",)`. *Decision:* accept
    or pick alternative.
13. **`counts_by_type` is enough vs. add a bounded
    `GrowthLedgerSnapshot`?** Synthesis position: `counts_by_type`
    is enough for v1. *Decision:* explicit accept or admit a
    `GrowthLedgerSnapshot` record at Step 5.
14. **Per-event-type caps?** Synthesis position: defer unless the
    Step 8 behavior report shows crowding. *Decision:* explicit
    accept of "defer" or admit per-event-type caps now with
    explicit numbers.
15. **Allowed imports — drop `brain.development.text_stream` etc.?**
    Kickoff recommendation: keep `growth_ledger.py` independent of
    Pattern Ledger / Coherence Monitor / `text_stream` modules.
    *Decision:* explicit accept or admit the typed-record imports
    with one-line rationale.
16. **Forbidden non-claim term audit — import the canonical
    Coherence Monitor `_FORBIDDEN_NON_CLAIM_TERMS` constant or
    duplicate it?** *Decision:* either is acceptable; if duplicated,
    Step 4 must commit to keeping both lists in sync via a
    static audit assertion that compares them.

## Banned Interpretations

The Step 3 advisor flagged "semantic leakage through naming and
descriptions" as a risk. The kickoff therefore restates the banned
interpretations explicitly. These prohibitions apply to every
Growth Ledger surface — module source, docstrings, catalog row text,
fixture docstrings, generated bounded printable strings, behavior
report wording, and step report disclosures:

```text
"growth" means:
  a bounded observed delta — one accepted, constructor-validated event,
  recorded by reference, with no scalar metric attached.

"growth" does NOT mean:
  improvement
  progress
  maturity
  capability
  intelligence
  development of "I"
  self-improvement
  selfhood
  agency
  consciousness
  sentience
  subjective experience
  semantic understanding
  truth tracking
  PRESERVE / DAMAGE adjudication
  preference
  intent / will / desire
  awareness
  coherence quality

Growth Ledger never:
  totalizes, ranks, normalizes, scores, summarizes,
  or expresses a scalar over the events it stores.
```

The Coherence Monitor's `_FORBIDDEN_NON_CLAIM_TERMS` constant is the
canonical forbidden-terms set; Growth Ledger inherits it.

## ChatGPT/Codex Consultation

A Stage A advisory review was run against the kickoff question file
(`/tmp/toyi_chatgpt_step3_question.md`). The wrapper output landed
at `/tmp/toyi_chatgpt_step3_answer.md`.

```text
ChatGPT/Codex consultation:
- used:           yes
- mode:           review
- model:          gpt-5.5
- effort:         medium
- wrapper command: python3 tools/claude_helpers/codex_chatgpt_subagent.py
                     --mode review --model gpt-5.5 --effort medium
                     --timeout 180
                     --prompt-file /tmp/toyi_chatgpt_step3_question.md
- question file:   /tmp/toyi_chatgpt_step3_question.md
- answer file:     /tmp/toyi_chatgpt_step3_answer.md
- wrapper status:  exit 0; error_class null; codex_returncode 0;
                   duration_ms 67237; stdout 4553 bytes; full Stage A
                   review template returned with sections Mode / Answer
                   / Suggested edits / Risks / Validation /
                   Disagreement (minor) / Confidence (medium). Audit
                   JSONL appended at .claude/codex_bridge_logs/
                   (gitignored).
- accepted advice:
   - Mark every implementation surface as "candidate pending Step 5
     plan and Step 6 review" (applied verbatim throughout this doc).
   - Add an explicit "Banned Interpretations" block (added above).
   - Add a "Corrigenda must decide" / "Open Design Decisions for
     Step 4" section (already in the operator-required structure;
     advisor confirmed the framing).
   - Plan the OperatorSession audit-tier (_PHASE_3_13_SESSION_ATTRS)
     at Step 4 / Step 5 instead of discovering it at Step 7
     (Phase 3.12c Step 11 deviation precedent cited as cautionary).
   - Persistence ambiguity ban extended: no derivation through
     session serialization, profile export, traces, coherence
     reports, or fixture snapshots (added to "Proposed
     Non-Integration List").
   - Dependency direction lock: growth_ledger.py is one-way; session
     and consumers import it, but it imports no session / runtime /
     development module back (added to "Proposed Allowed Imports").
   - Fixture admissibility caveat: every fixture family is a
     candidate; Step 5 plan amended by Step 6 is what lands at
     Step 7 (added to "Proposed Fixtures").
   - Banned aggregate scoring (already in synthesis; restated here in
     "Banned Interpretations" and "Proposed Non-Integration List").
- rejected advice:
   - None substantive. The advisor framed the kickoff as
     "directionally safe if it stays documentation-only and keeps
     Growth Ledger v1 session-local, narrow, and non-persistent";
     this kickoff is exactly that. The advisor's "minor disagreement"
     reflects its uncertainty about repo-local evidence rather than a
     concrete disagreement with the synthesis-locked choices.
- reason:          Advisor's verdict and recommendations are
                   consistent with the planned narrow v1; every
                   substantive suggestion was adopted as an explicit
                   block in the kickoff text. No substantive
                   disagreement remains.
```

Treat the bridge output as advisory. Repo-local files, gates, and
invariants override ChatGPT advice. The advisor's "minor
disagreement, medium confidence" verdict is consistent with the
kickoff choices.

## Next Artifact

Step 4:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CORRIGENDA.md
```

Step 4 corrigenda will issue LOCK A..F statements (mirroring
Phase 3.12c Pattern Ledger LOCK precedent) resolving each open
design decision above, and will restate the Banned Interpretations
in the LOCK syntax. The corrigenda is documentation only.

**Implementation remains blocked.** Step 5 produces a catalog patch
plan only. Step 6 is Review Gate A. Step 7 applies the implementation
**only if** the operator explicitly accepts the catalog patch plan at
Review Gate A. Nothing in this kickoff authorizes a code change.

## Validation

Re-ran after writing this kickoff (no source under `brain/**`,
`tools/**`, `.claude/**`, `lean_reference/**`, `scenarios/**`, or
`traces/**` was touched; no edit to `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`PHASE3_13_GROWTH_LEDGER_ROADMAP.md`, or the Step 2 synthesis; only
this new documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
