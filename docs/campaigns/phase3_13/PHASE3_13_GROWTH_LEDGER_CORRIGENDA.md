# PHASE3_13_GROWTH_LEDGER_CORRIGENDA.md

## Purpose

This corrigenda locks every remaining Growth Ledger v1 design decision that
was still open after Step 3 (kickoff). It exists so the Step 5 catalog patch
plan can be precise (exact row family, exact statuses, exact count delta,
exact fixture list, exact implementation files, exact resource-audit tier
updates) and so the Step 6 Review Gate A can be a single yes/no decision.

This document **does not authorize implementation**. Implementation remains
blocked until:

```text
Step 5  catalog patch plan
Step 6  Review Gate A — explicit operator acceptance
Step 7  applied implementation, if approved
```

This corrigenda touches no source under `brain/**`, `tools/**`, `.claude/**`,
`INVARIANT_CATALOG.md`, `README.md`, `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, `lean_reference/**`, `scenarios/**`, or `traces/**`. It
introduces no fixture, no committed helper, and no runtime behavior change.

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
Phase 3.13 Step 3 status:         complete (55b4fe7
                                  "phase3.13 step3: growth ledger
                                  kickoff"); pushed
Step 2 synthesis disposition:     narrow v1 selected (Option A);
                                  deferred trio = SESSION_SAVED /
                                  SESSION_LOADED / COHERENCE_REPORT_BUILT
Step 3 kickoff disposition:       implementation surface enumerated
                                  and open design decisions listed for
                                  this Step 4 corrigenda to lock
Active Stage A advisory bridge:   used in Steps 1, 2, 3 and again in
                                  this Step 4 (review / gpt-5.5 / medium)
Preflight (verified at start of Step 4):
  python3 -m tools.catalog counts     PASS  (240/85/11/14/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (333 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Corrigenda Authority

- These locks bind the Step 5 catalog patch plan and any Step 7
  implementation. Step 5 may not propose a row family, fixture, or
  implementation surface that conflicts with the locks below.
- A later review gate (Step 6 Review Gate A, or any subsequent gate)
  may override a lock **only by naming the lock and giving a reason**.
  Silent drift across the Step 5 plan or Step 7 implementation is a
  procedural deviation and must be flagged as such.
- If any lock below conflicts with a repo-local invariant
  (`I-STRM-*`, `I-UISTRM-*`, `I-PERSIST-*`, `I-OPSHARDEN-*`,
  `I-OBSERVE-*`, `I-AUTOSAVE-*`, `I-PLEDGER-*`, `I-COHMON-*`, the
  Phase 3.10c outcome-detection contract, or any future catalog row),
  **repo-local invariants win**. Step 5 must revise the conflicting
  lock with an explicit reason, and the revision is itself subject
  to Step 6 Review Gate A.

## LOCK A — Session-local-only v1

**Lock:** Growth Ledger v1 is session-local only.

**Consequences:**

- No DB schema change. No `growth_events` table.
- No `SCHEMA_VERSION_V*` bump.
- `/save-session` does **not** serialize the Growth Ledger.
- `/load-session` does **not** restore the Growth Ledger.
- `_maybe_autosave_after_dispatch` is **not** extended. The
  autosave trigger set remains exactly `{STEP_TICK, STREAM_PROMOTE}`
  (the existing `I-AUTOSAVE-12` set), unchanged.
- Cold start begins with an empty Growth Ledger
  (`GrowthLedger() == GrowthLedger(events=())`).
- A session loaded from disk leaves `OperatorSession.growth_ledger`
  untouched at its construction default. The loaded session's
  `tick_counter`, `stream_history`, `stream_candidates`, Pattern
  Ledger, profile, MSI, and registry are restored exactly as before
  this campaign; the only added field begins empty after load.

**Rationale.** Mirrors Phase 3.12c Pattern Ledger LOCK B. Persistence
may be revisited only after the Step 8 behavior report shows whether
cross-session continuity is load-bearing. Until then, persistence
stays out.

## LOCK B — OperatorSession field accepted

**Lock:** Growth Ledger v1 will add exactly one new
`OperatorSession` field. This lock is the **planned v1 attachment
point** for the field, not authorization to edit `brain/ui/session.py`
in Step 4. The edit happens only at Step 7 if Step 6 Review Gate A
accepts the Step 5 catalog patch plan.

The exact field shape Step 7 will apply (if approved):

```python
OperatorSession.growth_ledger: GrowthLedger = field(default_factory=GrowthLedger)
```

**Consequences:**

- The string `"growth_ledger"` is added to `_ALLOWED_SESSION_ATTRS`
  in `brain/ui/session.py`. No other name is added.
- The existing `OperatorSession.__post_init__` style does
  `isinstance` checks on typed-record fields (compare
  `brain/ui/session.py:370–373`, which type-checks
  `self.pattern_ledger`). Step 7 must add the parallel
  `isinstance(self.growth_ledger, GrowthLedger)` check with a
  matching error message.
- The field is resource-safe. It holds a frozen / slotted
  `GrowthLedger` value whose `events` tuple stores only frozen /
  slotted `GrowthEvent` records. No field is a callable, file
  handle, socket, subprocess handle, `pathlib.Path`,
  `sqlite3.Connection` / `Cursor`, curses object, or LLM client.
  The `OperatorSession`-level resource-safety contract (no
  forbidden resource attached anywhere under `__slots__`) is
  preserved.

**Rationale.** Mirrors Phase 3.12c Pattern Ledger Step 11. The
single new field is the minimum integration surface that lets
dispatcher call sites mutate ledger state copy-on-write
(`self.growth_ledger = self.growth_ledger.observe(...)`).

## LOCK C — Phase 3.13 resource-audit tier authorized

**Lock:** Because LOCK B adds `OperatorSession.growth_ledger`,
Step 7 must explicitly update the two persistence resource-audit
fixtures:

```text
brain/ui/fixtures/persistence_observe_resource_audit.py
brain/ui/fixtures/persistence_ops_resource_audit.py
```

The exact extension is the addition of a new Phase 3.13 tier:

```python
#: Phase 3.13 (Growth Ledger) additions to the OperatorSession
#: attribute surface. The fixture allows this name through the
#: I-OBSERVE-08 / I-OPSHARDEN-13 checks because the v0.23 catalog
#: patch authorizes it; the future I-GROW resource-audit row asserts
#: the positive shape (no callable / handle / client) of the Growth
#: Ledger field.
_PHASE_3_13_SESSION_ATTRS: frozenset[str] = frozenset({"growth_ledger"})
```

`_PHASE_3_13_SESSION_ATTRS` is folded into the `allowed` union that
`I-OBSERVE-08` and `I-OPSHARDEN-13` compare against
`_ALLOWED_SESSION_ATTRS`:

```python
allowed = (
    _PHASE_3_9_SESSION_ATTRS
    | _PHASE_3_10C_SESSION_ATTRS
    | _PHASE_3_12C_SESSION_ATTRS
    | _PHASE_3_13_SESSION_ATTRS
)
```

This is **authorized scope, not a deviation**. The Phase 3.12c Step 11
deviation precedent (audit tier added during implementation rather
than at plan time) is the cautionary precedent the Step 4 corrigenda
explicitly avoids. Step 5 catalog planning must enumerate the audit
tier update in its file list, and Step 7 must apply it as planned.

**Positive resource-shape validation remains owned by the future
`I-GROW` structural row**, mirroring how `I-PLEDGER-16` owns the
positive `OperatorSession.pattern_ledger` shape check. The two
persistence resource-audit fixtures change only at the `_ALLOWED`
membership level; their structural negative-resource assertions
(`sqlite3.Connection`, `Cursor`, `callable`, `fileno`,
`send_signal` / `communicate`) are unchanged and continue to iterate
`_ALLOWED_SESSION_ATTRS`.

## LOCK D — Dispatch-time observe only

**Lock:** Growth Ledger observes only at the end of successful
typed dispatcher paths, using the existing Phase 3.10c
outcome-detection contract.

**Allowed observe triggers in v1:**

- successful `_dispatch_stream_append` — emits
  `STREAM_CHUNK_ACCEPTED` and (by Pattern Ledger entry-delta tuple
  comparison) optionally `PATTERN_ENTRY_CREATED` or
  `PATTERN_ENTRY_UPDATED`
- successful `_dispatch_stream_promote` — emits
  `STREAM_PROMOTION_QUEUED`
- successful `_dispatch_step` — emits `TICK_SUCCEEDED` and (by
  pre/post tick set delta) `PROFILE_DOMAIN_ADDED` and
  `MSI_MEMBER_ADDED` per addition

**Forbidden observe triggers:**

- any read-only command (`/state`, `/tick`, `/stream-summary`,
  `/stream-candidates`, `/session-status`, `/db-status`,
  `/db-summary`, `/profile-summary`, `/stream-db-summary`,
  `/db-diff`, `/db-verify`, `/db-backup`, `/autosave-status`)
- parse failures (`LocalCommandError` never reaches an observe
  call site)
- dispatch failures (a dispatcher returning the
  Phase 3.10c-typed negative signal does not observe)
- tick failures (a `tick()` exception, an empty queue, or a
  `PerceptEvent` validation failure leaves the ledger unchanged)
- status / error string parsing (no `session.status_message`,
  `session.error_message`, UI output, or exception-message
  inspection)
- save / load (covered by the deferred set in LOCK J)
- coherence report construction (covered by the deferred set in
  LOCK J)
- fixtures (no observe call inside any fixture; fixtures use
  direct constructors and synthetic deltas)
- CLI status output (no observe driven by render / snapshot /
  command_line paths)

**Rationale.** Identical in shape to the Phase 3.12c Pattern Ledger
discipline (`I-PLEDGER-13` / `I-PLEDGER-14`) and the Phase 3.10c
autosave outcome-detection rule (`I-AUTOSAVE-14`). Reading typed
return values rather than status strings is what keeps the substrate
honest under failure.

## LOCK E — Event ID scheme

**Lock:** Every `GrowthEvent.event_id` is computed deterministically
as:

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

**Also locked:**

- Inputs are the **closed immutable acceptance payload only** (the
  five fields above, in this exact order).
- **No `dict` participates** in the id input. No `set` either. The
  `repr()` of a `dict` is insertion-ordered in CPython, but a future
  refactor placing a dict into the id input would be
  re-ordering-sensitive; the lock forbids it.
- **No raw object** participates in the id input. Other records
  (e.g. a `TickRecord`) are referenced only by their bounded
  printable identifier strings inside the `references` tuple.
- **No time / random / PID / hostname / `id(...)` / env lookup**
  participates in the id derivation path. The scheme must be
  reproducible across runs given the same payload.
- **Widening the id input set is a catalog-version-bump operation**,
  not an in-place edit, because existing `event_id` values would
  no longer match.

**Rationale.** Mirrors `I-PLEDGER-12` (Pattern Ledger uses
`"pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]`).
Same prefix-discriminated 16-hex-char convention, same closed
immutable input shape, same idempotency-on-duplicate guarantee.

## LOCK F — Duplicate event handling

**Lock:** Duplicate event payloads are **idempotent**.

- If an event with the same `event_id` already exists in
  `self.events`, `observe(...)` returns `self` unchanged. The
  same `GrowthLedger` instance is returned, not a new one with an
  identical tuple.
- `observe(...)` **does not raise** on duplicate payloads. The
  duplicate is a silent no-op by design.
- **Direct `GrowthLedger` construction** with two `GrowthEvent`
  records that share an `event_id` value **rejects** at the
  constructor level. The frozen / slotted dataclass post-init runs
  a uniqueness check across `events`, and a duplicate id raises
  `ValueError`.

**Rationale.** The dual contract — `observe(...)` is silently
idempotent, direct construction rejects — is exactly the Pattern
Ledger discipline (`PatternLedger.observe(...)` silently dedupes,
`PatternLedger.__post_init__` rejects malformed entries). It keeps
the runtime observe call sites trivially safe while keeping the
direct-construction surface strict for fixture / test code.

## LOCK G — Duplicate references within one event

**Lock:** References within one `GrowthEvent.references` tuple
**must be unique**.

- Direct `GrowthEvent` construction with a `references` tuple
  containing duplicate entries (e.g. `("X", "X")`) **rejects** at
  the constructor level with `ValueError`. The same rejection
  applies to `GrowthLedger.__post_init__` if it receives a malformed
  `GrowthEvent`.
- `observe(...)` performs reference-tuple validation **before**
  constructing the event. A caller passing
  `references=("chunk-1", "chunk-1")` raises before any id
  derivation. The observe path therefore never silently collapses
  malformed references into a different id.

**Rationale.** Duplicate references inside a single event have no
clear semantic meaning in the v1 vocabulary
(`STREAM_CHUNK_ACCEPTED` references exactly one `chunk_id`;
`PATTERN_ENTRY_CREATED` exactly one `pattern_id`;
`STREAM_PROMOTION_QUEUED` exactly one `candidate_id`; `TICK_SUCCEEDED`
exactly one tick label; `PROFILE_DOMAIN_ADDED` / `MSI_MEMBER_ADDED`
exactly one `content_id`). Admitting duplicates inflates the count
without adding information and invites Goodhart pressure on a future
per-event-type or aggregate metric. Rejecting at construction time
keeps the substrate honest.

**Validation order — fixed across LOCK F, LOCK G, LOCK H.** The
`observe(...)` path runs its validation in this exact order:

```text
1. saturation check       (LOCK H — at >= GROWTH_LEDGER_MAX_EVENTS,
                            return self unchanged; no further work)
2. event_type / source    (closed enum membership)
3. tick                   (non-negative int)
4. references shape       (tuple of bounded printable strings;
                            no element equals COGITO_ID;
                            0 <= len <= GROWTH_LEDGER_REFERENCE_MAX)
5. references uniqueness  (LOCK G — reject duplicate entries within
                            references tuple BEFORE event_id derivation)
6. provenance             (bounded printable, non-empty)
7. event_id derivation    (LOCK E — sha256 over the closed
                            immutable acceptance payload)
8. duplicate-event check  (LOCK F — if event_id already present in
                            self.events, return self unchanged)
9. append                 (copy-on-write; return new GrowthLedger)
```

This order makes LOCK F and LOCK G non-contradictory: malformed
references (duplicates within one event's reference tuple) reject
**before** any id derivation; duplicate event payloads (two
distinct observe calls with the same closed payload) collapse to
the same `event_id` and are silently idempotent at step 8. The
direct-construction path (LOCK F) runs the same `__post_init__`
validation in the same order, except that duplicate event_ids
across the constructed `events` tuple raise instead of returning
self (direct construction has no `self` to return).

## LOCK H — Max events behavior

**Lock:** At `len(self.events) >= GROWTH_LEDGER_MAX_EVENTS`,
`observe(...)` of any new event returns `self` unchanged.

**Explicitly forbidden behaviors at cap:**

- no eviction
- no pruning
- no FIFO drop (oldest-first removal)
- no LIFO drop (newest-first removal)
- no overwrite of any existing event slot
- no random replacement
- no per-event-type rebalancing

**Existing duplicate event handling at cap:** if the incoming
payload's `event_id` already matches an existing entry,
`observe(...)` still returns `self` unchanged (the LOCK F
idempotency rule subsumes LOCK H — both paths return self).

**Rationale.** Mirrors Phase 3.12c Pattern Ledger LOCK E. Hard
refusal at cap is the minimum-complexity bound that preserves the
anti-Goodhart invariant: spam cannot increase the event count
beyond `GROWTH_LEDGER_MAX_EVENTS`, and the implementation has no
ranking or eviction policy to misalign.

**Refusal scope — ledger-append boundary only.** "Hard refusal" in
this lock means the **ledger append refuses**. It does **not**
mean:

- the dispatcher's return value changes (the dispatcher still
  returns its existing Phase 3.10c-typed outcome signal — `True`
  on success, the existing negative signal on failure)
- the user-facing operator output changes (no new error message,
  no new status banner, no new exception bubbles out of the
  observe call)
- any other runtime ordering, queue, history, or kernel surface
  is affected
- agency / refusal / consent language enters the substrate (the
  module surface has no "refuse" verb; the contract is just
  "returns `self` unchanged")

Step 7 implementation must keep the failure-mode silent: the
operator session continues exactly as if the observe call had
landed an event, with the only observable consequence being that
`counts_by_type()` no longer increments for new events past the
cap.

## LOCK I — Final constants

**Lock:** The v1 constants are:

```text
GROWTH_LEDGER_MAX_EVENTS         = 256
GROWTH_LEDGER_REFERENCE_MAX      = 8
GROWTH_LEDGER_ID_MAX             = 64
GROWTH_LEDGER_PROVENANCE_MAX     = 64
```

**Also locked:**

```text
GROWTH_LEDGER_SOURCE_MAX         = 64
```

`GROWTH_LEDGER_SOURCE_MAX` exists to bound the length of any
bounded printable label that appears alongside the
`GrowthEventSource` enum (e.g. provenance prefixes such as
`"stream_append:_dispatch_stream_append"`, when used in places
where the closed enum value itself is not the only printable
surface). It **does not** widen the closed `GrowthEventSource`
enum and **does not** authorize any new enum member. Adding or
removing a `GrowthEventSource` member remains a catalog-version-bump
operation (Step 5 / Step 6).

**Not added in v1:**

- `GROWTH_LEDGER_SNAPSHOT_MAX` — no `GrowthLedgerSnapshot` record
  exists in v1 (LOCK M).
- `GROWTH_LEDGER_OBSERVE_LIMIT_PER_TYPE` — no per-event-type cap
  in v1 (LOCK N).

**Rationale.** 256 / 8 / 64 / 64 match the Step 2 synthesis
defaults, are conservative against the existing
`STREAM_HISTORY_MAX_CHUNKS = 256` chunk cap, and mirror the
Pattern Ledger `PATTERN_LEDGER_ID_MAX` and Coherence Monitor
source-label conventions. `GROWTH_LEDGER_SOURCE_MAX = 64` reuses the
same width so the v1 module avoids any 32-vs-64 ambiguity.

## LOCK J — v1 event scope

**Lock — v1 emits these event types only:**

```text
STREAM_CHUNK_ACCEPTED
PATTERN_ENTRY_CREATED
PATTERN_ENTRY_UPDATED
STREAM_PROMOTION_QUEUED
TICK_SUCCEEDED
PROFILE_DOMAIN_ADDED
MSI_MEMBER_ADDED
```

**Lock — these event types are deferred (not emitted in v1):**

```text
SESSION_SAVED
SESSION_LOADED
COHERENCE_REPORT_BUILT
```

**Deferred-enum-member policy.** Deferred event types **may exist
as closed-enum members** on `GrowthEventType` for future
compatibility, but Step 7 v1 must:

- never observe them from any v1 call site,
- enumerate them in catalog row text as "deferred — not emitted
  in v1",
- ensure the future `I-GROW` row family includes an explicit
  fixture row that asserts these enum values are **not emitted by**
  `_dispatch_save_session`, `_dispatch_load_session`, or
  `build_full_coherence_report` (or any other path) in v1.

Alternatively, Step 5 catalog planning may decide to omit the
deferred enum members from the v1 enum entirely. Either choice is
acceptable; the lock is that the deferred names are forbidden as
emitted events in v1 regardless.

**Rationale.** Deferred trio carries identified risk: session-local
ledger loses `SESSION_LOADED` on the very session that loads;
`COHERENCE_REPORT_BUILT` framing invites a quality / truth reading.
Narrow v1 sidesteps both risks until the Step 8 behavior report
shows whether either is load-bearing.

## LOCK K — Profile/MSI delta derivation

**Lock:** `PROFILE_DOMAIN_ADDED` and `MSI_MEMBER_ADDED` are
derived **after** a successful tick by comparing pre-tick and
post-tick bounded sets:

```text
PROFILE_DOMAIN_ADDED:
  for content_id in (post_state.profile.domain
                     - pre_state.profile.domain):
      observe(PROFILE_DOMAIN_ADDED, references=(content_id,), ...)

MSI_MEMBER_ADDED:
  for content_id in (post_state.msi.contents
                     - pre_state.msi.contents):
      observe(MSI_MEMBER_ADDED, references=(content_id,), ...)
```

**Only additions are recorded.** Removals, replacements, or
re-orderings do not generate Growth Ledger events in v1. The
ledger never emits a `PROFILE_DOMAIN_REMOVED` /
`MSI_MEMBER_REMOVED` event. Deletion events remain explicitly out
of v1 scope.

**No semantic interpretation of the additions.** The Growth Ledger
records the addition as a bounded `content_id` reference under the
post-tick state delta. It does **not** interpret what the
additions "mean".

**Wording requirement:** these events are **accepted additions
only, not evidence of identity, selfhood, agency, preference,
truth, or durable self-model state**. Step 7 must include this
exact wording care in the module docstring and in the eventual
catalog row text for `I-GROW-*` rows covering profile / MSI
additions.

**Rationale.** Pre/post bounded-set delta is the cleanest
outcome-detection signal available for the typed kernel surface.
`_dispatch_step` already records `prior_state`,
`prior_latest_tick`, and `prior_queue_size` locally for the
failure-rollback contract; reusing `prior_state` for the delta
avoids any new state-capture machinery and avoids any TickRecord
field-parsing.

## LOCK L — TICK_SUCCEEDED reference shape

**Lock:** The `TICK_SUCCEEDED` event's `references` tuple is:

```text
references = (f"tick-{record.tick_index}",)
```

`record.tick_index` is a non-negative int already produced by the
kernel and already used in existing renderings and bounded printable
contexts. The `"tick-"` prefix discriminates the bounded printable
identifier from arbitrary integer strings and keeps the reference
shape consistent across runs.

**Step 5 override clause.** If Step 5 catalog planning discovers a
more canonical bounded id on `TickRecord` in the current repo
(e.g. an existing `tick_record_id: str` field that the kernel
already emits), Step 5 may propose that alternative as the
locked reference shape. The decision is recorded in the catalog
patch plan as either "accepted LOCK L unchanged" or "amended
LOCK L to use `<alternative>` because <repo evidence>".

This is the only Step 5-level override permitted on the reference
shape; any other widening (e.g. adding chunk ids to a tick event)
remains a catalog-version-bump operation.

## LOCK M — No GrowthLedgerSnapshot in v1

**Lock:** No `GrowthLedgerSnapshot` record exists in v1.

**Allowed read-only summary:**

```python
def counts_by_type(self) -> tuple[tuple[str, int], ...]:
    """Return a deterministic ordered tuple of
    (event_type.value, count) pairs over the closed
    GrowthEventType enum. Factual summary; NOT a score."""
```

The return shape is:

- A `tuple[tuple[str, int], ...]`, never a `list`, `dict`, or
  scalar.
- Ordered by the closed `GrowthEventType` enum's declaration
  order (deterministic across runs).
- One pair per enum value, including deferred enum members if they
  exist (count of `0` for deferred members in v1).

This is a **factual summary, not a score**. No
`growth_total`, `growth_index`, `growth_rate`,
`intelligence_score`, `awareness_score`, `iness_score`,
`coherence_quality`, `capability_score`, `maturity_score`, or
similar scalar exists in `GrowthEvent`, `GrowthLedger`, or any
helper return type.

**No `/growth-ledger` UI command in v1** (see LOCK S). The
`counts_by_type()` surface is reachable only from in-process
callers (fixtures and future internal substrates); no operator
verb exposes it in Phase 3.13.

## LOCK N — Per-event-type caps deferred

**Lock:** No per-event-type caps in v1.

The v1 saturation discipline is exactly:

- one global `max_events` cap (`GROWTH_LEDGER_MAX_EVENTS = 256`,
  LOCK I)
- deterministic dedup by `event_id` (LOCK F)
- hard refusal at cap (LOCK H)

**Defer to a later campaign:** if the Step 8 behavior report shows
that one event type (e.g. `STREAM_CHUNK_ACCEPTED` under saturation
spam) crowds out other event types under the global cap, a
follow-up reviewed catalog patch may add per-event-type caps then.
That patch would introduce
`GROWTH_LEDGER_OBSERVE_LIMIT_PER_TYPE` or an equivalent surface and
its own `I-GROW` rows.

**Rationale.** Per-event-type caps add complexity (per-type
counters, per-type rejection paths, per-type fixture rows) without
clear v1 benefit. Global cap + dedup is the minimum-complexity
anti-Goodhart bound.

## LOCK O — Allowed imports for growth_ledger.py

**Lock — the only allowed imports in
`brain/development/growth_ledger.py` are:**

```text
dataclasses
enum
hashlib
typing
brain.tlica.profile         (for COGITO_ID only)
```

**Not allowed in v1:**

- `fractions` — no `Fraction` field in v1 (no statistic needs exact
  arithmetic; `counts_by_type` returns ints). Step 5 may propose
  re-introducing this import only if a `Fraction`-valued surface is
  needed and is itself reviewed.
- `brain.development.pattern_ledger`,
  `brain.development.coherence_monitor`,
  `brain.development.text_stream` — none of these is imported at
  runtime. Integration is by **bounded printable id string only**,
  passed in from the call site in `brain/ui/session.py`.
- `brain.tick` — the typed `BrainState` record is not imported.
  The runtime `tick` callable is forbidden.
- `brain.llm` — no LLM client field. The static AST audit (Step 5
  fixture `growth_ledger_static_audit`) must reject this import.
- `brain.ui.session` — no `OperatorSession` import. The session
  field (if accepted by LOCK B) holds a `GrowthLedger` value; the
  integration call sites live **in** session.py, **not** in
  growth_ledger.py.
- `sqlite3`, `pathlib`, `tempfile`, `shutil`, `os`, `subprocess`,
  `socket`, `urllib`, `http`, `requests`, `curses`, `threading`,
  `asyncio`, `atexit`, `signal`, `importlib`, `math` — forbidden
  outright (see LOCK P for the union).

**Dependency direction:**

```text
session.py    imports    growth_ledger.py    yes
growth_ledger.py imports session.py          NO
growth_ledger.py imports pattern_ledger      NO
growth_ledger.py imports coherence_monitor   NO
growth_ledger.py imports tick                NO
growth_ledger.py imports llm                 NO
growth_ledger.py imports ui.*                NO
```

The dependency direction is **one-way**. Step 5 fixtures must
include a static AST audit that asserts both the allowed list (no
unexpected imports) and the dependency direction (no import of
session / runtime / development substrates back into
growth_ledger.py).

## LOCK P — Forbidden imports / calls

**Lock — the static AST audit must reject every name below from
appearing inside `brain/development/growth_ledger.py` (either as
an `import` statement or as a call expression, as appropriate):**

Forbidden imports:

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
brain.tick                  (the tick callable; the BrainState
                              record is also forbidden at runtime
                              under the LOCK O recommendation)
brain.ui                    (any submodule)
brain.development.pattern_ledger
brain.development.coherence_monitor
threading
asyncio
atexit
signal
importlib
math
```

Forbidden calls / dynamic execution:

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
open                        (no filesystem mutation; no read either)
tick                        (no call to brain.tick.tick)
save_session
load_session
db_backup
db_verify
maybe_autosave_after_mutation
build_coherence_report
build_full_coherence_report
PatternLedger.observe       (PatternLedger.observe runs in
                              session.py BEFORE the growth observe
                              site; growth_ledger.py must not call it)
```

The union of LOCK O (allowed) and LOCK P (forbidden) is the
complete static-audit contract for the future module. Step 5
fixtures must implement both: an "only these imports appear"
positive assertion and a "none of these names appear" negative
assertion.

## LOCK Q — Non-claim audit

**Lock — Growth Ledger inherits the Coherence Monitor's forbidden
non-claim terms set.**

The canonical source is the
`_FORBIDDEN_NON_CLAIM_TERMS` tuple in
`brain/development/coherence_monitor.py`
(line 1234 as of catalog v0.22). The Step 5 catalog plan must
decide between two acceptable mechanisms:

- **Option A — fixture-side import / compare (recommended).** The
  static-audit fixture for `growth_ledger.py` imports the canonical
  `_FORBIDDEN_NON_CLAIM_TERMS` tuple from
  `brain.development.coherence_monitor` and asserts that the
  literal source of `brain/development/growth_ledger.py` contains
  none of those terms. `growth_ledger.py` itself does **not**
  import the Coherence Monitor module (preserving LOCK O dependency
  direction).
- **Option B — duplicate the list in the fixture.** The fixture
  redeclares the forbidden-terms tuple as a local constant and adds
  a `static_audit_terms_in_sync_with_coherence_monitor` assertion
  that compares the local copy against the canonical source. The
  comparison check is itself a fixture-row obligation.

**Recommendation:** Option A. It avoids drift by construction.
Option B is acceptable only if Step 5 explicitly accepts the
synchronization-check obligation and lists a fixture row that
enforces it.

**Also locked — no field, docstring, catalog row text, fixture
docstring or output, bounded printable string, or report output
produced by the Growth Ledger may claim any of:**

```text
consciousness
sentience
subjective experience / qualia
semantic understanding / language understanding / comprehension
truth adjudication / PRESERVE / DAMAGE judgment
agency / intent / will / desire
self-modification of code / fixtures / catalog / runtime
personhood
aggregate I-ness
aggregate growth score
capability / maturity / intelligence score
awareness score
coherence quality score
```

The static AST audit and the non-claim audit are the structural
gate. Wording care alone is not sufficient.

## LOCK R — Banned interpretations of growth

**Lock — the Step 3 kickoff Banned Interpretations block is
restated as a lock and applies to every Growth Ledger surface
(module source, docstrings, constant names, catalog row text,
fixture docstrings, generated bounded printable strings,
behavior report wording, step report disclosures, and any future
follow-up campaign that quotes the Growth Ledger).**

**"Growth" means:**

> a bounded observed accepted event delta — one accepted,
> constructor-validated event, recorded by reference, with no
> scalar metric attached.

**"Growth" does NOT mean:**

```text
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
```

The Growth Ledger never **totalizes**, **ranks**, **normalizes**,
**scores**, **summarizes-as-scalar**, or **expresses a scalar over
the events it stores**. The only allowed summary surface is
`counts_by_type()` (LOCK M), which returns a labelled tuple of
ints over the closed enum.

## LOCK S — Future UI deferred

**Lock — no Growth Ledger UI in v1.**

Specifically forbidden in Phase 3.13:

- no new `OperatorCommand` enum member (no `GROWTH_LEDGER` verb)
- no parser addition (no `/growth-ledger` slash command in
  `brain/ui/command_line.py`)
- no new `active_view` value (no `"growth_ledger"` view added to
  the `OperatorSession.active_view` allowed set)
- no `brain/ui/render.py` change
- no `brain/ui/snapshot.py` change
- no `brain/ui/commands.py` change
- no `brain/ui/command_line.py` change

Future Growth Ledger UI requires a separate reviewed catalog
patch. The Phase 3.12c Pattern Ledger UI (`I-PLEDGER-17`,
DEFERRED) and the Coherence Monitor UI (`I-COHMON-13`, DEFERRED)
are the precedents: each is structurally documented but not
promoted in v1.

## LOCK T — Catalog planning obligation

**Lock — Step 5 must produce exactly this document:**

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CATALOG_PATCH_PLAN.md
```

The plan must include, at minimum:

- the **`I-GROW-*` row family**, named row-by-row, with one-line
  purpose per row
- the **exact status** of each row
  (`REQUIRED` / `STRUCTURAL` / `DEFERRED` / `NOT-EXERCISED` /
  `OBSERVED`)
- the **exact catalog version bump** from `v0.22` to `v0.23`
- the **exact count delta** by status
  (`REQUIRED += n`, `STRUCTURAL += n`, `DEFERRED += n`,
  `NOT-EXERCISED += n`, `OBSERVED += n`)
- the **exact fixture list** (file paths under
  `brain/development/fixtures/` or `brain/ui/fixtures/`), with
  the row IDs each fixture drives
- the **exact implementation files** that Step 7 would touch
  (including `brain/development/growth_ledger.py`,
  `brain/ui/session.py`, `brain/invariants.py`,
  `tools/catalog.py`, the catalog rows in `INVARIANT_CATALOG.md`,
  the catalog version + counts banner in `README.md`,
  `CURRENT_MISSION.md`, and `CURRENT_CAMPAIGN.md`)
- the **explicit resource-audit fixture tier updates**
  (the `_PHASE_3_13_SESSION_ATTRS` addition in both
  `brain/ui/fixtures/persistence_observe_resource_audit.py` and
  `brain/ui/fixtures/persistence_ops_resource_audit.py`),
  authorized by LOCK C above
- a stop at Step 6 Review Gate A: the plan must not implement
  anything

Step 5 must **not** implement Growth Ledger code, must **not**
add fixtures, and must **not** edit `INVARIANT_CATALOG.md`. The
catalog patch plan is a document; the catalog itself changes only
in Step 7, and only if Step 6 accepts the plan.

## ChatGPT/Codex Consultation

Before finalizing this corrigenda, a single Stage A advisory review
call was run against the locked lock set above. The bridge usage
disclosure is below.

The actual wrapper command was:

```text
python3 tools/claude_helpers/codex_chatgpt_subagent.py \
  --mode review --model gpt-5.5 --effort medium \
  --timeout 180 \
  --prompt-file /tmp/toyi_chatgpt_step4_question.md \
  > /tmp/toyi_chatgpt_step4_answer.md
```

```text
ChatGPT/Codex consultation:
- used:           yes
- mode:           review
- model:          gpt-5.5
- effort:         medium
- wrapper command: python3 tools/claude_helpers/codex_chatgpt_subagent.py
                     --mode review --model gpt-5.5 --effort medium
                     --timeout 180
                     --prompt-file /tmp/toyi_chatgpt_step4_question.md
- question file:   /tmp/toyi_chatgpt_step4_question.md
- answer file:     /tmp/toyi_chatgpt_step4_answer.md
- wrapper status:  exit 0; error_class null; codex_returncode 0;
                   duration_ms 36739; stdout_bytes 8409;
                   stderr_bytes 11261; truncated false; codex-cli
                   0.130.0; auth "Logged in using ChatGPT". Audit
                   JSONL appended at .claude/codex_bridge_logs/
                   (gitignored).
- accepted advice:
   - Sharpen LOCK B wording to "planned v1 attachment point, not
     authorization to edit runtime/session code in Step 4"
     (applied as the second paragraph of LOCK B).
   - Lock a validation order across LOCK F / LOCK G / LOCK H to
     resolve the apparent contradiction between "duplicate events
     idempotent" and "duplicate references rejected" (added as a
     "Validation order" block at the end of LOCK G; references
     uniqueness check runs BEFORE event_id derivation, so the two
     locks are non-contradictory by construction).
   - Narrow LOCK H "hard refusal" to the ledger-append boundary
     only (added as a "Refusal scope" block; dispatcher return
     value, user-facing output, kernel surface, and queue/history
     are all explicitly unaffected; no agency / refusal / consent
     language enters the substrate).
   - The advisor flagged that the corrigenda should restate
     "Step 4 does not authorize implementation"; this is already
     present in the Purpose section, in the Corrigenda Authority
     section, in every individual lock's framing as a Step 5/Step 7
     constraint, and in the Next Artifact section. No additional
     edit needed; advice noted as already-satisfied.
   - The advisor flagged that fixtures must cover idempotency,
     duplicate-reference rejection, cap refusal, canonical id
     stability, allowed/disallowed event types, tick reference
     shape, and the no-hidden-persistence rule. The Step 3 kickoff
     already enumerates six fixture families that cover exactly
     this surface (growth_ledger_constructor,
     growth_ledger_event_id, growth_ledger_observe,
     growth_ledger_static_audit, growth_ledger_no_runtime_coupling,
     growth_ledger_session_integration). LOCK T binds Step 5 to
     produce the exact fixture list; the advisor's coverage
     requirement is therefore deferred to Step 5 catalog planning,
     not amended into the corrigenda.
- rejected advice:
   - "growth_ledger.py imports only dataclasses/enum/hashlib/typing
     /COGITO_ID is overly implementation-specific for Step 4."
     Rejected: the corrigenda's defined job is to lock
     implementation contracts that bind Step 5 catalog planning
     and any Step 7 implementation. Locking the allowed import set
     is exactly the kind of constraint the corrigenda must fix so
     Step 5 can be precise. LOCK O already includes a Step 5
     amendment clause ("Step 5 may propose re-introducing this
     import only if a Fraction-valued surface is needed and is
     itself reviewed") — that satisfies the advisor's "Step 5
     may request an amendment if a safer stdlib import is needed"
     suggestion. No further softening required.
   - "Define event identity to include version / domain prefix."
     Partially rejected: the locked id scheme is
     "growth:" + sha256(repr(closed-5-tuple))[:16]; the "growth:"
     prefix already discriminates the v1 id namespace. Adding a
     separate version field to the id input would require a
     catalog-version-bump operation per LOCK E and is exactly the
     kind of widening Step 5 must propose explicitly if needed.
     Locking it pre-emptively in v1 widens the id contract without
     evidence that it's needed.
   - "Tick reference may not be globally unique across reset/load
     paths." Rejected for v1: save/load is deferred by LOCK A, so
     there is no load path in v1. LOCK L already includes a Step 5
     override clause if a more canonical bounded id is found on
     TickRecord. The session-local-only framing of LOCK A makes
     reset/load collision non-load-bearing in v1.
- reason:          Advisor's three substantive concerns (LOCK B
                   wording, validation order between LOCK F/LOCK G,
                   LOCK H refusal-scope clarity) were adopted as
                   inline corrigenda edits. Remaining advisor
                   concerns were either already addressed by
                   existing lock language or appropriately deferred
                   to Step 5 catalog planning. "Minor disagreement,
                   medium confidence" verdict is consistent with
                   the locked design.
```

Treat the bridge output as advisory. Repo-local files, gates, and
invariants override ChatGPT advice. If ChatGPT advice conflicts with
a repo-local constraint, the conflict is reported and the repo wins.

## Next Artifact

Step 5:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CATALOG_PATCH_PLAN.md
```

Step 5 will translate every lock above into the catalog-patch
contract — exact row family, exact statuses, exact v0.22 → v0.23
banner, exact count delta, exact fixture list, exact implementation
files, and the explicit resource-audit fixture tier updates LOCK C
already authorized.

**Implementation remains blocked.** Step 5 is documentation only.
Step 6 is Review Gate A. Step 7 applies the implementation **only
if** the operator explicitly accepts the catalog patch plan at
Review Gate A. Nothing in this corrigenda authorizes a code change
under `brain/**`, `tools/**`, `.claude/**`, `INVARIANT_CATALOG.md`,
`README.md`, `lean_reference/**`, `scenarios/**`, or `traces/**`.

## Validation

Re-ran after writing this corrigenda (no source under `brain/**`,
`tools/**`, `.claude/**`, `lean_reference/**`, `scenarios/**`, or
`traces/**` was touched; no edit to `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`PHASE3_13_GROWTH_LEDGER_ROADMAP.md`, the Step 2 synthesis, or the
Step 3 kickoff; only this new documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS (240/85/11/14/16) |
| `python3 -m tools.citations verify` | PASS (100 citations resolved) |
| `python3 -m tools.import_audit` | PASS (I-PCE-05 clean) |
| `python3 -m brain.invariants run` | PASS (333 rows; 0 gate failures) |
| `bash tools/check_all.sh` | PASS (All checks passed.) |
