# CONTEXT_MANAGEMENT_GUIDE.md

## Purpose

Per-phase guidance on what to seed at the start of a fresh
conversation, when to start a new conversation, and rough token
budget estimates so context degradation can be anticipated.

## General principles

1. **One campaign per conversation.** Each of 3.32, 3.33, 3.34, 3.35
   should live in its own Claude Code conversation.

2. **Seed only what's needed.** Don't dump the entire bundle into
   context; read only the files relevant to the current campaign.

3. **Codex offloads should run in their own conversations too.** The
   Codex-side conversation reads ONLY the axis-specific spec and the
   template, not the full bundle.

4. **Pause and reset when responses degrade.** Signs of degradation:
   - Agent re-reads a file you know is in context.
   - Agent forgets an earlier-established constraint (e.g., a locked
     decision).
   - Agent's response repeats itself or gets vague.
   - Agent confuses Phase 3.33's diagnostic scope with Phase 3.35's
     intervention scope.

5. **Use this guide as a checklist.** Mismatch between the listed
   seeds and what the agent actually has loaded is a warning sign
   for token efficiency.

## Phase 3.32: Mainline Reconciliation + ProbeReport

### Seed at start

```text
- README.md                                  (bundle index)
- ADR-001-locked-decisions-D1-D8.md          (locked decisions)
- PHASE3_32_MAINLINE_RECONCILIATION_ROADMAP.md
- docs/campaigns/phase3_32/PHASE3_32_PR_STACK_AUDIT.md
- docs/campaigns/phase3_32/PHASE3_32_PROBE_REPORT_PROTOCOL.md
- CURRENT_MISSION_phase3_32.md (if pre-authored)
- CURRENT_CAMPAIGN_phase3_32.md (if pre-authored)
```

### Files to read on-demand (per step)

```text
Step 5 (protocol authoring):
  - brain/development/proto_speech_acquisition.py (the existing
    ProtoSpeechReport dataclass)
  - brain/development/curriculum_consolidation_probe.py (the
    existing CurriculumProbeReport)
```

### Approx token budget: ~50K (well within Claude Code limits)

## Phase 3.33: Proto-Speech Strict Corrigendum

### Seed at start

```text
- README.md
- ADR-001-locked-decisions-D1-D8.md
- ADR-003-strict-counter-pattern.md
- PHASE3_33_PROTO_SPEECH_STRICT_CORRIGENDUM_ROADMAP.md
- docs/campaigns/phase3_33/PHASE3_33_DESIGN.md
- docs/campaigns/phase3_33/PHASE3_33_STRICTNESS_AUDIT_PLAN.md
- CURRENT_MISSION_phase3_33.md
- CURRENT_CAMPAIGN_phase3_33.md
```

### Files to read on-demand

```text
Step 4 (audit):
  - tools/developmental_profile_audit.py
  - brain/development/proto_speech_acquisition.py
  - brain/development/curriculum_consolidation_probe.py
  - brain/development/active_hypothesis_probe.py
  - brain/development/osmotic_learning_probe.py

Steps 5a-5d (strict counter additions):
  - The probe modules being modified.
  - brain/development/probe_report_protocol.py (the ProbeReport
    contract — must stay typing-compatible).
```

### Approx token budget: ~70K

## Phase 3.34: Developmental Progression Profile

This is the heaviest phase by far. Plan accordingly.

### Seed at start

```text
- README.md
- ADR-001-locked-decisions-D1-D8.md
- ADR-002-bands-generic-not-per-axis.md
- ADR-005-predicate-monotonicity.md
- ADR-006-developmental-vocabulary.md
- PHASE3_34_DEVELOPMENTAL_PROGRESSION_PROFILE_ROADMAP.md
- docs/campaigns/phase3_34/PHASE3_34_DESIGN.md
- docs/campaigns/phase3_34/PHASE3_34_AXIS_AND_BAND_SPEC.md
- docs/campaigns/phase3_34/PHASE3_34_PROJECTOR_DESIGN.md
- docs/campaigns/phase3_34/PHASE3_34_PREREQUISITE_GRAPH_SPEC.md
- CURRENT_MISSION_phase3_34.md
- CURRENT_CAMPAIGN_phase3_34.md
```

### Files to read on-demand (per step)

```text
Step 1 (skeleton):
  - brain/development/probe_report_protocol.py (the input contract)

Step 4 (predicate authoring, reference axis):
  - docs/campaigns/phase3_34/PHASE3_34_PREDICATE_TEMPLATE.md

Step 4 (other axes — DELEGATE TO CODEX, do not load in Claude Code):
  - For each axis, fire off a Codex task with ONLY:
    * The relevant section of PHASE3_34_AXIS_AND_BAND_SPEC.md
    * The full PHASE3_34_PREDICATE_TEMPLATE.md
    * ADR-002, ADR-005 (reference)

Step 8 (static audit fixture):
  - The completed predicate_table.py
  - brain/development/fixtures/profile_canonical_substrate.py
```

### Approx token budget: ~150K — at the edge of single-conversation
viability.

### Recommended split

```text
Conversation 3.34.A (Steps 1-3): module skeleton, types, projector.
Conversation 3.34.B (Steps 4-5): predicate authoring + dispatch to
                                  Codex. Reset context after each
                                  axis batch.
Conversation 3.34.C (Steps 6-10): static audit, A16 benchmark,
                                  catalog, drop-in.
```

## Phase 3.35: First Targeted Consolidation

### Seed at start

```text
- README.md
- ADR-001-locked-decisions-D1-D8.md
- ADR-004-target-axes-regression-gate.md
- The roadmap authored from the template (named per axis).
- docs/campaigns/phase3_35/PHASE3_35_TEMPLATE_INSTRUCTIONS.md
  (the authoring guide — keep in context for reference)
- CURRENT_MISSION_phase3_35.md
- CURRENT_CAMPAIGN_phase3_35.md (or _phase3_35_<axis>.md)
```

### Files to read on-demand

```text
- The probe module being modified (specific to the mechanism).
- brain/development/developmental_progression_profile.py (to verify
  the projector reads the new behavior correctly).
- brain/development/predicate_table.py (to verify the predicates'
  monotonicity is preserved).
```

### Approx token budget: ~80K (lighter than 3.34 because the change
is scoped to one axis).

## When to start a fresh conversation mid-campaign

Hard signal: the conversation has exceeded ~70% of the context
budget and the campaign has multiple unresolved steps remaining.

Soft signals:

- The agent re-reads a file it should already have in context.
- The agent confuses Phase 3.33's discipline (diagnostic) with
  Phase 3.34's (the projector consumes the diagnostics).
- The agent's responses get slower or more verbose.

When restarting:

1. Save the campaign state to `CURRENT_CAMPAIGN_phase3_NN.md` with
   the current step number, completed steps, and any open
   questions.
2. Commit any pending edits.
3. Start a fresh conversation.
4. Seed with the phase's seed list plus
   `CURRENT_CAMPAIGN_phase3_NN.md`.
5. Tell the new conversation: "Resume Phase 3.NN at Step X. Read
   `CURRENT_CAMPAIGN_phase3_NN.md`."

## Codex sub-conversations

Codex tasks should be ultra-minimal context. For predicate authoring:

```text
Seed: ~10K
- PHASE3_34_PREDICATE_TEMPLATE.md (entirety)
- One axis row from PHASE3_34_AXIS_AND_BAND_SPEC.md
- ADR-002, ADR-005 (very brief excerpts)
- The relevant ProbeReport field names
```

Codex's output for one axis is small (~16 predicates × ~5 lines = ~80
lines of code). Merging into the main Claude Code conversation
consumes minimal context.

## Catastrophic context degradation

If the agent appears to have completely lost the campaign's purpose
(e.g., it's relitigating ADR-001, or it's making claims that violate
the non-claim discipline), STOP. Don't try to recover. Start a fresh
conversation with the seed list.

Recovery from a degraded conversation costs more tokens than
restarting.
