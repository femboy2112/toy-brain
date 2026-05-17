# PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_SYNTHESIS.md

## Purpose

Synthesize the Phase 3.11 Comprehensive Live Behavior Test
campaign before any new test report, runtime change, or catalog
patch lands. This is a planning artifact only. It does not edit
`INVARIANT_CATALOG.md`, `tools/catalog.py`, `brain/_catalog_ids.py`,
`brain/invariants.py`, `brain/ui/`, `brain/llm/`, or any guarded
kernel path.

Phase 3.11 is not a new cognitive layer and not yet a scenario
harness. It is a comprehensive live behavior test campaign whose
job is to determine whether ToyI actually launches, responds,
persists, reloads, autosaves, reports database state, handles
failures, and exposes intelligible behavior when used like a real
operator-facing system.

```text
Status: DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP /
        FINAL-PR / REVIEW-GATED
```

The campaign is evidence-seeking. Successful invariant fixtures
are necessary but not sufficient: a system can have a green
catalog and still mislaunch, mis-display, mis-persist, or behave
in surprising ways when an operator actually drives it. Phase
3.11 closes that gap with repo-local reports, not with new
abstractions.

---

## 1. Baseline

```text
Catalog version:  v0.19
REQUIRED:        212
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         15
Total fixtures:  130

Latest completed campaign:
  Phase 3.10 Operational Hardening + Persistence Observability +
              Autosave Policy   (PASS — Step 11 integrated audit)
Latest merged PR:
  PR #9 phase3.10: operational hardening, observability, and
        autosave policy

Preflight gates at HEAD of campaign/comprehensive-live-behavior-test:
  python3 -m tools.catalog counts            ok / ok / ok
  python3 -m tools.citations verify          100 citations resolve
  python3 -m tools.import_audit              agency.py clean
  python3 -m brain.invariants run            303 rows checked /
                                              213 REQUIRED green /
                                              83 STRUCTURAL green /
                                              7 OBSERVED pass /
                                              0 gate failures
  bash tools/check_all.sh                    All checks passed
```

---

## 2. Why live behavior testing follows Phase 3.10

Phase 3.9 + 3.10 gave the operator a substantially more powerful
surface:

```text
- /save-session / /load-session                 explicit persistence
- --session-db PATH                              session DB selection
- /session-status                                live session + DB pointer
- /db-status / /db-verify                        DB pointer + invariant verify
- /db-summary / /profile-summary /
  /stream-db-summary / /db-diff                  read-only saved-state inspection
- /db-backup                                     byte-faithful explicit copy
- /autosave-status / /autosave-enable /
  /autosave-disable                              opt-in autosave policy
- --autosave-mode {off, after-successful-mutation}
                                                 startup autosave selection
```

What Phase 3.9 + 3.10 did NOT test, and what the existing
fixtures cannot ever test:

```text
- whether `python3 -m brain.ui` actually launches and produces a
  usable curses surface on a real terminal
- whether `--print-once` and `--check-terminal` print what an
  operator can read
- whether typing /stream / /stream-promote / /step in order
  produces coherent profile / MSI / PtCns changes that an
  operator would call "the system is thinking about my input"
- whether persistence round-trips look right when an operator
  manually inspects the reloaded session
- whether autosave silently misbehaves on a slow disk, a missing
  parent directory, a permission error, or a write that lands
  between two read-only commands
- whether DB observability commands tell the truth when the DB
  was modified by a separate process between two calls
- whether the offline LLM mode produces deterministic,
  intelligible behavior under realistic operator pacing
- whether the mock LLM mode does anything that resembles a real
  classification trace
- whether the claude-cli / codex-cli paths fail closed cleanly
  when the executable is missing, the auth is missing, or the
  subprocess is killed mid-call
- whether any of the surfaces above produce confusing output,
  bad ergonomics, or operator-incomprehensible status text
```

A static catalog cannot catch ergonomic, latency, layout, or
text-rendering problems. A scenario harness is also too heavy a
tool to begin with: a scenario DSL would freeze a current design
that has not yet been exercised by a human operator. The right
intermediate step is a comprehensive live behavior test pass
that produces repo-local evidence reports per surface.

---

## 3. Difference between fixture correctness and operator behavior

The catalog and the runner answer:

```text
Q: Given a fixed input, does the implementation produce the
   shape the catalog requires, and only the shape the catalog
   requires?
```

That is a correctness claim about closed, deterministic
fixtures. It is necessary. It is not what an operator
experiences.

Operator behavior testing answers:

```text
Q: When I launch the system the way the README says to launch
   it, and I issue commands in an order an operator would
   plausibly issue them, do I get output I can read, with
   transitions that make sense, with persistence that survives a
   restart, with autosave that does what its name claims, with
   DB observability that matches the on-disk DB, and with LLM
   runtime modes that fail in bounded local ways when the
   external tool is unavailable?
```

Phase 3.11 separates these axes deliberately. A passing fixture
proves the closed contract holds. A passing behavior report
proves an operator can drive the system the way the catalog and
the audits describe. The two axes are independent. The campaign
ships reports about the second axis without weakening the first.

---

## 4. Test categories

The Step 12 live test matrix is canonical. The expected
categories are:

```text
A. launch tests
   - python3 -m brain.ui --print-once
   - python3 -m brain.ui --check-terminal
   - python3 -m brain.ui                           (interactive)
   - python3 -m brain.ui --session-db <path>
   - python3 -m brain.ui --session-db <path> --load-session
   - python3 -m brain.ui --session-db <path>
       --autosave-mode after-successful-mutation
   - python3 -m brain.ui --llm-mode {offline, mock,
       claude-cli, codex-cli, anthropic-api}

B. offline interaction tests
   - feed raw text via /stream
   - inspect candidates via /stream-summary /
       /stream-candidates
   - promote via /stream-promote
   - /step
   - /state
   - confirm profile / MSI / PtCns reactions are coherent

C. persistence and cold-start tests
   - /save-session
   - restart with --load-session against the same DB
   - /session-status
   - profile / stream / tick restoration matches
   - cold-start without --load-session is a fresh session
   - failed load leaves the live process untouched

D. autosave tests
   - default OFF on every cold start
   - --autosave-mode after-successful-mutation selects the mode
   - /autosave-enable / /autosave-disable behave as documented
   - successful mutation triggers exactly one save
   - read-only command does not trigger autosave
   - failed command does not trigger autosave
   - autosave failure is bounded local UI status
   - autosave never blocks tick() (visual sanity check)

E. DB observability + backup tests
   - /db-status
   - /db-verify
   - /db-summary
   - /profile-summary
   - /stream-db-summary
   - /db-diff
   - /db-backup
   - report accuracy when the DB is modified between calls

F. LLM runtime tests
   - offline                  deterministic
   - mock                     deterministic
   - claude-cli               available / missing-exec / killed
   - codex-cli                available / missing-exec / killed
   - anthropic-api            OBSERVED, only if credentialed and
                              explicitly accepted in corrigenda

G. failure-path tests
   - missing --session-db when --autosave-mode is non-off
   - corrupt DB at load time
   - missing parent directory on /save-session
   - permission denied on /db-backup destination
   - missing external executable for claude-cli / codex-cli
   - subprocess timeout for claude-cli / codex-cli

H. UX / readability tests
   - line-wrapping
   - status pane truncation
   - error messages are bounded and local
   - command echo / status pane / log pane separation is legible
   - help output is up-to-date with the current verb set
```

Each report is a Markdown artifact under
`PHASE3_11_*_REPORT.md`, produced in Steps 13-17.

---

## 5. Non-goals

Phase 3.11 does not authorize:

```text
- a new semantic interpretation layer.
- a new long-term memory model.
- a new multi-profile system.
- a scenario DSL.
- a transcript subsystem unless a test-report step proves it is
  required to capture behavior reproducibly. Even then, the
  proposal must be deferred to a follow-up campaign unless an
  explicit review gate accepts it inside Phase 3.11.
- direct tick() semantic changes.
- model-backed behavior as default.
- hidden autosave behavior (the Phase 3.10c contract is
  preserved).
- a new save_session helper.
- a new persistence schema bump.
- a new command verb beyond what Codex CLI requires (Track A may
  add CLI flags, not new operator verbs).
- bypassing the closed parser verb set inherited from earlier
  phases.
- a `--llm-mode` value that is not in the locked finite set.
- network calls inside standard fixtures.
- real LLM access inside standard fixtures.
- pickle / shelve / marshal / dill / cloudpickle / joblib / atexit
  / signal / threading / asyncio / curses-callback writes to the
  session DB.
```

Behavior reports may surface UX or ergonomic issues. The Step 19
triage plan classifies them. Only critical correctness or
safety/invariant fixes are eligible for in-campaign correction at
the Step 20 gate. UX work moves to a later campaign unless
explicitly approved.

---

## 6. Risk of discovering uncomfortable behavior

This is the most important section of this synthesis.

Phase 3.11 is the first campaign whose deliverables are
deliberately not-fixture-shaped. A behavior report may say things
like:

```text
- "running /stream with a long sentence drops mid-word in the
  candidates pane"
- "promotion accepts a candidate but the profile pane does not
  visibly update until the next /step"
- "--load-session against a DB written by a slightly different
  schema fails closed but the status text is a 200-char dump"
- "autosave fires correctly after /step but the status pane
  reports last_attempt_at in UTC while the rest of the UI uses
  local time"
- "claude-cli mode prints raw subprocess stderr on a single
  missing-executable case"
- "codex-cli is named in the catalog but is not implementable
  because the project has no CodexCLIClient and the LLMClient
  protocol does not yet accept an arbitrary subprocess backend"
- "the offline mode produces identical candidate suggestions
  across distinct prompts in fixtures, which is correct under
  the fixture contract but operator-incomprehensible in live
  use"
- "/db-diff against a backup taken in the same second reports a
  modtime collision that the operator reads as a real diff"
```

None of those are catalog failures. All of them would be valuable
findings. The campaign must not hide them, must not patch around
them silently, and must not promote them to a fixture-shaped fix
without going through the Step 19 triage and the Step 20
correctness gate.

Equally important: the campaign may discover that the system is
better than expected. A "works as expected, surprisingly
operator-friendly" finding is also evidence. Reports must be
specific about what was actually observed, not aspirational about
what the design intends.

The behavior reports should be read as a snapshot of the
post-Phase-3.10 state. They are not a verdict on the system's
ultimate value. They are the empirical record that future
campaigns will reference when they decide what to build next.

---

## 7. Codex CLI requirement

Phase 3.11 must add `codex-cli` as an explicit LLM runtime option
target before the live test matrix is considered complete.

Target spelling unless corrigenda overrides it:

```text
codex-cli
```

Candidate CLI:

```bash
python3 -m brain.ui --llm-mode codex-cli
```

The campaign must decide whether `codex-cli` is:

```text
A. implemented in Phase 3.11 as a real LLMClient-compatible
   backend, or
B. cataloged as a required follow-up discovered by the behavior
   test campaign.
```

Preferred path: implement it behind the existing `LLMClient`
protocol if it can be done without broadening the runtime
boundary. The Step 3 Codex CLI synthesis must determine which of
A or B is reachable inside this campaign's file budget without
violating any of the hard constraints below.

Hard constraints:

```text
offline remains default
codex-cli is explicit opt-in
missing executable / auth fails before session launch with
  bounded local error
deterministic tests do not require real Codex access
real Codex CLI smoke is OBSERVED/manual
selected client enters through existing tick(..., client, ...)
  seam
no second classification path
no hidden network/API path in standard fixtures
no codex-cli value appears in the accepted `--llm-mode` set
  until the catalog patch plan binds it
```

The Step 4 kickoff lists likely design targets (LlmRuntimeMode
member, optional CodexCLIClient or configured wrapper, executable
field, optional timeout field, optional executable CLI flag). The
Step 5 corrigenda locks every choice. The Step 6 catalog patch
plan binds the row family and the count deltas. The Step 7
review gate A stops the campaign until the plan is accepted.

The campaign must NOT widen the runtime boundary by:

```text
- introducing a new top-level classification pipeline
- introducing a new persistence path keyed on the Codex CLI
  result
- introducing a network fallback when the executable is missing
- bypassing the LLMClient protocol with a side-channel client
- adding a long-lived subprocess handle to OperatorSession
- adding a new autosave trigger keyed on Codex CLI results
- adding a new TLICA transition route outside tick()
- adding a new operator verb (Codex CLI is selected via the
  existing --llm-mode flag and is invoked through tick(),
  not via a new verb)
```

If implementation is not reachable inside the file budget, the
Step 5 corrigenda picks option B and the campaign documents the
follow-up explicitly. Either outcome is acceptable; what is not
acceptable is leaving `codex-cli` half-implemented or undefined.

---

## 8. Architectural guardrails (inherited)

Preserve these constraints throughout Phase 3.11. They are
quoted from CURRENT_MISSION.md and CURRENT_CAMPAIGN.md so they
travel with the synthesis:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
loaded state must reconstruct through public builders /
  constructors
loaded state must pass invariants before becoming active
failed load / save / verify / backup / autosave must not corrupt
  live state
tick() remains the only TLICA runtime transition route
/step remains the operator route that calls tick()
offline remains the default LLM mode
model-backed modes remain explicit opt-in
Codex CLI mode must be explicit opt-in
no LLM client, socket, file handle, subprocess handle, callable,
  curses object, or sqlite3.Connection is stored on
  OperatorSession
```

Phase 3.11 reports may surface uncomfortable behavior. The
campaign does not authorize hiding or patching around behavior
findings unless the Step 20 critical correctness patch gate
explicitly accepts a fix.

---

## 9. Likely file budget (planning estimate only)

Reports:

```text
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_SYNTHESIS.md    (this file)
PHASE3_11_CODEX_CLI_RUNTIME_SYNTHESIS.md
PHASE3_11_CODEX_CLI_RUNTIME_KICKOFF.md
PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md
PHASE3_11_CODEX_CLI_RUNTIME_CATALOG_PATCH_PLAN.md
PHASE3_11_LIVE_TEST_KICKOFF.md
PHASE3_11_LIVE_TEST_CORRIGENDA.md
PHASE3_11_LIVE_TEST_MATRIX.md
PHASE3_11_OFFLINE_INTERACTION_REPORT.md
PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
PHASE3_11_BEHAVIOR_FINDINGS.md
PHASE3_11_BUG_UX_TRIAGE_PLAN.md
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_AUDIT.md
```

Optional implementation files (only if Step 7 accepts Track A
implementation):

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/ui/llm_runtime.py
brain/llm/client.py           (CodexCLIClient if accepted)
brain/ui/fixtures/llm_runtime_codex_cli_*.py
README.md
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
```

Excluded unless an accepted plan reopens them:

```text
brain/tlica/
lean_reference/
traces/
scenarios/
brain/tick.py
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
brain/ui/session.py            (unless Codex CLI plumbing requires
                                a minimal addition that the
                                corrigenda locks)
brain/development/
```

The Step 6 Codex CLI catalog patch plan and the Step 12 live
test matrix bind the actual paths. This section is a planning
estimate only.

---

## 10. Stopping rules

The campaign stops at:

```text
- Step 7   Review gate A — Codex CLI
- Step 20  Critical correctness patch gate
- Step 22 / 23 PR open + review (PR not merged without explicit
                   approval)
- any preflight gate failure (counts / citations / import_audit
                              / invariants run / check_all.sh)
- any behavior report that uncovers an immediate
  correctness/safety regression; the Step 19 triage plan then
  routes the finding to the Step 20 gate
```

The campaign does NOT stop for:

```text
- UX-only findings (route to Step 19 triage; defer)
- "works but awkward" findings (route to Step 19 triage; defer)
- "blocked by environment" findings for external LLM CLIs
  (document and continue)
- a finding that an external tool (claude-cli / codex-cli /
  anthropic-api) is not available in the current environment
  (document and continue)
```

---

## 11. Next artifact

```text
PHASE3_11_CODEX_CLI_RUNTIME_SYNTHESIS.md
```

The Codex CLI synthesis (Step 3) should define:

```text
- current accepted --llm-mode values and where they are bound
- proposed codex-cli mode shape (enum member, default,
  parser shape)
- security and availability assumptions (executable presence,
  auth presence, network assumptions)
- executable / auth failure behavior (bounded local UI error
  before session launch)
- manual smoke vs gating fixture distinction (deterministic
  fixtures must not require real Codex access; OBSERVED rows
  cover the real smoke)
- why Codex CLI must not become the default
- why Codex CLI must not bypass the tick(..., client, ...) seam
- the proposed disposition of the campaign's "implement vs
  catalog as follow-up" decision, to be locked in the Step 5
  corrigenda
```

After the Codex CLI synthesis, the kickoff (Step 4) names design
targets, the corrigenda (Step 5) locks the choice, the catalog
patch plan (Step 6) binds the rows, and the Step 7 review gate
A stops the campaign until the plan is accepted.

The live-test track (Steps 10-17) runs after the Codex CLI track
either lands or is explicitly deferred. The behavior reports do
not block on the Codex CLI track's implementation outcome; they
do block on the corrigenda's decision so the LLM runtime behavior
report (Step 17) can record the final accepted set of
`--llm-mode` values.
