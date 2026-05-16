# brain — TLICA-constrained Python kernel (catalog v0.16)

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
```

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

Companion docs (consult the relevant one when editing the catalog):
- `PLAN_CORRIGENDA.md` (v0 plan corrigenda).
- `PHASE2_v1_KICKOFF.md` / `PHASE2_v1_CORRIGENDA.md` (LLM-backed `PtCns`).
- `PHASE2_v1_1_TRACE_KICKOFF.md` (cognition trace).
- `BASELINE_HARDENING_KICKOFF.md` (Phase 2 v1.2 baseline hardening).
- `PHASE3_5_EXPRESSION_READABILITY_AUDIT.md` (Phase 3.5 complete; PASS).
- `CURRENT_CAMPAIGN.md` (Fast Safe Text Interaction — Phase 3.6 next).

## Constraints (pre-coding rules — these are pulled from the catalog)

If any of these is unclear at code time, the catalog is canonical. Do not relax them.

### Catalog version

Use `INVARIANT_CATALOG.md` as shipped. Version banner inside should say **v0.16**. Confirmation numbers: **178 REQUIRED · 64 STRUCTURAL · 9 NOT-EXERCISED · 12 DEFERRED · 12 OBSERVED · 91 fixtures**. Run `python3 -m tools.catalog counts` to verify; the strict gate fails if banner / actual / expected ever drift. If you see anything that looks like 74 REQUIRED, 92 REQUIRED, float+EPS, or `Literal[...]` for `Act`, that is an older draft and is wrong.

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

For catalog v0.16, the expected count is:
**178 REQUIRED · 64 STRUCTURAL · 9 NOT-EXERCISED · 12 DEFERRED · 12 OBSERVED**.

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
