# CURRENT_CAMPAIGN.md — Phase 3.10 Operational Hardening + Persistence Observability + Autosave Campaign

## Status

```text
DRAFT / BRANCH-FIRST / REVIEW-GATED
```

This campaign replaces the completed Phase 3.9 Persistent Session Store campaign.

## Branch

```text
campaign/operational-hardening-observability-autosave
```

## Baseline

```text
Catalog: v0.18
Counts: 201 REQUIRED / 79 STRUCTURAL / 10 NOT-EXERCISED / 12 DEFERRED / 14 OBSERVED
Latest completed campaign: Phase 3.9 Persistent Session Store
Latest audit: PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md PASS
Latest dry run: PHASE3_9_PERSISTENCE_DRY_RUN.md
```

## Required reading

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_9_PERSISTENT_SESSION_STORE_AUDIT.md
PHASE3_9_PERSISTENCE_DRY_RUN.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
```

## Goal

Combine three follow-up tracks into one review-gated campaign:

```text
A. Operational Hardening
B. Persistence Observability
C. Autosave Policy
```

Operational hardening and persistence observability must land before autosave. Autosave is default-off and requires its own review gate before implementation.

## Target command surface

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
```

## Macro sequence

```text
Step 1       Repo-state sync for Phase 3.10
Step 2       Phase 3.10 synthesis
Step 3       Phase 3.10 kickoff
Step 4       Phase 3.10 corrigenda
Step 5       Ops/observability catalog patch plan
Step 6       Review gate A/B
Step 7       Apply accepted ops/observability catalog patch
Step 8       Implement status + verify core
Step 9       Implement read-only summaries + live-vs-saved diff
Step 10      Implement explicit backup command / policy
Step 11      Ops/observability audit
Step 12      Autosave synthesis
Step 13      Autosave kickoff
Step 14      Autosave corrigenda
Step 15      Autosave catalog patch plan
Step 16      Review gate C
Step 17      Apply accepted autosave catalog patch
Step 18      Implement opt-in autosave policy
Step 19      Autosave dry run + audit
Step 20      Integrated Phase 3.10 audit
Step 21      Final PR preparation
```

## Step 1 — Repo-state sync

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md
```

Required validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
bash tools/check_all.sh
```

## Review gates

```text
Step 6: stop unless ops/observability catalog patch plan is accepted.
Step 16: stop unless autosave catalog patch plan is accepted.
```

## Final PR

Open a PR to main titled:

```text
phase3.10: operational hardening, observability, and autosave policy
```

Do not merge without explicit user approval.
