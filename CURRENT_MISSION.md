# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below.

---

## Current mission

Tighten the Phase 3.1 proto-content promotion gate to the stronger Option A rule from the post-completion audit.

This is a **focused Phase 3.1 patch mission**.

Do **not** start Phase 3.2.
Do **not** implement output ladder, worldlet, Proto-BASIC REPL, expression, social/language, or Mode B surfaces.

---

## Important local command rule

Use `python3 -m ...` for all Python module commands.

Do **not** use `python -m ...` on this machine unless the user explicitly says a `python` alias exists.

If any copied command says `python -m`, convert it to `python3 -m` before running.

---

## Why this mission exists

`PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md` gave Phase 3.1 the verdict:

```text
PASS WITH PATCHES
```

The one P1 patch required before Phase 3.2 is promotion threshold/provenance alignment.

The audit found that the implementation currently allows hand-constructed `ProtoContent` with low positive support to promote, e.g.:

```text
salience = 0
stability = 1/10
prediction_gain = 1/10
trace provenance present
```

That is green against the current rows, but weaker than the stronger rule in the Phase 3.1 kickoff/corrigenda. The project decision is Option A:

```text
tighten implementation rather than relax catalog/docs
```

Bridge principle:

```text
PRESERVE should be earned, not labeled.
```

---

## Required source files to read first

Read these before editing:

```text
CURRENT_MISSION.md
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
INVARIANT_CATALOG.md
brain/development/promotion.py
brain/development/proto_content.py
brain/development/fixtures/proto_content_promotion.py
brain/development/fixtures/salience_is_not_truth.py
brain/invariants.py
```

Do not rely on unstated conversation context. The patch must stand on repo-local files and current tests.

---

## Required behavior

Tighten `can_promote_proto_content(...)` and `promote_proto_content(...)` so promotion requires the stronger deterministic threshold rule:

```text
salience >= 1/2
stability >= 1/2
prediction_gain >= 1/2
non-empty provenance / trace support
content_id != COGITO_ID
valid PerceptEvent construction
entry into runtime state only through tick()
```

Low positive evidence must not promote.

Specifically, a hand-constructed `ProtoContent` with:

```text
salience = 0
stability = 1/10
prediction_gain = 1/10
trace provenance present
```

must fail `can_promote_proto_content(...)` and must be rejected by `promote_proto_content(...)` with a `ValueError` naming `I-DEV-05`.

Zero support must still fail, and COGITO_ID must still fail with `I-DEV-06`.

---

## Provenance requirement

Do not weaken provenance.

At minimum, promotion must still require non-empty `trace_event_ids`.

If practical within the current data model, strengthen the error wording to clarify that promotion requires trace/probe provenance.

Do not invent a new `support_frame_ids` field in this patch unless it can be done without destabilizing existing Phase 3.1 rows. The audit patch target is threshold/provenance alignment, not a broader data-model rewrite.

---

## Allowed files

Allowed files for this mission:

```text
brain/development/promotion.py
brain/development/proto_content.py
brain/development/fixtures/proto_content_promotion.py
brain/development/fixtures/salience_is_not_truth.py
INVARIANT_CATALOG.md
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
```

Optional if genuinely necessary:

```text
brain/invariants.py
brain/_catalog_ids.py
tools/catalog.py
README.md
```

But avoid optional files unless count/catalog wording changes require them.

---

## Forbidden files / scopes

Do not modify:

```text
brain/tlica/
lean_reference/
traces/
scenarios/
brain/tick.py
brain/llm/
CURRENT_CAMPAIGN.md
.codex/
.agents/
```

Do not implement:

```text
Phase 3.2 output ladder
Minimal Worldlet
Proto-BASIC REPL
expression layer
social/language harness
Mode B developmental layer
real LLM behavior
```

---

## Catalog guidance

If the existing catalog wording already supports the stronger rule, do not change catalog counts or version.

If you update `INVARIANT_CATALOG.md`, keep it narrowly scoped to clarifying `I-DEV-05` / `I-DEV-03` promotion threshold wording. Do not add new rows unless absolutely necessary.

Preferred path:

```text
no new rows
no count change
fixture coverage tightened under existing I-DEV-03 / I-DEV-05
```

---

## Required fixture coverage

Add targeted checks showing:

```text
can_promote_proto_content(...) returns False for low positive support
promote_proto_content(...) raises ValueError naming I-DEV-05 for low positive support
salience=0 fails even if stability and prediction_gain are positive
stability < 1/2 fails
prediction_gain < 1/2 fails
missing trace provenance still fails
existing good stable proto-content still promotes
COGITO_ID still fails with I-DEV-06
```

Keep tests deterministic and exact-`Fraction`.

---

## Validation

Run:

```bash
python3 -m brain.invariants run --id I-DEV-03
python3 -m brain.invariants run --id I-DEV-05
python3 -m brain.invariants run --id I-DEV-06
python3 -m brain.invariants run --id I-SBX-02
python3 -m tools.catalog counts
bash tools/check_all.sh
```

Do not run real LLM scenario commands.

---

## Git persistence requirement

After validation passes, Codex must commit and push its result.

Rules:

```text
stage only intended files
commit with a clear message
push to current branch / main as appropriate
report the commit SHA
```

Do not commit accidental changes to guarded files.

If no files change, report why and do not commit.

---

## Final report

When done, report:

```text
Created/updated:
- <files>

Validation:
- command results

Git:
- commit: <sha or none>
- push: success / not run with reason

Verdict:
- PASS / PASS WITH PATCHES / BLOCKED

Next:
- if green, Phase 3.1 can be treated as clean PASS and Phase 3.2 planning may begin
```

---

## Stop condition

Stop after tightening promotion threshold/provenance behavior, validating, committing, pushing, and reporting.

Do not proceed into Phase 3.2 unless the user gives a new explicit instruction.
