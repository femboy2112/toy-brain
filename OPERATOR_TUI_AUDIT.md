# OPERATOR_TUI_AUDIT.md — Operator TUI Campaign Post-Completion Audit

## Verdict

```text
PASS
```

The Operator TUI campaign landed all I-UI-* catalog rows, all targeted
fixtures, the read-only snapshot layer, the pure renderer, the command
router with bottom-up event path, the thin curses wrapper, and the CLI
entrypoint. The full gate is green at v0.10. No guarded files were
mutated. No Phase 3.5 / Mode B / language / real-LLM / shell / network /
host-execution surface was introduced.

---

## Saved project state at audit time

```text
Catalog: v0.10
Counts (banner = actual = expected):
  REQUIRED       = 123
  STRUCTURAL     =  41
  NOT-EXERCISED  =   4
  DEFERRED       =  12
  OBSERVED       =   6
Total rows checked by invariants runner: 170
REQUIRED green: 123   REQUIRED red: 0
STRUCTURAL green:  41 STRUCTURAL red: 0
OBSERVED:           6 pass / 0 fail
Gate failures: 0
Full gate: green
Entrypoint: python3 -m brain.ui
```

Patch over v0.9: +7 REQUIRED, +6 STRUCTURAL, +1 NOT-EXERCISED, +1
OBSERVED for the Operator TUI surface.

---

## Scope creep

No scope creep observed.

The campaign did not modify guarded surfaces:

```text
brain/tlica/          untouched
brain/llm/            untouched
brain/tick.py         untouched
scenarios/            untouched
traces/first_scenario_real.jsonl   untouched
traces/RUN_SUMMARY.md untouched
lean_reference/       untouched
```

No new theory semantics, no Phase 3.5 Expression / ReadabilityPredictor,
no social/language harness, no Mode B, no real LLM call site, no
arbitrary code execution path, no network I/O, no filesystem write
outside the audit/synthesis/corrigenda/plan markdown trail and the
new `brain/ui/` module tree.

---

## Row registration

All accepted I-UI-* rows from `OPERATOR_TUI_CATALOG_PATCH_PLAN.md`
landed in `INVARIANT_CATALOG.md` and are present in
`brain/_catalog_ids.py`, registered through their owning modules:

```text
I-UI-01  REQUIRED       brain/ui/snapshot.py    snapshot_view.py
I-UI-02  REQUIRED       brain/ui/render.py      render_view.py
I-UI-03  REQUIRED       brain/ui/commands.py    command_router.py
I-UI-04  REQUIRED       brain/ui/commands.py    command_router.py
I-UI-05  REQUIRED       brain/ui/session.py     bottom_up_tick.py
I-UI-06  REQUIRED       brain/ui/session.py    command_router.py
I-UI-07  REQUIRED       brain/ui/__init__.py    tui_smoke.py
I-UI-08  STRUCTURAL     brain/ui/snapshot.py    snapshot_view.py
I-UI-09  STRUCTURAL     brain/ui/render.py      render_view.py
I-UI-10  STRUCTURAL     brain/ui/session.py     bottom_up_tick.py
I-UI-11  STRUCTURAL     brain/ui/tui.py         tui_smoke.py
I-UI-12  STRUCTURAL     brain/ui/__main__.py    tui_smoke.py
I-UI-13  STRUCTURAL     brain/ui/session.py     command_router.py
I-UI-14  OBSERVED       brain/ui/session.py     tui_smoke.py
I-UI-15  NOT-EXERCISED  brain/ui/__init__.py    (none)
```

Banner counts match actual counts under `python3 -m tools.catalog
counts`. Generated IDs in `brain/_catalog_ids.py` are consistent with
the catalog.

---

## Read-only snapshot discipline

Audited in `brain/ui/snapshot.py` and exercised by
`brain/ui/fixtures/snapshot_view.py` (I-UI-01, I-UI-08).

```text
BrainSnapshot / DevelopmentSnapshot construction is read-only over
  BrainState, ScalarProfile, MSI, PtCns, ContentRegistry, TickRecord,
  OutputHistory, WorldletHistory, ProtoBasicHistory, traces, scenarios,
  and catalog files.
Mutable kernel containers are projected into tuples / frozensets /
  display records before placement on a snapshot field.
Fraction values are rendered as strings; no float arithmetic is
  introduced into invariant-bearing paths.
Snapshot dataclasses are frozen (immutable display records).
```

I-UI-01 PASS and I-UI-08 PASS in the current runner output.

---

## Pure renderer determinism

Audited in `brain/ui/render.py` and exercised by
`brain/ui/fixtures/render_view.py` (I-UI-02, I-UI-09).

```text
Given the same TuiViewModel (or snapshot bundle + active view + width
  + height), render() returns equal display output across repeated
  calls.
Renderer does not call tick(), does not touch curses, and does not
  perform file / network / shell I/O.
TuiViewModel is a terminal-agnostic record of bounded primitives,
  tuples of bounded strings, and snapshot references; it carries no
  curses object, file handle, socket, LLM client, callable, or
  mutable reference into BrainState or developmental histories.
```

I-UI-02 PASS and I-UI-09 PASS in the current runner output.

---

## Bottom-up event route through tick()

Audited in `brain/ui/session.py` and `brain/ui/commands.py`, exercised
by `brain/ui/fixtures/bottom_up_tick.py` and
`brain/ui/fixtures/command_router.py` (I-UI-03, I-UI-04, I-UI-05,
I-UI-06, I-UI-13).

```text
OperatorCommand is a finite closed enumeration; construction with any
  other kind raises and no callable, shell string, file path, network
  endpoint, or arbitrary Python expression is accepted.
QUEUE_PERCEPT payloads are PerceptEvent-constructor-bounded; queued
  candidates are built via the public PerceptEvent constructor and
  out-of-range values raise without partial OperatorSession mutation.
STEP_TICK invokes tick(current_state, [queued_event], client) exactly
  once and stores the returned TickRecord on the OperatorSession; the
  session's BrainState is updated to the returned new state via the
  public tick() path only.
Validation and tick failures are recorded as local UI status / error
  text on the OperatorSession; BrainState, ScalarProfile, MSI, PtCns,
  ContentRegistry, OutputHistory, WorldletHistory, ProtoBasicHistory,
  trace files, scenario files, and catalog files are unchanged on
  failure.
UI status text is bounded printable text; the keyboard map is a finite
  enumeration matching the help pane.
```

I-UI-03, I-UI-04, I-UI-05, I-UI-06, I-UI-13 all PASS in the current
runner output.

---

## Curses wrapper thinness

Audited in `brain/ui/tui.py` and `brain/ui/__main__.py`, exercised by
`brain/ui/fixtures/tui_smoke.py` (I-UI-07, I-UI-11, I-UI-12, I-UI-14).

```text
brain/ui/tui.py imports only:
  __future__ annotations
  curses (stdlib)
  dataclasses.dataclass
  typing (TYPE_CHECKING, Callable, Optional)
  brain.ui.commands
  brain.ui.render
  brain.ui.session
  brain.ui.snapshot
It contains only screen initialization / teardown, key reading,
  key-to-OperatorCommand translation, painting of rendered rows, resize
  re-rendering, and clean quit.
It imports no module from brain/tlica/ or brain/llm/, calls no kernel
  mutation function, evaluates no arbitrary Python, and performs no
  file or network I/O.
brain/ui/__main__.py fails closed without a usable terminal and exits
  with a helpful local message; it does not spawn alternate shells,
  open files, call a browser, or mutate the filesystem.
tui_smoke.py performs a UI-specific static AST audit over brain/ui/
  rejecting forbidden imports (os.system, subprocess, socket, urllib,
  http, requests, brain.llm, TLICA beyond public surfaces) and
  forbidden host-execution surfaces.
```

I-UI-07 PASS, I-UI-11 PASS, I-UI-12 PASS, I-UI-14 OBS-PASS in the
current runner output.

---

## Kernel boundary

```text
No UI snapshot, renderer, command, router, session method, or curses
  wrapper code path:
  - calls real LLM client behavior
  - spawns a subprocess
  - opens a shell
  - performs network I/O
  - writes a file outside an explicitly user-approved save/export
    path (none exist in this campaign)
  - invokes arbitrary host execution
  - directly mutates BrainState, ScalarProfile, MSI, PtCns,
    ContentRegistry, developmental histories, traces, scenario files,
    or catalog files
The only kernel mutation route available to the UI is the public
  tick() path via STEP_TICK with a QUEUE_PERCEPT-built PerceptEvent.
The save/export NOT-EXERCISED placeholder I-UI-15 stands as the
  registered chokepoint that prevents a future campaign from quietly
  adding filesystem writes from the UI without registered coverage.
```

---

## Full gate

Step 10 full-gate command outputs at audit time:

```text
python3 -m tools.catalog counts
  REQUIRED       = 123 (banner = actual = expected)
  STRUCTURAL     =  41
  NOT-EXERCISED  =   4
  DEFERRED       =  12
  OBSERVED       =   6
  all ok

python3 -m tools.citations verify
  Verified 100 citations.
  All catalog citations resolve in lean_reference/.

python3 -m tools.import_audit
  I-PCE-05: agency.py is clean of pce imports.

python3 -m brain.invariants run
  170 rows checked
  REQUIRED green: 123   REQUIRED red: 0
  STRUCTURAL green: 41  STRUCTURAL red: 0
  OBSERVED: 6 pass / 0 fail
  gate failures: 0

bash tools/check_all.sh
  All checks passed.
```

Full gate is green.

---

## Step-by-step trail

```text
Step 1  synthesis             commit ccdceed
Step 2  kickoff               commit 03238b5
Step 3  corrigenda            commit cf48206
Step 4  catalog patch plan    commit fb35029
Step 5  review gate +
        D3 corrigendum        commit 4e3a024, 392d5db
Step 6  apply catalog patch   commit 2a08df0
Step 7  snapshots + renderer  commit 7e7ac64
Step 8  router + bottom-up    commit 874d513
Step 9  curses + CLI          commit 21001c9
Step 10 full gate             no file changes, green
Step 11 post-completion audit this file
```

---

## Stop-condition triggers encountered

None. No fix required:

```text
editing brain/tlica/
changing tick() semantics
changing scenario schema
real LLM execution
non-standard dependency
state inspection via direct mutation
bottom-up interaction outside public APIs
shell / file / network execution
uncommitted external changes
```

---

## Recommended next mission

The Operator TUI campaign is complete. The remaining deferred
cognitive work continues to be:

```text
Phase 3.5 Expression + ReadabilityPredictor
  followed by later cognitive campaigns (social / language, etc.)
```

Phase 3.5 is the next eligible cognitive layer per the saved project
state. A future mission should:

```text
synthesize Phase 3.5 Expression + ReadabilityPredictor scope
produce a kickoff, corrigenda, and catalog patch plan
gate on review before implementation
land catalog rows, fixtures, and module code under explicit allow-lists
keep Mode B, real LLM, social/language harness, and host execution out
  of scope unless a future explicit gate authorizes them
```

The Operator TUI surface is available for inspection during that work
via `python3 -m brain.ui` and provides bottom-up PerceptEvent injection
plus read-only inspection of `OutputHistory`, `WorldletHistory`, and
`ProtoBasicHistory` through public APIs only.

---

## Campaign complete output

```text
Operator TUI campaign complete.
Catalog: v0.10
Counts: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 6 OBSERVED
Full gate: pass
Entrypoint: python3 -m brain.ui
Remaining deferred work: Phase 3.5 Expression + ReadabilityPredictor and later cognitive campaigns
```
