---
description: Propose the next consolidation campaign based on the current developmental progression profile. Wraps tools/propose_next_campaign.py and dispatches to the brain-developmental-planner agent if available.
---

# /next-campaign

Propose the next consolidation campaign.

## What this does

1. Runs `python3 -m tools.propose_next_campaign --format roadmap-stub`
   to compute the canonical proposal.
2. Saves the output to `/tmp/next_campaign_stub.md`.
3. If the `brain-developmental-planner` subagent is available,
   dispatches to it for judgment review.
4. Reports the proposal + judgment to the user.
5. Suggests next steps (which template instructions to follow).

## Invocation

```text
/next-campaign
```

Optional arguments:

```text
/next-campaign --exclude-axis <AXIS_NAME>
/next-campaign --exclude-mechanism <MECHANISM_NAME>
```

## Implementation

Run this bash block in the repo root:

```bash
# 1. Generate the proposal.
python3 -m tools.propose_next_campaign --format roadmap-stub \
    $@ > /tmp/next_campaign_stub.md 2>/tmp/next_campaign_stderr.log

# 2. Show the proposal.
cat /tmp/next_campaign_stub.md

# 3. Show stderr if any.
if [ -s /tmp/next_campaign_stderr.log ]; then
    echo "===== stderr ====="
    cat /tmp/next_campaign_stderr.log
fi
```

After running the command, if a `brain-developmental-planner` agent is
available, invoke it to review the proposal and produce a judgment
paragraph.

If the proposal looks sound, suggest to the user:

```text
Next step: author the roadmap from this stub using
docs/campaigns/phase3_35/PHASE3_35_TEMPLATE_INSTRUCTIONS.md.

The recommended filename is:
PHASE3_<NN>_<AXIS_NAME>_CONSOLIDATION_ROADMAP.md
```

If the proposal recommends `DEFER_PENDING_PREREQUISITES`, suggest:

```text
This proposal defers consolidation pending prerequisites. Consider
re-running with --exclude-axis <THE_DEFERRED_AXIS> to see the next-
best target, OR author a prerequisite-extension campaign for the
blocked axis.
```

## Hard limits

- Read-only. This command does not modify the repo.
- Output is the proposal; the user authors the roadmap.
- The proposer is deterministic; the same repo state always produces
  the same proposal.
