# brain — TLICA-constrained Python kernel (catalog v0.19)

This package is the TLICA-constrained Python "brain" kernel. Open it, read this file, then read `INVARIANT_CATALOG.md`, then take direction from whichever current kickoff/corrigenda is in flight.

## What this is

A theorem-constrained Python state machine. The TLICA Lean formalization (snapshot in `lean_reference/`) is the *spec*, not the runtime. `INVARIANT_CATALOG.md` (canonical at the version on disk) binds each Lean theorem we honor — plus the engineering-hypothesis rows added by Phase 2 and beyond — to a Python runtime assertion, names the owning module, and assigns it to a fixture. The kernel is healthy when every REQUIRED row reports green.

This is not a brain in any philosophical sense. It is a runtime object that satisfies the structural prerequisites the TLICA theory says a "conscious I" must have — the constraints the Lean is good at enforcing. Whether the theory is right that those structural features are consciousness is untouched.

## What to do first

1. Read `INVARIANT_CATALOG.md`. That is canonical.
2. Read this README's "Constraints" section below for the pre-coding rules.
3. Build (or modify) according to the current kickoff document's build order.
4. Run `bash tools/check_all.sh` (catalog freshness → counts → citations → import audit → runner).
5. The kernel is healthy when every REQUIRED row reports green and all auxiliary gates pass.

Implement from the current `INVARIANT_CATALOG.md` exactly; the catalog is canonical.

## Package contents

| Path | What it is |
|---|---|
| `README.md` | This file. Read first. |
| `INVARIANT_CATALOG.md` | The current catalog spec (see version banner). The spine. |
| `SPEC_UPDATES.md` | How to consult `github.com/femboy2112/lean-scratch` for future spec evolution. |
| `lean_reference/` | Snapshot of the Lean source the catalog cites. Read-only reference. |
| `lean_reference/TLICA.lean` | Top-level Lean aggregator (lists every module imported). |
| `lean_reference/TLICA/` | Every TLICA module the catalog cites. |
| `lean_reference/TOCE_Core.lean` | The TOCE Boolean classifier layer (separate from TLICA proper). |
| `brain/` | The Python kernel: TLICA layer, LLM seam, trace seam, tick orchestration, fixtures. |
| `brain/ui/` | Operator TUI: read-only snapshots, pure renderer, command router, curses wrapper, and `python3 -m brain.ui` CLI entrypoint. |
| `scenarios/` | Locked scenario JSON files (e.g. `first_scenario_v1.json`). |
| `tools/` | Catalog parser, citation verifier, import audit, snapshot diff, runner wrappers. |

## Operator TUI

The Operator TUI is an agent-style inspection / bottom-up-injection
console for `BrainState`, `TickRecord`, and the Phase 3.1–3.4
developmental histories. It is an operator surface, not a new cognitive
layer.

```bash
python3 -m brain.ui --check-terminal   # probe terminal usability
python3 -m brain.ui --print-once       # render one deterministic agent frame to stdout
python3 -m brain.ui                    # launch the curses wrapper (TTY required)
```

### LLM runtime toggle (Phase 3.8b)

The default LLM runtime mode is `offline`: the kernel `tick()` path
is driven by `OfflineStandInClient`, which returns `"PRESERVE"` for
every prompt and performs no network I/O, no subprocess spawn, and
no file mutation. Model-backed modes are explicit opt-in via
`--llm-mode <mode>` or the `BRAIN_LLM_MODE` environment variable.

```bash
python3 -m brain.ui --llm-mode offline              # default; deterministic stand-in
python3 -m brain.ui --llm-mode mock \
    --llm-mock-response PRESERVE                    # canned-response stand-in
python3 -m brain.ui --llm-mode anthropic-api \
    --llm-anthropic-api-key <key>                   # real Anthropic API
python3 -m brain.ui --llm-mode claude-cli           # local `claude -p` CLI
python3 -m brain.ui --llm-mode anthropic-api \
    --llm-enable-cache                              # wrap with CachedClient
```

Rules (drive the `I-LLMTOG-*` row family):

- `offline` is the default. A stale `ANTHROPIC_API_KEY` in the
  environment does not silently widen the runtime surface.
- API key resolution order: `--llm-anthropic-api-key`, then
  `BRAIN_ANTHROPIC_API_KEY`, then `ANTHROPIC_API_KEY`.
- `--llm-enable-cache` is only honored for `anthropic-api` /
  `claude-cli`; it writes under `brain/.llm_cache/`. Cache writes
  only happen when a model-backed mode is selected and the operator
  explicitly opts in.
- `--print-once` and `--check-terminal` remain independent of the
  selected client.
- The toggle reuses the existing `LLMClient` protocol and the
  existing `tick(..., client, ...)` seam. It introduces no second
  classification path.

### Agent-style layout

`python3 -m brain.ui` opens a persistent multi-pane terminal interface
with a bottom typed-command composer. The layout is built from
`brain.ui.layout.AgentLayout.from_size(width, height)` and is
deterministic: header / state / inspector / transcript / composer /
footer panes always exist on terminals at or above the documented floor
(20 cols x 6 rows), and the composer is never dropped on small
terminals.

```text
+--------------------------------------------------------------+
| toy-brain operator · view=state · tick=0 · queue=0           |  header
+--------------------------------+-----------------------------+
| [ core state ]                 | [ latest tick ]             |
| profile domain size : 2        | tick index    : -           |  body
| ...                            | ...                         |  (state + inspector)
+--------------------------------+-----------------------------+
| [ transcript ]                                               |  transcript
| [SUBMIT@0] /queue beta hello-world                           |  log
| [QUEUED@0] queued percept 'beta' (queue size = 1)            |
+--------------------------------------------------------------+
| > /step_                                                     |  composer
| mode=local-cmd  cursor=5  history=1                          |  (edit + meta)
+--------------------------------------------------------------+
| keys: enter submit  ^u clear  ^p prev  ^n next  /help ...    |  footer
+--------------------------------------------------------------+
```

### Interactive flow

The primary path is typed commands in the bottom composer. Normal
typing edits the buffer; `Enter` submits one line through
`brain.ui.command_line.LocalCommandLine.parse` and dispatches the
resulting `Command` to `brain.ui.session.OperatorSession.dispatch`:

```text
> /queue beta hello-world<Enter>     queue a percept candidate
> /step<Enter>                       advance one tick using the queue head
> /state<Enter>                      inspect BrainState
> /tick<Enter>                       inspect the latest TickRecord
> /help<Enter>                       show the typed-command help
> /quit<Enter>                       exit the operator session
> /save-session<Enter>               save to the configured session DB
> /load-session<Enter>               load from the configured session DB
```

The closed set of typed verbs (one verb per submission):

```text
/help                       show typed-command help
/state                      inspect BrainState
/tick                       inspect latest TickRecord
/output                     inspect OutputHistory
/worldlet                   inspect WorldletHistory
/repl                       inspect Proto-BASIC REPL history (inspector only;
                            does NOT execute Python or Proto-BASIC)
/queue <id> <text>          queue a PerceptEvent candidate through the
                            public PerceptEvent constructor
/step                       advance one tick using the queue head
/clear                      clear local status/error (does NOT clear
                            the composer buffer; use ^U for that)
/quit                       exit
/save-session               save BrainState + session-local stream state to
                            the SQLite session DB configured by --session-db
                            (Phase 3.9; explicit operator command; no
                            autosave; does NOT call tick())
/load-session               read the configured session DB, reconstruct the
                            kernel state through public builders, run
                            invariant assertions, and swap the candidate
                            into the live session on success (Phase 3.9;
                            no implicit load; preserves the live session
                            on failure; does NOT call tick())
/session-status             bounded read-only summary of the live
                            OperatorSession (Phase 3.10a; no disk IO)
/db-status                  bounded read-only summary of the configured
                            session DB: existence, byte size, mtime,
                            schema_version, catalog_version, created_at,
                            updated_at (Phase 3.10a; sqlite3 mode=ro)
/db-verify                  reconstruct a candidate from the configured
                            DB through the Phase 3.9 load path, run
                            invariants, DROP the candidate, report
                            PASS / FAIL (Phase 3.10a; live session
                            unchanged on PASS or FAIL)
/db-summary                 bounded row-count + meta summary of the
                            saved DB (Phase 3.10b; sqlite3 mode=ro)
/profile-summary            COGITO-first, deterministically-sorted exact-
                            Fraction "num/den" listing of saved profile
                            values (Phase 3.10b; row cap 64)
/stream-db-summary          bounded head + tail slice of saved
                            stream_chunks + stream_candidates with text
                            preview cap 64 (Phase 3.10b)
/db-diff                    live OperatorSession vs saved snapshot
                            diff over the finite field enumeration;
                            "<missing>" explicit on one-sided absence
                            (Phase 3.10b; row cap 32)
/db-backup <path>           byte-faithful sqlite3.Connection.backup()
                            copy of the configured DB to <path>
                            (Phase 3.10a; refuses to overwrite without
                            --force; rejects URI-scheme destinations)
```

### Persistent session store (Phase 3.9)

The Phase 3.9 Persistent Session Store adds explicit, typed,
transactional, schema-versioned SQLite persistence over
`BrainState`, `MSI`, `PtCns`, `ContentRegistry`, the
`OperatorSession.tick_counter`, the Phase 3.7
`TextStreamHistory`, and `OperatorSession.stream_chunk_serial` /
`stream_candidates`. The persistence layer lives at
`brain/ui/persistence.py` (see `INVARIANT_CATALOG.md` rows
`I-PERSIST-01..I-PERSIST-16` for the bound contract).

```bash
python3 -m brain.ui --session-db brain/session.sqlite3              # configure but don't load yet
python3 -m brain.ui --session-db brain/session.sqlite3 --load-session   # load before launch
python3 -m brain.ui --session-db brain/session.sqlite3 --no-load-session # explicit opposite
```

Rules:

- The session DB is the only save / export path; no other
  filesystem write is authorized.
- Fractions persist exactly as `(num INTEGER, den INTEGER)`
  pairs. No `REAL` / `NUMERIC` / `FLOAT` / `DOUBLE` column stores
  kernel numeric data.
- Load reconstructs through the existing public builders
  (`make_profile_with_cogito`, `make_msi`, `make_ptcns`,
  `ContentRegistry`, `BrainState`, `make_text_stream_chunk`,
  `TextStreamHistory`, `make_stream_promotion_candidate`,
  `OperatorSession`) and runs `assert_state_invariants` on the
  candidate before swapping. `COGITO_ID` cannot be overwritten by
  persisted data.
- Save is `BEGIN IMMEDIATE` / `COMMIT` or `ROLLBACK`. A failed
  save preserves the live `OperatorSession` and leaves no orphan
  rows. Schema bootstrap (`CREATE TABLE IF NOT EXISTS`) runs in
  autocommit and is persistent across rollbacks.
- Load opens the DB in sqlite3 uri `mode=ro`, so a failed load
  never mutates the on-disk file.
- No `sqlite3.Connection` lives on `OperatorSession`; helpers use
  `with sqlite3.connect(...) as conn:` and close on with-block
  exit.
- Autosave is **not** authorized; `/save-session` and
  `/load-session` are the only persistence routes. A future
  autosave campaign requires an explicit reviewed policy
  artifact and dedicated catalog rows.

### Operational hardening + observability (Phase 3.10a / 3.10b)

Phase 3.10 adds eight typed read-mostly verbs and four one-shot
CLI flags over the Phase 3.9 session DB. Track A (Operational
Hardening) covers status / verify / backup; track B (Persistence
Observability) covers summaries + diff. Autosave (track C) remains
deferred behind its own review gate.

```bash
python3 -m brain.ui --session-db brain/session.sqlite3 --db-status   # one-shot DB status; exit 0/1
python3 -m brain.ui --session-db brain/session.sqlite3 --db-verify   # one-shot verify; exit 0/1
python3 -m brain.ui --session-db brain/session.sqlite3 \
    --db-backup /tmp/session.bak.sqlite3                             # one-shot byte-faithful backup
python3 -m brain.ui --session-db brain/session.sqlite3 \
    --db-backup /tmp/session.bak.sqlite3 --db-backup-force           # overwrite an existing dest
```

The three short-circuit flags (`--db-status`, `--db-verify`,
`--db-backup PATH`) are mutually exclusive and short-circuit after
`--check-terminal` / `--print-once` but before
`parse_llm_runtime_args` and curses initialization. Exit code is
`0` on PASS / success and `1` on FAIL / failure.

Inside the TUI, the same eight verbs route through the typed
composer:

```text
/session-status                    Phase 3.10a (no disk IO)
/db-status                         Phase 3.10a (sqlite3 mode=ro)
/db-verify                         Phase 3.10a (load → DROP candidate)
/db-summary                        Phase 3.10b (mode=ro; row counts)
/profile-summary                   Phase 3.10b (exact "num/den")
/stream-db-summary                 Phase 3.10b (head + tail slice)
/db-diff                           Phase 3.10b (live vs saved)
/db-backup <path> [--force]        Phase 3.10a (page-faithful copy)
```

Rules (driven by `I-OPSHARDEN-01..14` and `I-OBSERVE-01..11`):

- `/session-status` reads in-memory `OperatorSession` fields only;
  no disk IO; no `tick()`; no `sqlite3.Connection`.
- `/db-status`, `/db-verify`, `/db-summary`, `/profile-summary`,
  `/stream-db-summary`, `/db-diff` open the configured DB through
  `sqlite3.connect("file:<path>?mode=ro", uri=True)` inside a
  `with conn:` block; no live session mutation.
- `/db-verify` reuses `load_session` (the Phase 3.9 helper), runs
  the existing invariant assertions on the candidate `BrainState`,
  and immediately drops the candidate; the live `OperatorSession`
  reference is unchanged by `id()` before and after the call.
- `/db-backup` uses `sqlite3.Connection.backup()` (page-faithful)
  from a `mode=ro` source connection to a write-mode destination
  connection inside `with` blocks. It refuses URI-scheme
  destinations (`sqlite:`, `file:`, `http:`, `https:`, `ftp:`,
  `ws:`, `wss:`, `data:`, `gopher:`, `ssh:`, `git:`); it refuses
  `dest_path == source_path`; it refuses an existing destination
  unless `--force` is supplied; it never modifies the source DB.
- Observability commands never invoke a kernel builder
  (`make_profile_with_cogito`, `make_msi`, `make_ptcns`,
  `ContentRegistry`, `BrainState`, `make_text_stream_chunk`,
  `TextStreamHistory`, `make_stream_promotion_candidate`,
  `OperatorSession`); they read typed rows directly through
  `_deserialize_from_db` and the public `snapshot_session` helper.
- All `Fraction` values display as exact `"num/den"` strings via
  a single shared render helper; no `float()` / `repr()` / JSON
  leakage.
- `/db-diff` reports differences over the finite field enumeration
  declared in source (`profile.<id>`, `msi.contents`,
  `msi.threshold`, `ptcns_eval.<id>`, `registry.<id>`,
  `tick_counter`, `stream_chunk_serial`, `stream_history.count`,
  `stream_candidates.count`) and uses the literal `"<missing>"`
  for one-sided absence (never silent `0` / `null` defaults).
- Default row caps: `PROFILE_SUMMARY_ROW_CAP = 64`,
  `STREAM_DB_SUMMARY_HEAD_CAP = 8`,
  `STREAM_DB_SUMMARY_TAIL_CAP = 8`, `DB_DIFF_ROW_CAP = 32`,
  `STREAM_TEXT_PREVIEW_MAX_LEN = 64`,
  `OPS_REPORT_TEXT_MAX_LEN = 256`,
  `PROFILE_VALUE_STRING_MAX_LEN = 64`.
- Phase 3.10a/b adds NO new `OperatorSession` field; the
  resource-free property from Phase 3.9 is preserved.
- No autosave entry point exists in either
  `brain/ui/persistence_ops.py` or
  `brain/ui/persistence_observe.py`; both modules carry a
  defensive autosave-absent audit. Phase 3.10c autosave wiring is
  deferred to a later catalog patch.

Composer-only keys (always handled as edit events, regardless of
buffer state):

```text
Enter                      submit the buffer
Backspace                  delete one character
^U / ^C                    clear the composer buffer
^P                         recall previous submitted line
^N                         recall next submitted line
```

Single-letter accelerators (fire only when the buffer is empty AND
the typed key is not `/`):

```text
space          /step
s / t / o / w / r   /state, /tick, /output, /worldlet, /repl
c              /clear
? / h          /help
n              open the bounded curses two-field percept prompt
               (a wrapper concession; the typed /queue path is the
                primary surface)
q              /quit
```

Once any character is in the composer buffer — including a leading
`/` — every printable keystroke flows through the composer's edit
model until the buffer is submitted, cleared, or explicitly emptied.

Non-interactive entrypoints (no terminal required):

- `python3 -m brain.ui --print-once` renders one deterministic
  agent-layout frame of the default operator view, including the bottom
  composer, to `stdout` and exits;
- `python3 -m brain.ui --check-terminal` prints the result of the
  pure terminal-detection probe and exits without touching `curses`.

Behaviour rules (enforced by the `I-UI-*` catalog rows):

- read-only snapshots over kernel state (no mutation paths);
- pure renderers (`brain.ui.render.render` for the retained legacy
  view-model fixtures, `brain.ui.render.render_agent` for the live
  agent layout and `--print-once`) are deterministic and free of file /
  network / shell I/O;
- the only mutation route is `tick(...)` driven from a bounded
  operator event queue, dispatched through
  `OperatorSession.dispatch(Command(STEP_TICK))`;
- the curses wrapper imports no `brain.tick`, `brain.tlica`, or
  `brain.llm` runtime surface and never appends to
  `OperatorSession.event_queue` directly; every operator action is
  routed through the bottom composer → typed parser → session
  dispatcher chain (drives `I-UI-21`);
- the local transcript / event log lives only on the wrapper's stack,
  is bounded to 64 entries, and is destroyed when the wrapper exits
  (no cross-invocation persistence);
- the bottom composer is a typed local UI command line — not a chat
  surface and not a shell; the parser performs no shell expansion,
  no `eval` / `exec` / `compile`, no JSON/YAML parsing, no subprocess
  spawn, and no network access;
- no real LLM, no subprocess, no shell, no network, no filesystem
  writes outside an explicit reviewed save / export policy (none in
  this campaign).

## Catalog history

- **v0.2** — initial Lean-bound catalog (Phase 1 / v0 implementation).
- **v0.3** — +I-LLM-01/02/03/04, +I-RT-08, +I-BHV-01 (Phase 2 v1 LLM-backed `PtCns`).
- **v0.4** — +I-TRACE-01 (Phase 2 v1.1 cognition trace).
- **v0.5** — +I-RT-11, +I-RT-12, +I-TRACE-02, +I-TRACE-03, +I-CAT-01 (Phase 2 v1.2 baseline hardening plus pre-Phase-3.1 trace boundary hardening).
- **v0.6** — +I-FRAME-01/02/03/04, +I-DEV-01/02/03/04/05/06/07, +I-SBX-01/02 (Phase 3.1 Osmotic Chamber deterministic developmental substrate expansion).
- **v0.7** — +I-OUT-01..12 (Phase 3.2 Output Ladder deterministic developmental output rows).
- **v0.8** — +I-WLD-01..12 (Phase 3.3 Minimal Worldlet deterministic developmental worldlet rows).
- **v0.9** — +I-REPL-01..18 (Phase 3.4 Proto-BASIC REPL deterministic developmental REPL rows).
- **v0.10** — +I-UI-01..15 (Operator TUI deterministic operator-facing surface).
- **v0.11** — +I-UI-16..23 (Operator TUI Agent-Style Layout expansion).
- **v0.12** — +I-EXP-01..18 (Phase 3.5 Expression + ReadabilityPredictor bounded local layer).
- **v0.13** — +I-REF-01..14 (Phase 3.6 Reflective Inspection bounded local read-only developmental summary layer).
- **v0.14** — +I-STRM-01..17 (Phase 3.7 Text Stream Ingress bounded local raw-text substrate).
- **v0.15** — +I-UISTRM-01..17 (Phase 3.8 Operator Stream Interaction `/stream`, `/stream-summary`, `/stream-candidates`, `/stream-promote` typed routes over the Phase 3.7 substrate; `/step` remains the only `tick()` route).
- **v0.16** — +I-LLMTOG-01..15 (Phase 3.8b LLM Runtime Toggle: explicit `--llm-mode {offline,mock,anthropic-api,claude-cli}` opt-in over the existing `LLMClient` protocol; `offline` remains the default).
- **v0.17** — +I-PERSIST-01..16 (Phase 3.9 Persistent Session Store: explicit typed transactional SQLite-backed `/save-session` / `/load-session` over `BrainState` + `OperatorSession` at `brain/ui/persistence.py`; Fractions persist exactly as integer pairs; load reconstructs through public builders; failed save / load preserves the live session; autosave is NOT-EXERCISED).
- **v0.19** — +I-AUTOSAVE-01..15 (Phase 3.10c Autosave Policy: default-off, opt-in autosave layer at `brain/ui/autosave.py` over the existing Phase 3.9 `save_session` helper). `AutosaveMode` is a finite closed `(str, Enum)` with exactly `OFF` and `AFTER_SUCCESSFUL_MUTATION` members; `AutosaveTrigger` is a finite closed `(str, Enum)` with exactly `STEP_TICK` and `STREAM_PROMOTE` members. Default is `OFF` on every cold start at session construction AND at CLI parse time; no `BRAIN_AUTOSAVE_MODE` ambient env. `/autosave-enable` requires `--session-db` and raises `PersistenceError` otherwise; `/autosave-disable` is idempotent and never raises; `/autosave-status` returns a bounded report and never raises. `maybe_autosave_after_mutation` is the sole autosave entry point reachable from any dispatch path; fires AFTER `OperatorSession.dispatch` returns from a successful mutating dispatch (`/step` with `STEP_TICK`, `/stream-promote` with `STREAM_PROMOTE`); never fires after a failed dispatch, never fires after a read-only dispatch, never fires inside `tick()`; absorbs every `PersistenceError` into the typed status report (NEVER raises). Autosave reuses Phase 3.9 `save_session` via the existing transactional `BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK` discipline; no second save code path. Failure preserves the live `OperatorSession` and the on-disk session DB. New typed `OperatorCommand` kinds (`AUTOSAVE_STATUS`, `AUTOSAVE_ENABLE`, `AUTOSAVE_DISABLE`) + `AutosaveEnablePayload`. New CLI flag `--autosave-mode {off, after-successful-mutation}` (default `off`; requires `--session-db` for non-off). Two new optional `OperatorSession` fields (`autosave_config`, `last_autosave_status`). `brain/ui/autosave.py` static audit: no `@atexit`, no `threading`, no `asyncio`, no `signal` handler, no `curses` callback, no `tick(` call. The Phase 3.9 `I-PERSIST-16` row is RECLASSIFIED in this patch (NOT-EXERCISED -> STRUCTURAL) with a narrowed proposition (`brain/ui/persistence.py` owns no autosave trigger or background autosave hook); its row ID is preserved.
- **v0.18** — +I-OPSHARDEN-01..14 + I-OBSERVE-01..11 (Phase 3.10 Operational Hardening + Persistence Observability, tracks A + B only; track C autosave is deferred to a later catalog patch). Phase 3.10a adds read-only `/session-status`, read-only `/db-status` (sqlite3 uri `mode=ro`), candidate-DROPPING `/db-verify` that reuses `load_session` and runs invariants without swapping the live session, and byte-faithful `/db-backup` via `sqlite3.Connection.backup()` with `--force` overwrite gate and URI-scheme rejection (`sqlite:`, `file:`, `http:`, `https:`, `ftp:`, `ws:`, `wss:`, `data:`, `gopher:`, `ssh:`, `git:`). New one-shot CLI flags `--db-status` / `--db-verify` / `--db-backup PATH` / `--db-backup-force` are mutually exclusive at argparse time and short-circuit after `--check-terminal` / `--print-once` but before `parse_llm_runtime_args`; exit code 0 on success, 1 on failure. Phase 3.10b adds bounded read-only `/db-summary`, COGITO-first deterministically-sorted exact-`Fraction`-`"num/den"` `/profile-summary`, head+tail-bounded `/stream-db-summary` (`STREAM_TEXT_PREVIEW_MAX_LEN = 64`), and finite-field-enumeration `/db-diff` with explicit `"<missing>"` markers on one-sided absence. Observability commands never activate saved state and never mutate live `BrainState`. Default row caps: `PROFILE_SUMMARY_ROW_CAP = 64`, `STREAM_DB_SUMMARY_HEAD_CAP = 8`, `STREAM_DB_SUMMARY_TAIL_CAP = 8`, `DB_DIFF_ROW_CAP = 32`, `OPS_REPORT_TEXT_MAX_LEN = 256`. New typed `OperatorCommand` kinds (`SESSION_STATUS`, `DB_STATUS`, `DB_VERIFY`, `DB_BACKUP`, `DB_SUMMARY`, `PROFILE_SUMMARY`, `STREAM_DB_SUMMARY`, `DB_DIFF`) plus `DbBackupPayload`. New owning modules `brain/ui/persistence_ops.py` and `brain/ui/persistence_observe.py`; one narrow extension to `brain/ui/persistence.py` promoting `_snapshot_session` to the public `snapshot_session` helper. No autosave, no second save path, no new `OperatorSession` fields in 3.10a/b.

Companion docs (consult the relevant one when editing the catalog):
- `PLAN_CORRIGENDA.md` (v0 plan corrigenda).
- `PHASE2_v1_KICKOFF.md` / `PHASE2_v1_CORRIGENDA.md` (LLM-backed `PtCns`).
- `PHASE2_v1_1_TRACE_KICKOFF.md` (cognition trace).
- `BASELINE_HARDENING_KICKOFF.md` (Phase 2 v1.2 baseline hardening).
- `PHASE3_5_EXPRESSION_READABILITY_AUDIT.md` (Phase 3.5 complete; PASS).
- `PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md` (Phase 3.6 complete; PASS).
- `PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md` (Phase 3.7 complete; PASS).
- `PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md` (Phase 3.8 complete; PASS).
- `PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md` (Phase 3.8b complete; PASS).
- `PHASE3_TEXT_INTERACTION_DRY_RUN.md` (Fast Safe Text Interaction end-to-end walk).
- `CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` (Phase 3.9 Persistent Session Store — current).
- `PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md` (Phase 3.9 roadmap).

## Constraints (pre-coding rules — these are pulled from the catalog)

If any of these is unclear at code time, the catalog is canonical. Do not relax them.

### Catalog version

Use `INVARIANT_CATALOG.md` as shipped. Version banner inside should say **v0.19**. Confirmation numbers: **212 REQUIRED · 83 STRUCTURAL · 9 NOT-EXERCISED · 12 DEFERRED · 15 OBSERVED · 131 fixtures** (Phase 3.10c autosave fixtures land incrementally; pending registrations hold `I-AUTOSAVE-01..14` coverage coherent until Step 18; `I-PERSIST-16` was reclassified from NOT-EXERCISED to STRUCTURAL at v0.19 with the registration added in `brain/invariants.py` and the existing `persistence_static_audit.py` fixture unchanged). Run `python3 -m tools.catalog counts` to verify; the strict gate fails if banner / actual / expected ever drift. If you see anything that looks like 74 REQUIRED, 92 REQUIRED, float+EPS, or `Literal[...]` for `Act`, that is an older draft and is wrong.

### Numeric core

All profile values, distances, ranks, and projected-PCE values inside `brain/tlica/`, `brain/fixtures/`, and `brain/invariants.py` are `fractions.Fraction`. Raw `==` is safe and used throughout. The constructor `rho(value: int | float | str | Fraction) -> Fraction` normalizes at the I/O boundary and **raises** if the value is outside `[0, 1]` — never silently clamp. `math.inf` is the only permitted float, representing Lean's `⊤` for empty-intersection `dInfShared`.

### `Act`

```python
from enum import Enum

class Act(str, Enum):
    NOOP = "noop"
    INTEGRATE = "integrate"
    DIFFERENTIATE = "differentiate"
    ENCAPSULATE = "encapsulate"
```

`isinstance(x, Act)` works at runtime; `proj.no_action is Act.NOOP`.

### `PreservationRanking.rank` (cogito-gated)

```python
def rank(S: frozenset[ContentID]) -> Fraction:
    if COGITO_ID not in S:
        return Fraction(0)
    return Fraction(len(S & msi.contents), max(1, len(msi.contents)))
```

This satisfies `rank_nonneg`, `cogito_necessity`, `no_cogito_zero_rank`, `msi_maximality`, and `msi_monotonicity` by construction.

### `GlobalPreservationRanking.rank` (no cogito gating)

```python
def rank(S: frozenset[ContentID]) -> Fraction:
    return Fraction(len(S), max(1, len(universe)))
```

Non-negative and monotone. **No** cogito gating — only `PreservationRanking` over an MSI domain carries cogito necessity.

### `ProjectMap` Protocol

```python
class ProjectMap(Protocol):
    no_action: Act
    def project(self, action: Act, profile: ScalarProfile) -> ScalarProfile: ...
    def natural_dynamics(self, profile: ScalarProfile) -> ScalarProfile: ...
```

v0 deterministic stub: `natural_dynamics(P) = P` (identity); `project(NOOP, P) = natural_dynamics(P)`. Every projected profile **must** preserve `COGITO_ID` at value `1` (I-RT-07).

### `ModeOp` vs `Act` (disjoint namespaces)

`ModeOp` has four members: `MODE_A`, `MODE_B`, `MODE_C`, `NEUTRAL`. `Act` has four: `NOOP`, `INTEGRATE`, `DIFFERENTIATE`, `ENCAPSULATE`. They are not interchangeable. Mode B is parallel — it is **not** triggered by `ModeOp.from_eval`. The mapping from `ModeOp` to default `Act` is a lookup dict, not an identity.

### Action selection routes through `feasibleProjectedPCE` only

`brain/tlica/agency.py` must **never** import `brain.tlica.pce`. Foundation `PCE` is action-constant by Lean theorem (`PCE.all_actions_equal`); using it for action selection would make all actions equivalent. Selection goes through `feasibleProjectedPCE` (which routes through `action_projection.py`). The invariant runner performs an import-graph audit to enforce this (I-PCE-05).

### Free-will branch semantics are deferred

`brain/tlica/free_will.py` exposes surface types (`FreeWillWitness`, `PCEFreeWillWitness`) but no v0 fixture constructs them. Do not add one. Branch semantics are explicitly deferred per `Agency.lean`'s docstring.

### I-AFF-05 is REQUIRED — collapse fixture is mandatory

The `AffectKernelWitness` constructor **must** raise when every feasible action pair has equal branch profiles AND equal projected PCE. This is exercised by `brain/fixtures/affect_kernel_collapse.py`, which is the only fixture driving I-AFF-05.

### Validation file split

```
brain/tlica/builders.py     # construction-time preconditions; raises on invalid input
brain/validation.py         # reusable helpers (profile_equiv, is_in_unit_interval, …)
brain/invariants.py         # catalog registry + runner
```

Dependency graph: `builders → validation`; `invariants → fixtures + validation`; `tick → builders + invariants`. Do not fold validation into builders or builders into invariants.

## Build order

The kernel is already past every v0/v1/v1.1/v1.2 checkpoint. New work
follows the build order in the current kickoff document (see "Catalog
history" above for which is in flight); each kickoff specifies its own
ordering of catalog patch → tooling → modules → fixtures →
verification.

The original v0 eight-file checkpoint and its successor sequencing are
preserved in `ARCHIVE.md` as historical context. Do not use them as
instructions for new work.

## Success criterion

```
bash tools/check_all.sh
```

reports every REQUIRED row green, every STRUCTURAL row green, all
auxiliary gates pass, and OBSERVED rows are reported without gating.

For catalog v0.19, the expected count is:
**212 REQUIRED · 83 STRUCTURAL · 9 NOT-EXERCISED · 12 DEFERRED · 15 OBSERVED**.

The runner also performs the I-PCE-05 import-graph audit (`agency.py`
never imports `pce.py`) and the I-CAT-01 catalog↔registry coverage
audit (every REQUIRED/STRUCTURAL row has a registered check); both must
pass for the runner to claim "all green".

## Spec evolution

The Lean spec on `github.com/femboy2112/lean-scratch` is canonical and will evolve. When it does, the catalog needs to be re-aligned and the code re-validated against the new theorems. See `SPEC_UPDATES.md` for the refresh protocol.

## Things to not do

- Do not implement from stale draft counts or earlier catalog versions. Use the current `INVARIANT_CATALOG.md` exactly.
- Don't introduce modules outside the catalog's module map.
- Don't re-enable a deferred item (RCX, named affect taxonomy, love-as-constitutive-extension, substrate affect pathways, source-opacity affect, stochastic projection, phenomenological duration, temporal continuity metric, contestable-boundary refinement, free-will branch semantics, φ-coordinate / non-Archimedean δ) without an explicit upstream change.
- Don't use `typing.Literal` for `Act`.
- Don't use raw float arithmetic in `brain/tlica/`. Use `Fraction`.
- Don't push to `femboy2112/lean-scratch` — it is read-only from this package's perspective.
