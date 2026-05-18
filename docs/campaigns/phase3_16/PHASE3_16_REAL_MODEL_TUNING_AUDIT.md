# PHASE3_16_REAL_MODEL_TUNING_AUDIT.md

## Final verdict

```text
REAL MODEL TEST PASS
```

ToyI's runtime delivered a complete, inspectable, real-model-backed
operational walk through the existing public dispatch path within
the 30-call budget, with no kernel runtime change and no committed
secrets / cache files / raw prompts / raw responses.

The "PARTIAL" finding for codex-cli (CLI version compatibility) is
**not** a campaign blocker because the campaign explicitly says
"Use the first available/configured mode that can safely run. Do not
require all three." claude-cli supplied the full operational walk.

---

## 1. Files changed across the campaign

```text
Step 1 (mission install):
  CURRENT_MISSION.md
  CURRENT_CAMPAIGN.md
  PHASE3_16_REAL_MODEL_OPERATIONAL_TUNING_ROADMAP.md   (new)

Step 2 (synthesis):
  docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_SYNTHESIS.md   (new)

Step 3 (baseline):
  docs/campaigns/phase3_16/PHASE3_16_MODEL_AVAILABILITY_BASELINE.md   (new)

Step 4 (real model run):
  docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_RUN.md   (new)

Step 5 (findings):
  docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_FINDINGS.md   (new)

Step 8 (behavior report):
  docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_BEHAVIOR_REPORT.md   (new)

Step 9 (this audit):
  docs/campaigns/phase3_16/PHASE3_16_REAL_MODEL_TUNING_AUDIT.md   (new)
```

No source under `brain/**`, `tools/**`, `.claude/**`,
`INVARIANT_CATALOG.md`, `README.md`, `tools/catalog.py`,
`brain/invariants.py`, `scenarios/**`, `traces/**`, or
`lean_reference/**` was modified.

---

## 2. Gate results

Final gate run via `python3 -m tools.claude_helpers.gate_runner --json`
(captured at audit time):

```text
catalog_counts       : PASS
citations_verify     : PASS
import_audit         : PASS
invariants_run       : PASS  (377 rows checked; REQUIRED green 282;
                              REQUIRED red 0; STRUCTURAL green 88;
                              STRUCTURAL red 0; OBSERVED 7 pass / 0
                              fail; gate failures 0)
check_all            : PASS
summary              : 5 passed / 0 failed / 0 errors / 0 timed out
```

The new audit file forces one more re-run before the PR is opened
(Step 10); we expect identical results.

---

## 3. Real model call accounting (campaign total)

```text
Step 1   : 0
Step 2   : 0
Step 3   : 0
Step 4   : 6
           - 1 codex exec probe
           - 1 codex factory run (failed at trusted-dir check;
             counted as an attempt)
           - 1 claude -p probe
           - 2 walk-A ticks (1 call each)
           - 1 walk-B tick #1 (walk-B tick #2 hit L2 = 0 calls)
Step 5   : 0
Step 8   : 0
Step 9   : 0

Cumulative real model calls : 6 / 30
Budget remaining            : 24
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
- no tick semantic change (brain/tick.py untouched)          : confirmed
- L1 cache growth bounded by L1_CACHE_MAX_ENTRIES=1024       : confirmed
- L2 cache growth bounded by SEMANTIC_CACHE_MAX_ENTRIES=1024 : confirmed
- OFFLINE remains default                                    : confirmed
- model-backed modes remain explicit opt-in                  : confirmed
- no raw prompts committed to the repo                       : confirmed
- no raw model responses committed to the repo               : confirmed
- no raw cache contents printed in docs                      : confirmed
- no secrets committed to the repo                           : confirmed
- no secrets printed in reports (presence-only redaction)    : confirmed
- no cache files committed (brain/.llm_cache gitignored)     : confirmed
- no UI expansion                                            : confirmed
- no raw codex invocation through bridges                    : confirmed
- no Stage C.1 broad repo edits                              : confirmed
- no unbounded Codex collaboration loop                      : confirmed
- catalog v0.25 unchanged                                    : confirmed
- counts 281 / 88 / 14 / 15 / 16 unchanged                   : confirmed
- main branch was not pushed to during campaign execution    : confirmed
- campaign branch                                            :
    campaign/phase3-16-real-model-operational-tuning
- PR will be opened in Step 10 and will NOT be merged         : pending
```

---

## 5. Stage A / Stage B / Stage C.1 bridge usage across the campaign

```text
Stage A ChatGPT/Codex consultation:
- used in any step: no
- reason: every step produced bounded, self-contained deliverables;
  no measurement contestation arose; no adversarial review was
  required to make a decision.

Stage B limited-write collaboration:
- used in any step: no
- reason: parent Claude wrote every doc and config directly; the
  Stage B overhead would exceed the cost of direct writes.

Stage C.1 flow orchestration:
- used in any step: no
- reason: every step required either runtime measurements (Steps 3,
  4) or a small single-file doc draft (Steps 1, 2, 5, 8, 9). The
  campaign target was deliverable without flow orchestration. The
  Phase 3.16 roadmap allowed Stage C.1 at Step 1 / 2 / 5 / 8 / 9 but
  did not require it.
```

---

## 6. What ToyI actually demonstrated (bounded, non-claim)

ToyI demonstrated, under direct observation, that:

```text
- a real model-backed LLMClient can be constructed via the public
  brain.ui.llm_runtime.build_llm_client_from_config(...) factory and
  consumed end-to-end through brain.ui.session.OperatorSession.dispatch
- the brain.tick.tick(...) public path completes once per STEP_TICK
  command and produces a TickRecord (triggered_mode = NEUTRAL in
  the observed runs)
- brain.tlica.profile / brain.tlica.msi / brain.tlica.ptcns mutate
  in the documented direction when a new content_id enters via
  QUEUE_PERCEPT
- brain.llm.client.CachedClient writes to disk on a miss, persists
  one JSON entry per cache key, and exposes hit_count / miss_count /
  skip_count counters reachable from the test harness
- brain.llm.ptcns_backed.LLMBackedPtCns canonical eval cache writes
  to brain/.llm_cache/eval_v1/, restricts entry payload to
  {"key_prefix", "parsed"}, and returns a cache hit for identical
  evaluated text under a different content_id within the same MSI
  context — without a model call
- brain/.llm_cache remains gitignored and contains no committed
  artifact
```

ToyI did **not** demonstrate, and this campaign does **not** claim:

```text
- consciousness, sentience, awareness, subjective experience,
  semantic understanding, truth, agency, intent, will, desire, or
  self-modification
- a meaningful aggregate "I-ness" or "growth" score
- that the parsed ConsistencyEval value carries any normative or
  truth-adjudicative meaning; the parser maps a token to an enum
  and the kernel responds per its documented bias rules
- that the codex-cli mode is operationally compatible without
  the deferred patch
```

---

## 7. Deferred follow-ups (NOT shipped)

```text
F1 codex-cli compatibility: add --skip-git-repo-check to
   CodexCLIClient.command, or change cwd to repo root. Out of scope
   for Phase 3.16 (brain/llm/client.py edit).

F2 tracer wiring through OperatorSession.dispatch so trace events
   (llm.cache_*, llm.semantic_cache_*, parse.*) are externally
   observable. Out of scope (brain/tick.py + brain/ui/session.py
   surface).

F3 parser ambiguity hardening (PARSE_SCHEMA_VERSION bump). Out of
   scope; requires its own campaign.

F4 anthropic-api smoke (BLOCKED BY ENV in this checkout; no
   ANTHROPIC_API_KEY).

F5 SelfModel: remains explicitly out of scope.

F6 /pattern-ledger / /coherence-summary / /growth-ledger UIs remain
   DEFERRED at catalog level.

F7 I-LLMCACHE-21 / I-LLMCACHE-22 remain NOT-EXERCISED at catalog
   level. Phase 3.16 produced concrete evidence aligned with both
   (a real model-backed cache smoke and an end-to-end behavior
   probe) but did NOT commit to a catalog status change.
```

---

## 8. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- mode / model / effort: n/a
- wrapper command: n/a
- question file / answer file: n/a
- wrapper status: n/a
- accepted advice: none
- rejected advice: none
- reason: bounded self-contained audit; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: a single audit doc; bridge overhead exceeds the cost of
  writing directly.
```

---

## 9. Next-campaign note

```text
Phase 3.16 closes with the operational walk demonstrated under
claude-cli at 6/30 real model calls. The recommended next campaign
is a small "codex-cli compatibility + tracer wiring" campaign that
addresses F1 and F2 above and (optionally) promotes I-LLMCACHE-21
and I-LLMCACHE-22 from NOT-EXERCISED to REQUIRED / OBSERVED with
fresh measurement evidence.

SelfModel remains deferred. Promote only after a follow-up campaign
that explicitly accepts the SelfModel plan.
```

---

## 10. Next artifact

Step 10: PR preparation. Open a PR to `main` titled
`phase3.16: real model operational tuning`. Do NOT merge.
