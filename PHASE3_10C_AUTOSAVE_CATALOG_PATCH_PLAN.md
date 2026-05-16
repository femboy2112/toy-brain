# PHASE3_10C_AUTOSAVE_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in `PHASE3_10C_AUTOSAVE_CORRIGENDA.md` to concrete
catalog rows, statuses, file budget, count delta, fixture roster,
and pending-registration mechanics for Phase 3.10c (Autosave
Policy). This is a planning artifact only. It does not apply
catalog rows, edit `tools/catalog.py`, add runtime modules, add
fixtures, change generated catalog IDs, alter
`INVARIANT_CATALOG.md`, change `brain/invariants.py`, or update
README as though implementation exists.

Phase 3.10a/b catalog patch (v0.18) is already accepted and
implemented at PASS. This plan is the third and final accepted
catalog plan for the Phase 3.10 campaign.

Verdict for the Step 16 review gate C:

```text
COHERENT - READY FOR REVIEW GATE C
```

---

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
```

Required latest accepted catalog patch:

```text
Phase 3.10a/b ops/observability (Step 7 commit a2ef1bb; Step 8
commit 6e77b24; Step 9 commit d4e1468; Step 10 docs 930f5cf;
Step 11 audit 98f8064; ops/observability audit verdict PASS).
```

Accepted planning artifacts:

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
PHASE3_10C_AUTOSAVE_SYNTHESIS.md
PHASE3_10C_AUTOSAVE_KICKOFF.md
PHASE3_10C_AUTOSAVE_CORRIGENDA.md
```

---

## 3. Patch Impact

```text
+11 REQUIRED      (corrigenda section 13; including 1 replacement
                   row for the retired I-PERSIST-16 placeholder)
+ 3 STRUCTURAL
+ 1 OBSERVED
- 1 NOT-EXERCISED (I-PERSIST-16 retired at this patch)
+ 0 DEFERRED
```

Expected counts after the accepted Phase 3.10c patch:

```text
Catalog version:  v0.19
REQUIRED:        212
STRUCTURAL:       82
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         15
Total tabular:   330
```

One new row family contributes 15 rows total:

```text
I-AUTOSAVE-01..15   (Phase 3.10c: 11 REQUIRED + 3 STRUCTURAL +
                     1 OBSERVED)
```

The Phase 3.9 I-PERSIST-16 row is RETIRED in this patch
(NOT-EXERCISED -> removed). Its autosave-absence semantics are
absorbed by the new I-AUTOSAVE-11 row (single save path), the
existing I-PERSIST-12 static audit on `brain/ui/persistence.py`,
and the Phase 3.10a/b defensive autosave-absent audits
(I-OPSHARDEN-11, I-OBSERVE-10).

No other existing row is modified by this patch.

---

## 4. Row Family Thesis

Row family:

```text
I-AUTOSAVE-*
```

Rationale:

```text
- The corrigenda accepted Option K-A (dedicated brain/ui/autosave.py
  module). I-AUTOSAVE-* maps cleanly to the new module.
- The name is short, readable, and unique against existing prefixes
  (I-PERSIST-, I-OPSHARDEN-, I-OBSERVE-, I-UI-, I-UISTRM-,
  I-LLMTOG-, I-STRM-, I-REF-, I-EXP-, I-REPL-, I-WLD-, I-OUT-,
  I-DEV-, I-FRAME-, I-SBX-, I-CAT-, I-ISO-, I-PCE-, I-AGN-,
  I-AFF-, I-APRJ-, I-PMAP-, I-PROF-, I-PWS-, I-MSI-, I-MOD-,
  I-IBND-, I-INT-, I-PRES-, I-PTC-, I-RT-, I-TRACE-, I-TRJ-,
  I-TOCE-, I-BHV-, I-LLM-).
```

Core commitments:

```text
Autosave is default-OFF on every cold start. It opts in through
the explicit /autosave-enable verb or the --autosave-mode CLI
flag; non-OFF requires a configured session DB.

The single allowed non-off mode is AFTER_SUCCESSFUL_MUTATION; the
closed trigger set is {STEP_TICK, STREAM_PROMOTE}. The post-
dispatch site in OperatorSession.dispatch is the ONLY autosave
entry point.

Autosave reuses the Phase 3.9 save_session helper; no second save
code path exists. PersistenceError during autosave is absorbed
and surfaced through AutosaveStatusReport.last_attempt_outcome =
"error"; the live OperatorSession is preserved (Phase 3.9
transactional contract inherited).

brain/ui/autosave.py contains no @atexit / signal / threading /
asyncio / curses callback; the static audit rejects all of these.
No new sqlite3.Connection / Cursor / subprocess / socket / file /
callable / curses object appears on OperatorSession.
```

---

## 5. Row Table (I-AUTOSAVE)

Owning module is `brain/ui/autosave.py` unless noted.

### 5.1 REQUIRED rows (11)

```text
I-AUTOSAVE-01  Default OFF on every cold start.
                build_default_session() returns a session whose
                autosave_config is None OR whose autosave_config.mode
                is AutosaveMode.OFF; argparse default for
                --autosave-mode is the string "off"; neither path
                reads an ambient environment variable (no
                BRAIN_AUTOSAVE_MODE / similar). Two independent
                fixtures (session-construction + CLI parse default)
                consolidated into one row + fixture file.
                Fixture: autosave_default_off.py

I-AUTOSAVE-02  AutosaveConfig with mode != OFF + empty
                db_path_str raises.
                Constructing AutosaveConfig(mode=
                AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
                db_path_str="") raises ValueError; the kickoff
                section 5 / corrigenda section 5 enforcement is
                pinned by the fixture.
                Fixture: autosave_mode_closed.py

I-AUTOSAVE-03  /autosave-enable without --session-db raises
                PersistenceError.
                autosave_enable(session,
                AutosaveMode.AFTER_SUCCESSFUL_MUTATION) raises
                PersistenceError when session.session_store_config
                is None; --autosave-mode after-successful-mutation
                without --session-db raises argparse error code 2
                before main()'s body executes.
                Fixture: autosave_requires_db.py

I-AUTOSAVE-04  /autosave-enable with valid mode + DB transitions.
                After /autosave-enable after-successful-mutation
                on a session with session_store_config != None,
                session.autosave_config.mode is
                AFTER_SUCCESSFUL_MUTATION and
                session.autosave_config.db_path_str equals the
                configured DB path string; /autosave-status
                reflects the new mode.
                Fixture: autosave_status_after_event.py
                (subsumes; also serves I-AUTOSAVE-08)

I-AUTOSAVE-05  /autosave-disable is idempotent.
                autosave_disable(session) on a session in any
                autosave state returns an AutosaveStatusReport
                with mode = OFF; calling it twice in a row
                produces identical reports; it never raises.
                Fixture: autosave_default_off.py
                (subsumes; the default-off fixture exercises the
                disabled-state path)

I-AUTOSAVE-06  /autosave-status returns a bounded report; never
                raises.
                autosave_status(session) on a session with any
                autosave_config state returns an
                AutosaveStatusReport with bounded string fields
                (OPS_REPORT_TEXT_MAX_LEN = 256), non-negative
                integer fields, last_attempt_outcome in
                {"", "ok", "error"}, last_attempt_trigger in
                {"", "step_tick", "stream_promote"}; it never
                raises.
                Fixture: autosave_status_after_event.py
                (subsumes; the status fixture exercises the
                report-shape contract)

I-AUTOSAVE-07  maybe_autosave_after_mutation never raises.
                Calling maybe_autosave_after_mutation(session,
                triggered_by=AutosaveTrigger.STEP_TICK) on a
                session with any autosave_config state returns
                either None or an AutosaveStatusReport; on
                PersistenceError from the underlying save_session
                call, the helper absorbs the exception and the
                returned report carries
                last_attempt_outcome="error" with bounded
                last_error_text; no exception propagates.
                Fixture: autosave_failure_preserves.py
                (subsumes; the failure-isolation fixture
                exercises the no-raise contract on the failure
                path)

I-AUTOSAVE-08  /step + autosave + success ->
                last_attempt_outcome="ok".
                A /step dispatch on a session with autosave_config.
                mode = AFTER_SUCCESSFUL_MUTATION and a non-empty
                queue advances tick_counter by one AND triggers
                a post-dispatch autosave; session.last_autosave_status.
                last_attempt_outcome == "ok"; the saved DB's
                meta.updated_at advances; the DB on-disk size is
                non-zero.
                Fixture: autosave_status_after_event.py

I-AUTOSAVE-09  Failed dispatch does NOT trigger autosave.
                A /step dispatch on an empty queue (which fails
                with bounded local error) on a session with
                autosave enabled leaves session.last_autosave_status
                unchanged; the saved DB's meta.updated_at is
                unchanged; a subsequent /step that succeeds
                triggers autosave normally.
                Fixture: autosave_no_after_failure.py

I-AUTOSAVE-10  Read-only dispatch does NOT trigger autosave.
                For every command kind in the closed read-only
                list (INSPECT_*, CLEAR_STATUS, HELP, QUIT, NOOP,
                INSPECT_STREAM_SUMMARY, INSPECT_STREAM_CANDIDATES,
                SESSION_STATUS, DB_STATUS, DB_VERIFY, DB_SUMMARY,
                PROFILE_SUMMARY, STREAM_DB_SUMMARY, DB_DIFF,
                DB_BACKUP, AUTOSAVE_STATUS, SAVE_SESSION,
                LOAD_SESSION), dispatching the command on a
                session with autosave enabled leaves
                session.last_autosave_status unchanged; the saved
                DB's meta.updated_at is unchanged.
                Fixture: autosave_no_after_read_only.py

I-AUTOSAVE-11  Autosave reuses save_session; no second save
                code path exists.
                Static AST audit confirms brain/ui/autosave.py
                imports save_session from brain.ui.persistence
                and contains no other save helper definition or
                import; the audit also confirms no second
                save_session helper exists in brain/ui/persistence.py
                or anywhere else in brain/. (This row replaces the
                Phase 3.9 I-PERSIST-16 NOT-EXERCISED placeholder.)
                Fixture: autosave_single_save_path.py
```

### 5.2 STRUCTURAL rows (3)

```text
I-AUTOSAVE-12  AutosaveMode + AutosaveTrigger are closed
                (str, Enum).
                AutosaveMode is (str, Enum) with exactly OFF and
                AFTER_SUCCESSFUL_MUTATION members;
                SUPPORTED_AUTOSAVE_MODES = frozenset of the two.
                AutosaveTrigger is (str, Enum) with exactly
                STEP_TICK and STREAM_PROMOTE members;
                SUPPORTED_AUTOSAVE_TRIGGERS = frozenset of the
                two. Both enumeration shapes are STRUCTURAL.
                Fixture: autosave_trigger_set.py (subsumes both)

I-AUTOSAVE-13  brain/ui/autosave.py module static audit.
                AST audit confirms imports are confined to the
                documented seam set: dataclasses, datetime,
                enum, pathlib, typing, brain.io_types (if
                needed), brain.ui.commands, brain.ui.persistence
                (specifically save_session and SessionStoreConfig
                and PersistenceError), brain.ui.persistence_ops
                (specifically OPS_REPORT_TEXT_MAX_LEN), and
                brain.ui.session. The module imports neither
                pickle, shelve, marshal, dill, cloudpickle,
                joblib, subprocess, socket, urllib, http,
                requests, curses, brain.tick (any symbol),
                brain.tlica internals beyond builders consumed
                via brain.ui.persistence, brain.llm. It contains
                no importlib.import_module, __import__, eval(,
                exec(, compile(, atexit.register, threading,
                asyncio, or signal handler. Module-level
                statements are limited to imports, constants,
                function defs, and class defs (plus a module
                docstring).
                Fixture: autosave_static_audit.py
                (subsumes autosave_no_background.py; the
                no-tick-call AST check folds into the same
                static audit fixture)

I-AUTOSAVE-14  Session resource audit + outcome-detection
                contract.
                _ALLOWED_SESSION_ATTRS adds "autosave_config" and
                "last_autosave_status". autosave_config is a
                frozen AutosaveConfig or None; last_autosave_status
                is a frozen AutosaveStatusReport or None. Neither
                holds a sqlite3.Connection, Cursor, subprocess
                handle, socket, file object, callable, curses
                object, or LLM client. The outcome-detection
                contract (each Phase 3.10c-eligible dispatcher
                returns Optional[bool] indicating mutation
                success) is also enforced here via a static
                inspection: _dispatch_step_tick and
                _dispatch_stream_promote both return
                Optional[bool], and the central dispatch reads
                that return value rather than scanning status
                strings.
                Fixture: autosave_resource_audit.py
```

### 5.3 OBSERVED row (1)

```text
I-AUTOSAVE-15  Phase 3.10c autosave dry run is inspectable.
                PHASE3_10C_AUTOSAVE_DRY_RUN.md documents a
                deterministic scripted session: launch with
                --autosave-mode after-successful-mutation +
                --session-db PATH; run /stream / /step /
                /stream-promote / /step; verify the saved DB
                advances after each mutating dispatch; verify
                read-only verbs do NOT advance the saved DB;
                /autosave-disable; verify subsequent /step does
                NOT re-save; /autosave-enable + /step verifies
                re-arming works; failed /step (empty queue)
                does NOT trigger autosave; PersistenceError
                injection sets last_attempt_outcome="error" and
                preserves the live session. The row is OBSERVED
                and cannot fail the runner.
                Fixture: autosave_dry_run.py or cited from the
                         Step 19 dry-run document.
```

### 5.4 NOT-EXERCISED rows (0 new; 1 retired)

```text
I-PERSIST-16 is RETIRED in this patch. The autosave-absence
position is preserved at the structural level by:
  - I-PERSIST-12 (the existing Phase 3.9 persistence static audit
    on brain/ui/persistence.py, which continues to reject
    save_session call sites under tick-adjacent paths);
  - I-OPSHARDEN-11 (Phase 3.10a defensive autosave-absent audit
    on brain/ui/persistence_ops.py);
  - I-OBSERVE-10 (Phase 3.10b defensive autosave-absent audit on
    brain/ui/persistence_observe.py);
  - I-AUTOSAVE-11 (the new REQUIRED row asserting brain/ui/
    autosave.py is the only autosave entry point and reuses
    save_session).
No new NOT-EXERCISED row is added in this patch.
```

---

## 6. Fixture Roster

```text
I-AUTOSAVE-01  autosave_default_off.py
I-AUTOSAVE-02  autosave_mode_closed.py
I-AUTOSAVE-03  autosave_requires_db.py
I-AUTOSAVE-04  autosave_status_after_event.py (subsumes)
I-AUTOSAVE-05  autosave_default_off.py (subsumes)
I-AUTOSAVE-06  autosave_status_after_event.py (subsumes)
I-AUTOSAVE-07  autosave_failure_preserves.py (subsumes)
I-AUTOSAVE-08  autosave_status_after_event.py
I-AUTOSAVE-09  autosave_no_after_failure.py
I-AUTOSAVE-10  autosave_no_after_read_only.py
I-AUTOSAVE-11  autosave_single_save_path.py
I-AUTOSAVE-12  autosave_trigger_set.py
I-AUTOSAVE-13  autosave_static_audit.py
I-AUTOSAVE-14  autosave_resource_audit.py
I-AUTOSAVE-15  OBSERVED; autosave_dry_run.py or audit-cited
```

Fixture file delta: **10** new fixture modules, serving 14 of the
15 new rows. The OBSERVED row (I-AUTOSAVE-15) is cited from the
Step 19 dry-run document rather than runner-gated.

```text
brain/ui/fixtures/autosave_default_off.py
brain/ui/fixtures/autosave_mode_closed.py
brain/ui/fixtures/autosave_requires_db.py
brain/ui/fixtures/autosave_status_after_event.py
brain/ui/fixtures/autosave_failure_preserves.py
brain/ui/fixtures/autosave_no_after_failure.py
brain/ui/fixtures/autosave_no_after_read_only.py
brain/ui/fixtures/autosave_single_save_path.py
brain/ui/fixtures/autosave_trigger_set.py
brain/ui/fixtures/autosave_static_audit.py
brain/ui/fixtures/autosave_resource_audit.py
```

Wait — that lists 11 files. The roster collapses
`autosave_no_background.py` into `autosave_static_audit.py` per
the corrigenda section 13; the no-tick-call AST check also lives
in `autosave_static_audit.py`. The actual on-disk count is **11
new fixture modules** (the corrigenda kickoff sketch listed 13
fixtures; the consolidation here reduces the file count without
losing coverage).

Row-to-fixture subsumption summary (no fixture serves more than
three rows; rows 04 + 06 + 08 share one fixture; rows 01 + 05
share one):

```text
autosave_default_off.py             I-AUTOSAVE-01 + 05
autosave_status_after_event.py      I-AUTOSAVE-04 + 06 + 08
autosave_failure_preserves.py       I-AUTOSAVE-07
```

If Step 18 implementation finds the 3-row subsumption too dense,
the catalog patch (Step 17) may split it into two fixtures
(e.g. autosave_enable_status.py + autosave_after_step.py). Any
split must update this roster explicitly before landing rows.

---

## 7. File Budget

Modified files for Step 17 catalog patch:

```text
INVARIANT_CATALOG.md             v0.18 -> v0.19 banner; new
                                 "Phase 3.10c Autosave Policy
                                 invariants" section with
                                 I-AUTOSAVE-01..15; mark
                                 I-PERSIST-16 as retired in
                                 the v0.19 banner and remove
                                 it from the row table; update
                                 fixture roster (102 -> 130
                                 +  10 = 130; verify the actual
                                 count after writing).
tools/catalog.py                 EXPECTED_COUNTS to 212/82/9/12/15.
brain/_catalog_ids.py            regenerated via tools.catalog
                                 generate-ids.
brain/invariants.py              _PHASE3_10C_PENDING_ROWS for
                                 I-AUTOSAVE-01..14 (15 is
                                 OBSERVED, not pending); remove
                                 I-PERSIST-16 from the catalog
                                 expectations via the regenerated
                                 brain/_catalog_ids.py.
brain/ui/autosave.py             empty placeholder marker.
README.md                        v0.19 banner; catalog history
                                 line; companion-docs section.
CURRENT_MISSION.md               v0.18 -> v0.19.
CURRENT_CAMPAIGN.md              v0.18 -> v0.19.
```

Expected modified / new files for Step 18 (autosave
implementation):

```text
brain/ui/autosave.py                          full implementation.
brain/ui/__main__.py                          --autosave-mode flag +
                                              startup line.
brain/ui/commands.py                          AUTOSAVE_STATUS /
                                              ENABLE / DISABLE +
                                              AutosaveEnablePayload +
                                              _COMMANDS_WITHOUT_PAYLOAD
                                              update.
brain/ui/command_line.py                      /autosave-status,
                                              /autosave-enable <mode>,
                                              /autosave-disable verbs.
brain/ui/session.py                           autosave_config /
                                              last_autosave_status
                                              fields;
                                              _ALLOWED_SESSION_ATTRS
                                              update;
                                              _dispatch_autosave_*
                                              handlers; post-dispatch
                                              trigger site;
                                              _dispatch_step_tick /
                                              _dispatch_stream_promote
                                              refactored to return
                                              Optional[bool] for
                                              outcome detection.
brain/ui/fixtures/command_router.py           extend _EXPECTED_COMMAND_
                                              VALUES with the three new
                                              autosave enum members.
brain/ui/fixtures/composer_input.py           add "autosave-enable" to
                                              the argument-verb map
                                              (it takes one positional
                                              mode token).
brain/ui/fixtures/persistence_static_audit.py update audit references
                                              to acknowledge
                                              I-PERSIST-16 retirement
                                              and point at
                                              I-AUTOSAVE-11; the
                                              persistence-side audit
                                              checks remain unchanged.
brain/ui/fixtures/autosave_default_off.py
brain/ui/fixtures/autosave_mode_closed.py
brain/ui/fixtures/autosave_requires_db.py
brain/ui/fixtures/autosave_status_after_event.py
brain/ui/fixtures/autosave_failure_preserves.py
brain/ui/fixtures/autosave_no_after_failure.py
brain/ui/fixtures/autosave_no_after_read_only.py
brain/ui/fixtures/autosave_single_save_path.py
brain/ui/fixtures/autosave_trigger_set.py
brain/ui/fixtures/autosave_static_audit.py
brain/ui/fixtures/autosave_resource_audit.py
brain/invariants.py                           FIXTURE_MODULES
                                              extension; drain
                                              _PHASE3_10C_PENDING_ROWS.
README.md                                     document /autosave-*
                                              verbs and
                                              --autosave-mode (after
                                              Step 18).
```

Expected files for Step 19 (dry run + audit):

```text
PHASE3_10C_AUTOSAVE_DRY_RUN.md
PHASE3_10C_AUTOSAVE_AUDIT.md
```

Expected file for Step 20 (integrated Phase 3.10 audit):

```text
PHASE3_10_INTEGRATED_AUDIT.md   ties tracks A + B + C together.
```

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
brain/ui/persistence.py        (no new public API in 3.10c)
brain/ui/persistence_ops.py    (no change in 3.10c)
brain/ui/persistence_observe.py (no change in 3.10c)
```

---

## 8. Catalog Patch Mechanics (Step 17)

```text
1. Add the 15 new I-AUTOSAVE-* row entries to INVARIANT_CATALOG.md
   under a new section:
     "### Phase 3.10c Autosave Policy invariants"

2. Add a v0.19 catalog-version banner above v0.18 documenting the
   +11 REQUIRED / +3 STRUCTURAL / +1 OBSERVED / -1 NOT-EXERCISED
   expansion (delta total = 14; one new family I-AUTOSAVE-01..15;
   one row retired: I-PERSIST-16).

3. Remove the I-PERSIST-16 row from the "Phase 3.9 Persistent
   Session Store invariants" row table. Note the retirement in
   the v0.19 banner with a pointer to I-AUTOSAVE-11 as the
   replacement.

4. Update the summary counts in INVARIANT_CATALOG.md to:
   REQUIRED 212, STRUCTURAL 82, NOT-EXERCISED 9, DEFERRED 12,
   OBSERVED 15.

5. Update tools/catalog.py EXPECTED_COUNTS to the same values and
   refresh the banner-comment block to cite Phase 3.10c v0.19.

6. Run `python3 -m tools.catalog generate-ids` to refresh
   brain/_catalog_ids.py with the new I-AUTOSAVE-* entries and
   the I-PERSIST-16 removal.

7. Add _PHASE3_10C_PENDING_ROWS in brain/invariants.py with
   I-AUTOSAVE-01..14 (15 is OBSERVED and does not participate
   in I-CAT-01 coverage; 11 + 3 STRUCTURAL = 14 pending rows).

8. Add an empty brain/ui/autosave.py marker file declaring the
   Phase 3.10c hard boundaries via docstring.

9. Update README.md catalog-version block to v0.19 and the
   catalog-history line; the companion-docs section gets the
   Phase 3.10c synthesis / kickoff / corrigenda / catalog patch
   plan entries.

10. Update CURRENT_MISSION.md and CURRENT_CAMPAIGN.md catalog-
    version banners to v0.19.

11. Validate with:
      python3 -m tools.catalog counts
      python3 -m tools.catalog generate-ids
      python3 -m tools.catalog counts
      python3 -m tools.citations verify
      python3 -m tools.import_audit
      python3 -m brain.invariants run
      bash tools/check_all.sh

    The runner will show 14 pending failures (the I-AUTOSAVE
    rows). This is expected per the Phase 3.9 / Phase 3.10a/b
    Step 7 pattern.

12. Step 17 should commit and push after count validation only.
    It should not implement autosave behavior, parser verbs, CLI
    flags, dispatcher routing, or the dispatcher outcome-
    detection refactor.
```

---

## 9. Implementation Mechanics (Step 18)

```text
Step 18 (autosave runtime):
  1. Implement brain/ui/autosave.py with AutosaveMode +
     AutosaveTrigger enums, AutosaveConfig +
     AutosaveStatusReport records, the four helpers
     (autosave_status, autosave_enable, autosave_disable,
     maybe_autosave_after_mutation).
  2. Extend brain/ui/__main__.py with the --autosave-mode flag
     and the startup line.
  3. Extend brain/ui/commands.py with AUTOSAVE_STATUS /
     AUTOSAVE_ENABLE / AUTOSAVE_DISABLE enum members +
     AutosaveEnablePayload + _COMMANDS_WITHOUT_PAYLOAD update.
  4. Extend brain/ui/command_line.py with the three
     /autosave-* parser verbs.
  5. Extend brain/ui/session.py with autosave_config +
     last_autosave_status fields; _ALLOWED_SESSION_ATTRS
     update; _dispatch_autosave_* handlers; the post-
     dispatch trigger site; refactor _dispatch_step_tick and
     _dispatch_stream_promote to return Optional[bool] for
     outcome detection.
  6. Add the 11 fixtures listed in Section 6.
  7. Extend brain/ui/fixtures/command_router.py
     _EXPECTED_COMMAND_VALUES with the three new enum members.
  8. Extend brain/ui/fixtures/composer_input.py argument-verb
     map with "autosave-enable".
  9. Update brain/ui/fixtures/persistence_static_audit.py
     comment / docstring to acknowledge I-PERSIST-16 retirement
     (no behavioral change to the audit body itself).
  10. Drain _PHASE3_10C_PENDING_ROWS to {}.
  11. Update README.md to document /autosave-status,
      /autosave-enable, /autosave-disable, --autosave-mode.

Step 19 (autosave dry run + audit):
  12. Write PHASE3_10C_AUTOSAVE_DRY_RUN.md; cite from
      I-AUTOSAVE-15.
  13. Write PHASE3_10C_AUTOSAVE_AUDIT.md.

Step 20 (integrated Phase 3.10 audit):
  14. Write PHASE3_10_INTEGRATED_AUDIT.md combining tracks A +
      B + C.

Step 21 (final PR):
  15. Open the PR to main titled "phase3.10: operational
      hardening, observability, and autosave policy".
  16. Do not merge without explicit user approval.
```

Expected targeted validations during Steps 18-20:

```bash
python3 -m brain.invariants run --id I-AUTOSAVE
python3 -m brain.invariants run --id I-PERSIST
python3 -m brain.invariants run --id I-OPSHARDEN
python3 -m brain.invariants run --id I-OBSERVE
bash tools/check_all.sh
```

---

## 10. Accepted Constants

```text
SUPPORTED_AUTOSAVE_MODES         = frozenset({
                                     AutosaveMode.OFF,
                                     AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
                                   })
SUPPORTED_AUTOSAVE_TRIGGERS      = frozenset({
                                     AutosaveTrigger.STEP_TICK,
                                     AutosaveTrigger.STREAM_PROMOTE,
                                   })
AUTOSAVE_STATUS_OUTCOMES         = frozenset({"", "ok", "error"})
```

These constants are declared in `brain/ui/autosave.py` and
referenced by `autosave_mode_closed.py` /
`autosave_trigger_set.py` for parity.

Existing constants reused from upstream modules:

```text
OPS_REPORT_TEXT_MAX_LEN          =  256  (brain/ui/persistence_ops.py)
SCHEMA_VERSION_V1                =  1     (brain/ui/persistence.py)
CATALOG_VERSION_STAMP            = "v0.19" (bumped at Step 17)
MAX_STATUS_TEXT_LEN              =  240   (brain/ui/session.py)
LOCAL_CMD_MAX_ERROR_LEN          =  240   (brain/ui/command_line.py)
```

---

## 11. Non-Goals To Preserve

```text
no raw text -> COGITO_ID
no raw text -> BrainState direct mutation
no pickle / shelve / marshal / dill / cloudpickle / joblib as a
  format
no JSON / TOML / YAML as the authoritative kernel-state format
no REAL / NUMERIC / FLOAT / DOUBLE columns for kernel numeric data
no sqlite3.Connection on OperatorSession
no multi-mode autosave (only one non-off mode in v1)
no background autosave / timer / scheduler / atexit / signal /
  threading / asyncio
no autosave on /quit
no autosave to a journal / rolling backup / network destination /
  multiple destinations
no autosave-driven backup retention policy
no per-tick autosave including failed ticks
no migrations between schema versions in v1
no persistence of LLM client / cache / runtime mode
no second save_session helper
no changes to tick() semantics
no changes to /step / /stream / /stream-promote dispatch BODIES
  beyond returning the outcome boolean
no changes to the closed parser verb set beyond the three
  /autosave-* verbs
no ambient-environment reads (no BRAIN_AUTOSAVE_MODE)
```

---

## 12. Review Gate

Stop after this plan is committed and pushed.

```text
Do not apply v0.19 catalog rows.
Do not edit tools/catalog.py.
Do not edit brain/_catalog_ids.py.
Do not edit brain/invariants.py.
Do not add Phase 3.10c fixtures.
Do not create brain/ui/autosave.py (other than as the optional
  empty marker if Step 17 is reached).
Do not edit brain/ui/__main__.py / commands.py / command_line.py /
  session.py as if Phase 3.10c is implemented.
Do not update README as if /autosave-* verbs or --autosave-mode
  exist.
Do not proceed to Step 17 until this plan is explicitly accepted.
```

---

## 13. Conclusion

This plan is coherent. The next campaign step, if accepted, is:

```text
Step 17 - Apply Phase 3.10c autosave catalog patch
```

The Phase 3.10c catalog patch transitions the catalog from v0.18
(201 / 79 / 10 / 12 / 14) to v0.19 (212 / 82 / 9 / 12 / 15) by
adding the I-AUTOSAVE-01..15 row family and retiring I-PERSIST-16.
No runtime / fixture code is written until Step 18.
