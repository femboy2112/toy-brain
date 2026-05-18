# PHASE3_17_CODEX_PROCESSING_WINDOW_AUDIT.md

## Final verdict

```text
PASS WITH DEFERRED IMPLEMENTATION
```

Phase 3.17 unblocked codex-cli end-to-end through the public
`OperatorSession.dispatch` path under `codex-cli 0.130.0`, produced
a rigorous research artifact set for a bounded post-input
**internalization window** (synthesis, probe plan, implementation
plan, and an N=0 negative-control initial test), and confirmed
hypotheses H1, H5, H6 of the synthesis. The runtime
processing-window loop is deferred to a future
operator-approved campaign (Phase 3.18) behind GATE-PW-1..5.

---

## 1. Files changed across the campaign

```text
Step 1 (mission install):
  CURRENT_MISSION.md
  CURRENT_CAMPAIGN.md
  PHASE3_17_CODEX_PROCESSING_WINDOW_ROADMAP.md            (new)

Step 2 (codex-cli patch plan):
  docs/campaigns/phase3_17/PHASE3_17_CODEX_CLI_COMPAT_PATCH_PLAN.md (new)

Step 3 (apply codex-cli fix):
  brain/llm/client.py                                     (modified)
  brain/ui/llm_runtime.py                                 (modified)
  brain/ui/fixtures/llm_runtime_codex_cli_factory.py      (modified)

Step 4 (codex-cli real model smoke):
  docs/campaigns/phase3_17/PHASE3_17_CODEX_CLI_REAL_MODEL_SMOKE.md (new)

Step 5 (synthesis):
  docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_SYNTHESIS.md (new)

Step 6 (probe plan):
  docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_PROBE_PLAN.md (new)

Step 7 (implementation plan):
  docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_IMPLEMENTATION_PLAN.md (new)

Step 8 (initial test):
  docs/campaigns/phase3_17/PHASE3_17_PROCESSING_WINDOW_INITIAL_TEST.md (new)

Step 9 (findings):
  docs/campaigns/phase3_17/PHASE3_17_FINDINGS.md          (new)

Step 10 (this audit):
  docs/campaigns/phase3_17/PHASE3_17_CODEX_PROCESSING_WINDOW_AUDIT.md (new)
```

No source under `brain/tick.py`, `brain/llm/parse.py`,
`brain/llm/prompts.py`, `brain/llm/ptcns_backed.py`,
`brain/development/**`, `brain/tlica/**`, `brain/ui/session.py`,
`brain/ui/__main__.py`, `brain/io_types.py`, `tools/catalog.py`,
`INVARIANT_CATALOG.md`, `README.md`, `scenarios/**`,
`traces/**`, or `lean_reference/**` was modified.

---

## 2. Gate results

Final gate run via `python3 -m tools.claude_helpers.gate_runner --json`:

```text
catalog_counts       : PASS
citations_verify     : PASS
import_audit         : PASS
invariants_run       : PASS  (REQUIRED green 282; REQUIRED red 0;
                              STRUCTURAL green 88; STRUCTURAL red
                              0; OBSERVED 7/0; gate failures 0)
check_all            : PASS
summary              : 5 passed / 0 failed / 0 errors / 0 timed out
```

The new I-LLMTOG-17 assertions (Phase 3.17 Step 3 fixture
refresh) run as part of every `invariants_run` invocation; they
remained green after the patch landed.

---

## 3. Real model call accounting (campaign total)

```text
Step 1   : 0
Step 2   : 0
Step 3   : 0
Step 4   : 1   (codex-cli; tick 1 NEUTRAL; 12.5 s)
Step 5   : 0
Step 6   : 0
Step 7   : 0
Step 8   : 1   (codex-cli; S8.4 baseline; 7.7 s)
Step 9   : 0
Step 10  : 0
              ---
Cumulative real model calls : 2 / 20
Budget remaining            : 18

Mode tested: codex-cli (PRIMARY; resolved the Phase 3.16
             trusted-dir blocker via the Step 3 patch).

claude-cli  : not exercised in Phase 3.17 (already proven by
              Phase 3.16; no need to re-validate).
anthropic-api : BLOCKED BY ENV (no API key in this checkout);
                inherited from Phase 3.16 F4.
```

---

## 4. Constraint confirmations

```text
- no SelfModel implementation                                : confirmed
- no consciousness / sentience / subjective / semantic /
  truth / agency / self-modification claim                   : confirmed
- no aggregate consciousness / sentience / awareness /
  I-ness / growth score                                      : confirmed
- no hidden LLM calls                                        : confirmed
- no hidden persistence / autosave behavior                  : confirmed
- no DB schema change in v1                                  : confirmed
- no SCHEMA_VERSION bump                                     : confirmed
- no L2 (eval_v1) semantic change                            : confirmed
- no L1 cache semantic change                                : confirmed
  (the codex command tuple addition is a CLI compatibility
   flag, not a cache-policy change; L1 cap 1024 and write-skip-
   at-cap policy unchanged)
- no tick semantic change (brain/tick.py untouched)          : confirmed
- L1 cache growth bounded by L1_CACHE_MAX_ENTRIES=1024       : confirmed
- L2 cache growth bounded by SEMANTIC_CACHE_MAX_ENTRIES=1024 : confirmed
- OFFLINE remains default                                    : confirmed
- model-backed modes remain explicit opt-in                  : confirmed
- no parser change                                           : confirmed
- no prompt change                                           : confirmed
- no Growth Ledger semantic change                           : confirmed
- no Pattern Ledger semantic change                          : confirmed
- no Coherence Monitor semantic change                       : confirmed
- no UI expansion                                            : confirmed
- no raw codex invocation outside the sanctioned factory     : confirmed
- no raw prompts committed                                   : confirmed
- no raw model responses committed                           : confirmed
- no raw cache contents printed in docs                      : confirmed
- no secrets committed                                       : confirmed
- no secrets printed in reports                              : confirmed
- no cache files committed (brain/.llm_cache gitignored)     : confirmed
- catalog v0.25 unchanged                                    : confirmed
- counts 281 / 88 / 14 / 15 / 16 unchanged                   : confirmed
- main branch was not pushed to during campaign execution    : confirmed
- campaign branch                                            :
    campaign/phase3-17-codex-processing-window
- 50 internal ticks is an experimental default, not a runtime
  constant in v1                                             : confirmed
  (the synthesis recommends N=50 as a research starting point;
   Phase 3.17 does not bake any constant into the runtime; no
   internal-tick loop ships in this campaign)
- PR will be opened in Step 11 and will NOT be merged         : pending
```

---

## 5. Stage A / Stage B / Stage C.1 bridge usage across the campaign

```text
Stage A ChatGPT/Codex consultation:
- used in any step: no
- reason: every step produced bounded, self-contained
  deliverables (doc / patch / measurement / analysis); no
  measurement contestation arose; no adversarial review was
  required.

Stage B limited-write collaboration:
- used in any step: no
- reason: parent Claude wrote every doc and patch directly; the
  bridges' overhead would exceed the cost of direct writes.

Stage C.1 flow orchestration:
- used in any step: no
- reason: the campaign was bounded enough to deliver without
  flow orchestration; the campaign-level policy in
  CURRENT_MISSION.md / CURRENT_CAMPAIGN.md forbade Stage C.1
  for the real codex-cli loop (Step 4) and for the runtime
  patch itself (Step 3); for the remaining doc-only steps, a
  single bounded doc shard per step was cheaper to write
  directly than to orchestrate.
```

Disclosure block (canonical):

```text
Stage A:
- used: no
- mode / model / effort: n/a
- wrapper command: n/a
- question file / answer file: n/a
- wrapper status: n/a
- accepted advice: none
- rejected advice: none
- reason: see above.

Stage B:
- used: no
- mode / model / effort: n/a
- wrapper command: n/a
- allowed files / prompt file / answer file: n/a
- wrapper status: n/a
- files changed: n/a
- accepted/rejected edits: none
- reason: see above.

Stage C.1:
- used: no
- manifest path: n/a
- manifest validation: n/a
- wrapper command: n/a
- wrapper status: n/a
- nodes: n/a
- changed files: n/a
- accepted/rejected edits: none
- reason: see above.
```

---

## 6. What ToyI actually demonstrated (bounded, non-claim)

```text
- The Phase 3.16 codex-cli trusted-dir construction failure is
  resolved by adding the documented --skip-git-repo-check flag
  to CodexCLIClient.command. Two independent end-to-end ticks
  (Step 4 + Step 8 S8.4) under codex-cli 0.130.0 produced
  NEUTRAL parses cleanly within 90-second timeouts.

- The existing public dispatch path
  (OperatorSession.dispatch(QUEUE_PERCEPT) +
  OperatorSession.dispatch(STEP_TICK, client=...)) drives a
  complete model-backed tick, with measurable cache + state +
  ledger deltas.

- A bounded post-input internalization window can be designed
  using existing kernel surfaces, with a deterministic generator
  for internal PerceptEvent candidates from already-accepted
  state (Pattern Ledger entries, Coherence Monitor warnings,
  prior ConsistencyEvals). The synthesis fixes N=50 as the
  initial experimental parameter and identifies seven testable
  hypotheses (H1-H7).

- The Step 8 negative-control probe confirmed H1, H5, H6:
    H1 — at N=0 only external-source events appear; the
         counterfactual showed that even a well-shaped
         internal_processing_window-provenance event sitting
         in the queue produces NO Growth Ledger / Pattern
         Ledger / Coherence delta beyond queue_size += 1.
    H5 — no new FAIL emerged in any cell.
    H6 — no aggregate scalar was emitted; counts_by_status and
         counts_by_type remain labeled tuples.

- Hypotheses H2 / H3 / H4 / H7 are untestable at N=0 by
  construction and are deferred to Phase 3.18.
```

ToyI did **not** demonstrate, and Phase 3.17 does **not** claim:

```text
- consciousness, sentience, awareness, subjective experience,
  semantic understanding, truth, agency, intent, will, desire,
  or self-modification (in the strong sense);
- a meaningful aggregate "I-ness" / "growth" / "consciousness"
  / "awareness" score;
- that the parsed ConsistencyEval value carries normative or
  truth-adjudicative meaning beyond the strict parser's
  enum-mapping contract;
- that a runtime processing window is necessary, useful, or
  safe — those questions are deferred to Phase 3.18, subject to
  GATE-PW-1..5;
- that 50 internal ticks is the right N — it is the initial
  experimental default proposed in the synthesis; the actual
  N for any future implementation campaign is subject to
  empirical evidence from probe runs.
```

---

## 7. Deferred follow-ups (NOT shipped here; carries to Phase 3.18 or later)

```text
F1. Architecture A (session-level processing-window loop).
    Specified in detail in Step 7. Requires GATE-PW-1..5.

F2. The 75-cell probe matrix from Step 6 (full sweep).
    The methodology and per-cell measurement spec are ready.

F3. Architectures B / C / D / F.
    Named in the Step 5 synthesis as future work.

F4. Phase 3.16 F2 tracer wiring through OperatorSession.dispatch.

F5. Phase 3.16 F3 parser ambiguity hardening (PARSE_SCHEMA_VERSION
    bump).

F6. Phase 3.16 F4 anthropic-api smoke (env-dependent).

F7. SelfModel — remains OUT OF SCOPE indefinitely.

F8. Optional INVARIANT_CATALOG.md body refresh for
    I-LLMTOG-16/17/18 to mention --skip-git-repo-check (text
    only; no count change).

F9. /pattern-ledger / /coherence-summary / /growth-ledger UIs —
    DEFERRED at the catalog level since their respective
    Phase 3.12c / 3.13 campaigns.
```

---

## 8. Next-campaign recommendation

```text
Phase 3.18 — Bounded Internal Processing Window Prototype

Scope:
  1. Meet GATE-PW-1..5 (operator approval, architecture choice,
     catalog patch shape, fixture set, real-model budget).
  2. Land architecture A as specified in
     PHASE3_17_PROCESSING_WINDOW_IMPLEMENTATION_PLAN.md.
  3. Add the new module brain/development/processing_window.py
     plus one or two new fixtures.
  4. Run a reduced cell set from the Step-6 75-cell matrix
     under mock + codex-cli (~5-10 cells), within a Phase 3.18-
     specific real-model budget.
  5. Optional: refresh INVARIANT_CATALOG.md body text for the
     I-LLMTOG-16/17/18 mentions of ("codex", "exec") to match
     the new ("codex", "exec", "--skip-git-repo-check") tuple.
  6. Open a PR, do not merge, request human review.

Out of scope:
  - SelfModel.
  - Architectures B / C / D / F.
  - Parser ambiguity hardening (Phase 3.16 F3).
  - Tracer wiring (Phase 3.16 F2).
```

---

## 9. PR plan

```text
PR title           : phase3.17: codex runtime and processing window research
PR base            : main
PR head            : campaign/phase3-17-codex-processing-window
PR description     : see Step 11 PR body
Do NOT merge automatically.
```

---

## 10. Validation summary

```text
gate_runner --json    : PASS  (5 / 5)
campaign_state json   : current campaign = phase3.17, highest
                        step = 10
git status            : clean before the Step 10 commit (this
                        audit file is added by Step 10)
git diff (Step 3)     : 3 files; +47 / -13; no out-of-scope
                        touch
git diff (Steps 1-2,4-10): docs only (Steps 1 plus 2,4,5,6,7,8,9,10
                        add documents at known paths under
                        CURRENT_*.md / PHASE3_17_*.md /
                        docs/campaigns/phase3_17/*.md)
real model calls used : 2 / 20
```
