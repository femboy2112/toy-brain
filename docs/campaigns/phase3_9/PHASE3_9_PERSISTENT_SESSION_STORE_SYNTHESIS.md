# PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.9 Persistent Session Store campaign before any
catalog, runtime, or fixture work. This is a planning artifact only.
It does not edit `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `brain/invariants.py`, `brain/ui/`,
`brain/persistence/` (it does not exist yet), or any guarded kernel
path.

Phase 3.9 follows Phase 3.8b LLM Runtime Toggle because the operator
text-stream / `/step` loop is now functionally complete but is still
process-local: cold start always rebuilds a fresh deterministic
session via `build_default_session()`. Phase 3.9 adds explicit,
typed, invariant-checked persistence for `BrainState`, profile,
registry, the Phase 3.7/3.8 text-stream session-local state, and the
operator session counters, without weakening the existing
`PerceptEvent` / `tick()` boundary.

## 1. Baseline

```text
Catalog version:  v0.16
REQUIRED:         178
STRUCTURAL:        64
NOT-EXERCISED:      9
DEFERRED:          12
OBSERVED:          12
Total tabular:    275
Total fixtures:    91

Latest merged campaign:
  Fast Safe Text Interaction
    Phase 3.6 Reflective Inspection        (PASS)
    Phase 3.7 Text Stream Ingress           (PASS)
    Phase 3.8 Operator Stream Interaction   (PASS)
    Phase 3.8b LLM Runtime Toggle           (PASS)
    Step 26 dry run                         (PASS)
  PR #6 merged into main 2026-05-15.

Preflight gates at HEAD:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  python3 -m brain.invariants run            178 / 64 / 7-OBS / 0 red
  bash tools/check_all.sh                    All checks passed
  brain-catalog-lint                         C1 / C2 / C3 / C4 PASS
  brain-campaign-state                       READY (Step 1)
```

## 2. Why persistence follows Phase 3.8b

Phase 3.6 / 3.7 / 3.8 / 3.8b together produced a complete bounded
loop:

```text
operator types raw text
  -> /stream                appends bounded TextStreamChunk
  -> /stream-summary         read-only segment / pattern counts
  -> /stream-candidates      read-only promotion candidates
  -> /stream-promote <id>    queues exactly one validated payload
  -> /step                   calls tick() with the selected client
                              (offline default; explicit opt-in for
                               mock / anthropic-api / claude-cli)
```

The substrate exists. The promotion bridge exists. The runtime
toggle exists. What is missing is durability: every component of the
loop is reconstructed from scratch on every launch.

Phase 3.9 is the first step that touches saved state. It is
deliberately scoped to one thing — typed, exact, schema-versioned
session/profile persistence — so the operator can run a session,
quit, and pick up where they left off without losing accumulated
profile values, registry texts, MSI / PtCns extension, tick counter,
or text-stream history.

## 3. Why current interaction is process-local

`brain/ui/__main__.build_default_session()` is the only entry point:

```python
def build_default_session() -> OperatorSession:
    profile = make_profile_with_cogito(
        {COGITO_ID: 1, "alpha": Fraction(3, 4)}
    )
    msi = make_msi(profile, contents={COGITO_ID, "alpha"},
                   threshold=Fraction(1, 2))
    ptcns = make_ptcns(msi, eval_map={
        COGITO_ID: ConsistencyEval.PRESERVE,
        "alpha":   ConsistencyEval.PRESERVE,
    })
    registry = ContentRegistry(
        texts=MappingProxyType({"alpha": "alpha text"})
    )
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns,
                       registry=registry)
    return OperatorSession(state=state)
```

`OperatorSession` carries:

```text
state                BrainState (profile, msi, ptcns, registry)
latest_tick          Optional[TickRecord]
output_history       Optional[OutputHistory]
worldlet_history     Optional[WorldletHistory]
repl_history         Optional[ProtoBasicHistory]
event_queue          OperatorEventQueue (bounded)
active_view          str
status_message       str
error_message        str
quit_flag            bool
tick_counter         int
stream_history       TextStreamHistory
stream_candidates    tuple[StreamPromotionCandidate, ...]
stream_chunk_serial  int
```

None of this is written to disk. Cold start discards everything.
That is what Phase 3.9 fixes — for the first slice of fields, with
strict guardrails on the rest.

## 4. Why SQLite over pickle / arbitrary JSON

`pickle` and `shelve` execute arbitrary code at load time. They make
the persisted state an opaque object graph rather than a typed
record. They are explicitly forbidden by the campaign boundaries.

Arbitrary JSON dumps are tempting but fragile in this kernel:

```text
- ScalarProfile values are fractions.Fraction. JSON has no Fraction
  encoding; serializing as float would silently lose exactness and
  break I-PROF-* / I-RT-* rows that depend on raw == on Fractions.
- BrainState carries frozen records (MSI, PtCns, ContentRegistry).
  Loading a free-form dict into BrainState is a direct assignment
  path that bypasses the existing constructors that enforce
  COGITO_ID, threshold bounds, eval_map / domain coverage, and
  registry shape.
- TextStreamChunk / TextStreamHistory enforce I-STRM-02 / I-STRM-03
  / I-STRM-11 (bounded printable text, COGITO_ID rejected, bounded
  length, copy-on-write history). A raw JSON loader would either
  duplicate those checks or weaken them.
```

SQLite via the standard-library `sqlite3` module gives:

```text
- a typed schema with explicit columns and FOREIGN KEY discipline;
- exact integer storage for Fraction numerator / denominator;
- transactional save / load (BEGIN / COMMIT / ROLLBACK);
- explicit schema version in a `meta` table;
- no Python execution on load;
- no dependency outside the standard library;
- a single file the user can inspect, back up, copy, or delete.
```

The persistence layer is therefore a typed, schema-versioned mapping
between SQLite rows and a small set of `Persistent*Snapshot`
dataclasses. Loaded snapshots are inputs to existing public
builders / constructors. The constructors do the validation. The
runner runs invariants. Persistence does not become a second source
of truth for kernel state.

## 5. What state should persist first

The first accepted persistence layer should save and restore:

```text
BrainState:
  ScalarProfile domain and Fraction values
    (stored as content_id + num INTEGER + den INTEGER pairs)
  MSI contents and threshold
    (contents stored as content_id rows; threshold as num/den)
  PtCns eval_map
    (content_id + eval enum name)
  ContentRegistry texts
    (content_id + bounded text)

OperatorSession:
  tick_counter            INTEGER
  stream_history          (chunks: ordinal, chunk_id, source,
                           text, tick_at_event, provenance_tag)
  stream_chunk_serial     INTEGER
  stream_candidates       (either persisted as rows, or
                           deterministically rebuilt from
                           restored chunks at load time -- the
                           corrigenda must decide which)

Metadata:
  schema_version          INTEGER
  catalog_version         TEXT  (the catalog the snapshot was
                                  produced against, e.g. "v0.16")
  created_at              TEXT  (ISO-8601)
  updated_at              TEXT  (ISO-8601)
```

What this slice deliberately does NOT include:

```text
latest_tick               (TickRecord summary; deferred)
event_queue contents      (operator-queued unconsumed payloads;
                           deferred)
output_history            (Phase 3.2)
worldlet_history          (Phase 3.3)
repl_history              (Phase 3.4)
expression_history        (Phase 3.5)
reflective_inspection_summary  (Phase 3.6)
operator_transcript       (Phase 3.8b)
full event log            (no replay in v1)
autosave policy           (NOT-EXERCISED in v1)
multi-profile / multi-session support
```

The corrigenda may add or remove items from this slice. Anything
not in the first accepted slice must be either explicitly DEFERRED
or NOT-EXERCISED in the Step 5 catalog patch plan.

## 6. How persistence preserves constructor / invariant discipline

The load path is the dangerous one. The rule is:

```text
1. Open the configured session DB in read-only mode.
2. Read schema_version + catalog_version from the meta table.
3. Reject unknown schema_version locally before touching kernel
   state.
4. Read typed Persistent*Snapshot records out of SQLite.
5. Call existing public builders / constructors:
     make_profile_with_cogito({content_id: Fraction(num, den), ...})
     make_msi(profile, contents=..., threshold=Fraction(num, den))
     make_ptcns(msi, eval_map={content_id: ConsistencyEval[name], ...})
     ContentRegistry(texts=MappingProxyType({content_id: text, ...}))
     BrainState(profile=, msi=, ptcns=, registry=)
     make_text_stream_chunk(...)  for every restored chunk
     TextStreamHistory(chunks=tuple(...))
     OperatorSession(state=, stream_history=, tick_counter=, ...)
6. Run brain.invariants assertion routines or
   assert_state_invariants over the reconstructed BrainState
   before activating the loaded session.
7. Replace the live session only if every step above succeeded.
```

There is no path that takes a `dict` straight into `BrainState` or
`ScalarProfile`. Every field flows through the same constructors
that already enforce:

```text
COGITO_ID is reserved
COGITO_ID is at value 1 in profile
rho values are in [0, 1]
threshold is a Fraction in [0, 1]
eval_map.keys() == profile.domain
registry keys correspond to profile content IDs
TextStreamChunk text is bounded printable and not equal to COGITO_ID
TextStreamHistory chunks are immutable tuple
```

Persistence does not weaken any of those checks. If the database
contains a violating row, the constructor raises and the load
operation aborts. The campaign treats that as a local error: the
existing live session is preserved.

## 7. How failed save / load behaves

The persistence layer must be transactional in both directions.

Save failure:

```text
- /save-session opens (or creates) the SQLite database in a
  transaction (BEGIN IMMEDIATE).
- If schema creation or any INSERT raises, ROLLBACK; the SQLite
  file may have been created but contains either the prior
  consistent state or no rows beyond a meta row.
- The live OperatorSession is untouched: save is a write,
  not a swap.
- The failure is reported as a bounded local UI error message
  through the existing status/error pipeline. No exception
  propagates into the curses wrapper.
```

Load failure:

```text
- /load-session opens the SQLite database in read-only mode
  (uri=True, mode=ro).
- It reads schema_version + catalog_version first. Unknown
  versions raise a typed LoadError locally.
- It builds Persistent*Snapshot records, then reconstructs a
  candidate OperatorSession through public builders.
- If any constructor raises (Fraction out of [0,1], COGITO_ID
  attempted overwrite, eval_map mismatch, threshold invalid,
  TextStreamChunk text non-printable, etc.), the candidate is
  discarded.
- The live OperatorSession is preserved. The failure is reported
  as a bounded local UI error message. No partial overwrite occurs.
```

Specifically: `COGITO_ID` is reserved (`I-MSI-03`, `I-MSI-06`,
`I-PROF-01`, `I-PROF-02`). The load path must not allow a persisted
row to overwrite `COGITO_ID`'s reserved value. The existing
`make_profile_with_cogito` constructor refuses to construct a
profile without `COGITO_ID` at value 1; load piggybacks on that.

## 8. Why autosave is deferred

Autosave is appealing but requires policy decisions that the
campaign has not made:

```text
- when does autosave fire? after every /step? after every
  /stream-promote? after every /save-session keystroke?
- where does it write? always to the configured DB? to a
  rolling backup file? to a journal?
- does autosave block tick()? if not, what is the consistency
  contract under crash mid-tick?
- how does autosave interact with cold-start failure recovery?
- what limits prevent autosave from writing inside a static
  fixture run?
```

Until a dedicated autosave policy + catalog rows are accepted,
Phase 3.9 saves only on explicit `/save-session`. The Step 5
catalog patch plan should encode autosave as NOT-EXERCISED with a
placeholder.

## 9. Resource discipline

The campaign already forbids unsafe resources on `OperatorSession`.
Phase 3.9 must not regress this:

```text
OperatorSession.* fields remain in _ALLOWED_SESSION_ATTRS.
The open sqlite3.Connection IS NOT placed on OperatorSession.
The Connection is opened inside save / load helpers, used inside
  a `with conn:` block (auto-commit / auto-rollback on exit), and
  closed before return.
The persistence module imports only:
  sqlite3, dataclasses, fractions, datetime, pathlib, typing,
  brain.io_types, brain.tlica.builders, brain.tlica.profile,
  brain.tlica.ptcns, brain.development.text_stream,
  brain.ui.session, brain.ui.commands (if needed)
and does NOT import:
  pickle, shelve, marshal, subprocess, socket, urllib, http,
  requests, curses, brain.tlica directly (except builders),
  brain.tick directly (BrainState is reachable through
  brain.tlica.builders or brain.io_types as appropriate).
```

The static audit fixture for the persistence module enforces this
import set.

## 10. Boundaries Phase 3.9 must not cross

```text
no raw text -> COGITO_ID
no raw text -> BrainState direct mutation
tick() remains the only TLICA transition route
/step remains the only operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
no LLM client / socket / handle / subprocess / callable / curses
  object / open db connection persisted on OperatorSession
no model output written to traces / scenarios / source histories
  by this campaign
no save / export path outside the configured session DB
no implicit autosave before an autosave policy is accepted
no change to tick() semantics
no new typed command outside the closed parser verb set
```

These were already listed in `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, and `PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md`.
They are restated here to anchor the kickoff and corrigenda.

## 11. Likely module placement

The kickoff (Step 3) must decide one of:

```text
brain/ui/persistence.py
  + brain/ui/fixtures/persistence_*.py
  + brain/ui/__main__.py CLI flag integration
```

or:

```text
brain/persistence/__init__.py
brain/persistence/session_store.py
  + brain/persistence/fixtures/persistence_*.py
  + brain/ui/__main__.py CLI flag integration (thin)
```

Argument for `brain/ui/persistence.py`:

```text
The data being saved is operator-session shaped, the entry
points (/save-session, /load-session) are UI commands, and the
existing Phase 3.7 / 3.8 ownership pattern keeps session-local
machinery under brain/ui/.
```

Argument for `brain/persistence/`:

```text
Persistence touches BrainState, not just UI session state. A
dedicated subsystem separates "the operator presses a key" from
"the kernel state is serialized through public builders."
brain/ui/ stays free of sqlite3, schema migrations, and
disk-format concerns.
```

The corrigenda (Step 4) should decide and lock one location. The
catalog patch plan (Step 5) then encodes the chosen file paths in
the row table.

## 12. Likely catalog row family

The catalog patch plan (Step 5) is canonical. The expected family:

```text
I-PERSIST-*
```

Likely themes (ordered roughly by criticality):

```text
1.  schema version is explicit and stored in meta
2.  SQLite schema is finite and closed
3.  Fractions persist exactly (num/den INTEGER pairs)
4.  load reconstructs through public builders / constructors only
5.  load runs invariant assertions before activating the session
6.  COGITO_ID cannot be overwritten by persisted data
7.  failed load preserves the live session
8.  failed save preserves the live session
9.  save transaction is atomic
10. persistence module imports are bounded; no pickle / shelve /
    network / subprocess / curses / brain.tick / brain.tlica
    runtime
11. session DB stores no LLM client / callable / handle / socket /
    subprocess / curses / open-db-connection blob
12. /save-session and /load-session are bounded local commands
    (no shell, no network, no eval, no JSON parse of payload)
13. autosave is NOT-EXERCISED unless explicitly accepted
14. cold-start continuity dry run is OBSERVED
```

REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED splits are deferred
to Step 5.

## 13. Risks

```text
- snapshot drift: persistent dataclass shape diverges from
  BrainState shape after a future kernel change. Mitigation:
  schema_version + catalog_version stored in meta; load rejects
  unknown versions locally.

- constructor bypass: a "convenience" code path in persistence
  takes a dict straight into BrainState. Mitigation: persistence
  module imports the public builders by name and uses them; the
  static audit fixture rejects "BrainState(" construction with
  any argument that did not come through a builder.

- float leakage: a developer stores rho values as REAL columns
  in SQLite to "simplify queries". Mitigation: profile_values
  uses rho_num INTEGER + rho_den INTEGER; a fixture asserts no
  REAL column appears in CREATE TABLE for kernel numeric fields.

- pickle smuggling: a TEXT column ends up holding repr(obj). The
  static audit must reject the strings "pickle", "shelve",
  "marshal", "eval(", "exec(", "compile(", and "import_module("
  inside the persistence module body.

- COGITO overwrite: a row in profile_values claims COGITO_ID at
  a non-1 value. Mitigation: make_profile_with_cogito refuses
  to construct without COGITO_ID at value 1, and the load path
  surfaces the failure as a typed LoadError.

- autosave creep: a "small convenience" autosave call shows up
  in tick / step / promote. Mitigation: catalog row asserts that
  no UI/persistence code outside the explicit /save-session
  dispatch invokes the save helper.

- session DB as event log: the persistence layer accidentally
  becomes a runtime trace by writing on every tick. Mitigation:
  campaign explicitly defers autosave; full event log replay is
  not in scope.
```

The Step 5 catalog patch plan should turn these risks into testable
rows.

## 14. Non-goals

Phase 3.9 does not authorize:

```text
- multi-profile / multi-user persistence
- network-backed persistence
- a replication / backup subsystem
- autosave (deferred to a future campaign)
- full TickRecord / event-log replay
- migrations between schema versions (only v1 is defined; an
  unknown schema_version is a typed local error)
- persistence of LLM client state, cache contents, or runtime mode
- persistence of operator transcripts beyond what is already
  session-local
- persistence of curses configuration / terminal state
- raw-text-to-COGITO mappings
- raw-text-to-BrainState direct writes
- model output written to traces / scenarios / source histories
- save / export paths outside the configured DB
- change to tick() semantics
```

## 15. Next artifact

```text
PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md
```

The kickoff should define:

```text
- the exact module placement (brain/ui/persistence.py vs
  brain/persistence/session_store.py);
- the proposed typed records (SessionStoreConfig,
  SessionStoreSchemaVersion, PersistentSessionSnapshot,
  PersistentBrainStateSnapshot, PersistentStreamSnapshot,
  SaveSessionResult, LoadSessionResult, PersistenceError);
- the SQLite schema in detail (table names, columns, types,
  PRIMARY KEY / UNIQUE / NOT NULL constraints);
- the save / load helper signatures;
- the failure handling contract;
- the proposed CLI flag set (--session-db, --load-session,
  --no-load-session);
- the proposed /save-session and /load-session command shape;
- the proposed fixture roster sketch;
- the stop point before the corrigenda.
```

After the kickoff, the corrigenda (Step 4) audits and locks the
design before the Step 5 catalog patch plan binds rows. The
campaign stops at the Step 6 review gate after Step 5 lands.
