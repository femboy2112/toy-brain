# PHASE3_31_FINDINGS.md — Phase 3.31

## Top-level findings

1. **Drive-stream-grounded babble works**. Every babble emitted
   by the v1 battery traces back to a closed-kind frame in the
   `ProtoSpeechDriveStream`. No `random` / `time` / external
   seed is used; the static-audit fixture
   (`proto_speech_static_audit.py`) confirms the module source
   contains no `import random` / `from random` / `import time`
   / `from time` fragment.
2. **Caregiver feedback substrate updates are deterministic and
   bounded**. The closed integer rule set (`ACCEPTED` +3,
   `ECHO` +3, `EXPANDED` +1/+4, `CORRECTED` -2/+3, `IGNORED`
   -1, `AMBIENT_ONLY` +1) produces the v1 expected outcomes
   without any nondeterminism. The
   `ProtoSpeechEvidenceTable.digest_hex16` is stable across two
   invocations on equal inputs.
3. **Holophrastic transfer requires shape-digest equality**.
   The renamed-same-shape target context receives a
   TRANSFERRED record; the different-shape negative control
   does not. The v1 report has `transfer_success_count == 1`
   and `false_positive_count == 0`.
4. **Two-token combination gating is robust**. The combination
   form emerges only when two STABLE_SINGLE prerequisites are
   present in the context AND a COMBINATION_PRESSURE drive
   frame is added. The v1 plan demonstrates this without any
   premature 2-token emission.
5. **Suppression terminates ineffective forms**. Five IGNORED
   turns drive NA below the -3 threshold; the
   SUPPRESSION_PRESSURE drive frame thereafter filters NA from
   the eligibility set in the same context.
6. **Cognitive-claim refusal is intact**. The REFUSAL_HELD
   condition emits the REFUSAL_SENTINEL (length-0 utterance)
   and adds zero evidence records; no learned proto-utterance
   was ever surfaced under refusal-guard.
7. **Benchmark axis A15 lands green**. 18 cases A15.01..A15.18
   PASS; the full battery is 137 cases / 136 PASS / 1 WARN
   (A3.04 carry-over) / 0 FAIL. Transcript digest stable across
   two invocations.
8. **Catalog v0.37 is consistent**. `python3 -m tools.catalog
   counts` reports banner == actual == expected for every
   category (REQUIRED 392, STRUCTURAL 101, NOT-EXERCISED 14,
   DEFERRED 15, OBSERVED 16). 501 invariant rows; 0 RED; 0
   gate failures.
9. **All canonical gates green**. `python3 -m
   tools.claude_helpers.gate_runner --json` reports 5/5 PASS
   (catalog_counts, citations_verify, import_audit,
   invariants_run, check_all).

## Open / deferred items

- **W1**: No persistence of the proto-speech evidence table
  across sessions. The table is session-local only. Cross-
  session retention is a future campaign.
- **W2**: Two-token combinations do not yet themselves transfer
  across same-shape contexts; only single-token STABLE_SINGLE
  forms transfer. The transfer mechanism could be widened in a
  future campaign, but the bounded operational definition would
  need explicit thresholds and an additional audit row family.
- **W3**: The A3.04 (`coherence_variation` `NOT_APPLICABLE`)
  WARN carry-over from Phase 3.21 W3 is unchanged. Phase 3.31
  does not address it.
- **W4**: The proto-speech evidence rules do not currently
  promote a stable proto-form to an explicit verification-
  pathway tool. The architecture documents this future
  threshold but explicitly leaves it out of scope.

## What is operationally claimed

ToyI's runtime now exhibits bounded operational caregiver-
scaffolded proto-speech behavior: given a bounded structural
context and bounded caregiver ambient utterances plus bounded
caregiver feedback records, the runtime constructs a bounded
explicit `ProtoSpeechDriveStream` from public substrate
snapshots, selects a deterministic bounded `ProtoUtterance`
from that stream filtered by a session-local
`ProtoSpeechEvidenceTable`, updates the evidence table by a
closed-rule integer-weight update driven by a closed
`CaregiverFeedbackKind` enumeration, promotes single-token
forms to `STABLE_SINGLE` after enough reinforcement, emits a
`STABLE_COMBINATION` two-token form only when combination
pressure plus two distinct stable singles exist, transfers a
stable single only to a same-shape-digest context, suppresses
forms below the suppression threshold, and retains the
cognitive-claim refusal path. This is an operational
co-occurrence + closed-rule weight update + drive-stream-
grounded eligibility selection + LRU-style suppression +
shape-digest transfer effect over bounded structural records,
not a claim of language acquisition, language understanding,
communicative intent, inner speech, hidden chain-of-thought,
private subjective thought, agency, will, desire, belief,
introspection, metacognition, or any cognitive process.

## What is explicitly NOT claimed

- No consciousness, sentience, awareness, subjective experience,
  understanding, inner speech, private thought, hidden chain-
  of-thought, communicative intent, agency, will, desire,
  belief, introspection, metacognition, curiosity,
  deliberation, language acquisition, language understanding,
  or audience modelling.
- No new aggregate scalar (no "language score", no "fluency
  index", no "I-ness score").
- No claim that the chosen utterance tokens carry human
  semantics. SAME, MORE, AGAIN, NO, LOOK, DONE, HELP, etc. are
  not born with fixed meanings; their context-conditional
  binding emerges only from accumulated co-occurrence evidence.
