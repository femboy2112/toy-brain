# PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md

## 1. Purpose

This document designs the future catalog v0.9 patch for Phase 3.4 Proto-BASIC
REPL rows.

It is a planning artifact only. It does not apply catalog rows, edit
`tools/catalog.py`, add runtime modules, add fixtures, change generated catalog
IDs, alter `INVARIANT_CATALOG.md`, change `brain/invariants.py`, or change the
TLICA runtime boundary.

Verdict:

```text
COHERENT - READY FOR REVIEW GATE
```

No unresolved blocker prevents a later accepted v0.9 catalog patch. The plan
keeps Proto-BASIC REPL below language, below a real interpreter, below host
execution, below reflective Mode B agency, below social exchange, and below
`PerceptEvent` / `tick()` promotion.

## 2. Baseline

Current catalog baseline is v0.8:

```text
REQUIRED:       105
STRUCTURAL:      29
NOT-EXERCISED:    3
DEFERRED:        12
OBSERVED:         4
```

Total tabular entries: `153`.
Total registered fixtures: `28`.

`python3 -m tools.catalog counts` currently reports `ok` for every banner row
under v0.8.

The Phase 3.3 audit reports PASS. `I-WLD-*` rows are green, `I-WLD-12` is
OBSERVED only, worldlet evidence is local harness evidence, valence is exact
and bounded, and not-I pushback is recorded as local consequence evidence
rather than as an external-reality claim.

## 3. Patch Impact

The v0.9 Proto-BASIC REPL patch proposed here adds:

```text
+11 REQUIRED
 +6 STRUCTURAL
 +0 NOT-EXERCISED
 +0 DEFERRED
 +1 OBSERVED
```

Expected v0.9 counts after the accepted patch:

```text
REQUIRED:       116
STRUCTURAL:      35
NOT-EXERCISED:    3
DEFERRED:        12
OBSERVED:         5
```

Total tabular entries become `171` if no other rows are added or removed.
Total registered fixtures become `32`:

```text
28 existing v0.8 fixtures
+4 Proto-BASIC REPL fixtures
```

## 4. Row Family Thesis

The v0.9 row family should use `I-REPL-*` IDs.

Core commitments inherited from the kickoff and corrigenda:

```text
Proto-BASIC consequence is local deterministic harness evidence; it is not
  real interpreter behavior, not host execution, not language, not Mode B,
  and not runtime promotion.

The Proto-BASIC grammar is finite, enumerable, and deterministic. Tokenize
  and parse_line are total over their declared input domains.

ProtoBasicValence is a Fraction in [-1, 1] and never silently clamps.

ProtoBasicCommand construction requires a valid ProtoBasicParseResult plus
  registered token and learned-output support. Parse-validity alone is not
  enough.

Valid syntax alone never earns strong positive feedback. Strong positive
  feedback requires execution_result.effective == True.

Syntax-invalid, semantic-invalid, tool-unavailable, resource-limit, and
  sandbox-fault categories produce bounded negative ProtoBasicValence.

Near-miss correction hints are deterministic local edit records bounded by
  the grammar's edit distance. They are not teacher utterances and not
  natural-language explanations.

Repeated identical no-op commands receive deterministic diminishing returns
  on strong positive valence.

Proto-BASIC operations do not call tick(), do not emit PerceptEvent, and do
  not mutate profile, MSI, PtCns, content registry, scenario schema, or
  trace files.

The bridge from learned-output / worldlet evidence into Proto-BASIC command
  support is one-way. Proto-BASIC history does not flow back into
  OutputHistory, WorldletHistory, or TLICA runtime state in Phase 3.4.
```

## 5. Proposed Rows

Add a new catalog section after the Phase 3.3 Minimal Worldlet rows and before
the Meta / runner integrity section:

```text
### Phase 3.4 Proto-BASIC REPL developmental invariants
```

Rows:

| ID | Source | Proposition | Python assertion | Owning module | Fixture | Status |
|---|---|---|---|---|---|---|
| I-REPL-01 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicToken` is a finite enumeration with bounded text. | Construction requires a known `kind`, a printable bounded `text` (no whitespace-only, no empty, length cap), printable `token_id`, and the legal set is fixed at build time for a given `ProtoBasicGrammar` with no duplicate canonical text. | `brain/development/repl.py` | `repl_grammar.py` | STRUCTURAL |
| I-REPL-02 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicLine` has bounded length and bounded token count. | Construction requires printable `line_id`, printable `raw_text` within a small fixed length cap, and a `tokens` tuple within a small fixed token-count cap; `tokenize(raw_text)` is total and deterministic for any well-formed `raw_text`. | `brain/development/repl.py` | `repl_grammar.py` | STRUCTURAL |
| I-REPL-03 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicParseResult` is total over `ProtoBasicLine`. | For every `ProtoBasicLine`, `parse_line(line)` returns exactly one `ProtoBasicParseResult` and never raises; the same line under the same grammar yields the same result. | `brain/development/repl.py` | `repl_grammar.py` | REQUIRED |
| I-REPL-04 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Parse categories partition outcomes deterministically without overlap. | Each `ProtoBasicParseResult.category` is exactly one of `valid`, `near-miss`, `syntax-invalid`, `semantic-invalid`, `tool-unavailable`, `resource-limit`, or `sandbox-fault`; no line is classified in more than one category and every line falls in exactly one. | `brain/development/repl.py` | `repl_grammar.py` | REQUIRED |
| I-REPL-05 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Near-miss correction hints respect bounded edit distance. | A `ProtoBasicParseResult` with `category == near-miss` carries exactly one canonical `correction_hint` whose `edit_kind` is one of `SUBSTITUTE_TOKEN`, `INSERT_TOKEN`, `DELETE_TOKEN`, or `CASE_FOLD`, whose `edit_position` is within the line's token-count bound, whose `expected_token_id` (when present) references an enumerated `ProtoBasicToken`, and whose total edit distance from the nearest valid form is at most the grammar's declared bound; the hint generator does not invoke any external corrector, teacher, or language model. | `brain/development/repl.py` | `repl_grammar.py` | REQUIRED |
| I-REPL-06 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicValence` is exact and bounded. | Construction requires a `Fraction` value satisfying `-1 <= value <= 1`; out-of-range values raise and no silent clamping occurs. | `brain/development/repl.py` | `repl_feedback.py` | REQUIRED |
| I-REPL-07 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicFeedback` reuses existing source / provenance discipline. | `ProtoBasicFeedback` uses `FrameSourceKind`, `Fraction` confidence in `[0, 1]`, printable trace event IDs, and introduces no Proto-BASIC-specific source-kind enum member; the same source-tag audit accepts Proto-BASIC feedback without new exemptions. | `brain/development/repl.py` | `repl_feedback.py` | STRUCTURAL |
| I-REPL-08 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Syntax-invalid, semantic-invalid, tool-unavailable, resource-limit, and sandbox-fault produce bounded negative valence. | For each non-near-miss non-valid `ProtoBasicParseResult` category and for each `tool-unavailable`, `resource-limit`, and `sandbox-fault` `ProtoBasicExecutionResult`, `score_feedback` returns a `ProtoBasicFeedback` whose `valence` is a `Fraction` strictly less than zero and within `[-1, 0)`; values are deterministic and exact. | `brain/development/repl.py` | `repl_feedback.py` | REQUIRED |
| I-REPL-09 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Valid syntax alone does not grant strong positive feedback. | A `ProtoBasicParseResult` with `category == valid` whose corresponding `ProtoBasicExecutionResult.effective == False` (valid-ineffective) yields a `ProtoBasicFeedback.valence` whose magnitude is at most a small non-strong threshold (e.g. `<= Fraction(1, 10)`); near-miss feedback similarly cannot reach strong positive valence regardless of repetition. | `brain/development/repl.py` | `repl_feedback.py` | REQUIRED |
| I-REPL-10 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Strong positive feedback requires `execution_result.effective == True`. | A `ProtoBasicFeedback.valence` greater than the non-strong threshold is produced only when the source `ProtoBasicExecutionResult.category == valid-effective` and `effective == True`; no path bypasses `effective` to grant strong positive valence. | `brain/development/repl.py` | `repl_feedback.py` | REQUIRED |
| I-REPL-11 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicCommand` carries no agency, language, host-execution, or trace fields. | A `ProtoBasicCommand` exposes no `Act`, `ModeOp`, `AgencyWitness`, `PerceptEvent`, selected action, `feasibleProjectedPCE`, `tick` callback, real interpreter handle, subprocess handle, file descriptor, network socket, teacher utterance, social register, readability score, expression handle, or Mode B planning field. | `brain/development/repl.py` | `repl_execution.py` | STRUCTURAL |
| I-REPL-12 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicCommand` construction requires valid parse plus registered token and learned-output support. | Construction rejects non-valid parse results, parse results with unknown tokens, references to non-enumerated `ProtoBasicToken`s, missing `LearnedOutputToken` support in `OutputHistory` for tokens that require it, reserved command identifiers, and non-printable command/source IDs; readiness or parse-validity alone is insufficient. | `brain/development/repl.py` | `repl_execution.py` | REQUIRED |
| I-REPL-13 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicExecutionResult` exposes the declared category set. | A `ProtoBasicExecutionResult.category` is exactly one of `valid-effective`, `valid-ineffective`, `tool-unavailable`, `resource-limit`, or `sandbox-fault`; `effective` is `True` if and only if `category == valid-effective`; no result emits `PerceptEvent` or invokes host execution. | `brain/development/repl.py` | `repl_execution.py` | STRUCTURAL |
| I-REPL-14 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicHistory` appends entries copy-on-write. | Appending a parse result, command, execution result, or feedback returns a new `ProtoBasicHistory`, preserves prior entries exactly, and updates only the new history's `emit_counts` and entry collections; no Proto-BASIC operation mutates existing history in place. | `brain/development/repl.py` | `repl_history.py` | REQUIRED |
| I-REPL-15 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Repeated identical no-op commands receive diminishing returns. | For successive `valid-effective` `ProtoBasicExecutionResult` records sharing the same canonical command form, `score_feedback` returns valences whose strong-positive component is multiplied by a deterministic `diminishing_returns_factor`, a `Fraction` in `[0, 1]` that is non-increasing in `emit_counts` for that form, computed exactly, never silently clamped, and not reset by interleaving other commands; the resulting valence remains in `[-1, 1]`. | `brain/development/repl.py` | `repl_history.py` | REQUIRED |
| I-REPL-16 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Proto-BASIC operations do not mutate TLICA runtime state. | Before and after any Proto-BASIC parse, command construction, execution, feedback, or history operation, profile / MSI / PtCns / content registry identities are unchanged, no `tick()` is called, no `PerceptEvent` is emitted, `OutputHistory` and `WorldletHistory` are unmodified, and no entries are written to scenario schemas or trace files. | `brain/development/repl.py` | `repl_history.py` | REQUIRED |
| I-REPL-17 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | `ProtoBasicProgram`, if present, is a one-line wrapper with no control flow. | If `ProtoBasicProgram` exists in the build, it wraps exactly one `ProtoBasicLine`, exposes no GOTO/GOSUB, no line numbering with branching, no loop construct, no stored-program memory beyond `ProtoBasicHistory`, no nested block structure, and no multi-line program semantics. | `brain/development/repl.py` | `repl_grammar.py` | STRUCTURAL |
| I-REPL-18 | Engineering hypothesis (Phase 3.4 Proto-BASIC REPL) | Aggregate Proto-BASIC history summaries are inspectable. | The fixture records counts of valid-effective, valid-ineffective, near-miss, syntax-invalid, semantic-invalid, tool-unavailable, resource-limit, and sandbox-fault outcomes, and a qualitative anti-Goodhart sketch under repeated emissions, for inspection; the row is OBSERVED and cannot fail the runner. | `brain/development/repl.py` | `repl_history.py` | OBSERVED |

Row totals:

```text
REQUIRED:     I-REPL-03, I-REPL-04, I-REPL-05, I-REPL-06, I-REPL-08, I-REPL-09,
              I-REPL-10, I-REPL-12, I-REPL-14, I-REPL-15, I-REPL-16 (11 rows)
STRUCTURAL:   I-REPL-01, I-REPL-02, I-REPL-07, I-REPL-11, I-REPL-13, I-REPL-17 (6 rows)
OBSERVED:     I-REPL-18 (1 row)
```

`I-REPL-18` is OBSERVED for the same reason `I-WLD-12` and `I-OUT-11` are
OBSERVED in earlier phases: aggregate qualitative summaries are inspectable
local evidence and must not become a runtime gate.

## 6. Deterministic Convention

The first implementation should keep feedback values simple and exact.
Proposed initial convention:

```text
valid-effective (first emission):    Fraction(1, 2)
valid-effective (repeated emission): Fraction(1, 2) * diminishing_returns_factor
valid-ineffective:                   Fraction(0, 1)
near-miss:                           Fraction(-1, 10)
syntax-invalid:                      Fraction(-1, 4)
semantic-invalid:                    Fraction(-1, 4)
tool-unavailable:                    Fraction(-1, 4)
resource-limit:                      Fraction(-1, 4)
sandbox-fault:                       Fraction(-1, 2)
```

Diminishing returns convention (proposed):

```text
emit_counts:      0 -> diminishing_returns_factor = Fraction(1, 1)
emit_counts:      1 -> diminishing_returns_factor = Fraction(1, 2)
emit_counts:      2 -> diminishing_returns_factor = Fraction(1, 3)
emit_counts:      n -> diminishing_returns_factor = Fraction(1, n + 1)
```

Non-strong threshold (proposed):

```text
strong_positive_threshold = Fraction(1, 10)
```

`I-REPL-09` and `I-REPL-10` use this threshold to distinguish weak / zero
feedback from strong positive feedback.

These are local harness values only. They do not claim affect taxonomy,
fear, avoidance, reward learning, external-world truth, or runtime
self-model update.

Exact numeric values may be tightened by Step 7 / Step 8 / Step 9
fixtures, but the row-level statements above must remain true.

## 7. Fixture Roster

Add four new fixture files under `brain/development/fixtures/`:

| Fixture | Drives invariant IDs | Implementation step |
|---|---|---|
| `repl_grammar.py` | I-REPL-01, I-REPL-02, I-REPL-03, I-REPL-04, I-REPL-05, I-REPL-17 | Step 7 |
| `repl_feedback.py` | I-REPL-06, I-REPL-07, I-REPL-08, I-REPL-09, I-REPL-10 | Step 7 |
| `repl_execution.py` | I-REPL-11, I-REPL-12, I-REPL-13 | Step 8 |
| `repl_history.py` | I-REPL-14, I-REPL-15, I-REPL-16, I-REPL-18 (OBSERVED) | Step 8 / Step 9 |

The v0.9 fixture count becomes `32` total fixtures:

```text
28 existing v0.8 fixtures
+4 Proto-BASIC REPL fixtures
```

## 8. Owning Module Map

New runtime module:

```text
brain/development/repl.py
```

This single module should host the v0.9 Proto-BASIC REPL surface:

```text
ProtoBasicToken
ProtoBasicLine
ProtoBasicProgram (optional thin wrapper only)
ProtoBasicGrammar (legal token enumeration)
ProtoBasicParseResult
ProtoBasicCommand
ProtoBasicExecutionResult
ProtoBasicFeedback
ProtoBasicValence
ProtoBasicHistory
tokenize
parse_line
build_command
execute_command
score_feedback
append_history
summarize_repl_history
```

Existing module reuse:

```text
brain/development/output.py        # LearnedOutputToken / OutputHistory support
brain/development/worldlet.py      # optional supporting WorldletHistory evidence
brain/development/history.py       # printable ID / TraceEventID helpers
brain/development/stream.py        # FrameSourceKind source discipline
brain/development/drives.py        # require_unit_fraction for confidence checks
brain/tick.py                      # read-only in Phase 3.4; do not edit
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

## 9. Catalog Patch Mechanics

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
1. Add a v0.9 catalog-version banner above the v0.8 banner.
2. Add the Phase 3.4 Proto-BASIC REPL table with I-REPL-01..I-REPL-18.
3. Add the four Proto-BASIC fixtures to the fixture roster.
4. Update the fixture-total text from 28 to 32.
5. Update summary counts to 116 / 35 / 3 / 12 / 5.
6. Update total tabular entries from 153 to 171.
```

Required Step 6 tooling edits:

```text
1. Update tools/catalog.py EXPECTED_COUNTS to:
   REQUIRED=116, STRUCTURAL=35, NOT-EXERCISED=3, DEFERRED=12, OBSERVED=5.
2. Update the nearby comment from v0.8 to v0.9.
3. Run python3 -m tools.catalog generate-ids.
```

Required Step 6 registry coherence:

```text
1. Add a _PHASE3_4_PENDING_ROWS map in brain/invariants.py for I-REPL REQUIRED
   and STRUCTURAL rows.
2. Pending checks must raise NotImplementedError if executed.
3. Do not register I-REPL-18 as a pending failing gate. It is OBSERVED and
   does not participate in I-CAT-01 coverage.
4. Do not claim any I-REPL row green in Step 6.
5. Do not add Proto-BASIC runtime behavior in Step 6.
6. Do not add missing Proto-BASIC fixture modules to FIXTURE_MODULES until the
   corresponding fixture files exist.
```

The pending map should include:

```text
I-REPL-01 STRUCTURAL
I-REPL-02 STRUCTURAL
I-REPL-03 REQUIRED
I-REPL-04 REQUIRED
I-REPL-05 REQUIRED
I-REPL-06 REQUIRED
I-REPL-07 STRUCTURAL
I-REPL-08 REQUIRED
I-REPL-09 REQUIRED
I-REPL-10 REQUIRED
I-REPL-11 STRUCTURAL
I-REPL-12 REQUIRED
I-REPL-13 STRUCTURAL
I-REPL-14 REQUIRED
I-REPL-15 REQUIRED
I-REPL-16 REQUIRED
I-REPL-17 STRUCTURAL
```

Reason:

`I-CAT-01` audits coverage from `brain/_catalog_ids.py`. After the catalog
patch, REQUIRED and STRUCTURAL `I-REPL-*` rows need registered entries so
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
pending I-REPL rows have already been implemented; pending rows intentionally
make the full runner red until Step 7 / Step 8 / Step 9 replace them.

## 10. Strict Implementation Order

Step 6 - Apply accepted v0.9 catalog patch:

```text
catalog rows
expected counts
generated IDs
pending registrations only
no runtime behavior
```

Step 7 - Grammar / parser / feedback boundary rows:

```text
Implement I-REPL-01, I-REPL-02, I-REPL-03, I-REPL-04, I-REPL-05, I-REPL-06,
          I-REPL-07, I-REPL-08, I-REPL-09, I-REPL-10, I-REPL-17.
Files:
  brain/development/repl.py
  brain/development/fixtures/repl_grammar.py
  brain/development/fixtures/repl_feedback.py
  brain/invariants.py
  brain/_catalog_ids.py
Validation:
  python3 -m brain.invariants run --id I-REPL-01
  python3 -m brain.invariants run --id I-REPL-02
  python3 -m brain.invariants run --id I-REPL-03
  python3 -m brain.invariants run --id I-REPL-04
  python3 -m brain.invariants run --id I-REPL-05
  python3 -m brain.invariants run --id I-REPL-06
  python3 -m brain.invariants run --id I-REPL-07
  python3 -m brain.invariants run --id I-REPL-08
  python3 -m brain.invariants run --id I-REPL-09
  python3 -m brain.invariants run --id I-REPL-10
  python3 -m brain.invariants run --id I-REPL-17
```

Step 8 - Command execution and history rows:

```text
Implement I-REPL-11, I-REPL-12, I-REPL-13, I-REPL-14, I-REPL-16.
Files:
  brain/development/repl.py
  brain/development/fixtures/repl_execution.py
  brain/development/fixtures/repl_history.py
  brain/invariants.py
Validation:
  python3 -m brain.invariants run --id I-REPL-11
  python3 -m brain.invariants run --id I-REPL-12
  python3 -m brain.invariants run --id I-REPL-13
  python3 -m brain.invariants run --id I-REPL-14
  python3 -m brain.invariants run --id I-REPL-16
```

Step 9 - Anti-Goodhart / local evidence rows:

```text
Implement I-REPL-15 and I-REPL-18.
Files:
  brain/development/repl.py
  brain/development/fixtures/repl_history.py
  brain/invariants.py
Validation:
  python3 -m brain.invariants run --id I-REPL-15
  python3 -m brain.invariants run --id I-REPL-18
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
Write PHASE3_4_PROTO_BASIC_REPL_AUDIT.md after the full gate passes.
```

## 11. Design Decisions

These are resolved for v0.9:

```text
Use a single new brain/development/repl.py module for the Proto-BASIC surface.

Restrict the program surface to a one-line ProtoBasicLine. ProtoBasicProgram,
  if present at all, is a thin one-line wrapper with no control flow
  (I-REPL-17).

Treat the legal ProtoBasicToken set as fixed at build time for a given
  ProtoBasicGrammar; no dynamic token registration after grammar
  construction (I-REPL-01).

Use seven deterministic parse categories that partition outcomes without
  overlap: valid, near-miss, syntax-invalid, semantic-invalid,
  tool-unavailable, resource-limit, sandbox-fault (I-REPL-04).

Define near-miss by a small bounded edit distance with hint edit kinds
  drawn from a fixed set (SUBSTITUTE_TOKEN, INSERT_TOKEN, DELETE_TOKEN,
  CASE_FOLD) (I-REPL-05).

Use ProtoBasicValence with a Fraction in [-1, 1]; reject out-of-range
  construction (I-REPL-06). No silent clamping anywhere in the feedback
  layer.

Reuse FrameSourceKind for ProtoBasicFeedback provenance; do not add a
  Proto-BASIC-specific source-kind enum member (I-REPL-07).

Require ProtoBasicCommand construction to depend on a valid parse result
  plus registered LearnedOutputToken support; parse-validity alone is
  insufficient (I-REPL-12).

Keep effective execution as the strong-positive gate: strong positive
  feedback requires execution_result.effective == True (I-REPL-10).

Keep diminishing returns deterministic and exact, computed from
  per-canonical-form emit_counts in ProtoBasicHistory, with valence
  staying inside [-1, 1] (I-REPL-15).

Keep Proto-BASIC evidence local; no PerceptEvent emission, no tick()
  call, no profile / MSI / PtCns / content-registry / scenario / trace
  mutation (I-REPL-16).

Keep the bridge from output / worldlet evidence one-way: Proto-BASIC
  history does not flow back into OutputHistory or WorldletHistory in
  Phase 3.4.

Keep aggregate Proto-BASIC summaries OBSERVED only; do not gate the
  runner on qualitative anti-Goodhart claims (I-REPL-18).

Do not introduce a real BASIC interpreter, host execution, subprocess,
  file I/O, network I/O, eval / exec, natural-language teacher,
  expression / readability layer, social / language harness, Mode B
  reflective planning, or free-will branch semantics through Proto-BASIC.
```

## 12. Open Decisions

No open decision blocks Step 6.

The following items are intentionally deferred beyond v0.9. Each is local
to Phase 3.4 and does not require user adjudication before Step 6:

```text
Exact non-strong threshold value (Section 6 proposes Fraction(1, 10); the
  Step 7 fixture may tighten it as long as I-REPL-09 / I-REPL-10 remain
  true).

Exact diminishing-returns schedule (Section 6 proposes 1/(n+1); the Step 9
  fixture may select a different deterministic schedule as long as
  I-REPL-15 holds and valence stays in [-1, 1]).

Whether ProtoBasicProgram is emitted at all in v0.9 or only described as
  a STRUCTURAL surface (I-REPL-17 covers either choice).

Whether I-REPL-15 requires a separate fixture file or shares
  repl_history.py with I-REPL-14, I-REPL-16, and I-REPL-18 (Section 7
  consolidates them in repl_history.py).
```

Deferred beyond v0.9 entirely:

```text
Whether a later phase can promote Proto-BASIC evidence into PerceptEvent.
Whether expression / readability layers inspect ProtoBasicHistory.
Whether a social / language harness adds teacher correction or external
  feedback to Proto-BASIC.
Whether Mode B later inspects aggregate Proto-BASIC consequence history.
Whether the grammar grows beyond the one-line surface (multi-line, GOTO,
  loops, stored-program semantics).
Whether Proto-BASIC commands can address worldlet targets beyond the
  one-way support bridge.
Whether near-miss hints ever escalate to natural-language explanations.
```

These are later-phase design questions, not blockers for the v0.9 catalog
patch.

## 13. Stop Conditions

Stop and report if any later step requires:

```text
editing brain/tlica/
editing lean_reference/
changing tick() semantics
changing scenario schema
running a real LLM scenario
emitting PerceptEvent from Proto-BASIC evidence
implementing a real BASIC interpreter
implementing host execution, subprocess invocation, file I/O, or network I/O
implementing arbitrary Python eval / exec
adding a natural-language teacher or social corrector
adding expression / readability behavior in Phase 3.4
adding a social / language harness in Phase 3.4
adding Mode B reflective planning in Phase 3.4
adding free-will branch semantics through Proto-BASIC commands
claiming Proto-BASIC consequence evidence as external-world truth
claiming a valid parse as language understanding
claiming a near-miss hint as teacher correction
claiming Proto-BASIC feedback as named affect taxonomy
prompt-tuning solely to force the four-tick scenario or any other gate to pass
seeded-MSI shortcuts
making pending I-REPL rows pass without real fixture behavior
```

Step 5 is an explicit review gate. This plan is coherent and internally
complete, but the v0.9 catalog patch should not be applied until the user
says `go` again or explicitly accepts the plan.

## 14. Verdict

```text
COHERENT - READY FOR REVIEW GATE
```

Proceed to Step 5 (review gate) before applying the v0.9 catalog patch.
