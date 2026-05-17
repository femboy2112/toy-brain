# CURRENT_CAMPAIGN.md — Phase 3.13 Growth Ledger Campaign

## Campaign status

```text
DRAFT / BRANCH-FIRST / STEP-COMMIT / PUSH-EVERY-STEP / REVIEW-GATED
```

Phase 3.13 follows the completed Phase 3.12 Coherent I-Loop Observatory. Phase 3.12 shipped:

```text
measurement-first observatory over the existing /stream -> /stream-promote -> /step path
Pattern Ledger     brain/development/pattern_ledger.py     I-PLEDGER-01..18    catalog v0.21
Coherence Monitor  brain/development/coherence_monitor.py  I-COHMON-01..14     catalog v0.22
SelfModel / Growth Ledger ROADMAP (Step 15) deferred to Review Gate D
```

Subsequent merges on main:

```text
PR #12  docs cleanup: completed campaign artifacts archived under docs/campaigns/
PR #13  Claude -> Codex CLI -> ChatGPT advisory bridge (Stage A /ask-chatgpt)
```

Phase 3.13 asks the next bounded question:

```text
Can ToyI record accepted, constructor-validated growth events as a bounded developmental substrate without inventing growth from current state alone, and without any SelfModel / consciousness / sentience / subjective / semantic / truth / agency / self-modification claim?
```

This campaign does **not** implement SelfModel. The canonical Phase 3.12 Step 15 roadmap (`docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md`) recommends Growth Ledger first because SelfModel should later *quote* bounded growth facts rather than *infer* growth from current state alone. Phase 3.13 honors that ordering: Growth Ledger only.

Preferred campaign branch:

```text
campaign/phase3-13-growth-ledger
```

Preferred final PR title:

```text
phase3.13: growth ledger
```

Rules:

```text
work on the campaign branch
commit successful step results
push every successful step commit to the campaign branch
finish by opening a PR into main
never push campaign work directly to main
never merge without explicit user approval
```

---

## Mandatory files to read

Before doing campaign work, a repo-capable agent must read:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
CLAUDE.md
AGENTS.md
.claude/agents/brain-current-mission.md
.claude/agents/chatgpt-codex-subagent.md
.claude/commands/go.md
.claude/commands/ask-chatgpt.md
tools/claude_helpers/codex_chatgpt_subagent.py
CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md
docs/README.md
docs/campaigns/README.md
docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
docs/campaigns/phase3_12/PHASE3_12_COHERENT_I_LOOP_AUDIT.md
brain/development/pattern_ledger.py
brain/development/coherence_monitor.py
brain/ui/session.py
brain/tick.py
tools/check_all.sh
```

Then read whichever files the next campaign step names. Do not rely on chat memory.

---

## Baseline

Expected current state:

```text
Catalog: v0.22
Counts:
  REQUIRED:        240
  STRUCTURAL:       85
  NOT-EXERCISED:    11
  DEFERRED:         14
  OBSERVED:         16
Latest completed campaign:  Phase 3.12 Coherent I-Loop Observatory
Latest merged PRs:          PR #11 (Phase 3.12), PR #12 (docs archive),
                            PR #13 (ChatGPT/Codex advisory bridge)
Current campaign:           Phase 3.13 Growth Ledger
Next eligible step:         Step 1 repo-state sync and Phase 3.13 mission install
Canonical design seed:      docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
```

Inherited follow-ups deliberately deferred from Phase 3.12 and earlier:

```text
- SelfModel implementation (Phase 3.12 Step 15 roadmap) is OUT OF SCOPE
  for Phase 3.13. It will be reconsidered only after Growth Ledger lands.
- /pattern-ledger UI is DEFERRED (I-PLEDGER-17). Not promoted in Phase 3.13.
- /coherence-summary UI is DEFERRED (I-COHMON-13). Not promoted in
  Phase 3.13.
- end-to-end Pattern Ledger / Coherence Monitor dry-run helpers are
  NOT-EXERCISED (I-PLEDGER-18 / I-COHMON-14). Not promoted in Phase 3.13.
- SQLite backup wording note (carried from Phase 3.10c). Not in Phase 3.13
  scope.
- optional real ORS smoke for anthropic-api / claude-cli / codex-cli
  remains deferred. The Stage A /ask-chatgpt bridge is a separate,
  sanctioned advisory channel and is not a runtime LLM seam.
```

---

## Operational target

Phase 3.13 uses this operational definition (verbatim from the Phase 3.12 Step 15 roadmap, adapted as the active campaign's operating definition):

```text
Growth Ledger:
  a bounded developmental record of accepted, constructor-validated growth
  events produced by explicit successful runtime / developmental
  transitions. Events store bounded printable record references, never raw
  text payload. The ledger is session-local in v1, copy-on-write, capped at
  GROWTH_LEDGER_MAX_EVENTS, deduplicated against the obvious anti-Goodhart
  attacks, and never inflates under spam. The ledger does not call tick(),
  does not call any LLM client, does not open any DB, and does not extend
  /save-session / /load-session / autosave.

Growth event:
  one record with bounded printable event_id (not COGITO_ID), a finite
  closed event_type, a non-negative int tick (session.tick_counter at
  observe time), a closed-enum source label naming the dispatcher /
  builder, a tuple of bounded printable references (chunk_id, candidate_id,
  pattern_id, snapshot_id, autosave status snapshot id, ...), and a
  bounded printable provenance string.

Accepted:
  the source dispatcher returned a positive outcome through the Phase 3.10c
  outcome-detection contract that already powers autosave. Failed parse,
  failed dispatch, failed tick, and read-only command do not count.
  Status / error string parsing is forbidden.

Substrate composition:
  Pattern Ledger     bounded structural recurrence evidence
  Coherence Monitor  bounded read-only state consistency
  Growth Ledger      bounded historical accepted events
  SelfModel          (FUTURE; not in Phase 3.13) bounded quotation summary
```

---

## Non-goals

```text
no SelfModel implementation in Phase 3.13
no proof or claim of consciousness
no claim of sentience
no claim of subjective experience
no claim of semantic understanding
no truth adjudication or PRESERVE / DAMAGE judgment from raw text
no claim of agency / intent / will / desire
no claim of self-modification of code, fixtures, the catalog, or the runtime
no aggregate consciousness / sentience / awareness / I-ness / growth score
no model-backed behavior as default
no hidden LLM calls
no hidden autosave behavior
no direct raw-text-to-BrainState mutation
no direct raw-text-to-COGITO_ID mapping
no DB schema change in v1 unless explicitly planned and accepted at the
  review gate
no /save-session / /load-session / autosave extension in v1 unless
  explicitly planned and accepted at the review gate
no new long-term memory model before SelfModel (which is itself deferred)
no real external LLM smoke beyond the sanctioned Stage A /ask-chatgpt
  bridge
```

---

## Macro sequence

```text
Step 1   Repo-state sync and Phase 3.13 mission install
Step 2   Growth Ledger synthesis
Step 3   Growth Ledger kickoff
Step 4   Growth Ledger corrigenda
Step 5   Growth Ledger catalog patch plan
Step 6   Review Gate A — Growth Ledger implementation
Step 7   Apply accepted Growth Ledger implementation, if approved
Step 8   Growth Ledger behavior report
Step 9   Growth Ledger findings / triage
Step 10  Final Phase 3.13 audit
Step 11  Final PR preparation
```

Every step that lands files must pass the standard preflight gates before commit and must push the campaign branch on success:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

---

## ChatGPT/Codex consultation policy (Stage A bridge)

The repository now contains an explicit, read-only Claude → Codex CLI → ChatGPT advisory bridge (`/ask-chatgpt`; wrapper `tools/claude_helpers/codex_chatgpt_subagent.py`). Use it as advisory only, at high-leverage points. The full bridge policy lives in `CURRENT_MISSION.md`. This file restates only what each step must do.

When a step uses the bridge:

```text
- use the wrapper or /ask-chatgpt slash command, never raw codex
- use only Stage A modes: plan / review / summarize / debug
- use --model gpt-5.5 unless the operator approves another model in-session
- write the question to /tmp/toyi_chatgpt_<stepid>_question.md
- write the wrapper output to /tmp/toyi_chatgpt_<stepid>_answer.md
- the wrapper's hash-only audit JSONL lands under .claude/codex_bridge_logs/
  (gitignored); do not commit those logs
- treat repo-local files, gates, and invariants as authoritative if they
  conflict with ChatGPT advice
```

Every step report must include this disclosure block:

```text
ChatGPT/Codex consultation:
- used:           yes / no
- mode:           plan / review / summarize / debug / n/a
- model:          gpt-5.5 / n/a
- effort:         low / medium / high / n/a
- wrapper command: <full command or n/a>
- question file:   <path or n/a>
- answer file:     <path or n/a>
- wrapper status:  <exit code + error class or n/a>
- accepted advice: <bullets or none>
- rejected advice: <bullets or none>
- reason:          <one sentence>
```

---

# Step 1 — Repo-state sync and Phase 3.13 mission install

Purpose: replace stale Phase 3.12 mission/campaign routing prose and install Phase 3.13 as current, with the Phase 3.13 Growth Ledger roadmap landed at repo root.

Allowed files:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
PHASE3_13_GROWTH_LEDGER_ROADMAP.md
```

Forbidden in Step 1:

```text
brain/**
tools/**
.claude/**
INVARIANT_CATALOG.md
README.md  (unless a preflight reference is broken; stop and report first)
docs/campaigns/**
lean_reference/**
scenarios/**
traces/**
no fixtures
no code
```

Required work:

```text
sync fresh main and create branch campaign/phase3-13-growth-ledger
run all preflight gates green
write Phase 3.13 CURRENT_MISSION.md
write Phase 3.13 CURRENT_CAMPAIGN.md
create PHASE3_13_GROWTH_LEDGER_ROADMAP.md at repo root with the ten
  required sections enumerated in the mission spec (purpose, baseline,
  why Growth Ledger before SelfModel, operational definition, candidate
  event types, guardrails, initial policy recommendation, ChatGPT/Codex
  consultation policy, non-goals, next artifact)
run a Stage A /ask-chatgpt advisory smoke against gpt-5.5 / plan / low;
  the smoke is non-blocking — record wrapper status either way
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
git status --short
git diff -- CURRENT_MISSION.md CURRENT_CAMPAIGN.md PHASE3_13_GROWTH_LEDGER_ROADMAP.md
```

Commit message:

```text
phase3.13 step1: growth ledger mission sync
```

Push.

---

# Step 2 — Growth Ledger synthesis

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_SYNTHESIS.md
```

Required content:

```text
why Phase 3.13 follows Phase 3.12 (Pattern Ledger + Coherence Monitor
  already shipped; Growth Ledger is the next bounded substrate; SelfModel
  remains deferred)
operational definition of Growth Ledger / growth event / accepted /
  references / provenance / saturation
record shape proposal (frozen / slotted dataclass; bounded printable
  event_id != COGITO_ID; closed event_type enum; non-negative int tick;
  closed source enum; tuple of bounded references; bounded provenance)
event vocabulary (the candidate list from CURRENT_MISSION.md; mark each
  as "in v1" / "deferred" with reason)
integration points (dispatchers that already expose the outcome-detection
  contract; one observe(...) call site per integration; no observe on
  read-only commands; no observe on parse / dispatch / tick failure)
copy-on-write ledger discipline (observe returns a NEW GrowthLedger)
anti-Goodhart deduplication and saturation rule (final value picked here,
  including behavior at cap)
bounds (GROWTH_LEDGER_MAX_EVENTS; per-event-type caps if any)
event id scheme (deterministic sha256-based, OR monotone "grow-N";
  synthesis locks one)
non-claims (every forbidden term inherited from I-COHMON-11 stays
  forbidden; no aggregate growth scalar; no SelfModel)
ChatGPT/Codex consultation disclosure block
next artifact: kickoff
```

Commit message:

```text
phase3.13 step2: growth ledger synthesis
```

Push.

---

# Step 3 — Growth Ledger kickoff

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_KICKOFF.md
```

Required content:

```text
implementation surface: one new module brain/development/growth_ledger.py
proposed OperatorSession integration (one new optional field;
  membership in _ALLOWED_SESSION_ATTRS; resource-free guarantee)
proposed _PHASE_3_13_SESSION_ATTRS tier in the persistence resource-audit
  fixtures, if the synthesis locks a session field (mirrors Phase 3.12c
  Step 11 precedent for Pattern Ledger; otherwise skip)
proposed observe(...) call sites by dispatcher name (e.g. end of
  successful path of _dispatch_stream_append, _dispatch_stream_promote,
  _dispatch_step, _dispatch_save_session, _dispatch_load_session,
  build_full_coherence_report)
explicit non-integration list (offline-default unchanged; tick() body
  unchanged; LLM client unchanged; DB schema unchanged; autosave trigger
  set unchanged; Pattern Ledger / Coherence Monitor identity-stable)
allowed imports (closed set, mirrors Pattern Ledger / Coherence Monitor
  patterns)
forbidden imports / forbidden calls / forbidden runtime resources
ChatGPT/Codex consultation disclosure block
next artifact: corrigenda
```

Commit message:

```text
phase3.13 step3: growth ledger kickoff
```

Push.

---

# Step 4 — Growth Ledger corrigenda

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CORRIGENDA.md
```

Required content:

```text
resolve every open design decision still open at kickoff time
LOCK statements (mirror Phase 3.12c Pattern Ledger LOCK A..F precedent):
  - LOCK A: session-local-only in v1 (no persistence)
  - LOCK B: dispatch-time observe; no status-string parsing
  - LOCK C: event id scheme (sha256-based OR monotone)
  - LOCK D: deduplication / saturation rule with concrete cap
  - LOCK E: behavior at GROWTH_LEDGER_MAX_EVENTS (proposed: hard refusal
    of new events; mirror Pattern Ledger LOCK E)
  - LOCK F: SESSION_SAVED / SESSION_LOADED inclusion decision
ChatGPT/Codex consultation disclosure block
next artifact: catalog patch plan
```

Commit message:

```text
phase3.13 step4: growth ledger corrigenda
```

Push.

---

# Step 5 — Growth Ledger catalog patch plan

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_CATALOG_PATCH_PLAN.md
```

Required content:

```text
proposed row family: I-GROW-*
exact row-by-row status assignment
  (REQUIRED / STRUCTURAL / DEFERRED / NOT-EXERCISED / OBSERVED)
exact catalog version bump (v0.22 -> v0.23)
exact count delta (REQUIRED += n, STRUCTURAL += n, DEFERRED += n,
  NOT-EXERCISED += n, OBSERVED += n)
fixture list (one fixture per row family discipline; constructor /
  copy-on-write / observe / static-AST audit / runtime no-coupling /
  resource-free record / non-claim audit)
explicit non-rows (every cognitive-layer claim that Phase 3.13 does NOT
  authorize, inherited from the Phase 3.12 Step 15 roadmap's non-goals)
ChatGPT/Codex consultation disclosure block
next artifact: Review Gate A
```

Stop at the next review gate.

Commit message:

```text
phase3.13 step5: growth ledger catalog patch plan
```

Push.

---

# Step 6 — Review Gate A — Growth Ledger implementation

Stop unless the operator explicitly chooses one:

```text
[ ] ACCEPT PLAN AS WRITTEN
[ ] ACCEPT WITH AMENDMENTS (operator lists the amendments)
[ ] REJECT / REVISE (no implementation; return to Step 5)
```

No source-code changes are allowed before this gate clears.

---

# Step 7 — Apply accepted Growth Ledger implementation, if approved

Allowed files depend on the accepted plan. Likely set:

```text
brain/development/growth_ledger.py                              (new)
brain/ui/session.py                                             (narrow extension)
brain/ui/fixtures/<growth ledger fixtures listed in Step 5>    (new)
brain/invariants.py                                             (FIXTURE_MODULES extension)
tools/catalog.py                                                (EXPECTED_COUNTS banner update)
INVARIANT_CATALOG.md                                            (new v0.23 banner + I-GROW-* rows)
README.md                                                       (catalog version + counts string)
CURRENT_MISSION.md                                              (catalog version + counts string)
CURRENT_CAMPAIGN.md                                             (catalog version + counts string)
```

No implementation is authorized by this campaign text alone. The exact file set comes from the Step 5 catalog patch plan amended by the Step 6 gate.

Run every preflight gate green. Commit and push.

---

# Step 8 — Growth Ledger behavior report

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_BEHAVIOR_REPORT.md
```

Required content:

```text
measurement-first walk over the existing safe operator route
  (/stream -> /stream-promote -> /step), now observed through the
  Growth Ledger
event-type-by-event-type record of what fired and what did not
anti-Goodhart spam test (same input repeated; ledger must saturate or
  refuse)
no-mutation verification (Pattern Ledger / Coherence Monitor records
  identity-stable; BrainState identity-stable across observe calls;
  autosave trigger set unchanged)
ChatGPT/Codex consultation disclosure block
next artifact: findings / triage
```

Commit message:

```text
phase3.13 step8: growth ledger behavior report
```

Push.

---

# Step 9 — Growth Ledger findings / triage

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_FINDINGS.md
```

Required content:

```text
bugs / regressions observed in Step 8 (if any)
operator UX surprises (if any)
proposed deferred follow-ups
explicit list of items that DO NOT block this campaign
ChatGPT/Codex consultation disclosure block
next artifact: final audit
```

Commit message:

```text
phase3.13 step9: growth ledger findings
```

Push.

---

# Step 10 — Final Phase 3.13 audit

Create:

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_AUDIT.md
```

Validation:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Required content:

```text
PASS verdict (or FAIL with reason)
files changed across the campaign
gate results
explicit "no SelfModel implementation" confirmation
explicit "no consciousness / sentience / subjective / semantic / truth /
  agency / self-modification claim" confirmation
explicit "no aggregate growth / I-ness score" confirmation
explicit "no hidden LLM call / hidden persistence / DB schema change in
  v1" confirmation
explicit "Stage A /ask-chatgpt bridge usage, if any, is recorded" with
  per-step disclosure links
next-campaign note (SelfModel remains deferred; promote only after a
  follow-up campaign that explicitly accepts the SelfModel plan)
ChatGPT/Codex consultation disclosure block
```

Commit message:

```text
phase3.13 step10: final growth ledger audit
```

Push.

---

# Step 11 — Final PR preparation

Open a PR to main with title:

```text
phase3.13: growth ledger
```

PR body must include:

```text
completed steps
validation results
behavior findings summary
review gates reached
implementation, if any
remaining deferred work (SelfModel; /pattern-ledger UI; /coherence-summary UI;
  end-to-end dry runs)
confirmation main was not pushed directly during campaign execution
confirmation PR is not merged
Stage A /ask-chatgpt consultation summary across the campaign
```

Do not merge.
