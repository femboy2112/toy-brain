# PHASE3_32_PR_STACK_AUDIT.md

## Purpose

This is the recovery-time audit of the open PR stack (#24–#33) at the
start of Phase 3.32. It documents the current state of each PR, the
required retargeting order, and any conflicts that must be resolved
before merging.

This is a **fill-in-as-you-go** template. Phase 3.32 Step 1 populates
it. The body below is the structure; the placeholders are filled when
the audit runs.

## How to run the audit

```bash
# 1. Fetch the latest origin state.
git fetch origin --prune

# 2. List all open PRs in the stack with the metadata we need.
gh pr list --state open --json \
  number,title,headRefName,baseRefName,mergeable,statusCheckRollup,createdAt \
  > /tmp/pr-stack.json

# 3. Pretty-print and inspect.
cat /tmp/pr-stack.json | jq '.[] | {number, head: .headRefName, base: .baseRefName, mergeable, status: (.statusCheckRollup // [] | map(.conclusion) | unique)}'

# 4. Check each PR's diff against its base.
for pr in 24 25 26 27 28 29 30 31 32 33; do
  echo "=== PR #$pr ==="
  gh pr view "$pr" --json title,headRefName,baseRefName,mergeable | jq .
  gh pr diff "$pr" --stat | head -20
done

# 5. Verify the stack order on the file system.
git log --graph --oneline --all --decorate | head -50
```

## PR stack state (FILL IN at Phase 3.32 Step 1)

```text
PR #   Title                                              Base                                              Head                                              Mergeable  Checks
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
#24    phase3.19: internal feedback loop                  <FILL IN>                                         <FILL IN>                                         <FILL IN>  <FILL IN>
#25    phase3.20: coherence feedback bridge               campaign/phase3-19-internal-feedback-loop         campaign/phase3-20-coherence-feedback-bridge      <FILL IN>  <FILL IN>
#26    phase3.21: developmental trajectory                campaign/phase3-20-coherence-feedback-bridge      campaign/phase3-21-developmental-trajectory       <FILL IN>  <FILL IN>
#27    phase3.22 + 3.22b                                  campaign/phase3-21-developmental-trajectory       campaign/phase3-22-agent-communication-loop       <FILL IN>  <FILL IN>
#28    phase3.23: dispatch tracer                         campaign/phase3-22-agent-communication-loop       campaign/phase3-23-dispatch-tracer                <FILL IN>  <FILL IN>
#29    phase3.24: worldlet feedback bridge                campaign/phase3-23-dispatch-tracer                campaign/phase3-24-worldlet-feedback-bridge       <FILL IN>  <FILL IN>
#30    phase3.25: osmotic learning live test              campaign/phase3-24-worldlet-feedback-bridge       campaign/phase3-25-osmotic-learning-live-test     <FILL IN>  <FILL IN>
#31    phase3.26: active hypothesis                       campaign/phase3-25-osmotic-learning-live-test     campaign/phase3-26-active-hypothesis-probe        <FILL IN>  <FILL IN>
#32    phase3.30: curriculum consolidation                campaign/phase3-26-active-hypothesis-probe        campaign/phase3-30-curriculum-consolidation       <FILL IN>  <FILL IN>
#33    phase3.31: caregiver proto-speech                  campaign/phase3-30-curriculum-consolidation       campaign/phase3-31-caregiver-proto-speech         <FILL IN>  <FILL IN>
```

## Required merge sequence

Merge from the bottom of the stack upward, retargeting the next PR's
base to `main` after each merge. The expected sequence:

```text
1.  PR #24 → main                                   (no retarget needed)
2.  Retarget PR #25's base from campaign/phase3-19-* to main; merge.
3.  Retarget PR #26's base from campaign/phase3-20-* to main; merge.
4.  Retarget PR #27's base from campaign/phase3-21-* to main; merge.
5.  Retarget PR #28's base from campaign/phase3-22-* to main; merge.
6.  Retarget PR #29's base from campaign/phase3-23-* to main; merge.
7.  Retarget PR #30's base from campaign/phase3-24-* to main; merge.
8.  Retarget PR #31's base from campaign/phase3-25-* to main; merge.
9.  Retarget PR #32's base from campaign/phase3-26-* to main; merge.
10. Retarget PR #33's base from campaign/phase3-30-* to main; merge.
```

## Conflict prediction

The two files most likely to conflict during reconciliation are:

```text
INVARIANT_CATALOG.md         catalog version banner; row counts; new rows
PHASE3_HANDOFF_STATE.md      "Last updated" stanza; PR map
README.md                    catalog version banner
brain/_catalog_ids.py        auto-generated; should be regenerated post-merge
tools/catalog.py             EXPECTED_COUNTS dict
```

For each merge, the resolution rule is:

```text
catalog version banner       take the LATER campaign's value
row counts                   recompute by counting rows in the merged file
PHASE3_HANDOFF_STATE.md      take the LATER campaign's value
brain/_catalog_ids.py        regenerate via `python3 -m tools.catalog generate-ids`
tools/catalog.py EXPECTED_   take the LATER campaign's value (typically;
COUNTS                       verify against the merged INVARIANT_CATALOG.md)
```

Each merge must be followed by:

```bash
python3 -m tools.catalog counts          # verify banner/actual/expected agree
python3 -m tools.citations verify
python3 -m brain.invariants run
bash tools/check_all.sh
```

If any of these fail, ROLL BACK the merge, investigate, and re-merge
after the issue is fixed.

## Phase 3.32 branch creation

After all ten PRs are merged into `main`:

```bash
git checkout main
git pull origin main
git checkout -b campaign/phase3-32-mainline-reconciliation
```

Then proceed with Step 4 of the Phase 3.32 roadmap (Protocol declaration).

## Stop conditions

Stop Step 2 (the merge sequence) and escalate to operator if:

- Any PR's status checks are red. Operator decides whether to wait
  for the next commit or to merge as-is.
- Mergeability returns `CONFLICTING`. Operator decides resolution
  approach.
- A merge introduces a regression on `python3 -m brain.invariants run`
  that does not match the expected pattern from the catalog history.

## Cross-references

- `PHASE3_32_MAINLINE_RECONCILIATION_ROADMAP.md` — Phase 3.32's
  acceptance criteria.
- `PHASE3_HANDOFF_STATE.md` — current PR map and stack-merge order.
- `SPEC_UPDATES.md` — catalog version banner discipline.
