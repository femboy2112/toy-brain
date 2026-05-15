# OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md — Operator TUI Agent-Style Layout Campaign Post-Completion Audit

## Verdict

```text
PASS
```

The Operator TUI Agent-Style Layout campaign landed all eight new
`I-UI-16..I-UI-23` catalog rows at v0.11, the four new runtime modules
(`brain/ui/layout.py`, `brain/ui/composer.py`,
`brain/ui/command_line.py`, `brain/ui/transcript.py`), their four
fixtures (`brain/ui/fixtures/agent_layout.py`,
`brain/ui/fixtures/composer_input.py`,
`brain/ui/fixtures/transcript_log.py`,
`brain/ui/fixtures/agent_tui_smoke.py`), the renderer extension
(`render_agent`), the curses-wrapper switch to `AgentTuiViewModel`, and
the README sync. The full gate is green at v0.11. No guarded files were
mutated. No Phase 3.5 / Mode B / language / real-LLM / shell / network /
host-execution / filesystem-export surface was introduced. Every
ruling A–G from `OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md` section 10
was honored by the implementation.

---

## Saved project state at audit time

```text
Catalog: v0.11
Counts (banner = actual = expected):
  REQUIRED       = 127
  STRUCTURAL     =  44
  NOT-EXERCISED  =   4
  DEFERRED       =  12
  OBSERVED       =   7
Total rows checked by invariants runner: 178
REQUIRED green: 127   REQUIRED red: 0
STRUCTURAL green:  44 STRUCTURAL red: 0
OBSERVED:           7 pass / 0 fail
Gate failures: 0
Full gate (bash tools/check_all.sh): green
Entrypoint: python3 -m brain.ui
```

Patch over v0.10: +4 REQUIRED, +3 STRUCTURAL, +1 OBSERVED for the
agent-style operator surface.

---

## Catalog banner and expected counts cross-check

```text
INVARIANT_CATALOG.md banner block at line 5:
  "Catalog version: v0.11. Patches over v0.10 (Operator TUI Agent-Style
   Layout catalog expansion): +4 REQUIRED rows, +3 STRUCTURAL rows,
   +1 OBSERVED row. Adds the I-UI-16..I-UI-23 row family ..."

tools/catalog.py EXPECTED_COUNTS:
  REQUIRED:      127
  STRUCTURAL:     44
  NOT-EXERCISED:   4
  DEFERRED:       12
  OBSERVED:        7

python3 -m tools.catalog counts:
  Category            Banner    Actual  Expected
  REQUIRED               127       127       127  ok
  STRUCTURAL              44        44        44  ok
  NOT-EXERCISED            4         4         4  ok
  DEFERRED                12        12        12  ok
  OBSERVED                 7         7         7  ok
```

Banner = actual = expected at 127 / 44 / 4 / 12 / 7. PASS.

The v0.10 banner block remains in place above (chronologically below)
the v0.11 entry; no historical banner was rewritten. The catalog patch
plan's section 5.2 ("Catalog banner update") is honored exactly.

---

## I-UI-* row coverage

All `I-UI-*` rows (existing v0.10 + new v0.11) are green or
OBS-PASS in the invariants runner:

```text
[brain.ui.fixtures.snapshot_view]
  PASS      I-UI-01      REQUIRED
  PASS      I-UI-08      STRUCTURAL

[brain.ui.fixtures.render_view]
  PASS      I-UI-02      REQUIRED
  PASS      I-UI-09      STRUCTURAL

[brain.ui.fixtures.command_router]
  PASS      I-UI-03      REQUIRED
  PASS      I-UI-04      REQUIRED
  PASS      I-UI-06      REQUIRED
  PASS      I-UI-13      STRUCTURAL

[brain.ui.fixtures.bottom_up_tick]
  PASS      I-UI-05      REQUIRED
  PASS      I-UI-10      STRUCTURAL

[brain.ui.fixtures.tui_smoke]
  PASS      I-UI-07      REQUIRED
  PASS      I-UI-11      STRUCTURAL
  PASS      I-UI-12      STRUCTURAL
  OBS-PASS  I-UI-14      OBSERVED

[brain.ui.fixtures.agent_layout]
  PASS      I-UI-16      REQUIRED   (new)
  PASS      I-UI-20      STRUCTURAL (new)
  PASS      I-UI-22      STRUCTURAL (new)

[brain.ui.fixtures.composer_input]
  PASS      I-UI-17      REQUIRED   (new)
  PASS      I-UI-18      REQUIRED   (new)

[brain.ui.fixtures.transcript_log]
  PASS      I-UI-19      REQUIRED   (new)

[brain.ui.fixtures.agent_tui_smoke]
  PASS      I-UI-21      STRUCTURAL (new)
  OBS-PASS  I-UI-23      OBSERVED   (new)
```

I-UI-15 (NOT-EXERCISED, save/export placeholder) is unchanged and does
not appear in the runner's per-row summary, matching its NOT-EXERCISED
status. All `I-UI-*` rows green; no existing row was weakened, amended,
or retired (the campaign extends, it does not modify in place).

---

## Pending list cross-check

```text
brain/invariants.py:_OPERATOR_TUI_AGENT_LAYOUT_PENDING_ROWS = {}
```

The Operator TUI Agent-Style Layout pending list is empty. Every
REQUIRED / STRUCTURAL row in the I-UI-16..I-UI-22 set landed with a
fixture-backed registered check by Step 10. I-UI-23 (OBSERVED) is
registered alongside its fixture at Step 10, mirroring the
I-UI-14 / `tui_smoke.py` precedent.

Per the patch plan section 5.7, the pending list shrank monotonically:

```text
After Step 6:  pending = {I-UI-16, I-UI-17, I-UI-18, I-UI-19,
                          I-UI-20, I-UI-21, I-UI-22}
After Step 7:  pending = {I-UI-17, I-UI-18, I-UI-19, I-UI-21}
After Step 8:  pending = {I-UI-19, I-UI-21}
After Step 9:  pending = {I-UI-21}
After Step 10: pending = {}
```

Final state matches the planned final state. PASS.

The I-CAT-01 catalog↔registry coverage audit is green at the run-time
gate, confirming every REQUIRED / STRUCTURAL row has a registered
check.

---

## Rulings A–G honoured

### Ruling A — `ComposerState.status_line` kept as a field

```text
brain/ui/composer.py:
  ComposerState carries a `status_line: str` field (bounded printable).
  The SUBMIT action with an empty/whitespace-only buffer sets
  status_line="empty composer submission" and returns the unchanged
  buffer (no ComposerSubmission). Parse-time messages flow into
  status_line without reaching session.set_error.

brain/ui/render.py:
  _render_agent_composer prefers session.status_message when set;
  otherwise it reads ComposerState.status_line. The "prefer session"
  precedence keeps I-UI-13 status-pane semantics intact.
```

PASS. Honoured exactly.

### Ruling B — composer history does not bleed into the curses prompt

```text
brain/ui/tui.py:
  The `n` keystroke (when the composer buffer is empty and the key
  is not "/") opens the existing two-field bounded curses percept
  prompt wired in commit c4b8c07. The prompt does not receive the
  composer's submission ring; HISTORY_PREV / HISTORY_NEXT only walk
  ComposerState.history.

brain/ui/fixtures/agent_tui_smoke.py:
  Scripted walk exercises typed /queue (composer path), not the dialog
  path. No fixture wires composer history into the prompt.
```

PASS. Honoured exactly.

### Ruling C — `/clear` does not clear the composer buffer

```text
brain/ui/command_line.py:
  "/clear" -> Command(OperatorCommand.CLEAR_STATUS).
  The verb dispatch table contains no clear-buffer side effect.

brain/ui/composer.py:
  ComposerAction.CLEAR_BUFFER (^U / ^C) is the only path that resets
  buffer="" and history_idx=None outside of SUBMIT.

README.md / /help text:
  Documents "/clear clears local status/error (does NOT clear the
  composer buffer; use ^U for that)".
```

PASS. Honoured exactly.

### Ruling D — transcript is process-local, no persistence

```text
brain/ui/transcript.py:
  OperatorTranscript has no filesystem read/write. No `~/.brain_tui_*`
  path. No JSONL writer. No pickle/json/yaml/toml import. The append
  operation is copy-on-write and returns a new frozen record.

brain/ui/tui.py:
  The wrapper builds OperatorTranscript.empty() at startup and
  discards it on exit. No persistence hook.
```

PASS. Honoured exactly.

### Ruling E — legacy `TuiViewModel` retired in the live wrapper; legacy fixtures still pass

```text
brain/ui/tui.py:
  The live wrapper builds AgentTuiViewModel (line 238) and renders
  through render_agent. No call site in tui.py builds the legacy
  TuiViewModel.

brain/ui/render.py:
  Legacy TuiViewModel class is preserved (line 49) and still used by
  brain/ui/fixtures/render_view.py to drive I-UI-02 / I-UI-09 against
  the original single-pane renderer. Removing the legacy class would
  retire those existing fixtures, which the campaign explicitly
  refused (ruling E body: "the legacy TuiViewModel remains importable
  for the duration of Steps 6–9 so existing fixtures do not have to
  be rewritten").

brain/ui/__main__.py --print-once:
  Renders one deterministic frame through AgentTuiViewModel plus
  render_agent. The codex/operator-tui-input-switch-fixes repair
  branch brought this path back into line with the corrigenda Step 10
  ruling: the non-interactive snapshot now includes the header,
  transcript, bottom composer, and footer.
```

PASS. The wrapper and `--print-once` path both use
`AgentTuiViewModel`; the renderer keeps both forms available so legacy
fixtures still pass. The "legacy TuiViewModel retired in the live
wrapper but legacy fixtures still pass" cross-check is satisfied
exactly.

### Ruling F — single entrypoint `python3 -m brain.ui`

```text
brain/ui/__main__.py:
  Single entry file. argparse exposes --check-terminal and --print-once
  flags. No `python3 -m brain.ui.agent` or parallel entrypoint added.

python3 -m brain.ui:
  Picks the agent layout in the curses live path (TTY required).

python3 -m brain.ui --print-once:
  Renders one deterministic frame and exits without curses.

python3 -m brain.ui --check-terminal:
  Probes terminal usability and exits without touching curses.
```

PASS. Honoured exactly. Verified at audit time:

```text
$ python3 -m brain.ui --print-once
[ core state ]------------------------------------------------------------------
profile domain size : 2
profile values:
  __cogito__ = 1
  alpha = 3/4
... (deterministic frame)
```

### Ruling G — `I-UI-07` covers new modules transitively

```text
brain/ui/fixtures/tui_smoke.py:
  The package-scoped import-audit walks brain/ui/*.py and asserts the
  allowlist (typing helpers, brain.ui.commands, brain.ui.snapshot,
  brain.ui.render, brain.ui.session constants, etc.). The four new
  modules (layout.py, composer.py, command_line.py, transcript.py)
  fall under this walk by virtue of living in brain/ui/. No new
  per-module import-audit row was added; I-UI-07's fixture was
  extended in scope as the modules landed at Steps 7-9.

python3 -m brain.invariants run --id I-UI-07:
  PASS at v0.11. Allowlist still tight.
```

PASS. Honoured exactly.

---

## Guarded path discipline

```text
brain/tlica/                                  untouched
brain/llm/                                    untouched
brain/tick.py                                 untouched
scenarios/                                    untouched
traces/first_scenario_real.jsonl              untouched
traces/RUN_SUMMARY.md                         untouched
lean_reference/                               untouched
```

Verified via `git log --since="2 weeks ago" -- brain/tlica/
lean_reference/ traces/ scenarios/ brain/tick.py brain/llm/` — no
commits in the agent-layout campaign window touched any guarded
path. The most recent guarded-path edits are
Phase 2 / Phase 3 baseline work from months earlier
(`f4f62f7 feat(llm): ship ClaudeCLIClient ...`,
`4c7f9e9 Phase 2 v1.2 corrigenda ...`, etc.).

The non-fixture modules in `brain/ui/` carry no live imports of the
guarded packages outside `TYPE_CHECKING` blocks and the offline
stand-in client construction in `brain/ui/__main__.py`:

```text
brain/ui/tui.py line 98-99:
  if TYPE_CHECKING:  # pragma: no cover - typing-only imports
      from brain.llm.client import LLMClient

brain/ui/__main__.py inside _build_default_session():
  from brain.tick import BrainState
  from brain.tlica.builders import (...)
  from brain.tlica.profile import COGITO_ID
  from brain.tlica.ptcns import ConsistencyEval
```

The `__main__.py` imports are deliberate (the entrypoint must build a
minimal `BrainState` to render against; this is unchanged from the
prior `OPERATOR_TUI_AUDIT.md` PASS verdict, and the import-audit
allowlist for the entrypoint module explicitly permits them). The new
modules (`layout.py`, `composer.py`, `command_line.py`,
`transcript.py`) carry zero imports from any guarded package; they
import only typing / dataclasses / enum / `brain.ui.commands` /
`brain.ui.snapshot` / `brain.ui.constants` / `brain.io_types`.

PASS.

---

## Full gate

```text
$ python3 -m tools.catalog counts
  Banner = Actual = Expected at 127 / 44 / 4 / 12 / 7. ok across the board.

$ python3 -m tools.citations verify
  Verified 100 citations.
  All catalog citations resolve in lean_reference/.

$ python3 -m tools.import_audit
  I-PCE-05: agency.py is clean of pce imports.

$ python3 -m brain.invariants run
  178 rows checked  ·  REQUIRED green: 127 ·  REQUIRED red: 0
  STRUCTURAL green: 44 ·  STRUCTURAL red: 0
  OBSERVED: 7 pass / 0 fail  ·  gate failures: 0

$ bash tools/check_all.sh
  178 rows checked, every REQUIRED row green, every STRUCTURAL row
  green, all OBSERVED rows pass, no gate failures.
  All checks passed.
```

PASS across the full gate.

---

## Entrypoint cross-check (ruling F)

```text
$ python3 -m brain.ui --print-once
Renders the agent-layout frame deterministically and exits 0. The
frame includes the header, state/inspector panes, transcript pane,
bottom composer, and footer.

$ python3 -m brain.ui --check-terminal
Reports usable=False with reason "stdout is not attached to a terminal"
when run outside a TTY (expected); reports usable=True on a real
terminal. Exits 1 in the false case, matching the prior contract.

$ python3 -m brain.ui   (in a real TTY)
Opens the curses wrapper with AgentTuiViewModel + render_agent +
the bottom composer typing surface. Typed /queue, /step, /state,
/tick, /help, /quit flow through the LocalCommandLine parser into
OperatorSession.dispatch exactly as the typed-command flow
documented in section 12 of OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md.
```

PASS.

---

## Scope creep

No scope creep observed.

What the campaign **did not** add (the non-goals from
`OPERATOR_TUI_AGENT_LAYOUT_SYNTHESIS.md` section 8 and
`OPERATOR_TUI_AGENT_LAYOUT_KICKOFF.md` section 16):

```text
no Phase 3.5 Expression + ReadabilityPredictor
no social/language harness
no Mode B planning
no natural-language understanding of composer input
no LLM-backed autocomplete / suggestions
no chat surface (the composer is a typed local UI command line)
no real LLM call (offline stand-in client unchanged)
no shell, subprocess, or os.system path
no network I/O (no sockets, no HTTP, no DNS)
no filesystem writes (no save / export, no transcript persistence)
no scenario / trace schema changes
no tick() semantics changes
no developmental-history shape changes
no TLICA / Lean-bound row
no direct BrainState mutation
no new external dependencies
```

Each non-goal is enforced by an `I-UI-*` row or by the import-audit
gate:

```text
I-UI-07  REQUIRED    import audit — no curses / kernel / LLM / shell /
                                    network / file imports in
                                    brain/ui/*.py outside the wrapper
I-UI-10  REQUIRED    OperatorSession holds no callable, file handle,
                                    socket, or LLM client
I-UI-11  STRUCTURAL  curses wrapper imports no kernel / LLM / shell /
                                    network / file surfaces
I-UI-13  STRUCTURAL  status / error / transcript text is bounded
                                    printable
I-UI-15  NOT-EX'D    save/export route — remains NOT-EXERCISED
I-UI-18  REQUIRED    parser maps only to approved OperatorCommand /
                                    QueuePerceptPayload routes
I-UI-19  REQUIRED    transcript is local UI state only (no fs writes,
                                    no developmental-history appends)
I-UI-21  STRUCTURAL  curses wrapper delegates input to composer /
                                    router; does not mutate kernel state
                                    directly
```

PASS.

---

## Step-by-step trail

```text
Step  1  UX synthesis                       commit 0a9d3d4   PASS
Step  2  Kickoff                            commit 97cb503   PASS
Step  3  Corrigenda                         commit 45532e0   PASS
Step  4  Catalog patch plan                 commit ae58f78   PASS
Step  5  Review gate                        accepted         PASS
Step  6  Apply v0.11 catalog patch          commit b942cb5   PASS
Step  7  Layout + pure renderer upgrade     commit 161dfc0   PASS
Step  8  Bottom composer + typed parser     commit e135fa1   PASS
Step  9  Transcript + session integration   commit 1fd9f9b   PASS
Step 10  Curses wrapper + README sync       commit 7a60119   PASS
Step 11  Full gate                          no-commit (green) PASS
Step 12  Post-completion audit              this document    PASS
```

Each runtime step was committed and pushed in isolation; the catalog
patch (Step 6) landed before any runtime module; the pending list
shrank monotonically through Steps 7–10; Step 11 ran the full gate
clean (no fix-up commit needed); Step 12 records this verdict.

---

## Stop-condition triggers encountered

None.

The following stop conditions from
`OPERATOR_TUI_AGENT_LAYOUT_CATALOG_PATCH_PLAN.md` section 10 were
checked at every step and never tripped:

```text
- composer requires storing a callable / file handle / socket / LLM
  client on OperatorSession (would weaken I-UI-10)              not tripped
- parser requires shell expansion, subprocess, or eval / exec   not tripped
- transcript requires filesystem writes or JSONL trace output   not tripped
- layout requires curses calls inside the pure renderer         not tripped
- agent layout requires changes to tick() semantics, trace
  schema, scenario schema, developmental-history shapes, or
  TLICA contracts                                               not tripped
- catalog patch requires weakening an existing I-UI-* row       not tripped
- small-terminal degraded path drops the COMPOSER or FOOTER
  pane                                                          not tripped
- typed command flow needs natural-language interpretation      not tripped
- any open decision A-G is re-opened mid-implementation         not tripped
- the pending list adds a row outside I-UI-16..I-UI-22          not tripped
- catalog banner change modifies any v0.2..v0.10 entry          not tripped
- python3 -m tools.catalog counts reports actual != expected    not tripped
- generate-ids writes any ID outside I-UI-16..I-UI-23           not tripped
- a step touches a file outside its allowed-files list          not tripped
- I-CAT-01 reports more pending rows than enumerated            not tripped
- optional package marker contains import statements            not tripped
                                                                   (no markers created)
```

---

## Manual test instructions

```bash
python3 -m brain.ui
```

Expected interaction in a real TTY (>= 20 cols x 6 rows; default
80 x 24 recommended):

```text
1. bottom input bar visible immediately ("> _" with cursor)
2. type:    /queue beta hello-world
   press:   Enter
   expect:  transcript shows [SUBMIT] /queue beta hello-world
            transcript shows [QUEUED] queued percept 'beta' (queue size = 1)
            queue summary in header updates to queue=1
3. type:    /step
   press:   Enter
   expect:  transcript shows [SUBMIT] /step
            transcript shows [STEP] tick 1 ok (...)
            header tick counter increments
            inspector pane refreshes
4. type:    /tick     (or press t when the buffer is empty)
   expect:  inspector pane switches to the latest TickRecord view
5. type:    /state    (or press s when the buffer is empty)
   expect:  inspector pane switches to BrainState view
6. type:    /help     (or press ? when the buffer is empty)
   expect:  inspector pane switches to the typed-command help
7. type:    /quit     (or press q when the buffer is empty)
   expect:  wrapper exits cleanly with curses cleanup
```

Non-interactive sanity checks (no TTY required):

```bash
python3 -m brain.ui --print-once       # renders one deterministic frame
python3 -m brain.ui --check-terminal   # probes terminal usability
bash tools/check_all.sh                # full gate
```

All three were exercised at audit time and pass.

---

## Remaining limitations

The campaign was a UI/UX redesign of the operator surface. The
following are known limitations and are explicitly deferred to future
campaigns:

```text
- No transcript persistence across `python3 -m brain.ui` invocations
  (ruling D; the transcript is process-local by design).
- No scroll interaction in the transcript pane. Only the newest
  TRANSCRIPT_MAX_ENTRIES (64) entries are bounded; the renderer shows
  the newest transcript_rows entries derived from AgentLayout. A
  page-up / page-down surface is out of scope for this campaign.
- No multi-line composer. Each ComposerSubmission is one verb per
  submission. Multi-line input would require composer state changes
  and a multi-line renderer, both out of scope.
- No syntax highlighting, autocomplete, or fuzzy match in the parser.
  The grammar is finite by design (ruling Synthesis section 5 +
  Kickoff section 8); LLM-backed extensions would be Phase 3.5
  territory.
- No mouse handling, no colour attributes, no Unicode emoji rendering,
  no terminal automation outside the curses UI. The wrapper remains
  thin and uses only `addnstr` + `getstr` style operations.
- The legacy `TuiViewModel` record is preserved so the existing
  `render_view.py` fixtures still pass. A separate (small) cleanup
  campaign could migrate those fixtures and remove the legacy record;
  doing so was explicitly out of scope per ruling E.
- Phase 3.5 Expression + ReadabilityPredictor remains the next
  developmental campaign and is not started here.
```

None of these limitations weaken any existing safety row or invalidate
the campaign's PASS verdict; they are scoped follow-up work.

---

## Recommended next mission

Per `CURRENT_CAMPAIGN.md` and `README.md`, the next developmental
campaign is Phase 3.5 Expression + ReadabilityPredictor. That campaign
is **not** authorized to start automatically by this audit; a new
mission selection step (updating `CURRENT_MISSION.md` /
`CURRENT_CAMPAIGN.md` to point at the Phase 3.5 plan) is required
before any Phase 3.5 work begins.

One small follow-up UX campaign is visible (entirely optional):

```text
- Legacy TuiViewModel retirement: migrate the existing render_view.py
  fixtures onto AgentTuiViewModel via a thin adapter, remove the
  legacy record from brain/ui/render.py.
```

Neither is required for the agent-style campaign to PASS.

---

## Campaign complete output

```text
Operator TUI agent-style layout campaign complete.
Catalog: v0.11
Counts: 127 REQUIRED / 44 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 7 OBSERVED
Full gate: pass
Entrypoint: python3 -m brain.ui
Interactive flow: bottom composer supports /queue, /step, /state, /tick, /help, /quit
Remaining deferred work: Phase 3.5 Expression + ReadabilityPredictor
```
