# PHASE3_11_LIVE_TEST_KICKOFF.md

## Purpose

Define how the Phase 3.11 Comprehensive Live Behavior Test will
actually be executed. This is a planning artifact only. It does
not edit any source file, fixture, or kernel path. It binds the
test execution style for Steps 13-17 of `CURRENT_CAMPAIGN.md`.

```text
Status: DRAFT / PLANNING / NO-IMPLEMENTATION
```

The campaign is **evidence-seeking**, not green-by-default. The
purpose of Steps 13-17 is to surface what the system actually
does when launched and used, not to confirm a hypothesis. This
kickoff therefore deliberately permits unflattering findings.

---

## 1. Baseline

```text
Catalog version:  v0.20
REQUIRED:        214
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         16
Total fixtures:  137
  Current non-helper fixture modules:          137
  Phase 3.11 Codex CLI Runtime Option:          +2 fixture modules
  New fixture modules:
    - llm_runtime_codex_cli_requires_executable.py  (I-LLMTOG-16)
    - llm_runtime_codex_cli_factory.py              (I-LLMTOG-17)
Preflight at HEAD:
  catalog counts                  ok / ok / ok
  citations verify                100 citations resolve
  import_audit                    agency.py clean
  invariants run                  REQUIRED 215 green / 0 red;
                                  STRUCTURAL 83 green / 0 red;
                                  OBSERVED 7 pass / 0 fail;
                                  gate failures 0
  check_all.sh                    All checks passed
```

Steps 13-17 run on top of this baseline. Any divergence from
green at the start of a behavior test step is a finding to be
recorded, not silently fixed inside the live-test step.

---

## 2. Test execution styles

Four execution styles are permitted in Steps 13-17. Every
recorded observation in the Step 13/14/15/16/17 reports must
declare which style produced it.

### 2.1 Manual observed test (MOT)

```text
Definition:
  An operator runs a command interactively, watches output,
  and records what happened in prose.

When used:
  - curses-driven launch paths (full TUI session) — the curses
    UI does not accept a line-oriented scripted stdin in v0.20,
    so any sequence of typed operator commands (/stream, /step,
    /quit, ...) inside the running TUI is recorded as MOT
  - interactive REPL paths
  - any path where stdin/stdout sequencing is the subject of
    observation (e.g., does /step actually print MSI?)

Reporting requirement:
  - record the exact command line
  - record the bounded set of observed outputs (no full transcripts
    unless explicitly justified)
  - record any environment dependencies (TTY, terminal width)
  - mark the row "MOT" in the report
```

### 2.2 Scripted subprocess test (SST)

```text
Definition:
  Python or bash script invokes `python3 -m brain.ui ...` for a
  one-shot CLI path (no curses), OR invokes the operator
  command parser + OperatorSession.dispatch in-process from a
  driver script. The full curses TUI does NOT expose a
  line-oriented stdin command runner; piping a sequence of
  `/stream <text>` / `/step` etc. into `python3 -m brain.ui` is
  NOT a valid SST harness in v0.20. See Section 2.1 (MOT) for
  full-curses command sequences.

Valid SST paths:
  - --print-once
  - --check-terminal
  - --db-status / --db-verify / --db-backup one-shot flags
  - any other non-curses subprocess path where stdout / stderr /
    exit code is captured as text
  - in-process tests that import brain.ui.command_line and
    brain.ui.session and drive `LocalCommandLine.parse` +
    `OperatorSession.dispatch` against a real BrainState

Reporting requirement:
  - record the script's invocation (or import path) under
    repo-root cwd
  - record exit code, stdout summary, stderr summary
    (or returned dispatch outcome for in-process tests)
  - mark the row "SST" in the report
  - all temporary DB paths under /tmp/phase3_11_*/
```

### 2.3 Read-only file inspection (RFI)

```text
Definition:
  Operator reads an existing source / fixture / catalog file
  to verify a structural property that does not require runtime
  invocation (e.g., "does brain/ui/__main__.py have the codex-cli
  argument?").

When used:
  - structural audits the runner already covers but the live test
    wants to surface as part of the operator-readable narrative
  - module-import-graph spot checks

Reporting requirement:
  - record the file path and the cited line range
  - mark the row "RFI" in the report
```

### 2.4 OBSERVED real-LLM smoke (ORS)

```text
Definition:
  Operator invokes a model-backed mode against the real underlying
  LLM CLI / API. Cannot fail the runner.

When used:
  - I-LLMTOG-14 (real anthropic-api / claude-cli smoke)
  - I-LLMTOG-18 (real codex-cli smoke)
  - any path that requires operator-supplied auth / executable

Reporting requirement:
  - record whether the external tool was available
  - if unavailable, record "ORS skipped: <reason>" — this is a
    valid observation, not a failure
  - if available, record exit, stdout summary, any error surface
  - mark the row "ORS" in the report
  - real LLM smoke is always opt-in and never gating
```

---

## 3. Expected report format

Each Step 13-17 report (PHASE3_11_*_BEHAVIOR_REPORT.md) follows
this skeleton:

```text
# PHASE3_11_<topic>_BEHAVIOR_REPORT.md

## Purpose
<one paragraph; what the report covers and how it was produced>

## Environment
- python: <version>
- platform: <linux / mac / etc>
- terminal availability: <TTY / non-TTY>
- external tool availability:
    - claude:  <present at PATH / absent>
    - codex:   <present at PATH / absent>
    - anthropic api key: <present / absent>

## Method
- preflight: <commands run before observations>
- temporary DB policy: <under /tmp/phase3_11_*/>

## Observations
| ID | Style | Command / file | Expected | Observed | Verdict |
|----|-------|----------------|----------|----------|---------|
| ...|  MOT  | ...            | ...      | ...      | works / awkward / confusing / fails / blocked |

## Findings classification
- works as expected: <count>
- works but awkward: <count>
- confusing output:  <count>
- incorrect behavior:<count>
- missing feature:   <count>
- blocked by env:    <count>

## Notes
<free prose for context that does not fit the table>
```

The Step 18 behavior findings report aggregates the per-topic
reports into a single classification.

---

## 4. Temporary DB policy

```text
All session-db paths used in Steps 13-17 are created under
/tmp/phase3_11_<topic>_<utc_nanos>.db
and are removed at the end of the step that creates them.

No test DB lives inside the repo working tree.

No autosave DB / backup DB / verify DB persists past its
generating step.

If a test wants to share state across steps (e.g., Step 14
saves and Step 14b reloads), the path is documented in the
report.
```

---

## 5. External tool availability policy

```text
The behavior tests run on whatever the operator's environment
provides. The kickoff does NOT require:

  - a real codex binary on PATH
  - a real claude binary on PATH
  - an ANTHROPIC_API_KEY env var
  - network access to anthropic.com

When any of those is missing:

  - the corresponding test row is marked "blocked by env"
    (not "failed")
  - the per-topic report's Environment section records the
    absence explicitly
  - the Step 18 findings aggregator counts it under
    "blocked by environment", not under failures

Operator may opt into the real-LLM ORS smoke (Section 2.4)
if any of the external tools is available. The smoke walk is
documented in PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md when
performed and explicitly marked "ORS skipped" when not.
```

---

## 6. Real LLM smoke policy

```text
Real-LLM modes are ALWAYS optional in Steps 13-17:

  --llm-mode offline       deterministic; no opt-in needed
  --llm-mode mock          deterministic; no opt-in needed
  --llm-mode anthropic-api ORS only; requires --llm-anthropic-api-key
  --llm-mode claude-cli    ORS only; requires real claude on PATH
  --llm-mode codex-cli     ORS only; requires real codex on PATH

The Step 17 report explicitly distinguishes between:

  (a) "the mode constructs / errors correctly" (SST; gating)
  (b) "the mode actually returns coherent LLM output" (ORS; not gating)

(a) tests can run without any external tool. They are exercised
by the existing I-LLMTOG-* fixtures and re-exercised in Step 17
through the operator-facing CLI. They are gating.

(b) tests require external tools and are OBSERVED. They cannot
fail the campaign.
```

---

## 7. Failure-mode discipline

```text
Steps 13-17 do NOT auto-patch failures. If a behavior test
surfaces:

  - confusing output
  - awkward UX
  - missing-but-expected feature
  - incorrect behavior

the operator records the finding in the per-topic report and
moves on. The Step 18 / Step 19 triage decides whether the
finding is critical correctness, safety, UX, docs, or deferred.

Step 20 is a hard review gate. No code-modifying fix is applied
without explicit user acceptance of the Step 19 triage plan.

Exception: if a behavior test would damage on-disk state (e.g.,
overwrite the user's session DB), the operator MUST stop and
flag the risk before re-running. The temporary-DB policy
(Section 4) makes this unlikely.
```

---

## 8. Reporting non-goals

```text
Steps 13-17 do NOT produce:

  - a new semantic / language / truth layer
  - a transcript subsystem
  - a multi-profile model
  - a scenario DSL
  - automated regression of /step tick semantics
  - a model-backed default
  - hidden autosave behavior

Steps 13-17 DO produce:

  - per-topic behavior reports
  - explicit "works / awkward / confusing / fails / blocked"
    verdicts per command
  - a Step 18 findings aggregate
  - a Step 19 triage plan
```

---

## 9. Next artifact

```text
PHASE3_11_LIVE_TEST_CORRIGENDA.md   (Step 11)
```

The corrigenda locks:
- which observations are gating vs OBSERVED
- whether per-topic failures block merge
- exact wording of "blocked by environment"
- handling for missing claude / codex binaries
- the exact temporary-DB cleanup contract
