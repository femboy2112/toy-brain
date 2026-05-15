# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below, unless the user gives a more specific instruction.

---

## Current mission

Draft the Phase 3.1 kickoff document:

```text
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

This is a **planning artifact only**.

Do **not** implement Phase 3 code.

---

## Why this mission exists

`PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md` is now the bridge from the v0.5 hardened kernel to Phase 3. It names the next artifact:

```text
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

The kickoff must convert the synthesis into a precise implementation plan for Phase 3.1 while preserving the project discipline:

```text
plan → corrigenda → code
```

This mission drafts the kickoff only. It does not authorize runtime implementation.

---

## Required source files to read first

Read these before writing the kickoff:

```text
CURRENT_MISSION.md
README.md
INVARIANT_CATALOG.md
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
traces/RUN_SUMMARY.md
BASELINE_HARDENING_KICKOFF.md
PHASE2_v1_2_CORRIGENDA.md
.codex/README.md
.codex/CODEX_AGENT_MAP.md
```

Do not rely on unstated conversation context. The kickoff must stand on repo-local files.

---

## Required output file

Create:

```text
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

Do not edit any other file unless absolutely necessary and explicitly justified.

---

## Required thesis

The kickoff must carry this bridge principle:

```text
PRESERVE should be earned, not labeled.
```

It must explain that the real traced behavioral run showed a clean kernel but a 2/4 semantic expectation match, with both PRESERVE-expected self/sunset contents classified as DAMAGE.

It must frame cold-start conservatism as an inference, not a proven fact:

```text
The trace shows what the LLM emitted; it does not directly prove why.
```

It must explain Phase 3.1’s empirical motivation:

```text
In a cogito-only state, identity-adjacent content is not automatically PRESERVE.
Before lived content exists, new content may properly appear as perturbation.
The chamber’s job is to build the substrate history that makes clean integration possible.
```

---

## Required kickoff sections

The kickoff must include these sections or equivalent headings.

### 1. Purpose

State that Phase 3.1 builds the deterministic Osmotic Chamber substrate layer.

State that it is the first Phase 3 implementation phase, but this document is still only a kickoff plan.

### 2. Current baseline

State:

```text
catalog v0.5
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

State that v0.5 is the acceptance gate and must remain green.

### 3. Empirical motivation from trace

Summarize:

```text
trace file: traces/first_scenario_real.jsonl
summary file: traces/RUN_SUMMARY.md
kernel health: clean
semantic match: 2/4
cold-start conservatism: working inference
```

### 4. Scope

Phase 3.1 must include:

```text
PhenomenalFrame
FrameSource
SubstrateDrives
SubstrateHistory
ProtoPattern
ProtoContent
salience_v1
stability_v1
prediction_gain_v1
SIMILARITY
FOCUS_CONTACT
ProbeUse
ProbePolicyState
promotion gate to PerceptEvent
source-tag audit
first deterministic chamber fixtures
Phase 3.1 catalog rows and statuses
trace reserved-key protection decision
```

### 5. Non-goals

Explicitly prohibit:

```text
no Phase 3.2 output ladder
no Minimal Worldlet
no Proto-BASIC REPL
no expression layer
no social/language harness
no Mode B implementation
no stochastic REQUIRED behavior
no prompt tuning to force the four-tick scenario to pass
no seeded-MSI scenario hack as the immediate next move
no direct mutation of TLICA state
no bypassing PerceptEvent and tick()
```

### 6. Package / module plan

Propose a minimal `brain/development/` skeleton for Phase 3.1 only.

Do not include output ladder, worldlet, repl, expression, or language modules in Phase 3.1.

Recommended Phase 3.1-only skeleton:

```text
brain/development/
├── __init__.py
├── stream.py              # PhenomenalFrame, FrameSource
├── drives.py              # SubstrateDrives
├── history.py             # SubstrateHistory, trace/provenance ids
├── proto_pattern.py       # ProtoPattern, bucketing/signature logic
├── proto_content.py       # ProtoContent, PromotionProvenance
├── salience.py            # salience_v1
├── stability.py           # stability_v1
├── prediction_gain.py     # prediction_gain_v1
├── probes.py              # SIMILARITY, FOCUS_CONTACT, ProbeUse, ProbePolicyState
├── promotion.py           # ProtoContent -> PerceptEvent gate
└── fixtures/
    ├── recurrence_detection.py
    ├── unstable_noise_rejection.py
    ├── salience_is_not_truth.py
    ├── focus_stabilizes_or_dissolves.py
    ├── proto_content_promotion.py
    └── source_tag_audit.py
```

### 7. Data model to lock

Specify dataclass sketches for:

```text
FrameSource
PhenomenalFrame
SubstrateDrives
SubstrateHistory
ProtoPattern
ProtoContent
PromotionProvenance
ProtoProbe
ProbeUse
ProbePolicyState
```

Use `Fraction` for numeric values.

All dataclasses should be frozen and slots-based where practical.

### 8. Source tagging rule

Include a structural rule:

```text
Every channel in every PhenomenalFrame channel group must have a FrameSource.
```

Construction should raise if source tags are missing.

### 9. Metric formulas to lock

Define v1 formulas explicitly enough to be falsifiable:

```text
salience_v1
stability_v1
prediction_gain_v1
```

Formula choices may be heuristic, but the kickoff must mark them as engineering hypotheses, not TLICA theorems.

### 10. Primitive probes

Phase 3.1 only has:

```text
SIMILARITY
FOCUS_CONTACT
```

Do not include mature tools like cause/effect, conditionals, object persistence, or Mode B meta-learning.

### 11. Promotion gate

Define when ProtoContent may become a PerceptEvent.

The gate must require more than salience alone.

It must preserve:

```text
COGITO_ID cannot be created by developmental content
PerceptEvent validation still applies
existing tick() is the only entry into TLICA runtime state
```

### 12. Catalog rows and statuses

Propose Phase 3.1 rows conservatively.

Use:

```text
REQUIRED for safety / deterministic gates / kernel-boundary protections
STRUCTURAL for protocols and construction constraints
OBSERVED for noise robustness and qualitative developmental behavior
```

Do not introduce EXPERIMENTAL unless the tooling change is explicitly proposed and justified.

Potential row families:

```text
I-FRAME-*   PhenomenalFrame/source-tag structure
I-DEV-*     recurrence, salience-not-truth, focus, promotion gate
I-SBX-*     operator injection is not knowledge, salience drive is not truth
I-TRACE-*   reserved-key protection if handled here
```

### 13. Trace reserved-key protection decision

The kickoff must explicitly decide whether trace reserved-key protection is:

```text
A. a pre-Phase-3.1 micro-hardening patch, or
B. part of Phase 3.1 row set
```

The kickoff should recommend one and explain why.

### 14. Fixtures

Specify first deterministic fixtures.

Required fixture concepts:

```text
recurring pattern is detected
unstable noise is rejected
salience alone does not promote
focus can stabilize or dissolve a pattern
proto-content can promote through PerceptEvent and tick()
missing source tag raises
COGITO_ID cannot be produced by developmental content
```

### 15. Validation plan

Include expected validation commands.

Because this is a kickoff document only, Codex should not run the full gate unless explicitly asked.

The future implementation phase should eventually run:

```bash
python -m tools.catalog counts
python -m brain.invariants run --id I-FRAME
python -m brain.invariants run --id I-DEV
python -m brain.invariants run --id I-SBX
bash tools/check_all.sh
```

But the current mission should only run lightweight validation:

```bash
git diff --name-only
python -m tools.catalog counts
```

### 16. Build order

Specify a strict build order for the future implementation phase:

```text
catalog patch first
trace reserved-key decision
stream/source tags
history
metrics
proto-pattern
probes
proto-content
promotion
fixtures
runner registration
full validation
```

### 17. Roadblocks / open decisions

Include at least:

```text
formula arbitrariness
source-tag schema stability
SubstrateHistory granularity
promotion threshold selection
status discipline for OBSERVED vs REQUIRED
interaction with current tick single-event guard
whether trace reserved-key protection is pre-phase or in-phase
```

### 18. Stop condition

End the document by saying:

```text
Nothing builds until this kickoff is reviewed and a corrigenda pass is completed.
```

---

## Engineering disclaimer

Every Phase 3.1 row family must be marked as an engineering hypothesis unless it is a direct kernel-boundary rule.

Use this text:

```text
SOURCE: Engineering hypothesis (Phase 3.1 Osmotic Chamber). Not a TLICA theorem. Specific formulas and thresholds are parameterized simulation choices; the family of constraints is the commitment, not any single instantiation.
```

---

## Guardrails

Do not modify these files during this mission:

```text
brain/
INVARIANT_CATALOG.md
lean_reference/
traces/
scenarios/
```

Allowed file for this mission:

```text
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

Optional only if needed:

```text
CURRENT_MISSION.md
```

But do not update `CURRENT_MISSION.md` again unless the user asks.

---

## Validation

After drafting the kickoff:

Run lightweight checks only:

```bash
git diff --name-only
python -m tools.catalog counts
```

Do not run:

```bash
bash tools/check_all.sh
python -m brain.scenario run ...
```

unless the user explicitly asks.

---

## Git persistence requirement

After validation passes, Codex must commit and push its result.

Rules:

```text
stage only PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
commit with a clear message
push to the current branch / main as appropriate
report the commit SHA
```

Do not commit accidental changes to guarded files.

If there are no changes, Codex should report that no commit was made and explain why.

---

## Final report

When done, report:

```text
Created/updated:
- PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md

Validation:
- git diff --name-only: ...
- python -m tools.catalog counts: pass / not run with reason

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- review kickoff
- run kickoff corrigenda pass
- only then code Phase 3.1
```

---

## Stop condition

Stop after drafting `PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md`, validating, committing, pushing, and reporting the result.

Do not proceed into Phase 3.1 code unless the user gives a new explicit instruction.
