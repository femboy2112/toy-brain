# PHASE3_17_FINDINGS.md

## Purpose

Step 9 of Phase 3.17: classify each campaign deliverable, name
the next implementation campaign, and record blockers and
deferred work.

---

## 1. Classification

### 1.1 Codex fix

```text
codex fix success / fail        : SUCCESS

Evidence:
  - Step 3 patched CodexCLIClient.command default + the factory
    in brain/ui/llm_runtime.py to ("codex", "exec",
    "--skip-git-repo-check").
  - Fixture llm_runtime_codex_cli_factory.py extended with four
    new assertions; all five canonical gates remained PASS after
    the patch (commit 2239b7f).
  - Step 4 real-model smoke (commit 0b877f7) produced a clean
    end-to-end tick under codex-cli 0.130.0: NEUTRAL parsed,
    profile.domain += "phase317-codex-1", Growth Ledger
    TICK_SUCCEEDED + PROFILE_DOMAIN_ADDED, L1 miss=1, L2 store=1,
    1 real call (12.5 s).
  - Step 8 codex-cli baseline (S8.4) re-confirmed the route on a
    second prompt: 1 real call (7.7 s), L1 miss=1, L2 store=1,
    no parse failure.

Conclusion: the Phase 3.16 trusted-dir blocker is fully
resolved. codex-cli is now a usable real-model-backed mode for
the Phase 3.16 operational route, with no other runtime change,
no L1/L2 semantic change, no parser/prompt change, no kernel
change, no catalog count change.
```

### 1.2 Codex model route

```text
codex model route works / partial / fail : WORKS

Evidence:
  - Two independent codex-cli ticks (Step 4 + Step 8 S8.4) both
    parsed cleanly on the first attempt.
  - The Phase 3.16 Step 5 follow-up F3 risk (codex stdout
    headers polluting strict parser) did NOT manifest under the
    short prompts used; the response was a clean single-token
    "NEUTRAL\n" in both cases.
  - L1 and L2 cache directories grew predictably (one entry per
    miss); neither hit its 1024-entry cap.
  - Wall-clock per call: 12.5 s and 7.7 s — within the 90-s
    timeout configured by LlmRuntimeConfig.

Caveat:
  - Only short prompts were exercised. Longer or more
    contentious prompts may still hit parser ambiguity. This is
    a Phase 3.16 F3 follow-up; Phase 3.17 does NOT claim to have
    closed it.
```

### 1.3 Processing window feasibility now?

```text
processing window feasible NOW?          : NO (by design)

Phase 3.17 explicitly does NOT ship a runtime processing-window
loop. Step 8 ran the negative-control row only, and the
counterfactual proved that a well-shaped int:* event sitting in
the queue produces no Growth Ledger / Pattern Ledger / Coherence
delta beyond queue_size++.

A runtime processing window is feasible to ENGINEER from the
design in Step 7 (architecture A; session-level synchronous loop
behind a new optional OperatorSession field). Implementing it
requires meeting GATE-PW-1..5.
```

### 1.4 Processing window requires runtime design?

```text
processing window requires runtime design : YES

Specifically, ANY non-trivial processing-window probe (N >= 1)
needs:
  - A deterministic generator for internal PerceptEvent
    candidates (S1 / S2 / S3 from the synthesis).
  - A new optional OperatorSession field (processing_window_size).
  - A new method OperatorSession._run_processing_window that
    sits in the dispatch path AFTER a successful external
    _dispatch_step and BEFORE the autosave hook.
  - A new module brain/development/processing_window.py whose
    import set is bounded and whose generated text is audited
    against the existing _FORBIDDEN_NON_CLAIM_TERMS tuple.
  - At minimum one new fixture; possibly a new catalog row
    family (I-PWND-01..10 proposed in Step 7, with a minimal-
    shape alternative).

None of these is implemented in Phase 3.17.
```

### 1.5 What exact next implementation campaign is needed?

```text
recommended next campaign:

  Phase 3.18 — Bounded Internal Processing Window Prototype

  Scope (from Step 7 plan):
    - Implement architecture A behind GATE-PW-1..5.
    - Land the new module + new fixture(s) + the session.py
      extension.
    - Run the Step 6 probe matrix on a reduced cell set under
      mock + claude-cli + codex-cli.
    - Either ship the prototype as a structurally-bounded
      experiment (no new catalog rows; minimal-shape alternative)
      OR commit to the proposed I-PWND-* row family at v0.26.
      The choice is GATE-PW-3.

  Out of scope for Phase 3.18:
    - SelfModel.
    - Architecture B (kernel surface change).
    - Architecture C (REPL feedback).
    - Architecture D (worldlet feedback).
    - Architecture F (delayed consolidation queue).
    - Parser ambiguity hardening (Phase 3.16 F3).
    - OperatorSession.dispatch tracer wiring (Phase 3.16 F2).
    - L1 / L2 cache cap behavior probes.
```

### 1.6 Blockers

```text
B1. Stage C.1 unused in this campaign.
    Not a blocker; the campaign was self-contained at a scale
    where direct writes were strictly cheaper.

B2. anthropic-api smoke remains BLOCKED BY ENV.
    Not a blocker for Phase 3.17's stated target. Inherited
    from Phase 3.16 F4.

B3. Tracer not wired through OperatorSession.dispatch (Phase
    3.16 F2).
    Not a blocker for Phase 3.17; the Step 6 plan explicitly
    notes M06 (L2 hit/miss/store/skip) as "trace-only" today
    and reports via CachedClient counters + on-disk counts
    instead.

B4. Parser ambiguity risk under verbose model output (Phase
    3.16 F3).
    Not a blocker; the two real codex-cli runs both produced
    clean single-token output. The risk is documented and the
    mitigation (short template-driven internal text) is
    specified in the Step 7 plan.

B5. No FAIL from kernel invariants observed at any point.
```

### 1.7 Deferred work (carries forward to Phase 3.18 or later)

```text
D1. Architecture A implementation (full Step 7 plan).
D2. The 75-cell probe matrix from Step 6.
D3. Architecture B (kernel surface change).
D4. Architecture C (REPL feedback).
D5. Architecture D (worldlet feedback).
D6. Architecture F (delayed consolidation queue).
D7. Phase 3.16 F2 tracer wiring.
D8. Phase 3.16 F3 parser ambiguity hardening.
D9. Phase 3.16 F4 anthropic-api smoke (env-dependent).
D10. SelfModel — remains OUT OF SCOPE indefinitely until a
     separate operator-approved campaign authorizes it.
D11. INVARIANT_CATALOG.md body refresh for I-LLMTOG-16..18
     (mentions of ("codex", "exec") could be refreshed to
     reflect the new command tuple; not required, but tidy).
D12. /pattern-ledger / /coherence-summary / /growth-ledger
     UIs — DEFERRED at catalog level since Phase 3.12c / 3.13.
```

---

## 2. Decision

```text
Phase 3.17 Step 5 decision rule (from CURRENT_CAMPAIGN.md
macro sequence): Steps 5-8 proceed regardless of Step 4
outcome. Step 9 (this doc) records the classification.

DECISION: proceed to Step 10 (final audit) and Step 11 (PR
preparation). The campaign verdict, given:

  - codex fix SUCCESS,
  - codex model route WORKS,
  - processing-window research COMPLETE (synthesis + probe plan
    + implementation plan + initial test all delivered),
  - all five canonical gates green,
  - no kernel / cache / parser / prompt / catalog count change,
  - 2 / 20 real model calls consumed,

is "PASS WITH DEFERRED IMPLEMENTATION" (synthesis, probe plan,
implementation plan, and initial test exist; the runtime
processing-window loop is deferred to Phase 3.18).
```

---

## 3. Hypothesis status across the campaign

```text
H1  PASS at N=0 (Step 8).
H2  UNTESTABLE at N=0; deferred (needs Phase 3.18).
H3  UNTESTABLE at N=0; partial evidence at N=0 (mock cost = 0).
H4  UNTESTABLE at N=0; Phase 3.16 Step 5 walk B provides
    independent evidence under claude-cli.
H5  PASS for every cell in Step 8 (no new FAIL observed).
H6  PASS — no aggregate scalar appears anywhere in Phase 3.17.
H7  UNTESTABLE at N=0; deferred (needs Phase 3.18 with N=5/50).
```

H1, H5, H6 are confirmed. H2, H3, H4, H7 remain open and
become Phase 3.18 success criteria.

---

## 4. Real model call accounting

```text
Step 1 mission sync                 : 0
Step 2 patch plan                   : 0
Step 3 apply codex fix              : 0
Step 4 codex-cli real model smoke   : 1   (12.5 s)
Step 5 synthesis                    : 0
Step 6 probe plan                   : 0
Step 7 implementation plan          : 0
Step 8 initial test (S8.4 only)     : 1   (7.7 s)
Step 9 findings (this doc)          : 0
                                      ----
Cumulative campaign calls           : 2 / 20
Budget remaining                    : 18
```

---

## 5. Constraint sanity

```text
brain/tick.py                       : not modified
brain/llm/parse.py                  : not modified
brain/llm/prompts.py                : not modified
brain/llm/ptcns_backed.py           : not modified
brain/llm/client.py                 : modified by Step 3 (one
                                      element added to
                                      CodexCLIClient.command tuple)
brain/ui/llm_runtime.py             : modified by Step 3 (factory
                                      tuple updated to match)
brain/ui/session.py                 : not modified
brain/ui/__main__.py                : not modified
brain/development/*                 : not modified
INVARIANT_CATALOG.md                : not modified
tools/catalog.py                    : not modified
README.md                           : not modified
brain/.llm_cache contents           : not committed (gitignored)
raw prompts / responses             : not committed; only hashes,
                                      char counts, parsed enum
secrets                             : not present, not printed
gate_runner                         : ran green at every commit
catalog v0.25                       : unchanged
counts                              : 281 / 88 / 14 / 15 / 16
                                      unchanged
```

---

## 6. Non-claims confirmation

```text
- no consciousness claim
- no sentience claim
- no subjective-experience claim
- no semantic-understanding claim
- no truth-adjudication claim
- no agency / intent / will / desire / self-modification claim
- no aggregate consciousness / sentience / awareness / I-ness /
  growth score
- no SelfModel implementation
- no Growth Ledger semantic change
- no Pattern Ledger semantic change
- no Coherence Monitor semantic change
- no L2 (eval_v1) semantic change
- no L1 cache semantic change (the codex command tuple is a
  compatibility flag, not a cache-policy change)
- no tick semantic change (brain/tick.py untouched)
- no parser change
- no prompt change
- no DB schema change
- no SCHEMA_VERSION bump
- no persistence / autosave change
- no UI expansion
- 50 internal ticks is a research parameter, not a runtime
  constant
- offline remains the default
- model-backed remains explicit opt-in
```

---

## 7. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used across the campaign: no
- reason: every step's deliverable was either a small
  self-contained doc, a documented one-line patch, a measurement
  over inspectable surfaces, or an analysis of measured data; no
  measurement was contested or required external review.

Stage B limited-write collaboration:
- used across the campaign: no
- reason: parent Claude was the sole writer of every doc and
  every patch; the harness scripts that ran the real-model
  smoke and the initial test live under /tmp and are not
  committed.

Stage C.1 flow orchestration:
- used across the campaign: no
- reason: bridge overhead exceeds the cost of direct writes for
  bounded single-file docs; and the campaign-level Phase 3.17
  policy explicitly forbids Stage C.1 for the real codex-cli
  loop. The Stage C.1 wrapper is available for the future
  Phase 3.18 prototype campaign should bounded doc / fixture
  shards become useful then.
```

---

## 8. Next artifact

Step 10:
`docs/campaigns/phase3_17/PHASE3_17_CODEX_PROCESSING_WINDOW_AUDIT.md`
— the campaign-level audit with the explicit verdict.
