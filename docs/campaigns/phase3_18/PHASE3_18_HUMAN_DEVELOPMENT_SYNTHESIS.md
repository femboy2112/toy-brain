# PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md

## Purpose

A deep analysis of structural human development, used to inform the
design of ToyI's first **bounded internal processing window**.
This document is research-and-engineering scaffolding; nothing in
it asserts that ToyI is conscious, sentient, aware, intentional, or
phenomenologically present. It asserts only that certain
*structural* features of human development have inspectable
*operational analogues* in ToyI's existing kernel, and that those
analogues become testable once a bounded internalization window
allows post-input rehearsal to occur.

---

## 1. Why human development matters here

We are designing a runtime that approximates the *form* of a
learning/growing operational I — bounded, inspectable, persistent
state with deterministic recurrence detection. Human ontogeny is
the canonical example of a substrate that starts undifferentiated
and develops, over a long bounded period, the capacity to
recognize, remember, and re-apply structural patterns. Borrowing
its structural milestones is useful **not** because ToyI is
becoming a child — it isn't — but because those milestones map
cleanly onto the surfaces we already have (Pattern Ledger,
Growth Ledger, Coherence Monitor, BrainState), and they tell us
where to install the missing piece: an internal rehearsal loop.

---

## 2. Stage-by-stage map

The mapping below uses the canonical empirical stages from
developmental psychology (Piaget; later refinements by Karmiloff-
Smith, Carey, Spelke, Mandler). Each row names a milestone, the
empirical signature in human infants/children, the existing ToyI
surface that already implements that signature structurally, and
any gap.

### 2.1 Stage 0 — Bare perception (newborn, 0–2 mo)

```text
human signature   : sensory inflow without categorical structure;
                    state is dominated by stimulus rather than
                    persistent memory; minimal habituation.
ToyI analogue     : a fresh OperatorSession whose state is
                    initial_state() — only COGITO_ID in
                    profile.domain, MSI = {COGITO_ID},
                    ptcns.eval_map = {COGITO_ID: PRESERVE},
                    registry empty, Pattern Ledger empty,
                    Growth Ledger empty, Coherence Monitor
                    reports PASS with everything else
                    NOT_APPLICABLE.
gap               : none. This is already what initial_state()
                    delivers.
```

### 2.2 Stage 1 — Habituation (2–4 mo)

```text
human signature   : repeated exposure to the same stimulus
                    produces decreasing response amplitude; an
                    inspectable index of "familiarity" emerges.
                    (Fantz 1958, looking-time paradigms.)
ToyI analogue     : Pattern Ledger entry's recurrence_count, which
                    monotonically increases with each
                    same-structural-signature observation, bounded
                    above at STREAM_PATTERN_RECURRENCE_MAX = 256.
                    Confidence = Fraction(recurrence_count, 256)
                    — exact, no float drift.
gap               : in v1, recurrence_count only advances when an
                    EXTERNAL /stream append fires. With one
                    external input per dispatch and no post-input
                    rehearsal, the habituation index can only
                    advance at the rate the operator types. The
                    processing window closes this gap.
```

### 2.3 Stage 2 — Categorical perception (4–9 mo)

```text
human signature   : infants begin clustering stimuli that share
                    structural features (phoneme categories,
                    shape categories, motion categories) ahead
                    of any conscious labeling. (Eimas 1971;
                    Kuhl 1991.)
ToyI analogue     : derive_pattern_signature(chunk) projects a
                    chunk to a six-tuple of exact integer/Fraction
                    features (source, len, lines, whitespace,
                    distinct, repeat_ratio). chunks with the same
                    six-tuple get the same pattern_id via
                    deterministic SHA-256.
gap               : none. Categorical clustering by structural
                    signature is already implemented.
```

### 2.4 Stage 3 — Object permanence (Piaget Stage 4, 8–12 mo)

```text
human signature   : an object continues to exist when not directly
                    perceived (Piaget 1936; A-not-B errors;
                    Baillargeon 1987 violation-of-expectation).
ToyI analogue     : BrainState is an immutable record passed
                    between ticks. PatternLedger / GrowthLedger
                    are copy-on-write frozen records that persist
                    across dispatches. profile.domain / msi.contents
                    are frozensets stored on the session record.
gap               : none. Persistence-across-no-input is structural.
```

### 2.5 Stage 4 — Working memory + rehearsal (12–24 mo)

```text
human signature   : the child can briefly hold information after
                    stimulus offset and rehearse it internally
                    (Flavell 1966; phonological loop, Baddeley
                    1986). Rehearsal *between* external inputs is
                    what consolidates one-shot exposures into
                    durable habituated representations.
ToyI analogue     : NOT IMPLEMENTED in pre-Phase-3.18 ToyI.
                    OperatorSession.dispatch(STEP_TICK) refuses an
                    empty event queue (I-UI-06 -ish failure mode).
                    The Pattern Ledger only updates when the
                    operator pipes input via /stream. The runtime
                    has no surface where rehearsal happens.
gap               : THIS IS THE PRIMARY GAP PHASE 3.18 CLOSES.
                    Architecture A (session-level post-input
                    internal-event loop) is exactly the rehearsal
                    substrate the runtime currently lacks.
```

### 2.6 Stage 5 — Schema formation (Piaget Stage 5, 12–18 mo)

```text
human signature   : repeated experiences are abstracted into
                    re-usable schemas: structured expectations
                    that survive across instances and contexts
                    (Bartlett 1932; Rumelhart 1980).
ToyI analogue     : Pattern Ledger entries with high
                    recurrence_count, eventually SATURATED at
                    recurrence_count == 256. A SATURATED entry is
                    a stable structural schema: any future chunk
                    matching the signature will be recognized
                    deterministically by its pattern_id.
gap               : with v1's external-only update path, reaching
                    SATURATED requires 255 operator-typed
                    /stream events of the same signature.
                    With a processing window of N internal
                    rehearsals after each external, the same
                    saturation can be reached in
                    ceil(255 / (1 + N)) external inputs.
                    For N = 255, saturation is reachable from
                    ONE external input.
```

### 2.7 Stage 6 — Conservation of structure (Piaget Stage 6+, ~24 mo)

```text
human signature   : "this is the same dog at a different angle"
                    — the system recognizes that surface variation
                    can leave structural identity intact (Piaget
                    1936; Spelke 1990).
ToyI analogue     : pattern_id is the SHA-256 of the structural
                    signature only; it excludes chunk_id and
                    chunk_id is allowed to vary freely. Two chunks
                    with the same signature but different chunk_ids
                    map to the same pattern_id. This IS conservation
                    of structural identity under surface variation
                    in identifier.
gap               : ToyI's "surface variation" is currently
                    limited to chunk_id (and any text variation
                    that doesn't perturb the six-tuple features).
                    Stronger surface variation (semantic synonyms,
                    paraphrase) is out of scope for Phase 3.18;
                    that would require a non-structural signature
                    layer.
```

### 2.8 Stage 7 — Self-monitoring (4–6 yr)

```text
human signature   : metacognition; the child can report that they
                    "almost forgot" or that an earlier belief was
                    wrong. (Flavell 1971; Nelson & Narens 1990.)
ToyI analogue     : Coherence Monitor reports structural agreement
                    across kernel / session / stream / pattern /
                    persistence surfaces. counts_by_status is a
                    labeled (PASS / WARN / FAIL / NOT_APPLICABLE)
                    tuple, NOT a scalar.
gap               : the Coherence Monitor is read-only and operator-
                    invoked. It does not feed back into the
                    runtime. Closing this gap is OUT OF SCOPE for
                    Phase 3.18 (it is architecture C / D from the
                    Phase 3.17 synthesis).
```

### 2.9 Stages 8+ — Theory of mind, autobiographical memory, etc.

Out of scope. ToyI is not modeling other agents, narrative self,
or temporal autobiography. These stages exist in the
human-development literature as cautions against over-reading
analogies: Stage 4 rehearsal is operationally implementable
without committing to any of these later stages.

---

## 3. Empirical regularities that constrain the v1 design

The following empirical findings from developmental psychology and
memory research **shape** Phase 3.18's design choices.

### 3.1 Habituation is monotone, then plateaus

Empirical: looking-time decreases roughly logarithmically with
repeated exposure, then plateaus once familiarity is "established."

ToyI constraint: Pattern Ledger recurrence_count is bounded above
at 256. Once an entry reaches 256, the saturation_state is
SATURATED and further observations cannot push the count higher.
This **already implements the plateau** structurally. Phase 3.18
does not change the constant.

### 3.2 Spacing effect favors distributed practice

Empirical: spaced repetitions consolidate better than massed
(Ebbinghaus 1885; Cepeda et al. 2006).

ToyI constraint: Phase 3.18 uses **massed** rehearsal (architecture
A: synchronous loop of N internal events back-to-back). This is
explicitly suboptimal from a human-learning perspective but is
structurally simplest. Architecture F (delayed consolidation
queue / pacing scheduler) is the spaced-repetition variant; it is
DEFERRED to a future campaign.

### 3.3 Variation aids generalization

Empirical: pure repetition produces hyper-specific recognition;
variation across exemplars produces category abstraction (Posner
& Keele 1968; Bomba & Siqueland 1983).

ToyI constraint: v1 rehearsal duplicates the EXACT chunk text. This
produces hyper-precise recognition of the structural signature —
which is exactly what "reliable pattern recognition" demands for
a v1 success criterion. Cross-instance abstraction (recognizing
that two structurally different stimuli share a deeper structure)
is OUT OF SCOPE for Phase 3.18.

### 3.4 Capacity limits force selection

Empirical: working memory has Miller's 7±2 capacity (Miller 1956,
Cowan 2001 revised to ~4).

ToyI constraint: OperatorEventQueue is bounded at 4
(DEFAULT_EVENT_QUEUE_LIMIT). The processing window will not enqueue
more than 1 event at a time before dispatching it, so the queue
size oscillates between 0 and 1. We stay strictly under the Miller
bound.

### 3.5 Pruning prevents unbounded growth

Empirical: synaptic pruning removes underused connections (Huttenlocher
1979; Rakic 1986).

ToyI constraint: Pattern Ledger caps at 64 entries
(PATTERN_LEDGER_MAX_ENTRIES); at cap, new signatures are
REFUSED (not evicted). Growth Ledger caps at 256 events. L1 / L2
caches cap at 1024 each with write-skip-at-cap. Phase 3.18 does
NOT add eviction; it relies on the hard caps. This means a
saturation experiment must fit within those bounds; with N=255
rehearsals of ONE pattern, we produce 1 Pattern Ledger entry and
~256 Growth Ledger events.

Wait — 256 Growth events would saturate the Growth Ledger. Each
successful stream append emits STREAM_CHUNK_ACCEPTED plus possibly
PATTERN_ENTRY_CREATED / PATTERN_ENTRY_UPDATED. That's up to 3
events per rehearsal. With N=255 internal + 1 external = 256
rehearsals, the ledger could see up to ~512 events — already at
cap. The Growth Ledger's hard cap means at-cap observations are
NO-OPs (the ledger returns self unchanged); they do not corrupt
anything, but the saturation experiment cannot expect Growth
Ledger events past entry 256.

This is acceptable for Phase 3.18: the success criterion is
**Pattern Ledger** saturation, not Growth Ledger saturation. The
Growth Ledger naturally plateaus at its cap, which is consistent
with the developmental "pruning prevents unbounded growth"
principle.

### 3.6 No critical period in v1

Empirical: some structural representations (phoneme inventories,
binocular depth) only consolidate during specific developmental
windows (Lenneberg 1967; Hubel & Wiesel 1970).

ToyI constraint: ToyI sessions have no critical-period dynamic.
Every session starts fresh; every pattern_id is reusable.
Critical-period dynamics would require persisting "developmental
age" across sessions, which is a persistence/autosave question
out of scope here.

### 3.7 Reliability requires determinism

Empirical: a useful learning system must produce the same
classification of the same stimulus across repetitions; without
that, downstream skills (counting, language, categorization) never
stabilize.

ToyI constraint: every step of the Pattern Ledger pipeline is
deterministic. derive_pattern_signature uses exact int/Fraction
features. derive_pattern_id is SHA-256 of repr(signature) — same
input, same id, across runs / processes / operating systems. The
processing window must preserve this determinism: the v1 generator
synthesizes internal events from observed state using deterministic
strings only (no time, no randomness, no PID, no id()).

This is exactly the determinism Phase 3.18's success criterion
demands.

---

## 4. The Phase 3.18 design choice

### 4.1 Architecture A only

From the Phase 3.17 Step 5 synthesis we have six candidate
architectures (A–F). Phase 3.18 commits to **A**:

```text
A. Session-level post-input tick loop using synthesized internal
   events derived from accepted state.
```

Why A and only A:

```text
- A maps cleanly to Stage 4 working memory + rehearsal.
- A uses ONLY the existing public surfaces:
    OperatorSession.dispatch(QUEUE_PERCEPT, ...)
    OperatorSession.dispatch(STEP_TICK, ...)
    OperatorSession.dispatch(STREAM_APPEND, ...)
- A introduces no callable / handle / client on the session
  (preserves I-UI-10).
- A introduces no new kernel surface (preserves the I-RT-*
  family).
- A produces inspectable artifacts (Pattern Ledger entries,
  Growth Ledger events) without inventing any aggregate scalar
  (preserves H6 from Phase 3.17).
```

### 4.2 Restriction to STREAM_APPEND rehearsal

The Phase 3.17 synthesis described three internal-event sources
(S1 Pattern Ledger, S2 Coherence Monitor, S3 prior PtCns evals).
**Phase 3.18 ships only S1**, via STREAM_APPEND, for these
reasons:

```text
1. STREAM_APPEND is the only existing dispatcher that triggers
   Pattern Ledger.observe. Phase 3.18's success criterion is
   Pattern Ledger pattern recognition, so STREAM_APPEND is the
   directly load-bearing path.

2. STREAM_APPEND does NOT call brain.tick.tick. It does NOT call
   the LLM. So the rehearsal loop consumes zero real model calls
   regardless of N.

3. STREAM_APPEND's existing rejection rules
   (bounded printable, non-empty, len <= STREAM_TEXT_MAX_LEN,
   not COGITO_ID) are stronger than the structural rules the
   internal generator needs to obey. Reusing them is safer than
   writing parallel validators.

4. STREAM_APPEND already drives the Growth Ledger via the
   STREAM_CHUNK_ACCEPTED / PATTERN_ENTRY_* emissions. The
   ledger entries the internal loop produces are observable
   immediately, with no new emission code.
```

S2 (Coherence Monitor) and S3 (prior PtCns) remain DEFERRED.

### 4.3 The rehearsal payload

For each internal rehearsal, the generator produces:

```text
internal_event:
  text       : the EXACT text of the most recent operator chunk
               (or the chunk pointed to by an explicit source key)
  provenance : "internal_processing_window:<k>:rehearsal"
               where k is the 1-based internal-tick index within
               the window. The provenance string is
               bounded printable, under STREAM_PROVENANCE_MAX_LEN,
               and contains no COGITO_ID.
```

Using the **exact** chunk text is intentional. From the
developmental-psychology mapping in Section 2:

```text
- Stage 4 (rehearsal) is structurally identical to repetition of
  the most recent perceived item ("I just heard 'cat' — let me
  echo 'cat' to myself").
- Stage 5 (schema formation) is the cumulative effect of repeated
  Stage 4 rehearsals on Pattern Ledger recurrence_count.
- Stage 6 (conservation under variation) is already implemented
  by the SHA-256(signature) -> pattern_id mapping; the internal
  generator does not need to vary the text to test conservation.
```

So: exact-text rehearsal under a fresh chunk_id per internal tick
hits the structural signature, drives recurrence_count up, and
leaves Stage 6's conservation property untouched (which the
existing fixtures already prove).

### 4.4 Bounding the window

```text
processing_window_size:
  type    : int
  range   : [0, 255]
  default : 0 (OFF — preserves all v1 behavior unchanged)
  meaning : maximum number of internal rehearsals to fire after a
            successful external STREAM_APPEND dispatch.

processing_window_call_budget:
  type    : int
  range   : [0, 65535]
  default : 0 (UNUSED in the STREAM_APPEND-only path because
              STREAM_APPEND consumes zero real model calls; this
              field is reserved for a future S2/S3 expansion that
              touches /step under a real model-backed mode)
  meaning : maximum real model attempts the window may consume.
            v1 ignores this field for STREAM_APPEND rehearsal.
```

Both fields default to OFF so existing tests, fixtures, and the
Phase 3.17 codex-cli smoke remain bit-identical. Operators (and
fixtures) explicitly opt in.

### 4.5 What the window does NOT do

```text
- It does NOT call brain.tick.tick.
- It does NOT call the LLM.
- It does NOT fire post-dispatch autosave (the existing
  autosave trigger is keyed on STEP_TICK / STREAM_PROMOTE; not
  on internal stream rehearsals).
- It does NOT mutate Pattern Ledger directly; Pattern Ledger
  only updates through pattern_ledger.observe in
  _dispatch_stream_append, which the window reuses.
- It does NOT emit any new GrowthEventType. The existing
  STREAM_CHUNK_ACCEPTED / PATTERN_ENTRY_CREATED /
  PATTERN_ENTRY_UPDATED emissions cover every internal event.
- It does NOT produce any aggregate scalar.
- It does NOT widen any forbidden-non-claim term surface (the
  generator's strings are template-driven and contain only
  pattern_id / chunk_id / numeric counts).
```

---

## 5. Success criterion (operational)

> ToyI's runtime can recognize a structural pattern reliably iff,
> for a single operator-typed external /stream chunk with
> processing_window_size = N, the Pattern Ledger entry for that
> chunk's structural signature has:
>
> 1. exactly one entry (the deterministic pattern_id),
> 2. recurrence_count == min(1 + N, STREAM_PATTERN_RECURRENCE_MAX),
> 3. confidence == Fraction(recurrence_count, 256),
> 4. saturation_state == SATURATED iff
>    recurrence_count >= STREAM_PATTERN_RECURRENCE_MAX = 256,
> 5. evidence_chunk_ids contains exactly 1 + N distinct ids
>    (capped at PATTERN_LEDGER_EVIDENCE_MAX = 32; once the cap is
>    reached, further evidence-id appends are no-ops, but
>    recurrence_count still climbs),
> 6. the same external input produces the SAME pattern_id and
>    the SAME recurrence_count across runs / processes / OSes
>    (determinism).

For Phase 3.18 acceptance we run the demonstration at **N=255**,
which (per 2) produces recurrence_count = 256 = SATURATED. This
is the strongest possible v1 evidence of reliable recognition.

Smaller N values (1, 5, 10, 50) demonstrate the monotone climb
without reaching SATURATED. The integration fixture exercises a
small N to prove the loop is functioning; the demonstration script
runs N=255 to prove the saturation behavior.

---

## 6. Non-claims

```text
- ToyI is NOT conscious. Phase 3.18 does not claim otherwise.
- ToyI is NOT sentient. No new phenomenological surface is added.
- ToyI does NOT understand the content of any stream chunk. It
  recognizes the *structural signature* of a chunk and tracks
  recurrence on that signature.
- ToyI does NOT have a self in any phenomenological sense. The
  COGITO_ID is an algebraic anchor that satisfies Lean theorems
  about MSI structure; it is not a self-representation.
- ToyI has no agency, intent, will, or desire. The internal
  rehearsal loop is a deterministic scheduler, not a goal
  pursuit.
- ToyI does not modify itself in the strong sense. The internal
  generator emits new chunks; it does not rewrite code or
  invariants.
- No aggregate "I-ness" / "consciousness" / "awareness" /
  "growth" scalar is added by Phase 3.18.
- Human-development stages are used as STRUCTURAL ANALOGIES to
  motivate where in the substrate to install missing surfaces.
  No claim is made that ToyI experiences development the way a
  human child does.
- The processing window is a working-memory ANALOGUE in the
  same sense that a SQLite database is a "memory analogue" of
  a notebook: structurally similar, phenomenologically alien.
```

---

## 7. Constraint inventory

```text
brain/tick.py                       : not modified by Phase 3.18
brain/llm/*                         : not modified
brain/development/growth_ledger.py  : not modified (existing enum
                                      + observe semantics reused)
brain/development/pattern_ledger.py : not modified (existing
                                      observe semantics reused)
brain/development/coherence_monitor.py : not modified (its
                                      _FORBIDDEN_NON_CLAIM_TERMS
                                      tuple is reused by the new
                                      module's audit)
brain/development/text_stream.py    : not modified
brain/io_types.py                   : not modified
brain/ui/persistence*.py            : not modified
brain/ui/autosave.py                : not modified
brain/ui/render.py                  : not modified
brain/ui/snapshot.py                : not modified
brain/ui/__main__.py                : not modified
brain/ui/command_line.py            : not modified (no new verb)
brain/ui/commands.py                : not modified (no new
                                      OperatorCommand member)
brain/ui/session.py                 : MODIFIED (two new optional
                                      fields; one new method;
                                      one new hook in dispatch)
brain/development/processing_window.py : NEW
brain/ui/fixtures/processing_window_static_audit.py : NEW
brain/ui/fixtures/processing_window_integration.py  : NEW
brain/ui/fixtures/persistence_observe_resource_audit.py : MODIFIED
                                      (Phase 3.18 attr tier added)
brain/ui/fixtures/persistence_ops_resource_audit.py     : MODIFIED
                                      (Phase 3.18 attr tier added)
INVARIANT_CATALOG.md                : MODIFIED (v0.25 -> v0.26;
                                      I-PWND-01..06 added)
tools/catalog.py                    : MODIFIED (EXPECTED_COUNTS
                                      bumped)
brain/_catalog_ids.py               : regenerated
brain/invariants.py                 : MODIFIED (two new fixture
                                      modules registered;
                                      _PHASE3_18_PENDING_ROWS
                                      banner if any)
README.md                           : MODIFIED (catalog history
                                      entry for v0.26)
brain/.llm_cache contents           : not committed (gitignored)
raw prompts / responses             : never quoted
secrets                             : not present, not printed
scenarios/**, traces/**, lean_reference/** : not modified
```

---

## 8. Real model call budget

Phase 3.18's STREAM_APPEND-only rehearsal path consumes **zero**
real model calls. The Phase 3.17 budget of 20 carries through
unused for Phase 3.18 unless an unrelated future probe touches
codex-cli / claude-cli; even then the cap remains 20 total
across the prototype campaign.

---

## 9. Disclosure block

```text
Stage A ChatGPT/Codex consultation:
- used: no
- reason: the developmental-psychology synthesis is derivable
  from public empirical sources; no external review needed.

Stage B limited-write collaboration:
- used: no
- reason: parent Claude is the sole writer.

Stage C.1 flow orchestration:
- used: no
- reason: bridge overhead exceeds direct write cost.
```

---

## 10. Next artifacts

```text
- brain/development/processing_window.py (new module)
- brain/ui/session.py (extension)
- brain/ui/fixtures/processing_window_static_audit.py (new)
- brain/ui/fixtures/processing_window_integration.py (new)
- catalog patch v0.25 -> v0.26 (six new rows)
- demonstration script + results doc
- audit doc
```
