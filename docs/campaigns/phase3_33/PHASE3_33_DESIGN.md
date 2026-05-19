# PHASE3_33_DESIGN.md

## Row-ID normalization (Phase 3.33 catalog rows)

The bundle's design docs originally used descriptive multi-segment row
identifiers (`I-PSPEECH-STRICT-COUNTER`, etc.). These do not conform to
the existing catalog row-ID regex `^I-[A-Z]+-\d+[a-z]?$` enforced by
`tools/catalog.py`. At bundle drop-in time each multi-segment ID was
renamed to the next available single-segment-plus-number ID in that
probe's namespace. The semantic intent of each is preserved by this
table; downstream references in this design doc, the campaign roadmap,
the audit plan, the static-audit fixtures, and the catalog itself all
use the normalized IDs.

| Catalog row | Original (bundle) ID | Descriptive intent | Field(s) or discipline added | Status |
|---|---|---|---|---|
| `I-PSPEECH-20` | `I-PSPEECH-STRICT-COUNTER` | Proto-speech strict counters present (the headline fix that motivates Phase 3.33). | `stable_combination_count_strict` and `transfer_success_count_strict` on `ProtoSpeechAcquisitionReport`; both computed from the same evidence as their graceful siblings with acceptance narrowed to the canonical disposition (`STABLE_COMBINATION` / `TRANSFERRED`). | STRUCTURAL |
| `I-CURR-15` | `I-CURR-STRICT-COUNTER` | Curriculum strict counter — provisional, gated on the Step 4 strictness-audit affirming graceful-pass acceptance in `curriculum_consolidation_probe`. | The audit-affirmed strict counter on `CurriculumConsolidationReport` (working hypothesis: `survived_count_strict` for SURVIVED-disposition narrowness). Row dropped from the catalog patch if audit finds the runner already strict-only. | STRUCTURAL |
| `I-AHYP-15` | `I-AHYP-STRICT-COUNTER` | Active-hypothesis strict counter — provisional, gated on the Step 4 audit. | The audit-affirmed strict counter on `ActiveHypothesisLiveTestReport` (working hypothesis: `winner_selected_count_strict` for WINNER-only acceptance). Row dropped from the catalog patch if audit finds the runner already strict-only. | STRUCTURAL |
| `I-OSMO-15` | `I-OSMO-STRICT-COUNTER` | Osmotic strict counter — provisional, gated on the Step 4 audit. | The audit-affirmed strict counter on `OsmoticLiveTestReport` (working hypothesis: `transfer_success_count_strict` for successful-transfer narrowness). Row dropped from the catalog patch if audit finds the runner already strict-only. | STRUCTURAL |
| `I-PROBE-02` | `I-PROBE-STRICT-WARN-DISCIPLINE` | Strict-mismatch WARN discipline shared across every affected probe. | `strict_count_warnings: tuple[str, ...]` on every affected probe report; canonical printable line format (e.g. `"C5_TWO_TOKEN_COMBINATION strict_count=0 graceful_count=1"`); two fresh runs produce bit-identical tuples; WARN-only (never FAIL) per Phase 3.33 hard limits. | STRUCTURAL |

The "provisional, gated on the Step 4 audit" qualifier on
`I-CURR-15`, `I-AHYP-15`, and `I-OSMO-15` reflects ADR-001 D1
discipline: the strictness audit is the source of truth for which
probes are affected. If a probe's runner is found to be strict-only
already (or graceful in a non-disposition-based way — Decision rule 6
in `PHASE3_33_STRICTNESS_AUDIT_PLAN.md`, ESCALATE), its row is
dropped from the Step 8 catalog patch rather than left as a no-op
structural assertion. `I-PSPEECH-20` and `I-PROBE-02` are unconditional
because the proto-speech graceful-pass gap is the documented motivation
for the campaign and the WARN discipline applies across whichever
probes ultimately gain strict counters.

The numbering rule is "next available row number per probe namespace,"
not "global increment." Future phases follow the same rule:
`I-PSPEECH-21..`, `I-CURR-16..`, `I-AHYP-16..`, `I-OSMO-16..`,
`I-PROBE-03..` are the next slots when needed.

## Purpose

Detailed design for the Phase 3.33 Proto-Speech Strict Combination
Corrigendum, including the surgical scope of each report-layer
change, the strict counter computation rules, the WARN emission rule,
and the digest-stability discipline.

## Background

Phase 3.31's proto-speech probe TWO_TOKEN_COMBINATION condition has
a graceful-pass acceptance defined at lines 3239–3267 of
`brain/development/proto_speech_acquisition.py`:

```python
elif condition is ProtoSpeechCondition.TWO_TOKEN_COMBINATION:
    last = turns[-1]
    if last.selected_utterance.token_count != 2:
        status = ProtoSpeechStatus.FAIL
    else:
        combo_rec = final_table.select(
            context_signature=ctx_sig,
            utterance_digest=last.selected_utterance.digest_hex16,
        )
        if combo_rec is None or combo_rec.disposition is not (
            ProtoUtteranceDisposition.STABLE_COMBINATION
        ):
            # Acceptable if combination not yet "stable" by the
            # final turn but still emerged; require at least
            # CANDIDATE / REINFORCED disposition.
            if combo_rec is None or combo_rec.disposition not in (
                ProtoUtteranceDisposition.CANDIDATE,
                ProtoUtteranceDisposition.REINFORCED,
                ProtoUtteranceDisposition.STABLE_COMBINATION,
            ):
                status = ProtoSpeechStatus.FAIL
```

The graceful acceptance is GOOD ENGINEERING for early-development CI
gates. The problem is purely that the **report** doesn't surface the
gap, so a downstream consumer (the Phase 3.34 projector) cannot tell
the substrate is at B03_STABLE_IN_CONTEXT rather than B04_TRANSFERS
or B05_COMBINES.

## Design

### Strict counter computation rule

For every condition where a graceful acceptance set `{A, B, C}` is
used (where `A` is the canonical disposition and `B`, `C` are the
weaker accepted dispositions):

```python
graceful_count = count(records where disposition in {A, B, C})
strict_count   = count(records where disposition == A)
```

Both counts are computed from the same evidence (the same
`final_table.records()` tuple). The strict counter is a re-aggregation,
not a new pass through the runner.

### Field placement on the report dataclass

```python
@dataclass(frozen=True, slots=True)
class ProtoSpeechAcquisitionReport:
    # ... existing fields unchanged ...

    # Existing graceful counters (NOT removed, NOT renamed).
    stable_combination_count: int
    transfer_success_count: int
    # ... etc.

    # NEW: strict counters.
    stable_combination_count_strict: int
    transfer_success_count_strict: int

    # NEW: WARN-level structural findings.
    strict_count_warnings: tuple[str, ...]
```

### WARN emission rule

When a strict counter is **zero** and the corresponding graceful counter
is **non-zero**, the runner emits a WARN-level finding:

```python
def _emit_strict_warnings(
    stats: ProtoSpeechAcquisitionStats,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if stats.stable_combination_count_strict == 0 and \
            stats.stable_combination_count > 0:
        warnings.append(
            f"C5_TWO_TOKEN_COMBINATION strict_count=0 "
            f"graceful_count={stats.stable_combination_count}"
        )
    if stats.transfer_success_count_strict == 0 and \
            stats.transfer_success_count > 0:
        warnings.append(
            f"C6_HOLOPHRASE_TRANSFER strict_count=0 "
            f"graceful_count={stats.transfer_success_count}"
        )
    return tuple(warnings)
```

The condition-name prefix in the warning is the canonical condition
constant from `ProtoSpeechCondition`. The format is fixed and
deterministic. Two fresh runs produce bit-identical warning tuples.

### Digest stability discipline

`run_proto_speech_live_test()` returns a report with `digest_hex16`.
The digest input is the canonical evidence tuple, NOT the report
fields. Adding new report fields does not change the digest input,
so the digest remains bit-identical to Phase 3.31's reported value
(`f6a83b9caef0ac17`).

**This is verified by Step 9 of the campaign.** Any change to the
digest indicates the implementation has drifted from the design — the
strict counters or the warnings tuple have leaked into the digest
input. STOP and investigate.

### Where the strict counter is computed

Add a helper function in `proto_speech_acquisition.py`:

```python
def _compute_strict_combination_count(
    final_table: ProtoSpeechEvidenceTable,
) -> int:
    """Count evidence records with disposition == STABLE_COMBINATION.

    Strictly: no graceful acceptance of CANDIDATE or REINFORCED.
    """
    return sum(
        1
        for rec in final_table.records()
        if rec.disposition is ProtoUtteranceDisposition.STABLE_COMBINATION
        and rec.utterance_digest in _two_token_utterance_digests(rec)
    )


def _compute_strict_transfer_success_count(
    final_table: ProtoSpeechEvidenceTable,
) -> int:
    """Count evidence records with disposition == TRANSFERRED AND
    in a same-shape transfer target context.

    Strictly: no graceful acceptance of failed transfers.
    """
    return sum(
        1
        for rec in final_table.records()
        if rec.disposition is ProtoUtteranceDisposition.TRANSFERRED
        and rec.transfer_source_signature is not None
        and rec.transfer_target_shape_digest ==
            rec.transfer_source_shape_digest
    )
```

Both helpers are pure functions of the evidence table. They are
called once per `run_proto_speech_live_test()` invocation.

## Effect on Phase 3.31's report

Before Phase 3.33:

```text
proto_speech_acquisition.run_proto_speech_live_test() →
  ProtoSpeechAcquisitionReport(
    digest_hex16='f6a83b9caef0ac17',
    drive_stream_digest='dc060a88a814f448',
    false_positive_count=0,
    false_negative_count=0,
    stable_single_count=5,
    stable_combination_count=0,       # MASKED: looks like nothing
    suppressed_count=2,                # combined at all
    transfer_success_count=1,
    # ... other fields ...
  )
```

After Phase 3.33:

```text
proto_speech_acquisition.run_proto_speech_live_test() →
  ProtoSpeechAcquisitionReport(
    digest_hex16='f6a83b9caef0ac17',  # UNCHANGED
    drive_stream_digest='dc060a88a814f448',  # UNCHANGED
    false_positive_count=0,
    false_negative_count=0,
    stable_single_count=5,
    stable_combination_count=0,       # graceful counter unchanged
    stable_combination_count_strict=0, # NEW: also 0, exposing the gap
    suppressed_count=2,
    transfer_success_count=1,
    transfer_success_count_strict=1,   # NEW: same as graceful here
    strict_count_warnings=(
        # If a TWO_TOKEN_COMBINATION condition had graceful >0 and
        # strict ==0, a line would appear here. If graceful ==0,
        # no warning (there's nothing to compare).
    ),
    # ... other fields ...
  )
```

If `stable_combination_count` itself is zero in the Phase 3.31
baseline (the graceful count), then the strict count is necessarily
also zero, and no warning is emitted. The warning only fires when
**graceful > 0 AND strict == 0** — which is the precise condition
under which masking is occurring.

## What if the Phase 3.31 baseline has graceful == 0 too?

Then there's nothing masked. The substrate genuinely is not emitting
2-token combinations at all (not even as CANDIDATEs). In this case
Phase 3.33's effect on the proto-speech axis is:

- Strict counter is added (for future use).
- No warning is emitted (graceful is already 0).
- Phase 3.34's projector reads strict=0, graceful=0, and assigns
  PROTO_SPEECH_COMBINATION to B00_REFLEXIVE or B01_EMERGENT,
  depending on whether any 2-token utterance was attempted.

This is honest. The campaign has done its job.

## Audit-driven scope expansion

Step 4 of the campaign runs the strictness audit across the four
other probes. Probes whose runners have graceful-pass acceptance
will get strict counters in Steps 5a–5d. Probes without graceful-pass
acceptance get no changes.

Expected probable scope from preliminary inspection:

- `curriculum_consolidation_probe`: `survived_count_strict` (the
  graceful counter likely accepts marginal survivors). Audit confirms.
- `active_hypothesis_probe`: `winner_selected_count_strict` (the
  graceful counter accepts "winner OR no hypothesis survives" as
  PASS). Audit confirms.
- `osmotic_learning_probe`: `transfer_success_count_strict` (likely).
  Audit confirms.
- `worldlet_feedback_bridge`: no live-test runner per se; audit may
  find no graceful pass to surface. Audit confirms.

Final scope is set by the audit, not by this design doc. The audit
plan is in `PHASE3_33_STRICTNESS_AUDIT_PLAN.md`.

## Catalog rows

```text
I-PSPEECH-20          STRUCTURAL
  ProtoSpeechAcquisitionReport exposes stable_combination_count_strict
  and transfer_success_count_strict; both are computed from the same
  evidence as their graceful siblings with acceptance narrowed.

I-CURR-15             STRUCTURAL (if audit affirms)
  CurriculumConsolidationReport exposes survived_count_strict.

I-AHYP-15             STRUCTURAL (if audit affirms)
  ActiveHypothesisReport exposes winner_selected_count_strict.

I-OSMO-15             STRUCTURAL (if audit affirms)
  OsmoticLearningReport exposes transfer_success_count_strict.

I-PROBE-02    STRUCTURAL
  Every affected probe emits strict_count_warnings: tuple[str, ...]
  with the canonical format. Two fresh runs produce bit-identical
  warning tuples.
```

## Cross-references

- `PHASE3_33_STRICTNESS_AUDIT_PLAN.md` — the audit protocol.
- `ADR-003-strict-counter-pattern.md` — the full discipline.
- Phase 3.31 design: `docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_SPEC.md`.
