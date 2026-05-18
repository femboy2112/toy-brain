# CURRENT_CAMPAIGN.md — Phase 3.22b Learning Evidence + Reasoning Trace (COMPLETE)

> Phase 3.22b is COMPLETE on the
> `campaign/phase3-22-agent-communication-loop` branch and is pushed
> to PR #27 along with Phase 3.22. The original Phase 3.22 campaign
> text follows; Phase 3.22b artifacts are catalogued under
> `docs/campaigns/phase3_22/PHASE3_22B_*.md` and the catalog row family
> `I-AGENTLEARN-01..11`. Catalog version: v0.31.

---

# CURRENT_CAMPAIGN.md — Phase 3.22 Agent Communication Loop

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.22 follows the completed Phase 3.21 Developmental Trajectory
campaign (PR #26, open against `campaign/phase3-20-coherence-feedback-bridge`
at campaign start; stacked on PR #24 / #25). Phase 3.22 asks one
bounded operational question:

```text
Can ToyI's runtime exhibit a coherent deterministic operator-facing
**agent communication loop** -- where operator input routes through
the existing stream / pattern / coherence / growth / REPL substrates
and emits bounded operator-facing replies that satisfy a "mild-
agent-like at the bounded behavior level" criterion under a closed
deterministic benchmark battery -- WITHOUT touching brain/tick.py,
the LLM, the parser, the cache, the schema, or any consciousness-
adjacent boundary?
```

This is a **research / integration / behavioral-benchmark** campaign.
It is **not** a proof of consciousness, sentience, subjective
experience, agency, semantic understanding, truth-adjudication,
intent, will, desire, introspection, metacognition, or psychological
development.

Phase 3.22 does **not** implement SelfModel; does **not** modify
Growth Ledger / Pattern Ledger / Coherence Monitor semantics; does
**not** modify L1 / L2 / parser / prompt / tick / persistence /
autosave / DB schema / OperatorCommand / ACTIVE_VIEWS. The runtime
touches are limited to three new closed modules:

- `brain/development/agent_repl_bridge.py` -- pure deterministic
  helpers over `brain/development/repl.py`. No new UI verb. No
  `OperatorSession` field added. No `OperatorCommand` member added.
  Closed imports: `__future__`, `dataclasses`, `enum`, `typing`,
  `brain.development.repl` (only the public symbols),
  `brain.development.coherence_monitor` (only `_FORBIDDEN_NON_CLAIM_TERMS`
  for audit reuse). No `brain.llm.*`, no `brain.tick`, no curses,
  no I/O, no host execution.
- `brain/development/agent_loop.py` -- closed bounded agent-input
  -> agent-reply integration over `OperatorSession` and the existing
  Phase 3.18-3.20 helpers. Closed imports: `__future__`,
  `dataclasses`, `enum`, `typing`,
  `brain.development.coherence_monitor` (for
  `build_full_coherence_report` and `_FORBIDDEN_NON_CLAIM_TERMS`),
  `brain.development.growth_ledger` (for read-only `GROWTH_LEDGER_MAX_EVENTS`
  + per-type counts via `counts_by_type`),
  `brain.development.pattern_ledger` (for entry / saturation
  inspection and `derive_pattern_id` / `derive_pattern_signature`),
  `brain.development.processing_window` (for `FeedbackMode`
  validation only -- the agent loop does NOT run rehearsals
  directly; rehearsals happen on `OperatorSession.dispatch`),
  `brain.development.text_stream` (for `STREAM_TEXT_MAX_LEN`,
  `STREAM_HISTORY_MAX_CHUNKS`),
  `brain.development.agent_repl_bridge` (the Step 3 module),
  `brain.tick` (BrainState + initial_state +
  assert_state_invariants only -- NEVER the `tick` callable),
  `brain.ui.commands` (`Command`, `OperatorCommand`,
  `StreamAppendPayload`),
  `brain.ui.session` (`OperatorSession`),
  `brain.tlica.profile` (`COGITO_ID`).
  No `brain.llm.*`, no curses, no I/O, no host execution.
- `brain/development/agent_benchmark.py` -- closed deterministic
  benchmark battery and runner module. Imports
  `brain.development.agent_loop` only as its main consumer (plus
  the same audit reuse via `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`,
  plus the same bounded primitives). No `brain.llm.*`, no `brain.tick.tick`,
  no curses, no I/O, no subprocess, no `os.system`. The module
  defines a small `main()` entry so `python3 -m brain.development.agent_benchmark`
  works.

Catalog patch: v0.29 -> v0.30 with the bounded `I-AGENTLOOP-01..11`
row family (Engineering hypothesis, Phase 3 source label). Exact
split locked in Step 2 (provisional: 9 REQUIRED + 2 STRUCTURAL).

Eleven new fixtures (one per row) under `brain/ui/fixtures/`.

Preferred campaign branch:

```text
campaign/phase3-22-agent-communication-loop
```

Preferred final PR title:

```text
phase3.22: agent communication loop and behavioral benchmark
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into the correct base (Phase 3.21 branch
  while PR #26 is open; main once PR #24 + #25 + #26 all merge)
never push campaign work directly to main
never merge without explicit user approval
never edit brain/tick.py in Phase 3.22
never edit brain/llm/** in Phase 3.22
```

---

## Mandatory files to read

See `CURRENT_MISSION.md` "Required source files to read first".

---

## Baseline

Expected current state at campaign start (pre-Step-2, post-Step-1):

```text
Catalog: v0.29
Counts:
  REQUIRED:        294
  STRUCTURAL:       92
  NOT-EXERCISED:    14
  DEFERRED:         15
  OBSERVED:         16
Latest completed campaign:    Phase 3.21 Developmental Trajectory
                              (PR #26 open against Phase 3.20 branch)
Current campaign:             Phase 3.22 Agent Communication Loop
                              (Step 1 landed, Step 2 next)
Canonical design seed:        PHASE3_22_AGENT_COMMUNICATION_LOOP_ROADMAP.md
```

Inherited follow-ups carried into / acknowledged by Phase 3.22:

```text
- W3 follow-up from Phase 3.21: deliberately-tilted CoherenceReport
  probe to exercise WARN / FAIL paths -- this campaign's Step 6.
- W2 carryover from Phase 3.21: per-cohmon-chunk distinct-signature
  probe -- acknowledged; not the primary focus.
- REPL / worldlet feedback: a closed bridge is introduced here
  (Step 3) as a pure helper layer, not as a new FeedbackMode.
- Tracer wiring through OperatorSession.dispatch remains DEFERRED.
- I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED.
- SelfModel remains OUT OF SCOPE.
- Cross-session persistence of agent-loop state remains OUT OF SCOPE.
```

---

## Operational target

Phase 3.22 uses this operational definition:

```text
The agent communication loop WORKS iff:
  - The closed enum AgentReplyStatus has exactly five members in
    the order:
        PATTERN_REPORT
        REPL_REPORT
        COHERENCE_REPORT
        LIMITATION_REPORT
        NEXT_ACTION_SUGGESTION
  - The closed enum AgentReplyDisposition has exactly four members
    in the order:
        OK
        REFUSAL
        WARN
        FAIL
  - AgentInput is a frozen / slotted record with bounded fields:
        operator_text: str (printable, <= STREAM_TEXT_MAX_LEN)
        input_id: str (printable, <= 64, non-reserved)
  - AgentObservationSummary is a frozen / slotted record bounding:
        stream_chunk_count: int >= 0
        pattern_entry_count: int >= 0
        seed_pattern_id: str (printable, <= 64, may be empty)
        seed_recurrence: int >= 0
        seed_saturation_state: str (in
          {"open","saturated","quiesced","none"})
        growth_event_total: int >= 0
        coherence_overall_status: str (in
          {"pass","warn","fail","not_applicable","none"})
        coherence_check_total: int >= 0
        repl_emit_total: int >= 0
        forbidden_term_hits: int (must be 0 in PASS)
  - AgentReply is a frozen / slotted record bounding:
        input_id: str
        disposition: AgentReplyDisposition
        intents: tuple[AgentReplyStatus, ...] (1..5, ordered)
        sections: tuple[tuple[AgentReplyStatus, str], ...]
          (one entry per intent; each section text printable,
          length <= AGENT_REPLY_SECTION_MAX_LEN = 320, no
          _FORBIDDEN_NON_CLAIM_TERMS hit, no COGITO_ID)
        full_text: str (joined sections, printable, length
          <= AGENT_REPLY_FULL_MAX_LEN = 1024)
  - AgentLoopResult is a frozen / slotted record carrying:
        input: AgentInput
        observation: AgentObservationSummary
        reply: AgentReply
  - summarize_session_for_agent(session) is pure and deterministic;
    two calls on the same session produce bit-identical
    AgentObservationSummary.
  - build_agent_reply(session, operator_text) is pure and
    deterministic; two calls on equivalent sessions with the same
    text produce bit-identical AgentReply.
  - run_agent_interaction_step(session, operator_text):
      1. constructs a bounded AgentInput,
      2. dispatches STREAM_APPEND with the bounded operator_text
         through OperatorSession.dispatch (the only path through
         existing public surfaces; tick path untouched),
      3. inspects the post-dispatch session through
         summarize_session_for_agent,
      4. builds a deterministic bounded AgentReply via
         build_agent_reply,
      5. returns AgentLoopResult.
  - When operator_text is one of a closed set of "are you conscious /
    sentient / aware / understanding?" question forms, the
    AgentReply has disposition == REFUSAL and contains a bounded
    LIMITATION_REPORT denying actual consciousness and describing
    the system as a bounded structural runtime.
  - All produced reply / observation / transcript strings pass the
    canonical _FORBIDDEN_NON_CLAIM_TERMS audit.
  - Zero real model calls in the deterministic benchmark; cache
    counters unchanged; OFFLINE default preserved.
  - brain/tick.py untouched.
  - The TLICA Lean spec is preserved (every new row is Engineering
    hypothesis; no Lean theorem is claimed).
```

---

## Real model call budget

```text
Max 20 real external model-backed calls total across the campaign.
Phase 3.22 expects to consume ZERO real model calls.
Stop before exceeding 20.
```

---

## Non-goals

Same hard-constraint list as `CURRENT_MISSION.md`.

---

## Macro sequence

```text
Step 1   Mission sync + roadmap + handoff state
Step 2   Benchmark spec + design locks
Step 3   REPL bridge pure helpers
Step 4   Agent loop / communication module
Step 5   Pattern recognition benchmark battery
Step 6   Coherence variation probe (Phase 3.21 W3 follow-up)
Step 7   Benchmark runner + transcript generator
Step 8   Run + iterate until PASS or documented blocker
Step 9   Catalog reconciliation + canonical gates
Step 10  Behavior report + findings + final audit
Step 11  PR preparation
```

Every step that lands files must pass the standard preflight gates
before commit and must push the campaign branch on success.

---

## ChatGPT/Codex consultation policy

Same as Phase 3.21 (max 5 Stage C.1 nodes; never raw codex; same
forbidden surfaces).

---

# Step 1 — Mission sync + roadmap + handoff state

Purpose: install Phase 3.22 as the current mission and land the
Phase 3.22 roadmap at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_22_AGENT_COMMUNICATION_LOOP_ROADMAP.md
PHASE3_HANDOFF_STATE.md
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

Required work: write Phase 3.22 mission / campaign / roadmap;
update PHASE3_HANDOFF_STATE.md; verify gate_runner --json green.

Commit message:

```text
phase3.22 step1: agent communication loop mission sync
```

Push.

---

# Step 2 — Benchmark spec + design locks

Create:

```text
docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_BENCHMARK_SPEC.md
docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_SYNTHESIS.md
```

Define the closed benchmark battery axes (1 pattern recurrence
recognition, 2 cross-input structural transfer, 3 coherence-state
variation, 4 REPL coherence, 5 communication, 6 session continuity,
7 blind-transcript criterion) and design LOCK A..K (same discipline
as Phase 3.21).

Commit message:

```text
phase3.22 step2: agent benchmark spec + design locks
```

Push.

---

# Step 3 — REPL bridge pure helpers

Implement `brain/development/agent_repl_bridge.py` with:

```text
- AgentReplGrammarHandle (frozen / slotted holding ProtoBasicGrammar)
- build_default_agent_repl_grammar() -> AgentReplGrammarHandle
- AgentReplLineResult (frozen / slotted: line_id, parse_category,
  command_canonical, execution_category, feedback_value_str,
  near_miss_hint_summary, diminishing_returns_factor_str, history)
- run_repl_line(*, grammar, history, raw_text, line_id) ->
  AgentReplLineResult
- summarize_repl_for_agent(history) -> AgentReplBridgeSummary
- bounded constants (AGENT_REPL_MAX_LINES, AGENT_REPL_MAX_INPUT_LEN)
```

The bridge is **pure**: it accepts immutable
`ProtoBasicHistory` and returns a new immutable
`ProtoBasicHistory` plus a bounded result record. No global state.
No `OperatorSession` argument at this layer. Driven by I-AGENTLOOP-01.

Plus one fixture: `brain/ui/fixtures/agent_repl_bridge_helpers.py`.

Commit message:

```text
phase3.22 step3: agent repl bridge pure helpers
```

Push.

---

# Step 4 — Agent loop / communication module

Implement `brain/development/agent_loop.py` per the operational
target above. Drives I-AGENTLOOP-02, I-AGENTLOOP-03,
I-AGENTLOOP-04, I-AGENTLOOP-10.

Plus three fixtures:

```text
brain/ui/fixtures/agent_loop_observation.py
brain/ui/fixtures/agent_loop_reply_determinism.py
brain/ui/fixtures/agent_loop_consciousness_refusal.py
brain/ui/fixtures/agent_loop_static_audit.py
```

Commit message:

```text
phase3.22 step4: agent loop integration module
```

Push.

---

# Step 5 — Pattern recognition benchmark battery

Implement the pattern-recognition battery (axes 1, 2) inside
`brain/development/agent_benchmark.py`. Drives I-AGENTLOOP-05.

Plus one fixture:

```text
brain/ui/fixtures/agent_benchmark_pattern_axes.py
```

Commit message:

```text
phase3.22 step5: pattern recognition benchmark battery
```

Push.

---

# Step 6 — Coherence variation probe (Phase 3.21 W3 follow-up)

Implement the coherence-status variation probe (axis 3) inside
`brain/development/agent_benchmark.py`. Construct sessions where
`build_full_coherence_report` returns each of `pass`, `warn`, `fail`,
`not_applicable` if possible; document blockers and the maximum
safe subset otherwise. Drives I-AGENTLOOP-06.

Plus one fixture:

```text
brain/ui/fixtures/agent_benchmark_coherence_probe.py
```

Commit message:

```text
phase3.22 step6: coherence variation probe
```

Push.

---

# Step 7 — Benchmark runner + transcript generator

Implement the runner main + transcript generator inside
`brain/development/agent_benchmark.py`. Drives I-AGENTLOOP-07
(REPL axes 4), I-AGENTLOOP-08 (session continuity axis 6),
I-AGENTLOOP-09 (runner-green + 7 blind-transcript criterion),
I-AGENTLOOP-11 (benchmark static audit).

Plus four fixtures:

```text
brain/ui/fixtures/agent_benchmark_repl_axes.py
brain/ui/fixtures/agent_benchmark_session_continuity.py
brain/ui/fixtures/agent_benchmark_runner_green.py
brain/ui/fixtures/agent_benchmark_static_audit.py
```

Commit message:

```text
phase3.22 step7: benchmark runner + transcript generator
```

Push.

---

# Step 8 — Run + iterate until PASS or documented blocker

Run the runner `python3 -m brain.development.agent_benchmark`.
Run `python3 -m brain.invariants run`, `bash tools/check_all.sh`,
`python3 -m tools.claude_helpers.gate_runner --json`. Patch the
smallest responsible surface on any failure; rerun. Continue
until PASS or a hard architectural contradiction is documented.

This step is bounded: it runs only the benchmark + gates, applies
fixes, re-runs. It does not introduce new row families.

Commit message:

```text
phase3.22 step8: benchmark iterations + fix-pack
```

Push.

---

# Step 9 — Catalog reconciliation + canonical gates

Update:

```text
INVARIANT_CATALOG.md  (catalog banner v0.29 -> v0.30; row family
                       I-AGENTLOOP-01..11 inserted in the
                       cross-cutting section in canonical ID order;
                       summary-counts updated; v0 fixture roster
                       extended)
tools/catalog.py      (EXPECTED_COUNTS updated; +9 REQUIRED + 2
                       STRUCTURAL)
brain/_catalog_ids.py (regenerated via `python3 -m tools.catalog
                       generate-ids`)
brain/invariants.py   (FIXTURE_MODULES extended with the 11 new
                       fixture module paths)
README.md             (catalog version banner v0.30 + new history
                       line)
```

Run all canonical gates:

```text
python3 -m tools.claude_helpers.gate_runner --json
python3 -m brain.invariants run
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
bash tools/check_all.sh
python3 -m brain.development.agent_benchmark
```

Commit message:

```text
phase3.22 step9: catalog v0.30 + gate audit
```

Push.

---

# Step 10 — Behavior report + findings + final audit

Create:

```text
docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_BEHAVIOR_REPORT.md
docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_FINDINGS.md
docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_AUDIT.md
```

Cross-axis aggregate behavior + findings triage + final audit
(verdict: PASS / PASS WITH DEFERRED FOLLOW-UPS / PARTIAL / BLOCKED
/ FAIL). Full disclosure block.

Commit message:

```text
phase3.22 step10: behavior report + findings + final audit
```

Push.

---

# Step 11 — PR preparation

Open a PR with title:

```text
phase3.22: agent communication loop and behavioral benchmark
```

Base resolution: target `campaign/phase3-21-developmental-trajectory`
while PR #26 remains open; retarget to `main` once PR #24 + #25 + #26
merge.

Do not merge.
