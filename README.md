# brain — TLICA-constrained Python kernel (catalog v0.31)

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
python3 -m brain.ui --llm-mode codex-cli            # local `codex exec` CLI
python3 -m brain.ui --llm-mode anthropic-api \
    --llm-enable-cache                              # explicit affirmation of the new
                                                    # Phase 3.14 default (L1 cache on)
python3 -m brain.ui --llm-mode anthropic-api \
    --llm-disable-cache                             # Phase 3.14 opt-out: bare
                                                    # transport, no L1 / L2 cache
```

The `codex-cli` mode (Phase 3.11) targets the local OpenAI codex
binary via `("codex", "exec")`. Override the executable with
`--llm-codex-cli-executable PATH` (default: `codex`). Resolution
happens via `shutil.which` at session-launch; missing binaries fail
closed before launch with `LlmRuntimeError`. The mode is explicit
opt-in only; there is no `BRAIN_LLM_CODEX_CLI_EXECUTABLE` env var.

Rules (drive the `I-LLMTOG-*` row family):

- `offline` is the default. A stale `ANTHROPIC_API_KEY` in the
  environment does not silently widen the runtime surface.
- API key resolution order: `--llm-anthropic-api-key`, then
  `BRAIN_ANTHROPIC_API_KEY`, then `ANTHROPIC_API_KEY`.
- Cache discipline (Phase 3.14): once the operator explicitly selects
  a model-backed mode (`anthropic-api` / `claude-cli` / `codex-cli`),
  the L1 transport cache (`CachedClient` at `brain/.llm_cache/`) is on
  by default and the L2 canonical semantic evaluation cache (at
  `brain/.llm_cache/eval_v1/`) is active. `--llm-disable-cache` forces
  both layers off for the current run; `--llm-enable-cache` is an
  explicit affirmation of the new default; supplying both flags raises
  `LlmRuntimeError`. Offline / mock modes never read or write the
  cache regardless of either flag, and the factory still rejects
  `--llm-enable-cache` for those modes. Cache flags cannot promote
  offline / mock into a model-backed mode (mode selection remains
  governed by `--llm-mode` / `BRAIN_LLM_MODE`).
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

- **v0.31** — +I-AGENTLEARN-01..11 (Phase 3.22b Learning Evidence + Reasoning Trace Continuation). Scope: +10 REQUIRED rows, +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged. Adds three new modules: `brain/development/abstract_pattern.py` (pure bounded structural-form layer with `derive_abstract_pattern_signature(text)` and the closed `AbstractPatternSignature` record), `brain/development/learning_evidence.py` (session-local evidence ledger with the closed `LearningEvidenceKind` enum and the bounded `LearningEvidenceRecord`, `LearningEvidenceTrace`, `LearningProofReport` records), and `brain/development/reasoning_trace.py` (closed audit trail with the `ReasoningStepKind` enum and bounded `ReasoningTraceStep`, `ReasoningTrace`, `ReasoningTraceReport` records). The agent loop is extended to populate `AgentLoopResult.learning_evidence_trace` and `AgentLoopResult.reasoning_trace` on every interaction; `AgentLoopState` gains a `learning_trace` field that threads the accumulated evidence ledger across calls. The benchmark battery adds A8 `learning_evidence` (7 cases A8.01–A8.07) and A9 `reasoning_trace` (7 cases A9.01–A9.07); the full battery is 53 cases with 52 PASS + 1 documented WARN (A3.04, the Phase 3.21 W3 follow-up not_applicable-overall blocker) + 0 FAIL. The W3 refusal trigger is refined: a narrower `_classify_cognitive_claim(text)` substring scan over a closed bounded tuple of phrase fragments (synthesized at module load from the imported `_FORBIDDEN_NON_CLAIM_TERMS` tuple) identifies direct cognitive-property phrasing for the reasoning trace; the wider audit-tuple scan remains the floor that fires REFUSAL. The W2 abstract-pattern transfer follow-up is satisfied: renamed inputs sharing structural form map to the same `digest_hex16` and trigger `TRANSFER_RECOGNIZED` evidence. The W5 REPL valid-effective follow-up is satisfied: repeated valid-effective REPL commands produce `DIMINISHING_RETURNS_UPDATED` evidence records with shrinking DRF strings. The W4 dispatch trace is satisfied: the reasoning trace's `OBSERVE_INPUT` step records one of `{repl-bridge, session-dispatch-stream-append, refusal-no-dispatch, fail-no-dispatch, warn-no-dispatch}` as the dispatch-path label. No `brain.llm` import, no `brain.tick.tick` call in any new module; OFFLINE remains the default. Zero real model calls. `brain/tick.py` untouched. "Structural learning" means observable session-local state transitions captured as bounded records — never memory in the psychological sense. "Reasoning trace" means an explicit audit trail of deterministic structural operations — never private subjective reasoning. The TLICA Lean spec in `lean_reference/` is not contradicted: every new row is marked as Engineering hypothesis (Phase 3 source label), no Lean theorem is claimed, no existing REQUIRED row is modified.
- **v0.30** — +I-AGENTLOOP-01..11 (Phase 3.22 Agent Communication Loop + Behavioral Indistinguishability Harness). Scope: +9 REQUIRED rows, +2 STRUCTURAL rows; NOT-EXERCISED / DEFERRED / OBSERVED unchanged. Adds the `brain/development/agent_repl_bridge.py`, `brain/development/agent_loop.py`, and `brain/development/agent_benchmark.py` modules. The closed deterministic seven-axis benchmark battery runs 39 cases (38 PASS + 1 WARN A3.04 + 0 FAIL). No `brain.llm` import; `brain/tick.py` untouched; OFFLINE preserved; zero real model calls.
- **v0.29** — +I-DEVMILE-01..11 (Phase 3.21 Developmental Trajectory). Scope: +10 REQUIRED rows, +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged. Adds the `brain/development/milestone_harness.py` module: a strict consumer of existing public surfaces that defines a closed ten-member `DevelopmentalMilestone` `(str, Enum)`, a closed four-member `MilestoneStatus` `(str, Enum)`, a frozen / slotted `MilestoneResult` record (no aggregate scalar), ten pure deterministic per-milestone helpers `run_m01_*..run_m10_*`, and an aggregator `run_all_milestones()`. Eleven new fixtures land under `brain/ui/fixtures/`. No existing runtime file is modified; `brain/tick.py` untouched; no LLM call; zero cache writes. Each milestone is grounded in a human-development analogue at the level of **structural marker only** — ToyI has none of infancy, attention, preference, memory, learning, judgment, context, or vigilance in the psychological sense. The words "developmental", "milestone", "trajectory" are used in their operational sense only; the canonical `_FORBIDDEN_NON_CLAIM_TERMS` audit returns zero hits across the harness module, every fixture, and every produced summary string. The TLICA Lean spec in `lean_reference/` is not contradicted: every new row is marked as Engineering hypothesis (Phase 3 source label), no Lean theorem is claimed, no existing REQUIRED row is modified.
- **v0.28** — +I-CFBK-01..02 (Phase 3.20 Coherence Feedback Bridge). Scope: +1 REQUIRED row, +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged. Extends `brain/development/processing_window.py` with two new `FeedbackMode` members (`COHERENCE = "coherence"`, `PATTERN_AND_COHERENCE = "pattern_and_coherence"`), a pure deterministic `build_cohmon_summary_text(*, overall_status_value, pass_count, warn_count, fail_count, na_count, check_count)` helper that accepts only bounded primitives, the `COHMON_SUMMARY_TEXT_PREFIX = "cohmon_summary"` and `COHMON_SUMMARY_TEXT_MAX_LEN = 160` constants, and widens `_V1_EMITTED_SOURCES` to include `InternalEventSource.COHMON_SUMMARY` so `build_rehearsal_provenance(..., source=COHMON_SUMMARY)` no longer raises. `validate_feedback_mode` accepts the new members. `OperatorSession` gains a new `_run_cohmon_feedback_step(*, tick_index)` helper that performs a **deferred function-body import** of `brain.development.coherence_monitor.build_full_coherence_report` (mirroring the existing `SessionStoreConfig` / `AutosaveConfig` deferred-import pattern) to avoid a circular module load with `coherence_monitor` (which already imports `OperatorSession`); the helper extracts the live `CoherenceReport`'s `overall_status.value` and per-status counts, calls `build_cohmon_summary_text(...)`, builds the `cohmon_summary` provenance via `build_rehearsal_provenance(..., source=COHMON_SUMMARY)`, and dispatches a normal `_append_stream_chunk` call. `_run_processing_window` branches on the four `FeedbackMode` members; under `PATTERN_AND_COHERENCE` both the Phase 3.19 pledger_summary chunk and the new cohmon_summary chunk fire after each rehearsal (in that fixed order). The chunk-count formula becomes deterministic `1 + alpha * N` with `alpha in {1, 2, 2, 3}` for `OFF / PATTERN_LEDGER / COHERENCE / PATTERN_AND_COHERENCE` respectively. The integration audit (`I-CFBK-01`) drives the loop at `N = 0` (every mode strict no-op), `N = 5 / 10 / 50` across all four modes and asserts: stream chunk counts match the locked formula; under `COHERENCE` the Pattern Ledger has at least 2 entries with at least one cohmon-family second-order entry whose `pattern_id` differs from the seed; under `PATTERN_AND_COHERENCE` it has at least 3 entries with disjoint pledger and cohmon families; per-family observation sums each equal `N`; determinism; `assert_state_invariants(state)` green throughout; cumulative real model calls = 0. The static audit (`I-CFBK-02`) asserts the widened `FeedbackMode` membership, `validate_feedback_mode` rejection rules, `build_cohmon_summary_text` determinism + bounded-shape rejections (non-`str` / empty / non-printable / `COGITO_ID` / unknown `overall_status_value`; non-`int` / `bool` / negative / over-cap counts; `check_count != pass + warn + fail + na`); helper output is bounded printable, prefix-locked, under `COHMON_SUMMARY_TEXT_MAX_LEN = 160`, contains no `COGITO_ID`, contains no `_FORBIDDEN_NON_CLAIM_TERMS` term; the widened `_V1_EMITTED_SOURCES` produces non-claim-clean bounded provenances for all three `InternalEventSource` members. `I-PWND-02` body is updated to reflect the widened emit set; `I-IFBK-02` body is updated to widen the `FeedbackMode` value-set assertion and replace the historical `COHMON_SUMMARY`-raises assertion with a non-claim-clean emit assertion. The Phase 3.20 patch does NOT modify `brain/tick.py`, `brain/llm/`, `brain/tlica/`, `brain/development/coherence_monitor.py` (the monitor stays read-only and unchanged), `brain/development/pattern_ledger.py`, `brain/development/growth_ledger.py`, `brain/development/text_stream.py`, persistence / autosave runtime files, parser / prompt files, scenarios, traces, `lean_reference/`, or `.claude/` runtime contents. No new `GrowthEventType`, no new `GrowthEventSource`, no new `OperatorCommand`, no new `ACTIVE_VIEWS` value, no new dispatcher kind, no new operator verb, no aggregate scalar, no DB schema change, no `SCHEMA_VERSION` bump, no autosave change. `brain/.llm_cache/` remains gitignored. `STREAM_APPEND` does not invoke `brain.tick.tick` or the LLM; the feedback path consumes zero real model calls regardless of mode or `processing_window_size`. OFFLINE remains the default; model-backed modes remain explicit opt-in. PASS/WARN/FAIL/NOT_APPLICABLE labels are treated throughout as **structural statuses**, never recoded as truth claims. "Coherence feedback" is engineering language about the deterministic `CoherenceReport`-summary-to-stream loop and the resulting bounded **structural self-monitoring approximation**; it is not a claim of introspection, metacognition, self-awareness, or any cognitive property of the running system.
- **v0.27** — +I-IFBK-01..02 (Phase 3.19 Internal Feedback Loop Prototype). Scope: +1 REQUIRED row, +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged. Extends `brain/development/processing_window.py` with a closed `FeedbackMode` `(str, Enum)` (members `OFF`, `PATTERN_LEDGER`), a pure deterministic `build_pledger_summary_text(*, pattern_id, recurrence_count, saturation_state_value)` helper, a typed `validate_feedback_mode(value)` validator, and widens `_V1_EMITTED_SOURCES` to include `InternalEventSource.PLEDGER_SUMMARY` (the previously reserved member); `COHMON_SUMMARY` remains reserved per LOCK F and continues to raise from `build_rehearsal_provenance`. `OperatorSession` gains one new optional field `feedback_mode: FeedbackMode = FeedbackMode.OFF` (added to `_ALLOWED_SESSION_ATTRS` and authorized through the new Phase 3.19 attribute tier `_PHASE_3_19_SESSION_ATTRS = frozenset({"feedback_mode"})` in both persistence resource-audit fixtures); the default `OFF` preserves the Phase 3.18 rehearsal-only path bit-for-bit. `_run_processing_window` is extended with a paired-step structure: after each successful rehearsal, when `self.feedback_mode is FeedbackMode.PATTERN_LEDGER`, a new private `_run_feedback_step(tick_index, seed_pattern_id)` looks up the just-updated seed Pattern Ledger entry by `derive_pattern_id(derive_pattern_signature(seed_chunk))`, builds the deterministic summary text and the `pledger_summary` provenance, and dispatches the chunk through `_append_stream_chunk`; the feedback chunk's structural signature differs from the seed chunk's, so `PatternLedger.observe` records a second-order entry whose recurrence climbs independently. The integration audit (`I-IFBK-01`) drives the loop at `N = 0` (OFF strict no-op), `N = 5 / 10 / 50` with `feedback_mode in {OFF, PATTERN_LEDGER}` and asserts: stream chunk count `1 + 2 * N` under PATTERN_LEDGER and `1 + N` under OFF; at least one second-order Pattern Ledger entry under PATTERN_LEDGER with `pattern_id != seed_pattern_id`; the seed entry's `recurrence_count == min(STREAM_PATTERN_RECURRENCE_MIN + N, STREAM_PATTERN_RECURRENCE_MAX)` under both modes; the sum of `(recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1)` across all second-order entries equals `N` under PATTERN_LEDGER (one observation per feedback chunk); every entry's bounded constructor invariants hold; `assert_state_invariants(state)` remains green; two independent sessions with identical inputs produce bit-identical Pattern Ledger entry tuples and bit-identical Growth Ledger event_id tuples. The static audit (`I-IFBK-02`) asserts `FeedbackMode` membership, `validate_feedback_mode` rejection rules for `bool / int / str / None / tuple / list / object`, `build_pledger_summary_text` determinism and bounded-shape rejections (non-`str` / empty / non-printable / `COGITO_ID` `pattern_id`; non-`int` / `bool` / negative / over-cap `recurrence_count`; non-`str` / unknown `saturation_state_value`); the helper's output over a representative input set is bounded printable, prefix-locked, under `PLEDGER_SUMMARY_TEXT_MAX_LEN = 240`, contains no `COGITO_ID`, and contains no `_FORBIDDEN_NON_CLAIM_TERMS` term; the widened `_V1_EMITTED_SOURCES` produces non-claim-clean bounded provenances for both `REHEARSAL` and `PLEDGER_SUMMARY` while `COHMON_SUMMARY` continues to raise. `I-PWND-02` body is updated to reflect the widened emit set. The Phase 3.19 patch does NOT modify `brain/tick.py`, `brain/llm/`, `brain/tlica/`, `brain/development/pattern_ledger.py`, `brain/development/coherence_monitor.py`, `brain/development/growth_ledger.py`, `brain/development/text_stream.py`, `brain/ui/persistence.py`, `brain/ui/persistence_ops.py`, `brain/ui/persistence_observe.py`, `brain/ui/autosave.py`, `brain/ui/render.py`, `brain/ui/snapshot.py`, `brain/ui/__main__.py`, `brain/ui/command_line.py`, `brain/ui/commands.py`, scenarios, traces, `lean_reference/`, or `.claude/`. No new `GrowthEventType`, no new `GrowthEventSource`, no new `OperatorCommand`, no new `LOCAL_COMMAND_VERBS` entry, no new `ACTIVE_VIEWS` value, no new dispatcher kind, no new operator verb, no aggregate scalar, no DB schema change, no `SCHEMA_VERSION` bump, no autosave trigger change, no parser change, no prompt change. `brain/.llm_cache/` remains gitignored. `STREAM_APPEND` does not invoke `brain.tick.tick` and does not invoke the LLM; the feedback path consumes zero real model calls regardless of `processing_window_size`. OFFLINE remains the default; model-backed modes remain explicit opt-in. "Internal feedback" is engineering language about the deterministic Pattern-Ledger-summary-to-stream loop; it is not a claim of introspection, metacognition, or self-awareness.
- **v0.26** — +I-PWND-01..02 (Phase 3.18 Bounded Internal Processing Window). Scope: +1 REQUIRED row, +1 STRUCTURAL row; NOT-EXERCISED / DEFERRED / OBSERVED unchanged. Adds the `brain/development/processing_window.py` substrate: a closed-import rehearsal helper whose `plan_rehearsals(seed_text, window_size)` pure function emits a deterministic tuple of `RehearsalStep` records for a session-level synchronous loop. `OperatorSession` gains two optional bounded-int fields (`processing_window_size`, `processing_window_call_budget`; both default 0 = OFF) added through a new Phase 3.18 attribute tier in both persistence resource-audit fixtures. `_dispatch_stream_append` is refactored to return the appended `TextStreamChunk` and to delegate the core chunk-construction + Pattern Ledger observe + Growth Ledger emission body to a new private `_append_stream_chunk(text, chunk_provenance, growth_provenance)` helper shared with the new `_run_processing_window(seed_chunk)` method; the top-level `OperatorSession.dispatch` fires the window after a successful external `STREAM_APPEND`. Each internal rehearsal reuses the seed chunk's text verbatim so the structural Pattern Ledger signature is preserved; the entry's `recurrence_count` climbs by exactly one per successful rehearsal (saturating at `STREAM_PATTERN_RECURRENCE_MAX = 256`). `STREAM_APPEND` does not invoke `brain.tick.tick` and does not invoke the LLM, so the window consumes zero real model calls regardless of size. `InternalEventSource` is a finite closed `(str, Enum)` with `{REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}`; v1 ships `REHEARSAL` only and the two reserved members raise when passed to `build_rehearsal_provenance` so the dispatcher cannot widen the source set without a fresh review gate. `PROCESSING_WINDOW_SIZE_MAX = 255`, `PROCESSING_WINDOW_CALL_BUDGET_MAX = 65535`, `PROCESSING_WINDOW_PROVENANCE_PREFIX = "internal_processing_window"`. The static AST audit (`I-PWND-02`) over `brain/development/processing_window.py` restricts imports to `{__future__, dataclasses, enum, typing, brain.development.text_stream, brain.tlica.profile}`, rejects `os` / `subprocess` / `socket` / `urllib` / `http` / `requests` / `pathlib` / `tempfile` / `shutil` / `curses` / `brain.tick` / `brain.llm` / `brain.ui` / non-`profile` `brain.tlica.*` / `threading` / `asyncio` / `atexit` / `signal` / `importlib` / `math` / `hashlib` / `time` / `random` imports, rejects `eval` / `exec` / `compile` / `__import__` / `open` / `float` / `round` / `math.*` / `importlib.*` / `atexit.*` / `signal.*` / `hashlib.*` / `time.*` / `random.*` calls, and applies the canonical Phase 3.12c `_FORBIDDEN_NON_CLAIM_TERMS` audit to both the module source and the strings produced by `build_rehearsal_provenance`. The integration audit (`I-PWND-01`) drives the rehearsal loop at `N = 0` (OFF strict no-op), `N = 3` (recurrence_count = MIN + 3, deterministic internal provenances), and `N = 40` (evidence_chunk_ids capped at PATTERN_LEDGER_EVIDENCE_MAX = 32 while recurrence_count still climbs). The Phase 3.18 patch does NOT modify `brain/tick.py`, `brain/llm/`, `brain/tlica/`, `brain/development/text_stream.py`, `brain/development/pattern_ledger.py`, `brain/development/coherence_monitor.py`, `brain/development/growth_ledger.py`, `brain/ui/persistence.py`, `brain/ui/persistence_ops.py`, `brain/ui/persistence_observe.py`, `brain/ui/autosave.py`, `brain/ui/render.py`, `brain/ui/snapshot.py`, `brain/ui/__main__.py`, `brain/ui/command_line.py`, `brain/ui/commands.py`, scenarios, traces, `lean_reference/`, or `.claude/`. No new `GrowthEventType`, no new `OperatorCommand`, no new `LOCAL_COMMAND_VERBS` entry, no new `ACTIVE_VIEWS` value, no new dispatcher kind, no new operator verb, no aggregate scalar, no DB schema change, no `SCHEMA_VERSION` bump, no autosave trigger change (the existing `STEP_TICK` / `STREAM_PROMOTE` trigger set is preserved; the window does NOT fire autosave). `brain/.llm_cache/` remains gitignored. OFFLINE remains the default; model-backed modes remain explicit opt-in.
- **v0.25** — +I-LLMCACHE-23..26, promotes `I-LLMCACHE-20` from `DEFERRED` to `REQUIRED` (Phase 3.15 L1 Cache Hygiene). Scope: +4 REQUIRED rows, +1 STRUCTURAL row, -1 DEFERRED row; NOT-EXERCISED and OBSERVED unchanged. Binds a deterministic write-skip-at-cap admission policy with `L1_CACHE_MAX_ENTRIES = 1024` to the existing `CachedClient` L1 transport cache at `brain/llm/client.py`. The L1 entry count never exceeds the cap; at cap, `CachedClient` does not write a new entry; existing entries remain present and readable; hits continue to read. At-cap miss still calls the inner client and returns the response (only the write is skipped). Adds the `llm.cache_skip` trace event with payload exactly `{cache_key_prefix, reason}` and `reason="capacity"`, the `skip_count` counter on `CachedClient`, no-silent-repair guarantees (existing entries unchanged, corrupt entries still fail loud, no inner fall-back on corrupt read, no `llm.cache_skip` emission below cap), and a static AST audit (`I-LLMCACHE-26`) over `brain/llm/client.py`. L2 (`eval_v1`) semantics, the Phase 3.14 flag contract, and the OFFLINE/MOCK factory-boundary rejection of caching are all preserved unchanged. `brain/tick.py` is not edited; no `SCHEMA_VERSION` bump; no DB schema change; no persistence/autosave change; no UI expansion. `I-LLMCACHE-21` and `I-LLMCACHE-22` remain `NOT-EXERCISED`; raw bad-response replay remains durable (Option E deferred to a future campaign). No raw prompt/response/cache files committed; `brain/.llm_cache/` remains gitignored.
- **v0.24** — +I-LLMCACHE-01..22 (Phase 3.14 LLM Cache Discipline: makes the existing transport prompt-hash cache default-on once a model-backed mode is explicitly selected and adds a canonical semantic evaluation cache near `brain/llm/ptcns_backed.py`). Scope: +18 REQUIRED rows, +1 STRUCTURAL row, +1 DEFERRED row, +2 NOT-EXERCISED rows; OBSERVED unchanged. L0 (`LLMBackedPtCns._cache`) is unchanged. L1 is the existing `CachedClient` at `brain/llm/client.py`; new `--llm-disable-cache` opt-out flag forces it off for model-backed modes, `--llm-enable-cache` remains an explicit affirmation, and supplying both flags raises `LlmRuntimeError`. OFFLINE / MOCK still reject `--llm-enable-cache` and accept `--llm-disable-cache` as a no-op without unlocking cache access. L2 lives inside `LLMBackedPtCns`; the key is `sha256(repr(seven_tuple))` where the seven-tuple is `(SEMANTIC_CACHE_SCHEMA_VERSION="llm-semantic-cache-v1", PROMPT_TEMPLATE_VERSION="prompt-template-v1", PARSE_SCHEMA_VERSION="consistency-eval-v1", backend_family, model_identity, existing_msi_context, new_text)`; the evaluated `new_id` is excluded from the key but retained in the rendered prompt for diagnostics. L2 entries persist exactly `{"key_prefix", "parsed"}` under `brain/.llm_cache/eval_v1/` (covered by the existing gitignored `brain/.llm_cache/` root); raw prompts, raw responses, error text, and provider metadata are never persisted. L2 is bounded by `SEMANTIC_CACHE_MAX_ENTRIES = 1024`; at cap, hits read but misses do not write, emitting `llm.semantic_cache_skip` with `reason="capacity"`. Failure classes (parse failure, provider failure, timeout, refusal / empty, schema mismatch, corrupt entry) are kept distinct and never collapse into one cache state; retries exhausted without a parse-success emit `llm.semantic_cache_skip` with `reason="parse_failure"`. Corrupt L1 / L2 entries fail loud with bounded errors and never silently call the inner client. Cache observability adds the `llm.semantic_cache_hit` / `_miss` / `_store` / `_skip` events alongside the existing `llm.cache_hit` / `_miss`; trace payloads carry only `content_id`, the 8-character `key_prefix`, and `reason`. Dependency direction is one-way (`brain/llm/ptcns_backed.py` does not import `brain.ui.*` or `brain.tick`). L1 bounding remains DEFERRED (`I-LLMCACHE-20`) because Phase 3.14 introduces no new L1 cache surface — flipping `enable_cache=True` by default activates the existing v0.16 `CachedClient`. The real external model-backed cache smoke (`I-LLMCACHE-21`) and the end-to-end Phase 3.14 behavior probe (`I-LLMCACHE-22`) are NOT-EXERCISED in v1; Step 8's behavior report exercises L1 + L2 along the deterministic local-client route. The Phase 3.14 patch does NOT modify `brain/tick.py`, `brain/development/growth_ledger.py`, `brain/development/pattern_ledger.py`, `brain/development/coherence_monitor.py`, `brain/ui/session.py`, persistence / autosave runtime files, scenarios, traces, `lean_reference/`, or `.claude/`. The Phase 3.8b cache-gated audit (`brain/ui/fixtures/llm_runtime_cache_gated.py`) and the Phase 3.11 codex-cli factory audit (`brain/ui/fixtures/llm_runtime_codex_cli_factory.py`) remain green under the new default policy because they construct `LlmRuntimeConfig` directly with explicit `enable_cache` values rather than going through the parser. `(new_state, TickRecord)` parity at the kernel boundary is preserved bit-for-bit between cached and uncached evaluations for the same client responses.
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
- **v0.23** — +I-GROW-01..22 (Phase 3.13 Growth Ledger: bounded session-local developmental record of accepted, constructor-validated growth events at `brain/development/growth_ledger.py`). Scope: +19 REQUIRED rows, +1 STRUCTURAL row, +1 NOT-EXERCISED row, +1 DEFERRED row. `GrowthEventType` is a finite closed `(str, Enum)` containing the v1-emitted members (`STREAM_CHUNK_ACCEPTED`, `PATTERN_ENTRY_CREATED`, `PATTERN_ENTRY_UPDATED`, `STREAM_PROMOTION_QUEUED`, `TICK_SUCCEEDED`, `PROFILE_DOMAIN_ADDED`, `MSI_MEMBER_ADDED`) plus the deferred-for-future members (`SESSION_SAVED`, `SESSION_LOADED`, `COHERENCE_REPORT_BUILT`) which exist on the enum but are never emitted by any v1 dispatcher call site. `GrowthEventSource` is a finite closed `(str, Enum)` covering the v1-emitted sources (`STREAM_APPEND`, `PATTERN_LEDGER_OBSERVE`, `STREAM_PROMOTE`, `STEP_DISPATCH`) plus deferred sources (`PERSISTENCE_SAVE`, `PERSISTENCE_LOAD`, `COHERENCE_MONITOR`). `GrowthEvent` is a frozen / slotted record with bounded printable `event_id`, closed-enum `event_type`, non-negative int `tick` (not `bool`), closed-enum `source`, tuple-typed `references` of length at most `GROWTH_LEDGER_REFERENCE_MAX = 8` with pairwise-unique bounded printable entries, and bounded printable `provenance`. Event ids are deterministic `"growth:" + sha256(repr((event_type.value, tick, source.value, references, provenance)).encode("utf-8")).hexdigest()[:16]` over the closed immutable acceptance payload only (no `dict` / `set` / raw object / time / random / PID / hostname / `id(...)` / env input). `GrowthLedger.observe(...)` is pure copy-on-write with a fixed validation order (saturation → enum membership → tick → references shape → references uniqueness → provenance → event_id derivation → duplicate-event idempotency → append); duplicate event payloads return `self` unchanged (`event_id` collapse), and at `GROWTH_LEDGER_MAX_EVENTS = 256` any new event returns `self` (no eviction, no FIFO / LIFO drop, no overwrite, no random replacement, no per-type rebalancing). New constants: `GROWTH_LEDGER_MAX_EVENTS = 256`, `GROWTH_LEDGER_REFERENCE_MAX = 8`, `GROWTH_LEDGER_ID_MAX = 64`, `GROWTH_LEDGER_PROVENANCE_MAX = 64`, `GROWTH_LEDGER_SOURCE_MAX = 64`. Session-local integration through a single new optional `OperatorSession.growth_ledger` field (added to `_ALLOWED_SESSION_ATTRS`) and three observe call sites at the end of the successful paths of `_dispatch_stream_append` (emits `STREAM_CHUNK_ACCEPTED` plus `PATTERN_ENTRY_CREATED` / `PATTERN_ENTRY_UPDATED` from a pre/post Pattern Ledger entry-tuple comparison), `_dispatch_stream_promote` (emits `STREAM_PROMOTION_QUEUED`), and `_dispatch_step` (emits `TICK_SUCCEEDED` plus `PROFILE_DOMAIN_ADDED` / `MSI_MEMBER_ADDED` per `content_id` in the post/pre bounded set delta over `state.profile.domain` and `state.msi.contents`). A new Phase 3.13 audit tier `_PHASE_3_13_SESSION_ATTRS = frozenset({"growth_ledger"})` is added to both `brain/ui/fixtures/persistence_observe_resource_audit.py` and `brain/ui/fixtures/persistence_ops_resource_audit.py` and folded into the `allowed` union compared against `_ALLOWED_SESSION_ATTRS`. Static AST audit (`I-GROW-10` / `I-GROW-11`) rejects every forbidden import / module reference / dynamic-execution call; allowed imports are exactly `dataclasses`, `enum`, `hashlib`, `typing`, and `brain.tlica.profile` for `COGITO_ID`. Dependency direction is one-way (`brain/ui/session.py` imports `brain/development/growth_ledger.py`; the Growth Ledger module does not import the session, Pattern Ledger, Coherence Monitor, `brain.tick`, LLM, UI, or `text_stream` modules at runtime). Non-claim audit (`I-GROW-19`) inherits the canonical `_FORBIDDEN_NON_CLAIM_TERMS` tuple from `brain.development.coherence_monitor` on the fixture side and asserts the Growth Ledger module source and every bounded printable string the module produces contain none of those terms. Persistence is session-local only: no `growth_events` table, no `SCHEMA_VERSION_V*` bump, no `/save-session` serialization, no `/load-session` restore, no autosave extension. `I-GROW-21` (optional `/growth-ledger` UI) is DEFERRED in v1; `I-GROW-22` (end-to-end dry run) is NOT-EXERCISED in v1; both can be promoted by a follow-up reviewed catalog patch. The Phase 3.13 Growth Ledger does NOT modify `brain/tick.py`, `brain/llm/`, `brain/tlica/`, `brain/development/text_stream.py`, `brain/development/pattern_ledger.py`, `brain/development/coherence_monitor.py`, `brain/ui/persistence.py`, `brain/ui/persistence_ops.py`, `brain/ui/persistence_observe.py`, `brain/ui/autosave.py`, `brain/ui/commands.py`, `brain/ui/command_line.py`, `brain/ui/render.py`, `brain/ui/snapshot.py`, scenarios, traces, or any guarded kernel path; `/step` behavior is bit-for-bit identical to its pre-ledger semantics aside from one post-success `self.growth_ledger = self.growth_ledger.observe(...)` assignment per emitted event.
- **v0.22** — +I-COHMON-01..14 (Phase 3.12c Coherence Monitor: bounded read-only structural diagnostic at `brain/development/coherence_monitor.py`). Option A scope: +11 REQUIRED rows, +1 STRUCTURAL row, +1 NOT-EXERCISED row, +1 DEFERRED row. `CoherenceCheckStatus` is a finite closed enum (`PASS`, `WARN`, `FAIL`, `NOT_APPLICABLE`); `CoherenceCheck` is a frozen / slotted record with bounded printable `check_id` / `summary` / `detail` / closed `CHECK_SOURCES` membership for `source`; `CoherenceSnapshot` carries non-negative int counts, bool `session_db_configured`, bounded printable `autosave_mode`, and a tuple-typed `checks` capped at `COHERENCE_MAX_CHECKS = 64`; `CoherenceReport` carries the snapshot, a deterministic `overall_status` aggregated by `compute_overall_status(...)` (`FAIL > WARN > PASS > NOT_APPLICABLE`; `NOT_APPLICABLE` never produces a false PASS), a deterministic `counts_by_status` tuple, and a bounded printable `summary_text`. New constants: `COHERENCE_MAX_CHECKS = 64`, `MAX_CHECK_ID_LEN = 64`, `MAX_SUMMARY_LEN = 240`, `MAX_DETAIL_LEN = 240`, `MAX_SOURCE_LEN = 32`. Read-only check families cover kernel coherence (cogito-in-profile / cogito-in-MSI / profile-values-bounded / PtCns-total-over-profile-domain / MSI-subset-profile-domain / latest-tick-index-agrees), session coherence (no-unsafe-resources / active-view-legal / event-queue-bounded / status-error-bounded / pattern-ledger-field), stream coherence (history-bounded / candidates-bounded / chunk_serial-consistent / no-cogito-in-chunks), Pattern Ledger coherence (entries-bounded / entries-validate-constructor-invariants / recurrence-counts-bounded / confidence-matches-formula / evidence-ids-bounded / pattern_id-matches-signature / session-local-only), persistence/autosave reporting (read-only; no DB open; no `save_session` / `load_session` / `db_backup` / `db_verify` / autosave call), and a non-claim term audit. Static AST audit (`I-COHMON-10`) rejects every forbidden import / module reference / dynamic-execution call; allowed imports are exactly the documented seam (`dataclasses`, `enum`, `fractions`, `typing`, `brain.development.pattern_ledger`, `brain.development.text_stream`, `brain.io_types`, `brain.tick` typed record only, `brain.tlica.msi`, `brain.tlica.profile`, `brain.tlica.ptcns`, `brain.ui.session`, `brain.ui.snapshot`, `brain.ui.commands`). Implemented as Option A per Step 13 Review Gate C: pure read-only helper / snapshot API only; no `OperatorSession` slot is added, no new `OperatorCommand` member, no new `LOCAL_COMMAND_VERBS` entry, no new `ACTIVE_VIEWS` value, no new dispatcher, no new renderer, and no new fixture-allowlist tier in the persistence resource-audit fixtures. `I-COHMON-13` (`/coherence-summary` UI) is DEFERRED; `I-COHMON-14` (end-to-end dry run) is NOT-EXERCISED; both can be promoted by a follow-up reviewed catalog patch. The Phase 3.12c Coherence Monitor does NOT modify `brain/tick.py`, `brain/llm/`, `brain/tlica/`, `brain/development/text_stream.py`, `brain/development/pattern_ledger.py`, `brain/ui/persistence.py`, `brain/ui/persistence_ops.py`, `brain/ui/persistence_observe.py`, `brain/ui/autosave.py`, `brain/ui/commands.py`, `brain/ui/command_line.py`, `brain/ui/render.py`, `brain/ui/snapshot.py`, `brain/ui/session.py`, persistence / autosave / observability behavior, scenarios, traces, or any guarded kernel path; `/step` behavior is bit-for-bit identical to its pre-monitor semantics.
- **v0.21** — +I-PLEDGER-01..18 (Phase 3.12c Pattern Ledger: bounded session-local developmental ledger of recurring structural patterns at `brain/development/pattern_ledger.py`). Option A scope: +15 REQUIRED rows, +1 STRUCTURAL row, +1 NOT-EXERCISED row, +1 DEFERRED row. `PatternLedgerSourceKind` mirrors `TextStreamSource`; `PatternLedgerSaturationState` is `OPEN` / `SATURATED` / `QUIESCED`. `PatternLedgerEntry` is a frozen / slotted record with bounded printable identifiers, `COGITO_ID` rejection on every id-bearing field, tuple-typed evidence, exact `Fraction` confidence equal to `Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)`, `last_seen_tick >= first_seen_tick`, recurrence-count range `[STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX]`, and strict rejection of direct construction with duplicate evidence ids. Pattern signatures are derived from exact `StreamFeatureVector` values via `derive_pattern_signature(chunk)` with no raw text payload; pattern ids are deterministic `"pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]`. `PatternLedger.observe(chunk, candidate, *, current_tick)` is pure copy-on-write, saturates `recurrence_count` at `STREAM_PATTERN_RECURRENCE_MAX`, filters duplicate `chunk_id` / `candidate_id` evidence (idempotent), caps each evidence list at `PATTERN_LEDGER_EVIDENCE_MAX = 32` independently, and hard-refuses new signatures at `PATTERN_LEDGER_MAX_ENTRIES = 64` (no eviction). New constants: `PATTERN_LEDGER_MAX_ENTRIES = 64`, `PATTERN_LEDGER_EVIDENCE_MAX = 32`, `PATTERN_LEDGER_ID_MAX = 64`, `PATTERN_LEDGER_SIGNATURE_ELEM_MAX = 64`. Session-local integration through a single new `OperatorSession.pattern_ledger` field (added to `_ALLOWED_SESSION_ATTRS`) and a single `observe(...)` call site at the end of the successful path of `_dispatch_stream_append`. Static AST audit (`I-PLEDGER-15`) rejects every forbidden import / module reference / dynamic-execution call. Persistence is session-local only: no `pattern_ledger` table, no `SCHEMA_VERSION_V*` bump, no `/save-session` serialization, no `/load-session` restore, no autosave extension. `I-PLEDGER-17` (optional `/pattern-ledger` UI) is DEFERRED in v1; `I-PLEDGER-18` (end-to-end dry run) is NOT-EXERCISED in v1; both can be promoted by a follow-up reviewed catalog patch. The Phase 3.12c Pattern Ledger does NOT modify `brain/tick.py`, `brain/llm/`, `brain/tlica/`, `brain/development/text_stream.py`, persistence / autosave / observability modules, scenarios, traces, or any guarded kernel path; `/step` behavior is bit-for-bit identical to its pre-ledger semantics.
- **v0.20** — +I-LLMTOG-16..18 (Phase 3.11 Codex CLI Runtime Option: explicit `--llm-mode codex-cli` extension over the existing Phase 3.8b `I-LLMTOG-*` family). Adds `CODEX_CLI` as the fifth `LlmRuntimeMode` member; `build_llm_client_from_config` dispatches to a new `_build_codex_cli_client` helper that resolves `codex_cli_executable` via `_which`, raises `LlmRuntimeError` naming the missing executable when resolution fails, and otherwise returns a frozen/slots `CodexCLIClient` (in `brain/llm/client.py`) whose default `command` tuple is `("codex", "exec")` and whose `timeout_seconds` is shared with `--llm-timeout`. New CLI flag `--llm-codex-cli-executable PATH` (default `"codex"`). `BRAIN_LLM_MODE=codex-cli` accepted. Cache wrapping, `--print-once` independence, explicit-opt-in, tick seam, and static AST audit rules extend to `CODEX_CLI`. `LlmRuntimeConfig` adds one new field `codex_cli_executable: str`. I-LLMTOG-12 STRUCTURAL row body updates from four-member to five-member assertion. I-LLMTOG-18 is an OBSERVED real-codex smoke walk documented in `docs/campaigns/phase3_11/PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md` Section 11 and `docs/campaigns/phase3_11/PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md`. The Phase 3.11 Codex CLI Runtime Option does NOT modify `brain/tick.py`, persistence, autosave, observability, or any non-LLM source file; offline remains the default and `codex-cli` is explicit opt-in.
- **v0.19** — +I-AUTOSAVE-01..15 (Phase 3.10c Autosave Policy: default-off, opt-in autosave layer at `brain/ui/autosave.py` over the existing Phase 3.9 `save_session` helper). `AutosaveMode` is a finite closed `(str, Enum)` with exactly `OFF` and `AFTER_SUCCESSFUL_MUTATION` members; `AutosaveTrigger` is a finite closed `(str, Enum)` with exactly `STEP_TICK` and `STREAM_PROMOTE` members. Default is `OFF` on every cold start at session construction AND at CLI parse time; no `BRAIN_AUTOSAVE_MODE` ambient env. `/autosave-enable` requires `--session-db` and raises `PersistenceError` otherwise; `/autosave-disable` is idempotent and never raises; `/autosave-status` returns a bounded report and never raises. `maybe_autosave_after_mutation` is the sole autosave entry point reachable from any dispatch path; fires AFTER `OperatorSession.dispatch` returns from a successful mutating dispatch (`/step` with `STEP_TICK`, `/stream-promote` with `STREAM_PROMOTE`); never fires after a failed dispatch, never fires after a read-only dispatch, never fires inside `tick()`; absorbs every `PersistenceError` into the typed status report (NEVER raises). Autosave reuses Phase 3.9 `save_session` via the existing transactional `BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK` discipline; no second save code path. Failure preserves the live `OperatorSession` and the on-disk session DB. New typed `OperatorCommand` kinds (`AUTOSAVE_STATUS`, `AUTOSAVE_ENABLE`, `AUTOSAVE_DISABLE`) + `AutosaveEnablePayload`. New CLI flag `--autosave-mode {off, after-successful-mutation}` (default `off`; requires `--session-db` for non-off). Two new optional `OperatorSession` fields (`autosave_config`, `last_autosave_status`). `brain/ui/autosave.py` static audit: no `@atexit`, no `threading`, no `asyncio`, no `signal` handler, no `curses` callback, no `tick(` call. The Phase 3.9 `I-PERSIST-16` row is RECLASSIFIED in this patch (NOT-EXERCISED -> STRUCTURAL) with a narrowed proposition (`brain/ui/persistence.py` owns no autosave trigger or background autosave hook); its row ID is preserved.
- **v0.18** — +I-OPSHARDEN-01..14 + I-OBSERVE-01..11 (Phase 3.10 Operational Hardening + Persistence Observability, tracks A + B only; track C autosave is deferred to a later catalog patch). Phase 3.10a adds read-only `/session-status`, read-only `/db-status` (sqlite3 uri `mode=ro`), candidate-DROPPING `/db-verify` that reuses `load_session` and runs invariants without swapping the live session, and byte-faithful `/db-backup` via `sqlite3.Connection.backup()` with `--force` overwrite gate and URI-scheme rejection (`sqlite:`, `file:`, `http:`, `https:`, `ftp:`, `ws:`, `wss:`, `data:`, `gopher:`, `ssh:`, `git:`). New one-shot CLI flags `--db-status` / `--db-verify` / `--db-backup PATH` / `--db-backup-force` are mutually exclusive at argparse time and short-circuit after `--check-terminal` / `--print-once` but before `parse_llm_runtime_args`; exit code 0 on success, 1 on failure. Phase 3.10b adds bounded read-only `/db-summary`, COGITO-first deterministically-sorted exact-`Fraction`-`"num/den"` `/profile-summary`, head+tail-bounded `/stream-db-summary` (`STREAM_TEXT_PREVIEW_MAX_LEN = 64`), and finite-field-enumeration `/db-diff` with explicit `"<missing>"` markers on one-sided absence. Observability commands never activate saved state and never mutate live `BrainState`. Default row caps: `PROFILE_SUMMARY_ROW_CAP = 64`, `STREAM_DB_SUMMARY_HEAD_CAP = 8`, `STREAM_DB_SUMMARY_TAIL_CAP = 8`, `DB_DIFF_ROW_CAP = 32`, `OPS_REPORT_TEXT_MAX_LEN = 256`. New typed `OperatorCommand` kinds (`SESSION_STATUS`, `DB_STATUS`, `DB_VERIFY`, `DB_BACKUP`, `DB_SUMMARY`, `PROFILE_SUMMARY`, `STREAM_DB_SUMMARY`, `DB_DIFF`) plus `DbBackupPayload`. New owning modules `brain/ui/persistence_ops.py` and `brain/ui/persistence_observe.py`; one narrow extension to `brain/ui/persistence.py` promoting `_snapshot_session` to the public `snapshot_session` helper. No autosave, no second save path, no new `OperatorSession` fields in 3.10a/b.

Companion docs (consult the relevant one when editing the catalog). All
historical campaign artifacts live under `docs/campaigns/`; see
`docs/campaigns/README.md` for the per-phase index.

- `docs/campaigns/archive/PLAN_CORRIGENDA.md` (v0 plan corrigenda).
- `docs/campaigns/archive/PHASE2_v1_KICKOFF.md` / `docs/campaigns/archive/PHASE2_v1_CORRIGENDA.md` (LLM-backed `PtCns`).
- `docs/campaigns/archive/PHASE2_v1_1_TRACE_KICKOFF.md` (cognition trace).
- `docs/campaigns/archive/BASELINE_HARDENING_KICKOFF.md` (Phase 2 v1.2 baseline hardening).
- `docs/campaigns/archive/PHASE3_5_EXPRESSION_READABILITY_AUDIT.md` (Phase 3.5 complete; PASS).
- `docs/campaigns/archive/PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md` (Phase 3.6 complete; PASS).
- `docs/campaigns/archive/PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md` (Phase 3.7 complete; PASS).
- `docs/campaigns/archive/PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md` (Phase 3.8 complete; PASS).
- `docs/campaigns/archive/PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md` (Phase 3.8b complete; PASS).
- `docs/campaigns/archive/PHASE3_TEXT_INTERACTION_DRY_RUN.md` (Fast Safe Text Interaction end-to-end walk).
- `CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` (Phase 3.12 Coherent I-Loop Observatory — current).
- `docs/campaigns/phase3_9/PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md` (Phase 3.9 roadmap).
- `docs/campaigns/phase3_12/PHASE3_12_COHERENT_I_LOOP_AUDIT.md` (Phase 3.12 complete; PASS).
- `docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md` (canonical seed for a future Phase 3.13 Growth Ledger campaign).

## Constraints (pre-coding rules — these are pulled from the catalog)

If any of these is unclear at code time, the catalog is canonical. Do not relax them.

### Catalog version

Use `INVARIANT_CATALOG.md` as shipped. Version banner inside should say **v0.29**. Confirmation numbers: **294 REQUIRED · 92 STRUCTURAL · 14 NOT-EXERCISED · 15 DEFERRED · 16 OBSERVED · 181 fixtures** (Phase 3.21 Developmental Trajectory catalog patch added `I-DEVMILE-01..11` and eleven new fixtures: `developmental_milestone_m01.py` through `developmental_milestone_m10.py` covering the per-milestone REQUIRED rows and `developmental_milestone_static_audit.py` covering the STRUCTURAL row; all eleven rows participate in I-CAT-01 coverage. The Phase 3.20 Coherence Feedback Bridge additions, the Phase 3.19 Internal Feedback Loop additions, the Phase 3.18 Bounded Internal Processing Window additions, the Phase 3.15 L1 Cache Hygiene additions, and the Phase 3.14 LLM Cache Discipline additions are unchanged.). Run `python3 -m tools.catalog counts` to verify; the strict gate fails if banner / actual / expected ever drift. If you see anything that looks like 74 REQUIRED, 92 REQUIRED (without 294 alongside), float+EPS, or `Literal[...]` for `Act`, that is an older draft and is wrong.

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

For catalog v0.31, the expected count is:
**313 REQUIRED · 95 STRUCTURAL · 14 NOT-EXERCISED · 15 DEFERRED · 16 OBSERVED**.

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
