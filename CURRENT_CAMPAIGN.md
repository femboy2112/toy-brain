# CURRENT_CAMPAIGN.md — Operator TUI Campaign

## Purpose

Build a simple terminal / ncurses-style operator interface for `toy-brain`.

The UI is for **bottom-up interaction and inspection**:

```text
inspect BrainState / TickRecord
inspect Phase 3.1–3.4 developmental histories
queue bottom-up PerceptEvent inputs
step through tick() deterministically
view classifications, modes, actions, traces, and local evidence
```

This is an operator-facing UI campaign, not a new cognitive/theory phase.

It does **not** authorize Phase 3.5 Expression + ReadabilityPredictor, social/language, Mode B, real LLM behavior, real host execution, open-ended process execution, shell execution, network I/O, or arbitrary code execution.

---

## Saved project state / baseline

Current saved state:

```text
Catalog: v0.9
Phase 3.4 Proto-BASIC REPL: PASS
Counts: 116 REQUIRED / 35 STRUCTURAL / 3 NOT-EXERCISED / 12 DEFERRED / 5 OBSERVED
Full gate: green
Completed developmental layers: Phase 3.1 Osmotic Chamber, Phase 3.2 Output Ladder, Phase 3.3 Minimal Worldlet, Phase 3.4 Proto-BASIC REPL
Next cognitive campaign still deferred: Phase 3.5 Expression + ReadabilityPredictor
```

The TUI may inspect these layers but must not reinterpret them as language, reflective agency, Mode B, external reality, or runtime promotion.

---

## Model-agnostic execution rule

When the user says `go`, the active repo-capable agent should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
run preflight
find the next eligible step from repo state
execute only that step's allowed scope
validate as specified
commit and push after successful steps
stop at explicit gates, failures requiring user judgment, or campaign completion
```

This applies to Codex, Claude Code, or any future agent with equivalent repo, shell, validation, commit, and push capability.

---

## Command rule

Use `python3 -m ...` for all Python module commands. Convert copied `python -m ...` examples to `python3 -m ...`.

---

## Accepted inputs

Read these as current state references unless the user says otherwise:

```text
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
PHASE3_2_OUTPUT_LADDER_AUDIT.md
PHASE3_3_MINIMAL_WORLDLET_AUDIT.md
PHASE3_4_PROTO_BASIC_REPL_AUDIT.md
INVARIANT_CATALOG.md
README.md
brain/tick.py
brain/io_types.py
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
```

---

## UI-specific rule

The TUI may display and route operator inputs through public APIs only.

Allowed state transitions must go through approved public surfaces, such as:

```text
PerceptEvent -> tick()
OutputHistory helper functions
WorldletHistory helper functions
ProtoBasicHistory helper functions
```

No UI command may directly mutate `BrainState`, profile, MSI, PtCns, content registry, developmental histories, traces, scenario files, catalog files, or private dataclass fields.

---

## Global hard boundaries

Never modify unless a step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

Never implement in this campaign:

```text
Phase 3.5 Expression + ReadabilityPredictor
social/language harness
Mode B
real LLM calls
real host execution
open-ended process execution
arbitrary Python execution
shell execution
network I/O
file-system mutation outside explicit user-approved save/export paths
```

Prefer standard-library `curses` plus pure non-interactive renderer/router modules for tests. Do not add external dependencies unless a reviewed plan explicitly allows them.

---

# Step 0 — Preflight

## Required reads

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_4_PROTO_BASIC_REPL_AUDIT.md
brain/tick.py
brain/io_types.py
brain/development/output.py
brain/development/worldlet.py
brain/development/repl.py
```

## Commands

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-REPL-18
bash tools/check_all.sh
```

Stop if the tree is dirty, the full gate fails, or Phase 3.4 audit is absent/not PASS.

---

# Step 1 — Operator TUI synthesis

Create `OPERATOR_TUI_SYNTHESIS.md`.

Required content:

```text
v0.9 saved-state summary
why a TUI is an operator tool, not a cognitive layer
bottom-up interaction thesis
state-inspection requirements
allowed input routes
forbidden mutation routes
non-goals
risks
next artifact: OPERATOR_TUI_KICKOFF.md
```

Validation:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 2 — Operator TUI kickoff

Create `OPERATOR_TUI_KICKOFF.md`.

Scope only:

```text
OperatorSession
BrainSnapshot / StateSnapshot
DevelopmentSnapshot
TuiViewModel
pure renderer
thin curses wrapper
OperatorCommand
OperatorEventQueue
approved command router
bottom-up PerceptEvent injection through tick()
read-only inspection of OutputHistory / WorldletHistory / ProtoBasicHistory
keyboard map
status/error pane
```

No real LLM, no new theory semantics, no Mode B, no expression/readability, no social/language, no shell/file/network execution.

Validation:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 3 — Operator TUI corrigenda

Create `OPERATOR_TUI_CORRIGENDA.md`.

Check:

```text
UI view vs cognitive layer
snapshot read-only discipline
allowed public API routes
bottom-up input representation
interactive curses vs testable pure renderer split
I-UI-* row status choices
save/export policy
trace/scenario write prohibition by default
```

Validation:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 4 — Operator TUI catalog patch plan

Create `OPERATOR_TUI_CATALOG_PATCH_PLAN.md`.

Specify:

```text
I-UI-* rows, statuses, owning modules, fixtures
count impact from current v0.9
fixture roster
module map
catalog patch mechanics
implementation order
open decisions
stop conditions
```

Likely row themes:

```text
snapshots are read-only / serializable
pure renderer is deterministic
command router uses only approved APIs
bottom-up PerceptEvent route goes through tick()
UI cannot directly mutate core or developmental state
curses wrapper is thin over tested renderer/router
no LLM / shell / network / host execution
status pane is local UI state only
```

Do not apply the catalog patch.

Validation:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 5 — Review gate

Stop unless `OPERATOR_TUI_CATALOG_PATCH_PLAN.md` is coherent and no open decision blocks implementation. If coherent, proceed only when the user says `go` again or explicitly accepts the plan.

---

# Step 6 — Apply accepted UI catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/ui/__init__.py
brain/ui/fixtures/__init__.py
```

Apply accepted `I-UI-*` rows, expected counts, generated IDs, and pending registrations only. No UI runtime behavior unless explicitly allowed by the accepted plan.

Commands:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push.

---

# Step 7 — Read-only snapshots and pure renderer

Allowed files:

```text
brain/ui/snapshot.py
brain/ui/render.py
brain/ui/fixtures/snapshot_view.py
brain/ui/fixtures/render_view.py
brain/invariants.py
```

Expected behavior:

```text
read-only BrainSnapshot / DevelopmentSnapshot
snapshot creation does not mutate state
pure renderer returns deterministic strings / view models
missing histories handled gracefully
panes for core state, latest tick, output/worldlet/repl histories, errors
```

Run targeted rows from the accepted plan. Commit/push.

---

# Step 8 — Operator command router and bottom-up event path

Allowed files:

```text
brain/ui/session.py
brain/ui/commands.py
brain/ui/fixtures/command_router.py
brain/ui/fixtures/bottom_up_tick.py
brain/invariants.py
```

Expected behavior:

```text
OperatorSession stores current BrainState and local histories
OperatorCommand is finite and typed
router supports inspect, queue PerceptEvent, step tick, help, quit
queued bottom-up tick path calls existing tick()
router stores TickRecord
invalid commands update local UI status only
no direct mutation of BrainState internals or developmental histories
```

Run targeted rows. Commit/push.

---

# Step 9 — Curses-style wrapper and CLI entrypoint

Allowed files:

```text
brain/ui/tui.py
brain/ui/__main__.py
brain/ui/fixtures/tui_smoke.py
README.md
```

Expected behavior:

```text
python3 -m brain.ui launches TUI or prints helpful no-terminal message
curses layer is thin over renderer/router
keyboard map includes inspect, queue percept, step, help, quit
non-interactive smoke test does not require real terminal
no LLM / shell / network / file mutation / host execution
```

Run targeted rows. Commit/push.

---

# Step 10 — Full gate

Run:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit/push final sync docs if needed.

---

# Step 11 — Post-completion audit

Create `OPERATOR_TUI_AUDIT.md` with verdict:

```text
PASS
PASS WITH PATCHES
BLOCKED
```

Audit:

```text
scope creep
row registration
read-only snapshot discipline
pure renderer determinism
bottom-up event route through tick()
curses wrapper thinness
kernel boundary
full gate
recommended next mission
```

Commit/push.

---

## Stop conditions requiring user review

Stop if any fix requires:

```text
editing brain/tlica/
changing tick() semantics
changing scenario schema
real LLM execution
non-standard dependency
state inspection via direct mutation
bottom-up interaction outside public APIs
shell/file/network execution
uncommitted external changes
```

---

## Campaign complete output

```text
Operator TUI campaign complete.
Catalog: <version>
Counts: <actual>
Full gate: pass
Entrypoint: python3 -m brain.ui
Remaining deferred work: Phase 3.5 Expression + ReadabilityPredictor and later cognitive campaigns
```
