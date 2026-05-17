# PHASE3_12_PATTERN_LEDGER_KICKOFF.md

## Purpose

Translate `PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md` into an
implementation-ready plan for a future code change.

This kickoff is documentation only. It does **not** authorize code or
catalog mutation. Implementation is gated behind:

```text
Step 9   PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md  (plan only)
Step 10  Review Gate B                                    (explicit acceptance required)
Step 11  Apply accepted Pattern Ledger implementation     (only if Step 10 passed)
```

Every open question that Step 7 left undecided is resolved in the
companion `PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md` so Step 9 can write a
precise catalog patch plan.

## Baseline

```text
Catalog:                  v0.20
Counts:                   214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Branch:                   campaign/phase3-12-coherent-i-loop-observatory
Phase 3.11:               complete; PR #10 merged at 98b55ab
Phase 3.12 steps complete on this branch (in commit order):
  Step 1  566b109  coherent i-loop mission sync
  Step 2  631ae5a  coherent i-loop synthesis
  Step 3  c395989  coherent i-loop kickoff
  Step 4  10a93ee  coherent i-loop matrix
  Step 6  c65d37b  coherent i-loop observatory report
  Step 7  013585e  pattern ledger synthesis
Step 6 verdict:           existing /stream -> /stream-promote -> /step
                          route is coherent; bounded growth works;
                          pattern recognition partially supported
                          (evidence stored, not ledgered)
Step 7 outcome:           Pattern Ledger defined as a bounded
                          developmental summary substrate below
                          truth / agency / PtCns / MSI
```

## Problem Being Solved

The text-stream substrate stores raw structural evidence
(`TextStreamChunk`, `TextStreamHistory`, `StreamFeatureVector`,
`SegmentCandidate`, `StreamPattern`, `StreamPromotionCandidate`) and the
operator session stores a bounded recent-history slice
(`stream_history`, `stream_candidates`, saturating at
`STREAM_PROMOTION_MAX=64`). Step 6 confirmed:

- repeated motifs produce repeated chunks/candidates but identical
  chunk text — recurrence visible in stored fields,
- alternation and novelty preserve structural distinctness,
- contradiction-pressure text never touches `profile` / `msi` /
  `PtCns`,
- only successful `/step` mutates `profile.domain` / `msi.contents` /
  registry and advances `tick_counter`,
- `/stream-summary` and `/stream-candidates` only set `active_view`
  and write `view = ...` to status — no recurrence surface at the
  dispatch level.

There is no persistent, inspectable, ledgered record that says "this
pattern (by signature) has been seen N times, with these evidence chunk
IDs and these candidate IDs, first at tick X, last at tick Y." That gap
is what Phase 3.12c's Pattern Ledger closes.

## Proposed Implementation Surface

The following files would be touched only by Step 11, **only if** the
Step 9 catalog patch plan is accepted at Step 10 Review Gate B. Step 8
does **not** edit any of them.

```text
NEW MODULE:
  brain/development/pattern_ledger.py
    - PatternLedgerSourceKind        (closed enum)
    - PatternLedgerSaturationState   (closed enum)
    - PatternLedgerEntry             (frozen slotted dataclass)
    - PatternLedger                  (frozen slotted dataclass + observe + snapshot)
    - constants: PATTERN_LEDGER_MAX_ENTRIES,
                 PATTERN_LEDGER_EVIDENCE_MAX,
                 PATTERN_LEDGER_ID_MAX
    - module reuses STREAM_PATTERN_RECURRENCE_MIN / _MAX,
                    STREAM_PATTERN_SIG_MAX,
                    STREAM_PROVENANCE_MAX_LEN
                    from brain.development.text_stream

FIXTURE REGISTRATION (location per current repo conventions, e.g.
the `FIXTURE_MODULES` list in `brain/invariants.py` and per-row
`fixture` columns in `INVARIANT_CATALOG.md`):
  brain/development/fixtures/pattern_ledger_*.py        (multiple, one per row family)
    or whichever directory the catalog patch plan picks; existing
    repo convention is `brain/development/fixtures/text_stream_*.py`
    and similar — the catalog patch plan must lock the exact path.

CATALOG / RUNNER WIRING:
  brain/invariants.py                                   (FIXTURE_MODULES extension)
  brain/_catalog_ids.py                                 (new I-PLEDGER-* IDs)
  INVARIANT_CATALOG.md                                  (new rows + counts banner bump)
  tools/catalog.py                                      (only if EXPECTED_COUNTS needs to bump)
  README.md / CURRENT_MISSION.md / CURRENT_CAMPAIGN.md  (catalog-version stamp, if v0.20 -> v0.21)

OPTIONAL UI (per LOCK K, defer if it broadens scope):
  brain/ui/commands.py            (add OperatorCommand.INSPECT_PATTERN_LEDGER)
  brain/ui/command_line.py        (add /pattern-ledger verb to LOCAL_COMMAND_VERBS)
  brain/ui/session.py             (read-only dispatcher; set active_view='pattern_ledger')
  brain/ui/snapshot.py / render.py if a view pane is added.

PERSISTENCE (DEFERRED per LOCK B):
  brain/ui/persistence.py / persistence_ops.py / persistence_observe.py
  DO NOT TOUCH IN V1. No SCHEMA_VERSION bump. No new table.
```

Step 11 may not exceed this surface. A broader scope must be re-routed
through a new campaign step and a new review gate.

## Proposed Data Model

Pseudocode only. Field shapes and names match `PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md`.

```python
class PatternLedgerSourceKind(Enum):
    OPERATOR   = "operator"
    SYSTEM     = "system"
    PROBE_ECHO = "probe_echo"
    GENERATED  = "generated"


class PatternLedgerSaturationState(Enum):
    OPEN      = "open"       # recurrence_count < STREAM_PATTERN_RECURRENCE_MAX
    SATURATED = "saturated"  # recurrence_count == STREAM_PATTERN_RECURRENCE_MAX
    QUIESCED  = "quiesced"   # no new evidence in last N ticks
                             # (N to be locked by the catalog patch plan;
                             #  v1 may collapse this state into SATURATED
                             #  if the bound is hard to justify)


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


@dataclass(frozen=True, slots=True)
class PatternLedger:
    entries:                tuple[PatternLedgerEntry, ...] = ()
    max_entries:            int = PATTERN_LEDGER_MAX_ENTRIES
    max_evidence_per_entry: int = PATTERN_LEDGER_EVIDENCE_MAX

    def observe(
        self,
        chunk,
        candidate,
        *,
        current_tick: int,
    ) -> "PatternLedger":
        """Pure copy-on-write. Returns a NEW PatternLedger reflecting
        one observation. See LOCK D, LOCK E, LOCK F, LOCK G, LOCK I,
        LOCK J, LOCK L for exact semantics."""
        ...

    def snapshot(self) -> tuple["PatternLedgerEntrySummary", ...]:
        """Bounded printable read-only summary view, intended for the
        /pattern-ledger dispatch status text and the renderer (LOCK K)."""
        ...


@dataclass(frozen=True, slots=True)
class PatternLedgerEntrySummary:
    """Read-only printable summary of one PatternLedgerEntry.

    Carries only the bounded printable fields the renderer / status
    line need. No callable, no handle, no raw chunk text."""
    pattern_id:        str
    signature_text:    str   # bounded printable join of signature
    recurrence_count:  int
    saturation_state:  str   # PatternLedgerSaturationState.value
    source_kind:       str   # PatternLedgerSourceKind.value
    evidence_chunk_n:  int   # len(evidence_chunk_ids)
    evidence_cand_n:   int   # len(evidence_candidate_ids)
    first_seen_tick:   int
    last_seen_tick:    int
    confidence:        str   # "num/den" exact Fraction string
```

`observe(...)` is the **sole non-construction entry point** that
mutates the logical ledger. It takes no `BrainState`, no `LLMClient`,
no callable, no `pathlib.Path`. It is pure over its inputs.

## Proposed Constants

Implementation candidates for Step 11. Step 9 may rename or retune
them, but it must justify each change against the synthesis.

```text
PATTERN_LEDGER_MAX_ENTRIES         = 64
PATTERN_LEDGER_EVIDENCE_MAX        = 32
PATTERN_LEDGER_ID_MAX              = 64
```

Reused from `brain/development/text_stream.py`:

```text
STREAM_PATTERN_RECURRENCE_MIN      = 2      (lower bound for recurrence_count)
STREAM_PATTERN_RECURRENCE_MAX      = 256    (saturation cap, per LOCK G)
STREAM_PATTERN_SIG_MAX             = 16     (signature tuple length cap)
STREAM_PROVENANCE_MAX_LEN          = 64     (provenance length cap)
STREAM_TEXT_MAX_LEN                = 1024   (caller-side text bound; ledger does not hold text)
STREAM_HISTORY_MAX_CHUNKS          = 256    (caller-side; ledger references chunk IDs)
STREAM_PROMOTION_MAX               = 64     (caller-side; ledger references candidate IDs)
```

`PATTERN_LEDGER_MAX_ENTRIES = 64` mirrors `STREAM_PROMOTION_MAX` so the
ledger can hold at most one entry per recently-promoted candidate
signature without re-saturating at a different cap.
`PATTERN_LEDGER_EVIDENCE_MAX = 32` is half the entry cap, biased toward
keeping the evidence list compact for the snapshot view.

## Proposed Signature / ID Discipline

The signature is **structural and non-semantic**. It is derived from
exact `int` / `Fraction` features of the chunk (and optionally the
candidate), not from raw text, language, or readability.

Recommended v1 signature shape (LOCK I locks this in):

```python
signature = (
    f"source:{chunk.source.value}",
    f"len:{len(chunk.text)}",
    f"lines:{<line_count from StreamFeatureVector>}",
    f"ws:{<whitespace_run_count from StreamFeatureVector>}",
    f"distinct:{<distinct_char_count from StreamFeatureVector>}",
    f"repeat:{<repeat_ratio.numerator>}/{<repeat_ratio.denominator>}",
)
```

Element count ≤ `STREAM_PATTERN_SIG_MAX = 16`. Each element is a
bounded printable string. No element equals `COGITO_ID`. Element values
are derived from already-existing `StreamFeatureVector` fields produced
by `extract_stream_features(chunk)` (see `brain/development/text_stream.py`).

`pattern_id` is **deterministic** (LOCK J):

```python
pattern_id = "pledger:" + sha256(
    repr(signature).encode("utf-8")
).hexdigest()[:16]
```

- no randomness (no `random`, no `secrets`, no `uuid.uuid4`),
- no time (`time`, `datetime`, `monotonic`),
- no PID (`os.getpid`),
- no memory address (`id(...)`),
- no hostname (`socket.gethostname`),
- no environment variable lookup.

Same signature → same `pattern_id` across runs, across processes, and
across operating systems. Length ≤ `PATTERN_LEDGER_ID_MAX = 64`
("pledger:" prefix + 16 hex chars = 24 chars, well under the cap).

## Proposed Observe Semantics

`PatternLedger.observe(chunk, candidate, *, current_tick)` semantics:

1. **Compute signature** from `chunk` (and optionally `candidate`)
   using the LOCK I formula.
2. **Compute `pattern_id`** from signature using the LOCK J formula.
3. **Look up by `pattern_id`** in `self.entries`.
4. **Existing signature path:**
   - Increment `recurrence_count`, saturating at
     `STREAM_PATTERN_RECURRENCE_MAX` (LOCK G).
   - Update `last_seen_tick = current_tick` (must be `>= first_seen_tick`).
   - Append `chunk.chunk_id` to `evidence_chunk_ids` if not already
     present (LOCK D) and only if list length `< PATTERN_LEDGER_EVIDENCE_MAX` (LOCK F).
   - Append `candidate.candidate_id` to `evidence_candidate_ids`
     similarly.
   - Recompute `saturation_state` from the new `recurrence_count`
     (and the quiescence rule once locked).
   - Recompute `confidence` per LOCK H formula.
   - Return new `PatternLedger` with the new entry replacing the old.
5. **New signature path:**
   - If `len(self.entries) >= max_entries` (LOCK E), return `self`
     unchanged. Do not prune. Do not evict. (The dispatch caller may
     surface this as bounded status text; the ledger itself does not.)
   - Otherwise, construct a fresh `PatternLedgerEntry` with
     `recurrence_count = STREAM_PATTERN_RECURRENCE_MIN`,
     `first_seen_tick = last_seen_tick = current_tick`,
     `evidence_chunk_ids = (chunk.chunk_id,)`,
     `evidence_candidate_ids = (candidate.candidate_id,)`,
     `source_kind = chunk.source`-mapped value,
     `provenance = chunk.provenance`,
     `confidence = Fraction(STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX)` (LOCK H),
     `saturation_state = OPEN`.
   - Return new `PatternLedger` with the new entry appended.
6. **In every path:**
   - No `BrainState` is read or written.
   - No `tick()` is called.
   - No callable is invoked apart from pure helpers in this module.
   - No I/O occurs.
   - `self` is not mutated; `entries` is a fresh tuple in the returned
     ledger.

Failure paths (per LOCK L): if the caller passed a `chunk` /
`candidate` pair that would yield an invalid `PatternLedgerEntry`
(e.g. signature element equals `COGITO_ID`), the constructor raises
`ValueError` naming the relevant row. The caller is responsible for
catching this in the dispatch layer and surfacing it as bounded local
error text — the same pattern `_dispatch_stream_append` and
`_dispatch_stream_promote` already use.

## Proposed Integration Points

Per LOCK L the **only** integration in v1 is the successful `/stream`
append path:

```text
OperatorSession._dispatch_stream_append(...)
  on success:
    ... existing work ...
    self.pattern_ledger = self.pattern_ledger.observe(
        chunk, candidate, current_tick=self.tick_counter,
    )
    # observe may return self unchanged if at max_entries (LOCK E).
```

A new optional session field:

```text
OperatorSession.pattern_ledger: PatternLedger = field(default_factory=PatternLedger)
```

…added to `_ALLOWED_SESSION_ATTRS` so the `I-UI-10` self-audit accepts
it. The field is a frozen slotted dataclass and exposes neither
`eval_consistency`, `read`/`write`, `fileno`, `send_signal`, nor
`communicate`.

Explicitly **out of scope** for v1:

- `/stream-promote` does **not** call `observe(...)`. Promotion is an
  evidence link, not a new structural observation; the ledger already
  saw the chunk on `/stream` append.
- `/step` does **not** call `observe(...)`. The Pattern Ledger does
  not enter the `tick()` route in any form. `/step` continues to be
  the sole runtime transition path.
- Read-only commands (`/stream-summary`, `/stream-candidates`,
  `/state`, `/tick`, `/session-status`, `/db-summary`,
  `/profile-summary`, `/stream-db-summary`, `/db-diff`,
  `/autosave-status`, and the optional `/pattern-ledger`) do not call
  `observe(...)`.
- Failed parse, failed dispatch, and the empty-queue `/step` failure
  path do not call `observe(...)`.
- Persistence is deferred (LOCK B). `/save-session` does not write the
  ledger. `/load-session` does not restore it (LOCK C).
- Autosave triggers (`I-AUTOSAVE-08` / `09` / `10`) are not extended.
  `_maybe_autosave_after_dispatch` does not need to know about the
  ledger because the ledger is not persisted in v1.

Optional `/pattern-ledger` read-only command (LOCK K). If Step 9 keeps
it small:

```text
OperatorCommand.INSPECT_PATTERN_LEDGER  = "inspect_pattern_ledger"
INSPECT_VIEW_MAP[...]                   = "pattern_ledger"
LOCAL_COMMAND_VERBS                    += ("pattern-ledger",)
_COMMANDS_WITHOUT_PAYLOAD              += {INSPECT_PATTERN_LEDGER}
session.dispatch INSPECT_PATTERN_LEDGER:
    self.set_active_view("pattern_ledger")
    self.set_status(
        f"pattern-ledger: entries={len(self.pattern_ledger.entries)} "
        f"(max={self.pattern_ledger.max_entries})"
    )
```

It must not call `observe(...)`, must not call `tick()`, and must not
mutate session state beyond `active_view` and `status_message`.

If `/pattern-ledger` would broaden Step 11 too much, Step 9 should
split it into a follow-up row family and a follow-up campaign step.

## Proposed Fixtures / Tests

Future fixture families (location per repo conventions; exact filenames
locked by the Step 9 catalog patch plan):

| Family | Purpose |
|--------|---------|
| `pattern_ledger_constructor_bounds` | Every `PatternLedgerEntry` / `PatternLedger` field rejects malformed input (types, lengths, `COGITO_ID` collisions, `recurrence_count` out of range, `confidence` outside [0,1], non-printable strings). |
| `pattern_ledger_cogito_reject` | `pattern_id`, every `signature` element, every `evidence_chunk_ids` element, every `evidence_candidate_ids` element, and `provenance` reject `COGITO_ID` at construction. |
| `pattern_ledger_deterministic_id` | Same `signature` produces same `pattern_id` across repeated invocations and across import orders. |
| `pattern_ledger_duplicate_evidence` | `observe(...)` filters duplicate `chunk_id` / `candidate_id` before extending the evidence lists (LOCK D). |
| `pattern_ledger_recurrence_saturation` | Repeated identical observations cap `recurrence_count` at `STREAM_PATTERN_RECURRENCE_MAX` (LOCK G); arbitrary repetition cannot exceed that cap. |
| `pattern_ledger_evidence_list_cap` | Evidence lists do not grow past `PATTERN_LEDGER_EVIDENCE_MAX` (LOCK F); past that point recurrence may still saturate but no new evidence IDs append. |
| `pattern_ledger_max_entries_refuse` | When `len(entries) == max_entries` and a new signature arrives, `observe(...)` returns the same ledger unchanged (LOCK E); no eviction, no LRU, no random drop. |
| `pattern_ledger_cow` | `PatternLedger.observe(...)` returns a new record; the original ledger and its `entries` tuple are unchanged by identity check. |
| `pattern_ledger_static_audit` | AST audit of `brain/development/pattern_ledger.py` rejects every forbidden import / call listed in LOCK M. |
| `pattern_ledger_no_brainstate_no_tick_no_llm` | Before / after every `observe(...)` call, `BrainState`, `MSI`, `PtCns`, `ContentRegistry`, `latest_tick`, `tick_counter`, and `OperatorSession.event_queue` identities are unchanged; no `eval_consistency` reachable. |
| `pattern_ledger_exact_fraction` | `confidence` is always a `Fraction` in `[0, 1]`; the count / statistic path uses no `float`, no `round`, no `math.*`. |
| `pattern_ledger_snapshot_determinism` | `PatternLedger.snapshot()` returns a deterministic bounded tuple of `PatternLedgerEntrySummary`; equal ledgers produce equal snapshots; the call mutates nothing. |

Future fixture families if `/pattern-ledger` is included (LOCK K):

| Family | Purpose |
|--------|---------|
| `pattern_ledger_command_parser` | `/pattern-ledger` parses with no args; extra tokens reject. |
| `pattern_ledger_dispatch_read_only` | Dispatching `INSPECT_PATTERN_LEDGER` sets `active_view='pattern_ledger'` and bounded status; `BrainState`, `latest_tick`, `tick_counter`, `event_queue`, `stream_history`, and `stream_candidates` are unchanged. |
| `pattern_ledger_dispatch_no_observe` | The `/pattern-ledger` dispatch path does not call `observe(...)`. |

## Proposed Catalog Row Family

Working name `I-PLEDGER-NN`. **Indicative** rows (final IDs and exact
text locked by the Step 9 catalog patch plan):

```text
I-PLEDGER-01  PatternLedgerSourceKind is a finite closed enumeration.
I-PLEDGER-02  PatternLedgerSaturationState is a finite closed enumeration.
I-PLEDGER-03  PatternLedgerEntry constructor enforces bounded printable
              fields, exact-Fraction confidence, COGITO_ID rejection on
              every ID-bearing field, recurrence range
              [STREAM_PATTERN_RECURRENCE_MIN, _MAX], and tick ordering
              first_seen_tick <= last_seen_tick.
I-PLEDGER-04  PatternLedger is copy-on-write and bounded; entries is a
              tuple; max_entries / max_evidence_per_entry are positive
              ints; constructor enforces bounds.
I-PLEDGER-05  PatternLedger.observe(...) is pure: it returns a NEW
              PatternLedger; the original entries tuple is unchanged.
I-PLEDGER-06  PatternLedger.observe(...) does not mutate BrainState,
              MSI, PtCns, ContentRegistry, latest_tick, tick_counter,
              source histories, or OperatorSession.event_queue; does
              not call tick(); does not call any LLM client.
I-PLEDGER-07  pattern_id is deterministic: same signature -> same
              pattern_id across runs and across processes.
I-PLEDGER-08  Anti-growth: repeated identical observations saturate at
              STREAM_PATTERN_RECURRENCE_MAX; evidence lists do not grow
              past PATTERN_LEDGER_EVIDENCE_MAX; max_entries is hard
              (no eviction in v1).
I-PLEDGER-09  PatternLedger.observe(...) is idempotent for duplicate
              chunk_id / candidate_id evidence delivered against the
              same entry (filtered, not raising).
I-PLEDGER-10  PatternLedger records are frozen dataclasses; fields are
              bounded primitives, tuples of bounded primitives, or
              Fraction; no callable / handle / socket / subprocess /
              client / path object appears.
I-PLEDGER-11  Static audit: brain/development/pattern_ledger.py has no
              I/O / network / file / shell / LLM / tick / TLICA /
              curses / threading / asyncio / eval / exec / compile /
              __import__ / importlib.import_module / atexit / signal
              import or call (LOCK M).
I-PLEDGER-12  Confidence formula (LOCK H):
              confidence = Fraction(recurrence_count,
                                    STREAM_PATTERN_RECURRENCE_MAX),
              clamped to [0, 1]; no float, no round, no math.*.
I-PLEDGER-13  Pattern Ledger save/load path is NOT-EXERCISED in v1
              (LOCK B / LOCK C); any future write path requires a
              dedicated reviewed catalog patch.
I-PLEDGER-14  (Optional, only if /pattern-ledger is in scope per LOCK K)
              /pattern-ledger is read-only: dispatch sets
              active_view='pattern_ledger' and bounded status; does
              not call observe; does not call tick; does not mutate
              kernel containers or stream state.
I-PLEDGER-15  (Optional) /pattern-ledger parser is finite and typed;
              extra tokens reject as LocalCommandError.
I-PLEDGER-16  Aggregate Pattern Ledger snapshot view is inspectable
              (OBSERVED).
```

Row counts will follow what the Step 9 plan finalizes. Counts banner
in `tools/catalog.py` and the catalog-version stamps in `README.md` /
`CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` will need to move from
`v0.20` to `v0.21` if any REQUIRED / STRUCTURAL / NOT-EXERCISED /
DEFERRED / OBSERVED count changes.

## Risks

- **Semantic / truth creep.** Even with a "no truth, no agency"
  promise, signatures that include text-derived fields can creep
  toward language labels. Mitigation: LOCK I locks the signature shape
  to structural counts only.
- **Persistence schema creep.** Adding a DB table for the ledger is
  tempting but doubles the implementation surface. Mitigation: LOCK B
  forbids it in v1.
- **Spam counted as growth.** Mitigation: LOCK G saturates
  `recurrence_count`; LOCK F caps evidence list; LOCK L restricts
  observe to successful `/stream` append only.
- **Tick / `BrainState` coupling.** Adding a session field is a
  natural place to accidentally reach into the kernel. Mitigation:
  LOCK M static audit + `I-PLEDGER-06` runtime check.
- **UI scope creep.** A `/pattern-ledger` command can grow into a
  diff / search / filter API. Mitigation: LOCK K limits it to a
  bounded read-only view; if it grows, Step 9 must split it out.
- **Overclaiming "operational I" as consciousness.** Mitigation:
  LOCK N non-claims are stamped on every artifact and the
  `PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md` non-goals.

## Step 9 Handoff

Step 9 must produce exactly:

```text
PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md
```

The plan must:

- finalize `I-PLEDGER-*` row IDs, exact row text, and per-row fixture
  module assignments,
- decide row category (REQUIRED / STRUCTURAL / NOT-EXERCISED / DEFERRED
  / OBSERVED) for each proposed row,
- pick exact path(s) for the new fixture module(s),
- specify the catalog-version bump (`v0.20` -> `v0.21`) and the
  counts-banner update in `tools/catalog.py`,
- specify the `FIXTURE_MODULES` extension in `brain/invariants.py` and
  the `_PHASE3_*_PENDING_ROWS` docstring entry if needed,
- lock the LOCK K decision (`/pattern-ledger` in v1 or deferred),
- include a stop condition at Step 10 Review Gate B.

Step 9 must **not** edit `brain/**`, `tools/**`,
`INVARIANT_CATALOG.md`, `lean_reference/**`, `scenarios/**`, or
`traces/**`. Implementation is Step 11 only, and only if Step 10 is
explicitly accepted.
