Read `CLAUDE.md`, then execute the repo-local current mission exactly as if the
user said `go`.

Required source of truth:

1. `CURRENT_MISSION.md`
2. Every required-read file named by `CURRENT_MISSION.md`
3. `CURRENT_CAMPAIGN.md` when referenced by the mission

Use campaign state detection to choose the next incomplete eligible step. Run
preflight first, obey allowed-file and guardrail sections exactly, validate as
specified, commit and push successful step results when files changed, and stop
at explicit review gates, failures requiring user judgment, or campaign
completion.

Use `python3 -m ...` for Python module commands even if copied instructions say
`python -m ...`.
