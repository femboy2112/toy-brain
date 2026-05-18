# PHASE3_17_PROCESSING_WINDOW_IMPLEMENTATION_PLAN.md

## Purpose

Step 7 of Phase 3.17: a **design-only** implementation plan for a
session-level bounded processing-window prototype (architecture
**A** from the Step 5 synthesis). The plan specifies exactly what
the prototype would touch, what it would not touch, what each
catalog row would say, what each new fixture would assert, and —
critically — the explicit review gate Phase 3.17 must clear before
any runtime code under this plan lands.

**Phase 3.17 does NOT implement this plan.** No code from this
document is committed in Phase 3.17. Step 8 runs only the
negative-control probe described in Step 6 using existing public
surfaces. This file is the seed for a future operator-approved
campaign.

---

## 1. Review gate (mandatory before any code lands)

```text
GATE-PW-1. Operator (femboy2112) acknowledges this plan in writing
           in a follow-up campaign kickoff (a new PHASE3_18_*
           or similar campaign document).

GATE-PW-2. Operator confirms whether the runtime change is
           authorized as a session-level dispatcher extension only
           (architecture A; preferred) OR a kernel surface change
           (architecture B; out of scope here).

GATE-PW-3. Operator approves the proposed catalog patch shape
           in advance, OR explicitly rules that no new catalog
           rows are required (i.e., the prototype rides existing
           rows entirely and the new fixture is structural-only).

GATE-PW-4. Operator approves the proposed test surface:
           - which new fixtures are added,
           - which existing fixtures are extended,
           - what status (REQUIRED / STRUCTURAL / NOT-EXERCISED /
             OBSERVED / DEFERRED) each new row carries.

GATE-PW-5. Operator approves the proposed real-model-call budget
           for the implementation campaign separately from the
           Phase 3.17 budget. The current Phase 3.17 budget remains
           20 total; the implementation campaign needs its own
           cap.
```

If any of GATE-PW-1..5 are not met, implementation does NOT
proceed. The Step 8 negative-control probe is the only Phase 3.17
runtime touch.

---

## 2. Architecture (recap; see Step 5 Section 5.A)

```text
architecture A: session-level post-input tick loop

After OperatorSession._dispatch_step returns True (the external
tick succeeded), and BEFORE the post-dispatch autosave hook fires,
the session may invoke a new method, e.g.:

    self._run_processing_window(
        client=<the same client used for STEP_TICK>,
        N=self.processing_window_size,
    )

This method is the new code surface. It:
  - builds N internal PerceptEvent candidates from S1 / S2 / S3
    sources (synthesis Section 4) in a deterministic round-robin
    order, with strict bounded printable text,
  - enqueues each via the public _dispatch_queue path,
  - immediately calls _dispatch_step on each, with the supplied
    client,
  - aborts on any error class (parse failure, invariant violation,
    cache cap, call-budget cap),
  - emits NO new growth_ledger event types (it reuses the
    existing TICK_SUCCEEDED / PROFILE_DOMAIN_ADDED /
    MSI_MEMBER_ADDED emissions in _dispatch_step; an external
    filter on provenance can distinguish internal-source events
    later).
```

The window runs synchronously within the operator's `/step` call.
The session remains a single-threaded object with no asyncio,
no threading, no `signal` handler, no `atexit`, no curses callback.

---

## 3. Files this prototype would touch

### 3.1 Runtime files

```text
brain/ui/session.py
  - new method OperatorSession._run_processing_window(client, N)
  - new optional field processing_window_size: int = 0
  - new optional field processing_window_call_budget: int = 0
  - hook in OperatorSession.dispatch after a successful
    _dispatch_step (and before maybe_autosave_after_dispatch)
  - extension of _ALLOWED_SESSION_ATTRS to include the two new
    optional fields (LOCK: still no callable / handle / client
    field; both new fields are bounded ints)

brain/ui/commands.py
  - OPTIONAL: a new typed command kind PROCESSING_WINDOW_SET
    (taking an int N) plus its payload, so the operator can
    toggle the window per session without restarting the UI.
    DEFERRED unless GATE-PW-4 explicitly approves a new verb.

brain/ui/command_line.py
  - OPTIONAL: a new "/processing-window <N>" verb mapped to
    PROCESSING_WINDOW_SET. DEFERRED with the same gate.
```

### 3.2 Internal-event generator helper (new module)

```text
brain/development/processing_window.py
  - InternalEventSource (closed enum: PLEDGER, COHMON, CONSOL)
  - generate_internal_event(session, source, tick) -> Optional[
        QueuePerceptPayload
    ]
  - deterministic id namespace
  - bounded printable text discipline
  - forbidden-non-claim-term audit on every produced text (reuses
    brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS)
  - NO IMPORT of brain.ui.session (one-way dependency: session
    -> processing_window, never the reverse)
  - NO IMPORT of brain.tick / brain.tlica (one-way dependency:
    processing_window -> pattern_ledger, coherence_monitor only)
```

### 3.3 Fixtures (new)

```text
brain/ui/fixtures/processing_window_static_audit.py
  - asserts the import set of brain/development/processing_window.py
  - asserts no callable / handle / client / pathlib.Path /
    sqlite3.Connection / curses references appear on any new
    record
  - asserts the forbidden-non-claim-term audit covers every
    bounded printable string the module produces (the test
    constructs a probe session and exhaustively walks the
    generator's outputs)

brain/ui/fixtures/processing_window_integration.py
  - constructs a deterministic mock-mode session, drives one
    external tick, runs the window at small N (e.g. N=3), and
    asserts:
      - tick_counter advances by exactly 1 + N
      - growth_ledger event count advances by exactly the
        expected delta (1 per successful internal tick under
        the v1 emission set)
      - the new code path emits NO new growth_event_type values
      - the new code path produces NO new aggregate scalar in
        any session field
      - kernel invariants remain green
```

### 3.4 Catalog (proposed but NOT yet authorized)

```text
PROPOSED rows (status set by GATE-PW-4):

I-PWND-01 (STRUCTURAL?)  InternalEventSource is a closed enum.
I-PWND-02 (STRUCTURAL?)  generate_internal_event refuses
                         COGITO_ID / non-printable text /
                         oversize text / collision with
                         state.profile.domain.
I-PWND-03 (REQUIRED?)    OperatorSession._run_processing_window
                         emits NO new growth_event_type values
                         beyond TICK_SUCCEEDED /
                         PROFILE_DOMAIN_ADDED / MSI_MEMBER_ADDED.
I-PWND-04 (REQUIRED?)    The window honors session.processing_window_size
                         as its hard upper bound (and 0 = no
                         window).
I-PWND-05 (REQUIRED?)    The window aborts on any
                         _dispatch_step False return, parse
                         failure, or invariant FAIL, leaving
                         session.error_message bounded printable.
I-PWND-06 (REQUIRED?)    The window honors a per-window
                         processing_window_call_budget cap on
                         real model attempts.
I-PWND-07 (STRUCTURAL?)  brain/development/processing_window.py
                         import set is bounded to the documented
                         seam (forbidden-non-claim-term audit
                         delegates to coherence_monitor's
                         existing tuple).
I-PWND-08 (REQUIRED?)    No aggregate scalar field is added by
                         the window (no consciousness_score,
                         iness_score, growth_score, awareness_score).
I-PWND-09 (NOT-EXERCISED) End-to-end dry run under codex-cli at
                         N=50. Documented but cannot fail the
                         runner.
I-PWND-10 (DEFERRED)     "/processing-window <N>" operator verb.
                         Body asserts the verb is bound; STATUS
                         DEFERRED until a separate review gate.
```

The exact statuses (`STRUCTURAL` vs `REQUIRED` vs `NOT-EXERCISED`
vs `DEFERRED`) are subject to GATE-PW-4. The catalog count delta
under the proposed shape:

```text
REQUIRED       +5  (I-PWND-03..06, I-PWND-08)
STRUCTURAL     +3  (I-PWND-01, I-PWND-02, I-PWND-07)
NOT-EXERCISED  +1  (I-PWND-09)
DEFERRED       +1  (I-PWND-10)
OBSERVED       +0
catalog version v0.25 -> v0.26
```

Total runner row count: +9 (REQUIRED + STRUCTURAL).

Alternative (recommended for first cut, behind GATE-PW-3): drop
I-PWND-09 / I-PWND-10 and let the prototype ride entirely on the
existing rows without a catalog version bump. Under that
alternative the count delta is:

```text
REQUIRED       +0   (all new asserts ride existing rows / fixtures)
STRUCTURAL     +1   (the static-audit fixture as a new audit row)
NOT-EXERCISED  +0
DEFERRED       +0
OBSERVED       +0
catalog version v0.25 -> v0.25 (no bump)
```

The minimal-shape alternative is much smaller and safer.
GATE-PW-3 picks one.

---

## 4. Files this prototype would NOT touch

```text
brain/tick.py
brain/llm/client.py
brain/llm/parse.py
brain/llm/prompts.py
brain/llm/ptcns_backed.py
brain/development/growth_ledger.py
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/ui/persistence.py
brain/ui/persistence_ops.py
brain/ui/persistence_observe.py
brain/ui/autosave.py
brain/ui/render.py
brain/ui/snapshot.py
brain/ui/__main__.py
brain/io_types.py
brain/tlica/*
brain/toce_core.py
brain/validation.py
scenarios/**
traces/**
lean_reference/**
tools/catalog.py (unless the catalog count actually changes)
INVARIANT_CATALOG.md (unless GATE-PW-3 approves new rows)
```

If during implementation a touch to any of the above seems
required, the implementation campaign STOPS and re-opens the
review gate.

---

## 5. Behaviors the prototype MUST preserve

```text
B1. brain.tick.tick semantics: unchanged. The window does not
    re-enter the kernel except through the same
    `_dispatch_step -> tick()` call path used today.

B2. Growth Ledger v1 enum: unchanged. The window does NOT
    introduce new GrowthEventType members. Any "internal source"
    distinction is encoded in the existing `references` and
    `provenance` fields of GrowthEvent, which are bounded printable
    strings.

B3. Pattern Ledger v1: unchanged. The window does NOT call
    PatternLedger.observe directly; it relies on the existing
    `_dispatch_stream_append` -> Pattern Ledger trigger (the
    window does not append to the stream history at all in v1).

B4. Coherence Monitor v1: unchanged. The window does NOT call
    `build_coherence_snapshot` or any other monitor builder; the
    monitor remains operator-invoked.

B5. L1 / L2 cache semantics: unchanged. The window's internal
    ticks go through the same CachedClient(...) layer, so L1 and
    L2 admit / cap as documented in Phase 3.14 / 3.15.

B6. I-UI-10 (no unsafe resources): unchanged. The two new
    optional session fields are bounded ints.

B7. I-UI-13 (bounded printable status text): unchanged. The
    window writes status updates through `set_status`, which
    enforces bounds.

B8. I-PCE-05 (agency.py clean of pce imports): unchanged. The
    new processing_window module is in `brain.development`, not
    `brain.tlica.agency`.

B9. I-AUTOSAVE-08..10 (post-dispatch autosave trigger): unchanged.
    The new code path fires BEFORE the autosave hook; the
    autosave still triggers iff the original
    `_dispatch_step` returned True for the EXTERNAL tick. Internal
    ticks do NOT trigger their own autosave events (this is
    explicit; otherwise N=50 would produce 50 autosave attempts).

B10. Non-claim audit: unchanged. The processing_window module
     reuses brain.development.coherence_monitor's existing
     _FORBIDDEN_NON_CLAIM_TERMS tuple via import. The static
     audit fixture asserts the tuple is unchanged and the new
     module's source / generated strings contain none of the
     terms.
```

If any of B1–B10 cannot be preserved, the prototype is rejected
at the review gate.

---

## 6. Behaviors the prototype WOULD introduce

```text
N1. Session-level synchronous internal-tick loop, bounded by N.

N2. Two new optional OperatorSession fields:
    - processing_window_size: int = 0 (default OFF)
    - processing_window_call_budget: int = 0
    Both default to zero. Operator (or fixture) must explicitly
    set them. No env var bumps them out of zero (parity with
    LLMTOG explicit-opt-in policy).

N3. A new deterministic id namespace prefix
    "int:" for internal-event content_ids. This prefix is NOT a
    new constant in any shipped enum; it is just a string
    convention enforced by the generator and asserted by the
    static-audit fixture.

N4. A new generator module brain.development.processing_window
    whose import set is bounded:
        dataclasses, enum, typing,
        brain.development.coherence_monitor (for forbidden terms),
        brain.development.pattern_ledger,
        brain.io_types (for PerceptEvent reuse via builder),
        brain.tlica.profile (for COGITO_ID rejection),
        brain.ui.commands (for QueuePerceptPayload type)
    Nothing else.

N5. A new fixture file
    brain/ui/fixtures/processing_window_static_audit.py covering
    the import-set audit and the forbidden-term audit.

N6. A new fixture file
    brain/ui/fixtures/processing_window_integration.py covering
    one mock-mode end-to-end window at small N.
```

---

## 7. Risks

```text
R1. The kernel invariant I-RT-11 (at most one event per tick) is
    fine: the window dispatches sequential ticks, not multi-event
    ticks.

R2. I-RT-12 (one-shot promotion per content_id) demands unique
    internal content_ids per tick. The "int:<source>:<key>:<tick>"
    namespace handles this; the static-audit fixture asserts
    uniqueness.

R3. The L2 canonical key includes new_text but excludes
    content_id. Two internal events with identical text under
    the SAME msi_context will hit L2 (good for budget). But if
    the generator produces too much variation in synthesized
    text, L2 absorbs poorly and the call count creeps up.
    Mitigation: the generator emits a bounded template-driven
    text for each source; the only varying piece is the source
    payload identifier.

R4. Coherence Monitor's `compute_overall_status` rules say
    `FAIL > WARN > PASS > NOT_APPLICABLE`. If the window
    accidentally produces a new FAIL (e.g., an invariant fault),
    the campaign aborts that probe (F4) but the FAIL is now
    persistent in session.error_message. Mitigation: the
    integration fixture must clean up its session before the
    next probe; the session is local to the runner and never
    shared across probes.

R5. Autosave interaction: the window's N=50 internal ticks
    could each fire autosave if the trigger logic is loose. The
    plan explicitly says the autosave hook does NOT fire after
    internal ticks (B9). Mitigation: the static-audit fixture
    asserts the trigger set in
    `OperatorSession._maybe_autosave_after_dispatch` continues
    to fire only after the EXTERNAL dispatch returned True; the
    new method calls `_dispatch_step` directly and skips
    `_maybe_autosave_after_dispatch` for internal ticks.

R6. Bridge interaction: under codex-cli at N=50 the call budget
    will exhaust quickly. The window's per-window
    call-budget cap is a separate field; it MUST be honored
    BEFORE the campaign budget.

R7. Real model parse ambiguity: codex / claude may emit verbose
    headers under longer prompts that the strict parser
    rejects. Mitigation: keep the synthesized internal text
    short and template-driven; parse failures abort the window
    via F3.
```

---

## 8. Acceptance plan (under the future implementation campaign)

```text
1. GATE-PW-1..5 met.
2. Land the new module + new fixture(s) + the session.py extension.
3. Run gate_runner --json; all five gates PASS.
4. Run the new processing_window_integration fixture under
   mock mode at small N (e.g. N=3, N=10). Assert the documented
   deltas.
5. Run a single real-mode probe under either claude-cli or
   codex-cli at small N (e.g. N=3) to confirm L2 absorbs
   identical internal-event text.
6. Update the campaign audit doc with the result.
7. Open a PR. Do not merge.
```

Each of those steps maps to a Step in the future implementation
campaign. None of them happen in Phase 3.17.

---

## 9. What Phase 3.17 specifically does NOT promise

```text
- Phase 3.17 does NOT promise the runtime processing window will
  be implemented. The prototype proposed here may be rejected at
  the review gate.
- Phase 3.17 does NOT lock the catalog count delta. The minimal
  alternative (no new rows; one structural fixture) is
  acceptable.
- Phase 3.17 does NOT lock the operator verb / typed-command
  surface. The window may be configured purely via
  `OperatorSession.processing_window_size` set by the runner
  / fixture if no review approves a new verb.
- Phase 3.17 does NOT promise N=50 stays the default. The future
  campaign may choose a different default based on the actual
  probe results (Step 8 + an implementation-campaign probe
  expansion).
```

---

## 10. Constraint sanity

```text
brain/tick.py                       : not touched by this plan
brain/llm/parse.py                  : not touched
brain/llm/prompts.py                : not touched
brain/llm/ptcns_backed.py           : not touched
brain/development/growth_ledger.py  : not touched
brain/development/pattern_ledger.py : not touched
brain/development/coherence_monitor.py : not touched (reused only)
brain/ui/__main__.py                : not touched
INVARIANT_CATALOG.md                : not touched in Phase 3.17;
                                      a future campaign may patch
                                      it under GATE-PW-3
tools/catalog.py                    : not touched in Phase 3.17
brain/.llm_cache                    : remains gitignored
raw prompts / responses / secrets   : none committed
catalog v0.25 / 281/88/14/15/16     : unchanged in Phase 3.17
```

---

## 11. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: this is a design plan derivable from the synthesis,
  the probe plan, and the existing module sources; no external
  review is required to produce the plan.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: a single self-contained doc.
```

---

## 12. Real model call accounting

```text
mode tested:                       n/a (doc only)
calls used in this step:           0
cumulative campaign calls:         1 / 20
```

---

## 13. Next artifact

Step 8:
`docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_INITIAL_TEST.md`
— the actual probe run for the negative-control row (and any
safely-buildable mock cells) using only the existing public
surfaces. No runtime change.
