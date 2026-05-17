# PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md

## 1. Purpose

Roadmap document for the Phase 3.9 Persistent Session Store campaign.
This file complements `CURRENT_MISSION.md` and `CURRENT_CAMPAIGN.md`
by recording, in one place:

- where the kernel currently stands at catalog v0.16,
- why a persistent session store is the right next step,
- the macro shape of the campaign,
- the boundaries the campaign must not cross,
- the order in which campaign artifacts should land.

It is a planning document, not a runnable fixture. It introduces no
new catalog rows on its own. Catalog rows are proposed in the
Step 5 catalog patch plan and landed only after the Step 6 review
gate accepts them.

## 2. Baseline

```text
Catalog version:   v0.16
REQUIRED:         178
STRUCTURAL:        64
NOT-EXERCISED:      9
DEFERRED:          12
OBSERVED:          12
Fixtures:          91

Latest merged campaign:
  Fast Safe Text Interaction
    Phase 3.6 Reflective Inspection           (PASS)
    Phase 3.7 Text Stream Ingress              (PASS)
    Phase 3.8 Operator Stream Interaction      (PASS)
    Phase 3.8b LLM Runtime Toggle              (PASS)
    Step 26 dry run                            (PASS)
  PR #6 merged into main 2026-05-15.

Latest harness landing on main:
  PR #7 (claude/analyze-repo-state-4I6Di): catalog-lint and
  campaign-state helpers + parallel preflight wiring.

All preflight gates green at HEAD:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  python3 -m brain.invariants run            249 rows; 0 red; 0 gate failures
  brain-catalog-lint                         C1 / C2 / C3 / C4 PASS
  brain-campaign-state                       READY (Step 1)
```

## 3. Problem statement

`build_default_session()` constructs a fresh deterministic session
every launch. Cold start currently discards:

```text
BrainState.profile values
MSI contents and threshold
PtCns eval_map
ContentRegistry texts
OperatorSession.tick_counter
TextStreamHistory (chunks + features)
stream_chunk_serial
stream_candidates
```

Phase 3.7 / 3.8 / 3.8b made the operator surface able to ingest
text, promote candidates into the public `PerceptEvent` queue, and
advance `tick()` with an explicit LLM-runtime client. None of that
state survives process exit. Phase 3.9 closes that gap with an
explicit, typed, schema-versioned persistence layer.

## 4. Strategic target

```bash
python3 -m brain.ui --session-db brain/session.sqlite3 --load-session
```

Inside the operator TUI:

```text
/stream hello world
/stream-promote promo-strm-chunk-1
/step
/save-session
/quit
```

After process restart with the same DB path and `--load-session`,
the operator should observe restored:

```text
BrainState.profile values  (exact Fraction equality)
MSI contents + threshold   (exact)
PtCns eval_map             (exact)
ContentRegistry texts      (exact strings)
OperatorSession.tick_counter
TextStreamHistory          (chunks + features)
stream_chunk_serial
stream_candidates          (either restored or deterministically
                            rebuilt from restored chunks)
```

Persistence must never carry:

```text
LLM clients
sockets
file handles
subprocess handles
callables
curses objects
open database connections living on OperatorSession
```

## 5. Persistence thesis

The first acceptable persistence layer is:

```text
SQLite (Python standard library `sqlite3`)
typed records (no pickle, no shelve, no arbitrary JSON dump)
explicit schema version stored in `meta`
transactional save / load
Fractions persisted as integer (num, den) pairs (queryable + exact)
reconstruction through the existing public builders / constructors
invariant validation runs before a loaded snapshot is activated
failed load preserves the live session
failed save preserves the live session
SQLite connection lifetime is operation-scoped or held by a
  resource-safe persistence helper -- not stored on BrainState
no autosave; `/save-session` and `/load-session` are explicit
```

## 6. Non-negotiable boundaries

The campaign must preserve every existing guardrail. Specifically:

```text
COGITO_ID remains reserved and cannot be overwritten on load
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
tick() remains the only TLICA runtime transition route
/step remains the only operator route that calls tick()
offline remains the default LLM runtime mode
model-backed modes remain explicit opt-in
no LLM / socket / handle / subprocess / callable / curses /
  open-db-connection persisted on OperatorSession
no model output written to traces / scenarios / source histories
no save/export path outside the explicitly configured session DB
no implicit autosave before an autosave policy is accepted
no change to tick() semantics
```

These are the same boundaries listed in `CURRENT_MISSION.md` and
`CURRENT_CAMPAIGN.md`. They are restated here so that this roadmap
is self-contained.

## 7. Suggested directory placement

Either of these locations is acceptable. The Step 3 kickoff or
the Step 4 corrigenda must lock one:

```text
brain/ui/persistence.py
brain/ui/fixtures/persistence_*.py
```

or, if the corrigenda prefers a non-UI subsystem:

```text
brain/persistence/session_store.py
brain/persistence/fixtures/persistence_*.py
```

Existing UI-owned conventions (one fixture module per row family,
constant-parity static audits, frozen / slots dataclasses) should
carry over to the persistence layer.

## 8. Macro sequence

The campaign body in `CURRENT_CAMPAIGN.md` is the canonical
sequence; this section is a roadmap-level summary.

```text
Step 1   Repo-state sync                   (this commit; ends here)
Step 2   Persistence synthesis             PHASE3_9_..._SYNTHESIS.md
Step 3   Persistence kickoff               PHASE3_9_..._KICKOFF.md
Step 4   Persistence corrigenda            PHASE3_9_..._CORRIGENDA.md
Step 5   Persistence catalog patch plan    PHASE3_9_..._CATALOG_PATCH_PLAN.md
Step 6   Review gate                       stop until accepted
Step 7   Apply accepted catalog patch      INVARIANT_CATALOG.md, tools/catalog.py,
                                            brain/_catalog_ids.py, brain/invariants.py
Step 8   Implement SQLite schema + typed   brain/ui/persistence.py (or
         persistence records                brain/persistence/session_store.py),
                                            fixtures, brain/invariants.py
Step 9   Implement save/load reconstruction
         through public builders
Step 10  Add CLI flags + explicit          brain/ui/__main__.py,
         /save-session / /load-session     brain/ui/commands.py,
                                            brain/ui/command_line.py,
                                            brain/ui/session.py,
                                            brain/ui/render.py,
                                            README.md
Step 11  Cold-start continuity dry run     PHASE3_9_PERSISTENCE_DRY_RUN.md
Step 12  Full persistence audit            PHASE3_9_..._AUDIT.md
Step 13  Final PR preparation              PR title "phase3.9: persistent session store"
```

Each step that changes files must be committed and pushed to the
campaign branch. Steps 6 and 13 are stop points.

## 9. Likely catalog row family

The catalog patch plan (Step 5) is canonical. The row family will
likely be:

```text
I-PERSIST-*
```

Likely themes:

```text
schema version explicit
SQLite schema finite and closed
Fractions persist exactly
load reconstructs through builders / constructors only
load runs invariants before activation
COGITO_ID cannot be overwritten by persisted data
failed load does not replace the live session
failed save does not mutate the live session
save transaction is atomic
session DB stores no LLM client / callable / handle / socket /
  subprocess / curses object
explicit /save-session is bounded and local
explicit /load-session is bounded and local
autosave is NOT-EXERCISED unless explicitly accepted
cold-start continuity dry run is OBSERVED
```

Exact REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED splits and
fixture assignments are deferred to the Step 5 plan and Step 6
review.

## 10. Branch and PR rule

```text
preferred campaign branch: campaign/persistent-session-store
never commit campaign work directly to main
commit every successful step that changes files
push every successful step commit to the campaign branch
open the final PR into main at Step 13
never merge the PR without explicit user approval
```

This roadmap document itself may have landed on `main` or on a
harness-mandated feature branch by explicit user / environment
configuration. That exception applies only to the initial Step 1
sync; campaign implementation work (Steps 7-13) follows the
branch-first rule above.

## 11. Definition of done for Step 1

```text
PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md exists.
README.md companion-docs section points at Phase 3.9, not the
  retired "Phase 3.6 next" line.
CURRENT_MISSION.md and CURRENT_CAMPAIGN.md state that the Fast Safe
  Text Interaction campaign is merged to main (PR #6).
v0.16 baseline language is present and consistent across
  CURRENT_MISSION.md, CURRENT_CAMPAIGN.md, README.md, and this
  roadmap.
python3 -m tools.catalog counts            ok / ok / ok
python3 -m tools.citations verify          PASS
python3 -m tools.import_audit              PASS
bash tools/check_all.sh                    PASS
```

## 12. Next action after Step 1

Move to Step 2 (`PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md`)
on the campaign branch. Do not pre-empt the synthesis / kickoff /
corrigenda / catalog-patch-plan sequence by editing the catalog,
the invariant runner, or `brain/ui/` runtime code in the same
commit as the roadmap.
