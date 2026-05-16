# PHASE3_8B_LLM_TOGGLE_AMENDMENT.md

## Purpose

Add a future subcampaign for an explicit model-client toggle in the operator UI.

The completed text interaction loop should support two testing modes:

```text
offline  — default deterministic client
model    — explicit opt-in client selected by the user
```

The default remains offline. The model-backed path must reuse the existing `LLMClient` seam and feed the selected client through the existing `tick(..., client, ...)` argument.

## Placement

Insert this subcampaign after stream command implementation and before the final Phase 3.8 audit.

Recommended steps:

```text
Step 24A — LLM toggle synthesis
Step 24B — LLM toggle kickoff
Step 24C — LLM toggle corrigenda
Step 24D — LLM toggle catalog patch plan
Step 24E — Apply accepted catalog patch
Step 24F — Implement toggle
Step 24G — Toggle audit
```

## Required properties

```text
offline mode remains default
model mode is explicit opt-in
accepted modes are finite and closed
client construction returns an LLMClient-compatible object
selected client enters through the existing tick client parameter
standard fixtures remain deterministic
model-backed smoke checks are OBSERVED/manual, not REQUIRED
```

Likely modes:

```text
offline
mock
anthropic-api
claude-cli
```

Suggested command line:

```bash
python3 -m brain.ui --llm-mode offline
python3 -m brain.ui --llm-mode anthropic-api
python3 -m brain.ui --llm-mode claude-cli
```

Likely future files:

```text
brain/ui/llm_runtime.py
brain/ui/__main__.py
brain/ui/fixtures/llm_runtime_toggle.py
brain/invariants.py
README.md
```

## Gate verdict

Current review-gate disposition:

```text
PASS WITH REQUIRED AMENDMENT
```

This amendment does not block Phase 3.6. It must be integrated before final interactive testing is considered complete.
