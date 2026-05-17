# PHASE3_10_INTEGRATED_AUDIT.md

## 1. Purpose

Integrated audit of the complete Phase 3.10 Operational Hardening
+ Persistence Observability + Autosave campaign (tracks A + B +
C). This document ties the three track-level audits
(`PHASE3_10_OPS_OBSERVABILITY_AUDIT.md` for A + B and
`PHASE3_10C_AUTOSAVE_AUDIT.md` for C) into a single end-to-end
certification before the Step 21 final PR. It is an audit
artifact: it does not edit `INVARIANT_CATALOG.md`,
`tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, any runtime module, any fixture, or any
guarded kernel path.

```text
Verdict for Step 20: PASS
```

The Step 21 final PR opens after this audit lands. The PR is NOT
merged without explicit user approval.

## 2. Baseline at campaign completion

```text
Catalog version:  v0.19
REQUIRED:        212
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         15
Total tabular:   331
Total fixtures:  131
```

Catalog progression across the campaign:

```text
v0.17 (Phase 3.9 Persistent Session Store; pre-campaign baseline):
  187 / 69 / 10 / 12 / 13  (291 rows, 102 fixtures)

v0.18 (Phase 3.10a Operational Hardening + Phase 3.10b
       Persistence Observability; tracks A + B):
  +14 REQUIRED (I-OPSHARDEN: 9 + I-OBSERVE: 5)
  +10 STRUCTURAL (I-OPSHARDEN: 5 + I-OBSERVE: 5)
  + 1 OBSERVED  (I-OBSERVE-11 dry run)
  201 / 79 / 10 / 12 / 14  (316 rows, 120 fixtures)

v0.19 (Phase 3.10c Autosave Policy + I-PERSIST-16
       reclassification; track C):
  +11 REQUIRED  (I-AUTOSAVE: 11)
  + 4 STRUCTURAL (I-AUTOSAVE: 3 + I-PERSIST-16 reclassification: 1)
  + 1 OBSERVED  (I-AUTOSAVE-15 dry run)
  - 1 NOT-EXERCISED (I-PERSIST-16 reclassified, not retired)
  212 / 83 / 9 / 12 / 15   (331 rows, 131 fixtures)
```

## 3. Campaign step ledger

```text
Step 1   Repo-state sync                            (sync only; no commit)
Step 2   Phase 3.10 synthesis                       commit ac13e8e
Step 3   Phase 3.10 kickoff                         commit 5f5c875
Step 4   Phase 3.10 corrigenda                      commit 9807b75
Step 5   Ops/observability catalog patch plan       commit 88eb691
Step 6   Review gate A/B                            (accepted)
Step 7   v0.18 ops/observability catalog patch      commit a2ef1bb
Step 8   Operational hardening core                 commit 6e77b24
Step 9   Persistence observability                  commit d4e1468
Step 10  README documentation                       commit 930f5cf
Step 11  Ops/observability dry run + audit          commit 98f8064
Step 12  Autosave synthesis                         commit c72b112
Step 13  Autosave kickoff                           commit c72b112
Step 14  Autosave corrigenda                        commit c72b112
Step 15  Autosave catalog patch plan                commit c72b112
                                                    + patched: 3e57af7
Step 16  Review gate C                              (accepted, with
                                                     required patches)
Step 17  v0.19 autosave catalog patch               commit 0b9c7f0
Step 18  Autosave runtime + 11 fixtures             commit e3885a6
Step 19  Autosave dry run + audit                   commit ebdcc14
Step 20  This integrated audit                      this document
Step 21  Open PR to main                            (Step 21 action)
```

## 4. Track A — Operational Hardening (Phase 3.10a)

Row family: `I-OPSHARDEN-01..14` (9 REQUIRED + 5 STRUCTURAL).
Owning module: `brain/ui/persistence_ops.py`.

Per-row certification: see
`PHASE3_10_OPS_OBSERVABILITY_AUDIT.md` Sections 3-8.

```text
I-OPSHARDEN-01  /session-status read-only + bounded            PASS
I-OPSHARDEN-02  /db-status read-only mode=ro + bounded          PASS
I-OPSHARDEN-03  /db-verify reuses load_session + DROPS          PASS
I-OPSHARDEN-04  /db-verify failure preserves live session       PASS
I-OPSHARDEN-05  /db-backup uses sqlite3.Connection.backup()      PASS
I-OPSHARDEN-06  /db-backup refuses overwrite without --force     PASS
I-OPSHARDEN-07  /db-backup refuses URI-scheme destinations       PASS
I-OPSHARDEN-08  /db-backup never modifies source DB              PASS
I-OPSHARDEN-09  CLI short-circuit + mutual exclusion + exit codes PASS
I-OPSHARDEN-10  Source connection mode=ro during backup          PASS
I-OPSHARDEN-11  Phase 3.10a defensive autosave-absent audit      PASS
I-OPSHARDEN-12  persistence_ops module static audit              PASS
I-OPSHARDEN-13  persistence_ops session resource audit           PASS
I-OPSHARDEN-14  Exit-code mapping fixture                        PASS
```

Track A verdict: **PASS** (all 14 rows green).

## 5. Track B — Persistence Observability (Phase 3.10b)

Row family: `I-OBSERVE-01..11` (5 REQUIRED + 5 STRUCTURAL + 1
OBSERVED). Owning module: `brain/ui/persistence_observe.py`.

Per-row certification: see
`PHASE3_10_OPS_OBSERVABILITY_AUDIT.md` Sections 9-14.

```text
I-OBSERVE-01    /db-summary mode=ro + bounded                    PASS
I-OBSERVE-02    /profile-summary COGITO-first exact "num/den"    PASS
I-OBSERVE-03    /stream-db-summary bounded head + tail           PASS
I-OBSERVE-04    /db-diff finite enumeration + "<missing>"        PASS
I-OBSERVE-05    No saved-state activation; no live mutation      PASS
I-OBSERVE-06    persistence_observe module static audit          PASS
I-OBSERVE-07    No builder call in persistence_observe.py        PASS
I-OBSERVE-08    persistence_observe session resource audit       PASS
I-OBSERVE-09    Locked default row caps                          PASS
I-OBSERVE-10    Phase 3.10b defensive autosave-absent audit      PASS
I-OBSERVE-11    Phase 3.10 ops/observability dry run             PASS (OBSERVED)
```

Track B verdict: **PASS** (all 11 rows green; OBSERVED row
inspected via PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md).

## 6. Track C — Autosave Policy (Phase 3.10c)

Row family: `I-AUTOSAVE-01..15` (11 REQUIRED + 3 STRUCTURAL + 1
OBSERVED). Owning module: `brain/ui/autosave.py`.

Per-row certification: see `PHASE3_10C_AUTOSAVE_AUDIT.md`
Sections 3-14.

```text
I-AUTOSAVE-01   Default OFF on every cold start                  PASS
I-AUTOSAVE-02   AutosaveConfig non-OFF + empty db_path raises    PASS
I-AUTOSAVE-03   /autosave-enable without --session-db raises     PASS
I-AUTOSAVE-04   /autosave-enable transitions correctly           PASS
I-AUTOSAVE-05   /autosave-disable idempotent + never raises      PASS
I-AUTOSAVE-06   /autosave-status bounded report + never raises   PASS
I-AUTOSAVE-07   maybe_autosave_after_mutation never raises       PASS
I-AUTOSAVE-08   /step + autosave + success -> outcome="ok"       PASS
I-AUTOSAVE-09   Failed dispatch does NOT trigger autosave        PASS
I-AUTOSAVE-10   Read-only dispatch does NOT trigger autosave     PASS
I-AUTOSAVE-11   Autosave reuses save_session; no second path     PASS
I-AUTOSAVE-12   AutosaveMode + AutosaveTrigger closed enums      PASS
I-AUTOSAVE-13   brain/ui/autosave.py module static audit         PASS
I-AUTOSAVE-14   Session resource audit + outcome-detection       PASS
I-AUTOSAVE-15   Phase 3.10c autosave dry run                     PASS (OBSERVED)
```

Track C verdict: **PASS** (all 15 rows green; OBSERVED row
inspected via PHASE3_10C_AUTOSAVE_DRY_RUN.md).

## 7. I-PERSIST-16 reclassification (cross-track)

```text
Audit:    I-PERSIST-16 was the Phase 3.9 NOT-EXERCISED
          placeholder for "no autosave path exists". The Step 17
          catalog patch reclassified it from NOT-EXERCISED to
          STRUCTURAL with a narrowed proposition
          ("brain/ui/persistence.py owns no autosave trigger or
          background autosave hook"). The row ID, position, and
          owning module column are preserved. The registration
          is in brain/invariants.py and calls
          check_i_persist_12_static_audit (which already enforces
          the narrowed proposition); the
          persistence_static_audit.py fixture body is unchanged.
          The two rows (I-PERSIST-12 + I-PERSIST-16) are
          intentionally coupled: if I-PERSIST-12 fails,
          I-PERSIST-16 fails too (both are properties of
          brain/ui/persistence.py).

Evidence: `python3 -m brain.invariants run --id I-PERSIST-16`
          reports PASS STRUCTURAL.

Status:   PASS.
```

## 8. Cross-module autosave-absence audit

The campaign establishes a three-module autosave-absence posture
that the Step 20 audit verifies as a set:

```text
brain/ui/persistence.py         I-PERSIST-12 + I-PERSIST-16
                                 (Phase 3.9 static audit; the
                                  module owns save_session itself
                                  but no autosave hook).

brain/ui/persistence_ops.py     I-OPSHARDEN-11 + I-OPSHARDEN-12
                                 (Phase 3.10a static audit; no
                                  autosave entry point; no
                                  @atexit / threading / asyncio /
                                  signal handler).

brain/ui/persistence_observe.py  I-OBSERVE-06 + I-OBSERVE-10
                                  (Phase 3.10b static audit; no
                                   autosave entry point; no
                                   @atexit / threading / asyncio /
                                   signal handler).

brain/ui/autosave.py             I-AUTOSAVE-11 + I-AUTOSAVE-13
                                  (Phase 3.10c static audit;
                                   autosave entry point lives
                                   here exclusively; reuses
                                   save_session; no second save
                                   code path; no @atexit /
                                   threading / asyncio / signal
                                   handler).
```

The positive complement (`I-AUTOSAVE-11`) and the negative
complements (`I-PERSIST-16`, `I-OPSHARDEN-11`, `I-OBSERVE-10`)
together pin the autosave architecture: exactly one module owns
the autosave trigger, and three peer modules explicitly own none.

Audit status: **PASS** (all six rows green; the cross-module set
is consistent).

## 9. Closed-read-only verb list (cross-track)

`I-AUTOSAVE-10` asserts that every command kind in the closed
read-only list does NOT trigger autosave. The list at v0.19:

```text
INSPECT_STATE, INSPECT_TICK, INSPECT_OUTPUT, INSPECT_WORLDLET,
INSPECT_REPL, INSPECT_STREAM_SUMMARY, INSPECT_STREAM_CANDIDATES,
CLEAR_STATUS, HELP, QUIT, NOOP,
SESSION_STATUS, DB_STATUS, DB_VERIFY,            (Phase 3.10a)
DB_SUMMARY, PROFILE_SUMMARY, STREAM_DB_SUMMARY, DB_DIFF, DB_BACKUP,
                                                  (Phase 3.10b)
AUTOSAVE_STATUS,                                  (Phase 3.10c)
SAVE_SESSION, LOAD_SESSION                        (Phase 3.9)
```

The trigger set (closed; outside this read-only list):

```text
STEP_TICK            (/step)
STREAM_PROMOTE       (/stream-promote)
```

`/stream` (STREAM_APPEND) does mutate session-local stream state
but is deliberately excluded from the trigger set per the kickoff
section 4 / corrigenda section 4: text-stream chunk append is
buffered for batched promotion, and autosaving on every chunk
would create churn. The `autosave_no_after_read_only.py` fixture
asserts STREAM_APPEND does not trigger autosave; the Step 19 dry
run records this behavior explicitly.

`AUTOSAVE_ENABLE` and `AUTOSAVE_DISABLE` mutate
`session.autosave_config` but do not mutate kernel state; they are
also not in the trigger set (the operator just enabled / disabled
autosave; firing autosave from that path would be an immediate
no-op or near-no-op without operator-meaningful information).

Audit status: **PASS**.

## 10. Outcome-detection contract

The corrigenda section 10 pins:

```text
_dispatch_step              returns Optional[bool]  (True on success,
                                                     False on failure,
                                                     None for n/a)
_dispatch_stream_promote    returns Optional[bool]  (True on success,
                                                     False on failure)
```

The central `OperatorSession.dispatch` reads the sub-dispatcher's
return value to decide whether to fire `maybe_autosave_after_mutation`.
It does NOT scan `status_message` / `error_message` strings.

`autosave_resource_audit.py` (`I-AUTOSAVE-14`) asserts the return
type via static inspection of `brain/ui/session.py` source. A
future refactor that drops the return value would fail this
fixture.

Audit status: **PASS**.

## 11. Hard non-goals preserved (cross-campaign)

```text
no raw text -> COGITO_ID                                            PASS
no raw text -> BrainState direct mutation                           PASS
no pickle / shelve / marshal / dill / cloudpickle / joblib          PASS
no JSON / TOML / YAML as authoritative kernel-state format          PASS
no REAL / NUMERIC / FLOAT / DOUBLE columns for kernel numeric data  PASS
no sqlite3.Connection on OperatorSession                            PASS
no multi-mode autosave (only one non-off mode lands in v1)          PASS
no background autosave / timer / scheduler                          PASS
no autosave on /quit                                                PASS
no autosave to journal / rolling backup / network / multiple dests  PASS
no autosave-driven backup retention policy                          PASS
no per-tick autosave including failed ticks                         PASS
no migrations between schema versions in v1                         PASS
no persistence of LLM client / cache / runtime mode                 PASS
no persistence of curses configuration / terminal state             PASS
no second save_session helper                                       PASS
no changes to tick() semantics                                      PASS
no changes to /step / /stream / /stream-promote dispatch bodies
  beyond returning the outcome boolean                              PASS
no new typed operator commands outside the documented set
  (3.10a: /session-status, /db-status, /db-verify, /db-backup;
   3.10b: /db-summary, /profile-summary, /stream-db-summary,
   /db-diff; 3.10c: /autosave-status, /autosave-enable,
   /autosave-disable)                                                PASS
no save / export paths outside the configured session DB and the
  explicit /db-backup destination                                    PASS
no ambient-environment reads (no BRAIN_AUTOSAVE_MODE)                PASS
```

## 12. Pending-row hygiene (cross-campaign)

```text
brain/invariants.py:
  _PHASE3_10_OPS_PENDING_ROWS     = {}    (drained at Step 8)
  _PHASE3_10_OBSERVE_PENDING_ROWS = {}    (drained at Step 9)
  _PHASE3_10C_PENDING_ROWS        = {}    (drained at Step 18)
  All prior phase _PHASE3_*_PENDING_ROWS dicts are also empty.
```

No row is registered as pending; every REQUIRED / STRUCTURAL row
in the v0.19 catalog is backed by a real fixture function.

## 13. Full gate (final)

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

$ python3 -m brain.invariants run --id I-OPSHARDEN
15 rows checked  · 10 REQUIRED green · 5 STRUCTURAL green · 0 red

$ python3 -m brain.invariants run --id I-OBSERVE
10 rows checked  ·  5 REQUIRED green · 5 STRUCTURAL green · 0 red

$ python3 -m brain.invariants run --id I-AUTOSAVE
14 rows checked  · 11 REQUIRED green · 3 STRUCTURAL green · 0 red

$ python3 -m brain.invariants run --id I-PERSIST
17 rows checked (16 I-PERSIST-01..16 family rows; 1 reclassified)
                 · all REQUIRED green · all STRUCTURAL green
                 · 1 OBSERVED inspected (I-PERSIST-15 dry run)

$ python3 -m brain.invariants run
303 rows checked  ·  REQUIRED green: 213 ·  REQUIRED red: 0
              ·  STRUCTURAL green: 83 ·  STRUCTURAL red: 0
              ·  OBSERVED: 7 pass / 0 fail  ·  gate failures: 0

$ bash tools/check_all.sh
[...]
All checks passed.
```

## 14. Non-mutations confirmed (cross-campaign)

```text
- The live OperatorSession.state field-for-field equals the
  pre-call state after every read-only dispatch, every failed
  dispatch, every absorbed-PersistenceError autosave attempt,
  and every Phase 3.10a/b/c verb on every fixture path.
- The source DB file byte-equals the pre-call file after every
  read-only verb, every failed dispatch, every absorbed-
  PersistenceError autosave attempt, and every successful
  /db-backup (which only writes to the explicit destination).
- The on-disk DB grows only on /save-session, on a successful
  Phase 3.10c autosave trigger, and on the /db-backup
  destination (a separate file).
- No new OperatorSession field appears beyond the documented set
  (session_store_config + autosave_config + last_autosave_status,
  all Optional[frozen+slotted record]).
- No sqlite3.Connection / Cursor / subprocess / socket / file /
  callable / curses object appears in any session field after
  any Phase 3.10 verb or any post-dispatch autosave attempt.
- No tick() call occurs inside any Phase 3.10 dispatcher or
  inside maybe_autosave_after_mutation.
- No save_session call occurs from any read-only / failed
  dispatch, from any Phase 3.10a/b dispatcher, or from any
  brain/ui/persistence_ops.py / persistence_observe.py /
  persistence.py module-level code path.
- No @atexit / signal handler / threading / asyncio loop fires
  inside brain/ui/autosave.py, persistence_ops.py,
  persistence_observe.py, or persistence.py.
- The autosave entry point lives only at the post-dispatch site
  in OperatorSession.dispatch; no /step / /stream-promote
  dispatcher body invokes autosave directly.
- maybe_autosave_after_mutation NEVER raises; every exception
  (PersistenceError or otherwise) is absorbed into the typed
  AutosaveStatusReport.
```

## 15. Risks observed (cross-campaign)

```text
- The closed read-only verb list (I-AUTOSAVE-10) must stay in
  sync with the OperatorCommand enum. Any new enum member is a
  potential silent gap; the existing fixture iterates the list
  literally rather than introspecting the enum, so a new member
  added without explicit classification will fall through to
  "trigger unknown" (safe-by-default — maybe_autosave_after_mutation
  returns None on unrecognized triggers). A future campaign that
  adds an enum member must update both the trigger enum and the
  closed read-only list explicitly.

- The outcome-detection contract (_dispatch_step and
  _dispatch_stream_promote return Optional[bool]) is enforced by
  I-AUTOSAVE-14's resource-audit fixture via static inspection.
  A future refactor that drops the return value would silently
  break the autosave trigger; the fixture would fail. The
  fixture body must be kept in sync with any session.py
  refactor.

- I-PERSIST-16 is intentionally coupled to I-PERSIST-12 (the
  Step 17 patch re-runs the I-PERSIST-12 audit body under the
  I-PERSIST-16 row registration). A future campaign that widens
  the I-PERSIST-12 audit to allow new constructs in
  brain/ui/persistence.py must ensure the narrowed I-PERSIST-16
  proposition still holds (no autosave hook in
  brain/ui/persistence.py).

- The Phase 3.10c autosave runtime relies on brain/ui/persistence.
  save_session continuing to be the single save helper. Any future
  campaign that adds a second save_session-shaped helper would
  fail I-AUTOSAVE-11's static audit; the fixture body
  enumerates `def save_*` definitions in brain/ to detect this.

- The Phase 3.10a /db-backup destination is the only authorized
  write path outside /save-session. A future campaign that adds
  any new write path (e.g. journal, rolling backup, export)
  needs its own catalog row family and corrigenda; it must NOT
  reuse the /db-backup machinery without re-audit.
```

None of these risks blocks the Step 21 PR.

## 16. Phase 3.10 deliverables summary

```text
Modules:
  brain/ui/persistence_ops.py        (Phase 3.10a; 9 REQUIRED + 5
                                      STRUCTURAL rows)
  brain/ui/persistence_observe.py    (Phase 3.10b; 5 REQUIRED + 5
                                      STRUCTURAL + 1 OBSERVED rows)
  brain/ui/autosave.py               (Phase 3.10c; 11 REQUIRED + 3
                                      STRUCTURAL + 1 OBSERVED rows)

Narrow extension:
  brain/ui/persistence.py            (_snapshot_session promoted
                                      to public snapshot_session;
                                      I-PERSIST-16 reclassified
                                      NOT-EXERCISED -> STRUCTURAL
                                      with narrowed proposition)

New typed verbs (8 + 3 = 11 added at v0.18 + v0.19):
  /session-status, /db-status, /db-verify, /db-summary,
  /profile-summary, /stream-db-summary, /db-diff, /db-backup,
  /autosave-status, /autosave-enable, /autosave-disable.

New CLI flags (4 + 1 = 5):
  --db-status, --db-verify, --db-backup PATH, --db-backup-force,
  --autosave-mode {off, after-successful-mutation}.

New OperatorCommand kinds (8 + 3 = 11):
  SESSION_STATUS, DB_STATUS, DB_VERIFY, DB_BACKUP,
  DB_SUMMARY, PROFILE_SUMMARY, STREAM_DB_SUMMARY, DB_DIFF,
  AUTOSAVE_STATUS, AUTOSAVE_ENABLE, AUTOSAVE_DISABLE.

New payloads:
  DbBackupPayload(dest_path, force).
  AutosaveEnablePayload(mode).

New OperatorSession fields (0 + 2 = 2):
  autosave_config: Optional[AutosaveConfig]
  last_autosave_status: Optional[AutosaveStatusReport]

Fixture files added (18 + 11 = 29):
  10 persistence_ops_*.py + 8 persistence_observe_*.py
  + 11 autosave_*.py.

Catalog rows added (25 + 15 - 1 net = 39 net):
  +14 REQUIRED (Phase 3.10a/b) + 11 REQUIRED (3.10c) = +25 REQUIRED
  +10 STRUCTURAL (Phase 3.10a/b) + 3 STRUCTURAL (3.10c) + 1
    STRUCTURAL (I-PERSIST-16 reclassification) = +14 STRUCTURAL
  + 1 OBSERVED (Phase 3.10a/b) + 1 OBSERVED (3.10c) = +2 OBSERVED
  - 1 NOT-EXERCISED (I-PERSIST-16 reclassification)

Catalog version: v0.17 -> v0.18 -> v0.19.
```

## 17. Conclusion

Phase 3.10 (Operational Hardening + Persistence Observability +
Autosave Policy) is fully implemented, audited, and green. Each
of the three tracks lands its own row family at the documented
status counts; the cross-module autosave-absence posture is
consistent; the outcome-detection contract is enforced; and
every hard non-goal is preserved across the campaign.

```text
Verdict: PASS.
Next:    Step 21 — open the final PR to main.
         Do NOT merge without explicit user approval.
```
