# OPERATOR_TUI_CATALOG_PATCH_PLAN.md

## 1. Purpose

This document plans the catalog patch for the Operator TUI campaign. It
specifies the proposed `I-UI-*` row family, statuses, owning modules, fixture
files, count impact, fixture roster, module map, catalog patch mechanics,
implementation order, open decisions, and stop conditions.

It is a planning artifact only. It does not apply the patch. It does not edit
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`, or
`brain/invariants.py`. It does not add runtime modules under `brain/ui/`,
add fixtures under `brain/ui/fixtures/`, change `tick()` semantics, modify
developmental histories, write traces or scenarios, modify Lean reference
files under `lean_reference/`, add dependencies, or introduce host execution.

Step 6 of `CURRENT_CAMPAIGN.md` is the apply step. The review gate at Step 5
decides whether to enter Step 6.

## 2. Inherited Baseline

Catalog version: v0.9.

Current counts (verified via `python3 -m tools.catalog counts` on this branch
prior to this artifact):

```text
REQUIRED       116
STRUCTURAL      35
NOT-EXERCISED    3
DEFERRED        12
OBSERVED         5
```

Completed developmental layers: Phase 3.1 Osmotic Chamber, Phase 3.2 Output
Ladder, Phase 3.3 Minimal Worldlet, Phase 3.4 Proto-BASIC REPL. The full
gate is green and `I-REPL-18` remains OBSERVED.

The Operator TUI catalog patch is additive: it introduces a new `I-UI-*` row
family. It does not retire, renumber, or relocate any existing row.

## 3. Row-Family Conventions

The `I-UI-*` family captures Operator TUI discipline. It is an operator-console
family, not a cognitive-layer family. Each row must read as a constraint on a
display, snapshot, command, router, or thin terminal wrapper — not as a claim
about kernel cognition.

Each row follows the existing catalog schema with the columns:

```text
ID | Lean source | Proposition | Python assertion | Owning module | Fixture | Status
```

The Lean-source column should record an engineering hypothesis tied to this
campaign rather than a Lean theorem, mirroring the convention used by the
existing Phase 3.1-3.4 developmental rows (for example
`Engineering hypothesis (Phase 3.4 Proto-BASIC REPL)`). The Operator TUI rows
should use:

```text
Engineering hypothesis (Operator TUI)
```

The catalog section header for the new rows should be:

```text
### Operator TUI invariants
```

placed after the existing Phase 3.4 Proto-BASIC REPL developmental invariants
section and before the Meta / runner integrity section.

## 4. Proposed I-UI-* Rows

The proposed row set has 15 rows. Statuses are conservative: REQUIRED only when
a row has a deterministic assertion over a public surface; STRUCTURAL when the
property is enforced by construction or type discipline; OBSERVED when the row
is a qualitative inspection report; NOT-EXERCISED for placeholders intentionally
without a fixture in this campaign.

### REQUIRED rows (7)

```text
I-UI-01  Snapshot read-only over kernel state
         BrainSnapshot construction does not mutate BrainState, ScalarProfile,
         MSI, PtCns, ContentRegistry, TickRecord, OutputHistory,
         WorldletHistory, ProtoBasicHistory, trace backends, scenario files,
         or catalog files; identities and string representations of those
         containers are unchanged before and after snapshot construction.
         Owning module : brain/ui/snapshot.py
         Fixture       : snapshot_view.py
         Status        : REQUIRED

I-UI-02  Pure renderer determinism
         Given the same TuiViewModel (or snapshot bundle + active view +
         width + height), brain/ui/render.render(...) returns equal display
         output across repeated calls; rendering does not call tick(), does
         not touch curses, and does not perform file/network/shell I/O.
         Owning module : brain/ui/render.py
         Fixture       : render_view.py
         Status        : REQUIRED

I-UI-03  OperatorCommand is a finite closed enumeration
         OperatorCommand instances belong to the documented enumeration
         (INSPECT_STATE, INSPECT_TICK, INSPECT_OUTPUT, INSPECT_WORLDLET,
         INSPECT_REPL, QUEUE_PERCEPT, STEP_TICK, CLEAR_STATUS, HELP, QUIT,
         NOOP); construction with any other kind raises and no callable,
         shell string, file path, network endpoint, or arbitrary Python
         expression is accepted in any command payload.
         Owning module : brain/ui/commands.py
         Fixture       : command_router.py
         Status        : REQUIRED

I-UI-04  QUEUE_PERCEPT payload is PerceptEvent-constructor bounded
         A QUEUE_PERCEPT payload carries only content_id, text, ContentState
         flags, and initial_rho values accepted by the public PerceptEvent
         constructor; construction of a queued candidate uses that
         constructor and out-of-range values raise without partially
         mutating the OperatorSession.
         Owning module : brain/ui/commands.py
         Fixture       : command_router.py
         Status        : REQUIRED

I-UI-05  STEP_TICK route uses the public tick() path only
         A successful STEP_TICK call invokes
         tick(current_state, [queued_event], client) exactly once with the
         operator-queued PerceptEvent, stores the returned TickRecord on the
         OperatorSession, and updates the session's BrainState to the
         returned new state; no other kernel mutation route is taken.
         Owning module : brain/ui/session.py
         Fixture       : bottom_up_tick.py
         Status        : REQUIRED

I-UI-06  Validation and tick failures are local UI status only
         If PerceptEvent validation or tick() raises, the router records the
         failure as local UI status/error text on the OperatorSession and
         leaves BrainState, ScalarProfile, MSI, PtCns, ContentRegistry,
         OutputHistory, WorldletHistory, ProtoBasicHistory, trace files,
         scenario files, and catalog files unchanged.
         Owning module : brain/ui/session.py
         Fixture       : command_router.py
         Status        : REQUIRED

I-UI-07  No LLM / shell / network / file / host execution from any UI path
         No UI snapshot, renderer, command, router, session method, or
         curses-wrapper code path calls real LLM client behavior, spawns a
         subprocess, opens a shell, performs network I/O, writes a file
         outside an explicitly user-approved save/export path (none exist
         in this campaign), or invokes arbitrary host execution; static
         import audit over brain/ui/ confirms no imports of os.system,
         subprocess, socket, urllib, http, requests, brain.llm, or brain.tlica.
         Owning module : brain/ui/__init__.py
         Fixture       : tui_smoke.py
         Status        : REQUIRED
```

### STRUCTURAL rows (6)

```text
I-UI-08  Snapshot records are immutable display values
         BrainSnapshot and DevelopmentSnapshot are frozen dataclasses (or
         equivalently immutable records). Mutable kernel containers (maps,
         sets, sequences) are copied into tuples / frozensets / plain
         display records before being placed on a snapshot field. Exact
         Fraction values are rendered as strings; no UI display field
         introduces float arithmetic into invariant-bearing paths.
         Owning module : brain/ui/snapshot.py
         Fixture       : snapshot_view.py
         Status        : STRUCTURAL

I-UI-09  TuiViewModel is a small terminal-agnostic data contract
         TuiViewModel is an immutable record whose fields are bounded
         primitives, tuples of bounded strings, or snapshot references; it
         carries no curses objects, no file handles, no sockets, no real
         LLM client, no callable, and no mutable reference into BrainState
         or developmental histories.
         Owning module : brain/ui/render.py
         Fixture       : render_view.py
         Status        : STRUCTURAL

I-UI-10  OperatorSession holds no unsafe resources
         OperatorSession contains no real LLM client, no subprocess handle,
         no file descriptor, no network socket, no shell-command string
         intended for execution, and no host-execution callback. It holds
         only the current BrainState, optional latest TickRecord, optional
         local developmental histories, a bounded OperatorEventQueue, the
         active view selection, the local UI status/error, and a quit flag.
         Owning module : brain/ui/session.py
         Fixture       : bottom_up_tick.py
         Status        : STRUCTURAL

I-UI-11  Curses wrapper contains only terminal-handling code
         brain/ui/tui.py contains only screen initialization/teardown, key
         reading, key-to-OperatorCommand translation, painting of rendered
         rows, resize re-rendering, and clean quit. It imports no module
         from brain/tlica/ or brain/llm/, calls no kernel mutation
         function, evaluates no arbitrary Python, and performs no file or
         network I/O.
         Owning module : brain/ui/tui.py
         Fixture       : tui_smoke.py
         Status        : STRUCTURAL

I-UI-12  Entrypoint fails closed without a usable terminal
         brain/ui/__main__.py exits with a helpful local message when no
         usable terminal is available; it does not spawn alternate shells,
         open files, call a browser, or mutate the filesystem; the
         non-interactive smoke test exercises this code path without
         attaching to a real terminal.
         Owning module : brain/ui/__main__.py
         Fixture       : tui_smoke.py
         Status        : STRUCTURAL

I-UI-13  Local UI status text is bounded printable text only
         OperatorSession status/error text is bounded printable text and is
         never written to a trace event, scenario entry, OutputHistory /
         WorldletHistory / ProtoBasicHistory entry, or catalog row result;
         the keyboard map is a finite enumeration that matches the help
         pane.
         Owning module : brain/ui/session.py
         Fixture       : command_router.py
         Status        : STRUCTURAL
```

### OBSERVED rows (1)

```text
I-UI-14  Aggregate Operator TUI session walks are inspectable
         A sequence of operator commands (inspect / queue / step / clear /
         help / quit) over a deterministic injected tick client records
         a summary of view transitions, queued events, accepted and failed
         validations, tick records produced, and absence of kernel-boundary
         leaks; the row is OBSERVED and cannot fail the runner.
         Owning module : brain/ui/session.py
         Fixture       : tui_smoke.py
         Status        : OBSERVED
```

### NOT-EXERCISED rows (1)

```text
I-UI-15  Save / export path policy placeholder
         No Operator TUI save / export path exists in this campaign. Any
         future save / export path requires an explicit reviewed policy
         artifact, dedicated catalog rows that constrain the path, fixtures
         that exercise the path under bounded conditions, and a stop
         condition for failure modes. This row exists so a future campaign
         cannot quietly add filesystem writes from the UI without
         registering coverage.
         Owning module : brain/ui/__init__.py
         Fixture       : (none in this campaign)
         Status        : NOT-EXERCISED
```

## 5. Status Discipline

Status choices follow the corrigenda:

```text
REQUIRED rows have deterministic public-surface assertions: snapshot
  read-only check, renderer determinism check, OperatorCommand enumeration
  check, QUEUE_PERCEPT payload check, STEP_TICK tick() route check, failure
  isolation check, and import-audit-based no-host-execution check.
STRUCTURAL rows are construction- or type-enforced: immutable snapshots,
  contract-only TuiViewModel, resource-free OperatorSession, terminal-only
  curses wrapper, fail-closed entrypoint, bounded-printable status text.
OBSERVED is reserved for one summary walk row that records UI-session
  inspection evidence without gating the runner.
NOT-EXERCISED is reserved for the save/export placeholder, which exists to
  prevent silent expansion of filesystem mutation surfaces.
```

The plan deliberately keeps the REQUIRED set small. Each REQUIRED row should
read as an enforceable invariant over a public surface, not as a paragraph of
prose. If a property cannot be expressed as a deterministic assertion, it
should be STRUCTURAL or OBSERVED rather than REQUIRED.

## 6. Count Impact from v0.9

Adding the proposed rows yields the following projected counts:

```text
Category         v0.9 actual   v0.9 + I-UI-*   Delta
REQUIRED            116             123          +7
STRUCTURAL           35              41          +6
NOT-EXERCISED         3               4          +1
DEFERRED             12              12           0
OBSERVED              5               6          +1
```

`tools/catalog.py` records expected counts per category. The catalog patch
must update those expected counts to match the projected actuals, otherwise
`python3 -m tools.catalog counts` will report a mismatch.

If the review gate accepts a different row set or status mix, the count
impact must be recomputed before applying the patch.

## 7. Fixture Roster

Fixture files live under `brain/ui/fixtures/`. Each fixture is named for the
behaviour it drives, mirroring the convention used by
`brain/development/fixtures/`.

```text
brain/ui/fixtures/snapshot_view.py
  drives  : I-UI-01, I-UI-08
  asserts : snapshot construction is read-only over kernel state,
            snapshot records are immutable display values,
            mutable kernel containers are copied to immutable display fields,
            Fraction values appear as exact strings.

brain/ui/fixtures/render_view.py
  drives  : I-UI-02, I-UI-09
  asserts : pure renderer is deterministic over identical inputs,
            TuiViewModel carries only safe data,
            no curses / file / network / shell / tick() calls during render,
            missing histories render as empty / unavailable.

brain/ui/fixtures/command_router.py
  drives  : I-UI-03, I-UI-04, I-UI-06, I-UI-13
  asserts : OperatorCommand is a finite closed enumeration,
            QUEUE_PERCEPT payload is PerceptEvent-constructor bounded,
            validation / tick failures are local UI status only,
            local UI status text is bounded printable text and not trace,
              scenario, developmental, or catalog evidence.

brain/ui/fixtures/bottom_up_tick.py
  drives  : I-UI-05, I-UI-10
  asserts : STEP_TICK route uses tick(state, [event], client) exactly once,
            OperatorSession is updated with returned BrainState and
              TickRecord only,
            OperatorSession holds no unsafe resources (no real LLM client,
              no subprocess handle, no file descriptor, no socket, no
              host-execution callback).

brain/ui/fixtures/tui_smoke.py
  drives  : I-UI-07, I-UI-11, I-UI-12, I-UI-14
  asserts : no LLM / shell / network / file / host execution from any UI
              path (import-audit-based),
            curses wrapper contains only terminal-handling code,
            entrypoint fails closed without a usable terminal,
            aggregate operator session walks are inspectable (OBSERVED).
```

`I-UI-15` is NOT-EXERCISED and has no fixture. Its catalog Fixture column
should be empty or `(none)` consistent with existing NOT-EXERCISED rows.

The catalog's "v0 fixture roster" section should gain a sub-list for
`brain/ui/fixtures/` after the existing Phase 3.4 entries.

## 8. Module Map

The Operator TUI runtime layer adds the following modules under `brain/ui/`.

```text
brain/ui/__init__.py
  purpose : package marker; expose public UI symbols re-exported from
            brain/ui/snapshot.py, brain/ui/render.py, brain/ui/commands.py,
            brain/ui/session.py. No runtime side effects on import.
  rows    : I-UI-07 (no host execution), I-UI-15 (save/export placeholder)

brain/ui/snapshot.py
  purpose : read-only BrainSnapshot and DevelopmentSnapshot construction
            from existing public APIs and public helper functions on
            OutputHistory / WorldletHistory / ProtoBasicHistory.
  rows    : I-UI-01, I-UI-08

brain/ui/render.py
  purpose : pure terminal-agnostic renderer; accepts TuiViewModel + width
            + height; returns deterministic strings or display rows for
            panes (core state, latest tick, output / worldlet / repl
            histories, queued event, status / errors, help).
  rows    : I-UI-02, I-UI-09

brain/ui/commands.py
  purpose : OperatorCommand enumeration + bounded payload types; finite
            keyboard-to-command mapping; QUEUE_PERCEPT payload validation
            via the public PerceptEvent constructor.
  rows    : I-UI-03, I-UI-04, I-UI-13

brain/ui/session.py
  purpose : OperatorSession state container + command router; routes
            INSPECT_* / HELP / CLEAR_STATUS / QUIT / NOOP to local UI
            state changes only; routes STEP_TICK through tick(); captures
            validation and tick failures as local UI status/error.
  rows    : I-UI-05, I-UI-06, I-UI-10, I-UI-13, I-UI-14

brain/ui/tui.py
  purpose : thin curses adapter; screen init/teardown, key reading,
            key -> OperatorCommand translation, painting of renderer
            output, resize re-rendering, clean quit. No kernel semantics.
  rows    : I-UI-11

brain/ui/__main__.py
  purpose : CLI entrypoint for `python3 -m brain.ui`; either starts the
            curses wrapper or prints a helpful local message when no usable
            terminal is available. No filesystem mutation; no subprocess
            spawn.
  rows    : I-UI-07, I-UI-12

brain/ui/fixtures/__init__.py
  purpose : package marker for UI fixtures. No runtime side effects on
            import.
  rows    : none directly

brain/ui/fixtures/snapshot_view.py     (see Section 7)
brain/ui/fixtures/render_view.py       (see Section 7)
brain/ui/fixtures/command_router.py    (see Section 7)
brain/ui/fixtures/bottom_up_tick.py    (see Section 7)
brain/ui/fixtures/tui_smoke.py         (see Section 7)
```

Allowed imports for `brain/ui/`:

```text
standard library only for runtime use, including curses for tui.py
brain.io_types (PerceptEvent, ContentState, BrainState, TickRecord, ...)
brain.tick     (public tick() entrypoint, no semantic changes)
brain.development.output     (OutputHistory + public helpers)
brain.development.worldlet   (WorldletHistory + public helpers)
brain.development.repl       (ProtoBasicHistory + public helpers)
brain.invariants             (only inside fixtures, via @register)
brain.validation             (only inside fixtures, when useful)
```

Forbidden imports from `brain/ui/` (enforced by import audit + I-UI-07):

```text
brain.tlica.*       (no direct TLICA runtime mutation)
brain.llm.*         (no real LLM clients)
os.system, subprocess, socket, urllib, http, requests, asyncio.subprocess
ctypes, multiprocessing, signal-based process control
brain.tick internals beyond the public tick() entrypoint
private dataclass-field access on BrainState / developmental histories
```

## 9. Catalog Patch Mechanics

The Step 6 apply step is responsible for the following catalog patch
mechanics. Each item lists the file touched and the nature of the edit. No
runtime UI behaviour is introduced at Step 6; only catalog rows and pending
registrations.

```text
INVARIANT_CATALOG.md
  - Insert a new "### Operator TUI invariants" section after the existing
    Phase 3.4 Proto-BASIC REPL developmental invariants section and before
    the Meta / runner integrity section.
  - Add the 15 I-UI-* rows in the order listed in Section 4 of this plan.
  - Use "Engineering hypothesis (Operator TUI)" in the Lean source column.
  - Use the Owning module + Fixture columns listed in Sections 7 and 8.
  - Update the "v0 fixture roster" listing to include
      brain/ui/fixtures/snapshot_view.py     I-UI-01, I-UI-08
      brain/ui/fixtures/render_view.py       I-UI-02, I-UI-09
      brain/ui/fixtures/command_router.py    I-UI-03, I-UI-04, I-UI-06,
                                             I-UI-13
      brain/ui/fixtures/bottom_up_tick.py    I-UI-05, I-UI-10
      brain/ui/fixtures/tui_smoke.py         I-UI-07, I-UI-11, I-UI-12,
                                             I-UI-14 (OBSERVED)
    and increment the fixture total accordingly.
  - Update "Summary counts" to:
      REQUIRED         : 123
      STRUCTURAL       :  41
      NOT-EXERCISED    :   4
      DEFERRED         :  12
      OBSERVED         :   6
    and update the total tabular entries from 171 to 186.
  - Update the catalog version reference from v0.9 to v0.10.

tools/catalog.py
  - Update the EXPECTED_COUNTS table (or equivalent banner constants) to
    REQUIRED=123, STRUCTURAL=41, NOT-EXERCISED=4, DEFERRED=12, OBSERVED=6.
  - No new parser features required; the I-UI-* family uses the existing
    Markdown table schema.

brain/_catalog_ids.py
  - Regenerate via `python3 -m tools.catalog generate-ids`. The regenerated
    frozensets must include:
      EXPECTED_REQUIRED_IDS    : adds I-UI-01..07
      EXPECTED_STRUCTURAL_IDS  : adds I-UI-08..13
    OBSERVED and NOT-EXERCISED rows do not appear in the I-CAT-01 coverage
    frozensets, matching the existing convention.

brain/invariants.py
  - Add a "Operator TUI: pending row registrations" block after the existing
    Phase 3.4 pending block.
  - Pending dict (rows to register as REQUIRED / STRUCTURAL placeholders
    while Step 7/8/9 land the real fixtures):
      _OPERATOR_TUI_PENDING_ROWS : {
        "I-UI-01": "REQUIRED",  "I-UI-02": "REQUIRED",
        "I-UI-03": "REQUIRED",  "I-UI-04": "REQUIRED",
        "I-UI-05": "REQUIRED",  "I-UI-06": "REQUIRED",
        "I-UI-07": "REQUIRED",
        "I-UI-08": "STRUCTURAL","I-UI-09": "STRUCTURAL",
        "I-UI-10": "STRUCTURAL","I-UI-11": "STRUCTURAL",
        "I-UI-12": "STRUCTURAL","I-UI-13": "STRUCTURAL",
      }
  - _make_operator_tui_pending_check(row_id) raises NotImplementedError
    with the same wording shape as the existing pending-check factories;
    the runner reports those rows as registered-but-not-yet-implemented
    until Step 7 / 8 / 9 swap them out.
  - I-UI-14 (OBSERVED) and I-UI-15 (NOT-EXERCISED) are not pending entries
    here; OBSERVED rows are registered when their fixture lands, and
    NOT-EXERCISED rows do not participate in I-CAT-01 coverage.
  - No changes to coverage audit logic; the existing _audit_coverage()
    walks EXPECTED_REQUIRED_IDS / EXPECTED_STRUCTURAL_IDS, so the
    regenerated frozensets plus the new pending registrations keep
    I-CAT-01 green.

brain/ui/__init__.py
  - Create as an empty (or minimal docstring-only) package marker. Step 6
    introduces only the package shell. No runtime UI behaviour is exposed
    by import at this step; the file should not import curses, should not
    import brain.tick, and should not import brain.llm.

brain/ui/fixtures/__init__.py
  - Create as an empty (or minimal docstring-only) package marker. No
    fixture modules are imported here; brain.invariants imports them
    individually when the real fixtures land in Step 7 / 8 / 9.
```

Validation after Step 6 (per the campaign):

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Expected outcome: all banners match the new expected counts and
`python3 -m brain.invariants run` either reports the I-UI-* rows as
NotImplementedError-failed (the same shape used by other pending campaigns
before their runtime layers land) or, if Step 6 also lands the runtime
modules behind the pending mechanism, simply continues to report them as
pending until Step 7 / 8 / 9 supersede them. The campaign's preferred
posture is to land Step 6 with pending registrations and let Steps 7-9
replace them.

## 10. Implementation Order

After the review gate accepts this plan, the safe implementation order is:

```text
Step 6  Apply catalog patch
        - Edit INVARIANT_CATALOG.md (section, rows, fixture roster, counts).
        - Update tools/catalog.py expected counts.
        - Regenerate brain/_catalog_ids.py.
        - Add Operator TUI pending registrations to brain/invariants.py.
        - Create brain/ui/__init__.py and brain/ui/fixtures/__init__.py as
          empty package markers.
        - Validate: tools.catalog counts, tools.catalog generate-ids,
          tools.catalog counts.
        - No runtime UI behaviour.

Step 7  Read-only snapshots and pure renderer
        - Land brain/ui/snapshot.py, brain/ui/render.py.
        - Land brain/ui/fixtures/snapshot_view.py,
          brain/ui/fixtures/render_view.py.
        - Replace pending registrations for I-UI-01, I-UI-02, I-UI-08,
          I-UI-09 with real fixture-backed checks.
        - Run targeted invariants and the full gate.

Step 8  Operator command router and bottom-up event path
        - Land brain/ui/commands.py, brain/ui/session.py.
        - Land brain/ui/fixtures/command_router.py,
          brain/ui/fixtures/bottom_up_tick.py.
        - Replace pending registrations for I-UI-03, I-UI-04, I-UI-05,
          I-UI-06, I-UI-10, I-UI-13 with real fixture-backed checks.
        - Run targeted invariants and the full gate.

Step 9  Curses-style wrapper and CLI entrypoint
        - Land brain/ui/tui.py, brain/ui/__main__.py.
        - Land brain/ui/fixtures/tui_smoke.py covering I-UI-07, I-UI-11,
          I-UI-12, I-UI-14 (OBSERVED).
        - Replace pending registrations for I-UI-07, I-UI-11, I-UI-12 with
          real fixture-backed checks. Register I-UI-14 as OBSERVED. Leave
          I-UI-15 NOT-EXERCISED.
        - Run targeted invariants and the full gate.

Step 10 Full gate.
Step 11 Operator TUI audit (PASS / PASS WITH PATCHES / BLOCKED).
```

## 11. Open Decisions

The following items are explicitly called out for the Step 5 review gate. None
of them blocks drafting this plan; each is a small choice that the reviewer
should confirm before Step 6 is applied.

```text
D1  Catalog version bump on Step 6: v0.9 -> v0.10.
    Default: yes, because a row family is added and expected counts move.
    Alternative: keep v0.9 and treat the UI rows as a v0.9 addendum.
    Recommended: v0.10.

D2  Renderer determinism scope.
    Default: identical TuiViewModel + width + height -> identical output
    (strings or tuples of strings).
    Alternative: also assert identical output across snapshot identity
    rather than equality. The default is sufficient; identity-level
    equality would over-constrain the implementation.

D3  Import audit surface for I-UI-07.
    Default: the existing tools/import_audit.py walks brain/ui/ and
    rejects forbidden imports (subprocess, socket, urllib, http, requests,
    brain.llm, brain.tlica beyond public surfaces).
    Alternative: a dedicated UI-only audit module. The default is simpler
    and reuses existing coverage.

D4  Snapshot field representation for Fractions.
    Default: render exact Fractions as canonical strings on snapshot
    display fields, keep raw Fraction values only in non-display
    auxiliary fields (if any).
    Alternative: keep raw Fractions everywhere on the snapshot and
    convert at the renderer. The default is preferred so the snapshot
    itself is renderer-agnostic and import-of-display-fields stays simple.

D5  Aggregate session walk (I-UI-14) trigger.
    Default: a fixture-built scripted sequence of OperatorCommand values
    over a deterministic injected tick client; records summary counters
    only.
    Alternative: skip the OBSERVED row entirely. The default mirrors the
    Phase 3.3 / 3.4 aggregate inspection convention and is recommended.

D6  Save / export placeholder (I-UI-15).
    Default: include as NOT-EXERCISED so any future filesystem mutation
    surface must register coverage explicitly.
    Alternative: omit the row and rely on prose-only policy. The default
    is preferred because it makes future drift visible in the count
    banner.

D7  Pending-registration strategy in Step 6.
    Default: register I-UI-01..07 (REQUIRED) and I-UI-08..13 (STRUCTURAL)
    as pending checks that raise NotImplementedError until Step 7/8/9
    supersede them. OBSERVED and NOT-EXERCISED rows are not pending.
    Alternative: land catalog rows but skip pending registrations. The
    default is preferred because it keeps I-CAT-01 coverage explicit and
    matches the precedent used by Phase 3.3 and Phase 3.4.

D8  Number of REQUIRED rows.
    Default: 7 (I-UI-01..07).
    Alternative: collapse I-UI-05 and I-UI-06 into a single STEP_TICK row.
    The default is preferred because failure-isolation (I-UI-06) is a
    distinct enforceable property from the tick() route property
    (I-UI-05).
```

The reviewer may accept the defaults wholesale or amend individual items.
Any amendment must be reflected in counts, fixture roster, module map, and
patch mechanics before Step 6 is applied.

## 12. Stop Conditions

Per `CURRENT_CAMPAIGN.md` Step 5 (review gate), do not proceed to Step 6
unless this plan is coherent and no open decision blocks implementation.

Additionally, halt and request user judgment if any of the following becomes
true during plan review or Step 6 application:

```text
S1  A proposed I-UI-* row's plain-language reading implies a cognitive
    promotion (the UI "thinks", "decides", "understands", "talks", or
    "learns").
S2  A proposed fixture would require importing brain/tlica/* or
    brain/llm/* outside read-only public surfaces.
S3  A proposed implementation step needs to change tick() semantics, the
    scenario schema, the trace schema, or any file under brain/tlica/ or
    lean_reference/.
S4  Updating expected counts breaks an unrelated catalog property (for
    example, the I-CAT-01 audit reports new uncovered rows in another
    family).
S5  Any UI surface would require a real LLM call, real subprocess, real
    network I/O, real shell execution, or filesystem mutation outside an
    explicit reviewed save/export policy (none authorized in this
    campaign).
S6  The patch would require renumbering or relocating an existing catalog
    row.
S7  The patch would require introducing a non-standard dependency.
S8  The Phase 3.4 audit verdict is no longer PASS, or the full gate is no
    longer green at the time Step 6 starts.
```

Each stop condition is a user-judgment point, not a unilateral relaxation.

## 13. Validation

Validation for this planning step (Step 4) is:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

The counts banner must still report the v0.9 baseline because this plan is
documentation only and does not touch the catalog or the runner.

After Step 6 applies the patch, the campaign-defined validation is:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

After Step 9 lands the UI runtime layer, the full gate is:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

## 14. Final Decision

This plan is coherent and ready for the Step 5 review gate. The defaults in
Section 11 carry the plan into Step 6 without further branching.

Next artifact: none in this step. The next campaign action is the Step 5
review gate, followed (on acceptance) by Step 6 applying the catalog patch.
