# PHASE3_5_EXPRESSION_READABILITY_AUDIT.md

## Verdict

```text
PASS
```

The Phase 3.5 Expression + ReadabilityPredictor campaign landed the accepted
catalog patch (v0.12) and the corresponding runtime layer without scope creep
or kernel-boundary breach. All 16 registered `I-EXP-*` rows are green, the
full gate is green, and the OBSERVED / NOT-EXERCISED rows are documented
rather than promoted.

## Scope of audit

- v0.12 catalog patch (`I-EXP-01..I-EXP-18`)
- `brain/development/expression.py` (production module)
- Phase 3.5 fixture files under `brain/development/fixtures/`
- pending-row drain in `brain/invariants.py`
- guardrails and stop conditions enumerated in
  `PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md` section 13

## 1. Scope creep

```text
No
```

The implementation:

- did not call any real LLM client
- did not introduce a social/language harness
- did not introduce a natural-language teacher/corrector
- did not introduce Mode B reflective planning
- did not call host execution, subprocess, shell, or network I/O
- did not write any file outside the repository tree
- did not change scenario, trace, or catalog schemas
- did not authorize a UI inspection pane (Step 10 was SKIPPED per
  `C10-AMEND-01`)
- did not promote any expression evidence through `PerceptEvent` or `tick()`
- did not mutate `BrainState`, `ScalarProfile`, `MSI`, `PtCns`,
  `ContentRegistry`, `OutputHistory`, `WorldletHistory`,
  `ProtoBasicHistory`, or `OperatorTranscript`
- did not add an external dependency (standard library only)

`brain/development/expression.py` imports only `dataclasses`, `enum`,
`fractions`, `types`, `typing`, and `brain.development.history`. The static
audit fixture (`expression_static_audit.py`) AST-checks for forbidden
imports (`os`, `subprocess`, `socket`, `urllib`, `http`, `requests`,
`pathlib`, `tempfile`, `shutil`, `curses`, `brain.llm`, `brain.tlica`,
`brain.tick`) and for `float` / `round` / `math.*` calls on the score path,
and passes.

## 2. Row registration

```text
Catalog rows added: 18 (I-EXP-01..I-EXP-18)
  +12 REQUIRED  (I-EXP-01..I-EXP-12)
   +4 STRUCTURAL (I-EXP-13..I-EXP-16)
   +1 OBSERVED   (I-EXP-17 — documentation-only; no registered check)
   +1 NOT-EXERCISED (I-EXP-18 — placeholder for write-to-disk policy)

Registered runtime checks: 16
  I-EXP-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 (REQUIRED)
  I-EXP-13, 14, 15, 16 (STRUCTURAL)

I-CAT-01 audit: pass (REQUIRED ∪ STRUCTURAL ⊆ registered)
_PHASE3_5_PENDING_ROWS: empty
```

`tools.catalog counts` confirms banner = actual = expected for all five
status buckets at the v0.12 expansion (`139 / 48 / 5 / 12 / 8`).

## 3. Expression vs language distinction

```text
Maintained
```

`brain/development/expression.py` exposes:

- no grammar, parser, lexicon, syntax tree, dialogue state, utterance,
  speaker model, intent classifier, or natural-language teacher
- no `LanguageModel`, `ChatHistory`, `Message`, `Speaker`, or
  `Conversation` type
- only bounded local printable text records (`ExpressionItem`) and
  numeric feature vectors (`ExpressionFeatureVector`)

The predictor docstring states explicitly: *"This module computes a
bounded structural score over a local expression item. It does NOT model
language."* This sentence is also pinned in catalog row I-EXP-04.

## 4. Readability vs truth, social success, agency distinction

```text
Maintained
```

`ReadabilityScore` is a bounded `Fraction` in `[0, 1]` and is computed
deterministically from `ExpressionFeatureVector`. It is not derived from:

- a ground-truth source
- a teacher or corrector
- a social register
- a feasibility check against external reality
- a model of intent, will, or agency
- any TLICA construct (`Act`, `ModeOp`, `AgencyWitness`, `PerceptEvent`,
  `feasibleProjectedPCE`, `tick`)

The score's docstring and the I-EXP-04 row description both repeat the
non-truth / non-language disclaimer.

## 5. Score boundedness

```text
Maintained
```

`ReadabilityScore.__post_init__` rejects:

- non-`Fraction` values (including `int`, `float`, `str`)
- values strictly below `Fraction(0)`
- values strictly above `Fraction(1)`

with `I-EXP-04`-tagged `TypeError` / `ValueError`. `predict_readability`
clamps the combined sum with explicit `Fraction(0)` / `Fraction(1)`
bounds before constructing the score, so the score path cannot leak
out-of-range values into `ReadabilityScore.__post_init__`.

The static audit `I-EXP-16` confirms the score path uses only `int` and
`Fraction` arithmetic — no `float`, no `round`, no `math.*` calls — and
that the module does not import `math`.

## 6. Anti-Goodhart behavior

```text
Maintained
```

| Anti-Goodhart rule | Fixture | Result |
|---|---|---|
| Empty / whitespace-only text scores `Fraction(0)` | `readability_predictor_empty_item.py` (I-EXP-09) | PASS |
| Repetition alone never raises the score above the single-instance baseline | `readability_predictor_repetition_only.py` (I-EXP-10) | PASS |
| Length alone is capped at `LENGTH_SATURATION_BOUND` (= 64 tokens) | `readability_predictor_length_cap.py` (I-EXP-11) | PASS |
| Predictor is deterministic across repeated calls | `readability_predictor_determinism.py` (I-EXP-12) | PASS |

The length-cap fixture uses fixed-length 2-character distinct tokens so
the saturation probe isolates the length component from changes in the
shape component (a probe-engineering correction from the first
implementation draft).

## 7. History locality

```text
Maintained
```

`ExpressionHistory` is a frozen dataclass with a `tuple[ExpressionRecord, ...]`
field. `append` is copy-on-write and bounded by
`EXPRESSION_HISTORY_MAX_ENTRIES` (= 256); over-bound appends drop the oldest
record. Direct construction with > 256 records raises with an
`I-EXP-06`-tagged `ValueError`. The history holds no callable, file handle,
socket, LLM client, or path object.

`expression_no_brainstate_mutation.py` (I-EXP-07) and
`expression_no_source_history_mutation.py` (I-EXP-08) confirm that every
expression operation (`extract_features`, `predict_readability`,
`make_expression_record`, bridge constructors, `ExpressionHistory.append`)
leaves the kernel containers and the source histories
(`OutputHistory` / `WorldletHistory` / `ProtoBasicHistory` /
`OperatorTranscript`) bit-for-bit unchanged.

`I-EXP-17` (OBSERVED) is satisfied by `summarize_expression_history` which
produces an `ExpressionHistorySummary` of exact `Fraction` statistics over
the local history. The summary view is read-only and is documented here
rather than being driven by a registered runner check (per
`I-EXP-17 Fixture: (none)`).

`I-EXP-18` (NOT-EXERCISED) remains a policy placeholder: no
`ExpressionHistory` write-to-disk path exists in this campaign, and any
future write path requires reviewed policy, dedicated rows, fixtures
under bounded conditions, and a stop condition.

## 8. Kernel boundary

```text
Maintained
```

Phase 3.5 evidence flows strictly one-way:

```text
OutputHistory / WorldletHistory / ProtoBasicHistory / OperatorTranscript
    -> ExpressionRecord / ReadabilityPrediction
    -> local ExpressionHistory only
```

The reverse path is closed:

```text
ExpressionHistory -> BrainState / MSI / PtCns / registry / tick /
                     PerceptEvent / traces / scenarios   NOT ALLOWED
```

No new `brain/tick.py`, `brain/tlica/`, or `brain/llm/` content was
modified. The fixture for I-EXP-07 explicitly snapshots
`state.profile.values`, `state.msi.contents`, `state.ptcns.positive_contents`,
and `state.registry.texts` before and after running expression operations
and asserts equality.

## 9. Full gate

```text
python3 -m tools.catalog counts        ->  139 / 48 / 5 / 12 / 8  ok
python3 -m tools.citations verify      ->  100 citations resolved
python3 -m tools.import_audit          ->  I-PCE-05 clean
bash tools/check_all.sh                ->  194 rows checked
                                          REQUIRED green:   139 / 139
                                          STRUCTURAL green:  48 / 48
                                          OBSERVED pass:      7 / 0 fail
                                          gate failures:      0
                                          all checks passed
```

The 7-vs-8 OBSERVED count is by design: `I-EXP-17` is documentation-only
and not registered, so seven OBSERVED rows appear in the run summary.

## 10. Hard-boundary file audit

```text
brain/tlica/          unchanged
lean_reference/       unchanged
traces/               unchanged
scenarios/            unchanged
brain/tick.py         unchanged
brain/llm/            unchanged
brain/ui/             unchanged (Step 10 SKIPPED per C10-AMEND-01)
```

`git log` shows the Phase 3.5 commits touched only:

- `INVARIANT_CATALOG.md`
- `tools/catalog.py`
- `brain/_catalog_ids.py`
- `brain/invariants.py`
- `brain/development/expression.py`
- `brain/development/fixtures/*.py` (13 new files)
- `PHASE3_5_*.md` planning docs (Steps 1–5)

## 11. Patches landed during the campaign

Two probe corrections were made during implementation; both are visible
in the working tree and in the committed fixtures:

```text
fix(I-EXP-09): replace tab characters with space characters in the
               whitespace probe set so the ExpressionItem.text validator
               (which uses str.isprintable() — rejects tabs) does not
               short-circuit the score check
fix(I-EXP-11): switch the length-saturation probe to fixed-length
               2-character distinct tokens so the shape component stays
               constant across saturation/over-saturation and the length
               cap is isolated
```

Neither correction changed catalog rows, row IDs, statuses, count
expectations, or hard boundaries.

## 12. Recommended next mission

`Phase 3.6 Reflective Inspection (operator-facing summary view, no UI
integration of Phase 3.5)`

Rationale: with bottom-up developmental layers Phase 3.1–3.5 landed and
local-only, the next pre-Mode-B campaign that does not require external
language, social communication, or real LLM is a reflective inspection
layer that summarizes developmental histories (output / worldlet /
proto-basic / expression) into a single read-only inspectable record,
deferring any UI surface until a dedicated UI-integration campaign.

Alternative candidates the user may prefer instead:

```text
- Phase 3.5b Expression UI inspection pane (requires a new
  campaign that explicitly authorizes a UI integration pane and
  amends C10-AMEND-01 with a dedicated catalog patch)
- Phase 3.6 Worldlet expansion (more deterministic worldlets,
  more accepted-token classes, broader local consequence evidence)
- Phase 3.7 Proto-BASIC grammar expansion (more verbs, more
  bounded primitives, still below host execution)
```

Stop conditions for the next campaign must continue to refuse:

```text
real LLM calls
social/language harness
natural-language teacher/corrector
Mode B reflective planning
host execution / shell / subprocess / network I/O
filesystem save/export outside an explicit reviewed policy
PerceptEvent/tick() promotion of expression evidence
TLICA runtime mutation
weakening any existing I-* safety row
```

## Conclusion

Phase 3.5 Expression + ReadabilityPredictor campaign is complete. Catalog
is at v0.12 with full gate green. No outstanding patches, no blocked
rows, no scope-creep risks, and no follow-up corrigenda are required for
this campaign.
