# PHASE3_10C_AUTOSAVE_KICKOFF.md

## Purpose

Define the Phase 3.10c Autosave Policy build shape before any
catalog or runtime change. This is a planning artifact only. It
does not edit `INVARIANT_CATALOG.md`, `tools/catalog.py`,
`brain/_catalog_ids.py`, `brain/invariants.py`, `brain/ui/`,
`brain/ui/persistence.py`, `brain/ui/persistence_ops.py`,
`brain/ui/persistence_observe.py`, or any guarded kernel path.

Phase 3.10c is the third track of the Phase 3.10 campaign. The
review gate at Step 16 gates implementation. The default-off,
opt-in autosave landing in this track must satisfy every rule in
the synthesis section 4 and never widen the surface beyond what
the catalog patch plan binds at Step 15.

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
Prior artifact:  PHASE3_10C_AUTOSAVE_SYNTHESIS.md
```

Existing surfaces this kickoff must consume (not modify outside the
documented extension points):

```text
brain.ui.persistence:
  PersistenceError
  SessionStoreConfig
  SCHEMA_VERSION_V1
  SUPPORTED_SCHEMA_VERSIONS
  CATALOG_VERSION_STAMP
  PersistentSessionSnapshot
  SaveSessionResult
  LoadSessionResult
  snapshot_session                  (Phase 3.10b public helper)
  save_session(session, config, *, now=None) -> SaveSessionResult
  load_session(config, *, rebuild_candidates_if_missing=True)
      -> tuple[OperatorSession, LoadSessionResult]

brain.ui.persistence_ops:
  OPS_REPORT_TEXT_MAX_LEN = 256
  (no autosave entry point; the static audit forbids one)

brain.ui.persistence_observe:
  (no autosave entry point; the static audit forbids one)

brain.ui.session.OperatorSession
  (Phase 3.9 + Phase 3.10a/b frozen-by-convention record;
   session_store_config: Optional[SessionStoreConfig] exists;
   Phase 3.10c adds at most two new optional fields per Section 7)

brain.ui.commands.OperatorCommand
brain.ui.commands.Command / make_command
brain.ui.command_line.LocalCommandLine.parse
brain.ui.__main__.main / build_arg_parser / build_default_session
```

---

## 2. Module placement decision

Two candidate placements were called out in the synthesis. This
kickoff proposes:

```text
Option K-A: brain/ui/autosave.py + brain/ui/fixtures/autosave_*.py
```

Rationale:

```text
- Autosave is the most policy-loaded track. A dedicated module
  isolates the Step 16 review gate diff to a single file plus its
  fixtures + a small set of adjacent edits (commands.py,
  command_line.py, session.py, __main__.py).
- The static audit can target brain/ui/autosave.py precisely. The
  Phase 3.10a/b modules' static audits (I-OPSHARDEN-12,
  I-OBSERVE-06) already reject autosave hooks; placing autosave
  in its own file means none of those audits need to widen.
- Folding into persistence_ops.py would mix the read-mostly
  Phase 3.10a helpers with the policy-loaded autosave logic and
  force the I-OPSHARDEN-12 static audit to widen.
- The file is small (~150-300 lines); a new module is
  appropriate for the audit-surface isolation it buys.
```

The corrigenda (Step 14) is the canonical place to lock placement.
For the rest of this kickoff, file paths use the
`brain/ui/autosave.py` placement.

---

## 3. AutosaveMode enum

```python
class AutosaveMode(str, Enum):
    """Finite closed enumeration of autosave modes.

    OFF is the default on every cold start. AFTER_SUCCESSFUL_MUTATION
    is the only non-off mode authorized by Phase 3.10c v1; future
    modes require an explicit catalog row family extension.
    """

    OFF = "off"
    AFTER_SUCCESSFUL_MUTATION = "after-successful-mutation"


SUPPORTED_AUTOSAVE_MODES: frozenset[AutosaveMode] = frozenset({
    AutosaveMode.OFF,
    AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
})
```

Rules:

```text
- The enum is `(str, Enum)` so its serialized form is a bounded
  printable identifier (parallel to LlmRuntimeMode / OperatorCommand).
- AutosaveMode.OFF is the default at session construction and at
  CLI parse time.
- Membership is closed; any value outside SUPPORTED_AUTOSAVE_MODES
  raises ValueError on AutosaveConfig construction.
- Adding a new member requires an explicit corrigenda extension
  and a new catalog row family expansion.
```

---

## 4. AutosaveTrigger enum

```python
class AutosaveTrigger(str, Enum):
    """Finite closed enumeration of autosave triggers.

    The trigger is the *cause* of the post-dispatch autosave
    invocation. Only mutating dispatches that succeeded appear here;
    the static audit (catalog row in Step 15) confirms the trigger
    set is closed and that no read-only dispatch is wired to fire
    autosave.
    """

    STEP_TICK = "step_tick"
    STREAM_PROMOTE = "stream_promote"


SUPPORTED_AUTOSAVE_TRIGGERS: frozenset[AutosaveTrigger] = frozenset({
    AutosaveTrigger.STEP_TICK,
    AutosaveTrigger.STREAM_PROMOTE,
})
```

Rules:

```text
- STEP_TICK fires when /step succeeded and BrainState mutated
  (i.e. the dispatcher completed without error and the tick
  advanced).
- STREAM_PROMOTE fires when /stream-promote successfully queued
  exactly one PerceptEvent candidate (the dispatcher completed
  without error and event_queue grew).
- The enum does NOT include /stream (text-stream chunk append):
  appending a text-stream chunk does mutate session-local stream
  state, but the substrate already buffers many chunks before any
  promotion. Autosaving on every /stream would create churn.
  The corrigenda is the place to revisit this; for v1 we limit
  autosave to STEP_TICK + STREAM_PROMOTE.
- The enum does NOT include /save-session: a successful
  /save-session already wrote the snapshot, so re-triggering
  autosave would be redundant. The post-dispatch site checks the
  command kind and skips when it equals SAVE_SESSION.
- The enum does NOT include /load-session: load swaps the live
  session to a candidate that already matches the saved snapshot;
  autosaving after load would be a no-op write.
```

---

## 5. Typed records

```python
@dataclass(frozen=True, slots=True)
class AutosaveConfig:
    """Immutable autosave configuration carried on OperatorSession.

    Carries the active mode plus a denormalized path string copy
    for display. The actual SessionStoreConfig still lives on
    OperatorSession.session_store_config; autosave never duplicates
    the path semantics, only the display string.
    """

    mode: AutosaveMode = AutosaveMode.OFF
    db_path_str: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.mode, AutosaveMode):
            raise TypeError(
                "AutosaveConfig.mode must be an AutosaveMode "
                f"(got {type(self.mode).__name__})"
            )
        if self.mode not in SUPPORTED_AUTOSAVE_MODES:
            raise ValueError(
                "AutosaveConfig.mode must be in "
                f"{sorted(m.value for m in SUPPORTED_AUTOSAVE_MODES)!r} "
                f"(got {self.mode!r})"
            )
        if not isinstance(self.db_path_str, str):
            raise TypeError(
                "AutosaveConfig.db_path_str must be a str "
                f"(got {type(self.db_path_str).__name__})"
            )
        if len(self.db_path_str) > OPS_REPORT_TEXT_MAX_LEN:
            raise ValueError(
                "AutosaveConfig.db_path_str length "
                f"{len(self.db_path_str)} exceeds "
                f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
            )
        if self.db_path_str and not self.db_path_str.isprintable():
            raise ValueError(
                "AutosaveConfig.db_path_str must be printable "
                f"(got {self.db_path_str!r})"
            )
        # mode=OFF + db_path_str="" is valid (the cold-start default).
        # A non-OFF mode requires a non-empty db_path_str.
        if self.mode is not AutosaveMode.OFF and not self.db_path_str:
            raise ValueError(
                "AutosaveConfig with non-OFF mode requires a "
                "non-empty db_path_str"
            )


@dataclass(frozen=True, slots=True)
class AutosaveStatusReport:
    """Bounded read-only snapshot of the autosave subsystem state."""

    mode: AutosaveMode
    db_path_str: str
    last_attempt_tick: int            # 0 iff never attempted
    last_attempt_outcome: str         # "" | "ok" | "error"
    last_attempt_at: str              # ISO-8601 UTC; "" iff never
    last_attempt_trigger: str         # AutosaveTrigger.value; "" iff never
    last_error_text: str              # "" iff never failed

    def __post_init__(self) -> None:
        # bounded enforcement identical to AutosaveConfig +
        # SessionStatusReport patterns; outcome is one of the closed
        # strings {"", "ok", "error"}; trigger is in
        # SUPPORTED_AUTOSAVE_TRIGGERS.value U {""}.
        ...
```

Construction rules:

```text
- Every string field bounded by OPS_REPORT_TEXT_MAX_LEN=256.
- All integer fields non-negative.
- mode validated against SUPPORTED_AUTOSAVE_MODES.
- last_attempt_outcome validated against {"", "ok", "error"}.
- last_attempt_trigger validated against
  {t.value for t in SUPPORTED_AUTOSAVE_TRIGGERS} U {""}.
- ISO-8601 timestamps generated with
  datetime.datetime.now(tz=UTC).isoformat() (parallel to
  brain.ui.persistence._utc_now_iso).
```

---

## 6. Helper signatures

```python
def autosave_status(session: OperatorSession) -> AutosaveStatusReport:
    """Read OperatorSession.autosave_config /
    OperatorSession.last_autosave_status; never touches disk;
    returns a bounded AutosaveStatusReport."""


def autosave_enable(
    session: OperatorSession,
    mode: AutosaveMode,
) -> AutosaveStatusReport:
    """Switch session.autosave_config to the requested mode.

    Requires session.session_store_config != None when mode is
    non-OFF. Raises PersistenceError on invalid mode (any value
    outside SUPPORTED_AUTOSAVE_MODES) or missing DB config.
    Returns the resulting AutosaveStatusReport. Never invokes
    save_session itself; mutation triggers do that on the next
    eligible dispatch."""


def autosave_disable(session: OperatorSession) -> AutosaveStatusReport:
    """Switch session.autosave_config back to AutosaveMode.OFF.

    Always succeeds (idempotent). Returns the resulting
    AutosaveStatusReport. Never invokes save_session."""


def maybe_autosave_after_mutation(
    session: OperatorSession,
    *,
    triggered_by: AutosaveTrigger,
    now: Optional[datetime.datetime] = None,
) -> Optional[AutosaveStatusReport]:
    """Post-dispatch autosave trigger.

    Called by OperatorSession.dispatch AFTER a mutating dispatch
    returned cleanly. Behavior:
      1. If session.autosave_config is None or its mode is OFF:
         return None. No write occurs.
      2. If session.autosave_config.mode is
         AutosaveMode.AFTER_SUCCESSFUL_MUTATION and triggered_by
         is in SUPPORTED_AUTOSAVE_TRIGGERS:
         - call save_session(session, session.session_store_config,
                              now=now);
         - on success: update session.last_autosave_status with
           outcome="ok"; return the new report.
         - on PersistenceError: update session.last_autosave_status
           with outcome="error" + last_error_text; return the new
           report.
      3. The helper never raises; PersistenceError is absorbed and
         surfaced through the typed report.
    """
```

Behavior contracts (catalog plan binds these):

```text
- maybe_autosave_after_mutation is the ONLY autosave entry point
  reachable from any dispatch path.
- The dispatcher invokes it exactly once per eligible dispatch
  (after the dispatch body returned and BEFORE the dispatcher
  returns to its caller).
- It never opens a sqlite3.Connection directly; it routes
  entirely through brain.ui.persistence.save_session.
- It never calls tick().
- It never imports curses.
- It never stores a Connection or callable on OperatorSession.
- It never registers @atexit / signal / threading / asyncio.
```

---

## 7. Session attachment

Phase 3.10c adds at most two new fields to `OperatorSession`:

```text
autosave_config: Optional[AutosaveConfig] = None
last_autosave_status: Optional[AutosaveStatusReport] = None
```

`_ALLOWED_SESSION_ATTRS` is extended with both names. Both fields
carry frozen / slotted records over bounded primitives; neither
holds a `sqlite3.Connection`, callable, socket, subprocess handle,
or LLM client.

It does NOT add:

```text
- a callable trigger map (triggers are static enum members).
- a background timer / thread / asyncio loop / atexit hook /
  signal handler.
- a list of pending autosave attempts (autosave is one-shot per
  mutating dispatch).
- a sqlite3.Connection (forbidden).
- a "last autosave snapshot" cache (the saved DB is the source of
  truth; the snapshot lives only in the DB).
```

---

## 8. CLI flag

```text
--autosave-mode {off, after-successful-mutation}
                Sets the startup autosave mode. Default OFF.
                Without --session-db, supplying a non-off value
                raises a local argument error BEFORE
                parse_llm_runtime_args.
```

Behavior rules:

```text
- The default is "off" regardless of any ambient environment
  variable. (Parallel to the Phase 3.8b LLM toggle's "the default
  is offline regardless of ANTHROPIC_API_KEY" rule.)
- Combining --autosave-mode after-successful-mutation without
  --session-db raises argparse error code 2 BEFORE main()
  proceeds.
- --autosave-mode off is the same as omitting the flag (no error
  even if --session-db is unset; mode OFF needs no DB).
- The flag is parsed alongside --session-db. The Phase 3.10a/b
  short-circuit flags (--db-status / --db-verify / --db-backup)
  do NOT inherit the autosave mode (those flags exit before
  curses initialization; autosave only matters once dispatch
  runs).
- A bounded startup line announces the resolved autosave mode:
    "brain.ui: autosave mode = off"
    "brain.ui: autosave mode = after-successful-mutation"
```

---

## 9. Typed commands

```text
OperatorCommand.AUTOSAVE_STATUS    = "autosave_status"
OperatorCommand.AUTOSAVE_ENABLE    = "autosave_enable"
OperatorCommand.AUTOSAVE_DISABLE   = "autosave_disable"
```

Payloads:

```python
@dataclass(frozen=True, slots=True)
class AutosaveEnablePayload:
    mode: AutosaveMode
```

`AUTOSAVE_STATUS` and `AUTOSAVE_DISABLE` take no payload; they extend
`_COMMANDS_WITHOUT_PAYLOAD`. `AUTOSAVE_ENABLE` carries an
`AutosaveEnablePayload`.

Parser additions in `LocalCommandLine.parse`:

```text
/autosave-status                   no args; rejects trailing args.
/autosave-disable                  no args; rejects trailing args.
/autosave-enable <mode>            mode required; must parse as
                                   one of the closed enum value
                                   strings ("off",
                                   "after-successful-mutation").
                                   Trailing extra args raise
                                   LocalCommandError.
```

Dispatcher additions in `OperatorSession`:

```text
_dispatch_autosave_status      calls autosave_status(self) and
                                surfaces the bounded report
                                through status_message.
_dispatch_autosave_enable      requires session_store_config;
                                calls autosave_enable(self, mode);
                                surfaces the bounded report or
                                bounded error.
_dispatch_autosave_disable     calls autosave_disable(self);
                                surfaces the bounded report.
```

Post-dispatch site in `OperatorSession.dispatch`:

```text
After the per-command dispatcher returns, the central dispatch
method checks:
  1. session.autosave_config is not None
  2. session.autosave_config.mode is
     AutosaveMode.AFTER_SUCCESSFUL_MUTATION
  3. command.kind is in {STEP_TICK, STREAM_PROMOTE}
  4. the dispatch outcome is "success" (status_message ends with
     a non-error sentinel; the corrigenda may instead inspect a
     boolean returned by each sub-dispatcher — the exact
     check is for the corrigenda to pin)
  5. session.session_store_config is not None
If all five hold, call maybe_autosave_after_mutation(self,
triggered_by=...). The returned report (or None) is stored in
session.last_autosave_status and surfaced through the existing
status / error pipeline.
```

Dispatch rules (every one drives a catalog row in Step 15):

```text
- /autosave-status executes even when session_store_config is
  None or autosave_config is None (the report carries the answer).
- /autosave-enable fails closed if session_store_config is None.
- /autosave-disable always succeeds (idempotent).
- None of the three commands calls tick().
- maybe_autosave_after_mutation never fires after a failed
  dispatch.
- maybe_autosave_after_mutation never fires after a read-only
  dispatch.
- maybe_autosave_after_mutation invokes save_session through the
  existing helper; no second save code path.
- The post-dispatch site catches PersistenceError, populates the
  status report, and surfaces a bounded error_message; no
  exception propagates into the curses wrapper.
```

---

## 10. Disposition of I-PERSIST-16

`I-PERSIST-16` (Phase 3.9 NOT-EXERCISED, autosave path absent) is
the placeholder row that holds the "no autosave today" position. It
is enforced structurally by `persistence_static_audit.py` rejecting
tick-adjacent and ambient-trigger autosave hooks in
`brain/ui/persistence.py`.

The kickoff proposes:

```text
- I-PERSIST-16 is RETIRED at Step 17.
- A new REQUIRED row I-AUTOSAVE-12 takes its place and asserts:
    "Autosave reuses save_session and lives only in
     brain/ui/autosave.py at the post-dispatch site; no autosave
     call exists in brain/ui/persistence.py."
- The autosave-absence audit (the Phase 3.9 static check) is
  preserved against brain/ui/persistence.py: the persistence
  module itself still must not call save_session under
  tick-adjacent paths. The new I-AUTOSAVE-* row family augments
  rather than replaces this check.
- The Phase 3.10a I-OPSHARDEN-11 and Phase 3.10b I-OBSERVE-10
  defensive autosave-absent audits remain unchanged: neither
  persistence_ops.py nor persistence_observe.py may invoke
  autosave or save_session.
```

The corrigenda (Step 14) confirms or amends this disposition. The
catalog plan (Step 15) encodes it.

---

## 11. Likely file budget

For Step 17 (autosave catalog patch):

```text
INVARIANT_CATALOG.md            v0.18 -> v0.19 banner; new "Phase
                                3.10c Autosave Policy invariants"
                                section; I-PERSIST-16 marked as
                                retired with a pointer to
                                I-AUTOSAVE-12.
tools/catalog.py                EXPECTED_COUNTS update.
brain/_catalog_ids.py           regenerated via generate-ids.
brain/invariants.py             _PHASE3_10C_PENDING_ROWS for the
                                new REQUIRED + STRUCTURAL rows.
brain/ui/autosave.py            empty marker module.
README.md                       v0.19 banner; catalog history
                                line; companion-docs section.
CURRENT_MISSION.md              catalog banner v0.18 -> v0.19.
CURRENT_CAMPAIGN.md             catalog banner v0.18 -> v0.19.
```

For Step 18 (autosave implementation):

```text
brain/ui/autosave.py            full implementation.
brain/ui/__main__.py            --autosave-mode flag + startup
                                line.
brain/ui/commands.py            AUTOSAVE_STATUS / ENABLE / DISABLE
                                enum members + AutosaveEnablePayload
                                + _COMMANDS_WITHOUT_PAYLOAD update.
brain/ui/command_line.py        /autosave-status, /autosave-enable
                                <mode>, /autosave-disable verbs.
brain/ui/session.py             autosave_config / last_autosave_status
                                fields; _ALLOWED_SESSION_ATTRS
                                update; _dispatch_autosave_status /
                                _dispatch_autosave_enable /
                                _dispatch_autosave_disable; the
                                post-dispatch trigger site.
brain/ui/fixtures/autosave_default_off.py             new
brain/ui/fixtures/autosave_requires_db.py             new
brain/ui/fixtures/autosave_mode_closed.py             new
brain/ui/fixtures/autosave_trigger_set.py             new
brain/ui/fixtures/autosave_no_tick_call.py            new
brain/ui/fixtures/autosave_no_after_read_only.py      new
brain/ui/fixtures/autosave_no_after_failure.py        new
brain/ui/fixtures/autosave_failure_preserves.py       new
brain/ui/fixtures/autosave_no_background.py           new
brain/ui/fixtures/autosave_single_save_path.py        new
brain/ui/fixtures/autosave_status_after_event.py      new
brain/ui/fixtures/autosave_static_audit.py            new
brain/ui/fixtures/autosave_resource_audit.py          new
brain/invariants.py             FIXTURE_MODULES extension; drain
                                _PHASE3_10C_PENDING_ROWS.
README.md                       document /autosave-* verbs and
                                --autosave-mode (after Step 18).
```

For Step 19 (autosave dry run + audit):

```text
PHASE3_10C_AUTOSAVE_DRY_RUN.md   deterministic scripted walk.
PHASE3_10C_AUTOSAVE_AUDIT.md     row-by-row audit.
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
brain/ui/persistence.py        (no public API change; the autosave
                                path reuses the existing save_session)
brain/ui/persistence_ops.py     (no change in 3.10c)
brain/ui/persistence_observe.py (no change in 3.10c)
```

---

## 12. Fixture roster sketch

The Step 15 catalog patch plan binds exact row IDs. The likely
fixtures (~13 total):

```text
autosave_default_off.py
  - On every cold-start build_default_session(),
    session.autosave_config is None OR
    session.autosave_config.mode is AutosaveMode.OFF.
  - argparse default for --autosave-mode is "off".
  - Two independent fixtures (session-construction default
    + CLI parse default) consolidated into this one module.

autosave_requires_db.py
  - autosave_enable(session, AFTER_SUCCESSFUL_MUTATION) raises
    PersistenceError when session.session_store_config is None.
  - --autosave-mode after-successful-mutation without
    --session-db raises argparse error.

autosave_mode_closed.py
  - SUPPORTED_AUTOSAVE_MODES is a frozenset.
  - AutosaveMode is (str, Enum) with exactly OFF and
    AFTER_SUCCESSFUL_MUTATION.
  - AutosaveConfig with any other mode value raises.

autosave_trigger_set.py
  - SUPPORTED_AUTOSAVE_TRIGGERS is a frozenset.
  - AutosaveTrigger is (str, Enum) with exactly STEP_TICK and
    STREAM_PROMOTE.
  - maybe_autosave_after_mutation with an unknown trigger raises
    or returns None (the corrigenda pins the exact behavior).

autosave_no_tick_call.py
  - Triggering autosave during a /step dispatch does NOT route
    through tick(). The autosave call site lives AFTER the
    sub-dispatcher returned, not inside tick().
  - Static AST check that maybe_autosave_after_mutation contains
    no call to tick.

autosave_no_after_read_only.py
  - For every read-only verb in the closed list (/state, /tick,
    /output, /worldlet, /repl, /clear, /help, /quit,
    /stream-summary, /stream-candidates, /session-status,
    /db-status, /db-verify, /db-summary, /profile-summary,
    /stream-db-summary, /db-diff, /db-backup, /autosave-status,
    /save-session, /load-session), running the dispatch with
    autosave enabled does NOT invoke save_session a second time.

autosave_no_after_failure.py
  - A failed /step (e.g. empty queue) with autosave enabled
    leaves session.last_autosave_status unchanged.
  - A failed /stream-promote with autosave enabled leaves
    session.last_autosave_status unchanged.

autosave_failure_preserves.py
  - Simulated IntegrityError during the autosave save_session
    call -> ROLLBACK; live session preserved; AutosaveStatusReport.
    last_attempt_outcome = "error"; last_error_text populated.
  - A subsequent successful /step + autosave succeeds normally.

autosave_no_background.py
  - Static AST check that brain/ui/autosave.py contains no
    threading / asyncio / signal / atexit / curses callback.

autosave_single_save_path.py
  - Static AST check that brain/ui/autosave.py invokes
    save_session and no other save helper.
  - Static check that no second save_session helper exists in
    brain/ui/persistence.py or anywhere else.

autosave_status_after_event.py
  - After a successful /step that triggered autosave,
    session.last_autosave_status.last_attempt_outcome == "ok"
    with a non-empty last_attempt_at timestamp and
    last_attempt_trigger == "step_tick".

autosave_static_audit.py
  - AST audit over brain/ui/autosave.py. Imports confined to
    the documented seam set. No pickle / shelve / marshal /
    subprocess / socket / urllib / http / requests / curses /
    brain.tick / brain.tlica internals / brain.llm. No
    importlib / __import__ / eval / exec / compile / atexit /
    threading / asyncio / signal. Module-level statements
    limited to imports / constants / function defs / class defs
    (+ docstring).

autosave_resource_audit.py
  - autosave_config and last_autosave_status fields are frozen
    records over bounded primitives; no Connection / Cursor /
    callable / socket / curses object appears.
  - _ALLOWED_SESSION_ATTRS contains exactly the documented set
    plus the two new autosave field names.
```

OBSERVED row (Step 19 audit):

```text
- autosave_dry_run is documented in PHASE3_10C_AUTOSAVE_DRY_RUN.md
  (scripted walk: launch with --autosave-mode
  after-successful-mutation --session-db PATH; run /stream / /step
  / /stream-promote / /step; verify the saved DB advances; toggle
  /autosave-disable; verify subsequent /step does not re-save).
  The fixture either runs the deterministic walk or cites the
  audit.
```

---

## 13. Failure isolation contract

Phase 3.10c reuses the Phase 3.9 envelope. Every Phase 3.10c
helper:

```text
- raises PersistenceError on invalid argument or unrecoverable
  precondition failure (only autosave_enable can raise this way;
  autosave_disable is idempotent and never raises; autosave_status
  never raises);
- returns a typed report with last_attempt_outcome="error" +
  last_error_text populated on operational failure (transactional
  failure of the autosave save_session call);
- never partially mutates the live OperatorSession (the live
  session's BrainState and stream state are unchanged on
  autosave failure);
- never partially writes the session DB (BEGIN IMMEDIATE /
  ROLLBACK guarantees this);
- closes every sqlite3.Connection inside the existing
  save_session helper's `with conn:` block;
- runs inside a try / except in the post-dispatch site so no
  exception reaches the curses wrapper.
```

---

## 14. Stop point

Next artifact:

```text
PHASE3_10C_AUTOSAVE_CORRIGENDA.md
```

The corrigenda should audit this kickoff for:

```text
- module placement (Option K-A locked here; corrigenda confirms);
- AutosaveMode enum (members; default; parser shape);
- AutosaveTrigger enum (members; closure; STREAM exclusion);
- typed-record shapes (every field bounded; no float; no repr;
  no callable / Connection);
- helper signatures (autosave_status / autosave_enable /
  autosave_disable / maybe_autosave_after_mutation);
- CLI flag shape (--autosave-mode);
- closed parser verb additions (/autosave-status / -enable /
  -disable);
- closed OperatorCommand additions;
- post-dispatch trigger site (exact location in
  OperatorSession.dispatch; outcome detection);
- session attachment (autosave_config + last_autosave_status;
  _ALLOWED_SESSION_ATTRS extension);
- I-PERSIST-16 disposition (retire vs preserve);
- which Phase 3.10c rows should be REQUIRED / STRUCTURAL /
  OBSERVED / NOT-EXERCISED;
- fixture roster (subsumption; row-to-fixture mapping).
```

After the corrigenda, the catalog patch plan (Step 15) binds rows
and stops at the Step 16 review gate C before any catalog or
runtime implementation begins.
