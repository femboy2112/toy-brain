# CURRENT_CAMPAIGN.md — Phase 3.33 Proto-Speech Strict Combination Corrigendum

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED /
DIAGNOSTIC-ONLY (per ADR-001 D1)
```

Phase 3.33 stacks on the completed Phase 3.32 work
(`campaign/phase3-32-mainline-reconciliation`, expected PR #34 merged
into `main`). Phase 3.33 asks one bounded question:

```text
Under bounded read-only audit, do the existing five probe runners
(proto_speech_acquisition, curriculum_consolidation_probe,
active_hypothesis_probe, osmotic_learning_probe,
worldlet_feedback_bridge) use graceful-pass acceptance that masks
substrate capability gaps? For every probe where the answer is
yes, the campaign adds a *_strict counter to the report layer
that is computed from the same evidence with acceptance narrowed
to the canonical disposition; emits a WARN-level finding when
strict-vs-graceful counts diverge; and updates the static-audit
fixture to assert the strict counter is present. The campaign
does NOT change any probe runner's test conditions, priming
sequences, thresholds, acceptance enums, or evidence-update
rules. The pre-existing digest_hex16 on every probe report
remains bit-identical to its Phase 3.31/3.32 baseline.
```

This is a **diagnostic / observability** campaign. It is **NOT** a
proof of cognition, sentience, learning, language acquisition, or
any cognitive process. The campaign explicitly surfaces a previously
masked measurement gap; it does not change the underlying substrate.
The substrate has the same capability it had after Phase 3.31 — we
are simply now able to see it.

Phase 3.33 does **not** implement SelfModel; does **not** add any new
`OperatorCommand` member, `LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS`
value, `GrowthEventType`, `GrowthEventSource`, persistence schema
column, autosave trigger, `LearningEvidenceKind` member, or
`ReasoningStepKind` member; does **not** change L1 / L2 / parser /
prompt / tick / persistence / autosave / DB schema semantics. The
runtime touches are limited to:

- **Strict counter fields** added to the existing probe report
  dataclasses. Each strict counter is computed from the same
  per-condition evidence as its graceful sibling, with the
  acceptance set narrowed to the canonical disposition. NO RUNNER
  BEHAVIOR CHANGES.

- **`strict_count_warnings: tuple[str, ...]`** field added to each
  affected report. Each entry is a bounded printable line: e.g.,
  `"C5_TWO_TOKEN_COMBINATION strict_count=0 graceful_count=1"`.

- **One new fixture per affected probe**, asserting strict counter
  presence on the report dataclass.

- **Catalog patch**: v0.38 → v0.39 with +5 STRUCTURAL rows (one per
  affected probe + one for the WARN discipline). No new REQUIRED
  rows.

Branch:

```text
campaign/phase3-33-proto-speech-strict-corrigendum
```

Base: `main` (post-Phase-3.32). If `main` does not yet contain the
Phase 3.32 ProbeReport protocol, STOP.

Final PR (likely #35): `phase3.33: proto-speech strict combination
corrigendum`.

---

## Step ledger

```text
Step 1   Design + audit plan + roadmap sync                  commit phase3.33 step1
Step 2   stable_combination_count_strict on proto-speech     commit phase3.33 step2
Step 3   transfer_success_count_strict on proto-speech       commit phase3.33 step3
Step 4   Strictness audit (other 4 probes)                   commit phase3.33 step4
Step 5a  Strict counter on curriculum_consolidation_probe    commit phase3.33 step5a
Step 5b  Strict counter on active_hypothesis_probe           commit phase3.33 step5b
Step 5c  Strict counter on osmotic_learning_probe            commit phase3.33 step5c
Step 5d  Worldlet feedback (audit-driven, may be no-op)      commit phase3.33 step5d
Step 6   strict_count_warnings field on all affected probes  commit phase3.33 step6
Step 7   Static-audit fixtures for strict counter presence   commit phase3.33 step7
Step 8   Catalog v0.38 → v0.39 (+5 STRUCTURAL rows)          commit phase3.33 step8
Step 9   Verify A1..A15 digests unchanged; gates green       commit phase3.33 step9
Step 10  Open PR; update PHASE3_HANDOFF_STATE.md             commit phase3.33 step10
```

Push after every successful step.

Steps 5a/5b/5c/5d are file-disjoint and can be done in parallel.
Steps 6, 7, 8 can also overlap (different files, no shared state).

---

## Hard non-claim boundary

- No claim of consciousness, sentience, awareness, agency, will,
  desire, belief, communicative intent, inner speech, hidden
  chain-of-thought, introspection, metacognition, learning, language
  acquisition, language understanding, or any cognitive process.
- No aggregate scalar (no "self-knowledge score", no "honesty
  score", no "transparency index").
- No reply text uses language of being more "honest" or "accurate"
  about itself; the runtime is a bounded structural state machine.
- The strict counter is a re-aggregation of existing per-condition
  evidence, not a new measurement. The probe still passes by the
  same graceful-acceptance criterion it did before.

---

## Hard runner-invariance boundary (specific to 3.33)

```text
THE FOLLOWING ARE FORBIDDEN IN PHASE 3.33:
- Changing any probe runner's priming sequence length.
- Changing any closed-rule threshold (STABLE_COMBINATION_THRESHOLD,
  REINFORCEMENT_DELTA, SUPPRESSION_THRESHOLD, ...).
- Changing any acceptance enum (ProtoUtteranceDisposition,
  CurriculumConsolidationDisposition, ...).
- Adding a new ProtoVocalToken, CaregiverFeedbackKind,
  ProtoSpeechCondition, or other closed-rule enum member.
- Removing or renaming any existing graceful counter.
- Causing any probe's digest_hex16 to differ from its Phase 3.31/3.32
  baseline. The digest input is unchanged by design; if a step would
  change it, the step is out of scope.
- Emitting FAIL when strict mismatch occurs. WARN only.
- Treating the WARN as a gate-blocker. WARN findings are
  observability, not gate signals.
```

If any step's planned implementation appears to require one of the
above, STOP and report. Phase 3.33 is diagnostic-only.

---

## Acceptance criteria

Phase 3.33 succeeds only when:

1. `ProtoSpeechAcquisitionReport` exposes `stable_combination_count_strict`
   and `transfer_success_count_strict`.
2. Strict counters are correctly computed from the same per-condition
   evidence as their graceful siblings (verified by unit-style fixture).
3. Every affected probe (from Step 4 audit) has at least one strict
   counter.
4. Every affected probe emits `strict_count_warnings: tuple[str, ...]`.
5. `run_proto_speech_live_test()` and the other probe runners produce
   bit-identical `digest_hex16` to their Phase 3.31/3.32 baselines.
6. Two invocations of each runner produce bit-identical strict
   counters and bit-identical warning tuples.
7. Catalog v0.38 → v0.39 with +5 STRUCTURAL rows.
8. A1..A15 same case totals, same digests, all green.
9. `python3 -m brain.invariants run` fully green.
10. `bash tools/check_all.sh` and `python3 -m
    tools.claude_helpers.gate_runner --json` report 5/5 PASS.
11. No `brain.llm` import added; no `brain.tick.tick` call outside
    STEP_TICK; no DB schema change; no curses; no `random`, `time`,
    or external nondeterministic seed introduced.
12. PR opens with head `campaign/phase3-33-proto-speech-strict-corrigendum`
    against `main`; no PR is merged.

---

## Sequencing notes

- Step 4 (audit) should run BEFORE Step 5* (strict counter
  additions). If the audit reveals a probe has no graceful-pass
  acceptance, the corresponding Step 5 is a no-op (record this in
  the campaign log).
- Step 9 (verify digests unchanged) MUST be run after every
  Step 5* commit. If the digest changes, revert and investigate.

---

## Cross-references

- `PHASE3_33_PROTO_SPEECH_STRICT_CORRIGENDUM_ROADMAP.md` — full
  scope and acceptance.
- `docs/campaigns/phase3_33/PHASE3_33_DESIGN.md` — design walkthrough.
- `docs/campaigns/phase3_33/PHASE3_33_STRICTNESS_AUDIT_PLAN.md` —
  audit protocol.
- `ADR-001-locked-decisions-D1-D8.md` — D1 mandates diagnostic-only.
- `ADR-003-strict-counter-pattern.md` — full discipline.
- `ADR-004-target-axes-regression-gate.md` — the TARGET_AXES
  declaration for the eventual Phase 3.34 regression gate.
- `.claude/agents/brain-probe-strictness-auditor.md` — the agent
  that automates Step 4.
- `tools/developmental_profile_audit.py` — script that fan-outs the
  Step 4 audit work.
