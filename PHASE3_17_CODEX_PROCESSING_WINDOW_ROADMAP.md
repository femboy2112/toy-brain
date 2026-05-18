# PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md

Canonical seed for the Phase 3.17 campaign. Read `CURRENT_MISSION.md`
and `CURRENT_CAMPAIGN.md` first; this file expands the design intent
behind both.

---

## 1. What Phase 3.17 is

Phase 3.17 is a research-and-engineering campaign with two bounded
threads:

```text
Thread A: Codex-cli runtime fix
Thread B: Bounded post-input processing window research
```

Both threads target an operationally **learning / growing "I"
approximation**. The campaign uses the phrases:

```text
"operational I"
"model-backed processing"
"internalization window"
"growth ledger"
"pattern recurrence"
"state integration"
"bounded reflective processing"
```

The campaign does **not** claim:

```text
consciousness
sentience
subjective experience
true selfhood
true agency
semantic understanding
truth access
desires / will / intent
self-modification in the strong sense
```

Allowed claim shape:

```text
"ToyI approximates some functional properties associated with a
learning/growing I: persistent state, bounded memory, pattern
recurrence, model-backed evaluations, growth events, cache
discipline, and inspectable post-input processing."
```

---

## 2. Why now

Phase 3.16 proved that ToyI's runtime can drive a real model-backed
tick end-to-end through the public dispatch path. It also recorded:

```text
- codex-cli 0.130.0 refuses cwd=/tmp without --skip-git-repo-check
- the kernel tick accepts at most one external PerceptEvent per tick
- OperatorSession.dispatch(STEP_TICK) refuses an empty event queue
- the Growth Ledger records accepted-event deltas only after a
  successful dispatch step
- L1 and L2 caches are bounded after Phases 3.14 / 3.15
- Stage C.1 dynamic flow orchestrator and the workflow helpers
  are merged and available to this campaign
```

So two follow-ups become tractable:

1. A **one-line runtime patch** to `CodexCLIClient.command` (and the
   factory) to unblock codex-cli.
2. A **research design** for an operational internalization window:
   what should happen *between* external inputs so that growth /
   pattern / coherence surfaces can accumulate inspectable evidence
   without inventing a self-model or claiming consciousness.

---

## 3. Thread A — codex-cli compatibility (Steps 2–4)

### 3.1 Issue

`CodexCLIClient` (in `brain/llm/client.py`) defaults to:

```python
command: tuple[str, ...] = ("codex", "exec")
cwd: str = "/tmp"
```

`cwd="/tmp"` is intentional: it prevents the nested CLI from
auto-discovering this repo's `CLAUDE.md` / hooks / config (see the
comment in `brain/llm/client.py`).

But `codex-cli >= 0.130.0` enforces a trusted-directory check and
rejects `cwd=/tmp` with:

```text
Reading additional input from stdin...
Not inside a trusted directory and --skip-git-repo-check was not
specified.
```

so the first model call exits non-zero before any prompt is sent.

### 3.2 Preferred fix

Add the documented `--skip-git-repo-check` flag to the default
command tuple:

```python
command: tuple[str, ...] = ("codex", "exec", "--skip-git-repo-check")
```

and propagate it through the factory in
`brain/ui/llm_runtime.py::_build_codex_cli_client`:

```python
CodexCLIClient(
    command=(resolved_executable, "exec", "--skip-git-repo-check"),
    timeout_seconds=config.timeout_seconds,
)
```

### 3.3 Rejected alternative

Setting `cwd` to the repo root unblocks the trusted-dir check but
re-opens the previously-rejected discovery surface (parent
`CLAUDE.md`, hooks, repo-local config). The neutral `/tmp` cwd plus
the explicit `--skip-git-repo-check` flag is strictly the smaller
behavior change.

### 3.4 Files and expected catalog impact

```text
runtime files:
    brain/llm/client.py            # CodexCLIClient.command default
    brain/ui/llm_runtime.py        # _build_codex_cli_client factory

fixture files:
    brain/ui/fixtures/             # at least one fixture asserts the
                                   # exact command tuple; either update
                                   # the existing codex-cli factory
                                   # fixture or add a tiny new one
                                   # covering "--skip-git-repo-check"

catalog files:
    INVARIANT_CATALOG.md           # body of I-LLMTOG-16 / I-LLMTOG-17
                                   # may need a one-line refresh; the
                                   # COUNTS row remains
                                   # 281 / 88 / 14 / 15 / 16
    tools/catalog.py               # expected unchanged
```

If the fixture refresh requires bumping any structural row body,
the catalog version banner stays at v0.25 and the count line stays
at 281/88/14/15/16. If a real version bump is unavoidable, Phase
3.17 stops at Step 2 and asks the operator for explicit approval.

### 3.5 Validation

Standard preflight after Step 3 must pass:

```bash
python3 -m tools.claude_helpers.gate_runner --json
```

Step 4 runs a real codex-cli model call **only if** Step 3's gates
are green. Call budget for Step 4 ≤ 10. If codex-cli still fails
post-patch (e.g., auth missing, network blocked), Step 4 commits a
partial report and escalates to Step 9 triage.

---

## 4. Thread B — bounded processing window research (Steps 5–8)

### 4.1 The thesis (initial; subject to Step 9 refinement)

> An external input event should be followed by a **bounded
> internalization period** of N internal ticks during which the
> kernel does no new external perception but performs reflective
> work on the already-accepted state. The initial experimental
> parameter is **N = 50** — small enough to bound budget, large
> enough to make Pattern Ledger / Growth Ledger / Coherence
> Monitor evidence visible.

### 4.2 Tick taxonomy

Phase 3.17 distinguishes four classes of ticks (research-only;
no kernel change in v1):

```text
external input tick:
  one PerceptEvent from operator / stream / future-REPL/worldlet
  source. This is what brain.tick.tick currently supports (at
  most one PerceptEvent per tick).

internal processing tick:
  a tick whose triggering event was synthesized inside the session
  from already-accepted state (Pattern Ledger entries, Coherence
  Monitor warnings, prior ConsistencyEval values). Provenance is
  always tagged "internal_processing_window".

reflective feedback tick:
  an internal processing tick whose input is derived specifically
  from a coherence diagnostic (e.g., a WARN that says some MSI
  member's eval is stale relative to its profile value).

future REPL/worldlet interaction tick:
  a tick whose input comes from a controlled sandboxed REPL or
  worldlet response. Out of scope for Phase 3.17.
```

### 4.3 Why the current route cannot do this without research

Two existing facts make a naive "just loop /step" approach unsafe:

1. `OperatorSession.dispatch(STEP_TICK)` refuses an empty
   `event_queue`. There is no kernel notion of "tick with no
   external event."
2. `brain.tick.tick` rejects `len(events) > 1` (I-RT-11) and rejects
   re-promotion of a content already in `profile.domain` (I-RT-12).
   So an internal-processing tick must construct a *different*
   PerceptEvent each time, with a unique `content_id` and bounded
   text.

A v1 design must therefore generate well-formed internal
PerceptEvent candidates from existing inspectable state. The simplest
sources are:

```text
- PatternLedgerEntry → synthetic "pattern recurrence" event
- CoherenceCheck WARN/FAIL → synthetic "coherence anomaly" event
- prior ConsistencyEval → synthetic "consolidation" event
```

Each requires a deterministic content_id namespace
(e.g., `int:pledger:<pattern_id>:<tick>`), bounded printable text,
and provenance tagged `internal_processing_window`. None of this
ships in v1 — Step 7 plans it; Step 8 only exercises the negative
control (window = 0) plus, if feasible, a small mock-mode window
that the existing surfaces already accept.

### 4.4 Candidate architectures

```text
A. Session-level post-input tick loop using synthesized internal
   PerceptEvent candidates.
   PROS: zero kernel change; uses public dispatch path.
   CONS: needs a deterministic id-generator and a strict bounded
         text discipline so I-RT-01 / I-RT-09 / I-RT-12 cannot
         trip.

B. New internal event type / internal percept source.
   PROS: makes "internal" first-class.
   CONS: kernel surface change; out of scope for Phase 3.17.

C. Reflective REPL feedback generating queued internal events.
   PROS: leverages Phase 3.4 REPL substrate.
   CONS: REPL is an inspection surface in v1; needs design
         work.

D. Worldlet / working-memory feedback later.
   PROS: structurally clean; matches Phase 3.3.
   CONS: deferred; not Phase 3.17.

E. No-op empty tick window as a negative control.
   PROS: trivially safe; produces a clean baseline.
   CONS: by construction produces no growth / pattern delta;
         only useful as a control.

F. Delayed consolidation queue (process internal events on a
   pacing schedule rather than back-to-back).
   PROS: simpler accounting; safer call budget.
   CONS: requires a session-level scheduler; deferred design.
```

Phase 3.17 commits to **A** as the v1 candidate, **E** as the
negative control, and treats **B–D + F** as named future work.

### 4.5 Human analogy (carefully)

We use the well-known stack:

```text
input perception → working memory → consolidation → rehearsal →
self-monitoring → action selection
```

only as an **architectural analogy**. None of these phrases imply
ToyI has experience, awareness, or intent. The analogy guides
where to install bounded structural artifacts (Pattern Ledger,
Growth Ledger, Coherence Monitor); it does not justify any
claim about interior state.

### 4.6 Hypotheses to probe (Step 6)

```text
H1: At window = 0, the inspectable growth/pattern/coherence
    surfaces show only the direct external-input deltas.
H2: At window > 0 with a deterministic generator, repeated
    structural patterns drive Pattern Ledger recurrence counts up
    without consuming additional real-model calls (L2 absorbs
    repeats).
H3: At window = 50 under mock mode, the total call count stays
    well below the campaign budget (20) because mock has no real
    LLM calls.
H4: At window = 50 under a model-backed mode, the call count
    saturates at the L2 cap of distinct (msi_context, new_text)
    canonicalization keys.
H5: Coherence Monitor reports remain PASS or WARN; no NEW
    invariant failure (FAIL) is introduced.
H6: No aggregate "I-ness" score appears anywhere; coherence
    counts_by_status remains a labeled tuple.
```

### 4.7 Minimal v1

Phase 3.17 does **not** implement a SelfModel, does **not** ship a
runtime processing-window loop, and does **not** change the tick
kernel. Step 8 only exercises a negative control plus any test that
can be built using existing public surfaces without a runtime
patch. Real runtime work waits for a future operator-approved
campaign behind an explicit Step 7 review gate.

---

## 5. Success criteria

```text
Thread A success:
  - "--skip-git-repo-check" appears in CodexCLIClient.command and
    in _build_codex_cli_client's tuple.
  - At least one fixture pins the new tuple shape.
  - gate_runner --json is fully green after the patch.
  - Step 4 reports a complete codex-cli model-backed tick OR a
    precise post-patch blocker.

Thread B success:
  - PHASE3_17_PROCESSING_WINDOW_SYNTHESIS.md exists and addresses
    every item in Section 4 above.
  - PHASE3_17_PROCESSING_WINDOW_PROBE_PLAN.md exists with the
    {0,1,5,10,50} matrix, the mode set, and the per-output
    measurements.
  - PHASE3_17_PROCESSING_WINDOW_IMPLEMENTATION_PLAN.md exists and
    is explicitly review-gated.
  - PHASE3_17_PROCESSING_WINDOW_INITIAL_TEST.md exists and at
    minimum demonstrates the window=0 negative control using only
    existing public surfaces.

Campaign closes with one of:
  PASS
  PASS WITH DEFERRED IMPLEMENTATION
  PARTIAL
  BLOCKED
  FAIL
```

---

## 6. Non-claims and safety boundaries

```text
- No consciousness / sentience / subjective claim.
- No truth-adjudication claim from raw text.
- No agency / intent / will / desire / self-modification claim.
- No aggregate I-ness / growth / consciousness scalar.
- No DB schema change.
- No SCHEMA_VERSION bump.
- No autosave behavior change.
- No L1 / L2 cache semantic change beyond the codex-cli command
  tuple fix.
- No parser / prompt change.
- No tick kernel change.
- No SelfModel implementation.
- 50 internal ticks is a research parameter, not a runtime
  constant.
- Real model call budget is hard-capped at 20 for the campaign.
- All bridge usage is disclosed per-step.
```

---

## 7. Open questions for a future campaign (out of scope here)

```text
Q1. What is the right deterministic generator for internal
    PerceptEvent candidates so that I-RT-01 / I-RT-09 / I-RT-12
    are never triggered?
Q2. Should the post-input window be a single-shot fixed-N loop or
    a pacing scheduler (architecture F)?
Q3. How should the processing window interact with the operator's
    typed /step? Today /step is the only mutation route through
    the kernel; an internal window must not silently call /step.
Q4. Does the Phase 3.13 Growth Ledger emit useful "consolidation"
    events under an internal window, or do we need a new
    GrowthEventType (BREAKS Phase 3.13's locked enum — out of
    scope without a new catalog patch)?
Q5. Does L2 (eval_v1) correctly absorb internal-event repeats, or
    does the synthesized new_text break canonicalization?
Q6. What does a worldlet-driven internal tick look like
    (architecture D)?
```

These are intentionally deferred; the Step 9 findings doc records
which ones Phase 3.17 has new evidence on and which remain open
for the next campaign.
