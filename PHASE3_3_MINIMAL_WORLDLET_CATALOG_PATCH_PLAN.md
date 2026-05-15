# PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md

## 1. Purpose

This document designs the future catalog v0.8 patch for Phase 3.3 Minimal
Worldlet rows.

It is a planning artifact only. It does not apply catalog rows, edit
`tools/catalog.py`, add runtime modules, add fixtures, change generated catalog
IDs, or change the TLICA runtime boundary.

Verdict:

```text
COHERENT - READY FOR REVIEW GATE
```

No unresolved blocker prevents a later accepted v0.8 catalog patch. The plan
keeps Minimal Worldlet below language, below reflective agency, below Mode B,
below real host execution, and below `PerceptEvent` / `tick()` promotion.

## 2. Baseline

Current catalog baseline is v0.7:

```text
REQUIRED:        99
STRUCTURAL:      24
NOT-EXERCISED:    3
DEFERRED:        12
OBSERVED:         3
```

The v0.8 Minimal Worldlet patch proposed here adds:

```text
+6 REQUIRED
+5 STRUCTURAL
+0 NOT-EXERCISED
+0 DEFERRED
+1 OBSERVED
```

Expected v0.8 counts after the accepted patch:

```text
REQUIRED:       105
STRUCTURAL:      29
NOT-EXERCISED:    3
DEFERRED:        12
OBSERVED:         4
```

Total catalog table rows become `153` if no other rows are added or removed.

## 3. Row Family Thesis

The v0.8 row family should use `I-WLD-*` IDs.

Core commitments:

```text
worldlet state and objects are finite deterministic records
worldlet valence is exact, bounded, and never silently clamped
worldlet provenance reuses existing source discipline without a new source enum
worldlet history is copy-on-write and append-only
worldlet responses are local consequence evidence, not runtime mutation
worldlet attempts require both ready readiness and learned-token support
worldlet attempts are not Act, ModeOp, AgencyWitness, PerceptEvent, or REPL
accepted/rejected/unavailable/missing-target outcomes are deterministic
negative responses are bounded evidence, not fear or avoidance pathology
not-I pushback is recorded as local harness evidence, not external reality
```

The Minimal Worldlet converts local proto-output readiness into bounded
consequence-bearing attempts only inside a deterministic harness. It must not
retrofit Phase 3.2 output readiness into agency, language, or world causality.

## 4. Proposed Rows

Add a new catalog section after the Phase 3.2 Output Ladder rows and before the
Meta / runner integrity section:

```text
### Phase 3.3 Minimal Worldlet developmental invariants
```

Rows:

| ID | Source | Proposition | Python assertion | Owning module | Fixture | Status |
|---|---|---|---|---|---|---|
| I-WLD-01 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | `WorldletState` and `WorldletObject` are finite deterministic records. | Construction requires printable IDs, finite object mappings, boolean availability, tuple/frozenset accepted-token surfaces, and deterministic object lookup for the same state and target. | `brain/development/worldlet.py` | `worldlet_state.py` | STRUCTURAL |
| I-WLD-02 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | `WorldletValence` is exact and bounded. | Construction requires a `Fraction` value satisfying `-1 <= value <= 1`; out-of-range values raise and no silent clamping occurs. | `brain/development/worldlet.py` | `worldlet_response.py` | REQUIRED |
| I-WLD-03 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | Worldlet provenance reuses existing source discipline. | `WorldletProvenance` uses `FrameSourceKind`, `Fraction` confidence in `[0, 1]`, printable trace event IDs, and introduces no worldlet-specific source enum member. | `brain/development/worldlet.py` | `worldlet_response.py` | STRUCTURAL |
| I-WLD-04 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | `WorldletHistory` appends attempts/responses copy-on-write. | Appending a worldlet attempt or response returns a new history, preserves prior attempts/responses exactly, and updates only local `latest_state`. | `brain/development/worldlet.py` | `worldlet_state.py` | REQUIRED |
| I-WLD-05 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | `WorldletResponse` is a source-tagged local consequence record. | A response carries printable response/attempt IDs, accepted flag, finite reason, bounded `WorldletValence`, and worldlet provenance, but no `PerceptEvent` or runtime callback. | `brain/development/worldlet.py` | `worldlet_response.py` | STRUCTURAL |
| I-WLD-06 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | Worldlet response/history operations do not mutate TLICA runtime state. | Before and after worldlet response and history operations, profile/MSI/PtCns/registry identities are unchanged and no `tick()` call or `PerceptEvent` emission occurs. | `brain/development/worldlet.py` | `worldlet_response.py` | REQUIRED |
| I-WLD-07 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | `WorldletAttempt` construction requires ready readiness plus registered learned-token support. | Construction rejects readiness-alone, incomplete readiness, missing `LearnedOutputToken`, mismatched token/pattern IDs, missing `OutputHistory` support, reserved IDs, and non-printable attempt/target IDs. | `brain/development/worldlet.py` | `worldlet_attempt.py` | REQUIRED |
| I-WLD-08 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | `WorldletAttempt` remains below agency, language, and REPL syntax. | Attempt objects expose no `Act`, `ModeOp`, `AgencyWitness`, `PerceptEvent`, selected action, feasible-projected-PCE field, grammar, command syntax, teacher-correction, or `tick` callback. | `brain/development/worldlet.py` | `worldlet_attempt.py` | STRUCTURAL |
| I-WLD-09 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | Accepted worldlet attempts produce deterministic bounded responses. | For an available target whose accepted-token set contains the attempt token, `respond_worldlet` returns a deterministic accepted response with positive bounded valence and advances only local worldlet state/history. | `brain/development/worldlet.py` | `worldlet_consequence.py` | REQUIRED |
| I-WLD-10 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | Rejected, unavailable, and missing-target valid attempts produce bounded negative responses. | A valid constructed attempt against a rejecting target, unavailable target, or missing target returns a deterministic response with negative bounded valence instead of mutating TLICA state or raising after construction. | `brain/development/worldlet.py` | `worldlet_consequence.py` | REQUIRED |
| I-WLD-11 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | Not-I pushback is local response evidence, not an external reality claim. | Pushback fixtures assert response reasons and provenance remain local harness evidence and expose no external-world truth, social teacher, language-understanding, affect-taxonomy, free-will branch, or Mode B planning fields. | `brain/development/worldlet.py` | `worldlet_consequence.py` | STRUCTURAL |
| I-WLD-12 | Engineering hypothesis (Phase 3.3 Minimal Worldlet) | Aggregate local consequence history is inspectable. | The fixture records accepted/rejected/unavailable/missing-target response summaries for inspection; the row is OBSERVED and cannot fail the runner. | `brain/development/worldlet.py` | `worldlet_consequence.py` | OBSERVED |

## 5. Deterministic Convention

The first implementation should keep consequence values simple and exact:

```text
accepted target accepts token:      Fraction(1, 2)
target rejects token:               Fraction(-1, 2)
target unavailable:                 Fraction(-1, 2)
target missing:                     Fraction(-1, 2)
```

These values are local harness evidence only. They do not claim affect
taxonomy, fear, avoidance, reward learning, external-world truth, or runtime
self-model update.

State transition convention:

```text
respond_worldlet(state, attempt) -> (next_state, response)
next_state.objects == state.objects
next_state.step_index == state.step_index + 1
next_state.state_id is deterministically derived or explicitly supplied by the
worldlet implementation
```

The response and next state may be appended only to `WorldletHistory`.

## 6. Fixture Roster

Add four new fixture files under `brain/development/fixtures/`:

| Fixture | Drives invariant IDs | Implementation step |
|---|---|---|
| `worldlet_state.py` | I-WLD-01, I-WLD-04 | Step 7 |
| `worldlet_response.py` | I-WLD-02, I-WLD-03, I-WLD-05, I-WLD-06 | Step 7 |
| `worldlet_attempt.py` | I-WLD-07, I-WLD-08 | Step 8 |
| `worldlet_consequence.py` | I-WLD-09, I-WLD-10, I-WLD-11, I-WLD-12 (OBSERVED) | Step 8 / Step 9 |

The v0.8 fixture count becomes `28` total fixtures:

```text
24 existing v0.7 fixtures
+4 worldlet fixtures
```

## 7. Owning Module Map

New runtime module:

```text
brain/development/worldlet.py
```

This single module should host the v0.8 worldlet surface:

```text
WorldletID aliases
WorldletProvenance
WorldletValence
WorldletObject
WorldletState
WorldletAttempt
WorldletResponse
WorldletHistory
append_worldlet_attempt
append_worldlet_response
construct_worldlet_attempt
respond_worldlet
summarize_worldlet_history
```

Existing module reuse:

```text
brain/development/output.py        # OutputHistory, LearnedOutputToken, ProtoOutputActionReadiness
brain/development/history.py       # printable ID / TraceEventID helpers
brain/development/stream.py        # FrameSourceKind source discipline
brain/development/drives.py        # require_unit_fraction for provenance confidence
brain/tick.py                      # read-only in Phase 3.3; do not edit
```

Guarded modules remain untouched:

```text
brain/tlica/
lean_reference/
traces/
scenarios/
brain/tick.py
brain/llm/
```

## 8. Catalog Patch Mechanics

When the user accepts this plan and says `go`, Step 6 should apply only the
catalog patch and coherence scaffolding.

Allowed Step 6 edits:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/development/fixtures/__init__.py
```

Required Step 6 catalog edits:

```text
1. Add a v0.8 catalog-version banner above the v0.7 banner.
2. Add the Phase 3.3 Minimal Worldlet table with I-WLD-01..I-WLD-12.
3. Add the four worldlet fixtures to the fixture roster.
4. Update the fixture-total text from 24 to 28.
5. Update summary counts to 105 / 29 / 3 / 12 / 4.
6. Update total tabular entries from 141 to 153.
```

Required Step 6 tooling edits:

```text
1. Update tools/catalog.py EXPECTED_COUNTS to:
   REQUIRED=105, STRUCTURAL=29, NOT-EXERCISED=3, DEFERRED=12, OBSERVED=4.
2. Update the nearby comment from v0.7 to v0.8.
3. Run python3 -m tools.catalog generate-ids.
```

Required Step 6 registry coherence:

```text
1. Add a _PHASE3_3_PENDING_ROWS map in brain/invariants.py for I-WLD REQUIRED
   and STRUCTURAL rows.
2. Pending checks must raise NotImplementedError if executed.
3. Do not register I-WLD-12 as a pending failing gate. It is OBSERVED and does
   not participate in I-CAT-01 coverage.
4. Do not claim any I-WLD row green in Step 6.
5. Do not add worldlet runtime behavior in Step 6.
6. Do not add missing worldlet fixture modules to FIXTURE_MODULES until the
   corresponding fixture files exist.
```

The pending map should include:

```text
I-WLD-01 STRUCTURAL
I-WLD-02 REQUIRED
I-WLD-03 STRUCTURAL
I-WLD-04 REQUIRED
I-WLD-05 STRUCTURAL
I-WLD-06 REQUIRED
I-WLD-07 REQUIRED
I-WLD-08 STRUCTURAL
I-WLD-09 REQUIRED
I-WLD-10 REQUIRED
I-WLD-11 STRUCTURAL
```

Reason:

`I-CAT-01` audits coverage from `brain/_catalog_ids.py`. After the catalog
patch, REQUIRED and STRUCTURAL `I-WLD-*` rows need registered entries so
coverage is coherent, but those entries must fail explicitly if run before
implementation. This prevents fake green rows and avoids missing-registration
confusion.

Step 6 validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Do not run `bash tools/check_all.sh` as a Step 6 success gate unless all
pending I-WLD rows have already been implemented; pending rows intentionally
make the full runner red until Step 7 / Step 8 / Step 9 replace them.

## 9. Strict Implementation Order

Step 6 - Apply accepted v0.8 catalog patch:

```text
catalog rows
expected counts
generated IDs
pending registrations only
no runtime behavior
```

Step 7 - Worldlet state and response boundary rows:

```text
Implement I-WLD-01, I-WLD-02, I-WLD-03, I-WLD-04, I-WLD-05, I-WLD-06.
Files:
  brain/development/worldlet.py
  brain/development/fixtures/worldlet_state.py
  brain/development/fixtures/worldlet_response.py
  brain/invariants.py
  brain/_catalog_ids.py
Validation:
  python3 -m brain.invariants run --id I-WLD-01
  python3 -m brain.invariants run --id I-WLD-02
  python3 -m brain.invariants run --id I-WLD-03
  python3 -m brain.invariants run --id I-WLD-04
  python3 -m brain.invariants run --id I-WLD-05
  python3 -m brain.invariants run --id I-WLD-06
```

Step 8 - Worldlet attempt and consequence rows:

```text
Implement I-WLD-07, I-WLD-08, I-WLD-09, I-WLD-10.
Files:
  brain/development/worldlet.py
  brain/development/fixtures/worldlet_attempt.py
  brain/development/fixtures/worldlet_consequence.py
  brain/invariants.py
Validation:
  python3 -m brain.invariants run --id I-WLD-07
  python3 -m brain.invariants run --id I-WLD-08
  python3 -m brain.invariants run --id I-WLD-09
  python3 -m brain.invariants run --id I-WLD-10
```

Step 9 - Not-I pushback / local evidence rows:

```text
Implement I-WLD-11 and I-WLD-12.
Files:
  brain/development/worldlet.py
  brain/development/fixtures/worldlet_consequence.py
  brain/invariants.py
Validation:
  python3 -m brain.invariants run --id I-WLD-11
  python3 -m brain.invariants run --id I-WLD-12
```

Step 10 - Full gate:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Step 11 - Audit:

```text
Write PHASE3_3_MINIMAL_WORLDLET_AUDIT.md after the full gate passes.
```

## 10. Design Decisions

These are resolved for v0.8:

```text
Use a separate brain/development/worldlet.py module.
Keep WorldletObject in scope because the finite target surface is needed for
accepted/rejected/unavailable/missing-target cases.
Use WorldletProvenance with the same validation discipline as OutputProvenance,
not a new source-kind enum.
Require WorldletAttempt construction to check OutputHistory, readiness, and
LearnedOutputToken support together.
Treat readiness alone as insufficient for attempt construction.
Keep invalid attempt objects as constructor errors.
Treat valid rejected/unavailable/missing-target attempts as bounded negative
WorldletResponse records.
Keep not-I pushback as local deterministic harness response evidence.
Keep aggregate consequence history OBSERVED only.
Do not emit PerceptEvent or call tick() from worldlet operations.
Do not introduce Proto-BASIC grammar, REPL syntax, host execution, teacher
correction, expression/readability, social/language behavior, or Mode B.
```

## 11. Open Decisions

No open decision blocks Step 6.

Deferred beyond v0.8:

```text
Whether a later phase can promote selected worldlet evidence into PerceptEvent.
Whether Proto-BASIC command syntax can address worldlet targets.
Whether expression/readability layers inspect worldlet history.
Whether a social/language harness adds teacher correction or external feedback.
Whether Mode B later inspects aggregate worldlet consequence history.
Whether worldlet rules eventually mutate object availability or richer object
state beyond the Step 3.3 step-index transition.
```

These are later-phase design questions, not blockers for the v0.8 catalog
patch.

## 12. Stop Conditions

Stop and report if any later step requires:

```text
editing brain/tlica/
editing lean_reference/
changing tick() semantics
changing scenario schema
running a real LLM scenario
emitting PerceptEvent from worldlet evidence
adding Proto-BASIC syntax
adding open-ended host execution
adding natural-language teacher correction
adding expression/readability behavior
adding social/language exchange
adding Mode B reflective planning
claiming worldlet response as agency
claiming not-I pushback as external reality
claiming learned output tokens as language
making pending I-WLD rows pass without real fixture behavior
```

Step 5 is an explicit review gate. This plan is coherent and internally
complete, but the v0.8 catalog patch should not be applied until the user says
`go` again or explicitly accepts the plan.
