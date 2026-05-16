# PHASE3_9_PERSISTENT_SESSION_STORE_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in
`PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md` to concrete
catalog rows, statuses, file budget, count delta, fixture roster,
and pending-registration mechanics. This is a planning artifact
only. It does not apply catalog rows, edit `tools/catalog.py`, add
runtime modules, add fixtures, change generated catalog IDs, alter
`INVARIANT_CATALOG.md`, change `brain/invariants.py`, or update
README as though implementation exists.

Verdict for the Step 6 review gate:

```text
COHERENT - READY FOR REVIEW GATE
```

## 2. Baseline

```text
Catalog version:  v0.16
REQUIRED:         178
STRUCTURAL:        64
NOT-EXERCISED:      9
DEFERRED:          12
OBSERVED:          12
Total tabular:    275
Total fixtures:    91
```

Required latest merged campaign:

```text
Fast Safe Text Interaction (PR #6, merged 2026-05-15)
  Phase 3.6 Reflective Inspection        PASS
  Phase 3.7 Text Stream Ingress           PASS
  Phase 3.8 Operator Stream Interaction   PASS
  Phase 3.8b LLM Runtime Toggle           PASS
  Step 26 dry run                         PASS
```

Accepted planning artifacts:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md
PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md
PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md
PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md
```

## 3. Patch Impact

```text
+ 9 REQUIRED
+ 5 STRUCTURAL
+ 0 DEFERRED
+ 1 NOT-EXERCISED
+ 1 OBSERVED
```

Expected counts after the accepted patch:

```text
Catalog version:  v0.17
REQUIRED:         187
STRUCTURAL:        69
NOT-EXERCISED:     10
DEFERRED:          12
OBSERVED:          13
Total tabular:    291
```

The new I-PERSIST row family contributes 16 rows total.

## 4. Row Family Thesis

Row family:

```text
I-PERSIST-*
```

Rationale for the family spelling:

```text
- Existing catalog family prefixes are I-<UPPERCASEMODULE>-NN; the
  parser in tools/catalog.py recognizes a single uppercase token
  between the first and last hyphen.
- I-PERSIST-* keeps the family name short, readable, and unique
  against existing families (I-UI-, I-UISTRM-, I-LLMTOG-,
  I-STRM-, I-REF-, I-EXP-, I-REPL-, I-WLD-, I-OUT-, I-DEV-,
  I-FRAME-, I-SBX-, I-CAT-, I-ISO-, I-PCE-, I-AGN-, I-AFF-,
  I-APRJ-, I-PMAP-, I-PROF-, I-PWS-, I-MSI-, I-MOD-, I-IBND-,
  I-INT-, I-PRES-, I-PTC-, I-RT-, I-TRACE-, I-TRJ-, I-TOCE-,
  I-BHV-, I-LLM-).
- I-PERSIST-* maps directly to the brain/ui/persistence.py module
  and the brain/ui/fixtures/persistence_*.py fixture file naming.
```

Core commitments:

```text
The Persistent Session Store gives the operator typed, transactional,
schema-versioned SQLite persistence over the existing BrainState +
OperatorSession surface.

Save and load operate only through the configured session DB path.

Save is a single transactional write: BEGIN IMMEDIATE, write the
documented v1 schema rows, COMMIT, return SaveSessionResult. Any
failure rolls back. The live OperatorSession is unchanged on
failure.

Load is a read-only open (sqlite3 uri mode=ro) that reads typed
rows, builds Persistent*Snapshot records, reconstructs kernel
state through public builders, runs invariant assertions, and
returns the candidate session only if every step succeeds. Failed
loads preserve the live session.

Fractions persist exactly as integer numerator / denominator pairs.
No REAL / NUMERIC / FLOAT / DOUBLE column stores kernel numeric
data.

COGITO_ID is reserved on load: a persisted row attempting to bind
COGITO_ID to a non-canonical value raises PersistenceError.

The persistence module imports only the documented seam set:
sqlite3, pathlib, datetime, fractions, dataclasses, typing,
brain.io_types, brain.tlica.builders, brain.tlica.profile,
brain.tlica.msi, brain.tlica.ptcns, brain.development.text_stream,
brain.ui.session, brain.ui.commands. It imports neither pickle
nor any execution / network / subprocess / curses path.

No autosave is authorized in Phase 3.9. /save-session and
/load-session are explicit operator commands; no tick-adjacent
dispatch path calls the save helper.
```

## 5. Row Table

All rows use the `I-PERSIST-*` family. Owning module is
`brain/ui/persistence.py` unless noted.

### 5.1 REQUIRED rows

```text
I-PERSIST-01  SQLite schema is finite and closed.
               brain/ui/persistence.py defines exactly the v1
               tables (meta, content_registry, profile_values,
               msi_contents, msi_threshold, ptcns_eval,
               session_state, stream_chunks, stream_candidates)
               with the documented columns, NOT NULL constraints,
               PRIMARY KEY / UNIQUE / FOREIGN KEY structure, and
               CHECK constraints (rho_den > 0, den > 0,
               msi_threshold.id = 1). No additional kernel-state
               table exists in v1.
               Fixture: persistence_schema.py

I-PERSIST-02  Unknown schema_version is rejected on load.
               load_session reads the meta.schema_version row,
               coerces to int, and raises PersistenceError with a
               bounded printable message when the value is not in
               SUPPORTED_SCHEMA_VERSIONS. The live session is
               unchanged.
               Fixture: persistence_failed_load.py

I-PERSIST-03  Fractions persist exactly as integer pairs.
               save_session writes ScalarProfile values and the
               MSI threshold as (num INTEGER, den INTEGER) rows;
               load_session reconstructs them as Fraction(num,
               den) and the resulting Fraction values are
               byte-for-byte equal to the originals under Fraction
               __eq__. No float() / Decimal / REAL column appears
               in any kernel-numeric path.
               Fixture: persistence_save_roundtrip.py

I-PERSIST-04  COGITO_ID cannot be overwritten by persisted data.
               A profile_values row with content_id = COGITO_ID
               and rho != 1, a missing msi_contents COGITO_ID row,
               or a ptcns_eval row mapping COGITO_ID to a non-
               PRESERVE eval, raises PersistenceError on load.
               The live OperatorSession is unchanged. Save of a
               session with COGITO_ID at value 1 round-trips
               exactly.
               Fixture: persistence_cogito_protected.py

I-PERSIST-05  Load reconstructs kernel state through public
               builders / constructors only.
               brain/ui/persistence.py builds the candidate
               OperatorSession by calling make_profile_with_cogito,
               make_msi, make_ptcns, ContentRegistry(...),
               BrainState(profile=, msi=, ptcns=, registry=),
               make_text_stream_chunk, TextStreamHistory(chunks=
               ...), make_stream_promotion_candidate, and
               OperatorSession(state=, ...). It performs no
               attribute / private-field assignment on any kernel
               record, no object.__setattr__ on frozen records,
               no pickle / shelve / marshal load, and no
               json.loads-as-dict-direct-into-constructor on
               authoritative kernel state.
               Fixture: persistence_load_constructor_only.py

I-PERSIST-06  Load runs invariant assertions before returning.
               After assembling the candidate state, load_session
               invokes the existing invariant-assertion entrypoint
               (assert_state_invariants or its current equivalent)
               on the candidate BrainState. If the assertion
               raises, load_session raises PersistenceError and
               returns no candidate session.
               Fixture: persistence_load_invariants.py

I-PERSIST-07  Failed save preserves the live session.
               If any sqlite3.IntegrityError / OperationalError /
               DatabaseError or constructor error is raised mid-
               save, the transaction rolls back and the live
               OperatorSession is unchanged. A subsequent
               successful save into the same DB produces a clean
               v1-shaped snapshot.
               Fixture: persistence_failed_save.py

I-PERSIST-08  Failed load preserves the live session.
               Missing DB, wrong file type, missing meta rows,
               unknown schema_version, FOREIGN KEY violations,
               malformed Fraction pairs, over-bound text, and
               constructor / invariant rejection all surface as
               PersistenceError. In each case the live
               OperatorSession field-for-field equals the pre-call
               session, and the on-disk DB file is unchanged
               (load runs in sqlite3 uri mode=ro).
               Fixture: persistence_failed_load.py

I-PERSIST-09  /save-session and /load-session are bounded and
               local, and do not call tick().
               LocalCommandLine.parse accepts /save-session and
               /load-session as closed verbs and rejects trailing
               arguments. _dispatch_save_session and
               _dispatch_load_session call save_session /
               load_session, surface bounded printable status /
               error text on OperatorSession, and never invoke
               tick(). The dispatchers fail closed on a missing
               session_store_config, leaving live state untouched.
               Fixture: persistence_commands.py
```

### 5.2 STRUCTURAL rows

```text
I-PERSIST-10  Save transaction is atomic.
               save_session uses sqlite3.connect(...) with
               isolation_level=None and an explicit BEGIN
               IMMEDIATE / COMMIT pair. A mid-save failure
               triggers ROLLBACK and leaves no orphaned rows
               from the failed attempt; the next successful save
               into the same DB produces a snapshot
               indistinguishable from one made without the
               injected failure.
               Fixture: persistence_atomic_save.py

I-PERSIST-11  Session resource-free with SessionStoreConfig.
               OperatorSession may carry an Optional[
               SessionStoreConfig]. _ALLOWED_SESSION_ATTRS adds
               "session_store_config". SessionStoreConfig's
               fields are bounded (pathlib.Path, int, str). No
               OperatorSession or SessionStoreConfig field
               contains an sqlite3.Connection,
               sqlite3.Cursor, subprocess handle, socket, file
               object, callable, curses object, or LLM client.
               Fixture: persistence_session_resource_audit.py

I-PERSIST-12  Persistence module static audit rejects forbidden
               side effects.
               brain/ui/persistence.py imports are confined to
               the documented seam set (sqlite3, pathlib,
               datetime, fractions, dataclasses, typing,
               brain.io_types, brain.tlica.builders,
               brain.tlica.profile, brain.tlica.msi,
               brain.tlica.ptcns,
               brain.development.text_stream,
               brain.ui.session, brain.ui.commands). The module
               imports no pickle, shelve, marshal, dill,
               cloudpickle, joblib, subprocess, socket, urllib,
               http, requests, or curses. It contains no
               importlib.import_module, __import__, eval(,
               exec(, compile(, atexit.register, threading,
               asyncio, or signal handler. Module-level
               statements are limited to imports, constants,
               function defs, and class defs (plus a module
               docstring).
               Fixture: persistence_static_audit.py

I-PERSIST-13  No kernel-numeric REAL column in the schema.
               The schema declared in brain/ui/persistence.py
               uses INTEGER for every kernel-numeric value
               (rho_num, rho_den, msi_threshold.num,
               msi_threshold.den, tick_at_event), TEXT for every
               identifier / enum name / printable text /
               timestamp, and contains no REAL / NUMERIC /
               FLOAT / DOUBLE column.
               Fixture: persistence_schema.py

I-PERSIST-14  No long-lived sqlite3.Connection on
               OperatorSession.
               Save and load helpers use `with sqlite3.connect(
               ...) as conn:` and close the connection on the
               with-block exit. The static audit asserts that
               brain/ui/persistence.py contains no module-level
               connection, no class field of type
               sqlite3.Connection, and that no function returns
               a sqlite3.Connection to an external caller. No
               OperatorSession field stores an open connection.
               Fixture: persistence_session_resource_audit.py
```

### 5.3 OBSERVED row

```text
I-PERSIST-15  Cold-start continuity dry run is inspectable.
               PHASE3_9_PERSISTENCE_DRY_RUN.md documents a
               deterministic scripted session (/stream hello
               world, /stream-promote <id>, /step, /save-session,
               relaunch with --load-session, verify restored
               profile / MSI / PtCns / ContentRegistry /
               tick_counter / stream_history / stream_chunk_serial
               / stream_candidates). The row is OBSERVED and
               cannot fail the runner.
               Fixture: persistence_dry_run.py or cited from
                        the Step 11 dry-run document.
```

### 5.4 NOT-EXERCISED row

```text
I-PERSIST-16  Autosave path is NOT-EXERCISED.
               No autosave path exists in Phase 3.9. /save-session
               and /load-session are the only persistence routes;
               they are explicit operator commands. brain/ui/
               persistence.py is not reachable from /step, /stream,
               /stream-promote, or any other tick-adjacent
               dispatch path. No atexit / signal / threading /
               asyncio autosave hook is registered. Any future
               autosave path requires an explicit reviewed policy
               artifact, a dedicated catalog row, bounded fixtures,
               and a new stop condition.
               Fixture: none. The placeholder is held by the
                        persistence_autosave_absent.py audit (a
                        STRUCTURAL static rejection check that
                        complements this NOT-EXERCISED row); the
                        Step 7 patch may either keep that audit
                        separately or fold it into
                        persistence_static_audit.py.
```

## 6. Fixture Roster

```text
I-PERSIST-01  persistence_schema.py
I-PERSIST-02  persistence_failed_load.py
I-PERSIST-03  persistence_save_roundtrip.py
I-PERSIST-04  persistence_cogito_protected.py
I-PERSIST-05  persistence_load_constructor_only.py
I-PERSIST-06  persistence_load_invariants.py
I-PERSIST-07  persistence_failed_save.py
I-PERSIST-08  persistence_failed_load.py
I-PERSIST-09  persistence_commands.py
I-PERSIST-10  persistence_atomic_save.py
I-PERSIST-11  persistence_session_resource_audit.py
I-PERSIST-12  persistence_static_audit.py
I-PERSIST-13  persistence_schema.py
I-PERSIST-14  persistence_session_resource_audit.py
I-PERSIST-15  OBSERVED; persistence_dry_run.py or audit-cited
I-PERSIST-16  NOT-EXERCISED; no dedicated fixture
                (folds into persistence_static_audit.py or remains
                 placeholder-only)
```

Fixture file delta: **10** new files.

```text
brain/ui/fixtures/persistence_schema.py
brain/ui/fixtures/persistence_failed_load.py
brain/ui/fixtures/persistence_save_roundtrip.py
brain/ui/fixtures/persistence_cogito_protected.py
brain/ui/fixtures/persistence_load_constructor_only.py
brain/ui/fixtures/persistence_load_invariants.py
brain/ui/fixtures/persistence_failed_save.py
brain/ui/fixtures/persistence_commands.py
brain/ui/fixtures/persistence_atomic_save.py
brain/ui/fixtures/persistence_session_resource_audit.py
brain/ui/fixtures/persistence_static_audit.py
```

That is 11 fixture modules (one — persistence_failed_load.py —
serves two rows; one — persistence_schema.py — serves two rows;
one — persistence_session_resource_audit.py — serves two rows).
The OBSERVED row (I-PERSIST-15) is fixture-cited rather than
runner-gated; the NOT-EXERCISED row (I-PERSIST-16) needs no
dedicated module.

If the Step 8 implementation combines persistence_failed_save.py
and persistence_failed_load.py into one persistence_failure.py
module, or folds the I-PERSIST-13 row's check into
persistence_save_roundtrip.py, the catalog patch must update this
roster explicitly before landing rows.

## 7. File Budget

Modified files for Step 7 catalog patch:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional marker file (the corrigenda locked module placement at
`brain/ui/persistence.py`, but Step 7 may land an empty
placeholder module so the catalog row imports do not fail):

```text
brain/ui/persistence.py  (empty placeholder; full implementation in Step 8)
```

Expected modified / new files for Step 8 implementation:

```text
brain/ui/persistence.py
brain/ui/fixtures/persistence_schema.py
brain/ui/fixtures/persistence_failed_load.py
brain/ui/fixtures/persistence_save_roundtrip.py
brain/ui/fixtures/persistence_cogito_protected.py
brain/ui/fixtures/persistence_load_constructor_only.py
brain/ui/fixtures/persistence_load_invariants.py
brain/ui/fixtures/persistence_failed_save.py
brain/ui/fixtures/persistence_commands.py
brain/ui/fixtures/persistence_atomic_save.py
brain/ui/fixtures/persistence_session_resource_audit.py
brain/ui/fixtures/persistence_static_audit.py
brain/invariants.py                    (FIXTURE_MODULES extension)
```

Expected modified files for Step 9 reconstruction implementation:

```text
brain/ui/persistence.py        (load + save bodies, builder routing)
brain/ui/session.py            (Optional[SessionStoreConfig] field,
                                _ALLOWED_SESSION_ATTRS update)
```

Expected modified files for Step 10 command integration:

```text
brain/ui/commands.py           (OperatorCommand.SAVE_SESSION,
                                OperatorCommand.LOAD_SESSION,
                                SaveSessionPayload, LoadSessionPayload)
brain/ui/command_line.py       (/save-session, /load-session verbs)
brain/ui/session.py            (_dispatch_save_session,
                                _dispatch_load_session)
brain/ui/__main__.py           (--session-db, --load-session,
                                --no-load-session flags + launch
                                wiring)
brain/ui/render.py             (optional persistence-status display)
README.md                      (document save/load AFTER impl)
```

`README.md` should be updated only after the accepted implementation
exists. Step 7 should not document unimplemented persistence
commands as available.

Explicitly excluded unless a future accepted plan reopens them:

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

## 8. Catalog Patch Mechanics (Step 7)

```text
1. Add the 16 new I-PERSIST-* row entries to INVARIANT_CATALOG.md
   under a new "### Phase 3.9 Persistent Session Store invariants"
   section.

2. Add a v0.17 catalog-version banner above v0.16 documenting the
   +9 REQUIRED / +5 STRUCTURAL / +1 NOT-EXERCISED / +1 OBSERVED
   expansion (delta total = 16; new family I-PERSIST-01..16).

3. Update the summary counts in INVARIANT_CATALOG.md to:
   REQUIRED 187, STRUCTURAL 69, NOT-EXERCISED 10, DEFERRED 12,
   OBSERVED 13.

4. Update tools/catalog.py EXPECTED_COUNTS to the same values and
   refresh the banner-comment block to cite Phase 3.9 v0.17.

5. Run `python3 -m tools.catalog generate-ids` to refresh
   brain/_catalog_ids.py with the new I-PERSIST entries.

6. Add _PHASE3_9_PENDING_ROWS in brain/invariants.py with every
   REQUIRED and STRUCTURAL row that is not yet backed by a real
   fixture (i.e. I-PERSIST-01..14). I-PERSIST-15 (OBSERVED) and
   I-PERSIST-16 (NOT-EXERCISED) do not participate in I-CAT-01
   coverage and are not pending.

7. Optionally add an empty brain/ui/persistence.py marker so the
   future fixture imports have a target module. Implementation
   begins in Step 8.

8. Update README.md catalog-version block to v0.17 and the
   companion-docs section to add the new corrigenda / catalog
   patch plan entries (README command documentation for
   /save-session and /load-session is deferred to Step 10).

9. Validate with:
     python3 -m tools.catalog counts
     python3 -m tools.catalog generate-ids
     python3 -m tools.catalog counts
     python3 -m brain.invariants run
     bash tools/check_all.sh

10. Step 7 should commit and push after count validation only.
    It should not implement save/load behavior, parser verbs,
    CLI flags, or dispatcher routing.
```

## 9. Implementation Mechanics (Step 8 onward)

The later implementation steps should drain `_PHASE3_9_PENDING_ROWS`
by landing fixture-backed checks in a controlled order:

```text
Step 8 (SQLite schema + typed records):
  1. Extend brain/ui/persistence.py with SCHEMA_VERSION_V1,
     SUPPORTED_SCHEMA_VERSIONS, SessionStoreConfig, the
     Persistent*Snapshot records, PersistenceError,
     SaveSessionResult, LoadSessionResult.
  2. Add the persistence_schema.py and
     persistence_static_audit.py fixtures.
  3. Drain I-PERSIST-01, I-PERSIST-12, I-PERSIST-13.

Step 9 (save / load reconstruction):
  4. Implement save_session and load_session bodies in
     brain/ui/persistence.py.
  5. Extend brain/ui/session.py with the
     Optional[SessionStoreConfig] field and update
     _ALLOWED_SESSION_ATTRS.
  6. Add persistence_save_roundtrip.py,
     persistence_load_constructor_only.py,
     persistence_load_invariants.py,
     persistence_cogito_protected.py,
     persistence_failed_save.py, persistence_failed_load.py,
     persistence_atomic_save.py,
     persistence_session_resource_audit.py.
  7. Drain I-PERSIST-02..08, I-PERSIST-10..11, I-PERSIST-14.

Step 10 (CLI flags + explicit commands):
  8. Extend brain/ui/commands.py with SAVE_SESSION /
     LOAD_SESSION + payload records.
  9. Extend brain/ui/command_line.py with the closed verbs.
  10. Extend brain/ui/session.py with the dispatch methods.
  11. Extend brain/ui/__main__.py with --session-db /
      --load-session / --no-load-session.
  12. Add persistence_commands.py.
  13. Drain I-PERSIST-09.

Step 11 (dry run):
  14. Write PHASE3_9_PERSISTENCE_DRY_RUN.md; cite from
      I-PERSIST-15 (OBSERVED).

Step 12 (full audit):
  15. Write PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md.
  16. Run the full gate.

Step 13 (final PR).
```

Expected targeted validations during Steps 8-10:

```bash
python3 -m brain.invariants run --id I-PERSIST
python3 -m brain.invariants run --id I-UI
bash tools/check_all.sh
```

## 10. Accepted Constants

```text
SCHEMA_VERSION_V1                 = 1
SUPPORTED_SCHEMA_VERSIONS         = frozenset({SCHEMA_VERSION_V1})
DEFAULT_SESSION_DB_PATH           = (no global default; the operator
                                     must supply --session-db; the
                                     campaign body refers to
                                     brain/session.sqlite3 only as a
                                     recommended location)
CATALOG_VERSION_STAMP             = "v0.17" (saved in meta when
                                     Phase 3.9 v0.17 has landed; the
                                     Step 7 marker uses the value
                                     current at save time)
PROFILE_VALUES_TABLE_NAME         = "profile_values"
MSI_CONTENTS_TABLE_NAME           = "msi_contents"
MSI_THRESHOLD_TABLE_NAME          = "msi_threshold"
PTCNS_EVAL_TABLE_NAME             = "ptcns_eval"
CONTENT_REGISTRY_TABLE_NAME       = "content_registry"
SESSION_STATE_TABLE_NAME          = "session_state"
STREAM_CHUNKS_TABLE_NAME          = "stream_chunks"
STREAM_CANDIDATES_TABLE_NAME      = "stream_candidates"
META_TABLE_NAME                   = "meta"
META_SCHEMA_VERSION_KEY           = "schema_version"
META_CATALOG_VERSION_KEY          = "catalog_version"
META_CREATED_AT_KEY               = "created_at"
META_UPDATED_AT_KEY               = "updated_at"
SESSION_STATE_TICK_COUNTER_KEY    = "tick_counter"
SESSION_STATE_STREAM_SERIAL_KEY   = "stream_chunk_serial"
```

These constants are module-private in `brain/ui/persistence.py` and
are referenced by the persistence_schema.py fixture for parity.

Existing constants reused from upstream modules:

```text
STREAM_TEXT_MAX_LEN              = 1024  (brain/development/text_stream.py)
STREAM_PROVENANCE_MAX_LEN        =   64  (brain/development/text_stream.py)
STREAM_PROMOTION_MAX             =   64  (brain/development/text_stream.py)
MAX_STATUS_TEXT_LEN              =  240  (brain/ui/session.py)
LOCAL_CMD_MAX_ERROR_LEN          =  240  (brain/ui/command_line.py)
```

If `brain/ui/persistence.py` duplicates any of these, the
persistence_schema.py or persistence_static_audit.py fixture must
include a parity check against the owning module constants.

## 11. Non-Goals To Preserve

```text
no raw text -> COGITO_ID
no raw text -> BrainState direct mutation
no pickle / shelve / marshal / dill / cloudpickle / joblib as a
  persistence format
no JSON / TOML / YAML as the authoritative kernel-state format
no REAL / NUMERIC / FLOAT / DOUBLE columns for kernel numeric data
no sqlite3.Connection on OperatorSession
no autosave from /step, /stream, /stream-promote, or any other
  tick-adjacent dispatch path
no network-backed persistence
no multi-profile / multi-user persistence
no migrations between schema versions in v1
no persistence of LLM client / cache / runtime mode
no persistence of operator transcripts beyond bounded session-local
  state
no persistence of curses configuration / terminal state
no modifications to tick() semantics
no typed operator commands outside /save-session and /load-session
no save / export path outside the configured session DB
no real LLM call below the explicit Phase 3.8b toggle (Phase 3.9
  does not alter the toggle)
```

## 12. Review Gate

Stop after this plan is committed and pushed.

```text
Do not apply v0.17 catalog rows.
Do not edit tools/catalog.py.
Do not edit brain/_catalog_ids.py.
Do not edit brain/invariants.py.
Do not add persistence fixtures.
Do not create brain/ui/persistence.py (other than as the optional
  empty marker described in Section 8, and only if Step 7 is
  reached).
Do not edit brain/ui/__main__.py / commands.py / command_line.py /
  session.py / render.py as if persistence is implemented.
Do not update README as if /save-session and /load-session exist.
Do not proceed to Step 7 until this plan is explicitly accepted.
```

## Conclusion

This plan is coherent and ready for review. The next campaign step,
if accepted, is:

```text
Step 7 - Apply Phase 3.9 catalog patch
```

The Phase 3.9 catalog patch transitions the catalog from v0.16
(178 / 64 / 9 / 12 / 12) to v0.17 (187 / 69 / 10 / 12 / 13) by
adding the I-PERSIST-01..16 row family. No runtime / fixture code
is written until Step 8.
