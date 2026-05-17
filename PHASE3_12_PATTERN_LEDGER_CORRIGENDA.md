# PHASE3_12_PATTERN_LEDGER_CORRIGENDA.md

## Purpose

Lock every design decision that `PHASE3_12_PATTERN_LEDGER_SYNTHESIS.md`
left open, so the Step 9 catalog patch plan can be precise and the
Step 10 Review Gate B can be a yes/no decision.

This file is documentation only. It does **not** edit `brain/**`,
`tools/**`, `INVARIANT_CATALOG.md`, `lean_reference/**`, `scenarios/**`,
or `traces/**`. It does not change runtime behavior, add fixtures, or
authorize implementation.

Each LOCK is binding on the Step 9 catalog patch plan and on any
Step 11 implementation. A LOCK may only be changed by a later
explicitly-accepted review gate; the gate must cite the LOCK label
being overridden.

## Locks

### LOCK A — Implementation authorization

```text
Step 8 creates documentation only.
No file under brain/, tools/, INVARIANT_CATALOG.md, lean_reference/,
scenarios/, or traces/ is modified by Step 8.
No fixture is added.
No committed helper script is added.
```

Implementation requires:

1. `PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md` (Step 9), and
2. **explicit operator acceptance at Step 10 Review Gate B**.

Step 11 is the only step in this campaign that may touch code or the
catalog, and only if Step 10 was explicitly accepted with reference to
this corrigenda.

### LOCK B — First implementation persistence policy

```text
Pattern Ledger v1 is session-local only.
```

Specifically, in any Step 11 implementation:

- No `pattern_ledger` table is added to the session DB schema.
- `SCHEMA_VERSION_V*` is not bumped (`brain/ui/persistence.py`).
- `/save-session` does **not** serialize the ledger.
- `/load-session` does **not** restore the ledger.
- Autosave (`_maybe_autosave_after_dispatch`) is **not** extended for
  the ledger.
- `brain/ui/persistence.py`, `brain/ui/persistence_ops.py`,
  `brain/ui/persistence_observe.py`, and `brain/ui/autosave.py` are
  **not** edited by Step 11.

Reason: avoid persistence schema creep before runtime invariants are
validated. A future campaign may revisit persistence behind its own
review gate.

### LOCK C — Cold-start behavior

Because Pattern Ledger v1 is session-local only (LOCK B):

```text
Fresh session            -> empty PatternLedger().
/load-session            -> does NOT touch session.pattern_ledger.
Cold start across runs   -> ledger does NOT survive.
```

Implementation note: the `/load-session` dispatcher in
`brain/ui/session.py` (`_dispatch_load_session`) currently swaps
`state`, `tick_counter`, `stream_history`, `stream_candidates`, and
`stream_chunk_serial`. Step 11 **must not** add `pattern_ledger` to
that swap list. The simplest safe behavior is: leave
`session.pattern_ledger` untouched across `/load-session`. The live
ledger continues to reflect whatever was observed in the live session.

A future option may rebuild the ledger from a loaded
`TextStreamHistory` by replaying observations on load. That option is
explicitly **deferred** to a later reviewed patch and is not v1.

### LOCK D — Duplicate-evidence handling

```text
observe(chunk, candidate, *, current_tick) is idempotent against
duplicate evidence delivery for the same entry.
```

Specifically:

- If `chunk.chunk_id` already appears in the target entry's
  `evidence_chunk_ids`, `observe(...)` does **not** append it a second
  time and does **not** raise.
- If `candidate.candidate_id` already appears in
  `evidence_candidate_ids`, same behavior.
- `recurrence_count` still saturates per LOCK G; the duplicate filter
  only governs the evidence lists.

`PatternLedgerEntry`'s constructor remains strict:

- Direct construction with a tuple that contains a duplicate element
  raises `ValueError`. The deduplication is performed by
  `observe(...)` *before* it constructs the new entry; constructors
  are not silent normalizers.

Rationale: `observe(...)` is operator-facing and should accept a
slightly redundant call without raising; `PatternLedgerEntry` is a
record contract and must remain strict.

### LOCK E — Max-entry behavior

```text
When len(entries) >= PATTERN_LEDGER_MAX_ENTRIES and a NEW signature
arrives, observe(...) returns the same PatternLedger unchanged.
```

Specifically:

- No LRU eviction.
- No oldest-drop.
- No random eviction.
- No "least confident" eviction.
- No silent overwrite of any existing entry.

The caller (the dispatch layer) may surface this as bounded status
text by inspecting the returned ledger's `entries` length, but the
ledger itself does not log or emit a warning. The fixture family
`pattern_ledger_max_entries_refuse` asserts this behavior.

Rationale: hiding evidence loss behind implicit pruning would defeat
the observability goal. A hard refusal is auditable.

### LOCK F — Evidence-list cap

```text
When len(entry.evidence_chunk_ids) == PATTERN_LEDGER_EVIDENCE_MAX,
no further chunk IDs are appended to that entry.
Same for evidence_candidate_ids.
recurrence_count may continue saturating (LOCK G).
```

Specifically:

- `observe(...)` checks the evidence list length *before* appending.
- If the list is at cap, the evidence-append step is a no-op for that
  list.
- The opposite list (chunks vs candidates) is treated independently.
- No FIFO drop. No eviction. The first
  `PATTERN_LEDGER_EVIDENCE_MAX` distinct chunk / candidate IDs win.

Rationale: keeps the snapshot view bounded and printable; preserves
earliest evidence for cross-tick comparison.

### LOCK G — Recurrence count saturation

```text
recurrence_count saturates at STREAM_PATTERN_RECURRENCE_MAX.
```

Specifically:

- `STREAM_PATTERN_RECURRENCE_MIN` (currently 2) is the lower bound for
  a freshly constructed entry. Direct construction below the minimum
  raises `ValueError`.
- Each successful `observe(...)` against an existing entry increments
  `recurrence_count` by exactly 1, capped at
  `STREAM_PATTERN_RECURRENCE_MAX` (currently 256).
- No integer growth beyond cap.
- The cap is the same constant `StreamPattern` already uses
  (`brain/development/text_stream.py`), so the ledger and the existing
  text-stream substrate cannot disagree on the bound.

### LOCK H — Confidence formula

```text
confidence = Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)
```

Specifically:

- Result is an exact `fractions.Fraction`.
- Bounded to `[0, 1]` by construction (numerator ≤ denominator after
  saturation per LOCK G).
- `confidence` is recomputed every time `observe(...)` increments
  `recurrence_count`.
- No length weighting (chunk text length does not affect confidence).
- No semantic weighting.
- No model weighting.
- No `float`, no `round`, no `math.*` on this path. The
  `pattern_ledger_exact_fraction` fixture asserts the type and bounds.

Direct construction with a `confidence` outside `[0, 1]`, or a
`confidence` whose value is not consistent with `Fraction(recurrence_count,
STREAM_PATTERN_RECURRENCE_MAX)`, raises `ValueError`.

### LOCK I — Pattern signatures

```text
v1 signature is structural and non-semantic.
```

Recommended v1 signature shape:

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

Constraints:

- Element count between 1 and `STREAM_PATTERN_SIG_MAX = 16`.
- Each element is a bounded printable `str` with `len <=`
  `STREAM_PATTERN_SIG_ELEM_MAX` (Step 9 picks the exact cap; a
  reasonable default is 64).
- No element equals `COGITO_ID`.
- Every numeric value rendered into a signature element comes from
  `extract_stream_features(chunk)` (exact `int` / `Fraction` values
  produced by the existing `StreamFeatureVector` constructor). No
  `float`, no `round`, no `math.*`.
- No semantic labels (no part-of-speech, no language detection, no
  topic, no truth flag, no readability score).
- No textual payload (no chunk text, no excerpt, no hash of the chunk
  text — the ID is hashed from the signature tuple, not from the raw
  text).

If `candidate` is supplied to `observe(...)`, the signature must be
derived from `chunk` features; `candidate.text` is identical to
`chunk.text` in the current substrate and adds no structural
information. Step 9 may extend the signature to include
`candidate.source` if it differs from `chunk.source`, but must justify
the extension against this LOCK.

### LOCK J — Pattern ID

```text
pattern_id = "pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]
```

Specifically:

- Hash function: `hashlib.sha256` (standard library; deterministic
  across Python implementations).
- Input encoding: `repr(signature)` is a stable, bounded Python
  representation of a tuple of bounded strings. It is identical across
  runs and across processes for equal signatures.
- Prefix `"pledger:"` is a fixed printable string.
- Truncated to the first 16 hex characters (64 bits) of the digest;
  collisions are not a security boundary, only a deterministic
  uniqueness boundary among at most `PATTERN_LEDGER_MAX_ENTRIES = 64`
  active entries.
- Total length 24 characters, well below `PATTERN_LEDGER_ID_MAX = 64`.

No nondeterministic inputs are read:

- no `time`,
- no `random`,
- no `secrets`,
- no `uuid.uuid4`,
- no `os.getpid`,
- no `socket.gethostname`,
- no `id(...)`,
- no `os.environ` lookup,
- no environment-derived locale.

`pattern_id` equality is a function of `signature` equality only.

### LOCK K — UI surface

```text
/pattern-ledger is OPTIONAL for v1. Preferred IF the patch surface
stays small and the parser / dispatcher fits the existing read-only
pattern.
```

If included, every constraint below must hold:

- `OperatorCommand.INSPECT_PATTERN_LEDGER` is added to the closed
  `OperatorCommand` enumeration and to `INSPECT_VIEW_MAP` with view
  string `"pattern_ledger"`.
- `LOCAL_COMMAND_VERBS` gains the verb `"pattern-ledger"`. The parser
  accepts no arguments (same shape as `/state`, `/tick`,
  `/session-status`, etc.).
- `_COMMANDS_WITHOUT_PAYLOAD` gains `INSPECT_PATTERN_LEDGER`.
- Dispatch is read-only: it may set `active_view = "pattern_ledger"`
  and `status_message` to a bounded printable summary line. It does
  not call `observe(...)`. It does not call `tick()`. It does not
  mutate `state`, `latest_tick`, `tick_counter`, `event_queue`,
  `stream_history`, `stream_candidates`, or `stream_chunk_serial`.
- `pattern_ledger_dispatch_read_only` and
  `pattern_ledger_dispatch_no_observe` fixtures (per the Step 8
  kickoff) cover this.

If Step 9 judges the UI broadens the implementation too much, the UI
is **split out** into a separate follow-up campaign step and a
separate row family. v1 then implements only the data substrate and
the `/stream` integration trigger; operators can read the ledger via a
Python REPL or a future renderer pane.

### LOCK L — Integration trigger

```text
v1 integration is exactly one trigger:
  successful /stream append.
```

Specifically:

- After `_dispatch_stream_append` successfully appends a chunk and a
  candidate, the dispatcher computes the new
  `session.pattern_ledger = session.pattern_ledger.observe(chunk, candidate,
  current_tick=session.tick_counter)`.
- The dispatcher does **not** observe on read-only commands
  (`/stream-summary`, `/stream-candidates`, `/state`, `/tick`,
  `/session-status`, `/db-summary`, `/profile-summary`,
  `/stream-db-summary`, `/db-diff`, `/autosave-status`, and the
  optional `/pattern-ledger`).
- The dispatcher does **not** observe on parse failures
  (`LocalCommandError`).
- The dispatcher does **not** observe on dispatch failures (e.g.
  malformed `StreamAppendPayload`).
- The dispatcher does **not** observe on `/step`.
- Pattern Ledger does **not** alter `/step` behavior, the `tick()`
  signature, or the `_dispatch_step` failure path. The empty-queue
  `/step` and tick-exception paths remain bit-for-bit identical to
  their current behavior.
- `/stream-promote` does **not** call `observe(...)`. Promotion
  records an evidence link via the chunk that `/stream` already
  observed; double-observing would inflate `recurrence_count`.

The `pattern_ledger_no_brainstate_no_tick_no_llm` fixture asserts that
across every `observe(...)` call, `BrainState`, `MSI`, `PtCns`,
`ContentRegistry`, `latest_tick`, `tick_counter`, and
`OperatorSession.event_queue` are unchanged.

### LOCK M — Static audit

```text
The future brain/development/pattern_ledger.py module must pass a
static AST audit that rejects every entry in the forbidden list below.
```

Forbidden imports / module references:

- `os`
- `os.system`
- `subprocess`
- `socket`
- `urllib`
- `http`
- `requests`
- `pathlib`
- `tempfile`
- `shutil`
- `curses`
- `brain.tick`
- `brain.llm`
- `brain.tlica` (the pattern ledger sits below the TLICA layer)
- `brain.ui` (the ledger does not depend on the operator UI)
- `threading`
- `asyncio`
- `atexit`
- `signal`
- `signal.signal`

Forbidden builtins / dynamic-execution calls:

- `eval`
- `exec`
- `compile`
- `__import__`
- `importlib.import_module`
- `importlib.__import__`

Allowed imports:

- `dataclasses`
- `enum`
- `fractions`
- `hashlib` (for the deterministic pattern ID per LOCK J)
- `typing`
- `brain.development.text_stream` (only for the bounded constants
  `STREAM_PATTERN_RECURRENCE_MIN`, `STREAM_PATTERN_RECURRENCE_MAX`,
  `STREAM_PATTERN_SIG_MAX`, `STREAM_PROVENANCE_MAX_LEN` and for the
  source-kind shape; **no** runtime `tick`, `BrainState`, `MSI`,
  `PtCns`, `Act`, or LLM-related import is allowed).
- `brain.tlica.profile` for `COGITO_ID` (read-only, for rejection
  checks).
- `brain.io_types` (if needed for shared bounded primitives).

The `pattern_ledger_static_audit` fixture (Step 9 will name the exact
filename) asserts the audit at runner time.

### LOCK N — Non-claims

```text
The Pattern Ledger work claims no consciousness, no sentience, no
subjective experience, no semantic understanding, no truth
adjudication, no agency, no self-modification, and no aggregate
consciousness score.
```

Specifically:

- The module surface includes **no** field, function, method,
  comment, or docstring that asserts the system is conscious,
  sentient, aware, experiencing, "understanding", or "thinking".
- The catalog row family includes **no** row that scores or asserts
  any of the above.
- The `/pattern-ledger` status text (if included per LOCK K) is
  factual and bounded: it reports entry counts, IDs, and recurrence
  counts, not subjective claims.
- The Pattern Ledger emits **no** aggregate scalar that purports to
  summarize "I-ness", coherence, awareness, or experience. Confidence
  is per-entry and is the LOCK H exact-Fraction formula only.
- The Pattern Ledger does not produce truth labels, PRESERVE/DAMAGE
  evaluations, semantic categories, or language labels.
- The Pattern Ledger does not adjudicate contradictions in the chunk
  stream. Contradiction-pressure text (e.g. `door=open`,
  `door=closed`) is recorded as structurally distinct evidence under
  the LOCK I signature; the ledger never picks a side.
- The Pattern Ledger does not self-modify code, fixtures, the
  catalog, or its own constants.

These non-claims survive any future review-gate edit unless the gate
explicitly cites and overrides LOCK N.

### LOCK O — Step 9 obligation

```text
Step 9 produces exactly:
  PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md
and STOPS at Step 10 Review Gate B.
```

Specifically, Step 9 must:

- finalize `I-PLEDGER-*` row IDs (working `I-PLEDGER-01..NN`),
- finalize exact row text per row (REQUIRED / STRUCTURAL /
  NOT-EXERCISED / DEFERRED / OBSERVED category, owning module,
  fixture assignment, Lean citation if any),
- specify the exact module path for the new fixture(s) and the
  exact `FIXTURE_MODULES` extension in `brain/invariants.py`,
- specify the catalog-version bump from `v0.20` to `v0.21` (or
  document why no bump is needed) and the corresponding banner
  update in `tools/catalog.py` (`EXPECTED_COUNTS`) plus the version
  stamps in `README.md`, `CURRENT_MISSION.md`, and
  `CURRENT_CAMPAIGN.md`,
- pick the LOCK K decision (`/pattern-ledger` in v1, or split into
  a follow-up row family),
- include a stop condition at Step 10 Review Gate B.

Step 9 must **not**:

- edit `brain/**`,
- edit `tools/**`,
- edit `INVARIANT_CATALOG.md`,
- edit `lean_reference/**`, `scenarios/**`, or `traces/**`,
- add fixtures,
- add committed helper scripts,
- run real LLM-backed commands.

Step 10 is a **review-only** step. No file changes. The operator
either accepts the Step 9 plan (allowing Step 11 to proceed) or
explicitly rejects / amends it (sending the plan back for revision).

Step 11 may apply the implementation only after Step 10 acceptance,
and only within the surface declared in `PHASE3_12_PATTERN_LEDGER_KICKOFF.md`
and the locks of this corrigenda.

## Summary

| Lock | Decision (one-line) |
|------|---------------------|
| A | Step 8 is documentation only; implementation requires Step 9 + Step 10. |
| B | Pattern Ledger v1 is session-local only; no DB schema change, no `SCHEMA_VERSION` bump. |
| C | Cold start = empty ledger; `/load-session` does not restore. |
| D | `observe(...)` filters duplicate evidence (idempotent); constructors stay strict. |
| E | At `max_entries`, `observe(...)` of a new signature returns the ledger unchanged — no eviction. |
| F | Evidence lists do not grow past `PATTERN_LEDGER_EVIDENCE_MAX`. |
| G | `recurrence_count` saturates at `STREAM_PATTERN_RECURRENCE_MAX`. |
| H | `confidence = Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)`, bounded `[0,1]`, no float. |
| I | Signature is structural (counts and source), not semantic. |
| J | `pattern_id = "pledger:" + sha256(repr(signature))[:16]` — fully deterministic. |
| K | `/pattern-ledger` UI is optional and read-only; split out if it broadens scope. |
| L | Observe on successful `/stream` append only; never on `/step`, read-only commands, or failures. |
| M | Static audit rejects every I/O / shell / dynamic-import / LLM / tick / TLICA import or call. |
| N | No consciousness / sentience / experience / truth / agency / self-modification / aggregate score. |
| O | Step 9 writes the catalog patch plan and stops at Step 10 Review Gate B. |

## Validation

Re-ran after writing this corrigenda (no source under `brain/**`,
`tools/**`, `lean_reference/**`, `scenarios/**`, or `traces/**` was
touched; only this and the companion kickoff file were added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
