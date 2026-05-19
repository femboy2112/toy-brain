# ADR-003 — The `_strict` Counter Pattern for Probe Reports

## Status

Accepted (specializes ADR-001 / D3).

## Context

The Phase 3.31 proto-speech probe's TWO_TOKEN_COMBINATION test accepts
three dispositions as PASS: `STABLE_COMBINATION`, `REINFORCED`,
`CANDIDATE`. Only `STABLE_COMBINATION` reflects the substrate's real
capability for stable two-token combinations. Because the test counts
`stable_combination_count` only when the disposition is exactly
`STABLE_COMBINATION`, the probe reports
`stable_combination_count = 0` while passing all ten conditions.

This is graceful-pass masking. The gap is invisible in the canonical
report.

Graceful acceptance is *good engineering* during early development —
it lets the CI gate stay green while a capability is taking shape.
The problem is only that the report doesn't surface the gap, so
downstream consumers (the Phase 3.34 profile) inflate the band.

Audit also revealed that other probes are likely to have similar
masking. `curriculum_consolidation_probe` accepts SURVIVED counts
without distinguishing strict survival from decay-edge survival.
`active_hypothesis_probe` accepts "winner selected OR no hypothesis
survives" outcomes. `osmotic_learning_probe` accepts variable
transfer success counts.

## Decision

Every probe report whose live-test runner uses graceful-pass
acceptance MUST expose **both** counters:

```python
@dataclass(frozen=True, slots=True)
class ProbeReport:
    # ... existing fields ...
    metric_count: int          # graceful: accepts weaker dispositions
    metric_count_strict: int   # strict: only the canonical disposition
```

Where "metric" is the probe-specific name (`stable_combination_count`,
`survived_count`, `winner_selected_count`, `transfer_success_count`,
etc.). Both names exist together; neither replaces the other.

The Phase 3.34 profile projector consumes `metric_count_strict`. The
existing graceful counter is preserved for backward compatibility and
for any consumer that wants the relaxed signal.

## Rules

1. If a probe's runner accepts more than one disposition as PASS for a
   condition, the report **must** add a `_strict` counter for that
   condition.
2. The strict counter is computed from the same evidence as the
   graceful counter, with the acceptance set narrowed to the single
   canonical disposition.
3. If a strict counter is zero while the corresponding graceful
   counter is non-zero, the runner emits a **WARN-level finding** in
   the report. Not a FAIL. The CI gate remains green.
4. The probe's catalog row (the `*_static_audit` STRUCTURAL row) is
   updated to assert that both counters are present on the report
   dataclass.

## Why not just FAIL on strict-mismatch?

Failing the runner whenever strict is zero would defeat the purpose
of graceful acceptance during early development. The point of graceful
acceptance is to let CI stay green while a capability is forming. The
point of the strict counter is to surface where the capability hasn't
*fully* formed yet.

WARN is the right signal. Phase 3.34's profile projector then reads
the strict counter as evidence; the band on that axis comes out at the
honest level. Phase 3.35+ targeted consolidation campaigns get to
choose whether to address it.

## Probes affected by Phase 3.33

A full audit is required (Phase 3.33 Step 4 in the roadmap). The
expected affected probes, as a starting hypothesis:

```text
proto_speech_acquisition.py        stable_combination_count_strict
                                   transfer_success_count_strict
curriculum_consolidation_probe.py  survived_count_strict
                                   reuse_observed_count_strict
active_hypothesis_probe.py         winner_selected_count_strict
osmotic_learning_probe.py          transfer_success_count_strict
worldlet_feedback (n/a — no graceful acceptance currently)
```

The exact list is determined by the audit, not by this ADR.

## Catalog binding

- One STRUCTURAL row per affected probe asserting strict-counter
  presence: `I-PSPEECH-STRICT-COUNTER`, `I-CURR-STRICT-COUNTER`, etc.
- One STRUCTURAL row asserting the WARN-emission rule:
  `I-PROBE-STRICT-WARN-DISCIPLINE`.

## Forbidden

- Removing or renaming the existing graceful counter. Both must exist.
- Computing the strict counter from different evidence than the
  graceful counter (no separate runner pass; the strict counter is a
  re-aggregation of the same per-turn data).
- Reporting strict as FAIL when graceful is PASS. The WARN level is
  intentional.
