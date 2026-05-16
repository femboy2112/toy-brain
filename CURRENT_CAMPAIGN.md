# CURRENT_CAMPAIGN.md — Phase 3.9 Persistent Session Store Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / FINAL-PR
```

This campaign replaces the completed Fast Safe Text Interaction campaign. The repo can now run a bounded operator text-stream loop with an explicit LLM runtime toggle, but that loop is still process-local: cold start recreates a fresh default session instead of restoring the accumulated profile, registry, text-stream history, tick counter, and session-local state.

Phase 3.9 adds explicit, invariant-checked persistence for session/profile continuity.

Preferred campaign branch:

```text
campaign/persistent-session-store
```

Preferred final PR title:

```text
phase3.9: persistent session store
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
```

This file may have been installed directly on `main` by explicit user instruction. That exception applies only to mission/campaign installation, not to campaign execution.

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_TEXT_INTERACTION_DRY_RUN.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
brain/ui/__main__.py
brain/ui/session.py
brain/tick.py
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Strategic target

Target user-visible capability:

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

Then, after process restart:

```bash
python3 -m brain.ui --session-db brain/session.sqlite3 --load-session
```

Expected restored state:

```text
BrainState.profile values restored exactly
MSI contents and threshold restored exactly
PtCns eval_map restored exactly
ContentRegistry texts restored exactly
OperatorSession.tick_counter restored
TextStreamHistory restored
stream_chunk_serial restored
stream candidates either restored or deterministically rebuilt
no LLM client persisted
no curses object persisted
```

---

## Baseline

Expected current state:

```text
Catalog: v0.16
Counts:
  REQUIRED:        178
  STRUCTURAL:       64
  NOT-EXERCISED:     9
  DEFERRED:         12
  OBSERVED:         12
Latest completed campaign: Fast Safe Text Interaction through Phase 3.8b LLM Runtime Toggle and Step 26 dry-run documentation
Latest audits:
  PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md      PASS
  PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md             PASS
Latest dry run:
  PHASE3_TEXT_INTERACTION_DRY_RUN.md
```

Known gap:

```text
build_default_session() constructs a fresh deterministic session every launch.
No durable BrainState/profile/session persistence exists yet.
Existing save/export rows are placeholders or cache-specific, not profile persistence.
```

---

## Persistence design thesis

Phase 3.9 should use SQLite through the Python standard library `sqlite3` module.

The persistence layer is not an arbitrary object dump. It is a typed store with explicit schema versioning, transactional writes, and load-time reconstruction through existing builders and constructors.

Recommended database path:

```text
brain/session.sqlite3
```

Recommended CLI flags:

```text
--session-db <path>
--load-session
--no-load-session
```

Recommended operator commands:

```text
/save-session
/load-session
```

Initial campaign should prefer explicit save/load. Autosave is deferred unless a later catalog row and policy explicitly authorize it.

---

## Non-negotiable boundaries

```text
no pickle
no shelve
no arbitrary object graph serialization
no direct assignment of loaded dicts into BrainState
no load that bypasses public builders / constructors
no load that skips assert_state_invariants
no persistence of LLM clients, sockets, file handles, subprocess handles, callables, curses objects, or open database connections on OperatorSession
no model output written to traces / scenarios / source histories by this campaign
no implicit autosave before an autosave policy exists
no save/export path outside the configured session database
no raw text -> BrainState direct mutation
no raw text -> COGITO_ID
no change to tick() semantics
```

Durable persistence may write only to the explicitly configured session database path. The SQLite connection itself must be scoped to save/load operations or a resource-safe persistence helper, not stored in BrainState.

---

## Minimum persisted state

The first accepted persistence layer should store and restore:

```text
BrainState:
  ScalarProfile domain and Fraction values
  MSI contents and threshold
  PtCns eval_map
  ContentRegistry texts

OperatorSession:
  tick_counter
  latest_tick summary or latest_tick absent marker
  stream_history
  stream_chunk_serial
  stream_candidates if accepted, otherwise deterministic rebuild

Metadata:
  schema version
  catalog version expected by the store
  created_at / updated_at timestamps
```

Optional / later:

```text
full TickRecord history
OperatorTranscript
OutputHistory / WorldletHistory / ProtoBasicHistory / ExpressionHistory / ReflectiveInspectionSummary
full event log replay
autosave policy
multi-profile support
```

---

## Exactness rules

Fractions must persist exactly. Use one of these forms:

```text
num INTEGER + den INTEGER
```

or:

```text
canonical string "num/den"
```

The campaign should prefer `num INTEGER + den INTEGER` for queryability. Do not store kernel numeric values as float.

---

## Suggested SQLite schema sketch

The kickoff and catalog patch plan may revise exact table names, but the accepted design should cover this shape:

```sql
meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
)

content_registry(
  content_id TEXT PRIMARY KEY,
  text TEXT NOT NULL
)

profile_values(
  content_id TEXT PRIMARY KEY,
  rho_num INTEGER NOT NULL,
  rho_den INTEGER NOT NULL
)

msi_contents(
  content_id TEXT PRIMARY KEY
)

ptcns_eval(
  content_id TEXT PRIMARY KEY,
  eval TEXT NOT NULL
)

session_state(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
)

stream_chunks(
  ordinal INTEGER PRIMARY KEY,
  chunk_id TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL,
  text TEXT NOT NULL,
  tick_at_event INTEGER NOT NULL,
  provenance_tag TEXT NOT NULL
)

stream_candidates(
  ordinal INTEGER PRIMARY KEY,
  candidate_id TEXT NOT NULL UNIQUE,
  target_content_id TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  pattern_id TEXT,
  source TEXT NOT NULL,
  text TEXT NOT NULL,
  provenance_tag TEXT NOT NULL
)

persistence_events(
  event_id INTEGER PRIMARY KEY,
  event_kind TEXT NOT NULL,
  created_at TEXT NOT NULL,
  detail TEXT NOT NULL
)
```

No table may store executable code, import paths for execution, shell commands, callable names for later invocation, raw pickle blobs, or opaque Python object reprs as authoritative state.

---

## Macro sequence

```text
Step 1      Repo-state sync for Phase 3.9
Step 2      Persistence synthesis
Step 3      Persistence kickoff
Step 4      Persistence corrigenda
Step 5      Persistence catalog patch plan
Step 6      Review gate
Step 7      Apply accepted catalog patch
Step 8      Implement SQLite schema + typed persistence records
Step 9      Implement save/load reconstruction through builders
Step 10     Add CLI flags and explicit /save-session / /load-session commands
Step 11     Cold-start continuity dry run
Step 12     Full persistence audit
Step 13     Final PR preparation
```

---

# Step 1 — Repo-state sync

Purpose: remove stale completed-campaign language and ensure the repo entrypoint points to Phase 3.9.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
PHASE3_9_PERSISTENT_SESSION_STORE_ROADMAP.md
```

Required work:

```text
update mission/campaign files to v0.16 baseline
state the completed Fast Safe Text Interaction campaign is merged
state Phase 3.9 is current
add or refresh the Phase 3.9 roadmap
preserve branch-first workflow for campaign execution
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
bash tools/check_all.sh
```

Commit and push.

---

# Step 2 — Persistence synthesis

Create:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_SYNTHESIS.md
```

Required content:

```text
v0.16 baseline
why persistence follows Phase 3.8b
why current interaction is process-local
why SQLite is preferred over pickle / arbitrary JSON dumps
what state should persist first
what remains deferred
how persistence preserves constructor / invariant discipline
how failed save/load behaves
why autosave is deferred
```

Validation:

```bash
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 3 — Persistence kickoff

Create:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_KICKOFF.md
```

Define likely structures:

```text
SessionStoreConfig
SessionStoreSchemaVersion
PersistentSessionSnapshot
PersistentBrainStateSnapshot
PersistentStreamSnapshot
SaveSessionResult
LoadSessionResult
PersistenceError
```

Define likely module:

```text
brain/ui/persistence.py
```

or, if corrigenda prefers a non-UI location:

```text
brain/persistence/session_store.py
```

The kickoff must decide or explicitly leave for corrigenda whether persistence is UI-owned, app-owned, or a new top-level subsystem.

Commit and push.

---

# Step 4 — Persistence corrigenda

Create:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md
```

Audit and lock:

```text
SQLite vs file snapshot
schema versioning
exact Fraction persistence
COGITO_ID reservation on load
constructor-only reconstruction
load failure isolation
save transaction behavior
no pickle / no object repr authority
session resource-free property
whether DB connection may be long-lived or operation-scoped
whether autosave is deferred
which rows should be REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED
```

Commit and push.

---

# Step 5 — Persistence catalog patch plan

Create:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-PERSIST-*
```

Likely row themes:

```text
schema version explicit
SQLite schema finite and closed
Fractions persist exactly
load reconstructs through builders / constructors
load runs invariants before activation
COGITO_ID cannot be overwritten by persisted data
failed load does not replace live session
failed save does not mutate live session
save transaction is atomic
session DB stores no LLM client / callable / handle / socket / subprocess / curses object
explicit /save-session command is bounded and local
explicit /load-session command is bounded and local
autosave is NOT-EXERCISED unless explicitly accepted
cold-start continuity dry run is OBSERVED
```

Stop at review gate after committing and pushing this plan. Do not apply catalog rows until the plan is accepted.

---

# Step 6 — Review gate

Stop unless Step 5 is explicitly accepted.

---

# Step 7 — Apply accepted catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional marker file only if accepted:

```text
brain/ui/persistence.py
```

or:

```text
brain/persistence/session_store.py
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 8 — Implement SQLite schema + typed persistence records

Allowed files per accepted plan, likely:

```text
brain/ui/persistence.py
brain/ui/fixtures/persistence_schema.py
brain/invariants.py
```

Required behavior:

```text
creates schema transactionally
stores schema version in meta
rejects unknown schema version
stores Fractions exactly
stores no pickles
stores no executable object repr as authoritative state
```

Validation:

```bash
python3 -m brain.invariants run --id I-PERSIST
bash tools/check_all.sh
```

Commit and push.

---

# Step 9 — Implement save/load reconstruction through builders

Allowed files per accepted plan.

Required behavior:

```text
save BrainState/profile/MSI/PtCns/registry/session stream fields
load reconstructs through public constructors / builders
load runs invariants before replacing session
failed load preserves existing session
failed save preserves existing session
COGITO_ID cannot be overwritten
```

Commit and push after targeted and full validation.

---

# Step 10 — Add CLI flags and explicit save/load commands

Likely files:

```text
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/render.py
brain/ui/fixtures/persistence_commands.py
README.md
```

Required behavior:

```text
--session-db <path>
--load-session / --no-load-session
/save-session
/load-session
explicit save/load only
default launch still works without persistence
invalid DB path or schema failure is local error
no autosave unless separately authorized
```

Commit and push after validation.

---

# Step 11 — Cold-start continuity dry run

Create:

```text
PHASE3_9_PERSISTENCE_DRY_RUN.md
```

Required scenario:

```text
launch with session DB
/stream hello world
/stream-promote promo-strm-chunk-1
/step
/save-session
quit
relaunch with same DB and --load-session
verify profile / registry / MSI / PtCns / tick_counter / stream_history restored
verify /stream-summary and /tick reflect restored state
```

Commit and push.

---

# Step 12 — Full persistence audit

Create:

```text
PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md
```

Audit:

```text
schema and migration behavior
exact Fraction persistence
constructor-only load
invariant checks before activation
COGITO_ID protections
failed save/load isolation
no forbidden persisted resources
explicit command behavior
full gate
remaining deferred work
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit and push.

---

# Step 13 — Final PR preparation

Open a PR to main with title:

```text
phase3.9: persistent session store
```

PR body must include:

```text
completed steps
catalog version/count transition
validation results
cold-start continuity achieved
persistence storage path and schema version
remaining deferred work, especially autosave if still deferred
confirmation that main was not pushed directly during campaign execution
confirmation that PR is not merged
```

Do not merge.
