# PHASE3_13_GROWTH_LEDGER_BEHAVIOR_REPORT.md

## Purpose

This document is the Step 8 behavior report for Phase 3.13 Growth Ledger
v1. It measures the actual behavior of the Growth Ledger after the
Step 7 implementation landed `brain/development/growth_ledger.py`, the
`OperatorSession.growth_ledger` field, and the three dispatcher observe
call sites in `brain/ui/session.py`.

The report **does not change** code, catalog rows, fixtures, runtime
behavior, persistence, the UI surface, or the ChatGPT/Codex advisory
bridge. It is documentation only.

**Scope of claim.** All emission / non-emission findings below are
established through the existing safe operator route
(`/stream -> /stream-promote -> /step` plus the listed read-only verbs
and `build_full_coherence_report`), and through direct in-process
construction calls on `GrowthLedger` / `GrowthEvent`. They are observed
behavior over the tested scenarios in this report; they are **not**
universal proofs that no future call site can change the ledger. Every
finding below carries the route or surface it was observed on so the
reader can scope future regressions exactly.

## Baseline

```text
Catalog version:               v0.23
Counts:
  REQUIRED:                    259
  STRUCTURAL:                   86
  NOT-EXERCISED:                12
  DEFERRED:                     15
  OBSERVED:                     16
Branch:                        campaign/phase3-13-growth-ledger
Step 7 implementation commit:  1cc73da  (phase3.13 step7: implement
                                          growth ledger option A)
Growth Ledger row family:      I-GROW-01..22
v1 emitted event types:        STREAM_CHUNK_ACCEPTED
                               PATTERN_ENTRY_CREATED
                               PATTERN_ENTRY_UPDATED
                               STREAM_PROMOTION_QUEUED
                               TICK_SUCCEEDED
                               PROFILE_DOMAIN_ADDED
                               MSI_MEMBER_ADDED
Deferred event types:          SESSION_SAVED
                               SESSION_LOADED
                               COHERENCE_REPORT_BUILT
v1 emitted source labels:      STREAM_APPEND
                               PATTERN_LEDGER_OBSERVE
                               STREAM_PROMOTE
                               STEP_DISPATCH
Deferred source labels:        PERSISTENCE_SAVE
                               PERSISTENCE_LOAD
                               COHERENCE_MONITOR
No /growth-ledger UI in v1:    confirmed (LOCK S; I-GROW-21 DEFERRED)
No persistence/DB/autosave
extension in v1:               confirmed (LOCK A; autosave trigger set
                                          remains {STEP_TICK,
                                          STREAM_PROMOTE})
No SelfModel in Phase 3.13:    confirmed (mission baseline)
Bounds:                        GROWTH_LEDGER_MAX_EVENTS        = 256
                               GROWTH_LEDGER_REFERENCE_MAX     =   8
                               GROWTH_LEDGER_ID_MAX            =  64
                               GROWTH_LEDGER_PROVENANCE_MAX    =  64
                               GROWTH_LEDGER_SOURCE_MAX        =  64
```

Preflight gates re-verified at Step 8 entry (every gate PASS):

```text
python3 -m tools.catalog counts     PASS  (259 / 86 / 12 / 15 / 16)
python3 -m tools.citations verify   PASS  (100 citations resolved)
python3 -m tools.import_audit       PASS  (I-PCE-05 clean)
python3 -m brain.invariants run     PASS  (353 rows; 0 gate failures)
bash tools/check_all.sh             PASS  (All checks passed.)
```

## Method

A temporary in-process probe was authored at
`/tmp/phase3_13_growth_ledger_probe.py`. The probe is **not committed**
and is not required for any future invariants run. It uses only
repo-local public surfaces:

```text
brain.ui.command_line.LocalCommandLine.parse(...)
brain.ui.session.OperatorSession.dispatch(command, client=...)
brain.ui.__main__.build_default_session()
brain.ui.__main__.OfflineStandInClient
brain.development.growth_ledger.GrowthLedger
brain.development.growth_ledger.GrowthEvent
brain.development.growth_ledger.GrowthEventType
brain.development.growth_ledger.GrowthEventSource
brain.development.growth_ledger.derive_growth_event_id
brain.development.coherence_monitor.build_full_coherence_report
```

The probe was invoked exactly once with:

```bash
PYTHONPATH=. python3 /tmp/phase3_13_growth_ledger_probe.py
```

No real LLM-backed runtime mode was used. `OfflineStandInClient` is the
deterministic `eval_consistency` stand-in shipped by `brain.ui.__main__`
specifically for offline operator routes; it performs no network I/O,
no subprocess spawn, and no file mutation. No model-backed flag was
passed. No real `/save-session` / `/load-session` DB was opened. No
probe JSON or helper script is committed.

The probe recorded:

- the initial Growth Ledger `events` length and `counts_by_type` tuple
- the event count, type counts, event ids, types, source enums,
  references, and provenance after each dispatched scenario
- whether duplicate / spam inputs were idempotent or bounded
- whether read-only commands changed the ledger
- whether failure paths changed the ledger
- whether `/save-session` / `/load-session` /
  `build_full_coherence_report` emitted any deferred-event-type event
- pre/post-observe identity equality for `BrainState`,
  `OperatorSession.pattern_ledger`, `OperatorSession.autosave_config`,
  `OperatorSession.session_store_config`

The probe also runs a structural check that `counts_by_type` equals the
events grouped by `event_type.value` (the deterministic
labelled-tuple-over-the-closed-enum surface — `I-GROW-09`).

This method is bounded by the safe operator route plus direct
`GrowthLedger` construction. It does not exercise every conceivable
future call site or runtime container; future regressions in any new
call site would require a re-run.

## Test Matrix

The matrix below is the full set of scenarios the probe exercised. Each
row records the route or surface, the expected emission shape, the
forbidden emission shape, the observed event delta, observed
`counts_by_type` delta, the no-mutation check (if applicable), and the
classification (PASS / NOT RUN / etc.). Every row's evidence is the
probe output.

```text
#  Scenario                                  Route / surface                     Expected            Forbidden          Observed (delta)                                                                                                                            Mutation check                                                Verdict
1  Baseline empty session                    build_default_session()             events==0           any event          events=0; counts_by_type returns 10 (event_type,0) pairs                                                                                    n/a                                                          PASS
2  Successful /stream append                 /stream hello world                 STREAM_CHUNK_ACCEPTED + PATTERN_ENTRY_CREATED   raw text in refs;  +2 events; types=(stream_chunk_accepted:1, pattern_entry_created:1); refs=('strm-chunk-1',)/('pledger:df68...',) BrainState identity unchanged; pattern_ledger replaced;       PASS
                                                                                                     read-only mutation                                                                                                                                              copy-on-write growth_ledger replaced
3  Repeated /stream same motif (4x)          /stream alpha beta x4               +4 STREAM_CHUNK_ACCEPTED; 1 created + 1 updated  unbounded; double-id  +6 events; types=(stream_chunk_accepted:4, pattern_entry_created:1, pattern_entry_updated:1)                  no aggregate scalar attr on GrowthLedger                     PASS
                                                                                                     for identical payload
4  Alternating /stream motifs (4x)           /stream alpha alpha; /stream beta beta x2 each   +4 chunk + 2 created + 2 updated   raw text in refs   +8 events; pattern_id references only ('pledger:f7b3...' & 'pledger:a95d...')                                     —                                                            PASS
5  /stream-promote success                   /stream gamma; /stream-promote      STREAM_PROMOTION_QUEUED with candidate_id  /step events without /step  +1 event STREAM_PROMOTION_QUEUED refs=('promo-strm-chunk-1',); no TICK events                                  —                                                            PASS
6  /step success after queued percept        /stream delta; /stream-promote;     TICK_SUCCEEDED + PROFILE_DOMAIN_ADDED + MSI_MEMBER_ADDED for each delta entry                         +3 events tick=1: tick_succeeded refs=('tick-1',); profile_domain_added refs=('strm-strm-chunk-1',); msi_member_added refs=('strm-strm-chunk-1',)  BrainState changed by /step path only (tick(...) call site)  PASS
                                              /step                                                  removal events; eval_consistency-derived event
7  /step empty queue                         /step (queue empty)                 no event            any growth event   delta=0; error_message="STEP_TICK with empty event queue"                                                                                   no kernel mutation; no ledger change                          PASS
8  Read-only commands (17 verbs)             /state /tick /output /worldlet      no event            any growth event   delta=0 for every verb; growth_ledger identity unchanged across the whole sequence                                                          autosave/persistence/state identity all preserved             PASS
                                              /repl /stream-summary /stream-candidates
                                              /session-status /db-status /db-summary
                                              /profile-summary /stream-db-summary
                                              /db-diff /db-verify /autosave-status
                                              /help /clear
9  Save/load deferred non-emission           /save-session; /load-session        SESSION_SAVED & SESSION_LOADED NOT emitted   any event           delta=0; both dispatchers surfaced "requires a configured --session-db" error_message; SESSION_SAVED count=0; SESSION_LOADED count=0
                                              (session_store_config=None)                                                                                                                                                                                          autosave/persistence config identity preserved               PASS (failure-path coverage)
                                                                                                                                                                                                                                                                                                                                  + STRUCTURAL: source code of _dispatch_save_session
                                                                                                                                                                                                                                                                                                                                  / _dispatch_load_session contains no GrowthLedger.observe
                                                                                                                                                                                                                                                                                                                                  call (verified by reading brain/ui/session.py)
10 Coherence report deferred non-emission    build_full_coherence_report(session)  COHERENCE_REPORT_BUILT NOT emitted   any event           delta=0; growth_ledger identity unchanged; COHERENCE_REPORT_BUILT count=0    BrainState identity preserved                                PASS
11 Anti-Goodhart spam / saturation           /stream unique-motif-N for N in 0..299  events <= 256; observe returns self at cap  unbounded growth; aggregate score  final count=256; cap hit; observe(ledger_at_cap, brand-new payload) returns self (same id)  autosave/persistence/state identity preserved across loop  PASS
12 Direct idempotency probe                  GrowthLedger().observe(...) x2     same event_id; second observe returns self  duplicate event_ids in events  ledger2 is ledger1 (identity); event_id "growth:7e091befbac02698"; ledger0.events==() preserved (copy-on-write)  n/a                                                          PASS
13 No-mutation audit across observe          full /stream + /stream-promote + /step then direct observe   PatternLedger entries identical; autosave_config & session_store_config identity preserved; state preserved across direct observe   any mutation by observe   PatternLedger entries equal pre- and post-observe (no recurrence_count change); autosave_config is preserved; session_store_config is preserved   pre/post direct-observe identity stable on pattern_ledger and state PASS
14 Constructor / observe validation          GrowthEvent / observe with bad inputs  ValueError on COGITO_ID, negative tick, duplicate refs, non-enum type  silent acceptance; double-id  ValueError raised for negative tick, duplicate references, non-enum event_type   no ledger state observable (rejected before append)         PASS
15 Deferred enum inventory                   list(GrowthEventType)              SESSION_SAVED, SESSION_LOADED, COHERENCE_REPORT_BUILT present as members  any extra/unauthorized members  closed enum contains exactly the 7 v1 members + 3 deferred members; deferred members appear in counts_by_type with count=0  n/a                                                          PASS
```

The classification vocabulary follows the operator-supplied template:
**works / awkward / confusing / fails / missing / blocked by env /
not exercised by design**. The probe found no fail, no missing, no
awkward, no confusing, and no blocked-by-env scenarios for the v1
emission scope. The single "not exercised by design" cases are the
deferred trio: their non-emission is confirmed in v1 by both the
failure-path probe (Family 9) and the source inspection of
`_dispatch_save_session` / `_dispatch_load_session` (which contain no
`GrowthLedger.observe` call) and the absence of any `observe(...)` call
on `build_coherence_report` / `build_full_coherence_report` in
`brain/development/coherence_monitor.py`.

### Probe quirks

The probe's Family 14 includes an attempted `event_id="COGITO"` test
that does not match the actual `COGITO_ID` constant value
`"__cogito__"`, so the probe silently accepts that synthetic input.
This is a **probe defect, not a Growth Ledger defect**: the runtime
contract is structural and lives in `brain/development/growth_ledger.py`
at the `if value == COGITO_ID: raise ValueError(...)` check inside
`_require_bounded_printable`. The constructor and observe paths still
reject any input equal to `COGITO_ID`. The probe's negative-tick,
duplicate-references, and non-enum tests all raised correctly.

## Event-Type Results

```text
Event type                  Expected v1 behavior                                         Observed behavior                                          Verdict                          Evidence (probe family)
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
STREAM_CHUNK_ACCEPTED       emitted at end of successful _dispatch_stream_append;       1 event per successful /stream; references=(chunk_id,)     works                            Families 2, 3, 4, 5, 6, 11
                            references=(chunk_id,); provenance "stream_append:_dispatch_stream_append"  provenance "stream_append:_dispatch_stream_append"
PATTERN_ENTRY_CREATED       emitted when PatternLedger.observe(...) returned a new      emitted whenever a previously-unseen pattern_id appeared    works                            Families 2, 4
                            entry not present in prior_pattern_ledger.entries           in the post-observe entries tuple
PATTERN_ENTRY_UPDATED       emitted when PatternLedger.observe(...) returned an entry   emitted whenever an existing pattern_id's recurrence_count works                            Families 3, 4
                            whose recurrence_count strictly increased                   strictly increased
STREAM_PROMOTION_QUEUED     emitted at end of successful _dispatch_stream_promote;      1 event per successful /stream-promote;                    works                            Families 5, 6
                            references=(candidate_id,)                                  references=(candidate_id,)
TICK_SUCCEEDED              emitted at end of successful _dispatch_step;                1 event per successful /step;                              works                            Family 6
                            references=(f"tick-{record.tick_index}",)                   references=('tick-1',)
PROFILE_DOMAIN_ADDED        emitted per element of (post.profile.domain                 1 event per addition; references=(content_id,);            works                            Family 6
                            - pre.profile.domain) after a successful tick               provenance "step_dispatch:profile_delta"
MSI_MEMBER_ADDED            emitted per element of (post.msi.contents                   1 event per addition; references=(content_id,);            works                            Family 6
                            - pre.msi.contents) after a successful tick                 provenance "step_dispatch:msi_delta"
SESSION_SAVED               not emitted in v1 (LOCK J; LOCK A)                          0 events; failure path of /save-session triggered;          not exercised by design          Family 9 (failure path) + source inspection
                                                                                        successful-path observe call absent from
                                                                                        _dispatch_save_session by source inspection
SESSION_LOADED              not emitted in v1 (LOCK J; LOCK A)                          0 events; failure path of /load-session triggered;          not exercised by design          Family 9 (failure path) + source inspection
                                                                                        successful-path observe call absent from
                                                                                        _dispatch_load_session by source inspection
COHERENCE_REPORT_BUILT      not emitted in v1 (LOCK J)                                  0 events after build_full_coherence_report;                 not exercised by design          Family 10 + source inspection
                                                                                        observe call absent from build_coherence_report /
                                                                                        build_full_coherence_report by source inspection
```

The seven v1 emitted event types' references all stayed on bounded
printable identifiers — `chunk_id`, `pattern_id`, `candidate_id`,
`f"tick-{tick_index}"`, `content_id`. No reference observed in the
probe carried raw chunk text or any field that would let raw operator
text leak into the ledger. Provenance strings observed are all on the
closed list documented in `brain/development/growth_ledger.py` and the
catalog patch plan.

## No-Mutation Verification

The following surfaces were checked for identity-stability or
documented-only mutation across the probe scenarios. "Identity-stable"
means the Python `is` check returned true. "Replaced (copy-on-write)"
means the field was reassigned to a new value through the documented
path. "Mutated through tick(...)" means the `BrainState` was changed by
the existing public `brain.tick.tick` callable only — not by any
Growth Ledger code.

```text
Surface                                       Behavior                                  Evidence
-------------------------------------------------------------------------------------------------------------------------------------
GrowthLedger.observe(...) on prior ledger     prior ledger identity preserved;          ledger0.events == () after ledger1 = ledger0.observe(...);
                                              new ledger returned                       direct-observe family family 13: pre_obs_pl is session.pattern_ledger after observe
GrowthLedger.observe duplicate payload         returns self (same Python object)         family 12: ledger2 is ledger1 == True; cap test family 11: observe at cap returns same object
GrowthLedger.observe at cap                   returns self (same Python object)         family 11: at cap, observe(brand-new payload) returns ledger_at_cap (identity)
Pattern Ledger records                        not mutated by GrowthLedger.observe       family 13: pre-/post-direct-observe pattern_ledger is identical;
                                                                                       Pattern Ledger entries equal across the post-step direct observe
Coherence Monitor records                     not mutated by GrowthLedger.observe       no Growth Ledger code constructs a Coherence Monitor record;
                                                                                       Family 10 confirms growth_ledger identity unchanged across a build call
BrainState                                    mutated only through the existing         family 6: BrainState changed by /step path (tick(...) call);
                                              tick(...) call                            family 13: state identity preserved across a direct GrowthLedger.observe call
OperatorSession.autosave_config               identity-stable across Growth Ledger      family 13: autosave_config is preserved across /stream, /stream-promote, /step,
                                              integration                               and a direct observe call
OperatorSession.session_store_config          identity-stable across Growth Ledger      family 13: session_store_config is preserved across the same sequence
                                              integration
OperatorSession.event_queue                   mutated only by the existing               operator-route exercise of the queue follows the existing
                                              dispatch path                              _dispatch_step / _dispatch_stream_promote contract; no Growth Ledger code
                                                                                       enqueues or dequeues
OperatorSession.stream_history /              mutated only by the existing               _dispatch_stream_append is the only path that mutates either; no Growth
stream_candidates / stream_chunk_serial       _dispatch_stream_append path               Ledger code touches these fields
persistence schema                            unchanged in v1 (LOCK A)                   no SCHEMA_VERSION bump in Step 7 commit;
                                                                                       INVARIANT_CATALOG.md and tools/catalog.py reflect v0.23 catalog version
                                                                                       only — no growth_events table is declared anywhere
autosave trigger set                          unchanged in v1 (LOCK A)                   {STEP_TICK, STREAM_PROMOTE} preserved in
                                                                                       brain/ui/session.py:_maybe_autosave_after_dispatch
LLM client surface                            no Growth Ledger code calls a client      growth_ledger.py imports only dataclasses, enum, hashlib, typing,
                                                                                       and COGITO_ID from brain.tlica.profile (verified by source inspection
                                                                                       and by I-GROW-10 / I-GROW-11 STATIC AST audit fixtures, both green
                                                                                       in `python3 -m brain.invariants run`)
UI / parser / render / snapshot               unchanged in v1 (LOCK S; I-GROW-21)       no OperatorCommand member, no parser verb, no active_view value, no
                                                                                       render / snapshot / commands / command_line change in Step 7 commit
hidden DB writes                              none                                       Growth Ledger has no sqlite3 / pathlib / open import; LOCK O / LOCK P
                                                                                       enforce this and the static AST audit is green
hidden LLM calls                              none                                       no brain.llm import in growth_ledger.py; no eval_consistency-bearing
                                                                                       object ever touches a GrowthLedger field
```

In-memory ledger mutation is expected and documented: each
`GrowthLedger.observe(...)` call returns a new ledger reassigned to
`OperatorSession.growth_ledger`. This is the copy-on-write substrate
contract (LOCK F / I-GROW-05). It is not a mutation of the prior
ledger object; the prior ledger's `events` tuple is unchanged after the
call. The no-mutation guarantees above are scoped accordingly: they
cover persistence, catalog, fixture, runtime container, autosave, LLM
client, UI, DB, and external resources — not the in-memory ledger
itself, whose copy-on-write replacement is the documented v1 behavior.

## Deferred Non-Emission Verification

Explicit verification for each deferred behavior:

```text
SESSION_SAVED is not emitted in v1
  - Family 9 failure path: 0 emissions through /save-session under
    session_store_config=None.
  - Source inspection: _dispatch_save_session in brain/ui/session.py
    contains no GrowthLedger.observe call on the successful path.
    The success path returns after calling save_session(self, config)
    and setting status; no Growth Ledger interaction occurs.
  - GrowthEventType.SESSION_SAVED count remains 0 across all probe
    families.

SESSION_LOADED is not emitted in v1
  - Family 9 failure path: 0 emissions through /load-session under
    session_store_config=None.
  - Source inspection: _dispatch_load_session in brain/ui/session.py
    contains no GrowthLedger.observe call on the successful path.
    The success path applies the loaded candidate's kernel + stream
    state and sets status; no Growth Ledger interaction occurs.
  - GrowthEventType.SESSION_LOADED count remains 0 across all probe
    families.

COHERENCE_REPORT_BUILT is not emitted in v1
  - Family 10 read-only build: 0 emissions through
    build_full_coherence_report.
  - Source inspection: brain/development/coherence_monitor.py
    contains no GrowthLedger.observe call. build_coherence_report
    and build_full_coherence_report are pure read-only helpers and
    do not import or call brain.development.growth_ledger.
  - GrowthEventType.COHERENCE_REPORT_BUILT count remains 0 across
    all probe families.

/growth-ledger UI does not exist in v1
  - Source inspection: brain/ui/commands.py contains no
    OperatorCommand.GROWTH_LEDGER member; LOCAL_COMMAND_VERBS in
    brain/ui/command_line.py contains no "growth-ledger" verb;
    brain/ui/snapshot.py ACTIVE_VIEWS contains no "growth_ledger"
    value; brain/ui/render.py contains no growth_ledger pane;
    brain/ui/commands.py INSPECT_VIEW_MAP has no growth_ledger entry.
  - Drives I-GROW-21 (DEFERRED in the v0.23 catalog).

SelfModel is not implemented
  - Repo-wide grep: no brain/development/self_model.py or any
    SelfModel class exists. The Phase 3.12 Step 15 roadmap remains
    deferred to a future campaign.
  - Drives mission baseline guardrail: "no SelfModel implementation
    in Phase 3.13".
```

The non-emission of the deferred trio is the conjunction of (a) "no
observe call exists in the relevant dispatcher's code" and (b) "the
runtime probe never produced one of those event types across the
exercised scope". (a) is the stronger structural guarantee — it
forecloses emission on *any* runtime path the dispatcher takes, not
just the failure path the probe exercised. (b) is the runtime
confirmation that the structural guarantee holds in practice.

The probe did not exercise a successful `/save-session` /
`/load-session` round-trip against a configured `--session-db`. That
scenario is **NOT RUN** (blocked by environmental setup cost only) and
is marked accordingly above. The source-inspection result is the
load-bearing evidence: even if the successful save / load path were
run in a future campaign step, no `GrowthLedger.observe` call exists
on it. Promoting the deferred trio to v1 would require a Step 7-class
edit to those dispatchers (and a row-family catalog patch); the v1
implementation has no such code.

## Anti-Goodhart Verification

Explicit verification for each anti-Goodhart guarantee:

```text
Repeated identical text does not create raw-text growth scoring
  - GrowthEvent.references stores chunk_id / pattern_id /
    candidate_id / content_id strings only. The probe Family 4
    inspected every emitted reference and found no raw chunk text.
  - The /stream payload's text body lives only in TextStreamChunk
    and is reachable through stream history; the Growth Ledger is a
    referencing layer over the resulting bounded ids.

Long text does not create stronger growth
  - GrowthEvent has no text-length-derived field. references is
    tuple[str, ...] bounded by GROWTH_LEDGER_REFERENCE_MAX=8; each
    entry is bounded by GROWTH_LEDGER_ID_MAX=64. None of these
    bounds reflects chunk-text length.

Duplicate event payload is idempotent
  - Family 12: GrowthLedger().observe(same payload).observe(same
    payload) returns the second result as the same Python object as
    the first. ledger2 is ledger1 == True.
  - Direct GrowthLedger construction with two GrowthEvent records
    sharing event_id rejects with ValueError in __post_init__
    (I-GROW-07; fixture growth_ledger_constructor.py is green).

Global cap behavior is bounded
  - Family 11: 300 successive distinct /stream commands produced
    exactly 256 events in the ledger (GROWTH_LEDGER_MAX_EVENTS).
    Observe at cap returned self (same Python object) for a brand-
    new payload.
  - No eviction, no pruning, no FIFO drop, no LIFO drop, no
    overwrite of an existing event slot, no random replacement, no
    per-event-type rebalancing was observed.
  - LOCK H "refusal scope is ledger-append boundary only" was
    visible: the dispatcher's return values, the user-facing
    error_message, the event_queue, stream_history, and
    stream_candidates were all unaffected by the cap-refusal
    boundary.

counts_by_type is a factual tuple, not a score
  - Family 1 / 3 / 11: counts_by_type returns
    tuple[tuple[str, int], ...] ordered by the closed enum's
    declaration order; one pair per member; deferred members
    present at count 0.
  - The probe verified that grouping events by event_type.value
    matches counts_by_type for every observed ledger.
  - No scalar field summarizes the ledger.

No aggregate growth score exists
  - Family 3 enumerated forbidden scalar attribute names
    (growth_total, growth_index, growth_rate, growth_score,
    intelligence_score, awareness_score, iness_score,
    coherence_quality, capability_score, maturity_score). None is
    present on GrowthEvent / GrowthLedger.
  - I-GROW-09 / I-GROW-19 (catalog v0.23) audit the same surface
    from the catalog side; both rows are green in
    `python3 -m brain.invariants run`.
```

## Findings Classification

```text
Finding id        Severity    Category              Description                                                                                                                                                                Evidence (probe family / source)                                          Recommendation                                                Blocker
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
F-1               minor       documentation          Probe Family 14's COGITO_ID rejection check used the literal string "COGITO" instead of the COGITO_ID constant value "__cogito__". The probe silently accepted the synthetic input. The actual runtime contract (rejection on equality with COGITO_ID) is enforced inside _require_bounded_printable in brain/development/growth_ledger.py and is exercised by I-GROW-03 fixture growth_ledger_constructor.py (green).                                                                                                                                                  Probe file /tmp/phase3_13_growth_ledger_probe.py family 14; growth_ledger.py _require_bounded_printable               Drop the synthetic test or fix it to use brain.tlica.profile.COGITO_ID in a future probe; not load-bearing for v1.        no
F-2               minor       deferred enhancement   Successful /save-session / /load-session round-trip against a configured --session-db was not exercised (NOT RUN by design — DB scaffolding cost). The deferred non-emission for SESSION_SAVED / SESSION_LOADED was confirmed structurally by source inspection and through the failure-path probe; the successful-path runtime measurement is deferred.                                                                                                                                                                                                            Family 9 + source inspection of _dispatch_save_session and _dispatch_load_session in brain/ui/session.py                If a future campaign opens a configured DB for behavior probing, run the successful save/load round-trip and confirm 0 deferred-event emissions.    no
F-3               minor       deferred enhancement   I-GROW-22 NOT-EXERCISED placeholder remains as documented. The end-to-end Growth Ledger dry-run helper is a placeholder mirroring I-PLEDGER-18 / I-COHMON-14; it is not promoted in Phase 3.13.                                                                                                                                                                                                                                                                                                                                                                                  INVARIANT_CATALOG.md v0.23 / catalog patch plan / I-GROW-22 status      Leave as NOT-EXERCISED; revisit only as part of a follow-up campaign that explicitly authorizes the dry-run row.            no
F-4               none        no issue              Anti-Goodhart cap behavior observed exactly as locked: 300 successive /stream commands produced 256 events; observe at cap returned self.                                                                                                                                                                                                                                                                                                                                                                                                                                                Family 11                                                                                                       —                                                            no
F-5               none        no issue              Read-only command coverage (17 verbs including /help and /clear, /db-* read-only family, /autosave-status, /stream-summary, /stream-candidates, /session-status, /state, /tick, /output, /worldlet, /repl, /db-diff, /db-verify) all produced zero growth events. growth_ledger identity was preserved across the entire sequence.                                                                                                                                                                                                                                              Family 8                                                                                                       —                                                            no
F-6               none        no issue              Constructor / observe validation rejects negative tick, duplicate references, and non-enum event_type with ValueError. The validation order locked in LOCK G is observable: references uniqueness rejects before event_id derivation.                                                                                                                                                                                                                                                                                                                                                Family 14 + growth_ledger.py _require_references                                                                                                                  —                                                            no
F-7               none        no issue              Pattern Ledger entries are identity-stable across a direct GrowthLedger.observe call; BrainState identity is preserved across a direct observe; autosave_config and session_store_config identities are preserved across the full safe-route exercise.                                                                                                                                                                                                                                                                                                                                                                                              Family 13                                                                                                       —                                                            no
F-8               none        no issue              Deferred event types appear in the closed enum (LOCK J permits this for future compatibility) and the runtime emits zero events for any of them across the exercised scope; counts_by_type reports zero for each.                                                                                                                                                                                                                                                                                                                                                                  Family 1, Family 9, Family 10, Family 15                                                                                                                  —                                                            no
```

No finding is a blocker. F-1 is a probe artifact; F-2 / F-3 are
deliberate deferred enhancements documented in the catalog patch plan
and the Step 4 corrigenda. F-4 through F-8 are observed PASSes.

## ChatGPT/Codex Consultation

Used the sanctioned Stage A advisory bridge once during Step 8, mode
`review`, model `gpt-5.5`, effort `medium`, timeout `180`. The question
file and answer file are both in `/tmp` and are not committed; the
wrapper's hash-only audit JSONL appended to
`.claude/codex_bridge_logs/2026-05-18.jsonl` (gitignored by design).

```text
ChatGPT/Codex consultation:
- used:           yes
- mode:           review
- model:          gpt-5.5
- effort:         medium
- wrapper command: python3 tools/claude_helpers/codex_chatgpt_subagent.py
                     --mode review --model gpt-5.5 --effort medium
                     --timeout 180
                     --prompt-file /tmp/toyi_chatgpt_step8_question.md
                     > /tmp/toyi_chatgpt_step8_answer.md
- question file:   /tmp/toyi_chatgpt_step8_question.md
- answer file:     /tmp/toyi_chatgpt_step8_answer.md
- wrapper status:  exit 0; error_class null; codex_returncode 0;
                   duration_ms 39715; stdout_bytes 6184; stderr_bytes 8650;
                   truncated false; codex-cli 0.130.0; auth
                   "Logged in using ChatGPT". Audit JSONL appended at
                   .claude/codex_bridge_logs/ (gitignored).
- accepted advice:
   - Scope the report's findings to "behavior observed through the
     existing safe operator route", not as exhaustive proofs about
     all ledger call sites or future integrations. Applied as the
     "Scope of claim" paragraph in Purpose and the per-row scoping
     in Test Matrix and Event-Type Results.
   - Tie deferred-event non-emission to specific exercised paths
     and inspected state. Applied: every deferred row in
     Event-Type Results cites both the runtime path (failure-path
     probe; build_full_coherence_report) and the source inspection.
   - Distinguish "no persistence / file / catalog / fixture
     mutation" from in-memory ledger mutation, which is expected
     behavior. Applied as the closing paragraph of "No-Mutation
     Verification" calling out that in-memory copy-on-write
     replacement is the documented behavior.
   - Verify counts_by_type equals the events grouped by type.
     Applied as a structural check in the probe and noted in the
     Method section.
   - Include a "Not established" framing for global ledger
     correctness, future / deferred events, persistence semantics,
     aggregate growth scoring, and any subjective / semantic /
     agency claims. Applied in "Scope of claim" and reflected in
     the No-Mutation, Deferred Non-Emission, and Anti-Goodhart
     sections.
   - Verify failure paths do not emit success-shaped events.
     Applied via Family 7 (/step empty queue) and Family 9
     (/save-session / /load-session failure path).
   - Verify read-only commands leave ledger state and runtime
     state unchanged. Applied via Family 8.
   - Use a scenario matrix with route, expected emissions,
     forbidden emissions, observed event delta, observed count
     delta, mutation check, and classification. Applied as the
     Test Matrix table.
- rejected advice:
   - "Convert absence of an aggregate growth score into proof that
     no downstream consumer can infer one." The advisor flagged
     this as an overclaim risk; the report adopts that scoping
     (it does NOT claim downstream-consumer impossibility, only
     module-surface absence). Rejected as a *to-do* — the
     phrasing was applied by negation in "Anti-Goodhart
     Verification" rather than as an additional claim.
   - "Imply /stream-promote creates an autonomous promotion
     mechanism." Rejected as a *to-do*: the report describes
     /stream-promote as a typed operator-initiated dispatch path
     and references the existing I-AUTOSAVE-14 outcome-detection
     contract.
   - "Repeat git status --short after report generation as the
     primary mutation guarantee for repo state." The repo-local
     validation contract uses the five preflight gates
     (catalog counts, citations verify, import_audit, invariants
     run, check_all.sh) instead. `git status --short` is run in
     the Step 8 final-validation block, but it is not the
     load-bearing no-mutation check; the gates are.
- reason:          Advisor's "minor disagreement, medium
                   confidence" verdict was consistent with the
                   plan. Every substantive scoping suggestion was
                   adopted as inline report language; rejections
                   are scope clarifications, not contradictions.
```

Treated the bridge output as advisory. Repo-local files, gates, and
invariants override ChatGPT advice; the ChatGPT advisor explicitly
acknowledged this requirement in the answer ("Repo-local evidence is
missing for a claim the report intends to make" is one of its stop
conditions, which the report does not trigger).

## Final Verdict

```text
PASS WITH DEFERRED FOLLOW-UPS
```

The Growth Ledger v1 behavior over the existing safe operator route
matches the locked contract from Steps 2–5 exactly:

- the seven v1 event types emit at the expected dispatcher call sites
  with the expected references and provenance
- the three deferred event types are not emitted on any path the probe
  exercised and have no observe call in their nominal dispatchers
- read-only commands, parse failures, dispatch failures, and tick
  failures do not emit any growth event
- the global cap (256) and idempotent dedup keep the ledger bounded
  under spam
- the ledger does not mutate `BrainState`, the Pattern Ledger entries,
  the autosave config, the session_store_config, or any
  external / persistence / DB / LLM surface
- no aggregate growth scalar exists anywhere on the module surface

The deferred follow-ups (F-2 / F-3) are intentional, documented in the
Step 4 corrigenda and the Step 5 catalog patch plan, and not blockers
for the v1 verdict. F-1 is a probe artifact, not a runtime defect.

## Next Artifact

```text
docs/campaigns/phase3_13/PHASE3_13_GROWTH_LEDGER_FINDINGS.md
```

Step 9 will triage the findings above (F-1..F-8) and any operator UX
surprises, list proposed deferred follow-ups, and explicitly enumerate
the items that do **not** block the Phase 3.13 campaign.

## Validation

Re-ran after writing this behavior report (no source under `brain/**`,
`tools/**`, `.claude/**`, `lean_reference/**`, `scenarios/**`, or
`traces/**` was touched; no edit to `INVARIANT_CATALOG.md`,
`README.md`, `CURRENT_MISSION.md`, `CURRENT_CAMPAIGN.md`,
`PHASE3_13_GROWTH_LEDGER_ROADMAP.md`, or any prior Phase 3.13 docs;
only this new documentation file was added):

| Command | Result |
|---------|--------|
| `python3 -m tools.catalog counts` | PASS (259 / 86 / 12 / 15 / 16) |
| `python3 -m tools.citations verify` | PASS (100 citations resolved) |
| `python3 -m tools.import_audit` | PASS (I-PCE-05 clean) |
| `python3 -m brain.invariants run` | PASS (353 rows; 0 gate failures) |
| `bash tools/check_all.sh` | PASS (All checks passed.) |
