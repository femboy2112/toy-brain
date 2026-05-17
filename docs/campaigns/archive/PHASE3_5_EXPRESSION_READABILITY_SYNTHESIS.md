# PHASE3_5_EXPRESSION_READABILITY_SYNTHESIS.md

Step 1 synthesis for the Phase 3.5 Expression + ReadabilityPredictor
campaign (`CURRENT_CAMPAIGN.md`). This document is the planning brief
that seeds the campaign. It does **not** change runtime behavior, the
catalog, or any fixture. No code lands in this step. Steps 2–4 produce
the kickoff, corrigenda, and catalog patch plan; only after Step 5
(review gate) may any runtime code or catalog row land.

---

## 1. v0.11 baseline summary

Baseline at the time of writing (preflight green):

```text
Catalog: v0.11
Counts: 127 REQUIRED / 44 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 7 OBSERVED
Operator TUI campaign: PASS
Operator TUI live input patch: PASS and merged
Operator TUI Agent-Style Layout: PASS (audit OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md)
Operator TUI input/switch repair: merged
Full gate (bash tools/check_all.sh): green (178 rows checked)
Entrypoint: python3 -m brain.ui
```

Required audits present and at PASS:

```text
OPERATOR_TUI_AUDIT.md                           — PASS
OPERATOR_TUI_LIVE_INPUT_PATCH_AUDIT.md          — PASS
OPERATOR_TUI_AGENT_LAYOUT_AUDIT.md              — PASS
```

Layered developmental evidence available for local inspection:

```text
Phase 3.1 Osmotic Chamber           — bottom-up percept seam, proto-content promotion
Phase 3.2 Output Ladder             — OutputImpulse / OutputEcho / OutputHistory
Phase 3.3 Minimal Worldlet          — WorldletAttempt / WorldletResponse / WorldletHistory
Phase 3.4 Proto-BASIC REPL          — ProtoBasicLine / parse / exec / feedback / ProtoBasicHistory
Operator TUI v0.11                  — read-only BrainSnapshot/DevelopmentSnapshot + OperatorTranscript
```

Each layer already exposes a bounded, copy-on-write history record with
a stable typed API. Phase 3.5 will inspect those records as **local
evidence** without mutating any of them.

---

## 2. Why Expression follows Proto-BASIC + Operator TUI

Phase 3.4 is the first layer where the kernel emits something a human
operator can read **as a fragment of structured output** — a Proto-BASIC
line, its parse category, its execution category, and a bounded local
feedback signal. The Operator TUI then makes those fragments visible
through a deterministic agent-style layout and a bounded transcript.

This produces a new local question that prior phases could not pose:

```text
Given a bounded local item shaped for inspection, can we score how
*shapely* it is — how well it satisfies bounded local readability
constraints — without claiming it is meaningful, true, intelligent,
linguistic, or communicative?
```

Phase 3.5 says: yes, but only as a **local harness construct**. The
score is a deterministic Fraction in [0, 1] over bounded features of a
local item. It is not a measure of truth, intelligence, language
understanding, social success, persuasion, or agency.

Expression follows Proto-BASIC + Operator TUI because:

1. The earlier histories now contain bounded printable items
   (`OutputEcho`, `ProtoBasicLine`, `WorldletAttempt`, transcript
   entries) that are well-typed and finite.
2. The Operator TUI proved a one-way inspection bridge is possible
   without kernel mutation, without LLM calls, without shell/network/
   file access, and without scenario/trace writes.
3. The catalog and gate disciplines (`I-UI-*`, import audit, runner)
   are now strong enough to enforce the "no upward mutation" boundary
   that Phase 3.5 needs.

Earlier than this would mean inventing the feature surface before the
evidence existed. Later than this risks letting expression bleed into
language / cognition before its locality is locked.

---

## 3. Expression thesis

Expression is a **bounded local representation of how an output-like
item is shaped for display or inspection**. It is *not*:

- a language model output;
- a generated natural-language sentence;
- a chat / message / utterance;
- a communicative act with an audience model;
- a planning / Mode B intent;
- a stand-in for the kernel's `tick()` or `PerceptEvent` semantics.

Concretely, an `ExpressionItem` is a frozen dataclass that captures:

```text
source        : ExpressionSource           — finite closed enumeration
content_id    : str                        — printable, bounded, non-reserved
text          : str                        — bounded printable representation
shape         : ExpressionShape            — bounded structural summary
provenance    : ExpressionProvenance       — local source tag + tick index
```

`ExpressionSource` is a finite enumeration whose membership is locked
by the catalog patch plan (Step 4). Candidate sources (subject to
corrigenda confirmation):

```text
OUTPUT_ECHO          — derived from an existing OutputEcho
PROTO_BASIC_LINE     — derived from an existing ProtoBasicLine
WORLDLET_ATTEMPT     — derived from an existing WorldletAttempt
OPERATOR_TRANSCRIPT  — derived from an existing TranscriptEntry
```

No `ExpressionSource` variant reaches outside the local developmental
histories or the operator transcript. There is **no** `LLM_REPLY`
variant, **no** `SOCIAL_REPLY` variant, **no** `EXTERNAL_TEXT` variant,
and **no** `HOST_PROCESS_OUTPUT` variant.

The Phase 3.5 thesis is therefore:

```text
Expression = a bounded local representation of how an existing
local-history item is shaped for inspection.
```

Expression evidence is constructed by **inspecting** local histories
through their public read accessors; it does not call into the kernel,
the LLM seam, traces, or scenarios.

---

## 4. ReadabilityPredictor thesis

`ReadabilityPredictor` is a **bounded local predictor over expression
features**. It is *not*:

- a language model;
- a comprehension test;
- a truth scorer;
- an intelligence scorer;
- a social-success scorer;
- a Goodhart-able quality KPI for the kernel;
- a feedback signal that updates BrainState, MSI, PtCns, or any
  developmental history.

The contract has three layers:

1. **Feature extraction.** A pure function maps an `ExpressionItem` to
   an `ExpressionFeatureVector`. Features are deterministic, bounded,
   and exact (Fraction or int). Candidate features (subject to kickoff
   confirmation):

   ```text
   length_chars               : int            — bounded, capped
   length_tokens              : int            — bounded, capped
   printable_ratio            : Fraction       — in [0, 1]
   distinct_token_ratio       : Fraction       — in [0, 1]
   reserved_token_collisions  : int            — bounded
   shape_balance              : Fraction       — in [0, 1]
   repetition_penalty_basis   : Fraction       — in [0, 1]
   ```

2. **Score computation.** A pure function maps an
   `ExpressionFeatureVector` to a `ReadabilityScore`. The score is an
   **exact `Fraction` in [0, 1]**, computed by a fixed deterministic
   combinator over the features. Floating point is forbidden in the
   score path; rounding is forbidden; the combinator weights are
   constants in the module.

3. **Anti-Goodhart rules.** The combinator must satisfy:

   ```text
   - repetition alone never increases the score
   - length alone never increases the score above a defined cap
   - empty / whitespace-only items score 0
   - items whose printable_ratio is below a floor score below a cap
   - identical items always produce identical scores (deterministic)
   ```

The output is a `ReadabilityPrediction`:

```text
ReadabilityPrediction
  expression_id   : ExpressionItemID
  source          : ExpressionSource
  features        : ExpressionFeatureVector
  score           : ReadabilityScore (Fraction in [0,1])
  predictor_tag   : str (frozen module-level constant)
  tick_at_predict : int
```

`predictor_tag` is a fixed identifier (e.g.
`"readability_predictor.v1"`) so future predictor variants can coexist
without ambiguity.

The Phase 3.5 thesis is therefore:

```text
ReadabilityPredictor = a deterministic, bounded, local predictor over
ExpressionFeatureVector that emits an exact Fraction-in-[0,1] score and
a source-tagged prediction record. The score is harness evidence, not
truth, intelligence, language, or social success.
```

---

## 5. Local evidence boundaries

Phase 3.5 is a **one-way inspection bridge** over the existing local
histories. The directions of data flow are:

```text
OutputHistory        ┐
WorldletHistory      ├─► (read-only inspection) ─► ExpressionRecord ─► ExpressionHistory
ProtoBasicHistory    │                                                          │
OperatorTranscript   ┘                                                          ▼
                                                                ReadabilityPrediction (local only)
```

Reverse mutation is forbidden:

```text
ExpressionHistory ─/─► BrainState
ExpressionHistory ─/─► MSI / PtCns / registry
ExpressionHistory ─/─► OutputHistory / WorldletHistory / ProtoBasicHistory
ExpressionHistory ─/─► OperatorTranscript
ExpressionHistory ─/─► tick() / PerceptEvent
ExpressionHistory ─/─► traces/ / scenarios/
ExpressionHistory ─/─► TLICA / lean_reference
```

Operationally:

- Phase 3.5 modules import from `brain.development.output`,
  `brain.development.worldlet`, `brain.development.repl`, and
  `brain.ui.transcript` **only through public read accessors**;
- Phase 3.5 modules do **not** import from `brain.tick`, `brain.llm`,
  `brain.tlica`, `tools`, or `scenarios`;
- Phase 3.5 modules do **not** import `os`, `subprocess`, `socket`,
  `urllib`, `http`, `requests`, `pathlib`-as-writer, or any I/O sink;
- `ExpressionHistory` is copy-on-write and bounded;
- `ExpressionHistory` is process-local and is destroyed when the
  process exits;
- `ExpressionHistory` is **not** written to disk, JSONL, traces,
  scenarios, or any external sink.

The import audit (`tools.import_audit`) will be extended in Step 6 to
cover the new expression module(s) under the same rules that already
cover `brain/ui/`.

---

## 6. Why readability is not truth, language, social success, or intelligence

Phase 3.5 deliberately constructs a *narrow* score. The corrigenda
(Step 3) will lock these distinctions; the synthesis records them now
so the kickoff cannot drift.

- **Readability ≠ truth.** A `ReadabilityScore` of `1` does not assert
  the expressed content is correct, well-grounded, valid in
  Proto-BASIC, valid as a worldlet attempt, or true of any external
  world. Truth scoring is not in Phase 3.5 and is not on the roadmap
  for any near-term campaign.

- **Readability ≠ language understanding.** Features are structural
  (length, printable ratio, distinct-token ratio, shape balance,
  repetition penalty). No feature parses natural language, looks up a
  word, consults a vocabulary, or models meaning. A score of `1` over
  a printable shape says nothing about whether the shape is a word, a
  sentence, a program, or a meaningful symbol.

- **Readability ≠ social success.** No feature models an audience, a
  recipient, a conversation partner, a teacher, or a corrector. The
  predictor has no read of "did anyone understand this" or "did this
  persuade anyone". The score is computed from the item alone.

- **Readability ≠ agency.** The predictor never feeds back into the
  kernel. `BrainState`, MSI, PtCns, registry, and the developmental
  histories cannot be changed by a `ReadabilityPrediction`. The kernel
  does not "try harder" because a score is low; the kernel does not
  see the score at all. The one-way bridge enforces this.

- **Readability ≠ intelligence.** The score is a Fraction in [0, 1]
  over bounded features; it has no claim about reasoning, planning,
  learning, generalization, or any cognitive capacity. It is harness
  evidence.

The corrigenda will explicitly say, in plain text, that high
readability scores carry **no** entitlement claim: they do not earn
the item promotion to a developmental layer, they do not earn the
item entry into traces or scenarios, they do not entitle the system
to claim "language", "thinking", "intent", or "agency", and they do
not warrant relaxation of any existing `I-*` row.

---

## 7. One-way bridge from earlier histories

Concretely, the construction of `ExpressionRecord` from earlier
histories is a pure, deterministic function that:

1. **Reads only.** Takes the existing history record (`OutputHistory`,
   `WorldletHistory`, `ProtoBasicHistory`, `OperatorTranscript`) as a
   parameter; returns a new `ExpressionRecord`. Does not mutate the
   input record. The earlier history records are frozen dataclasses
   already; this property is structurally enforced.

2. **Tags source.** Sets `ExpressionItem.source` to the exact
   `ExpressionSource` variant that names the originating history.

3. **Binds provenance.** Records the originating record's stable ID
   (e.g. `OutputEchoID`, `ProtoBasicLineID`, `WorldletAttemptID`,
   `TranscriptEntry`'s synthetic ID) in
   `ExpressionProvenance.source_ref`, and the current tick index in
   `ExpressionProvenance.tick_at_observe`.

4. **Bounds text.** Truncates the source text to a fixed maximum
   length using the same `_bound_printable(...)` policy the operator
   transcript already uses. No new printable policy is introduced.

5. **Returns local-only output.** The new `ExpressionRecord` is the
   only output. It is appended to a local `ExpressionHistory` via a
   copy-on-write helper (`append_expression_record(...)`). Nothing is
   returned to the originating history, no callback is registered, no
   trace seam is touched.

The bridge is purely functional. There is no shared mutable state
between the bridge and the originating history.

---

## 8. Non-goals

The following are **explicitly out of scope** for Phase 3.5 and any
proposal requiring them must escalate rather than be folded in:

- a real language model integration, a real LLM call, or any reach into
  `brain.llm` from expression code;
- a social/language harness (multi-agent communication,
  teacher/corrector, audience model, dialogue, chat);
- Mode B reflective planning, goal-conditioned action selection, or
  any planning layer that consumes readability scores;
- a natural-language understanding or generation surface;
- writing `ExpressionHistory` to traces, scenarios, files, sockets, or
  any external sink;
- shell, subprocess, network, or arbitrary Python execution;
- save/export of `BrainState` or any developmental history;
- TLICA runtime promotion, new Lean-bound rows, or weakening any
  existing Lean-bound row;
- `PerceptEvent` promotion from expression evidence;
- `tick()` semantic changes;
- catalog-row weakening (no existing REQUIRED/STRUCTURAL row is
  relaxed by this campaign);
- new external dependencies (standard library + existing project APIs
  only);
- UI integration in the same step as expression-core implementation;
  any UI inspection pane is deferred to Step 10 *if* the catalog patch
  plan explicitly authorizes it.

---

## 9. Risks

- **Score drift to truth/intelligence claims.** The biggest risk is
  semantic creep — describing the score as "quality" or "validity" or
  "understanding". Mitigation: the corrigenda enumerates the four
  "readability ≠ X" distinctions in normative language, and the
  catalog rows are phrased as feature-level invariants
  (boundedness / determinism / non-mutation), not quality claims.

- **Goodhart by length / repetition.** A naive combinator could let
  long or repetitive items inflate scores. Mitigation: explicit
  anti-Goodhart rules in the predictor contract, a REQUIRED row that
  exercises a repetition-only case and a length-cap case, and a
  feature fixture (Step 7) that pins the combinator behavior.

- **Reverse coupling.** A future caller could accidentally feed a
  `ReadabilityScore` back into `BrainState` / MSI / PtCns / a
  developmental history. Mitigation: import-audit coverage of the
  new module(s), a STRUCTURAL row asserting `ExpressionHistory`
  produces no side effects on earlier histories, and a kernel-boundary
  audit row similar to `I-PCE-05`.

- **UI temptation.** Surfacing readability in the Operator TUI is
  intuitive but can blur the operator UI / cognitive-layer line.
  Mitigation: UI integration is gated behind the Step 5 review and
  must be opt-in by the catalog patch plan; if accepted, the UI pane
  is read-only and never computes expression state itself.

- **History bloat.** `ExpressionHistory` could grow unbounded if every
  history append triggers an expression append. Mitigation: explicit
  bound (`EXPRESSION_HISTORY_MAX_ENTRIES`), copy-on-write semantics,
  and a REQUIRED row asserting the bound holds under any append
  sequence.

- **Catalog count drift.** Adding rows must update banners and
  expected counts in lockstep. Mitigation: Step 4 catalog patch plan
  enumerates each row, its status, and the exact expected-count delta;
  Step 6 runs `python3 -m tools.catalog counts` and `generate-ids` and
  re-runs counts before commit.

- **Determinism by floating point.** Any use of `float` in the score
  path would break determinism on different platforms. Mitigation: the
  score path uses `Fraction` exclusively; a REQUIRED row asserts the
  output is a `Fraction` and lies in [0, 1].

- **Cross-campaign drift.** A reader of Phase 3.5 could assume it
  implies Mode B / language / social work is next. Mitigation: this
  synthesis lists those as non-goals; the audit (Step 12) names them
  again as "Remaining deferred work".

---

## 10. Next artifact

The next campaign step (Step 2) produces:

```text
PHASE3_5_EXPRESSION_READABILITY_KICKOFF.md
```

That document will lock the concrete contracts named in this synthesis:

- `ExpressionSource` (finite closed enumeration with locked variants);
- `ExpressionItem`, `ExpressionShape`, `ExpressionProvenance`
  (frozen dataclasses with bounded printable invariants);
- `ExpressionFeatureVector` (deterministic, exact features);
- `ExpressionRecord` (the local-history entry shape);
- `ReadabilityScore` (exact `Fraction` in [0, 1]);
- `ReadabilityPrediction` (source-tagged, local-only);
- `ReadabilityPredictor` (pure function over feature vectors with
  anti-Goodhart guarantees);
- `ExpressionHistory` (bounded, copy-on-write, local-only);
- the one-way bridge constructors from each source history;
- the anti-Goodhart rules and their fixture roster.

The kickoff explicitly excludes real LLM calls, social/language
harness, Mode B planning, a natural-language teacher/corrector,
external corpus, file/network access, `PerceptEvent` promotion, and
TLICA runtime mutation.

After the kickoff, Step 3 is the corrigenda; Step 4 is the catalog
patch plan; Step 5 is the explicit review gate; only after the gate
opens may any runtime code or catalog row land.

Stop condition for the campaign as a whole is `CURRENT_CAMPAIGN.md`
Step 12: a post-completion audit verdict of PASS / PASS WITH PATCHES /
BLOCKED, recorded in `PHASE3_5_EXPRESSION_READABILITY_AUDIT.md`.
