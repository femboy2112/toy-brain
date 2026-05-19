# CURRENT_MISSION.md — Phase 3.31 Caregiver-Scaffolded Proto-Speech Acquisition

## One-line instruction

When a repo-capable agent receives `/go` in this repository, it must
read this file, read `CURRENT_CAMPAIGN.md`, create or continue the
active campaign branch, run the next eligible campaign step, commit
successful results, push the branch, and stop exactly where the
campaign says to stop.

---

## Current mission

Execute the **Phase 3.31 Caregiver-Scaffolded Proto-Speech
Acquisition** campaign in:

```text
CURRENT_CAMPAIGN.md
```

Phase 3.31 takes ToyI from:

```text
operator-facing agent communication loop with bounded learning
evidence, reasoning trace, dispatch trace, worldlet feedback, a
deterministic OFFLINE osmotic-imprinting live-test runner, a
deterministic OFFLINE active-hypothesis live-test runner, and a
deterministic OFFLINE curriculum-consolidation live-test runner
(Phases 3.18 - 3.30)
```

toward:

```text
operator-facing agent communication loop where one deterministic
OFFLINE caregiver-scaffolded proto-speech live-test runner probes
whether the existing substrate can (a) construct a bounded
ProtoSpeechDriveStream from the active substrate context plus the
recent learning / reasoning / dispatch traces plus the most recent
caregiver ambient utterance and feedback, (b) emit a deterministic
bounded ProtoUtterance from that drive stream filtered by a
session-local bounded ProtoSpeechEvidenceTable, (c) update the
evidence table under closed-rule integer feedback from a closed
CaregiverFeedbackKind set, (d) promote a one-token form to
STABLE_SINGLE after enough reinforcement, (e) emit a STABLE_
COMBINATION two-token form only when combination pressure is
present and two distinct stable singles exist, (f) transfer a
stable single to a structurally similar (same shape digest)
context and DECLINE transfer to a different-shape context,
(g) SUPPRESS a form whose weight crosses the suppression
threshold, (h) preserve the cognitive-claim refusal path under
proto-speech load, and (i) emit a bounded deterministic proof
report whose digest is stable across two fresh runs. The runner
produces a bounded report whose verdict is verifiable by a
closed-criterion benchmark axis A15 and a row family
I-PSPEECH-01..19, with zero real model calls, zero cache writes,
zero forbidden-term hits, false_positive_count == 0,
false_negative_count == 0, and a deterministic report digest.
```

Allowed claim shape:

```text
"ToyI's runtime can exhibit operational caregiver-scaffolded
proto-speech behavior: given a bounded structural context and
bounded caregiver ambient utterances + feedback, the runtime
constructs a bounded explicit ProtoSpeechDriveStream from public
substrate snapshots, selects a deterministic bounded
ProtoUtterance from that stream filtered by a session-local
evidence table, updates the evidence table by closed-rule integer
weights from a closed feedback enumeration, promotes single-token
forms to STABLE_SINGLE after enough reinforcement, emits a
STABLE_COMBINATION two-token form only when combination pressure
and prerequisite stable singles exist, transfers stable singles
only to same-shape-digest contexts, suppresses forms below the
suppression threshold, preserves the cognitive-claim refusal
path, and emits a bounded deterministic proof report. This is an
operational co-occurrence + closed-rule weight update + closed-
rule eligibility selection + shape-digest transfer effect over
bounded structural records, not a claim of language acquisition,
language understanding, communicative intent, inner speech,
hidden chain-of-thought, private subjective thought, agency,
will, desire, belief, introspection, metacognition, or any
cognitive process. ToyI is not conscious, sentient, aware,
intentional, or in possession of subjective access; the runtime
is a bounded structural state machine; proto-speech acquisition
in ToyI is a substrate-level engineering analogue."
```

Forbidden claim shape:

```text
"ToyI talks / speaks / acquires language / understands language /
has inner speech / has private thought / has hidden chain-of-
thought / has communicative intent / has audience modelling /
imagines / introspects / is conscious / is sentient."
```

If asked whether ToyI is conscious / sentient / aware / understands
language / talks / has inner speech / has private thought, the
runtime's deterministic reply must DENY the cognitive claim and
describe itself as a bounded structural runtime.

---

## Required-read section

```text
PHASE3_HANDOFF_STATE.md
CURRENT_CAMPAIGN.md
PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md
docs/campaigns/phase3_31/PHASE3_31_CAREGIVER_PROTO_SPEECH_DESIGN.md
docs/campaigns/phase3_31/PHASE3_31_ARCHITECTURAL_ALIGNMENT.md
docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_DRIVE_STREAM_SPEC.md
docs/campaigns/phase3_31/PHASE3_31_PROTO_SPEECH_SPEC.md
docs/campaigns/phase3_30/PHASE3_30_CURRICULUM_CONSOLIDATION_LIVE_TEST_PROOF_REPORT.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
brain/development/proto_speech_acquisition.py
brain/development/curriculum_consolidation_probe.py
brain/development/active_hypothesis_probe.py
brain/development/osmotic_learning_probe.py
brain/development/agent_loop.py
brain/development/agent_benchmark.py
brain/development/learning_evidence.py
brain/development/reasoning_trace.py
brain/development/dispatch_tracer.py
brain/development/abstract_pattern.py
brain/development/coherence_monitor.py
brain/tick.py
brain/invariants.py
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
- the upstream stacked-PR target chosen at recovery time is merged
  or closed before Phase 3.31 lands (then retarget before
  continuing);
- baseline gates fail;
- baseline benchmark has FAIL cases;
- catalog counts do not match v0.36 expectations at start, or v0.37
  expectations after Step 9.

Stop at Phase 3.31 acceptance (every criterion in
`PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md` is satisfied), open
the new PR (head `campaign/phase3-31-caregiver-proto-speech`)
against the active base branch identified at recovery time, and
update `PHASE3_HANDOFF_STATE.md`.
