# Phase 3.1 Osmotic Chamber Catalog Patch Plan

## 1. Purpose

This document designs the future v0.6 Phase 3.1 catalog patch for the
deterministic Osmotic Chamber substrate layer.

It is a planning artifact only. It does not edit `INVARIANT_CATALOG.md`, does
not implement Phase 3 runtime code, and does not create `brain/development/`.

The planned patch is scoped to the substrate layer needed to make the Phase 3
bridge principle operational:

```text
PRESERVE should be earned, not labeled.
```

## 2. Baseline

Current verified baseline:

```text
catalog v0.5
84 REQUIRED
16 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

`I-TRACE-03` is already present as trace reserved-key hardening. It rejects
trace payload keys that would collide with the event envelope fields `type`,
`timestamp_ns`, and `tick_id`.

Some earlier Phase 3 planning documents mention 15 STRUCTURAL rows because
they predate the completed trace reserved-key micro-hardening. The current
catalog, README, and `tools.catalog` gate agree on 16 STRUCTURAL rows.

## 3. Versioning Decision

Recommendation:

```text
The accepted Phase 3.1 Osmotic Chamber catalog patch should bump the catalog to v0.6.
```

Reason: this is the first developmental-layer catalog expansion. It should not
be folded into v0.5 trace hardening, which is now complete and belongs to the
trace-envelope boundary rather than the Osmotic Chamber semantics.

The future accepted patch should update the catalog banner/history from v0.5 to
v0.6 and describe v0.6 as the Phase 3.1 deterministic Osmotic Chamber catalog
expansion.

## 4. Source-Kind Policy

All Phase 3.1 developmental rows should use source wording equivalent to:

```text
Engineering hypothesis (Phase 3.1 Osmotic Chamber). Not a TLICA theorem.
Specific formulas and thresholds are parameterized simulation choices; the
family of constraints is the commitment, not any single instantiation.
```

Rows that are pure kernel-boundary or trace-envelope rules may use
plan-convention wording instead. This planned row set does not add new trace
rows because `I-TRACE-03` is already in the v0.5 baseline.

The planned rows are catalog commitments over deterministic construction,
boundary discipline, recurrence behavior, salience/stability/prediction-gain
gates, and promotion routing. They are not Lean theorem claims.

## 5. Proposed Row Families

| Family | Purpose | Scope discipline |
|---|---|---|
| `I-FRAME-*` | `PhenomenalFrame` / `FrameSource` structure and exact source coverage. | Phase 3.1 source tags only. |
| `I-DEV-*` | Recurrence, salience, stability, prediction gain, probes, and promotion. | Deterministic substrate behavior only. |
| `I-SBX-*` | Substrate boundary constraints such as salience-is-not-truth and operator-injection-is-not-knowledge. | Boundary-protection rows only. |

Do not add output-ladder, worldlet, REPL, expression, or social/language rows
in this patch.

Do not add later-phase source kinds as active enum values:

```text
WORLDLET_RESPONSE
OUTPUT_ECHO
REPL_FEEDBACK
TEACHER_SIGNAL
```

## 6. Proposed Rows Table

The proposed patch adds exactly 13 rows.

Source abbreviation used below:

```text
Phase 3.1 engineering hypothesis
```

means the full source-kind wording in section 4.

| ID | Source | Proposition | Owning module | Fixture | Status | Rationale |
|---|---|---|---|---|---|---|
| `I-FRAME-01` | Phase 3.1 engineering hypothesis | Every frame channel has exactly one source tag. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL | Source coverage is a construction invariant for usable substrate history. |
| `I-FRAME-02` | Phase 3.1 engineering hypothesis | Source confidence is a `Fraction` in `[0, 1]`. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL | Numeric source metadata must follow the existing exact-`Fraction` discipline. |
| `I-FRAME-03` | Phase 3.1 engineering hypothesis | Missing, extra, empty, or mismatched source tags raise at construction. | `brain/development/stream.py` | `source_tag_audit.py` | REQUIRED | Source confusion would make later stability and promotion provenance unsound. |
| `I-FRAME-04` | Phase 3.1 engineering hypothesis | Active source kinds distinguish `ENDOGENOUS`, `OPERATOR_INJECTION`, `PROBE_ECHO`, `EXTERNAL`, and `GENERATED`. | `brain/development/stream.py` | `source_tag_audit.py` | STRUCTURAL | Phase 3.1 must not conflate operator input, probe echo, external contact, and endogenous patterning. |
| `I-DEV-01` | Phase 3.1 engineering hypothesis | A recurring signature creates or updates a `ProtoPattern`. | `brain/development/proto_pattern.py` | `recurrence_detection.py` | REQUIRED | Recurrence is the first deterministic substrate condition for earned content. |
| `I-DEV-02` | Phase 3.1 engineering hypothesis | Unstable one-off noise does not become stable proto-content. | `brain/development/proto_content.py` | `unstable_noise_rejection.py` | REQUIRED | One-off perturbation must not be mistaken for stable developmental content. |
| `I-DEV-03` | Phase 3.1 engineering hypothesis | Salience alone does not promote. | `brain/development/promotion.py` | `salience_is_not_truth.py` | REQUIRED | High salience is not truth, knowledge, stability, or preservation. |
| `I-DEV-04` | Phase 3.1 engineering hypothesis | `FOCUS_CONTACT` updates `ProbeUse` / policy history, accounts for focus budget, and does not promote by itself. | `brain/development/probes.py` | `focus_contact_protocol.py` | REQUIRED | The probe protocol can be deterministic without overclaiming qualitative stabilization. |
| `I-DEV-05` | Phase 3.1 engineering hypothesis | Proto-content promotion creates a valid `PerceptEvent` and enters TLICA runtime state only through `tick()`. | `brain/development/promotion.py` | `proto_content_promotion.py` | REQUIRED | Promotion must respect the existing kernel boundary and single-event tick semantics. |
| `I-DEV-06` | Phase 3.1 engineering hypothesis | Developmental content cannot produce `COGITO_ID`. | `brain/development/promotion.py` | `proto_content_promotion.py` | REQUIRED | The developmental layer must independently defend the cogito sentinel before and during promotion. |
| `I-DEV-07` | Phase 3.1 engineering hypothesis | Focused contact can stabilize under recurrence or remain unpromoted / dissolve without recurrence. | `brain/development/probes.py` | `focus_stabilizes_or_dissolves.py` | OBSERVED | This is a qualitative developmental trend useful to inspect, not a correctness gate. |
| `I-SBX-01` | Phase 3.1 engineering hypothesis | Probe output is not knowledge by itself. | `brain/development/probes.py` | `salience_is_not_truth.py` | STRUCTURAL | Probe echo may aid inspection but must not be treated as truth or preservation. |
| `I-SBX-02` | Phase 3.1 engineering hypothesis | Salience drive is not truth and cannot bypass stability or prediction gain. | `brain/development/promotion.py` | `salience_is_not_truth.py` | REQUIRED | Promotion must require multiple independent deterministic gates. |

## 7. Count Impact

Starting from v0.5:

```text
84 REQUIRED
16 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

Proposed v0.6 additions:

```text
REQUIRED +8
STRUCTURAL +4
OBSERVED +1
```

Arithmetic by row:

| Status | Added rows |
|---|---|
| REQUIRED | `I-FRAME-03`, `I-DEV-01`, `I-DEV-02`, `I-DEV-03`, `I-DEV-04`, `I-DEV-05`, `I-DEV-06`, `I-SBX-02` |
| STRUCTURAL | `I-FRAME-01`, `I-FRAME-02`, `I-FRAME-04`, `I-SBX-01` |
| OBSERVED | `I-DEV-07` |

Projected v0.6 counts:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

Projected total tabular entries:

```text
129
```

## 8. Fixture Roster

Future fixture files:

| Fixture | Proposed rows owned |
|---|---|
| `brain/development/fixtures/source_tag_audit.py` | `I-FRAME-01`, `I-FRAME-02`, `I-FRAME-03`, `I-FRAME-04` |
| `brain/development/fixtures/recurrence_detection.py` | `I-DEV-01` |
| `brain/development/fixtures/unstable_noise_rejection.py` | `I-DEV-02` |
| `brain/development/fixtures/salience_is_not_truth.py` | `I-DEV-03`, `I-SBX-01`, `I-SBX-02` |
| `brain/development/fixtures/focus_contact_protocol.py` | `I-DEV-04` |
| `brain/development/fixtures/focus_stabilizes_or_dissolves.py` | `I-DEV-07` |
| `brain/development/fixtures/proto_content_promotion.py` | `I-DEV-05`, `I-DEV-06` |

All fixtures should be deterministic, use `Fraction` for normalized numeric
values, and avoid real LLM calls, stochastic sampling, or real traced scenarios
for REQUIRED / STRUCTURAL behavior.

## 9. Owning Module Map

Future owning modules:

```text
brain/development/stream.py
brain/development/drives.py
brain/development/history.py
brain/development/proto_pattern.py
brain/development/proto_content.py
brain/development/salience.py
brain/development/stability.py
brain/development/prediction_gain.py
brain/development/probes.py
brain/development/promotion.py
```

Do not create these files as part of this planning mission.

Suggested responsibility split:

| Module | Responsibility |
|---|---|
| `brain/development/stream.py` | `PhenomenalFrame`, `FrameSource`, `FrameSourceKind`, exact source coverage, source confidence validation. |
| `brain/development/drives.py` | `SubstrateDrives` and normalized drive validation. |
| `brain/development/history.py` | `SubstrateHistory`, frame storage, proto-pattern/proto-content maps, provenance IDs. |
| `brain/development/proto_pattern.py` | `ProtoPattern`, signature bucketing, recurrence update logic. |
| `brain/development/proto_content.py` | `DevContentID`, `ProtoContent`, `PromotionProvenance`. |
| `brain/development/salience.py` | `salience_v1` deterministic metric helper. |
| `brain/development/stability.py` | `stability_v1` deterministic metric helper. |
| `brain/development/prediction_gain.py` | Positive-delta `prediction_gain_v1` deterministic metric helper. |
| `brain/development/probes.py` | `SIMILARITY`, `FOCUS_CONTACT`, `ProbeUse`, `ProbePolicyState`. |
| `brain/development/promotion.py` | `ProtoContent -> PerceptEvent` gate and `tick()` boundary routing helpers. |

## 10. Catalog Patch Mechanics

The future implementation mission must update:

```text
INVARIANT_CATALOG.md banner/history
INVARIANT_CATALOG.md row table(s)
summary counts
tools/catalog.py EXPECTED_COUNTS
brain/_catalog_ids.py via python3 -m tools.catalog generate-ids
brain/invariants.py FIXTURE_MODULES once fixtures exist
```

Because `I-CAT-01` enforces catalog-to-registry coverage, do not apply the
catalog rows before the corresponding fixture registration plan is ready to
land in the same implementation pass.

The v0.6 catalog patch should add a new Phase 3.1 table rather than mixing the
Osmotic Chamber rows into Lean-bound TLICA module sections. The table should
use the seven-column cross-cutting shape already supported by `tools.catalog`:

```text
ID | Source | Proposition | Python assertion | Owning module | Fixture | Status
```

## 11. Implementation Order After Catalog Acceptance

The future implementation mission should use this strict order:

1. Accepted catalog patch to v0.6.
2. Stream/source tags.
3. Drives.
4. History.
5. Metrics.
6. Proto-pattern.
7. Probes.
8. Proto-content.
9. Promotion.
10. Fixtures.
11. Runner registration / generated IDs.
12. Targeted checks.
13. Full gate.

In concrete file terms, that means the accepted implementation pass should
patch `INVARIANT_CATALOG.md`, update `tools/catalog.py EXPECTED_COUNTS`, create
the `brain/development/` package, register fixture modules in
`brain/invariants.py`, regenerate `brain/_catalog_ids.py`, run targeted row
checks, and finish with `bash tools/check_all.sh`.

Hard constraints:

```text
no runtime behavior before the accepted catalog patch
no direct mutation of BrainState, MSI, PtCns, mode state, trace state, or content registry
no bypassing PerceptEvent and tick()
no promotion of COGITO_ID
no salience-only promotion
no later Phase 3.2+ surfaces in the Phase 3.1 row set
```

Promotion fixtures must feed one `PerceptEvent` per tick, preserving the
existing v1 single-event tick semantics.

## 12. Non-Goals

This mission and the future v0.6 row patch explicitly exclude:

```text
no runtime implementation in this mission
no direct catalog edits in this mission
no brain/development files in this mission
no Phase 3.2+ rows
no output ladder/worldlet/REPL/expression/social-language rows
no Mode B rows
no real LLM scenario run
```

For the later implementation pass, the catalog patch should also keep these
outside Phase 3.1:

```text
no cause/effect probes
no conditional probes
no object-persistence probes
no language probes
no stochastic REQUIRED behavior
no prompt tuning to force the four-tick scenario to pass
no seeded-MSI scenario shortcut as the immediate Phase 3.1 move
```

## 13. Open Decisions For Review

Before applying the v0.6 catalog patch, reviewers should decide:

| Decision | Default recommendation |
|---|---|
| Whether projected v0.6 counts are acceptable. | Accept `92 REQUIRED`, `20 STRUCTURAL`, `3 NOT-EXERCISED`, `12 DEFERRED`, `2 OBSERVED` if this exact 13-row set is accepted. |
| Whether `I-DEV-07` should remain OBSERVED. | Keep OBSERVED unless the stabilize/dissolve claim becomes a crisp deterministic gate. |
| Whether `I-SBX-*` belongs as a separate family or folded into `I-DEV-*`. | Keep separate; boundary-protection rows are easier to audit when not mixed with developmental dynamics. |
| Whether promotion requires at least one `ProbeUse` in initial v0.6. | Prefer requiring at least one `ProbeUse` unless the accepted patch gives a concrete reason to allow probe-free promotion. |
| Whether source kinds should be exactly five active values or include reserved future enum members. | Use exactly five active values: `ENDOGENOUS`, `OPERATOR_INJECTION`, `PROBE_ECHO`, `EXTERNAL`, `GENERATED`. Mention later-phase concepts only in docs. |

## 14. Validation Expectations

For this planning artifact:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

For the future v0.6 implementation patch:

```bash
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-FRAME-01
python3 -m brain.invariants run --id I-FRAME-02
python3 -m brain.invariants run --id I-FRAME-03
python3 -m brain.invariants run --id I-FRAME-04
python3 -m brain.invariants run --id I-DEV-01
python3 -m brain.invariants run --id I-DEV-02
python3 -m brain.invariants run --id I-DEV-03
python3 -m brain.invariants run --id I-DEV-04
python3 -m brain.invariants run --id I-DEV-05
python3 -m brain.invariants run --id I-DEV-06
python3 -m brain.invariants run --id I-SBX-01
python3 -m brain.invariants run --id I-SBX-02
bash tools/check_all.sh
```

`I-DEV-07` is OBSERVED. It should be reported for inspection but should not
gate the kernel unless a later accepted catalog patch changes its status.

## 15. Stop Condition

This planning mission is complete when
`PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md` exists and documents the exact
future v0.6 catalog patch without changing catalog rows, runtime code, or
future `brain/development/` files.

Do not apply this catalog patch until this plan is reviewed and accepted.
