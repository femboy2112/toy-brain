# CURRENT_MISSION.md — Phase 3.33 Proto-Speech Strict Combination Corrigendum

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.33 Proto-Speech Strict Combination
Corrigendum** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.33 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning
evidence, reasoning trace, dispatch trace, worldlet feedback, a
deterministic OFFLINE osmotic-imprinting live-test runner, a
deterministic OFFLINE active-hypothesis live-test runner, a
deterministic OFFLINE curriculum-consolidation live-test runner,
a deterministic OFFLINE caregiver-scaffolded proto-speech
live-test runner with graceful-pass acceptance masking the
stable-combination capability gap, and a thin ProbeReport
protocol from Phase 3.32 (Phases 3.18 - 3.32)
```

toward:

```text
the same substrate but with measurement-instrument transparency:
every probe whose runner uses graceful-pass acceptance also
exposes a *_strict counter computed from the same evidence with
acceptance narrowed to the canonical disposition; the proto-speech
probe specifically exposes stable_combination_count_strict and
transfer_success_count_strict; strict counter / graceful counter
mismatches emit WARN-level findings; no probe runner's test
conditions, priming sequences, thresholds, acceptance enums, or
evidence-update rules change; the baseline that Phase 3.34's
profile projector will read is honest across all probes
simultaneously. The campaign produces a bounded deterministic
proof report whose pre-existing digest_hex16 fields are unchanged
(no behavior change), whose strict-counter fields are non-empty
where the audit found masking, and whose strict_count_warnings
tuples are deterministic across two fresh runs.
```

Allowed claim shape:

```text
"ToyI's probe reports now expose both graceful-pass counters and
strict counters where graceful-pass acceptance is used; strict
counters are computed from the same per-condition evidence with
acceptance narrowed to the canonical disposition; mismatches emit
WARN-level structural findings; no probe runner behavior changes.
This is a measurement-instrument transparency improvement over a
bounded structural state machine, not a claim of capability
change, cognition, sentience, awareness, intentionality, learning,
language acquisition, language understanding, or any cognitive
process. ToyI remains a bounded structural state machine."
```

Forbidden claim shape:

```text
"ToyI has learned to be more honest / acquired better self-
knowledge / become more accurate / improved its self-assessment /
gained insight / become more introspective / improved its
metacognition."
```

If asked whether ToyI is conscious / sentient / aware / introspective /
learning, the runtime's deterministic reply must DENY the cognitive
claim and describe itself as a bounded structural runtime.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_33_PROTO_SPEECH_STRICT_CORRIGENDUM_ROADMAP.md
docs/campaigns/phase3_33/PHASE3_33_DESIGN.md
docs/campaigns/phase3_33/PHASE3_33_STRICTNESS_AUDIT_PLAN.md
ADR-001-locked-decisions-D1-D8.md
ADR-003-strict-counter-pattern.md
ADR-004-target-axes-regression-gate.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/proto_speech_acquisition.py
brain/development/curriculum_consolidation_probe.py
brain/development/active_hypothesis_probe.py
brain/development/osmotic_learning_probe.py
brain/development/probe_report_protocol.py
brain/development/coherence_monitor.py
tools/catalog.py
tools/check_all.sh
```

---

## Local command rule

Use `python3 -m ...` for Python module commands. Do not run real LLM
scenario commands unless the user explicitly asks.

---

## Stop conditions

Stop and report if:

- worktree is dirty before changes;
- branch is wrong;
- `main` does not yet contain the Phase 3.32 ProbeReport protocol
  (Phase 3.33 depends on it);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- adding a strict counter would require changing a probe runner's
  behavior (out of scope for 3.33 — defer to Phase 3.35+);
- any probe's `digest_hex16` would change as a result of strict
  counter addition (the digest is excluded from strict-counter
  effects by design; a change indicates the implementation has
  drifted from the design).

Stop at Phase 3.33 acceptance (every criterion in
`PHASE3_33_PROTO_SPEECH_STRICT_CORRIGENDUM_ROADMAP.md` is
satisfied), open the new PR (head
`campaign/phase3-33-proto-speech-strict-corrigendum`) against
`main`, and update `PHASE3_HANDOFF_STATE.md`.

---

## Efficiency notes for Claude Code

- Step 4 (the strictness audit across the four other probes) is
  the heaviest single piece of cognitive work. Offload it to the
  `brain-probe-strictness-auditor` agent via
  `.claude/agents/brain-probe-strictness-auditor.md` and let it
  produce findings before authoring strict counters in Step 5.
- Steps 5a / 5b / 5c / 5d (one strict counter per affected probe)
  are file-disjoint and can be authored in parallel batches.
- The bundle includes `_to_tools/developmental_profile_audit.py`
  which has a `--audit-only` mode that does Step 4 by reading the
  probe modules' source and looking for the graceful-pass pattern.
  Faster than reading each probe module manually.
- Total expected token budget: ~30-40k tokens for the strictness
  audit, ~15-20k tokens per strict-counter addition, ~10k tokens
  for the static-audit fixture + catalog rows. Well within session
  budget.
- See `workflow/PARALLEL_EXECUTION_PATTERNS.md` for the precise
  fan-out graph.
