# PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md

## Purpose

Audit `PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md` before the
catalog patch plan. This is a planning artifact only. It does not
edit the catalog, runtime modules, fixtures, README, traces,
scenarios, or guarded kernel paths.

Verdict for Step 4:

```text
COHERENT - PROCEED TO CATALOG PATCH PLAN
```

## 1. Baseline

```text
Catalog version:  v0.16
REQUIRED:         178
STRUCTURAL:        64
NOT-EXERCISED:      9
DEFERRED:          12
OBSERVED:          12
Total fixtures:    91
Current phase:    Phase 3.9 Persistent Session Store
```

Accepted prior artifacts:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md
PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md
PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md
```

## 2. SQLite vs file snapshot

Kickoff proposal:

```text
SQLite via the standard-library sqlite3 module, schema bootstrapped
with CREATE TABLE IF NOT EXISTS in a single transactional save.
```

Corrigendum:

```text
ACCEPTED.
```

Reasoning:

```text
- sqlite3 is part of Python's standard library; the repo gains no
  new external dependency.
- A typed schema gives column-level checks for kernel numeric data
  (rho_num INTEGER + rho_den INTEGER + CHECK den > 0) that a JSON
  / TOML / YAML / pickle file cannot enforce without a second
  validation layer.
- A single .sqlite3 file is easy to inspect (sqlite3 CLI), back
  up (cp), and delete (rm). It matches the campaign's preferred
  path brain/session.sqlite3.
- The standard-library `with sqlite3.connect(...) as conn:` context
  guarantees commit-or-rollback on the with-block exit; combined
  with BEGIN IMMEDIATE this gives the atomic-save property without
  bringing in an external library.
- Plain-file snapshots (TOML / JSON / sexp) lose exactness or
  require a parallel typed validation layer to recover what
  sqlite3's column types give for free.
```

Decision:

```text
The catalog patch plan must require:
- sqlite3-only implementation
- no pickle / shelve / marshal / dill / cloudpickle / joblib
- no JSON / TOML / YAML as the authoritative kernel-state format
- no executable-format file (.py, .so, etc.) as a save target
```

## 3. Schema versioning

Kickoff proposal:

```text
SCHEMA_VERSION_V1 = 1
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION_V1})
meta rows: schema_version, catalog_version, created_at, updated_at
```

Corrigendum:

```text
ACCEPTED WITH EXPLICIT MIGRATION DEFERRAL.
```

Additions required for the catalog patch plan:

```text
- The integer schema_version must be stored as a TEXT meta value
  (sqlite uses dynamic typing, but a TEXT-coerced integer is
  unambiguous and avoids accidental REAL drift).
- The reader must `int()` the TEXT value before comparing against
  SUPPORTED_SCHEMA_VERSIONS.
- Migration paths between schema versions are explicitly NOT
  defined in Phase 3.9. An unknown schema_version raises
  PersistenceError("unsupported schema_version: <value>; expected
  one of {1}"). The catalog plan must include a row that asserts
  this rejection.
- catalog_version is a bounded ASCII string; it is recorded for
  diagnostics but does NOT participate in load-time gating in
  v1. The corrigenda explicitly defers catalog_version migration
  to a later campaign so a future I-PERSIST row can pick it up.
- created_at is written only when the row is absent in meta
  (preserves the original session DB origin time across save
  cycles).
- updated_at is written on every successful save.
- ISO-8601 timestamps use datetime.datetime.now(tz=UTC).isoformat();
  the corrigenda forbids strftime() with locale-dependent output.
```

Decision:

```text
The kickoff's schema versioning is coherent. The catalog plan
must add a row for unknown schema_version rejection.
```

## 4. Exact Fraction persistence

Kickoff proposal:

```text
profile_values:  rho_num INTEGER, rho_den INTEGER CHECK (rho_den > 0)
msi_threshold:   num INTEGER, den INTEGER CHECK (den > 0)
```

Corrigendum:

```text
ACCEPTED WITH NO-REAL-COLUMN RULE.
```

The catalog plan must require:

```text
- Every kernel-numeric column is INTEGER. No REAL or NUMERIC column
  may hold a kernel rho, threshold, distance, rank, projected-PCE,
  or other Fraction-valued field.
- The CHECK (rho_den > 0) and CHECK (den > 0) constraints are
  asserted at schema-creation time.
- Load reconstructs values via Fraction(num, den). The corrigenda
  notes that Fraction(num, den) does not enforce coprimality;
  saving uses Fraction(value).numerator / .denominator which is
  already canonicalized.
- The static AST audit must reject "REAL", "NUMERIC", "FLOAT",
  "DOUBLE", and `float(` arithmetic on kernel rho/threshold values
  inside brain/ui/persistence.py.
- A fixture compares saved rho_num/rho_den against the original
  Fraction values byte-for-byte. The kickoff calls this
  persistence_schema.py + persistence_save_roundtrip.py; the
  corrigenda confirms both fixtures.
```

Decision:

```text
The kickoff's exact-Fraction storage is coherent. The catalog plan
must lock the no-REAL-kernel-column rule as a STRUCTURAL row.
```

## 5. COGITO_ID reservation on load

Kickoff proposal:

```text
make_profile_with_cogito refuses to construct without COGITO_ID at
value 1; load piggybacks on that. A DB row claiming COGITO_ID at a
non-1 value triggers PersistenceError. Live session preserved.
```

Corrigendum:

```text
ACCEPTED AS HARD BOUNDARY.
```

The catalog plan must require a dedicated REQUIRED row covering:

```text
- A persisted profile_values row with content_id = COGITO_ID and
  rho_num/rho_den != 1/1 must fail load with PersistenceError.
- A persisted msi_contents missing COGITO_ID must fail load.
- A persisted ptcns_eval row mapping COGITO_ID to something other
  than ConsistencyEval.PRESERVE must fail load (or be normalized
  through make_ptcns, whichever the implementation chooses; the
  fixture pins the chosen behavior).
- A persisted registry row binding COGITO_ID to a non-default text
  is acceptable iff the existing ContentRegistry constructor
  accepts it; the corrigenda does not require Phase 3.9 to widen
  or narrow the existing registry contract.
- The save side preserves COGITO_ID: a session with COGITO_ID at
  value 1 round-trips to a saved row with rho_num=1, rho_den=1.
```

Decision:

```text
COGITO_ID protections are mandatory. The catalog plan must encode
them as one or two REQUIRED rows (likely one combined fixture).
```

## 6. Constructor-only reconstruction

Kickoff proposal:

```text
Load reconstructs through make_profile_with_cogito, make_msi,
make_ptcns, ContentRegistry, BrainState, make_text_stream_chunk,
TextStreamHistory, make_stream_promotion_candidate, OperatorSession.
No direct attribute assignment.
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require:

```text
- Static AST audit (persistence_static_audit.py / persistence_load_
  constructor_only.py) over brain/ui/persistence.py that confirms
  every kernel-record construction site is one of:
    BrainState(profile=..., msi=..., ptcns=..., registry=...)
    ContentRegistry(texts=MappingProxyType({...}))
    OperatorSession(state=..., ...)
  and that profile / msi / ptcns / text_stream_chunk /
  text_stream_history / stream_promotion_candidate constructions go
  through the documented builders.
- The audit must reject any line that assigns to a private field of
  BrainState, ScalarProfile, MSI, PtCns, ContentRegistry,
  TextStreamChunk, TextStreamHistory, StreamPromotionCandidate, or
  OperatorSession (e.g. `state.profile = ...`,
  `object.__setattr__(state, "profile", ...)`,
  `_replace` shenanigans on frozen records, etc.).
- The audit must reject the use of pickle.loads / shelve.open /
  marshal.loads / json.loads-as-dict-direct-into-constructor on
  authoritative kernel state. (json.loads on a single TEXT meta
  value is OK; the test pins the distinction.)
```

Decision:

```text
The kickoff's constructor-only contract is coherent. The catalog
plan must encode it both as behavioral (round-trip equality) and
structural (AST audit) rows.
```

## 7. Load failure isolation

Kickoff proposal:

```text
load_session returns (OperatorSession, LoadSessionResult) on
success. On any failure raises PersistenceError; the candidate is
discarded and the live session is unchanged.
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require fixtures for:

```text
- DB path does not exist.
- DB path is a directory.
- DB schema_version row is missing.
- DB schema_version row holds an unknown integer.
- DB schema_version row holds non-integer TEXT.
- profile_values row violates CHECK rho_den > 0 (corrupted DB).
- msi_threshold row missing or duplicated.
- msi_contents references a content_id not present in
  profile_values (FK violation).
- ptcns_eval references a content_id not present in
  profile_values.
- ContentRegistry text exceeds the bounded length.
- Fraction(rho_num, rho_den) is outside [0, 1].
- make_profile_with_cogito raises (COGITO_ID overwrite attempt or
  missing COGITO_ID).
- assert_state_invariants raises after constructor assembly.
- A read-mode load is attempted and the DB file cannot be opened.
```

Every fixture asserts:

```text
- PersistenceError is raised.
- The live OperatorSession field-for-field equals the pre-call
  session (state identity preserved or identical via __eq__).
- The on-disk DB file is unchanged (read-only mode guarantees this;
  the fixture may also stat() before and after).
```

Decision:

```text
Failed-load isolation is coherent. The catalog plan should
consolidate the fixtures into one or two persistence_failed_load
modules with parameterized cases, mirroring how
stream_failure_isolation.py covers multiple cases in one module.
```

## 8. Save transaction behavior

Kickoff proposal:

```text
Single BEGIN IMMEDIATE / COMMIT pair; ROLLBACK on any failure;
live OperatorSession never mutated.
```

Corrigendum:

```text
ACCEPTED WITH ATOMIC-SAVE FIXTURE REQUIRED.
```

The catalog plan must require:

```text
- A fixture (persistence_atomic_save.py) that injects a failure
  mid-save (e.g. monkeypatches an INSERT to raise) and asserts:
  * the transaction rolled back;
  * the live OperatorSession is unchanged;
  * a subsequent successful save into the same DB path produces
    a clean snapshot indistinguishable from one made without the
    injected failure.
- The save helper must use `with sqlite3.connect(...) as conn:`
  with isolation_level=None and an explicit BEGIN IMMEDIATE so the
  with-block's __exit__ commits on success and rolls back on
  exception (per sqlite3 module semantics).
- Save uses DELETE-then-INSERT (or an equivalent typed-upsert) so
  partial overwrites cannot leave orphaned rows after a successful
  COMMIT. The corrigenda prefers DELETE-then-INSERT for simplicity.
- Save must not depend on `pragma synchronous = OFF` or similar
  durability degradations; the SQLite default journaling is
  sufficient.
```

Decision:

```text
The kickoff's atomic-save contract is coherent. The catalog plan
should add a STRUCTURAL row tying the contract to the
persistence_atomic_save.py fixture.
```

## 9. No pickle / no object-repr authority

Kickoff proposal:

```text
No table stores executable code, callable names, import paths,
shell commands, pickle blobs, or arbitrary Python object repr as
authoritative state.
```

Corrigendum:

```text
ACCEPTED AS HARD BOUNDARY.
```

The catalog plan must require:

```text
- Static AST audit (persistence_static_audit.py) over
  brain/ui/persistence.py that rejects:
    * `import pickle`, `import shelve`, `import marshal`,
      `import dill`, `import cloudpickle`, `import joblib`
    * `__import__(`, `importlib.import_module(`
    * `eval(`, `exec(`, `compile(`
    * `subprocess.`, `socket.`, `urllib.`, `http.`,
      `requests.`, `curses.`
    * `brain.tick` direct imports of `tick` callable (builders
      and BrainState are OK; the corrigenda treats BrainState as
      a typed value, not a runtime callable).
- Static text-string audit that rejects the bare strings "pickle",
  "shelve", "marshal", "eval(", "exec(", "compile(",
  "import_module(", "subprocess" anywhere in the module body
  outside docstring / comment context (the AST audit is the
  primary gate; the string scan is a defense-in-depth).
- No TEXT column anywhere in the schema may store a Python repr
  as authoritative state. A meta diagnostic row may store
  catalog_version or created_at strings; those are typed
  diagnostics, not authoritative state.
```

Decision:

```text
The catalog plan must encode the static audit as a STRUCTURAL row
and reference it from the persistence_static_audit fixture.
```

## 10. Session resource-free property

Kickoff proposal:

```text
OperatorSession adds an Optional[SessionStoreConfig] field. No
sqlite3.Connection is stored on OperatorSession; connection
lifetime is scoped to save / load helpers.
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require:

```text
- _ALLOWED_SESSION_ATTRS adds "session_store_config".
- A fixture (persistence_session_resource_audit.py) confirms that
  every OperatorSession field is one of:
    BrainState, OperatorEventQueue, bounded printable str,
    bool, non-negative int, TextStreamHistory,
    tuple[StreamPromotionCandidate, ...],
    Optional[OutputHistory], Optional[WorldletHistory],
    Optional[ProtoBasicHistory], Optional[TickRecord],
    Optional[SessionStoreConfig]
  and rejects any field containing sqlite3.Connection,
  subprocess.Popen, socket.socket, file objects, callables,
  curses objects, or LLM clients.
- The fixture asserts that SessionStoreConfig's own fields are
  bounded: pathlib.Path, int, str -- no Connection, no Cursor,
  no callable.
```

Decision:

```text
The kickoff's resource discipline is coherent. The catalog plan
must extend the existing resource-free row family (or add a new
persistence resource-audit row) to cover SessionStoreConfig.
```

## 11. DB connection lifetime

Kickoff question:

```text
Whether the SQLite connection may be long-lived or
operation-scoped.
```

Corrigendum:

```text
OPERATION-SCOPED. NO LONG-LIVED CONNECTION ON OPERATORSESSION.
```

Rationale:

```text
- A long-lived sqlite3.Connection on OperatorSession would
  violate the resource-free policy and require new lifecycle
  management at curses-wrapper exit.
- Save and load are infrequent (operator types /save-session or
  /load-session; not on every tick), so connection-open cost is
  negligible.
- An operation-scoped `with sqlite3.connect(...) as conn:` is
  the simplest atomic shape: the with-block commits or rolls back
  deterministically.
- A future autosave campaign (not Phase 3.9) may revisit
  connection lifetime if it ever justifies a long-lived
  connection.
```

The catalog plan must encode "no long-lived sqlite3.Connection on
OperatorSession" as a STRUCTURAL invariant.

## 12. Autosave deferral

Kickoff proposal:

```text
Autosave is NOT-EXERCISED in v1. /save-session and /load-session
are explicit only.
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require:

```text
- A NOT-EXERCISED row (I-PERSIST-AUTOSAVE) that holds the place
  for a future autosave catalog row.
- A STRUCTURAL static-audit row that confirms brain/ui/persistence.py
  is not called from /step, /stream, /stream-promote, or any
  other tick-adjacent dispatch path.
- The audit also rejects @atexit, signal handlers, threading
  primitives, asyncio primitives, and "background autosave"
  patterns in the persistence module.
```

Decision:

```text
No autosave in Phase 3.9. The catalog plan must place an explicit
NOT-EXERCISED row so a future campaign cannot land an autosave
path without an accepted catalog row.
```

## 13. Stream candidate persistence

Kickoff proposal:

```text
Stream candidates are either persisted as rows or
deterministically rebuilt from restored chunks at load time.
```

Corrigendum:

```text
PERSIST IF PRESENT; REBUILD ONLY IF ABSENT.
```

Rationale:

```text
- Persisting candidates preserves the operator's view of the
  session at save time (the displayed candidate list survives
  cold start exactly).
- Rebuilding from restored chunks is the safe fallback if a
  partial DB lacks candidate rows (e.g. an older v1 save that
  predates a candidate rebuild change).
- The implementation in v1 always saves candidates when they
  exist on the session; rebuild_candidates_if_missing=True is
  the documented fallback behavior on load.
- LoadSessionResult.rebuilt_candidates reports which path the
  load took. A fixture asserts the round-trip is exact when
  candidates are persisted, and that the rebuild path produces
  the same candidates the Phase 3.7 substrate would produce
  given the restored chunks.
```

Decision:

```text
The catalog plan must encode candidate round-trip equality in a
REQUIRED row (likely persistence_save_roundtrip.py).
```

## 14. Catalog row status assignment

Kickoff sketch named the likely fixture roster. The corrigenda
proposes the following status assignment, subject to the Step 5
catalog patch plan:

```text
REQUIRED:
  schema is finite and closed                              (audit)
  unknown schema_version is rejected on load               (failed_load)
  exact Fraction round-trip                                (save_roundtrip)
  COGITO_ID cannot be overwritten on load                  (cogito_protected)
  load reconstructs through public builders / constructors (load_constructor_only)
  load runs invariants before returning                    (load_invariants)
  failed save preserves the live session                   (failed_save)
  failed load preserves the live session                   (failed_load)
  /save-session and /load-session are bounded + no tick    (commands)

STRUCTURAL:
  save transaction is atomic                               (atomic_save)
  session resource-free with SessionStoreConfig            (session_resource_audit)
  persistence module static audit                          (static_audit)
  no kernel-numeric REAL columns                           (schema)
  no long-lived sqlite3.Connection on OperatorSession      (session_resource_audit)

OBSERVED:
  cold-start continuity dry run                            (persistence_dry_run, Step 11)

NOT-EXERCISED:
  autosave path                                            (autosave_absent)
```

Decision:

```text
The Step 5 catalog patch plan binds the exact row IDs and the
exact count delta. The corrigenda's recommended split is:
  + 9 REQUIRED
  + 5 STRUCTURAL
  + 1 OBSERVED
  + 1 NOT-EXERCISED
This brings v0.17 to:
  REQUIRED       = 178 + 9  = 187
  STRUCTURAL     =  64 + 5  =  69
  NOT-EXERCISED  =   9 + 1  =  10
  DEFERRED       =  12          (unchanged)
  OBSERVED       =  12 + 1  =  13
The Step 5 plan is canonical; it may shift one or two rows
between REQUIRED and STRUCTURAL if a fixture turns out to cover
two rows naturally. Any change to this split must keep the
delta totals coherent with the v0.17 catalog banner.
```

## 15. File budget audit

Kickoff proposal:

```text
brain/ui/persistence.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/render.py
brain/ui/fixtures/persistence_*.py
brain/invariants.py
brain/_catalog_ids.py
INVARIANT_CATALOG.md
tools/catalog.py
README.md
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must NOT touch:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
brain/development/text_stream.py
brain/development/fixtures/text_stream_*.py
```

If a fixture needs a stream chunk for round-trip testing, it must
build the chunk through the existing public
`make_text_stream_chunk` constructor; it must not import private
text_stream module internals.

## 16. Module placement decision

Kickoff proposal:

```text
brain/ui/persistence.py with fixtures under brain/ui/fixtures/.
```

Corrigendum:

```text
ACCEPTED.
```

Rationale (restated for the catalog plan):

```text
- Phase 3.7 / 3.8 / 3.8b established the precedent of placing
  session-local machinery in brain/ui/ with bounded fixtures in
  brain/ui/fixtures/.
- The data being saved is operator-session shaped; the entry
  points are typed operator commands.
- A future, broader persistence subsystem (multi-profile, network,
  replication, autosave) may graduate into brain/persistence/
  under a later campaign. Phase 3.9 v1 does not require that move.
```

The catalog plan must therefore use `brain/ui/persistence.py` as
the owning module identifier in the row table and use
`brain/ui/fixtures/persistence_*.py` as the fixture paths.

## 17. Hard non-goals (restated)

The catalog plan must not authorize any of the following in any
Phase 3.9 row, fixture, or runtime path:

```text
- raw text -> COGITO_ID
- raw text -> BrainState direct mutation
- pickle / shelve / marshal / dill / cloudpickle / joblib as a
  persistence format
- JSON / TOML / YAML as the authoritative kernel-state format
- REAL / NUMERIC / FLOAT / DOUBLE columns for kernel numeric data
- a sqlite3.Connection on OperatorSession
- autosave from /step, /stream, /stream-promote, or any other
  tick-adjacent path
- network-backed persistence
- multi-profile / multi-user persistence
- migrations between schema versions
- persistence of LLM client / cache / runtime mode
- persistence of operator transcripts beyond bounded session-local
  state
- persistence of curses configuration / terminal state
- modifications to tick() semantics
- new typed operator commands outside /save-session and
  /load-session
- any save / export path outside the configured session DB
```

## 18. Stop point

Next artifact:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_CATALOG_PATCH_PLAN.md
```

The plan must:

```text
- bind the row family name (likely I-PERSIST-*)
- bind row statuses per Section 14
- compute the exact count delta and the resulting v0.17 banner
- pin the file budget per Section 15
- pin the fixture roster
- pin pending-registration mechanics
- restate the v0.17 review-gate stop condition
```

Then the campaign must stop at the Step 6 review gate. No catalog
row, runtime module, fixture, or README change may land until the
Step 5 plan is explicitly accepted.

## Conclusion

The Phase 3.9 kickoff is coherent. The next artifact is:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_CATALOG_PATCH_PLAN.md
```

After that plan is committed and pushed, the campaign halts at the
Step 6 review gate.
