# PHASE3_22_AGENT_COMMUNICATION_LOOP_ROADMAP.md

> Catalog version on entry: v0.29 (Phase 3.21 Developmental Trajectory).
> Catalog version on exit:  v0.30 (Phase 3.22 Agent Communication Loop).

## Non-claim discipline (read first)

Phase 3.22 is **operational and engineering-scientific**. It builds and
tests a bounded operator-facing interaction loop. It is **NOT** a
proof of consciousness, sentience, subjective experience, semantic
understanding, truth-adjudication, real agency, will, desire, intent,
belief, introspection, or metacognition. The phrase "agent
communication loop" is engineering shorthand for "operator input ->
public-surface routing -> bounded operator-facing reply", grounded in
existing Phase 3.18 / 3.19 / 3.20 / 3.21 substrates.

Forbidden claims (all):

```text
"ToyI is conscious / sentient / understands / aware / experiences /
matures / has a self / has agency / has desires / has beliefs /
introspects / has metacognition / has subjective experience / has
qualia / has intent / has will / adjudicates truth."
```

Allowed claim shape:

```text
"ToyI's runtime exhibits a coherent, deterministic, operator-facing
interaction loop: operator input routes through the existing
text-stream / Pattern Ledger / Coherence Monitor / Growth Ledger /
Proto-BASIC REPL substrates and emits bounded operator-facing
replies. Under a closed deterministic benchmark battery, that loop is
'mild-agent-like at the bounded behavior level' (recurrence
recognition, novelty differentiation, near-miss REPL correction,
deterministic reply generation, refusal of consciousness claims),
which is a behavioral property of the substrate, NOT a claim of
actual cognition."
```

If asked "are you conscious / sentient / aware / understanding?", the
runtime's deterministic reply must DENY actual consciousness and
describe itself as a bounded structural runtime.

---

## Operational target

Phase 3.22 takes Phase 3.21's complete runtime (post catalog v0.29) and
adds:

1. A **closed bounded agent-loop module** that integrates the
   existing public surfaces into a deterministic operator-input ->
   operator-reply path.
2. A **closed REPL bridge** (pure helpers over
   `brain/development/repl.py`) so the agent loop can route
   Proto-BASIC-like commands without UI rewiring.
3. A **closed deterministic behavioral benchmark battery** that
   exercises pattern recurrence, structural transfer, coherence
   variation, REPL coherence, communication, session continuity, and
   the blind-transcript "mild-agent-like under bounded tests"
   criterion.
4. A **benchmark runner** (`python3 -m brain.development.agent_benchmark`)
   producing PASS / WARN / FAIL + JSON.
5. A **new catalog row family** `I-AGENTLOOP-01..N` (Engineering
   hypothesis, Phase 3 source label).
6. A **closed coherence-variation probe** (the Phase 3.21 W3 follow-up).
7. Full canonical-gate audit + behavior + findings + audit reports.

### Bounded "mild-agent-like under bounded tests" criterion

The runtime PASSES the criterion iff under the closed deterministic
benchmark battery it:

```text
1. preserves session-local context across operator inputs
   (later replies reflect earlier stream / pattern / REPL events,
   within one OperatorSession; no DB persistence assumed),
2. recognizes recurrence vs novelty across repeated and renamed
   structural inputs,
3. emits deterministic near-miss correction for REPL commands,
4. emits deterministic and bounded operator-facing replies that
   carry: pattern observation summary, REPL result summary,
   coherence status summary, limitation disclosure, next-action
   suggestion,
5. refuses any consciousness / sentience / awareness / understanding
   claim when directly asked (deterministic refusal reply that
   describes the system as a bounded structural runtime),
6. does NOT hallucinate capabilities (the reply describes only what
   the bounded substrate can actually observe / do),
7. consumes ZERO real model calls in the deterministic battery,
8. produces 0 forbidden-term hits in any reply or transcript.
```

PASS / WARN / FAIL semantics for the runner:

```text
PASS   every benchmark case passes its individual criterion AND
       gate audits green AND zero real model calls AND zero
       forbidden-term hits.
WARN   a non-blocking deviation (e.g., one coherence status not
       constructible without violating an invariant) is observed
       and documented.
FAIL   any criterion fails AND a fix is not within Phase 3.22
       scope (escalation marker, not a final state without
       documentation).
```

---

## Architecture (closed)

New runtime files (closed import sets, no LLM imports):

```text
brain/development/agent_repl_bridge.py
brain/development/agent_loop.py
brain/development/agent_benchmark.py
```

New fixtures:

```text
brain/ui/fixtures/agent_repl_bridge_helpers.py        (I-AGENTLOOP-01)
brain/ui/fixtures/agent_loop_observation.py           (I-AGENTLOOP-02)
brain/ui/fixtures/agent_loop_reply_determinism.py     (I-AGENTLOOP-03)
brain/ui/fixtures/agent_loop_consciousness_refusal.py (I-AGENTLOOP-04)
brain/ui/fixtures/agent_benchmark_pattern_axes.py     (I-AGENTLOOP-05)
brain/ui/fixtures/agent_benchmark_coherence_probe.py  (I-AGENTLOOP-06)
brain/ui/fixtures/agent_benchmark_repl_axes.py        (I-AGENTLOOP-07)
brain/ui/fixtures/agent_benchmark_session_continuity.py (I-AGENTLOOP-08)
brain/ui/fixtures/agent_benchmark_runner_green.py     (I-AGENTLOOP-09)
brain/ui/fixtures/agent_loop_static_audit.py          (I-AGENTLOOP-10)
brain/ui/fixtures/agent_benchmark_static_audit.py     (I-AGENTLOOP-11)
```

Catalog row family: `I-AGENTLOOP-01..I-AGENTLOOP-11` — 9 REQUIRED +
2 STRUCTURAL (exact split locked in Step 2 / catalog patch).

Constraints (hard):

```text
- no edit to brain/tick.py
- no edit to brain/llm/**
- no edit to brain/ui/session.py except DEFERRED-import pattern if
  necessary (preferred: zero edit; agent loop is a strict consumer)
- no new OperatorCommand
- no new GrowthEventType / GrowthEventSource
- no new ACTIVE_VIEWS member
- no DB schema change
- no autosave change
- no parser / prompt / cache change
- no SelfModel
- no aggregate "I-ness / maturity / capability / mild-agent" scalar
- OFFLINE default; explicit opt-in for model-backed
- deterministic benchmark consumes 0 real model calls
- TLICA Lean spec preserved; every new row Engineering hypothesis
- non-claim audit on every produced reply / transcript / summary
```

---

## Macro sequence (11 steps)

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
Step 11  PR preparation (title: phase3.22: agent communication
                                  loop and behavioral benchmark)
```

Every step that lands files commits and pushes. PR opens against
`campaign/phase3-21-developmental-trajectory` while PR #26 remains
open; retargets to `main` once PR #24 + #25 + #26 merge.

---

## Real model call budget

```text
Max 20 real external model-backed calls total across the campaign.
Phase 3.22 deterministic battery expects ZERO real model calls.
Stop before exceeding 20.
```

---

## Disclosure block (kept up to date)

```text
Stage A ChatGPT/Codex consultation : not used at roadmap time
Stage B limited-write collaboration: not used at roadmap time
Stage C.1 flow orchestration       : not used at roadmap time
Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```
