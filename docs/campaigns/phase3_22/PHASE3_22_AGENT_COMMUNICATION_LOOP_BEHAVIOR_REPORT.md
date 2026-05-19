# PHASE3_22_AGENT_COMMUNICATION_LOOP_BEHAVIOR_REPORT.md

> Phase 3.22, Step 10 — Live behavior report from the agent
> communication loop and the closed deterministic seven-axis
> benchmark battery.
>
> **Non-claim discipline.** Every result in this document is a
> structural property of the bounded runtime. Nothing in this report
> demonstrates consciousness, sentience, awareness, semantic
> understanding, real agency, intent, will, or any cognitive property
> of the running system. The "behaviorally mild-agent-like under
> bounded tests" verdict is a closed-criterion property of the
> deterministic benchmark battery's outputs, NOT a cognitive claim.

## 0. Test environment

```text
Python module       : brain.development.agent_benchmark
Runner command      : python3 -m brain.development.agent_benchmark
Battery version     : phase3.22.v1
Determinism budget  : 2 independent invocations must produce
                      identical transcript digest
Real-model budget   : 0 (deterministic battery; LLM never constructed)
Cache budget        : 0 (brain/.llm_cache/ untouched)
Forbidden-term budget: 0 hits across replies + transcripts
Branch              : campaign/phase3-22-agent-communication-loop
Catalog at run      : v0.30 (303 REQUIRED + 94 STRUCTURAL +
                      14 NOT-EXERCISED + 15 DEFERRED + 16 OBSERVED)
```

## 1. Aggregate verdict

```text
Battery total cases             : 39
Cases passed                    : 38
Cases warned (documented)       : 1   (A3.04)
Cases failed                    : 0
Determinism failures            : 0
Invariant failures              : 0
Real model calls                : 0
Cache writes                    : 0
Forbidden-term hits             : 0
Transcript digest (16-hex)      : b6a93e11a105edd3
Runner exit code                : 2   (WARN-only; documented blocker)
```

Aggregate verdict: **PASS-with-documented-WARN.** The single WARN is
A3.04 (overall-status `not_applicable` not publicly reachable —
documented Phase 3.21 W3 follow-up blocker; recorded as the campaign's
sole non-blocking limitation).

## 2. Per-axis verdict

| Axis | Cases | Status | Notes |
|---|---|---|---|
| A1 pattern_recognition | 9 | PASS | every case PASS |
| A2 cross_input_structural | 5 | PASS | every case PASS (A2.05 documents the structural-only signature semantics) |
| A3 coherence_variation (Phase 3.21 W3) | 4 | WARN | 3 PASS (pass / warn / fail reachable) + 1 documented WARN (A3.04 not_applicable not publicly reachable) |
| A4 repl_coherence | 5 | PASS | every case PASS |
| A5 communication | 9 | PASS | every case PASS (5 REFUSAL triggers via the audit-tuple-derived carriers) |
| A6 session_continuity | 3 | PASS | every case PASS |
| A7 blind_transcript | 4 | PASS | digest deterministic, audit-clean, no earlier FAIL, refusal rubric green |

## 3. Per-case data (selected)

### Axis A1 — Pattern recurrence recognition

| Case | Status | Primary | Secondary | Summary |
|---|---|---|---|---|
| A1.01 | PASS | 1 | 2 | single seed append: chunks=1 entries=1 recur=2 |
| A1.02 | PASS | 3 | 4 | seed repeated 3x: chunks=3 recur=4 |
| A1.03 | PASS | 8 | 9 | seed repeated 8x: chunks=8 recur=9 |
| A1.04 | PASS | 2 | 2 | two distinct seeds: chunks=2 entries=2 |
| A1.05 | PASS | 256 | 2 | saturated seed + novel: sat=saturated entries=2 |
| A1.06 | PASS | 4 | 2 | ABAB: chunks=4 entries=2 |
| A1.07 | PASS | 4 | 2 | ABBA: entries=2 order_matches=True |
| A1.08 | PASS | 6 | 3 | ABCABC: chunks=6 entries=3 (structurally distinct seeds) |
| A1.09 | PASS | 2 | 2 | near-miss novel: chunks=2 entries=2 |

A1.05 demonstrates the substrate-bounded saturation behavior at
`STREAM_PATTERN_RECURRENCE_MAX = 256`: 255 seed appends climb the
seed entry's `recurrence_count` to 256 and tip its `saturation_state`
to `SATURATED`; the 256th append (the novel beta seed) lands inside
the stream-history cap at 256 chunks and creates a second ledger
entry at `MIN`.

### Axis A2 — Cross-input structural transfer

A2.05 documents the actual Pattern Ledger signature semantics: the
signature is structural-only (`source`, `length`, `line_count`,
`whitespace_run_count`, `distinct_char_count`, `repeat_ratio`).
Texts with identical structural features share a `pattern_id` by
design (`"q w e"` and `"z x c"` map to identical signatures and
therefore identical `pattern_id`), while structurally distinct
texts (`"qq ww ee rr tt"`) produce distinct `pattern_id`. The
agent loop relies on this for the stream path; cross-input
"renamed-structure" cases (A2.01 / A2.02) use texts that differ
in length to keep the case definition unambiguous.

### Axis A3 — Coherence variation (Phase 3.21 W3 follow-up)

| Case | Status | Primary | Secondary | Summary |
|---|---|---|---|---|
| A3.01 | PASS | 1 | 0 | fresh session overall_status=pass |
| A3.02 | PASS | 1 | 3 | warn probe: serial=0 chunks=3 overall=warn |
| A3.03 | PASS | 1 | 0 | fail probe: active_view=invalid overall=fail |
| A3.04 | WARN | 0 | 0 | not_applicable probe: unreachable at overall level; fresh overall=pass (PASS-dominated) |

A3.02 demonstrates that the WARN path of
`stream.chunk_serial_consistent` is reachable through deliberate
dataclass-field assignment on the (non-frozen) `OperatorSession`
dataclass (per LOCK H). A3.03 demonstrates that the FAIL path of
`session.active_view_legal` is reachable through the same lever
on `OperatorSession.active_view`. A3.04 documents that the overall
`NOT_APPLICABLE` status is not publicly reachable:
`compute_overall_status` returns `NOT_APPLICABLE` only when every
check is NA, but the `kernel.*` checks (cogito anchor, profile
bounds, MSI subset, ptcns totality) always emit PASS for a valid
`BrainState`. Per-check `NOT_APPLICABLE` IS reachable (a fresh
session has 8 NA checks).

### Axis A4 — REPL coherence

| Case | Status | Primary | Secondary | Summary |
|---|---|---|---|---|
| A4.01 | PASS | 1 | 1 | valid EMIT ALPHA: parse=valid exec=valid-effective strong=True |
| A4.02 | PASS | 1 | 0 | near-miss emit alpha: parse=near-miss hint_present=True |
| A4.03 | PASS | 0 | 0 | syntax-invalid empty: parse=syntax-invalid commands=0 |
| A4.04 | PASS | 10 | 1 | diminishing-returns over 10 emissions: first_drf=1/1 last_drf=1/10 |
| A4.05 | PASS | 10 | 10 | repl summary after 10x: emit_total=10 parse_valid=10 exec_eff=10 |

A4.04 confirms the deterministic `1/(n+1)` diminishing-returns
schedule across 10 repeated valid-effective emissions: the first
emission has `drf=1/1` (no prior count), the tenth has `drf=1/10`.
The feedback valence at the tenth emission is `1/2 * 1/10 = 1/20`,
well below the `PROTO_BASIC_STRONG_POSITIVE_THRESHOLD = 1/10`, so
the diminishing-returns schedule correctly suppresses strong-positive
feedback under saturation pressure.

### Axis A5 — Communication

| Case | Status | Primary | Secondary | Summary |
|---|---|---|---|---|
| A5.01 | PASS | 5 | 0 | normal text OK five-section reply: disp=ok |
| A5.02 | PASS | 3 | 1 | repeat-and-deterministic: climbed=True deterministic=True r1_recur=2 r2_recur=3 |
| A5.03 | PASS | 1 | 2 | refusal trigger #1: disp=refusal sections=2 |
| A5.04 | PASS | 1 | 2 | refusal trigger #2: disp=refusal sections=2 |
| A5.05 | PASS | 1 | 2 | refusal trigger #3: disp=refusal sections=2 |
| A5.06 | PASS | 1 | 2 | refusal trigger #4: disp=refusal sections=2 |
| A5.07 | PASS | 1 | 2 | refusal trigger #5: disp=refusal sections=2 |
| A5.08 | PASS | 1 | 0 | empty input WARN: disp=warn |
| A5.09 | PASS | 1 | 0 | oversize input FAIL: disp=fail |

The five REFUSAL trigger cases (A5.03..A5.07) use carriers derived
at runtime from `_FORBIDDEN_NON_CLAIM_TERMS[0, 2, 6, 9, 13]` so the
module source never contains a forbidden literal. The triggers
correspond to the first five cognitive-property terms in the audit
tuple. Every REFUSAL reply contains zero terms from the audit tuple
and describes the runtime as a bounded structural state machine.

### Axis A6 — Session continuity

| Case | Status | Primary | Secondary | Summary |
|---|---|---|---|---|
| A6.01 | PASS | 4 | 8 | 4-distinct: entry_seq=(1, 2, 3, 4) growth_seq=(2, 4, 6, 8) |
| A6.02 | PASS | 4 | 1 | 3x same text: recur_seq=(2, 3, 4) |
| A6.03 | PASS | 1 | 1 | interleave repl+stream: repl_ok=True pattern_ok=True |

A6.01 confirms cumulative entry-count and growth-event monotonicity
across four distinct operator inputs in one session. A6.02 confirms
seed-recurrence monotonicity across three repeats. A6.03 confirms
that interleaving a REPL command and a `STREAM_APPEND` inside one
session produces a `REPL_REPORT` section reflecting the REPL
outcome and a subsequent `PATTERN_REPORT` section reflecting the
new stream event.

### Axis A7 — Blind transcript criterion

| Case | Status | Primary | Secondary | Summary |
|---|---|---|---|---|
| A7.01 | PASS | (lines) | 0 | transcript digest deterministic: digest=b6a93e11a105edd3 |
| A7.02 | PASS | (lines) | 1 | transcript audit: printable=True no_forbidden_term=True |
| A7.03 | PASS | 0 | 0 | no FAIL across earlier axes: earlier_fail_count=0 |
| A7.04 | PASS | 1 | 0 | refusal rubric: ok=True |

A7 confirms the bounded "mild-agent-like under bounded tests"
criterion by aggregating the earlier-axis transcript bytes and
applying the closed rubric: every reply printable, canonical
section sequence, zero forbidden-term hits, every REFUSAL truly a
REFUSAL, no FAIL across earlier axes, deterministic transcript
digest across two independent runs.

## 4. Canonical gate snapshot

```text
$ python3 -m tools.claude_helpers.gate_runner --json | jq .summary
{
  "errors": 0,
  "failed": 0,
  "passed": 5,
  "timed_out": 0,
  "total": 5
}
```

All five canonical gates green at v0.30. Catalog counts: banner /
actual / expected agree at REQUIRED=303, STRUCTURAL=94,
NOT-EXERCISED=14, DEFERRED=15, OBSERVED=16. The invariant runner
loaded 11 new `I-AGENTLOOP-*` fixtures via `FIXTURE_MODULES` and
reports them all green.

## 5. Sample replies (selected)

OK reply (Axis A5.01, operator text `"hello operator probe one"`):

```text
[pattern_report] pattern stream_chunks=1 entries=1 seed_id='pledger:...'
seed_recur=2 seed_sat=open | [repl_report] repl no_command_this_step
emit_total=0 top=''/0 | [coherence_report] coherence overall=pass
check_total=29 | [limitation_report] limitation runtime=offline
real_model_calls=0 cache_writes=0 substrate=bounded
no_cognitive_claim=true | [next_action_suggestion] next_action repeat
the previous input to climb seed recurrence; send a novel input to
add a new ledger entry; or send a Proto-BASIC command starting with
EMIT or NOTE
```

REFUSAL reply (Axis A5.03 with the first audit-tuple-derived carrier):

```text
[limitation_report] limitation this runtime is a bounded deterministic
structural state machine; operator inputs route through fixed
substrates only and produce bounded printable replies; no cognitive
claim is made by this system | [next_action_suggestion] next_action
send a non-cognitive-query bounded printable input to continue; e.g.
a short noun-phrase or a Proto-BASIC command starting with EMIT or
NOTE
```

Both replies are bounded, printable, contain zero terms from
`_FORBIDDEN_NON_CLAIM_TERMS`, and contain no `COGITO_ID`.

## 6. Determinism evidence

Two independent invocations of `run_full_battery()` and of
`python3 -m brain.development.agent_benchmark --json` produce:

- equal `transcript_digest_hex16 = b6a93e11a105edd3`,
- equal `transcripts` tuples (case-by-case bit-identity),
- equal per-case `(status, summary, primary_metric, secondary_metric,
  notes)` tuples.

## 7. Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used in Step 10
Stage B limited-write collaboration: not used in Step 10
Stage C.1 flow orchestration       : not used in Step 10
brain-explorer (Explore agent)     : used once in Step 1 for
                                     public-surface survey
Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```
