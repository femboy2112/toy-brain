# PHASE3_4_PROTO_BASIC_REPL_AUDIT.md

## 1. Purpose

This audit reviews the Phase 3.4 Proto-BASIC REPL campaign after Step 10's
full gate. It checks scope creep, row-family registration, syntax vs language,
execution vs host execution, bounded feedback / valence, anti-Goodhart
behavior, the kernel boundary, the full-gate result, and recommends the next
campaign.

The campaign began at catalog v0.8 (Phase 3.3 baseline) and ended at catalog
v0.9. The full gate passes with `0` gate failures.

This audit is a planning artifact. It does not edit catalog rows, runtime
modules, fixtures, or guarded directories. It cites repo-local state captured
during Step 10 and the final implementation commits.

---

## 2. Inputs Reviewed

```text
PHASE3_4_PROTO_BASIC_REPL_SYNTHESIS.md
PHASE3_4_PROTO_BASIC_REPL_KICKOFF.md
PHASE3_4_PROTO_BASIC_REPL_CORRIGENDA.md
PHASE3_4_PROTO_BASIC_REPL_CATALOG_PATCH_PLAN.md
INVARIANT_CATALOG.md (v0.9 rows I-REPL-01..I-REPL-18)
brain/development/repl.py
brain/development/fixtures/repl_grammar.py
brain/development/fixtures/repl_feedback.py
brain/development/fixtures/repl_execution.py
brain/development/fixtures/repl_history.py
brain/_catalog_ids.py
brain/invariants.py
tools/catalog.py
tools/check_all.sh
```

Phase 3.3 audit (`PHASE3_3_MINIMAL_WORLDLET_AUDIT.md`) is the inherited PASS
baseline.

---

## 3. Inherited Baseline

Catalog v0.8 baseline at the start of the campaign:

```text
REQUIRED:       105
STRUCTURAL:      29
NOT-EXERCISED:    3
DEFERRED:        12
OBSERVED:         4
```

Phase 3.3 PASS verdict: worldlet evidence is local deterministic harness
evidence, `I-WLD-*` rows are green, `I-WLD-12` is OBSERVED only, valence is
exact and bounded, not-I pushback is recorded as local consequence evidence
rather than external-reality truth.

---

## 4. v0.9 Catalog Patch Outcome

Catalog v0.9 banner (final):

```text
REQUIRED:       116
STRUCTURAL:      35
NOT-EXERCISED:    3
DEFERRED:        12
OBSERVED:         5
```

`python3 -m tools.catalog counts` reports `ok` for every banner row. Banner
matches actual matches expected.

Row-family delta:

```text
+11 REQUIRED   (Phase 3.4 Proto-BASIC REPL)
 +6 STRUCTURAL (Phase 3.4 Proto-BASIC REPL)
 +1 OBSERVED   (Phase 3.4 Proto-BASIC REPL: I-REPL-18)
```

Total tabular entries increased from `153` to `171`. Fixture roster grew from
`28` to `32` registered fixtures (added `repl_grammar.py`, `repl_feedback.py`,
`repl_execution.py`, `repl_history.py`).

The patch matches the catalog patch plan exactly. No row was renumbered, no
row was reclassified during implementation, and no row was added or removed
beyond `I-REPL-01..I-REPL-18`.

---

## 5. Row-Family Registration

The Phase 3.4 row family is `I-REPL-*` and was registered as follows:

```text
I-REPL-01  STRUCTURAL  repl_grammar.py   ProtoBasicToken finite enumeration
I-REPL-02  STRUCTURAL  repl_grammar.py   ProtoBasicLine bounded length / tokens
I-REPL-03  REQUIRED    repl_grammar.py   parse_line total over ProtoBasicLine
I-REPL-04  REQUIRED    repl_grammar.py   parse categories partition deterministically
I-REPL-05  REQUIRED    repl_grammar.py   near-miss hints respect bounded edit distance
I-REPL-06  REQUIRED    repl_feedback.py  ProtoBasicValence exact in [-1, 1]
I-REPL-07  STRUCTURAL  repl_feedback.py  source/provenance discipline reused
I-REPL-08  REQUIRED    repl_feedback.py  non-valid categories produce bounded negative valence
I-REPL-09  REQUIRED    repl_feedback.py  valid syntax alone is not strong positive
I-REPL-10  REQUIRED    repl_feedback.py  strong positive requires effective execution
I-REPL-11  STRUCTURAL  repl_execution.py ProtoBasicCommand carries no agency/language fields
I-REPL-12  REQUIRED    repl_execution.py ProtoBasicCommand needs valid parse + support
I-REPL-13  STRUCTURAL  repl_execution.py ProtoBasicExecutionResult declared category set
I-REPL-14  REQUIRED    repl_history.py   ProtoBasicHistory copy-on-write append
I-REPL-15  REQUIRED    repl_history.py   repeated no-op commands get diminishing returns
I-REPL-16  REQUIRED    repl_history.py   no TLICA runtime mutation
I-REPL-17  STRUCTURAL  repl_grammar.py   ProtoBasicProgram is a one-line wrapper
I-REPL-18  OBSERVED    repl_history.py   aggregate Proto-BASIC summaries inspectable
```

All eighteen rows are registered, have owning modules, have fixtures, and are
green under the runner. `I-CAT-01` reports STRUCTURAL PASS, meaning catalog
coverage is coherent and no `I-REPL-*` row is missing a registered handler.

`I-REPL-18` is OBSERVED only and never gates the runner; this matches the
plan and the corrigenda recommendation to keep qualitative anti-Goodhart
summaries below REQUIRED.

Verdict on registration: clean. The intended row family was applied without
distortion.

---

## 6. Scope Creep Check

The campaign was scoped narrowly. The kickoff, corrigenda, and catalog patch
plan all enumerate explicit non-goals. Checking each non-goal against the
final repo state:

```text
real BASIC interpreter           - not introduced
host execution                   - not introduced
shell access                     - not introduced
subprocess invocation            - not introduced
file I/O outside REPL state      - not introduced
network I/O                      - not introduced
arbitrary Python eval / exec     - not introduced
natural-language teacher         - not introduced
expression / readability layer   - not introduced
readability predictor            - not introduced
social / language harness        - not introduced
Mode B reflective planning       - not introduced
real LLM training behavior       - not introduced
prompt tuning for scenario gates - not introduced
seeded-MSI shortcuts             - not introduced
direct TLICA state mutation      - not introduced
Proto-BASIC -> PerceptEvent      - not introduced
Proto-BASIC -> affect taxonomy   - not introduced
free-will branch semantics       - not introduced
multi-line programs              - not introduced
GOTO / GOSUB / loops             - not introduced
stored-program semantics         - not introduced
```

The repl module documents these exclusions at the top of `brain/development/
repl.py` and `I-REPL-11` / `I-REPL-13` / `I-REPL-16` enforce them
structurally. No new fields in `ProtoBasicCommand`, `ProtoBasicExecutionResult`,
`ProtoBasicFeedback`, or `ProtoBasicHistory` carry `Act`, `ModeOp`,
`AgencyWitness`, `PerceptEvent`, `feasibleProjectedPCE`, `tick` callbacks,
real interpreter handles, subprocess handles, file descriptors, or network
sockets.

Guarded directories are untouched:

```text
brain/tlica/                       - unchanged
lean_reference/                    - unchanged
traces/first_scenario_real.jsonl   - unchanged
traces/RUN_SUMMARY.md              - unchanged
scenarios/                         - unchanged
brain/tick.py                      - unchanged
brain/llm/                         - unchanged
```

Verdict on scope creep: none observed. The campaign stayed inside the
Proto-BASIC harness boundary.

---

## 7. Syntax vs Language Distinction

The kickoff and corrigenda both required that Proto-BASIC syntax not be
confused with language. The implementation honors this in three concrete
ways:

1. `ProtoBasicToken` is a fixed enumeration with bounded printable text.
   Construction rejects unknown kinds, empty/whitespace-only text, oversize
   text, and duplicate canonical text. There is no extension point for
   natural-language words.

2. `tokenize` is total and deterministic over bounded `raw_text`. The same
   input always yields the same token sequence. There is no NLP step, no
   external corpus, no language model call, no learned tokenizer.

3. Near-miss correction hints (`I-REPL-05`) are deterministic edit records
   drawn from a fixed set: `SUBSTITUTE_TOKEN`, `INSERT_TOKEN`, `DELETE_TOKEN`,
   `CASE_FOLD`. Hints carry an `edit_position`, an optional `expected_token_id`
   that must reference an enumerated `ProtoBasicToken`, and an optional
   `observed_token_text`. They do not phrase corrections in natural language,
   do not address a listener, do not score readability, and do not invoke
   any external corrector or language model.

The parse result categories themselves are mechanical, not communicative:

```text
valid             - grammar accepts and local semantics permit
near-miss         - within bounded local edit distance of a valid form
syntax-invalid    - no bounded edit reaches a valid form
semantic-invalid  - structurally valid but disallowed by local rules
tool-unavailable  - references a Proto-BASIC operation not in this build
resource-limit   - exceeds a bounded local resource cap
sandbox-fault    - a local containment guard fired
```

`valid` is "grammar accepts and local semantics permit", not "the system
understood the input". `tool-unavailable` is not a missing OS tool;
`resource-limit` is not a real CPU/memory exhaustion; `sandbox-fault` is not
a real sandbox alarm. The repl module docstring and the catalog row text
both make these non-claims explicit.

Verdict on syntax vs language: clean. Syntax is local rule-governed form;
language was not implemented or smuggled in.

---

## 8. Execution vs Host Execution

`ProtoBasicCommand` and `ProtoBasicExecutionResult` describe deterministic
local effects on `ProtoBasicHistory` only. Audit checks:

- `I-REPL-11` (STRUCTURAL) enforces that a `ProtoBasicCommand` carries no
  `Act`, `ModeOp`, `AgencyWitness`, `PerceptEvent`, selected-action,
  `feasibleProjectedPCE`, `tick` callback, real interpreter handle,
  subprocess handle, file descriptor, network socket, teacher utterance,
  social register, readability score, expression handle, or Mode B planning
  field. The fixture verifies the absence of each of these attribute names.

- `I-REPL-12` (REQUIRED) enforces that `ProtoBasicCommand` construction
  requires both a `valid` parse and registered learned-output / token
  support. Parse-validity alone is rejected. Reserved command identifiers
  and non-printable IDs are rejected.

- `I-REPL-13` (STRUCTURAL) enforces the declared category set
  (`valid-effective`, `valid-ineffective`, `tool-unavailable`,
  `resource-limit`, `sandbox-fault`) and that `effective == True` if and
  only if `category == valid-effective`. No execution result emits
  `PerceptEvent` or invokes a host process.

- The repl module never imports `subprocess`, `os.system`, `eval`,
  `exec`, `socket`, `urllib`, `requests`, `pathlib.write_text`, or any
  network/file-mutation surface. The only `subprocess` strings present are
  the names of forbidden attributes inside `_FORBIDDEN_COMMAND_FIELDS` /
  `_FORBIDDEN_RESULT_FIELDS` used as exclusion checks.

- `tool-unavailable`, `resource-limit`, and `sandbox-fault` are local
  bounded categories. None of them shells out, raises a real OS error, or
  inspects a real resource quota. They are predicates against a fixed local
  cap and a fixed local containment guard.

Verdict on execution vs host execution: clean. Proto-BASIC execution is
deterministic local rule application against in-memory state; there is no
host execution surface.

---

## 9. Bounded Feedback and Valence

`ProtoBasicValence` is an exact `Fraction` constrained to `[-1, 1]` with
out-of-range construction raising. The audit checks:

- `I-REPL-06` (REQUIRED) enforces exact `Fraction` storage and rejects
  out-of-range values without silent clamping. Floats and other numeric
  types are rejected at construction.

- `I-REPL-08` (REQUIRED) enforces bounded negative valence for every non-
  valid non-near-miss category and for `tool-unavailable`, `resource-limit`,
  and `sandbox-fault` execution categories. All such valences are strictly
  less than zero, exactly representable, and lie within `[-1, 0)`.

- `I-REPL-09` (REQUIRED) enforces that valid syntax alone does not earn
  strong positive feedback. Valid-ineffective execution and near-miss
  outcomes both stay at or below the small non-strong threshold.

- `I-REPL-10` (REQUIRED) enforces that strong positive feedback requires
  `execution_result.category == valid-effective` and
  `execution_result.effective == True`. There is no bypass path.

- `I-REPL-07` (STRUCTURAL) confirms `ProtoBasicFeedback` reuses the existing
  `FrameSourceKind` discipline with `Fraction` confidence in `[0, 1]` and
  printable trace event IDs. No Proto-BASIC-specific source-kind enum
  member was added.

The deterministic feedback convention used in the implementation matches
the catalog patch plan's proposed values:

```text
valid-effective (first emission):    Fraction(1, 2)
valid-effective (repeated):          Fraction(1, 2) * diminishing_returns_factor
valid-ineffective:                   Fraction(0, 1)
near-miss:                           Fraction(-1, 10)
syntax-invalid:                      Fraction(-1, 4)
semantic-invalid:                    Fraction(-1, 4)
tool-unavailable:                    Fraction(-1, 4)
resource-limit:                      Fraction(-1, 4)
sandbox-fault:                       Fraction(-1, 2)
```

Every value is exact, bounded, and source-tagged. None enters affect
taxonomy, profile values, MSI scoring, or PtCns weights.

Verdict on bounded feedback / valence: clean.

---

## 10. Anti-Goodhart Behavior

Anti-Goodhart in Phase 3.4 has two mechanisms: effect-required reward and
diminishing returns. Both are exercised by `I-REPL-09`, `I-REPL-10`, and
`I-REPL-15`.

Effect-required reward:

```text
A ProtoBasicFeedback.valence > strong_positive_threshold is produced only
when execution_result.category == valid-effective and effective == True.
Valid-ineffective and near-miss can never reach strong positive valence,
regardless of how many times the same form is emitted.
```

This is enforced by `I-REPL-09` (REQUIRED) and `I-REPL-10` (REQUIRED). The
fixtures exhibit at least one valid-ineffective and at least one near-miss
case that is repeated and never crosses the strong-positive threshold.

Diminishing returns:

```text
For successive valid-effective execution results that share a canonical
command form, score_feedback multiplies the strong-positive component by a
deterministic diminishing_returns_factor Fraction in [0, 1] that is
non-increasing in emit_counts, computed exactly, never silently clamped, and
not reset by interleaving other commands.
```

This is enforced by `I-REPL-15` (REQUIRED). The fixture demonstrates that:

- The factor is exact `Fraction`, not `float`.
- The factor is non-increasing in `emit_counts` for the same canonical form.
- The factor is not reset by emitting other commands in between.
- The resulting valence stays in `[-1, 1]` and is never silently clamped.
- Emitting one strong-positive command repeatedly does not cause its
  cumulative or single-step feedback to dominate `ProtoBasicHistory` summaries
  in a runaway way.

`I-REPL-18` (OBSERVED) records aggregate Proto-BASIC history summaries
(counts of valid-effective, valid-ineffective, near-miss, syntax-invalid,
semantic-invalid, tool-unavailable, resource-limit, sandbox-fault outcomes)
for inspection. It does not gate the runner.

Importantly, neither mechanism feeds back into the profile, MSI, PtCns, or
content registry. They live entirely inside the Proto-BASIC feedback layer.

Verdict on anti-Goodhart: clean. Effect-required reward and diminishing
returns are implemented deterministically and exactly, and both correctly
prevent emission rate or syntactic conformance alone from dominating
feedback distribution.

---

## 11. Kernel Boundary

The kernel boundary (no PerceptEvent emission, no `tick()` call, no TLICA
runtime mutation) is enforced by `I-REPL-16` (REQUIRED) and reinforced by
the surface checks in `I-REPL-11` and `I-REPL-13`.

`I-REPL-16` asserts that before and after any Proto-BASIC parse, command
construction, execution, feedback, or history operation:

```text
profile / MSI / PtCns / content registry identities are unchanged
no tick() is called
no PerceptEvent is emitted
OutputHistory and WorldletHistory are unmodified
no entries are written to scenario schemas or trace files
```

The repl module imports `COGITO_ID` only for the reserved-identifier check
(rejecting `COGITO_ID` as a Proto-BASIC command ID). It does not import
`brain.tick`, `brain.llm`, anything in `brain.tlica` beyond the profile
identifier constant, anything in `scenarios/`, anything in `traces/`, or any
LLM-side seam.

The bridge from output / worldlet evidence is one-way as required:

```text
output / worldlet evidence -> ProtoBasicCommand support  (allowed)
ProtoBasicHistory entries -> OutputHistory                (NOT allowed)
ProtoBasicHistory entries -> WorldletHistory              (NOT allowed)
ProtoBasicHistory entries -> PerceptEvent / tick() / TLICA (NOT allowed)
```

No code path in Phase 3.4 promotes a Proto-BASIC entry back into earlier-phase
state. `I-REPL-16` exercises this directly by comparing identities before
and after operations.

Verdict on kernel boundary: clean.

---

## 12. Full Gate Result

Step 10 commands and outcomes:

```bash
python3 -m tools.catalog counts
# 116 / 35 / 3 / 12 / 5 - all ok

python3 -m tools.citations verify
# Verified 100 citations. All catalog citations resolve in lean_reference/.

python3 -m tools.import_audit
# I-PCE-05: agency.py is clean of pce imports.

python3 -m brain.invariants run
# 156 rows checked. REQUIRED green: 116, REQUIRED red: 0.
# STRUCTURAL green: 35, STRUCTURAL red: 0.
# OBSERVED: 5 pass / 0 fail. gate failures: 0.

bash tools/check_all.sh
# 0/5 generated catalog IDs freshness: wrote brain/_catalog_ids.py
# 1/5 catalog counts (strict): all ok
# 2/5 citation verification: 100/100 verified
# 3/5 import audit (I-PCE-05): clean
# 4/5 invariant runner: 156 rows, 0 gate failures
# All checks passed.
```

`I-CAT-01` (catalog coverage), `I-ISO-01..03` (module isolation),
`I-PCE-05` (PCE/agency import boundary), and every `I-REPL-*` row are green.

Verdict on full gate: PASS.

---

## 13. Risks and Limitations

Resolved within Phase 3.4:

```text
Syntax confused with language        - prevented by I-REPL-01, I-REPL-05, I-REPL-11
Valid parse confused with effect     - prevented by I-REPL-09, I-REPL-10
Reward hacking via emission spam     - prevented by I-REPL-15
Real interpreter / host execution    - prevented by I-REPL-11, I-REPL-13, I-REPL-16
PerceptEvent / tick promotion        - prevented by I-REPL-16
Affect taxonomy growth               - prevented by I-REPL-07 source discipline
Profile / MSI / PtCns mutation       - prevented by I-REPL-16
External-reality claims              - prevented by category non-claims in catalog text
```

Out of scope and deferred:

```text
Expression layer / readability predictor       (Phase 3.5)
Social / language harness                       (Phase 3.6)
Mode B reflective planning                      (later phase)
Multi-line programs / GOTO / loops              (later phase, may never apply)
Free-will branch semantics through REPL         (out of scope)
Proto-BASIC -> PerceptEvent promotion           (requires explicit later campaign)
Proto-BASIC -> affect taxonomy promotion        (requires explicit later campaign)
Expression layer inspection of ProtoBasicHistory (Phase 3.5+)
Mode B inspection of aggregate Proto-BASIC consequence history (later phase)
External teacher / corrector / LLM in near-miss hints (out of scope)
Grammar growth beyond the one-line surface      (later phase)
Proto-BASIC commands addressing worldlet targets beyond the one-way bridge
                                                 (later phase)
Near-miss hints escalating to natural-language explanations (out of scope)
```

The audit identifies no additional risks beyond those already acknowledged in
the kickoff and corrigenda. The diminishing-returns schedule
(`Fraction(1, n+1)`) and the strong-positive threshold (`Fraction(1, 10)`)
are reasonable initial choices; future phases may tighten them while
preserving `I-REPL-09`, `I-REPL-10`, and `I-REPL-15`.

---

## 14. Internal Consistency

The four planning artifacts (synthesis, kickoff, corrigenda, catalog patch
plan) are internally consistent with each other and with the final code:

```text
Synthesis core thesis           -> implemented and gated by I-REPL-*.
Kickoff object model            -> implemented with the documented fields.
Corrigenda tightenings          -> appear as row-level invariants.
Catalog patch plan row table    -> applied verbatim into INVARIANT_CATALOG.md.
Catalog patch plan banner deltas -> match v0.9 counts exactly.
Catalog patch plan fixture roster -> present at the named paths.
Catalog patch plan implementation order -> commits 6, 7, 8, 9 follow that order.
```

No row was renamed or reclassified between planning and implementation. No
fixture was silently swapped. The pending-registration approach worked as
intended: between Step 6 and Step 9 the runner refused to claim green rows
without real fixture behavior, then turned green only after each
implementation step.

Verdict on internal consistency: clean.

---

## 15. Verdict

```text
PASS
```

The Phase 3.4 Proto-BASIC REPL campaign achieves all of:

```text
Scope held: no creep into language, host execution, affect taxonomy,
            expression / readability, social language, Mode B, free-will
            branch semantics, or runtime promotion.
Row family registered: 18 I-REPL-* rows green; I-CAT-01 STRUCTURAL PASS.
Syntax-vs-language distinction enforced at row level.
Execution-vs-host-execution distinction enforced at row level.
Bounded feedback and exact Fraction valence enforced at row level.
Anti-Goodhart implemented deterministically and exactly via effect-required
            reward and diminishing returns.
Kernel boundary intact: no PerceptEvent, no tick() call, no TLICA mutation,
            no profile / MSI / PtCns / content registry / scenario / trace
            change.
Full gate green: catalog counts ok, 100/100 citations verified, import audit
            clean, 156 rows checked, 0 gate failures, check_all.sh passed.
Internal consistency between synthesis, kickoff, corrigenda, catalog patch
            plan, and final code.
```

No patches are required. There are no outstanding warnings that block
campaign completion.

---

## 16. Recommended Next Mission

The natural next campaign in the inherited Phase 3 sequence is:

```text
Phase 3.5 - Expression + ReadabilityPredictor
```

Phase 3.5 should ask whether Proto-BASIC outputs (and earlier output / worldlet
material) admit a deterministic local expression layer with a bounded
readability predictor that does not become language, does not become a
teacher, does not promote evidence into `PerceptEvent` or `tick()`, and does
not collapse into Mode B reflective planning.

Suggested first artifacts for the next campaign (analogous to Phase 3.4):

```text
PHASE3_5_EXPRESSION_READABILITY_SYNTHESIS.md
PHASE3_5_EXPRESSION_READABILITY_KICKOFF.md
PHASE3_5_EXPRESSION_READABILITY_CORRIGENDA.md
PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md
```

Suggested initial constraints (to be refined in the next synthesis):

```text
Expression and ReadabilityPredictor remain local deterministic harness
            constructs.
Readability is a bounded local predictor, not natural-language fluency.
Expression evidence is local; it does not enter PerceptEvent, tick(),
            profile, MSI, PtCns, content registry, scenarios, or traces.
Expression bounded valence (if introduced) follows the same Fraction-in-
            [-1, 1] discipline as ProtoBasicValence and WorldletValence.
Anti-Goodhart applies: a uniformly high readability score must not arise
            from emission rate alone.
The bridge from Proto-BASIC / worldlet / output evidence into Expression is
            one-way; Expression history does not flow back into earlier-phase
            state in Phase 3.5.
No social / language harness in Phase 3.5; that remains Phase 3.6.
No Mode B reflective planning in Phase 3.5.
No real LLM call in Phase 3.5.
```

Until a new `CURRENT_MISSION.md` or `CURRENT_CAMPAIGN.md` authorizes Phase
3.5, the agent should stop at this audit.

---

## 17. Campaign Complete

```text
Phase 3.4 Proto-BASIC REPL campaign complete.
Catalog: v0.9
Counts: REQUIRED=116, STRUCTURAL=35, NOT-EXERCISED=3, DEFERRED=12, OBSERVED=5
Full gate: pass
Commits: synthesis (319823d), kickoff (146b2e5), corrigenda (092cc4a),
         catalog patch plan (8f899cc), catalog v0.9 patch (ad89177),
         step 7 grammar/parser/feedback (40621d1),
         step 8 execution/history (14eac83),
         step 9 anti-Goodhart / local evidence (d62d225)
Remaining deferred work: expression / readability (Phase 3.5),
                          social / language harness (Phase 3.6),
                          Mode B reflective planning (later),
                          any later promotion of Proto-BASIC evidence into
                          PerceptEvent / tick() / TLICA runtime state.
```
