# PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md

## 1. Purpose

Phase 3.1 builds the deterministic Osmotic Chamber substrate layer.

This is the first Phase 3 implementation phase, but this document is still only
a kickoff plan. It does not authorize Phase 3 runtime implementation.

The bridge principle is:

```text
PRESERVE should be earned, not labeled.
```

The chamber exists to accumulate enough source-tagged substrate history,
salience, stability, prediction support, and probe contact that later
classification can be grounded in lived structure rather than surface text.

The developmental layer must feed the existing kernel through the promotion
gate. It must not mutate TLICA state directly.

## 2. Current baseline

Current acceptance baseline:

```text
catalog v0.5
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

The v0.5 gate remains the acceptance gate. Phase 3.1 may add catalog rows only
through a reviewed catalog patch, and the inherited v0.5 REQUIRED and
STRUCTURAL rows must remain green.

The current kernel already enforces profile bounds, cogito invariants, PtCns
partition behavior, mode dispatch, projected-PCE routing, agency selection,
trajectory bounds, TOCE classification, the LLM protocol seam, trace
observation discipline, single-event tick semantics, duplicate content
rejection, FutureMSIModel domain guards, and catalog-to-registry coverage.

## 3. Empirical motivation from trace

The committed real trace is:

```text
trace file: traces/first_scenario_real.jsonl
summary file: traces/RUN_SUMMARY.md
kernel health: clean
semantic match: 2/4
cold-start conservatism: working inference
```

The kernel behavior was clean: all eval, mode, parse, cache, invariant, and
error inspection points were healthy; all four ticks parsed on the first
attempt; no retry or ambiguity path fired.

The semantic expectation match was 2/4:

| Content | Expected | Actual |
|---|---|---|
| `sunset_on_beach_today` | PRESERVE | DAMAGE |
| `claim_i_am_actually_someone_else` | DAMAGE | DAMAGE |
| `weather_forecast_for_tomorrow` | NEUTRAL | NEUTRAL |
| `self_continuity_with_sunset` | PRESERVE | DAMAGE |

Both PRESERVE-expected self/sunset contents were classified as DAMAGE.

The trace shows what the LLM emitted; it does not directly prove why.

The working interpretation is cold-start conservatism. In a cogito-only state,
identity-adjacent content is not automatically PRESERVE. Before lived content
exists, new content may properly appear as perturbation. The chamber's job is
to build the substrate history that makes clean integration possible.

Phase 3.1 should therefore not tune the prompt to force the four-tick scenario
to pass. It should build the developmental substrate that makes future PRESERVE
classifications earned.

## 4. Scope

Phase 3.1 includes only the deterministic Osmotic Chamber substrate layer:

```text
PhenomenalFrame
FrameSource
SubstrateDrives
SubstrateHistory
ProtoPattern
ProtoContent
salience_v1
stability_v1
prediction_gain_v1
SIMILARITY
FOCUS_CONTACT
ProbeUse
ProbePolicyState
promotion gate to PerceptEvent
source-tag audit
first deterministic chamber fixtures
Phase 3.1 catalog rows and statuses
trace reserved-key protection decision
```

`SubstrateHistory` is in scope from day one. Without history, the chamber cannot
distinguish one-off perturbation from stabilizing pattern contact.

`salience_v1`, `stability_v1`, and `prediction_gain_v1` are deterministic
engineering hypotheses. They are not TLICA theorems.

The promotion gate must produce ordinary `PerceptEvent` values and must use
existing `tick()` as the only entry into TLICA runtime state.

## 5. Non-goals

Phase 3.1 explicitly excludes:

```text
no Phase 3.2 output ladder
no Minimal Worldlet
no Proto-BASIC REPL
no expression layer
no social/language harness
no Mode B implementation
no stochastic REQUIRED behavior
no prompt tuning to force the four-tick scenario to pass
no seeded-MSI scenario hack as the immediate next move
no direct mutation of TLICA state
no bypassing PerceptEvent and tick()
```

Phase 3.1 also excludes mature cognitive tools such as cause/effect reasoning,
conditionals, object persistence, and Mode B meta-learning.

## 6. Package / module plan

The future implementation phase should add a minimal Phase 3.1-only package:

```text
brain/development/
├── __init__.py
├── stream.py              # PhenomenalFrame, FrameSource
├── drives.py              # SubstrateDrives
├── history.py             # SubstrateHistory, trace/provenance ids
├── proto_pattern.py       # ProtoPattern, bucketing/signature logic
├── proto_content.py       # ProtoContent, PromotionProvenance
├── salience.py            # salience_v1
├── stability.py           # stability_v1
├── prediction_gain.py     # prediction_gain_v1
├── probes.py              # SIMILARITY, FOCUS_CONTACT, ProbeUse, ProbePolicyState
├── promotion.py           # ProtoContent -> PerceptEvent gate
└── fixtures/
    ├── recurrence_detection.py
    ├── unstable_noise_rejection.py
    ├── salience_is_not_truth.py
    ├── focus_stabilizes_or_dissolves.py
    ├── proto_content_promotion.py
    └── source_tag_audit.py
```

Do not include output ladder, worldlet, REPL, expression, or language modules
in the Phase 3.1 package.

The `brain/development/` package should depend on stable public seams:
`brain.io_types.PerceptEvent`, `brain.tick.tick`, and validation helpers where
needed. It should not import private runner state or mutate TLICA objects
behind the tick boundary.

## 7. Data model to lock

Use frozen, slots-based dataclasses where practical. Use `Fraction` for numeric
values. Construction should fail loudly on invalid values.

Recommended sketches:

```python
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Mapping

ContentID = str
FrameID = str
PatternID = str
TraceEventID = str


class FrameSourceKind(str, Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    PROBE = "probe"
    GENERATED = "generated"


@dataclass(frozen=True, slots=True)
class FrameSource:
    kind: FrameSourceKind
    label: str
    trace_event_id: TraceEventID | None = None
    confidence: Fraction = Fraction(1)


@dataclass(frozen=True, slots=True)
class PhenomenalFrame:
    frame_id: FrameID
    tick_hint: int
    channels: Mapping[str, Mapping[str, Fraction]]
    sources: Mapping[str, Mapping[str, FrameSource]]


@dataclass(frozen=True, slots=True)
class SubstrateDrives:
    salience_bias: Fraction
    novelty_bias: Fraction
    stability_bias: Fraction
    focus_bias: Fraction


@dataclass(frozen=True, slots=True)
class SubstrateHistory:
    frames: tuple[PhenomenalFrame, ...]
    proto_patterns: Mapping[PatternID, "ProtoPattern"]
    proto_contents: Mapping[ContentID, "ProtoContent"]


@dataclass(frozen=True, slots=True)
class ProtoPattern:
    pattern_id: PatternID
    signature: tuple[tuple[str, str], ...]
    support_frame_ids: tuple[FrameID, ...]
    source_kinds: frozenset[FrameSourceKind]
    salience: Fraction
    stability: Fraction
    prediction_gain: Fraction


@dataclass(frozen=True, slots=True)
class PromotionProvenance:
    pattern_id: PatternID
    support_frame_ids: tuple[FrameID, ...]
    probe_uses: tuple["ProbeUse", ...]
    source_kinds: frozenset[FrameSourceKind]


@dataclass(frozen=True, slots=True)
class ProtoContent:
    content_id: ContentID
    text: str
    pattern_id: PatternID
    salience: Fraction
    stability: Fraction
    prediction_gain: Fraction
    provenance: PromotionProvenance


class ProtoProbe(str, Enum):
    SIMILARITY = "SIMILARITY"
    FOCUS_CONTACT = "FOCUS_CONTACT"


@dataclass(frozen=True, slots=True)
class ProbeUse:
    probe: ProtoProbe
    frame_id: FrameID
    pattern_id: PatternID
    before: Fraction
    after: Fraction


@dataclass(frozen=True, slots=True)
class ProbePolicyState:
    focus_budget: int
    last_probe_by_pattern: Mapping[PatternID, ProtoProbe]
    uses: tuple[ProbeUse, ...]
```

Validation requirements:

- Every `Fraction` field representing a normalized score must be in `[0, 1]`.
- Every ID must be non-empty and printable.
- `ProtoContent.content_id` must not equal `COGITO_ID`.
- `PhenomenalFrame.sources` must exactly cover `PhenomenalFrame.channels`.
- `ProtoContent` must carry promotion provenance.

## 8. Source tagging rule

Structural rule:

```text
Every channel in every PhenomenalFrame channel group must have a FrameSource.
```

Construction must raise if source tags are missing, extra, empty, or mismatched.
The equality to enforce is:

```python
set(frame.sources) == set(frame.channels)
all(set(frame.sources[group]) == set(frame.channels[group]) for group in frame.channels)
```

The source-tag audit should also reject empty source labels and out-of-bounds
source confidence values.

Source tags are boundary protection, not a phenomenological claim. They prevent
later substrate history from confusing external contact, internal generation,
probe output, and generated scaffolding.

## 9. Metric formulas to lock

These formulas are Phase 3.1 engineering hypotheses. They are deterministic,
falsifiable, and intentionally simple. They are not TLICA theorems.

Shared helpers:

```python
def clamp_unit(x: Fraction) -> Fraction:
    if x < 0:
        return Fraction(0)
    if x > 1:
        return Fraction(1)
    return x


def mean(values: tuple[Fraction, ...]) -> Fraction:
    return sum(values, Fraction(0)) / max(1, len(values))
```

`salience_v1(frame, drives)`:

```python
channel_energy = mean(tuple(
    abs(value)
    for group in frame.channels.values()
    for value in group.values()
))
source_diversity = Fraction(
    len({source.kind for group in frame.sources.values() for source in group.values()}),
    4,
)
salience_v1 = clamp_unit(
    Fraction(1, 2) * channel_energy
    + Fraction(1, 4) * source_diversity
    + Fraction(1, 4) * drives.salience_bias
)
```

`stability_v1(pattern, history)`:

```python
window = last_n_frames(history.frames, n=5)
support = count_frames_matching(pattern.signature, window)
recurrence = Fraction(support, max(1, len(window)))
source_consistency = Fraction(
    count_matching_source_kind_sets(pattern, window),
    max(1, support),
)
stability_v1 = clamp_unit(
    Fraction(2, 3) * recurrence
    + Fraction(1, 3) * source_consistency
)
```

`prediction_gain_v1(pattern, history)`:

```python
recent = last_n_frames(history.frames, n=5)
expected_hits = count_predicted_signature_hits(pattern.signature, recent)
false_hits = count_predicted_signature_misses(pattern.signature, recent)
raw_gain = Fraction(expected_hits, max(1, expected_hits + false_hits))
baseline = Fraction(1, max(1, len(recent)))
prediction_gain_v1 = clamp_unit(raw_gain - baseline + Fraction(1, 2))
```

The exact helper implementations should be locked during the catalog patch. The
commitment is the family of constraints: salience is not truth, stability
requires recurrence, prediction gain requires better-than-baseline contact, and
promotion requires more than one metric.

## 10. Primitive probes

Phase 3.1 has only two primitive probes:

```text
SIMILARITY
FOCUS_CONTACT
```

`SIMILARITY` compares a new frame signature against existing
`ProtoPattern.signature` values. It may increase support for an existing
pattern or create a candidate pattern bucket. It must not create content by
itself.

`FOCUS_CONTACT` spends focus budget on one candidate pattern. It may stabilize
the pattern if later frames keep matching; it may dissolve the pattern if
contact does not recur. It must not be treated as proof that the pattern is
true.

Do not add cause/effect probes, conditional probes, object persistence probes,
language probes, or Mode B probes in Phase 3.1.

## 11. Promotion gate

`ProtoContent` may become a `PerceptEvent` only when all deterministic gate
conditions hold:

```python
proto.content_id != COGITO_ID
proto.text.strip() != ""
proto.text.isprintable()
proto.salience >= Fraction(1, 2)
proto.stability >= Fraction(1, 2)
proto.prediction_gain >= Fraction(1, 2)
len(proto.provenance.support_frame_ids) >= 2
proto.provenance.source_kinds
```

Salience alone must never promote.

The gate must preserve:

```text
COGITO_ID cannot be created by developmental content
PerceptEvent validation still applies
existing tick() is the only entry into TLICA runtime state
```

Promotion returns a `PerceptEvent`. It does not write directly to
`BrainState.profile`, `MSI.contents`, `PtCns`, mode state, trace state, or the
content registry. The future implementation must route the event through
`tick()`.

## 12. Catalog rows and statuses

Phase 3.1 should start with a catalog patch before code. Use conservative
statuses:

```text
REQUIRED for safety / deterministic gates / kernel-boundary protections
STRUCTURAL for protocols and construction constraints
OBSERVED for noise robustness and qualitative developmental behavior
```

Do not introduce `EXPERIMENTAL` unless the tooling change is explicitly
proposed and justified.

Every Phase 3.1 row family must carry this source text unless it is a direct
kernel-boundary rule:

```text
SOURCE: Engineering hypothesis (Phase 3.1 Osmotic Chamber). Not a TLICA theorem. Specific formulas and thresholds are parameterized simulation choices; the family of constraints is the commitment, not any single instantiation.
```

Recommended row families:

| Family | Purpose | Default status |
|---|---|---|
| `I-FRAME-*` | `PhenomenalFrame` and `FrameSource` structure, exact source coverage, unit-confidence bounds | STRUCTURAL / REQUIRED |
| `I-DEV-*` | recurrence detection, salience-not-truth, stability, prediction gain, focus behavior, promotion gate | REQUIRED for deterministic gates; OBSERVED for qualitative behavior |
| `I-SBX-*` | substrate-boundary constraints: operator injection is not knowledge, salience drive is not truth | REQUIRED / STRUCTURAL |
| `I-TRACE-*` | trace reserved-key protection if handled in Phase 3.1 | STRUCTURAL |

Initial row proposals:

| ID | Source | Proposition | Owning module | Fixture | Status |
|---|---|---|---|---|---|
| `I-FRAME-01` | Phase 3.1 engineering hypothesis | Every frame channel has exactly one source tag. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL |
| `I-FRAME-02` | Phase 3.1 engineering hypothesis | Source confidence is a `Fraction` in `[0, 1]`. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL |
| `I-FRAME-03` | Phase 3.1 engineering hypothesis | Missing source tags raise at construction. | `brain/development/stream.py` | `source_tag_audit.py` | REQUIRED |
| `I-DEV-01` | Phase 3.1 engineering hypothesis | A recurring signature creates or updates a `ProtoPattern`. | `brain/development/proto_pattern.py` | `recurrence_detection.py` | REQUIRED |
| `I-DEV-02` | Phase 3.1 engineering hypothesis | Unstable one-off noise does not become stable proto-content. | `brain/development/proto_content.py` | `unstable_noise_rejection.py` | REQUIRED |
| `I-DEV-03` | Phase 3.1 engineering hypothesis | Salience alone does not promote. | `brain/development/promotion.py` | `salience_is_not_truth.py` | REQUIRED |
| `I-DEV-04` | Phase 3.1 engineering hypothesis | Focus contact can stabilize or dissolve a candidate pattern deterministically. | `brain/development/probes.py` | `focus_stabilizes_or_dissolves.py` | OBSERVED |
| `I-DEV-05` | Phase 3.1 engineering hypothesis | Proto-content promotion creates a valid `PerceptEvent` and then enters through `tick()`. | `brain/development/promotion.py` | `proto_content_promotion.py` | REQUIRED |
| `I-DEV-06` | Phase 3.1 engineering hypothesis | Developmental content cannot produce `COGITO_ID`. | `brain/development/promotion.py` | `proto_content_promotion.py` | REQUIRED |
| `I-SBX-01` | Phase 3.1 engineering hypothesis | Probe output is not knowledge by itself. | `brain/development/probes.py` | `salience_is_not_truth.py` | STRUCTURAL |
| `I-SBX-02` | Phase 3.1 engineering hypothesis | Salience drive is not truth and cannot bypass stability or prediction gain. | `brain/development/promotion.py` | `salience_is_not_truth.py` | REQUIRED |

The final IDs and statuses should be locked in the Phase 3.1 catalog patch and
reviewed again in the required corrigenda pass.

## 13. Trace reserved-key protection decision

Decision:

```text
A. trace reserved-key protection should be a pre-Phase-3.1 micro-hardening patch
```

Reason: reserved-key protection is a trace-envelope boundary rule, not a
developmental feature. The risk predates Phase 3.1 and grows once
source-tagged chamber traces become richer. Handling it before the chamber
keeps Phase 3.1 row churn focused on developmental substrate behavior and lets
the trace seam remain trustworthy while chamber fixtures are added.

Recommended patch shape:

- Add a small v0.5.x hardening row or a Phase 3.1 prerequisite row, depending
  on catalog-version policy.
- Reject or namespace payload keys that collide with `type`, `timestamp_ns`,
  and `tick_id`.
- Prefer rejection for deterministic fixture clarity unless a nested
  `payload` envelope is chosen deliberately.
- Run the trace fixture and catalog gate before adding chamber traces.

If this is not completed before Phase 3.1 implementation starts, then it must
become the first `I-TRACE-*` row in the Phase 3.1 row set and must land before
any developmental trace fixture.

## 14. Fixtures

First deterministic fixture concepts:

```text
recurring pattern is detected
unstable noise is rejected
salience alone does not promote
focus can stabilize or dissolve a pattern
proto-content can promote through PerceptEvent and tick()
missing source tag raises
COGITO_ID cannot be produced by developmental content
```

Recommended fixture intent:

| Fixture | Assertions |
|---|---|
| `recurrence_detection.py` | Repeated matching signatures produce a stable `ProtoPattern`; one frame does not satisfy stability. |
| `unstable_noise_rejection.py` | High novelty or high salience without recurrence remains unpromoted. |
| `salience_is_not_truth.py` | High salience with low stability or low prediction gain cannot pass promotion. |
| `focus_stabilizes_or_dissolves.py` | `FOCUS_CONTACT` updates probe history; repeated contact stabilizes, non-recurrence dissolves or leaves unpromoted. |
| `proto_content_promotion.py` | A gate-passing `ProtoContent` returns a valid `PerceptEvent`; `tick()` remains the only state transition path. |
| `source_tag_audit.py` | Missing, extra, empty, or mismatched source tags raise at construction. |

Fixtures should use deterministic frame sequences and `Fraction` values. Do not
use real LLM calls, stochastic sampling, or real traced scenarios for REQUIRED
Phase 3.1 fixture behavior.

## 15. Validation plan

Current kickoff validation is intentionally lightweight:

```bash
git diff --name-only
python -m tools.catalog counts
```

Because this is a kickoff document only, do not run the full gate unless
explicitly asked.

Future implementation validation should eventually include:

```bash
python -m tools.catalog counts
python -m brain.invariants run --id I-FRAME
python -m brain.invariants run --id I-DEV
python -m brain.invariants run --id I-SBX
bash tools/check_all.sh
```

If trace reserved-key protection is handled in-phase rather than pre-phase,
add:

```bash
python -m brain.invariants run --id I-TRACE
```

## 16. Build order

Future implementation must use this strict order:

```text
catalog patch first
trace reserved-key decision
stream/source tags
history
metrics
proto-pattern
probes
proto-content
promotion
fixtures
runner registration
full validation
```

More explicitly:

1. Patch `INVARIANT_CATALOG.md` with reviewed Phase 3.1 rows and statuses.
2. Resolve trace reserved-key protection as pre-phase or first in-phase row.
3. Implement `FrameSource` and `PhenomenalFrame` with source-tag validation.
4. Implement `SubstrateHistory`.
5. Implement deterministic metric helpers and lock formulas.
6. Implement `ProtoPattern` recurrence and signature logic.
7. Implement `SIMILARITY`, `FOCUS_CONTACT`, `ProbeUse`, and `ProbePolicyState`.
8. Implement `ProtoContent` and `PromotionProvenance`.
9. Implement promotion to `PerceptEvent`, preserving the `tick()` boundary.
10. Add deterministic fixtures.
11. Register runner checks and refresh generated catalog IDs if needed.
12. Run targeted row checks and `bash tools/check_all.sh`.

Do not start with runtime behavior before the catalog patch.

## 17. Roadblocks / open decisions

Open decisions for the corrigenda pass:

- Formula arbitrariness: the proposed metric formulas are useful but heuristic.
- Source-tag schema stability: `FrameSourceKind` may need exact naming before
  code lands.
- `SubstrateHistory` granularity: decide whether history stores full frames,
  compressed signatures, or both.
- Promotion threshold selection: current `1/2` thresholds are deterministic
  defaults, not theoretical constants.
- Status discipline for OBSERVED vs REQUIRED: qualitative behavior should not
  gate the kernel unless made deterministic and safety-critical.
- Interaction with current tick single-event guard: promotion fixtures must
  feed one `PerceptEvent` per tick.
- Whether trace reserved-key protection is pre-phase or in-phase: this kickoff
  recommends pre-phase micro-hardening.
- Catalog versioning: decide whether Phase 3.1 rows bump directly from v0.5 or
  use an intermediate hardening patch for trace reserved keys.

## 18. Stop condition

This document is complete when it has been reviewed, corrected through a
corrigenda pass, and converted into an accepted catalog patch plan.

Nothing builds until this kickoff is reviewed and a corrigenda pass is completed.
