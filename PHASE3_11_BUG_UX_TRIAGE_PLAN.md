# PHASE3_11_BUG_UX_TRIAGE_PLAN.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 19: classify Phase 3.11 live behavior
findings into critical correctness, safety/invariant, operator UX,
documentation, and deferred enhancement buckets.

Source findings:

```text
PHASE3_11_BEHAVIOR_FINDINGS.md
```

This is a report-only triage artifact. It does not edit source code,
fixtures, catalog rows, mission/campaign routing prose, or prior reports.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 19
Prior step evidence: 80a684c phase3.11 step18: behavior findings
```

## Triage Summary

```text
critical correctness: 0
safety/invariant:     0
operator UX:          1
documentation:        2
deferred enhancement: 1
```

No Step 13-17 observation produced a `fails` verdict. No critical
correctness or safety/invariant patch is proposed for Step 21.

## Critical Correctness

None.

Rationale:

```text
No live behavior row was classified as fails.
All standard gates stayed green after each report.
No kernel state corruption, failed invariant, failed persistence load/save,
failed autosave trigger, or failed LLM fail-closed path was observed.
```

Step 20 consequence:

```text
No critical correctness code patch is proposed.
```

## Safety / Invariant

None.

Rationale:

```text
Catalog counts, citation verification, import audit, and check_all.sh all
passed after Steps 13-18.
No observation showed raw text mapping to COGITO_ID, direct BrainState
mutation outside tick/load paths, unsafe OperatorSession resources, hidden
LLM calls, hidden autosave, or hidden network/API behavior.
```

Step 20 consequence:

```text
No safety/invariant code patch is proposed.
```

## Operator UX

### UX-01: parse rejection can leave prior status visible

Finding:

```text
Step 16: /db-backup file:/tmp/disallowed.db was rejected at parse time
with a clear parse error, but the prior successful /db-backup status
remained visible in the helper snapshot because parsing failed before
dispatch.
```

Classification:

```text
operator UX
```

Severity:

```text
low
```

Proposed action:

```text
Defer. If a later UX campaign revisits parse-error rendering, consider
clearing or visually separating stale status when the composer/parser
rejects input before dispatch.
```

Step 20 consequence:

```text
No critical code patch proposed.
```

## Documentation

### DOC-01: Step 16 matrix overstates backup byte identity

Finding:

```text
Step 16: SQLite backup files had the same size as the source DB but a
different SHA-256 hash. The source DB hash stayed unchanged and the
backup reported pages=18/18, so the runtime behavior matches a SQLite
backup API copy, not a byte-identical file clone.
```

Classification:

```text
documentation
```

Severity:

```text
low
```

Proposed action:

```text
At the next documentation refresh boundary, replace "byte-faithful
SQLite backup" wording with "SQLite backup API copy that preserves the
source DB and creates a valid same-size backup" or equivalent.
```

Step 20 consequence:

```text
No code patch proposed.
```

### DOC-02: CURRENT_MISSION / CURRENT_CAMPAIGN next-step prose is stale

Finding:

```text
Mission/campaign baseline prose still says Steps 8-12 complete and
next eligible Step 13, while committed branch evidence now shows Steps
13-19 complete through this triage plan.
```

Classification:

```text
documentation
```

Severity:

```text
low
```

Proposed action:

```text
At the next accepted documentation sync boundary, refresh mission and
campaign routing prose so "next eligible step" no longer points at
Step 13. This triage step does not edit those files because Steps 13-19
are report-only by campaign discipline.
```

Step 20 consequence:

```text
No code patch proposed.
```

## Deferred Enhancement

### DEFER-01: optional real LLM smoke remains manual / explicitly accepted

Finding:

```text
Step 17 deterministic gates recorded Claude and Codex executables on
PATH but did not invoke real external CLI smokes. Anthropic API smoke
was also skipped because no API key was accepted/configured for a real
smoke.
```

Classification:

```text
deferred enhancement
```

Severity:

```text
optional
```

Proposed action:

```text
Run a separate operator-approved ORS pass only if real external runtime
confidence is needed. That pass should state credentials/auth/tool
availability expectations explicitly and remain OBSERVED/manual unless
a future campaign deliberately makes it gating.
```

Step 20 consequence:

```text
No critical code patch proposed.
```

## Step 20 Gate Recommendation

```text
No critical correctness patch is requested.
No safety/invariant patch is requested.
No Step 21 code changes are proposed by this triage plan.
Documentation and UX follow-ups are deferred to later accepted doc/UX
work or to the final comprehensive audit recommendations.
```

If the Step 20 gate requires an explicit decision, the recommended
decision is:

```text
No critical fixes to apply; skip Step 21 unless the operator explicitly
promotes one of the non-critical follow-ups.
```

## Validation

Post-report validation:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

Scope guard after validation:

```text
git status --short                    only PHASE3_11_BUG_UX_TRIAGE_PLAN.md
git diff --name-only                  no tracked source/catalog/mission diff
```

## Next

The next campaign point is Step 20:

```text
Critical correctness patch gate.
```

This triage plan proposes no critical correctness/safety code patch.
