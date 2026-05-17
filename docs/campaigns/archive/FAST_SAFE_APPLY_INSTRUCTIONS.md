# FAST_SAFE_APPLY_INSTRUCTIONS.md

This file records how the Fast Safe Text Interaction campaign should be applied by repo-capable agents.

## Files installed by this PR

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
```

The full campaign sequence is encoded in `CURRENT_CAMPAIGN.md`.

## Branch-first execution

Work should continue from:

```text
campaign/fast-safe-text-interaction
```

Each successful campaign step should be committed and pushed to that branch.

Do not push directly to `main`. Final completed work should be presented as a pull request into `main`.

## Validation before merge

A repo agent should run:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
bash tools/check_all.sh
```

## Expected first follow-up task

The first campaign step is repo-state sync. It should update stale top-level documentation, especially README catalog/version language, before Phase 3.6 planning begins.
