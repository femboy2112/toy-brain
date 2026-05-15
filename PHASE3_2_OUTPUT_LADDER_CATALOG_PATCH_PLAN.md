# PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md

## 1. Purpose

This document designs the future catalog v0.7 patch for Phase 3.2 Output
Ladder rows.

It is a planning artifact only. It does not apply catalog rows, edit
`tools/catalog.py`, add runtime modules, add fixtures, or change generated
catalog IDs.

Verdict:

```text
COHERENT - READY FOR REVIEW GATE
```

No unresolved blocker prevents a later accepted v0.7 catalog patch. The plan
keeps Phase 3.2 below language, below reflective agency, below Mode B, and
below Phase 3.3 worldlet semantics.

## 2. Baseline

Current catalog baseline is v0.6:

```text
REQUIRED:       92
STRUCTURAL:     20
NOT-EXERCISED:   3
DEFERRED:       12
OBSERVED:        2
```

The v0.7 Output Ladder patch proposed here adds:

```text
+7 REQUIRED
+4 STRUCTURAL
+0 NOT-EXERCISED
+0 DEFERRED
+1 OBSERVED
```

Expected v0.7 counts after the accepted patch:

```text
REQUIRED:       99
STRUCTURAL:     24
NOT-EXERCISED:   3
DEFERRED:       12
OBSERVED:        3
```

Total catalog table rows become `141` if no other rows are added or removed.

## 3. Row Family Thesis

The v0.7 row family should use `I-OUT-*` IDs.

Core commitments:

```text
output impulses are source-tagged
output echo enters output history but is not agency
one-off output noise does not become a pattern
repeated output impulses create OutputPattern
token candidates require recurrence and echo provenance
learned output tokens are still not language
proto-output-action readiness is local and OBSERVED only
output history cannot directly mutate TLICA runtime state
```

The word "correction" from earlier campaign notes is interpreted for v0.7 as
internal echo/provenance support, not teacher correction. Natural-language
teacher correction remains out of scope.

## 4. Proposed Rows

Add a new catalog section after the Phase 3.1 Osmotic Chamber rows and before
the Meta / runner integrity section:

```text
### Phase 3.2 Output Ladder developmental invariants
```

Rows:

| ID | Source | Proposition | Python assertion | Owning module | Fixture | Status |
|---|---|---|---|---|---|---|
| I-OUT-01 | Engineering hypothesis (Phase 3.2 Output Ladder) | `OutputImpulse` is a bounded printable output event below language and agency. | Construction requires non-empty printable output text, a printable impulse ID, and no reserved `COGITO_ID` target. | `brain/development/output.py` | `output_echo.py` | STRUCTURAL |
| I-OUT-02 | Engineering hypothesis (Phase 3.2 Output Ladder) | Output provenance reuses existing Phase 3.1 source kinds and exact confidence discipline. | Output provenance uses `FrameSourceKind` values from the existing enum and `Fraction` confidence in `[0, 1]`; no `OUTPUT_ECHO` enum member is introduced in v0.7. | `brain/development/output.py` | `output_echo.py` | STRUCTURAL |
| I-OUT-03 | Engineering hypothesis (Phase 3.2 Output Ladder) | Source-tagged output impulses can be recorded deterministically. | Appending an `OutputImpulse` to `OutputHistory` is copy-on-write / append-only and preserves source/provenance metadata exactly. | `brain/development/output.py` | `output_echo.py` | REQUIRED |
| I-OUT-04 | Engineering hypothesis (Phase 3.2 Output Ladder) | Output echo enters output history but is not agency. | Creating an output echo records the impulse and echo provenance without selecting an `Act`, constructing an `AgencyWitness`, claiming `PRESERVE`, or calling `tick()`. | `brain/development/output.py` | `output_echo.py` | REQUIRED |
| I-OUT-05 | Engineering hypothesis (Phase 3.2 Output Ladder) | Output echo objects carry no direct agency or runtime mutation handles. | `OutputEcho` / `OutputHistory` objects expose no `Act`, `ModeOp`, `AgencyWitness`, `PerceptEvent`, direct state-mutation callback, or feasible-PCE field. | `brain/development/output.py` | `output_echo.py` | STRUCTURAL |
| I-OUT-06 | Engineering hypothesis (Phase 3.2 Output Ladder) | One-off output noise does not become an output pattern. | A single output impulse leaves no `OutputPattern`, `OutputTokenCandidate`, or `LearnedOutputToken` in history. | `brain/development/output.py` | `output_pattern.py` | REQUIRED |
| I-OUT-07 | Engineering hypothesis (Phase 3.2 Output Ladder) | Repeated matching output impulses create or update an `OutputPattern`. | Two matching source-tagged output impulses deterministically create or update the same pattern ID with recurrence evidence. | `brain/development/output.py` | `output_pattern.py` | REQUIRED |
| I-OUT-08 | Engineering hypothesis (Phase 3.2 Output Ladder) | Token candidates require recurrence plus echo provenance. | `OutputTokenCandidate` construction rejects recurrent-only support, echo-only support, one-off support, missing provenance, and reserved identifiers. | `brain/development/output.py` | `output_token_candidate.py` | REQUIRED |
| I-OUT-09 | Engineering hypothesis (Phase 3.2 Output Ladder) | Learned output tokens remain below language. | `LearnedOutputToken` exposes stable token bookkeeping but no grammar, teacher-correction, world-reference, readability, social-meaning, or command-syntax fields. | `brain/development/output.py` | `output_token_candidate.py` | STRUCTURAL |
| I-OUT-10 | Engineering hypothesis (Phase 3.2 Output Ladder) | Learned output token construction requires token-candidate support and remains below runtime mutation. | A learned token can be created only from a valid `OutputTokenCandidate`; construction does not emit a `PerceptEvent`, call `tick()`, or mutate TLICA state. | `brain/development/output.py` | `output_token_candidate.py` | REQUIRED |
| I-OUT-11 | Engineering hypothesis (Phase 3.2 Output Ladder) | Proto-output-action readiness is inspectable but non-gating in v0.7. | The fixture records whether local output-history support would make a below-agency proto-output-action candidate plausible; the row is OBSERVED and cannot fail the runner. | `brain/development/output.py` | `output_token_candidate.py` | OBSERVED |
| I-OUT-12 | Engineering hypothesis (Phase 3.2 Output Ladder) | Output history cannot bypass the `PerceptEvent` / `tick()` boundary. | Before and after output impulse, echo, pattern, candidate, and learned-token construction, profile/MSI/PtCns/registry identities are unchanged. | `brain/development/output.py` | `output_echo.py` | REQUIRED |

## 5. Fixture Roster

Add three new fixture files under `brain/development/fixtures/`:

| Fixture | Drives invariant IDs | Implementation step |
|---|---|---|
| `output_echo.py` | I-OUT-01, I-OUT-02, I-OUT-03, I-OUT-04, I-OUT-05, I-OUT-12 | Step 7 |
| `output_pattern.py` | I-OUT-06, I-OUT-07 | Step 8 |
| `output_token_candidate.py` | I-OUT-08, I-OUT-09, I-OUT-10, I-OUT-11 (OBSERVED) | Step 8 / Step 9 |

The v0.7 fixture count becomes `24` total fixtures:

```text
21 existing v0.6 fixtures
+3 output-ladder fixtures
```

## 6. Owning Module Map

New runtime module:

```text
brain/development/output.py
```

This single module should host the v0.7 output-ladder surface:

```text
OutputImpulse
OutputProvenance
OutputEcho
OutputHistory
OutputPattern
OutputTokenCandidate
LearnedOutputToken
ProtoOutputActionReadiness
append_output_impulse
echo_output_impulse
update_output_pattern
maybe_create_output_token_candidate
learn_output_token
observe_proto_output_action_readiness
```

Do not create separate language, expression, worldlet, REPL, or Mode B modules
in v0.7.

Existing module reuse:

```text
brain/development/history.py        # ID type helpers and printable ID checks only
brain/development/stream.py         # FrameSourceKind / FrameSource discipline
brain/development/drives.py         # require_unit_fraction
brain/tick.py                       # read-only in Phase 3.2; do not edit
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

## 7. Catalog Patch Mechanics

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
1. Add a v0.7 catalog-version banner above the v0.6 banner.
2. Add the Phase 3.2 Output Ladder table with I-OUT-01..I-OUT-12.
3. Add the three output fixtures to the fixture roster.
4. Update the fixture-total text from 21 to 24.
5. Update summary counts to 99 / 24 / 3 / 12 / 3.
6. Update total tabular entries from 129 to 141.
```

Required Step 6 tooling edits:

```text
1. Update tools/catalog.py EXPECTED_COUNTS to:
   REQUIRED=99, STRUCTURAL=24, NOT-EXERCISED=3, DEFERRED=12, OBSERVED=3.
2. Update the nearby comment from v0.6 to v0.7.
3. Run python3 -m tools.catalog generate-ids.
```

Required Step 6 registry coherence:

```text
1. Add a _PHASE3_2_PENDING_ROWS map in brain/invariants.py for I-OUT rows
   with REQUIRED / STRUCTURAL status.
2. Pending checks must raise NotImplementedError if executed.
3. Do not register OBSERVED I-OUT-11 as a pending failing gate unless Step 6
   also gives it a harmless OBSERVED placeholder.
4. Do not claim any I-OUT row green in Step 6.
5. Do not add output runtime behavior in Step 6.
```

Reason:

`I-CAT-01` audits coverage from `brain/_catalog_ids.py`. After the catalog
patch, REQUIRED and STRUCTURAL `I-OUT-*` rows need registered entries so
coverage is coherent, but those entries must fail explicitly if run before
implementation. This mirrors the Phase 3.1 pending-registration pattern and
prevents fake green rows.

Step 6 validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Do not run `bash tools/check_all.sh` as a Step 6 success gate unless all pending
I-OUT rows have already been implemented; pending rows intentionally make the
full runner red until Step 7 / Step 8 / Step 9 replace them.

## 8. Strict Implementation Order

Step 6 - Apply accepted v0.7 catalog patch:

```text
catalog rows
expected counts
generated IDs
pending registrations only
no runtime behavior
```

Step 7 - Output echo and source-tag rows:

```text
Implement I-OUT-01, I-OUT-02, I-OUT-03, I-OUT-04, I-OUT-05, I-OUT-12.
Files:
  brain/development/output.py
  brain/development/fixtures/output_echo.py
  brain/invariants.py
  brain/_catalog_ids.py
Validation:
  python3 -m brain.invariants run --id I-OUT-01
  python3 -m brain.invariants run --id I-OUT-02
  python3 -m brain.invariants run --id I-OUT-03
  python3 -m brain.invariants run --id I-OUT-04
  python3 -m brain.invariants run --id I-OUT-05
  python3 -m brain.invariants run --id I-OUT-12
```

Step 8 - Output pattern and token candidate rows:

```text
Implement I-OUT-06, I-OUT-07, I-OUT-08, I-OUT-09, I-OUT-10.
Files:
  brain/development/output.py
  brain/development/fixtures/output_pattern.py
  brain/development/fixtures/output_token_candidate.py
  brain/invariants.py
Validation:
  python3 -m brain.invariants run --id I-OUT-06
  python3 -m brain.invariants run --id I-OUT-07
  python3 -m brain.invariants run --id I-OUT-08
  python3 -m brain.invariants run --id I-OUT-09
  python3 -m brain.invariants run --id I-OUT-10
```

Step 9 - Proto-output-action readiness:

```text
Implement I-OUT-11 as OBSERVED only.
Files:
  brain/development/output.py
  brain/development/fixtures/output_token_candidate.py
Validation:
  python3 -m brain.invariants run --id I-OUT-11
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
Write PHASE3_2_OUTPUT_LADDER_AUDIT.md after the full gate passes.
```

## 9. Design Decisions

These are resolved for v0.7:

```text
Use a separate OutputHistory object rather than extending SubstrateHistory.
Represent echo as provenance / event role, not as a new source enum member.
Reuse FrameSourceKind values from Phase 3.1.
Require recurrence plus echo provenance for token candidates.
Keep learned output tokens below language.
Keep proto-output-action readiness OBSERVED and local only.
Do not add worldlet consequence evidence in v0.7.
Do not add Proto-BASIC syntax, teacher correction, readability, social meaning,
or Mode B output behavior.
```

## 10. Open Decisions

No open decision blocks Step 6.

Deferred beyond v0.7:

```text
Whether Phase 3.3 worldlet evidence upgrades proto-output-action readiness.
Whether Proto-BASIC later introduces command syntax.
Whether teacher correction or social-language loops add new source/provenance
fields in a later phase.
Whether expression/readability requires a separate token surface after v0.7.
```

These are later-phase design questions, not blockers for the v0.7 catalog
patch.

## 11. Stop Conditions

Stop and report if any later step requires:

```text
editing brain/tlica/
editing lean_reference/
changing tick() semantics
changing scenario schema
running a real LLM scenario
adding worldlet consequence rules
adding Proto-BASIC syntax
adding natural-language teacher correction
adding Mode B reflective planning
claiming output echo as agency
claiming learned output tokens as language
making pending I-OUT rows pass without real fixture behavior
```

Step 5 is an explicit review gate. This plan is coherent and internally
complete, but the v0.7 catalog patch should not be applied until the user says
`go` again or explicitly accepts the plan.
