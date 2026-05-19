# CURRENT_CAMPAIGN.md — Phase 3.32 Mainline Reconciliation

## Campaign status

```text
RECONCILIATION / SINGLE-PR / NO-NEW-FEATURES / REVIEW-GATED
```

Phase 3.32 is a stabilization campaign. The Phases 3.20 .. 3.31
campaign stack landed via stacked PRs that merged into prior
campaign branches instead of into `main`, so `main` is currently
stale at Phase 3.19 / catalog v0.27. Phase 3.31 PR #33 was merged
on 2026-05-19 into `campaign/phase3-30-curriculum-consolidation`,
which is now the latest completed stack tip and contains
Phase 3.31 / catalog v0.37.

Phase 3.32 asks one bounded operational question:

```text
Can the completed campaign stack through Phase 3.31 (catalog v0.37)
be brought onto main as a single reconciliation PR, with every
canonical gate green, every catalog-version banner aligned, every
generated-id file regenerated, and the operator-facing handoff /
mission docs no longer pointing future agents at stale branch
assumptions, while adding zero new behavioral features and
preserving every existing non-claim discipline guardrail?
```

This is a **reconciliation / stabilization** campaign. It is
**NOT** a proof of consciousness, sentience, subjective experience,
agency, semantic understanding, real reasoning, real learning, real
memory, real language acquisition, real language understanding, real
communicative intent, real inner speech, real private thought, real
hidden chain-of-thought, real audience modelling, intentionality,
awareness, intuition, embodiment, psychological development, or any
cognitive process. No new claims are introduced; every prior
non-claim guardrail carries forward unchanged.

Phase 3.32 does **not** add any new `OperatorCommand` member,
`LOCAL_COMMAND_VERBS` entry, `ACTIVE_VIEWS` value, `GrowthEventType`,
`GrowthEventSource`, persistence schema column, autosave trigger,
`LearningEvidenceKind` member, `ReasoningStepKind` member,
benchmark axis, runtime module, or catalog row. It does **not**
change L1 / L2 / parser / prompt / tick / persistence / autosave /
DB schema semantics. It does **not** modify theory semantics. The
allowed edits are strictly:

- a `--no-ff` merge of `origin/campaign/phase3-30-curriculum-
  consolidation` into a new branch
  `campaign/phase3-32-mainline-reconciliation` cut from `main`;
- corrections to stale README / INVARIANT_CATALOG / handoff /
  current-mission / current-campaign banners and version strings;
- regeneration of `brain/_catalog_ids.py` if drift is detected;
- the reconciliation commit message and PR body.

---

## Source-of-truth

- Reconciliation branch: `campaign/phase3-32-mainline-reconciliation`
- Reconciliation base: `main`
- Source merged: `origin/campaign/phase3-30-curriculum-consolidation`
  (which contains Phase 3.31 via PR #33 merged 2026-05-19)
- Expected catalog version: v0.37
- Expected catalog counts: REQUIRED 392 / STRUCTURAL 101 /
  NOT-EXERCISED 14 / DEFERRED 15 / OBSERVED 16
- Expected benchmark: 137 total / 136 PASS / 1 WARN (A3.04
  carry-over) / 0 FAIL
- Expected proto-speech live-test: 10/10 PASS, fp=0, fn=0,
  stable_single=5, stable_combination=0, suppressed=2,
  transfer_success=1, report_digest=`f6a83b9caef0ac17`,
  drive_stream_digest=`dc060a88a814f448`
- Expected invariants: 0 red
- Expected gate_runner: 5/5 PASS
- Expected real model calls: 0
- Expected cache writes: 0
- Expected forbidden-term hits: 0

---

## Steps

### Step 1 — verify state (read-only)

- Confirm worktree is clean.
- Confirm PR #33 is MERGED into
  `campaign/phase3-30-curriculum-consolidation`.
- Confirm the source branch contains
  `brain/development/proto_speech_acquisition.py`,
  `docs/campaigns/phase3_31/`, and the
  `PHASE3_31_CAREGIVER_PROTO_SPEECH_ROADMAP.md` roadmap.

### Step 2 — cut reconciliation branch

```
git checkout main
git pull --ff-only origin main
git checkout -b campaign/phase3-32-mainline-reconciliation
```

### Step 3 — merge campaign stack

```
git merge --no-ff origin/campaign/phase3-30-curriculum-consolidation
```

Resolve any conflicts by preferring campaign-branch content unless
there is a clear main-only fix that is genuinely absent upstream.
Do not drop campaign files; do not hand-edit large generated
sections.

### Step 4 — patch staleness

Verify and, if needed, patch:

- `README.md` catalog-version banner reads `v0.37`.
- `INVARIANT_CATALOG.md` title and explicit-version paragraph
  both read `v0.37`.
- `tools/catalog.py` `EXPECTED_COUNTS` and the parsed catalog agree
  (counts gate passes).
- `brain/_catalog_ids.py` is regenerated via
  `python3 -m tools.catalog generate-ids`.
- `PHASE3_HANDOFF_STATE.md` reflects Phase 3.32 reconciliation in
  flight and the merged status of the campaign stack.
- `CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` describe Phase 3.32
  (not a stale Phase 3.31 instruction).
- Any "PR #N open" / "stack is open" wording in handoff/mission
  is either corrected or annotated as historical.

No new behavioral code is added under any circumstances.

### Step 5 — run full gate set

```
python3 -m brain.development.proto_speech_acquisition
python3 -m brain.development.agent_benchmark
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
python3 -m tools.claude_helpers.gate_runner --json
```

Every command must succeed at the expected verdicts listed under
"Source-of-truth".

### Step 6 — commit, push, open PR

Commit message:

```
phase3.32: reconcile campaign stack into main
```

Push the branch and open a PR with `--base main --head
campaign/phase3-32-mainline-reconciliation`. The PR body must
include catalog version, counts, benchmark totals, proto-speech
live-test result, gate verdict, invariants result, real-model-call
count, cache-write count, forbidden-term-hit count, staleness
patches applied, remaining WARNs, an explicit non-claim
disclosure, and an explicit "Merge with merge commit only after
operator approval" instruction.

Do NOT merge the PR.

---

## Acceptance criteria

Phase 3.32 succeeds only when:

- branch `campaign/phase3-32-mainline-reconciliation` exists,
  cut from `main`, with `origin/campaign/phase3-30-curriculum-
  consolidation` merged via `--no-ff`;
- README, INVARIANT_CATALOG, tools/catalog.py, and
  brain/_catalog_ids.py agree on catalog v0.37 with banner
  counts REQUIRED=392 STRUCTURAL=101 NOT-EXERCISED=14
  DEFERRED=15 OBSERVED=16;
- `python3 -m brain.development.proto_speech_acquisition`
  reports 10/10 PASS, fp=0, fn=0, digest `f6a83b9caef0ac17`;
- `python3 -m brain.development.agent_benchmark` reports
  137 total / 136 PASS / 1 WARN / 0 FAIL;
- `python3 -m brain.invariants run` is fully green;
- `bash tools/check_all.sh` and
  `python3 -m tools.claude_helpers.gate_runner --json` report
  5/5 PASS;
- real_model_calls == 0; cache_writes == 0;
  forbidden_term_hits == 0;
- `PHASE3_HANDOFF_STATE.md`, `CURRENT_MISSION.md`, and
  `CURRENT_CAMPAIGN.md` describe Phase 3.32 (not stale Phase
  3.31 instructions);
- a single PR is opened with base `main` and head
  `campaign/phase3-32-mainline-reconciliation`;
- the PR is NOT merged automatically;
- no new behavioral feature, runtime module, fixture, catalog
  row, or benchmark axis is introduced;
- no theory semantics are changed;
- non-claim discipline is preserved.
