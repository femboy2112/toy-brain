# Phase 3.1 Osmotic Chamber Post-Completion Audit

Date: 2026-05-15

## 1. Executive Verdict

Verdict: PASS WITH PATCHES.

Definition used in this audit:

- PASS means the catalog, runner, and scope checks are green with no material pre-Phase-3.2 patch recommended.
- PASS WITH PATCHES means the completed Phase 3.1 gate is green, but one or more focused patches should land before Phase 3.2 planning or implementation.
- BLOCKED means a required gate fails, the catalog/runner is incoherent, or Phase 3.1 appears to have crossed a hard boundary.

Phase 3.1 is not blocked. The v0.6 catalog counts agree, all required validation commands pass, I-FRAME / I-DEV / I-SBX row families are registered and green, OBSERVED rows are non-gating, and I found no runtime implementation of Phase 3.2+ surfaces.

The reason this is not a clean PASS is the promotion threshold/provenance boundary. The implemented promotion gate rejects COGITO_ID and rejects zero stability or zero prediction gain, but it accepts a hand-constructed `ProtoContent` with low positive `stability=1/10`, low positive `prediction_gain=1/10`, and `salience=0` as long as probe trace provenance is present. That is green against the current catalog rows, but looser than the stronger promotion rule captured in the Phase 3.1 corrigenda.

## 2. Current Counts and Gate Status

`python3 -m tools.catalog counts` reports:

```text
Category            Banner    Actual  Expected
REQUIRED                92        92        92  ok
STRUCTURAL              20        20        20  ok
NOT-EXERCISED            3         3         3  ok
DEFERRED                12        12        12  ok
OBSERVED                 2         2         2  ok
```

The v0.6 target is coherent:

- REQUIRED: 92
- STRUCTURAL: 20
- NOT-EXERCISED: 3
- DEFERRED: 12
- OBSERVED: 2

## 3. Full Validation Status

Required validation commands were run with `python3`:

```text
git status --short
git log --oneline -10
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Results:

- `git status --short`: clean before writing this audit.
- `git log --oneline -10`: current head was `801f1b1 docs(codex): set current mission to phase 3.1 audit`.
- `python3 -m tools.catalog counts`: pass, all five categories agree.
- `python3 -m tools.citations verify`: pass, 100 citations verified against `lean_reference/`.
- `python3 -m tools.import_audit`: pass, `I-PCE-05: agency.py is clean of pce imports.`
- `python3 -m brain.invariants run`: pass, 114 rows checked; 92 REQUIRED green, 20 STRUCTURAL green, 2 OBSERVED pass / 0 fail, 0 gate failures.
- `bash tools/check_all.sh`: pass, including generated ID freshness, catalog counts, citation verification, import audit, and invariant runner.

No real LLM scenario command was run.

## 4. Row-Family Audit

### I-FRAME-*

Expected rows:

- `I-FRAME-01` STRUCTURAL
- `I-FRAME-02` STRUCTURAL
- `I-FRAME-03` REQUIRED
- `I-FRAME-04` STRUCTURAL

Owning module: `brain/development/stream.py`

Fixture: `brain/development/fixtures/source_tag_audit.py`

Targeted check:

```text
python3 -m brain.invariants run --id I-FRAME
4 rows checked; REQUIRED green: 1; STRUCTURAL green: 3; gate failures: 0
```

Audit result: pass. `FrameSourceKind` exposes exactly `ENDOGENOUS`, `OPERATOR_INJECTION`, `PROBE_ECHO`, `EXTERNAL`, and `GENERATED`; source confidence is exact `Fraction` in `[0, 1]`; missing, extra, empty, and mismatched source coverage are rejected by construction.

### I-DEV-*

Expected rows:

- `I-DEV-01` REQUIRED
- `I-DEV-02` REQUIRED
- `I-DEV-03` REQUIRED
- `I-DEV-04` REQUIRED
- `I-DEV-05` REQUIRED
- `I-DEV-06` REQUIRED
- `I-DEV-07` OBSERVED

Owning modules:

- `brain/development/proto_pattern.py`
- `brain/development/proto_content.py`
- `brain/development/promotion.py`
- `brain/development/probes.py`

Fixtures:

- `recurrence_detection.py`
- `unstable_noise_rejection.py`
- `salience_is_not_truth.py`
- `focus_contact_protocol.py`
- `proto_content_promotion.py`
- `focus_stabilizes_or_dissolves.py`

Targeted check:

```text
python3 -m brain.invariants run --id I-DEV
7 rows checked; REQUIRED green: 6; OBSERVED: 1 pass / 0 fail; gate failures: 0
```

Audit result: pass with one recommended patch. Recurrence, one-off noise rejection, salience-alone rejection, focus-contact bookkeeping, PerceptEvent promotion, tick routing, and COGITO_ID rejection are all exercised. `I-DEV-07` is correctly OBSERVED. The promotion gate is functionally safe against zero prediction gain, but its threshold/provenance semantics are weaker than the corrigenda-level promotion rule.

### I-SBX-*

Expected rows:

- `I-SBX-01` STRUCTURAL
- `I-SBX-02` REQUIRED

Owning modules:

- `brain/development/probes.py`
- `brain/development/promotion.py`

Fixture: `brain/development/fixtures/salience_is_not_truth.py`

Targeted check:

```text
python3 -m brain.invariants run --id I-SBX
2 rows checked; REQUIRED green: 1; STRUCTURAL green: 1; gate failures: 0
```

Audit result: pass. Probe echo is not treated as knowledge or promotion by itself, and salience cannot bypass absent stability or absent prediction gain.

## 5. Scope-Creep Audit

Searches for Phase 3.2+ surfaces found references only in planning, guardrail, README, catalog, and Lean-reference prose. I found no runtime package or implementation for:

- output ladder
- Minimal Worldlet
- Proto-BASIC REPL
- expression layer
- social/language harness
- Mode B developmental layer
- real LLM training behavior

The active runtime additions are limited to `brain/development/` substrate modules and deterministic fixtures. No Phase 3.2+ source kinds such as `WORLDLET_RESPONSE`, `OUTPUT_ECHO`, `REPL_FEEDBACK`, or `TEACHER_SIGNAL` appear as active enum members.

## 6. Kernel-Boundary Audit

Promotion produces a `PerceptEvent` through `brain/development/promotion.py::promote_proto_content`.

The fixture `proto_content_promotion.py` checks that promotion construction does not mutate the existing runtime state. It snapshots `profile`, `msi`, `ptcns`, and `registry`, confirms the promoted event is absent from the profile before tick, then feeds exactly one event through `tick(state, [event], MockClient(["PRESERVE"]))`.

`tick()` remains the runtime state transition path. The developmental package imports `PerceptEvent` and `COGITO_ID` only at the promotion boundary, and the runtime mutation happens inside `brain/tick.py`. The single-event guard is still active through `I-RT-11`, and the full runner shows `I-RT-11` green.

Audit result: pass.

## 7. COGITO_ID Audit

COGITO_ID is protected at two boundaries:

- `PerceptEvent.__post_init__` rejects `content_id == COGITO_ID` through `I-RT-01`.
- `promote_proto_content` rejects `content.content_id == COGITO_ID` with an `I-DEV-06` error before emitting an event.

The fixture `proto_content_promotion.py` constructs a stable content candidate, replaces its ID with `COGITO_ID`, and verifies promotion raises `ValueError` naming `I-DEV-06`.

Audit result: pass.

## 8. OBSERVED-Row Audit

OBSERVED rows are reported but do not gate success.

The full runner reported:

```text
OBSERVED: 2 pass / 0 fail  -  gate failures: 0
```

`I-DEV-07` appears as `OBS-PASS` in `brain.development.fixtures.focus_stabilizes_or_dissolves`. Runner logic excludes OBSERVED rows from `all_passed`, so an OBSERVED row is visible in summaries without becoming a correctness gate.

Audit result: pass.

## 9. Source-Tag / Provenance Audit

`FrameSourceKind` has exactly the five active Phase 3.1 values:

- `ENDOGENOUS`
- `OPERATOR_INJECTION`
- `PROBE_ECHO`
- `EXTERNAL`
- `GENERATED`

`PhenomenalFrame` construction requires exact key coverage between channels and sources, rejects empty maps, rejects empty channel/source keys, and rejects mismatched `FrameSource.channel` values. `ProbeUse` requires its result frame to carry a `PROBE_ECHO` source for the target channel.

Source confidence is enforced as `Fraction` in `[0, 1]`; construction does not silently clamp supplied source confidence.

Audit result: pass.

## 10. Metric / Promotion Audit

Metric helpers:

- `salience_v1` uses exact `Fraction` channel energy, source diversity over the five active source kinds, and drive bias.
- `stability_v1` uses recurrence over the last five frames plus source-kind consistency.
- `prediction_gain_v1` uses the corrected positive-delta formulation: `clamp_unit(raw_gain - baseline)`, with no `+ 1/2` offset.

The good news: zero prediction gain does not promote. A direct probe with `prediction_gain=0` raised:

```text
ValueError I-DEV-05 violated: promotion requires stability and positive prediction gain
```

The risk: low positive prediction gain and low positive stability do promote if a caller hand-constructs `ProtoContent` with trace provenance. I verified:

```text
content.salience = 0
content.stability = 1/10
content.prediction_gain = 1/10
content.provenance.trace_event_ids = ("probe:low",)
can_promote_proto_content(content) == True
promote_proto_content(content).initial_rho == 1/10
```

This follows from `ProtoContent.eligible_for_promotion`, which requires only `stability > 0` and `prediction_gain > 0`, and from `promote_proto_content`, which checks that predicate plus non-empty trace provenance. It does not enforce the corrigenda rule of `salience >= 1/2`, `stability >= 1/2`, `prediction_gain >= 1/2`, and explicit support-frame provenance.

This is not a current catalog gate failure: the v0.6 catalog rows commit to rejecting salience-only promotion and missing stability/prediction-gain support, not necessarily to the stronger `1/2` thresholds. But before Phase 3.2, the project should either patch the gate to the stronger rule or explicitly update the catalog/docs to bless the current lower-threshold interpretation.

Audit result: pass with P1 patch recommended.

## 11. Risks and Recommended Patches

P0 blocker:

- None found.

P1 before Phase 3.2:

- Align promotion threshold/provenance semantics. Either enforce the corrigenda-level promotion rule in `promote_proto_content` / `can_promote_proto_content` and add targeted fixture coverage, or explicitly patch the catalog/docs to state that Phase 3.1 promotion requires only positive stability, positive prediction gain, and probe trace provenance. Current behavior is green but underspecified against the stronger planning rule.

P2 cleanup:

- Remove or update the stale "pending row registrations" comment block in `brain/invariants.py`. `_PHASE3_1_PENDING_ROWS` is now empty and harmless, but the surrounding comment still describes a past incremental state.

## 12. Next Recommended Mission

Because the verdict is PASS WITH PATCHES, the next mission should be a focused patch mission:

```text
Tighten or explicitly re-specify Phase 3.1 proto-content promotion thresholds and provenance before Phase 3.2 output ladder synthesis.
```

Do not proceed into Phase 3.2 until that decision is made and validated.
