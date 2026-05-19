# PHASE3_33_PROTO_SPEECH_STRICT_CORRIGENDUM_ROADMAP.md — Phase 3.33

## One-paragraph thesis

Phase 3.33 is a **diagnostic-only** corrigendum. It surfaces the
masked proto-speech two-token-stability gap by adding
`stable_combination_count_strict` to the proto-speech probe's report,
emits a WARN when the strict count is zero while graceful conditions
PASS, and establishes the `_strict` counter pattern as project-wide
discipline by auditing every other probe with graceful-pass
acceptance and adding strict counters wherever masking is found. No
probe's runner behavior changes. No test condition is altered. The
only changes are: (1) new report fields, (2) new audit fixtures, (3)
new structural catalog rows, and (4) WARN-level findings in the
existing reports. The baseline that Phase 3.34's profile projector
will read becomes honest across all axes simultaneously.

## Branch

```text
campaign/phase3-33-proto-speech-strict-corrigendum
```

Base: reconciled `main` from Phase 3.32.

## Mandatory non-claim discipline

This is a measurement-instrument transparency fix. It does not change
behavior. It does not make a new cognitive claim. The WARN-level
finding is structural: "the strict acceptance criterion did not hold
in N conditions." It is not a claim about ToyI's psychology.

## Acceptance criteria

Phase 3.33 succeeds only when every item below is true:

### Strict counter on proto-speech (the headline fix)

- `brain.development.proto_speech_acquisition.ProtoSpeechAcquisitionReport`
  exposes `stable_combination_count_strict: int` and
  `transfer_success_count_strict: int` (audit may identify more).
- The strict counter for `stable_combination_count_strict` counts only
  evidence records with `disposition == STABLE_COMBINATION`. It does NOT
  count `CANDIDATE` or `REINFORCED`.
- The strict counter for `transfer_success_count_strict` counts only
  evidence records with `disposition == TRANSFERRED` AND
  `context_signature` matching a `same_shape` transfer target. (No
  graceful acceptance of failed transfers.)
- `run_proto_speech_live_test()` digest is **unchanged** because the
  report's `digest_hex16` does not include the new strict fields by
  default. (See §"Digest discipline" below.)
- A new WARN-level field `strict_count_warnings: tuple[str, ...]` is
  emitted on the report. Each entry is a bounded printable line of the
  form: `"C5_TWO_TOKEN_COMBINATION strict_count=0 graceful_count=1"`.
- Both invocations of `run_proto_speech_live_test()` on the same
  substrate produce bit-identical `digest_hex16` AND bit-identical
  strict counter fields AND bit-identical warning tuples.

### Strictness audit (the discipline establishment)

- `docs/campaigns/phase3_33/PHASE3_33_STRICTNESS_AUDIT_PLAN.md` is
  fully populated with the audit results across all five probes
  (proto_speech, curriculum_consolidation, active_hypothesis,
  osmotic_learning, worldlet_feedback).
- Every probe report identified by the audit as having graceful-pass
  acceptance receives at least one `_strict` counter for that
  condition. The strict counter is computed from the same evidence
  as the graceful counter, with narrowed acceptance.
- Every affected probe emits its own `strict_count_warnings` tuple
  with the same bounded printable format.
- No probe runner's test conditions, priming sequences, thresholds,
  acceptance enums, or evidence-update rules change. Only the report
  layer is altered.

### Catalog

- v0.38 → v0.39.
- New STRUCTURAL rows:
  - `I-PSPEECH-20` (proto-speech strict counters present)
  - `I-CURR-15` (curriculum consolidation, if audit affirms)
  - `I-AHYP-15` (active hypothesis, if audit affirms)
  - `I-OSMO-15` (osmotic learning, if audit affirms)
  - `I-PROBE-02` (strict-mismatch emits WARN, not FAIL)
- No new REQUIRED rows. (No new test passes/fails are claimed; only
  observability is added.)

### Existing axes do not regress

- A1..A15 same case totals as before.
- A1..A15 same digests as before (because no runner behavior changed).
- `python3 -m brain.invariants run` fully green.
- `bash tools/check_all.sh` green.
- `python3 -m tools.claude_helpers.gate_runner --json` 5/5 PASS.

### TARGET_AXES declaration (for the eventual Phase 3.34 regression gate)

```text
TARGET_AXES_FOR_DEVELOPMENTAL_PROFILE = {
    PROTO_SPEECH_COMBINATION,
    PROTO_SPEECH_TRANSFER,
    # plus any axes whose probe was affected by the audit
}
```

The expected direction in Phase 3.34's first projector run is downward
(or unchanged) on these axes. Upward would indicate a catalog error.

## Step ledger (planned)

```text
Step 1   Design + audit plan + roadmap sync                  phase3.33 step1
Step 2   stable_combination_count_strict on proto-speech     phase3.33 step2
Step 3   transfer_success_count_strict on proto-speech       phase3.33 step3
Step 4   Strictness audit across the four other probes       phase3.33 step4
Step 5   Strict counters on affected probes (parallel)       phase3.33 step5
Step 6   strict_count_warnings field on all affected probes  phase3.33 step6
Step 7   Static-audit fixtures for strict counter presence   phase3.33 step7
Step 8   Catalog v0.38 → v0.39 (+5 STRUCTURAL rows)          phase3.33 step8
Step 9   Verify A1..A15 digests unchanged; gates green       phase3.33 step9
Step 10  Open PR; update PHASE3_HANDOFF_STATE.md             phase3.33 step10
```

Push after every successful step.

### Parallelizable steps

Step 5 fans out one strict counter per affected probe. Steps 5a/5b/5c/5d
are independent and can be authored in parallel (file-disjoint commits).

Step 4 audit is fan-out-friendly to Codex (see
`OFFLOAD_TO_CODEX_PATTERNS.md`).

## Digest discipline

The proto-speech runner's `digest_hex16` is computed from the
canonical evidence tuple. Adding new report fields that are NOT in
the digest input keeps the digest stable, which is what we want
(no apparent behavior change).

The strict counters and `strict_count_warnings` tuple are **outside**
the digest input. They are observability, not behavior.

A separate digest, `report_digest_with_strictness_hex16`, may be
computed for downstream consumers that want a stable hash of the
full report including strict fields. This is optional and can be
added in Phase 3.34 if the projector wants it.

## Hard limits

```text
- No probe runner's test conditions change.
- No new threshold values.
- No new priming sequence lengths.
- No new ProtoVocalToken, ProtoSpeechCondition, or
  ProtoUtteranceDisposition member.
- No new evidence-update rule.
- No removal or rename of an existing graceful counter.
- No FAIL emission when strict mismatch occurs (WARN only).
- No regression on A1..A15 digests.
- No new OperatorCommand, LOCAL_COMMAND_VERBS, ACTIVE_VIEWS,
  GrowthEventType, GrowthEventSource, LearningEvidenceKind,
  or ReasoningStepKind member.
- No DB schema change.
- No brain.llm import.
- No brain.tick.tick call outside STEP_TICK.
- 0 real model calls.
- 0 cache writes.
```

## Cross-references

- `docs/campaigns/phase3_33/PHASE3_33_DESIGN.md` — the surgical scope
  of every report field added.
- `docs/campaigns/phase3_33/PHASE3_33_STRICTNESS_AUDIT_PLAN.md` — the
  audit protocol and the per-probe findings template.
- `ADR-001-locked-decisions-D1-D8.md` — D1 mandates diagnostic-only,
  D3 mandates the `_strict` pattern.
- `ADR-003-strict-counter-pattern.md` — the full discipline.
- `ADR-004-target-axes-regression-gate.md` — declares why this
  campaign's TARGET_AXES is non-empty.
