# Phase 3.1 Osmotic Chamber Corrigenda

## Purpose

This corrigenda tightens `PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md` before any
Phase 3.1 implementation begins.

It is a planning artifact only. It does not authorize Phase 3 runtime code,
catalog edits, trace changes, scenario edits, or Lean-reference changes.

The governing discipline remains:

```text
plan -> corrigenda -> code
```

The bridge principle remains:

```text
PRESERVE should be earned, not labeled.
```

Phase 3.1 remains limited to the deterministic Osmotic Chamber substrate layer.
It does not include the output ladder, worldlet, REPL, expression layer, or
social/language harness.

## Baseline Preserved

The kickoff is directionally sound and should be preserved in these respects:

- Phase 3.1 is still planning-only until kickoff plus corrigenda are accepted.
- The Osmotic Chamber is a developmental substrate before symbolic PRESERVE is
  expected to become stable.
- `SubstrateHistory` is in scope from day one.
- Existing `PerceptEvent` and `tick()` remain the only path into TLICA runtime
  state.
- Salience, stability, and prediction gain are engineering hypotheses, not
  TLICA theorems.
- Deterministic fixture behavior should be locked before noisy or qualitative
  behavior is treated as evidence.
- Real LLM trace behavior remains empirical evidence, not a REQUIRED fixture
  oracle.

The corrections below are implementation-readiness changes to the plan, not a
change in phase scope.

## C1 - FrameSourceKind Granularity

### Problem

The kickoff's proposed source enum is too coarse:

```python
class FrameSourceKind(str, Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    PROBE = "probe"
    GENERATED = "generated"
```

This conflates source types that Phase 3.1 must keep distinct. In particular,
operator-injected content must not be confused with endogenous patterning, and
probe echo must not be confused with external contact.

Source confusion would undermine the histories that Phase 3.1 is supposed to
build: salience history, stability history, prediction-support history, and
promotion provenance.

### Required correction

Use this Phase 3.1 source enum:

```python
class FrameSourceKind(str, Enum):
    ENDOGENOUS = "endogenous"
    OPERATOR_INJECTION = "operator_injection"
    PROBE_ECHO = "probe_echo"
    EXTERNAL = "external"
    GENERATED = "generated"
```

Interpretation:

| Kind | Meaning |
|---|---|
| `ENDOGENOUS` | Chamber-internal patterning or internally maintained substrate state. |
| `OPERATOR_INJECTION` | Developer/operator-provided frame material used to seed or inspect behavior. |
| `PROBE_ECHO` | Material produced by chamber probes such as `SIMILARITY` or `FOCUS_CONTACT`. |
| `EXTERNAL` | Contact from outside the chamber/kernel boundary. |
| `GENERATED` | Deterministic generated scaffolding that is neither probe echo nor endogenous recurrence. |

The future implementation should treat these as semantic provenance tags, not
as truth labels. A source kind does not make a frame trustworthy, preservative,
or promotable by itself.

### Explicit deferrals

Do not include later-phase source kinds as active Phase 3.1 values:

```text
WORLDLET_RESPONSE
OUTPUT_ECHO
REPL_FEEDBACK
TEACHER_SIGNAL
```

These belong to later phases. If the catalog patch wants forward-compatible
names, they may be mentioned in comments or documentation as reserved future
concepts, but they should not appear as enum members until their phase creates
real fixtures.

## C2 - Developmental IDs Must Not Shadow TLICA ContentID

### Problem

The kickoff sketch aliases:

```python
ContentID = str
```

That risks confusion with `brain.tlica.profile.ContentID`, which already names
kernel-level profile content. Phase 3.1 needs a developmental proto-content
identifier that remains below the promotion boundary.

### Required correction

Use developmental names until promotion:

```python
DevContentID = str
FrameID = str
PatternID = str
TraceEventID = str
```

Then define `SubstrateHistory` and `ProtoContent` with `DevContentID`:

```python
@dataclass(frozen=True, slots=True)
class SubstrateHistory:
    frames: tuple[PhenomenalFrame, ...]
    proto_patterns: Mapping[PatternID, "ProtoPattern"]
    proto_contents: Mapping[DevContentID, "ProtoContent"]


@dataclass(frozen=True, slots=True)
class ProtoContent:
    content_id: DevContentID
    text: str
    pattern_id: PatternID
    salience: Fraction
    stability: Fraction
    prediction_gain: Fraction
    provenance: PromotionProvenance
```

Rule:

```text
developmental proto-content IDs are developmental IDs until promotion;
existing TLICA ContentID is used only when producing a PerceptEvent.
```

The promotion function is the boundary where a `DevContentID` is validated and
converted into the `content_id` carried by `brain.io_types.PerceptEvent`.

## C3 - Revisit prediction_gain_v1

### Problem

The kickoff proposes:

```python
prediction_gain_v1 = clamp_unit(raw_gain - baseline + Fraction(1, 2))
```

The `+ Fraction(1, 2)` offset can lift weak or non-predictive patterns toward
the proposed promotion threshold. That makes promotion too easy: a metric with
little evidence can sit near `1/2` merely because the formula is offset upward.

If `prediction_gain >= Fraction(1, 2)` is part of the promotion gate, the gain
metric must represent positive predictive structure, not a centered display
score.

### Required correction

Use a positive-delta formulation:

```python
prediction_gain_v1 = clamp_unit(raw_gain - baseline)
```

Where:

```python
recent = last_n_frames(history.frames, n=5)
expected_hits = count_predicted_signature_hits(pattern.signature, recent)
false_hits = count_predicted_signature_misses(pattern.signature, recent)
raw_gain = Fraction(expected_hits, max(1, expected_hits + false_hits))
baseline = Fraction(1, max(1, len(recent)))
prediction_gain_v1 = clamp_unit(raw_gain - baseline)
```

If the later catalog patch chooses a different normalized positive-delta
formula, it must preserve the same commitment:

```text
non-predictive or baseline-only contact stays low;
promotion requires better-than-baseline predictive structure.
```

The promotion threshold may remain `Fraction(1, 2)` as an initial deterministic
default, but it should now be understood as a real positive-gain threshold
rather than the midpoint of an offset score.

## C4 - Focus Behavior Row Status

### Problem

The kickoff proposes row `I-DEV-04`:

```text
Focus contact can stabilize or dissolve a candidate pattern deterministically.
```

but assigns it `OBSERVED`. That mixes two different claims:

- a narrow deterministic protocol claim about `FOCUS_CONTACT`
- a broader qualitative developmental claim about stabilize/dissolve dynamics

The first can be REQUIRED. The second should remain OBSERVED unless it is made
crisp enough to fail deterministically.

### Required correction

Split the focus plan:

| ID | Proposition | Fixture | Status |
|---|---|---|---|
| `I-DEV-04` | `FOCUS_CONTACT` records a `ProbeUse`, updates `ProbePolicyState` history, spends or accounts for focus budget, and does not promote content by itself. | `focus_contact_protocol.py` or a narrowed `focus_stabilizes_or_dissolves.py` | REQUIRED |
| `I-DEV-07` | Focused contact may stabilize under recurrence or remain unpromoted / dissolve without recurrence. This qualitative trend is recorded for inspection. | `focus_stabilizes_or_dissolves.py` | OBSERVED |

If the implementation keeps one fixture file, the fixture name should not
overstate the REQUIRED claim. Preferred split:

```text
focus_contact_protocol.py        # REQUIRED protocol behavior
focus_stabilizes_or_dissolves.py # OBSERVED trend behavior
```

The deterministic REQUIRED claim should be narrow:

```text
FOCUS_CONTACT updates ProbeUse history and cannot promote by itself.
```

## C5 - Trace Reserved-Key Protection Sequencing

### Problem

The kickoff correctly identifies trace reserved-key collision as a risk, but it
leaves a residual in-phase fallback.

Current tracer payloads can collide with envelope fields such as:

```text
type
timestamp_ns
tick_id
```

This is a trace-envelope boundary problem, not an Osmotic Chamber feature.
Phase 3.1 will increase trace volume and payload richness, so the boundary
should be hardened before developmental trace events are introduced.

### Required correction

Decision:

```text
trace reserved-key protection should be the next mission before Phase 3.1 implementation.
```

Recommended patch shape for that next mission:

- Add a micro-hardening row for trace reserved-key protection.
- Reject reserved payload keys rather than silently overwriting envelope fields.
- Name the invariant as an `I-TRACE-*` row.
- Keep the patch outside Phase 3.1 semantics.
- Run trace-targeted validation plus the normal catalog count gate.

Rationale:

- Reserved-key protection predates Phase 3.1.
- It protects trace envelope integrity, not developmental behavior.
- It should be fixed before source-tagged chamber traces create larger payloads.
- It keeps the later Phase 3.1 catalog patch focused on developmental rows.

If this pre-phase mission is skipped, then the first Phase 3.1 catalog patch
must add the trace row before any chamber trace fixture. The preferred path is
still pre-phase hardening.

## C6 - Data Model Validation Details

### Problem

The kickoff says constructors should fail loudly, but several exact validation
rules need to be explicit before code lands.

### Required correction

The Phase 3.1 catalog patch should lock these constructor rules.

#### Normalized Fraction fields

Every normalized score field must be a `Fraction` in `[0, 1]`:

```text
FrameSource.confidence
SubstrateDrives.salience_bias
SubstrateDrives.novelty_bias
SubstrateDrives.stability_bias
SubstrateDrives.focus_bias
ProtoPattern.salience
ProtoPattern.stability
ProtoPattern.prediction_gain
ProtoContent.salience
ProtoContent.stability
ProtoContent.prediction_gain
ProbeUse.before
ProbeUse.after
```

No silent clamping in constructors. Invalid values raise.

Metric functions may use `clamp_unit(...)` internally to define their
deterministic output, but object constructors should reject invalid supplied
state.

#### Non-empty printable IDs

These identifiers must be non-empty strings and printable:

```text
DevContentID
FrameID
PatternID
TraceEventID when present
FrameSource.label
channel group names
channel names
```

Whitespace-only IDs are invalid.

#### Source-map exact coverage

`PhenomenalFrame.sources` must exactly cover `PhenomenalFrame.channels`:

```python
set(frame.sources) == set(frame.channels)
all(
    set(frame.sources[group]) == set(frame.channels[group])
    for group in frame.channels
)
```

Missing, extra, empty, or mismatched source tags raise at construction.

Each source label must be non-empty and printable. Each source confidence must
be a normalized `Fraction`.

#### Non-empty promotion provenance

`PromotionProvenance` must be non-empty enough to justify promotion:

```text
pattern_id is non-empty and printable
support_frame_ids has length >= 2
source_kinds is non-empty
source_kinds contains only active Phase 3.1 kinds
```

`probe_uses` may be empty only if the catalog row explicitly permits promotion
without probe contact. Preferred initial rule: promotion provenance includes at
least one `ProbeUse` unless the later catalog patch gives a concrete reason not
to require it.

#### COGITO_ID rejection

`COGITO_ID` must be rejected at both boundaries:

```text
developmental ID boundary: ProtoContent.content_id != COGITO_ID
promotion boundary: produced PerceptEvent.content_id != COGITO_ID
```

The second check must remain even if the first exists. The promotion boundary is
where developmental IDs become kernel content IDs, so it must defend the kernel
sentinel independently.

## C7 - Catalog Versioning and Row Family Plan

### Problem

The kickoff leaves open whether trace reserved-key protection creates a v0.5.x
or v0.6-pre hardening step, and whether Phase 3.1 rows bump directly from v0.5
to v0.6.

### Required correction

Versioning decision:

```text
trace reserved-key protection gets its own micro-hardening mission without
changing Phase 3 semantics; Phase 3.1 Osmotic Chamber catalog patch then bumps
the catalog to v0.6.
```

Recommended naming:

- Keep the current catalog banner at v0.5 until the trace hardening mission is
  accepted.
- The trace reserved-key mission may be documented as a v0.5 hardening
  completion or v0.5.x-style micro-hardening pass, but it should not introduce
  developmental semantics.
- The first accepted Osmotic Chamber catalog patch should bump the catalog to
  v0.6.

Recommended Phase 3.1 row families:

| Family | Purpose | Default status |
|---|---|---|
| `I-FRAME-*` | `PhenomenalFrame`, `FrameSource`, exact source coverage, source confidence bounds | STRUCTURAL / REQUIRED |
| `I-DEV-*` | recurrence, salience, stability, prediction gain, focus protocol, promotion gate | REQUIRED for deterministic gates; OBSERVED for qualitative trends |
| `I-SBX-*` | substrate-boundary constraints such as operator injection is not knowledge and salience is not truth | REQUIRED / STRUCTURAL |

Trace reserved-key protection should not wait for `I-FRAME-*` or `I-DEV-*`.
It should be closed first as an `I-TRACE-*` hardening row.

The Phase 3.1 rows should carry source text like:

```text
Engineering hypothesis (Phase 3.1 Osmotic Chamber). Not a TLICA theorem.
Specific formulas and thresholds are parameterized simulation choices; the
family of constraints is the commitment, not any single instantiation.
```

## C8 - Build-Order Correction

### Problem

The kickoff's build order is mostly right, but the corrigenda should make the
guardrail explicit enough that later implementation cannot accidentally begin
with runtime behavior.

### Required correction

Use this strict order:

```text
1. trace reserved-key micro-hardening mission, before Phase 3.1 implementation
2. accepted Phase 3.1 catalog patch to v0.6
3. data model/source-tag constructors
4. SubstrateHistory
5. deterministic metric helpers
6. ProtoPattern recurrence/signature logic
7. probes and ProbePolicyState
8. ProtoContent and PromotionProvenance
9. promotion to PerceptEvent
10. deterministic fixtures
11. runner registration and generated catalog IDs
12. targeted row checks
13. full validation
```

Hard ordering constraints:

```text
no code before accepted catalog patch
no runtime behavior before data model/source-tag constructors
no promotion before source-tag and metric fixtures are green
no direct mutation of BrainState, MSI, PtCns, mode state, trace state, or content registry
no bypassing PerceptEvent and tick()
```

Promotion fixtures must feed one `PerceptEvent` per tick, preserving the
existing v1 single-event tick semantics.

## Revised Initial Row Sketch

The catalog patch should refine the kickoff's first row set approximately as
follows. Final IDs may change during the catalog patch, but the status
discipline should not.

| ID | Proposition | Owning module | Fixture | Status |
|---|---|---|---|---|
| `I-FRAME-01` | Every frame channel has exactly one source tag. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL |
| `I-FRAME-02` | Source confidence is a `Fraction` in `[0, 1]`. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL |
| `I-FRAME-03` | Missing, extra, or mismatched source tags raise at construction. | `brain/development/stream.py` | `source_tag_audit.py` | REQUIRED |
| `I-FRAME-04` | Active source kinds distinguish endogenous, operator injection, probe echo, external contact, and generated scaffolding. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL |
| `I-DEV-01` | A recurring signature creates or updates a `ProtoPattern`. | `brain/development/proto_pattern.py` | `recurrence_detection.py` | REQUIRED |
| `I-DEV-02` | Unstable one-off noise does not become stable proto-content. | `brain/development/proto_content.py` | `unstable_noise_rejection.py` | REQUIRED |
| `I-DEV-03` | Salience alone does not promote. | `brain/development/promotion.py` | `salience_is_not_truth.py` | REQUIRED |
| `I-DEV-04` | `FOCUS_CONTACT` updates `ProbeUse`/policy history and does not promote by itself. | `brain/development/probes.py` | `focus_contact_protocol.py` | REQUIRED |
| `I-DEV-05` | Proto-content promotion creates a valid `PerceptEvent` and enters through `tick()`. | `brain/development/promotion.py` | `proto_content_promotion.py` | REQUIRED |
| `I-DEV-06` | Developmental content cannot produce `COGITO_ID`. | `brain/development/promotion.py` | `proto_content_promotion.py` | REQUIRED |
| `I-DEV-07` | Focused contact can stabilize under recurrence or remain unpromoted / dissolve without recurrence. | `brain/development/probes.py` | `focus_stabilizes_or_dissolves.py` | OBSERVED |
| `I-SBX-01` | Probe output is not knowledge by itself. | `brain/development/probes.py` | `salience_is_not_truth.py` | STRUCTURAL |
| `I-SBX-02` | Salience drive is not truth and cannot bypass stability or prediction gain. | `brain/development/promotion.py` | `salience_is_not_truth.py` | REQUIRED |

## Revised Promotion Rule

The kickoff's promotion gate remains directionally correct, with these
corrigenda adjustments:

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

Additional requirements:

- `proto.content_id` is a `DevContentID` until promotion.
- The produced `PerceptEvent.content_id` is rechecked against `COGITO_ID`.
- Promotion provenance must be non-empty and source-tagged.
- Salience cannot compensate for missing stability or missing prediction gain.
- Operator injection and probe echo may support inspection, but neither is
  knowledge or PRESERVE by itself.

## Revised Validation Expectations

For this corrigenda artifact only:

```bash
git diff --name-only
python -m tools.catalog counts
```

For the next trace reserved-key micro-hardening mission:

```bash
python -m tools.catalog counts
python -m brain.invariants run --id I-TRACE
bash tools/check_all.sh
```

For the future Phase 3.1 implementation:

```bash
python -m tools.catalog counts
python -m brain.invariants run --id I-FRAME
python -m brain.invariants run --id I-DEV
python -m brain.invariants run --id I-SBX
bash tools/check_all.sh
```

Exact targeted command support may need runner-prefix handling if the runner
currently accepts only exact row IDs. The catalog patch should keep validation
commands aligned with real tooling.

## Stop Condition

This corrigenda is complete when it has been reviewed and accepted as the input
to the next mission:

```text
trace reserved-key micro-hardening before Phase 3.1 implementation
```

After that hardening mission, the Phase 3.1 catalog patch may begin. Runtime
Osmotic Chamber implementation still requires a separate explicit instruction.
