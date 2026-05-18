# PHASE3_13_GROWTH_LEDGER_FINDINGS.md

## Purpose

This document is the Step 9 findings / triage artifact for Phase 3.13
Growth Ledger v1. It consolidates the eight findings F-1..F-8 emitted
by the Step 8 behavior report
(`docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_BEHAVIOR_REPORT.md`),
classifies each finding's triage disposition, and decides which (if
any) are blockers for the Phase 3.13 Step 10 final audit.

This document **does not change** code, catalog rows, fixtures, runtime
behavior, persistence, the UI surface, the autosave trigger set, the
ChatGPT/Codex advisory bridge, or any earlier Phase 3.13 artifact. It
is documentation only. No code, catalog, fixture, runtime, SelfModel,
UI, persistence extension, aggregate growth score, or claim-boundary
expansion is authorized by this triage. The Step 4 corrigenda locks
(LOCK A through LOCK T) and the Step 5 catalog patch plan remain
unchanged.

## Baseline

```text
Catalog version:               v0.23
Counts:
  REQUIRED:                    259
  STRUCTURAL:                   86
  NOT-EXERCISED:                12
  DEFERRED:                     15
  OBSERVED:                     16
Branch:                        campaign/phase3-13-growth-ledger
Step 7 implementation commit:  1cc73da  (phase3.13 step7: implement
                                          growth ledger option A)
Step 8 behavior report commit: 8851639  (phase3.13 step8: growth
                                          ledger behavior report)
Step 8 behavior verdict:       PASS WITH DEFERRED FOLLOW-UPS
Growth Ledger row family:      I-GROW-01..22 (catalog v0.23)
Active Stage A advisory bridge: /ask-chatgpt; wrapper
                                tools/claude_helpers/codex_chatgpt_subagent.py
                                used in Steps 1, 2, 3, 4, 5, 8, and
                                again in this Step 9 (review /
                                gpt-5.5 / low)
```

Preflight gates re-verified at Step 9 entry (every gate PASS):

```text
python3 -m tools.catalog counts     PASS  (259 / 86 / 12 / 15 / 16)
python3 -m tools.citations verify   PASS  (100 citations resolved)
python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
python3 -m brain.invariants run     PASS  (353 rows; 0 gate failures)
bash tools/check_all.sh             PASS  (All checks passed.)
```

## Source Findings

The eight Step 8 findings F-1..F-8 are imported below in compact form
and triaged. Each row's Step 8 severity / category is preserved
verbatim; the triage disposition and action columns are this step's
additions. The target campaign / step column records the explicit
deferral target (or "n/a" for pass evidence).

```text
ID    Step 8 severity   Step 8 category          Triage disposition                Blocker?  Action                                                                       Target campaign / step
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
F-1   minor             documentation             documentation / probe artifact;   no        record as future probe cleanup only; no code patch. The actual runtime         future probe author (not
                                                  superseded by repo-local                    contract is enforced by _require_bounded_printable in                            Phase 3.13); not Step 10
                                                  evidence (runtime contract                  brain/development/growth_ledger.py and asserted by the                          gate-affecting
                                                  green; I-GROW-03 fixture                    growth_ledger_constructor fixture (I-GROW-03 REQUIRED, green).
                                                  green)                                       The probe is the synthetic test that was wrong; the substrate is correct.

F-2   minor             deferred enhancement      deferred enhancement;             no        defer to a future persistence-oriented behavior probe only if SESSION_SAVED   future persistence-promotion
                                                  not required for Step 10 entry              / SESSION_LOADED are promoted from deferred to v1 in a follow-up reviewed       campaign (not Phase 3.13);
                                                  by the campaign macro sequence              catalog patch. Until then, the deferred non-emission for those event types     LOCK A keeps v1 session-local
                                                                                              is structurally guaranteed by source inspection: _dispatch_save_session and    so a successful-path runtime
                                                                                              _dispatch_load_session contain no GrowthLedger.observe call on the              probe is not load-bearing for
                                                                                              successful path. The Step 8 behavior report explicitly marked this as           v1.
                                                                                              NOT RUN (configured-DB scaffolding cost), not as a validation gap.

F-3   minor             deferred enhancement      planned placeholder;              no        leave NOT-EXERCISED. Revisit only in a follow-up campaign that explicitly      future follow-up campaign
                                                  not required for Step 10 entry              authorizes the I-GROW-22 end-to-end dry-run row. The row mirrors                (post-Phase 3.13);
                                                                                              I-PLEDGER-18 and I-COHMON-14 (also NOT-EXERCISED placeholders); the v0.23       LOCK T explicitly authorized
                                                                                              catalog has 12 NOT-EXERCISED rows total, all by design. The row is not          this row as NOT-EXERCISED in
                                                                                              described as exercised, covered, or validated.                                  the Step 5 plan.

F-4   none              no issue                   pass evidence (anti-Goodhart      no        no action. Evidence: 300 successive distinct /stream commands produced         n/a
                                                  cap behavior observed                       exactly 256 events; observe at cap returned self. This is observed cap
                                                  exactly as locked)                          behavior in the tested spam scenario only; it is not a general "anti-
                                                                                              Goodhart-solved" claim.

F-5   none              no issue                   pass evidence (17 read-only        no        no action. Evidence: 17 read-only verbs (/state /tick /output /worldlet         n/a
                                                  verbs produced zero growth                  /repl /stream-summary /stream-candidates /session-status /db-status
                                                  events)                                      /db-summary /profile-summary /stream-db-summary /db-diff /db-verify
                                                                                              /autosave-status /help /clear) each produced growth_delta=0 and the
                                                                                              ledger identity was unchanged across the sequence.

F-6   none              no issue                   pass evidence (constructor /       no        no action. Evidence: GrowthLedger().observe(...) with negative tick,           n/a
                                                  observe validation rejects                  duplicate references, and non-enum event_type each raised ValueError.
                                                  bad inputs)                                  COGITO_ID rejection is enforced by _require_bounded_printable;
                                                                                              I-GROW-03 fixture confirms.

F-7   none              no issue                   pass evidence (no-mutation         no        no action. Evidence: BrainState identity preserved across direct                 n/a
                                                  verification passed)                        GrowthLedger.observe; Pattern Ledger entries identical pre / post a
                                                                                              direct observe; autosave_config and session_store_config identities
                                                                                              preserved across the full safe-route exercise; persistence schema
                                                                                              unchanged; autosave trigger set unchanged.

F-8   none              no issue                   pass evidence; deferred design    no        no action. Evidence: SESSION_SAVED / SESSION_LOADED /                          n/a
                                                  confirmed (deferred event                   COHERENCE_REPORT_BUILT counts remain 0 across every exercised scenario.
                                                  types emitted zero events                   The non-emission is the conjunction of "no observe call on those paths"
                                                  across exercised scope)                     (source inspection) and "no event observed at runtime" (probe). The
                                                                                              claim is scoped to the exercised paths; it is not a global impossibility
                                                                                              proof for any future call site.
```

## Blocker Assessment

```text
No blocker findings.

No critical correctness finding.
No safety / invariant finding.
No catalog-count finding.
No runtime mutation finding.
No hidden persistence finding.
No hidden LLM finding.
No SelfModel creep.
No UI creep.
No aggregate score creep.
```

Each forbidden category above maps to a Step 8 surface that produced
evidence:

```text
critical correctness       — F-4 / F-5 / F-6 / F-7 / F-8 pass
safety / invariant         — F-6 (constructor validation) +
                              `python3 -m brain.invariants run` PASS
                              (353 rows; 0 gate failures)
catalog-count              — `python3 -m tools.catalog counts` PASS
                              (259 / 86 / 12 / 15 / 16) at every gate
runtime mutation           — F-7 no-mutation evidence over BrainState,
                              Pattern Ledger, autosave_config,
                              session_store_config
hidden persistence         — LOCK A; no SCHEMA_VERSION bump in
                              Step 7 commit; no growth_events table;
                              /save-session and /load-session do not
                              serialize the Growth Ledger
hidden LLM                 — growth_ledger.py imports only
                              dataclasses / enum / hashlib / typing /
                              COGITO_ID; I-GROW-10 / I-GROW-11 static
                              AST audit fixtures both green
SelfModel creep            — no SelfModel module exists; mission
                              baseline preserved
UI creep                   — LOCK S; I-GROW-21 DEFERRED; no
                              OperatorCommand member, no parser entry,
                              no active_view value, no render /
                              snapshot / commands / command_line edit
                              in Step 7 commit
aggregate score creep      — F-7 forbidden-attribute check;
                              I-GROW-09 / I-GROW-19 green
```

The triage's conclusion that "no Step 8 finding is a blocker" depends
on the Step 8 behavior report and the green preflight gates at Step 9
entry. If any of those gates fail in a future re-run, this triage's
verdict is void and the campaign must re-enter Step 8.

## Non-blocking Follow-ups

```text
1. Probe cleanup
   - F-1 traces to a synthetic test in /tmp/phase3_13_growth_ledger_probe.py
     that used the literal "COGITO" rather than the COGITO_ID constant
     value "__cogito__".
   - The probe is not committed and is not load-bearing for any
     invariant.
   - A future probe author should import brain.tlica.profile.COGITO_ID
     and reuse it in any COGITO-rejection check.
   - No code / catalog / fixture change is needed for Phase 3.13.

2. Persistence-oriented behavior probe
   - F-2 is a scope choice, not a defect. v1 Growth Ledger is
     session-local (LOCK A), so the v1 contract has no successful save /
     load round-trip to observe.
   - If a future campaign promotes SESSION_SAVED / SESSION_LOADED from
     the deferred set into v1 emit scope, that campaign will need a
     persistence-oriented behavior probe (configured --session-db,
     successful save, successful load, observed-zero-emission still
     holds OR the promoted-event emission shape is asserted) plus a
     fresh catalog patch.
   - Not in Phase 3.13 scope.

3. I-GROW-22 dry-run row
   - F-3 is a planned placeholder. The row stays NOT-EXERCISED in
     v0.23. The Step 5 catalog patch plan explicitly enumerated this
     row as a NOT-EXERCISED placeholder mirroring I-PLEDGER-18 /
     I-COHMON-14; the v0.22 → v0.23 count delta (+1 NOT-EXERCISED)
     allocated exactly this slot for it.
   - A future campaign may promote the row to REQUIRED / OBSERVED via
     a follow-up reviewed catalog patch.
   - Not in Phase 3.13 scope.

4. Potential future /growth-ledger UI
   - The UI surface remains DEFERRED at I-GROW-21 (mirroring
     I-PLEDGER-17 /pattern-ledger and I-COHMON-13 /coherence-summary).
   - Promotion requires a separate reviewed catalog patch in a
     follow-up campaign — no OperatorCommand member, no parser entry,
     no active_view value, no render / snapshot / commands /
     command_line change is authorized by Phase 3.13.

5. Future SelfModel
   - SelfModel remains deferred per the Phase 3.12 Step 15 roadmap
     and the Phase 3.13 mission baseline.
   - A future SelfModel campaign should consume Growth Ledger facts
     (counts_by_type, references, provenance, source label) and the
     Coherence Monitor status surface (CoherenceReport overall_status
     and counts_by_status) as bounded read-only inputs. It should not
     re-derive growth from current BrainState alone.
   - Not in Phase 3.13 scope and not authorized by this triage.
```

None of these follow-ups requires a Phase 3.13 patch. Each is a
separate, future, reviewed campaign step or deliberate non-action.

## Items That Do NOT Block Phase 3.13

Explicitly enumerated for the Step 10 audit:

```text
- F-1 probe artifact (literal "COGITO" mismatch in temporary probe;
  runtime contract and I-GROW-03 fixture green)
- F-2 successful save/load against a configured --session-db NOT RUN
  by design (configured-DB scaffolding cost; deferred event types
  remain non-emitted under LOCK A)
- F-3 I-GROW-22 NOT-EXERCISED placeholder remaining as planned
- lack of /growth-ledger UI (LOCK S; I-GROW-21 DEFERRED)
- lack of persistence for Growth Ledger (LOCK A; session-local only
  in v1)
- lack of SelfModel (Phase 3.12 Step 15 roadmap deferred; mission
  baseline)
- lack of observed dry-run row promotion (I-GROW-22 NOT-EXERCISED by
  design)
- lack of real external LLM runtime smoke beyond Stage A /ask-chatgpt
  advisor bridge (mission baseline; only the Stage A bridge is
  sanctioned)
```

Each non-block above is anchored to a specific corrigenda lock, mission
guardrail, or catalog row classification, so the Step 10 audit can
verify the same set without re-discovering it.

## Campaign Verdict After Triage

```text
PASS WITH DEFERRED FOLLOW-UPS
```

Reason:

```text
- all five preflight gates green at Step 9 entry
  (catalog counts / citations / import_audit / brain.invariants run /
   check_all.sh — see Baseline)
- the seven v1 emitted event types' behavior is observed correctly
  through the safe operator route (Step 8 Test Matrix Families 2–6)
- the three deferred event types are confirmed non-emitted across the
  exercised scope, by both runtime probe and source inspection
  (Step 8 Families 9, 10; F-8 evidence)
- no blocker finding emerged from Step 8 (F-1..F-8 all classified
  non-blocking)
- no unauthorized scope expansion occurred: no SelfModel, no UI, no
  persistence, no aggregate score, no LLM call, no DB schema change,
  no autosave trigger-set extension, no kernel mutation, no claim
  beyond what the locked operational definition permits
```

The verdict is **PASS WITH DEFERRED FOLLOW-UPS**, not plain **PASS**,
because F-2 and F-3 remain unresolved by design and the campaign has
not exercised every Growth Ledger row (I-GROW-22 stays NOT-EXERCISED).
The deferred follow-ups are not silent gaps — each is named,
scoped, and recorded above so a future campaign can pick it up.

## ChatGPT/Codex Consultation

Used the sanctioned Stage A advisory bridge once during Step 9, mode
`review`, model `gpt-5.5`, effort `low`, timeout `120`. The question
file and answer file are both in `/tmp` and are not committed; the
wrapper's hash-only audit JSONL appended to
`.claude/codex_bridge_logs/2026-05-18.jsonl` (gitignored by design).

```text
ChatGPT/Codex consultation:
- used:           yes
- mode:           review
- model:          gpt-5.5
- effort:         low
- wrapper command: python3 tools/claude_helpers/codex_chatgpt_subagent.py
                     --mode review --model gpt-5.5 --effort low
                     --timeout 120
                     --prompt-file /tmp/toyi_chatgpt_step9_question.md
                     > /tmp/toyi_chatgpt_step9_answer.md
- question file:   /tmp/toyi_chatgpt_step9_question.md
- answer file:     /tmp/toyi_chatgpt_step9_answer.md
- wrapper status:  exit 0; error_class null; codex_returncode 0;
                   duration_ms 69844; stdout_bytes 4460; stderr_bytes
                   8601; truncated false; codex-cli 0.130.0; auth
                   "Logged in using ChatGPT". Audit JSONL appended at
                   .claude/codex_bridge_logs/ (gitignored).
- accepted advice:
   - Use PASS WITH DEFERRED FOLLOW-UPS, not plain PASS, while F-2 and
     F-3 remain unresolved. Applied in Campaign Verdict After Triage.
   - Label F-2 and F-3 as "deferred follow-up, not required for
     Step 10 entry"; do not describe them as satisfied, covered, or
     validated. Applied in the Source Findings table and in
     Non-blocking Follow-ups.
   - For F-1, say the temporary probe had a literal mismatch, but
     repo-local runtime contract and I-GROW-03 fixture evidence
     remain green. Applied verbatim in the Source Findings row.
   - Do not turn "zero events emitted by deferred event types" into a
     broad claim that deferred behaviors are impossible or globally
     prevented. Applied as the scoping language in the F-8 row.
   - Do not frame anti-Goodhart cap behavior as a general solution to
     Goodharting; keep it tied to the observed cap behavior from
     Step 8. Applied as the scoping language in the F-4 row.
   - Include a sentence that no code, catalog, fixture, runtime,
     SelfModel, UI, persistence extension, aggregate score, or
     claim-boundary expansion is authorized by this triage. Applied
     in Purpose.
- rejected advice:
   - None substantive. The advisor's risk note that "if repo-local
     final audit gates require every Growth Ledger row to be
     exercised, F-3 could become blocking" was treated as a scoping
     question rather than a contradiction. The Step 5 catalog patch
     plan and LOCK T explicitly authorize the NOT-EXERCISED status of
     I-GROW-22 and CURRENT_CAMPAIGN.md's Step 10 contract does not
     impose a "every row must be exercised" gate; the final-audit
     gates are catalog counts / citations / import audit /
     brain.invariants run / check_all.sh. F-3 therefore remains
     non-blocking by design, not by oversight.
   - The advisor's parallel risk note that "if configured DB save /
     load is part of an explicit Step 10 entry criterion, F-2 could
     become blocking" was likewise treated as scoping. The campaign
     contract does not impose such a criterion; the Step 8 behavior
     report and LOCK A together explain why the v1 contract has no
     successful save / load round-trip to observe.
- reason:          Advisor's "minor disagreement, medium confidence"
                   verdict matched the triage. Every substantive
                   scoping suggestion was applied as inline wording;
                   rejections are explicit-scope clarifications, not
                   contradictions.
```

Treated the bridge output as advisory. Repo-local files, gates, and
invariants override ChatGPT advice; the advisor's own answer requires
this priority.

## Next Artifact

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_AUDIT.md
```

Step 10 is the Final Phase 3.13 Audit. The audit will:

- re-run every preflight gate (catalog counts / citations verify /
  import audit / brain.invariants run / check_all.sh) and record the
  results
- enumerate files changed across the campaign (Steps 1–9 commits)
- restate the explicit "no SelfModel" / "no consciousness /
  sentience / subjective / semantic / truth / agency /
  self-modification claim" / "no aggregate growth / I-ness score" /
  "no hidden LLM call / hidden persistence / DB schema change in v1"
  confirmations
- record per-step Stage A /ask-chatgpt bridge usage with links to
  this triage and the prior step disclosures
- note that SelfModel remains deferred to a future campaign

Implementation remains unchanged at Step 10. Step 11 prepares the
final PR.

## Validation

Re-ran after writing this findings file (no source under `brain/**`,
`tools/**`, `.claude/**`, `lean_reference/**`, `scenarios/**`, or
`traces/**` was touched; no edit to `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`PHASE3_13_GROWTH_LEDGER_ROADMAP.md`, the Step 2 synthesis, the
Step 3 kickoff, the Step 4 corrigenda, the Step 5 catalog patch plan,
or the Step 8 behavior report; only this new documentation file was
added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS (259 / 86 / 12 / 15 / 16) |
| `python3 -m tools.citations verify` | PASS (100 citations resolved) |
| `python3 -m tools.import_audit` | PASS (I-PCE-05 clean) |
| `python3 -m brain.invariants run` | PASS (353 rows; 0 gate failures) |
| `bash tools/check_all.sh` | PASS (All checks passed.) |
