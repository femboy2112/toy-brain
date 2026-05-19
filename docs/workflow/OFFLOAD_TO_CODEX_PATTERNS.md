# OFFLOAD_TO_CODEX_PATTERNS.md

## Purpose

Concrete patterns for delegating work to Codex (via the
`chatgpt-codex-orchestrator` agent) when the work is structurally
repetitive, has well-defined inputs, and produces independent outputs.

The goal is to keep the Claude Code conversation focused on
high-judgment work (architectural decisions, cross-step
synthesis) and offload structurally-bounded fan-out work to lower-
context Codex sub-conversations.

## When to offload

Offload to Codex when ALL of these hold:

1. The work is structurally repetitive (N similar tasks).
2. Each task has a small, well-defined input.
3. Each task's output is independent of other tasks' outputs.
4. The total token cost of doing it in Claude Code would exceed
   ~50K (saving real conversation budget).
5. The task can be validated mechanically after completion.

Do NOT offload to Codex when:

- The work requires reading a large slice of the codebase.
- The work requires reasoning across multiple campaign decisions.
- The task is small enough that Codex setup cost exceeds Claude
  Code execution cost.
- The work involves novel architectural decisions (those require the
  campaign's full context).

## Phase 3.34 fan-out: predicate authoring (9 axes × 16 predicates)

This is the canonical example of when to offload.

### Setup

In the Claude Code campaign conversation, after the reference axis
(PROTO_SPEECH_COMBINATION) is fully authored:

```text
ROUND 1: dispatch 5 Codex tasks in parallel (one per axis):
  - PROTO_SPEECH_BABBLE
  - PROTO_SPEECH_STABLE_SINGLE
  - PROTO_SPEECH_TRANSFER
  - PATTERN_TRANSFER
  - OSMOTIC_IMPRINTING

ROUND 2: dispatch the remaining 4:
  - ACTIVE_PROBE
  - CURRICULUM_RETENTION
  - WORLDLET_FEEDBACK
  - REFUSAL_SAFETY
```

(Split into two rounds because Codex's parallel-task limit is
typically 5-8 at a time; check the orchestrator's config.)

### Prompt template (per axis)

```text
You are authoring the certification and falsification predicates for
the <AXIS_NAME> axis of the toy-brain developmental progression
profile. ToyI is a bounded structural state machine; predicates
read probe reports and return bool.

INPUTS (pasted below):
1. PHASE3_34_PREDICATE_TEMPLATE.md (full file)
2. The semantic row for <AXIS_NAME> from PHASE3_34_AXIS_AND_BAND_SPEC.md
3. The relevant ProbeReport fields (the probe module names + the
   integer counter fields they expose)
4. ADR-002-bands-generic-not-per-axis.md (excerpt)
5. ADR-005-predicate-monotonicity.md (excerpt)

TASK:
- Author 16 predicates for the <AXIS_NAME> axis:
  cert_<AXIS_ABBREV>_B00 through cert_<AXIS_ABBREV>_B07
  fals_<AXIS_ABBREV>_B00 through fals_<AXIS_ABBREV>_B07
- Each predicate takes `reports: tuple[ProbeReport, ...]` and returns
  bool.
- Use the helper functions _proto_speech_report, _curriculum_report,
  _active_hypothesis_report, _osmotic_report, and _i from the
  template. DO NOT import probe modules directly.
- Follow the PSC reference axis structure exactly.
- Ensure monotonicity: cert is non-decreasing in band index reversed,
  fals is non-increasing in band index.
- Where a band is unreachable on this axis (e.g., REFUSAL_SAFETY's
  B05_COMBINES has no meaning), return cert=False and fals=True for
  that band.

OUTPUT:
- A single Python code block with the 16 predicates + the sub-table
  fragment (an entry for each band in the axis's predicate map).
- No prose outside the code block.
- No imports beyond what's in the template.

VALIDATION (you must trace through these synthetic fixtures):
- All-zeros fixture: most bands' cert should be False; only B00.
- Strong-on-this-axis fixture: highest reachable band's cert should
  be True.
- Strong-on-all-axes fixture: this axis's cert should be at the
  highest reachable band; other axes' cert tested separately.

After authoring, mentally walk through the cert values
[cert(B00), ..., cert(B07)] and confirm:
- The True-False transition happens AT MOST ONCE (cert is monotonic).
- The fals values are also monotonic in the opposite direction.
```

### Merging Codex output back

The Claude Code conversation:

1. Collects all 9 axes' code blocks.
2. Pastes them into `predicate_table.py` after the reference axis.
3. Updates `PREDICATE_TABLE` to include all 10 axes' sub-tables.
4. Runs `python3 -m tools.verify_predicate_monotonicity`.
5. If any axis violates monotonicity, re-dispatch that single axis
   to Codex with the violation message as additional input.

### Token savings

In-Claude authoring: ~10K context per axis × 9 axes = ~90K tokens of
context churn (re-loading the template and the axis spec for each).

Codex fan-out: ~10K context per axis, but each in a SEPARATE
conversation. Claude Code only pays ~5K to dispatch and ~3K to
collect each result. Net: ~70K saved.

## Phase 3.33 fan-out: strict counter authoring (4 probes)

Smaller fan-out, less worth offloading, but still applicable:

```text
ROUND 1: dispatch up to 4 Codex tasks (one per affected probe).
Each task adds a strict counter field to the probe's report
dataclass and the corresponding compute step.

Tasks:
  - proto_speech_acquisition: stable_combination_count_strict
  - proto_speech_acquisition: transfer_success_count_strict
    (these two CAN be merged into one task since they're in the same module)
  - curriculum_consolidation_probe: <axis-specific strict counter>
  - active_hypothesis_probe: <axis-specific strict counter>
  - osmotic_learning_probe: <axis-specific strict counter>
```

Token savings smaller (~20K saved) but pattern is the same.

## Phase 3.35 fan-out: not usually applicable

Phase 3.35+ campaigns target a single axis. The mechanism change is
typically a single concentrated edit, not a fan-out. Don't try to
parallelize Phase 3.35 work; the campaign is small enough.

## Codex output validation patterns

Every Codex output should be validated mechanically before being
merged. Recommended:

### For predicate authoring (Phase 3.34 Step 4)

```bash
# After merging Codex's output:
python3 -m tools.verify_predicate_monotonicity --axis <AXIS_NAME>
```

If the check fails, the merged predicates are reverted and the axis
is re-dispatched to Codex.

### For strict counter authoring (Phase 3.33 Step 5)

```bash
# After merging Codex's output:
python3 -m pytest tests/test_<probe>.py
python3 -m brain.development.benchmark_battery --axes <relevant>
```

If the test or benchmark fails, the merged counter is reverted.

### For probe behavior changes (Phase 3.35)

DON'T offload these to Codex. Probe behavior changes require the
full campaign context (the mechanism's parameter choice, the
regression gate scoping, the catalog row plan).

## Anti-patterns

### Don't offload "design this axis's prerequisite"

Cross-axis dependencies require the full DAG context. Author them in
Claude Code, not Codex.

### Don't offload "decide which mechanism to use"

Mechanism selection requires reading the profile and reasoning about
the substrate's current state. Author in Claude Code.

### Don't offload "audit this for non-claim discipline"

The non-claim discipline is highly contextual; what's "claim-clean"
depends on the surrounding text. Audit in Claude Code.

### Don't dispatch Codex tasks without a clear merge plan

Always know up-front how you'll merge the Codex outputs back into
the main codebase. If the merge plan is unclear, the fan-out isn't
ready.

## Tracking dispatched tasks

In long campaigns with multiple Codex fan-outs, keep a running list
in the campaign's `CURRENT_CAMPAIGN.md`:

```markdown
## Outstanding Codex dispatches

| Axis | Dispatched | Returned | Merged | Validated |
|---|---|---|---|---|
| PROTO_SPEECH_BABBLE | 2026-01-20 14:30 | 14:45 | 14:50 | OK |
| PROTO_SPEECH_STABLE_SINGLE | 2026-01-20 14:30 | 14:42 | 14:50 | OK |
| PATTERN_TRANSFER | 2026-01-20 14:30 | 14:50 | 14:52 | OK |
| OSMOTIC_IMPRINTING | 2026-01-20 14:30 | pending | - | - |
| ACTIVE_PROBE | 2026-01-20 15:00 | 15:08 | 15:15 | FAIL → redispatched |
```

This makes parallel Codex work tractable in long-running campaigns.
