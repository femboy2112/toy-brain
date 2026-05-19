# PREDICATE_TABLE_<AXIS_NAME>_TEMPLATE.md

<!--
USAGE: this template is for authoring the 16 predicates (8 cert + 8 fals)
for a single developmental axis. Use this when fanning out predicate
authoring to Codex per OFFLOAD_TO_CODEX_PATTERNS.md.

Copy this file, replace every <<<...>>> placeholder, and run:
  python3 -m tools.verify_predicate_monotonicity --axis <AXIS_NAME>

If the check passes, paste the predicates into predicate_table.py
under the appropriate section.
-->

## Axis: <<<AXIS_NAME>>>

## Axis abbreviation (for predicate naming)

<<<3-5 letter abbreviation. Examples:
  PROTO_SPEECH_BABBLE        → PSB
  PROTO_SPEECH_STABLE_SINGLE → PSS
  PROTO_SPEECH_COMBINATION   → PSC
  PROTO_SPEECH_TRANSFER      → PST
  PATTERN_TRANSFER           → PT
  OSMOTIC_IMPRINTING         → OI
  ACTIVE_PROBE               → AP
  CURRICULUM_RETENTION       → CR
  WORLDLET_FEEDBACK          → WF
  REFUSAL_SAFETY             → RS
>>>

Abbreviation: `<<<AXIS_ABBREV>>>`

## Semantic source

The semantic gloss for this axis is in
`docs/campaigns/phase3_34/PHASE3_34_AXIS_AND_BAND_SPEC.md` under the
`### <<<AXIS_NAME>>>` heading.

Copy that section here for reference while authoring:

```text
B00 <<<gloss from spec>>>
B01 <<<gloss from spec>>>
B02 <<<gloss from spec>>>
B03 <<<gloss from spec>>>
B04 <<<gloss from spec>>>
B05 <<<gloss from spec>>>
B06 <<<gloss from spec>>>
B07 <<<gloss from spec>>>
```

## Probe report fields this axis reads

<<<List the specific ProbeReport fields the predicates will inspect.
Examples for PROTO_SPEECH_COMBINATION:

  proto_speech_report.two_token_attempt_count           int
  proto_speech_report.stable_combination_count          int (graceful)
  proto_speech_report.stable_combination_count_strict   int (post-3.33)
  proto_speech_report.three_token_attempt_count         int
  proto_speech_report.post_suppression_resurgence_count int
  proto_speech_report.different_shape_transfer_success_count int
  proto_speech_report.transfer_success_count_strict     int

Confirm each field actually exists on the report dataclass before
authoring; if a field is missing, the predicate cannot be authored
until a follow-up campaign adds it.>>>

```text
<<<Field 1>>>: <description>
<<<Field 2>>>: <description>
...
```

## Unreachable bands

<<<List which bands are STRUCTURALLY UNREACHABLE on this axis given
the current probe set. For these bands:
  cert returns False
  fals returns True
This caps the axis at the highest reachable band.

Example: REFUSAL_SAFETY.B05_COMBINES has no obvious meaning; bands
B05–B07 may all be unreachable.

If no bands are unreachable, write "none".>>>

Unreachable bands on this axis: <<<list of bands, or "none">>>

## Predicate authoring

Paste the predicates below as you author them. Follow the
PROTO_SPEECH_COMBINATION reference structure exactly from
`PHASE3_34_PREDICATE_TEMPLATE.md`.

```python
# ---- Predicates: <<<AXIS_NAME>>> axis -----------------------------

def cert_<<<AXIS_ABBREV>>>_B00(reports):
    """B00_REFLEXIVE: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B00(reports):
    """<<<one-line gloss>>>."""
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B01(reports):
    """B01_EMERGENT: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B01(reports):
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B02(reports):
    """B02_REPEATABLE: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B02(reports):
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B03(reports):
    """B03_STABLE_IN_CONTEXT: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B03(reports):
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B04(reports):
    """B04_TRANSFERS: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B04(reports):
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B05(reports):
    """B05_COMBINES: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B05(reports):
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B06(reports):
    """B06_REPAIRS: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B06(reports):
    <<<body>>>

def cert_<<<AXIS_ABBREV>>>_B07(reports):
    """B07_GENERALIZES: <<<one-line gloss>>>."""
    <<<body>>>

def fals_<<<AXIS_ABBREV>>>_B07(reports):
    <<<body>>>


_<<<AXIS_ABBREV>>>_PREDICATES: Mapping[
    DevelopmentalBand,
    tuple[CertificationPredicate, FalsificationPredicate],
] = {
    DevelopmentalBand.B00_REFLEXIVE:
        (cert_<<<AXIS_ABBREV>>>_B00, fals_<<<AXIS_ABBREV>>>_B00),
    DevelopmentalBand.B01_EMERGENT:
        (cert_<<<AXIS_ABBREV>>>_B01, fals_<<<AXIS_ABBREV>>>_B01),
    DevelopmentalBand.B02_REPEATABLE:
        (cert_<<<AXIS_ABBREV>>>_B02, fals_<<<AXIS_ABBREV>>>_B02),
    DevelopmentalBand.B03_STABLE_IN_CONTEXT:
        (cert_<<<AXIS_ABBREV>>>_B03, fals_<<<AXIS_ABBREV>>>_B03),
    DevelopmentalBand.B04_TRANSFERS:
        (cert_<<<AXIS_ABBREV>>>_B04, fals_<<<AXIS_ABBREV>>>_B04),
    DevelopmentalBand.B05_COMBINES:
        (cert_<<<AXIS_ABBREV>>>_B05, fals_<<<AXIS_ABBREV>>>_B05),
    DevelopmentalBand.B06_REPAIRS:
        (cert_<<<AXIS_ABBREV>>>_B06, fals_<<<AXIS_ABBREV>>>_B06),
    DevelopmentalBand.B07_GENERALIZES:
        (cert_<<<AXIS_ABBREV>>>_B07, fals_<<<AXIS_ABBREV>>>_B07),
}


# Merge into PREDICATE_TABLE:
PREDICATE_TABLE.update({
    (DevelopmentalAxis.<<<AXIS_NAME>>>, band): preds
    for band, preds in _<<<AXIS_ABBREV>>>_PREDICATES.items()
})
```

## Monotonicity self-check (REQUIRED before submission)

Walk through these synthetic fixtures and trace the cert/fals
values for each band. Confirm:

1. All-zeros fixture (every probe report's relevant fields are 0):
   - `cert_<<<AXIS_ABBREV>>>_B00` should return True (B00 always certifies).
   - `cert_<<<AXIS_ABBREV>>>_B01..B07` should return False.
   - `fals_<<<AXIS_ABBREV>>>_B00` should return False.
   - `fals_<<<AXIS_ABBREV>>>_B01..B07` should return True.

2. Strong-on-this-axis fixture (all relevant fields are above their
   highest thresholds, other axes' fields are 0):
   - `cert_<<<AXIS_ABBREV>>>_B00..B<<<HIGHEST_REACHABLE>>>` should return True.
   - `cert_<<<AXIS_ABBREV>>>_B<<<HIGHEST_REACHABLE+1>>>..B07` should return False
     (because of unreachable bands or because evidence isn't there).

3. Strong-on-all-axes fixture:
   - This axis's cert should match case 2 (axes are independent).

Trace your predicates against each fixture, write the resulting
[B00, B01, ..., B07] cert vector and fals vector, and confirm
monotonicity:

- cert vector: at most one True→False transition, no False→True.
- fals vector: at most one False→True transition, no True→False.

If your traces fail monotonicity, re-author before submitting.

## Submission

After authoring + self-check:

```bash
# Merge into predicate_table.py.
# Then:
python3 -m tools.verify_predicate_monotonicity --axis <<<AXIS_NAME>>> -v
```

If the check passes on all fixtures, the axis is complete.
If the check fails, the error message identifies the violation;
fix the offending predicate and re-run.

## Cross-references

- `docs/campaigns/phase3_34/PHASE3_34_PREDICATE_TEMPLATE.md` — the
  full template with the PROTO_SPEECH_COMBINATION reference axis.
- `docs/campaigns/phase3_34/PHASE3_34_AXIS_AND_BAND_SPEC.md` — the
  semantic source for every cell.
- `ADR-002-bands-generic-not-per-axis.md` — why bands are generic.
- `ADR-005-predicate-monotonicity.md` — the monotonicity invariant.
- `workflow/OFFLOAD_TO_CODEX_PATTERNS.md` — how to fan out to Codex.
