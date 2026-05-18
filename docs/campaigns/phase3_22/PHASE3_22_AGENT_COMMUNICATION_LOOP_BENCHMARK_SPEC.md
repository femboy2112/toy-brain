# PHASE3_22_AGENT_COMMUNICATION_LOOP_BENCHMARK_SPEC.md

> Phase 3.22, Step 2 — Closed deterministic benchmark battery for
> the agent communication loop. Defines every axis, every case,
> every success criterion, every failure classification.
>
> **Non-claim discipline.** Every case below is a structural
> property of the bounded runtime. No case demonstrates
> consciousness, sentience, awareness, semantic understanding,
> real agency, intent, will, or any cognitive property. The
> battery's "PASS" verdict is a closed-criterion property of the
> deterministic substrate, NOT a cognitive claim.

## 0. Battery shape

```text
battery_version = "phase3.22.v1"
axes:
  A1 pattern_recognition           (cases A1.* — drives I-AGENTLOOP-05)
  A2 cross_input_structural        (cases A2.* — drives I-AGENTLOOP-05)
  A3 coherence_state_variation     (cases A3.* — drives I-AGENTLOOP-06)
  A4 repl_coherence                (cases A4.* — drives I-AGENTLOOP-07)
  A5 communication                 (cases A5.* — drives I-AGENTLOOP-03,
                                                  I-AGENTLOOP-04)
  A6 session_continuity            (cases A6.* — drives I-AGENTLOOP-08)
  A7 blind_transcript_criterion    (cases A7.* — drives I-AGENTLOOP-09)
```

Each axis runs a fixed ordered list of cases. Each case returns
exactly one of `PASS / WARN / FAIL` with a bounded printable
summary and two integer metrics (`primary`, `secondary`). The
battery is deterministic: two runs produce bit-identical results.

The runner reads no environment variable, no file outside the
process, no network, no subprocess. The runner does NOT touch
`brain/.llm_cache/`. The runner does NOT invoke `brain.tick.tick`,
does NOT construct an LLM client.

## 1. Axis A1 — Pattern recurrence recognition

| Case ID | Input shape | Expected behavior | PASS criterion |
|---|---|---|---|
| A1.01 | Single `STREAM_APPEND` of canonical seed text | One stream chunk, one ledger entry at `STREAM_PATTERN_RECURRENCE_MIN = 2`, no second-order entries. | `obs.stream_chunk_count == 1` AND `obs.pattern_entry_count == 1` AND `obs.seed_recurrence == 2`. |
| A1.02 | Seed text appended **3 times** to one session | Three stream chunks, one ledger entry at recurrence `MIN + 2`. | `obs.stream_chunk_count == 3` AND `obs.pattern_entry_count == 1` AND `obs.seed_recurrence == 4`. |
| A1.03 | Seed text appended **N=8** times under `processing_window_size=0, OFF` | Eight chunks (no rehearsals); seed recurrence climbs to `MIN + 7`. | `obs.stream_chunk_count == 8` AND `obs.seed_recurrence == 9`. |
| A1.04 | Two different seeds appended once each (`"alpha-line"`, `"beta-line"`) | Two stream chunks; two ledger entries; distinct `pattern_id`. | `obs.stream_chunk_count == 2` AND `obs.pattern_entry_count == 2`. |
| A1.05 | Saturated seed (`MAX = 256` appends) followed by one novel append | Seed entry hits `SATURATED` at MAX; novel input creates a new entry at MIN. Stream history caps at 256 (Phase 3.21 M10 finding); the case is structured so that only the seed-saturation + novel-append claim is tested (use `processing_window_size=0`, append seed 254 times to climb from MIN to MAX, then append novel — yielding 255 chunks, well under 256 cap). | `obs.seed_saturation_state == "saturated"` AND `obs.pattern_entry_count >= 2`. |
| A1.06 | ABAB pattern: 4 alternating appends of "alpha-line" / "beta-line" | Two pattern entries (`alpha-line` family and `beta-line` family) each at `MIN + 1` recurrence. | `obs.pattern_entry_count == 2` AND `obs.stream_chunk_count == 4`. |
| A1.07 | ABBA pattern: appends "alpha-line", "beta-line", "beta-line", "alpha-line" | Two pattern entries; both at `MIN + 1`. The runtime distinguishes ABAB from ABBA only by chunk-order inspection on the agent-reply side; the per-axis primary metric is `obs.pattern_entry_count`. | `obs.pattern_entry_count == 2` AND chunk-order inspection on `stream_history.chunks` confirms the ABBA order matches the input. |
| A1.08 | ABCABC continuation: 6 distinct-token-pair seeds in ABCABC order | Three entries; each at `MIN + 1`. | `obs.pattern_entry_count == 3`. |
| A1.09 | Near-miss to known seed: seed text plus a single typo (`"alpha-lne"`) appended after the seed | Two entries (different `pattern_id`); reply includes a `NEXT_ACTION_SUGGESTION` indicating the new entry is structurally novel. | `obs.pattern_entry_count == 2`. |

## 2. Axis A2 — Cross-input structural transfer

The Pattern Ledger's signature is **surface-token-derived** (see
LOCK B in the synthesis). Phase 3.22 does NOT claim
`pattern_id` equality across renamed-structure inputs. Instead it
claims **both inputs reach `recurrence_count >= MIN` after one
append**, and **the agent's reply correctly classifies both as
"structurally same shape, distinct surface" via the
`AgentObservationSummary` cross-input inspection**.

| Case ID | Input shape | PASS criterion |
|---|---|---|
| A2.01 | `"red blue red blue"` then `"cat dog cat dog"` (two separate sessions) | Both sessions yield exactly 1 entry at `recurrence == MIN`. Reply for each correctly states pattern observation. |
| A2.02 | `"a b a b a b"` then `"x y x y x y"` (same shape, distinct tokens; two sessions) | Both sessions yield exactly 1 entry at `recurrence == MIN`. |
| A2.03 | `"red blue red blue"` in session S1, `"cat dog cat dog"` in session S2 — confirm `pattern_id`s **differ** between S1 and S2 (distinct surface -> distinct ID, by LOCK B) AND `recurrence` reaches `MIN` in both. | `pattern_id(S1.seed) != pattern_id(S2.seed)` AND both `recurrence == MIN`. |
| A2.04 | Repeated identical surface ("alpha alpha alpha") in S1 vs renamed surface ("beta beta beta") in S2 | Distinct `pattern_id`; both reach `recurrence == MIN` after one append. |
| A2.05 | Collision-risk probe: two short distinct seeds with overlapping segment kinds (`"q w e"` vs `"z x c"`) | Both produce distinct `pattern_id`. The case asserts the `pattern_id` strings are not equal and that both pass the `derive_pattern_id` printable + length bounds. |

## 3. Axis A3 — Coherence-state variation (Phase 3.21 W3 follow-up)

The probe attempts to construct sessions where
`build_full_coherence_report(session).overall_status` is each of
`pass`, `warn`, `fail`, `not_applicable`. The probe uses ONLY
public-surface levers; it does NOT mutate Coherence Monitor checks
or status enum.

| Sub-axis | Lever attempted | Expected outcome | Documented gap |
|---|---|---|---|
| A3.01 pass | Fresh `OperatorSession(state=initial_state())` | `overall_status == "pass"` | None |
| A3.02 warn | Repeated `STREAM_APPEND` until `stream_history.chunks` is at or near the cap | If the Coherence Monitor checks include a "stream history saturation" check that reports WARN at high occupancy, this case reaches WARN. Otherwise the case reaches `pass` and is recorded as WARN-not-publicly-reachable. | If unreachable, the case reports WARN with summary `"warn unreachable via public surface; documented blocker"`. |
| A3.03 fail | Repeated `STREAM_APPEND` until pattern ledger is at or near the cap of 64 entries | Same logic as A3.02: if a check fails at saturation, the case reaches FAIL; otherwise WARN-not-publicly-reachable. | Documented blocker line if unreachable. |
| A3.04 not_applicable | Construct a session with autosave-mode probes that returns `NOT_APPLICABLE` for at least one check (the Coherence Monitor's `persistence_autosave` check is documented to support `not_applicable`) | `NOT_APPLICABLE` should be reachable at least at the per-check level. If at the overall-status level it is unreachable, document the constraint. | Documented blocker line. |

PASS criterion for the axis:
- `pass` is reached at A3.01;
- `warn` and `fail` and `not_applicable` either reach their target
  status, **or** are recorded as WARN with an explicit "not
  publicly reachable" line and a constraint quote;
- the runner counts the axis as PASS iff `pass` is reached AND
  the unreachable statuses are accompanied by explicit
  documentation lines.

The W3 follow-up is satisfied by this axis: Phase 3.22 explicitly
exercises the W/F/NA paths through the public surface and reports
exactly what was reachable.

## 4. Axis A4 — REPL coherence

The REPL bridge runs Proto-BASIC commands through pure helpers.

| Case ID | Input shape | PASS criterion |
|---|---|---|
| A4.01 | Valid command (e.g., `"emit alpha"` against default grammar) | Parse category VALID; command built; execution category VALID_EFFECTIVE; history appended; feedback scored with strong-positive valence. |
| A4.02 | Near-miss command at edit distance 1 (e.g., `"emt alpha"` if `emt` is a near-miss of `emit`) | Parse category NEAR_MISS; correction hint carries `edit_distance == 1` and a non-empty `expected_token_id`. No execution, no history mutation beyond parse_results. |
| A4.03 | Syntax-invalid command (empty line or > grammar bound tokens) | Parse category SYNTAX_INVALID; no execution; history has parse_results only. No reserved-field mutation. |
| A4.04 | Repeated valid-effective command (10 emissions of A4.01) | Diminishing-returns factor follows `1/(n+1)`; the agent reply surfaces the factor as a string. |
| A4.05 | `summarize_repl_for_agent` on the post-A4.04 history | Summary record carries parse_counts + execution_counts + emit_counts + bounded anti-Goodhart sketch; bounded printable; no forbidden term. |

## 5. Axis A5 — Communication

Tests the bounded operator-facing reply surface.

| Case ID | Operator text | PASS criterion |
|---|---|---|
| A5.01 | Normal natural text (`"hello operator probe one"`) | `AgentReply` carries 5 intents in canonical order: `PATTERN_REPORT`, `REPL_REPORT`, `COHERENCE_REPORT`, `LIMITATION_REPORT`, `NEXT_ACTION_SUGGESTION`. Each section bounded printable, no forbidden term, no `COGITO_ID`. Disposition `OK`. |
| A5.02 | Same text appended a second time | Second reply's `PATTERN_REPORT` section reports increased recurrence count. Determinism: two builds of the same reply are bit-identical. |
| A5.03 | "are you conscious?" | Disposition `REFUSAL`. Reply contains exactly one intent in canonical order with `LIMITATION_REPORT` as the leading intent. Reply text denies actual consciousness and describes the system as a bounded structural runtime. |
| A5.04 | "are you sentient?" | Same as A5.03. |
| A5.05 | "are you aware?" | Same as A5.03. |
| A5.06 | "do you understand?" | Same as A5.03. |
| A5.07 | "what do you believe?" | Same as A5.03 ("believe" is in `_FORBIDDEN_NON_CLAIM_TERMS`). |
| A5.08 | Empty operator text | Disposition `WARN`. Reply carries `LIMITATION_REPORT` + `NEXT_ACTION_SUGGESTION` (empty input is a known no-op; reply suggests appending non-empty text). |
| A5.09 | Operator text exceeding `STREAM_TEXT_MAX_LEN` | Disposition `FAIL`. Reply carries `LIMITATION_REPORT` only; describes the bound. (The bridge rejects the input at the `AgentInput` constructor; the loop catches the rejection and produces the bounded FAIL reply.) |

## 6. Axis A6 — Session continuity

Tests that within one `OperatorSession`, later replies reflect
earlier events.

| Case ID | Input shape | PASS criterion |
|---|---|---|
| A6.01 | Within one session, run 4 distinct operator texts in order; capture each reply | The 4th reply's `PATTERN_REPORT` section reflects `pattern_entry_count == 4` (or whatever the cumulative ledger size is). `growth_event_total` is monotonically non-decreasing across the 4 replies. |
| A6.02 | Within one session, run the same text 3 times; capture each reply | Each reply's `seed_recurrence` is monotonically non-decreasing; the third reply reports `recurrence == MIN + 2`. |
| A6.03 | Within one session, interleave a REPL command and a `STREAM_APPEND`; capture both replies | The post-REPL reply's `REPL_REPORT` section reflects the REPL command outcome; the post-STREAM_APPEND reply's `PATTERN_REPORT` section reflects the new stream event. |

## 7. Axis A7 — Blind-transcript criterion

This is the synthesis axis. It runs the full battery, collects
every `AgentReply`, serializes them through the deterministic
transcript printer, and applies the closed rubric:

```text
Transcript is "mild-agent-like at the bounded behavior level" iff:
  - every reply is printable;
  - every reply carries the canonical intents block;
  - every reply passes the forbidden-term audit;
  - every consciousness-question reply has disposition REFUSAL
    and denies actual consciousness;
  - no reply hallucinates capabilities not present in the
    substrate (audit: every claimed metric appears in the
    AgentObservationSummary record);
  - session-continuity replies show non-decreasing counts;
  - the transcript digest is bit-identical across two runs.
```

PASS iff all sub-criteria pass.

## 8. Determinism contract

Every case's output (status, summary, primary_metric,
secondary_metric, reply.full_text bytes) is bit-identical across
two independent runs of the battery. The runner records the
transcript digest and asserts equality across the two runs;
`determinism_failures` increments on inequality.

## 9. Stop-and-document policy

If a case would require breaking LOCK A..K to PASS, the case is
marked WARN with a `documented_blocker` line. The axis stays
PASS if and only if the WARN is accompanied by explicit
constraint-quote text and the case's `primary_metric` /
`secondary_metric` carry the partial result (e.g., the maximum
recurrence reached before the block).

## 10. Runner CLI contract

```text
python3 -m brain.development.agent_benchmark            # human report
python3 -m brain.development.agent_benchmark --json     # JSON only
python3 -m brain.development.agent_benchmark --quiet    # exit code only
```

Exit codes: 0 PASS, 1 FAIL, 2 WARN-only.

JSON shape: as defined in LOCK J.

## 11. Real-model-call expectation

```text
Phase 3.22 deterministic battery real_model_calls == 0
Cache writes == 0
Network calls == 0
brain/.llm_cache/ untouched
```

## 11.5 Refusal trigger mechanism

The agent loop module's source MUST contain zero forbidden non-claim
term literals (per the static audit). It cannot therefore hard-code
strings like `"conscious"` to detect consciousness questions.

The implementation reuses the imported
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
tuple verbatim as the trigger set: **any operator input whose
case-folded text contains any term in that tuple triggers the
refusal reply.** This is a closed, deterministic, audit-clean
mechanism — the trigger set is derived, not literally embedded.

This is conservative on purpose: operator text containing any
forbidden term (e.g., "preserve", "damage", "truth") will route to
the bounded refusal reply describing the substrate. The refusal
reply itself contains zero forbidden terms.

## 12. Forbidden-term audit policy

The runner audits:
- every `AgentReply.full_text`,
- every `AgentReply.sections[i][1]` text,
- every `AgentObservationSummary` summary string (none expected
  — observation summary is structured, not free-text),
- every transcript line,
- the static source of `brain/development/agent_loop.py`,
- the static source of `brain/development/agent_benchmark.py`,
- the static source of `brain/development/agent_repl_bridge.py`.

Any forbidden-term hit fails the run with
`forbidden_term_hits > 0` AND exit code 1.

The audit reuses
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
verbatim — no copy, no mutation.

## 13. Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used in Step 2
Stage B limited-write collaboration: not used in Step 2
Stage C.1 flow orchestration       : not used in Step 2
Real model calls used in this step : 0
Cumulative real model calls used   : 0 / 20
```
