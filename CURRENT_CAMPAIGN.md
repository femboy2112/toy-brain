# CURRENT_CAMPAIGN.md — Phase 3.20 Coherence Feedback Bridge

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.20 follows the completed Phase 3.19 Internal Feedback Loop
Prototype campaign (PR #24, open against `main` at campaign start;
the Phase 3.20 branch is stacked on its HEAD). Phase 3.19 shipped:

```text
- brain/development/processing_window.py with FeedbackMode
  (str, Enum) {OFF, PATTERN_LEDGER}; the widened
  _V1_EMITTED_SOURCES set {REHEARSAL, PLEDGER_SUMMARY};
  build_pledger_summary_text deterministic helper; the
  PLEDGER_SUMMARY_TEXT_PREFIX = "pledger_summary" bounded
  constant; extended MODULE_PRODUCED_STRINGS; validate_feedback_mode.
- OperatorSession gained the optional feedback_mode:
  FeedbackMode = FeedbackMode.OFF field, plus the
  _run_feedback_step(*, tick_index, seed_pattern_id) helper.
  _run_processing_window interleaves a pledger_summary chunk after
  each rehearsal when feedback_mode is PATTERN_LEDGER, producing
  exactly 1 + 2 * N stream chunks and a second-order Pattern Ledger
  entry whose recurrence climbs independently.
- INVARIANT_CATALOG.md v0.26 -> v0.27 with rows I-IFBK-01
  (integration) and I-IFBK-02 (static audit); I-PWND-02 body
  widened to include PLEDGER_SUMMARY in the v1-emit set.
- Zero real model calls; brain/tick.py unchanged; no LLM/cache/
  parser/schema change; OFFLINE default preserved.
- COHMON_SUMMARY remained reserved per LOCK F; continued to raise
  from build_rehearsal_provenance.
```

Phase 3.20 asks one bounded operational question:

```text
Can ToyI's runtime route a bounded Coherence Monitor summary
feedback event, derived from the live read-only Coherence Monitor
report observed after the rehearsal, back into the same Pattern
Ledger / Growth Ledger substrate -- without touching brain/tick.py,
the LLM, the parser, the cache, the schema, or any
consciousness-adjacent boundary, and without breaking the closed
import discipline that keeps brain/development/processing_window.py
decoupled from brain/development/coherence_monitor.py?
```

This is a **research** campaign toward a bounded conflict-monitoring-
like loop. It is **not** a proof of consciousness, sentience,
subjective experience, true agency, semantic understanding, or
self-modification.

Phase 3.20 does **not** implement SelfModel; does **not** modify
Growth Ledger / Pattern Ledger / Coherence Monitor semantics; does
**not** modify L1 / L2 / parser / prompt / tick / persistence /
autosave / DB schema. The runtime touches are limited to:

- `brain/development/processing_window.py` (extend with a new
  closed `FeedbackMode` member, a pure deterministic
  `build_cohmon_summary_text` helper that accepts only primitives,
  and the widened `_V1_EMITTED_SOURCES` set that includes
  `InternalEventSource.COHMON_SUMMARY`);
- `brain/ui/session.py` (extend `_run_processing_window` to
  optionally fire a coherence-summary chunk after each rehearsal
  when the mode is `COHERENCE` or `PATTERN_AND_COHERENCE`; add a
  bounded `_run_cohmon_feedback_step` helper that calls
  `build_full_coherence_report` via a local deferred import to
  avoid the circular `coherence_monitor <-> session` dependency at
  module load time);
- `INVARIANT_CATALOG.md` v0.27 -> v0.28 with bounded new row family
  `I-CFBK-01..NN` (exact count fixed in Step 5);
- new fixtures under `brain/ui/fixtures/`.

Preferred campaign branch:

```text
campaign/phase3-20-coherence-feedback-bridge
```

Preferred final PR title:

```text
phase3.20: coherence feedback bridge
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into the correct base (Phase 3.19 branch
  while PR #24 is open; main once PR #24 merges)
never push campaign work directly to main
never merge without explicit user approval
never edit brain/tick.py in Phase 3.20
```

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
PHASE3_20_COHERENCE_FEEDBACK_BRIDGE_ROADMAP.md
docs/campaigns/phase3_18/PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md
docs/campaigns/phase3_18/PHASE3_18_PATTERN_RECOGNITION_DEMO.md
docs/campaigns/phase3_18/PHASE3_18_AUDIT.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_SYNTHESIS.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_BEHAVIOR_REPORT.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_FINDINGS.md
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_AUDIT.md
brain/development/processing_window.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/development/growth_ledger.py
brain/development/text_stream.py
brain/ui/session.py
brain/ui/snapshot.py
brain/tick.py
brain/llm/client.py
brain/llm/ptcns_backed.py
tools/claude_helpers/campaign_state.py
tools/claude_helpers/gate_runner.py
tools/claude_helpers/flow_manifest.py
tools/claude_helpers/codex_chatgpt_flow_orchestrator.py
.claude/agents/brain-current-mission.md
.claude/agents/chatgpt-codex-flow-orchestrator.md
.claude/commands/orchestrate-flow-with-codex.md
.claude/commands/go.md
tools/check_all.sh
```

Then read whichever files the next campaign step names.

---

## Baseline

Expected current state at campaign start (pre-Step-7):

```text
Catalog: v0.28
Counts:
  REQUIRED:        284
  STRUCTURAL:       91
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.19 Internal Feedback Loop
                              Prototype (PR #24 open against main)
Current campaign:             Phase 3.20 Coherence Feedback Bridge
                              (Step 7 implementation landed)
Next eligible step:           Step 8 behavior report
Canonical design seed:        PHASE3_20_COHERENCE_FEEDBACK_BRIDGE_ROADMAP.md
```

Inherited follow-ups deliberately deferred:

```text
- SelfModel implementation remains OUT OF SCOPE.
- /pattern-ledger / /coherence-summary / /growth-ledger UIs remain
  DEFERRED at catalog level.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- Tracer wiring through OperatorSession.dispatch remains DEFERRED.
- REPL / worldlet feedback (architectures D / E from Phase 3.19's
  taxonomy) remain DEFERRED.
- Real-model reflection over feedback events remains DEFERRED.
- Combined pattern + coherence feedback mode
  (PATTERN_AND_COHERENCE) ships only if Step 5 explicitly bundles
  it as a bounded composition of the two existing helpers and the
  Step 6 review gate accepts; otherwise DEFERRED to Phase 3.21.
- Any change to Coherence Monitor's check set, status enum, or
  source labels remains OUT OF SCOPE for v1 (LOCK E).
```

---

## Operational target

Phase 3.20 uses this operational definition:

```text
Bounded coherence feedback WORKS iff:
  - OperatorSession.feedback_mode = FeedbackMode.COHERENCE
    (and, if Step 5 bundles it, FeedbackMode.PATTERN_AND_COHERENCE)
    drives _run_processing_window to emit, in addition to the
    Phase 3.18 rehearsal chunks (and, under
    PATTERN_AND_COHERENCE, the Phase 3.19 pledger_summary chunks),
    a bounded number of coherence-summary feedback chunks whose
    text is a deterministic
    "cohmon_summary overall=<status> pass=<np> warn=<nw>
     fail=<nf> na=<nna> checks=<nc>"
    string derived from the live Coherence Monitor report observed
    after the rehearsal.
  - Each coherence-summary chunk has provenance prefix
    "internal_processing_window:<k>:cohmon_summary".
  - Each coherence-summary chunk drives Pattern Ledger.observe and
    Growth Ledger.observe through the existing
    _append_stream_chunk call site (no new emission code, no new
    GrowthEventType, no new GrowthEventSource).
  - The coherence-summary chunks produce additional second-order
    Pattern Ledger entries whose structural signature differs from
    the seed entry's signature and from the Phase 3.19
    pledger_summary entry's signature.
  - Same input + same configuration produces the same Pattern
    Ledger / Growth Ledger state across runs / processes / OSes.
  - Zero real model calls; brain/tick.py untouched; cache
    counters unchanged; no schema change; OFFLINE default
    preserved.
  - The non-claim audit (canonical
    _FORBIDDEN_NON_CLAIM_TERMS tuple) passes against the new
    coherence-summary text generator and every bounded printable
    string the module produces.
  - The closed import discipline of
    brain/development/processing_window.py is preserved: the
    module does NOT import brain.development.coherence_monitor or
    brain.ui.session. The new helper accepts only bounded
    primitives (status value string, integer counts).
  - The widened _V1_EMITTED_SOURCES set is
    {REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}; the
    build_rehearsal_provenance helper no longer raises for
    COHMON_SUMMARY but still composes a bounded printable
    non-claim-clean provenance string.

Combined feedback (PATTERN_AND_COHERENCE) SHIPS only if Step 5
explicitly bundles it as a bounded composition of the two existing
helpers; otherwise DEFERRED to Phase 3.21.
```

---

## Real model call budget

```text
Max 20 real external model-backed calls total across the campaign.
Phase 3.20 expects to consume ZERO real model calls because the
  feedback path uses STREAM_APPEND which does not invoke
  brain.tick.tick or the LLM.
Stop before exceeding 20.
No unbounded loops; no "keep trying forever."
```

---

## Non-goals

```text
no SelfModel implementation
no Growth Ledger semantic change (no new GrowthEventType, no new
  GrowthEventSource)
no Pattern Ledger semantic change (no new SourceKind, no new
  saturation state, no signature shape change)
no Coherence Monitor semantic change (no new check, no new
  status, no new source label, no mutation of any kernel
  container; the monitor stays read-only)
no L1 cache semantic change
no L2 (eval_v1) semantic change
no parser change
no prompt change
no proof or claim of consciousness
no claim of sentience
no claim of subjective experience
no claim of semantic understanding
no truth adjudication
no claim of agency / intent / will / desire
no claim of self-modification in the strong sense
no aggregate consciousness / sentience / awareness / I-ness /
  growth score
no model-backed behavior as default
no hidden LLM calls
no silent network/model calls in offline/mock modes
no silent repair calls
no hidden autosave behavior
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
no DB schema change
no SCHEMA_VERSION bump
no /save-session / /load-session / autosave extension
no tick semantic change (brain/tick.py untouched)
no raw prompts or model outputs committed to the repo
no raw cache contents printed in docs
no secrets committed to the repo
no cache files committed to the repo (brain/.llm_cache stays
  gitignored)
no UI verb expansion unless explicitly reviewed
no raw codex invocation outside the sanctioned bridges
no Stage C.1 broad repo edits
no unbounded Codex collaboration loop
no unbounded state growth
no brain.development.coherence_monitor import inside
  brain/development/processing_window.py (I-PWND-02 import
  discipline)
no PASS/WARN/FAIL/NOT_APPLICABLE treated as truth claims; they
  remain structural statuses only
no runtime change that elevates the "coherence feedback" surface
  above bounded printable record identifiers + ints + Fractions
```

---

## Macro sequence

```text
Step 1   Mission sync + roadmap
Step 2   Coherence feedback synthesis
Step 3   Coherence feedback probe matrix
Step 4   Corrigenda / design locks
Step 5   Catalog patch plan
Step 6   Review Gate A
Step 7   Apply implementation (if gated through)
Step 8   Behavior report
Step 9   Findings / triage
Step 10  Final audit
Step 11  PR preparation
```

Every step that lands files must pass the standard preflight gates
before commit and must push the campaign branch on success:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

(or, on gate_runner failure:)

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

---

## ChatGPT/Codex consultation policy

```text
Stage A wrapper:  python3 tools/claude_helpers/codex_chatgpt_subagent.py
Stage A modes:    plan / review / summarize / debug
Stage A slash:    /ask-chatgpt
Stage B wrapper:  python3 tools/claude_helpers/codex_chatgpt_write_worker.py
Stage B modes:    write
Stage B slash:    /ask-chatgpt-write
Stage C.1 wrapper: python3 tools/claude_helpers/codex_chatgpt_flow_orchestrator.py
Stage C.1 shape:  dynamic DAG; max 2 active nodes; isolated nodes may
                   run in parallel; chained nodes require depends_on;
                   no automatic retry; hard cap 8 nodes;
                   campaign cap 5 nodes unless operator approves more
Stage C.1 slash:  /orchestrate-flow-with-codex
```

Stage A is allowed at: synthesis / patch plan / behavior report /
final audit adversarial review.

Stage B is allowed at: bounded single-file doc drafts whose exact
path is on the allowlist.

Stage C.1 is allowed at:

```text
Step 1   parent Claude writes directly
Step 2   synthesis doc shard (optional)
Step 3   probe matrix shard (optional)
Step 4   corrigenda shard (optional)
Step 5   catalog patch plan shard (optional)
Step 6   never; review gate is a parent-Claude decision
Step 7   bounded module/fixture shards permitted after review gate
Step 8   docs around the test; not the test itself if a runtime
         change would be needed
Step 9   findings doc draft after measurements exist
Step 10  audit doc draft after measurements exist
Step 11  PR body draft only
```

Stage C.1 is **forbidden** at:

```text
never    raw codex / codex exec invocation
never    running the real codex-cli model loop itself
never    touching secrets
never    committing cache files
never    broad runtime changes
never    brain/tick.py edits
never    final catalog reconciliation
never    overlapping write sets among active nodes
never    declared read/write collisions among active nodes
never    staging / commit / push
```

Before every Stage C.1 wave:

```bash
python3 -m tools.claude_helpers.flow_manifest validate \
  /tmp/<manifest>.json --strict
python3 -m tools.claude_helpers.flow_manifest summary \
  /tmp/<manifest>.json
```

Every step report must include the Stage A / Stage B / Stage C.1
disclosure block defined in `CURRENT_MISSION.md`.

---

# Step 1 — Mission sync + roadmap

Purpose: install Phase 3.20 as the current mission and land the
Phase 3.20 roadmap at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_20_COHERENCE_FEEDBACK_BRIDGE_ROADMAP.md
```

Forbidden in Step 1:

```text
brain/**
tools/**
.claude/**
INVARIANT_CATALOG.md
README.md
docs/campaigns/**
lean_reference/**
scenarios/**
traces/**
```

Required work: write Phase 3.20 mission / campaign / roadmap;
verify gate_runner --json green.

Commit message:

```text
phase3.20 step1: coherence feedback mission sync
```

Push.

---

# Step 2 — Coherence feedback synthesis

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_SYNTHESIS.md
```

Required analysis (per Phase 3.20 mission):

```text
1. Current Phase 3.19 mechanism (rehearsal + pledger_summary
   feedback).
2. Gap (Coherence Monitor output is read-only; COHMON_SUMMARY
   remains reserved; coherence results do not yet re-enter
   internal processing).
3. Proposed coherence feedback loop and event shape.
4. Candidate architectures A-E (session-level builder vs narrow
   helper vs direct import vs deferred vs combined).
5. Preferred architecture (session-level builder + bounded
   primitive helper on processing_window.py).
6. Testable hypotheses H1-H7.
7. Recommended v1 (FeedbackMode.COHERENCE; pure
   build_cohmon_summary_text accepting only primitives;
   COHMON_SUMMARY unlocked; combined PATTERN_AND_COHERENCE bundled
   only if simple and bounded).
```

Commit message:

```text
phase3.20 step2: coherence feedback synthesis
```

Push.

---

# Step 3 — Coherence feedback probe matrix

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_PROBE_MATRIX.md
```

Matrix:

```text
- window sizes: 0, 5, 10, 50
- modes: OFF, PATTERN_LEDGER, COHERENCE,
  PATTERN_AND_COHERENCE (planned if not yet implemented)
- inputs: repeated motif, contradiction pair, self-reference
  phrase, neutral factual text, emotionally valenced text
- measurements: stream chunk count, rehearsal step count, pattern
  feedback chunk count, coherence feedback chunk count, pattern
  entries, recurrence_count, confidence, saturation_state,
  CoherenceReport overall_status, CoherenceCheck statuses, Growth
  Ledger events, model call count if any, L1 / L2 cache counters
  if any, state mutation footprint, invariant status, non-claim
  scan result
```

If implementation does not yet support coherence feedback, mark
cells as planned/probe-blocked and state exactly what runtime
surface is missing.

Commit message:

```text
phase3.20 step3: coherence feedback probe matrix
```

Push.

---

# Step 4 — Corrigenda / design locks

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_CORRIGENDA.md
```

Lock LOCK A through LOCK K as described in the mission.

Commit message:

```text
phase3.20 step4: coherence feedback corrigenda
```

Push.

---

# Step 5 — Catalog patch plan

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_CATALOG_PATCH_PLAN.md
```

Must include: exact implementation architecture, exact files,
exact row family + statuses, exact catalog version/count delta,
exact fixtures, exact behavior-report plan, exact non-goals,
review-gate decision request.

Commit message:

```text
phase3.20 step5: coherence feedback catalog patch plan
```

Push.

---

# Step 6 — Review Gate A

Apply the autonomy authorization from `CURRENT_MISSION.md`. If
all eleven conditions pass, record `Review Gate A — ACCEPT PLAN
AS WRITTEN` and proceed. If any fails, stop.

This step does NOT change files. Commit only if the gate-status
record is part of an updated doc artifact created in step 5 or
4; otherwise this step is a transition record only.

---

# Step 7 — Apply implementation

Implement bounded coherence feedback per the accepted plan.
Required properties:

```text
- bounded deterministic coherence feedback
- no tick.py change
- no real model calls by default
- no unbounded growth
- provenance on every coherence-feedback artifact
- no raw prompt/model response
- no scalar score
- PASS/WARN/FAIL/NOT_APPLICABLE are structural statuses only
- closed enums where appropriate
- constructor validation
- tests for N = 0, 5, 10, 50
- tests for no non-claim language
- tests that COHMON_SUMMARY no longer raises (since v1 emits it)
- tests that coherence feedback creates a distinct pattern entry
```

Commit message:

```text
phase3.20 step7: implement coherence feedback bridge
```

Push.

---

# Step 8 — Behavior report

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_BEHAVIOR_REPORT.md
```

Run and report:

```text
- OFF baseline
- PATTERN_LEDGER baseline
- COHERENCE feedback
- combined PATTERN_AND_COHERENCE if implemented
- N = 0 / 5 / 10 / 50
- deterministic repeatability
- distinct input independence
- coherence status output
- recurrence effects
- saturation / cap behavior
- cache / call count if any
- invariant gates
- non-claim audit
```

Commit message:

```text
phase3.20 step8: coherence feedback behavior report
```

Push.

---

# Step 9 — Findings

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_FINDINGS.md
```

Classify:

```text
- blockers
- safety/invariant findings
- behavior successes
- weak behavior
- deferred enhancements
- next research directions
```

Commit message:

```text
phase3.20 step9: coherence feedback findings
```

Push.

---

# Step 10 — Final audit

Create:

```text
docs/campaigns/phase3_20/PHASE3_20_COHERENCE_FEEDBACK_AUDIT.md
```

Verdict options:

```text
PASS                          : feedback path implemented and
                                demonstrated end-to-end
PASS WITH DEFERRED FOLLOW-UPS : feedback path shipped; combined
                                mode or REPL/worldlet feedback
                                deferred
PARTIAL                       : feedback path partial
BLOCKED                       : feedback path blocked at design
FAIL                          : invariant / runtime regression
```

Validation (canonical preflight):

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

Required content: verdict; files changed across the campaign; gate
results; cumulative real model call count; mode tested; explicit
"no SelfModel implementation"; "no consciousness / sentience /
subjective / semantic / truth / agency / self-modification claim";
"no aggregate awareness / I-ness / growth score"; "no hidden LLM
call / hidden persistence / DB schema change"; "no L2 semantic
change"; "no tick semantic change"; "no raw prompts / responses /
cache files / secrets committed"; "OFFLINE remains default;
model-backed remains explicit opt-in"; Stage A / Stage B / Stage C.1
bridge usage disclosure; next-campaign note.

Commit message:

```text
phase3.20 step10: final coherence feedback audit
```

Push.

---

# Step 11 — PR preparation

Open a PR with title:

```text
phase3.20: coherence feedback bridge
```

Base resolution: target `campaign/phase3-19-internal-feedback-loop`
while PR #24 remains open; retarget to `main` once PR #24 has
merged. PR body must include: PR URL, base/head, catalog
version/counts, what coherence feedback was implemented, whether
pattern recurrence and coherence status now both feed back into
later processing, whether combined mode is implemented or
deferred, whether 50-tick processing window remains recommended,
validation, real model calls used, non-claims, next campaign
recommendation.

Do not merge.
