# PHASE3_12_COHERENCE_MONITOR_SYNTHESIS.md

## Purpose

Synthesize the Coherence Monitor concept that follows Phase 3.12c
Step 11 (Pattern Ledger Option A implementation). This is a planning
artifact only; it does not edit `brain/**`, `tools/**`,
`INVARIANT_CATALOG.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**`, and it does not change runtime behavior.

Phase 3.11 verified that ToyI launches, runs the operator route, and
persists / autosaves / reports DB state without correctness or
safety findings. Phase 3.12a/b observed that the existing
`/stream` → `/stream-promote` → `/step` path is coherent and that
bounded growth through `tick()` works (`PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md`).
Phase 3.12c Step 11 added a bounded session-local
:class:`PatternLedger` so that recurrence evidence is now ledgered
through a deterministic, copy-on-write, exact-`Fraction`-confidence
substrate (`brain/development/pattern_ledger.py`).

The Coherence Monitor measures whether ToyI's current
runtime/developmental state remains **coherent** after Pattern
Ledger integration: whether the operator-visible kernel state, the
operator session state, the stream substrate, the Pattern Ledger,
the persistence and autosave configuration / status, and the
non-claim discipline all remain mutually consistent at a single
point in time.

The Coherence Monitor is a **diagnostic** layer, not a cognitive
layer. It does **not** claim consciousness, sentience, subjective
experience, semantic understanding, truth adjudication, or agency,
and it does **not** introduce any aggregate "I-ness" / awareness /
quality scalar. It produces bounded printable evidence about
factual structural agreement among substrates that already exist.

## Baseline

```text
Catalog version:                  v0.21
Counts:
  REQUIRED:                       229
  STRUCTURAL:                      84
  NOT-EXERCISED:                   10
  DEFERRED:                        13
  OBSERVED:                        16
Branch:                           campaign/phase3-12-coherent-i-loop-observatory
Phase 3.11:                       complete; PR #10 merged at 98b55ab
Phase 3.12 steps complete (in commit order on this branch):
  Step 1  566b109  coherent i-loop mission sync
  Step 2  631ae5a  coherent i-loop synthesis
  Step 3  c395989  coherent i-loop kickoff
  Step 4  10a93ee  coherent i-loop matrix
  Step 5  (review gate A — passed implicitly by Step 6 execution)
  Step 6  c65d37b  coherent i-loop observatory report
  Step 7  013585e  pattern ledger synthesis
  Step 8  7839f7d  pattern ledger kickoff + corrigenda
  Step 9  ffbe4d9  pattern ledger catalog patch plan
  Step 10 (Review Gate B — ACCEPT PLAN AS WRITTEN)
  Step 11 05e214c  implement pattern ledger option A
Step 11 deviation note:
  The Step 11 implementation added a Phase 3.12c attribute-surface
  tier to two existing resource-audit fixtures
  (brain/ui/fixtures/persistence_observe_resource_audit.py and
  brain/ui/fixtures/persistence_ops_resource_audit.py) so the
  catalog-authorized OperatorSession.pattern_ledger field would
  not register as drift. The operator reviewed this deviation and
  ACCEPTED IT AS JUSTIFIED. Coherence Monitor design must respect
  that the I-OBSERVE-08 / I-OPSHARDEN-13 audit tiers are the
  canonical place to record new authorized session attributes,
  and that I-PLEDGER-16 owns the positive shape audit of
  pattern_ledger.
Step 12 stop condition:
  Step 13 Review Gate C (no implementation in this step).
Preflight (verified at the start of Step 12):
  python3 -m tools.catalog counts     PASS  (229/84/10/13/16)
  python3 -m tools.citations verify   PASS  (100 citations resolved)
  python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
  python3 -m brain.invariants run     PASS  (321 rows; 0 gate failures)
  bash tools/check_all.sh             PASS  (All checks passed.)
```

## Problem Being Solved

The current Phase 3.12 substrate has:

- **Kernel state.** `BrainState` (`profile`, `msi`, `ptcns`,
  `registry`) and `latest_tick` / `tick_counter` on
  `OperatorSession`.
- **Operator session state.** `OperatorSession` with active view,
  status/error text, event queue, allowed-attrs surface, and the
  `_assert_no_unsafe_resources` runtime self-audit (I-UI-10).
- **Stream state.** `TextStreamHistory`, `stream_candidates`,
  `stream_chunk_serial`, the Phase 3.7 substrate, and the Phase
  3.8 dispatch surface.
- **Pattern Ledger state.** `OperatorSession.pattern_ledger`, a
  bounded copy-on-write :class:`PatternLedger` (Step 11) with
  deterministic ids, exact-`Fraction` confidence, evidence caps
  and the LOCK O Option A non-persistence policy.
- **Persistence configuration / status.** Optional
  `SessionStoreConfig`, `/save-session` / `/load-session`, the
  Phase 3.10a/b operational hardening and observability surfaces
  (`/session-status`, `/db-status`, `/db-verify`, `/db-summary`,
  `/profile-summary`, `/stream-db-summary`, `/db-diff`,
  `/db-backup`).
- **Autosave configuration / status.** Optional `AutosaveConfig`
  and `last_autosave_status` on `OperatorSession`,
  `/autosave-status` / `/autosave-enable` / `/autosave-disable`,
  and the post-dispatch `_maybe_autosave_after_dispatch` trigger.

The Step 6 observatory found that each surface, taken
individually, is coherent. The Step 11 implementation added a
fifth substrate (the Pattern Ledger) without coupling to the
kernel runtime — but it added it as one more bounded session
field that an operator must inspect in isolation. From the
operator's typed-route perspective:

```text
There is no single bounded read-only report that says whether
the kernel state, the session state, the stream state, the
Pattern Ledger, the persistence config / status, and the
autosave config / status remain mutually coherent at a given
moment.
```

Today an operator answers "is the system coherent?" by issuing
many separate commands (`/state`, `/tick`, `/session-status`,
`/db-status`, `/db-verify`, `/db-summary`, `/profile-summary`,
`/stream-db-summary`, `/db-diff`, `/autosave-status`) and
cross-checking the bounded printable outputs by eye. The
operator gets the truth but not a single bounded summary
of whether the truths agree.

The Coherence Monitor closes that summary gap **without**
adding a new cognitive layer, a new runtime control surface, or
any new claim about ToyI's interior state.

## Coherence Monitor Definition

**Coherence Monitor** is a bounded read-only
developmental/operator diagnostic that summarizes, in a single
bounded printable report, whether live ToyI state satisfies a
finite set of coherence checks across:

```text
kernel state              (BrainState: profile, MSI, PtCns, registry,
                           latest_tick, tick_counter)
operator session state    (OperatorSession fields, view, status,
                           event queue, resource audit)
stream state              (TextStreamHistory, StreamPromotionCandidate
                           records, stream_chunk_serial, bounds)
Pattern Ledger state      (PatternLedger entries, bounds, deterministic
                           IDs, confidence formula, session-locality)
persistence config/status (SessionStoreConfig, save / load fail-closed
                           contracts; the monitor reports what is
                           configured, never opens the DB by default)
autosave config/status    (AutosaveConfig, last_autosave_status,
                           outcome-detection contract)
known non-claims          (no consciousness / sentience / subjective
                           experience / semantic / truth / agency
                           assertions appear in fields or output)
```

It is a **diagnostic layer**, not a **cognitive layer**:

- It reads existing records (`BrainState`, `OperatorSession`,
  `TextStreamHistory`, `PatternLedger`, `AutosaveConfig`,
  `SessionStoreConfig`) and computes pass/warn/fail/not-applicable
  judgments about structural agreement.
- It does **not** evaluate `PtCns`, does **not** call `tick()`,
  does **not** call any LLM client, does **not** mutate any
  kernel container, does **not** open the session DB by default,
  and does **not** perform any I/O / network / shell / file
  operation.
- It does **not** introduce a `consciousness_score`,
  `awareness_score`, or any aggregate scalar that purports to
  summarize subjective experience or "I-ness".
- It is **not** a control surface: it never schedules ticks,
  never enqueues percepts, never promotes candidates, never
  saves / loads / backs up the session, and never alters
  autosave configuration.

The Coherence Monitor is to the operator's bounded inspection
surfaces what the Pattern Ledger is to `StreamPattern`: an
aggregating bounded read-only collection that consumes existing
records, computes a deterministic summary, and exposes a small
typed snapshot that downstream design layers (Growth Ledger,
SelfModel) can reference without re-deriving the underlying
agreement.

## Proposed Snapshot Shape

Pseudocode — not implementation. Field names, defaults, and
bounds are illustrative and may be refined in the catalog patch
plan.

```python
class CoherenceCheckStatus(Enum):
    PASS           = "pass"
    WARN           = "warn"
    FAIL           = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class CoherenceCheck:
    check_id:   str                       # e.g. "kernel.cogito_in_profile"
    status:     CoherenceCheckStatus
    summary:    str                       # bounded printable, <= MAX_SUMMARY_LEN
    detail:     str                       # bounded printable, <= MAX_DETAIL_LEN
    source:     str                       # one of CHECK_SOURCES (closed enum)


@dataclass(frozen=True, slots=True)
class CoherenceSnapshot:
    snapshot_id:                 str
    tick_counter:                int
    profile_domain_size:         int
    msi_size:                    int
    registry_size:               int
    stream_chunk_count:          int
    stream_candidate_count:      int
    pattern_ledger_entry_count:  int
    autosave_mode:               str       # bounded printable, AutosaveMode.value or ""
    session_db_configured:       bool
    checks:                      tuple[CoherenceCheck, ...]


@dataclass(frozen=True, slots=True)
class CoherenceReport:
    snapshot:          CoherenceSnapshot
    overall_status:    CoherenceCheckStatus
    counts_by_status:  tuple[tuple[str, int], ...]
                       # e.g. (("pass", 12), ("warn", 1), ("fail", 0),
                       #       ("not_applicable", 2))
    summary_text:      str                  # bounded printable, deterministic
```

Constraints (constructor-enforced):

- `snapshot_id`, `check_id`, `summary`, `detail`, and `source`
  are bounded printable strings; none equals `COGITO_ID`.
- `tick_counter`, `profile_domain_size`, `msi_size`,
  `registry_size`, `stream_chunk_count`,
  `stream_candidate_count`, and `pattern_ledger_entry_count` are
  non-negative ints.
- `autosave_mode` is either `""` (no autosave configured) or one
  of the `AutosaveMode` enum values rendered as a string; the
  monitor never invents a new mode.
- `session_db_configured` is `bool`.
- `checks` is a `tuple[CoherenceCheck, ...]` whose length is
  bounded by a future `COHERENCE_MAX_CHECKS` constant.
- `counts_by_status` is a deterministic ordered tuple of
  `(status_value, count)` pairs over the closed
  `CoherenceCheckStatus` enum.
- `overall_status` is deterministic over `checks` per the
  aggregation rule below.
- All records are frozen / slotted; no field is a callable, file
  handle, socket, subprocess handle, `pathlib.Path`,
  `sqlite3.Connection` / `Cursor`, curses object, or LLM client.

Aggregation rule (deterministic, no scalars):

```text
overall_status =
    FAIL          if any check.status == FAIL
    else WARN     if any check.status == WARN
    else PASS     if at least one check.status == PASS
    else NOT_APPLICABLE
```

`NOT_APPLICABLE` never creates a false PASS or FAIL: a report
whose every check is `NOT_APPLICABLE` reports `overall_status =
NOT_APPLICABLE`, not `PASS`.

## Proposed Checks

The Coherence Monitor's first implementation should ship a finite
closed list of checks organized into the families below. The
exact `check_id` strings, `source` values, and `summary` /
`detail` templates are catalog-patch-plan concerns; this section
fixes the scope.

### Kernel coherence

```text
kernel.cogito_in_profile
  COGITO_ID is a member of BrainState.profile.domain.

kernel.cogito_in_msi
  COGITO_ID is a member of BrainState.msi.contents.

kernel.profile_values_bounded
  Every value of BrainState.profile.values is a Fraction in [0, 1].

kernel.ptcns_total_over_profile_domain
  BrainState.ptcns.eval_map's key set is exactly
  BrainState.profile.domain (the PtCns total-function discipline
  asserted by the existing I-PTC-* row family).

kernel.msi_subset_profile_domain
  BrainState.msi.contents is a subset of BrainState.profile.domain.

kernel.latest_tick_index_agrees
  If session.latest_tick is not None, its tick_index equals
  session.tick_counter; if session.latest_tick is None, this check
  is NOT_APPLICABLE.
```

### Operator session coherence

```text
session.no_unsafe_resources
  Re-runs the existing _assert_no_unsafe_resources audit (I-UI-10)
  as a read-only check; any callable / eval_consistency /
  file-handle / socket / subprocess-handle field in a session slot
  fails the row.

session.event_queue_bounded
  len(session.event_queue) <= session.event_queue.limit and
  session.event_queue.limit > 0.

session.active_view_legal
  session.active_view is in the closed ACTIVE_VIEWS set declared by
  brain/ui/snapshot.py.

session.status_error_bounded
  session.status_message and session.error_message are bounded
  printable strings (length <= MAX_STATUS_TEXT_LEN) — mirrors
  I-UI-13.
```

### Stream coherence

```text
stream.history_bounded
  len(session.stream_history.chunks) <= STREAM_HISTORY_MAX_CHUNKS.

stream.candidates_bounded
  len(session.stream_candidates) <= STREAM_PROMOTION_MAX.

stream.chunk_serial_consistent
  session.stream_chunk_serial >= len(session.stream_history.chunks)
  and stream_chunk_serial >= max(chunk_id-numeric-suffix observed)
  where chunk ids follow the deterministic 'strm-chunk-N' pattern.

stream.no_cogito_in_chunks
  No chunk in stream_history.chunks has chunk_id == COGITO_ID,
  text == COGITO_ID, or provenance == COGITO_ID; no candidate has
  candidate_id == COGITO_ID or target_content_id == COGITO_ID.
```

### Pattern Ledger coherence

```text
pledger.entries_bounded
  len(session.pattern_ledger.entries) <= PATTERN_LEDGER_MAX_ENTRIES.

pledger.entries_validate_constructor_invariants
  For every entry in session.pattern_ledger.entries: re-running the
  PatternLedgerEntry constructor with the same field values
  succeeds without raising. This is the cheapest way to assert that
  no entry has been mutated underneath the slot (defense in depth
  against frozen-record drift).

pledger.recurrence_counts_bounded
  For every entry: STREAM_PATTERN_RECURRENCE_MIN <=
  recurrence_count <= STREAM_PATTERN_RECURRENCE_MAX.

pledger.confidence_matches_formula
  For every entry: confidence ==
  Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX).
  No float / round / math.* participates.

pledger.evidence_ids_bounded
  For every entry: len(evidence_chunk_ids) <=
  PATTERN_LEDGER_EVIDENCE_MAX, len(evidence_candidate_ids) <=
  PATTERN_LEDGER_EVIDENCE_MAX, and both tuples have no duplicate
  members.

pledger.pattern_id_matches_signature
  For every entry: entry.pattern_id ==
  derive_pattern_id(entry.signature).

pledger.session_local_only
  No /save-session / /load-session / persistence layer claims to
  persist the Pattern Ledger; the monitor verifies (statically) that
  brain/ui/persistence*.py contains no "pattern_ledger" reference
  and (dynamically) that a fresh OperatorSession built from a
  loaded session has session.pattern_ledger.entries == () unless
  the live session populated it through the /stream trigger.
```

### Persistence / autosave coherence

```text
persistence.session_db_configured_reported
  Reports session_db_configured = (session.session_store_config is
  not None). The monitor does NOT open the DB. If
  session_store_config is None, every persistence check is
  NOT_APPLICABLE — NOT FAIL.

persistence.no_pledger_schema_claim
  The monitor reports that v1 Pattern Ledger is session-local and
  not represented in the session DB schema (LOCK B). No DB row /
  table claim about Pattern Ledger appears in the report text.

persistence.commands_remain_separate
  /db-status, /db-verify, /db-summary, /profile-summary,
  /stream-db-summary, /db-diff, and /db-backup remain owned by
  their existing dispatchers; the monitor never re-implements them
  or opens the DB unless a later review gate explicitly
  authorizes it.

autosave.mode_reported
  Reports session.autosave_config.mode.value if autosave_config is
  not None, else the bounded string "". The monitor does NOT
  enable / disable autosave and never calls
  _maybe_autosave_after_dispatch.

autosave.no_persistence_extension_claim
  The monitor reports that Phase 3.12c did NOT extend the
  autosave trigger set (I-AUTOSAVE-12 set is unchanged).
```

### Non-claim coherence

```text
nonclaim.no_consciousness_terms_in_report
  The bounded printable report text contains no occurrence of
  "conscious", "consciousness", "sentience", "sentient",
  "subjective", "subjective experience", "qualia", "aware",
  "awareness", or "I-ness" (case-insensitive). Static string
  audit; deterministic.

nonclaim.no_truth_or_agency_terms
  The report text contains no PRESERVE / DAMAGE / agency
  adjudication phrase. The monitor never assigns truth values to
  raw text.

nonclaim.no_aggregate_iness_score
  No field in CoherenceSnapshot / CoherenceReport is a single
  scalar in [0, 1] / [0, n] purporting to summarize "I-ness",
  coherence-as-a-number, or awareness. counts_by_status is allowed
  (it is a tuple of bounded labelled counts, not a scalar).

nonclaim.no_semantic_understanding_claim
  The report text contains no claim that ToyI understands /
  comprehends / knows / believes / intends. Only structural
  agreements are reported.
```

## Proposed Integration Surface

### Option A — Pure Python read-only helper / snapshot API only

```text
brain/development/coherence_monitor.py
  - CoherenceCheckStatus enum
  - CoherenceCheck, CoherenceSnapshot, CoherenceReport records
  - finite closed CHECK_SOURCES enumeration of source values
  - constants: COHERENCE_MAX_CHECKS, MAX_SUMMARY_LEN, MAX_DETAIL_LEN
  - pure constructor and helper functions:
      build_coherence_snapshot(session, *, current_tick) ->
          CoherenceSnapshot
      build_coherence_report(snapshot) -> CoherenceReport
      compute_overall_status(checks) -> CoherenceCheckStatus
  - no UI command surface
  - no OperatorSession field; the monitor reads the session as an
    argument and returns a new bounded record
  - imports: dataclasses, enum, fractions, typing,
    brain.development.pattern_ledger,
    brain.development.text_stream, brain.io_types,
    brain.tlica.profile (COGITO_ID), brain.tlica.msi,
    brain.tlica.ptcns, brain.tick (for the BrainState typed
    record only — never the tick callable), brain.ui.session
    (for the OperatorSession typed record only), brain.ui.commands
    (only for the active_view set), brain.ui.snapshot (for
    ACTIVE_VIEWS); read-only.
```

Pros:

- Smallest implementation surface; ships the substrate without
  expanding the operator UI.
- No risk to the I-UISTRM-* / I-UI-* / I-OPSHARDEN-* /
  I-OBSERVE-* / I-AUTOSAVE-* / I-PLEDGER-* row families.
- Operators can build a report from any test harness or
  follow-up dry-run helper.
- A later UI step can ship `/coherence-summary` without
  re-running review gate C.

Cons:

- No bounded printable status line in the dispatch UX yet.
  Operators must construct the report explicitly.

### Option B — Add a read-only `/coherence-summary` command in v1

```text
brain/development/coherence_monitor.py         (as in Option A)
brain/ui/commands.py                           (add INSPECT_COHERENCE_SUMMARY)
brain/ui/command_line.py                       (add 'coherence-summary' verb)
brain/ui/session.py                            (add read-only dispatcher)
brain/ui/snapshot.py / brain/ui/render.py      (optional view pane)
brain/ui/fixtures/coherence_summary_ui_*.py    (fixture for the UI rows)
```

Constraints if Option B is selected:

- Dispatch is read-only: it may set `active_view =
  "coherence_summary"` and write a bounded printable status line.
- No `observe(...)` call, no `tick(...)` call, no kernel
  mutation, no DB open, no autosave trigger.
- The parser accepts no arguments; extra tokens reject as
  `LocalCommandError`.

Pros:

- One-step typed surface for "is the system coherent right now".
- Mirrors the existing `/session-status`, `/db-status`,
  `/autosave-status` ergonomic pattern.

Cons:

- Larger Step 14 patch; touches the UI parser / command set /
  dispatcher / renderer.
- Risk of UI scope creep: a single `/coherence-summary` command
  has a natural pull toward `/coherence-diff`,
  `/coherence-watch`, etc.

### Recommendation

**Option A first.** The Pattern Ledger just landed in Step 11 and
the I-OBSERVE-08 / I-OPSHARDEN-13 audit tier mechanism is fresh.
The right move is to ship the data substrate (`CoherenceCheck`,
`CoherenceSnapshot`, `CoherenceReport`) so a follow-up campaign
can promote `/coherence-summary` to REQUIRED if and only if the
operator decides the UI affordance is load-bearing. The deferred
`/coherence-summary` UI is the I-COHMON-13 DEFERRED row in the
companion catalog patch plan.

## Relationship to Future SelfModel / Growth Ledger

The Coherence Monitor is a **factual substrate** for two later
design layers:

- **Growth Ledger (Phase 3.12e roadmap).** A bounded ledger of
  *accepted growth events*: stream chunk accepted, pattern
  strengthened (a `PatternLedger.observe(...)` call that
  increased `recurrence_count`), candidate promoted, tick
  succeeded, content entered profile, content entered MSI,
  session saved / loaded, coherence report passed. The Coherence
  Monitor supplies the "coherence report passed" signal directly:
  a `CoherenceReport` with `overall_status == PASS` is the
  canonical event the Growth Ledger records, without re-deriving
  the underlying agreement.

- **Operational SelfModel (Phase 3.12e roadmap).** A read-only
  self-report that references the Coherence Monitor's latest
  snapshot rather than inventing self-claims. The SelfModel
  reports "I am anchored to `COGITO_ID`; my last coherence
  snapshot is X; my last tick is Y; my recognized pattern set has
  N entries" — every clause is a quote from an existing bounded
  record. No subjective claim is added.

Neither layer is implemented or fixtured here. They are listed
solely so the Coherence Monitor's record shape is sized for them
in advance (the snapshot is small, the report is bounded, the
overall status is a closed enum value).

## Non-goals

The Coherence Monitor work, at every step from Step 12 through
the eventual Step 14 implementation, must **not**:

- claim consciousness, sentience, subjective experience, or
  qualia,
- claim semantic understanding, language understanding, or
  comprehension,
- claim truth adjudication or assign PRESERVE / DAMAGE values to
  raw text or to anything else,
- claim agency, intent, or will,
- self-modify code, fixtures, the catalog, or its own
  constants,
- emit any hidden LLM call,
- emit any hidden filesystem write, network call, subprocess
  spawn, or shell command,
- introduce hidden persistence: the monitor does not save / load
  / back up the session, and it does not open the configured
  session DB unless a later review gate explicitly authorizes a
  DB-reading check,
- introduce an aggregate consciousness score, an aggregate
  "I-ness" score, or any single scalar claiming to summarize
  subjective experience,
- be reachable through `tick()`: the kernel runtime transition
  route remains untouched,
- mutate `BrainState`, `MSI`, `PtCns`, `ContentRegistry`,
  `OperatorSession.event_queue`, `stream_history`,
  `stream_candidates`, `stream_chunk_serial`, the Pattern Ledger,
  `latest_tick`, or `tick_counter`,
- map any raw text to `COGITO_ID`,
- alter `/step`, `/stream`, `/stream-promote`, `/save-session`,
  `/load-session`, `/db-*`, `/autosave-*`, or any existing
  dispatcher.

These prohibitions are inherited from the Phase 3.12 mission,
the Phase 3.11 audit, and the existing
`I-STRM-*` / `I-UISTRM-*` / `I-PERSIST-*` / `I-OPSHARDEN-*` /
`I-OBSERVE-*` / `I-AUTOSAVE-*` / `I-PLEDGER-*` discipline.

## Recommended Next Step

Pair this synthesis with the companion catalog patch plan:

```text
PHASE3_12_COHERENCE_MONITOR_CATALOG_PATCH_PLAN.md
```

Both documents are documentation only. **Implementation is not
authorized by either file.** Step 13 is Review Gate C; Step 14
implementation may proceed only after the operator explicitly
accepts the catalog patch plan at Review Gate C.
