# PHASE3_13_GROWTH_LEDGER_ROADMAP.md

## 1. Purpose

Phase 3.13 starts from the archived Phase 3.12 SelfModel / Growth Ledger
roadmap and implements **Growth Ledger first**. Operational SelfModel is
explicitly out of scope for this campaign.

Canonical design seed:

```text
docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
```

That seed is treated as the authoritative design source for Growth Ledger
and SelfModel. This roadmap restates only what Phase 3.13 must do, what it
must not do, and how it must consult ChatGPT / Codex.

This is a roadmap artifact. It does not authorize implementation of either
Growth Ledger or Operational SelfModel by itself. Implementation is gated
behind the Step 6 Review Gate A in `CURRENT_CAMPAIGN.md`. This file does
not edit `brain/**`, `tools/**`, `INVARIANT_CATALOG.md`, `README.md`,
`docs/campaigns/**`, `lean_reference/**`, `scenarios/**`, `traces/**`,
or any `.claude/**` file. It changes runtime behavior in no way.

## 2. Baseline

```text
Catalog version:                  v0.22
Counts:
  REQUIRED:                       240
  STRUCTURAL:                      85
  NOT-EXERCISED:                   11
  DEFERRED:                        14
  OBSERVED:                        16
Branch:                           campaign/phase3-13-growth-ledger
Phase 3.12:                       complete; PR #11 merged
docs cleanup:                     complete; PR #12 merged
ChatGPT/Codex Stage A bridge:     shipped; PR #13 merged
Existing bounded substrates:
  Pattern Ledger                  brain/development/pattern_ledger.py
                                  I-PLEDGER-01..18  (catalog v0.21)
  Coherence Monitor               brain/development/coherence_monitor.py
                                  I-COHMON-01..14   (catalog v0.22)
Canonical Phase 3.13 design seed:
  docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md
Active Stage A advisory bridge:
  /ask-chatgpt   (.claude/commands/ask-chatgpt.md)
  wrapper        (tools/claude_helpers/codex_chatgpt_subagent.py)
  bridge audit   (CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md)
  audit JSONL    (.claude/codex_bridge_logs/, gitignored)
```

Preflight verified at the start of Phase 3.13 Step 1:

```text
python3 -m tools.catalog counts     PASS  (240 / 85 / 11 / 14 / 16)
python3 -m tools.citations verify   PASS  (100 citations resolved)
python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
python3 -m brain.invariants run     PASS  (333 rows; 0 gate failures)
bash tools/check_all.sh             PASS  (All checks passed.)
```

## 3. Why Growth Ledger before SelfModel

Three bounded substrates already exist or are scheduled:

```text
Pattern Ledger    bounded structural recurrence evidence over /stream history
Coherence Monitor bounded read-only structural consistency report
Growth Ledger     bounded historical accepted-event record (this campaign)
SelfModel         bounded read-only quotation summary  (FUTURE; not in Phase 3.13)
```

The Phase 3.12 Step 15 roadmap explains the ordering in detail; the
short form is:

- **Pattern Ledger** records structural recurrence (what has been seen
  and how often).
- **Coherence Monitor** records read-only structural consistency
  (whether the substrates still agree at one point in time).
- **Growth Ledger** records accepted growth events (what successfully
  happened, when, on which records).
- **SelfModel** later quotes facts from Pattern Ledger / Coherence
  Monitor / Growth Ledger. It does not invent growth itself.

A SelfModel that quotes "growth" from current state alone is unstable:
`tick_counter == 42` could mean 42 meaningful events or 42 empty-step
events, and cold-start sessions reset the counter. A Growth Ledger that
records accepted, constructor-validated events with outcome-detected
provenance gives a future SelfModel a stable factual surface to quote.

The dependency arrow points only one way:

```text
SelfModel  ->  Growth Ledger  ->  (Pattern Ledger, Coherence Monitor, kernel records)
```

None of the upstream substrates may depend on SelfModel. Growth Ledger
therefore does not depend on SelfModel either; it can ship first.

## 4. Growth Ledger operational definition

```text
Growth Ledger:
  a bounded developmental record of accepted, constructor-validated growth
  events produced by explicit successful runtime / developmental
  transitions.
```

Equivalent expansion:

- **bounded** — capped by `GROWTH_LEDGER_MAX_EVENTS` and per-event-type
  saturation. The behavior at cap is hard refusal of new events
  (mirroring Pattern Ledger LOCK E) unless the synthesis explicitly
  picks a different rule and the operator accepts it at the review
  gate.
- **developmental record** — copy-on-write history of `GrowthEvent`
  records. `observe(...)` returns a NEW `GrowthLedger`; the original
  `events` tuple is unchanged.
- **accepted** — the source dispatcher returned a positive outcome
  through the Phase 3.10c outcome-detection contract that already
  powers autosave. Failed parse, failed dispatch, failed tick, and
  read-only command do not count. Status / error string parsing is
  forbidden.
- **constructor-validated** — every `GrowthEvent` and every
  `GrowthLedger` mutation goes through a constructor that enforces
  bounded printable identifiers, `COGITO_ID` rejection on every
  id-bearing field, closed-enum membership, non-negative int counts,
  tuple references, and bounded provenance.
- **growth event** — one record with the seven required fields named
  in Section 6. Events store *references* to existing bounded records;
  they never store raw text payload.
- **explicit successful runtime / developmental transition** — the
  observe call site lives at the *end of the successful path* of an
  existing dispatcher / builder. The list of such call sites is
  fixed at synthesis time; new call sites are catalog-version-bump
  operations, not in-place edits.

## 5. Candidate event types

Initial event vocabulary (final names locked at the Step 2 synthesis):

```text
STREAM_CHUNK_ACCEPTED
PATTERN_ENTRY_CREATED
PATTERN_ENTRY_UPDATED
STREAM_PROMOTION_QUEUED
TICK_SUCCEEDED
PROFILE_DOMAIN_ADDED
MSI_MEMBER_ADDED
SESSION_SAVED
SESSION_LOADED
COHERENCE_REPORT_BUILT
```

Each candidate's `in-v1 / deferred` status is decided in the Step 2
synthesis and locked at Step 4 corrigenda LOCK F. Two notes carried
from the Phase 3.12 Step 15 roadmap:

- `SESSION_SAVED` / `SESSION_LOADED` raise an open question: a
  session-local-only Growth Ledger loses its `SESSION_LOADED` event on
  the very session that loads. The synthesis must pick and lock the
  inclusion rule.
- `COHERENCE_REPORT_BUILT` references the read-only diagnostic
  substrate but does not change it. The build callable already exists
  (`build_coherence_report(...)` / `build_full_coherence_report(...)`).

## 6. Growth Ledger guardrails

The Growth Ledger implementation, when it lands behind the Step 6
review gate, must respect every guardrail below. These guardrails
inherit from the Phase 3.12 Step 15 roadmap and from the existing
Pattern Ledger / Coherence Monitor discipline.

- **bounded max events.** `GROWTH_LEDGER_MAX_EVENTS` (proposed `1024`)
  caps the ledger. Behavior at cap is hard refusal of new events
  (LOCK E precedent) unless the synthesis explicitly picks a
  different rule and the operator accepts it at the review gate.
- **closed event enum.** `GrowthEventType` is a finite closed
  `(str, Enum)` class. Adding or removing a member is a
  catalog-version-bump operation, not an in-place edit.
- **exact event IDs.** Every `GrowthEvent.event_id` is bounded
  printable. Either deterministic
  `"grow:" + sha256(repr((event_type, references, tick))).hexdigest()[:16]`,
  or monotone session-local `"grow-N"`. The synthesis locks one and
  the corrigenda re-locks it.
- **references only, no raw text payload.** Events store bounded
  printable record ids (`chunk_id`, `candidate_id`, `pattern_id`,
  `snapshot_id`, autosave-status snapshot id) but never raw chunk
  text. The text already lives in the source histories; the Growth
  Ledger is a *referencing* layer.
- **no `COGITO_ID` as event id.** `event_id != COGITO_ID`. Every
  `references` element `!= COGITO_ID`. `provenance != COGITO_ID`.
- **no `BrainState` mutation.** Across every `observe(...)` call,
  `BrainState`, `MSI`, `PtCns`, `ContentRegistry`, `latest_tick`,
  `tick_counter`, source histories, `OperatorSession.event_queue`,
  `stream_history`, `stream_candidates`, `stream_chunk_serial`, the
  Pattern Ledger, the Coherence Monitor records, the persistence
  configuration, and the autosave configuration are identity-stable.
- **no `tick(...)` call inside Growth Ledger.** The Growth Ledger
  does not import `brain.tick` at runtime callable level; the
  `BrainState` typed record may be imported as a type only.
- **no LLM client.** No field stores or accepts an object with
  `eval_consistency`. The static AST audit must reject `brain.llm`
  imports.
- **no semantic / truth / agency / self-modification fields.** Every
  forbidden non-claim term enforced by `I-COHMON-11` stays forbidden
  in the Growth Ledger module surface and in every generated bounded
  printable string.
- **no persistence in v1 unless explicitly accepted at the review
  gate.** v1 Growth Ledger is session-local. `/save-session` does not
  serialize it; `/load-session` does not restore it;
  `_maybe_autosave_after_dispatch` is not extended. Any future
  persistence requires its own reviewed catalog patch.
- **no aggregate growth score in v1.** No field, method, or output is
  a scalar in `[0, 1]` / `[0, n]` purporting to summarize total
  growth. Per-event-type counts (deterministic tuple of
  `(event_type.value, count)` pairs, mirroring Coherence Monitor's
  `counts_by_status`) are allowed; aggregate scalars are not.
- **anti-Goodhart deduplication and saturation.** Re-recording the
  same `(event_type, references, tick)` triple is a no-op; the
  ledger does not double-count. Long runs of legitimate but
  low-information events must either be bounded by
  `GROWTH_LEDGER_MAX_EVENTS` (hard refusal at cap) or saturate at a
  per-event-type cap that the synthesis fixes explicitly.
- **copy-on-write history if modeled as a developmental substrate.**
  `GrowthLedger.observe(...)` returns a NEW ledger; the original
  `events` tuple is unchanged.
- **failed parse / dispatch / tick / read-only command do not count.**
  The outcome-detection contract is the canonical filter; no
  observe call may sit on a failure path or on a read-only verb.

## 7. Initial policy recommendation

Growth Ledger v1 should be **session-local first** — no DB schema
change, no `SCHEMA_VERSION_V*` bump, no `growth_events` table.

It should **observe accepted events in the same dispatcher outcome
discipline as autosave and Pattern Ledger**:

- only after a successful mutation,
- not after read-only commands,
- not after parse / dispatch / tick failures,
- not from status / error string parsing
  (the Phase 3.10c autosave contract is the precedent; parsing
  status strings violates `I-AUTOSAVE-14`'s outcome-detection rule).

Concretely, the v1 observe call sites should sit at the end of the
successful path of the dispatchers that already expose an outcome
boolean (or equivalent typed signal):

```text
_dispatch_stream_append    -> STREAM_CHUNK_ACCEPTED, PATTERN_ENTRY_CREATED,
                              PATTERN_ENTRY_UPDATED
_dispatch_stream_promote   -> STREAM_PROMOTION_QUEUED
_dispatch_step             -> TICK_SUCCEEDED, PROFILE_DOMAIN_ADDED,
                              MSI_MEMBER_ADDED
_dispatch_save_session     -> SESSION_SAVED (subject to LOCK F)
_dispatch_load_session     -> SESSION_LOADED (subject to LOCK F)
build_full_coherence_report-> COHERENCE_REPORT_BUILT
```

The synthesis must lock the exact set; this list is the recommended
default, not the final lock.

## 8. ChatGPT/Codex consultation policy

The repository ships an explicit Stage A Claude → Codex CLI → ChatGPT
advisory bridge:

```text
slash command:
  /ask-chatgpt --mode plan --model gpt-5.5 --effort low <prompt>

direct wrapper (policy boundary):
  python3 tools/claude_helpers/codex_chatgpt_subagent.py \
    --mode plan --model gpt-5.5 --effort low --timeout 120 \
    --prompt-file /tmp/toyi_chatgpt_<stepid>_question.md
```

The direct wrapper is the policy boundary. The Claude settings
allowlist contains only:

```text
Bash(python3 tools/claude_helpers/codex_chatgpt_subagent.py:*)
```

Strict prohibitions:

```text
do not invoke raw codex
do not invoke codex exec directly
do not add Bash(codex:*) allowlists
do not add Bash(codex exec:*) allowlists
do not use code mode (Stage A excludes code mode)
do not ask Codex to produce patches
do not apply Codex suggestions automatically
do not commit runtime audit JSONL under .claude/codex_bridge_logs/
  (gitignored by design)
```

Allowed Stage A modes:

```text
plan
review
summarize
debug
```

Preferred model:

```text
gpt-5.5
```

Reason: the real Stage A bridge smoke (recorded in
`CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md`) found `gpt-5.5` worked with
this ChatGPT-account Codex backend. Other tested names
(`gpt-5.1-codex`, `gpt-5`, `gpt-5-codex`, `gpt-5.1`, `o3`, `gpt-4o`)
were rejected by the backend with HTTP 400 as unsupported. Use a
different model only when the operator approves it in-session.

Effort guidance:

```text
low     quick smoke / sanity check
medium  normal review-gate critique
high    high-stakes row-family or invariant-boundary analysis
```

Use the bridge only at high-leverage points:

```text
row-family design
competing invariant choices
unresolved validation failure after local inspection
scope ambiguity
possible TLICA boundary violation
pre-review-gate adversarial check
pre-final-audit critique
```

Do not use the bridge for routine file reading, routine edits, routine
validation, or as a replacement for repo-local evidence.

**Stage A smoke during Step 1.** Step 1 runs a low-risk advisory
smoke after preflight, using the wrapper, not raw Codex. The
question file is `/tmp/toyi_chatgpt_step1_question.md`; the answer
file is `/tmp/toyi_chatgpt_step1_answer.md`. The wrapper writes a
hash-only audit JSONL record under `.claude/codex_bridge_logs/`
(gitignored). If the wrapper fails, Step 1 records the wrapper
status and error class and continues without blocking — the smoke
is non-blocking by design.

**Treat ChatGPT as advisory.** Claude remains the parent integrator.
Repo-local files, gates, and invariants override ChatGPT advice. If
ChatGPT advice conflicts with a repo-local constraint, report the
conflict and follow the repo.

**Disclose bridge usage in every step report** using the disclosure
block in `CURRENT_CAMPAIGN.md`:

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

## 9. Non-goals

Phase 3.13 must **not**:

- implement Operational SelfModel in any form,
- claim consciousness,
- claim sentience,
- claim subjective experience,
- claim semantic understanding,
- claim truth adjudication or assign `PRESERVE` / `DAMAGE` values to
  raw text,
- claim agency, intent, will, or desire,
- claim self-modification of code, fixtures, the catalog, or the
  runtime,
- introduce an aggregate consciousness score, sentience score,
  awareness score, "I-ness" score, growth score, or any single
  scalar purporting to summarize interior state,
- introduce a model-backed default (offline remains the default),
- emit any hidden LLM call,
- emit any hidden filesystem write, network call, subprocess spawn,
  or shell command,
- introduce hidden persistence outside the explicit
  `/save-session` / `/load-session` route (and that route is not
  extended in v1),
- change the DB schema in v1 (no `growth_events` table, no
  `SCHEMA_VERSION_V*` bump),
- extend the autosave trigger set in v1,
- run any real external LLM smoke beyond the sanctioned Stage A
  `/ask-chatgpt` bridge,
- count failed parse, failed dispatch, failed tick, or read-only
  command as growth,
- inflate growth on repeated spam (anti-Goodhart deduplication and
  saturation are mandatory),
- store raw text payload in any Growth Ledger field (events store
  references only),
- mutate `BrainState`, `MSI`, `PtCns`, `ContentRegistry`, source
  histories, `OperatorSession.event_queue`, `stream_history`,
  `stream_candidates`, `stream_chunk_serial`, the Pattern Ledger,
  the Coherence Monitor records, the persistence configuration,
  or the autosave configuration from any observe call,
- call `tick(...)` from any Growth Ledger code path.

These prohibitions inherit from `CURRENT_MISSION.md`,
`CURRENT_CAMPAIGN.md`, the Phase 3.12 Step 15 roadmap
(`docs/campaigns/phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md`),
the Phase 3.12 final audit
(`docs/campaigns/phase3_12/PHASE3_12_COHERENT_I_LOOP_AUDIT.md`),
and the existing `I-STRM-*` / `I-UISTRM-*` / `I-PERSIST-*` /
`I-OPSHARDEN-*` / `I-OBSERVE-*` / `I-AUTOSAVE-*` / `I-PLEDGER-*` /
`I-COHMON-*` discipline.

## 10. Next artifact

Step 2: `docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_SYNTHESIS.md`.

Until Step 6 Review Gate A explicitly accepts a catalog patch plan,
no file under `brain/**`, `tools/**`, `INVARIANT_CATALOG.md`,
`README.md`, `lean_reference/**`, `scenarios/**`, `traces/**`, or
`.claude/**` may be modified in pursuit of Growth Ledger
implementation. SelfModel remains explicitly out of scope for the
entire Phase 3.13 campaign and is not reconsidered before a separate
follow-up campaign.
