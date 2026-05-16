# PHASE3_7_TEXT_STREAM_INGRESS_KICKOFF.md

## Purpose

Concretize the bounded local structures named in
`PHASE3_7_TEXT_STREAM_INGRESS_SYNTHESIS.md`. This is a planning artifact
only. It does not introduce catalog rows, edit `tools/catalog.py`,
change `brain/invariants.py`, add runtime modules, add fixtures, or
change the TLICA runtime boundary. The corrigenda audits this artifact;
the catalog patch plan binds the audited result.

## 1. Structural commitments

```text
TextStreamSource              finite closed enumeration of source kinds
TextStreamChunk               bounded raw / printable text record
TextStreamHistory             copy-on-write bounded local history of chunks
StreamFeatureVector           deterministic exact int / Fraction features
SegmentCandidate              structural span (e.g. delimiter / line) only
StreamPattern                 recurrence-backed structural pattern
StreamPromotionCandidate      explicit candidate for the existing
                              PerceptEvent / tick() route, not a
                              PerceptEvent itself
```

All records are frozen dataclasses (or equivalent immutable shapes).
Every field is a bounded primitive, an enumeration value, an exact
`Fraction`, a tuple of bounded primitives, or a reference to another
frozen `text_stream` record. No callable, file handle, socket, LLM
client, or path object appears on any field.

## 2. TextStreamSource enumeration

```text
class TextStreamSource(Enum):
    OPERATOR     = "operator"      # operator-typed text (Phase 3.8 /stream)
    SYSTEM       = "system"        # deterministic local-system text
    PROBE_ECHO   = "probe_echo"    # echo of an existing chunk
    GENERATED    = "generated"     # deterministic local generation tag
```

The enumeration is closed at v0.14. Adding a kind requires a future
campaign and a new catalog row. `TextStreamSource` deliberately does
*not* alias `FrameSourceKind` — it is its own closed enumeration so
Phase 3.7 can evolve without coupling to Phase 3.1's frame source
discipline. (Reuse is fine; aliasing creates back-pressure on
Phase 3.1.)

A real LLM-backed `MODEL` source kind is *not* introduced in Phase 3.7;
the explicit LLM Runtime Toggle (Phase 3.8b) reuses the existing
`LLMClient` / `tick(..., client, ...)` seam, never a second
classification path through the stream substrate.

## 3. TextStreamChunk

```text
@dataclass(frozen=True, slots=True)
class TextStreamChunk:
    chunk_id: str                 # bounded printable, never COGITO_ID
    source: TextStreamSource
    text: str                     # bounded printable, length <= TEXT_MAX_LEN
    tick_at_event: int            # non-negative int
    provenance_tag: str           # bounded printable
```

Field-level rules (the corrigenda will audit these):

```text
chunk_id            bounded printable; not equal to COGITO_ID; rejected
                    on collision with the reserved sentinel
source              must be a TextStreamSource
text                bounded printable; length <= STREAM_TEXT_MAX_LEN
                    (small fixed cap; corrigenda locks the exact value);
                    not equal to COGITO_ID; rejection on over-bound text
                    is hard (no silent truncation on the chunk text path)
tick_at_event       int >= 0
provenance_tag      bounded printable, length <= STREAM_PROVENANCE_MAX_LEN;
                    a closed-vocabulary tag derived from the source
                    record's existing provenance (no free-form text)
```

The constructor copies bounded values out of the caller's input; it
does not store any reference to a mutable container. `__post_init__`
applies all the above rejections and tags failures with `I-STRM-*`
identifiers.

## 4. TextStreamHistory

```text
@dataclass(frozen=True, slots=True)
class TextStreamHistory:
    chunks: tuple[TextStreamChunk, ...] = ()
```

History rules:

```text
chunks                  tuple[TextStreamChunk, ...]; copy-on-write;
                        bounded by STREAM_HISTORY_MAX_CHUNKS (small
                        fixed cap; corrigenda locks the exact value);
                        construction with > MAX raises ValueError
                        tagged with the row id; the append() returns a
                        new TextStreamHistory with the oldest entry
                        dropped when the buffer is full
no other field          the history holds no callable, file handle,
                        socket, LLM client, path object, or reference
                        into BrainState / source histories
```

`append(chunk)` must reject non-`TextStreamChunk` values with `TypeError`.

## 5. StreamFeatureVector

```text
@dataclass(frozen=True, slots=True)
class StreamFeatureVector:
    char_count: int
    token_count: int
    distinct_token_count: int
    line_count: int
    max_run_length: int
    whitespace_only: bool
```

Rules:

```text
all fields are exact int values (no float, no math, no round)
extract_features(chunk) is a pure deterministic function that returns
  the same StreamFeatureVector for any equal chunk text
the function uses str.split / str.splitlines / set length and
  printable-char counting only — no regex, no parser, no language
  model, no probabilistic step
```

`StreamFeatureVector` is *structural*; it is not language and is not
truth-evaluative.

## 6. SegmentCandidate

```text
@dataclass(frozen=True, slots=True)
class SegmentCandidate:
    chunk_id: str
    start: int                    # 0 <= start < end <= len(chunk.text)
    end: int
    segment_kind: str             # closed vocabulary, e.g. "line",
                                  # "delimited_span", "whitespace_run"
```

Rules:

```text
chunk_id              bounded printable; not COGITO_ID
start, end            int; 0 <= start < end <= chunk text length
segment_kind          one of a small closed vocabulary locked in the
                      catalog patch plan (suggested initial set:
                      "line", "delimited_span", "whitespace_run")
no payload text       SegmentCandidate carries spans only; the chunk
                      text is the source of truth, not a copy on the
                      candidate
```

A `SegmentCandidate` is *not* a parse tree. It is a span. The
construction discipline rejects empty spans (`start == end`) and
out-of-bounds spans.

## 7. StreamPattern

```text
@dataclass(frozen=True, slots=True)
class StreamPattern:
    pattern_id: str                # bounded printable; not COGITO_ID
    signature: tuple[str, ...]    # bounded tuple of bounded printable
                                   # tokens that defines the structural
                                   # shape; not a grammar production
    recurrence_count: int          # int; >= STREAM_PATTERN_RECURRENCE_MIN
    last_seen_tick: int            # int; >= 0
```

Rules:

```text
recurrence_count      must be >= STREAM_PATTERN_RECURRENCE_MIN (small
                      fixed cap; corrigenda locks; suggested: 2);
                      construction with recurrence_count below the
                      threshold raises ValueError tagged with the row id
signature             bounded; len(signature) <= STREAM_PATTERN_SIG_MAX;
                      each token bounded printable; not a grammar
                      production; not a language model output
no truth field        StreamPattern carries no PRESERVE / DAMAGE / PCE /
                      ProjectedPCE / Act / ModeOp / AgencyWitness field;
                      it does not enter PtCns.evaluate or any TLICA
                      runtime path
```

A `StreamPattern` is structural recurrence evidence below the kernel.
It is not a TLICA `PRESERVE` claim and cannot be promoted to one without
the explicit Phase 3.8 `/stream-promote` route.

## 8. StreamPromotionCandidate

```text
@dataclass(frozen=True, slots=True)
class StreamPromotionCandidate:
    candidate_id: str               # bounded printable; not COGITO_ID
    target_content_id: str          # bounded printable; not COGITO_ID
    chunk_id: str                   # source chunk id
    pattern_id: str | None          # supporting StreamPattern, if any
    source: TextStreamSource
    text: str                       # bounded printable; not COGITO_ID
    provenance_tag: str             # bounded printable
```

Rules:

```text
candidate_id          bounded printable; not COGITO_ID; rejected on
                      collision with the reserved sentinel
target_content_id     bounded printable; not COGITO_ID; rejected on
                      collision; not derived from text alone — must be
                      explicitly supplied by the caller (Phase 3.8
                      /stream-promote)
chunk_id              must reference an existing chunk_id (the
                      validator does not load the history; the caller
                      is responsible for passing the matching chunk;
                      the catalog patch plan locks this contract)
pattern_id            either None or bounded printable; not COGITO_ID
text                  bounded printable; not COGITO_ID; equality with
                      the source chunk's text is permitted but the
                      candidate carries its own copy
not a PerceptEvent    the candidate is queued for explicit operator
                      action in Phase 3.8; the candidate constructor
                      does not call tick(), does not construct a
                      PerceptEvent, and does not mutate any kernel
                      container
```

The constructor is a pure function. It does not register callbacks.

## 9. Constructor surface

Public callables (final names locked by the catalog patch plan):

```text
def construct_text_stream_chunk(
    *,
    chunk_id: str,
    source: TextStreamSource,
    text: str,
    tick_at_event: int = 0,
    provenance_tag: str = "",
) -> TextStreamChunk: ...

def append_text_stream_chunk(
    history: TextStreamHistory,
    chunk: TextStreamChunk,
) -> TextStreamHistory: ...

def extract_stream_features(chunk: TextStreamChunk) -> StreamFeatureVector: ...

def find_segment_candidates(
    chunk: TextStreamChunk,
    *,
    delimiters: tuple[str, ...] = (),
) -> tuple[SegmentCandidate, ...]: ...

def detect_stream_patterns(
    history: TextStreamHistory,
) -> tuple[StreamPattern, ...]: ...

def construct_stream_promotion_candidate(
    *,
    candidate_id: str,
    target_content_id: str,
    chunk: TextStreamChunk,
    pattern: StreamPattern | None = None,
    provenance_tag: str = "",
) -> StreamPromotionCandidate: ...
```

All constructors are pure. They do not register callbacks, do not call
`tick()`, do not emit `PerceptEvent`, and do not mutate any input.

## 10. Bounded feature extraction

`extract_stream_features(chunk)` extracts only:

```text
char_count            len(chunk.text)
token_count           len(chunk.text.split())
distinct_token_count  len(set(chunk.text.split()))
line_count            len(chunk.text.splitlines())
max_run_length        max consecutive identical token run
whitespace_only       not chunk.text or not chunk.text.strip()
```

No regex, no parser, no language model, no probabilistic step
participates. All arithmetic uses `int` only.

## 11. Anti-growth and boundedness

```text
TextStreamHistory                 bounded by STREAM_HISTORY_MAX_CHUNKS
TextStreamChunk.text              bounded by STREAM_TEXT_MAX_LEN; over-
                                  bound raises (no silent truncation)
SegmentCandidate count per chunk  bounded by STREAM_SEGMENTS_MAX
StreamPattern recurrence_count    must be >= STREAM_PATTERN_RECURRENCE_MIN
StreamPromotionCandidate per
  history walk                    bounded by STREAM_PROMOTION_MAX
```

Repeated identical chunks must not inflate `StreamPattern` strength
beyond the cap; the suggested `recurrence_count` saturates at
`STREAM_PATTERN_RECURRENCE_MAX`. The corrigenda locks the exact
constants and the catalog patch plan binds them.

## 12. COGITO_ID defenses

```text
TextStreamChunk.chunk_id                cannot equal COGITO_ID
TextStreamChunk.text                    cannot equal COGITO_ID
StreamPattern.pattern_id                cannot equal COGITO_ID
SegmentCandidate.chunk_id               cannot equal COGITO_ID
StreamPromotionCandidate.candidate_id   cannot equal COGITO_ID
StreamPromotionCandidate.target_content_id
                                        cannot equal COGITO_ID
StreamPromotionCandidate.chunk_id       cannot equal COGITO_ID
StreamPromotionCandidate.pattern_id     cannot equal COGITO_ID (when set)
StreamPromotionCandidate.text           cannot equal COGITO_ID
```

The validators reuse the existing reserved sentinel from
`brain/_catalog_ids.py` (`COGITO_ID`).

## 13. Non-mutating substrate contract

The text stream module is forbidden to do any of:

```text
mutate BrainState / ScalarProfile / MSI / PtCns / ContentRegistry
mutate any existing Phase 3.1-3.5 source history
call any source-history mutator
register an atexit / signal / callback hook
call float(), round(), or math.*
import os, subprocess, socket, urllib, http, requests, pathlib,
       tempfile, shutil, curses, brain.llm, brain.tlica, brain.tick
write to disk
open a file
open a socket
spawn a subprocess
invoke a real LLM client
emit a PerceptEvent
schedule a tick
```

The static audit fixture (catalog plan) AST-checks the module to enforce
these rules.

## 14. Exclusions for Phase 3.7

```text
no Mode B reflective planning
no language understanding / parser / grammar / chat
no natural-language teacher / corrector
no real LLM calls
no operator command surface (Phase 3.8 owns /stream commands)
no LLM Runtime Toggle (Phase 3.8b)
no TLICA mutation
no scenario / trace schema change
no save / export path
no cross-invocation persistence
no aggregate "quality" / "intelligence" / "social-success" stream score
no UI integration in Phase 3.7
```

## 15. Open questions for the corrigenda

```text
Q1  Are STREAM_TEXT_MAX_LEN, STREAM_HISTORY_MAX_CHUNKS,
    STREAM_SEGMENTS_MAX, STREAM_PATTERN_RECURRENCE_MIN,
    STREAM_PATTERN_RECURRENCE_MAX, and STREAM_PROMOTION_MAX
    the right names and ranges? (Suggested initial values: 1024,
    256, 32, 2, 256, 64.)

Q2  Should SegmentCandidate carry only spans, or should it also
    carry the segment kind explicitly? (Recommended: spans + a
    closed-vocabulary kind tag.)

Q3  Should StreamPattern carry the actual signature tokens, or
    only a hash of them? (Recommended: actual tokens, bounded by
    STREAM_PATTERN_SIG_MAX, since structural transparency matters.)

Q4  Should StreamPromotionCandidate require a supporting
    StreamPattern (pattern_id non-None), or allow chunk-only
    candidates? (Recommended: allow chunk-only for /stream-promote
    explicit operator action; the operator carries the
    accountability, not the substrate.)

Q5  Should the chunk_id on a StreamPromotionCandidate be looked up
    against TextStreamHistory at construction time, or treated as
    a caller contract? (Recommended: caller contract; the catalog
    patch plan locks this.)

Q6  Should the OBSERVED aggregate stream walk be a Python frozen
    dataclass only, or include a JSON-printable form? (Recommended:
    Python frozen dataclass only; serialization is a future-campaign
    concern.)

Q7  Should there be a NOT-EXERCISED row for stream save / export
    (mirroring I-EXP-18 and I-REF-14)? (Recommended: yes — same
    policy, same shape.)
```

## 16. Next artifact

```text
PHASE3_7_TEXT_STREAM_INGRESS_CORRIGENDA.md
```

The corrigenda will audit each of §1–§15 here, lock the open questions,
choose final constants, and produce a verdict on whether the kickoff is
ready for the catalog patch plan.
