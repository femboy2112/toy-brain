# PHASE3_11_COMPREHENSIVE_LIVE_BEHAVIOR_TEST_ROADMAP.md

## Purpose

Phase 3.11 is a comprehensive live behavior test campaign.

The project now has enough runtime machinery that more feature work is premature. The next question is whether the system actually behaves well when used in realistic operator flows.

This roadmap intentionally comes before a scenario harness or a new cognitive layer.

---

## Baseline

```text
Catalog: v0.19
Counts: 212 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 15 OBSERVED
Latest complete campaign: Phase 3.10 Operational Hardening + Persistence Observability + Autosave Policy
```

Phase 3.10 gave:

```text
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
--autosave-mode
```

Earlier phases gave:

```text
/stream
/stream-summary
/stream-candidates
/stream-promote
/step
/save-session
/load-session
--llm-mode offline
--llm-mode mock
--llm-mode anthropic-api
--llm-mode claude-cli
```

Phase 3.11 must add `codex-cli` as an explicit LLM runtime option target.

---

## Track A — Codex CLI runtime option

Goal:

```text
Add or formally plan codex-cli as an explicit --llm-mode option.
```

Preferred target:

```bash
python3 -m brain.ui --llm-mode codex-cli
```

Rules:

```text
offline remains default
codex-cli is explicit opt-in
missing executable/auth fails before launch
standard fixtures do not require real Codex access
real Codex smoke is OBSERVED/manual
selected client enters through existing tick client seam
```

---

## Track B — Comprehensive live behavior testing

Goal:

```text
Use the system as an operator would and document real behavior.
```

Test categories:

```text
launch
offline interaction
stream promotion
tick integration
persistence and reload
autosave
DB status/verify/summary/diff/backup
LLM runtime modes
failure paths
operator readability
```

---

## Track C — Findings and triage

Goal:

```text
Turn behavior observations into a clear next-action map.
```

Classifications:

```text
works as expected
works but awkward
confusing output
incorrect behavior
blocked by environment
critical correctness fix
deferred enhancement
next campaign candidate
```

---

## Expected reports

```text
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_SYNTHESIS.md
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

---

## Completion condition

The campaign is complete when:

```text
Codex CLI option status is resolved
launch behavior is tested
offline behavior is tested
persistence behavior is tested
autosave behavior is tested
DB observability/backup behavior is tested
LLM runtime modes are tested
behavior findings are documented
critical fixes, if any, are either applied or explicitly deferred
full gate is green
PR is opened and not merged without approval
```
