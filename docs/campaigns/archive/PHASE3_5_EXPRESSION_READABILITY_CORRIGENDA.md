# PHASE3_5_EXPRESSION_READABILITY_CORRIGENDA.md

Step 3 corrigenda for the Phase 3.5 Expression + ReadabilityPredictor
campaign (`CURRENT_CAMPAIGN.md`). This document audits the kickoff
(`PHASE3_5_EXPRESSION_READABILITY_KICKOFF.md`) against the synthesis
(`PHASE3_5_EXPRESSION_READABILITY_SYNTHESIS.md`) and the campaign hard
boundaries. Where the kickoff is correct, the corrigenda affirms it.
Where it is unclear, ambiguous, or in tension with the campaign's
hard boundaries, the corrigenda amends it.

The corrigenda is still a **planning artifact**: no runtime code, no
catalog row, and no fixture lands in this step. Step 4 (catalog patch
plan) maps the corrected contracts onto proposed rows; Step 5 is the
explicit review gate; only after the gate opens may any runtime code
or catalog row land.

Each section names a property to audit, the kickoff's position, a
verdict (`AFFIRM`, `AMEND`, or `DEFER`), and (for `AMEND`) the exact
amendment.

---

## C1. Expression vs language distinction

**Audit.** Does the kickoff keep Expression strictly distinct from
"language"? Concretely: are there any features, sources, or accessors
that import a language model, a vocabulary, a parser of natural
language, a grammar, a corpus, or a comprehension surface?

**Kickoff position.** Sections 1–3 declare:

```text
- ExpressionSource has no LLM_REPLY / SOCIAL_REPLY / EXTERNAL_TEXT
  variant
- tokenization is whitespace-split only
- there is no dictionary lookup, no stemming, no vocabulary
- features are int / Fraction only
- the predictor is not a language model, not a comprehension test
```

**Verdict.** `AFFIRM` with one **AMEND**.

**Amendment (C1-AMEND-01).** Add an explicit normative sentence to the
predictor module docstring (planned for Step 8) stating:

```text
"This module computes a bounded structural score over a local
expression item. It does NOT model language. It does NOT understand,
parse, generate, or evaluate natural language. The score is harness
evidence, not a measure of linguistic quality."
```

This sentence is reproduced verbatim in the eventual catalog row's
description text (proposed in Step 4) and again in the post-completion
audit (Step 12).

---

## C2. Readability vs truth distinction

**Audit.** Does the kickoff keep readability strictly distinct from
truth, correctness, validity, or any other epistemic claim?

**Kickoff position.** Sections 4 and 7.3 declare:

```text
- the predictor is not a truth scorer
- the predictor is not a quality / validity scorer
- a high score does not assert the content is correct, well-grounded,
  valid in Proto-BASIC, valid as a worldlet attempt, or true of any
  external world
```

The synthesis already states (Section 6):

```text
"Readability != truth. A ReadabilityScore of 1 does not assert the
expressed content is correct."
```

**Verdict.** `AFFIRM`.

**Note (C2-NOTE-01).** The Step 4 catalog patch plan must phrase any
row that involves `ReadabilityScore` as a **structural** property of
the score (boundedness, determinism, locality) and **not** as a
quality claim. Specifically, no proposed row may use the words
"correct", "true", "valid", "accurate", or "good" in describing what
the score asserts about the expressed content.

---

## C3. Readability vs social success distinction

**Audit.** Does the kickoff keep readability strictly distinct from
social or communicative success — i.e. from any signal that some
recipient understood, accepted, agreed with, or was persuaded by the
expressed content?

**Kickoff position.** Sections 4 and 7.3 declare:

```text
- the predictor is not a social-success scorer
- the predictor is not a teacher / corrector / audience model
- there is no SOCIAL_REPLY ExpressionSource variant
- no feature models a recipient, audience, conversation partner, or
  corrector
- the score is computed from the item alone
```

**Verdict.** `AFFIRM`.

**Note (C3-NOTE-01).** The Step 4 catalog patch plan must NOT propose
any row that requires a "recipient", "audience", "teacher",
"corrector", or "feedback" entity. Any such proposal escalates to a
new campaign.

---

## C4. Readability vs agency distinction

**Audit.** Does the kickoff keep readability strictly distinct from
agency — i.e. from any claim that the system acted, chose, intended,
preferred, planned, or pursued anything?

**Kickoff position.** Sections 6, 7.3, and 8 declare:

```text
- the prediction does not change BrainState / MSI / PtCns / registry
- the prediction does not invoke tick() / PerceptEvent
- the prediction does not feed back into the kernel
- ExpressionHistory does not feed back into BrainState / MSI / PtCns
- the predictor is not a feedback signal into the kernel
- the predictor is not a planner input
```

**Verdict.** `AFFIRM` with one **AMEND**.

**Amendment (C4-AMEND-01).** The corrigenda adds a hard rule that
**no catalog row in this campaign** may use language such as "the
brain prefers higher readability", "the agent learns to maximize
readability", "the score drives selection", or any other phrasing that
implies agency, intent, or learning. Row descriptions are limited to
structural invariants (boundedness, determinism, non-mutation,
locality, anti-Goodhart). This is checked in Step 4 row drafting.

---

## C5. Feature extraction determinism

**Audit.** Are all feature definitions deterministic, exact, and
free of platform-dependent or stateful behavior?

**Kickoff position.** Section 3 declares:

```text
- all features are int or Fraction; no float anywhere in this layer
- ratios are exact Fractions; no rounding
- ratios are clamped to [0, 1] by construction
- identical ExpressionItem inputs always produce identical vectors
- vector construction is a pure function; no global state, no I/O
```

**Verdict.** `AFFIRM` with one **AMEND**.

**Amendment (C5-AMEND-01).** Two feature definitions in the kickoff
(`shape_balance` and `repetition_penalty_basis`) are described as
"the exact form is fixed by the corrigenda". The corrigenda locks them
as follows:

```text
shape_balance (locked):
    Let w = shape.whitespace_count, c = shape.char_count.
    If c == 0:                 shape_balance := Fraction(0, 1)
    Else let r = Fraction(w, c):
        target := SHAPE_BALANCE_TARGET            # module-frozen Fraction in (0, 1)
        width  := SHAPE_BALANCE_WIDTH             # module-frozen Fraction in (0, 1)
        dist   := abs(r - target)                 # Fraction
        if dist >= width:      shape_balance := Fraction(0, 1)
        else:                  shape_balance := Fraction(1) - dist / width
    Invariant: shape_balance in [0, 1] as Fraction.

repetition_penalty_basis (locked):
    Let t  = shape.token_count, d = shape.distinct_token_count.
    If t == 0:                 repetition_penalty_basis := Fraction(0, 1)
    Else:
        # share of repeated tokens; 0 when all distinct; bounded
        repetition_penalty_basis := Fraction(t - d, t)
    Invariant: repetition_penalty_basis in [0, 1] as Fraction.
```

Both definitions are pure functions of `ExpressionShape`. No floats.
No randomness. No I/O.

**Amendment (C5-AMEND-02).** All module-frozen constants used in
features and the score combinator must be declared at module top
level as `Fraction` literals (e.g. `SHAPE_BALANCE_TARGET =
Fraction(1, 5)`). They must not be computed at import time from a
mutable source, environment variable, or file.

---

## C6. Bounded exact score discipline

**Audit.** Is the `ReadabilityScore` strictly bounded, exact, and free
of float?

**Kickoff position.** Sections 5 and 7 declare:

```text
- value is fractions.Fraction (exact)
- value lies in [0, 1] inclusive
- value is never a float
- score combinator is Fraction-only; no float, no math.* on features,
  no rounding
- constructor raises on out-of-range, non-Fraction, or NaN-like inputs
```

**Verdict.** `AFFIRM` with one **AMEND**.

**Amendment (C6-AMEND-01).** The corrigenda locks the score
combinator as a **convex combination of Fractions clamped to [0, 1]
with anti-Goodhart caps applied in a fixed order**:

```text
score_features(features) -> ReadabilityScore:

    # Step 1: positive contributions (Fractions in [0, 1]):
    p_printable        := features.printable_ratio              # in [0, 1]
    p_shape            := features.shape_balance                # in [0, 1]
    p_distinct         := features.distinct_token_ratio         # in [0, 1]

    # Step 2: negative contributions (Fractions in [0, 1]):
    n_repetition       := features.repetition_penalty_basis     # in [0, 1]

    # Step 3: convex combination (Fractions, exact):
    base := (
        W_PRINTABLE * p_printable
      + W_SHAPE     * p_shape
      + W_DISTINCT  * p_distinct
      - W_REPEAT    * n_repetition
    )
    # Weights W_* are module-frozen Fraction constants with
    # W_PRINTABLE + W_SHAPE + W_DISTINCT == Fraction(1)
    # and W_REPEAT in [0, Fraction(1, 2)].

    # Step 4: clamp to [0, 1]:
    base := max(Fraction(0), min(Fraction(1), base))

    # Step 5: anti-Goodhart caps in fixed order:
    if features.length_chars == 0:
        return ReadabilityScore(Fraction(0))
    if features.printable_ratio < PRINTABLE_FLOOR:
        base := min(base, PRINTABLE_CAP)
    if features.length_chars > LENGTH_CAP_THRESHOLD:
        base := min(base, LENGTH_CAP)
    if features.reserved_token_collisions > 0:
        base := min(base, RESERVED_CAP)

    return ReadabilityScore(base)
```

All weights and caps are module-frozen `Fraction` constants. The
combinator uses `Fraction` arithmetic only. No `float`, no `math.*`,
no `round(...)` on the feature side or the score side.

**Amendment (C6-AMEND-02).** `ReadabilityScore.__init__` raises
`TypeError` on non-`Fraction` inputs and `ValueError` on out-of-range
inputs. The factory may accept `int` or `Fraction`; it must reject
`float`, `Decimal`, and `str` even if they appear numerically valid.

---

## C7. Anti-Goodhart requirements

**Audit.** Do the kickoff's anti-Goodhart rules (Section 10, rules
A–I) cover the relevant failure modes, and do they hold under the
score combinator locked in C6?

**Kickoff position.** Rules A–I in Section 10, mapped to fixture
cases.

**Verdict.** `AFFIRM` with two **AMEND**s.

**Amendment (C7-AMEND-01).** Rule **F** ("a single token repeated N
times scores no higher than the same token occurring once") is now
provable from the locked `repetition_penalty_basis` and the locked
combinator:

```text
Let item_1 have token T occurring once: distinct_token_count == 1,
token_count == 1, so repetition_penalty_basis == 0.
Let item_N have token T occurring N times: distinct_token_count == 1,
token_count == N, so repetition_penalty_basis == (N-1)/N >= 0.
The combinator subtracts W_REPEAT * repetition_penalty_basis, so
score(item_N) <= score(item_1), modulo the printable / shape /
distinct contributions which are >= for item_1 (distinct ratio is
higher for the single-occurrence case).
```

This is recorded so the Step 8 fixture
(`readability_predictor_single_token_repeat.py`) can be expressed as a
strict-monotone inequality and not merely a non-decreasing assertion.

**Amendment (C7-AMEND-02).** Add rule **J**:

```text
J. The combinator is a pure function of ExpressionFeatureVector
   and the module-frozen constants. It is NOT a function of any
   external history, any other ExpressionRecord, any aggregate
   over ExpressionHistory, or any clock.
```

Rule J prevents a future patch from introducing "context-aware"
scoring that depends on the rest of the history, which would
re-introduce a Goodhart surface (e.g. "score relative to recent
average").

The fixture roster from the kickoff is extended:

```text
J -> readability_predictor_history_independent.py
```

---

## C8. Which rows should be REQUIRED / STRUCTURAL / OBSERVED / NOT-EXERCISED

**Audit.** The Step 4 catalog patch plan will propose rows. The
corrigenda decides their statuses **a priori** so the patch plan does
not drift into REQUIRED creep or OBSERVED dilution.

**Verdict.** `AMEND` (this section is the canonical mapping the patch
plan must follow).

Proposed status mapping (row family `I-EXP-*`):

```text
REQUIRED:
    I-EXP-01  ExpressionSource is a finite closed enumeration
    I-EXP-02  ExpressionItem.text is bounded printable
    I-EXP-03  ExpressionFeatureVector is deterministic and exact
              (Fraction / int only, no float)
    I-EXP-04  ReadabilityScore is Fraction in [0, 1]
    I-EXP-05  ReadabilityPrediction is source-tagged and predictor-tagged
    I-EXP-06  ExpressionHistory is copy-on-write and bounded
    I-EXP-07  No mutation of BrainState / MSI / PtCns / registry from
              expression code
    I-EXP-08  No mutation of OutputHistory / WorldletHistory /
              ProtoBasicHistory / OperatorTranscript from expression code
    I-EXP-09  Anti-Goodhart: empty / whitespace-only items score Fraction(0)
    I-EXP-10  Anti-Goodhart: repetition alone never increases the score
    I-EXP-11  Anti-Goodhart: length alone is capped (length_chars >
              LENGTH_CAP_THRESHOLD -> score <= LENGTH_CAP)
    I-EXP-12  Predictor determinism: identical (item, predictor_tag)
              produce identical predictions modulo tick_at_predict

STRUCTURAL:
    I-EXP-13  ExpressionHistory has no I/O / network / file / shell
              import (covered by import-audit row)
    I-EXP-14  ExpressionRecord is a frozen dataclass
    I-EXP-15  Bridge constructors are pure and do not register callbacks
              on source histories
    I-EXP-16  Predictor module has no float, no math.*, no round on the
              score path (covered by import-audit / static-grep row)

OBSERVED:
    I-EXP-17  Aggregate ExpressionHistory summary view (count, mean,
              max by source) is OBSERVED only; it carries no
              entitlement claim and is not consumed by any
              developmental layer

NOT-EXERCISED:
    I-EXP-18  ExpressionHistory write-to-disk path is NOT-EXERCISED
              and intentionally absent (placeholder row to make the
              absence auditable; phrased as "no public helper exists
              to serialize ExpressionHistory")
```

The Step 4 patch plan must use exactly these statuses. The patch plan
is allowed to **drop** rows from this list (and update count deltas
accordingly) but must not **promote** rows (e.g. OBSERVED -> REQUIRED)
without a new corrigenda revision.

The plan must also justify the count delta against the saved baseline:

```text
v0.11 baseline: 127 REQUIRED / 44 STRUCTURAL / 4 NOT-EXERCISED / 12 DEFERRED / 7 OBSERVED  (194 total)
After full landing (if all 18 rows accepted):
    REQUIRED    : 127 + 12 = 139
    STRUCTURAL  :  44 +  4 =  48
    NOT-EXERCISED:  4 +  1 =   5
    DEFERRED    :  12 +  0 =  12
    OBSERVED    :   7 +  1 =   8
    TOTAL       : 212
```

The patch plan must reconcile its row table with these deltas.

---

## C9. Whether ExpressionHistory must remain local only

**Audit.** Is `ExpressionHistory` strictly process-local, or does any
clause in the kickoff hint at persistence, export, replay, or cross-
process visibility?

**Kickoff position.** Section 8 locality rules `L1`–`L7`.

**Verdict.** `AFFIRM` with one **AMEND**.

**Amendment (C9-AMEND-01).** The corrigenda makes `L1`–`L7` normative
**campaign-level** rules: any proposal — in this campaign or any
future campaign — that would write `ExpressionHistory` to disk,
traces, scenarios, or any sink must open a **new campaign** with its
own synthesis, kickoff, corrigenda, and catalog patch plan. It must
not be folded into Phase 3.5.

This is enforced structurally by:

```text
- I-EXP-13 (STRUCTURAL): no I/O / network / file / shell imports
- I-EXP-18 (NOT-EXERCISED): no public serialization helper exists
```

`I-EXP-18` is the explicit "absence" row that makes the lack of a
write path auditable.

---

## C10. Whether any UI integration is allowed or deferred

**Audit.** The kickoff (Section 12) and the synthesis (Section 8)
both list UI integration as potentially deferred. Does the corrigenda
allow UI integration in this campaign?

**Kickoff position.** "any UI inspection pane is deferred to Step 10
*if* the catalog patch plan explicitly authorizes it."

**Verdict.** `AMEND` -> `DEFER`.

**Amendment (C10-AMEND-01).** UI integration is **deferred** for this
campaign. The Step 4 catalog patch plan **must not** authorize a UI
inspection pane in Phase 3.5. Step 10 is therefore skipped: no
`brain/ui/*` files are touched in Phase 3.5.

Rationale:

```text
- the kickoff already says "any UI inspection pane is deferred ... if
  the catalog patch plan explicitly authorizes it"
- the synthesis "UI temptation" risk (Section 9) is best mitigated by
  keeping the UI line strictly clean for the duration of Phase 3.5
- the Operator TUI audit pipeline (3 PASS audits) should not be
  reopened by an opportunistic pane
- the locality rules L1-L7 are stronger when no UI surface reads
  ExpressionHistory in the same campaign that introduces it
- a future campaign can propose a read-only ExpressionHistory pane
  with its own synthesis / kickoff / corrigenda / patch plan
```

The Step 4 catalog patch plan therefore enumerates:

```text
- new file budget: brain/development/expression.py and its fixtures
- new file budget DOES NOT include any brain/ui/* file
- import-audit coverage extends to the new expression module(s) only
- Step 10 is explicitly SKIPPED in the campaign plan
```

If a future user explicitly asks for a UI pane, that requires opening
a new campaign step or a new campaign; it does not reopen this one.

---

## C11. Summary of amendments

```text
C1-AMEND-01   Predictor module docstring states it does not model language;
              reproduced in row description and post-completion audit.
C4-AMEND-01   No catalog row uses agency-implying language.
C5-AMEND-01   shape_balance and repetition_penalty_basis are locked as
              pure Fraction functions of ExpressionShape.
C5-AMEND-02   Module-frozen constants are Fraction literals declared at
              module top level.
C6-AMEND-01   Score combinator is a clamped convex combination with
              anti-Goodhart caps applied in fixed order.
C6-AMEND-02   ReadabilityScore factory rejects float / Decimal / str.
C7-AMEND-01   Rule F is now provable as a strict-monotone inequality;
              fixture asserts the strict form.
C7-AMEND-02   Rule J is added: combinator is history-independent.
C8            18 row IDs proposed with locked statuses (12 REQUIRED,
              4 STRUCTURAL, 1 OBSERVED, 1 NOT-EXERCISED).
C9-AMEND-01   ExpressionHistory persistence requires a new campaign.
C10-AMEND-01  UI integration is deferred; Step 10 is skipped.
```

The Step 4 catalog patch plan must:

```text
- adopt the C8 status mapping (drops allowed, promotions not allowed)
- adopt the C9 / C10 amendments (no persistence, no UI in Phase 3.5)
- reconcile its row table with the count delta in C8
- enumerate the file budget consistent with C10 (no brain/ui/* files)
```

---

## 12. Next artifact

The next campaign step (Step 4) produces:

```text
PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md
```

The catalog patch plan will:

```text
- enumerate the 18 proposed I-EXP-* rows with their locked statuses
- specify owning modules and fixture roster
- specify the count delta against v0.11
- specify catalog patch mechanics and pending-registration plan
- specify the strict implementation order (Steps 6 -> 7 -> 8 -> 9 ->
  11 -> 12; Step 10 skipped per C10)
- enumerate open decisions (if any) and stop conditions
- enumerate the file budget (no brain/ui/* files)
```

After the catalog patch plan, Step 5 is the explicit review gate. Only
after the gate opens may any runtime code or catalog row land.
