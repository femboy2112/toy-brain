# Phase 3.24 — Worldlet Substrate Survey

This document is the repo-grounded analysis Phase 3.24 Step 1 produces
**before any worldlet-feedback implementation lands**. It establishes
what worldlet records already exist, what their public surface looks
like, and which surface the new feedback path is allowed to read.

## 1. What worldlet records exist today

The Minimal Worldlet substrate (Phase 3.3, catalog rows
`I-WLD-01..I-WLD-12`) ships the following frozen / slotted records in
`brain/development/worldlet.py`:

| record | summary |
|---|---|
| `WorldletObject` | one finite target on the local harness; carries `object_id`, `label`, `available: bool`, `accepted_token_ids: frozenset`. |
| `WorldletState` | immutable snapshot of the deterministic harness; carries `state_id`, `objects: Mapping[id -> WorldletObject]`, `step_index: int >= 0`. |
| `WorldletProvenance` | bounded provenance metadata: `source_kind: FrameSourceKind`, `confidence: Fraction in [0,1]`, `trace_event_ids: tuple[TraceEventID, ...]`. |
| `WorldletAttempt` | below-agency attempt record; `attempt_id`, `token_id`, `pattern_id`, `target_id`, `provenance`. |
| `WorldletValence` | exact `Fraction` valence in `[-1, 1]`. |
| `WorldletResponse` | `response_id`, `attempt_id`, `accepted: bool`, `reason in {accepted, missing-target, rejected, target-unavailable}`, `valence`, `provenance`. |
| `WorldletHistory` | copy-on-write `(latest_state, attempts, responses)` triple. |
| `WorldletConsequenceSummary` | bounded inspectable summary of a single response (`summarize_worldlet_consequences` walks the history). |

## 2. Where worldlet state lives on the session

`brain/ui/session.py` declares the field

```python
worldlet_history: Optional["WorldletHistory"] = None
```

in `OperatorSession`. It is listed in `_ALLOWED_SESSION_ATTRS` (so the
I-UI-10 audit accepts it). The default is `None`: an operator who never
exercises the worldlet harness never pays a cost.

## 3. Which UI commands mutate worldlet_history

**None.** A whole-tree grep across `brain/ui/commands.py`,
`brain/ui/session.py`, `brain/ui/persistence.py`, and the rest of the UI
surface shows zero call sites that *assign* a new `WorldletHistory` to
`OperatorSession.worldlet_history`. The field is **populated only
explicitly by test fixtures or by future / external code paths**. No
existing command, no parser path, no autosave hook, and no persistence
layer reads or writes `worldlet_history`.

This is the load-bearing observation for Phase 3.24: the
worldlet-feedback path must therefore **tolerate
`worldlet_history is None`** as the dominant operator scenario. When
`worldlet_history is None`, the bounded summary text must still be
deterministic and bounded — it simply encodes a "no worldlet recorded
yet" structural snapshot.

## 4. Persistence semantics

`worldlet_history` is **session-local only**. It is not in any
persistence schema column, not in any autosave payload, not in any
session-store reload path, and not in any export. Phase 3.24 must
preserve this property: the new feedback path must not introduce any
persistence, network, or filesystem coupling.

## 5. Existing invariants governing worldlet state

`I-WLD-01..I-WLD-12` cover the Minimal Worldlet substrate; the rows
that matter most for Phase 3.24's read-only summary are:

- `I-WLD-01` — bounded state / object record shape (state_id printable,
  step_index >= 0).
- `I-WLD-05` — bounded response record (closed reason set
  `{accepted, missing-target, rejected, target-unavailable}`).
- `I-WLD-11` — local-evidence scope on consequence summaries
  (`WORLDLET_LOCAL_EVIDENCE_SCOPE = "local-harness"`).
- `I-WLD-12` — `WorldletConsequenceSummary` bounded surface.

Phase 3.24 must not weaken any of these. The new helper only **reads**
counts and a latest-reason value; it never constructs a new
`WorldletResponse` or `WorldletState`.

## 6. Safe public surface for a bounded worldlet summary

The bounded worldlet summary helper Phase 3.24 ships in Step 2 may
read **only** the following primitive values from
`OperatorSession.worldlet_history`:

| field | shape | source |
|---|---|---|
| `latest_state.state_id` | printable str | `WorldletState.state_id` |
| `latest_state.step_index` | int >= 0 | `WorldletState.step_index` |
| `len(latest_state.objects)` | int | `WorldletState.objects` length |
| `len(history.attempts)` | int | `WorldletHistory.attempts` length |
| `len(history.responses)` | int | `WorldletHistory.responses` length |
| accepted count = `sum(1 for r in history.responses if r.accepted)` | int | derived |
| pushback count = `sum(1 for r in history.responses if (not r.accepted) and r.reason in WORLDLET_PUSHBACK_REASONS)` | int | derived |
| latest reason = `history.responses[-1].reason if history.responses else "absent"` | str (closed set) | `WorldletResponse.reason` or sentinel `"absent"` |

All of these are bounded primitives. None of them require importing the
worldlet record classes inside the helper module (the caller in
`OperatorSession._run_worldlet_feedback_step` passes the primitives).
This mirrors the existing decoupling between `processing_window.py` and
`coherence_monitor.py`: the helper accepts bounded primitives so the
audit forbids `from brain.development.worldlet import ...` inside
`processing_window.py`.

## 7. Closed reason set for the summary

The Phase 3.24 helper validates `latest_reason_value` against the
closed set

```text
{"accepted", "missing-target", "rejected", "target-unavailable", "absent"}
```

`"absent"` is the Phase 3.24 sentinel for "no responses yet" or
"worldlet_history is None". This matches the existing v0.27 Coherence
Monitor pattern: the closed status set
`{"pass", "warn", "fail", "not_applicable"}` is mirrored inline in
`processing_window.build_cohmon_summary_text` without importing the
monitor.

## 8. Forbidden surfaces

The Phase 3.24 helper / feedback path may NOT:

- import `brain.development.worldlet` from `processing_window.py`
  (mirrors the existing forbidden imports of `pattern_ledger` and
  `coherence_monitor`);
- import `brain.llm.*` from any new development module;
- call `brain.tick.tick` outside the approved `STEP_TICK` route (the
  feedback path goes through the same internal `STREAM_APPEND` seam
  as `pledger_summary` / `cohmon_summary`, which consumes zero real
  model calls);
- emit a raw worldlet payload (no token labels, no object accepted-set,
  no full attempt-id list — only bounded counts plus a closed-set
  `latest_reason` value);
- introduce any external-world claim, perception claim, embodiment
  claim, or "ToyI experiences X" reply text;
- mutate `OperatorSession.worldlet_history` (the feedback path is
  **read-only** on the worldlet substrate).

## 9. Why "transverse to the four imprinting kinds"

Per the Two-Layer Identity-Correlation Architecture corrigendum at the
end of the Phase 3.25 mission, **osmotic** imprinting is a
substrate-level mechanism, *transverse* to the four imprinting kinds,
not a fifth parallel kind. Phase 3.24 does **not** introduce an osmotic
mechanism; it introduces a *bounded structural feedback path that
re-enters the existing Pattern Ledger seam*. The worldlet-feedback
chunk is just another internal stream chunk: the Pattern Ledger /
Coherence Monitor / Growth Ledger / Dispatch Trace observe it under
the same rules as `pledger_summary` and `cohmon_summary`.

Osmotic imprinting (the Phase 3.25 campaign) is built on top of this
Phase 3.24 substrate plus the existing abstract-pattern infrastructure;
Phase 3.24's job is to extend the bounded feedback architecture by one
strictly substrate-level path.
