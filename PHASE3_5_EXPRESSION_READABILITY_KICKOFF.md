# PHASE3_5_EXPRESSION_READABILITY_KICKOFF.md

Step 2 kickoff for the Phase 3.5 Expression + ReadabilityPredictor
campaign (`CURRENT_CAMPAIGN.md`). This document locks the concrete
contracts named by `PHASE3_5_EXPRESSION_READABILITY_SYNTHESIS.md`. It
is still a **planning artifact**: no runtime code, no catalog row, and
no fixture lands in this step. Step 3 (corrigenda) may amend any
contract; Step 4 (catalog patch plan) maps the locked contracts onto
proposed rows; Step 5 is the explicit review gate; only after the gate
opens may any runtime code or catalog row land.

This kickoff stays inside the campaign's hard boundaries. It does
**not** specify:

```text
real LLM scoring or any reach into brain/llm/
a natural-language teacher / corrector / audience model
social communication, dialogue, chat, or multi-agent harness
Mode B reflective planning or goal-conditioned selection
external corpus, file I/O, network I/O, or process I/O
PerceptEvent promotion or tick() semantic changes
TLICA runtime mutation or new Lean-bound rows
scenario / trace schema changes
new external dependencies (standard library + existing project APIs only)
```

---

## 1. ExpressionSource

`ExpressionSource` is a **finite, closed enumeration**. Membership is
locked here and re-confirmed by Step 3 (corrigenda). New variants
require a new campaign step and a catalog row update; they are not
added at the implementation step.

Locked variants:

```text
OUTPUT_ECHO          — derived from an existing OutputEcho
PROTO_BASIC_LINE     — derived from an existing ProtoBasicLine
WORLDLET_ATTEMPT     — derived from an existing WorldletAttempt
OPERATOR_TRANSCRIPT  — derived from an existing TranscriptEntry
```

Explicitly forbidden variants (any proposal adding one must escalate):

```text
LLM_REPLY                — would require brain/llm/ reach
SOCIAL_REPLY             — implies audience / dialogue
EXTERNAL_TEXT            — implies external corpus / file access
HOST_PROCESS_OUTPUT      — implies subprocess / shell reach
TRACE_PLAYBACK           — implies traces/ read coupling
SCENARIO_PLAYBACK        — implies scenarios/ read coupling
TICK_DERIVED             — implies tick() semantic coupling
```

`ExpressionSource` is implemented as a `str`-valued `Enum`. The string
values are stable identifiers (`"output_echo"`, `"proto_basic_line"`,
`"worldlet_attempt"`, `"operator_transcript"`) so that diagnostics and
test output remain deterministic.

Contract guarantees:

```text
- finite, no UNKNOWN / OTHER / ANY variant
- closed under future revisions (no implicit "extension point")
- str-valued for stable repr in tests and audit output
- variant set is treated as a typed enumeration by all callers
```

---

## 2. ExpressionItem

`ExpressionItem` is a **frozen dataclass** capturing the bounded
printable evidence carried by a single expression observation.

```text
ExpressionItem (frozen):
    item_id        : ExpressionItemID            # newtype around str
    source         : ExpressionSource            # locked enumeration
    content_id     : str                         # bounded, printable, non-reserved
    text           : str                         # bounded printable representation
    shape          : ExpressionShape             # bounded structural summary
    provenance     : ExpressionProvenance        # source ref + tick index
```

Bounds and policy:

```text
EXPRESSION_TEXT_MAX_LEN        : int       (module-level constant)
EXPRESSION_CONTENT_ID_MAX_LEN  : int       (module-level constant)
RESERVED_CONTENT_ID_PREFIXES   : tuple[str, ...]
PRINTABLE_REPLACEMENT          : str       (single replacement char)
```

- `text` is truncated to `EXPRESSION_TEXT_MAX_LEN` using the same
  `_bound_printable(...)` policy the operator transcript already
  applies. No new printable policy is introduced; the transcript's
  policy is the reference.
- `content_id` is printable, capped to `EXPRESSION_CONTENT_ID_MAX_LEN`,
  and must not collide with `RESERVED_CONTENT_ID_PREFIXES`. Reserved
  prefixes are deterministic and module-frozen.
- `item_id` is generated deterministically from `(source,
  content_id, tick_at_observe)` via a stable hashing scheme. Identical
  inputs produce identical `item_id`s; this is required by determinism.

`ExpressionItem` is **inert evidence**. It carries no behavior, no
mutation hook, no callback, and no reference back to the originating
history beyond the source ref string in `ExpressionProvenance`.

---

### 2.1 ExpressionShape

`ExpressionShape` is a frozen dataclass with bounded ints summarizing
the structure of `text`. It is computed by a pure function over `text`
alone; it does not consult any history, predictor, or external state.

```text
ExpressionShape (frozen):
    char_count          : int   # bounded by EXPRESSION_TEXT_MAX_LEN
    token_count         : int   # bounded; token = whitespace-split
    distinct_token_count: int   # bounded; <= token_count
    printable_count     : int   # bounded; <= char_count
    whitespace_count    : int   # bounded; <= char_count
    line_count          : int   # bounded; 1 + count('\n')
```

Tokenization is whitespace-split only. There is no language-aware
tokenization, stemming, lemmatization, dictionary lookup, or
vocabulary in this layer.

---

### 2.2 ExpressionProvenance

`ExpressionProvenance` is a frozen dataclass binding the expression
item to its originating local-history record.

```text
ExpressionProvenance (frozen):
    source           : ExpressionSource  # mirrors ExpressionItem.source
    source_ref       : str               # OutputEchoID / ProtoBasicLineID / ...
    tick_at_observe  : int               # current tick index when observed
```

`source_ref` is the **stable ID string** exposed by the originating
history record. It is treated as opaque; the expression layer does
not parse it.

`tick_at_observe` is the current tick index at the moment the bridge
constructor is called. It is **not** a kernel mutation hook — it is
captured from a read-only accessor for diagnostic ordering only.

---

## 3. ExpressionFeatureVector

`ExpressionFeatureVector` is a frozen dataclass of **deterministic,
exact features** computed from an `ExpressionItem` (via its `text` and
`shape`).

```text
ExpressionFeatureVector (frozen):
    length_chars               : int        # bounded, capped
    length_tokens              : int        # bounded, capped
    printable_ratio            : Fraction   # in [0, 1]
    distinct_token_ratio       : Fraction   # in [0, 1]
    reserved_token_collisions  : int        # bounded, >= 0
    shape_balance              : Fraction   # in [0, 1]
    repetition_penalty_basis   : Fraction   # in [0, 1]
```

Determinism rules:

```text
- all features are int or Fraction; no float anywhere in this layer
- ratios are exact Fractions; no rounding
- ratios are clamped to [0, 1] by construction, not by post-clamp
- identical ExpressionItem inputs always produce identical vectors
- vector construction is a pure function; no global state, no I/O
```

Feature semantics (locked here, subject to corrigenda confirmation):

- `length_chars` = `shape.char_count`, capped at `EXPRESSION_TEXT_MAX_LEN`.
- `length_tokens` = `shape.token_count`, capped at a module constant.
- `printable_ratio` = `Fraction(shape.printable_count, shape.char_count)`
  with the convention `Fraction(0, 1)` when `char_count == 0`.
- `distinct_token_ratio` =
  `Fraction(shape.distinct_token_count, shape.token_count)` with the
  convention `Fraction(0, 1)` when `token_count == 0`.
- `reserved_token_collisions` = count of whitespace-split tokens of
  `text` that appear in a module-frozen reserved-token set
  (`RESERVED_TOKENS`). The reserved set is bounded and deterministic.
- `shape_balance` is a bounded Fraction in [0, 1] derived from the
  ratio of `whitespace_count` to `char_count` against a target band
  (kickoff scope: a single bounded triangular kernel pinned at a
  module-frozen target; exact form is fixed by the corrigenda).
- `repetition_penalty_basis` is a bounded Fraction in [0, 1] that is
  `0` when no token repeats and grows monotonically with the share of
  repeated tokens, but **never** exceeds a module-frozen cap. The
  exact form is fixed by the corrigenda.

Feature vectors are inert. They do not mutate the source item.

---

## 4. ExpressionRecord

`ExpressionRecord` is the **local-history entry** for one expression
observation. It bundles an `ExpressionItem` with its feature vector,
its readability prediction, and a creation index in
`ExpressionHistory`.

```text
ExpressionRecord (frozen):
    record_id      : ExpressionRecordID     # newtype around str
    item           : ExpressionItem
    features       : ExpressionFeatureVector
    prediction     : ReadabilityPrediction
    history_index  : int                    # position in ExpressionHistory
    tick_at_record : int                    # current tick at record creation
```

Bridge constructor signatures (one per source):

```text
expression_from_output_echo(echo: OutputEcho, *, tick: int) -> ExpressionRecord
expression_from_proto_basic_line(line: ProtoBasicLine, *, tick: int) -> ExpressionRecord
expression_from_worldlet_attempt(attempt: WorldletAttempt, *, tick: int) -> ExpressionRecord
expression_from_operator_transcript(entry: TranscriptEntry, *, tick: int) -> ExpressionRecord
```

Each bridge constructor:

```text
- takes the source record as a parameter (frozen dataclass)
- reads only public accessors of the source record
- does NOT mutate the source record
- returns a new ExpressionRecord
- does NOT append to any history (append is a separate explicit step)
```

The constructor is a pure function. Appending the resulting record to
`ExpressionHistory` is a deliberate, separate call (see Section 8).

---

## 5. ReadabilityScore (exact Fraction in [0, 1])

`ReadabilityScore` is a **newtype around `fractions.Fraction`** with
an **enforced invariant** of `0 <= value <= 1`. It is constructed
through a module-level factory that raises on out-of-range or non-
`Fraction` inputs.

```text
ReadabilityScore:
    value : Fraction   # exact; 0 <= value <= 1; constructed via factory
```

Hard rules:

```text
- value is fractions.Fraction (exact)
- value lies in [0, 1] inclusive
- value is never a float
- value is never the result of float() / round() / math.* on a feature
- constructor raises on out-of-range, non-Fraction, or NaN-like inputs
```

The score's repr is deterministic (`Fraction`'s repr), so test
output is stable across runs and platforms.

---

## 6. ReadabilityPrediction

`ReadabilityPrediction` is a frozen dataclass binding a
`ReadabilityScore` to its expression item, its feature vector, and a
**predictor tag**.

```text
ReadabilityPrediction (frozen):
    prediction_id   : ReadabilityPredictionID   # newtype around str
    expression_id   : ExpressionItemID
    source          : ExpressionSource
    features        : ExpressionFeatureVector
    score           : ReadabilityScore           # Fraction in [0, 1]
    predictor_tag   : str                        # frozen module constant
    tick_at_predict : int
```

`predictor_tag` is a module-frozen identifier (e.g.
`"readability_predictor.v1"`) so future predictor variants can coexist
without ambiguity. Predictions are tagged with their predictor and are
**not interchangeable** across predictor tags.

The prediction is **inert**:

```text
- the prediction does not change BrainState / MSI / PtCns / registry
- the prediction does not change OutputHistory / WorldletHistory
- the prediction does not change ProtoBasicHistory / OperatorTranscript
- the prediction does not invoke tick() / PerceptEvent
- the prediction does not write to traces / scenarios / files / sockets
```

---

## 7. ReadabilityPredictor

`ReadabilityPredictor` is a **pure function** from
`ExpressionFeatureVector` to `ReadabilityScore`, plus a thin wrapper
that emits a `ReadabilityPrediction` from an `ExpressionItem`.

Pure score function signature:

```text
score_features(features: ExpressionFeatureVector) -> ReadabilityScore
```

Wrapper signature:

```text
predict(item: ExpressionItem, *, tick: int) -> ReadabilityPrediction
```

The score combinator is a **fixed deterministic linear-ish formula**
over the feature vector. Concrete weights are constants in the
predictor module, locked at corrigenda time. The formula must satisfy
all anti-Goodhart rules in Section 7.1.

### 7.1 Anti-Goodhart rules

The combinator and feature definitions must jointly satisfy:

```text
G1  empty / whitespace-only items score Fraction(0)
G2  printable_ratio below PRINTABLE_FLOOR caps the score at PRINTABLE_CAP
G3  repetition alone never increases the score
G4  length alone never increases the score above LENGTH_CAP
G5  identical items always produce identical scores (determinism)
G6  reserved_token_collisions > 0 caps the score at RESERVED_CAP
G7  a single token repeated N times scores no higher than a single occurrence
G8  the score combinator uses Fraction arithmetic only (no float, no rounding)
```

`PRINTABLE_FLOOR`, `PRINTABLE_CAP`, `LENGTH_CAP`, `RESERVED_CAP` are
module-frozen `Fraction` constants. Each anti-Goodhart rule has at
least one fixture case in the Step 8 fixture roster.

### 7.2 Determinism contract

```text
- score_features is a pure function (no globals, no I/O, no time)
- predict reads only the provided item and tick; no globals, no I/O
- identical (item, tick) always produce identical predictions
- predictor_tag is a module constant; it does not change at call time
- predictor_tag is included in equality for predictions
```

### 7.3 What the predictor is not

```text
- not a language model
- not a comprehension test
- not a truth scorer
- not a quality / validity scorer
- not an intelligence scorer
- not a social-success scorer
- not a feedback signal into the kernel
- not a planner input
- not a teacher / corrector / audience model
- not a Goodhart-able KPI
```

---

## 8. ExpressionHistory

`ExpressionHistory` is a **bounded, copy-on-write, process-local**
container of `ExpressionRecord`s. It mirrors the existing developmental
history shape (`OutputHistory`, `WorldletHistory`, `ProtoBasicHistory`)
in semantics; it does **not** share state with any of them.

```text
ExpressionHistory (frozen):
    entries  : tuple[ExpressionRecord, ...]   # bounded
    capacity : int                            # EXPRESSION_HISTORY_MAX_ENTRIES
```

Helpers:

```text
empty_expression_history() -> ExpressionHistory
append_expression_record(
    history: ExpressionHistory,
    record:  ExpressionRecord,
) -> ExpressionHistory
expression_history_view(history: ExpressionHistory) -> ExpressionHistoryView
```

Semantics:

```text
- append returns a NEW ExpressionHistory (copy-on-write)
- input ExpressionHistory is not mutated
- when entries length == capacity, the oldest entry is dropped (FIFO);
  the drop is deterministic and recorded in the view's summary
- view is a read-only projection (counts, last N items, summary stats)
- view does NOT expose mutation hooks
```

Locality rules:

```text
L1  ExpressionHistory is process-local; not written to disk
L2  ExpressionHistory is not written to traces/, scenarios/, or any sink
L3  ExpressionHistory is not visible to brain.tick / brain.llm / brain.tlica
L4  ExpressionHistory is not coupled to PerceptEvent
L5  ExpressionHistory does not feed back into BrainState / MSI / PtCns
L6  ExpressionHistory does not mutate OutputHistory / WorldletHistory /
    ProtoBasicHistory / OperatorTranscript
L7  ExpressionHistory is destroyed on process exit
```

Aggregate summary in the view (e.g. mean score, max score, count by
source) is **OBSERVED only**; it carries no entitlement claim and is
not consumed by any developmental layer.

---

## 9. Bounded feature extraction from local histories

The bridge from local histories to `ExpressionRecord` is realized as
four pure constructor functions (Section 4). Each constructor:

```text
1. reads the originating record via its public accessors only
2. constructs an ExpressionItem with the correct ExpressionSource tag
3. computes the ExpressionShape via a pure function over item.text
4. computes the ExpressionFeatureVector via a pure function over shape
5. computes the ReadabilityPrediction via the predictor wrapper
6. returns the ExpressionRecord
```

Boundedness:

```text
- text is truncated to EXPRESSION_TEXT_MAX_LEN
- token-derived features cap at EXPRESSION_TOKEN_MAX_COUNT
- feature ratios are Fractions in [0, 1] by construction
- the constructor performs O(len(text)) work; no recursion over history
- the constructor does NOT iterate other histories
```

Locality:

```text
- imports from brain.development.output / .worldlet / .repl only
  through their public read accessors
- imports from brain.ui.transcript only through its public read
  accessors
- no import of brain.tick, brain.llm, brain.tlica, tools, or scenarios
- no use of os, subprocess, socket, urllib, http, requests, pathlib
  for writing, or any I/O sink
```

The Step 6 catalog patch will extend `tools.import_audit` coverage to
the new expression module(s) under the same rules already covering
`brain/ui/`.

---

## 10. Anti-Goodhart rules

Re-stated as a single normative block (also covered by predictor
Section 7.1; this section is the canonical statement that corrigenda
and the catalog patch plan will cite):

```text
A. Empty / whitespace-only items score Fraction(0).
B. Items whose printable_ratio is below a frozen PRINTABLE_FLOOR are
   capped at PRINTABLE_CAP < 1.
C. Repetition alone never increases the score; the
   repetition_penalty_basis is a penalty term, not a reward term.
D. Length alone never increases the score above LENGTH_CAP < 1; once
   length_chars hits LENGTH_CAP_THRESHOLD, further length growth does
   not raise the score.
E. Reserved-token collisions cap the score at RESERVED_CAP < 1.
F. A single token repeated N times scores no higher than the same
   token occurring once.
G. The score combinator is Fraction-only; no float, no math.* on
   features, no rounding.
H. Identical (ExpressionItem, predictor_tag) always produce identical
   ReadabilityPrediction (modulo tick_at_predict).
I. No combinator constant depends on a global, a random source, a
   clock, or any I/O.
```

Each rule maps to at least one fixture case in the Step 8 fixture
roster (planned, not yet written):

```text
A -> readability_predictor_empty_item.py
B -> readability_predictor_low_printable.py
C -> readability_predictor_repetition_only.py
D -> readability_predictor_length_cap.py
E -> readability_predictor_reserved_collision.py
F -> readability_predictor_single_token_repeat.py
G -> readability_predictor_fraction_exact.py
H -> readability_predictor_determinism.py
I -> covered by predictor_purity import-audit row
```

The actual fixture filenames are confirmed by the Step 4 catalog patch
plan.

---

## 11. Non-mutating inspection of OutputHistory / WorldletHistory /
ProtoBasicHistory / OperatorTranscript

The bridge constructors **inspect** the four source histories; they do
not mutate them. The properties enforcing this:

```text
M1  All source records (OutputEcho, ProtoBasicLine, WorldletAttempt,
    TranscriptEntry) are frozen dataclasses; this is already true in
    the codebase as of v0.11.
M2  Bridge constructors read only public accessor fields; they do not
    call any "register", "append", or "promote" method on the source
    histories.
M3  Bridge constructors do not register callbacks on any source
    history.
M4  Bridge constructors do not append to OutputHistory /
    WorldletHistory / ProtoBasicHistory / OperatorTranscript.
M5  Appending an ExpressionRecord to ExpressionHistory does not, by
    construction, alter any source history. Source histories are
    referenced only via stable IDs in ExpressionProvenance.
M6  The Operator TUI session, if a UI bridge is later authorized
    (Step 10), reads ExpressionHistory through expression_history_view
    only; it does not call append_expression_record itself.
```

Re-statement of the one-way bridge from the synthesis:

```text
OutputHistory        ┐
WorldletHistory      ├─► (read-only inspection) ─► ExpressionRecord ─► ExpressionHistory
ProtoBasicHistory    │                                                          │
OperatorTranscript   ┘                                                          ▼
                                                                ReadabilityPrediction (local only)
```

Reverse mutation is forbidden by the locality rules `L1`–`L7` and the
mutation rules `M1`–`M6`.

---

## 12. Out-of-scope (re-affirmed)

The kickoff does **not** introduce or assume any of:

```text
- real language-model scoring
- a natural-language teacher / corrector / audience model
- social feedback, multi-agent dialogue, or chat
- Mode B reflective planning or goal-conditioned action
- external corpus or vocabulary
- file I/O, network I/O, shell, subprocess
- PerceptEvent promotion from expression evidence
- tick() semantic changes
- TLICA runtime mutation or new Lean-bound rows
- weakening of existing I-* safety rows
- scenario / trace schema changes
- new external dependencies
```

Any future proposal that would require one of these escalates by
opening a new campaign step or a new campaign, not by extending this
kickoff.

---

## 13. Next artifact

The next campaign step (Step 3) produces:

```text
PHASE3_5_EXPRESSION_READABILITY_CORRIGENDA.md
```

The corrigenda will:

```text
- audit each contract above for clarity and scope
- enforce the four "readability != X" distinctions in normative language
- confirm or amend the locked ExpressionSource variant set
- confirm or amend the feature definitions and their bounds
- confirm or amend the anti-Goodhart rules
- decide the catalog row statuses (REQUIRED / STRUCTURAL / OBSERVED /
  NOT-EXERCISED) for the proposed rows
- confirm that ExpressionHistory remains process-local only
- decide whether any UI inspection is authorized in this campaign or
  deferred to a later one
```

After the corrigenda, Step 4 is the catalog patch plan; Step 5 is the
explicit review gate; only after the gate opens may any runtime code
or catalog row land.
