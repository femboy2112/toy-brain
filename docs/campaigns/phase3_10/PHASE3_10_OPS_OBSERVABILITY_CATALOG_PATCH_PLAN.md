# PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in
`PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md` to
concrete catalog rows, statuses, file budget, count delta, fixture
roster, and pending-registration mechanics for tracks A
(Operational Hardening) and B (Persistence Observability). This is
a planning artifact only. It does not apply catalog rows, edit
`tools/catalog.py`, add runtime modules, add fixtures, change
generated catalog IDs, alter `INVARIANT_CATALOG.md`, change
`brain/invariants.py`, or update README as though implementation
exists.

Phase 3.10c (Autosave Policy) catalog rows are NOT included in
this plan. They are addressed at Step 15 (autosave catalog patch
plan) after Step 11 audit is PASS.

Verdict for the Step 6 review gate:

```text
COHERENT - READY FOR REVIEW GATE A/B
```

## 2. Baseline

```text
Catalog version:  v0.17
REQUIRED:         187
STRUCTURAL:        69
NOT-EXERCISED:     10
DEFERRED:          12
OBSERVED:          13
Total tabular:    291
Total fixtures:   106
```

Required latest merged campaign:

```text
Phase 3.9 Persistent Session Store (PR #8, merged 2026-05-15)
  PASS
```

Accepted planning artifacts:

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_SYNTHESIS.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_KICKOFF.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md
```

## 3. Patch Impact

```text
+14 REQUIRED        (9 I-OPSHARDEN + 5 I-OBSERVE)
+10 STRUCTURAL      (5 I-OPSHARDEN + 5 I-OBSERVE)
+ 1 OBSERVED        (I-OBSERVE dry run)
+ 0 NOT-EXERCISED
+ 0 DEFERRED
```

Expected counts after the accepted Phase 3.10a/b patch:

```text
Catalog version:  v0.18
REQUIRED:         201
STRUCTURAL:        79
NOT-EXERCISED:     10
DEFERRED:          12
OBSERVED:          14
Total tabular:    316
```

Two new row families contribute 25 rows total:

```text
I-OPSHARDEN-01..14   (Phase 3.10a: 9 REQUIRED + 5 STRUCTURAL)
I-OBSERVE-01..11     (Phase 3.10b: 5 REQUIRED + 5 STRUCTURAL +
                       1 OBSERVED)
```

The existing I-PERSIST family (Phase 3.9, 16 rows) is unchanged.
The Phase 3.10a/b plan does NOT modify any existing I-PERSIST row.

## 4. Row Family Thesis

Row families:

```text
I-OPSHARDEN-*        Phase 3.10a Operational Hardening
I-OBSERVE-*          Phase 3.10b Persistence Observability
```

Rationale:

```text
- The corrigenda accepted Option K-B (split modules). I-OPSHARDEN
  maps to brain/ui/persistence_ops.py; I-OBSERVE maps to
  brain/ui/persistence_observe.py.
- Keeping the families separate makes the static audit and the
  fixture roster file-aligned: persistence_ops_static_audit covers
  every I-OPSHARDEN-* structural concern, and
  persistence_observe_static_audit covers every I-OBSERVE-*
  structural concern.
- The names are short, readable, and unique against existing
  prefixes (I-UI-, I-UISTRM-, I-LLMTOG-, I-STRM-, I-REF-, I-EXP-,
  I-REPL-, I-WLD-, I-OUT-, I-DEV-, I-FRAME-, I-SBX-, I-CAT-,
  I-ISO-, I-PCE-, I-AGN-, I-AFF-, I-APRJ-, I-PMAP-, I-PROF-,
  I-PWS-, I-MSI-, I-MOD-, I-IBND-, I-INT-, I-PRES-, I-PTC-, I-RT-,
  I-TRACE-, I-TRJ-, I-TOCE-, I-BHV-, I-LLM-, I-PERSIST-).
```

Core commitments:

```text
Phase 3.10a (Operational Hardening) gives the operator typed,
bounded, read-mostly visibility into the configured session DB
plus an explicit byte-faithful backup path. /session-status reads
in-memory only; /db-status and /db-verify open the DB in mode=ro
and never activate saved state; /db-backup uses
sqlite3.Connection.backup() to write to an explicit destination
that is not the source.

Phase 3.10b (Persistence Observability) gives the operator
bounded read-only summaries of saved state without loading it:
/db-summary, /profile-summary, /stream-db-summary, /db-diff. None
of these invoke a kernel builder; they read typed rows and
report exact-Fraction "num/den" strings, with explicit
"<missing>" markers on one-sided absence.

Both modules respect the Phase 3.9 envelope: no
sqlite3.Connection on OperatorSession, no thread / signal handler
/ atexit, no autosave entry point. Connection lifetime is
operation-scoped inside `with conn:` blocks.
```

## 5. Row Table (Phase 3.10a — I-OPSHARDEN)

Owning module is `brain/ui/persistence_ops.py` unless noted.

### 5.1 REQUIRED rows (9)

```text
I-OPSHARDEN-01  /session-status is read-only and bounded.
                 session_status(session) reads OperatorSession
                 fields only; no disk IO; no tick(); no curses; no
                 sqlite3.Connection. The returned
                 SessionStatusReport's string / integer fields are
                 bounded by OPS_REPORT_TEXT_MAX_LEN = 256 and
                 non-negativity. _dispatch_session_status surfaces
                 the report through status_message.
                 Fixture: persistence_ops_session_status.py

I-OPSHARDEN-02  /db-status is read-only mode=ro and bounded.
                 db_status(config) opens the configured DB through
                 sqlite3.connect("file:<path>?mode=ro", uri=True)
                 inside a `with conn:` block, reads meta rows,
                 closes the connection, returns a
                 DbStatusReport. On a missing DB, the report has
                 db_exists=False and empty schema/catalog/timestamp
                 fields; no sqlite3 error propagates.
                 Fixture: persistence_ops_db_status.py

I-OPSHARDEN-03  /db-verify reuses load_session and DROPS the
                 candidate.
                 db_verify(config) calls load_session(config) on
                 the configured DB, captures the returned
                 (candidate, LoadSessionResult), runs
                 assert_state_invariants on the candidate's
                 BrainState (already performed inside load_session
                 in the Phase 3.9 path; the catalog row asserts
                 the reuse), and immediately drops the candidate.
                 The live OperatorSession reference is unchanged
                 by id() before and after the call. The returned
                 DbVerifyReport has passed=True on success.
                 Fixture: persistence_ops_db_verify.py +
                          persistence_ops_db_verify_drop.py

I-OPSHARDEN-04  /db-verify failure preserves the live session.
                 A DB with a tampered row (rho_den=0, negative
                 schema_version, missing meta row, broken FK, etc.)
                 causes db_verify to catch the PersistenceError and
                 return a DbVerifyReport with passed=False and a
                 bounded error_text. The live OperatorSession
                 field-for-field equals the pre-call session. The
                 on-disk DB file byte-equals the pre-call file
                 (mode=ro guarantees this).
                 Fixture: persistence_ops_db_verify.py (failure
                          branches)

I-OPSHARDEN-05  /db-backup uses sqlite3.Connection.backup().
                 db_backup(config, dest_path, *, force=False) opens
                 the source DB in mode=ro and the destination DB
                 (sqlite3.connect(dest_path)) and calls
                 source.backup(dest) inside a `with` block. The
                 backup is page-faithful; load_session against the
                 destination yields the same PersistentSession-
                 Snapshot as the source. shutil.copyfile /
                 shutil.copy2 / shutil.copytree are NOT used and
                 the static audit (I-OPSHARDEN-12) rejects them.
                 Fixture: persistence_ops_db_backup.py

I-OPSHARDEN-06  /db-backup refuses to overwrite without --force.
                 If dest_path.exists() and force=False, db_backup
                 returns a DbBackupReport with succeeded=False,
                 overwritten=False, and a bounded error_text. No
                 destination write occurs. The same rejection
                 applies to /db-backup composer verb without --force.
                 With force=True, the existing destination is
                 overwritten and overwritten=True is reported.
                 Fixture: persistence_ops_db_backup_force.py

I-OPSHARDEN-07  /db-backup refuses URI-scheme destinations.
                 dest_path strings that parse as URIs (sqlite:,
                 file:, http:, https:, ftp:, ws:, wss:, data:,
                 gopher:, ssh:, git:) are rejected at argument
                 validation time. The rejection applies to both
                 the CLI flag (--db-backup PATH) and the composer
                 verb (/db-backup <path>). PersistenceError is
                 raised; no sqlite3 call is made; no destination
                 file is touched.
                 Fixture: persistence_ops_db_backup_dest_uri.py

I-OPSHARDEN-08  /db-backup never modifies the source DB.
                 The source connection uses mode=ro; the operation
                 is page-read-only on the source. A fixture
                 confirms that after a successful backup the source
                 DB file byte-equals the pre-call file. dest_path
                 == source_path is rejected as PersistenceError.
                 Fixture: persistence_ops_db_backup.py (source-
                          integrity branch)

I-OPSHARDEN-09  CLI short-circuit ordering and mutual exclusion +
                 exit codes.
                 brain/ui/__main__.py parses --db-status,
                 --db-verify, --db-backup PATH, and --db-backup-
                 force. The three new short-circuit flags are
                 mutually exclusive at argparse time. They
                 short-circuit AFTER --check-terminal and
                 --print-once but BEFORE parse_llm_runtime_args
                 and curses initialization. On success the
                 process exits with code 0; on failure with
                 code 1. Stderr is unused; bounded reports go
                 to stdout.
                 Fixture: persistence_ops_cli_short_circuit.py
                 (the fixture also covers I-OPSHARDEN-13's
                 exit-code mapping below)
```

### 5.2 STRUCTURAL rows (5)

```text
I-OPSHARDEN-10  Source connection mode=ro during backup.
                 db_backup opens the source connection through
                 sqlite3.connect("file:<source>?mode=ro", uri=True)
                 inside `with conn:`. The static audit confirms
                 the source open string contains "mode=ro" and the
                 destination open string does not.
                 Fixture: persistence_ops_static_audit.py
                          (subsumes; no dedicated fixture)

I-OPSHARDEN-11  Phase 3.10a defensive autosave-absent audit.
                 brain/ui/persistence_ops.py contains no autosave
                 entry point, no @atexit.register, no
                 threading.Thread / Timer, no asyncio loop, no
                 signal handler, no curses callback, no call site
                 that invokes save_session outside what is needed
                 for /save-session (which lives in the Phase 3.9
                 dispatcher, not in persistence_ops). The audit is
                 a static-AST + import-set check.
                 Fixture: persistence_ops_static_audit.py

I-OPSHARDEN-12  persistence_ops module static audit.
                 brain/ui/persistence_ops.py imports are confined
                 to the documented seam set:
                   sqlite3, dataclasses, datetime, fractions,
                   pathlib, typing, brain.io_types,
                   brain.tlica.profile (COGITO_ID only),
                   brain.ui.persistence,
                   brain.ui.session.
                 The module imports no pickle, shelve, marshal,
                 dill, cloudpickle, joblib, subprocess, socket,
                 urllib, http, requests, curses, brain.tick,
                 brain.tlica internals beyond builders consumed via
                 brain.ui.persistence, or brain.llm. It contains no
                 importlib.import_module / __import__ / eval(
                 / exec( / compile(. Module-level statements are
                 limited to imports, constants, function defs, and
                 class defs (plus a module docstring).
                 Fixture: persistence_ops_static_audit.py

I-OPSHARDEN-13  persistence_ops session resource audit.
                 No OperatorSession field added in Phase 3.10a.
                 After /session-status, /db-status, /db-verify,
                 /db-backup, the session field shape is identical
                 to the pre-call shape (no sqlite3.Connection /
                 Cursor / subprocess / socket / file object /
                 callable / curses object appears anywhere).
                 Fixture: persistence_ops_resource_audit.py

I-OPSHARDEN-14  Exit code mapping fixture.
                 --db-status returns code 0 if the report has
                 error_text == "" and db_exists, code 1 otherwise.
                 --db-verify returns code 0 if passed and code 1
                 otherwise. --db-backup returns code 0 if
                 succeeded and code 1 otherwise. The mapping is
                 captured in a small dispatcher in __main__.
                 Fixture: persistence_ops_cli_short_circuit.py
                          (subsumes; serves both I-OPSHARDEN-09
                          and I-OPSHARDEN-14)
```

## 6. Row Table (Phase 3.10b — I-OBSERVE)

Owning module is `brain/ui/persistence_observe.py` unless noted.

### 6.1 REQUIRED rows (5)

```text
I-OBSERVE-01    /db-summary reads in mode=ro; closed `with`
                 block; bounded report.
                 db_summary(config) opens the DB in mode=ro inside
                 `with conn:`, reads meta + per-table row counts
                 (profile_values, msi_contents, msi_threshold,
                 ptcns_eval, content_registry, stream_chunks,
                 stream_candidates), and returns a DbSummaryReport
                 with bounded string fields (
                 OPS_REPORT_TEXT_MAX_LEN = 256) and non-negative
                 integer fields. The msi_threshold field is the
                 exact "num/den" string.
                 Fixture: persistence_observe_db_summary.py

I-OBSERVE-02    /profile-summary returns exact-Fraction "num/den"
                 rows, COGITO first, deterministic sort.
                 profile_summary(config, *, row_cap=64) reads
                 profile_values in mode=ro, builds
                 tuple[ProfileSummaryRow, ...] sorted with
                 COGITO_ID first then content_id ASCII-ascending,
                 renders each Fraction(num, den) as the exact
                 "num/den" string (PROFILE_VALUE_STRING_MAX_LEN =
                 64), and truncates at row_cap with truncated=True
                 when the cap is hit. No float() / repr() /
                 str(Fraction) leakage; the fixture asserts the
                 render helper is a single named function reused
                 across reports.
                 Fixture: persistence_observe_profile_summary.py

I-OBSERVE-03    /stream-db-summary returns bounded head + tail.
                 stream_db_summary(config, *, head_cap=8,
                 tail_cap=8) reads stream_chunks and
                 stream_candidates row counts plus a head slice
                 (first head_cap chunks by ordinal) and a tail
                 slice (last tail_cap chunks by ordinal). Each
                 StreamDbSummaryRow's text_preview is bounded by
                 STREAM_TEXT_PREVIEW_MAX_LEN = 64; full chunk text
                 is never returned. truncated=True iff the chunk
                 count exceeds head_cap + tail_cap.
                 Fixture: persistence_observe_stream_db_summary.py

I-OBSERVE-04    /db-diff reports finite field enumeration;
                 "<missing>" on one-sided absence.
                 db_diff(session, config, *, row_cap=32) snapshots
                 the live session via the promoted public helper
                 snapshot_session(session), reads the saved
                 PersistentSessionSnapshot in mode=ro, diffs over
                 the finite field enumeration declared in source
                 ("profile.<content_id>", "msi.contents",
                 "msi.threshold", "ptcns_eval.<content_id>",
                 "registry.<content_id>", "tick_counter",
                 "stream_chunk_serial", "stream_history.count",
                 "stream_candidates.count"). DbDiffField.live and
                 .saved use exact "num/den" strings for kernel
                 numeric values, integer text for counters, and
                 the literal "<missing>" for one-sided absence.
                 The diff never invents defaults. truncated=True
                 iff diff_count > row_cap.
                 Fixture: persistence_observe_db_diff.py

I-OBSERVE-05    Observability commands never activate saved state
                 and never mutate live BrainState.
                 None of db_summary / profile_summary /
                 stream_db_summary / db_diff invokes any kernel
                 builder (make_profile_with_cogito, make_msi,
                 make_ptcns, ContentRegistry constructor,
                 BrainState constructor, make_text_stream_chunk,
                 TextStreamHistory constructor,
                 make_stream_promotion_candidate, OperatorSession
                 constructor). None mutates session.state /
                 session.stream_history / session.stream_candidates
                 / session.tick_counter / session.stream_chunk_
                 serial. The session __eq__ before and after each
                 command is True. (See I-OBSERVE-07 for the static
                 AST audit complement.)
                 Fixture: persistence_observe_db_summary.py
                          (subsumes; serves I-OBSERVE-01 and
                          I-OBSERVE-05's behavioral half)
```

### 6.2 STRUCTURAL rows (5)

```text
I-OBSERVE-06    persistence_observe module static audit.
                 brain/ui/persistence_observe.py imports are
                 confined to the documented seam set:
                   sqlite3, dataclasses, fractions, pathlib,
                   typing, brain.io_types,
                   brain.tlica.profile (COGITO_ID only),
                   brain.ui.persistence (typed records and the
                     promoted public snapshot_session helper),
                   brain.ui.session.
                 The module imports no pickle / shelve / marshal /
                 dill / cloudpickle / joblib, no subprocess /
                 socket / urllib / http / requests / curses, no
                 brain.tick, no brain.tlica internals beyond
                 what brain.ui.persistence re-exports, no
                 brain.llm. Module-level statements are limited
                 to imports, constants, function defs, and class
                 defs (plus a module docstring).
                 Fixture: persistence_observe_static_audit.py

I-OBSERVE-07    persistence_observe.py contains no builder call.
                 Static AST audit asserts brain/ui/persistence_
                 observe.py contains no call to
                 make_profile_with_cogito, make_msi, make_ptcns,
                 make_text_stream_chunk,
                 make_stream_promotion_candidate, no instantiation
                 of ContentRegistry, BrainState, TextStreamHistory,
                 or OperatorSession. This complements I-OBSERVE-05
                 (behavioral non-mutation) with structural
                 absence-of-construction.
                 Fixture: persistence_observe_no_builder_call.py

I-OBSERVE-08    persistence_observe session resource audit.
                 No OperatorSession field added in Phase 3.10b.
                 After /db-summary, /profile-summary,
                 /stream-db-summary, /db-diff, the session field
                 shape is identical to the pre-call shape; no
                 sqlite3.Connection / Cursor / subprocess /
                 socket / file object / callable / curses object
                 appears.
                 Fixture: persistence_observe_resource_audit.py

I-OBSERVE-09    Locked default row caps.
                 The module-level constants
                   PROFILE_SUMMARY_ROW_CAP = 64
                   STREAM_DB_SUMMARY_HEAD_CAP = 8
                   STREAM_DB_SUMMARY_TAIL_CAP = 8
                   DB_DIFF_ROW_CAP = 32
                   STREAM_TEXT_PREVIEW_MAX_LEN = 64
                   OPS_REPORT_TEXT_MAX_LEN = 256
                   PROFILE_VALUE_STRING_MAX_LEN = 64
                 are declared in brain/ui/persistence_observe.py
                 (or in a small shared constants module that the
                 corrigenda permits). A fixture asserts the values
                 and that the helpers default to them.
                 Fixture: persistence_observe_default_caps.py

I-OBSERVE-10    Phase 3.10b defensive autosave-absent audit.
                 brain/ui/persistence_observe.py contains no
                 autosave entry point, no @atexit.register, no
                 threading.Thread / Timer, no asyncio loop, no
                 signal handler, no curses callback, no call site
                 that invokes save_session. The audit is a
                 static-AST + import-set check.
                 Fixture: persistence_observe_static_audit.py
                          (subsumes; no dedicated fixture)
```

### 6.3 OBSERVED row (1)

```text
I-OBSERVE-11    Phase 3.10 ops/observability dry run is
                 inspectable.
                 PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md (Step 11)
                 documents a deterministic scripted session:
                   launch with --session-db PATH
                   /save-session
                   /db-status
                   /db-verify
                   /db-summary
                   /profile-summary
                   /stream-db-summary
                   /db-diff
                   /db-backup BACKUP_PATH
                   /quit
                   relaunch with --session-db BACKUP_PATH
                     --load-session
                   verify the loaded session matches the original
                 The row is OBSERVED and cannot fail the runner.
                 Fixture: persistence_observe_dry_run.py or cited
                          from the Step 11 dry-run document.
```

## 7. Fixture Roster

```text
I-OPSHARDEN-01  persistence_ops_session_status.py
I-OPSHARDEN-02  persistence_ops_db_status.py
I-OPSHARDEN-03  persistence_ops_db_verify.py
                persistence_ops_db_verify_drop.py
I-OPSHARDEN-04  persistence_ops_db_verify.py (subsumes)
I-OPSHARDEN-05  persistence_ops_db_backup.py
I-OPSHARDEN-06  persistence_ops_db_backup_force.py
I-OPSHARDEN-07  persistence_ops_db_backup_dest_uri.py
I-OPSHARDEN-08  persistence_ops_db_backup.py (subsumes)
I-OPSHARDEN-09  persistence_ops_cli_short_circuit.py
I-OPSHARDEN-10  persistence_ops_static_audit.py (subsumes)
I-OPSHARDEN-11  persistence_ops_static_audit.py (subsumes)
I-OPSHARDEN-12  persistence_ops_static_audit.py
I-OPSHARDEN-13  persistence_ops_resource_audit.py
I-OPSHARDEN-14  persistence_ops_cli_short_circuit.py (subsumes)

I-OBSERVE-01    persistence_observe_db_summary.py
I-OBSERVE-02    persistence_observe_profile_summary.py
I-OBSERVE-03    persistence_observe_stream_db_summary.py
I-OBSERVE-04    persistence_observe_db_diff.py
I-OBSERVE-05    persistence_observe_db_summary.py (subsumes)
I-OBSERVE-06    persistence_observe_static_audit.py
I-OBSERVE-07    persistence_observe_no_builder_call.py
I-OBSERVE-08    persistence_observe_resource_audit.py
I-OBSERVE-09    persistence_observe_default_caps.py
I-OBSERVE-10    persistence_observe_static_audit.py (subsumes)
I-OBSERVE-11    OBSERVED; persistence_observe_dry_run.py or
                 audit-cited
```

Fixture file delta: **18** new fixture modules (10 ops + 8 observe),
serving 24 of the 25 new rows. The OBSERVED row (I-OBSERVE-11) is
cited from the Step 11 dry-run document rather than runner-gated.

```text
brain/ui/fixtures/persistence_ops_session_status.py
brain/ui/fixtures/persistence_ops_db_status.py
brain/ui/fixtures/persistence_ops_db_verify.py
brain/ui/fixtures/persistence_ops_db_verify_drop.py
brain/ui/fixtures/persistence_ops_db_backup.py
brain/ui/fixtures/persistence_ops_db_backup_force.py
brain/ui/fixtures/persistence_ops_db_backup_dest_uri.py
brain/ui/fixtures/persistence_ops_cli_short_circuit.py
brain/ui/fixtures/persistence_ops_resource_audit.py
brain/ui/fixtures/persistence_ops_static_audit.py
brain/ui/fixtures/persistence_observe_db_summary.py
brain/ui/fixtures/persistence_observe_profile_summary.py
brain/ui/fixtures/persistence_observe_stream_db_summary.py
brain/ui/fixtures/persistence_observe_db_diff.py
brain/ui/fixtures/persistence_observe_no_builder_call.py
brain/ui/fixtures/persistence_observe_resource_audit.py
brain/ui/fixtures/persistence_observe_default_caps.py
brain/ui/fixtures/persistence_observe_static_audit.py
```

Row-to-fixture subsumption summary (a fixture may serve multiple
rows but no fixture serves more than two in this plan):

```text
persistence_ops_db_verify.py            I-OPSHARDEN-03 + 04
persistence_ops_db_backup.py            I-OPSHARDEN-05 + 08
persistence_ops_static_audit.py         I-OPSHARDEN-12; also covers
                                          I-OPSHARDEN-10 (mode=ro
                                          string) + I-OPSHARDEN-11
                                          (autosave-absent) as
                                          subsumed structural checks
persistence_ops_cli_short_circuit.py    I-OPSHARDEN-09 + 14
persistence_observe_db_summary.py       I-OBSERVE-01 + 05 (behavioral
                                          non-activation; the AST
                                          half is in -07)
persistence_observe_static_audit.py     I-OBSERVE-06; also covers
                                          I-OBSERVE-10 (autosave-
                                          absent) as a subsumed
                                          structural check
```

If Step 8/9 implementation finds two rows naturally fit one
fixture, the catalog patch (Step 7) must update this roster
explicitly before landing rows. The catalog plan locks at most a
two-row collapse per fixture; a fixture covering three or more
rows requires a corrigenda amendment.

## 8. File Budget

Modified files for Step 7 catalog patch:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
README.md
CURRENT_MISSION.md           (catalog-version banner v0.17 -> v0.18)
CURRENT_CAMPAIGN.md          (catalog-version banner v0.17 -> v0.18)
```

Optional marker files (Step 7 may land empty placeholders so the
future fixture imports have target modules):

```text
brain/ui/persistence_ops.py       (empty placeholder; impl in Step 8)
brain/ui/persistence_observe.py   (empty placeholder; impl in Step 9)
```

Expected modified / new files for Step 8 implementation
(operational hardening core):

```text
brain/ui/persistence_ops.py
brain/ui/__main__.py                 (--db-status, --db-verify,
                                      --db-backup, --db-backup-force
                                      flags + short-circuit branches)
brain/ui/commands.py                 (SESSION_STATUS, DB_STATUS,
                                      DB_VERIFY, DB_BACKUP enum
                                      members + DbBackupPayload;
                                      _COMMANDS_WITHOUT_PAYLOAD
                                      extension)
brain/ui/command_line.py             (/session-status, /db-status,
                                      /db-verify, /db-backup parser
                                      verbs)
brain/ui/session.py                  (_dispatch_session_status,
                                      _dispatch_db_status,
                                      _dispatch_db_verify,
                                      _dispatch_db_backup;
                                      NO new session fields)
brain/ui/fixtures/persistence_ops_session_status.py
brain/ui/fixtures/persistence_ops_db_status.py
brain/ui/fixtures/persistence_ops_db_verify.py
brain/ui/fixtures/persistence_ops_db_verify_drop.py
brain/ui/fixtures/persistence_ops_db_backup.py
brain/ui/fixtures/persistence_ops_db_backup_force.py
brain/ui/fixtures/persistence_ops_db_backup_dest_uri.py
brain/ui/fixtures/persistence_ops_cli_short_circuit.py
brain/ui/fixtures/persistence_ops_resource_audit.py
brain/ui/fixtures/persistence_ops_static_audit.py
brain/invariants.py                  (_PHASE3_10_OPS_PENDING_ROWS
                                      drained as fixtures land)
```

Expected modified / new files for Step 9 implementation
(observability summaries + diff):

```text
brain/ui/persistence.py              (narrow extension: promote
                                      _snapshot_session ->
                                      snapshot_session as a public
                                      helper. No other Phase 3.9
                                      public API change.)
brain/ui/persistence_observe.py
brain/ui/commands.py                 (DB_SUMMARY, PROFILE_SUMMARY,
                                      STREAM_DB_SUMMARY, DB_DIFF
                                      enum members; payload-less)
brain/ui/command_line.py             (/db-summary, /profile-summary,
                                      /stream-db-summary, /db-diff
                                      parser verbs)
brain/ui/session.py                  (_dispatch_db_summary,
                                      _dispatch_profile_summary,
                                      _dispatch_stream_db_summary,
                                      _dispatch_db_diff)
brain/ui/fixtures/persistence_observe_db_summary.py
brain/ui/fixtures/persistence_observe_profile_summary.py
brain/ui/fixtures/persistence_observe_stream_db_summary.py
brain/ui/fixtures/persistence_observe_db_diff.py
brain/ui/fixtures/persistence_observe_no_builder_call.py
brain/ui/fixtures/persistence_observe_resource_audit.py
brain/ui/fixtures/persistence_observe_default_caps.py
brain/ui/fixtures/persistence_observe_static_audit.py
brain/invariants.py                  (_PHASE3_10_OBSERVE_PENDING_
                                      ROWS drained as fixtures land)
```

Expected modified files for Step 10 (backup command landing):

```text
The Step 8 implementation already lands /db-backup. Step 10 is
the explicit backup-policy step which adds:
brain/ui/render.py                   (optional persistence-status
                                      display)
README.md                            (document new commands AFTER
                                      Step 8 + Step 9 + Step 10
                                      implementations land)
```

Step 10 may also tighten the `/db-backup` policy: e.g. add a
post-backup `/db-verify` self-check that confirms the destination
parses (the corrigenda does not require this; the audit step may
add it as a nice-to-have).

Explicitly excluded unless a future accepted plan reopens them
(Phase 3.10a/b only — Phase 3.10c reopens autosave-adjacent
paths at Step 17):

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
brain/ui/autosave.py                  (Phase 3.10c; Step 18)
```

Phase 3.10a/b touches `brain/ui/persistence.py` for exactly one
narrow change — the `_snapshot_session` -> `snapshot_session`
promotion authorized in Section 9 of the corrigenda. No other
Phase 3.9 public API change is permitted.

## 9. Catalog Patch Mechanics (Step 7)

```text
1. Add the 25 new I-OPSHARDEN-* / I-OBSERVE-* row entries to
   INVARIANT_CATALOG.md under two new sections:
     "### Phase 3.10a Operational Hardening invariants"
     "### Phase 3.10b Persistence Observability invariants"

2. Add a v0.18 catalog-version banner above v0.17 documenting the
   +14 REQUIRED / +10 STRUCTURAL / +1 OBSERVED expansion (delta
   total = 25; two new families I-OPSHARDEN-01..14 and
   I-OBSERVE-01..11).

3. Update the summary counts in INVARIANT_CATALOG.md to:
   REQUIRED 201, STRUCTURAL 79, NOT-EXERCISED 10, DEFERRED 12,
   OBSERVED 14.

4. Update tools/catalog.py EXPECTED_COUNTS to the same values and
   refresh the banner-comment block to cite Phase 3.10a/b v0.18.

5. Run `python3 -m tools.catalog generate-ids` to refresh
   brain/_catalog_ids.py with the new I-OPSHARDEN-* and
   I-OBSERVE-* entries.

6. Add _PHASE3_10_OPS_PENDING_ROWS and
   _PHASE3_10_OBSERVE_PENDING_ROWS in brain/invariants.py with
   every REQUIRED and STRUCTURAL row that is not yet backed by a
   real fixture (i.e. I-OPSHARDEN-01..14, I-OBSERVE-01..10).
   I-OBSERVE-11 (OBSERVED) does not participate in I-CAT-01
   coverage and is not pending.

7. Optionally add empty brain/ui/persistence_ops.py and
   brain/ui/persistence_observe.py marker files so future fixture
   imports have a target module. Implementation begins in Step 8.

8. Update README.md catalog-version block to v0.18 and the
   companion-docs section to add the new corrigenda / catalog
   patch plan entries (README command documentation for the eight
   Phase 3.10a/b verbs is deferred to Step 10).

9. Update CURRENT_MISSION.md and CURRENT_CAMPAIGN.md catalog-
   version banners to v0.18.

10. Validate with:
      python3 -m tools.catalog counts
      python3 -m tools.catalog generate-ids
      python3 -m tools.catalog counts
      python3 -m tools.citations verify
      python3 -m tools.import_audit
      python3 -m brain.invariants run
      bash tools/check_all.sh

11. Step 7 should commit and push after count validation only. It
    should not implement status / verify / summary / diff / backup
    behavior, parser verbs, CLI flags, or dispatcher routing.
```

## 10. Implementation Mechanics (Step 8 onward)

The later implementation steps should drain
`_PHASE3_10_OPS_PENDING_ROWS` and
`_PHASE3_10_OBSERVE_PENDING_ROWS` by landing fixture-backed
checks in a controlled order:

```text
Step 8 (status + verify + backup core):
  1. Implement brain/ui/persistence_ops.py with session_status,
     db_status, db_verify, db_backup helpers + typed reports.
  2. Extend brain/ui/__main__.py with --db-status, --db-verify,
     --db-backup, --db-backup-force short-circuit flags.
  3. Extend brain/ui/commands.py with SESSION_STATUS, DB_STATUS,
     DB_VERIFY, DB_BACKUP enum members and DbBackupPayload.
  4. Extend brain/ui/command_line.py with the four Phase 3.10a
     verbs.
  5. Extend brain/ui/session.py with _dispatch_session_status,
     _dispatch_db_status, _dispatch_db_verify,
     _dispatch_db_backup.
  6. Add fixtures: persistence_ops_session_status.py,
     persistence_ops_db_status.py, persistence_ops_db_verify.py,
     persistence_ops_db_verify_drop.py,
     persistence_ops_db_backup.py,
     persistence_ops_db_backup_force.py,
     persistence_ops_db_backup_dest_uri.py,
     persistence_ops_cli_short_circuit.py,
     persistence_ops_resource_audit.py,
     persistence_ops_static_audit.py.
  7. Drain I-OPSHARDEN-01..14.

Step 9 (summaries + diff):
  8. Narrow extension of brain/ui/persistence.py to promote
     _snapshot_session -> snapshot_session (public).
  9. Implement brain/ui/persistence_observe.py with db_summary,
     profile_summary, stream_db_summary, db_diff helpers +
     typed reports.
  10. Extend brain/ui/commands.py with DB_SUMMARY,
      PROFILE_SUMMARY, STREAM_DB_SUMMARY, DB_DIFF enum members
      (no new payloads).
  11. Extend brain/ui/command_line.py with the four Phase 3.10b
      verbs.
  12. Extend brain/ui/session.py with _dispatch_db_summary,
      _dispatch_profile_summary, _dispatch_stream_db_summary,
      _dispatch_db_diff.
  13. Add fixtures: persistence_observe_db_summary.py,
      persistence_observe_profile_summary.py,
      persistence_observe_stream_db_summary.py,
      persistence_observe_db_diff.py,
      persistence_observe_no_builder_call.py,
      persistence_observe_resource_audit.py,
      persistence_observe_default_caps.py,
      persistence_observe_static_audit.py.
  14. Drain I-OBSERVE-01..10.

Step 10 (explicit backup policy / docs):
  15. README.md: document the eight Phase 3.10a/b verbs and
      the four short-circuit CLI flags.
  16. Optional render.py update for persistence-status display.

Step 11 (audit):
  17. Write PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md; cite from
      I-OBSERVE-11 (OBSERVED).
  18. Write PHASE3_10_OPS_OBSERVABILITY_AUDIT.md; run the full
      gate.

Step 12-21: Autosave track (Phase 3.10c) — separate plan.
```

Expected targeted validations during Steps 8-10:

```bash
python3 -m brain.invariants run --id I-OPSHARDEN
python3 -m brain.invariants run --id I-OBSERVE
python3 -m brain.invariants run --id I-UI
python3 -m brain.invariants run --id I-PERSIST
bash tools/check_all.sh
```

## 11. Accepted Constants

```text
PROFILE_SUMMARY_ROW_CAP           = 64
STREAM_DB_SUMMARY_HEAD_CAP        = 8
STREAM_DB_SUMMARY_TAIL_CAP        = 8
DB_DIFF_ROW_CAP                   = 32
STREAM_TEXT_PREVIEW_MAX_LEN       = 64
OPS_REPORT_TEXT_MAX_LEN           = 256
PROFILE_VALUE_STRING_MAX_LEN      = 64
DB_BACKUP_FORBIDDEN_SCHEMES       = frozenset({
                                      "sqlite", "file", "http",
                                      "https", "ftp", "ws", "wss",
                                      "data", "gopher", "ssh", "git"
                                    })
```

These constants are declared in `brain/ui/persistence_ops.py` and
`brain/ui/persistence_observe.py` (whichever owns each cap is
documented in the module). The `persistence_observe_default_caps.py`
fixture asserts the values; the `persistence_ops_db_backup_dest_uri.py`
fixture asserts the forbidden scheme list.

Existing constants reused from upstream modules:

```text
SCHEMA_VERSION_V1                 = 1     (brain/ui/persistence.py)
SUPPORTED_SCHEMA_VERSIONS         = ...   (brain/ui/persistence.py)
CATALOG_VERSION_STAMP             = "v0.18" (bumped at Step 7)
STREAM_TEXT_MAX_LEN               = 1024  (brain/development/text_stream.py)
STREAM_PROVENANCE_MAX_LEN         =   64  (brain/development/text_stream.py)
MAX_STATUS_TEXT_LEN               =  240  (brain/ui/session.py)
LOCAL_CMD_MAX_ERROR_LEN           =  240  (brain/ui/command_line.py)
```

If `brain/ui/persistence_ops.py` or
`brain/ui/persistence_observe.py` duplicates any of these, the
corresponding static-audit fixture must include a parity check
against the owning module constants.

## 12. Non-Goals To Preserve

```text
no raw text -> COGITO_ID
no raw text -> BrainState direct mutation
no pickle / shelve / marshal / dill / cloudpickle / joblib as a
  format
no JSON / TOML / YAML as the authoritative kernel-state format
no REAL / NUMERIC / FLOAT / DOUBLE columns for kernel numeric data
no sqlite3.Connection on OperatorSession
no autosave from any dispatch path (Phase 3.10a/b)
no network-backed persistence / observability
no multi-profile / multi-user persistence
no migrations between schema versions in v1
no persistence of LLM client / cache / runtime mode
no persistence of operator transcripts beyond bounded session-local
  state
no persistence of curses configuration / terminal state
no modifications to tick() semantics
no typed operator commands outside the eight Phase 3.10a/b verbs
no save / export path outside the configured session DB and the
  explicit /db-backup destination
no Phase 3.10c autosave wiring in Phase 3.10a/b (the
  --autosave-mode flag and /autosave-* verbs are deferred to
  Step 18)
no Phase 3.9 public API change other than the narrow
  _snapshot_session -> snapshot_session promotion
no real LLM call below the existing Phase 3.8b toggle (Phase 3.10
  does not alter the toggle)
```

## 13. Review Gate

Stop after this plan is committed and pushed.

```text
Do not apply v0.18 catalog rows.
Do not edit tools/catalog.py.
Do not edit brain/_catalog_ids.py.
Do not edit brain/invariants.py.
Do not add Phase 3.10a/b fixtures.
Do not create brain/ui/persistence_ops.py or brain/ui/
  persistence_observe.py (other than as optional empty markers
  if Step 7 is reached).
Do not edit brain/ui/__main__.py / commands.py / command_line.py /
  session.py / render.py as if Phase 3.10a/b is implemented.
Do not update README as if the eight Phase 3.10a/b verbs exist.
Do not proceed to Step 7 until this plan is explicitly accepted.
```

## Conclusion

This plan is coherent. The next campaign step, if accepted, is:

```text
Step 7 - Apply Phase 3.10a/b catalog patch
```

The Phase 3.10a/b catalog patch transitions the catalog from v0.17
(187 / 69 / 10 / 12 / 13) to v0.18 (201 / 79 / 10 / 12 / 14) by
adding the I-OPSHARDEN-01..14 and I-OBSERVE-01..11 row families.
No runtime / fixture code is written until Step 8.

The Phase 3.10c autosave catalog patch (Step 15) and implementation
(Step 18) are deferred until the Phase 3.10a/b audit (Step 11) is
PASS.
