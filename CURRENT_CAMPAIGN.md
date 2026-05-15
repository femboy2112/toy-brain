# CURRENT_CAMPAIGN.md — Fast Safe Text Interaction Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / FINAL-PR
```

This campaign replaces the completed Phase 3.5 Expression + ReadabilityPredictor campaign. It defines the fastest safe route from the current v0.12 repo to a bounded text-stream interaction loop.

The campaign must run on a dedicated branch, must push successful step commits to that branch, and must finish by opening a pull request into `main`. It must not commit or push directly to `main`, and it must not merge without explicit user approval.

Preferred campaign branch:

```text
campaign/fast-safe-text-interaction
```

Preferred final PR title:

```text
phase3: fast safe text interaction campaign
```

---

## 0. Strategic target

Target user-visible loop:

```text
operator submits bounded text chunks
  -> chunks enter local TextStreamHistory
  -> deterministic stream summaries and candidates become inspectable
  -> operator explicitly promotes a validated candidate into the queue
  -> existing /step route remains the only tick() route
```

Target commands after the final campaign phase:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
/step
/tick
/state
```

This is not a free-form chat layer. Text first becomes local developmental evidence. Only explicit, validated promotion candidates may approach the existing event queue.

---

## 1. Baseline

Expected starting state:

```text
Catalog: v0.12
Counts: 139 REQUIRED / 48 STRUCTURAL / 5 NOT-EXERCISED / 12 DEFERRED / 8 OBSERVED
Latest complete campaign: Phase 3.5 Expression + ReadabilityPredictor
Latest audit: PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
Audit verdict: PASS
Recommended next mission: Phase 3.6 Reflective Inspection
```

Known operational drift to fix first:

```text
README.md still contains older catalog-count language.
CURRENT_MISSION.md still pointed at Phase 3.5 before this campaign.
CURRENT_CAMPAIGN.md still contained the completed Phase 3.5 campaign before this campaign.
```

---

## 2. Non-negotiable boundaries

Preserve these boundaries throughout the whole macro-campaign:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
developmental histories remain local until explicit promotion
tick() remains the only TLICA runtime transition route
single-event tick discipline remains intact
Expression remains local evidence only
Readability remains local readability evidence only
Reflective Inspection remains read-only and below Mode B
operator commands remain finite, typed, bounded, and inspectable
```

Do not add unrestricted host capabilities, real LLM behavior, social/language harnessing, Mode B planning, or direct TLICA mutation from developmental histories.

Guarded paths may be touched only when a step explicitly allows them:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

---

## 3. Macro-campaign phases

```text
Step 1      Repo-state sync
Steps 2-9   Phase 3.6 Reflective Inspection
Steps 10-18 Phase 3.7 Text Stream Ingress
Steps 19-26 Phase 3.8 Operator Stream Interaction
Step 27     Final PR preparation
```

Each step that changes files must be committed and pushed to the campaign branch before stopping or continuing.

---

# Step 1 — Repo-state sync

Purpose: remove operational drift before any new runtime layer is planned.

Allowed files:

```text
README.md
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_FAST_SAFE_TEXT_INTERACTION_ROADMAP.md
```

Required work:

```text
update README.md so it no longer claims catalog v0.6/v0.5 as current
make CURRENT_MISSION.md point to this campaign
make CURRENT_CAMPAIGN.md describe this campaign
add or refresh PHASE3_FAST_SAFE_TEXT_INTERACTION_ROADMAP.md
state that Phase 3.5 is complete and Phase 3.6 is next
state branch/push/PR workflow explicitly
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
bash tools/check_all.sh
```

Commit message:

```text
docs(campaign): sync fast-safe text interaction mission
```

Push branch. Stop after this step if validation fails or README state is ambiguous.

---

# Step 2 — Phase 3.6 synthesis

Create:

```text
PHASE3_6_REFLECTIVE_INSPECTION_SYNTHESIS.md
```

Purpose: define Reflective Inspection as a read-only developmental summary layer.

Required content:

```text
v0.12 baseline
why Phase 3.6 follows Phase 3.5 audit recommendation
Reflective Inspection thesis
read-only summary over OutputHistory / WorldletHistory / ProtoBasicHistory / ExpressionHistory / OperatorTranscript where available
why this is not Mode B
why this is not language/social communication
why this is not truth scoring
why this is not agency
non-goals
risks
next artifact: kickoff
```

Validation:

```bash
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 3 — Phase 3.6 kickoff

Create:

```text
PHASE3_6_REFLECTIVE_INSPECTION_KICKOFF.md
```

Define only local read-only structures, likely:

```text
ReflectiveSource
ReflectiveSummaryItem
ReflectiveInspectionSnapshot
ReflectiveInspectionSummary
ReflectionHistory or InspectionHistory if needed, copy-on-write only
```

Required exclusions:

```text
no Mode B planning
no self-modification
no natural-language teacher
no social model
no real LLM calls
no direct tick promotion
no TLICA mutation
no UI integration unless later accepted
```

Validation:

```bash
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 4 — Phase 3.6 corrigenda

Create:

```text
PHASE3_6_REFLECTIVE_INSPECTION_CORRIGENDA.md
```

Check:

```text
reflection vs Mode B
inspection vs agency
summary vs truth
read-only locality
bounded exact counts/statistics
source-history non-mutation
whether UI integration is deferred
which rows should be REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED
```

Commit and push.

---

# Step 5 — Phase 3.6 catalog patch plan

Create:

```text
PHASE3_6_REFLECTIVE_INSPECTION_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-REF-*
```

Likely row themes:

```text
finite source enumeration
bounded read-only summary records
deterministic exact aggregate counts
summary construction does not mutate source histories
summary construction does not mutate BrainState/MSI/PtCns/registry
no Mode B / agency / truth / language claims
OBSERVED aggregate inspection walk
```

Stop at review gate after committing and pushing this plan. Do not apply catalog patch until user approves the plan.

---

# Step 6 — Apply Phase 3.6 catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional package marker if the accepted plan allows it:

```text
brain/development/reflective.py
brain/development/fixtures/reflective_*.py
```

Apply accepted rows only. Register pending checks where needed so coverage stays coherent.

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 7 — Implement Phase 3.6 core

Allowed files per accepted plan, likely:

```text
brain/development/reflective.py
brain/development/fixtures/reflective_core.py
brain/invariants.py
```

Required behavior:

```text
frozen/slots records
bounded source enumeration
read-only summary construction
no mutation of source histories
no mutation of BrainState/MSI/PtCns/registry
```

Validation:

```bash
python3 -m brain.invariants run --id I-REF
bash tools/check_all.sh
```

Commit and push.

---

# Step 8 — Phase 3.6 full gate and audit

Create:

```text
PHASE3_6_REFLECTIVE_INSPECTION_AUDIT.md
```

Verdict must be PASS / PASS WITH PATCHES / BLOCKED.

Audit:

```text
row registration
read-only behavior
source-history non-mutation
kernel boundary
Mode B boundary
truth/language/social boundary
full gate
recommended next mission: Phase 3.7 Text Stream Ingress
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit and push.

---

# Step 9 — Phase 3.6 review gate

Stop unless the Phase 3.6 audit is PASS or the user explicitly accepts PASS WITH PATCHES.

If accepted, continue to Phase 3.7.

---

# Step 10 — Phase 3.7 text-stream synthesis

Create:

```text
PHASE3_7_TEXT_STREAM_INGRESS_SYNTHESIS.md
```

Purpose: define raw text stream ingress below promotion.

Required thesis:

```text
TextStreamChunk = bounded local raw/operator text evidence
TextStreamHistory = copy-on-write bounded local history
SegmentCandidate = structural span/delimiter candidate, not a language parse
StreamPattern = recurrence-backed structural pattern, not truth/PRESERVE
StreamPromotionCandidate = explicit candidate, not yet PerceptEvent
```

Validation:

```bash
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 11 — Phase 3.7 kickoff

Create:

```text
PHASE3_7_TEXT_STREAM_INGRESS_KICKOFF.md
```

Define likely structures:

```text
TextStreamSource
TextStreamChunk
TextStreamHistory
StreamFeatureVector
SegmentCandidate
StreamPattern
StreamPromotionCandidate
```

Hard constraints:

```text
bounded printable text
exact deterministic counts/statistics
copy-on-write histories
no direct tick call
no BrainState mutation
no COGITO_ID collision
no language/truth/social/agency claim
```

Commit and push.

---

# Step 12 — Phase 3.7 corrigenda

Create:

```text
PHASE3_7_TEXT_STREAM_INGRESS_CORRIGENDA.md
```

Check:

```text
raw stream vs PerceptEvent
chunk text vs language meaning
segment candidate vs parse
stream pattern vs truth/PRESERVE
promotion candidate vs event queue
bounds and anti-growth rules
source/provenance rules
COGITO_ID defenses
```

Commit and push.

---

# Step 13 — Phase 3.7 catalog patch plan

Create:

```text
PHASE3_7_TEXT_STREAM_INGRESS_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-STRM-*
```

Likely rows:

```text
bounded TextStreamChunk
TextStreamHistory copy-on-write and bounded
deterministic feature extraction
SegmentCandidate is structural only
StreamPattern requires recurrence
promotion candidate requires explicit provenance and non-reserved ID
no BrainState/source-history mutation
no direct tick route
anti-growth behavior for repeated or huge chunks
```

Stop at review gate after committing and pushing this plan.

---

# Step 14 — Apply Phase 3.7 catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional package marker if accepted:

```text
brain/development/text_stream.py
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit and push.

---

# Step 15 — Implement text stream core

Allowed files per accepted plan, likely:

```text
brain/development/text_stream.py
brain/development/fixtures/text_stream_core.py
brain/invariants.py
```

Required behavior:

```text
bounded chunk construction
bounded copy-on-write history
exact deterministic feature vector
non-reserved IDs
no mutation outside TextStreamHistory
```

Validation:

```bash
python3 -m brain.invariants run --id I-STRM
bash tools/check_all.sh
```

Commit and push.

---

# Step 16 — Implement segment/pattern/promotion-candidate layer

Allowed files per accepted plan.

Required behavior:

```text
segment candidates are structural spans only
patterns require recurrence
promotion candidates require explicit source/provenance/evidence
promotion candidates are not PerceptEvents
promotion candidates do not call tick
```

Validation:

```bash
python3 -m brain.invariants run --id I-STRM
bash tools/check_all.sh
```

Commit and push.

---

# Step 17 — Phase 3.7 full audit

Create:

```text
PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md
```

Audit:

```text
boundedness
copy-on-write behavior
COGITO_ID defenses
no direct tick route
no language/truth/social/agency claims
full gate
recommended next mission: Phase 3.8 Operator Stream Interaction
```

Commit and push.

---

# Step 18 — Phase 3.7 review gate

Stop unless Phase 3.7 audit is PASS or user accepts PASS WITH PATCHES.

---

# Step 19 — Phase 3.8 operator stream synthesis

Create:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_SYNTHESIS.md
```

Purpose: expose text stream ingress through the finite Operator TUI command surface.

Required target commands:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
```

Rules:

```text
/stream appends to TextStreamHistory only
/stream-summary is read-only
/stream-candidates is read-only
/stream-promote validates and queues one explicit candidate
/stream-promote does not call tick
/step remains the tick route
```

Commit and push.

---

# Step 20 — Phase 3.8 kickoff

Create:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md
```

Plan changes to:

```text
brain/ui/command_line.py
brain/ui/commands.py
brain/ui/session.py
brain/ui/render.py
brain/ui/fixtures/...
README.md
```

Only include exact files if accepted by the later catalog plan.

Commit and push.

---

# Step 21 — Phase 3.8 corrigenda

Create:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_CORRIGENDA.md
```

Check:

```text
finite command parser
bounded input length
stream command does not tick
promotion command only queues
failure isolation is local UI status only
session resource-free property remains true
read-only render path remains deterministic
```

Commit and push.

---

# Step 22 — Phase 3.8 catalog patch plan

Create:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-UI-STRM-* or I-UI-* continuation
```

Stop at review gate after committing and pushing.

---

# Step 23 — Apply Phase 3.8 catalog patch

Allowed files per accepted plan, likely:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Commit and push after catalog count validation.

---

# Step 24 — Implement stream commands

Allowed files per accepted plan, likely:

```text
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/render.py
brain/ui/fixtures/stream_commands.py
brain/invariants.py
```

Required behavior:

```text
finite parser extension
bounded text field
stream history append through session only
summary/candidate views read-only
promotion command queues one candidate
/step remains the only tick route
```

Validation:

```bash
python3 -m brain.invariants run --id I-UI
python3 -m brain.invariants run --id I-STRM
bash tools/check_all.sh
```

Commit and push.

---

# Step 25 — Phase 3.8 audit

Create:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md
```

Audit complete interaction path:

```text
/stream -> TextStreamHistory only
/stream-summary -> read-only
/stream-candidates -> read-only
/stream-promote -> queue only
/step -> existing tick path
failure isolation
full gate
```

Commit and push.

---

# Step 26 — End-to-end dry run documentation

Create or update:

```text
PHASE3_TEXT_INTERACTION_DRY_RUN.md
```

Document a deterministic local session:

```text
/stream hello world
/stream hello world
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
/step
/tick
```

No real LLM scenario is required unless the user explicitly requests it.

Commit and push.

---

# Step 27 — Final PR preparation

Required final validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Open a PR to `main` with title:

```text
phase3: fast safe text interaction campaign
```

PR body must include:

```text
completed steps
catalog version/count transition
validation results
interaction loop achieved
remaining deferred work
confirmation that main was not pushed directly
confirmation that PR is not merged
```

Do not merge.
