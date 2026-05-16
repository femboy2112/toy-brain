# PHASE3_8_OPERATOR_STREAM_INTERACTION_AUDIT.md

## 1. Purpose

Audit the complete Phase 3.8 Operator Stream Interaction surface
(`/stream`, `/stream-summary`, `/stream-candidates`,
`/stream-promote`, `/step`) together with the Phase 3.8b LLM
Runtime Toggle that selects which `LLMClient` backs `tick()`. This
document is an audit artifact: it does not edit any runtime module,
fixture, catalog row, or registry.

```text
Verdict for Step 25: PASS
```

## 2. Baseline

```text
Catalog version:  v0.16
REQUIRED:        178
STRUCTURAL:       64
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         12
Total tabular:   275
Total fixtures:   91

Landed campaign steps:
  Step 1   repo-state sync
  Steps 2-9    Phase 3.6 Reflective Inspection         (audit PASS)
  Steps 10-18  Phase 3.7 Text Stream Ingress           (audit PASS)
  Steps 19-24  Phase 3.8 Operator Stream Interaction   (this audit)
  Steps 24A-24G Phase 3.8b LLM Runtime Toggle          (audit PASS)
  Step 25  this audit
```

Required source artifacts:

```text
INVARIANT_CATALOG.md (v0.16)
PHASE3_8_OPERATOR_STREAM_INTERACTION_SYNTHESIS.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_KICKOFF.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_CORRIGENDA.md
PHASE3_8_OPERATOR_STREAM_INTERACTION_CATALOG_PATCH_PLAN.md
PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md
brain/ui/command_line.py
brain/ui/commands.py
brain/ui/session.py
brain/ui/snapshot.py
brain/ui/render.py
brain/ui/llm_runtime.py
brain/ui/__main__.py
brain/development/text_stream.py
brain/ui/fixtures/stream_*.py
brain/ui/fixtures/llm_runtime_*.py
brain/development/fixtures/text_stream_*.py
```

## 3. /stream — TextStreamHistory append only

```text
Audit:    Dispatching OperatorCommand.STREAM_APPEND constructs one
          TextStreamChunk with TextStreamSource.OPERATOR via the
          accepted Phase 3.7 constructor and returns updated
          session-local stream state. BrainState / ScalarProfile /
          MSI / PtCns / ContentRegistry / latest_tick / tick_counter /
          OutputHistory / WorldletHistory / ProtoBasicHistory /
          ExpressionHistory / OperatorTranscript /
          OperatorSession.event_queue identities are unchanged.

Evidence: brain/ui/session.py — _dispatch_stream() builds a chunk via
          make_text_stream_chunk and appends through
          TextStreamHistory.append on the session's local stream
          state container. The dispatch path does NOT call tick(),
          does NOT touch BrainState, and does NOT append to
          OperatorSession.event_queue.

Row:      I-UISTRM-03 REQUIRED.
Fixture:  brain/ui/fixtures/stream_session_append.py — PASS.

Status:   PASS.
```

## 4. /stream-summary and /stream-candidates — read-only views

```text
Audit:    Dispatching OperatorCommand.INSPECT_STREAM_SUMMARY and
          OperatorCommand.INSPECT_STREAM_CANDIDATES selects view
          state on OperatorSession; before and after dispatch,
          local stream history identity, candidate records,
          BrainState, source histories, event_queue, latest_tick,
          and tick_counter are unchanged. Neither dispatch calls
          tick().

Evidence: brain/ui/session.py routes both verbs into
          read-only view selection; no mutation occurs. The
          Phase 3.7 substrate's extract_stream_features /
          extract_segment_candidates / make_stream_pattern /
          make_stream_promotion_candidate constructors are pure.

Rows:     I-UISTRM-04 REQUIRED (summary read-only),
          I-UISTRM-05 REQUIRED (candidates read-only).
Fixture:  brain/ui/fixtures/stream_summary_candidates.py — PASS.

Status:   PASS.
```

## 5. /stream-promote — queue exactly one validated candidate

```text
Audit:    Dispatching OperatorCommand.STREAM_PROMOTE resolves one
          explicit StreamPromotionCandidate by candidate_id,
          converts it to one QueuePerceptPayload through the
          existing constructor-bounded path, and enqueues it
          through OperatorEventQueue.enqueue. The dispatch does
          NOT call tick(), does NOT call dequeue, does NOT touch
          private queue storage directly, and does NOT mutate
          BrainState. On success, OperatorSession.event_queue
          length increases by exactly one; on failure, length is
          unchanged.

Evidence: brain/ui/session.py — _dispatch_stream_promote() looks up
          the candidate, hands it to the QueuePerceptPayload
          constructor (PerceptEvent-validation-checked), and calls
          OperatorSession.event_queue.enqueue exactly once. The
          tick path is never invoked.

Row:      I-UISTRM-06 REQUIRED.
Fixture:  brain/ui/fixtures/stream_promotion_queue.py — PASS.

Status:   PASS.
```

## 6. /step — only tick route

```text
Audit:    Across /stream, /stream-summary, /stream-candidates, and
          /stream-promote dispatches, OperatorSession.tick_counter,
          OperatorSession.latest_tick, and the underlying
          BrainState identity are unchanged. Only
          OperatorCommand.STEP_TICK reaches the existing
          _dispatch_step route that invokes the public tick()
          entrypoint with the queued events.

Evidence: brain/ui/session.py — _dispatch_step is the sole path
          that imports brain.tick.tick at function scope and
          invokes it. No stream-route dispatch contains a tick
          import or call.

Row:      I-UISTRM-07 REQUIRED.
Fixture:  brain/ui/fixtures/stream_tick_boundary.py — PASS.

Status:   PASS.
```

## 7. LLM toggle integration (Phase 3.8b)

```text
Audit:    The LLM runtime mode is selected via parse_llm_runtime_args
          before any session / curses initialization. Default mode
          remains OFFLINE; the selected client enters tick()
          through run_curses(session, client=..., ...). No second
          classification path is introduced. --print-once remains
          independent of the selected client.

Evidence: brain/ui/__main__.py main() — resolves the config and
          builds the client via build_llm_client_from_config
          before constructing the session and dispatching to
          run_curses. The print-once and check-terminal branches
          short-circuit before factory invocation. The startup
          line `brain.ui: llm runtime mode = <mode> (<explanation>)`
          is printed to stdout on the launch path.

Rows:     I-LLMTOG-01..15 (Phase 3.8b audit covers in detail).
Audit:    PHASE3_8B_LLM_RUNTIME_TOGGLE_AUDIT.md — PASS.

Status:   PASS (offline default preserved; explicit opt-in only).
```

## 8. Failure isolation

```text
Audit:    Malformed /stream input, over-bound /stream text,
          non-printable text, unknown /stream-promote candidate_id,
          candidate-to-payload constructor rejection, PerceptEvent
          validation failure, and a full OperatorEventQueue all
          surface as bounded local UI status/error text on
          OperatorSession; BrainState / ScalarProfile / MSI / PtCns /
          ContentRegistry / latest_tick / tick_counter / source
          histories / OperatorTranscript / event_queue length are
          unchanged. Only a successful /stream-promote increases
          event_queue length by exactly one.

Evidence: brain/ui/command_line.py — LocalCommandLine.parse returns
          a LocalCommandError for malformed lines and over-bound
          payloads, without partially mutating session state.
          brain/ui/session.py — _dispatch_stream / _dispatch_stream
          _promote / _dispatch_stream_summary / _dispatch_stream
          _candidates catch ValueError from constructors and
          surface a bounded printable status message; no exception
          escapes into the curses wrapper.

Row:      I-UISTRM-08 REQUIRED.
Fixture:  brain/ui/fixtures/stream_failure_isolation.py — PASS.

Status:   PASS.
```

## 9. Static audit / structural properties

```text
Audit:    Stream snapshots and render output are deterministic
          and read-only (I-UISTRM-09); stream session state is
          resource-free and local (I-UISTRM-11); stream UI
          records are immutable display / payload values
          (I-UISTRM-12); the static AST audit over the Phase 3.8
          additions in commands.py / command_line.py / session.py /
          snapshot.py / render.py / stream_* fixtures rejects
          language / truth / social / agency / Mode B / model-backed
          surfaces (I-UISTRM-10, I-UISTRM-13, I-UISTRM-15) and
          confirms constant parity with the Phase 3.7 substrate
          (I-UISTRM-14).

Evidence: brain/ui/fixtures/stream_snapshot_render.py,
          stream_session_resource_audit.py,
          stream_static_audit.py, stream_constant_parity.py — all
          pass under the runner.

Rows:     I-UISTRM-09..15 (REQUIRED + STRUCTURAL).
Status:   PASS.
```

## 10. OBSERVED scripted walk

```text
Audit:    A deterministic scripted operator session
          (/stream hello world, /stream hello world,
          /stream-summary, /stream-candidates,
          /stream-promote <candidate_id>, /step, /tick) over an
          injected deterministic tick client records parser
          results, dispatched OperatorSession routes, stream
          history counts, candidate queueing through
          OperatorEventQueue.enqueue, TickRecord production after
          /step only, and absence of kernel-boundary leaks; the
          row is OBSERVED and cannot fail the runner.

Documented walk: see Step 26 dry-run document.

Row:      I-UISTRM-16 OBSERVED.
Status:   OBSERVED (audit-cited; not a runner gate). The dry-run
          document in Step 26 will exercise the walk explicitly.
```

## 11. NOT-EXERCISED guard

```text
Audit:    No Phase 3.8 Operator TUI stream save, export,
          serialization, trace weaving, scenario weaving, or
          write-to-disk path exists in this campaign. The static
          audit rejects forbidden imports (pathlib write paths,
          tempfile, shutil) that would enable such a path.

Row:      I-UISTRM-17 NOT-EXERCISED.
Status:   PASS (placeholder is in place; no path exists).
```

## 12. Full gate

```text
Required final validation (run on the post-Step-24G tree):

  python3 -m tools.catalog counts
    -> Banner / Actual / Expected agree on
       REQUIRED=178, STRUCTURAL=64, NOT-EXERCISED=9,
       DEFERRED=12, OBSERVED=12.

  python3 -m tools.citations verify
    -> Verified 100 citations. All catalog citations resolve in
       lean_reference/.

  python3 -m tools.import_audit
    -> I-PCE-05: agency.py is clean of pce imports.

  python3 -m brain.invariants run
    -> 249 rows checked
       REQUIRED green: 178 · REQUIRED red: 0
       STRUCTURAL green: 64 · STRUCTURAL red: 0
       OBSERVED: 7 pass / 0 fail
       gate failures: 0

  bash tools/check_all.sh
    -> All checks passed.

All gates green.
```

## 13. Verdict

```text
PASS

Phase 3.8 Operator Stream Interaction is implemented per the
accepted synthesis, kickoff, corrigenda, and catalog patch plan.
All I-UISTRM-01..15 rows are green; I-UISTRM-16 OBSERVED is
documented; I-UISTRM-17 NOT-EXERCISED guard is in place. The
Phase 3.8b LLM Runtime Toggle integrates cleanly: default offline
behavior is preserved, model-backed modes are explicit opt-in,
and the selected client enters tick() through the existing
run_curses(session, client=..., ...) seam. /step remains the
only route that calls tick().

Recommended next steps:

  Step 26  PHASE3_TEXT_INTERACTION_DRY_RUN.md
  Step 27  open PR to main
```
