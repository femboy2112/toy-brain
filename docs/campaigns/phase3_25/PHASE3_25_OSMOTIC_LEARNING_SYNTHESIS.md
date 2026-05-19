# Phase 3.25 — Osmotic Learning Synthesis

## How the live test composes with the existing substrate

Phase 3.25 does not invent a new mechanism. It adds a deterministic
runner that probes whether the existing substrate — the Phase 3.22b
abstract-pattern signature layer (`AbstractPatternSignature`,
`derive_abstract_pattern_signature`) and the Phase 3.22b learning
evidence ledger (`ABSTRACT_PATTERN_ACQUIRED`,
`ABSTRACT_PATTERN_REUSED`, `TRANSFER_RECOGNIZED`) — realizes the
operational analogue of osmotic imprinting + activation under bounded
conditions.

The key substrate property is **structural digest stability under
renaming**: `derive_abstract_pattern_signature("red blue red blue")`
and `derive_abstract_pattern_signature("cat dog cat dog")` produce
the same `digest_hex16 == d37efc29b0c680ba` because both inputs share
the abstract shape `A B A B`. This is what makes the renamed-probe
transfer test meaningful: the runtime path never sees the abstract
shape as input, but the substrate computes the same digest from the
operator-input tokens because the form is the same.

## Mapping to TLICA imprinting

Per the Two-Layer Identity-Correlation Architecture:

- **Osmotic imprinting** is substrate-level, transverse to the four
  imprinting kinds, not a fifth parallel kind.
- **Imprinting** = formation of a substrate pattern.
- **Activation** = later operational triggering / reuse of the
  imprinted pattern.

ToyI's engineering analogues:

| TLICA concept | ToyI substrate analogue |
|---|---|
| Substrate-level imprinting | `ABSTRACT_PATTERN_ACQUIRED` record emitted on first exposure to an abstract digest |
| Substrate-level activation | `ABSTRACT_PATTERN_REUSED` + `TRANSFER_RECOGNIZED` records emitted on a later renamed probe with the same digest |
| Imprinting without focus / verification | the agent loop's `run_agent_interaction_step` does not classify the input as "structural" or "to-be-learned"; it just dispatches `STREAM_APPEND` and the substrate records the form |
| Later operational triggering | the same `run_agent_interaction_step` call on a renamed probe automatically routes through the same `_derive_evidence_for_step` path, which compares digests and emits the reuse / transfer records |

The two phases are distinct: the imprinting and activation records
are emitted on different `run_agent_interaction_step` calls with
different inputs; the digest equality is the bridge.

## Why this is engineering, not psychology

- ToyI has no attention mechanism, no focus, no salience filter, no
  preference, no goal, and no awareness. The substrate just records
  the digest of every operator-input form.
- "Osmotic" is a controlled technical metaphor for the
  *unlabeled exposure path*: the operator never says "learn this" or
  "remember this", but the substrate records the form anyway. There
  is no subjective absorption, intuition, or unconscious learning.
- The substrate is **lossy**: any abstract digest collision (e.g.
  two inputs that share the same shape) cannot be disambiguated.
  This is by design; the abstract-pattern layer is a *structural*
  signature, not a semantic one.

## What the test rules out

- A trivial echo runtime that records every input verbatim would
  fail C2 SHAM_EXPOSURE (the ABBA exposure would falsely match the
  later ABAB probe if "exposure" meant "lexical match"). The
  substrate passes C2 because the digest comparison is structural,
  not lexical.
- A pure novelty detector (treating every new pid as a fresh
  acquisition) would pass C0 control but fail C1 true exposure (it
  would not record `ABSTRACT_PATTERN_REUSED` on the renamed probe).
- A substrate that "absorbs every input as an instance of every
  prior shape" would emit false positives in C0 / C2. The substrate
  passes these because acquisition is digest-bounded.
- The static-audit fixture confirms the runner imports only the
  allowed module set; it cannot smuggle in a hidden model call or
  a `tick` invocation.

## What the test does NOT prove

- It does not prove ToyI is conscious / sentient / aware /
  intentional / intuitive.
- It does not prove ToyI has insight, understanding, or any
  cognitive-property of the running system.
- It does not establish a continuity of learning across sessions;
  the trial state is session-local only.
- It does not establish a multi-shot integration effect: each trial
  uses a fresh `AgentLoopState`; cross-trial residue is by design
  zero.

## Substrate dependencies (closed)

- `brain.development.abstract_pattern.derive_abstract_pattern_signature`
  computes the bounded structural digest.
- `brain.development.agent_loop.run_agent_interaction_step` is the
  single point through which the runner drives the agent loop.
- `brain.development.learning_evidence.has_acquired_digest` is the
  read-only inspection used to compute `prior_acquired_observed`.
- `brain.development.reasoning_trace.build_reasoning_trace_report`
  produces the bounded reasoning-trace digest for each probe.

No new imports beyond these. No `brain.llm`, no `brain.tick`, no
`brain.ui`, no curses, no I/O.
