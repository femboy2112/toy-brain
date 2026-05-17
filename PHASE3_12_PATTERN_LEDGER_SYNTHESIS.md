# PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md

## Purpose

Phase 3.12c follows directly from the Step 6 observatory report
(`PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md`). Step 6 found that
the existing `/stream` → `/stream-promote` → `/step` route is coherent,
that bounded growth through `tick()` works, and that contradiction
pressure is correctly ignored at the truth layer. It also found that
**recurrence evidence exists but is not ledgered**: identical motifs
produce identical chunk text inside `TextStreamHistory`, alternation and
novelty are visible in stored fields, and saturation caps candidates at
`STREAM_PROMOTION_MAX=64`, but the dispatch surface for
`/stream-summary` and `/stream-candidates` only sets `active_view = ...`.
There is no persistent inspectable record that says "this pattern has
been seen N times across these chunks and these candidates."

The job of this synthesis is to define the **Pattern Ledger** concept
that closes that observability and growth-measurement gap, *without*
adding semantic truth, agency, PtCns evaluation, MSI mutation, raw-text
→ `COGITO_ID` mapping, hidden LLM calls, or hidden persistence. The
synthesis is documentation only. It does not implement, fixture, or
catalog-row the ledger; those steps remain behind Review Gate B
(`CURRENT_CAMPAIGN.md` Step 10).

This document does not edit `brain/**`, `tools/**`,
`INVARIANT_CATALOG.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**`. It introduces no fixture, no committed helper, and no
runtime behavior change.

## Current evidence from Step 6

Quoted from `PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md` and the
underlying probe output:

- **Repeated motifs.** 5× `/stream alpha alpha alpha` produces 5
  `TextStreamChunk` records with identical text and 5 distinct
  `StreamPromotionCandidate` records (`promo-strm-chunk-1..5`).
  Distinct chunk texts after the run: 1. Recurrence is structural and
  visible in the stored fields, but the dispatch return only says
  `view = stream_summary` / `view = stream_candidates`.

- **Alternating motifs.** 4× `/stream alpha beta alpha beta` produces 4
  identical-text chunks with 4 distinct chunk and candidate IDs. The
  alternation lives inside the chunk text, not as a recognized pattern
  signature.

- **Novelty after repetition.** 3× `alpha alpha alpha`, then `gamma
  novelty after repetition`, then `delta surprise` produces 5 chunks
  whose chunk texts are correctly distinct. No candidate-id collision,
  no profile/MSI mutation, no truth claim.

- **Contradiction-pressure text.** `/stream door=open` / `/stream
  door=closed` / repeat: 4 chunks accepted, `profile_domain` stays at
  `['__cogito__']`, `msi_contents` stays at `['__cogito__']`, no
  `PtCns` mutation. The text-stream layer correctly refuses to
  adjudicate.

- **Saturation.** 120× `/stream spam motif` produces 120 chunks (cap
  `STREAM_HISTORY_MAX_CHUNKS=256` — under cap) and 64 candidates
  (exactly `STREAM_PROMOTION_MAX=64` — saturated). Over-length
  `/stream` is parse-rejected (`/stream text exceeds 1024 chars`),
  never reaching dispatch.

- **Bounded growth via tick.** Only successful `/step` adds an entry to
  `profile.domain`, `msi.contents`, and the content registry, and
  advances `tick_counter` by one. Empty-queue `/step` and unconfigured
  `/load-session` produce bounded errors with no state mutation.

- **Persistence.** `/save-session` followed by `/load-session` into a
  fresh `OperatorSession` round-trips every recorded field exactly:
  `tick_counter`, `stream_chunks`, `stream_candidates`,
  `stream_chunk_serial`, `profile_domain`, `msi_contents`, registry
  size. The session DB is 73,728 bytes for the probe's 2-chunk /
  1-tick scenario.

- **Existing `StreamPattern`.** `I-STRM-06` already defines a bounded
  `StreamPattern` record with `recurrence_count` saturating at
  `STREAM_PATTERN_RECURRENCE_MAX`. `I-STRM-11` (anti-growth) guarantees
  spam cannot exceed that cap. `StreamPattern` is recurrence-backed
  structural evidence and explicitly *excludes* `PRESERVE` / `DAMAGE` /
  `PCE` / `Act` / `ModeOp` / `AgencyWitness` / `tick` callbacks.
  However, `StreamPattern` is a single record. There is no aggregate,
  persistent, inspectable ledger of *recognized* patterns across many
  chunks, sessions, and reports.

The summary is consistent with the operational definitions: coherent
(works), pattern-recognizing (partial — evidence stored, not ledgered),
growing (works), operational I (partial — anchor + bounded status, no
self-summary surface).

## Problem statement

The current text-stream substrate stores raw structural evidence
(`TextStreamChunk`, `TextStreamHistory`, `StreamFeatureVector`,
`SegmentCandidate`, `StreamPattern`, `StreamPromotionCandidate`) and the
operator session stores a bounded recent-history slice
(`stream_history`, `stream_candidates`). What is missing is:

```text
A bounded, persistent, inspectable, copy-on-write developmental record
of recurring structural patterns observed across many chunks (and
optionally across sessions), with deterministic identifiers, exact
Fraction confidence, saturation caps, and constructor rejection on
malformed records.
```

Without that record:

- repeated identical motifs vs alternation vs novelty are not
  surfaced as recognized recurrence at the dispatch level;
- growth across many ticks cannot be measured beyond the
  already-saturating `stream_candidates` slice (which the substrate
  trims at 64);
- a future Coherence Monitor cannot pose "did the recognized pattern
  set change in this tick?" without re-deriving it;
- a future Operational SelfModel has no bounded source of "what
  recurring structures has the system been exposed to?".

## Pattern Ledger definition

**Pattern Ledger** is a bounded developmental record of recurring
structural patterns observed in stream/developmental histories. It sits
strictly *below* truth, agency, `PtCns`, `MSI`, and semantic
interpretation, and strictly *above* `TextStreamChunk` /
`TextStreamHistory` / `StreamPromotionCandidate`. It is a *summary
substrate*, not a runtime control surface.

It is to `StreamPattern` what `OperatorTranscript` is to the typed
local command line: an aggregating bounded read-only collection layered
on top of the underlying records.

It carries:

- structural pattern identifiers,
- bounded signatures (already constrained by `STREAM_PATTERN_SIG_MAX`),
- bounded evidence lists referencing chunk / candidate IDs,
- exact `Fraction` recurrence/confidence,
- bounded first/last tick metadata,
- a closed enumeration of saturation states.

It does **not** carry:

- raw text payload (text lives in `TextStreamChunk`),
- a `PtCns` eval (`PRESERVE` / `DAMAGE`),
- an agency or `Act` field,
- a callable, file handle, socket, subprocess handle, LLM client, or
  path object,
- any reference to `COGITO_ID`,
- any tick callback.

A typed read-only operator command (proposed working name
`/pattern-ledger`) would surface a bounded snapshot view, mirroring how
`/stream-summary` and `/session-status` already work.

## Proposed record shape

Pseudocode — not implementation. Field names, defaults, and bounds are
illustrative and may be refined in Step 8 / Step 9.

```python
class PatternLedgerSourceKind(Enum):
    OPERATOR     = "operator"
    SYSTEM       = "system"
    PROBE_ECHO   = "probe_echo"
    GENERATED    = "generated"

class PatternLedgerSaturationState(Enum):
    OPEN         = "open"       # below recurrence cap
    SATURATED    = "saturated"  # equals recurrence cap
    QUIESCED     = "quiesced"   # no new evidence in last N ticks


@dataclass(frozen=True, slots=True)
class PatternLedgerEntry:
    pattern_id:             str
    signature:              tuple[str, ...]
    evidence_chunk_ids:     tuple[str, ...]
    evidence_candidate_ids: tuple[str, ...]
    recurrence_count:       int
    first_seen_tick:        int
    last_seen_tick:         int
    source_kind:            PatternLedgerSourceKind
    confidence:             Fraction
    saturation_state:       PatternLedgerSaturationState
    provenance:             str

    # Constructor bounds (proposed):
    #   pattern_id           : printable, non-empty, != COGITO_ID,
    #                          len <= PATTERN_LEDGER_ID_MAX
    #   signature            : tuple of printable strings,
    #                          1 <= len <= STREAM_PATTERN_SIG_MAX (16),
    #                          each element bounded printable,
    #                          no element equal to COGITO_ID
    #   evidence_chunk_ids   : tuple of printable strings,
    #                          0 <= len <= PATTERN_LEDGER_EVIDENCE_MAX,
    #                          all distinct, none equal to COGITO_ID
    #   evidence_candidate_ids:
    #                          same shape, same bounds, same exclusions
    #   recurrence_count     : int,
    #                          STREAM_PATTERN_RECURRENCE_MIN <= n
    #                          <= STREAM_PATTERN_RECURRENCE_MAX (saturates)
    #   first_seen_tick      : int >= 0
    #   last_seen_tick       : int >= first_seen_tick
    #   source_kind          : PatternLedgerSourceKind
    #   confidence           : Fraction, 0 <= c <= 1
    #   saturation_state     : PatternLedgerSaturationState
    #   provenance           : printable, non-empty,
    #                          len <= STREAM_PROVENANCE_MAX_LEN (64)


@dataclass(frozen=True, slots=True)
class PatternLedger:
    entries:               tuple[PatternLedgerEntry, ...] = ()
    max_entries:           int = PATTERN_LEDGER_MAX_ENTRIES
    max_evidence_per_entry:int = PATTERN_LEDGER_EVIDENCE_MAX

    def observe(self, chunk, candidate, *, current_tick) -> "PatternLedger":
        """Return a NEW PatternLedger that records one observation
        (copy-on-write). Saturates recurrence_count; bumps last_seen_tick;
        extends evidence_chunk_ids / evidence_candidate_ids up to the
        cap; never mutates self. Never calls tick(). Never touches
        BrainState / MSI / PtCns / registry / agency / LLM."""
        ...

    def snapshot(self) -> tuple[PatternLedgerEntrySummary, ...]:
        """Return a bounded printable read-only summary view, suitable
        for /pattern-ledger dispatch status text and the renderer."""
        ...
```

Proposed constants (numbers are illustrative — Step 9 catalog patch
planning would fix exact values and tie them into the existing
`STREAM_*` bound family):

```text
PATTERN_LEDGER_MAX_ENTRIES         ~  64   (matches STREAM_PROMOTION_MAX)
PATTERN_LEDGER_EVIDENCE_MAX        ~  32
PATTERN_LEDGER_ID_MAX              ~  64
(re-uses STREAM_PATTERN_RECURRENCE_MIN / _MAX, STREAM_PATTERN_SIG_MAX,
 STREAM_PROVENANCE_MAX_LEN already defined in brain.development.text_stream)
```

`PatternLedger.observe(...)` is **the sole non-construction entry
point**. It does not take a `BrainState`, it does not take an
`LLMClient`, it does not take a callable. It is pure over its inputs
and emits a new `PatternLedger`. A `/step` handler that wished to
attach a ledger observation would call it explicitly *after* `tick()`
on the operator session, mirroring how `/stream-promote` already lays
its work down without entering `tick()`.

## Bounds and invariants

The Pattern Ledger must respect every bound the existing TLICA /
Phase 3.7 / Phase 3.8 / Phase 3.10 / Phase 3.11 work already enforces.
Specifically:

- **`COGITO_ID` reservation.** `pattern_id`, every element of
  `signature`, every element of `evidence_chunk_ids` and
  `evidence_candidate_ids`, and `provenance` are all **distinct from
  `COGITO_ID`**. The constructor must raise (`ValueError` naming the
  relevant row) on a `COGITO_ID`-equal value. This mirrors `I-STRM-02`
  / `I-STRM-07`.

- **No raw text → `COGITO_ID` mapping.** The ledger has no `text`
  field. Raw text remains under `TextStreamChunk`; the ledger only
  references chunk IDs.

- **No `BrainState` mutation.** `PatternLedger` does not import
  `brain.tick`. It does not construct or compare `BrainState`. It does
  not write to `profile`, `msi`, `ptcns`, or the registry.

- **No `tick()` call.** `PatternLedger` does not call
  `brain.tick.tick`. It does not register a tick callback. The Phase
  3.7 `I-STRM-10` discipline carries forward: the only way to advance
  the kernel runtime is `/step` → `_dispatch_step` → `tick()`.

- **No truth / agency / PtCns fields.** No `PRESERVE` / `DAMAGE` /
  `PCE` / `ProjectedPCE` / `Act` / `ModeOp` / `AgencyWitness` field.
  No `feasibleProjectedPCE`. No semantic truth label. No language
  label. No readability score.

- **No LLM client.** `PatternLedger` does not store, accept, or call
  any object with `eval_consistency`. The static AST audit envisioned
  for the new module rejects imports of `brain.llm`.

- **No I/O / network / shell / filesystem.** The module rejects
  imports of `os`, `os.system`, `subprocess`, `socket`, `urllib`,
  `http`, `requests`, `pathlib`, `tempfile`, `shutil`, and `curses`,
  in the spirit of `I-STRM-12`.

- **Exact arithmetic only.** Recurrence and confidence are computed
  with `int` and `Fraction`. No `float`, no `round`, no `math.*` on
  the count / statistic path (mirroring `I-STRM-14`).

- **Bounded max entries / bounded evidence list.** Both are
  enforced by the constructor; `observe(...)` saturates rather than
  growing past `max_entries` and rather than appending evidence past
  `max_evidence_per_entry`.

- **Deterministic pattern IDs.** `pattern_id` is derived from
  `signature` (a stable bounded function of the chunk's structural
  features), not from time, process state, randomness, hostname, PID,
  or memory address. The same signature on the same input must produce
  the same `pattern_id` across runs and across processes.

- **Constructor rejection.** Every bound above is enforced by
  raising on construction. The ledger does **not** silently clamp,
  truncate, replace, or substitute a malformed value with a default.

- **Copy-on-write only.** `PatternLedger.observe(...)`,
  `PatternLedger.prune(...)`, etc. return new `PatternLedger` records.
  `entries` is a `tuple`. The whole record is a frozen slotted
  dataclass. No mutation is performed in place.

- **No callable / handle storage.** No field is a callable, file
  handle, socket, subprocess handle, LLM client, or `pathlib.Path`.
  The fixture should re-use the `I-UI-10`-style runtime self-audit
  pattern.

## Anti-Goodhart / saturation policy

Pattern Ledger growth must resist trivial inflation. Specifically:

- **Repeated spam saturates, does not strengthen.** Repeated identical
  `/stream alpha alpha alpha` does not push `recurrence_count` past
  `STREAM_PATTERN_RECURRENCE_MAX` and does not append a 65th distinct
  entry past `max_entries`. Once a chunk's structural signature
  matches an existing entry, the entry's `recurrence_count` increments
  and its `evidence_chunk_ids` extends only up to
  `max_evidence_per_entry`; further duplicates are dropped at the
  evidence-list boundary, not silently merged into the count.

- **Long text does not boost confidence.** Confidence is a function of
  recurrence and signature stability, not chunk-text length. A chunk
  whose text is 1023 bytes long and a chunk whose text is 4 bytes long
  contribute the same recurrence increment when their structural
  signatures match.

- **Duplicate evidence does not inflate growth.** If the same
  `chunk_id` or `candidate_id` is offered to `observe(...)` twice
  against the same entry, the evidence list does not double-count it.
  Either the constructor rejects the duplicate, or `observe(...)`
  filters duplicates before extending the list. (Step 8 should pick
  one and lock it.)

- **Failed parse / promote / step does not count as pattern growth.**
  A `LocalCommandError`, a failed `/stream-promote` (unknown
  `candidate_id`, full queue), and a failed `/step` (empty queue,
  `PerceptEvent` validation failure, `tick()` exception) leave the
  ledger unchanged. Pattern growth must follow the same
  outcome-detection contract `I-AUTOSAVE-14` uses: a mutation only
  counts when its dispatcher returns `True`.

- **Read-only commands do not count as growth.** `/stream-summary`,
  `/stream-candidates`, `/state`, `/tick`, `/session-status`,
  `/db-summary`, `/profile-summary`, `/stream-db-summary`, `/db-diff`,
  `/autosave-status`, and the proposed `/pattern-ledger` must not
  cause an `observe(...)` call.

- **Model proposals (later, if any) do not count without
  construction.** If a future campaign adds a model-backed pattern
  proposal layer, that layer must funnel its proposals through the
  same `PatternLedger.observe(...)` constructor path. The constructor
  applies the same bounds it applies to operator-driven chunks. A
  model proposal that fails construction is dropped, not stored under
  a "tentative" or "shadow" field.

## Persistence question

Two options. This synthesis does not pick one; the implementation step
should pick after the catalog patch plan is reviewed.

### Option A — session-local only in Phase 3.12

- `PatternLedger` lives only on `OperatorSession` (or on a derived
  bounded snapshot field).
- It is not saved by `/save-session`.
- It is rebuilt by replaying observations from the loaded stream
  history on `/load-session`, **or** it is intentionally reset to
  empty on `/load-session` (Step 8 decides which).
- Pros: zero schema change. Zero risk to the existing
  `I-PERSIST-*` / `I-AUTOSAVE-*` invariants. Smallest catalog patch
  surface in Step 9. Honors the existing `I-STRM-17` "text-stream save
  / export path is NOT-EXERCISED" boundary by keeping aggregation
  in-process.
- Cons: cold-start does not preserve recognized recurrence across
  sessions. Growth measurement is per-session only.

### Option B — persist through the existing session DB in a later reviewed catalog patch

- Add a `pattern_ledger` table to the session DB schema (subject to
  `SCHEMA_VERSION_V*` bump and meta-table catalog-version stamp).
- `/save-session` writes ledger entries; `/load-session` rebuilds the
  ledger through public constructors that re-enforce every invariant
  above. A schema mismatch or invariant violation on load surfaces as
  `PersistenceError` and the live session is preserved (same pattern
  as today).
- Pros: cross-session growth measurement. Operational SelfModel and
  Coherence Monitor can ask "what recognized patterns survived save /
  load?".
- Cons: schema migration. Catalog rows must constrain the write path
  (mirroring `I-PERSIST-*` and the not-yet-exercised `I-STRM-17`
  policy boundary). Round-trip equality fixtures required. Larger
  Step 9 catalog patch surface.

**Recommendation.** Defer the persistence decision to Step 9 catalog
patch planning. The Step 9 plan should explicitly compare A vs B with
the same template the existing `I-PERSIST-*` rows used. Step 11
implementation, if approved at Review Gate B, can land Option A first
and Option B as a follow-up campaign if cross-session growth
measurement turns out to be load-bearing for the Coherence Monitor or
SelfModel design.

## Relationship to future layers

Pattern Ledger is a *substrate*, not an end. Its consumers are the
later-design components:

- **Coherence Monitor (Phase 3.12d).** The monitor is a bounded
  read-only snapshot over `BrainState` / `latest_tick` / stream state
  / pattern state / persistence status / known constraints. With a
  Pattern Ledger in place, the monitor can ask:
  *Did the recognized pattern set change in this tick? Did any entry
  cross the `SATURATED` → `QUIESCED` boundary? Does the load-side
  ledger match the save-side ledger (Option B)?* These are the kind
  of bounded inspectable checks the monitor needs, and they reduce to
  comparing two `PatternLedger` snapshots — exact, deterministic,
  callable-free.

- **Growth Ledger (Phase 3.12e roadmap).** A separate bounded
  developmental ledger that records *accepted* growth events (stream
  chunk accepted, pattern strengthened, candidate promoted, tick
  succeeded, content entered profile, content entered MSI, session
  saved / loaded, coherence report passed). The Pattern Ledger
  provides the "pattern strengthened" signal cleanly: a
  `PatternLedger.observe(...)` call that returns a record with
  `recurrence_count` strictly increased is the canonical growth
  event. The Growth Ledger does not need to re-derive structure; it
  only records that the increment happened.

- **Operational SelfModel (Phase 3.12e roadmap).** A read-only self
  report layer ("what is the system currently anchored to, in tick
  terms, in constraint terms, in recognized-pattern terms"). Pattern
  Ledger gives it the "in recognized-pattern terms" half. The
  SelfModel must remain *summary-of* the ledger, not a writable view
  on it.

None of these consumers are implemented or fixtured by this synthesis.
They are listed solely so the Pattern Ledger surface is sized for them
in advance.

## Non-goals

The Pattern Ledger work, at every step from Step 8 through Step 11,
must **not**:

- claim consciousness, sentience, subjective experience, or
  semantic understanding,
- claim language understanding from raw text,
- introduce a semantic truth layer,
- make any model-backed behavior the default,
- self-modify code, fixtures, the catalog, or the runner,
- emit any hidden LLM call,
- emit any hidden filesystem write, network call, subprocess spawn,
  or shell command,
- introduce hidden persistence outside the explicit `/save-session`
  / `/load-session` route (Option B, if chosen) or
  `_maybe_autosave_after_dispatch`,
- introduce an aggregate consciousness score, an aggregate "I-ness"
  score, or any single scalar claiming to summarize subjective
  experience,
- be reachable through `tick()` (the kernel runtime transition route
  remains untouched),
- map any raw text to `COGITO_ID`,
- mutate `BrainState`, `MSI`, `PtCns`, or the content registry
  outside the existing `tick()` and load-path routes.

These prohibitions are inherited from the Phase 3.12 mission, the
Phase 3.11 audit, and the existing `I-STRM-*` / `I-UISTRM-*` /
`I-PERSIST-*` / `I-AUTOSAVE-*` discipline. Step 8 corrigenda will
restate the relevant ones in the language of the Pattern Ledger
record shape.

## Recommended next artifact

The next campaign step is Step 8:

```text
PHASE3_12_PATTERN_LEDGER_KICKOFF.md
PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md
```

The kickoff fixes the record shape (resolves all "Step 8 should pick
one and lock it" notes above), enumerates the proposed catalog row
family (working name `I-PLEDGER-*`, per `CURRENT_CAMPAIGN.md` Step 9),
and sketches the proposed module location and import boundary
(probable: `brain/development/pattern_ledger.py`, importable from
`brain/ui/session.py` but not from `brain/tick.py`).

The corrigenda restates each Phase 3.7 / 3.8 / 3.10 / 3.11 invariant
that touches the new surface in Pattern-Ledger-specific language so
the catalog patch plan in Step 9 can cite them precisely.

**Implementation remains blocked.** Step 9 produces a catalog patch
plan only. Step 10 is Review Gate B. Step 11 applies the implementation
**only if** the operator explicitly accepts the catalog patch plan at
Review Gate B. Nothing in this synthesis authorizes a code change
under `brain/**`, `tools/**`, `INVARIANT_CATALOG.md`,
`lean_reference/**`, `scenarios/**`, or `traces/**`.

## Validation

Re-ran after writing this synthesis (no source under `brain/**`,
`tools/**`, `lean_reference/**`, `scenarios/**`, or `traces/**` was
touched; only this new documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
