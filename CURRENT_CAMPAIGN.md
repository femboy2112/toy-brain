# CURRENT_CAMPAIGN.md — Phase 3.11 Comprehensive Live Behavior Test Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / FINAL-PR / REVIEW-GATED
```

This campaign replaces the completed Phase 3.10 Operational Hardening + Persistence Observability + Autosave Policy campaign.

Phase 3.11 is not a new cognitive layer and not yet a scenario harness. It is a comprehensive live behavior test campaign. Its job is to determine whether ToyI actually launches, responds, persists, reloads, autosaves, reports database state, handles failures, and exposes intelligible behavior when used like a real operator-facing system.

Preferred campaign branch:

```text
campaign/comprehensive-live-behavior-test
```

Preferred final PR title:

```text
phase3.11: comprehensive live behavior test
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

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_10_INTEGRATED_AUDIT.md
PHASE3_10C_AUTOSAVE_AUDIT.md
PHASE3_10C_AUTOSAVE_DRY_RUN.md
PHASE3_10_OPS_OBSERVABILITY_AUDIT.md
PHASE3_10_OPS_OBSERVABILITY_DRY_RUN.md
PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md
PHASE3_9_PERSISTENCE_DRY_RUN.md
PHASE3_TEXT_INTERACTION_DRY_RUN.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
brain/ui/llm_runtime.py
brain/ui/autosave.py
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/session.py
brain/ui/__main__.py
brain/ui/commands.py
brain/ui/command_line.py
```

Then read whichever files the next campaign step names. Do not rely on chat memory; use repo-local files and the current catalog.

---

## Baseline

Expected current state:

```text
Catalog: v0.20
Counts:
  REQUIRED:        214
  STRUCTURAL:       83
  NOT-EXERCISED:     9
  DEFERRED:         12
  OBSERVED:         16
Latest completed campaign: Phase 3.10 Operational Hardening + Persistence Observability + Autosave Policy
Latest integrated audit: PHASE3_10_INTEGRATED_AUDIT.md PASS
Latest merged PR: PR #9
In-flight: Phase 3.11 Comprehensive Live Behavior Test
  Steps 8-12 complete on campaign branch:
    Step 8 Codex CLI catalog patch applied (v0.19 -> v0.20)
    Step 9 Codex CLI runtime option implemented
    Step 10 live test kickoff created
    Step 11 live test corrigenda created
    Step 12 live test matrix created
  Next eligible step: Step 13 launch/offline/basic interaction tests
```

Known live-behavior gap:

```text
The repo has many invariants, fixtures, dry runs, and audits.
It still needs a comprehensive operator-style behavior campaign to see what actually happens in realistic use.
```

---

## Strategic target

Answer these questions with repo-local evidence:

```text
Can the UI launch cleanly?
Can a user feed text, inspect candidates, promote, and step?
Does /step produce coherent profile/MSI/PtCns changes?
Does persistence actually preserve expected state across cold starts?
Does autosave behave unsurprisingly?
Do DB status/verify/summary/diff/backup commands tell the truth?
Do offline and mock LLM modes behave deterministically?
Can Claude CLI and Codex CLI be represented as explicit runtime options?
What happens when external LLM CLI modes are unavailable?
What behavior is confusing, brittle, fake, or ergonomically poor?
```

---

## Required Codex CLI inclusion

This campaign must add `codex-cli` as an explicit LLM runtime option target before the live test matrix is considered complete.

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
A. implemented in Phase 3.11 as a real LLMClient-compatible backend, or
B. cataloged as a required follow-up discovered by the behavior test campaign.
```

Preferred path: implement it behind the existing `LLMClient` protocol if it can be done without broadening the runtime boundary.

Hard constraints:

```text
offline remains default
codex-cli is explicit opt-in
missing executable/auth fails before session launch with bounded local error
deterministic tests do not require real Codex access
real Codex smoke is OBSERVED/manual
selected client enters through existing tick(..., client, ...) seam
no second classification path
no hidden network/API path in standard fixtures
```

---

## Test surface

Commands and modes to exercise:

```text
/stream
/stream-summary
/stream-candidates
/stream-promote
/step
/state
/save-session
/load-session
/session-status
/db-status
/db-verify
/db-summary
/profile-summary
/stream-db-summary
/db-diff
/db-backup
/autosave-status
/autosave-enable
/autosave-disable
```

Launch surfaces to exercise:

```bash
python3 -m brain.ui --print-once
python3 -m brain.ui --check-terminal
python3 -m brain.ui
python3 -m brain.ui --session-db <path>
python3 -m brain.ui --session-db <path> --load-session
python3 -m brain.ui --session-db <path> --autosave-mode after-successful-mutation
python3 -m brain.ui --llm-mode offline
python3 -m brain.ui --llm-mode mock
python3 -m brain.ui --llm-mode claude-cli
python3 -m brain.ui --llm-mode codex-cli
```

External LLM modes are OBSERVED/manual unless the campaign explicitly accepts a deterministic fixture strategy.

---

## Non-goals

```text
no new semantic interpretation layer
no new long-term memory model
no new multi-profile system
no scenario DSL yet
no transcript subsystem yet unless a test-report step proves it is needed
no direct tick() semantic changes
no model-backed behavior as default
no hidden autosave behavior
```

---

## Macro sequence

```text
Step 1       Repo-state sync for Phase 3.11
Step 2       Comprehensive behavior test synthesis
Step 3       Codex CLI runtime option synthesis
Step 4       Codex CLI runtime option kickoff
Step 5       Codex CLI runtime option corrigenda
Step 6       Codex CLI catalog patch plan
Step 7       Review gate A — Codex CLI
Step 8       Apply accepted Codex CLI catalog patch
Step 9       Implement accepted Codex CLI runtime option
Step 10      Live test kickoff
Step 11      Live test corrigenda
Step 12      Live test matrix
Step 13      Execute launch/offline/basic interaction tests
Step 14      Execute persistence/cold-start tests
Step 15      Execute autosave tests
Step 16      Execute DB observability/backup tests
Step 17      Execute LLM runtime tests: offline, mock, Claude CLI, Codex CLI, optional API
Step 18      Behavior findings report
Step 19      Bug/UX triage plan
Step 20      Critical correctness patch gate
Step 21      Apply only accepted critical fixes, if any
Step 22      Final comprehensive behavior audit
Step 23      Final PR preparation
```

---

# Step 1 — Repo-state sync for Phase 3.11

Purpose: install Phase 3.11 as current and record Phase 3.10 completion.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
PHASE3_11_COMPREHENSIVE_LIVE_BEHAVIOR_TEST_ROADMAP.md
```

Required work:

```text
update mission/campaign files to v0.19 baseline
state Phase 3.10 is complete and merged
state Phase 3.11 is current
add or refresh the Phase 3.11 roadmap
preserve branch-first workflow
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

# Step 2 — Comprehensive behavior test synthesis

Create:

```text
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_SYNTHESIS.md
```

Required content:

```text
v0.19 baseline
why live behavior testing follows Phase 3.10
difference between fixture correctness and operator behavior
test categories
non-goals
risk of discovering uncomfortable behavior
Codex CLI requirement
next artifact: Codex CLI synthesis
```

Commit and push.

---

# Step 3 — Codex CLI runtime option synthesis

Create:

```text
PHASE3_11_CODEX_CLI_RUNTIME_SYNTHESIS.md
```

Purpose:

```text
Define why codex-cli belongs in the LLM runtime set and how it must fit the existing LLMClient/tick seam.
```

Required content:

```text
current accepted modes
proposed codex-cli mode
security/availability assumptions
executable/auth failure behavior
manual smoke vs gating fixture distinction
why Codex CLI must not become default
why Codex CLI must not bypass tick/client seam
```

Commit and push.

---

# Step 4 — Codex CLI runtime option kickoff

Create:

```text
PHASE3_11_CODEX_CLI_RUNTIME_KICKOFF.md
```

Likely design targets:

```text
LlmRuntimeMode.CODEX_CLI
CodexCLIClient or configured wrapper if accepted
codex_cli_executable field
codex_cli_timeout_seconds field if needed
--llm-mode codex-cli
--llm-codex-cli-executable <path> if accepted
```

Hard rule:

```text
Do not implement until catalog patch plan is accepted.
```

Commit and push.

---

# Step 5 — Codex CLI runtime option corrigenda

Create:

```text
PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md
```

Lock:

```text
mode spelling
executable field
auth/tool availability behavior
whether Codex CLI gets a new backend class or a generic subprocess-backed CLI client
fixture strategy that does not require real Codex access
OBSERVED/manual real Codex smoke
row family name
file budget
```

Commit and push.

---

# Step 6 — Codex CLI catalog patch plan

Create:

```text
PHASE3_11_CODEX_CLI_RUNTIME_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-CODEXCLI-* or I-LLMTOG-* continuation
```

Likely rows:

```text
codex-cli is a finite accepted llm mode
codex-cli is explicit opt-in
missing executable fails before launch
factory returns LLMClient-compatible client
standard fixtures do not require real Codex access
selected client enters through existing tick client seam
real Codex CLI smoke is OBSERVED/manual
```

Stop at review gate.

---

# Step 7 — Review gate A — Codex CLI

Stop unless Step 6 is explicitly accepted.

---

# Step 8 — Apply accepted Codex CLI catalog patch

Allowed files depend on accepted plan, likely:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional marker files only if accepted.

Commit and push after count validation.

---

# Step 9 — Implement accepted Codex CLI runtime option

Allowed files per accepted plan, likely:

```text
brain/ui/llm_runtime.py
brain/llm/client.py
brain/ui/fixtures/llm_runtime_codex_cli_*.py
brain/invariants.py
README.md
```

Commit and push after targeted and full validation.

---

# Step 10 — Live test kickoff

Create:

```text
PHASE3_11_LIVE_TEST_KICKOFF.md
```

Define test execution style:

```text
manual observed tests
scripted subprocess tests if feasible
expected report format
temporary DB policy
external tool availability policy
real LLM smoke policy
```

Commit and push.

---

# Step 11 — Live test corrigenda

Create:

```text
PHASE3_11_LIVE_TEST_CORRIGENDA.md
```

Lock:

```text
which tests are gating
which tests are OBSERVED/manual
whether failures create bugs or block merge
how to report confusing behavior
how to handle unavailable Codex/Claude executables
```

Commit and push.

---

# Step 12 — Live test matrix

Create:

```text
PHASE3_11_LIVE_TEST_MATRIX.md
```

Matrix sections:

```text
launch tests
offline interaction tests
persistence tests
autosave tests
DB observability tests
backup tests
LLM runtime tests
failure-path tests
UX/readability tests
```

Stop for review only if the matrix adds implementation beyond reports.

---

# Step 13 — Execute launch/offline/basic interaction tests

Create:

```text
PHASE3_11_OFFLINE_INTERACTION_REPORT.md
```

Test:

```text
--print-once
--check-terminal
fresh launch where feasible
/stream
/stream-summary
/stream-candidates
/stream-promote
/step
/state
```

Report actual behavior. Do not sanitize awkward results.

Commit and push.

---

# Step 14 — Execute persistence/cold-start tests

Create:

```text
PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
```

Test:

```text
/save-session
restart with --load-session
/session-status
profile/stream/tick restoration
```

Commit and push.

---

# Step 15 — Execute autosave tests

Create:

```text
PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
```

Test:

```text
default off
enable after-successful-mutation
successful mutation saves
read-only command does not save
failed command does not save
disable works
failure injection if feasible
```

Commit and push.

---

# Step 16 — Execute DB observability/backup tests

Create:

```text
PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
```

Test:

```text
/db-status
/db-verify
/db-summary
/profile-summary
/stream-db-summary
/db-diff
/db-backup
```

Commit and push.

---

# Step 17 — Execute LLM runtime tests

Create:

```text
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
```

Test:

```text
offline
mock
claude-cli availability/failure behavior
codex-cli availability/failure behavior
anthropic-api only if credentialed and explicitly accepted
real external CLI smoke only if available
```

Real external LLM/CLI smoke is OBSERVED/manual by default.

Commit and push.

---

# Step 18 — Behavior findings report

Create:

```text
PHASE3_11_BEHAVIOR_FINDINGS.md
```

Classify:

```text
works as expected
works but awkward
confusing output
incorrect behavior
missing feature
blocked by environment
should be next campaign
```

Commit and push.

---

# Step 19 — Bug/UX triage plan

Create:

```text
PHASE3_11_BUG_UX_TRIAGE_PLAN.md
```

Classify findings:

```text
critical correctness
safety/invariant
operator UX
documentation
deferred enhancement
```

Commit and push.

---

# Step 20 — Critical correctness patch gate

Stop if the triage plan proposes code changes.

Only critical correctness/safety fixes may proceed in this campaign. UX or feature improvements move to a later campaign unless explicitly approved.

---

# Step 21 — Apply accepted critical fixes, if any

Allowed files depend on the accepted triage plan.

Commit and push after targeted and full validation.

---

# Step 22 — Final comprehensive behavior audit

Create:

```text
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_AUDIT.md
```

Audit:

```text
Codex CLI option status
launch behavior
offline behavior
persistence behavior
autosave behavior
DB observability/backup behavior
LLM runtime behavior
critical fixes if any
full gate
recommended next mission
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

# Step 23 — Final PR preparation

Open a PR to main with title:

```text
phase3.11: comprehensive live behavior test
```

PR body must include:

```text
completed steps
validation results
Codex CLI runtime option status
behavior findings summary
critical fixes if any
remaining deferred work
confirmation main was not pushed directly during campaign execution
confirmation PR is not merged
```

Do not merge.
