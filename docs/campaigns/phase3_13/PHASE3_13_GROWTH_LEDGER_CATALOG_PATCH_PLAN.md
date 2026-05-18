# PHASE3_13_GROWTH_LEDGER_CATALOG_PATCH_PLAN.md

## Purpose

This catalog patch plan converts the Step 4 locked corrigenda
(`docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CORRIGENDA.md`)
into an exact catalog / version / fixture / implementation plan for
Growth Ledger v1.

The plan is the **contract** that Step 6 Review Gate A approves,
amends, or rejects. Step 7 implementation, if authorized, must
match this contract exactly — including the row family, statuses,
count delta, fixture set, implementation file list, validation
gates, and resource-audit fixture tier updates.

State clearly:

- **Step 5 does not authorize implementation.**
- **Step 6 Review Gate A must explicitly accept or amend the
  plan.** Until that gate clears, no source under `brain/**`,
  `tools/**`, `.claude/**`, `INVARIANT_CATALOG.md`, `README.md`,
  `lean_reference/**`, `scenarios/**`, or `traces/**` is
  modified in pursuit of Growth Ledger implementation.
- **Step 7 may implement only after Step 6 acceptance**, and only
  the file set this plan enumerates (as amended by Step 6, if
  amended).

This document touches no source outside the new file path. It
introduces no fixture, no committed helper, and no runtime
behavior change.

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
Phase 3.13 Step 4 status:         complete (f0cbd21
                                  "phase3.13 step4: growth ledger
                                  corrigenda"); pushed
Step 4 corrigenda binding:        LOCK A through LOCK T bind this
                                  Step 5 plan
Active Stage A advisory bridge:   used in Steps 1, 2, 3, 4 and
                                  again in this Step 5 (review /
                                  gpt-5.5 / high)
Preflight (verified at start of Step 5):
  python3 -m tools.catalog counts     PASS  (240/85/11/14/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (333 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Locks Imported from Corrigenda

Step 4 issued LOCK A through LOCK T. The plan does **not** rewrite
the locks loosely; it preserves every material decision verbatim
and uses each lock to constrain at least one row of the proposed
catalog patch.

```text
LOCK A  session-local-only v1
        - no DB schema change
        - no SCHEMA_VERSION bump
        - no save-session serialization
        - no load-session restoration
        - no autosave trigger-set extension
        - cold start empty
        - loaded session begins growth-event-empty

LOCK B  OperatorSession.growth_ledger field accepted
        - "planned v1 attachment point, not authorization to edit
          runtime/session code in Step 4"
        - field default = GrowthLedger() via default_factory
        - isinstance check in __post_init__
        - resource-safe (no callable / handle / client under
          OperatorSession.__slots__)

LOCK C  _PHASE_3_13_SESSION_ATTRS audit tier authorized
        - frozenset({"growth_ledger"}) added to both
          brain/ui/fixtures/persistence_observe_resource_audit.py
          and
          brain/ui/fixtures/persistence_ops_resource_audit.py
        - folded into the allowed-attrs union compared against
          _ALLOWED_SESSION_ATTRS
        - authorized scope, not a deviation
        - positive shape ownership stays with the future I-GROW
          structural row (not with I-OBSERVE-08 / I-OPSHARDEN-13)

LOCK D  dispatch-time observe only
        - allowed:  successful _dispatch_stream_append,
                    successful _dispatch_stream_promote,
                    successful _dispatch_step
        - forbidden: read-only commands, parse / dispatch / tick
                    failures, status / error string parsing,
                    save / load (deferred), coherence report
                    construction (deferred), fixtures, CLI status

LOCK E  deterministic "growth:" + sha256(repr(closed-5-tuple))[:16]
        event ids
        - closed input shape: (event_type.value, tick, source.value,
                               references, provenance)
        - no dict / set / raw object / time / random / PID /
          hostname / id() / env in id input
        - widening the id input set is a catalog-version-bump
          operation

LOCK F  duplicate event payloads idempotent
        - observe(...) returns self unchanged on duplicate event_id
        - direct GrowthLedger construction rejects duplicate ids

LOCK G  duplicate references within one event rejected
        - constructor rejects with ValueError
        - reference validation runs BEFORE event_id derivation
        - validation order is fixed across LOCK F / LOCK G / LOCK H:
            1. saturation check
            2. enum membership (event_type / source)
            3. non-negative tick
            4. references shape
            5. references uniqueness
            6. provenance
            7. event_id derivation
            8. duplicate-event check (LOCK F)
            9. append (copy-on-write)

LOCK H  hard refusal at GROWTH_LEDGER_MAX_EVENTS
        - returns self unchanged
        - no eviction / FIFO / LIFO drop / overwrite / random
          replacement / per-type rebalancing
        - refusal scope is ledger-append boundary only;
          dispatcher return / user-facing output / kernel surface
          and queue / history are unaffected

LOCK I  final constants:
        - GROWTH_LEDGER_MAX_EVENTS     = 256
        - GROWTH_LEDGER_REFERENCE_MAX  =   8
        - GROWTH_LEDGER_ID_MAX         =  64
        - GROWTH_LEDGER_PROVENANCE_MAX =  64
        - GROWTH_LEDGER_SOURCE_MAX     =  64
        - no GROWTH_LEDGER_SNAPSHOT_MAX
        - no GROWTH_LEDGER_OBSERVE_LIMIT_PER_TYPE

LOCK J  v1 event scope fixed:
        - v1 emits: STREAM_CHUNK_ACCEPTED,
                    PATTERN_ENTRY_CREATED,
                    PATTERN_ENTRY_UPDATED,
                    STREAM_PROMOTION_QUEUED,
                    TICK_SUCCEEDED,
                    PROFILE_DOMAIN_ADDED,
                    MSI_MEMBER_ADDED
        - deferred (allowed as enum members; never emitted in v1):
                    SESSION_SAVED,
                    SESSION_LOADED,
                    COHERENCE_REPORT_BUILT

LOCK K  profile / MSI additions derived by pre/post tick set delta
        - PROFILE_DOMAIN_ADDED:
            post_state.profile.domain - pre_state.profile.domain
        - MSI_MEMBER_ADDED:
            post_state.msi.contents - pre_state.msi.contents
        - additions only; no deletion events
        - "accepted addition only, not evidence of identity,
          selfhood, agency, preference, truth, or durable
          self-model state" wording requirement

LOCK L  TICK_SUCCEEDED reference shape = (f"tick-{record.tick_index}",)
        - Step 5 override clause: if a more canonical bounded
          TickRecord id exists in the current repo, Step 5 may
          propose the alternative

LOCK M  no GrowthLedgerSnapshot in v1
        - allowed surface: counts_by_type() returning
          tuple[tuple[str, int], ...]
        - no scalar / aggregate score
        - no /growth-ledger UI

LOCK N  no per-event-type caps in v1
        - global max + dedup only
        - revisit only after Step 8 behavior report

LOCK O  allowed imports for growth_ledger.py:
        - dataclasses
        - enum
        - hashlib
        - typing
        - brain.tlica.profile (COGITO_ID only)
        - no fractions / pattern_ledger / coherence_monitor /
          text_stream / tick / llm / ui / session import
        - dependency direction one-way

LOCK P  forbidden imports / calls / dynamic-execution surfaces
        locked (os / subprocess / socket / urllib / http /
        requests / pathlib / tempfile / shutil / curses /
        sqlite3 / brain.llm / brain.tick / brain.ui /
        brain.development.pattern_ledger /
        brain.development.coherence_monitor / threading /
        asyncio / atexit / signal / importlib / math; eval /
        exec / compile / __import__ / importlib.import_module /
        atexit.register / signal.signal / signal.setitimer /
        threading.* / asyncio.* / open / tick / save_session /
        load_session / db_backup / db_verify /
        maybe_autosave_after_mutation / build_coherence_report /
        build_full_coherence_report / PatternLedger.observe)

LOCK Q  non-claim term audit inherits Coherence Monitor
        _FORBIDDEN_NON_CLAIM_TERMS
        - Option A recommended: fixture-side import / compare
        - growth_ledger.py does NOT import coherence_monitor
        - no consciousness / sentience / subjective / semantic /
          truth / agency / self-modification / personhood /
          aggregate-score language on any Growth Ledger surface

LOCK R  banned interpretations of "growth"
        - growth = bounded observed accepted event delta only
        - never improvement / progress / maturity / capability /
          intelligence / selfhood / agency / consciousness /
          sentience / subjective experience / semantic
          understanding / truth tracking / preference / intent /
          awareness / coherence quality
        - never totalize / rank / normalize / score / express
          scalar

LOCK S  no v1 UI
        - no OperatorCommand member
        - no parser entry
        - no active_view value
        - no render / snapshot / commands / command_line change

LOCK T  Step 5 catalog planning obligation:
        - this document
        - I-GROW-* row family
        - exact statuses
        - exact v0.22 → v0.23 banner
        - exact count delta
        - exact fixture list
        - exact implementation file set
        - explicit resource-audit fixture tier updates
        - stop at Step 6 Review Gate A
```

## Version / Count Strategy

**Current catalog version:** `v0.22`.

**Proposed catalog version after Step 7 (if approved):** `v0.23`.

**Reason for bump.** Adding the `I-GROW-*` row family and the
Growth Ledger implementation is a catalog expansion: a new
typed helper module, a new `OperatorSession` field, two
existing audit fixtures gaining a new tier, and a row family
the catalog has not contained before. The v0.22 → v0.23 step
follows the same precedent as v0.20 → v0.21 (Pattern Ledger)
and v0.21 → v0.22 (Coherence Monitor): one campaign → one
catalog version bump → one banner paragraph at the top of
`INVARIANT_CATALOG.md` documenting the bump.

**Files Step 7 must update (specified here, not edited in
Step 5):**

```text
INVARIANT_CATALOG.md       v0.22 → v0.23 banner + I-GROW-* rows
tools/catalog.py           EXPECTED_COUNTS dict bumped to v0.23
                             counts; comment updated from
                             "v0.22 expected counts" to "v0.23
                             expected counts" with Phase 3.13
                             attribution
brain/_catalog_ids.py      regenerated from the new catalog via
                             `python3 -m tools.catalog generate-ids`
README.md                  catalog stamp + counts string updated
                             from v0.22 to v0.23 (and the matching
                             "240 / 85 / 11 / 14 / 16" stamp updated
                             to the new counts)
CURRENT_MISSION.md         baseline block "Catalog: v0.22" and the
                             counts stamp updated
CURRENT_CAMPAIGN.md        baseline block "Catalog: v0.22" and the
                             counts stamp updated
```

**Step 5 does not edit any of these files.** They are listed so
that Step 7 has a complete, auditable update set when (and only
when) Step 6 accepts the plan.

## Proposed Row Family

The row family is `I-GROW-01..I-GROW-22` (22 rows total). Each
row is named, statused, and tied to at least one fixture from the
fixture plan below. Recommended statuses are listed; if Step 6
amends a row, the count delta below is updated as part of the
amendment.

```text
ID            Status         Title (one-line)
---------------------------------------------------------------
I-GROW-01     REQUIRED       GrowthEventType closed enum
I-GROW-02     REQUIRED       GrowthEventSource closed enum
I-GROW-03     REQUIRED       GrowthEvent constructor validation
I-GROW-04     REQUIRED       event_id deterministic derivation
I-GROW-05     REQUIRED       GrowthLedger frozen / slotted / cow
I-GROW-06     REQUIRED       observe duplicate idempotent
I-GROW-07     REQUIRED       construction with duplicate ids rejects
I-GROW-08     REQUIRED       hard refusal at GROWTH_LEDGER_MAX_EVENTS
I-GROW-09     REQUIRED       counts_by_type deterministic / no scalar
I-GROW-10     REQUIRED       growth_ledger.py allowed import surface
I-GROW-11     REQUIRED       static AST audit forbidden imports/calls
I-GROW-12     REQUIRED       no unsafe resources stored in records
I-GROW-13     REQUIRED       OperatorSession.growth_ledger field
I-GROW-14     REQUIRED       _PHASE_3_13_SESSION_ATTRS audit tier
I-GROW-15     REQUIRED       _dispatch_stream_append observes correctly
I-GROW-16     REQUIRED       _dispatch_stream_promote observes correctly
I-GROW-17     REQUIRED       _dispatch_step observes tick/profile/MSI
I-GROW-18     REQUIRED       deferred event types not emitted in v1
I-GROW-19     REQUIRED       non-claim / banned-interpretation audit
I-GROW-20     STRUCTURAL     dependency direction & no runtime coupling
I-GROW-21     DEFERRED       /growth-ledger UI not in v1
I-GROW-22     NOT-EXERCISED  end-to-end behavior dry-run placeholder
```

### Row-by-row purpose

```text
I-GROW-01  REQUIRED
  GrowthEventType is a finite closed (str, Enum) class. The v1 set
  is exactly:
    STREAM_CHUNK_ACCEPTED, PATTERN_ENTRY_CREATED,
    PATTERN_ENTRY_UPDATED, STREAM_PROMOTION_QUEUED,
    TICK_SUCCEEDED, PROFILE_DOMAIN_ADDED, MSI_MEMBER_ADDED.
  The deferred members SESSION_SAVED, SESSION_LOADED,
  COHERENCE_REPORT_BUILT may exist as closed-enum members in the
  v1 module for future compatibility, but are NEVER emitted by
  any v1 call site (asserted by I-GROW-18). Adding or removing a
  member is a future catalog-version-bump operation, not an
  in-place edit.

I-GROW-02  REQUIRED
  GrowthEventSource is a finite closed (str, Enum) class
  containing the v1 sources:
    STREAM_APPEND, PATTERN_LEDGER_OBSERVE, STREAM_PROMOTE,
    STEP_DISPATCH.
  The deferred sources PERSISTENCE_SAVE, PERSISTENCE_LOAD,
  COHERENCE_MONITOR may exist as closed-enum members for future
  compatibility; they are NEVER emitted by any v1 call site
  (asserted by I-GROW-18). Member changes are catalog-bump
  operations.

I-GROW-03  REQUIRED
  GrowthEvent constructor enforces:
    - bounded printable event_id (1 <= len <= GROWTH_LEDGER_ID_MAX,
      printable, non-empty, not equal to COGITO_ID)
    - event_type and source membership in the closed enums
    - non-negative int tick
    - references is a tuple[str, ...] of bounded printable
      strings, each non-COGITO_ID, with 0 <= len <=
      GROWTH_LEDGER_REFERENCE_MAX
    - references entries are pairwise unique (LOCK G; rejected
      with ValueError before any event_id derivation)
    - bounded printable provenance (1 <= len <=
      GROWTH_LEDGER_PROVENANCE_MAX, non-empty, not COGITO_ID)
    - no silent normalization (strip / lowercase / unicode-fold
      etc.); inputs are accepted as-is or rejected.

I-GROW-04  REQUIRED
  event_id is derived deterministically as:
    event_id = "growth:" + sha256(
        repr((
            event_type.value, tick, source.value,
            references, provenance,
        )).encode("utf-8")
    ).hexdigest()[:16]
  Inputs are only the closed immutable acceptance payload above.
  No dict / set / raw object / time / random / PID / hostname /
  id(...) / env participates. The prefix is always "growth:";
  the full id length is exactly 23.

I-GROW-05  REQUIRED
  GrowthLedger is @dataclass(frozen=True, slots=True). events is
  a tuple[GrowthEvent, ...]. observe(...) returns a NEW
  GrowthLedger unless (a) the duplicate-event idempotency rule
  (LOCK F / I-GROW-06) returns self unchanged, or (b) the
  max-cap refusal rule (LOCK H / I-GROW-08) returns self
  unchanged. The original record's events tuple is never
  mutated. No callable / handle / client appears in any
  GrowthLedger field.

I-GROW-06  REQUIRED
  observe(...) is idempotent for duplicate event payloads. If
  the incoming payload's derived event_id already matches an
  existing entry, observe(...) returns self unchanged (same
  Python object, not a new ledger with an identical tuple).
  observe(...) does not raise on duplicate payloads. The
  validation order in LOCK G applies: references uniqueness is
  checked before event_id derivation, so the duplicate check
  only fires after references already pass.

I-GROW-07  REQUIRED
  Direct GrowthLedger(events=(...)) construction with two
  GrowthEvent entries sharing the same event_id value rejects
  with ValueError in __post_init__. The reject path applies to
  direct construction; observe(...) covers the same case
  silently per I-GROW-06.

I-GROW-08  REQUIRED
  At len(self.events) >= GROWTH_LEDGER_MAX_EVENTS, observe(...)
  of any new event returns self unchanged. No eviction, no
  pruning, no FIFO / LIFO drop, no overwrite, no random
  replacement, no per-type rebalancing. The refusal is the
  ledger-append boundary only — the dispatcher return value,
  user-facing output, kernel surface, and queue / history are
  unaffected.

I-GROW-09  REQUIRED
  counts_by_type() returns a deterministic
  tuple[tuple[str, int], ...] ordered by the closed
  GrowthEventType enum declaration order. Same ledger, same
  tuple, every call. No aggregate scalar exists in GrowthEvent,
  GrowthLedger, or any helper return type; the row asserts that
  no field whose name matches /growth_total|growth_index|
  growth_rate|intelligence_score|awareness_score|iness_score|
  coherence_quality|capability_score|maturity_score|growth_score|
  growth_value/ appears on the module surface.

I-GROW-10  REQUIRED
  brain/development/growth_ledger.py allowed import surface is
  exactly:
    dataclasses, enum, hashlib, typing,
    brain.tlica.profile (for COGITO_ID only).
  No other top-level import appears. In particular,
  brain.development.pattern_ledger,
  brain.development.coherence_monitor,
  brain.development.text_stream, brain.tick (any path),
  brain.llm (any path), brain.ui (any submodule), sqlite3,
  pathlib, tempfile, shutil, os, subprocess, socket, urllib,
  http, requests, curses, threading, asyncio, atexit, signal,
  importlib, math, fractions are NOT imported.

I-GROW-11  REQUIRED
  Static AST audit over brain/development/growth_ledger.py
  rejects every name in LOCK P (forbidden imports + forbidden
  calls + dynamic-execution surfaces). The audit asserts the
  source contains no eval / exec / compile / __import__ /
  importlib.import_module / atexit.register / signal.signal /
  signal.setitimer / threading.* / asyncio.* / open / tick /
  save_session / load_session / db_backup / db_verify /
  maybe_autosave_after_mutation / build_coherence_report /
  build_full_coherence_report / PatternLedger.observe.

I-GROW-12  REQUIRED
  No GrowthEvent or GrowthLedger field stores a callable, file
  handle, socket, subprocess handle, pathlib.Path,
  sqlite3.Connection / Cursor, curses object, LLM
  client-shaped object, or object with eval_consistency. The
  audit reuses the existing _value_looks_unsafe discipline that
  Coherence Monitor applies in
  brain/development/coherence_monitor.py.

I-GROW-13  REQUIRED
  OperatorSession adds exactly one new field:
    growth_ledger: GrowthLedger = field(default_factory=GrowthLedger)
  "growth_ledger" is added to _ALLOWED_SESSION_ATTRS. The
  __post_init__ contract adds:
    isinstance(self.growth_ledger, GrowthLedger)
  with an error message that mirrors the existing pattern_ledger
  isinstance message (brain/ui/session.py:370–373). The field is
  resource-safe (no callable / handle / client value type can
  pass the isinstance check).

I-GROW-14  REQUIRED
  brain/ui/fixtures/persistence_observe_resource_audit.py and
  brain/ui/fixtures/persistence_ops_resource_audit.py each
  declare:
    _PHASE_3_13_SESSION_ATTRS: frozenset[str] = frozenset(
        {"growth_ledger"})
  and fold it into the `allowed` union compared against
  _ALLOWED_SESSION_ATTRS. The negative-resource iteration
  (sqlite3.Connection, Cursor, callable, fileno, send_signal /
  communicate) is unchanged. This is authorized scope, not a
  deviation — the corrigenda LOCK C established the
  authorization at planning time.

I-GROW-15  REQUIRED
  At the end of the successful path of
  _dispatch_stream_append, the session performs:
    self.growth_ledger = self.growth_ledger.observe(
        event_type=STREAM_CHUNK_ACCEPTED, ...)
  and, if PatternLedger.observe(...) produced a delta
  (created-or-updated entry detected by comparing prior and
  post entries tuples), additionally:
    self.growth_ledger = self.growth_ledger.observe(
        event_type=PATTERN_ENTRY_CREATED, ...)
    or
    self.growth_ledger = self.growth_ledger.observe(
        event_type=PATTERN_ENTRY_UPDATED, ...)
  Failures, parse errors, and read-only paths emit nothing. The
  created/updated distinction is derived by pure tuple
  comparison, never by status-string parsing.

I-GROW-16  REQUIRED
  At the end of the successful path of
  _dispatch_stream_promote, the session performs:
    self.growth_ledger = self.growth_ledger.observe(
        event_type=STREAM_PROMOTION_QUEUED,
        references=(candidate.candidate_id,), ...)
  The _dispatch_stream_promote return value (Optional[bool]
  under the existing I-AUTOSAVE-14 outcome-detection contract)
  is the typed signal that triggers the observe; no status /
  error string is read.

I-GROW-17  REQUIRED
  At the end of the successful path of _dispatch_step, the
  session performs:
    self.growth_ledger = self.growth_ledger.observe(
        event_type=TICK_SUCCEEDED,
        references=(f"tick-{record.tick_index}",), ...)
  and, derived from pre/post bounded set deltas computed
  against the same prior_state already captured for the
  failure-rollback contract:
    for content_id in post.profile.domain - pre.profile.domain:
        observe(PROFILE_DOMAIN_ADDED,
                references=(content_id,), ...)
    for content_id in post.msi.contents - pre.msi.contents:
        observe(MSI_MEMBER_ADDED,
                references=(content_id,), ...)
  Tick failures (exceptions, empty queue, percept validation
  failure) emit nothing. No deletion / removal / rename events
  are emitted (LOCK K — additions only).

I-GROW-18  REQUIRED
  Deferred event types (SESSION_SAVED, SESSION_LOADED,
  COHERENCE_REPORT_BUILT) are present in the enum (LOCK J) but
  NEVER emitted by any v1 path. The fixture exercises a
  successful /save-session, /load-session, and
  build_full_coherence_report (where applicable) and asserts
  the resulting GrowthLedger contains zero events of those
  types. Equivalently, if Step 7 chooses to omit the deferred
  enum members entirely, the row asserts the enum does not
  contain them and that no observe call references them.

I-GROW-19  REQUIRED
  Non-claim and banned-interpretation audit over:
    - brain/development/growth_ledger.py source
    - GrowthLedger fixture outputs
    - GrowthEvent / GrowthLedger / counts_by_type bounded
      printable strings produced under representative inputs
  None of these surfaces contains any term from
  brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS
  (Option A from LOCK Q). The audit imports the canonical
  constant from the Coherence Monitor module on the fixture
  side; growth_ledger.py itself does NOT import the Coherence
  Monitor module (LOCK O).

I-GROW-20  STRUCTURAL
  Growth Ledger integration is structurally one-way and
  decoupled at runtime:
    - brain/ui/session.py imports
      brain/development/growth_ledger.py
    - brain/development/growth_ledger.py does NOT import
      session / tick / llm / ui / pattern_ledger /
      coherence_monitor / text_stream
    - GrowthLedger.observe(...) does not mutate BrainState,
      MSI, PtCns, ContentRegistry, latest_tick, tick_counter,
      OperatorSession.event_queue, stream_history,
      stream_candidates, stream_chunk_serial, PatternLedger,
      Coherence Monitor records, persistence config, or
      autosave config (a pre/post identity-stability assertion
      verifies this on a constructed session).
  The row is STRUCTURAL rather than REQUIRED because it
  asserts structural decoupling rather than a Lean-citable
  runtime equality, mirroring the precedent of
  I-PLEDGER-16 (STRUCTURAL: Pattern Ledger resource-audit
  shape).

I-GROW-21  DEFERRED
  /growth-ledger UI command is deferred. No OperatorCommand
  enum addition, no parser entry, no active_view value, no
  render / snapshot / commands / command_line change in v1.
  Future UI requires a separate reviewed catalog patch.
  Mirrors I-PLEDGER-17 (/pattern-ledger UI deferred) and
  I-COHMON-13 (/coherence-summary UI deferred).

I-GROW-22  NOT-EXERCISED
  End-to-end Growth Ledger behavior dry-run helper placeholder.
  The Step 8 behavior report exercises Growth Ledger emissions
  along the existing /stream → /stream-promote → /step route
  and may either promote this row to REQUIRED / OBSERVED via a
  follow-up catalog patch or leave it NOT-EXERCISED as a
  documented future surface. Mirrors I-PLEDGER-18 and
  I-COHMON-14 (end-to-end dry-run placeholders).
```

### Row-family count recap

```text
REQUIRED:        19   (I-GROW-01..19)
STRUCTURAL:       1   (I-GROW-20)
DEFERRED:         1   (I-GROW-21)
NOT-EXERCISED:    1   (I-GROW-22)
OBSERVED:         0
---------------------------------
Total new rows:  22
```

### Row-to-fixture summary

Compact view of each row's status, the fixture file that drives
its assertion, and the primary implementation file the row
asserts against. Step 6 Review Gate A can use this table as the
single approval surface.

```text
Row id        Status         Fixture file                                       Primary implementation file
---------------------------------------------------------------------------------------------------------------------
I-GROW-01     REQUIRED       growth_ledger_constructor.py                        brain/development/growth_ledger.py
I-GROW-02     REQUIRED       growth_ledger_constructor.py                        brain/development/growth_ledger.py
I-GROW-03     REQUIRED       growth_ledger_constructor.py                        brain/development/growth_ledger.py
I-GROW-04     REQUIRED       growth_ledger_event_id.py                           brain/development/growth_ledger.py
I-GROW-05     REQUIRED       growth_ledger_observe.py                            brain/development/growth_ledger.py
I-GROW-06     REQUIRED       growth_ledger_observe.py                            brain/development/growth_ledger.py
I-GROW-07     REQUIRED       growth_ledger_constructor.py                        brain/development/growth_ledger.py
I-GROW-08     REQUIRED       growth_ledger_observe.py                            brain/development/growth_ledger.py
I-GROW-09     REQUIRED       growth_ledger_observe.py                            brain/development/growth_ledger.py
I-GROW-10     REQUIRED       growth_ledger_static_audit.py                       brain/development/growth_ledger.py
I-GROW-11     REQUIRED       growth_ledger_static_audit.py                       brain/development/growth_ledger.py
I-GROW-12     REQUIRED       growth_ledger_no_runtime_coupling.py                brain/development/growth_ledger.py
I-GROW-13     REQUIRED       growth_ledger_session_integration.py                brain/ui/session.py
I-GROW-14     REQUIRED       growth_ledger_session_integration.py                brain/ui/fixtures/persistence_observe_resource_audit.py
                                                                                 brain/ui/fixtures/persistence_ops_resource_audit.py
I-GROW-15     REQUIRED       growth_ledger_session_integration.py                brain/ui/session.py
I-GROW-16     REQUIRED       growth_ledger_session_integration.py                brain/ui/session.py
I-GROW-17     REQUIRED       growth_ledger_session_integration.py                brain/ui/session.py
I-GROW-18     REQUIRED       growth_ledger_session_integration.py                brain/ui/session.py
I-GROW-19     REQUIRED       growth_ledger_static_audit.py                       brain/development/growth_ledger.py
I-GROW-20     STRUCTURAL     growth_ledger_no_runtime_coupling.py                brain/development/growth_ledger.py + brain/ui/session.py
I-GROW-21     DEFERRED       (no fixture; deferred placeholder)                  (no implementation file in v1)
I-GROW-22     NOT-EXERCISED  (no fixture; behavior-report placeholder)           (no implementation file in v1)
```

Validation route for every REQUIRED / STRUCTURAL row is the same
mandatory gate: `python3 -m brain.invariants run` plus the four
other preflight commands listed under
"Proposed Validation for Step 7". DEFERRED / NOT-EXERCISED rows
do not register in the runner; their catalog-row presence is
checked by `python3 -m tools.catalog counts`.

The row split mirrors the Phase 3.12c Pattern Ledger split
(`I-PLEDGER-01..18`: 15 REQUIRED + 1 STRUCTURAL + 1 DEFERRED +
1 NOT-EXERCISED = 18 rows over 6 fixtures) and the Coherence
Monitor split (`I-COHMON-01..14`: 11 REQUIRED + 1 STRUCTURAL +
1 DEFERRED + 1 NOT-EXERCISED = 14 rows over 6 fixtures). Growth
Ledger's REQUIRED count is higher because its session
integration is wider — three dispatcher call sites instead of
one — and each emit-shape obligation gets its own row to keep
the catalog rows narrow and testable.

## Proposed v0.23 Count Delta

**Current v0.22 counts:**

```text
REQUIRED:        240
STRUCTURAL:       85
NOT-EXERCISED:    11
DEFERRED:         14
OBSERVED:         16
```

**Delta from this plan (preferred row split):**

```text
REQUIRED:        +19
STRUCTURAL:       +1
NOT-EXERCISED:    +1
DEFERRED:         +1
OBSERVED:          0
```

**Proposed v0.23 counts:**

```text
REQUIRED:        259
STRUCTURAL:       86
NOT-EXERCISED:    12
DEFERRED:         15
OBSERVED:         16
```

**Total catalog-row count (sum of the five statuses):**

```text
v0.22 total = 240 + 85 + 11 + 14 + 16 = 366
v0.23 total = 259 + 86 + 12 + 15 + 16 = 388
delta       = +22 rows (exactly the I-GROW-01..22 row family)
```

The baseline `v0.22` numbers are repo-local evidence: they come
from `python3 -m tools.catalog counts` run on this branch at
Step 5 preflight (PASS, 240 / 85 / 11 / 14 / 16). They are not
model-supplied numbers.

**Step 7 must update both the catalog banner and
`tools/catalog.py EXPECTED_COUNTS` to these v0.23 numbers in the
same commit.** A mismatch between
`INVARIANT_CATALOG.md` banner and `EXPECTED_COUNTS` will fail
`python3 -m tools.catalog counts` and block the gate before
commit.

**If Step 6 Review Gate A amends row count or status**, recompute
the delta exactly as part of the amendment record and update
both the banner and `EXPECTED_COUNTS` to the amended numbers.
Do not split this update across commits; the
catalog-counts gate must stay green at every commit boundary in
Step 7.

## Proposed Constants

Step 7, if approved, will introduce exactly the following
module-level constants in `brain/development/growth_ledger.py`:

```python
GROWTH_LEDGER_MAX_EVENTS:     int = 256
GROWTH_LEDGER_REFERENCE_MAX:  int =   8
GROWTH_LEDGER_ID_MAX:         int =  64
GROWTH_LEDGER_PROVENANCE_MAX: int =  64
GROWTH_LEDGER_SOURCE_MAX:     int =  64
```

**Not introduced in v1:**

- `GROWTH_LEDGER_SNAPSHOT_MAX` — no `GrowthLedgerSnapshot` record
  exists (LOCK M).
- `GROWTH_LEDGER_OBSERVE_LIMIT_PER_TYPE` — no per-event-type
  caps in v1 (LOCK N).
- any per-field length constant beyond the five above — bounded
  by the `*_MAX` constants and the closed enum membership; no
  additional Fraction / float / metric scalar exists.

## Proposed Implementation Files

If Step 6 accepts the plan, **Step 7 may touch only the
following files**:

```text
NEW
  brain/development/growth_ledger.py
  brain/development/fixtures/growth_ledger_constructor.py
  brain/development/fixtures/growth_ledger_event_id.py
  brain/development/fixtures/growth_ledger_observe.py
  brain/development/fixtures/growth_ledger_static_audit.py
  brain/development/fixtures/growth_ledger_no_runtime_coupling.py
  brain/development/fixtures/growth_ledger_session_integration.py

EXTENDED
  brain/invariants.py
    - extend FIXTURE_MODULES with the seven new growth_ledger_*
      fixture entries, appended after the existing Coherence
      Monitor block ("brain.development.fixtures.coherence_monitor_no_runtime_coupling")
  brain/ui/session.py
    - import GrowthLedger
    - add "growth_ledger" to _ALLOWED_SESSION_ATTRS
    - add growth_ledger field on OperatorSession with
      default_factory=GrowthLedger
    - add isinstance(self.growth_ledger, GrowthLedger) check
      in __post_init__
    - add observe call sites at the end of the successful path
      of _dispatch_stream_append, _dispatch_stream_promote,
      and _dispatch_step (each is exactly one
      self.growth_ledger = self.growth_ledger.observe(...)
      assignment per emitted event; no other dispatcher line
      changes)
  brain/ui/fixtures/persistence_observe_resource_audit.py
    - add _PHASE_3_13_SESSION_ATTRS frozenset
    - fold into the allowed union
  brain/ui/fixtures/persistence_ops_resource_audit.py
    - same _PHASE_3_13_SESSION_ATTRS addition and union update

CATALOG / VERSION BANNER
  INVARIANT_CATALOG.md
    - v0.22 → v0.23 banner paragraph (the existing v0.21 / v0.22
      banner pattern is the template; see lines 1–7 of
      INVARIANT_CATALOG.md for the precise prose model)
    - I-GROW-01..22 rows appended to the catalog table after
      the I-COHMON family (the section header and table format
      mirror the I-PLEDGER and I-COHMON families)
  brain/_catalog_ids.py
    - regenerated via `python3 -m tools.catalog generate-ids`
  tools/catalog.py
    - EXPECTED_COUNTS dict updated to v0.23 numbers
    - "v0.22 expected counts" comment updated to
      "v0.23 expected counts" with Phase 3.13 attribution

VERSION STAMPS
  README.md
    - catalog version stamp v0.22 → v0.23
    - counts string updated to 259 / 86 / 12 / 15 / 16
  CURRENT_MISSION.md
    - "Catalog: v0.22" line updated
    - counts block updated
  CURRENT_CAMPAIGN.md
    - "Catalog: v0.22" line updated
    - counts block updated
```

**Files explicitly excluded in v1 (must NOT be touched in
Step 7):**

```text
brain/tick.py                                  (kernel tick body
                                                  is unchanged)
brain/llm/**                                   (no LLM coupling)
brain/ui/persistence.py                        (no save extension)
brain/ui/persistence_ops.py                    (no save extension)
brain/ui/persistence_observe.py                (no observe extension)
brain/ui/autosave.py                           (LOCK A: trigger
                                                  set unchanged)
brain/ui/commands.py                           (LOCK S: no UI)
brain/ui/command_line.py                       (LOCK S: no parser)
brain/ui/render.py                             (LOCK S: no render
                                                  change)
brain/ui/snapshot.py                           (LOCK S: no snapshot
                                                  change)
DB schema files                                (LOCK A: no schema
                                                  change)
SCHEMA_VERSION constants                       (LOCK A: no bump)
brain/development/pattern_ledger.py            (read-only; Growth
                                                  Ledger does not
                                                  call Pattern
                                                  Ledger)
brain/development/coherence_monitor.py         (read-only;
                                                  fixture-side
                                                  forbidden-term
                                                  import is the
                                                  only coupling)
lean_reference/**                              (engineering
                                                  hypothesis; no
                                                  Lean theorem)
scenarios/**                                   (no scenario change)
traces/**                                      (no trace change)
.claude/**                                     (no settings /
                                                  agent / skill /
                                                  command edit)
```

## Proposed Fixture Plan

Six fixture files cover I-GROW-01..20. I-GROW-21 is DEFERRED
(no fixture) and I-GROW-22 is NOT-EXERCISED (no fixture); both
are placeholders mirroring `I-PLEDGER-17/18` and
`I-COHMON-13/14`.

### 1. `brain/development/fixtures/growth_ledger_constructor.py`

**Covers:** `I-GROW-01`, `I-GROW-02`, `I-GROW-03`, `I-GROW-07`

**Assertions:**

- closed `GrowthEventType` enum membership (every name accepted,
  any other name rejected; deferred members present-or-absent
  per Step 7 decision but consistent across enum / catalog row
  text)
- closed `GrowthEventSource` enum membership (same shape)
- valid `GrowthEvent` constructs for representative payloads of
  every v1 emit-shape
- `event_id` rejection: empty, oversized
  (`len > GROWTH_LEDGER_ID_MAX`), non-printable,
  `COGITO_ID`-equal
- `references` element rejection: empty string, oversized
  (`len > GROWTH_LEDGER_ID_MAX` reused as ref length cap, or a
  separate ref-length cap if Step 7 chooses one), non-printable,
  `COGITO_ID`-equal
- `references` tuple cap: rejects `len > GROWTH_LEDGER_REFERENCE_MAX`
- `references` uniqueness: rejects duplicates within one tuple
  (LOCK G; raises before any event_id derivation)
- `tick` rejection: negative ints, non-int values
- `provenance` rejection: empty, oversized, non-printable,
  `COGITO_ID`-equal
- no silent normalization (strip / lowercase / unicode-fold)
- direct `GrowthLedger(events=(e1, e2))` construction where
  `e1.event_id == e2.event_id` rejects with `ValueError`
  (I-GROW-07)

### 2. `brain/development/fixtures/growth_ledger_event_id.py`

**Covers:** `I-GROW-04`

**Assertions:**

- identical payload → identical `event_id` across two
  constructions
- different payload → different `event_id` (probabilistic
  comparison across the v1 emit-shapes)
- prefix is always `"growth:"`; full `event_id` length is
  exactly 23
- closed input shape: `(event_type.value, tick, source.value,
  references, provenance)`; any deviation (extra positional, a
  dict, a set) is structurally impossible because the helper
  takes typed kwargs
- no nondeterministic input: the id derivation contains no
  `time.*`, `random.*`, `os.getpid`, `socket.gethostname`,
  `id(...)`, or env lookup (static AST audit reused from
  I-GROW-11)
- the same `repr()` over the closed 5-tuple is what produces
  the id (fixture exercises a known payload and asserts the
  resulting hexdigest matches the deterministic expected value)

### 3. `brain/development/fixtures/growth_ledger_observe.py`

**Covers:** `I-GROW-05`, `I-GROW-06`, `I-GROW-08`, `I-GROW-09`

**Assertions:**

- empty `GrowthLedger().observe(...)` returns a one-event ledger
- old ledger's `events` tuple is unchanged after `observe(...)`
  (`id(old.events) != id(new.events)`; tuple equality preserved
  for the prefix)
- duplicate-event idempotency (LOCK F): a second
  `observe(...)` with the same payload returns `self`
  unchanged (`id(...)`-equality, not just tuple equality)
- max-cap refusal (LOCK H): at
  `len(events) == GROWTH_LEDGER_MAX_EVENTS`, any new
  `observe(...)` returns `self`; the events tuple is unchanged;
  no Python exception bubbles out
- `counts_by_type()` is deterministic over the closed
  `GrowthEventType` enum (same ledger → same tuple)
- `counts_by_type()` includes every closed enum value,
  including deferred members (`count == 0` for any never-emitted
  type)
- no scalar field appears in `GrowthEvent`, `GrowthLedger`, or
  any helper return type (banned-name regex audit)

### 4. `brain/development/fixtures/growth_ledger_static_audit.py`

**Covers:** `I-GROW-10`, `I-GROW-11`, `I-GROW-19`

**Assertions:**

- allowed imports only (LOCK O):
  `dataclasses`, `enum`, `hashlib`, `typing`,
  `brain.tlica.profile` (with `COGITO_ID` as the only allowed
  binding)
- forbidden imports absent (LOCK P): every name in
  `os / subprocess / socket / urllib / http / requests /
  pathlib / tempfile / shutil / curses / sqlite3 / brain.llm /
  brain.tick / brain.ui / brain.development.pattern_ledger /
  brain.development.coherence_monitor / threading / asyncio /
  atexit / signal / importlib / math / fractions`
- forbidden call expressions absent: `eval`, `exec`, `compile`,
  `__import__`, `importlib.import_module`, `atexit.register`,
  `signal.signal`, `signal.setitimer`, `threading.*`,
  `asyncio.*`, `open`, `tick`, `save_session`, `load_session`,
  `db_backup`, `db_verify`,
  `maybe_autosave_after_mutation`, `build_coherence_report`,
  `build_full_coherence_report`, `PatternLedger.observe`
- module-level statements limited to: imports, constants,
  function defs, class defs, and a module docstring (Pattern
  Ledger / Coherence Monitor static-audit precedent)
- non-claim audit (LOCK Q / LOCK R): the fixture imports
  `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
  (Option A) and asserts the literal source of
  `brain/development/growth_ledger.py` contains none of those
  terms (case-insensitive substring scan, matching the
  Coherence Monitor I-COHMON-11 discipline)
- non-claim audit over generated bounded printable strings: the
  fixture constructs representative `GrowthEvent` /
  `GrowthLedger` / `counts_by_type()` outputs and scans them
  with the same forbidden-term set

### 5. `brain/development/fixtures/growth_ledger_no_runtime_coupling.py`

**Covers:** `I-GROW-12`, `I-GROW-20`

**Assertions:**

- no unsafe resources stored: for every field of every
  `GrowthEvent` and `GrowthLedger` constructed in the fixture,
  the value is not a callable, file handle, socket, subprocess
  handle, `pathlib.Path`, `sqlite3.Connection` / `Cursor`,
  curses object, or LLM client-shaped object (reuses the
  `_value_looks_unsafe` discipline from Coherence Monitor)
- no `eval_consistency`-bearing object is stored or accepted
  by any constructor or by `observe(...)`
- runtime no-coupling: a constructed `OperatorSession` with a
  representative pre-state is passed through a single
  `observe(...)` call; assertions verify that `BrainState`,
  `MSI`, `PtCns`, `ContentRegistry`, `latest_tick`,
  `tick_counter`, `event_queue`, `stream_history`,
  `stream_candidates`, `stream_chunk_serial`, the
  `PatternLedger`, the `CoherenceReport` records (if a report
  is also built), the persistence config, and the autosave
  config are **identity-stable** (same Python `id(...)`) across
  the observe call
- dependency-direction static check: the fixture re-asserts
  the I-GROW-10 / I-GROW-11 import surface and additionally
  asserts that `brain.development.growth_ledger`'s module
  `__dict__` does not contain a name binding for
  `OperatorSession`, `tick`, `PatternLedger`, or
  `CoherenceReport`

### 6. `brain/development/fixtures/growth_ledger_session_integration.py`

**Covers:** `I-GROW-13`, `I-GROW-14`, `I-GROW-15`, `I-GROW-16`,
`I-GROW-17`, `I-GROW-18`

**Assertions:**

- `OperatorSession.growth_ledger` exists, default is an empty
  `GrowthLedger`, and `isinstance(self.growth_ledger,
  GrowthLedger)` is type-checked in `__post_init__`
- `_ALLOWED_SESSION_ATTRS` contains `"growth_ledger"`
- the persistence resource-audit fixtures'
  `_PHASE_3_13_SESSION_ATTRS` includes `"growth_ledger"` and
  the `allowed` union compared against
  `_ALLOWED_SESSION_ATTRS` matches `_ALLOWED_SESSION_ATTRS`
  exactly (the fixture imports the tier constants and the
  `_ALLOWED` set, then asserts identity)
- a successful `/stream <text>` append records
  `STREAM_CHUNK_ACCEPTED` with `references=(chunk_id,)` and
  `provenance` matching the locked prefix; the new ledger has
  exactly one more event than the prior ledger
- when the same append causes Pattern Ledger to create a new
  entry, an additional `PATTERN_ENTRY_CREATED` event records;
  when it strictly increases an existing entry's recurrence,
  `PATTERN_ENTRY_UPDATED` records instead — never both for the
  same append, never either for a `/stream` that does not
  produce a delta
- a successful `/stream-promote` records `STREAM_PROMOTION_QUEUED`
  with `references=(candidate_id,)` and no other event
- a successful `/step` records `TICK_SUCCEEDED` with
  `references=(f"tick-{record.tick_index}",)`, plus one
  `PROFILE_DOMAIN_ADDED` event per `content_id` in
  `post.profile.domain - pre.profile.domain`, plus one
  `MSI_MEMBER_ADDED` event per `content_id` in
  `post.msi.contents - pre.msi.contents`. No deletion / removal
  events emit.
- failed parse, dispatch, or tick paths emit **nothing**:
  `LocalCommandError`, the existing negative typed signal from
  the Phase 3.10c contract, and a `tick()` exception each
  leave the ledger identity-stable
- read-only verbs emit **nothing**: `/state`, `/tick` (the
  read-only verb, not `/step`), `/stream-summary`,
  `/stream-candidates`, `/session-status`, `/db-status`,
  `/db-summary`, `/profile-summary`, `/stream-db-summary`,
  `/db-diff`, `/db-verify`, `/db-backup`, `/autosave-status`
- save / load / coherence-report-built paths emit **nothing**
  (LOCK J deferred trio; I-GROW-18): a successful
  `/save-session`, a successful `/load-session`, and a
  successful `build_full_coherence_report(...)` each leave the
  Growth Ledger free of `SESSION_SAVED` / `SESSION_LOADED` /
  `COHERENCE_REPORT_BUILT` events
- spam: repeating the exact same `/stream alpha` 257 times
  does NOT inflate the ledger past `GROWTH_LEDGER_MAX_EVENTS`;
  the same `event_id` re-observation is a no-op (LOCK F /
  LOCK H combined check)

### 7. (no fixture) `I-GROW-21` DEFERRED

The `/growth-ledger` UI command remains deferred. No fixture
file is created. The catalog row text documents the deferral
and references the future review gate that would promote it.

### 8. (no fixture) `I-GROW-22` NOT-EXERCISED

The end-to-end Growth Ledger behavior dry-run remains
NOT-EXERCISED in v1. No fixture file is created. The Step 8
behavior report is the campaign-internal exercise; promoting
the row to REQUIRED / OBSERVED is a future-campaign decision.

## Proposed Implementation Sequence for Step 7

If Step 6 Review Gate A accepts this plan, **Step 7 must
proceed in the following order** to keep `python3 -m
brain.invariants run` green at every commit boundary.

```text
 1. Add brain/development/growth_ledger.py
    - module docstring (non-claim audit clean)
    - constants (LOCK I)
    - GrowthEventType / GrowthEventSource closed enums
    - GrowthEvent / GrowthLedger frozen / slotted dataclasses
    - observe(...) and counts_by_type() methods
    - no session integration yet
 2. Add growth_ledger_constructor / event_id / observe fixtures
    - WITHOUT registering them in brain/invariants.py yet
    - OR commit them together with the FIXTURE_MODULES extension;
      a partial registration would fail the runner
 3. Add growth_ledger_static_audit / no_runtime_coupling fixtures
    - same rule: register all-or-none with brain/invariants.py
 4. Add growth_ledger_session_integration fixture
    - this fixture exercises a constructed OperatorSession;
      it is expected to FAIL until step 5 below patches
      session.py. Therefore session.py must be patched in the
      SAME commit as the session-integration fixture
      registration, OR the fixture must be added unregistered
      and registered in the same commit that lands the session
      patch.
 5. Patch brain/ui/session.py:
    - add: from brain.development.growth_ledger import GrowthLedger
    - add "growth_ledger" to _ALLOWED_SESSION_ATTRS
    - add the growth_ledger field with default_factory
    - add isinstance check in __post_init__
    - add observe call sites at the end of the successful path
      of _dispatch_stream_append, _dispatch_stream_promote,
      _dispatch_step (exactly one assignment per emitted event)
 6. Patch brain/ui/fixtures/persistence_observe_resource_audit.py
    and brain/ui/fixtures/persistence_ops_resource_audit.py:
    - add _PHASE_3_13_SESSION_ATTRS frozenset
    - fold into the allowed union
 7. Wire the seven new fixtures into brain/invariants.py
    FIXTURE_MODULES list (append after the
    coherence_monitor_no_runtime_coupling entry).
 8. Patch INVARIANT_CATALOG.md:
    - update the top banner from v0.22 to v0.23
    - prepend a v0.22 → v0.23 banner paragraph with the
      I-GROW-* family description (same prose model as the
      existing v0.21 → v0.22 Coherence Monitor banner and the
      v0.20 → v0.21 Pattern Ledger banner)
    - append the I-GROW-01..22 rows in a new section after the
      I-COHMON family
 9. Regenerate brain/_catalog_ids.py:
    python3 -m tools.catalog generate-ids
10. Update tools/catalog.py EXPECTED_COUNTS to v0.23 numbers
    and refresh the "v0.22 expected counts" comment to v0.23
    Phase 3.13 attribution.
11. Update README.md catalog stamp + counts.
12. Update CURRENT_MISSION.md catalog baseline + counts.
13. Update CURRENT_CAMPAIGN.md catalog baseline + counts.
14. Run the full validation gate:
      python3 -m tools.catalog counts
      python3 -m tools.citations verify
      python3 -m tools.import_audit
      python3 -m brain.invariants run
      bash tools/check_all.sh
    All must PASS before commit.
15. Commit and push.
```

**Commit-boundary rule.** The runner requires
`FIXTURE_MODULES`, the catalog, and the implementation to agree
at every commit. Steps 1–7 may be condensed into a single
"implementation + audit-tier + registration" commit, or split
into a fixture-first commit (1–4) followed by a
session-integration commit (5–7), as long as
`python3 -m brain.invariants run` is green at every commit
that lands on the campaign branch. Steps 8–13 must land in the
same commit as the matching code so the catalog banner and
runner row set agree at every commit boundary.

## Proposed Validation for Step 7

**Mandatory before every commit:**

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

All five must PASS. The existing invariant runner is used; no
new runner is invented.

**Optional during development:**

- direct fixture imports for fast iteration
  (`python3 -m brain.development.fixtures.growth_ledger_constructor`)
- direct module import + ad-hoc construction smoke
  (`python3 -c "from brain.development.growth_ledger import
  GrowthLedger; print(GrowthLedger())"`)
- the existing `brain-current-mission`-style preflight
  combination

**Forbidden during Step 7:**

- bypassing the `brain.invariants run` runner
- bypassing `tools/check_all.sh`
- bypassing the `tools.catalog counts` banner-vs-EXPECTED_COUNTS
  check
- running real LLM-backed scenario commands (the offline
  default stays; the only sanctioned external bridge is the
  Stage A `/ask-chatgpt` advisory channel, used only at the
  high-leverage Phase 3.13 step boundaries)

## Risks and Mitigations

```text
Risk                                  Mitigation
-----------------------------------   -------------------------------
session surface drift                 LOCK B + I-GROW-13 lock the
                                        exact field; LOCK C +
                                        I-GROW-14 lock the audit-tier
                                        update; both are tied to
                                        explicit catalog rows.
hidden persistence                    LOCK A + I-GROW-18 + fixture
                                        assertions on save / load /
                                        coherence-report paths;
                                        FIXTURE_MODULES file lists
                                        no growth_ledger persistence
                                        fixture.
event inflation / spam                LOCK F + LOCK H + I-GROW-06 /
                                        I-GROW-08 + the spam-test
                                        assertion in the session
                                        integration fixture
                                        (257 repeats does not
                                        exceed the cap).
event ID canonicalization drift       LOCK E + I-GROW-04 lock the
                                        closed input shape and the
                                        deterministic value; the
                                        fixture asserts a known
                                        payload yields the expected
                                        hexdigest.
profile / MSI semantic overclaiming   LOCK K + LOCK R + LOCK Q +
                                        I-GROW-17 + I-GROW-19;
                                        wording requirement is stated
                                        in the module docstring,
                                        the catalog row text, and
                                        scanned by the non-claim
                                        audit.
status-string parsing                 LOCK D + I-GROW-11 forbid the
                                        relevant calls in the static
                                        AST audit; observe call
                                        sites use only typed return
                                        values (Phase 3.10c
                                        I-AUTOSAVE-14 discipline).
Growth Ledger becoming a score        LOCK M + LOCK R + I-GROW-09 +
                                        the banned-name regex audit
                                        in the observe fixture.
SelfModel creep                       Campaign-level non-goal +
                                        LOCK A (session-local only)
                                        + LOCK Q non-claim audit +
                                        explicit "no SelfModel"
                                        statement in this plan and
                                        in every step report.
UI creep                              LOCK S + I-GROW-21 DEFERRED;
                                        no UI files appear in the
                                        Proposed Implementation
                                        Files list and Step 7 is
                                        forbidden from touching
                                        them.
import / coupling creep               LOCK O + LOCK P + I-GROW-10 +
                                        I-GROW-11 + I-GROW-20;
                                        dependency direction is
                                        verified at static-AST level
                                        and at runtime via the
                                        no-coupling fixture.
catalog count mismatch                Step 7 commit-boundary rule:
                                        EXPECTED_COUNTS and the
                                        banner update land in the
                                        same commit; the catalog
                                        counts gate enforces it.
fixture sprawl                        Six fixture files cover 20
                                        rows; the Pattern Ledger
                                        (6 fixtures → 16 active
                                        rows) and Coherence Monitor
                                        (6 fixtures → 12 active
                                        rows) precedents established
                                        the same density.
```

## Review Gate A Decision Request

**Step 5 stops here.** No source under `brain/**`, `tools/**`,
`.claude/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`lean_reference/**`, `scenarios/**`, or `traces/**` is
modified by this Step 5 plan, and no Growth Ledger code is
written by it.

Step 6 Review Gate A must explicitly choose one option, naming
the option in the operator's response so the next step can
proceed deterministically:

```text
[ ] ACCEPT PLAN AS WRITTEN
[ ] ACCEPT WITH AMENDMENTS
       Amendment list:
       - <row id / fixture / file / status / count change>
       - <...>
[ ] REJECT / REVISE
       Return to Step 5 with explicit revisions; no
       implementation until a revised plan re-enters the
       review gate.
```

**No implementation is authorized before a Step 6 acceptance.**
If the operator chooses ACCEPT WITH AMENDMENTS, the amendment
list is recorded in the Step 6 gate response and the Step 7
implementation must match the amended plan exactly. If the
operator chooses REJECT / REVISE, Step 5 is re-entered with
revisions and no Growth Ledger code lands.

### Review Gate A negative-boundary checklist

For an ACCEPT decision (with or without amendments), Step 6 must
explicitly confirm each negative-boundary item below. These
restate the campaign-level non-goals at the gate so a future
audit can verify Step 6 saw and approved each one. Items
match the locks the plan inherits from the Step 4 corrigenda.

```text
[ ] no persistence change (LOCK A; no DB schema; no
    SCHEMA_VERSION bump; no save / load extension; no autosave
    trigger-set extension)
[ ] no UI (LOCK S; no OperatorCommand / parser / active_view /
    render / snapshot / commands / command_line edit;
    I-GROW-21 remains DEFERRED)
[ ] no SelfModel (campaign-wide; SelfModel reconsidered only by
    a separate future campaign)
[ ] no aggregate growth / I-ness / awareness / capability /
    maturity / intelligence / coherence-quality score
    (LOCK M / LOCK R; I-GROW-09 banned-name regex audit)
[ ] no consciousness / sentience / subjective / semantic /
    truth-adjudication / agency / intent-will-desire /
    self-modification / personhood claim anywhere on the
    Growth Ledger surface (LOCK Q / LOCK R; I-GROW-19
    non-claim audit)
[ ] no hidden persistence path through session serialization,
    profile export, traces, coherence reports, or fixture
    snapshots (LOCK A; campaign-level non-integration list;
    growth_ledger_session_integration.py asserts /save-session,
    /load-session, and build_full_coherence_report emit
    nothing)
[ ] no hidden LLM call, network call, filesystem mutation,
    subprocess spawn, or shell command from the Growth Ledger
    module surface (LOCK O / LOCK P; I-GROW-10 / I-GROW-11)
[ ] no Step 5 code change (this plan touched only
    docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CATALOG_PATCH_PLAN.md;
    no source under brain/**, tools/**, .claude/**,
    INVARIANT_CATALOG.md, README.md, CURRENT_MISSION.md,
    CURRENT_CAMPAIGN.md, lean_reference/**, scenarios/**, or
    traces/** was modified)
```

If any item cannot be confirmed, the gate result is REJECT /
REVISE and Step 5 is re-entered.

## ChatGPT/Codex Consultation

Before finalizing this catalog patch plan, a single Stage A
advisory review call was run against the locked plan above.

The actual wrapper command was:

```text
python3 tools/claude_helpers/codex_chatgpt_subagent.py \
  --mode review --model gpt-5.5 --effort high \
  --timeout 300 \
  --prompt-file /tmp/toyi_chatgpt_step5_question.md \
  > /tmp/toyi_chatgpt_step5_answer.md
```

```text
ChatGPT/Codex consultation:
- used:           yes
- mode:           review
- model:          gpt-5.5
- effort:         high
- wrapper command: python3 tools/claude_helpers/codex_chatgpt_subagent.py
                     --mode review --model gpt-5.5 --effort high
                     --timeout 300
                     --prompt-file /tmp/toyi_chatgpt_step5_question.md
- question file:   /tmp/toyi_chatgpt_step5_question.md
- answer file:     /tmp/toyi_chatgpt_step5_answer.md
- wrapper status:  exit 0; error_class null; codex_returncode 0;
                   duration_ms 48197; stdout_bytes 5059;
                   stderr_bytes 7890; truncated false; codex-cli
                   0.130.0; auth "Logged in using ChatGPT". Audit
                   JSONL appended at .claude/codex_bridge_logs/
                   (gitignored).
- accepted advice:
   - Add a compact "row id / status / fixture file / primary
     implementation file" summary table so Step 6 has a single
     approval surface (applied as the "Row-to-fixture summary"
     subsection inside the Proposed Row Family section).
   - State the total-row delta explicitly with labels and the
     v0.22 → v0.23 sum (applied as "Total catalog-row count"
     block: 240 + 85 + 11 + 14 + 16 = 366; 259 + 86 + 12 + 15 + 16
     = 388; +22 = the I-GROW family).
   - State explicitly that the baseline counts are repo-local
     evidence from `python3 -m tools.catalog counts` at Step 5
     preflight, not model-supplied numbers (applied at the end
     of the Total catalog-row count block).
   - Add a Review Gate A negative-boundary checklist that names
     each non-goal item the gate must confirm: no persistence
     change, no UI, no SelfModel, no aggregate score, no
     consciousness / sentience / semantic / truth / agency /
     self-modification claim, no hidden persistence path, no
     hidden LLM / network / filesystem / subprocess call, no
     Step 5 code change (applied as the
     "Review Gate A negative-boundary checklist" subsection).
- rejected advice:
   - "OBSERVED 0 is acceptable only if no row is intended as
     inspectable-but-non-gating evidence." Rejected as a
     blocker: the Phase 3.12c Pattern Ledger
     (I-PLEDGER-01..18) and Coherence Monitor
     (I-COHMON-01..14) campaigns both shipped with OBSERVED 0
     in their new row families using exactly this row-shape
     pattern. OBSERVED rows are added when a row's *evidence*
     is repo-local but its *gate semantics* are not a hard
     pass/fail; Growth Ledger v1 has no such row. Step 8
     behavior report may promote I-GROW-22 into OBSERVED via a
     follow-up patch if behavior evidence merits it; in v1 the
     NOT-EXERCISED placeholder is the precedent-correct shape.
   - "`_PHASE_3_13_SESSION_ATTRS` tier visibility is
     ambiguous." Rejected: LOCK C in the Step 4 corrigenda and
     I-GROW-14 in this plan already specify the visibility
     exactly. The tier is fixture-visible (declared in both
     persistence_observe_resource_audit.py and
     persistence_ops_resource_audit.py); runner-visible only
     transitively through the existing I-OBSERVE-08 /
     I-OPSHARDEN-13 fixture runs that compare the tier union
     against _ALLOWED_SESSION_ATTRS; catalog-visible through
     the I-GROW-14 row text in the v0.23 banner. No mechanism
     is expanded.
   - "Validation should add `python3 -m tools.catalog lint`
     and `python3 -m tools.invariant_runner --list`." Rejected:
     `tools.catalog` exposes `counts` / `list` / `show` /
     `generate-ids` subcommands (no `lint` subcommand exists in
     the current repo), and the invariant runner is invoked as
     `python3 -m brain.invariants run` (no
     `tools.invariant_runner` module exists). The plan keeps
     the existing five-command preflight gate; introducing
     model-suggested commands that don't exist in the repo
     would silently no-op or fail.
- reason:          Three substantive amendments adopted as
                   inline edits (row-to-fixture summary table,
                   labeled total-row delta with repo-local
                   provenance statement, Review Gate A
                   negative-boundary checklist). Rejected
                   advice was either contradicted by repo-local
                   precedent (OBSERVED 0; Pattern Ledger /
                   Coherence Monitor shape), already specified
                   by existing lock / row (audit-tier
                   visibility), or referenced commands that
                   do not exist in this repo (catalog lint /
                   invariant_runner --list). Minor disagreement,
                   medium confidence verdict is consistent with
                   the locked plan.
```

Treat the bridge output as advisory. Repo-local files, gates,
and invariants override ChatGPT advice. If ChatGPT advice
conflicts with a repo-local constraint, the conflict is reported
and the repo wins.

## Next Artifact

Step 6 Review Gate A.

No new document is created in Step 6; the gate is a single
operator response naming one of the three options in the
Review Gate A Decision Request section above.

If Step 6 accepts the plan (with or without amendments),
Step 7 produces the code changes in `brain/**`, `tools/**`, and
the catalog version banners listed above. **Until Step 6
accepts, no source change under those paths is permitted.**

## Validation

Re-ran after writing this catalog patch plan (no source under
`brain/**`, `tools/**`, `.claude/**`, `lean_reference/**`,
`scenarios/**`, or `traces/**` was touched; no edit to
`INVARIANT_CATALOG.md`, `README.md`, `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, `PHASE3_13_GROWTH_LEDGER_ROADMAP.md`,
the Step 2 synthesis, the Step 3 kickoff, or the Step 4
corrigenda; only this new documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS (240/85/11/14/16) |
| `python3 -m tools.citations verify` | PASS (100 citations resolved) |
| `python3 -m tools.import_audit` | PASS (I-PCE-05 clean) |
| `python3 -m brain.invariants run` | PASS (333 rows; 0 gate failures) |
| `bash tools/check_all.sh` | PASS (All checks passed.) |
