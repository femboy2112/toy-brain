# PHASE3_10C_AUTOSAVE_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.10c Autosave Policy track before any catalog,
runtime, or fixture work. This is a planning artifact only. It does
not edit `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `brain/invariants.py`, `brain/ui/`,
`brain/ui/persistence.py`, `brain/ui/persistence_ops.py`,
`brain/ui/persistence_observe.py`, or any guarded kernel path.

Phase 3.10c is the third and final track of the Phase 3.10
Operational Hardening + Persistence Observability + Autosave
campaign. Tracks A (Operational Hardening) and B (Persistence
Observability) landed at v0.18 with the Step 11 audit verdict PASS.
This synthesis follows the existing pattern (synthesis → kickoff →
corrigenda → catalog patch plan → review gate) for the autosave
track.

The track is review-gated. Implementation does NOT begin until the
Step 16 review gate C accepts the Step 15 autosave catalog patch
plan.

```text
Status: PROPOSED / REVIEW-GATED / DEFAULT-OFF
```

Autosave is **not** authorized by default. The campaign explicitly
preserves the "default off on every cold start" rule throughout.

---

## 1. Baseline

```text
Catalog version:  v0.18
REQUIRED:        201
STRUCTURAL:       79
NOT-EXERCISED:    10
DEFERRED:         12
OBSERVED:         14
Total fixtures:  120

Latest completed track:
  Phase 3.10a Operational Hardening      (PASS — Step 11)
  Phase 3.10b Persistence Observability   (PASS — Step 11)

Preflight gates at HEAD:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  python3 -m brain.invariants run            202 / 79 / 7-OBS green
  bash tools/check_all.sh                    All checks passed
```

---

## 2. Why autosave follows Phase 3.10a/b

Phase 3.10a + 3.10b gave the operator:

```text
- /session-status / /db-status / /db-verify   visible session + DB state
- /db-summary / /profile-summary /
  /stream-db-summary / /db-diff                read-only saved-state inspection
- /db-backup                                   byte-faithful explicit copy
```

These tracks made the saved DB safely operatable. The operator can
inspect, verify, compare, and back up the saved state without ever
mutating the live `OperatorSession` or the saved file (except via
the explicit `/db-backup` destination).

What is still missing:

```text
- the operator must remember to type /save-session after every
  /step or accepted /stream-promote. Forgetting loses everything
  produced since the last manual save.
- there is no "is autosave on" indicator. The default is "no
  autosave"; the operator has no need to ask because autosave
  doesn't exist. Once it does, the question becomes load-bearing.
- there is no operator-facing way to enable autosave without
  re-launching the process with a different flag.
```

Phase 3.10c adds exactly one finite, default-off, opt-in autosave
mode plus three typed verbs to manage it. The mode is the smallest
useful one: fire exactly once after an accepted `/step` or accepted
`/stream-promote` that mutated kernel state. No background thread,
no signal handler, no atexit, no implicit on-quit save.

---

## 3. Why autosave is the most dangerous track

Autosave turns persistence from "an explicit operator action" into
"a side-effect of other actions". That makes the design questions
much harder than tracks A and B. The list from the synthesis is
restated here to anchor the kickoff:

```text
- when does autosave fire? after every /step? after every
  accepted /stream-promote? after every operator command? on
  /quit?
- where does it write? always to the configured DB? to a
  journal file? to a rolling backup?
- does autosave block tick()? if not, what is the consistency
  contract under a crash mid-tick?
- how does autosave interact with cold-start failure recovery?
- what prevents autosave from writing inside a static fixture
  run?
- what is the operator-visible "is autosave on" indicator?
- does autosave failure stop the session, demote to manual, or
  silently retry?
```

Phase 3.10c locks one finite answer to each of these. The corrigenda
and the catalog patch plan bind every answer to a catalog row so a
future PR cannot quietly widen the surface.

---

## 4. What Phase 3.10c — Autosave Policy — adds

Target verbs:

```text
/autosave-status     show current autosave mode + last attempt
                     outcome + last attempt tick + last attempt at
                     timestamp
/autosave-enable     switch from OFF to AFTER_SUCCESSFUL_MUTATION
                     (the single allowed non-off mode in v1);
                     requires the configured session DB
/autosave-disable    switch back to OFF
```

Proposed CLI flag (corrigenda locks the final shape):

```text
--autosave-mode {off, after-successful-mutation}
                     default OFF. Sets the startup mode. Only
                     honored when --session-db is also supplied.
                     Without --session-db, supplying a non-off
                     mode raises a local argument error before
                     curses initialization.
```

Single allowed non-off mode:

```text
after-successful-mutation
  Fire exactly once after an accepted /step or accepted
  /stream-promote that mutated BrainState or session-local
  stream state. Other dispatch paths do NOT trigger autosave.
```

Rules (every one drives a catalog row in Step 15):

```text
- Default is OFF on every cold start, regardless of prior session.
- Requires --session-db PATH (or session_store_config set at session
  construction time); /autosave-enable without a configured DB
  fails closed with a bounded local UI error and leaves
  autosave_config.mode = OFF.
- The trigger set is finite, declared in source as a closed
  enum, and audited by a fixture.
- Autosave never fires inside tick(). The autosave call site is
  AFTER OperatorSession.dispatch returns, not inside the tick
  path or inside the dispatcher's body.
- Autosave never fires after a failed command (Command dispatch
  raised, or status_message ends with the bounded failure
  prefix).
- Autosave never fires after a read-only command (/state, /tick,
  /output, /worldlet, /repl, /clear, /help, /quit, /stream-summary,
  /stream-candidates, /session-status, /db-status, /db-verify,
  /db-summary, /profile-summary, /stream-db-summary, /db-diff,
  /db-backup, /autosave-status). These produce reports or status
  text but do not mutate kernel state.
- Autosave is invoked through the SAME save_session helper used by
  /save-session. There is no second save code path; the static
  audit (Step 15 catalog row) rejects any new save helper.
- Autosave failure is bounded local UI status; the live session
  is preserved exactly as the Phase 3.9 transactional contract
  requires. The autosave_status report reflects the failure for
  operator visibility.
- No background thread, no signal handler, no atexit autosave
  hook, no asyncio loop, no curses callback writes to the DB.
- The autosave entry point is reachable ONLY from the
  post-dispatch site in OperatorSession.dispatch. The static
  audit confirms this.
```

---

## 5. How Phase 3.10c preserves the Phase 3.9 contract

Autosave reuses the Phase 3.9 `save_session` pipeline:

```text
- BEGIN IMMEDIATE / COMMIT / ROLLBACK transaction discipline.
- SessionStoreConfig immutable across the autosave call.
- Public builders are not re-invoked (save reads the live
  session via the same _snapshot_session / public snapshot_session
  helper used by Phase 3.10b).
- assert_state_invariants over the live BrainState happens at the
  /save-session entry path; autosave inherits this property.
- COGITO_ID protection is inherited.
- The session DB is opened inside `with sqlite3.connect(...)` and
  closed before return.
- No sqlite3.Connection lives on OperatorSession.
```

The single difference from `/save-session` is the call site: rather
than the operator typing the verb, the dispatcher checks the active
autosave config after a mutating dispatch returned cleanly and
invokes `save_session` exactly once.

---

## 6. How failed autosave behaves

The Phase 3.9 envelope governs autosave failure too:

```text
- save_session raises PersistenceError on transactional / IO
  failure -> the dispatcher catches it, records the failure in
  AutosaveStatusReport.last_attempt_outcome = "error" and
  last_error_text = <bounded reason>, sets
  session.last_autosave_status, and surfaces a bounded
  error_message ("autosave failed: <reason>") through the
  existing UI pipeline.
- The live OperatorSession is unchanged: save is a write, not a
  swap; PersistenceError is raised before any swap could occur
  in the autosave path (which has no swap step in the first
  place).
- The DB file may exist but reverts to the prior consistent
  state under ROLLBACK.
- A subsequent mutating dispatch re-triggers autosave; the
  operator-visible status reflects the new attempt. Autosave does
  NOT silently retry inside a single dispatch.
- Persistent autosave failure does NOT promote to /save-session
  bypass; the operator must take explicit action (toggle
  /autosave-disable, fix the underlying disk issue, or invoke
  /save-session directly).
```

---

## 7. Resource discipline

Phase 3.9 / 3.10a / 3.10b forbade unsafe resources on
`OperatorSession`. Phase 3.10c must not regress this:

```text
- New OperatorSession fields are limited to:
    autosave_config: Optional[AutosaveConfig]
    last_autosave_status: Optional[AutosaveStatusReport]
  Both are frozen / slotted records over bounded primitives
  (mode enum, bounded path string, integer counters, bounded
  error string, ISO-8601 timestamp string).
- No sqlite3.Connection lives on OperatorSession.
- No thread, signal handler, atexit hook, or asyncio loop is
  registered.
- brain/ui/autosave.py imports are confined to:
    sqlite3 (only if the helper needs explicit handling; the
              Phase 3.10c module can opt to import nothing from
              sqlite3 and route entirely through
              brain.ui.persistence.save_session),
    dataclasses, datetime, enum, pathlib, typing,
    brain.ui.persistence, brain.ui.session,
    brain.ui.commands.
  It does NOT import:
    pickle, shelve, marshal, dill, cloudpickle, joblib,
    subprocess, socket, urllib, http, requests, curses,
    brain.tick, brain.tlica internals, brain.llm.
- No @atexit / signal / threading / asyncio.
```

The static audit fixture rejects every forbidden import or
side-effect.

---

## 8. Boundaries Phase 3.10c must not cross

```text
COGITO_ID remains reserved.
raw text never maps to COGITO_ID.
raw text never mutates BrainState directly.
loaded state must reconstruct through public builders / constructors.
loaded state must pass invariants before becoming active.
failed save / autosave must not mutate the live session.
tick() remains the only TLICA runtime transition route.
/step remains the operator route that calls tick().
offline remains the default LLM mode.
no LLM client / socket / file handle / subprocess handle / callable /
  curses object / sqlite3.Connection on OperatorSession.
autosave is default-OFF on every cold start.
autosave never fires inside tick().
autosave never fires after a failed dispatch.
autosave never fires after a read-only dispatch.
autosave does not introduce a second save code path.
autosave does not introduce a background runner.
no implicit on-quit save.
no automatic export.
no widening of the closed parser verb set beyond
  /autosave-status / /autosave-enable / /autosave-disable.
no migration or schema bump for the autosave config (the v1
  SQLite schema is unchanged; AutosaveConfig and
  AutosaveStatusReport live on OperatorSession, not on the DB).
```

---

## 9. Likely module placement

The kickoff (Step 13) decides one of:

```text
Option K-A: brain/ui/autosave.py
  + add the autosave helpers (autosave_status / autosave_enable /
    autosave_disable / maybe_autosave_after_mutation) as free
    functions in a new module.
  + add new fixtures under brain/ui/fixtures/autosave_*.py.
  + register dispatch handlers in brain/ui/session.py.

Option K-B: fold into brain/ui/persistence_ops.py
  + put the autosave helpers next to the Phase 3.10a operational
    helpers.

Argument for K-A:
  - autosave is the most policy-loaded track. A separate file makes
    the Step 16 review gate a minimal diff.
  - the static audit can target a single file.
  - the file budget keeps autosave logically isolated from the
    read-mostly Phase 3.10a helpers.

Argument for K-B:
  - autosave is small (~150-300 lines). A new module adds import
    surface for a small payload.
```

The corrigenda (Step 14) decides and locks. The catalog patch plan
(Step 15) encodes the chosen file paths in the row table.

---

## 10. Likely catalog row family

The Step 15 catalog patch plan is canonical. The expected family:

```text
I-AUTOSAVE-*
```

Likely themes:

```text
1.  Default OFF on every cold start (audited in two independent
    fixtures: session construction + CLI parse time).
2.  --autosave-mode is a finite enum (only "off" and one non-off
    mode are accepted).
3.  /autosave-enable without --session-db fails closed.
4.  /autosave-enable transitions OFF -> AFTER_SUCCESSFUL_MUTATION
    via the typed dispatcher; /autosave-disable transitions back.
5.  /autosave-status returns a bounded report (mode, db_path_str,
    last_attempt_tick, last_attempt_outcome, last_attempt_at,
    last_error_text).
6.  The trigger set is finite, declared in source as a closed
    enum, audited.
7.  Autosave never fires inside tick().
8.  Autosave never fires after a failed dispatch.
9.  Autosave never fires after a read-only dispatch (the closed
    "never" verb list is audited as a set).
10. Autosave invokes save_session through the existing Phase 3.9
    helper; no second save code path exists.
11. Autosave failure preserves the live session and the DB
    transactional invariant.
12. No @atexit / signal / threading / asyncio / curses callback
    triggers autosave.
13. /autosave-status reflects the last attempt outcome
    deterministically.
14. brain/ui/autosave.py static audit (import set + module-level
    statement audit).
15. Session resource audit (new autosave_config and
    last_autosave_status fields are bounded; no Connection /
    Cursor / callable / socket / curses object).
16. The Phase 3.9 I-PERSIST-16 NOT-EXERCISED autosave-absent row
    is either retired or promoted to REQUIRED (the corrigenda
    decides; the catalog plan binds the migration).
```

Likely expected count delta:

```text
+10 REQUIRED      (rules 1, 3-11, 13)
+ 3 STRUCTURAL    (rules 12, 14, 15)
+ 1 OBSERVED      (autosave dry run)
+ 0 NOT-EXERCISED (I-PERSIST-16 may be retired and replaced; this
                   is the corrigenda's decision)
-or- + 1 NOT-EXERCISED if a future autosave option is held in
     reserve.
```

These numbers are estimates; the Step 15 plan pins them.

---

## 11. Likely file budget (Step 17 + Step 18)

For Step 17 (autosave catalog patch):

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/ui/autosave.py             (empty marker module)
README.md
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
```

For Step 18 (autosave implementation):

```text
brain/ui/autosave.py              full implementation
brain/ui/__main__.py              --autosave-mode flag
brain/ui/commands.py              AUTOSAVE_STATUS / ENABLE /
                                  DISABLE + AutosaveEnablePayload
brain/ui/command_line.py          /autosave-status, /autosave-enable,
                                  /autosave-disable verbs
brain/ui/session.py               autosave_config + last_autosave_status
                                  fields; _dispatch_autosave_status,
                                  _dispatch_autosave_enable,
                                  _dispatch_autosave_disable;
                                  post-dispatch autosave trigger site
brain/ui/fixtures/autosave_*.py   ~11 new fixtures
brain/invariants.py               FIXTURE_MODULES extension; drain
                                  _PHASE3_10C_PENDING_ROWS
```

Excluded unless a later accepted plan reopens them:

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
brain/ui/persistence.py        (no public API change in 3.10c)
brain/ui/persistence_ops.py    (no change in 3.10c)
brain/ui/persistence_observe.py (no change in 3.10c)
```

---

## 12. Risks

```text
- autosave creep: a "small convenience" autosave call appears
  inside tick(), _dispatch_step_tick, _dispatch_stream_promote,
  or any other tick-adjacent path. Mitigation: static audit
  fixture rejects save-helper invocations outside the
  post-dispatch site.

- autosave default drift: a future PR flips the default to on.
  Mitigation: two independent fixtures assert default OFF at
  session construction and at CLI parse time.

- background autosave creep: a future PR adds @atexit / signal /
  threading / asyncio. Mitigation: static audit rejects each of
  these.

- silent failure: autosave fails and the operator does not know.
  Mitigation: AutosaveStatusReport.last_attempt_outcome and
  last_error_text surface the failure; /autosave-status displays
  them; the dispatcher's bounded error_message reports the
  failure once per failure event.

- DB exhaustion: long sessions with many mutations write many
  autosaves, growing the DB. Mitigation: each save is a full
  DELETE-then-INSERT (per Phase 3.9 atomic-save discipline), so
  the DB size is bounded by the snapshot size, not by attempt
  count.

- second save path: a future PR adds a "fast path" autosave
  helper that skips constructor validation. Mitigation: catalog
  row asserts only one save_session entry point exists in
  brain.ui.persistence.

- bypass via direct attribute write: a future PR mutates
  session.autosave_config from a non-dispatch path. Mitigation:
  AutosaveConfig is frozen; _ALLOWED_SESSION_ATTRS audit catches
  attempts to add new attributes; the dispatchers are the only
  documented mutation route for autosave_config.

- crash during autosave: a process crash mid-autosave leaves
  the DB in the pre-save state via BEGIN IMMEDIATE / ROLLBACK.
  Mitigation: this is the Phase 3.9 transactional property,
  inherited.
```

---

## 13. Non-goals

Phase 3.10c does not authorize:

```text
- multi-mode autosave (only one non-off mode lands in v1).
- background autosave / autosave timer / autosave scheduler.
- autosave on /quit (the operator must explicitly /save-session
  before quitting if they want to capture the final state; the
  trigger set is mutation-triggered, not exit-triggered).
- autosave to a journal / rolling backup. The configured session
  DB is the only autosave destination. (Phase 3.10a /db-backup
  remains the explicit byte-faithful copy path.)
- autosave to a network destination.
- autosave to multiple destinations.
- autosave-driven backup retention policies.
- a per-tick autosave (the "after every /step" mode collapses to
  the single AFTER_SUCCESSFUL_MUTATION mode; "after every tick"
  including failed ticks is explicitly disallowed).
- mid-session schema migrations.
- persistence of LLM client / cache / runtime mode (already
  forbidden by Phase 3.9).
- autosave of operator transcripts beyond the bounded session-local
  state already serialized by /save-session.
- a new save_session helper.
- changes to tick() semantics.
- changes to /step / /stream / /stream-promote semantics beyond
  the post-dispatch autosave hook.
- changes to the closed parser verb set beyond /autosave-status,
  /autosave-enable, /autosave-disable.
```

---

## 14. Next artifact

```text
PHASE3_10C_AUTOSAVE_KICKOFF.md
```

The kickoff should define:

```text
- the locked module placement (Option K-A or K-B from Section 9);
- the locked AutosaveMode enum (members, default, parser shape);
- the locked AutosaveTrigger enum (the closed mutating-dispatch set);
- the typed records:
    AutosaveConfig(mode, db_path_str)
    AutosaveStatusReport(mode, db_path_str, last_attempt_tick,
                          last_attempt_outcome, last_attempt_at,
                          last_error_text)
- the helper signatures:
    autosave_status(session)
    autosave_enable(session, mode)
    autosave_disable(session)
    maybe_autosave_after_mutation(session, *, triggered_by)
- the dispatcher wiring (post-dispatch trigger site in
  OperatorSession.dispatch);
- the proposed CLI flag (--autosave-mode);
- the proposed fixture roster sketch (~11 fixtures);
- the disposition of the existing I-PERSIST-16 NOT-EXERCISED row
  (retire / promote / both);
- the stop point before the corrigenda.
```

After the kickoff, the corrigenda (Step 14) audits and locks the
design before the Step 15 catalog patch plan binds the autosave
rows. The campaign stops at the Step 16 review gate C after Step
15 lands. Implementation (Step 18) does NOT begin until that gate
is accepted.
