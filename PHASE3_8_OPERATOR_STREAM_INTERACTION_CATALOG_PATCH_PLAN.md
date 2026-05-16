# PHASE3_8_OPERATOR_STREAM_INTERACTION_CATALOG_PATCH_PLAN.md

## 1. Purpose

Bind the rulings in
`PHASE3_8_OPERATOR_STREAM_INTERACTION_CORRIGENDA.md` to concrete catalog
rows, statuses, file budget, count delta, fixture roster, and
pending-registration mechanics. This is a planning artifact only. It
does not apply catalog rows, edit `tools/catalog.py`, add runtime
modules, add fixtures, change generated catalog IDs, alter
`INVARIANT_CATALOG.md`, change `brain/invariants.py`, or update README
as though implementation exists.

Verdict for the Step 22 review gate:

```text
COHERENT - READY FOR REVIEW GATE
```

## 2. Baseline

```text
Catalog version:  v0.14
REQUIRED:        158
STRUCTURAL:       56
NOT-EXERCISED:     7
DEFERRED:         12
OBSERVED:         10
Total tabular:   243
```

Required latest audit:

```text
PHASE3_7_TEXT_STREAM_INGRESS_AUDIT.md   PASS
```

Accepted planning artifacts:

```text
PHASE3_8_OPERATOR_STREAM_INTERACTION_SYNTHESIS.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_CORRIGENDA.md
```

## 3. Patch Impact

```text
+ 10 REQUIRED
+  5 STRUCTURAL
+  1 NOT-EXERCISED
+  0 DEFERRED
+  1 OBSERVED
```

Expected counts after the accepted patch:

```text
Catalog version:  v0.15
REQUIRED:        168
STRUCTURAL:       61
NOT-EXERCISED:     8
DEFERRED:         12
OBSERVED:         11
Total tabular:   260
```

## 4. Row Family Thesis

Row family:

```text
I-UISTRM-*
```

Rationale for family spelling:

```text
Use I-UISTRM-* rather than I-UI-STRM-* because the current catalog
parser recognizes row IDs in the I-<UPPERCASEMODULE>-NN shape. A second
hyphen inside the module token would not be parsed by tools/catalog.py
without a tooling change.
```

Core commitments:

```text
Operator Stream Interaction extends the existing Operator TUI with a
finite typed route over the accepted Phase 3.7 Text Stream Ingress
substrate.

/stream appends bounded operator text to session-local TextStreamHistory
only. It does not construct a PerceptEvent, does not enqueue an event,
does not call tick(), and does not mutate BrainState.

/stream-summary and /stream-candidates are read-only views over local
stream history, exact feature counts, structural segments, recurrence
patterns, and explicit promotion candidates. They are not language,
truth, social, agency, Mode B, or model-backed surfaces.

/stream-promote validates one explicit StreamPromotionCandidate by ID
and queues exactly one QueuePerceptPayload through the existing
OperatorEventQueue surface. It does not call tick(); /step remains the
only route that calls tick().

Stream session state remains local UI/session state. It is not stored in
BrainState, MSI, PtCns, the content registry, source histories, traces,
or scenarios.

The render path uses immutable display snapshots and remains pure and
deterministic.

Model-backed behavior remains deferred to the explicit Phase 3.8b LLM
Runtime Toggle subcampaign. Standard fixtures remain deterministic.
```

## 5. Row Table

All rows use the `I-UISTRM-*` family. Owning modules are under
`brain/ui/` unless noted.

### 5.1 REQUIRED rows

```text
I-UISTRM-01  Stream command parser is finite and typed.
              LocalCommandLine accepts exactly /stream,
              /stream-summary, /stream-candidates, and
              /stream-promote in addition to the existing approved
              verbs; malformed stream forms return LocalCommandError.
              Fixture: stream_command_parser.py

I-UISTRM-02  Stream command payloads are bounded and constructor-
              checked.
              /stream text is non-empty bounded raw text compatible
              with TextStreamChunk; /stream-promote candidate_id is
              bounded printable text; payload records are frozen and
              carry no callable/resource/client values.
              Fixture: stream_command_parser.py

I-UISTRM-03  /stream appends to session-local TextStreamHistory only.
              Dispatching STREAM_APPEND creates one TextStreamChunk
              with TextStreamSource.OPERATOR and returns updated local
              stream state without mutating BrainState, latest_tick,
              tick_counter, source histories, or event_queue.
              Fixture: stream_session_append.py

I-UISTRM-04  /stream-summary is read-only.
              Dispatching INSPECT_STREAM_SUMMARY selects a stream
              summary view and may build immutable summary snapshots,
              but does not mutate TextStreamHistory, promotion
              candidates, BrainState, source histories, or event_queue,
              and does not call tick().
              Fixture: stream_summary_candidates.py

I-UISTRM-05  /stream-candidates is read-only.
              Dispatching INSPECT_STREAM_CANDIDATES selects a candidate
              view and may build immutable candidate snapshots from
              SegmentCandidate / StreamPattern /
              StreamPromotionCandidate records, but does not mutate
              local stream state, BrainState, source histories, or
              event_queue, and does not call tick().
              Fixture: stream_summary_candidates.py

I-UISTRM-06  /stream-promote queues exactly one validated candidate and
              does not tick.
              Dispatching STREAM_PROMOTE resolves one explicit
              StreamPromotionCandidate by candidate_id, converts it to
              one QueuePerceptPayload through the same constructor-
              bounded path as /queue, enqueues it through
              OperatorEventQueue.enqueue, and does not call tick(),
              dequeue, or append to private queue storage directly.
              Fixture: stream_promotion_queue.py

I-UISTRM-07  /step remains the only stream interaction path that calls
              tick().
              Across /stream, /stream-summary, /stream-candidates, and
              /stream-promote, tick_counter and latest_tick are
              unchanged; only OperatorCommand.STEP_TICK reaches the
              existing _dispatch_step route.
              Fixture: stream_tick_boundary.py

I-UISTRM-08  Stream command failure paths are local UI status/error only.
              Malformed /stream input, over-bound /stream text, unknown
              /stream-promote candidate_id, full event_queue, and
              candidate-to-payload constructor rejection leave
              BrainState, latest_tick, tick_counter, source histories,
              and event_queue length unchanged except on successful
              queueing.
              Fixture: stream_failure_isolation.py

I-UISTRM-09  Stream snapshots and render output are deterministic and
              read-only.
              For equal stream interaction state and equal view-model
              inputs, stream summary / candidate snapshots and rendered
              rows are equal across repeated calls; construction and
              rendering mutate no stream history, candidate record,
              BrainState, source history, event queue, trace, scenario,
              or catalog file.
              Fixture: stream_snapshot_render.py

I-UISTRM-10  Stream interaction introduces no language / truth / social
              / agency / Mode B / model-backed behavior.
              Stream commands and stream views expose structural raw
              text counts, segments, recurrence patterns, and explicit
              promotion candidates only; they add no parser/grammar,
              semantic understanding, truth score, readability score,
              speaker/dialogue state, natural-language teacher,
              agency witness, Mode B planner, real LLM call, or second
              classification path.
              Fixture: stream_static_audit.py
```

### 5.2 STRUCTURAL rows

```text
I-UISTRM-11  Stream session state is resource-free and local.
              OperatorSession or a session-owned StreamInteractionState
              may hold TextStreamHistory and bounded immutable
              StreamPromotionCandidate tuples, but no LLM client,
              subprocess handle, file descriptor, socket, path object
              used for save/export, shell command for execution,
              callback, or mutable external history reference.
              Fixture: stream_session_resource_audit.py

I-UISTRM-12  Stream UI records are immutable display / payload values.
              Stream command payloads, stream interaction state,
              summary snapshots, and candidate snapshots are frozen
              dataclasses or equivalent immutable records whose fields
              are bounded primitives, tuples of bounded primitives,
              strings for exact Fraction display values, or frozen
              text-stream records.
              Fixture: stream_snapshot_render.py

I-UISTRM-13  Stream UI static audit rejects forbidden side effects.
              Stream-command additions to command_line / commands /
              session / snapshot / render perform no shell, subprocess,
              network, filesystem mutation, curses call from pure
              parser/snapshot/render paths, real LLM call, TLICA
              mutation, or tick call outside the existing STEP_TICK
              dispatch route.
              Fixture: stream_static_audit.py

I-UISTRM-14  Stream UI constants preserve Phase 3.7 bounds.
              /stream text length, candidate ID length, promotion
              candidate display cap, parser error length, and
              status/error length match the accepted constants:
              STREAM_TEXT_MAX_LEN = 1024,
              STREAM_PROVENANCE_MAX_LEN = 64,
              STREAM_PROMOTION_MAX = 64,
              LOCAL_CMD_MAX_ERROR_LEN = 240, and
              MAX_STATUS_TEXT_LEN = 240.
              Fixture: stream_constant_parity.py

I-UISTRM-15  Stream command constructors are pure and register no
              callbacks.
              Stream payload constructors and stream view/snapshot
              constructors have no module-level side effects, registry
              mutation, callback registration, atexit handler,
              decorator-installed hook, source-history mutator call, or
              event-queue mutation.
              Fixture: stream_static_audit.py
```

### 5.3 OBSERVED row

```text
I-UISTRM-16  Scripted stream interaction walk is inspectable.
              A deterministic scripted session
              (/stream hello world, /stream-summary,
              /stream-candidates, /stream-promote <candidate_id>,
              /step, /tick) records parser results, session route
              transitions, stream history counts, candidate queueing,
              tick record production after /step only, and absence of
              kernel-boundary leaks. The row is OBSERVED and cannot fail
              the runner.
              Fixture: stream_interaction_walk.py or cited from audit.
```

### 5.4 NOT-EXERCISED row

```text
I-UISTRM-17  Stream UI save / export path is NOT-EXERCISED.
              No Operator TUI stream save, export, serialization, trace
              weaving, scenario weaving, or write-to-disk path exists
              in Phase 3.8. Any future path requires an explicit
              reviewed policy artifact, dedicated catalog rows,
              bounded fixtures, and a stop condition.
              Fixture: none.
```

## 6. Fixture Roster

```text
I-UISTRM-01  stream_command_parser.py
I-UISTRM-02  stream_command_parser.py
I-UISTRM-03  stream_session_append.py
I-UISTRM-04  stream_summary_candidates.py
I-UISTRM-05  stream_summary_candidates.py
I-UISTRM-06  stream_promotion_queue.py
I-UISTRM-07  stream_tick_boundary.py
I-UISTRM-08  stream_failure_isolation.py
I-UISTRM-09  stream_snapshot_render.py
I-UISTRM-10  stream_static_audit.py
I-UISTRM-11  stream_session_resource_audit.py
I-UISTRM-12  stream_snapshot_render.py
I-UISTRM-13  stream_static_audit.py
I-UISTRM-14  stream_constant_parity.py
I-UISTRM-15  stream_static_audit.py
I-UISTRM-16  OBSERVED; stream_interaction_walk.py or audit-cited
I-UISTRM-17  NOT-EXERCISED; no fixture
```

Fixture file delta: **10** new files.

```text
brain/ui/fixtures/stream_command_parser.py
brain/ui/fixtures/stream_session_append.py
brain/ui/fixtures/stream_summary_candidates.py
brain/ui/fixtures/stream_promotion_queue.py
brain/ui/fixtures/stream_tick_boundary.py
brain/ui/fixtures/stream_failure_isolation.py
brain/ui/fixtures/stream_snapshot_render.py
brain/ui/fixtures/stream_static_audit.py
brain/ui/fixtures/stream_session_resource_audit.py
brain/ui/fixtures/stream_constant_parity.py
```

If implementation combines `stream_session_resource_audit.py` into
`stream_static_audit.py`, or folds `stream_constant_parity.py` into
`stream_command_parser.py`, the catalog patch must update this roster
explicitly before landing rows.

## 7. File Budget

Modified files for Step 23 catalog patch:

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
```

Expected modified files for Step 24 implementation:

```text
brain/ui/commands.py
brain/ui/command_line.py
brain/ui/session.py
brain/ui/snapshot.py
brain/ui/render.py
brain/ui/fixtures/stream_command_parser.py
brain/ui/fixtures/stream_session_append.py
brain/ui/fixtures/stream_summary_candidates.py
brain/ui/fixtures/stream_promotion_queue.py
brain/ui/fixtures/stream_tick_boundary.py
brain/ui/fixtures/stream_failure_isolation.py
brain/ui/fixtures/stream_snapshot_render.py
brain/ui/fixtures/stream_static_audit.py
brain/ui/fixtures/stream_session_resource_audit.py
brain/ui/fixtures/stream_constant_parity.py
brain/invariants.py
README.md
```

`README.md` should be updated only after the accepted implementation
exists. Step 23 should not document unimplemented runtime commands as
available.

Explicitly excluded unless a future accepted plan reopens them:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
brain/development/text_stream.py
brain/development/fixtures/text_stream_*.py
```

## 8. Catalog Patch Mechanics (Step 23)

```text
1. Add the 17 new I-UISTRM-* row entries to INVARIANT_CATALOG.md under
   a new "### Phase 3.8 Operator Stream Interaction UI invariants"
   section.

2. Add a v0.15 catalog-version banner above v0.14 documenting the
   +10 REQUIRED / +5 STRUCTURAL / +1 NOT-EXERCISED / +1 OBSERVED
   expansion.

3. Update the summary counts in INVARIANT_CATALOG.md to:
   REQUIRED 168, STRUCTURAL 61, NOT-EXERCISED 8, DEFERRED 12,
   OBSERVED 11.

4. Update tools/catalog.py EXPECTED_COUNTS to the same values.

5. Run python3 -m tools.catalog generate-ids to refresh
   brain/_catalog_ids.py.

6. Add _PHASE3_8_PENDING_ROWS in brain/invariants.py with every
   REQUIRED and STRUCTURAL row that is not yet backed by a real fixture.
   OBSERVED I-UISTRM-16 and NOT-EXERCISED I-UISTRM-17 do not
   participate in I-CAT-01 coverage.

7. Validate with:
   python3 -m tools.catalog counts
   python3 -m tools.catalog generate-ids
   python3 -m tools.catalog counts
```

Step 23 should commit and push after count validation only. It should not
implement parser/session/render behavior.

## 9. Implementation Mechanics (Step 24)

The later implementation step should drain `_PHASE3_8_PENDING_ROWS` by
landing fixture-backed checks in a controlled order:

```text
1. Extend OperatorCommand and Command payload typing.
2. Extend LocalCommandLine with stream verbs.
3. Add session-local stream state and /stream routing.
4. Add read-only summary and candidate routing.
5. Add /stream-promote queue-only bridge.
6. Add stream snapshots and render paths.
7. Add static/resource/constant fixtures.
8. Update README only after behavior exists.
```

Expected targeted validations:

```bash
python3 -m brain.invariants run --id I-UISTRM
python3 -m brain.invariants run --id I-UI
python3 -m brain.invariants run --id I-STRM
bash tools/check_all.sh
```

## 10. Accepted Constants

```text
STREAM_TEXT_MAX_LEN             1024
STREAM_PROVENANCE_MAX_LEN         64
STREAM_PROMOTION_MAX              64
LOCAL_CMD_MAX_ERROR_LEN          240
MAX_STATUS_TEXT_LEN              240
```

These constants may be imported from their owning modules. If copied,
the copied values require explicit fixture parity against the owning
module constants.

## 11. Non-Goals To Preserve

```text
no raw text mutation of BrainState
no raw text mapping to COGITO_ID
no raw text bypass of PerceptEvent construction
no automatic promotion
no direct tick call from stream commands
no language parser, grammar, semantic understanding, or dialogue state
no truth scoring
no readability scoring
no social model
no agency witness
no Mode B planner
no self-modification
no host execution, shell, subprocess, network, or filesystem save/export
no real LLM call below Phase 3.8b
no second model-backed classification path
```

## 12. Review Gate

Stop after this plan is committed and pushed.

```text
Do not apply v0.15 catalog rows.
Do not edit tools/catalog.py.
Do not edit brain/_catalog_ids.py.
Do not edit brain/invariants.py.
Do not add stream fixtures.
Do not edit brain/ui/ runtime modules.
Do not update README as if stream commands are implemented.
Do not proceed to Step 23 until this plan is explicitly accepted.
```

## Conclusion

This plan is coherent and ready for review. The next campaign step, if
accepted, is:

```text
Step 23 - Apply Phase 3.8 catalog patch
```
