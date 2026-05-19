# EFFICIENCY_PLAYBOOK.md

## Purpose

Global patterns for running campaigns efficiently. These apply to
every phase but become especially important in 3.34 (the predicate
authoring fan-out) and 3.35+ (where the regression gate must run on
every change).

## Pattern 1: Parallel preflight

At the start of every campaign step, the following can run in
parallel (no dependencies between them):

```text
- Run the failing benchmark axis subset that this step targets.
- Read the relevant ADRs (if not already in context).
- Read the relevant test fixtures.
- Run the linter.
- Run the catalog validity check.
```

In Claude Code, do this by issuing one tool-use turn with multiple
independent bash invocations. Don't sequence them.

Bad:

```text
1. read ADR-005
2. (wait)
3. read predicate_table.py
4. (wait)
5. run the lint
```

Good (one turn, parallel):

```text
read ADR-005 + read predicate_table.py + run lint
```

## Pattern 2: Batch independent edits

When a campaign step modifies multiple files independently (e.g.,
adding a `_strict` counter to four probe report dataclasses, each in
its own module), do all edits in one turn. Do NOT serialize.

The Phase 3.33 Steps 5a–5d edits should be **one turn**, not four. The
test-then-edit cycle is shared across them anyway (a single benchmark
run validates all four edits).

## Pattern 3: Codex offload for fan-out work

For work that is structurally repetitive — like authoring 16
predicates × 9 axes — delegate to Codex via the
`chatgpt-codex-orchestrator` agent. The Claude Code conversation
should:

1. Author ONE axis's predicates fully (the reference implementation;
   PROTO_SPEECH_COMBINATION is already done in
   `PHASE3_34_PREDICATE_TEMPLATE.md`).
2. Delegate the remaining 9 axes' predicates to Codex with a fan-out
   prompt (see `OFFLOAD_TO_CODEX_PATTERNS.md`).
3. Collect Codex's output and merge it into `predicate_table.py`.
4. Run `python3 -m tools.verify_predicate_monotonicity` to validate.

This pattern moves the bulk of the per-axis predicate authoring out
of the high-context Claude Code conversation and into a low-context
Codex conversation that only sees the relevant spec + one axis's row
of the semantic table.

## Pattern 4: Self-generated bash for repetitive code searches

If you find yourself running similar grep commands repeatedly, write
a one-liner Python or bash script and reuse it. For example, the
graceful-pass audit (Phase 3.33 Step 4) became a permanent tool
(`tools/developmental_profile_audit.py`) rather than ad-hoc greps.

## Pattern 5: One campaign, one conversation

Each phase (3.32, 3.33, 3.34, 3.35) should be its own conversation,
started fresh. The context required for Phase 3.34 alone is
substantial; mixing it with 3.33's context wastes tokens.

See `CONTEXT_MANAGEMENT_GUIDE.md` for what to seed at the start of
each phase.

## Pattern 6: Read-once, reference-many

When a long document (like a roadmap or design doc) will be referenced
multiple times in a campaign step, read it once at the start of the
step and don't re-read it. The agent's context already has it.

Conversely, if you find yourself paging through the same file
repeatedly because each grep returned a snippet, just `cat` the file
once.

## Pattern 7: Benchmark axis subsetting

The full benchmark battery is expensive. For a campaign that targets
a specific axis subset, run only the relevant axes:

```bash
# Run only A16 (Phase 3.34's axis).
python3 -m brain.development.benchmark_battery --axes A16

# Run A1..A15 minus A16 (the regression gate for Phase 3.34).
python3 -m brain.development.benchmark_battery --axes A1-A15 --exclude A16
```

The regression gate (ADR-004) requires the FULL benchmark suite at
campaign acceptance. But during step development, subsetting is OK.

## Pattern 8: Determinism check via two-run digest

The cheapest test of "is this thing deterministic" is to run it twice
and compare digests. Build this into every digest-producing test:

```python
def test_projector_deterministic():
    reports = canonical_probe_reports()
    profile_a = project_developmental_progression_profile(reports)
    profile_b = project_developmental_progression_profile(reports)
    assert profile_a.profile_digest_hex16 == profile_b.profile_digest_hex16
```

This is faster than asserting structural equality of the full
DevelopmentalProgressionProfile object.

## Pattern 9: Failure first, success second

When implementing a step that adds a new check (predicate
monotonicity, audit-clean, etc.), write the failure case before the
success case:

1. Author a synthetic fixture that should FAIL the check.
2. Confirm the check rejects it.
3. THEN author the canonical (passing) fixture.
4. Confirm the check accepts it.

This guarantees the check is doing something. A check that only ever
runs against passing inputs is a passing check by construction.

## Pattern 10: Catalog row first, code second

When adding a structural assertion (anything REQUIRED in the
catalog), write the catalog row first. The row description forces
you to articulate the assertion in plain language. Then the code
implements the row's assertion.

This pattern avoids the failure mode "I added the code but forgot to
add the catalog row" — a frequent regression in Phase 3.31 and
earlier.

## Pattern 11: Bundle drop-in cadence

Don't drop in all campaigns' files at once. The drop-in cadence:

```text
Now:        Permanent files + Phase 3.32 files.
After 3.32: Add Phase 3.33 files.
After 3.33: Add Phase 3.34 files.
After 3.34: Add Phase 3.35 files.
```

Permanent files (the ADRs, agents, commands, skills, tools) stay
across campaigns. Phase-specific files (the roadmaps, designs,
audit plans) get dropped in just before the campaign runs.

This minimizes "stale doc references previously-rejected design"
confusion.
