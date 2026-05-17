# PHASE3_12_COHERENT_I_LOOP_KICKOFF.md

## Purpose

Define how Phase 3.12 will execute its first behavior observatory over the existing safe operator route.

This is a planning artifact. It does not edit source code, fixtures, catalog rows, scenarios, traces, or runtime semantics.

## Execution style

Use scripted in-process operator dispatch where possible:

```python
LocalCommandLine.parse(line)
OperatorSession.dispatch(command, client=OfflineStandInClient())
```

The observatory must drive the same typed commands that the operator path exposes:

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
```

Do not call private helpers or mutate `BrainState` directly.

## LLM policy

```text
default: OfflineStandInClient
allowed deterministic alternative: MockClient with explicit responses
not required: anthropic-api, claude-cli, codex-cli
real external LLM smoke: OBSERVED/manual only and not part of Step 6 gates
```

## Temporary helper policy

Temporary helpers may live under `/tmp/phase3_12_*`. They must be:

```text
deterministic
local
no network
no real LLM call
no repo writes except explicit report artifact
not committed unless a later step explicitly allows helper files
```

## Input families

### Repetition

Feed repeated motifs:

```text
alpha alpha alpha
alpha alpha alpha
alpha alpha alpha
```

Expected observation:

```text
stream chunks accepted
promotion candidates bounded
repetition visible in stream summaries or candidate evidence
no unbounded growth
```

### Alternation

Feed alternating motifs:

```text
alpha beta alpha beta
alpha beta alpha beta
```

Expected observation:

```text
alternation distinguishable from pure repetition in recorded chunk text / features
```

### Novelty after repetition

Feed a novel item after repeated motifs:

```text
gamma arrives after alpha repetition
```

Expected observation:

```text
novel item does not corrupt existing state
candidate ids remain bounded and distinct
```

### Contradiction pressure

Feed structurally conflicting text, without semantic truth claims:

```text
operator says door=open
operator says door=closed
```

Expected observation:

```text
system records bounded text evidence
no direct truth adjudication
no direct PtCns mutation before explicit promotion/tick
```

### Saturation

Feed many repeated chunks or a near-boundary chunk length.

Expected observation:

```text
history and candidates remain bounded
errors are local and bounded if input exceeds limits
```

### Cold-start continuity

Save after interaction, load into a fresh session, then compare:

```text
tick_counter
profile domain
MSI contents
stream chunk count
stream candidate count
latest status/report evidence
```

Expected observation:

```text
saved and loaded state match expected fields
failed load preserves live session
```

## Verdict vocabulary

Use:

```text
works
awkward
confusing
fails
missing
blocked by env
ORS skipped
```

## Report artifact

Step 6 creates:

```text
PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md
```

Required sections:

```text
Purpose
Environment
Method
Observation table
Metric summary
Findings classification
Next-campaign recommendations
```

## Stop conditions

Stop and report if:

```text
standard gates fail before observations
existing /stream -> /step route corrupts state
save/load corrupts or truncates DB
COGITO_ID reservation is violated
helper requires real LLM or network to continue
```
