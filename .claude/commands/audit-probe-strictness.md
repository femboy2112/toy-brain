---
description: Audit probe modules for graceful-pass acceptance patterns. Wraps tools/developmental_profile_audit.py --audit-only and dispatches to the brain-probe-strictness-auditor agent if available.
---

# /audit-probe-strictness

Audit probe modules for graceful-pass acceptance that should be
surfaced via a `_strict` counter.

## What this does

1. Runs `python3 -m tools.developmental_profile_audit --audit-only`
   on the configured probe set.
2. Saves the raw findings to `/tmp/probe_strictness_audit.md`.
3. If the `brain-probe-strictness-auditor` subagent is available,
   dispatches to it for manual review and findings cleanup.
4. Suggests next steps (which probes need a strict counter added).

## Invocation

```text
/audit-probe-strictness
```

Optional:

```text
/audit-probe-strictness --probes <comma_separated_module_names>
```

Default probes:

```text
proto_speech_acquisition,
curriculum_consolidation_probe,
active_hypothesis_probe,
osmotic_learning_probe,
worldlet_feedback_bridge
```

## Implementation

Run this bash block in the repo root:

```bash
PROBES="${1:-proto_speech_acquisition,curriculum_consolidation_probe,active_hypothesis_probe,osmotic_learning_probe,worldlet_feedback_bridge}"

python3 -m tools.developmental_profile_audit \
    --audit-only \
    --probes "$PROBES" \
    --format markdown \
    > /tmp/probe_strictness_audit.md \
    2>/tmp/audit_stderr.log

echo "=== Audit findings ==="
cat /tmp/probe_strictness_audit.md

if [ -s /tmp/audit_stderr.log ]; then
    echo ""
    echo "=== stderr ==="
    cat /tmp/audit_stderr.log
fi
```

After the audit:

1. Review every finding manually. The script identifies graceful-pass
   *candidates*; a human (or planner agent) decides the canonical
   disposition for each.
2. If `brain-probe-strictness-auditor` is available, dispatch to it
   with the raw findings as input.
3. The final output should be a fully-populated
   `docs/campaigns/phase3_33/PHASE3_33_STRICTNESS_AUDIT_PLAN.md`
   with no `<FILL IN>` placeholders.

## Output

The command's stdout is the raw audit findings in Markdown. The
findings table at the top is a starting point; the per-probe
finding entries (further down) need human review.

## Hard limits

- Read-only. This command does not modify probe modules.
- The audit only documents what's there; it doesn't recommend
  changes.
- Decisions about which strict counters to add live in the audit
  plan document, not in the probe modules themselves.
