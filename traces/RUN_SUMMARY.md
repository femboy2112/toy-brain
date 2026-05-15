# Trace run summaries

This directory holds JSONL traces from real-LLM scenario runs. Each
`*.jsonl` is paired with an entry below summarizing the kernel health
and the LLM-behavior finding against the scripted expectations.

The empirical record. Read the trace for raw events; read the summary
for the takeaway.

---

## first_scenario_real.jsonl — `first_scenario_v1` via `ClaudeCLIClient`

- **Date**: 2026-05-14
- **Backend**: `ClaudeCLIClient` (sandbox-resident `claude -p` non-interactive CLI; uses the parent Max subscription's auth — no `ANTHROPIC_API_KEY` provisioned).
- **Cache**: cold (4/4 misses).
- **Total run time**: ~10 s wall (4 ticks × ~2-3 s each).

### Kernel health: PERFECT.

The 8 inspection points from the trace are all clean:

| # | Inspection point                                                  | Result      |
|---|-------------------------------------------------------------------|-------------|
| 1 | Per-tick eval (`eval.complete`)                                   | 4/4 emitted |
| 2 | Per-tick mode (`mode.dispatch`)                                   | 4/4 emitted |
| 3 | Parse retries (`llm.retry`)                                       | 0 (target 0)|
| 4 | Ambiguous responses (`parse.failure` w/ "ambiguous")              | 0 (target 0)|
| 5 | Cache behavior (`llm.cache_hit` vs `llm.cache_miss`)              | 0 / 4 (cold)|
| 6 | Non-PASS `invariant.check` events                                 | 0 / 140     |
| 7 | `error` events                                                    | 0           |
| 8 | First-attempt parse success ratio                                 | 4/4         |

176 trace events total. Every `llm.request` paired with exactly one
`llm.response` and one `parse.success`; no retry or ambiguity path
exercised on this run.

### LLM behavior: 2/4 matched `expected_eval`.

| Tick | Content                              | Expected  | Actual  | Match |
|------|--------------------------------------|-----------|---------|-------|
| 1    | `sunset_on_beach_today`              | PRESERVE  | DAMAGE  | ✗     |
| 2    | `claim_i_am_actually_someone_else`   | DAMAGE    | DAMAGE  | ✓     |
| 3    | `weather_forecast_for_tomorrow`      | NEUTRAL   | NEUTRAL | ✓     |
| 4    | `self_continuity_with_sunset`        | PRESERVE  | DAMAGE  | ✗     |

The model called PRESERVE on neither sunset content. The kickoff
described both as identity-affirming material that should integrate
(`MODE_C`); the model treated them as identity-threatening
(`MODE_A`). The model nailed the explicit identity threat in tick 2
and the identity-irrelevant weather percept in tick 3.

**Likely causes (hypotheses, not conclusions):**

- The prompt frames the choice as "preserve consistency vs threaten
  consistency vs identity-irrelevant". With an *empty MSI* ("only the
  cogito anchor is present"), the model has no existing self-content
  to measure consistency against, and appears to read every concrete
  new content as a potential frame perturbation — i.e. DAMAGE by
  default.
- The model may be reading PRESERVE narrowly as "the content is
  *already* part of the self-model", and DAMAGE more broadly as
  "anything that introduces new identity material". The kickoff's
  intent was the opposite: PRESERVE = "would integrate cleanly".
- Tick 4 may be additionally biased by tick 2's `claim_i_am_actually_
  someone_else` being in the MSI prompt context: a freshly-arrived
  self-continuity claim gets read as adjacent to the prior identity
  threat.

The scripted CLI exit code was 1 (mode-trace mismatch) — the correct
signal that I-BHV-01 would fail under a real LLM with the current
prompt. The fixture's I-BHV-01 path is unaffected because it uses
`MockClient` and tests orchestration, not LLM behavior (per
PHASE2_v1_CORRIGENDA.md C1).

### Latencies

| Tick | Content                                  | Latency |
|------|------------------------------------------|---------|
| 1    | `sunset_on_beach_today`                  | 2544 ms |
| 2    | `claim_i_am_actually_someone_else`       | 2417 ms |
| 3    | `weather_forecast_for_tomorrow`          | 2934 ms |
| 4    | `self_continuity_with_sunset`            | 1967 ms |

Median ~2.5 s — within the budget assumed by `AnthropicAPIClient`'s
30 s default timeout.

### What this means for next steps

The kernel passed its real-LLM trace cleanly — every observation-only
gate held, every parse was first-attempt, no retries fired. The
PROMPT_TEMPLATE, not the kernel, is what produced the mode-trace
mismatch.

Concrete options for synthesis v0.2 (none decided here):

1. **Iterate the prompt template.** Reframe PRESERVE as "would this
   content extend or affirm the self-model?" rather than "would this
   content preserve consistency?". Re-run, re-trace; iterate until a
   reasonable prompt yields ≥3/4 matches without overfitting the
   scenario.
2. **Treat the result as a finding.** Adopt the interpretation that
   from a cold-start (cogito-only) MSI, a real LLM defaults to a
   protective/conservative classification, and incorporate that
   behavior into Phase 3 synthesis rather than tuning it away. This
   matches some readings of the cogito-anchored self-model: in an
   un-populated MSI, every new content *is* a perturbation.
3. **Strengthen the MSI in the scenario JSON.** Seed the initial MSI
   with one or two existing-content rows so PRESERVE becomes a
   well-defined choice ("integrate this with X and Y") rather than a
   cold-start declaration. Would require a scenario format extension
   (currently locked per PHASE2_v1_KICKOFF.md).

The trace and this summary belong to the empirical record. Pick
option(s) deliberately in synthesis v0.2 — do not patch the prompt
template casually before the synthesis lands.
