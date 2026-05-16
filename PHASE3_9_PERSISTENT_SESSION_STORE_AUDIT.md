# PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md

## 1. Purpose

Audit the complete Phase 3.9 Persistent Session Store implementation
against the accepted synthesis, kickoff, corrigenda, and catalog
patch plan. This document is an audit artifact: it does not edit
`brain/ui/persistence.py`, any persistence fixture,
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
or `brain/invariants.py`.

```text
Verdict for Step 12: PASS
```

## 2. Baseline

```text
Catalog version:  v0.17
REQUIRED:        187
STRUCTURAL:       69
NOT-EXERCISED:    10
DEFERRED:         12
OBSERVED:         13
Total tabular:   291
Total fixtures:  103

Landed campaign steps:
  Step 1   repo-state sync                   commit 770dc24
  Step 2   persistence synthesis             commit bc2ffd3
  Step 3   persistence kickoff               commit aab9e5e
  Step 4   persistence corrigenda            commit 35ee067
  Step 5   persistence catalog patch plan    commit 89f043e (+ user
                                             review patch d4e902d)
  Step 6   review gate                       (accepted)
  Step 7   v0.17 catalog patch landed        commit 59fd6a5
  Step 8   schema + typed records            commit 81123b7
  Step 9   save/load reconstruction          commit a92d4d3
  Step 10  /save-session + /load-session +   commit eac52f6
           CLI flags
  Step 11  cold-start dry run                commit 824c796
  Step 12  this audit                        this document
```

Required source artifacts (all readable from the campaign branch):

```text
PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md
PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md
PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md
PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md
PHASE3_9_PERSISTENT_SESSION_STORE_CATALOG_PATCH_PLAN.md
PHASE3_9_PERSISTENCE_DRY_RUN.md
INVARIANT_CATALOG.md (v0.17)
brain/ui/persistence.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/fixtures/persistence_*.py
brain/invariants.py
tools/catalog.py
README.md
```

## 3. Schema + migration behaviour (I-PERSIST-01, I-PERSIST-02, I-PERSIST-13)

```text
Audit:    brain/ui/persistence.py declares exactly the v1 schema
          (meta, content_registry, profile_values, msi_contents,
          msi_threshold, ptcns_eval, session_state, stream_chunks,
          stream_candidates). PRIMARY KEY, UNIQUE, FOREIGN KEY, and
          CHECK constraints (rho_den > 0, den > 0,
          msi_threshold.id = 1) are present and enforced. Every
          kernel-numeric column is INTEGER; identifiers / enum
          names / printable text / ISO timestamps are TEXT; no
          REAL / NUMERIC / FLOAT / DOUBLE column exists.
          load_session reads meta.schema_version, coerces to int,
          and raises PersistenceError for any value outside
          SUPPORTED_SCHEMA_VERSIONS = {1}; migrations between
          schema versions are explicitly deferred.

Evidence: persistence_schema.py constructs the schema on an
          in-memory SQLite database, asserts table set ==
          EXPECTED_TABLES, asserts every table's PRAGMA
          table_info matches the documented column shape, asserts
          the documented FOREIGN KEYs exist, and confirms the CHECK
          constraints by attempting violating INSERTs.
          persistence_failed_load.py overwrites
          meta.schema_version to '99' and to 'not-an-int' and
          asserts both surface as PersistenceError.

Rows:     I-PERSIST-01 REQUIRED, I-PERSIST-02 REQUIRED,
          I-PERSIST-13 STRUCTURAL.
Status:   PASS.
```

## 4. Exact Fraction persistence (I-PERSIST-03)

```text
Audit:    save_session stores ScalarProfile values and the MSI
          threshold as (num INTEGER, den INTEGER) pairs;
          load_session reconstructs them as Fraction(num, den).
          Round-trip equality holds under Fraction.__eq__. No
          float() / Decimal / REAL column appears in any
          kernel-numeric path.

Evidence: persistence_save_roundtrip.py constructs a sample
          OperatorSession with profile values 3/7 and 11/13, MSI
          threshold 1/3, and ptcns_eval covering all three domain
          entries; saves and reloads; asserts profile.domain,
          profile.values (per-key Fraction equality + isinstance
          Fraction), msi.contents, msi.threshold, ptcns.eval_map,
          ContentRegistry texts, tick_counter, stream_chunk_serial,
          and stream_history.chunks (chunk_id / text / source /
          provenance) are equal field-for-field. A subsequent
          re-save round-trip is idempotent.

Row:      I-PERSIST-03 REQUIRED.
Status:   PASS.
```

## 5. COGITO_ID reservation (I-PERSIST-04)

```text
Audit:    A persisted profile_values row with content_id =
          COGITO_ID and rho != 1, a missing msi_contents
          COGITO_ID row, a ptcns_eval row mapping COGITO_ID to a
          non-PRESERVE evaluation, or a removed COGITO profile
          row all raise PersistenceError on load. Save of a
          session with COGITO_ID at value 1 round-trips exactly.

Evidence: persistence_cogito_protected.py performs a baseline
          save+load round-trip (COGITO at rho 1, PRESERVE eval,
          present in msi.contents), then mutates each of the four
          documented attack shapes in turn and confirms each
          raises PersistenceError. The live OperatorSession is
          unchanged on every failure.

Row:      I-PERSIST-04 REQUIRED.
Status:   PASS.
```

## 6. Constructor-only reconstruction (I-PERSIST-05)

```text
Audit:    brain/ui/persistence.py builds the candidate
          OperatorSession by calling make_profile_with_cogito,
          make_msi, make_ptcns, ContentRegistry(...),
          BrainState(profile=, msi=, ptcns=, registry=),
          make_text_stream_chunk, TextStreamHistory(chunks=...),
          make_stream_promotion_candidate, and OperatorSession(
          state=, ...). No attribute / private-field assignment on
          any kernel record; no object.__setattr__; no pickle /
          shelve / marshal / dill / cloudpickle load on
          authoritative kernel state.

Evidence: persistence_load_constructor_only.py combines a static
          AST audit over brain/ui/persistence.py (rejects forbidden
          setattr targets and pickle / shelve / marshal / dill /
          cloudpickle loads, asserts every required builder name is
          called) with a behavioural test that wraps each builder
          in a counting closure and confirms load_session calls
          each at least once during reconstruction.

Row:      I-PERSIST-05 REQUIRED.
Status:   PASS.
```

## 7. Invariant assertion on load (I-PERSIST-06)

```text
Audit:    After assembling the candidate state, load_session
          invokes brain.tick.assert_state_invariants on the
          candidate BrainState. If the assertion raises,
          load_session raises PersistenceError and returns no
          candidate session.

Evidence: persistence_load_invariants.py patches
          brain.ui.persistence.assert_state_invariants with a
          counting wrapper, runs save_session + load_session, and
          confirms the assertion was called at least once. It then
          patches assert_state_invariants with a stub that raises
          a synthetic ValueError; load_session is expected to
          surface that as PersistenceError without returning a
          candidate session. Both behaviours hold.

Row:      I-PERSIST-06 REQUIRED.
Status:   PASS.
```

## 8. Save / load failure isolation (I-PERSIST-07, I-PERSIST-08, I-PERSIST-10)

```text
Audit:    save_session opens a sqlite3.connect(...) with
          isolation_level=None, bootstraps the schema in
          autocommit (idempotent CREATE TABLE IF NOT EXISTS), then
          wraps the data writes in BEGIN IMMEDIATE / COMMIT or
          ROLLBACK on failure. A mid-save failure (synthetic
          IntegrityError / OperationalError) triggers ROLLBACK and
          leaves no orphaned rows from the failed attempt; the
          schema persists because it was bootstrapped in
          autocommit before the data transaction; the live
          OperatorSession is unchanged.

          load_session opens the DB in sqlite3 uri mode=ro, so a
          failed load never mutates the on-disk file. Missing DB,
          directory path, missing meta rows, unknown
          schema_version, FOREIGN KEY violations, malformed
          Fraction pairs, and constructor / invariant rejection
          all surface as PersistenceError; the live
          OperatorSession is unchanged.

Evidence: persistence_failed_save.py injects a synthetic
          sqlite3.IntegrityError mid-save, confirms the live
          session is unchanged after the rollback, confirms the
          DB does not contain the orphan row, and confirms a
          subsequent successful save produces a clean snapshot.
          persistence_atomic_save.py performs an AST audit that
          save_session passes isolation_level=None, executes
          BEGIN IMMEDIATE / COMMIT / ROLLBACK, and behaviourally
          confirms ROLLBACK removes synthetic rows.
          persistence_failed_load.py covers every documented
          failed-load mode (missing DB, directory path, missing
          schema_version row, missing msi_threshold, malformed
          Fraction rho_num=5 / rho_den=3), confirms PersistenceError
          is raised, and asserts the live OperatorSession field
          values + BrainState identity are unchanged.

Rows:     I-PERSIST-07 REQUIRED, I-PERSIST-08 REQUIRED,
          I-PERSIST-10 STRUCTURAL.
Status:   PASS.
```

## 9. /save-session and /load-session (I-PERSIST-09)

```text
Audit:    LocalCommandLine.parse accepts /save-session and
          /load-session as closed verbs. Both verbs route through
          _parse_no_args so any trailing argument surfaces as
          LocalCommandError. Both dispatchers call save_session /
          load_session; both surface bounded printable status /
          error text on OperatorSession via the existing
          set_status / set_error helpers; both fail closed when
          session_store_config is None. Neither dispatcher
          invokes tick().

Evidence: persistence_commands.py confirms the verbs are in
          LOCAL_COMMAND_VERBS, parser produces typed Commands with
          payload=None, trailing arguments are rejected, the
          dispatchers do NOT call tick (verified via a counting
          wrapper around brain.ui.session.tick), success surfaces
          a "saved session ..." / "loaded session ..." status, and
          missing config surfaces a bounded local error message
          without mutating live state.

Row:      I-PERSIST-09 REQUIRED.
Status:   PASS.
```

## 10. Resource-free session + no long-lived connection (I-PERSIST-11, I-PERSIST-14)

```text
Audit:    OperatorSession carries an Optional[SessionStoreConfig]
          field. _ALLOWED_SESSION_ATTRS includes
          "session_store_config". SessionStoreConfig's fields are
          bounded primitives (pathlib.Path, int, str). No
          OperatorSession or SessionStoreConfig field is a
          sqlite3.Connection, sqlite3.Cursor, subprocess handle,
          socket, file object, callable, curses object, or LLM
          client. Save and load helpers use `with
          sqlite3.connect(...) as conn:` (save) / explicit
          try/finally + conn.close() (load), and close the
          connection on with-block exit. No module-level
          sqlite3.Connection lives in brain/ui/persistence.py; no
          class field is typed sqlite3.Connection; no top-level
          function returns sqlite3.Connection.

Evidence: persistence_session_resource_audit.py confirms
          session_store_config is in _ALLOWED_SESSION_ATTRS,
          SessionStoreConfig field types are exactly (pathlib.Path,
          int, str), runs the existing I-UI-10 resource-free audit
          on a session carrying a SessionStoreConfig, performs a
          save through the config and confirms the session gains
          no _conn attribute, performs an AST audit over
          brain/ui/persistence.py to reject module-level
          sqlite3.connect bindings, Connection-typed class fields,
          Connection-returning top-level functions, and any
          'conn' / 'connection' / 'cursor' session slot, and
          behaviourally confirms no OperatorSession field is a
          sqlite3.Connection / Cursor after a save.

Rows:     I-PERSIST-11 STRUCTURAL, I-PERSIST-14 STRUCTURAL.
Status:   PASS.
```

## 11. Persistence module static audit (I-PERSIST-12)

```text
Audit:    An AST audit over brain/ui/persistence.py confirms
          imports are confined to the documented seam set:
          sqlite3, pathlib, datetime, fractions, dataclasses,
          typing, types, brain.io_types, brain.tlica.builders /
          profile / msi / ptcns, brain.development.text_stream,
          brain.ui.session, brain.ui.commands, and brain.tick (for
          BrainState and assert_state_invariants only). The
          module imports neither pickle, shelve, marshal, dill,
          cloudpickle, joblib, subprocess, socket, urllib, http,
          requests, nor curses. The audit rejects calls to eval /
          exec / compile / __import__ / importlib.import_module /
          importlib.reload / atexit.register / os.system / os.popen
          / os.exec* / os.spawn* / os.fork / os.forkpty / os.kill.
          Importing or calling the tick callable from brain.tick
          (from brain.tick import tick, brain.tick.tick(...), and
          any call target named tick(...)) is forbidden. Module-
          level statements are restricted to imports, constants,
          function defs, and class defs (plus a module docstring).

Evidence: persistence_static_audit.py implements the AST audit
          described above. The audit's allowlist treats
          brain.tlica.builders / profile / msi / ptcns explicitly
          (the brain.tlica root is otherwise forbidden) and
          brain.tick imports are constrained to {BrainState,
          assert_state_invariants}. brain/ui/fixtures/tui_smoke.py
          (I-UI-07) has been extended with narrow per-file
          exemptions so brain/ui/persistence.py is allowed to
          import brain.tlica.* at module level (the I-PERSIST-12
          audit is the canonical scope-check here) and
          persistence_*.py fixtures are allowed tempfile imports
          for throw-away SQLite databases. Every other
          forbidden-surface rule still applies.

Row:      I-PERSIST-12 STRUCTURAL.
Status:   PASS.
```

## 12. OBSERVED cold-start walk (I-PERSIST-15)

```text
Audit:    PHASE3_9_PERSISTENCE_DRY_RUN.md documents a deterministic
          scripted operator session (/stream hello world,
          /stream-promote promo-strm-chunk-1, /step, /save-session;
          quit; relaunch with --load-session) and verifies the
          restored profile / MSI / PtCns / ContentRegistry /
          tick_counter / stream_history / stream_chunk_serial /
          stream_candidates match the saved state field-for-field.
          The row is OBSERVED and cannot fail the runner.

Documented walk: PHASE3_9_PERSISTENCE_DRY_RUN.md sections 3-7.

Row:      I-PERSIST-15 OBSERVED.
Status:   OBSERVED (audit-cited; not a runner gate). The walk
          itself is reproducible; the dry-run document captures
          the exact resulting numbers.
```

## 13. NOT-EXERCISED autosave guard (I-PERSIST-16)

```text
Audit:    No autosave path exists in Phase 3.9. /save-session and
          /load-session are the only persistence routes, both
          explicit operator commands. brain/ui/persistence.py is
          not reachable from /step, /stream, /stream-promote, or
          any other tick-adjacent dispatch path. No atexit /
          signal / threading / asyncio autosave hook is
          registered. Autosave absence is structurally enforced by
          persistence_static_audit.py, which rejects atexit,
          threading, asyncio, and signal imports plus
          atexit.register / importlib calls in the persistence
          module. The catalog row exists so a future campaign
          cannot quietly add filesystem autosave without
          registering coverage.

Evidence: persistence_static_audit.py (I-PERSIST-12 fixture)
          contains the autosave-hook prohibitions. brain/ui/
          session.py routes /save-session through the explicit
          SAVE_SESSION dispatcher only; no /step / /stream /
          /stream-promote handler imports brain.ui.persistence or
          calls save_session / load_session.

Row:      I-PERSIST-16 NOT-EXERCISED.
Status:   PASS (placeholder is in place; no path exists).
```

## 14. Interaction with prior phases

```text
The Phase 3.9 persistence layer composes cleanly with every
existing campaign:

- Phase 3.6 Reflective Inspection: ReflectiveInspectionSnapshot
  remains a read-only view-model; nothing in brain/ui/persistence.py
  imports it. Operator transcripts, output histories, worldlet
  histories, and ProtoBASIC histories are not persisted in v1
  (deferred).

- Phase 3.7 Text Stream Ingress: TextStreamChunk and
  TextStreamHistory persist exactly through
  make_text_stream_chunk; the substrate's COGITO_ID rejection,
  bounded-text policy, and copy-on-write history are preserved
  unchanged.

- Phase 3.8 Operator Stream Interaction: /stream, /stream-summary,
  /stream-candidates, /stream-promote, and /step are unchanged.
  The session's stream_history and stream_candidates fields
  participate in save/load directly; no Phase 3.8 dispatcher was
  modified.

- Phase 3.8b LLM Runtime Toggle: the persistence layer carries no
  LLM client. The static audit forbids brain.llm imports. /step
  remains the only tick route; the resolved LLMClient continues
  to enter tick() through the existing run_curses(client=...,
  ...) seam. Persistence does not interact with --llm-mode.

- /step remains the only tick route across the whole repo;
  /save-session and /load-session do NOT call tick() (drives
  I-PERSIST-09).
```

## 15. Full gate

```text
Required final validation (run on the post-Step-11 tree):

  python3 -m tools.catalog counts
    -> Banner / Actual / Expected agree on
       REQUIRED=187, STRUCTURAL=69, NOT-EXERCISED=10,
       DEFERRED=12, OBSERVED=13.

  python3 -m tools.citations verify
    -> Verified 100 citations. All catalog citations resolve in
       lean_reference/.

  python3 -m tools.import_audit
    -> I-PCE-05: agency.py is clean of pce imports.

  python3 -m brain.invariants run
    -> 263 rows checked
       REQUIRED green: 187 · REQUIRED red: 0
       STRUCTURAL green: 69 · STRUCTURAL red: 0
       OBSERVED: 7 pass / 0 fail
       gate failures: 0

  bash tools/check_all.sh
    -> All checks passed.

All gates green.
```

## 16. Remaining deferred work

The following items are explicitly deferred from Phase 3.9 v1 and
remain available targets for a future campaign:

```text
- Autosave (NOT-EXERCISED; would require a dedicated catalog row
  family and explicit policy artifact).
- Migrations between schema versions (only v1 is defined; any
  unknown schema_version is a hard local error today).
- Multi-profile / multi-user persistence.
- Network-backed persistence / replication / backup subsystem.
- Full TickRecord / event-log replay.
- Persistence of OperatorTranscript, OutputHistory, WorldletHistory,
  ProtoBasicHistory, ExpressionHistory,
  ReflectiveInspectionSummary.
- Persistence of LLM client state, cache contents, or runtime mode.
- Persistence of curses configuration / terminal state.
- A reviewed save/export policy for paths outside the configured
  session DB (none authorized today).
```

Each of these is a separate campaign-class decision. None blocks
the Phase 3.9 PR; each requires its own synthesis / kickoff /
corrigenda / catalog-patch-plan sequence.

## 17. Verdict

```text
PASS

Phase 3.9 Persistent Session Store is implemented per the accepted
synthesis, kickoff, corrigenda, and catalog patch plan (including
the user's review-gate amendment that locked the 11-fixture roster,
the brain.tick.BrainState typed-import allowance, the
tick-callable forbiddance, and the I-PERSIST-16
no-dedicated-fixture wording). All I-PERSIST-01..14 rows are
green; I-PERSIST-15 OBSERVED is documented in
PHASE3_9_PERSISTENCE_DRY_RUN.md; I-PERSIST-16 NOT-EXERCISED guard
is in place and structurally enforced. The Phase 3.7 / 3.8 / 3.8b
operator surface is unchanged; /step remains the only tick route;
COGITO_ID remains reserved; offline remains the default LLM mode.
The recommended next step is the final PR (Step 13).
```
