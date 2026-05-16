# PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.10 Operational Hardening + Persistence
Observability + Autosave campaign before any catalog, runtime, or
fixture work. This is a planning artifact only. It does not edit
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, `brain/ui/`, `brain/ui/persistence.py`, or any
guarded kernel path.

Phase 3.10 follows Phase 3.9 Persistent Session Store because the
explicit SQLite `/save-session` / `/load-session` pair is now landed
but the operator has no way to inspect, verify, back up, or compare
the saved state — and no mature gate for the next obvious step
(autosave). Phase 3.10 closes that gap in three tracks:

```text
A. Operational Hardening      status / verify / backup / bounded recovery
B. Persistence Observability  read-only summaries + saved-vs-live diff
C. Autosave Policy            explicit opt-in autosave behind a second gate
```

Autosave is **not** authorized by default. The campaign explicitly
keeps autosave behind a dedicated review gate (Step 16) after A + B
land. Until that gate, the saved DB is touched only by
`/save-session` and the new explicit Phase 3.10a backup command, and
read only by the Phase 3.10b observability commands.

## 1. Baseline

```text
Catalog version:  v0.17
REQUIRED:        187
STRUCTURAL:       69
NOT-EXERCISED:    10
DEFERRED:         12
OBSERVED:         13
Total tabular:   291
Total fixtures:  106

Latest merged campaign:
  Phase 3.9 Persistent Session Store        (PASS)
  PR #8 merged into main 2026-05-15.

Preflight gates at HEAD:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  python3 -m brain.invariants run            187 / 69 / 7-OBS / 0 red
  bash tools/check_all.sh                    All checks passed
  brain-catalog-lint                         C1 / C2 / C3 / C4 PASS
  brain-campaign-state                       eligible at Step 1
```

## 2. Why operational hardening + observability follow Phase 3.9

Phase 3.9 gave the operator durable session state:

```text
--session-db PATH                  configure session DB
--load-session / --no-load-session explicit cold-start policy
/save-session                      explicit save through builders
/load-session                      explicit load through builders
brain/ui/persistence.py            typed transactional SQLite layer
exact Fraction round-trip          (num INTEGER, den INTEGER) pairs
no autosave                        explicit verbs are the only routes
```

What Phase 3.9 did not give:

```text
- a way to inspect the saved state without loading it;
- a way to verify the saved DB still parses through the public
  builders and passes invariants without swapping it in;
- a way to take a manual backup of the DB before risky operations;
- a way to compare the live session against the saved snapshot;
- an answer to the obvious next operator question "is autosave on?".
```

These gaps are not theoretical. An operator who runs a long session,
runs `/save-session`, then quits, has no way to tell whether the saved
file is intact, what catalog version it claims, or how it differs from
the running session. Loading is the only inspection route, and load is
a session swap. That is exactly the kind of all-or-nothing operation
that makes operators stop trusting persistence.

Phase 3.10a and 3.10b are read-only paths over the same DB Phase 3.9
already authorized. They do not introduce new write paths; they reuse
the existing read path discipline (sqlite3 `mode=ro`) and the existing
typed-snapshot builder discipline. Phase 3.10a adds exactly one new
explicit write path — `/db-backup` — which is bounded to a single
explicit destination and never touches the live session DB except as
the read source for the copy.

## 3. Why autosave is gated separately

Autosave is the obvious follow-up. It is also the most dangerous
because it turns persistence from "an explicit operator action" into
"a side-effect of other actions". The Phase 3.9 boundary list and the
Phase 3.10 mission explicitly forbid autosave landing without its own
accepted review gate.

The autosave policy questions are the same ones the Phase 3.9
synthesis listed and explicitly deferred:

```text
- when does autosave fire? after every /step? after every accepted
  /stream-promote? after every operator command? on /quit?
- where does it write? always to the configured DB? to a journal?
  rolling backups?
- does autosave block tick()? if not, what is the consistency
  contract under crash mid-tick?
- how does autosave interact with cold-start failure recovery?
- what prevents autosave from writing inside a static fixture run?
- what is the operator-visible "is autosave on" indicator?
- does autosave failure stop the session, demote to manual, or
  silently retry?
```

Phase 3.10c locks one finite answer to each of these. The implementation
must remain default-off and explicit opt-in. The autosave campaign work
(Steps 12-19) starts only after the Phase 3.10a/3.10b audit (Step 11) is
PASS and the autosave catalog patch plan (Step 15) is accepted at the
Step 16 review gate.

## 4. What Phase 3.10a — Operational Hardening — adds

Target verbs:

```text
/session-status   read-only live OperatorSession status summary
/db-status        read-only configured-DB existence / size / mtime /
                  schema_version / catalog_version
/db-verify        open the configured DB in mode=ro, reconstruct
                  through builders, run assert_state_invariants on
                  the candidate, DROP the candidate; report PASS / FAIL
/db-backup PATH   copy the configured DB to PATH via sqlite3 Backup
                  API; bounded local report on success / failure;
                  refuses to overwrite an existing file unless an
                  explicit --force flag is accepted by the corrigenda
```

CLI flag additions (proposed; the corrigenda locks these):

```text
--db-backup PATH               one-shot backup at startup, then exit
--db-verify                    one-shot verify at startup, then exit
```

Rules (all driven by I-OPSHARDEN-* catalog rows in Step 5):

```text
- /session-status touches no disk; reads only OperatorSession fields
  and produces bounded text output through the existing UI status
  pipeline.
- /db-status opens the DB in mode=ro, reads the meta table, closes
  the connection in a `with` block. No tick(), no swap, no builder
  call.
- /db-verify reconstructs through the same builders /load-session
  uses, runs assert_state_invariants on the reconstructed candidate,
  then DROPS the candidate (it is never assigned to the live session).
  Failure is reported as a bounded local error.
- /db-backup uses sqlite3.Connection.backup() (the typed page-level
  Backup API), not file copy. This is consistent with Phase 3.9's
  rule that "the session DB is the only save / export path"; backup
  is now a second authorized write path with bounded contract.
- All four commands respect the closed verb set and route through
  OperatorSession.dispatch with new Command kinds.
- No command calls tick().
- No command opens an LLM client, socket, subprocess, or curses
  context.
- No command stores a sqlite3.Connection on OperatorSession.
- All failures are bounded local UI status / error messages.
```

## 5. What Phase 3.10b — Persistence Observability — adds

Target verbs:

```text
/db-summary           bounded row-count + meta summary of the saved DB
                      (profile rows, msi rows, ptcns rows, registry
                       rows, stream-history rows, candidate rows)
/profile-summary      bounded saved-profile listing
                      (content_id + Fraction(num, den) shown as the
                       exact string "num/den"; COGITO_ID always at 1)
/stream-db-summary    bounded saved stream-history summary
                      (chunk count, segment hash if Phase 3.7 stores
                       one, first/last ordinals)
/db-diff              live OperatorSession vs saved snapshot
                      (counts + content_id set diff; values shown
                       as exact Fraction strings)
```

Rules:

```text
- Every command opens the DB in mode=ro and closes it inside `with`.
- No command activates the saved snapshot.
- No command mutates the live BrainState.
- All Fraction values display as exact "num/den" strings, never as
  floats.
- All listings are bounded (per-section row caps; the corrigenda
  fixes the numbers).
- Diff is symmetric over the visible field set; missing-on-one-side
  rows are flagged explicitly. Diff never invents a default value.
- /db-summary is the entry point; the others are drill-downs.
- All four commands route through OperatorSession.dispatch with new
  Command kinds.
- No command calls tick().
```

## 6. What Phase 3.10c — Autosave Policy — adds (gated; Step 16)

Target verbs and flags:

```text
/autosave-status                 show current autosave mode + trigger
                                 + last-attempt outcome
/autosave-enable                 switch from off to the single allowed
                                 mode for this campaign
/autosave-disable                switch back to off; default at startup
--autosave-mode off|<one-mode>   startup flag matching the verbs
```

The single allowed mode is decided at Step 14 / 15. The campaign
explicitly resists a richer mode set in v1. The plausible candidate
is:

```text
after-successful-mutation   fire exactly once after an accepted
                            /step or accepted /stream-promote that
                            mutated BrainState or session-local
                            stream state. Other commands do not
                            trigger autosave.
```

Rules (every one drives a catalog row in Step 15):

```text
- default off on every cold start, regardless of prior session.
- requires --session-db PATH (or --session-db at startup); fails
  closed with a local UI error if no DB is configured.
- finite trigger set, declared in source.
- never fires inside tick(). Autosave runs after dispatch returns,
  not inside the tick path.
- never fires after a failed command.
- never fires after a read-only command (status / verify / summary /
  diff / db-status).
- failure is bounded local UI status; live session is preserved.
- a single typed AutosaveError is raised internally and absorbed by
  the dispatcher.
- no background thread, no signal handler, no atexit autosave.
- the runtime static audit fixture rejects autosave calls outside
  the explicit dispatch path.
```

## 7. How Phase 3.10 preserves constructor / invariant discipline

Phase 3.9 established the load discipline:

```text
1. Open the configured session DB in read-only mode.
2. Read schema_version + catalog_version from meta.
3. Reject unknown schema_version locally.
4. Read typed Persistent*Snapshot records.
5. Reconstruct through public builders / constructors.
6. Run assert_state_invariants on the candidate.
7. Replace the live session only if every step above succeeded.
```

Phase 3.10 reuses this exact pipeline:

```text
/db-verify performs steps 1-6 on a throwaway candidate and reports
the outcome. It does not perform step 7. The candidate is GC'd.

/db-summary, /profile-summary, /stream-db-summary perform steps 1-3
and then read typed Persistent*Snapshot records (step 4) without
running the builders (step 5). The summaries display typed-snapshot
shape, not BrainState shape. This is the safer side of the boundary:
no constructor is invoked unless the operator explicitly asks for it
via /db-verify or /load-session.

/db-diff performs steps 1-3 and reads typed Persistent*Snapshot
records; it compares against the live OperatorSession's projected
typed-snapshot shape (a pure derivation; no DB writes). It does not
invoke builders.

/db-backup opens the source DB in mode=ro and writes pages to the
destination via sqlite3 Backup API. No builder, no invariant runner.
The backup file is a byte-faithful copy; it is also bounded by the
same schema discipline because pages are copied verbatim.

Autosave (Phase 3.10c) reuses /save-session's existing path, including
the BEGIN IMMEDIATE / COMMIT / ROLLBACK transaction discipline, the
public builders, and assert_state_invariants on the live BrainState
prior to write. Autosave does not introduce a second save code path.
```

There is no path in Phase 3.10 that takes a `dict` straight into
`BrainState` or `ScalarProfile`, no path that bypasses the existing
builders, and no path that opens the session DB for write outside the
explicit `/save-session` / `/db-backup` / autosave-after-mutation
triggers.

## 8. How failed status / verify / summary / diff / backup behaves

```text
/session-status failure:
  - Cannot fail at the disk level (no disk read). If a kernel access
    raises, the dispatcher catches it and reports a bounded UI error.
  - The live session is untouched.

/db-status failure:
  - If --session-db is unset: bounded UI error "no session DB
    configured", no disk access.
  - If the file does not exist: bounded UI error "session DB at
    <path> does not exist", no follow-on access.
  - If the file exists but is corrupt / unreadable / wrong schema:
    bounded UI error with the schema_version / catalog_version
    reported as "unknown" or the typed sqlite3 error message.
  - The live session is untouched.

/db-verify failure:
  - At read time: same envelope as /db-status failure.
  - At builder time: typed LoadError / constructor error -> bounded
    UI error; candidate is discarded; live session is untouched.
  - At invariant time: typed InvariantError -> bounded UI error;
    candidate is discarded; live session is untouched.

/db-summary, /profile-summary, /stream-db-summary failure:
  - Read failures envelope is identical to /db-status failure.
  - Type-mismatch (e.g. negative numerator) is a typed error reported
    locally; nothing is partially displayed.

/db-diff failure:
  - Read failures envelope is identical to /db-status failure.
  - The diff routine never invents data on either side: if either
    side is missing a field, the diff row says so explicitly. There
    is no silent "0" or "null" fallback.

/db-backup failure:
  - If --session-db is unset or the file does not exist: bounded UI
    error; no destination touched.
  - If destination exists and --force is not set: bounded UI error;
    destination untouched.
  - If sqlite3.Backup API raises mid-copy: the destination file may
    be partial; the operator-visible status reports "backup failed,
    destination may be partial" with the typed sqlite3 error
    message. The corrigenda decides whether to attempt a destination
    unlink on partial-write failure (default proposed: do not unlink;
    the operator is in a better position to decide).
  - The source session DB is opened in mode=ro and is never modified
    by the backup path.

Autosave failure (Phase 3.10c):
  - Identical envelope to /save-session failure: BEGIN IMMEDIATE /
    ROLLBACK; bounded UI error in status; live session preserved;
    autosave-status reflects the failure for operator visibility.
```

## 9. Resource discipline

Phase 3.9 forbade unsafe resources on `OperatorSession`. Phase 3.10
must not regress this:

```text
OperatorSession.* fields remain in _ALLOWED_SESSION_ATTRS.
No sqlite3.Connection is placed on OperatorSession.
Connections are opened inside save / load / verify / summary / diff /
  backup helpers, used inside `with conn:` blocks, and closed before
  return.
No thread, signal handler, or atexit hook persists session state.
No autosave timer / watchdog / asyncio loop / curses callback writes
  to the DB.
Persistence-adjacent modules import only:
  sqlite3, dataclasses, fractions, datetime, pathlib, typing,
  shutil (only if /db-backup chooses shutil + safety wrappers
    instead of sqlite3 Backup API; the corrigenda must lock the
    choice and the static audit enforces it),
  brain.io_types, brain.tlica.builders, brain.tlica.profile,
  brain.tlica.ptcns, brain.development.text_stream,
  brain.ui.session, brain.ui.persistence (the Phase 3.9 module),
  brain.ui.commands.
The Phase 3.10 modules do NOT import:
  pickle, shelve, marshal, subprocess, socket, urllib, http,
  requests, curses, brain.tick directly, brain.tlica internals
  outside builders, brain.llm runtime clients.
```

The static audit fixture for each new persistence-adjacent module
enforces this import set.

## 10. Boundaries Phase 3.10 must not cross

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
loaded state must reconstruct through public builders / constructors
loaded state must pass invariants before becoming active
failed load / verify / backup must not mutate the live session
failed save / autosave must not mutate the live session
tick() remains the only TLICA runtime transition route
/step remains the operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
no LLM client / socket / file handle / subprocess handle / callable
  / curses object / sqlite3.Connection on OperatorSession
no autosave until Phase 3.10c is explicitly accepted at Step 16
no implicit background persistence
no unreviewed export path
no new typed command outside the closed parser verb set
```

These restate `CURRENT_MISSION.md` and `CURRENT_CAMPAIGN.md`. They
are anchored here for the kickoff and corrigenda.

## 11. Likely module placement

The kickoff (Step 3) must decide one of:

```text
Option K-A: extend brain/ui/persistence.py
  + add status / verify / backup / summary / diff helpers as
    free functions inside the existing module.
  + add new fixture modules under brain/ui/fixtures/.
  + add new Command kinds + dispatch handlers in
    brain/ui/commands.py and brain/ui/session.py.

Option K-B: brain/ui/persistence_status.py (or .ops.py) +
            brain/ui/persistence_summary.py (or .observe.py) +
            brain/ui/autosave.py (Phase 3.10c only)
  + keep brain/ui/persistence.py as the save/load core.
  + add a thin module per track.
  + register each module's static audit fixture separately.
```

Argument for K-A:

```text
The Phase 3.9 layer is already one cohesive file. Status / verify
are direct extensions of the existing schema knowledge. Splitting
adds import surface without separation-of-concerns benefit.
```

Argument for K-B:

```text
Phase 3.10c autosave is the most policy-loaded piece. Keeping it in
its own module limits the static-audit blast radius and makes the
Step 16 review gate a smaller diff.
```

The corrigenda (Step 4) decides and locks. The catalog patch plan
(Step 5 for A+B, Step 15 for C) encodes the chosen file paths in
the row table.

## 12. Likely catalog row family

The catalog patch plans (Step 5 for ops/observability, Step 15 for
autosave) are canonical. The expected families:

```text
I-OPSHARDEN-*   Phase 3.10a operational hardening (status / verify /
                backup)
I-OBSERVE-*     Phase 3.10b persistence observability (summaries +
                diff)
I-AUTOSAVE-*    Phase 3.10c autosave policy (gated; Step 15)
```

Likely Phase 3.10a themes:

```text
1.  /session-status is read-only and bounded.
2.  /db-status is read-only and bounded.
3.  /db-verify reconstructs through builders, runs invariants, DROPS
    the candidate. No live mutation.
4.  /db-verify failure is local; live session preserved.
5.  /db-backup uses bounded byte-faithful copy (sqlite3 Backup API
    or audited shutil + size + checksum guard).
6.  /db-backup refuses to overwrite without explicit --force.
7.  /db-backup never touches the live session.
8.  All four commands route through the closed dispatcher; no
    tick(); no curses; no subprocess.
9.  Status commands display Fractions as exact "num/den" strings.
10. New CLI flags (--db-verify / --db-backup) exit after their
    action; they do not launch curses.
```

Likely Phase 3.10b themes:

```text
1.  /db-summary reads in mode=ro; closed `with` block.
2.  /profile-summary reads in mode=ro; lists exact Fractions; COGITO
    always shown at 1.
3.  /stream-db-summary reads in mode=ro; bounded row count.
4.  /db-diff reads in mode=ro; compares live vs saved typed
    snapshots; missing-on-one-side is explicit.
5.  No observability command activates saved state.
6.  No observability command mutates live BrainState.
7.  All summary outputs are bounded (row caps in source).
8.  Static audit fixture rejects builder calls inside observability
    code paths.
```

Likely Phase 3.10c themes (gated; Step 15 only):

```text
1.  Default is off on every cold start.
2.  --autosave-mode off is the only mode active without explicit
    enable.
3.  /autosave-enable requires a configured session DB.
4.  Finite trigger set declared in source.
5.  Autosave never fires inside tick().
6.  Autosave never fires after a failed command.
7.  Autosave never fires after a read-only command.
8.  Autosave failure is bounded local; live session preserved.
9.  Autosave reuses /save-session's transactional path; no second
    save code path.
10. No background thread / signal handler / atexit autosave.
11. Static audit fixture rejects autosave calls outside the explicit
    dispatch path.
12. /autosave-status reports current mode, last attempt outcome,
    last attempt tick, and last attempt timestamp.
```

REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED splits are deferred
to the respective catalog patch plans.

## 13. Risks

```text
- audit blur: an observability command quietly invokes a builder
  "to be safe", introducing a second load path. Mitigation: static
  audit fixtures per module reject builder imports inside
  observability files.

- diff drift: live-vs-saved diff invents defaults for missing
  fields, leading the operator to believe sides are aligned when
  one is empty. Mitigation: catalog row asserts diff rows are
  explicit about missing-on-one-side; fixtures exercise the
  empty-DB and partial-DB cases.

- backup-as-export: /db-backup is used to route saved state to a
  third-party tool. Mitigation: catalog row asserts /db-backup is
  bounded to the local filesystem and refuses URI destinations
  (no `sqlite://`, `file:` URIs, etc.). The corrigenda locks the
  allowed PATH shape.

- partial backup: /db-backup fails mid-copy and the operator
  cannot tell whether the destination is usable. Mitigation:
  /db-backup status reports the typed sqlite3 error and explicitly
  warns about destination state. /db-verify can be re-run against
  the backup file.

- autosave creep: a "small convenience" autosave call appears in
  tick / step / promote outside the explicit dispatch path.
  Mitigation: static audit fixture rejects save-helper invocations
  outside the dispatcher.

- autosave default drift: a future PR flips the default to on.
  Mitigation: catalog row asserts the default is off at session
  construction and at CLI parse time, in two independent fixtures.

- session DB as event log: autosave fires on every tick, turning
  the DB into a runtime trace. Mitigation: finite trigger set
  declared in source; fixture exercises a /step path and asserts
  exactly one autosave call.

- silent autosave failure: autosave fails and the operator does
  not know. Mitigation: /autosave-status surfaces the last attempt
  outcome, and the status banner reports the failure once per
  failure event.
```

The Step 5 and Step 15 catalog patch plans turn these risks into
testable rows.

## 14. Non-goals

Phase 3.10 does not authorize:

```text
- multi-profile / multi-user persistence
- network-backed persistence
- a replication / hot-standby subsystem
- a richer autosave mode set (only one mode lands; the catalog row
  family asserts the mode set is finite)
- full TickRecord / event-log replay
- schema migration between Phase 3.9 v1 and a future v2
  (still a typed local error)
- persistence of LLM client state, cache contents, or runtime mode
- persistence of operator transcripts beyond what is already
  session-local
- persistence of curses configuration / terminal state
- raw-text-to-COGITO mappings
- raw-text-to-BrainState direct writes
- model output written to traces / scenarios / source histories
- save / export paths outside the configured DB and the explicit
  /db-backup destination
- changes to tick() semantics
- changes to /step / /stream / /stream-promote semantics
- changes to the closed parser verb set beyond the verbs listed in
  the target command surface
```

## 15. Next artifact

```text
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_KICKOFF.md
```

The kickoff should define for tracks A + B (and sketch C without
locking it):

```text
- the locked module placement (option K-A or K-B from section 11);
- proposed typed records:
    SessionStatusReport
    DbStatusReport
    DbVerifyReport
    DbBackupReport
    DbSummaryReport
    ProfileSummaryReport
    StreamDbSummaryReport
    DbDiffReport
    AutosaveConfig                (Phase 3.10c; deferred)
    AutosaveStatusReport          (Phase 3.10c; deferred)
- the helper signatures (status / verify / summary / diff / backup);
- the failure handling contract restated against the actual helpers;
- the proposed CLI flag set
    (--db-backup PATH, --db-verify, --autosave-mode <mode>);
- the proposed Command kinds and dispatch handlers;
- the proposed fixture roster sketch per track;
- the stop point before the corrigenda.
```

After the kickoff, the corrigenda (Step 4) audits and locks the
design before the Step 5 catalog patch plan binds the
ops/observability rows. The campaign stops at the Step 6 review gate
after Step 5 lands. Autosave artifacts (Steps 12-15) are produced
only after Step 11 (ops/observability audit) is PASS.
