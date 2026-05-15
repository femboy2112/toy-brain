# OPERATOR_TUI_AGENT_LAYOUT_CATALOG_PATCH_PLAN.md

Step 4 catalog patch plan for the Operator TUI Agent-Style Layout
campaign (`CURRENT_CAMPAIGN.md`). This document turns the Step 3
corrigenda's locked contracts into a concrete catalog patch
specification ready for Step 6 to apply.

It is a **planning artifact only**. It does not:

```text
modify runtime code
add or amend catalog rows
create fixtures
change tick() semantics
change developmental histories
write traces or scenarios
add dependencies
authorize host execution, shell, network, or LLM calls
```

Baseline at the time of writing (preflight green):

```text
Catalog: v0.10
Counts: 123 REQUIRED / 41 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 6 OBSERVED
Operator TUI campaign: PASS
Operator TUI live input patch: PASS and merged (commit 084f545)
Synthesis (Step 1): present (commit 0a9d3d4)
Kickoff (Step 2): present (commit 97cb503)
Corrigenda (Step 3): present (commit 45532e0)
Full gate (bash tools/check_all.sh): green (170 rows checked)
Entrypoint: python3 -m brain.ui
```

---

## 1. Purpose

The synthesis (Step 1) established the UX deficit. The kickoff
(Step 2) locked the contracts (`AgentLayout`, `PaneSpec`,
`PaneRenderResult`, `BottomComposer`, `ComposerState`,
`ComposerAction`, `LocalCommandLine`, `OperatorTranscript`,
`TranscriptEntry`, `AgentTuiViewModel`, responsive pane sizing, typed
command flow, keyboard flow, scrollback / log discipline,
non-interactive fixture strategy). The corrigenda (Step 3) resolved
the seven open decisions (A–G), rechecked every campaign boundary,
and locked the proposed `I-UI-16..I-UI-23` row family with their
statuses.

This catalog patch plan does five things:

```text
1. Quotes the corrigenda's row table (section 9) verbatim so Step 6
   can apply rows without re-deriving them.
2. Quotes the corrigenda's open-decision rulings (section 10)
   verbatim so Steps 6-10 cannot drift.
3. Specifies the catalog patch mechanics: catalog banner update,
   summary-count update, tools.catalog expected-count update,
   tools.catalog generate-ids invocation order, brain/_catalog_ids.py
   regeneration, pending-registration list.
4. Names the strict implementation order: Step 6 catalog → Step 7
   layout / renderer → Step 8 composer / parser → Step 9 transcript
   → Step 10 wrapper switch + README.
5. Restates the stop conditions and the unchanged-rows list verbatim
   so Step 5 has a single document to review.
```

Every contract below is engineering-hypothesis material. None of it
modifies the kernel, the trace seam, developmental histories,
scenarios, or the Lean reference. No resolution **loosens** a
kickoff contract or weakens an existing `I-UI-*` row.

---

## 2. Quoted row table from corrigenda section 9

The following row table is quoted verbatim from
`OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md` section 9 ("New I-UI-* row
family for Step 4"). Step 6 applies it without modification.

> Row table (proposed for catalog v0.11):
>
> ```text
> ID         Status      Drives / Contract
> ---------- ----------- ------------------------------------------------
> I-UI-16    REQUIRED    AgentLayout exposes persistent named panes plus
>                        bottom composer. (kickoff section 2, 11)
>                        Owning module: brain/ui/layout.py
>                        Fixture: brain/ui/fixtures/agent_layout.py
>
> I-UI-17    REQUIRED    BottomComposer edit model supports type /
>                        backspace / enter / history deterministically.
>                        (kickoff section 5-7)
>                        Owning module: brain/ui/composer.py
>                        Fixture: brain/ui/fixtures/composer_input.py
>
> I-UI-18    REQUIRED    LocalCommandLine parser is finite, typed, and
>                        maps only to approved OperatorCommand /
>                        QueuePerceptPayload routes. (kickoff section 8,
>                        this corrigenda section 7-8)
>                        Owning module: brain/ui/command_line.py
>                        Fixture: brain/ui/fixtures/composer_input.py
>
> I-UI-19    REQUIRED    OperatorTranscript records UI events
>                        copy-on-write and remains local UI state only.
>                        (kickoff section 9, this corrigenda section 5)
>                        Owning module: brain/ui/transcript.py
>                        Fixture: brain/ui/fixtures/transcript_log.py
>
> I-UI-20    STRUCTURAL  AgentLayout / PaneSpec / AgentTuiViewModel are
>                        terminal-agnostic immutable contracts. (kickoff
>                        sections 2, 3, 10)
>                        Owning module: brain/ui/layout.py +
>                                       brain/ui/render.py
>                        Fixture: brain/ui/fixtures/agent_layout.py
>
> I-UI-21    STRUCTURAL  Curses wrapper delegates input to composer /
>                        router and does not mutate kernel state
>                        directly. (kickoff section 12-13)
>                        Owning module: brain/ui/tui.py
>                        Fixture: brain/ui/fixtures/agent_tui_smoke.py
>                        (plus continued reliance on I-UI-11)
>
> I-UI-22    STRUCTURAL  Responsive pane geometry is deterministic and
>                        preserves a visible bottom composer on small
>                        terminals. (kickoff section 11, this corrigenda
>                        section 4)
>                        Owning module: brain/ui/layout.py
>                        Fixture: brain/ui/fixtures/agent_layout.py
>
> I-UI-23    OBSERVED    Scripted agent-style interaction walk is
>                        inspectable and non-gating. (kickoff section 15)
>                        Owning module: brain/ui/tui.py +
>                                       brain/ui/session.py
>                        Fixture: brain/ui/fixtures/agent_tui_smoke.py
> ```
>
> Status rationale (per row):
>
> ```text
> I-UI-16 REQUIRED — the layout is the campaign's primary structural
>         promise. Without persistent panes plus composer the campaign
>         has not shipped. Fixture asserts pane presence and ordering.
>
> I-UI-17 REQUIRED — the composer is the campaign's primary ergonomic
>         promise. The fixture exercises every ComposerAction including
>         edge cases (empty submit, history wrap, non-printable
>         INSERT_CHAR rejection).
>
> I-UI-18 REQUIRED — the parser is the safety surface. Anything the
>         operator types is constrained by this row. Fixture is
>         table-driven over the verb enumeration.
>
> I-UI-19 REQUIRED — bounding the transcript is the only thing that
>         keeps the UI from leaking memory or violating I-UI-13. The
>         row asserts both the bound and the copy-on-write contract.
>
> I-UI-20 STRUCTURAL — the contracts are enforced at construction time
>         (frozen dataclasses + __post_init__ checks). No per-tick
>         assertion is needed beyond the fixtures driving the rows that
>         depend on them (I-UI-16 and I-UI-22).
>
> I-UI-21 STRUCTURAL — the wrapper-delegation property is a structural
>         invariant of the codebase (the wrapper has no kernel imports,
>         composer/parser handle input). I-UI-11 already covers the
>         import audit; I-UI-21 captures the delegation pattern itself
>         and is exercised by the OBSERVED smoke walk plus the wrapper's
>         construction-time delegation table.
>
> I-UI-22 STRUCTURAL — derives from I-UI-16's fixture sweep. The
>         geometry is a pure function of (width, height); the fixture
>         sweeps a deterministic grid and asserts the small-terminal
>         preservation property. STRUCTURAL because it is a property of
>         the AgentLayout constructor, not a runtime tick-time check.
>
> I-UI-23 OBSERVED — like I-UI-14 today, this is an inspectable walk
>         that helps operators verify the agent surface end-to-end
>         without being a correctness gate. It runs under the full gate
>         but does not fail the runner.
> ```
>
> Projected catalog impact (from v0.10):
>
> ```text
> REQUIRED       123 -> 127   (+4: I-UI-16, I-UI-17, I-UI-18, I-UI-19)
> STRUCTURAL      41 -> 44    (+3: I-UI-20, I-UI-21, I-UI-22)
> NOT-EXERCISED    4 -> 4     (+0)
> DEFERRED        12 -> 12    (+0)
> OBSERVED         6 ->  7    (+1: I-UI-23)
> Total rows     186 -> 194
> ```
>
> This matches the kickoff section 16 projection and the campaign's
> Step 4 recommended-row table. Step 4 must restate the table verbatim;
> this corrigenda is the canonical mapping.

End of corrigenda section 9 quote.

---

## 3. Quoted open-decision rulings from corrigenda section 10

The following rulings are quoted verbatim from
`OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md` section 10 ("Open decisions
A–G — binding rulings"). Step 6 carries them into row text, Step 7–10
implement them, and the Step 12 audit checks they were honored.

> ### A. ComposerState.status_line field
>
> Kickoff recommendation: keep the field.
>
> Ruling: **keep the field**. The composer pane shows the most recent
> local-cmd status without re-reading `session.status_message` mid-frame.
> This decouples the composer's meta row from the session's status pane
> and lets the composer surface parse-time messages (for example, "empty
> composer submission") that never reach `session.set_error` because they
> are not session-level errors.
>
> Implementation note for Step 8:
>
> ```text
> ComposerState.status_line is set ONLY by:
>   - the SUBMIT action when buffer.strip() == "" (sets "empty composer
>     submission" and returns the unchanged buffer);
>   - the wrapper, after a successful parse, by writing session.status_message
>     into the next ComposerState via apply(state.with_status(...)).
> The composer pane renderer reads ComposerState.status_line for the meta
> row's third field when session.status_message is empty; otherwise it
> prefers session.status_message. The "prefer session" precedence keeps
> the existing I-UI-13 status-pane semantics intact.
> ```
>
> Rationale: the field is bounded printable text (kickoff section 6),
> costs one tuple slot, and prevents the parser from reaching across
> into `OperatorSession.set_status`/`set_error` for parser-internal
> messages. No safety row is weakened.
>
> ### B. HISTORY_PREV / HISTORY_NEXT and the live curses /queue prompt
>
> Kickoff recommendation: no.
>
> Ruling: **no**. HISTORY_PREV / HISTORY_NEXT walk the composer's own
> submission ring. The live curses percept prompt (opened by the `n`
> key, from the live-input patch) is a separate, single-shot bounded
> prompt that does not share history with the composer.
>
> Rationale:
>
> ```text
> 1. The live curses prompt is a two-field dialog over (content_id, text)
>    with bounded-printable inputs. It has no notion of "previous
>    submission".
> 2. Sharing history would require the prompt to read the composer's
>    ring (cross-module coupling) and would invite the operator to
>    recall a "/queue beta hello" line into the prompt's content_id
>    field, which would fail validation.
> 3. The composer is the primary surface for /queue (this corrigenda
>    section 7). The `n` key remains as a wrapper concession for users
>    who prefer the dialog; new fixtures cover the composer path, not
>    the dialog path.
> ```
>
> Implementation note: the wrapper continues to map `n` to the existing
> percept-prompt factory wired in commit c4b8c07. No history field is
> threaded into the prompt.
>
> ### C. Should /clear also clear the composer buffer?
>
> Kickoff recommendation: no.
>
> Ruling: **no**. `/clear` maps to `Command(CLEAR_STATUS)` and clears
> only the session's status/error fields. The composer buffer survives
> across `/clear` so the operator does not lose typed input by clearing
> status.
>
> The explicit composer-clear path is `CLEAR_BUFFER` (ComposerAction)
> which is bound to `^U` and `^C` (kickoff section 13). The operator who
> wants to clear both submits `/clear` and then types `^U` (or vice
> versa).
>
> Implementation note for Step 8:
>
> ```text
> Verb dispatch table (Step 8):
>   /clear -> Command(OperatorCommand.CLEAR_STATUS)
>   ^U / ^C (when composer has focus) -> ComposerAction.CLEAR_BUFFER
>
> These are independent. /clear never returns a ComposerSubmission with
> an empty buffer; it returns a parsed Command, and the wrapper adopts
> the new ComposerState (with buffer="", because SUBMIT always returns
> buffer="") only because Enter was pressed.
>
> Note: SUBMIT does clear the buffer by design — that is the existing
> ComposerState transition for SUBMIT (kickoff section 7). After SUBMIT,
> the wrapper passes "/clear" to the parser, gets Command(CLEAR_STATUS),
> and dispatches it. The buffer is empty after SUBMIT, which is
> consistent with "buffer survives /clear" because /clear only operates
> on session fields; the empty buffer is a side effect of pressing Enter.
> ```
>
> Documentation note: /help must explicitly say "/clear clears status,
> ^U clears the composer".
>
> ### D. Transcript persistence across `python3 -m brain.ui` invocations
>
> Kickoff recommendation: no.
>
> Ruling: **no**. The transcript is process-local and dies with the
> curses wrapper.
>
> Rationale:
>
> ```text
> 1. Persistence requires filesystem writes, which kickoff section 16
>    explicitly excludes.
> 2. Persistence would invite confusion with the trace seam (which is a
>    kernel-level surface, not a UI surface).
> 3. Persistence would invite cross-session "agent memory" semantics that
>    are out of scope for the campaign (and would smell like Phase 3.5
>    without going through Phase 3.5).
> 4. The OperatorSession itself is also process-local under the existing
>    I-UI-10 row; transcript persistence would create an asymmetry.
> ```
>
> Implementation note: no read/write of `~/.brain_tui_history` or
> similar. The transcript is built fresh in every wrapper startup
> (`OperatorTranscript.empty()`).
>
> ### E. Retire the existing TuiViewModel now or at Step 10?
>
> Kickoff recommendation: keep both during the implementation phase.
> Retire at Step 10.
>
> Ruling: **keep both through Step 9; retire at Step 10**. The legacy
> `TuiViewModel` remains importable for the duration of Steps 6–9 so
> existing fixtures (`brain/ui/fixtures/render_view.py`,
> `brain/ui/fixtures/snapshot_view.py`, etc.) do not have to be rewritten
> in lock-step with the new layout module.
>
> Retirement protocol at Step 10:
>
> ```text
> 1. Move existing TuiViewModel fixtures that test render() with the
>    legacy view model onto AgentTuiViewModel (a thin adapter is
>    acceptable in fixtures).
> 2. Remove the legacy TuiViewModel record from brain/ui/render.py.
> 3. The renderer's public signature becomes
>    render(view: AgentTuiViewModel) -> tuple[str, ...].
> 4. The "active_view" / "queue_summary" / "status_message" /
>    "error_message" / "keyboard_help" / "width" / "height" fields
>    continue to exist on AgentTuiViewModel (kickoff section 10), so
>    nothing observable to the renderer changes.
> ```
>
> This keeps Steps 6–9 from triggering a wrapper-wide refactor and
> isolates the wrapper-only switch to Step 10.
>
> ### F. Should the agent-style entrypoint share `python3 -m brain.ui`?
>
> Kickoff recommendation: yes, share.
>
> Ruling: **share `python3 -m brain.ui`**. The wrapper picks the layout
> at startup. The campaign does not register a new submodule
> (no `python3 -m brain.ui.agent` or similar).
>
> Rationale:
>
> ```text
> 1. The campaign is a UX upgrade, not a parallel UI. Two entrypoints
>    would force users to remember which is "the new one".
> 2. The legacy renderer remains importable during Steps 6-9 (open
>    decision E), but the wrapper switches to the agent layout at
>    Step 10. After Step 10, the only callable surface is the
>    layout-aware path.
> 3. README is updated at Step 10 to document the new interface in
>    place; no separate "agent UI" section is added.
> ```
>
> Implementation note: `brain/ui/__main__.py` remains the single entry
> file. Its `--check-terminal` / `--print-once` flags continue to work,
> with `--print-once` switching to render an `AgentTuiViewModel` of the
> default operator view at Step 10.
>
> ### G. Does any new module require its own import-audit row, or does
>        I-UI-07 cover them transitively?
>
> Kickoff recommendation: I-UI-07 covers `brain/ui/*.py`; extend the
> existing fixture.
>
> Ruling: **I-UI-07 covers the new modules**; the fixture is extended.
> No new import-audit row is added.
>
> Rationale:
>
> ```text
> 1. I-UI-07's owning module is brain.ui.tui (the curses wrapper) and
>    its fixture is brain/ui/fixtures/tui_smoke.py. The fixture walks
>    the brain/ui package's modules and asserts the import allowlist.
> 2. Adding a per-module row would inflate the catalog without adding
>    coverage; the existing audit is already package-scoped.
> 3. The fixture extension at Step 6 / Step 8 adds the four new modules
>    (layout.py, composer.py, command_line.py, transcript.py) to the
>    audited set. The audit allowlist remains:
>        typing-only imports
>        brain.ui.commands (where the closed enumeration lives)
>        brain.ui.constants (where the bounds live)
>        brain.ui.render constants (MIN_WIDTH / MIN_HEIGHT)
>        brain.io_types.PerceptEvent (for QueuePerceptPayload construction)
>    No new module imports curses, kernel, LLM, shell, network, or file
>    surfaces.
> 4. The pending registration list at Step 6 lists fixture-extension
>    work for I-UI-07 alongside the new I-UI-16..I-UI-23 registrations.
> ```
>
> Implementation note for Step 6 / Step 8: when the fixture's audited
> module list expands, the catalog row's "Fixture" cell stays
> "tui_smoke.py" because that is the fixture that drives the audit.

End of corrigenda section 10 quote.

---

## 4. Unchanged existing I-UI-* rows

The Step 6 patch leaves every existing `I-UI-*` row at its current
status, owning module, and fixture. The campaign **extends**; it does
not modify in place. The corrigenda section 9 closing block is quoted
verbatim:

> Existing I-UI-* rows (must be restated as **unchanged** in Step 4):
>
> ```text
> I-UI-01  REQUIRED    snapshot_view  unchanged
> I-UI-02  REQUIRED    render_view    unchanged
> I-UI-03  REQUIRED    command_router unchanged
> I-UI-04  REQUIRED    command_router unchanged
> I-UI-05  REQUIRED    command_router unchanged
> I-UI-06  REQUIRED    command_router unchanged
> I-UI-07  REQUIRED    tui_smoke      unchanged (fixture extended at
>                                     Step 6 to cover new modules)
> I-UI-08  STRUCTURAL  snapshot_view  unchanged
> I-UI-09  STRUCTURAL  render_view    unchanged
> I-UI-10  REQUIRED    command_router unchanged
> I-UI-11  STRUCTURAL  tui_smoke      unchanged
> I-UI-12  STRUCTURAL  tui_smoke      unchanged
> I-UI-13  STRUCTURAL  command_router unchanged
> I-UI-14  OBSERVED    tui_smoke      unchanged
> I-UI-15  NOT-EX'D    (none)         unchanged
> ```
>
> The corrigenda explicitly affirms: no existing I-UI-* row is weakened,
> amended, or retired. The campaign extends; it does not modify in
> place.

Step 6 emits no row-text edits against I-UI-01..I-UI-15. The
fixture-level extension for I-UI-07 (adding the new modules to the
audited set) is implementation work for Step 8 (where `composer.py`
and `command_line.py` come into existence) and Step 10 (where
`layout.py` and `transcript.py` are already in place from Steps 7 / 9
but the wrapper finally imports them through the agent layout path).

---

## 5. Catalog patch mechanics for Step 6

This section names the **exact mechanics** Step 6 must perform. No
runtime code is touched in Step 6; only the catalog spec and the
generated identifier file change.

### 5.1 Allowed files

Per `CURRENT_CAMPAIGN.md` Step 6, the only files Step 6 may modify:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional package markers, only if Step 6 chooses to land empty stubs
to avoid Step 7+ scaffolding work (the plan does **not** require
this; the recommended path is to defer module creation to Steps 7-10
so each step lands its own module alongside its fixture):

```text
brain/ui/layout.py
brain/ui/composer.py
brain/ui/command_line.py
brain/ui/transcript.py
brain/ui/fixtures/__init__.py
```

The recommendation is: **do not create the optional package markers
in Step 6**. Step 6 stays a pure catalog patch. The `brain/ui/`
package already exists with `__init__.py`, and the four new modules
land alongside their fixtures in Steps 7–9 (and the wrapper integration
at Step 10). This keeps Step 6 small enough to review at the gate.

### 5.2 Catalog banner update

`INVARIANT_CATALOG.md` carries a chronological version banner block at
the top of the file. v0.10 is the current entry. v0.11 is appended
**above** the v0.10 banner using the same format:

```text
> **Catalog version:** v0.11. Patches over v0.10 (Operator TUI
> Agent-Style Layout catalog expansion): +4 REQUIRED rows, +3
> STRUCTURAL rows, +1 OBSERVED row. Adds the I-UI-16..I-UI-23 row
> family for an agent-style operator terminal: persistent named panes
> plus bottom composer (`AgentLayout` / `PaneSpec`), a deterministic
> `BottomComposer` edit model, a finite typed `LocalCommandLine`
> parser that maps only to approved `OperatorCommand` /
> `QueuePerceptPayload` routes, a copy-on-write local `OperatorTranscript`,
> a terminal-agnostic `AgentTuiViewModel` contract, a curses-wrapper
> delegation property, deterministic small-terminal pane geometry,
> and a scripted agent-style interaction OBSERVED walk. These rows
> are engineering hypotheses, not Lean theorem claims, and they cover
> the operator-facing UI surface only — they do not authorize Phase
> 3.5 Expression + ReadabilityPredictor, social/language, Mode B,
> real LLM, real host execution, or any new cognitive layer.
```

The v0.10 banner remains in place; the v0.11 banner is added above it
in the chronological list. No previous banner is rewritten.

### 5.3 Summary-counts update

`INVARIANT_CATALOG.md` section "Summary counts" carries five bullet
lines plus a "Total tabular entries" trailer. Step 6 updates them to:

```text
- **REQUIRED v0.11 invariants:** 127
- **STRUCTURAL (constructor- or type-enforced, not per-tick asserted):** 44
- **NOT-EXERCISED row-level:** 4 (plus 5 modules covered at module-level
  in "Modules with no v0-required invariants")
- **DEFERRED row-level:** 12 (plus inherited deferrals table)
- **OBSERVED row-level:** 7 (recorded in run summary, not gating)
```

Trailer:

```text
Total tabular entries: 194. v0.11 success is gated by the 127
REQUIRED rows + 44 STRUCTURAL rows (OBSERVED rows are logged but do
not gate; the I-CAT-01 runner audit gates separately at startup).
```

The "REQUIRED v0.10" label changes to "REQUIRED v0.11" to track the
banner; the older banner block above it preserves its v0.10 label.

### 5.4 Row insertion locations

The eight new rows land in the existing `brain/ui/*` section of
`INVARIANT_CATALOG.md` immediately after the I-UI-15 entry,
preserving numerical order. The relevant sub-sections inside the
catalog are:

```text
brain/ui/layout.py        (new module; row block introduced for it)
  I-UI-16 REQUIRED
  I-UI-20 STRUCTURAL
  I-UI-22 STRUCTURAL

brain/ui/composer.py      (new module; row block introduced for it)
  I-UI-17 REQUIRED

brain/ui/command_line.py  (new module; row block introduced for it)
  I-UI-18 REQUIRED

brain/ui/transcript.py    (new module; row block introduced for it)
  I-UI-19 REQUIRED

brain/ui/tui.py           (existing module; rows appended to its block)
  I-UI-21 STRUCTURAL
  I-UI-23 OBSERVED
```

The module-header lines (`### \`brain/ui/<module>.py\` — ...`) are
added for the four new modules even though the module files do not
yet exist. This is consistent with the v0.7-v0.10 precedent where
catalog rows for a module are landed before the module itself is
written. The `tools/catalog.py` parser tolerates module headers whose
target file does not yet exist; the I-CAT-01 audit only checks that
every REQUIRED / STRUCTURAL row has a registered check, not that the
owning module file is on disk.

### 5.5 `tools/catalog.py` expected-counts update

`tools/catalog.py` carries a `EXPECTED_COUNTS` dict. Step 6 updates
it as follows:

```python
# v0.11 expected counts — bumped by the Operator TUI Agent-Style
# Layout catalog patch (I-UI-16..23): +4 REQUIRED, +3 STRUCTURAL,
# +1 OBSERVED.
EXPECTED_COUNTS: dict[str, int] = {
    "REQUIRED": 127,
    "STRUCTURAL": 44,
    "NOT-EXERCISED": 4,
    "DEFERRED": 12,
    "OBSERVED": 7,
}
```

The v0.10 comment is replaced. The dict shape is unchanged.

### 5.6 `brain/_catalog_ids.py` regeneration

`brain/_catalog_ids.py` is generated by
`python3 -m tools.catalog generate-ids`. After updating
`INVARIANT_CATALOG.md` and `tools/catalog.py`, Step 6 runs:

```bash
python3 -m tools.catalog generate-ids
```

This rewrites `brain/_catalog_ids.py` to include the eight new IDs in
numerical order. The expected diff inserts `"I-UI-16"`, `"I-UI-17"`,
... `"I-UI-23"` in the appropriate alphabetical positions in the
generated tuples / lookup tables, with no manual edits required.

### 5.7 Pending registration plan in `brain/invariants.py`

REQUIRED and STRUCTURAL rows must have registered checks for the
I-CAT-01 catalog↔registry coverage audit to remain green. The rows
introduced in Step 6 cannot yet be checked because their owning
modules and fixtures do not exist until Steps 7–10.

`brain/invariants.py` carries a "pending registrations" mechanism
that records REQUIRED / STRUCTURAL row IDs whose checks are
deliberately deferred to a later step in the active campaign. Step 6
extends the pending registrations list with the seven non-OBSERVED
new rows:

```text
I-UI-16  REQUIRED    pending — driven by brain.ui.fixtures.agent_layout
                     (Step 7).
I-UI-17  REQUIRED    pending — driven by brain.ui.fixtures.composer_input
                     (Step 8).
I-UI-18  REQUIRED    pending — driven by brain.ui.fixtures.composer_input
                     (Step 8).
I-UI-19  REQUIRED    pending — driven by brain.ui.fixtures.transcript_log
                     (Step 9).
I-UI-20  STRUCTURAL  pending — driven by brain.ui.fixtures.agent_layout
                     (Step 7).
I-UI-21  STRUCTURAL  pending — driven by brain.ui.fixtures.agent_tui_smoke
                     (Step 10).
I-UI-22  STRUCTURAL  pending — driven by brain.ui.fixtures.agent_layout
                     (Step 7).
```

I-UI-23 OBSERVED is not on the pending list (OBSERVED rows are not
gated by I-CAT-01); it is registered as an OBSERVED row alongside
I-UI-14 when its fixture lands at Step 10.

The pending list shrinks step by step:

```text
After Step 6:  pending = {I-UI-16, I-UI-17, I-UI-18, I-UI-19,
                          I-UI-20, I-UI-21, I-UI-22}
After Step 7:  pending = {I-UI-17, I-UI-18, I-UI-19, I-UI-21}
After Step 8:  pending = {I-UI-19, I-UI-21}
After Step 9:  pending = {I-UI-21}
After Step 10: pending = {}
```

If `tools.catalog counts` reports a row count mismatch or the
runner's I-CAT-01 audit complains, Step 6 stops and reports rather
than weakening the pending list.

### 5.8 Validation commands for Step 6

After applying the catalog edits, Step 6 runs in order:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Expected output of the first `counts` invocation (banner vs actual vs
expected): banner 127/44/4/12/7, actual 127/44/4/12/7, expected
127/44/4/12/7, all `ok`. If the first invocation fails because the
generated IDs file is stale, that is acceptable — `generate-ids` is
run next and the second `counts` invocation must pass cleanly.

After both `counts` invocations pass:

```bash
python3 -m brain.invariants run
```

The runner reports the seven pending rows as pending (with the
expected fixture targets) and does not fail. OBSERVED rows
I-UI-14 remains green; I-UI-23 has no fixture yet and is not yet
registered, so the OBSERVED count in the runner is 6 (unchanged
since the OBSERVED registration lands with the fixture at Step 10).

The campaign-level full gate `bash tools/check_all.sh` is **not** run
at Step 6; that gate is reserved for Step 11. Step 6's gate is the
pair of `tools.catalog counts` invocations plus the runner.

### 5.9 Commit message convention for Step 6

Per the campaign's commit history (commits 0a9d3d4, 97cb503,
45532e0), Step 6's commit message uses the form:

```text
operator-tui(agent-layout step6): apply v0.11 catalog patch
```

Files staged are exactly the four allowed files above (no optional
package markers). Push to `main` after the commit per the established
push-after-each-step rule.

---

## 6. Strict implementation order

The campaign's Steps 6 through 10 must run in **strict order**. Each
step depends on the artifacts of the previous step; out-of-order
execution will trip the I-CAT-01 audit or violate the pending-list
discipline of section 5.7.

```text
Step 6  apply catalog patch.
        - Allowed files: INVARIANT_CATALOG.md, tools/catalog.py,
          brain/_catalog_ids.py, brain/invariants.py.
        - Rows added: I-UI-16..I-UI-23.
        - Pending registrations open for I-UI-16..I-UI-22.
        - I-UI-23 (OBSERVED) waits for Step 10's fixture.
        - No runtime modules created.
        - Gate: python3 -m tools.catalog counts (twice);
                python3 -m brain.invariants run (pending list reported).

Step 7  layout module + pure renderer upgrade.
        - Allowed files: brain/ui/layout.py (new), brain/ui/render.py,
          brain/ui/fixtures/agent_layout.py (new), brain/invariants.py.
        - Drives rows: I-UI-16 (REQUIRED), I-UI-20 (STRUCTURAL),
          I-UI-22 (STRUCTURAL).
        - Implements AgentLayout, PaneSpec, PaneRenderResult,
          AgentTuiViewModel (legacy TuiViewModel kept importable per
          ruling E), responsive geometry with small-terminal collapse
          per corrigenda section 4.
        - Removes those three rows from the pending list.
        - Gate: python3 -m brain.invariants run --id I-UI-16,
                                                  --id I-UI-20,
                                                  --id I-UI-22;
                python3 -m brain.invariants run (pending list shrinks).

Step 8  bottom composer + typed local command parser.
        - Allowed files: brain/ui/composer.py (new),
          brain/ui/command_line.py (new), brain/ui/commands.py,
          brain/ui/session.py, brain/ui/fixtures/composer_input.py
          (new), brain/invariants.py.
        - Drives rows: I-UI-17 (REQUIRED), I-UI-18 (REQUIRED).
        - Implements BottomComposer, ComposerState, ComposerAction,
          LocalCommandLine, the verb dispatch table from ruling A and
          ruling C, and the rejection paths from corrigenda section 7.
        - I-UI-07 fixture (tui_smoke.py) is extended at this step to
          audit composer.py and command_line.py (per ruling G).
        - Removes those two rows from the pending list.
        - Gate: python3 -m brain.invariants run --id I-UI-17,
                                                  --id I-UI-18;
                python3 -m brain.invariants run --id I-UI-07
                (extended audit still green).

Step 9  transcript + session integration.
        - Allowed files: brain/ui/transcript.py (new),
          brain/ui/session.py, brain/ui/render.py,
          brain/ui/fixtures/transcript_log.py (new),
          brain/invariants.py.
        - Drives row: I-UI-19 (REQUIRED).
        - Implements OperatorTranscript, TranscriptEntry,
          TranscriptKind, copy-on-write append with the
          TRANSCRIPT_MAX_ENTRIES = 64 bound from corrigenda section 5.
        - Transcript is local UI state only; no developmental history
          touched (ruling D + corrigenda section 5).
        - Removes that row from the pending list.
        - Gate: python3 -m brain.invariants run --id I-UI-19;
                python3 -m brain.invariants run --id I-UI-13
                (bounded-printable status text still green).

Step 10 curses wrapper integration + README sync.
        - Allowed files: brain/ui/tui.py, brain/ui/__main__.py,
          brain/ui/fixtures/agent_tui_smoke.py (new), README.md,
          brain/invariants.py.
        - Drives rows: I-UI-21 (STRUCTURAL), I-UI-23 (OBSERVED).
        - Wires the composer / parser / transcript / layout into the
          wrapper; switches the renderer to AgentTuiViewModel; retires
          the legacy TuiViewModel per ruling E.
        - Extends I-UI-07's fixture audit to include layout.py and
          transcript.py (per ruling G).
        - I-UI-07 audit must remain green.
        - I-UI-11 audit (curses wrapper imports allowlist) must remain
          green.
        - README updates the Operator TUI section to document the new
          agent-style flow (bottom composer + /queue /step /state /tick
          /help /quit), keeping the existing `n`-key dialog path as a
          secondary entry point per ruling B.
        - Removes the last row (I-UI-21) from the pending list;
          registers I-UI-23 as OBSERVED alongside I-UI-14.
        - Gate: python3 -m brain.invariants run --id I-UI-21,
                                                  --id I-UI-23,
                                                  --id I-UI-11,
                                                  --id I-UI-07;
                python3 -m brain.ui --print-once (renders one
                deterministic agent-style frame and exits).
```

Step 11 (full gate) and Step 12 (post-completion audit) come after
the strict order above; they are not part of the catalog patch plan's
scope but are listed in `CURRENT_CAMPAIGN.md`.

### 6.1 Forbidden orderings

```text
- Step 7 must not run before Step 6 (no rows to drive).
- Step 8 must not run before Step 7 (the composer's renderer needs
  AgentLayout + PaneSpec + AgentTuiViewModel from Step 7).
- Step 9 must not run before Step 8 (the transcript's append site is
  the wrapper, but the wrapper's call into the parser comes from
  Step 8; landing the transcript first would leave its append site
  uncalled and the I-UI-19 fixture would have to fake the entry path).
- Step 10 must not run before Step 9 (the wrapper imports the
  transcript module).
- The pending list must shrink monotonically. If a step adds rows back
  to the pending list (i.e., a fixture lands but does not actually
  drive its row green), the step has failed and must stop.
```

### 6.2 Rollback discipline

Each step in the order is committed and pushed in a separate commit.
A step that fails validation reverts only its own commit; previous
steps stay in place. The pending list and the I-CAT-01 audit are the
canary signals — if either drifts, the active agent stops and reports
rather than attempting to fix forward.

---

## 7. Owning modules and fixtures

The full set of owning modules and fixtures named by the corrigenda
row table is reiterated here for Step 6's row text:

```text
Module                              Status      Rows it owns
----------------------------------- ----------- ------------------
brain/ui/layout.py                  new         I-UI-16, I-UI-20, I-UI-22
brain/ui/composer.py                new         I-UI-17
brain/ui/command_line.py            new         I-UI-18
brain/ui/transcript.py              new         I-UI-19
brain/ui/render.py                  existing    I-UI-20 (shared)
brain/ui/tui.py                     existing    I-UI-21, I-UI-23
brain/ui/session.py                 existing    I-UI-23 (shared)
```

```text
Fixture                                       Status   Rows it drives
--------------------------------------------- -------- ------------------
brain/ui/fixtures/agent_layout.py             new      I-UI-16, I-UI-20, I-UI-22
brain/ui/fixtures/composer_input.py           new      I-UI-17, I-UI-18
brain/ui/fixtures/transcript_log.py           new      I-UI-19
brain/ui/fixtures/agent_tui_smoke.py          new      I-UI-21, I-UI-23
brain/ui/fixtures/tui_smoke.py                existing I-UI-07 extension
                                                       (audit allowlist)
```

The existing fixture `brain/ui/fixtures/tui_smoke.py` is extended at
Steps 8 and 10 to walk the new modules in its import-audit; no new
fixture replaces it. Per ruling G, this extension is fixture-level
work, not catalog-level work, and does not require a new row.

---

## 8. Count impact summary

```text
Category         v0.10  Step 4 delta  v0.11
---------------- ----- ------------- -----
REQUIRED           123  +4             127
STRUCTURAL          41  +3              44
NOT-EXERCISED        4  +0               4
DEFERRED            12  +0              12
OBSERVED             6  +1               7
Total              186  +8             194
```

Rationale:

```text
+4 REQUIRED:    I-UI-16, I-UI-17, I-UI-18, I-UI-19
+3 STRUCTURAL:  I-UI-20, I-UI-21, I-UI-22
+1 OBSERVED:    I-UI-23
+0 NOT-EXERCISED: I-UI-15 stays NOT-EXERCISED (no save/export route
                  is introduced).
+0 DEFERRED:    no row migrates into or out of DEFERRED in this
                campaign.
```

The total count delta (`+8 rows`) matches the corrigenda section 9
projection and the kickoff section 16 projection.

---

## 9. Open decisions

There are **no open decisions** for the Step 5 review gate to
resolve.

Open decisions A–G from kickoff section 17 are closed by corrigenda
section 10 (quoted verbatim in section 3 above). Open decisions H+
(if the gate raises any) would re-open the campaign at the
corrigenda level, not at the catalog patch level, because the
contracts are upstream of the catalog rows.

The Step 5 review gate's role is to confirm:

```text
1. The row table (section 2) is consistent with the corrigenda.
2. The rulings (section 3) are quoted verbatim and the catalog patch
   does not contradict them.
3. The catalog patch mechanics (section 5) leave the runner and the
   I-CAT-01 audit in a defined state at every intermediate point.
4. The strict implementation order (section 6) is preserved.
5. No stop condition (section 10 below) is implicitly tripped.
6. The count impact (section 8) matches the corrigenda projection.
```

If any of those checks fails, the gate stops and reports. Otherwise,
Step 6 runs against the catalog as specified.

---

## 10. Stop conditions

The stop conditions from corrigenda section 11 are restated verbatim
below. The Step 5 review gate must check none of them is tripped by
the catalog patch plan above; Steps 6–10 must continue to honor them.

> Carried from the kickoff:
>
> ```text
> - composer requires storing a callable / file handle / socket / LLM
>   client on OperatorSession (would weaken I-UI-10)
> - parser requires shell expansion, subprocess, or eval / exec
> - transcript requires filesystem writes or JSONL trace output
> - layout requires curses calls inside the pure renderer
> - agent layout requires changes to tick() semantics, trace schema,
>   scenario schema, developmental-history shapes, or TLICA contracts
> - catalog patch requires weakening an existing I-UI-* row
> - small-terminal degraded path drops the COMPOSER or FOOTER pane
> - typed command flow needs natural-language interpretation
> ```
>
> Added by this corrigenda:
>
> ```text
> - any open decision A-G is re-opened mid-implementation without an
>   explicit operator instruction (Steps 6-12 must follow the rulings
>   in section 10 above).
> ```

Catalog-patch-plan-specific stop conditions (in addition to the
above):

```text
- The pending registrations list at Step 6 contains a REQUIRED or
  STRUCTURAL row not in the I-UI-16..I-UI-22 set (i.e., the patch
  silently introduces a pending dependency on another module).
- The catalog banner change at Step 6 modifies any v0.2..v0.10
  banner block instead of inserting a new v0.11 banner above v0.10.
- python3 -m tools.catalog counts reports actual != expected != banner
  at any intermediate point during Step 6 (the catalog must reach
  127/44/4/12/7 cleanly, not via a temporary mismatch).
- python3 -m tools.catalog generate-ids writes any ID outside the
  I-UI-16..I-UI-23 set, indicating an unintended catalog edit elsewhere.
- A step in the strict order (section 6) needs to touch a file
  outside its allowed-files list to satisfy its driven rows. That
  signals a contract gap — stop and reopen the corrigenda.
- The runner's I-CAT-01 audit reports more pending rows than the
  pending list explicitly enumerates.
- Any optional package marker created in Step 6 contains import
  statements (markers must remain empty modules; runtime imports
  belong to the step that lands the module's real implementation).
```

If any stop condition trips, the active agent stops and reports
rather than folding the change in. Step 5 (review gate) is the
natural checkpoint to surface a stop-condition concern before any
catalog edit lands.

---

## 11. Validation footprint

This document is text-only. Validation is:

```text
git diff --name-only           -> OPERATOR_TUI_AGENT_LAYOUT_CATALOG_PATCH_PLAN.md
python3 -m tools.catalog counts -> 123/41/4/12/6 (unchanged)
```

No catalog row is added at Step 4. No fixture is added at Step 4. No
runtime module is added at Step 4. The catalog patch lands at Step 6
after the Step 5 review gate passes.

---

## 12. Next artifact

The next campaign step is **Step 5 — Review gate**.

`CURRENT_CAMPAIGN.md` Step 5 says:

```text
Do not proceed to Step 6 unless the catalog patch plan is coherent
and no open decision blocks implementation.

Stop and report if the plan requires shell/network/host execution,
real LLM calls, direct BrainState mutation, tick() semantic changes,
scenario/trace schema changes, external dependencies, or weakening
existing I-UI safety rows.

Proceed only when the user says `go` again or explicitly accepts the
plan.
```

This catalog patch plan asserts (and the Step 5 gate must verify):

```text
1. No shell, network, or host execution is required.
2. No real LLM call is required.
3. No direct BrainState mutation is introduced.
4. tick() semantics are unchanged.
5. scenario / trace schemas are unchanged.
6. No external dependencies are added.
7. No existing I-UI safety row is weakened (section 4 above).
```

After Step 5 accepts the plan, Step 6 lands the catalog patch per
section 5 mechanics, the pending list opens per section 5.7, and the
strict implementation order in section 6 carries the campaign through
Step 10. Step 11 runs the full gate; Step 12 lands the post-completion
audit.

The campaign's overall stop condition (Step 12 audit verdict of
PASS / PASS WITH PATCHES / BLOCKED) is unchanged.
