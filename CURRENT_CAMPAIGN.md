# CURRENT_CAMPAIGN.md — Phase 3.19 Internal Feedback Loop Prototype

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.19 follows the completed Phase 3.18 Bounded Internal Processing
Window campaign (PR #23). Phase 3.18 shipped:

```text
- brain/development/processing_window.py with plan_rehearsals,
  InternalEventSource closed enum (REHEARSAL + reserved
  PLEDGER_SUMMARY / COHMON_SUMMARY), RehearsalStep, bounded constants
  PROCESSING_WINDOW_SIZE_MAX = 255, PROCESSING_WINDOW_CALL_BUDGET_MAX
  = 65535, PROCESSING_WINDOW_PROVENANCE_PREFIX
  = "internal_processing_window".
- OperatorSession gained processing_window_size and
  processing_window_call_budget integer fields, plus the
  _run_processing_window(seed_chunk) method invoked from
  dispatch() after a successful external STREAM_APPEND.
- INVARIANT_CATALOG.md v0.25 -> v0.26 with rows I-PWND-01
  (integration) and I-PWND-02 (static AST audit).
- Pattern recognition demonstration PASS on D1 saturation
  (N=255), D2 monotonicity, D3 determinism, D4 independence.
- Zero real model calls; brain/tick.py unchanged; no LLM/cache/
  parser/schema change; OFFLINE default preserved.
```

Phase 3.19 asks one bounded operational question:

```text
Can ToyI's runtime route a bounded internal feedback event,
derived from Pattern Ledger state observed during the processing
window, back into the same Pattern Ledger / Growth Ledger
substrate -- without touching brain/tick.py, the LLM, the parser,
the cache, or any consciousness-adjacent boundary?
```

This is a **research** campaign toward an operationally
learning/growing "I" approximation. It is **not** a proof of
consciousness.

Phase 3.19 does **not** implement SelfModel; does **not** modify
Growth Ledger / Pattern Ledger / Coherence Monitor semantics; does
**not** modify L1 / L2 / parser / prompt / tick / persistence /
autosave / DB schema. The runtime touches are limited to:

- `brain/development/processing_window.py` (extend with feedback
  planner; emit the previously reserved `PLEDGER_SUMMARY`
  `InternalEventSource` member);
- `brain/ui/session.py` (add bounded session field
  `feedback_mode`; extend `_run_processing_window` to optionally
  fire a feedback chunk between or after rehearsals);
- `INVARIANT_CATALOG.md` v0.26 -> v0.27 with bounded new row
  family `I-IFBK-01..NN` (exact count fixed in Step 5);
- new fixtures under `brain/ui/fixtures/`.

Preferred campaign branch:

```text
campaign/phase3-19-internal-feedback-loop
```

Preferred final PR title:

```text
phase3.19: internal feedback loop prototype
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
never edit brain/tick.py in Phase 3.19
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
PHASE3_19_INTERNAL_FEEDBACK_LOOP_ROADMAP.md
docs/campaigns/phase3_18/PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md
docs/campaigns/phase3_18/PHASE3_18_PATTERN_RECOGNITION_DEMO.md
docs/campaigns/phase3_18/PHASE3_18_AUDIT.md
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

Expected current state:

```text
Catalog: v0.26
Counts:
  REQUIRED:        282
  STRUCTURAL:       89
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.18 Bounded Internal Processing
                              Window (PR #23)
Current campaign:             Phase 3.19 Internal Feedback Loop
                              Prototype
Next eligible step:           Step 1 mission sync and roadmap
                              install (this file's first step)
Canonical design seed:        PHASE3_19_INTERNAL_FEEDBACK_LOOP_ROADMAP.md
```

Inherited follow-ups deliberately deferred:

```text
- SelfModel implementation remains OUT OF SCOPE.
- /pattern-ledger / /coherence-summary / /growth-ledger UIs remain
  DEFERRED at catalog level.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- Tracer wiring through OperatorSession.dispatch remains DEFERRED.
- Coherence Monitor feedback (architecture C) may ship as a v1
  read-only branch or remain DEFERRED depending on Step 4 LOCK F.
- Combined pattern + coherence feedback (architecture D) is
  DEFERRED unless Step 5 explicitly bundles it.
- REPL / worldlet feedback (architectures D / E) remain
  DEFERRED.
- Real-model reflection over feedback events remains DEFERRED.
```

---

## Operational target

Phase 3.19 uses this operational definition:

```text
Bounded internal feedback WORKS iff:
  - OperatorSession.feedback_mode = FEEDBACK_MODE_PATTERN_LEDGER
    drives _run_processing_window to emit, in addition to the
    Phase 3.18 rehearsal chunks, a bounded number of feedback
    chunks whose text is a deterministic Pattern Ledger summary
    string derived from the live entry's pattern_id /
    recurrence_count / saturation_state.
  - Each feedback chunk has provenance prefix
    "internal_processing_window:<k>:pledger_summary".
  - Each feedback chunk drives Pattern Ledger.observe and Growth
    Ledger.observe through the existing _append_stream_chunk
    call site (no new emission code, no new GrowthEventType).
  - The feedback chunks produce SECOND-ORDER Pattern Ledger
    entries whose structural signature differs from the seed
    chunk's structural signature (they are derived from a
    different deterministic text shape).
  - Pattern Ledger reaches a final state with: 1 first-order
    entry (the seed pattern) AND 1 second-order entry (the
    feedback pattern); both have deterministic pattern_ids.
  - Recurrence counts match deterministic formulas (no off-by-
    one, no float drift).
  - Same input + same configuration produces the same Pattern
    Ledger / Growth Ledger state across runs / processes / OSes.
  - Zero real model calls; brain/tick.py untouched; cache
    counters unchanged; no schema change; OFFLINE default
    preserved.
  - The non-claim audit (canonical
    _FORBIDDEN_NON_CLAIM_TERMS tuple) passes against the new
    feedback-summary text generator and every bounded printable
    string the module produces.

Coherence Monitor feedback (architecture C) SHIPS only if Step 4
LOCK F authorizes a bounded read-only summary that does NOT touch
truth claims, scalar I-ness, or aggregate scoring; otherwise
DEFERRED.

Combined feedback (architecture D) is DEFERRED unless Step 5
explicitly bundles it.
```

---

## Real model call budget

```text
Max 20 real external model-backed calls total across the campaign.
Phase 3.19 expects to consume ZERO real model calls because the
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
no Coherence Monitor semantic change
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
no runtime change that elevates the "internal feedback" surface
  above bounded printable record identifiers + ints + Fractions
```

---

## Macro sequence

```text
Step 1   Mission sync + roadmap
Step 2   Internal feedback synthesis
Step 3   Internal feedback probe matrix
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

Purpose: install Phase 3.19 as the current mission and land the
Phase 3.19 roadmap at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_19_INTERNAL_FEEDBACK_LOOP_ROADMAP.md
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

Required work: write Phase 3.19 mission / campaign / roadmap;
verify gate_runner --json green.

Commit message:

```text
phase3.19 step1: internal feedback mission sync
```

Push.

---

# Step 2 — Internal feedback synthesis

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_SYNTHESIS.md
```

Required analysis (per Phase 3.19 mission):

```text
1. Current Phase 3.18 mechanism (rehearsal-only).
2. Gap (recurrence does not feed back; Coherence Monitor is
   read-only; Growth Ledger records; no REPL/worldlet
   participation).
3. Proposed feedback loop and event shape.
4. Candidate architectures A-F (see roadmap).
5. Human-development analogy (carefully bounded).
6. Testable hypotheses H1-H7.
7. Recommended v1 (pattern-ledger feedback only; coherence
   feedback either bundled bounded-read-only or DEFERRED;
   no model-generated reflection; no SelfModel).
```

Commit message:

```text
phase3.19 step2: internal feedback synthesis
```

Push.

---

# Step 3 — Internal feedback probe matrix

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_PROBE_MATRIX.md
```

Matrix:

```text
- window sizes: 0, 5, 10, 50
- modes: rehearsal-only, pattern feedback, coherence feedback (if
  in scope), combined feedback (if in scope)
- inputs: repeated motif, contradiction pair, self-reference
  phrase, neutral factual text, emotionally valenced text
- measurements: stream chunk count, rehearsal step count, pattern
  entries, recurrence_count, confidence, saturation_state, Growth
  Ledger events, Coherence Monitor status, model call count if
  any, L1 / L2 cache counters if any, state mutation footprint,
  invariant status
```

If implementation does not yet support feedback, mark cells as
planned/probe-blocked and state exactly what runtime surface is
missing.

Commit message:

```text
phase3.19 step3: internal feedback probe matrix
```

Push.

---

# Step 4 — Corrigenda / design locks

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_CORRIGENDA.md
```

Lock LOCK A through LOCK J as described in the mission.

Commit message:

```text
phase3.19 step4: internal feedback corrigenda
```

Push.

---

# Step 5 — Catalog patch plan

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_CATALOG_PATCH_PLAN.md
```

Must include: exact implementation architecture, exact files,
exact row family + statuses, exact catalog version/count delta,
exact fixtures, exact behavior-report plan, exact non-goals,
review-gate decision request.

Commit message:

```text
phase3.19 step5: internal feedback catalog patch plan
```

Push.

---

# Step 6 — Review Gate A

Apply the autonomy authorization from `CURRENT_MISSION.md`. If
all ten conditions pass, record `Review Gate A — ACCEPT PLAN AS
WRITTEN` and proceed. If any fails, stop.

This step does NOT change files. Commit only if the gate-status
record is part of an updated doc artifact created in step 5 or
4; otherwise this step is a transition record only.

---

# Step 7 — Apply implementation

Implement bounded internal feedback per the accepted plan. Required
properties:

```text
- bounded deterministic feedback
- no tick.py change
- no real model calls by default
- no unbounded growth
- provenance on every internal feedback artifact
- no raw prompt/model response
- closed enums where appropriate
- constructor validation, no silent clamp except where existing
  pattern uses saturation
- tests for N = 0, 5, 10, 50
- tests for no non-claim language
```

Commit message:

```text
phase3.19 step7: implement internal feedback loop
```

Push.

---

# Step 8 — Behavior report

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_BEHAVIOR_REPORT.md
```

Run and report:

```text
- rehearsal-only baseline
- pattern feedback
- coherence feedback if implemented
- combined feedback if implemented
- N = 0 / 5 / 10 / 50
- deterministic repeatability
- distinct input independence
- saturation / cap behavior
- cache / call count if any
- invariant gates
- non-claim audit
```

Commit message:

```text
phase3.19 step8: internal feedback behavior report
```

Push.

---

# Step 9 — Findings

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_FINDINGS.md
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
phase3.19 step9: internal feedback findings
```

Push.

---

# Step 10 — Final audit

Create:

```text
docs/campaigns/phase3_19/PHASE3_19_INTERNAL_FEEDBACK_AUDIT.md
```

Verdict options:

```text
PASS                          : feedback path implemented and
                                demonstrated end-to-end
PASS WITH DEFERRED FOLLOW-UPS : feedback path shipped; coherence
                                feedback or combined feedback
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
phase3.19 step10: final internal feedback audit
```

Push.

---

# Step 11 — PR preparation

Open a PR to main with title:

```text
phase3.19: internal feedback loop prototype
```

PR body must include: PR URL, base/head, catalog version/counts,
what feedback was implemented, whether pattern recurrence now feeds
back into later processing, whether coherence feedback is included
or deferred, whether 50-tick processing window remains recommended,
validation, real model calls used, non-claims, next campaign
recommendation.

Do not merge.
