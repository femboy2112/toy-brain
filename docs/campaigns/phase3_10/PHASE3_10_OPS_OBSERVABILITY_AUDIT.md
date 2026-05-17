# PHASE3_10_OPS_OBSERVABILITY_AUDIT.md

## 1. Purpose

Audit the complete Phase 3.10 Operational Hardening + Persistence
Observability implementation (tracks A + B) against the accepted
synthesis, kickoff, corrigenda, and ops/observability catalog patch
plan. This document is an audit artifact: it does not edit
`brain/ui/persistence_ops.py`, `brain/ui/persistence_observe.py`,
any Phase 3.10 fixture, `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `brain/invariants.py`, or any guarded
kernel path.

```text
Verdict for Step 11: PASS
```

The Phase 3.10c autosave track is explicitly out of scope here. It
is gated behind a separate review gate at Step 16.

## 2. Baseline

```text
Catalog version:  v0.18
REQUIRED:        201
STRUCTURAL:       79
NOT-EXERCISED:    10
DEFERRED:         12
OBSERVED:         14
Total tabular:   316
Total fixtures:  120

Landed campaign steps (tracks A + B):
  Step 1   repo-state sync                          (sync only; no commit)
  Step 2   Phase 3.10 synthesis                     commit ac13e8e
  Step 3   Phase 3.10 kickoff                       commit 5f5c875
  Step 4   Phase 3.10 corrigenda                    commit 9807b75
  Step 5   ops/observability catalog patch plan     commit 88eb691
  Step 6   review gate A/B                          (accepted)
  Step 7   v0.18 ops/observability catalog patch    commit a2ef1bb
  Step 8   operational hardening core               commit 6e77b24
  Step 9   persistence observability                commit d4e1468
  Step 10  README documentation                     commit 930f5cf
  Step 11  ops/observability dry run + this audit   this document
```

Required source artifacts (all readable from the campaign branch):

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_SYNTHESIS.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_KICKOFF.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md
PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md
PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md
INVARIANT_CATALOG.md (v0.18)
brain/ui/persistence.py        (Phase 3.10b narrow extension only:
                                _snapshot_session -> snapshot_session)
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/fixtures/persistence_ops_*.py        (10 fixtures)
brain/ui/fixtures/persistence_observe_*.py    (8 fixtures)
brain/ui/fixtures/command_router.py           (Phase 3.10 enum updates)
brain/ui/fixtures/composer_input.py           (Phase 3.10 arg-verb update)
brain/ui/fixtures/tui_smoke.py                (Phase 3.10 module exemption)
brain/invariants.py
tools/catalog.py
README.md
```

## 3. /session-status (I-OPSHARDEN-01)

```text
Audit:    brain/ui/persistence_ops.py session_status(session) reads
          OperatorSession fields only (tick_counter, queue_size,
          active_view, has_* flags, stream counts,
          session_db_configured, session_db_path_str, quit_flag);
          no sqlite3 import path is exercised; no Connection is
          opened. _dispatch_session_status surfaces the bounded
          report through status_message and clears error_message.
          The dispatcher path performs no tick() call.

Evidence: persistence_ops_session_status.py builds a default
          session, calls session_status, asserts the returned
          report's field shapes are bounded
          (OPS_REPORT_TEXT_MAX_LEN cap), asserts integer fields
          are non-negative, asserts the dispatcher surfaces the
          report through status_message, and asserts no
          sqlite3.Connection / open file handle appears anywhere
          on the session after the call.

Row:      I-OPSHARDEN-01 REQUIRED.
Status:   PASS.
```

## 4. /db-status (I-OPSHARDEN-02)

```text
Audit:    db_status(config) opens the configured DB through
          sqlite3.connect("file:<path>?mode=ro", uri=True) inside
          a `with conn:` block, reads meta rows, returns a typed
          DbStatusReport, closes the connection. Missing DB
          yields db_exists=False and empty version / timestamp
          fields with a bounded error_text. The dispatcher
          performs no tick() call.

Evidence: persistence_ops_db_status.py asserts:
          - missing DB -> db_exists=False, no sqlite3 error
            propagates;
          - freshly-saved DB -> schema_version=1,
            catalog_version="v0.18", non-empty timestamps;
          - report string fields are bounded.

Row:      I-OPSHARDEN-02 REQUIRED.
Status:   PASS.
```

## 5. /db-verify (I-OPSHARDEN-03, I-OPSHARDEN-04)

```text
Audit:    db_verify(config) calls load_session(config), captures
          the returned (candidate, LoadSessionResult), runs the
          existing invariant assertions inside load_session, and
          drops the candidate IMMEDIATELY. The function returns a
          DbVerifyReport with passed=True on success or
          passed=False with a bounded error_text on any
          PersistenceError. The candidate is never assigned to
          the live OperatorSession; the live session reference
          (id()) is unchanged before and after the call. The
          dispatcher does not call tick().

Evidence: persistence_ops_db_verify.py asserts passing verify on
          a clean DB and failing verify on a tampered DB (rho_den=
          0 injection, broken FK, missing meta row); in every
          failure branch the live session and on-disk DB file
          byte-equal the pre-call state (mode=ro guarantees
          the latter).
          persistence_ops_db_verify_drop.py asserts id(session)
          is unchanged before and after db_verify, and that no
          field on session is rebound to the returned candidate.

Rows:     I-OPSHARDEN-03 REQUIRED, I-OPSHARDEN-04 REQUIRED.
Status:   PASS.
```

## 6. /db-backup (I-OPSHARDEN-05, I-OPSHARDEN-06, I-OPSHARDEN-07, I-OPSHARDEN-08, I-OPSHARDEN-10)

```text
Audit:    db_backup(config, dest_path, *, force=False) opens the
          source DB through sqlite3.connect("file:<source>?mode=ro",
          uri=True) inside `with src:` and the destination through
          sqlite3.connect(dest_path) inside `with dest:`. It calls
          src.backup(dest) (page-faithful). The returned
          DbBackupReport carries source / dest sizes, pages copied,
          total pages, succeeded, overwritten, and a bounded
          error_text. Argument validation rejects URI-scheme
          destinations against DB_BACKUP_FORBIDDEN_SCHEMES
          (sqlite, file, http, https, ftp, ws, wss, data, gopher,
          ssh, git), rejects dest_path == source_path, rejects
          dest_path that is a directory, and rejects existing dest
          without force=True. The static audit (I-OPSHARDEN-12)
          confirms shutil is NOT imported and that the source
          connection string contains "mode=ro".

Evidence: persistence_ops_db_backup.py constructs a session, saves
          to a source DB, backs up to a destination, and asserts
          load_session against the destination yields the same
          PersistentSessionSnapshot as the source; the source file
          byte-equals the pre-call file; dest_path == source_path
          raises PersistenceError before any sqlite3 call.
          persistence_ops_db_backup_force.py asserts the
          without-force rejection, the with-force overwrite, and
          the overwritten=True report flag.
          persistence_ops_db_backup_dest_uri.py asserts every
          forbidden URI scheme is rejected at validation time; no
          destination file is touched.
          persistence_ops_static_audit.py subsumes the
          mode=ro-string check (I-OPSHARDEN-10).

Rows:     I-OPSHARDEN-05 REQUIRED, I-OPSHARDEN-06 REQUIRED,
          I-OPSHARDEN-07 REQUIRED, I-OPSHARDEN-08 REQUIRED,
          I-OPSHARDEN-10 STRUCTURAL.
Status:   PASS.
```

## 7. CLI short-circuit ordering + exit codes (I-OPSHARDEN-09, I-OPSHARDEN-14)

```text
Audit:    brain/ui/__main__.build_arg_parser adds --db-status,
          --db-verify, --db-backup PATH, --db-backup-force; the
          three "verb" flags are mutually exclusive via
          add_mutually_exclusive_group. _dispatch_ops_short_circuit
          fires in main() after the --check-terminal and
          --print-once branches and before
          _resolve_llm_runtime_config and curses initialization.
          Exit code 0 on PASS / success, 1 on FAIL / failure.
          Bounded reports go to stdout; stderr is unused.

Evidence: persistence_ops_cli_short_circuit.py constructs argv
          stand-ins, calls main() with injected stdin/stdout/env,
          asserts:
          - --db-status + --db-verify on the same command line
            raises an argparse error;
          - --db-status on a freshly-saved DB exits 0;
          - --db-status on a missing DB exits 1;
          - --db-verify on a clean DB exits 0;
          - --db-verify on a tampered DB exits 1;
          - --db-backup PATH writes the destination and exits 0;
          - --db-backup PATH against an existing dest without
            --db-backup-force exits 1.

Rows:     I-OPSHARDEN-09 REQUIRED, I-OPSHARDEN-14 STRUCTURAL.
Status:   PASS.
```

## 8. Phase 3.10a static + resource audits (I-OPSHARDEN-11, I-OPSHARDEN-12, I-OPSHARDEN-13)

```text
Audit:    persistence_ops_static_audit.py asserts brain/ui/
          persistence_ops.py imports are confined to sqlite3,
          dataclasses, datetime, pathlib, typing, brain.ui.
          persistence, brain.ui.session (and brain.tlica.profile
          for COGITO_ID if needed). The module imports neither
          pickle, shelve, marshal, dill, cloudpickle, joblib,
          subprocess, socket, urllib, http, requests, curses,
          brain.tick (any symbol), brain.tlica internals beyond
          what brain.ui.persistence re-exports, nor brain.llm. It
          contains no importlib.import_module, __import__, eval(,
          exec(, compile(, atexit.register, threading, asyncio,
          or signal handler. Module-level statements are limited
          to imports, constants, function defs, and class defs
          (plus the module docstring). The autosave-absent audit
          (I-OPSHARDEN-11) is enforced by the same static AST
          check: no call site invokes save_session outside the
          Phase 3.9 dispatcher (which lives in brain.ui.session,
          not in persistence_ops). The mode=ro substring check
          for the source backup connection lives in the same
          fixture.
          persistence_ops_resource_audit.py asserts no
          OperatorSession field is added in Phase 3.10a; after
          /session-status, /db-status, /db-verify, /db-backup,
          the session field shape is identical to the pre-call
          shape (no sqlite3.Connection / Cursor / subprocess /
          socket / file / callable / curses object appears in
          any session field).

Rows:     I-OPSHARDEN-11 STRUCTURAL, I-OPSHARDEN-12 STRUCTURAL,
          I-OPSHARDEN-13 STRUCTURAL.
Status:   PASS.
```

## 9. /db-summary (I-OBSERVE-01, I-OBSERVE-05)

```text
Audit:    db_summary(config) opens the DB in mode=ro inside
          `with conn:`, reads meta rows plus per-table row
          counts (profile_values, msi_contents, msi_threshold,
          ptcns_eval, content_registry, stream_chunks,
          stream_candidates), and returns a typed DbSummaryReport
          with bounded string fields and non-negative integer
          fields. The msi_threshold field is the exact
          "num/den" string rendered by the single shared
          _render_fraction helper. No builder call occurs. The
          dispatcher does not call tick(). session.__eq__ before
          and after the dispatch is True (I-OBSERVE-05 behavioral
          half).

Evidence: persistence_observe_db_summary.py builds a default
          session, saves to a temp DB, calls db_summary, and
          asserts profile_row_count=2, msi_content_count=2,
          msi_threshold="1/2", registry_row_count=1,
          ptcns_eval_row_count=2, stream_chunk_count=0,
          stream_candidate_count=0. The fixture also asserts
          session pre/post equality.

Rows:     I-OBSERVE-01 REQUIRED, I-OBSERVE-05 REQUIRED.
Status:   PASS.
```

## 10. /profile-summary (I-OBSERVE-02)

```text
Audit:    profile_summary(config, *, row_cap=PROFILE_SUMMARY_ROW_CAP)
          opens the DB in mode=ro, reads profile_values, sorts
          with COGITO_ID first then content_id ASCII-ascending,
          renders each Fraction(num, den) via _render_fraction
          to the exact "num/den" string (bounded by
          PROFILE_VALUE_STRING_MAX_LEN=64), and truncates at
          row_cap with truncated=True when the cap is hit. No
          float() / repr() / str(Fraction(...)) leakage occurs;
          the static audit (I-OBSERVE-06) confirms the render
          helper is the single named function reused across
          reports.

Evidence: persistence_observe_profile_summary.py asserts:
          - COGITO_ID is the first row;
          - remainder is sorted;
          - every value_str is an exact "num/den" string;
          - row_cap=1 truncates a 2-row profile and sets
            truncated=True.

Row:      I-OBSERVE-02 REQUIRED.
Status:   PASS.
```

## 11. /stream-db-summary (I-OBSERVE-03)

```text
Audit:    stream_db_summary(config, *, head_cap=8, tail_cap=8)
          opens the DB in mode=ro, reads stream_chunks and
          stream_candidates row counts plus a head + tail slice.
          Each StreamDbSummaryRow.text_preview is bounded by
          STREAM_TEXT_PREVIEW_MAX_LEN=64. Full chunk text is
          never returned. truncated=True iff chunk_count exceeds
          head_cap + tail_cap.

Evidence: persistence_observe_stream_db_summary.py builds a
          session with multiple stream chunks, saves, calls
          stream_db_summary, asserts head and tail slice sizes
          are bounded, asserts text_preview is truncated to the
          cap, and asserts the truncated flag flips when the
          chunk count exceeds head_cap + tail_cap.

Row:      I-OBSERVE-03 REQUIRED.
Status:   PASS.
```

## 12. /db-diff (I-OBSERVE-04)

```text
Audit:    db_diff(session, config, *, row_cap=32) calls the
          public snapshot_session(session) helper (promoted from
          brain.ui.persistence._snapshot_session in the Phase
          3.10b narrow extension), reads the saved
          PersistentSessionSnapshot via _deserialize_from_db,
          and diffs over the finite field enumeration
          (profile.<id>, msi.contents, msi.threshold,
          ptcns_eval.<id>, registry.<id>, tick_counter,
          stream_chunk_serial, stream_history.count,
          stream_candidates.count). DbDiffField.live / .saved
          use exact "num/den" strings for kernel-numeric values,
          integer text for counters, and the literal "<missing>"
          marker for one-sided absence. The diff never invents
          defaults. truncated=True iff diff_count > row_cap.

Evidence: persistence_observe_db_diff.py asserts:
          - matching session/DB returns matches=True,
            diff_count=0;
          - divergent live profile yields an explicit
            DbDiffField with live="<num>/<den>" and
            saved="<missing>";
          - a content_id that exists only on the saved side
            yields the reciprocal "<missing>" on live;
          - the finite field-name enumeration is enforced
            (constructing DbDiffField with an unknown name
            raises).

Row:      I-OBSERVE-04 REQUIRED.
Status:   PASS.
```

## 13. Phase 3.10b static + structural audits (I-OBSERVE-06, I-OBSERVE-07, I-OBSERVE-08, I-OBSERVE-09, I-OBSERVE-10)

```text
Audit:    persistence_observe_static_audit.py asserts
          brain/ui/persistence_observe.py imports are confined
          to sqlite3, dataclasses, fractions, pathlib, typing,
          brain.tlica.profile (COGITO_ID only),
          brain.ui.persistence, brain.ui.persistence_ops (for
          OPS_REPORT_TEXT_MAX_LEN re-export), and brain.ui.
          session (for OperatorSession typing). The module
          imports no pickle, shelve, marshal, dill, cloudpickle,
          joblib, subprocess, socket, urllib, http, requests,
          curses, brain.tick, brain.tlica internals beyond what
          brain.ui.persistence re-exports, or brain.llm. It
          contains no importlib.import_module, __import__,
          eval(, exec(, compile(, atexit.register, threading,
          asyncio, or signal handler. Module-level statements
          are limited to imports, constants, function defs, and
          class defs (plus the module docstring). The
          autosave-absent audit (I-OBSERVE-10) is enforced by
          the same static AST check: no call site invokes
          save_session.

          persistence_observe_no_builder_call.py asserts
          brain/ui/persistence_observe.py contains no call to
          make_profile_with_cogito, make_msi, make_ptcns,
          make_text_stream_chunk, or make_stream_promotion_
          candidate, and no instantiation of ContentRegistry,
          BrainState, TextStreamHistory, or OperatorSession
          (I-OBSERVE-07).

          persistence_observe_resource_audit.py asserts no
          OperatorSession field is added in Phase 3.10b; after
          /db-summary, /profile-summary, /stream-db-summary,
          /db-diff, the session field shape is identical to the
          pre-call shape; no sqlite3.Connection / Cursor /
          subprocess / socket / file / callable / curses object
          appears in any session field (I-OBSERVE-08).

          persistence_observe_default_caps.py asserts
          PROFILE_SUMMARY_ROW_CAP=64,
          STREAM_DB_SUMMARY_HEAD_CAP=8,
          STREAM_DB_SUMMARY_TAIL_CAP=8, DB_DIFF_ROW_CAP=32,
          STREAM_TEXT_PREVIEW_MAX_LEN=64,
          OPS_REPORT_TEXT_MAX_LEN=256,
          PROFILE_VALUE_STRING_MAX_LEN=64; the helpers default
          to these constants (I-OBSERVE-09).

Rows:     I-OBSERVE-06 STRUCTURAL, I-OBSERVE-07 STRUCTURAL,
          I-OBSERVE-08 STRUCTURAL, I-OBSERVE-09 STRUCTURAL,
          I-OBSERVE-10 STRUCTURAL.
Status:   PASS.
```

## 14. Phase 3.10 ops/observability dry run (I-OBSERVE-11)

```text
Audit:    PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md documents a
          deterministic scripted session that exercises the
          eight typed verbs and the four short-circuit CLI
          flags on the offline stand-in client, saves to a
          source DB, backs up to a destination, relaunches
          against the backup, and asserts the loaded session
          matches the original.

Evidence: the dry-run document itself (Steps 3.1-3.7); the
          fixture roster (persistence_ops_db_backup.py,
          persistence_ops_db_verify.py, persistence_observe_*)
          pins the negative paths programmatically. This row is
          OBSERVED and cannot fail the runner.

Row:      I-OBSERVE-11 OBSERVED.
Status:   PASS (OBSERVED).
```

## 15. Phase 3.9 _snapshot_session promotion (narrow Phase 3.10b extension)

```text
Audit:    brain/ui/persistence.py promotes _snapshot_session to
          the public snapshot_session helper (drop the leading
          underscore; identical behavior; internal save_session
          caller updated to use the public name; added to
          __all__). No other public API change to
          brain.ui.persistence. The Phase 3.9 static audit
          (I-PERSIST-12) accommodates the new public name via
          its import-set allowlist. The existing 11 Phase 3.9
          persistence_*.py fixtures continue to pass.

Evidence: All I-PERSIST-01..16 rows green in the full runner
          gate. The fixture
          persistence_observe_db_diff.py exercises
          snapshot_session against a default session and a
          mutated session; the resulting
          PersistentSessionSnapshot is byte-identical to the
          pre-promotion private helper's output.

Rows:     I-PERSIST-01..16 unchanged in this audit (all green).
Status:   PASS.
```

## 16. tui_smoke I-UI-07 module exemption

```text
Audit:    brain/ui/fixtures/tui_smoke.py extends the I-UI-07
          is_persistence_module exemption to cover
          persistence_ops.py and persistence_observe.py (both
          legitimately import brain.tlica.profile for COGITO_ID).
          The per-module audits I-OPSHARDEN-12 and I-OBSERVE-06
          enforce the seam set for each module independently; the
          UI-wide audit's narrower exemption avoids
          double-counting.

Rows:     I-UI-07 REQUIRED (unchanged).
Status:   PASS.
```

## 17. Full gate

```text
$ python3 -m tools.catalog counts
Category            Banner    Actual  Expected
REQUIRED               201       201       201  ok
STRUCTURAL              79        79        79  ok
NOT-EXERCISED           10        10        10  ok
DEFERRED                12        12        12  ok
OBSERVED                14        14        14  ok

$ python3 -m tools.citations verify
Verified 100 citations.
All catalog citations resolve in lean_reference/.

$ python3 -m tools.import_audit
I-PCE-05: agency.py is clean of pce imports.

$ python3 -m brain.invariants run --id I-OPSHARDEN
15 rows checked  ·  REQUIRED green: 10 ·  REQUIRED red: 0
              ·  STRUCTURAL green: 5 ·  STRUCTURAL red: 0
              ·  gate failures: 0

$ python3 -m brain.invariants run --id I-OBSERVE
10 rows checked  ·  REQUIRED green: 5 ·  REQUIRED red: 0
              ·  STRUCTURAL green: 5 ·  STRUCTURAL red: 0
              ·  gate failures: 0

$ bash tools/check_all.sh
[...]
288 rows checked  ·  REQUIRED green: 202 ·  REQUIRED red: 0
              ·  STRUCTURAL green: 79 ·  STRUCTURAL red: 0
              ·  OBSERVED: 7 pass / 0 fail  ·  gate failures: 0
All checks passed.
```

## 18. Pending-row hygiene

```text
brain/invariants.py:
  _PHASE3_10_OPS_PENDING_ROWS         = {}    (drained at Step 8)
  _PHASE3_10_OBSERVE_PENDING_ROWS     = {}    (drained at Step 9)
  All prior phase _PHASE3_*_PENDING_ROWS dicts are also empty.
```

No row is registered as pending; every REQUIRED / STRUCTURAL row in
the v0.18 catalog is backed by a real fixture function.

## 19. Non-mutations confirmed

```text
- The live OperatorSession field-for-field equals the pre-call
  session after every Phase 3.10a/b verb on every fixture path.
- The source DB file byte-equals the pre-call file after every
  read-only verb and after a successful /db-backup.
- No new OperatorSession field appears (Phase 3.10a/b is
  no-new-fields per the corrigenda).
- No sqlite3.Connection / Cursor / subprocess / socket / file /
  callable / curses object appears in any session field.
- No tick() call occurs inside any Phase 3.10a/b dispatcher.
- No save_session call occurs from any Phase 3.10a/b path.
- No @atexit / signal handler / threading / asyncio loop fires
  inside brain/ui/persistence_ops.py or
  brain/ui/persistence_observe.py.
```

## 20. Phase 3.10c separation

```text
- brain/ui/autosave.py does not yet exist; it lands at Step 18
  only after the Step 16 review gate C accepts the autosave
  catalog patch plan.
- No --autosave-mode CLI flag is present.
- No /autosave-status / /autosave-enable / /autosave-disable
  parser verb is present.
- No OperatorSession.autosave_config field exists.
- The existing I-PERSIST-16 NOT-EXERCISED row continues to hold
  the autosave-absence placeholder; it will be retired or
  promoted to REQUIRED at Step 17.
```

## 21. Risks observed

```text
- The Phase 3.10b _render_fraction helper is module-private inside
  brain/ui/persistence_observe.py. Future observability commands
  must reuse it (or a shared renderer if one is later promoted)
  rather than recreating Fraction -> str logic.
- The /db-diff finite field enumeration is closed; adding a new
  diffable field requires a corrigenda extension. This is the
  intended behavior per I-OBSERVE-04.
- The Phase 3.9 _snapshot_session -> snapshot_session promotion
  is a single public-name change. Any future Phase 3.10 narrow
  extension must be re-authorized by an explicit corrigenda
  section; the rule is one promotion per accepted extension.
```

No risk currently blocks campaign progression to Step 12 (autosave
synthesis), since the autosave track has its own review gate at
Step 16.

## 22. Conclusion

Phase 3.10 tracks A (Operational Hardening) and B (Persistence
Observability) are fully implemented, audited, and green.

```text
Verdict: PASS.
Next: Step 12 — Phase 3.10c autosave synthesis (planning artifact
      only; the Step 16 review gate gates implementation).
```
