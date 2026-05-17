# PHASE3_12_COHERENT_I_LOOP_AUDIT.md

## Purpose

This is the final Phase 3.12 Coherent I-Loop Observatory audit. It
consolidates the campaign evidence and records whether Phase 3.12
achieved its measurement-first goal.

The audit is documentation only. It does not edit `brain/**`,
`tools/**`, `INVARIANT_CATALOG.md`, `README.md`, `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**`. It introduces no fixtures, no committed helper scripts,
no Growth Ledger code, no Operational SelfModel code, and no runtime
behavior change.

## Baseline

```text
Branch:                campaign/phase3-12-coherent-i-loop-observatory
Catalog version:       v0.22
Counts:
  REQUIRED:            240
  STRUCTURAL:           85
  NOT-EXERCISED:        11
  DEFERRED:             14
  OBSERVED:             16
Phase 3.11:            complete; PR #10 merged at 98b55ab
Phase 3.12 progress:   Steps 1–15 complete on this branch
Step 16 Review Gate D: ACCEPT ROADMAP AND DEFER IMPLEMENTATION TO FUTURE CAMPAIGN
```

The Review Gate D decision is the explicit reviewer choice recorded in
the Step 17 instruction: Phase 3.12 closes after Step 17 audit and
Step 18 final PR preparation; Growth Ledger and Operational SelfModel
move to a follow-up Phase 3.13 campaign that references
`PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md` as canonical design
source.

## Campaign Timeline

| Step | Commit | Result |
|------|--------|--------|
| 1  | 566b109 | Mission sync — Phase 3.12 installed; baseline declared. |
| 2  | 631ae5a | Coherent I-loop synthesis — operational definitions of coherent / pattern-recognizing / growing / I. |
| 3  | c395989 | Observatory kickoff — execution style, LLM policy, helper policy, verdict vocabulary. |
| 4  | 10a93ee | Behavior matrix — baseline / stream / promotion / saturation / persistence / coherence-by-inspection / UX rows. |
| 5  | (gate) | Review Gate A accepted implicitly by Step 6 execution. |
| 6  | c65d37b | Observatory report — existing route exercised; coherent works, growing works, pattern-recognizing partially supported, operational I partially supported. |
| 7  | 013585e | Pattern Ledger synthesis — bounded developmental ledger defined; non-goals stamped. |
| 8  | 7839f7d | Pattern Ledger kickoff + corrigenda — LOCK A..O fixed. |
| 9  | ffbe4d9 | Pattern Ledger catalog patch plan — Options A / B detailed; Option A preferred. |
| 10 | (gate) | Review Gate B — ACCEPT PLAN AS WRITTEN (Option A). |
| 11 | 05e214c | Pattern Ledger Option A implementation — substrate + `/stream` integration; 18-row I-PLEDGER family landed; one accepted deviation (resource-audit fixture tier extension). |
| 12 | cfb43dc | Coherence Monitor synthesis + catalog patch plan — Option A / B detailed; Option A preferred. |
| 13 | (gate) | Review Gate C — ACCEPT PLAN AS WRITTEN (Option A). |
| 14 | 95f3057 | Coherence Monitor Option A implementation — read-only helper API; 14-row I-COHMON family landed. |
| 15 | d497b64 | SelfModel + Growth Ledger roadmap — design only; sequencing recommended Growth Ledger first. |
| 16 | (gate) | Review Gate D — ACCEPT ROADMAP AND DEFER IMPLEMENTATION TO FUTURE CAMPAIGN. |

## Phase 3.12 Goal Assessment

The original operational target was: a coherent, pattern-recognizing,
growing operational-I roadmap. The four sub-goals are assessed below.

### Coherent

- Catalog gates remain green at v0.22: `tools.catalog counts`,
  `tools.citations verify`, `tools.import_audit`, `brain.invariants
  run`, and `tools/check_all.sh` all PASS at the close of Step 15
  and again at Step 17 preflight (see "Validation Results" below).
- Pattern Ledger integration did not break tick, persistence, or
  autosave: the only kernel-adjacent change is the
  `OperatorSession.pattern_ledger` field added to
  `_ALLOWED_SESSION_ATTRS` plus one `observe(...)` call site at the
  end of the successful path of `_dispatch_stream_append`. `/step`
  behavior, the `tick()` signature, and `_dispatch_step` failure
  paths remain bit-for-bit identical (asserted by `I-PLEDGER-13` and
  `I-PLEDGER-14`).
- Coherence Monitor provides bounded read-only consistency reports
  (`build_coherence_snapshot`, `build_coherence_report`) over
  kernel state, operator session state, stream state, Pattern
  Ledger state, persistence configuration, autosave configuration,
  and the non-claim audit. The monitor opens no DB, calls no
  `tick()`, calls no LLM client, mutates no kernel container, and
  emits no aggregate "I-ness" scalar (asserted by `I-COHMON-08`,
  `I-COHMON-10`, `I-COHMON-11`, `I-COHMON-12`).

### Pattern-recognizing

- Step 6's observatory report showed that structural recurrence
  evidence already existed in stored fields (5× `/stream alpha alpha
  alpha` produced 5 identical-text chunks and 5 distinct candidate
  ids; alternation, novelty after repetition, contradiction
  pressure, and saturation behaved as bounded text evidence with
  no truth, agency, or PtCns mutation).
- Step 11 added the session-local Pattern Ledger and aggregated
  recurrence into a deterministic, copy-on-write, exact-`Fraction`
  developmental record. The ledger sits strictly below truth,
  agency, `PtCns`, `MSI`, and semantic interpretation (`I-PLEDGER-14`,
  `I-PLEDGER-15`); recurrence saturates at
  `STREAM_PATTERN_RECURRENCE_MAX` (`I-PLEDGER-06`); evidence lists
  cap independently at `PATTERN_LEDGER_EVIDENCE_MAX = 32`
  (`I-PLEDGER-11`); the entry cap is a hard refusal at
  `PATTERN_LEDGER_MAX_ENTRIES = 64` with no eviction
  (`I-PLEDGER-12`).
- The optional `/pattern-ledger` operator UI remains deferred
  (`I-PLEDGER-17` DEFERRED); operators inspect ledger state through
  the session field or future read-only commands. Pattern Ledger
  end-to-end dry run remains `NOT-EXERCISED` (`I-PLEDGER-18`).

### Growing

- Step 6 showed bounded growth: only successful `/step` adds a
  content to `profile.domain` / `msi.contents` / registry and
  advances `tick_counter`. Save/load round-trips every recorded
  field; failure paths do not inflate growth.
- Pattern Ledger adds bounded structural recurrence growth: the
  `observe(...)` entry point is the sole non-construction mutation
  surface, it is invoked exactly once per successful `/stream`
  append (`I-PLEDGER-13`), and it never enters the `tick()` route.
  Saturation, duplicate-evidence filtering, and the entry cap
  collectively defeat anti-Goodhart inflation.
- Growth Ledger is not implemented. Step 15 produced
  `PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md`, which defines a
  bounded developmental record of accepted growth events keyed off
  the existing outcome-detection contract (Phase 3.10c autosave
  precedent). Step 16 deferred implementation to a follow-up
  Phase 3.13 campaign.

### Operational-I roadmap

- Operational SelfModel is not implemented. The roadmap defines a
  bounded read-only quotation record anchored to `COGITO_ID`,
  consuming bounded counts from the kernel, the operator session,
  the Pattern Ledger, the Coherence Monitor's overall status, and
  the future Growth Ledger's accepted-event counts. The record
  forbids subjective / semantic / truth / agency / self-modification
  language and any scalar purporting to summarize interior state.
- The roadmap recommends implementing Growth Ledger first, then
  SelfModel, so SelfModel can quote stable accepted-event facts
  rather than invent growth from the current state alone. Step 16
  accepted that recommendation: implementation is deferred to a
  follow-up campaign.

## Pattern Ledger Audit

```text
Catalog version when patch landed:   v0.21
Row family:                          I-PLEDGER-01..18
Per-status totals (Option A as accepted at Review Gate B):
  REQUIRED      : 15  (I-PLEDGER-01..15)
  STRUCTURAL    :  1  (I-PLEDGER-16)
  DEFERRED      :  1  (I-PLEDGER-17 — /pattern-ledger UI)
  NOT-EXERCISED :  1  (I-PLEDGER-18 — end-to-end dry run)
  OBSERVED      :  0
  Total new rows: 18
Implementation scope:
  - Option A: session-local only.
  - No DB schema change; SCHEMA_VERSION unchanged.
  - No /pattern-ledger UI in v1.
  - No end-to-end observed dry run in v1.
  - Successful /stream append observes exactly once.
  - No /step / no tick() mutation through the ledger.
  - No LLM coupling.
  - No truth / agency / semantic claims; no aggregate "I-ness" scalar.
```

Step 11 accepted deviation (documented in
`PHASE3_12_COHERENCE_MONITOR_CATALOG_PATCH_PLAN.md`):

- `brain/ui/fixtures/persistence_observe_resource_audit.py` and
  `brain/ui/fixtures/persistence_ops_resource_audit.py` gained a
  Phase 3.12c attribute tier
  (`_PHASE_3_12C_SESSION_ATTRS = frozenset({"pattern_ledger"})`)
  authorizing the catalog-blessed `OperatorSession.pattern_ledger`
  field against the `I-OBSERVE-08` / `I-OPSHARDEN-13` audits.
- Accepted as justified: it mirrors the documented Phase 3.10c
  precedent in the same fixtures and changed no runtime behavior.
  Positive resource-shape validation of `pattern_ledger` is owned
  by `I-PLEDGER-16` (STRUCTURAL — Pattern Ledger records carry no
  callable / handle / client field).

## Coherence Monitor Audit

```text
Catalog version when patch landed:   v0.22
Row family:                          I-COHMON-01..14
Per-status totals (Option A as accepted at Review Gate C):
  REQUIRED      : 11  (I-COHMON-01..11)
  STRUCTURAL    :  1  (I-COHMON-12)
  DEFERRED      :  1  (I-COHMON-13 — /coherence-summary UI)
  NOT-EXERCISED :  1  (I-COHMON-14 — end-to-end dry run)
  OBSERVED      :  0
  Total new rows: 14
Implementation scope:
  - Option A: pure read-only helper / snapshot API.
  - No OperatorSession slot added.
  - No new OperatorCommand member.
  - No new LOCAL_COMMAND_VERBS entry.
  - No new ACTIVE_VIEWS value.
  - No /coherence-summary UI in v1.
  - No end-to-end observed dry run in v1.
  - No DB open, no save_session / load_session / db_backup / db_verify
    / maybe_autosave_after_mutation call.
  - No tick() call.
  - No LLM coupling.
  - No non-claim term in module source, in CoherenceCheck templates,
    or in CoherenceReport.summary_text (case-insensitive static +
    runtime audits).
```

## SelfModel + Growth Ledger Roadmap Audit

```text
Artifact:                            PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
Scope:                               Roadmap / design documentation only.
Code changes:                        none.
Catalog changes:                     none.
Runtime behavior changes:            none.
Sequencing recommendation:           Growth Ledger first, SelfModel second.
Step 16 decision:                    ACCEPT ROADMAP AND DEFER
                                     IMPLEMENTATION TO FUTURE CAMPAIGN.
                                     Implementation is rolled into a
                                     follow-up Phase 3.13 Growth
                                     Ledger campaign that references
                                     this roadmap as canonical design
                                     source.
```

## Validation Results

Preflight commands executed at the start of Step 17 (no source under
`brain/**`, `tools/**`, `INVARIANT_CATALOG.md`, `README.md`,
`CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`, `lean_reference/**`,
`scenarios/**`, or `traces/**` was touched at this point):

| Command | Result | Salient output |
|---------|--------|----------------|
| `python3 -m tools.catalog counts` | PASS | `REQUIRED 240/240/240 ok`, `STRUCTURAL 85/85/85 ok`, `NOT-EXERCISED 11/11/11 ok`, `DEFERRED 14/14/14 ok`, `OBSERVED 16/16/16 ok` |
| `python3 -m tools.citations verify` | PASS | `Verified 100 citations. All catalog citations resolve in lean_reference/.` |
| `python3 -m tools.import_audit` | PASS | `I-PCE-05: agency.py is clean of pce imports.` |
| `python3 -m brain.invariants run` | PASS | `333 rows checked · REQUIRED green: 241 · REQUIRED red: 0 · STRUCTURAL green: 85 · STRUCTURAL red: 0 · OBSERVED: 7 pass / 0 fail · gate failures: 0` |
| `bash tools/check_all.sh` | PASS | `All checks passed.` (catalog IDs freshness · counts · citations · import audit · invariant runner — all five steps green.) |

The invariant runner reports 241 REQUIRED-green vs the catalog's
240 REQUIRED count because one REQUIRED row (`I-OPSHARDEN-03`) is
covered by two fixtures, both reporting green; the strict counts gate
remains satisfied at 240. The Operator-TUI argparse smoke fixtures
intentionally exercise the mutually-exclusive `--db-status` /
`--db-verify` / `--db-backup` short-circuit flags and print argparse
usage lines as part of their checks; those are expected fixture
output, not failures.

## Scope / Diff Audit

Phase 3.12 changed the following categories of files.

Documentation / campaign artifacts:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_12_COHERENT_I_LOOP_ROADMAP.md
PHASE3_12_COHERENT_I_LOOP_SYNTHESIS.md
PHASE3_12_COHERENT_I_LOOP_KICKOFF.md
PHASE3_12_COHERENT_I_LOOP_MATRIX.md
PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md
PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md
PHASE3_12_PATTERN_LEDGER_KICKOFF.md
PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md
PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md
PHASE3_12_COHERENCE_MONITOR_SYNTHESIS.md
PHASE3_12_COHERENCE_MONITOR_CATALOG_PATCH_PLAN.md
PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
PHASE3_12_COHERENT_I_LOOP_AUDIT.md           (this file, Step 17)
```

Catalog / version artifacts:

```text
INVARIANT_CATALOG.md                          (v0.20 -> v0.21 -> v0.22; +I-PLEDGER-* and +I-COHMON-* rows)
brain/_catalog_ids.py                         (regenerated by tools.catalog generate-ids)
tools/catalog.py                              (EXPECTED_COUNTS bumped for v0.21 and v0.22)
README.md                                     (catalog banner v0.20 -> v0.22; version history entries)
```

Runtime / development substrate:

```text
brain/development/pattern_ledger.py           (new module, Step 11)
brain/development/coherence_monitor.py        (new module, Step 14)
```

Fixtures:

```text
brain/development/fixtures/pattern_ledger_constructor.py
brain/development/fixtures/pattern_ledger_signature_id.py
brain/development/fixtures/pattern_ledger_observe.py
brain/development/fixtures/pattern_ledger_static_audit.py
brain/development/fixtures/pattern_ledger_no_runtime_coupling.py
brain/development/fixtures/pattern_ledger_stream_integration.py
brain/development/fixtures/coherence_monitor_constructor.py
brain/development/fixtures/coherence_monitor_kernel_checks.py
brain/development/fixtures/coherence_monitor_session_checks.py
brain/development/fixtures/coherence_monitor_pattern_ledger_checks.py
brain/development/fixtures/coherence_monitor_no_runtime_coupling.py
brain/development/fixtures/coherence_monitor_static_audit.py
brain/ui/fixtures/persistence_observe_resource_audit.py    (Step 11 deviation: Phase 3.12c attribute tier added)
brain/ui/fixtures/persistence_ops_resource_audit.py        (Step 11 deviation: Phase 3.12c attribute tier added)
```

Operator session integration (Step 11 only):

```text
brain/ui/session.py
  - import of PatternLedger from brain.development.pattern_ledger
  - "pattern_ledger" added to _ALLOWED_SESSION_ATTRS
  - new OperatorSession field: pattern_ledger: PatternLedger = field(default_factory=PatternLedger)
  - constructor self-audit accepts pattern_ledger
  - one observe(...) call at the end of the successful path of _dispatch_stream_append
  - no other dispatcher modified
```

Explicitly untouched categories across Phase 3.12:

```text
brain/tick.py                                 untouched
brain/llm/**                                  untouched
brain/ui/persistence.py                       untouched
brain/ui/persistence_ops.py                   untouched
brain/ui/persistence_observe.py               untouched
brain/ui/autosave.py                          untouched
brain/ui/commands.py                          untouched (no new OperatorCommand member)
brain/ui/command_line.py                      untouched (no new verb)
brain/ui/render.py                            untouched
brain/ui/snapshot.py                          untouched (ACTIVE_VIEWS unchanged)
brain/development/text_stream.py              untouched (only bounded constants reused)
DB schema                                     untouched
SCHEMA_VERSION_V*                             unchanged
lean_reference/**                             untouched
scenarios/**                                  untouched
traces/**                                     untouched
```

No real LLM-backed command was required for Phase 3.12; offline
remained the default throughout, and the optional real ORS smoke
from Phase 3.11 remains deferred unless separately authorized.

## Deferred Items

Carried forward out of Phase 3.12, all behind explicit review gates
or follow-up campaigns:

```text
/pattern-ledger UI                             I-PLEDGER-17 DEFERRED
Pattern Ledger end-to-end observed dry run     I-PLEDGER-18 NOT-EXERCISED
/coherence-summary UI                          I-COHMON-13 DEFERRED
Coherence Monitor end-to-end observed dry run  I-COHMON-14 NOT-EXERCISED
Growth Ledger campaign                         Phase 3.13 (recommended)
Operational SelfModel campaign                 follows Growth Ledger
Real external LLM ORS smoke from Phase 3.11    deferred unless separately authorized
SQLite-backup wording refresh                  inherited Phase 3.11 follow-up; deferred
```

## Risks / Follow-up Recommendations

- **Phase 3.13 should start with Growth Ledger, not SelfModel.** The
  roadmap rationale is that SelfModel should quote stable
  accepted-event facts; building it before Growth Ledger forces it
  to invent a growth signal (cognitive-layer scope creep) or to be
  re-shaped a second time once Growth Ledger lands.
- **Growth Ledger should remain session-local first unless
  explicitly reviewed.** Mirrors LOCK B from the Pattern Ledger
  corrigenda. Persisting on the first patch doubles the
  implementation surface and risks `SCHEMA_VERSION_V*` churn.
- **SelfModel should consume Growth Ledger + Coherence Monitor
  facts, not invent self-claims.** Per the roadmap, every SelfModel
  field is a quote from an existing bounded record; no aggregate
  scalar; no subjective / semantic / truth / agency language.
- **A follow-up UX campaign may be warranted for read-only operator
  views once substrates stabilize.** Both `/pattern-ledger` and
  `/coherence-summary` remain DEFERRED rows that can be promoted to
  REQUIRED by a small reviewed catalog patch when the operator
  decides the UI affordance is load-bearing.
- **The inherited Phase 3.11 wording refresh for SQLite backup API
  semantics** ("SQLite backup API copy, not byte-identical file
  clone") remains an open documentation-only follow-up. Phase 3.12
  did not address it; Phase 3.13 may pick it up.

## Final Verdict

```text
PASS WITH DEFERRED FOLLOW-UPS
```

Reasoning:

- All hard gates green (`tools.catalog counts`, `tools.citations
  verify`, `tools.import_audit`, `brain.invariants run`,
  `tools/check_all.sh`).
- Pattern Ledger (Step 11) and Coherence Monitor (Step 14) landed
  within their reviewed Option A scopes; the one accepted Step 11
  deviation is documented and changed no runtime behavior.
- The mission's measurement-first targets (coherent, growing,
  pattern-recognizing, operational-I roadmap) are met to the extent
  bounded substrates can support them; the deferred items above are
  intentional review-gated deferrals, not failures.
- No catalog row reports red. No correctness or safety finding was
  observed by the Step 6 observatory, by the Step 11 implementation,
  by the Step 14 implementation, or by the Step 17 preflight.

## Next Step

```text
Step 18 Final PR preparation.
```

Step 18 opens a PR to `main` with title
`phase3.12: coherent i-loop observatory`. The PR body must summarize
completed steps, validation results, behavior findings, review gates
reached (A / B / C / D), the Pattern Ledger and Coherence Monitor
Option A implementations, the deferred follow-ups listed above, and
confirm that `main` was not pushed directly during campaign execution
and that the PR is not merged.

## Validation

Re-ran after writing this audit (only this new documentation file
was added; no source under `brain/**`, `tools/**`,
`INVARIANT_CATALOG.md`, `README.md`, `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**` was touched):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
