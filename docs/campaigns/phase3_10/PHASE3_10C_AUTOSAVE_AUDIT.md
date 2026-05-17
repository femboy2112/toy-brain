# PHASE3_10C_AUTOSAVE_AUDIT.md

## 1. Purpose

Audit the complete Phase 3.10c Autosave Policy implementation
against the accepted synthesis, kickoff, corrigenda, and autosave
catalog patch plan. This document is an audit artifact: it does
not edit `brain/ui/autosave.py`, any autosave fixture,
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, or any guarded kernel path.

```text
Verdict for Step 19: PASS
```

The Phase 3.10 integrated audit (Step 20) ties tracks A + B + C
together. The final PR opens at Step 21.

## 2. Baseline

```text
Catalog version:  v0.19
REQUIRED:        212
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         15
Total tabular:   331
Total fixtures:  131

Landed Phase 3.10c steps:
  Step 12  autosave synthesis                   commit c72b112
  Step 13  autosave kickoff                     commit c72b112
  Step 14  autosave corrigenda                  commit c72b112
  Step 15  autosave catalog patch plan          commit c72b112
                                                (+ patched: 3e57af7)
  Step 16  review gate C                        (accepted)
  Step 17  v0.19 autosave catalog patch         commit 0b9c7f0
  Step 18  autosave runtime + 11 fixtures       commit e3885a6
  Step 19  autosave dry run + this audit        this document
```

Required source artifacts (all readable from the campaign branch):

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
PHASE3_10C_AUTOSAVE_SYNTHESIS.md
PHASE3_10C_AUTOSAVE_KICKOFF.md
PHASE3_10C_AUTOSAVE_CORRIGENDA.md
PHASE3_10C_AUTOSAVE_CATALOG_PATCH_PLAN.md
PHASE3_10C_AUTOSAVE_DRY_RUN.md
INVARIANT_CATALOG.md (v0.19)
brain/ui/autosave.py
brain/ui/__main__.py             (--autosave-mode wiring)
brain/ui/commands.py             (AUTOSAVE_* enum + payload)
brain/ui/command_line.py         (3 /autosave-* verbs)
brain/ui/session.py              (autosave_config / last_autosave_status
                                  fields; _ALLOWED_SESSION_ATTRS;
                                  _dispatch_autosave_*;
                                  post-dispatch trigger site;
                                  outcome-detection refactor)
brain/ui/fixtures/autosave_*.py  (11 fixtures)
brain/ui/fixtures/command_router.py   (Phase 3.10c enum updates)
brain/ui/fixtures/composer_input.py   (Phase 3.10c arg-verb update)
brain/ui/fixtures/tui_smoke.py        (Phase 3.10c module exemption)
brain/ui/fixtures/persistence_ops_resource_audit.py    (widened
                                                        baseline)
brain/ui/fixtures/persistence_observe_resource_audit.py (widened
                                                         baseline)
brain/invariants.py
tools/catalog.py
README.md
```

## 3. Default OFF (I-AUTOSAVE-01, I-AUTOSAVE-05)

```text
Audit:    build_default_session() returns a session whose
          autosave_config is None (cold-start default). argparse
          default for --autosave-mode is the string "off"; the
          parser never reads an ambient environment variable
          (no BRAIN_AUTOSAVE_MODE). autosave_disable(session) is
          idempotent: calling it twice in a row returns identical
          AutosaveStatusReport objects with mode = OFF; it never
          raises.

Evidence: autosave_default_off.py asserts the session-construction
          default, the CLI parse default, the no-env-read property,
          and the autosave_disable idempotency (two consecutive
          calls; identical reports; no raise).

Rows:     I-AUTOSAVE-01 REQUIRED, I-AUTOSAVE-05 REQUIRED.
Status:   PASS.
```

## 4. AutosaveConfig bound enforcement (I-AUTOSAVE-02)

```text
Audit:    AutosaveConfig(mode=AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
          db_path_str="") raises ValueError; AutosaveConfig(
          mode=AutosaveMode.OFF, db_path_str="") succeeds (the
          cold-start default). Bounded db_path_str (rejected when
          longer than OPS_REPORT_TEXT_MAX_LEN=256 or non-printable).

Evidence: autosave_mode_closed.py asserts the non-OFF-with-empty-
          db_path rejection, the OFF-with-empty-db_path acceptance,
          and the AutosaveMode value-membership check (only OFF
          and AFTER_SUCCESSFUL_MUTATION are accepted; any other
          mode raises ValueError).

Row:      I-AUTOSAVE-02 REQUIRED.
Status:   PASS.
```

## 5. /autosave-enable requires DB (I-AUTOSAVE-03)

```text
Audit:    autosave_enable(session, AutosaveMode.
          AFTER_SUCCESSFUL_MUTATION) on a session with
          session.session_store_config = None raises
          PersistenceError. The corresponding --autosave-mode
          after-successful-mutation CLI flag without --session-db
          raises argparse error code 2 BEFORE main()'s body
          executes; bounded error text goes to stderr.

Evidence: autosave_requires_db.py asserts the Python-API rejection
          and the CLI rejection (uses main() with injected argv
          / stderr; expects non-zero exit code or SystemExit; live
          session unchanged on the Python-API path).

Row:      I-AUTOSAVE-03 REQUIRED.
Status:   PASS.
```

## 6. /autosave-enable transitions + /autosave-status + successful trigger (I-AUTOSAVE-04, I-AUTOSAVE-06, I-AUTOSAVE-08)

```text
Audit:    autosave_enable(session, AutosaveMode.
          AFTER_SUCCESSFUL_MUTATION) on a session with a
          configured session_store_config transitions
          session.autosave_config.mode to AFTER_SUCCESSFUL_MUTATION
          and session.autosave_config.db_path_str to the configured
          DB path string. _dispatch_autosave_status surfaces the
          bounded AutosaveStatusReport through status_message.
          autosave_status(session) never raises; it always returns
          a report with bounded string fields, non-negative integer
          fields, last_attempt_outcome in {"", "ok", "error"}, and
          last_attempt_trigger in {"", "step_tick",
          "stream_promote"}.

          A /step dispatch on a session with autosave enabled +
          a non-empty queue advances tick_counter by one AND
          triggers the post-dispatch autosave; session.
          last_autosave_status.last_attempt_outcome equals "ok",
          last_attempt_trigger equals "step_tick", last_attempt_at
          is a non-empty ISO-8601 timestamp; the saved DB's
          meta.updated_at advances; the DB on-disk size is
          non-zero.

Evidence: autosave_status_after_event.py exercises enable +
          status + the /step trigger; asserts the report shape;
          asserts the post-/step outcome / trigger / timestamp;
          asserts session.last_autosave_status reflects the
          successful autosave.

Rows:     I-AUTOSAVE-04 REQUIRED, I-AUTOSAVE-06 REQUIRED,
          I-AUTOSAVE-08 REQUIRED.
Status:   PASS.
```

## 7. maybe_autosave_after_mutation never raises (I-AUTOSAVE-07)

```text
Audit:    maybe_autosave_after_mutation(session, triggered_by=...)
          absorbs every PersistenceError raised inside the
          underlying save_session call into the typed
          AutosaveStatusReport (last_attempt_outcome="error" +
          bounded last_error_text); it also absorbs any other
          unexpected exception into outcome="error". It returns
          either None (when autosave is OFF / autosave_config is
          None / triggered_by is unrecognized) or an
          AutosaveStatusReport (success or absorbed failure).

Evidence: autosave_failure_preserves.py injects a PersistenceError
          (e.g. by pointing autosave at a read-only / corrupt
          destination) and asserts maybe_autosave_after_mutation
          NEVER raises; the returned report has outcome="error"
          with bounded last_error_text; session.state and
          session.stream_history are byte-identical to the
          pre-call state; the on-disk DB file is unchanged
          (save_session's BEGIN IMMEDIATE / ROLLBACK preserves
          it).

Row:      I-AUTOSAVE-07 REQUIRED.
Status:   PASS.
```

## 8. Failed dispatch does NOT trigger autosave (I-AUTOSAVE-09)

```text
Audit:    A failed /step dispatch (e.g. empty queue; dispatcher
          returns False per the outcome-detection contract) on a
          session with autosave enabled leaves session.
          last_autosave_status unchanged; the saved DB's
          meta.updated_at is unchanged. A subsequent /step that
          succeeds triggers autosave normally with a fresh
          last_attempt_at timestamp.

Evidence: autosave_no_after_failure.py asserts the unchanged
          status across a failure + success sequence; asserts the
          DB mtime is unchanged after the failure and advances
          after the next success.

Row:      I-AUTOSAVE-09 REQUIRED.
Status:   PASS.
```

## 9. Read-only dispatch does NOT trigger autosave (I-AUTOSAVE-10)

```text
Audit:    For every command kind in the closed read-only list
          (INSPECT_STATE, INSPECT_TICK, INSPECT_OUTPUT,
          INSPECT_WORLDLET, INSPECT_REPL, INSPECT_STREAM_SUMMARY,
          INSPECT_STREAM_CANDIDATES, CLEAR_STATUS, HELP, QUIT,
          NOOP, SESSION_STATUS, DB_STATUS, DB_VERIFY, DB_SUMMARY,
          PROFILE_SUMMARY, STREAM_DB_SUMMARY, DB_DIFF, DB_BACKUP,
          AUTOSAVE_STATUS, SAVE_SESSION, LOAD_SESSION), dispatching
          the command on a session with autosave enabled leaves
          session.last_autosave_status unchanged and the saved
          DB's meta.updated_at unchanged. The central dispatch
          reads the sub-dispatcher's return value (Optional[bool])
          rather than scanning status_message / error_message
          strings — the corrigenda's outcome-detection contract.

Evidence: autosave_no_after_read_only.py iterates the closed list,
          dispatches each command on an autosave-enabled session,
          and asserts unchanged status / DB mtime after each.

Row:      I-AUTOSAVE-10 REQUIRED.
Status:   PASS.
```

## 10. Autosave reuses save_session; no second save path (I-AUTOSAVE-11)

```text
Audit:    Static AST audit confirms brain/ui/autosave.py imports
          save_session from brain.ui.persistence and contains no
          other save helper definition or import; no second
          save_session helper exists in brain/ui/persistence.py
          or anywhere else in brain/. This row is the positive
          complement to the reclassified I-PERSIST-16 structural
          row (which asserts brain/ui/persistence.py owns no
          autosave hook).

Evidence: autosave_single_save_path.py performs the static AST
          audit on brain/ui/autosave.py and asserts only one
          save_session helper definition exists across the
          repository.

Row:      I-AUTOSAVE-11 REQUIRED.
Status:   PASS.
```

## 11. Closed enums (I-AUTOSAVE-12)

```text
Audit:    AutosaveMode is a (str, Enum) subclass with exactly
          OFF and AFTER_SUCCESSFUL_MUTATION members;
          SUPPORTED_AUTOSAVE_MODES is a frozenset matching the
          enum membership set. AutosaveTrigger is a (str, Enum)
          subclass with exactly STEP_TICK and STREAM_PROMOTE
          members; SUPPORTED_AUTOSAVE_TRIGGERS is a frozenset
          matching the enum membership set. Any value outside
          either enum raises ValueError on construction.

Evidence: autosave_trigger_set.py asserts the enum class shape
          (str, Enum), the member sets, the frozenset parity,
          and the rejection of invalid values.

Row:      I-AUTOSAVE-12 STRUCTURAL.
Status:   PASS.
```

## 12. brain/ui/autosave.py module static audit (I-AUTOSAVE-13)

```text
Audit:    An AST audit over brain/ui/autosave.py confirms imports
          are confined to the documented seam set (dataclasses,
          datetime, enum, typing + brain.ui.persistence for
          save_session / SessionStoreConfig / PersistenceError +
          brain.ui.persistence_ops for OPS_REPORT_TEXT_MAX_LEN).
          The module imports neither sqlite3 directly, pickle,
          shelve, marshal, dill, cloudpickle, joblib, subprocess,
          socket, urllib, http, requests, curses, brain.tick,
          brain.tlica internals, nor brain.llm. It contains no
          importlib.import_module, __import__, eval(, exec(,
          compile(, atexit.register, threading, asyncio, or
          signal handler. Module-level statements are limited to
          imports, constants, function defs, and class defs (plus
          the module docstring). No `tick(` call appears anywhere
          in the module.

Evidence: autosave_static_audit.py runs the AST audit, asserts
          the import set is a subset of the allowed set,
          rejects every forbidden import / call, and confirms the
          module-level statement constraint.

Row:      I-AUTOSAVE-13 STRUCTURAL.
Status:   PASS.
```

## 13. Session resource audit + outcome-detection contract (I-AUTOSAVE-14)

```text
Audit:    _ALLOWED_SESSION_ATTRS contains "autosave_config" and
          "last_autosave_status". autosave_config is an
          Optional[AutosaveConfig]; last_autosave_status is an
          Optional[AutosaveStatusReport]; both are frozen / slotted
          records over bounded primitives. Neither field carries
          a sqlite3.Connection, sqlite3.Cursor, subprocess handle,
          socket, file object, callable, curses object, or LLM
          client. The outcome-detection contract pins
          _dispatch_step and _dispatch_stream_promote to return
          Optional[bool] indicating mutation success; the central
          dispatch method reads that return value (not the status
          string) to decide whether to fire
          maybe_autosave_after_mutation.

Evidence: autosave_resource_audit.py builds a session, enables
          autosave, runs /step + /stream-promote sequences, and
          asserts:
            - _ALLOWED_SESSION_ATTRS contains the two new names;
            - session.autosave_config is None or Optional[
              AutosaveConfig];
            - session.last_autosave_status is None or Optional[
              AutosaveStatusReport];
            - no sqlite3.Connection / Cursor / subprocess / socket
              / file / callable / curses object appears in any
              session field after any /autosave-* verb or any
              post-dispatch autosave attempt;
            - _dispatch_step and _dispatch_stream_promote return
              True on success and False on failure (verified by
              direct call + inspection of the source).

          persistence_ops_resource_audit.py and
          persistence_observe_resource_audit.py were widened in
          Step 18 to acknowledge the v0.19-authorized Phase 3.10c
          session field additions; both fixtures continue to
          assert the Phase 3.10a/b commands add no new fields
          themselves.

Row:      I-AUTOSAVE-14 STRUCTURAL.
Status:   PASS.
```

## 14. Phase 3.10c autosave dry run (I-AUTOSAVE-15)

```text
Audit:    PHASE3_10C_AUTOSAVE_DRY_RUN.md (Step 19) documents the
          deterministic scripted walk: launch with
          --autosave-mode after-successful-mutation +
          --session-db PATH; /stream / /step / /stream-promote /
          /step; verify the saved DB advances after each
          mutating dispatch; verify read-only verbs do NOT
          advance the saved DB; /autosave-disable; verify
          subsequent /step does NOT re-save; /autosave-enable +
          /step verifies re-arming works; failed /step (empty
          queue) does NOT trigger autosave; PersistenceError
          injection sets last_attempt_outcome="error" and
          preserves the live session and on-disk DB.

Evidence: the dry-run document itself (Sections 3.1-3.8); the
          fixture roster pins every negative path programmatically.
          This row is OBSERVED and cannot fail the runner.

Row:      I-AUTOSAVE-15 OBSERVED.
Status:   PASS (OBSERVED).
```

## 15. I-PERSIST-16 reclassification (v0.19)

```text
Audit:    I-PERSIST-16 was reclassified at Step 17 from
          NOT-EXERCISED to STRUCTURAL with a narrowed proposition
          ("brain/ui/persistence.py owns no autosave trigger or
          background autosave hook; runtime autosave is owned
          only by I-AUTOSAVE-* and brain/ui/autosave.py"). The
          row ID, position, and owning module column are
          preserved. The registration lives in brain/invariants.py
          and calls back into the existing I-PERSIST-12 static
          audit body (which already enforces the narrowed
          proposition); the persistence_static_audit.py fixture
          file body is unchanged.

Evidence: brain.invariants imports and re-runs
          check_i_persist_12_static_audit under the I-PERSIST-16
          row registration; the runner reports the row green.

Row:      I-PERSIST-16 STRUCTURAL (reclassified at v0.19).
Status:   PASS.
```

## 16. Adjacent fixture updates

```text
brain/ui/fixtures/command_router.py extended _EXPECTED_COMMAND_VALUES
with AUTOSAVE_STATUS / AUTOSAVE_ENABLE / AUTOSAVE_DISABLE (drives
I-UI-03 enumeration check).

brain/ui/fixtures/composer_input.py extended _arg_verbs with
"autosave-enable" (drives I-UI-18 enumeration check; the verb
takes one positional mode token).

brain/ui/fixtures/tui_smoke.py extended the persistence_fixture
exemption to cover brain/ui/autosave.py (legitimately imports
brain.ui.persistence and brain.ui.persistence_ops; per-module
audit I-AUTOSAVE-13 enforces its own seam set).

brain/ui/fixtures/persistence_ops_resource_audit.py and
brain/ui/fixtures/persistence_observe_resource_audit.py were
widened to acknowledge the v0.19-authorized Phase 3.10c session
field additions (autosave_config, last_autosave_status); the
Phase 3.10a/b dispatchers themselves still add NO new fields.

Rows:     I-UI-03 REQUIRED, I-UI-18 REQUIRED, I-UI-07 REQUIRED,
          I-OPSHARDEN-13 STRUCTURAL, I-OBSERVE-08 STRUCTURAL
          (all unchanged in status; their fixtures' acceptance
          criteria were widened to acknowledge the v0.19 baseline).
Status:   PASS.
```

## 17. Full gate

```text
$ python3 -m tools.catalog counts
Category            Banner    Actual  Expected
REQUIRED               212       212       212  ok
STRUCTURAL              83        83        83  ok
NOT-EXERCISED            9         9         9  ok
DEFERRED                12        12        12  ok
OBSERVED                15        15        15  ok

$ python3 -m tools.citations verify
Verified 100 citations.
All catalog citations resolve in lean_reference/.

$ python3 -m tools.import_audit
I-PCE-05: agency.py is clean of pce imports.

$ python3 -m brain.invariants run --id I-AUTOSAVE
14 rows checked  ·  REQUIRED green: 11 ·  REQUIRED red: 0
              ·  STRUCTURAL green: 3 ·  STRUCTURAL red: 0
              ·  gate failures: 0

$ python3 -m brain.invariants run
303 rows checked  ·  REQUIRED green: 213 ·  REQUIRED red: 0
              ·  STRUCTURAL green: 83 ·  STRUCTURAL red: 0
              ·  OBSERVED: 7 pass / 0 fail  ·  gate failures: 0

$ bash tools/check_all.sh
[...]
All checks passed.
```

## 18. Pending-row hygiene

```text
brain/invariants.py:
  _PHASE3_10_OPS_PENDING_ROWS     = {}    (drained at Step 8)
  _PHASE3_10_OBSERVE_PENDING_ROWS = {}    (drained at Step 9)
  _PHASE3_10C_PENDING_ROWS        = {}    (drained at Step 18)
  All prior phase _PHASE3_*_PENDING_ROWS dicts are also empty.
```

No row is registered as pending; every REQUIRED / STRUCTURAL row
in the v0.19 catalog is backed by a real fixture function.

## 19. Non-mutations confirmed

```text
- The live OperatorSession.state field-for-field equals the
  pre-call state after every read-only dispatch, every failed
  dispatch, and every absorbed-PersistenceError autosave attempt
  on every fixture path.
- The source DB file byte-equals the pre-call file after every
  read-only dispatch, every failed dispatch, and every absorbed-
  PersistenceError autosave attempt.
- No new OperatorSession field appears beyond the two Phase 3.10c
  additions (autosave_config + last_autosave_status).
- No sqlite3.Connection / Cursor / subprocess / socket / file /
  callable / curses object appears in any session field.
- No tick() call occurs inside any Phase 3.10c dispatcher or
  inside maybe_autosave_after_mutation.
- No save_session call occurs from any read-only / failed
  dispatch.
- No @atexit / signal handler / threading / asyncio loop fires
  inside brain/ui/autosave.py.
- The autosave entry point lives only at the post-dispatch site
  in OperatorSession.dispatch; no /step / /stream-promote
  dispatcher body invokes autosave directly.
- maybe_autosave_after_mutation NEVER raises; PersistenceError
  is absorbed into the typed status report.
```

## 20. Risks observed

```text
- The closed read-only verb list in I-AUTOSAVE-10 must stay in
  sync with the OperatorCommand enum. A future enum member added
  without explicit classification will fall through to "trigger
  unknown" and maybe_autosave_after_mutation will return None
  (safe-by-default). The Step 20 integrated audit re-checks
  this contract.

- Outcome-detection contract: _dispatch_step and
  _dispatch_stream_promote must continue to return Optional[bool].
  A future refactor that drops the return value would silently
  break the autosave trigger. I-AUTOSAVE-14 asserts the return
  type via the resource audit; any change must update that
  fixture.

- The autosave-absent posture for brain/ui/persistence_ops.py
  (I-OPSHARDEN-11) and brain/ui/persistence_observe.py
  (I-OBSERVE-10) must continue to hold; adding any autosave hook
  to those modules would fail their static audits. The Step 20
  integrated audit re-checks the three-module autosave-absence
  set.

- I-PERSIST-16's STRUCTURAL registration calls back into
  check_i_persist_12_static_audit. The two rows are now
  intentionally coupled: if I-PERSIST-12 fails, I-PERSIST-16
  also fails. This is the intended behavior (both rows assert
  properties of brain/ui/persistence.py).
```

No risk currently blocks campaign progression to Step 20.

## 21. Conclusion

Phase 3.10c (Autosave Policy) is fully implemented, audited, and
green.

```text
Verdict: PASS.
Next:    Step 20 — integrated Phase 3.10 audit (ties tracks
         A + B + C together).
```
