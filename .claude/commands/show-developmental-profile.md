---
description: Project and display the current developmental progression profile. Shows each (axis, band) assignment with rationale and cited evidence rows.
---

# /show-developmental-profile

Project the current developmental progression profile and display
each axis's band assignment.

## What this does

1. Runs the projector on the current probe outputs.
2. Displays the profile in a readable table format.
3. Shows the cited evidence rows for each assignment.
4. Optionally shows the next-target proposal (with `--with-next-target`).

## Invocation

```text
/show-developmental-profile
/show-developmental-profile --with-next-target
/show-developmental-profile --format json
```

## Implementation

Run this bash block:

```bash
python3 -c "
from brain.development.probe_report_protocol import collect_probe_reports
from brain.development.developmental_progression_profile import (
    project_developmental_progression_profile,
    select_next_progression_target,
)
import sys

reports = collect_probe_reports()
profile = project_developmental_progression_profile(reports)

# Format selection
fmt = 'table'
if '--format' in sys.argv:
    fmt = sys.argv[sys.argv.index('--format') + 1]

if fmt == 'json':
    import json
    out = {
        'profile_digest': profile.profile_digest_hex16,
        'forbidden_audit_clean': profile.forbidden_audit_clean,
        'assignments': [
            {
                'axis': a.axis.value,
                'band': a.band.value,
                'evidence_digest': a.evidence_digest_hex16,
                'cited_rows': list(a.cited_evidence_rows),
                'rationale': a.rationale_summary,
            } for a in profile.assignments
        ],
    }
    if '--with-next-target' in sys.argv:
        nt = select_next_progression_target(profile)
        out['next_target'] = {
            'axis': nt.axis.value,
            'current_band': nt.current_band.value,
            'target_band': nt.target_band.value,
            'mechanism': nt.recommended_mechanism.value,
            'rationale': nt.rationale_summary,
            'cited_rows': list(nt.cited_evidence_rows),
        }
    print(json.dumps(out, indent=2))
else:
    print(f'Profile digest: {profile.profile_digest_hex16}')
    print(f'Audit clean:    {profile.forbidden_audit_clean}')
    print()
    print(f'{\"Axis\":<32} {\"Band\":<24} {\"Rationale\"}')
    print(f'{\"-\"*32} {\"-\"*24} {\"-\"*40}')
    for a in profile.assignments:
        print(f'{a.axis.value:<32} {a.band.value:<24} {a.rationale_summary[:40]}...')
    if '--with-next-target' in sys.argv:
        nt = select_next_progression_target(profile)
        print()
        print('Next progression target:')
        print(f'  axis:         {nt.axis.value}')
        print(f'  current band: {nt.current_band.value}')
        print(f'  target band:  {nt.target_band.value}')
        print(f'  mechanism:    {nt.recommended_mechanism.value}')
        print(f'  rationale:    {nt.rationale_summary}')
        print(f'  cites:        {\", \".join(nt.cited_evidence_rows)}')
"
```

## When to use

- At the start of a campaign, to see the current profile state.
- After Phase 3.33 strict counter additions, to see how strict-vs-
  graceful affects band assignments.
- After Phase 3.34 lands, as a sanity check the projector is working.
- Before opening a Phase 3.35+ PR, to confirm the targeted axis's
  band actually moved.

## Hard limits

- Read-only. This command does not modify the repo.
- The projector is deterministic; running it twice produces the same
  output.
- No real model calls; no LLM; no network.
