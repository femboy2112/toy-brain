# PHASE3_10C_AUTOSAVE_CORRIGENDA.md

## Purpose

Audit `PHASE3_10C_AUTOSAVE_KICKOFF.md` before the Phase 3.10c
autosave catalog patch plan. This is a planning artifact only. It
does not edit the catalog, runtime modules, fixtures, README,
traces, scenarios, or guarded kernel paths.

Verdict for Step 14:

```text
COHERENT - PROCEED TO AUTOSAVE CATALOG PATCH PLAN
```

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
Current phase:    Phase 3.10c Autosave Policy
```

Accepted prior artifacts:

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
PHASE3_10C_AUTOSAVE_SYNTHESIS.md
PHASE3_10C_AUTOSAVE_KICKOFF.md
PHASE3_10_OPS_OBSERVABILITY_AUDIT.md   (Step 11 PASS)
```

---

## 2. Module placement

Kickoff proposal:

```text
Option K-A: brain/ui/autosave.py + brain/ui/fixtures/autosave_*.py
```

Corrigendum:

```text
ACCEPTED.
```

Reasoning:

```text
- Autosave is the highest-policy track in Phase 3.10. Isolating
  it in its own module keeps the Step 16 review gate diff
  inspectable.
- The static audit can target a single file.
- Phase 3.10a/b's audits (I-OPSHARDEN-12, I-OBSERVE-06) already
  forbid autosave entry points; placing autosave in autosave.py
  means none of those audits need to widen.
```

The catalog plan must use the owning-module identifier
`brain/ui/autosave.py` for every Phase 3.10c row.

---

## 3. AutosaveMode enum

Kickoff proposal:

```text
AutosaveMode(str, Enum):
  OFF = "off"
  AFTER_SUCCESSFUL_MUTATION = "after-successful-mutation"
SUPPORTED_AUTOSAVE_MODES = frozenset({OFF, AFTER_SUCCESSFUL_MUTATION})
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must include:

```text
- A STRUCTURAL row asserting AutosaveMode is (str, Enum) with
  exactly the two documented members and SUPPORTED_AUTOSAVE_MODES
  matches the enum membership set.
- A REQUIRED row asserting the default is OFF at session
  construction AND at CLI parse time (two-fixture, two-call-site
  audit).
- A REQUIRED row asserting AutosaveConfig with any other mode
  value raises ValueError.
```

---

## 4. AutosaveTrigger enum

Kickoff proposal:

```text
AutosaveTrigger(str, Enum):
  STEP_TICK = "step_tick"
  STREAM_PROMOTE = "stream_promote"
SUPPORTED_AUTOSAVE_TRIGGERS = frozenset({STEP_TICK, STREAM_PROMOTE})

Excluded triggers: /stream, /save-session, /load-session, every
other read-only command, every other dispatcher.
```

Corrigendum:

```text
ACCEPTED FOR v1.
```

Additions required for the catalog plan:

```text
- A STRUCTURAL row asserting AutosaveTrigger is (str, Enum) with
  exactly the two documented members.
- A REQUIRED row asserting maybe_autosave_after_mutation called
  with an unknown trigger returns None (does NOT raise; the
  static audit pins this to make the post-dispatch site
  safe-by-default).
- A REQUIRED row asserting /stream (text-stream chunk append),
  /save-session, /load-session, and every dispatch in the
  closed read-only list do NOT trigger autosave even when
  autosave is enabled.
- The fixture roster collapses these into a single
  autosave_no_after_read_only.py + autosave_trigger_set.py pair
  (the corrigenda already permits two-row collapse).
```

Decision:

```text
The kickoff's trigger set is coherent. The catalog plan must
encode the closed enum and the closed read-only verb list.
```

---

## 5. Typed records

Kickoff proposal:

```text
AutosaveConfig(mode, db_path_str)
AutosaveStatusReport(mode, db_path_str, last_attempt_tick,
                      last_attempt_outcome, last_attempt_at,
                      last_attempt_trigger, last_error_text)
```

Corrigendum:

```text
ACCEPTED WITH BOUND-ENFORCEMENT + OUTCOME / TRIGGER WHITELIST RULES.
```

The catalog plan must require:

```text
- Both records are dataclass(frozen=True, slots=True).
- Every string field bounded by OPS_REPORT_TEXT_MAX_LEN = 256
  (reused from brain.ui.persistence_ops).
- All integer fields non-negative.
- AutosaveConfig with mode != OFF and empty db_path_str raises
  ValueError.
- AutosaveStatusReport.last_attempt_outcome is in
  {"", "ok", "error"} (closed whitelist).
- AutosaveStatusReport.last_attempt_trigger is in
  {t.value for t in SUPPORTED_AUTOSAVE_TRIGGERS} U {""} (closed
  whitelist).
- Neither record carries a Fraction, float, list, callable,
  Connection, Cursor, socket, subprocess handle, file object,
  curses object, or LLM client.
```

---

## 6. Helper signatures

Kickoff proposal:

```text
autosave_status(session) -> AutosaveStatusReport
autosave_enable(session, mode) -> AutosaveStatusReport
autosave_disable(session) -> AutosaveStatusReport
maybe_autosave_after_mutation(session, *, triggered_by, now=None)
  -> Optional[AutosaveStatusReport]
```

Corrigendum:

```text
ACCEPTED.
```

Locked behavior contracts:

```text
- autosave_status reads in-memory fields only; never raises;
  always returns an AutosaveStatusReport (the report's fields are
  populated from session.autosave_config / session.last_autosave_status
  with "" / 0 defaults when those fields are None).
- autosave_enable raises PersistenceError when mode is non-OFF
  and session.session_store_config is None. It NEVER invokes
  save_session itself; future mutating dispatches do that. It
  produces an AutosaveStatusReport on success.
- autosave_disable is idempotent; it never raises. It produces
  an AutosaveStatusReport reflecting the new OFF mode.
- maybe_autosave_after_mutation NEVER raises. It returns None
  when autosave is OFF or when no mode-matched trigger fires;
  otherwise it returns the resulting AutosaveStatusReport. On
  PersistenceError from the underlying save_session call, it
  absorbs the exception and surfaces it through
  last_attempt_outcome="error" + last_error_text.
- All four helpers route every connection through
  brain.ui.persistence.save_session; no direct sqlite3.connect
  call appears in brain/ui/autosave.py.
```

The catalog plan must lock the no-raise contracts in three
REQUIRED rows (autosave_status / autosave_disable / maybe_autosave_after_mutation
each get one) and the PersistenceError-on-missing-DB contract in
one REQUIRED row (autosave_enable).

---

## 7. CLI flag

Kickoff proposal:

```text
--autosave-mode {off, after-successful-mutation}
  default OFF; requires --session-db for non-off mode.
```

Corrigendum:

```text
ACCEPTED.
```

Locked rules:

```text
- The default is "off" regardless of ambient environment
  variables (no BRAIN_AUTOSAVE_MODE / similar; the flag is the
  only knob).
- --autosave-mode after-successful-mutation without --session-db
  raises argparse error code 2 BEFORE main()'s body executes.
- --autosave-mode off is the same as omitting the flag and does
  NOT require --session-db.
- The Phase 3.10a/b short-circuit flags (--db-status, --db-verify,
  --db-backup) ignore --autosave-mode (those flags exit before
  curses initialization; autosave only matters once dispatch is
  active).
- A bounded startup line announces the resolved mode:
    "brain.ui: autosave mode = off"   (always at start)
    "brain.ui: autosave mode = after-successful-mutation"
- /autosave-enable / -disable inside the TUI override the
  startup mode; the next process invocation re-defaults to OFF.
```

The catalog plan must include one REQUIRED row covering the
default-OFF + no-env-read property and one REQUIRED row covering
the non-off-requires-session-db argparse rejection.

---

## 8. Closed parser verb additions

Kickoff proposal:

```text
/autosave-status                       no args
/autosave-disable                      no args
/autosave-enable <mode>                mode required (closed enum)
```

Corrigendum:

```text
ACCEPTED.
```

Parser-shape rules:

```text
- /autosave-status / /autosave-disable reject trailing args as
  LocalCommandError.
- /autosave-enable requires exactly one positional argument that
  parses as one of the closed enum value strings. Unknown values
  raise LocalCommandError before any dispatch.
- The composer parser performs NO shell expansion, glob expansion,
  or variable substitution on the mode token.
```

The catalog plan must include one REQUIRED row per verb covering
the closed-arg shape.

---

## 9. Closed OperatorCommand additions

Kickoff proposal:

```text
AUTOSAVE_STATUS    no payload
AUTOSAVE_ENABLE    AutosaveEnablePayload(mode: AutosaveMode)
AUTOSAVE_DISABLE   no payload
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must include a STRUCTURAL row asserting:

```text
- _COMMANDS_WITHOUT_PAYLOAD is extended to include AUTOSAVE_STATUS
  and AUTOSAVE_DISABLE.
- AUTOSAVE_ENABLE's payload is the only Phase 3.10c payload;
  make_command validates it through AutosaveEnablePayload's
  constructor.
- AutosaveEnablePayload's mode field is type-checked against the
  closed AutosaveMode enum.
```

---

## 10. Post-dispatch trigger site

Kickoff proposal:

```text
After the per-command dispatcher returns, the central dispatch
method checks:
  1. session.autosave_config is not None
  2. session.autosave_config.mode is
     AutosaveMode.AFTER_SUCCESSFUL_MUTATION
  3. command.kind is in {STEP_TICK, STREAM_PROMOTE}
  4. the dispatch outcome is "success"
  5. session.session_store_config is not None
```

Corrigendum:

```text
ACCEPTED WITH EXPLICIT OUTCOME-DETECTION CONTRACT.
```

Outcome-detection rule:

```text
- Each Phase 3.10c-eligible dispatcher (_dispatch_step_tick,
  _dispatch_stream_promote) MUST return a boolean (or update a
  per-call sentinel) the central dispatch reads. Inspecting
  error_message / status_message is brittle and the corrigenda
  forbids it.
- The cleanest shape is to refactor each eligible dispatcher to
  return Optional[bool]: True iff the dispatch mutated kernel
  state; False iff it failed; None for read-only paths.
- An alternative is a thread-unsafe transient attribute on the
  session set per call. The corrigenda PREFERS the return-value
  refactor and the catalog plan locks that as the contract; the
  implementation may use either as long as the static audit
  passes.
- The autosave trigger site is the LAST line of dispatch before
  return. It is NOT inside _dispatch_step_tick / _dispatch_stream_
  promote bodies.
```

The catalog plan must include one REQUIRED row covering the
post-dispatch site location and one STRUCTURAL row covering the
outcome-detection contract.

---

## 11. Session attachment

Kickoff proposal:

```text
autosave_config: Optional[AutosaveConfig] = None
last_autosave_status: Optional[AutosaveStatusReport] = None
```

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must require:

```text
- _ALLOWED_SESSION_ATTRS adds "autosave_config" and
  "last_autosave_status".
- A fixture (autosave_resource_audit.py) confirms every
  OperatorSession field after a /autosave-enable +
  /step + autosave-trigger sequence is one of the allowed types
  (BrainState, OperatorEventQueue, bounded primitives,
  TextStreamHistory, tuple[StreamPromotionCandidate, ...],
  Optional[OutputHistory], Optional[WorldletHistory],
  Optional[ProtoBasicHistory], Optional[TickRecord],
  Optional[SessionStoreConfig], Optional[AutosaveConfig],
  Optional[AutosaveStatusReport]); it rejects sqlite3.Connection,
  subprocess.Popen, socket.socket, file objects, callables,
  curses objects, and LLM clients in any field.
- AutosaveConfig and AutosaveStatusReport themselves contain no
  Connection / callable / socket / curses object.
```

---

## 12. I-PERSIST-16 disposition

Kickoff proposal:

```text
- I-PERSIST-16 RETIRED at Step 17.
- New REQUIRED row I-AUTOSAVE-12 takes its place and asserts the
  autosave path lives only in brain/ui/autosave.py at the
  post-dispatch site; no autosave call in brain/ui/persistence.py.
- Persistence-side autosave-absence audit preserved against
  brain/ui/persistence.py.
- Phase 3.10a/b defensive autosave-absent audits unchanged.
```

Corrigendum:

```text
ACCEPTED.
```

Mechanics:

```text
- The catalog patch at Step 17 strikes I-PERSIST-16 from the
  NOT-EXERCISED count (-1) and adds a new REQUIRED row I-AUTOSAVE-XX
  in the same patch (+1 REQUIRED for the replacement); the net
  effect on the v0.19 banner is one row family added rather than
  two adjustments.
- The persistence_static_audit.py fixture is updated at Step 17
  or 18 to reflect that I-PERSIST-16 is retired and that the
  autosave-absence check on brain/ui/persistence.py is folded
  into the existing I-PERSIST-12 static audit.
- The corrigenda explicitly forbids striking the
  brain/ui/persistence.py autosave-absence check. The check
  remains; only the dedicated NOT-EXERCISED row is retired.
```

---

## 13. Catalog row status assignment

The corrigenda proposes the following status assignment, subject
to the Step 15 catalog patch plan:

```text
REQUIRED (11 rows):
  1.  Default OFF at session construction + CLI parse time (two
      independent fixtures consolidated into one row).
  2.  AutosaveConfig with mode != OFF + empty db_path_str raises.
  3.  /autosave-enable without --session-db raises PersistenceError.
  4.  /autosave-enable with valid mode + DB transitions correctly.
  5.  /autosave-disable is idempotent.
  6.  /autosave-status returns the bounded report (never raises).
  7.  maybe_autosave_after_mutation never raises.
  8.  /step + autosave + success -> last_attempt_outcome="ok".
  9.  Failed dispatch (e.g. empty queue /step) does NOT trigger
      autosave.
  10. Read-only dispatch does NOT trigger autosave (closed verb
      list audited).
  11. Autosave reuses save_session; no second save code path.

STRUCTURAL (3 rows):
  12. AutosaveMode + AutosaveTrigger are closed (str, Enum).
  13. brain/ui/autosave.py static audit (import set + module-level
      statement audit + no @atexit / threading / asyncio / signal).
  14. Session resource audit (autosave_config + last_autosave_status
      bounded; _ALLOWED_SESSION_ATTRS extension).

OBSERVED (1 row):
  15. Phase 3.10c autosave dry run.

NOT-EXERCISED (0 net rows):
  - I-PERSIST-16 RETIRED (-1 NOT-EXERCISED).
  - One new REQUIRED row replaces it (counted above).
```

Resulting count delta (v0.18 -> v0.19):

```text
+11 REQUIRED  (including 1 replacement for retired I-PERSIST-16)
+ 3 STRUCTURAL
+ 1 OBSERVED
- 1 NOT-EXERCISED  (I-PERSIST-16 retired)
+ 0 DEFERRED

REQUIRED       = 201 + 11 = 212
STRUCTURAL     =  79 + 3  =  82
NOT-EXERCISED  =  10 - 1  =   9
DEFERRED       =  12          (unchanged)
OBSERVED       =  14 + 1  =  15
```

The Step 15 plan is canonical and may shift one or two rows between
REQUIRED and STRUCTURAL if a fixture turns out to cover two rows
naturally. Any change must keep the delta totals coherent with the
v0.19 catalog banner.

---

## 14. File budget audit

Kickoff proposal: as listed in kickoff section 11.

Corrigendum:

```text
ACCEPTED.
```

The catalog plan must NOT touch (Phase 3.10c):

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
brain/ui/persistence.py        (no new public API; the autosave
                                path reuses the existing
                                save_session helper)
brain/ui/persistence_ops.py    (no change in 3.10c)
brain/ui/persistence_observe.py (no change in 3.10c)
```

The Phase 3.9 persistence_static_audit.py fixture may need a tiny
allowlist tweak to acknowledge that the autosave-absence check now
references the new I-AUTOSAVE replacement row; the corrigenda
treats this as a fixture-internal documentation update, not a new
catalog row.

---

## 15. Hard non-goals (restated)

The catalog plan must not authorize any of the following in any
Phase 3.10c row, fixture, or runtime path:

```text
- multi-mode autosave (only one non-off mode lands in v1).
- background autosave / timer / scheduler.
- autosave on /quit.
- autosave to a journal / rolling backup.
- autosave to a network destination.
- autosave to multiple destinations.
- autosave-driven backup retention.
- per-tick autosave including failed ticks.
- mid-session schema migrations.
- persistence of LLM client / cache / runtime mode.
- new save_session helper.
- changes to tick() semantics.
- changes to /step / /stream / /stream-promote dispatch bodies
  beyond returning the outcome boolean.
- changes to the closed parser verb set beyond
  /autosave-status / /autosave-enable / /autosave-disable.
- autosave reading or writing operator transcripts beyond
  bounded session-local state.
- autosave reading or writing curses configuration / terminal
  state.
- a sqlite3.Connection on OperatorSession.
- ambient-environment reads from build_default_session() or
  the parser default (no BRAIN_AUTOSAVE_MODE).
```

---

## 16. Stop point

Next artifact:

```text
PHASE3_10C_AUTOSAVE_CATALOG_PATCH_PLAN.md
```

The plan must:

```text
- bind the row family name (I-AUTOSAVE-*);
- bind row statuses per Section 13;
- compute the exact count delta and the resulting v0.19 banner;
- pin the file budget per Section 14 and kickoff Section 11;
- pin the fixture roster (13 modules; row-to-fixture mapping);
- pin pending-registration mechanics (_PHASE3_10C_PENDING_ROWS);
- restate the v0.19 review-gate stop condition;
- record the I-PERSIST-16 retirement mechanics for Step 17.
```

Then the campaign must stop at the Step 16 review gate C. No
catalog row, runtime module, fixture, or README change may land
until the Step 15 plan is explicitly accepted.

## Conclusion

The Phase 3.10c kickoff is coherent. The next artifact is:

```text
PHASE3_10C_AUTOSAVE_CATALOG_PATCH_PLAN.md
```

After that plan is committed and pushed, the campaign halts at the
Step 16 review gate C.
