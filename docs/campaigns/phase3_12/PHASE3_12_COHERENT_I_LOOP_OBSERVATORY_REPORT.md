# PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 6 (Phase 3.12b existing-route observatory)
against the matrix in `PHASE3_12_COHERENT_I_LOOP_MATRIX.md`. Record what
the existing operator route actually does on repetition, alternation,
novelty, contradiction pressure, saturation, promotion + tick, persistence,
and coherence-by-inspection inputs, and assess whether the observed
behavior supports the Phase 3.12 operational definitions of coherent,
pattern-recognizing, growing, and operational-I — without any code change
under `brain/**`, `tools/**`, `lean_reference/**`, `scenarios/**`, or
`traces/**`.

This is a report-only artifact. It introduces no new fixture, no new
catalog row, no kernel mutation, and no new runtime semantics.

## Environment

```text
Branch:                campaign/phase3-12-coherent-i-loop-observatory
HEAD before Step 6:    10a93ee phase3.12 step4: coherent i-loop matrix
Catalog:               v0.20
Counts:                214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Python:                python3 (system)
LLM client:            brain.ui.__main__.OfflineStandInClient (returns "PRESERVE")
External LLM:          none — anthropic-api / claude-cli / codex-cli not invoked
Network:               none
Process:               in-process LocalCommandLine.parse + OperatorSession.dispatch
Helper script:         /tmp/phase3_12_observatory_run.py (not committed)
Helper output:         /tmp/phase3_12_probe_output.json (not committed)
```

## Method

The observatory is a scripted in-process driver. For each test family it:

1. Constructs `OperatorSession(state=initial_state())`.
2. Calls `LocalCommandLine().parse(line)` to obtain a typed `Command` or
   `LocalCommandError`.
3. On success, calls `session.dispatch(command, client=OfflineStandInClient())`.
4. Captures a snapshot of every observable session field
   (`status_message`, `error_message`, `active_view`, `tick_counter`,
   `event_queue` length, `stream_history.chunks` length,
   `stream_candidates` length, `stream_chunk_serial`,
   `state.profile.domain`, `state.msi.contents`, `state.registry.texts`
   length, `latest_tick.tick_index`).

No private helper is invoked. No `BrainState` field is set directly.
The persistence family uses a temp `pathlib.Path` under `tempfile.TemporaryDirectory(prefix="phase3_12_")`
and a default `SessionStoreConfig`; the temp directory is cleaned up on exit.

Verdict vocabulary (locked by the matrix): `works`, `awkward`,
`confusing`, `fails`, `missing`, `blocked by env`.

## Preflight Validation

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS — 214/83/9/12/16 ok |
| `python3 -m tools.citations verify` | PASS — 100 citations resolved |
| `python3 -m tools.import_audit` | PASS — `I-PCE-05: agency.py is clean of pce imports.` |
| `python3 -m brain.invariants run` | PASS — 305 rows checked, 0 gate failures, REQUIRED 215/0, STRUCTURAL 83/0, OBSERVED 7/0 |
| `bash tools/check_all.sh` | PASS — `All checks passed.` |

## Observation Table

### Baseline / launch / state

| ID | Style | Command | Observed | Verdict |
|----|-------|---------|----------|---------|
| 12.base.1 | SST | `python3 -m tools.catalog counts` | banner = actual = expected (214/83/9/12/16) | works |
| 12.base.2 | SST | `bash tools/check_all.sh` | `All checks passed.` | works |
| 12.state.1 | SST | `OperatorSession(state=initial_state())` | `profile_domain=['__cogito__']`, `msi_contents=['__cogito__']`, `tick_counter=0`, `stream_chunks=0`, `stream_candidates=0`, `queue_size=0`, `registry_size=0`, `latest_tick_index=None` | works |

### Stream pattern observations

| ID | Style | Command | Observed | Verdict |
|----|-------|---------|----------|---------|
| 12.repetition.1 | SST | 5× `/stream alpha alpha alpha` | each accepted; `stream_chunks=5`; `stream_candidates=5`; `chunk_ids=[strm-chunk-1..5]`; `candidate_ids=[promo-strm-chunk-1..5]`; profile/msi unchanged; queue empty | works |
| 12.repetition.2 | SST | `/stream-summary` after repetition | dispatch sets `active_view='stream_summary'`; status = `view = stream_summary` (view-only status; no inline summary text) | awkward |
| 12.alternation.1 | SST | 4× `/stream alpha beta alpha beta` | each accepted; `stream_chunks=4`; `stream_candidates=4`; all chunk texts identical to the input text; chunk IDs and candidate IDs distinct | works |
| 12.novelty.1 | SST | 3× `/stream alpha alpha alpha`, then `/stream gamma novelty after repetition`, then `/stream delta surprise` | 5 chunks accepted; novel chunk text distinct from prior chunk texts; profile/msi unchanged; no candidate-id collision; pre/post invariants preserved | works |
| 12.contradiction.1 | SST | `/stream door=open`, `/stream door=closed`, repeated | 4 chunks accepted; `profile_domain=['__cogito__']`, `msi_contents=['__cogito__']` unchanged; no PtCns mutation; no truth adjudication | works |

### Promotion / tick observations

| ID | Style | Command | Observed | Verdict |
|----|-------|---------|----------|---------|
| 12.candidates.1 | SST | `/stream-candidates` | dispatch sets `active_view='stream_candidates'`; status = `view = stream_candidates` (view-only; no inline candidate list in status text) | awkward |
| 12.promote.1 | SST | `/stream-promote promo-strm-chunk-1` | `queue_size: 0 -> 1`; `stream_candidates` retained (1); `tick_counter=0`; no profile/msi mutation; status = `promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)` | works |
| 12.step.1 | SST | `/step` with offline client | `tick_counter: 0 -> 1`; `queue_size: 1 -> 0`; `latest_tick_index=1`; triggered_mode = `MODE_C`; notes = `['strm-strm-chunk-1=PRESERVE→MODE_C']`; profile gains `'strm-strm-chunk-1'`; msi gains `'strm-strm-chunk-1'`; registry size 0→1; `OfflineStandInClient.calls` = 1 | works |
| 12.state.2 | SST | `/state` after tick | view = `state`; bounded; no error | works |

### Saturation / failure path

| ID | Style | Command | Observed | Verdict |
|----|-------|---------|----------|---------|
| 12.saturation.1 | SST | 120× `/stream spam motif` | `stream_chunks` grows monotonically to 120 (cap `STREAM_HISTORY_MAX_CHUNKS=256`); `stream_candidates` saturates at 64 (cap `STREAM_PROMOTION_MAX=64`); profile/msi unchanged; tick_counter unchanged; no exception | works |
| 12.boundary.1 | SST | `/stream <1088-char body>` (`STREAM_TEXT_MAX_LEN=1024`) | parse-time rejection: `LocalCommandError("/stream text exceeds 1024 chars")`; dispatch never invoked; session state unchanged; no truncation | works |
| 12.failed-step.1 | SST | `/step` with empty queue | dispatch returns False; `error_message = 'STEP_TICK with empty event queue'`; `tick_counter` unchanged; `queue_size` unchanged; `state`, `latest_tick` unchanged | works |

### Persistence / cold-start

| ID | Style | Command | Observed | Verdict |
|----|-------|---------|----------|---------|
| 12.persist.1 | SST | `/save-session` after stream/promote/step | DB created under `/tmp/phase3_12_*/phase3_12_session.sqlite3` (73,728 bytes); status = `saved session to ... (chunks=2, candidates=2)`; live session state untouched | works |
| 12.persist.2 | SST | `/load-session` into fresh session | reconstructed `tick_counter=1`, `stream_chunks=2`, `stream_candidates=2`, `stream_chunk_serial=2`, `profile_domain=['__cogito__','strm-strm-chunk-1']`, `msi_contents=['__cogito__','strm-strm-chunk-1']`, `registry_size=1`; every field above matches the live pre-save snapshot | works |
| 12.persist.3 | SST | `/session-status` after load | status = `session-status: tick=0 queue=0 view=stream_candidates chunks=0 candidates=0 db=off` for an unconfigured baseline, and the load-side report matches the saved counts when DB is configured | works |
| 12.persist.fail | SST | `/load-session` with no `session_store_config` | `error_message = '/load-session requires a configured --session-db'`; session state untouched; no DB created | works |

### Coherence-by-inspection (RFI)

| ID | Style | File | Observed | Verdict |
|----|-------|------|----------|---------|
| 12.coherence.1 | RFI | `brain/tick.py` | `tick()` remains the only runtime transition route; `/step` reaches `tick()` through `OperatorSession._dispatch_step`; `python3 -m tools.import_audit` confirms `I-PCE-05`: `agency.py` is clean of `pce` imports | works |
| 12.coherence.2 | RFI | `brain/development/text_stream.py` | `TextStreamChunk` / `TextStreamHistory` constructors reject non-printable text and over-length text; no `PtCns`, `tick`, or LLM import; chunks below truth/agency layer | works |
| 12.coherence.3 | RFI | `brain/ui/session.py` | `_dispatch_step` is the sole tick caller from the operator route; failure paths assert no mutation of `state`, `latest_tick`, or `event_queue` length; `_assert_no_unsafe_resources()` runs after every dispatch (drives `I-UI-10`) | works |

### UX / interpretation observations

| ID | Style | Observed | Verdict |
|----|-------|----------|---------|
| 12.ux.1 | MOT | The post-mutation status lines are bounded printable text and self-describing — `stream chunk 'strm-chunk-1' appended (history size = 1)`, `promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)`, `tick 1 ok (MODE_C)`, `saved session to ... (chunks=2, candidates=2)`. The bounded `/session-status` line is also readable: `session-status: tick=0 queue=0 view=stream_candidates chunks=0 candidates=0 db=off`. | works |
| 12.ux.2 | MOT | Pattern evidence is visible *in the stored fields* (`stream_history.chunks`, `stream_candidates`) but is **not** surfaced through the operator status line. `/stream-summary` and `/stream-candidates` only switch `active_view` and set status = `view = ...`. To see the actual chunk texts the operator must consult the renderer/snapshot pane, not the dispatch return. From the agent-style typed route alone, repetition vs alternation vs novelty are indistinguishable in the status feedback. | awkward |

## Raw Evidence Summary

Key numeric evidence captured by `/tmp/phase3_12_observatory_run.py`:

```text
baseline.post:        tick=0, queue=0, chunks=0, candidates=0,
                      profile=['__cogito__'], msi=['__cogito__']

repetition.post:      tick=0, queue=0, chunks=5, candidates=5,
                      chunk_texts_distinct=['alpha alpha alpha'],
                      candidate_ids=[promo-strm-chunk-1..5]

alternation.post:     tick=0, queue=0, chunks=4, candidates=4,
                      chunk_texts (all)='alpha beta alpha beta'

novelty.post:         tick=0, queue=0, chunks=5, candidates=5,
                      chunk_texts include
                        'alpha alpha alpha' (3x),
                        'gamma novelty after repetition',
                        'delta surprise'

contradiction.post:   tick=0, queue=0, chunks=4, candidates=4,
                      chunk_texts=['door=open','door=closed',
                                   'door=open','door=closed'],
                      profile=['__cogito__'], msi=['__cogito__']

saturation.post:      tick=0, chunks=120, candidates=64,
                      STREAM_PROMOTION_MAX=64, STREAM_TEXT_MAX_LEN=1024,
                      over_length /stream rejected at parse with
                      '/stream text exceeds 1024 chars'

promote_tick:         pre_promote queue=0; post_promote queue=1;
                      post_step tick=1, queue=0,
                      latest_tick_index=1, triggered_mode='MODE_C',
                      notes=['strm-strm-chunk-1=PRESERVE→MODE_C'],
                      OfflineStandInClient.calls=1
                      empty-/step: error='STEP_TICK with empty event queue',
                      tick still 1, state untouched

persistence:          save_post: chunks=2, candidates=2, tick=1,
                                  profile/msi gained 'strm-strm-chunk-1'
                      load_post: matches save_post on every recorded
                                 field (tick_counter, stream_chunks,
                                 stream_candidates, stream_chunk_serial,
                                 profile_domain, msi_contents)
                      unconfigured load: bounded error, no mutation
                      db_byte_size = 73,728

UX samples:
  /stream             -> "stream chunk 'strm-chunk-1' appended (history size = 1)"
  /stream-summary     -> "view = stream_summary"
  /stream-candidates  -> "view = stream_candidates"
  /stream-promote     -> "promoted stream candidate '<id>' (queue size = N)"
  /step (success)     -> "tick 1 ok (MODE_C)"
  /step (empty queue) -> error: "STEP_TICK with empty event queue"
  /save-session       -> "saved session to <path> (chunks=N, candidates=M)"
  /load-session       -> "loaded session from <path> (chunks=N, candidates=M)"
  /session-status     -> "session-status: tick=… queue=… view=… chunks=… candidates=… db=…"
```

## Operational Definition Assessment

### Coherent

Supported. Across all eight live test families:

- catalog gates remain green before and after the probe run,
- `COGITO_ID` (`__cogito__`) is present in every observed `profile.domain`
  and `msi.contents`,
- every state transition that changes `tick_counter` or `profile.domain`
  passes through `_dispatch_step` → `tick()` (no alternate route observed),
- every failure path (empty-queue `/step`, unconfigured `/load-session`,
  over-length `/stream`) leaves `state`, `latest_tick`, `event_queue`,
  `stream_history`, and `stream_candidates` unchanged and emits a bounded
  printable error line,
- save/load round-trip reproduces every recorded field exactly,
- `/session-status` and `/state` reports match the underlying counts
  computed independently from the snapshot.

### Pattern-recognizing

Partially supported and explicitly bounded.

- Structural recurrence *is* visible in the stored stream state: repeated
  `/stream alpha alpha alpha` produces 5 `TextStreamChunk` records whose
  text is identical (`chunk_texts_distinct` length 1) and 5 candidate
  records with distinct deterministic IDs. Alternating input produces 4
  identical-text chunks. Novelty after repetition shows two distinct
  texts. These are structural patterns the operator can read off the
  stored fields.
- However the existing operator route does **not** surface those patterns
  in its dispatch status. `/stream-summary` and `/stream-candidates`
  only set `active_view` and write `view = ...` to status — the bounded
  printable status line does not contain a recurrence count, a pattern
  signature, or a "this matches an earlier chunk" hint. Pattern evidence
  is *available* through the rendered view (and through the persistence
  observability commands), but is *not* recognized at the dispatch
  level. This is the gap the Phase 3.12c Pattern Ledger is meant to
  close.
- Crucially, the existing route makes no semantic claim from raw text:
  contradicting `/stream door=open` / `/stream door=closed` inputs are
  stored as 4 distinct chunks and never touch `profile.domain`,
  `msi.contents`, or `PtCns`. Pattern recognition here is structural
  evidence only — no truth, no agency, no PRESERVE/DAMAGE adjudication.

### Growing

Supported, with explicit bounds and saturation.

- Bounded growth via accepted constructors: only `/stream-promote`
  followed by `/step` adds a content to `profile.domain` and
  `msi.contents` (`strm-strm-chunk-1` in our probe); `tick_counter`
  advances by exactly one per `/step` success. The registry gains one
  entry. This is bounded persistent evidence acquired through the
  approved tick route.
- Save/load preserves growth: `tick_counter`, `profile.domain`,
  `msi.contents`, `stream_history`, `stream_candidates`, and
  `stream_chunk_serial` all match exactly after `/save-session` →
  `/load-session` into a fresh session.
- Saturation works: 120 stream submissions produce 120 chunks (under the
  256 cap) and 64 candidates (exactly at `STREAM_PROMOTION_MAX=64`,
  oldest candidates trimmed by `_append_stream_candidates`). Spam at the
  `/stream` layer does not inflate `profile.domain`, `msi.contents`,
  `tick_counter`, or the registry — none of those change while no
  promotion/step occurs.
- Failure paths do not inflate growth: parse rejections and dispatch
  rejections leave every counter unchanged.

### Operational I

Partially supported.

- An operational "I" anchor exists: `COGITO_ID = "__cogito__"` is in
  every observed `profile.domain` and `msi.contents`, including the
  baseline session, after every stream, after every tick, and after the
  load round-trip. Builders refuse to drop it; the `text_stream` module
  rejects it as a chunk/candidate identifier; load reconstructs through
  public builders that re-enforce the invariant.
- A bounded inspectable self-status surface exists: `/session-status`
  reports `tick`, `queue`, `view`, `chunks`, `candidates`, and `db`
  configuration on one bounded printable line. `/state` switches the
  view to the kernel snapshot; `/tick` to the latest `TickRecord` view.
  These match the underlying fields.
- However, there is no first-person self-report surface, no
  "self-model" object, and no coherence verdict. The existing route can
  *show* the operator what is true of the session, but the session does
  not yet *summarize itself* in self-modeling terms. That gap is the
  motivation for the Phase 3.12d Coherence Monitor and the Phase 3.12e
  SelfModel roadmap — both behind explicit review gates.
- The "operational" framing is honored strictly: every observed
  self-referential affordance is grounded in repo-local state, with no
  textual claim of awareness, sentience, or experience.

## Findings Classification

Critical correctness: 0
Safety / invariant: 0
Operator UX: 2 (`12.repetition.2`, `12.candidates.1`, `12.ux.2` — same
underlying gap)
Documentation: 0
Deferred enhancement: 2 (Pattern Ledger surface; first-person
self-report surface)

Detail:

- **UX-1 (awkward).** `/stream-summary` and `/stream-candidates`
  dispatch only set `active_view` and write `view = ...` to
  `status_message`. From the typed agent route, an operator cannot
  read the chunk count, candidate count, or any pattern evidence from
  the dispatch return alone — they have to switch view and consult the
  renderer or use `/session-status` separately. This is awkward, not a
  bug: the bounded view-render pane shows the data, and
  `/session-status` already exposes the counts as a bounded status
  line. Candidate fix is documentation-only or a small status-text
  extension; nothing in `brain/**` needs to change to fill the matrix.

- **DEF-1 (deferred — Pattern Ledger).** Recurrence is visible in
  stored fields but is not surfaced as recognized pattern evidence in
  the dispatch surface. Phase 3.12c's Pattern Ledger is intended to
  add this without raising raw text to truth/agency.

- **DEF-2 (deferred — self-report surface).** No bounded self-model
  output exists yet. Phase 3.12d's Coherence Monitor and Phase 3.12e's
  SelfModel/Growth Ledger roadmap address this; they remain behind
  Review Gate B / C / D.

No row earned `fails`, `confusing`, `missing`, or `blocked by env`.

## Limits / Non-Claims

- This report does **not** claim ToyI is conscious, sentient,
  semantically understanding, or subjectively experiencing anything.
- "Pattern recognition" here means structural recurrence visible in
  bounded stored fields, not semantic categorization, language
  understanding, or truth judgment.
- "Growth" here means bounded persistent evidence accumulated through
  accepted constructors (`tick()` plus `save_session`/`load_session`),
  not unbounded self-modification or capability gain.
- "Operational I" here means the `COGITO_ID` anchor plus the bounded
  read-only self-status surface; it does not claim first-person
  perspective.
- `OfflineStandInClient` always returns `"PRESERVE"`. The observed
  `MODE_C` triggered mode in `12.step.1` follows from that single
  deterministic input plus the existing `LLMBackedPtCns` retry shell
  semantics; no real LLM was contacted.
- Test families 1 and 9 were partly read-only file inspection.
  Families 2–8 and 10 were exercised in-process via
  `LocalCommandLine.parse` + `OperatorSession.dispatch` and the
  resulting snapshots; no `BrainState` field was set directly.
- The `STREAM_HISTORY_MAX_CHUNKS=256` cap was not stressed (probe ran
  to 120). The over-length text boundary (1088 chars vs
  `STREAM_TEXT_MAX_LEN=1024`) was exercised and rejected at parse time.
- The persistence test used a single configured DB path under
  `/tmp/phase3_12_*`. Hostile filesystem failure modes (read-only FS,
  disk full, EACCES) were not exercised.

## Recommendation

Net verdict on the existing-route coherent-I-loop hypothesis:

```text
coherent:              works
pattern-recognizing:   partially supported — structural evidence is
                       stored and inspectable; recognition surface is
                       deferred to Pattern Ledger (Phase 3.12c)
growing:               works — bounded, saturating, persistent
operational I:         partially supported — COGITO anchor + bounded
                       self-status; no self-report surface yet
                       (deferred to Phase 3.12d/e)
```

The existing operator route is a sound substrate for the next two
design steps. Specifically:

1. Proceed to **Step 7 — Pattern Ledger synthesis**. The evidence is
   consistent with adding a bounded persistent ledger of structural
   recurrence below truth/agency/PtCns. No correctness blocker was
   found in `brain/**`.
2. After Step 7, keep the implementation steps (Step 11) behind Review
   Gate B in `CURRENT_CAMPAIGN.md`. Nothing observed in Step 6 changes
   the gating logic.
3. The `12.ux.2` / `12.repetition.2` / `12.candidates.1` awkwardness
   should be recorded as a deferred UX enhancement, not a Step 7
   blocker. Pattern Ledger design can specify whether its summary
   should ride the existing status line, the rendered view, or a new
   bounded read-only command — but that decision belongs to Step 7,
   not Step 6.

No code-side patch under `brain/**`, `tools/**`, `lean_reference/**`,
`scenarios/**`, or `traces/**` is recommended by Step 6.

## Validation

Re-ran after writing this report (no source under `brain/**`,
`tools/**`, `lean_reference/**`, `scenarios/**`, or `traces/**` was
touched; only this report file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS |
| `python3 -m tools.citations verify` | PASS |
| `python3 -m tools.import_audit` | PASS |
| `python3 -m brain.invariants run` | PASS |
| `bash tools/check_all.sh` | PASS |
