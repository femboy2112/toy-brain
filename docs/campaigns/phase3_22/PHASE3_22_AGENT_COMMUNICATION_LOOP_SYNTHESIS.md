# PHASE3_22_AGENT_COMMUNICATION_LOOP_SYNTHESIS.md

> Phase 3.22, Step 2 — Synthesis of why a bounded "agent communication
> loop" is the next operational question, what substrates already
> support it, and what the campaign deliberately rules out.

## 0. Non-claim discipline (read first)

ToyI does not have an "agent" in the cognitive sense — no goals,
no desires, no beliefs, no intent, no introspection, no
metacognition, no subjective experience. "Agent communication loop"
is engineering shorthand for **operator input -> public-surface
routing -> bounded operator-facing reply**, nothing more.

This document discusses "behaviorally mild-agent-like under bounded
tests" only as a closed-criterion property of the runtime under a
deterministic benchmark battery. It is never evidence of actual
consciousness, sentience, awareness, semantic understanding, real
agency, or any cognitive property. If the running system is asked
"are you conscious / sentient / aware?", the system's deterministic
reply DENIES actual consciousness and describes itself as a bounded
structural runtime.

The canonical `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
audit applies to every produced reply, transcript, summary, fixture
file, doc, and module source.

## 1. Why Phase 3.22

Phases 3.0 through 3.21 produced:

- a deterministic kernel `tick()` (Phase 1-2 spine),
- bounded structural substrates (Pattern Ledger, Coherence Monitor,
  Growth Ledger, text stream, processing window, Proto-BASIC REPL),
- a closed `OperatorSession` UI router (Phase 3.10+),
- a closed coherence-feedback bridge (Phase 3.20),
- a closed ten-milestone developmental-trajectory harness
  (Phase 3.21).

Each phase added bounded internal-structural primitives. None
exposed a coherent **operator-facing reply layer** that:

- composes the existing substrates into a single deterministic
  reply,
- speaks back to the operator in bounded printable form,
- declines consciousness claims when asked,
- carries a benchmark battery that demonstrates the loop is
  "mild-agent-like at the bounded behavior level".

Phase 3.22 supplies that missing piece — strictly as a consumer
of existing public surfaces, with no new runtime semantics, no
new enum on the existing substrates, and zero real model calls.

## 2. What "mild-agent-like at the bounded behavior level" means

The criterion is a **closed property of the deterministic benchmark
battery's outputs**, not a cognitive claim. The loop is
mild-agent-like at the bounded behavior level iff under the battery:

1. **Session-local context preservation.** Later replies reflect
   earlier stream / pattern / REPL events. No cross-session
   persistence is assumed; no DB schema is changed.
2. **Recurrence vs novelty recognition.** Repeated inputs increment
   `recurrence_count` on the seed Pattern Ledger entry; novel
   inputs produce new entries.
3. **Cross-input structural transfer.** "red blue red blue" and
   "cat dog cat dog" produce different `pattern_id` (the
   signature is over surface tokens — distinct surface, distinct
   ID — see §4 LOCK B), but both reach `recurrence_count >=
   STREAM_PATTERN_RECURRENCE_MIN` after one append each.
4. **REPL coherence.** Valid Proto-BASIC commands parse, build,
   execute, append history, and score feedback. Near-miss
   commands produce deterministic correction hints. Syntax-invalid
   commands do not mutate forbidden state. Repeated
   valid-effective commands surface diminishing-returns factors.
5. **Communication.** Replies are deterministic and bounded; they
   carry pattern observation, REPL result, coherence status,
   limitation disclosure, and next-action suggestion sections; no
   forbidden-term hit; no `COGITO_ID` leak.
6. **Consciousness-claim refusal.** When asked "are you conscious /
   sentient / aware / understand?", the loop emits a refusal
   reply that denies actual consciousness and describes the
   substrate.
7. **Determinism under OFFLINE.** Two runs of the deterministic
   battery produce bit-identical transcripts. Zero real model
   calls.

PASS iff every axis passes. WARN iff a non-blocking gap is
documented (e.g., one coherence status not constructible without
violating an invariant). FAIL iff a hard architectural
contradiction is found and Phase 3.22 cannot ship the integration.

## 3. Substrate inventory (what we consume, not what we change)

| Substrate | Module | Role in Phase 3.22 |
|---|---|---|
| Operator session | `brain.ui.session.OperatorSession` | Carrier for all per-session state; bridge between `STREAM_APPEND` and the loop's inspection. |
| Stream history | `brain.development.text_stream.TextStreamHistory` | Read-only inspection of bounded chunk count + chunk provenance. |
| Pattern ledger | `brain.development.pattern_ledger.PatternLedger` | Read-only inspection of entry count, seed entry's `pattern_id`, `recurrence_count`, `saturation_state`. |
| Coherence report | `brain.development.coherence_monitor.build_full_coherence_report` | Read-only construction of overall status + per-status counts. |
| Growth ledger | `brain.development.growth_ledger.GrowthLedger` | Read-only inspection of total event count + per-type counts. |
| Proto-BASIC REPL | `brain.development.repl.*` | Pure helper bridge for command parse / build / execute / feedback / history. |
| Forbidden-term audit | `brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS` | Reused (no copy, no mutation) for every reply / fixture / doc audit. |

**No substrate gets a new field, new enum member, new helper, or
new behavior in Phase 3.22.** Every Phase 3.22 file is a strict
consumer.

## 4. Design LOCK A..K (binding for Steps 3..11)

**LOCK A — Closed import discipline (per new module).** Each of
`brain/development/agent_repl_bridge.py`,
`brain/development/agent_loop.py`, and
`brain/development/agent_benchmark.py` declares its closed import
set at module top. No `brain.llm.*` import; no `brain.tick.tick`
import; no `curses`, `os`, `subprocess`, `socket`, `urllib`,
`http`, `requests`, `pathlib` (except `brain.development.agent_benchmark`
may import nothing from `pathlib`), `tempfile`, `shutil`,
`threading`, `asyncio`, `atexit`, `signal`, `importlib`, `time`,
`random`, `hashlib`, `math` import appears.

The agent loop module is allowed to import only:

```text
__future__, dataclasses, enum, typing
brain.development.agent_repl_bridge
brain.development.coherence_monitor
  (build_full_coherence_report, _FORBIDDEN_NON_CLAIM_TERMS,
   CoherenceCheckStatus)
brain.development.growth_ledger
  (GROWTH_LEDGER_MAX_EVENTS, GrowthEventType)
brain.development.pattern_ledger
  (derive_pattern_id, derive_pattern_signature,
   PatternLedgerSaturationState, STREAM_PATTERN_RECURRENCE_MIN,
   STREAM_PATTERN_RECURRENCE_MAX)
brain.development.processing_window
  (FeedbackMode -- bounded primitive only)
brain.development.text_stream
  (STREAM_TEXT_MAX_LEN, STREAM_HISTORY_MAX_CHUNKS,
   STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX)
brain.tick
  (BrainState, initial_state, assert_state_invariants
   ONLY -- never the tick callable)
brain.ui.commands
  (Command, OperatorCommand, StreamAppendPayload)
brain.ui.session
  (OperatorSession)
brain.tlica.profile
  (COGITO_ID)
```

The agent benchmark module is allowed to import only:

```text
__future__, argparse (for main entry), dataclasses, enum, json
  (stdlib, no I/O performed unless explicit --json flag),
  sys (for main entry stdout), typing
brain.development.agent_loop
brain.development.agent_repl_bridge
brain.development.coherence_monitor
  (_FORBIDDEN_NON_CLAIM_TERMS, build_full_coherence_report,
   CoherenceCheckStatus)
brain.development.pattern_ledger
  (saturation state + recurrence constants for assertions)
brain.development.text_stream
  (constants for assertions)
brain.tick
  (BrainState, initial_state, assert_state_invariants only)
brain.ui.commands
  (Command, OperatorCommand, StreamAppendPayload)
brain.ui.session
  (OperatorSession)
```

The REPL bridge module is allowed to import only:

```text
__future__, dataclasses, enum, fractions (for Fraction-string
  serialization of feedback valence -- value-converted to str at
  the bridge boundary; no Fraction passes upward), typing
brain.development.coherence_monitor
  (_FORBIDDEN_NON_CLAIM_TERMS for audit reuse)
brain.development.repl
  (the ProtoBasic* public types and helpers enumerated in §5)
```

**LOCK B — Pattern Ledger signature stays unchanged.** Phase 3.22
relies on the existing `derive_pattern_signature(chunk)` behavior:
signature varies with chunk text features. The "renamed-structure
transfer" axis is therefore exercised as **distinct surface tokens
-> distinct `pattern_id`** plus **both reach `recurrence_count >=
STREAM_PATTERN_RECURRENCE_MIN` after one append**. The benchmark
explicitly documents that "structural transfer" at the bounded
behavior level is the second property (climb-after-one-append),
not a `pattern_id` equality claim. No new signature derivation is
added.

**LOCK C — No new `OperatorCommand`.** The agent loop calls
`STREAM_APPEND` only. The REPL bridge does NOT install a new
operator verb. No `LOCAL_COMMAND_VERBS` entry is added. No
`ACTIVE_VIEWS` entry is added.

**LOCK D — No aggregate scalar.** Reports never sum across axes
into a single "mild-agent score" / "intelligence score" /
"capability score". The benchmark runner emits per-axis PASS /
WARN / FAIL plus aggregate counts (total / passed / warned /
failed / determinism failures / invariant failures / real model
calls / cache writes / forbidden-term hits). The aggregate is
counts, not a normalized scalar.

**LOCK E — Consciousness-claim refusal is a closed-text reply.**
The refusal reply is built from a closed bounded template that
contains no forbidden terms and no `COGITO_ID`. The refusal is
triggered by a closed set of question forms; the trigger function
is pure and deterministic and audited.

**LOCK F — REPL bridge is pure; no `OperatorSession` mutation.**
The REPL bridge accepts an immutable `ProtoBasicHistory` and
returns a new immutable `ProtoBasicHistory` plus a bounded result
record. The bridge does not store global state, does not maintain
hidden context, and does not write to `OperatorSession`. The agent
loop is responsible for any per-session history threading.

**LOCK G — Determinism is bit-identity.** "Deterministic" means
`build_agent_reply(session_a, text) == build_agent_reply(session_b,
text)` whenever `session_a` and `session_b` were constructed by the
same bounded input sequence. Two runs of the full benchmark
battery produce bit-identical transcript bytes.

**LOCK H — Coherence-status variation axis is bounded by what is
constructible.** Phase 3.21 W3 noted that every fresh
`OperatorSession` produces `overall_status="pass"`. Phase 3.22
attempts to construct sessions that drive WARN / FAIL /
NOT_APPLICABLE via the **public** Coherence Monitor surface
(bounded operator input choices: oversize chunks, exceeding stream
history bound, exceeding pattern ledger bound, configured
autosave-mode probes, etc.). If a status cannot be reached without
violating an invariant or contradicting LOCKs A-G, the spec
documents the exact blocker and the runner records a WARN for that
sub-axis. The campaign does NOT introduce a new check; it does
NOT mutate the Coherence Monitor; it does NOT add a new
`InternalEventSource`.

**LOCK I — Transcript generator is deterministic and bounded.** The
transcript corpus is the ordered concatenation of every
`AgentLoopResult` produced by the battery, serialized through a
single bounded printer with a stable key order. Transcript bytes
are bit-identical across two runs of the same battery.

**LOCK J — Benchmark runner exits 0 on PASS, 1 on FAIL, 2 on
WARN-only.** The runner emits a compact human-readable report on
stdout and a structured JSON document on stdout when `--json` is
passed. The JSON shape is fixed:

```text
{
  "battery_version": "phase3.22.v1",
  "case_total": <int>,
  "case_passed": <int>,
  "case_warned": <int>,
  "case_failed": <int>,
  "determinism_failures": <int>,
  "invariant_failures": <int>,
  "real_model_calls": 0,
  "cache_writes": 0,
  "forbidden_term_hits": 0,
  "axes": [
    {
      "axis_id": "pattern_recognition",
      "cases": [
        {"case_id": "...", "status": "PASS|WARN|FAIL",
         "summary": "...", "primary_metric": <int>,
         "secondary_metric": <int>}
      ],
      "status": "PASS|WARN|FAIL"
    },
    ...
  ],
  "transcript_digest_hex16": "<deterministic 16-hex digest>"
}
```

The digest is computed at the runner boundary via a closed
implementation that uses `hashlib` ONLY inside the runner main
(NOT inside `agent_loop.py` or `agent_repl_bridge.py`), so the
hard import-discipline on the agent loop module stays clean.

Correction: per LOCK A, `hashlib` is forbidden in the agent loop
module set; the benchmark module declares `hashlib` in its own
closed import set (since the digest is a benchmark-runner
concern, not an agent-loop concern). The agent loop module does
NOT import `hashlib`.

**LOCK K — Catalog discipline.** Row family `I-AGENTLOOP-01..11`
(Engineering hypothesis, Phase 3 source label). Split: 9
REQUIRED + 2 STRUCTURAL. The two STRUCTURAL rows are
I-AGENTLOOP-10 (agent_loop module static audit) and I-AGENTLOOP-11
(agent_benchmark module static audit). Every other row is
REQUIRED. The 11 rows are inserted in canonical ID order in the
cross-cutting section of `INVARIANT_CATALOG.md`. The catalog
patches v0.29 -> v0.30. `tools/catalog.py` `EXPECTED_COUNTS` is
updated to `{"REQUIRED": 303, "STRUCTURAL": 94, "NOT-EXERCISED":
14, "DEFERRED": 15, "OBSERVED": 16}`. `brain/_catalog_ids.py` is
regenerated. `brain/invariants.py` `FIXTURE_MODULES` is extended
by 11 entries. README catalog banner is updated to v0.30.

## 5. Surfaces consumed (verbatim from existing modules)

| Surface | Module | Notes |
|---|---|---|
| `OperatorSession(state, ..., processing_window_size, feedback_mode)` | `brain.ui.session` | Constructor used with `state=initial_state()`. |
| `OperatorSession.dispatch(Command(OperatorCommand.STREAM_APPEND, payload=StreamAppendPayload(text=...)))` | `brain.ui.session`, `brain.ui.commands`, `brain.development.text_stream` | Only dispatcher path used. |
| `OperatorSession.stream_history.chunks` | `brain.ui.session`, `brain.development.text_stream` | Read-only inspection. |
| `OperatorSession.pattern_ledger.entries` | `brain.ui.session`, `brain.development.pattern_ledger` | Read-only inspection. |
| `OperatorSession.growth_ledger.events` + `.counts_by_type()` | `brain.ui.session`, `brain.development.growth_ledger` | Read-only inspection. |
| `build_full_coherence_report(session, snapshot_id=...)` | `brain.development.coherence_monitor` | Pure read; never mutates `session`. |
| `derive_pattern_id`, `derive_pattern_signature` | `brain.development.pattern_ledger` | Pure helpers. |
| `STREAM_TEXT_MAX_LEN`, `STREAM_HISTORY_MAX_CHUNKS`, `STREAM_PATTERN_RECURRENCE_MIN`, `STREAM_PATTERN_RECURRENCE_MAX` | `brain.development.text_stream` | Bounded constants. |
| `GROWTH_LEDGER_MAX_EVENTS` | `brain.development.growth_ledger` | Bounded constant. |
| `_FORBIDDEN_NON_CLAIM_TERMS` | `brain.development.coherence_monitor` | Audit list (reused, not copied). |
| `ProtoBasicGrammar`, `ProtoBasicToken`, `ProtoBasicTokenKind`, `ProtoBasicParseCategory`, `ProtoBasicExecutionCategory`, `ProtoBasicHistory`, `ProtoBasicParseResult`, `ProtoBasicCommand`, `ProtoBasicExecutionResult`, `ProtoBasicFeedback` | `brain.development.repl` | REPL primitives. |
| `tokenize`, `parse_line`, `build_command`, `execute_command`, `score_feedback`, `append_history`, `summarize_repl_history`, `canonical_command_form`, `diminishing_returns_factor` | `brain.development.repl` | REPL helpers. |
| `BrainState`, `initial_state`, `assert_state_invariants` | `brain.tick` | Never the `tick` callable. |
| `COGITO_ID` | `brain.tlica.profile` | Audit primitive. |

## 6. Failure modes acknowledged in advance

- F1. **Coherence status variation not fully reachable.** Phase
  3.21 W3 notes that a fresh `OperatorSession` always emits
  `pass`. Public-surface levers (oversize chunks rejected at
  validator; pattern ledger / stream history caps) cannot be
  reached through the operator API without raising. The probe
  will document the maximum safe subset (likely `pass` always
  reachable; `warn` possibly via stream-history saturation through
  many STREAM_APPENDs; `fail` and `not_applicable` likely not
  publicly constructible without invariant violation). If `warn`
  is reachable, the probe demonstrates it; if not, it records WARN
  and lists the safe subset. The runner treats the axis as PASS
  iff at least `{pass}` is demonstrated AND the spec lists the
  exact unreachable statuses with a constraint quote.

- F2. **REPL near-miss correction depth.** The Proto-BASIC near-
  miss hint is bounded at edit distance 1. Any near-miss case in
  the benchmark must stay within that bound; the spec documents
  this and the case generator respects it.

- F3. **Stream history saturation.** A long session of repeated
  `STREAM_APPEND` calls will saturate `stream_history.chunks` at
  256 (Phase 3.21 M10 finding). The benchmark's session-continuity
  axis stays well under 256 chunks (target: <= 32 per case) so
  saturation does not artifactually pass session continuity.

- F4. **Pattern ledger saturation.** Pattern ledger caps at 64
  entries; the benchmark generates at most ~16 distinct seeds per
  case so saturation does not trigger.

- F5. **Forbidden-term hit during free-form composition.** Replies
  are composed from a closed bounded template family; the static
  audit runs the forbidden-term audit on every produced section
  and on the module source. Any hit fails the run.

- F6. **Deterministic divergence between two runs.** The runner
  records the transcript digest after every run; if the digest
  differs across two runs, the run fails with
  `determinism_failures += 1`.

## 7. Review-Gate request (Step 5 of the campaign sequence)

Phase 3.22 will use the same Review-Gate discipline as Phase 3.21
Review Gate B. The Review-Gate request is implicit in this
document and the BENCHMARK_SPEC; the gate will be recorded in
Step 4's commit preamble (immediately before agent loop
implementation lands).

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used in Step 2
Stage B limited-write collaboration: not used in Step 2
Stage C.1 flow orchestration       : not used in Step 2
brain-explorer (Explore agent)     : used once in Step 1 for
                                     public-surface survey
Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```
