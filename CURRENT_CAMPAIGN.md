# CURRENT_CAMPAIGN.md — Fast Safe Text Interaction Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / FINAL-PR
```

This campaign replaces the completed Phase 3.5 Expression + ReadabilityPredictor campaign. It defines the fastest safe route from the current v0.12 repo to a bounded text-stream interaction loop, while preserving the existing catalog, identity, event, and tick-boundary disciplines.

Preferred campaign branch:

```text
campaign/fast-safe-text-interaction
```

Preferred final PR title:

```text
phase3: fast safe text interaction campaign
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
```

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
PHASE3_8B_LLM_TOGGLE_AMENDMENT.md
```

The LLM toggle amendment is mandatory context. It must be incorporated before final interactive testing is considered complete.

---

## Strategic target

Target user-visible loop:

```text
/stream <text>
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
/step
/tick
/state
```

Meaning:

```text
/stream            appends bounded text to local stream history
/stream-summary    displays read-only stream statistics
/stream-candidates displays read-only candidate structure
/stream-promote    validates and queues one explicit candidate
/step              remains the route that advances tick processing
```

Final testing must also support an explicit runtime client mode toggle:

```text
offline       default deterministic mode
mock          deterministic canned-response mode
anthropic-api explicit model-backed API mode
claude-cli    explicit local CLI-backed mode
```

The default must remain:

```text
offline
```

Model-backed modes must be opt-in and must reuse the existing `LLMClient` protocol and existing `tick(..., client, ...)` seam. This campaign does not authorize a second classification path.

---

## Baseline

Expected starting state:

```text
Catalog: v0.12
Counts: 139 REQUIRED / 48 STRUCTURAL / 5 NOT-EXERCISED / 12 DEFERRED / 8 OBSERVED
Latest complete campaign: Phase 3.5 Expression + ReadabilityPredictor
Latest audit: PHASE3_5_EXPRESSION_READABILITY_AUDIT.md
Audit verdict: PASS
Recommended next mission: Phase 3.6 Reflective Inspection
```

Known repo-state drift to address first:

```text
README.md contains older catalog-count language
current mission/campaign files previously pointed at completed Phase 3.5 work
standalone roadmap file should exist and agree with this campaign
```

---

## Guardrails

Preserve these constraints throughout:

```text
COGITO_ID remains reserved
raw text never maps to COGITO_ID
raw text never mutates BrainState directly
developmental histories remain local until explicit promotion
tick() remains the only formal runtime transition route
single-event tick discipline remains intact
Expression remains local evidence only
Readability remains local readability evidence only
Reflective Inspection remains read-only and below Mode B
operator commands remain finite, typed, bounded, and inspectable
model-backed testing remains explicit opt-in and defaults offline
```

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

## Macro sequence

```text
Step 1        Repo-state sync
Steps 2-9     Phase 3.6 Reflective Inspection
Steps 10-18   Phase 3.7 Text Stream Ingress
Steps 19-24   Phase 3.8 Operator Stream Interaction
Steps 24A-24G Phase 3.8b LLM Runtime Toggle
Steps 25-27   Final audit, dry run, and PR preparation
```

Every step that changes files must be committed and pushed to the campaign branch.

---

# Step 1 — Repo-state sync

Purpose: remove operational drift before new runtime work.

Allowed files:

```text
README.md
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_FAST_SAFE_TEXT_INTERACTION_ROADMAP.md
```

Required work:

```text
sync README with catalog v0.12
make mission/campaign point to this macro-campaign
ensure roadmap agrees with this campaign
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

Commit and push.

---

# Step 2 — Phase 3.6 synthesis

Create:

```text
PHASE3_6_REFLECTIVE_INSPECTION_SYNTHESIS.md
```

Required content:

```text
v0.12 baseline
why Phase 3.6 follows the Phase 3.5 audit
Reflective Inspection thesis
read-only summary over existing developmental histories
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
no model-backed scoring
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

Stop at review gate after committing and pushing this plan. Do not apply catalog changes until the plan is accepted.

---

# Step 6 — Apply Phase 3.6 catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional package marker if accepted:

```text
brain/development/reflective.py
brain/development/fixtures/reflective_*.py
```

Apply accepted rows only. Register pending checks where needed.

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

Target commands:

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

# Step 24A — LLM runtime toggle synthesis

Create:

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_SYNTHESIS.md
```

Use `PHASE3_8B_LLM_TOGGLE_AMENDMENT.md` as mandatory source context.

Required thesis:

```text
offline mode remains the default
model-backed mode is explicit opt-in
client selection reuses the existing LLMClient protocol
selected client enters through the existing tick client argument
no second classification path is introduced
fixtures remain deterministic unless explicitly OBSERVED/manual
```

Commit and push.

---

# Step 24B — LLM runtime toggle kickoff

Create:

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_KICKOFF.md
```

Define:

```text
LlmRuntimeMode
LlmRuntimeConfig
build_llm_client_from_config(...)
CLI/env precedence
cache policy
startup failure behavior
fixture policy
```

Likely accepted modes:

```text
offline
mock
anthropic-api
claude-cli
```

Commit and push.

---

# Step 24C — LLM runtime toggle corrigenda

Create:

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_CORRIGENDA.md
```

Check:

```text
finite mode parsing
default deterministic behavior
explicit opt-in semantics
credential/tool availability behavior
cache behavior
trace/summary wording
fixture status mapping
UI import-audit implications
```

Commit and push.

---

# Step 24D — LLM runtime toggle catalog patch plan

Create:

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_CATALOG_PATCH_PLAN.md
```

Likely row family:

```text
I-LLMTOG-*
```

Likely rows:

```text
default client mode is offline
accepted modes are finite and closed
model-backed modes require explicit opt-in
unavailable backend fails locally before launch
deterministic fixtures do not require model-backed mode
model-backed smoke is OBSERVED/manual, not REQUIRED
client factory returns an LLMClient-compatible object
selected client enters through the existing tick client argument
```

Stop at review gate after committing and pushing. Do not implement until the plan is accepted.

---

# Step 24E — Apply accepted LLM toggle catalog patch

Allowed files:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Optional marker files only if accepted by the patch plan:

```text
brain/ui/llm_runtime.py
brain/ui/fixtures/llm_runtime_toggle.py
```

Commit and push after catalog count validation.

---

# Step 24F — Implement LLM runtime toggle

Likely files:

```text
brain/ui/llm_runtime.py
brain/ui/__main__.py
brain/ui/fixtures/llm_runtime_toggle.py
brain/invariants.py
README.md
```

Required behavior:

```text
closed LlmRuntimeMode enumeration
config object with CLI/env-derived fields
factory returning LLMClient-compatible client
offline default
model-backed modes explicit only
optional cache wrapping if configured
clear local error on unavailable backend
run_curses receives selected client
--print-once remains independent of selected client
```

Commit and push after targeted and full validation.

---

# Step 24G — LLM runtime toggle audit

Create:

```text
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
```

Audit:

```text
default offline behavior
explicit model-backed opt-in
client factory behavior
fixture determinism
OBSERVED/manual smoke status
full gate result
interaction with final Phase 3.8 audit
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
LLM toggle default remains offline
LLM toggle model-backed modes are explicit opt-in
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

Document deterministic local session:

```text
/stream hello world
/stream hello world
/stream-summary
/stream-candidates
/stream-promote <candidate_id>
/step
/tick
```

Also document optional model-backed launch examples after the toggle exists.

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
LLM runtime toggle status and offline-default confirmation
remaining deferred work
confirmation that main was not pushed directly
confirmation that PR is not merged
```

Do not merge.
