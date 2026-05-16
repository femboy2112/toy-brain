# PHASE3_TEXT_INTERACTION_DRY_RUN.md

## 1. Purpose

Document the end-to-end deterministic local operator session for the
Phase 3.6 / 3.7 / 3.8 / 3.8b campaign track:

- Phase 3.6 Reflective Inspection (read-only)
- Phase 3.7 Text Stream Ingress (substrate)
- Phase 3.8 Operator Stream Interaction (typed UI routes)
- Phase 3.8b LLM Runtime Toggle (explicit opt-in)

The dry run targets the OBSERVED row `I-UISTRM-16` (scripted stream
interaction walk) and shows how the `/stream-promote` route bridges
the Phase 3.7 substrate into the existing `OperatorEventQueue` and
how `/step` consumes that queued event through the public `tick()`
path. The default `--llm-mode offline` is exercised throughout; an
optional model-backed launch example follows at the end.

## 2. Baseline

```text
Catalog version:  v0.16
Total fixtures:   91
Runner state:     all green
Default LLM mode: offline (OfflineStandInClient)
```

## 3. Scripted offline walk

The walk uses the deterministic offline stand-in client. Every
command is parsed by `brain.ui.command_line.LocalCommandLine.parse`
and dispatched through `OperatorSession.dispatch`. No file is
mutated; no network call is made; no subprocess is spawned.

```text
Setup:
  session = build_default_session()
  client  = OfflineStandInClient()
  parser  = LocalCommandLine()
```

Command sequence:

```text
> /stream hello world
  view=stream_summary
  status="stream chunk 'strm-chunk-1' appended (history size = 1)"
  stream_history.chunks: 1
  stream_candidates: 1
  event_queue: 0
  tick_counter: 0

> /stream hello world
  view=stream_summary
  status="stream chunk 'strm-chunk-2' appended (history size = 2)"
  stream_history.chunks: 2
  stream_candidates: 2
  event_queue: 0
  tick_counter: 0

> /stream-summary
  view=stream_summary
  status="view = stream_summary"
  stream_history.chunks: 2
  stream_candidates: 2
  event_queue: 0
  tick_counter: 0

> /stream-candidates
  view=stream_candidates
  status="view = stream_candidates"
  stream_history.chunks: 2
  stream_candidates: 2  (ids: promo-strm-chunk-1, promo-strm-chunk-2)
  event_queue: 0
  tick_counter: 0

> /stream-promote promo-strm-chunk-1
  view=queue
  status="promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)"
  stream_history.chunks: 2
  stream_candidates: 2
  event_queue: 1
  tick_counter: 0

> /step
  view=tick
  status="tick 1 ok (MODE_C)"
  stream_history.chunks: 2
  stream_candidates: 2
  event_queue: 0
  tick_counter: 1

> /tick
  view=tick
  status="view = tick"
  stream_history.chunks: 2
  stream_candidates: 2
  event_queue: 0
  tick_counter: 1
```

Observations:

```text
- /stream appends to session-local TextStreamHistory only;
  event_queue and tick_counter are unchanged after each /stream.
- /stream-summary and /stream-candidates are read-only; only
  active_view + status_message change.
- /stream-promote increases event_queue length by exactly one and
  does not call tick(); tick_counter remains 0.
- /step is the only command that calls tick(); the queue drops
  from 1 -> 0 and tick_counter increments from 0 -> 1.
- /tick is a read-only inspector view; nothing mutates.
- The promotion-candidate ids are deterministic: the Phase 3.7
  substrate produces candidate_id = "promo-<chunk_id>" so the
  walk above is reproducible across runs.
```

## 4. Optional model-backed launch examples

These are NOT run as REQUIRED or STRUCTURAL fixtures and they are
NOT exercised by `bash tools/check_all.sh`. They are operator-side
inspection commands; the runner gate stays clean with no
`ANTHROPIC_API_KEY`, no `BRAIN_ANTHROPIC_API_KEY`, and no `claude`
executable on PATH.

```bash
# Anthropic API mode (requires a valid key):
export BRAIN_ANTHROPIC_API_KEY=<your-key>
python3 -m brain.ui --llm-mode anthropic-api

# Anthropic API + on-disk cache (writes under brain/.llm_cache/):
python3 -m brain.ui \
    --llm-mode anthropic-api \
    --llm-anthropic-api-key <your-key> \
    --llm-enable-cache

# Claude CLI mode (requires the `claude` CLI on PATH):
python3 -m brain.ui --llm-mode claude-cli

# Mock mode (deterministic canned responses; no network, no shell):
python3 -m brain.ui \
    --llm-mode mock \
    --llm-mock-response PRESERVE \
    --llm-mock-response PRESERVE
```

Expected behavior:

```text
- On launch, the entrypoint prints one informational line to
  stdout:

    brain.ui: llm runtime mode = <mode> (<explanation>)

  where <explanation> is one of:

    "default offline stand-in; no network, no shell"
    "deterministic mock; no network, no shell"
    "anthropic-api; cache=<on|off>"
    "claude-cli; executable=<path>; cache=<on|off>"

- After the launch line, the curses TUI opens. The selected client
  is passed to run_curses(session, client=..., ...). Subsequent
  /step commands invoke tick() with that client.

- --print-once short-circuits before the factory; you can confirm
  the resolved mode without launching the TUI:

    python3 -m brain.ui --print-once --llm-mode mock \
        --llm-mock-response PRESERVE

  This renders one deterministic frame to stdout and exits.

- Bad configurations fail locally before any session / curses
  init:

    python3 -m brain.ui --llm-mode anthropic-api
      brain.ui: llm runtime error: mode 'anthropic-api' requires
      --llm-anthropic-api-key, BRAIN_ANTHROPIC_API_KEY, or
      ANTHROPIC_API_KEY

    python3 -m brain.ui --llm-mode claude-cli \
        --llm-claude-cli-executable /no/such/path
      brain.ui: llm runtime error: mode 'claude-cli' requires
      executable '/no/such/path' on PATH

    python3 -m brain.ui --llm-mode mock
      brain.ui: llm runtime error: mode 'mock' requires at least
      one --llm-mock-response

    python3 -m brain.ui --llm-mode bogus
      brain.ui: llm runtime error: unknown --llm-mode: 'bogus';
      expected one of {offline, mock, anthropic-api, claude-cli}
```

## 5. Recovery paths

```text
- A failed /stream-promote (unknown candidate_id, full queue,
  constructor rejection) records a bounded local UI status / error
  message on OperatorSession and does NOT change event_queue
  length, BrainState identity, latest_tick, or tick_counter. The
  operator can re-run the command with a corrected candidate_id.

- A failed /step (empty queue, missing client argument) similarly
  records a local error without mutating any kernel container.

- Ctrl-C from the curses wrapper exits cleanly via the documented
  KeyboardInterrupt path.

- A model-backed eval_consistency failure (HTTP error, subprocess
  timeout) raises a transport-level RuntimeError that the kernel
  treats as a retry input to LLMBackedPtCns; the LLM runtime
  toggle is unrelated to retry semantics.
```

## 6. Catalog rows exercised

```text
Stream substrate (Phase 3.7):
  I-STRM-01..15  REQUIRED + STRUCTURAL
  I-STRM-16      OBSERVED (aggregate TextStreamHistory walk)
  I-STRM-17      NOT-EXERCISED

Stream UI (Phase 3.8):
  I-UISTRM-01..15  REQUIRED + STRUCTURAL
  I-UISTRM-16      OBSERVED (this walk's primary target)
  I-UISTRM-17      NOT-EXERCISED

LLM toggle (Phase 3.8b):
  I-LLMTOG-01..13  REQUIRED + STRUCTURAL
  I-LLMTOG-14      OBSERVED (optional real model-backed smoke;
                              documented in section 4 above)
  I-LLMTOG-15      NOT-EXERCISED
```

## 7. Reproducibility

The deterministic offline walk in section 3 can be reproduced
exactly by:

```python
from brain.ui.__main__ import build_default_session, OfflineStandInClient
from brain.ui.command_line import LocalCommandLine

session = build_default_session()
client  = OfflineStandInClient()
parser  = LocalCommandLine()

for line in (
    "/stream hello world",
    "/stream hello world",
    "/stream-summary",
    "/stream-candidates",
    f"/stream-promote {session.stream_candidates[0].candidate_id}"
        if False else "/stream-promote promo-strm-chunk-1",
    "/step",
    "/tick",
):
    cmd = parser.parse(line)
    if hasattr(cmd, "kind"):
        session.dispatch(cmd, client=client)
```

The stream chunk ids (`strm-chunk-1`, `strm-chunk-2`) and the
promotion candidate ids (`promo-strm-chunk-1`,
`promo-strm-chunk-2`) are deterministic across runs because the
Phase 3.7 substrate uses a monotonic per-session counter on
`OperatorSession.stream_chunk_serial`.

## 8. Conclusion

The end-to-end loop from operator-typed text into the public
`tick()` path through the explicit `/stream-promote` bridge is
operational, deterministic, and audit-clean. The default
`--llm-mode offline` produces no network / shell / file activity;
the optional model-backed modes are explicit opt-in via the
documented CLI flags.
