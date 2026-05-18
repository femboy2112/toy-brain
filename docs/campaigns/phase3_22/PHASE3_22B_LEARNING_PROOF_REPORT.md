# PHASE3_22B_LEARNING_PROOF_REPORT.md

This report is a documented operational proof that the runtime, under
bounded deterministic tests, accumulates structural records, reuses
that structure in later interactions, transfers recognized structure
across renamed inputs, and updates diminishing-returns / correction
records on the REPL bridge.

**Non-claim disclaimer.** "Structural learning" here means observable
session-local state transitions captured as bounded
`LearningEvidenceRecord` rows. It is NOT memory in the psychological
sense. It is NOT semantic interpretation. It asserts no cognitive
property of the running system.

## Aggregate digest

A fresh session advanced through the deterministic sequence

```text
"alpha line one", "alpha line one", "red blue red blue",
"cat dog cat dog", "EMIT ALPHA", "EMIT ALPHA"
```

produces a `LearningProofReport` with:

```text
record_total = 10
observed_count = 3
recurrence_increased_count = 1
abstract_pattern_acquired_count = 2
abstract_pattern_reused_count = 2
transfer_recognized_count = 1
repl_correction_applied_count = 0
diminishing_returns_updated_count = 1
limitation_recorded_count = 0
digest_hex16 = df75162f93605181
```

Two fresh sessions advanced through this sequence produce equal
records and equal digests. The benchmark case A8.07 asserts this
determinism.

## Per-scenario proof rows

| case_id | input sequence | pre-state | post-state | evidence emitted | later reuse / transfer | reply excerpt | digest | verdict |
|---|---|---|---|---|---|---|---|---|
| A8.01 | `"alpha line one"` x2 | `pattern_entry_count=0, seed_recur=0` | `pattern_entry_count=1, seed_recur=3` | `OBSERVED` + `ABSTRACT_PATTERN_ACQUIRED` (call 1); `ABSTRACT_PATTERN_REUSED` + `RECURRENCE_INCREASED` (call 2) | recurrence climbed 2 -> 3 in call 2 | `pattern stream_chunks=2 entries=1 seed_recur=3 seed_sat=open` | (per-trace) | PASS |
| A8.02 | `"red blue red blue"` | no prior trace records for ABAB digest | ABAB digest acquired in trace | `OBSERVED` + `ABSTRACT_PATTERN_ACQUIRED` for digest `d37efc29b0c680ba` | — | `pattern stream_chunks=1 entries=1 seed_recur=2` | acquired digest = `d37efc29b0c680ba` | PASS |
| A8.03 | `"red blue red blue"` -> `"cat dog cat dog"` | ABAB acquired with `prior_pid=pledger:1669ab0ef2ed6bba` | reuse + transfer recognized | `ABSTRACT_PATTERN_REUSED` + `TRANSFER_RECOGNIZED` for digest `d37efc29b0c680ba` | transfer prior_pid -> new_pid | `pattern stream_chunks=2 entries=2 seed_recur=2` | transfer recorded | PASS |
| A8.04 | `"alpha line one"` x2 | recurrence_count=2 | recurrence_count=3 | `RECURRENCE_INCREASED` | later reply pattern section cites climbed recurrence | `pattern stream_chunks=2 entries=1 seed_recur=3 seed_sat=open` | (per-trace) | PASS |
| A8.05 | `"emit alpha"` (near-miss) -> `"EMIT ALPHA"` (valid) | last parse_result = near-miss | trace contains correction record | `REPL_CORRECTION_APPLIED` | — | `repl last_parse=valid last_exec=valid-effective last_canonical='shape=verb|target;...' last_val=1/2 last_drf=1/1 emit_total=1` | correction recorded | PASS |
| A8.06 | `"EMIT BETA"` x4 | repl emit_count=0 | repl emit_count=4 | 3 `DIMINISHING_RETURNS_UPDATED` records | DRF sequence `(1/1, 1/2)`, `(1/2, 1/3)`, `(1/3, 1/4)` | last `repl last_drf=1/4` | DRF sequence captured | PASS |
| A8.07 | aggregate (6-step seq above) | empty trace | 10-record trace | full proof | digest determinism witness | (composite) | `df75162f93605181` | PASS |

## Scenario A: ABAB transfer (verbatim trace excerpt)

```text
observed                       observed novel input shape='A B A B' class=recurring-form digest=d37efc29b0c680ba
abstract_pattern_acquired      abstract pattern d37efc29b0c680ba acquired shape='A B A B' class=recurring-form
observed                       observed novel input shape='A B A B' class=recurring-form digest=d37efc29b0c680ba
abstract_pattern_reused        abstract pattern d37efc29b0c680ba reused (this is reuse 1)
transfer_recognized            abstract pattern d37efc29b0c680ba transferred from pledger:1669ab0ef2ed6bba to pledger:ba9d1415920680b0
```

The two surface inputs (`"red blue red blue"` and `"cat dog cat dog"`)
share zero surface tokens but share the abstract structural digest
`d37efc29b0c680ba`. The runtime treats the renamed input as transfer
of the abstract structure — captured deterministically as a
`TRANSFER_RECOGNIZED` record.

## Scenario B: REPL near-miss correction (verbatim trace excerpt)

```text
repl_correction_applied        near-miss correction applied: hint kind=CASE_FOLD pos=0 expect=agent-repl:verb:emit dist=1 -> shape=verb|target;tokens=agent-repl:verb:emit|agent-repl:target:alpha
```

The lowercase typing `"emit alpha"` is routed through the REPL bridge,
which emits a near-miss with the bounded `CASE_FOLD` hint. The
follow-up valid command `"EMIT ALPHA"` triggers the
`REPL_CORRECTION_APPLIED` record, citing the prior hint and the new
canonical form.

## Scenario C: REPL diminishing returns (verbatim trace excerpts)

```text
diminishing_returns_updated    diminishing-returns factor 1/1 -> 1/2 for shape=verb|target;tokens=agent-repl:verb:emit|agent-repl:target:beta
diminishing_returns_updated    diminishing-returns factor 1/2 -> 1/3 for shape=verb|target;tokens=...
diminishing_returns_updated    diminishing-returns factor 1/3 -> 1/4 for shape=verb|target;tokens=...
diminishing_returns_updated    diminishing-returns factor 1/4 -> 1/5 for shape=verb|target;tokens=...
```

Each repeated valid REPL command updates the diminishing-returns
factor, captured as a deterministic record. The W5 follow-up is
satisfied: repeated valid-effective actions produce diminishing
returns and later replies reflect the bounded local consequence.

## What does NOT count as proof here

- A narrative about "what the model learned" — not bounded, not
  auditable.
- An aggregate "intelligence" or "capability" or "I-ness" score —
  forbidden by the non-claim discipline.
- A claim that the system "remembers" the input in any subjective
  sense — forbidden.
- A claim that the system "recognizes" semantic content — the
  pattern signature operates on surface tokens only; no semantic
  embedding is computed.

## How to reproduce

```bash
python3 -m brain.development.agent_benchmark
python3 -m brain.invariants run --id I-AGENTLEARN
```

The deterministic battery consumes 0 real model calls, 0 cache
writes, and produces 0 forbidden-term hits.
