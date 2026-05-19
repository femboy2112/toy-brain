# PARALLEL_EXECUTION_PATTERNS.md

## Purpose

Concrete parallelization opportunities per campaign phase. Issue
parallel work in a single tool-use turn when the operations are
verifiably output-independent.

## Phase 3.32: Mainline Reconciliation + ProbeReport Protocol

### Step 1 Audit (parallel-safe)

```text
PARALLEL:
- cat docs/PR_OPEN_LIST.md (or equivalent)
- gh pr list --state open
- git log --oneline main..HEAD
- ls -1 docs/campaigns/phase3_31/
```

All four operations are read-only; results don't depend on each other.

### Step 5 Protocol authoring (parallel-safe)

```text
PARALLEL:
- write brain/development/probe_report_protocol.py
- read brain/development/proto_speech_acquisition.py
  (to confirm the existing report dataclass shape)
- read brain/development/curriculum_consolidation_probe.py
  (same)
```

The probe modules don't change; only the protocol file is authored.

### Step 8 Verification (parallel-safe)

```text
PARALLEL:
- python3 -m pytest tests/test_probe_report_protocol.py
- python3 -m pytest tests/test_proto_speech_acquisition.py
- python3 -m pytest tests/test_curriculum_consolidation_probe.py
- python3 -m pytest tests/test_active_hypothesis_probe.py
- python3 -m pytest tests/test_osmotic_learning_probe.py
```

Distinct test files; no shared module-level state.

## Phase 3.33: Strict Counter Corrigendum

### Step 4 Audit (parallel-safe)

```text
PARALLEL:
- python3 -m tools.developmental_profile_audit --audit-only \
    --probes proto_speech_acquisition --format json
- python3 -m tools.developmental_profile_audit --audit-only \
    --probes curriculum_consolidation_probe --format json
- python3 -m tools.developmental_profile_audit --audit-only \
    --probes active_hypothesis_probe --format json
- python3 -m tools.developmental_profile_audit --audit-only \
    --probes osmotic_learning_probe --format json
```

The audit is read-only per probe; four invocations are independent.

### Steps 5a–5d Strict counter additions (parallel-safe BUT...)

The four `_strict` counter additions are textually independent.
However, the catalog row addition (Step 6) and the benchmark
re-run (Step 7) must happen AFTER all four edits complete.

Recommended sequence:

```text
PARALLEL (one turn):
- edit brain/development/proto_speech_acquisition.py (add stable_combination_count_strict)
- edit brain/development/proto_speech_acquisition.py (add transfer_success_count_strict)
- edit brain/development/curriculum_consolidation_probe.py (if applicable)
- edit brain/development/active_hypothesis_probe.py (if applicable)
- edit brain/development/osmotic_learning_probe.py (if applicable)

SEQUENTIAL:
- edit brain/development/catalog.py (add catalog rows)
- python3 -m brain.development.benchmark_battery
```

Caveat: if two edits are to the SAME file, str_replace must be
sequential within that file (otherwise the first edit's view is
stale by the second). Different files are safe in parallel.

## Phase 3.34: Developmental Progression Profile

### Step 1 Module skeleton (parallel-safe)

```text
PARALLEL:
- write brain/development/developmental_progression_profile.py
- write brain/development/predicate_table.py
- write brain/development/prerequisite_graph.py
- write brain/development/fixtures/predicate_monotonicity_basic.py
```

Skeleton files; each file is self-contained at this stage.

### Step 4 Predicate authoring (parallel via Codex fan-out)

This is the BIG parallelization opportunity. The 9 remaining axes
(after the reference axis PROTO_SPEECH_COMBINATION) are independent:

```text
CODEX FAN-OUT:
- 9 parallel Codex tasks, one per axis.
- Each task: input = the axis row + ADR-005 + the template; output =
  16 predicates for that axis.
- Total wall-clock time: max of the 9, not sum.
```

See `OFFLOAD_TO_CODEX_PATTERNS.md` for the prompt template.

### Step 8 Static-audit fixture (parallel-safe)

```text
PARALLEL:
- write brain/development/fixtures/developmental_progression_static_audit.py
- write brain/development/fixtures/profile_canonical_substrate.py
- write tests/test_developmental_progression_profile.py
```

These three test surface artifacts are independent at write time.
They WILL depend on each other at run time (the static-audit imports
the canonical substrate; tests import both).

### Step 9 Benchmark axis A16 (sequential)

A16 requires the projector to be fully working. Cannot parallelize
with Step 8.

## Phase 3.35+: First Targeted Consolidation

### Mechanism implementation (parallel-safe)

```text
PARALLEL (where applicable):
- edit the targeted probe module (the mechanism's parameter change)
- edit closed-rule weights (if mechanism is THRESHOLD_ADJUSTMENT)
- author the test fixture for the post-intervention substrate

SEQUENTIAL after that:
- python3 -m tools.verify_predicate_monotonicity
- python3 -m brain.development.benchmark_battery
  (the regression gate must run AFTER all edits)
```

### Regression gate (parallel-safe across axes)

```text
PARALLEL:
- run benchmark axis A1..A8 in one subprocess
- run benchmark axis A9..A16 in another

JOIN: compare both digests against baseline.
```

The benchmark battery is internally serial per axis, but axis-level
parallelization is safe (no shared mutable state across axes).

## Anti-patterns

### Don't parallelize edits to the same file

`str_replace` requires the file's current state in context. Two
parallel `str_replace` operations to the same file create a race
condition; the second one's view is stale.

If you need to make multiple edits to one file, either:

- Sequence the `str_replace` calls (slower but safe), OR
- Build the full new file in memory and write it once.

### Don't parallelize when there's an implicit dependency

The catalog row addition must happen AFTER the code change that needs
the row. Don't parallelize them even if they're in different files;
the catalog validity check will reference code that doesn't yet
exist.

### Don't parallelize Codex fan-outs without a merge plan

If you fan out 9 axes to Codex in parallel, you need a merge plan
back into `predicate_table.py`. Either:

- Each Codex task writes to a separate file (axis-specific module);
  the main `predicate_table.py` imports all of them, OR
- Each Codex task returns a code block; a final pass merges them.

The simpler approach is per-axis files; the trade-off is more files
to maintain.
