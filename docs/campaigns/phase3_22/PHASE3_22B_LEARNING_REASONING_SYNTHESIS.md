# PHASE3_22B_LEARNING_REASONING_SYNTHESIS.md

Phase 3.22b extends Phase 3.22 with two bounded engineering layers:

1. **Documented structural learning.** A session-local evidence layer
   that records observable state transitions (recurrence climbs,
   abstract-pattern acquisitions, transfer recognitions, REPL
   diminishing-returns updates, near-miss corrections) and exposes
   them as a printable, deterministic, non-claim-clean record.
2. **Explicit reasoning trace.** An external audit trail of
   deterministic structural operations that explains how each
   `AgentReply` was selected.

Phase 3.22b is a continuation of Phase 3.22 inside the same campaign
branch (`campaign/phase3-22-agent-communication-loop`) and the same
PR (#27). It does NOT introduce new TLICA Lean rows; every new
catalog row is an Engineering hypothesis under Phase 3.

## Non-claim discipline

These layers do NOT claim the runtime is conscious, sentient, aware,
or that it understands its input. They do NOT introduce a
consciousness/sentience/awareness/I-ness/maturity score. They do NOT
add a `SelfModel`. Every produced string passes the
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
audit (case-insensitive substring), and every new module's source is
audited the same way.

### Definitions

- **Structural learning** (Phase 3.22b): A documented operational
  property whose observable witness is a session-local state
  transition. The witness is one or more bounded
  `LearningEvidenceRecord` rows derived from `OperatorSession` and
  bridge state by pure deterministic functions. It is NOT memory in
  the psychological sense. It is NOT "knowing". It is a record of
  bounded structural events.
- **Structural reasoning trace** (Phase 3.22b): An explicit audit
  trail of deterministic structural operations the agent loop
  performed to select a reply. The trace is externally inspectable,
  bounded, printable, and non-claim-clean. It is NOT private
  chain-of-thought. It is NOT a metacognitive description of the
  system's "inner experience".

## Scope vs Phase 3.22

| Aspect | Phase 3.22 | Phase 3.22b |
|---|---|---|
| Modules added | 3 (`agent_repl_bridge.py`, `agent_loop.py`, `agent_benchmark.py`) | 3 (`abstract_pattern.py`, `learning_evidence.py`, `reasoning_trace.py`) |
| New catalog rows | 11 (I-AGENTLOOP-01..11) | 11 (I-AGENTLEARN-01..11) |
| Benchmark axes | 7 | 9 (adds A8 learning_evidence + A9 reasoning_trace) |
| `OperatorSession` schema change | none | none |
| `brain.tick.tick` import | forbidden | forbidden |
| `brain.llm.*` import | forbidden | forbidden |
| Real model calls in deterministic battery | 0 | 0 |
| Catalog version | v0.30 | v0.31 |

## Weak-behavior follow-ups carried into 3.22b

Phase 3.22b extends or sharpens the five known weak behaviors from
Phase 3.22:

- **W1 not_applicable overall-status.** Architectural blocker; keep
  as a documented `WARN`. The Phase 3.22b audit adds a proof-style
  paragraph in the Findings doc explaining why public construction
  cannot reach it without violating invariants.
- **W2 abstract-pattern transfer.** Phase 3.22b adds the
  `brain/development/abstract_pattern.py` layer. It composes with
  the Pattern Ledger; it does NOT replace ledger semantics.
- **W3 refusal overbreadth.** Phase 3.22b refines the refusal trigger
  into a bounded cognitive-claim classifier so harmless structural
  uses are no longer flagged. The classifier remains deterministic,
  closed, and non-claim-clean.
- **W4 tick routing.** Phase 3.22b adds a dispatch-level trace step
  that documents the public surfaces used; tick path remains
  untouched in deterministic OFFLINE tests.
- **W5 REPL valid-effective.** Phase 3.22b preserves no-host-execution
  and adds a proof-shape paragraph documenting that "valid-effective"
  is a local structural consequence; the diminishing-returns evidence
  layer cites the prior local consequence in later replies.

## LOCK list (Phase 3.22b)

LOCK L — `derive_abstract_pattern_signature(text)` is a pure
deterministic function from `str` to a frozen / slotted
`AbstractPatternSignature` record. It performs token-equality and
recurrence-class detection only; it does not compute semantic
embeddings.

LOCK M — `LearningEvidenceRecord` carries a closed
`LearningEvidenceKind` enum, a session-local interaction id, a
bounded printable summary, and bounded pre/post integer fact tuples.
It is frozen and slotted.

LOCK N — `LearningEvidenceTrace` is a bounded tuple of records under
`LEARNING_TRACE_MAX_RECORDS`. Two equivalent sessions advanced by the
same operator-input sequence produce equal `LearningEvidenceTrace`
records.

LOCK O — `LearningProofReport` is a bounded record with the trace,
integer counters per kind, a 16-char digest, and a printable summary
line. Two equivalent traces produce equal reports.

LOCK P — `ReasoningTraceStep` carries a closed `ReasoningStepKind`
enum, an integer step number, bounded printable input/derived/next
strings, and a 16-char step digest. It is frozen and slotted.

LOCK Q — `ReasoningTrace` is a bounded tuple of steps under
`REASONING_TRACE_MAX_STEPS`. Two equivalent agent calls produce equal
`ReasoningTrace` records.

LOCK R — `ReasoningTraceReport` is a bounded record with the trace,
per-kind counters, a 16-char trace digest, and a printable summary
line. Two equivalent traces produce equal reports.

LOCK S — `AgentLoopResult` (Phase 3.22b) gains two optional fields:
`learning_evidence_trace: Optional[LearningEvidenceTrace]` and
`reasoning_trace: Optional[ReasoningTrace]`. Existing fields and
ordering are preserved. Optional defaults preserve backward
compatibility for any pre-Phase-3.22b construction sites in the
catalog; in practice the loop populates both fields on every call.

LOCK T — The refusal classifier remains deterministic and closed.
The classifier surface is `_classify_cognitive_claim(text) -> bool`,
implemented as a substring scan over a closed tuple
`_COGNITIVE_CLAIM_PHRASES`. The Phase 3.22 wider scan over
`_FORBIDDEN_NON_CLAIM_TERMS` remains as a defense-in-depth audit on
every produced string but is no longer the trigger; the trigger is
the narrower classifier. The wider audit still gates produced
strings against the canonical tuple.

LOCK U — No new module imports `brain.llm.*`, no new module calls
`brain.tick.tick`, no new module imports curses, subprocess, socket,
urllib, http, requests, pathlib, tempfile, shutil, threading,
asyncio, atexit, signal, importlib, time, random, math, hashlib (in
the development module files; `learning_evidence.py` and
`reasoning_trace.py` use a tiny internal digest computed via
`stdlib hashlib` only at the report-construction boundary, mirroring
`agent_benchmark.py` precedent).

LOCK V — Catalog v0.30 → v0.31. Counts before: REQUIRED 303,
STRUCTURAL 94, NOT-EXERCISED 14, DEFERRED 15, OBSERVED 16. Counts
after: REQUIRED 312 (+9), STRUCTURAL 96 (+2), others unchanged.

## Benchmark axes

Phase 3.22b adds two axes to the closed deterministic benchmark
battery:

- **A8 learning_evidence** (7 cases A8.01–A8.07).
- **A9 reasoning_trace** (7 cases A9.01–A9.07).

Total cases: 39 (Phase 3.22) + 14 (Phase 3.22b) = 53.

Acceptance: existing 39 cases unchanged; new 14 cases PASS; A3.04
remains WARN; total benchmark `main` exits with code 2 (WARN-only).

## Out of scope (Phase 3.22b)

- No `SelfModel` implementation.
- No new `OperatorCommand`.
- No new `ACTIVE_VIEWS` value.
- No `GrowthEventType` / `GrowthEventSource` addition.
- No cross-session persistence; all evidence and traces are
  session-local.
- No external execution surface (no subprocess, no filesystem
  writes, no network).
- No claim of consciousness, sentience, awareness, agency, will,
  desire, belief, intent, introspection, metacognition, or
  understanding.
