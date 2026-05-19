# ADR-006 — Developmental Vocabulary Discipline

## Status

Accepted (specializes the project-wide non-claim discipline).

## Context

The whole point of the developmental progression track is to make ToyI's
capability profile measurable and comparable across campaigns. But the
language used to describe that profile is the highest-risk vector for
cognitive overclaim. Words like "mental age," "developmental stage,"
"infant," "preschool," "language acquisition," "learning trajectory"
carry psychological connotations that the project explicitly forbids.

The Phase 3.21 milestone harness solved an earlier instance of this by
using purely structural labels (`M01_REFLEXIVE_BASELINE`) and pushing
the human-developmental analogy into a design doc paragraph qualified
with "structural marker only." This ADR extends that discipline to the
progression profile.

## Decision

### 1. Runtime/produced strings: no age vocabulary

The following terms are **forbidden** in any string produced by
`brain/development/developmental_progression_profile.py` or any module
it imports for the purpose of the profile track:

```text
month        months       year         years
year-old     years old    infant       infants
toddler      preschool    childhood    childhood
adolescence  adolescent   neonate      newborn
baby         babies       child        children
juvenile     adult        immature     mature
"X-month-old"  any age-numeric construct
```

The static-audit fixture greps every `MODULE_PRODUCED_STRINGS` entry,
every report field that contains a printable string, and every
docstring-derived report excerpt against this list. A hit is a FAIL.

### 2. Band labels are STRUCTURAL only

The eight bands defined in ADR-002 have purely structural names:

```text
B00_REFLEXIVE          B04_TRANSFERS
B01_EMERGENT           B05_COMBINES
B02_REPEATABLE         B06_REPAIRS
B03_STABLE_IN_CONTEXT  B07_GENERALIZES
```

These names refer to **runtime behavior shape**, not to psychological
stages. The runtime never says "infant-like behavior"; it says
"B01_EMERGENT".

### 3. The word "developmental" is allowed but constrained

"Developmental" appears in module names (`developmental_progression_profile`)
and class names (`DevelopmentalAxis`, `DevelopmentalBand`,
`DevelopmentalProgressionProfile`) because the project has been using it
in the structural sense since Phase 3.21 (`milestone_harness.py`'s
`DevelopmentalMilestone` enum).

It is **not** allowed in produced strings except as part of these names.
A report that says "developmental band assignment" is fine; a report
that says "developmental progress over time" is not (it suggests
psychological development).

### 4. The word "training" is forbidden in this track

Replacements:

```text
"training ladder"     →  "progression ladder"
"training target"     →  "consolidation target" or "progression target"
"training campaign"   →  "consolidation campaign"
"trained model"       →  "post-consolidation runtime"
```

This is consistent with Phase 3.30's `curriculum_consolidation`
discipline.

### 5. Age-mapping documentation rules

Where it is useful to explain a band's behavioral shape by analogy to
a human-developmental phenomenon, the analogy:

- Lives ONLY in design docs (`docs/campaigns/phase3_34/*.md`), NEVER
  in code, fixtures, or runtime strings.
- Is always introduced with the explicit qualifier "structural marker
  only — this is engineering shorthand, not a claim of psychological
  development."
- Uses bounded narrow analogies (e.g., "stable single-token forms have
  a structural shape analogous to early holophrastic forms in human
  speech development at the marker level").
- Never names a specific age in months or years in the same paragraph
  as a band label.

The Phase 3.21 roadmap's Section 3 is the gold-standard template for
this language. Match its tone.

### 6. The static-audit fixture

`brain/development/fixtures/developmental_progression_static_audit.py`
implements the audit:

```python
def audit_no_age_vocabulary(text: str) -> Optional[str]:
    """Return the first forbidden term found, or None."""
    for term in _FORBIDDEN_AGE_VOCABULARY:
        if term.lower() in text.lower():
            return term
    return None

def audit_module_produced_strings() -> tuple[str, ...]:
    """Return all violations across the module's produced strings."""
```

The audit runs over:

- Every entry in `MODULE_PRODUCED_STRINGS`.
- Every printable bounded string field in every dataclass the module
  exports.
- Every docstring excerpt that flows into reports.

Catalog: `I-DEVPROF-NO-AGE-VOCAB` STRUCTURAL row.

## Why this is more than discipline theater

Age vocabulary is a slippery slope. A single produced string saying
"toddler-like" appears benign in isolation, but it would:

1. Set a precedent that age vocabulary is OK in some places.
2. Drift into fixtures, then into the report layer.
3. Eventually appear in user-facing output, where it could be
   misinterpreted as a cognitive claim.
4. Compromise the project's overall non-claim discipline by giving a
   foothold to broader psychological vocabulary.

The check is cheap and the discipline is clear. Hold the line.

## Forbidden

- Any age-month or age-year string in any produced runtime string.
- "Mental age", "developmental quotient", "psychological age",
  "biological age", "chronological age".
- "Like a toddler", "like an infant", "child-like", "infant-like",
  "preschool-level".
- Implying that the profile measures cognitive maturity, language
  ability, learning capacity, or any psychological attribute.
