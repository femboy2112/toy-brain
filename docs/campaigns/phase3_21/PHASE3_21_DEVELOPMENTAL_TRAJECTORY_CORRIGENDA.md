# PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CORRIGENDA.md

## Purpose

Lock the Phase 3.21 design decisions in advance of the Step 4
catalog patch plan. Each LOCK names a single tightly-scoped
choice.

---

## LOCK A — Milestone set

**Locked:** exactly ten milestones, with closed-enum membership
`{M01_REFLEXIVE_BASELINE, M02_HABITUATION, M03_RECOGNITION,
M04_REHEARSAL, M05_PATTERN_SELF_FEEDBACK,
M06_STRUCTURAL_SELF_MONITORING, M07_MULTI_MODAL_INTEGRATION,
M08_SATURATION_NOVELTY, M09_CROSS_INPUT_DIFFERENTIATION,
M10_SUSTAINED_BEHAVIOR}`. The PHASE3_21_TEN_MILESTONES.md doc binds
each member's helper signature, inputs, success criterion, and
metrics.

**Out of v1 scope:** any additional milestone; any renaming;
any relaxation of the "structural marker only" framing.

---

## LOCK B — No new core runtime code

**Locked:** Phase 3.21 introduces exactly one new runtime module
`brain/development/milestone_harness.py`. No existing module is
modified for runtime behavior. The harness imports only:

```text
__future__, dataclasses, enum, typing,
brain.development.coherence_monitor (for build_full_coherence_report
    used by M06/M07; no deferred-import shim needed because
    milestone_harness is not imported by coherence_monitor),
brain.development.pattern_ledger (for derive_pattern_id /
    derive_pattern_signature used by M03/M09),
brain.development.processing_window (for FeedbackMode /
    InternalEventSource / PROCESSING_WINDOW_PROVENANCE_PREFIX),
brain.development.text_stream (for STREAM_PATTERN_RECURRENCE_*,
    STREAM_TEXT_MAX_LEN),
brain.development.growth_ledger (for GROWTH_LEDGER_MAX_EVENTS),
brain.tick (BrainState + initial_state + assert_state_invariants
    only — never the tick callable),
brain.ui.commands (Command / OperatorCommand / StreamAppendPayload),
brain.ui.session (OperatorSession),
brain.tlica.profile (COGITO_ID).
```

No `brain.llm`, no `curses`, no `os` / `subprocess` / `socket` /
`urllib` / `http` / `requests` / `pathlib` / `tempfile` / `shutil`
/ `threading` / `asyncio` / `atexit` / `signal` / `importlib` /
`time` / `random` / `hashlib` / `math`.

**Out of v1 scope:** any extension of `processing_window.py`,
`session.py`, or any other runtime file. The harness is a strict
consumer of the existing surfaces.

---

## LOCK C — MilestoneResult shape

**Locked:** `MilestoneResult` is a frozen / slotted dataclass with
exactly five fields: `milestone`, `status`, `summary`,
`primary_metric`, `secondary_metric`. The constructor enforces
bounded shapes (see PHASE3_21_TEN_MILESTONES.md Section 12).

**Out of v1 scope:** additional fields (especially anything that
could become an aggregate scalar). No `developmental_score`, no
`maturity_index`, no `growth_rate`.

---

## LOCK D — No aggregate scalar

**Locked:** Phase 3.21 introduces no aggregate scalar of any kind.
`run_all_milestones()` returns a tuple of ten records; the
acceptance condition is a per-record predicate; no rolled-up
index appears in the runtime, the catalog, the fixtures, or the
docs.

**Out of v1 scope:** any "developmental I-ness score", "maturity
score", "growth-trajectory score", "milestone-completion percent",
or any similar single scalar.

---

## LOCK E — Status enum

**Locked:** `MilestoneStatus` is a closed `(str, Enum)` with
exactly the members `{PASS, WARN, FAIL, NOT_APPLICABLE}`. These
labels are **structural status labels only**, never truth claims
or value judgments about the running system. The v1 acceptance
condition expects ten PASS / zero WARN / zero FAIL / zero
NOT_APPLICABLE.

**Out of v1 scope:** any additional status member; any
re-interpretation of the existing four labels.

---

## LOCK F — No psychological language

**Locked:** every produced summary string and every doc /
fixture / catalog row produced by Phase 3.21 is audited against
the canonical
`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
tuple. The audit must produce zero hits. The words "develop" /
"developmental" / "milestone" / "trajectory" are used only in
the operational sense (the runtime *develops a deterministic
trajectory*; the system *crosses a milestone* in the sequence);
never in the developmental-psychology sense.

**Out of v1 scope:** any relaxation of `_FORBIDDEN_NON_CLAIM_TERMS`;
any per-row exception; any reframing of "develop" /
"developmental" in psychological terms.

---

## LOCK G — No tick.py change

**Locked:** Phase 3.21 does **not** modify `brain/tick.py`,
`brain/tlica/**`, or any kernel surface. Every milestone helper
calls `STREAM_APPEND` only; `tick(...)` is never invoked.

**Out of v1 scope:** any edit to the kernel; any call to the
LLM seam; any change to `(new_state, TickRecord)` shape.

---

## LOCK H — No new GrowthEventType / GrowthEventSource

**Locked:** Phase 3.21 reuses the existing Growth Ledger event
types and sources. The M10 milestone documents that the Growth
Ledger may saturate at `GROWTH_LEDGER_MAX_EVENTS = 256` during
the sustained sequence; this is the existing bounded behavior
(no eviction at cap; the existing Phase 3.13 fixture covers it)
and counts as PASS for the milestone.

**Out of v1 scope:** any new event type / source; any change to
the Growth Ledger semantics.

---

## LOCK I — Determinism

**Locked:** every milestone helper is pure deterministic over its
inputs. Two invocations with identical `seed_offset` produce
bit-identical `MilestoneResult`. `run_all_milestones()` is
bit-deterministic across processes and OSes. The static-audit
fixture re-runs each helper with two different `seed_offset`
values to confirm determinism.

**Out of v1 scope:** any time / random / PID / hostname / `id()`
input.

---

## LOCK J — WARN justification

**Locked:** if Step 7 returns any WARN outcome, the
`PHASE3_21_MILESTONE_LOG.md` document must include an explicit
justification: the known limitation, why the milestone's intent
is still met, and what (if anything) the Step 8 behavior report
recommends for follow-up. The v1 acceptance condition expects
ten PASS; WARN is permitted only with justification.

**Out of v1 scope:** silent WARN; FAIL handling (the campaign
halts on FAIL).

---

## LOCK K — Stage C.1 implementation policy

**Locked:** Stage C.1 may be used for bounded doc shards
(synthesis, ten-milestones, corrigenda, catalog patch plan, PR
body) when the operator believes a shard is large enough to
justify bridge overhead. Stage C.1 may also be used for the
bounded milestone-harness module + fixture shards **after** Step 5
review gate, subject to:

- a validated manifest under the canonical
  `python3 -m tools.claude_helpers.flow_manifest validate`
  command;
- `max_parallel = 2`;
- at most 5 total Codex nodes across the campaign;
- no automatic retry;
- no overlap in declared write sets;
- no Codex staging / commit / push.

Stage C.1 is **forbidden** for: raw codex / codex exec invocation;
secrets, raw prompts, raw model responses; broad runtime changes;
`brain/tick.py` edits; final catalog reconciliation; the final
invariant runner gate.

Parent Claude commits and pushes every step.

---

## Lock cross-check vs the Step 5 autonomy authorization checklist

```text
 1. Step 4 has zero critical correctness blockers.
    -> Determined in Step 4 (catalog patch plan).
 2. Step 4 has zero safety/invariant blockers.
    -> Determined in Step 4.
 3. Step 4 does not require brain/tick.py edits.
    -> Locked here (LOCK G).
 4. Step 4 preserves L1/L2 cache semantics.
    -> Implied by LOCK B (no LLM seam touched).
 5. Step 4 preserves parser and prompt semantics.
    -> Implied by LOCK B.
 6. Step 4 preserves OFFLINE default + explicit opt-in.
    -> Implied by LOCK B + LOCK G.
 7. Step 4 has exact row family, statuses, count delta, fixture
    list, implementation files, validation plan.
    -> Step 4 output.
 8. Step 4 has a bounded developmental-trajectory design.
    -> Locked here (LOCK A + LOCK B + LOCK C + LOCK E + LOCK I).
 9. Step 4 does not introduce cognitive overclaims.
    -> Locked here (LOCK D + LOCK F).
10. Stage A review identifies no blocking flaw.
    -> Stage A not used in Phase 3.21 by default.
11. Implementation fits the allowed file set; stays within Lean spec.
    -> Locked here (LOCK B + LOCK G + LOCK H).
```

---

## Disclosure block

```text
Stage A ChatGPT/Codex consultation : not used
Stage B limited-write collaboration: not used
Stage C.1 flow orchestration       : not used
```

---

## Next artifact

`docs/campaigns/phase3_21/PHASE3_21_DEVELOPMENTAL_TRAJECTORY_CATALOG_PATCH_PLAN.md`
— the Step 4 catalog patch plan, which converts these locks into
exact rows, fixtures, files, counts, and validation steps.
