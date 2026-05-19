# ADR-NNN-<short-name-hyphenated>.md

<!--
USAGE: copy this template to ADR-NNN-<short-name-hyphenated>.md.
- NNN is the next sequential ADR number (last one in the bundle is
  ADR-006).
- short-name is 3-5 words, kebab-case.
- The file goes at the repo root (where ADR-001..006 already live).
- Fill in every <<<...>>> placeholder.
-->

## Title

<<<One-line title describing the decision.>>>

## Status

<<<One of: Proposed | Accepted | Superseded by ADR-NNN | Deprecated>>>

Date authored: <<<YYYY-MM-DD>>>
Date accepted: <<<YYYY-MM-DD or "pending">>>

## Context

<<<What problem does this ADR address? What was true about the
codebase before this decision that made the decision necessary?
2-4 paragraphs. Cite specific files, prior ADRs, prior campaigns,
or benchmark results where relevant. Do NOT make cognitive claims
about ToyI; the context is structural.>>>

<<<If this ADR was prompted by a specific campaign or finding (e.g.,
"Phase 3.32 step 4 revealed that ProbeReport had no shared protocol"),
state that explicitly.>>>

## Decisions

<<<Number each decision: D1, D2, ... Each decision is one sentence
in declarative form. Decisions are LOCKED once the ADR is accepted;
relitigating them requires a successor ADR.>>>

**D1**: <<<First locked decision.>>>

**D2**: <<<Second locked decision (if applicable).>>>

...

## Consequences

### Positive

- <<<What this ADR makes possible or easier.>>>
- <<<...>>>

### Negative

- <<<What this ADR forecloses or makes harder. Be honest; this section
  matters for future ADRs that may want to revisit.>>>
- <<<...>>>

### Neutral / observed

- <<<Effects that are neither clearly positive nor negative, but
  worth documenting.>>>

## Catalog binding

<<<If this ADR introduces or modifies catalog rows, list them here.
Otherwise write "No catalog rows directly bound to this ADR."

Format for each row:

  I-<CATEGORY>-<SHORT-NAME>          (REQUIRED|STRUCTURAL)
    Brief description of what the row asserts. The implementing
    code/test that verifies the assertion. The campaign that
    introduces the row.

The catalog binding section is the bridge from the ADR (architectural
commitment) to the catalog (machine-checkable invariant). Every
REQUIRED catalog row should trace back to an ADR; every ADR with
mechanical implications should bind a catalog row.>>>

## Forbidden under this ADR

<<<List things that this ADR explicitly forbids. This is a
non-exhaustive list of "do not do X" rules that future campaigns
must respect. Examples:

- No <pattern> introduced into <file/module>.
- No use of <forbidden term> in any produced string.
- No widening of <scope> without a successor ADR.

The forbidden list complements the decisions: the decisions say what
to do; the forbidden list says what NOT to do.>>>

## Open questions deferred to successor ADRs

<<<If this ADR leaves questions open, list them here with rough
disposition. Examples:

- "How <pattern> generalizes to <future axis> is deferred to a
  successor ADR after Phase 3.NN."
- "Whether <decision D-N> should extend to <related context> is
  deferred."

This section is optional but useful for long-running campaigns.
Leaving questions unaddressed without flagging them produces drift.>>>

## Cross-references

```text
Related ADRs:
  ADR-<N>-<...>  — relationship: <e.g., "depends on", "supersedes">

Related campaign roadmaps:
  PHASE3_NN_*_ROADMAP.md

Related skills / agents / commands:
  <list>

Related code:
  <file/module names this ADR governs>
```

## Hard limits

<<<Compact statement of what this ADR forbids and what the
mechanical check is. Mirrors the "Forbidden" section but oriented
toward enforcement.

Examples:

- <Forbidden pattern> is detected by <tool/test> and fails CI.
- <Required pattern> is verified by <tool/test> at <import time | CI
  | benchmark time>.
- Violation results in <ImportError | test FAIL | benchmark FAIL>.

If there's no mechanical check, write "Enforced by reviewer
judgment, not by automation." This is acceptable for some ADRs but
the bias should be toward mechanical enforcement.>>>
