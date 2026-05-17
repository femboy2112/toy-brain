# PHASE2_v1_1_TRACE_KICKOFF.md — Togglable Cognition Trace

This document is the implementation spec for Phase 2 v1.1. It patches `INVARIANT_CATALOG.md` from v0.3 to v0.4, adds a `CognitionTracer` Protocol seam, and ships three backends (`NullTracer`, `MemoryTracer`, `FileTracer`). Purpose: turn opaque pass/fail behavioral runs into inspectable JSONL traces of the brain's full cognitive flow — input → calculation → LLM prompt → LLM response → parse → mode dispatch → state update → invariant check.

The tracer is observation-only. `tick()` output must be byte-identical whether the tracer is present or not.

## Scope

- **Additive only.** No existing invariant changes; no existing fixture changes semantically; no Lean spec touches.
- **One new STRUCTURAL row** in the catalog (I-TRACE-01: observation-only determinism).
- **No new REQUIRED rows.** This is infrastructure for debugging behavioral runs, not a theory-derived obligation.
- **Pluggable backend.** A fourth `CognitionTracer` Protocol seam parallel to `LLMClient`. Three v1.1 backends; future backends (Memory ring buffer, OpenTelemetry export, replay-ready format) can be added without touching the brain.

## Success criterion

`python -m brain.invariants run` reports all v0.3 rows green + the new I-TRACE-01 STRUCTURAL row. New post-patch counts: 84 REQUIRED, 11 STRUCTURAL, 3 NOT-EXERCISED, 12 DEFERRED, 1 OBSERVED.

Plus: `BRAIN_TRACE_PATH=/tmp/trace.jsonl python -m brain.scenario run scenarios/first_scenario_v1.json` produces a JSONL file containing one line per cognition event, schema-conforming to the taxonomy below, end-to-end through the four-tick scenario.

## Catalog patch — v0.3 → v0.4

Bump the banner. Add one row. All v0.3 rows stay unchanged.

### New section: `brain/trace.py` — Cognition trace seam

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-TRACE-01 | Plan convention (Phase 2 v1.1) | The tracer is observation-only. `tick(state, events, client, tracer)` produces identical `(BrainState, TickRecord)` output regardless of which `CognitionTracer` backend is supplied. | Run the first scenario through each of `{NullTracer(), MemoryTracer(), FileTracer(tmp_path)}` with the same MockClient seed; assert all three final `BrainState` values are equal and all three `mode_trace` sequences are identical. | `trace_v1_1.py` | STRUCTURAL |

### Updated summary counts (after patch)

- REQUIRED: 84 (unchanged)
- STRUCTURAL: 11 (was 10; +I-TRACE-01)
- NOT-EXERCISED: 3 (unchanged)
- DEFERRED: 12 (unchanged)
- OBSERVED: 1 (unchanged)
- Total tabular entries: 111 (was 110)
- Fixtures: 14 (was 13; +trace_v1_1.py)

### Update `tools/catalog.py`

Bump STRUCTURAL expected count: 10 → 11.

## `CognitionTracer` architecture

Lives in `brain/trace.py`. Protocol + three backends + a JSON encoder that handles brain-side types.

### Protocol

```python
from typing import Any, Protocol, runtime_checkable
from collections.abc import Mapping

@runtime_checkable
class CognitionTracer(Protocol):
    """Observation-only cognition trace surface.

    Implementations must not affect tick() output. The brain calls record()
    at every interesting boundary; calls to set_tick() / clear_tick() bracket
    each tick so events inside automatically inherit tick_id.
    """

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """Record one event. event_type follows the taxonomy below."""
        ...

    def set_tick(self, tick_id: int) -> None:
        """Set the current tick id; subsequent record() calls auto-tag."""
        ...

    def clear_tick(self) -> None:
        """Clear the current tick id (called at tick.end)."""
        ...

    def close(self) -> None:
        """Flush and release resources. Called by the scenario runner on exit."""
        ...
```

### Three v1.1 backends

**1. `NullTracer`** — the default. Does nothing; zero overhead. Used in fixtures, in CI, and when no trace is requested.

```python
class NullTracer:
    def record(self, event_type, payload): pass
    def set_tick(self, tick_id): pass
    def clear_tick(self): pass
    def close(self): pass
```

**2. `MemoryTracer`** — accumulates events in a list. For inspection in tests and ad-hoc analysis.

```python
class MemoryTracer:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._current_tick_id: int | None = None

    def record(self, event_type, payload):
        event = {
            "type": event_type,
            "timestamp_ns": time.time_ns(),
            **({"tick_id": self._current_tick_id} if self._current_tick_id is not None else {}),
            **dict(payload),
        }
        self.events.append(event)

    def set_tick(self, tick_id): self._current_tick_id = tick_id
    def clear_tick(self): self._current_tick_id = None
    def close(self): pass
```

**3. `FileTracer`** — streams JSONL to disk. One event per line, flushed after every write for crash resilience.

```python
class FileTracer:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")
        self._current_tick_id: int | None = None

    def record(self, event_type, payload):
        event = {
            "type": event_type,
            "timestamp_ns": time.time_ns(),
            **({"tick_id": self._current_tick_id} if self._current_tick_id is not None else {}),
            **dict(payload),
        }
        self._file.write(json.dumps(event, cls=_BrainJSONEncoder) + "\n")
        self._file.flush()

    def set_tick(self, tick_id): self._current_tick_id = tick_id
    def clear_tick(self): self._current_tick_id = None
    def close(self): self._file.close()
```

### JSON encoder for brain types

```python
class _BrainJSONEncoder(json.JSONEncoder):
    """Serialize Fraction, Enum, frozenset, and dataclass instances cleanly.

    Fractions become strings like "1/2" — human-readable, parseable back via
    Fraction("1/2"). Enums become their .name. Frozensets become sorted lists
    (deterministic). Dataclasses become asdict() output recursively.
    """

    def default(self, obj):
        if isinstance(obj, Fraction):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, (frozenset, set)):
            return sorted(obj, key=str)
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        if isinstance(obj, MappingProxyType):
            return dict(obj)
        return super().default(obj)
```

### Factory from environment

```python
def make_tracer_from_env() -> CognitionTracer:
    """If BRAIN_TRACE_PATH is set, return FileTracer pointed at it.
    Otherwise return NullTracer. Single source of truth for the toggle."""
    path = os.environ.get("BRAIN_TRACE_PATH")
    if path:
        return FileTracer(Path(path))
    return NullTracer()
```

## Event taxonomy

JSONL, one event per line. Every event has `type`, `timestamp_ns`, and (when inside a tick) `tick_id`. Event-specific fields listed below. Extra fields are permitted; consumers should ignore unknowns.

### `tick.start`
```json
{
  "type": "tick.start",
  "tick_id": 1,
  "timestamp_ns": 1731600000000000000,
  "events": [{"content_id": "...", "text": "...", "content_state": {...}, "initial_rho": "3/5"}],
  "state_before": {"profile_domain": ["__cogito__"], "msi_contents": ["__cogito__"], "msi_threshold": "1/2", "registry_size": 0, "boundary": []}
}
```

### `tick.end`
```json
{
  "type": "tick.end",
  "tick_id": 1,
  "timestamp_ns": ...,
  "state_after": {...},
  "mode_trace": ["MODE_C"],
  "triggered_mode": "MODE_C",
  "duration_ms": 412
}
```

### `llm.request`
```json
{
  "type": "llm.request",
  "tick_id": 1,
  "content_id": "sunset_on_beach_today",
  "attempt": 1,
  "prompt": "<full prompt text, verbatim>"
}
```

### `llm.response`
```json
{
  "type": "llm.response",
  "tick_id": 1,
  "content_id": "sunset_on_beach_today",
  "attempt": 1,
  "raw": "PRESERVE",
  "latency_ms": 410
}
```

### `llm.retry`
```json
{
  "type": "llm.retry",
  "tick_id": 1,
  "content_id": "...",
  "attempt": 2,
  "reason": "Could not parse 'maybe preserve?' as one of PRESERVE / DAMAGE / NEUTRAL"
}
```

### `llm.cache_hit` / `llm.cache_miss`
```json
{
  "type": "llm.cache_hit",
  "tick_id": 1,
  "content_id": "sunset_on_beach_today",
  "cache_key_prefix": "3f7a2b1c"
}
```

(`cache_key_prefix` is the first 8 hex chars of the SHA256 — enough for debugging without bloating the trace.)

### `parse.success` / `parse.failure`
```json
{
  "type": "parse.success",
  "tick_id": 1,
  "content_id": "...",
  "raw": "PRESERVE",
  "parsed": "PRESERVE"
}
```

### `eval.complete`
```json
{
  "type": "eval.complete",
  "tick_id": 1,
  "content_id": "sunset_on_beach_today",
  "result": "PRESERVE",
  "attempts_consumed": 1,
  "cache_hit": false
}
```

### `mode.dispatch`
```json
{
  "type": "mode.dispatch",
  "tick_id": 1,
  "content_id": "sunset_on_beach_today",
  "eval": "PRESERVE",
  "mode": "MODE_C"
}
```

### `state.update`
```json
{
  "type": "state.update",
  "tick_id": 1,
  "content_id": "sunset_on_beach_today",
  "profile_delta": {
    "added": {"sunset_on_beach_today": "3/5"},
    "modified": {},
    "removed": []
  },
  "msi_delta": {"added": ["sunset_on_beach_today"], "removed": []},
  "boundary_delta": {"added": [], "removed": []}
}
```

### `invariant.check`
```json
{
  "type": "invariant.check",
  "tick_id": 1,
  "source": "post_tick",
  "row_id": "I-MSI-02",
  "passed": true
}
```

(Only emitted by `assert_state_invariants`; per-row pass/fail. On failure, additional `error` field with the violation message.)

### `error`
```json
{
  "type": "error",
  "tick_id": 1,
  "origin": "brain.llm.ptcns_backed",
  "error_type": "ValueError",
  "message": "I-LLM-01 violated: PtCns.eval('foo') failed after 3 attempts. ...",
  "traceback": "..."
}
```

## Plumbing

The tracer is an explicit parameter, threaded through three call sites. Default everywhere is `NullTracer()`.

### `brain/tick.py`

```python
def tick(
    state: BrainState,
    events: list[PerceptEvent],
    client: LLMClient,
    tracer: CognitionTracer = NullTracer(),
    tick_id: int = 0,
) -> tuple[BrainState, TickRecord]:
    tracer.set_tick(tick_id)
    try:
        tracer.record("tick.start", {"events": events, "state_before": _summarize(state)})
        start_ns = time.time_ns()

        # ... existing tick logic, but pass tracer to LLMBackedPtCns construction
        ptcns = LLMBackedPtCns(msi=new_msi, content_texts=new_registry.texts, client=client, tracer=tracer)

        # ... eval each new content
        for event in events:
            result = ptcns.eval(event.content_id)
            tracer.record("eval.complete", {"content_id": event.content_id, "result": result.name, "attempts_consumed": ..., "cache_hit": ...})
            mode = from_eval(result)
            tracer.record("mode.dispatch", {"content_id": event.content_id, "eval": result.name, "mode": mode.name})
            # ... apply mode operator
            tracer.record("state.update", {"content_id": event.content_id, "profile_delta": ..., "msi_delta": ..., "boundary_delta": ...})

        # ... assert_state_invariants emits invariant.check events (see below)
        assert_state_invariants(new_state, tracer=tracer)

        duration_ms = (time.time_ns() - start_ns) // 1_000_000
        tracer.record("tick.end", {"state_after": _summarize(new_state), "mode_trace": [m.name for m in mode_trace], "triggered_mode": triggered_mode.name if triggered_mode else None, "duration_ms": duration_ms})
        return new_state, record
    finally:
        tracer.clear_tick()
```

`assert_state_invariants` gains an optional `tracer` parameter; on each row check, emits `invariant.check`. On raise, also emits `error` before re-raising. Adds to the C6 maintenance contract: when a new row is added, also add its `invariant.check` emission.

### `brain/llm/ptcns_backed.py`

`LLMBackedPtCns.__init__` gains `tracer: CognitionTracer = NullTracer()`. `eval()` emits `llm.request`, `llm.response`, `llm.retry`, `parse.success`, `parse.failure` at the appropriate points.

### `brain/llm/client.py`

`AnthropicAPIClient.eval_consistency` accepts an optional `tracer` parameter (defaults to NullTracer); records latency on successful response. `CachedClient.eval_consistency` accepts tracer and emits `llm.cache_hit` / `llm.cache_miss`.

Alternative: store the tracer at construction time on `CachedClient` and `AnthropicAPIClient`. Cleaner — the LLMBackedPtCns doesn't need to pass tracer through to each call. Pick the constructor-storage option:

```python
class CachedClient:
    def __init__(self, inner: LLMClient, cache_dir: Path = Path("brain/.llm_cache"), tracer: CognitionTracer = NullTracer()) -> None:
        ...

class AnthropicAPIClient:
    def __init__(self, api_key=None, model="claude-sonnet-4-6", base_url=..., max_tokens=256, tracer: CognitionTracer = NullTracer()) -> None:
        ...
```

This is the recommended pattern. The tracer is part of client construction. tick() builds the LLM stack with the same tracer it uses internally.

### `brain/scenario.py`

The scenario runner instantiates the tracer (via env var or CLI flag), constructs the LLM client with it, passes it to tick(), and calls close() at the end:

```python
def run_scenario(spec: ScenarioSpec, client: LLMClient | None = None, tracer: CognitionTracer | None = None) -> ScenarioResult:
    if tracer is None:
        tracer = make_tracer_from_env()
    # ... rest

    try:
        for tick_id, scenario_tick in enumerate(spec.ticks, start=1):
            state, record = tick(state, [event], client, tracer=tracer, tick_id=tick_id)
            # ... accumulate trace
        return result
    finally:
        tracer.close()
```

CLI flag:

```
python -m brain.scenario run scenarios/first_scenario_v1.json --trace /tmp/trace.jsonl
```

If `--trace` is set, it overrides `BRAIN_TRACE_PATH`. If neither is set, `NullTracer()`.

## Toggle semantics summary

| Condition | Tracer used |
|---|---|
| Neither env var nor flag set | `NullTracer()` |
| `BRAIN_TRACE_PATH` env var set | `FileTracer(Path($BRAIN_TRACE_PATH))` |
| `--trace /path` flag passed to CLI | `FileTracer(Path(/path))` (overrides env) |
| Explicit `tracer=...` in code | The supplied tracer (overrides both) |

Fixtures use `NullTracer()` for I-BHV-01 / I-RT-08 / I-RT-09 / I-RT-10 (existing v0.3 fixtures) — no trace overhead in the runner. The new `trace_v1_1.py` fixture explicitly constructs and compares each tracer backend.

## Build order

1. **Patch `INVARIANT_CATALOG.md` to v0.4.** Add I-TRACE-01 row in a new section `brain/trace.py — Cognition trace seam`. Bump banner. Update summary counts. Update `tools/catalog.py` expected STRUCTURAL count.
2. **`brain/trace.py`** — Protocol + `NullTracer` + `MemoryTracer` + `FileTracer` + `_BrainJSONEncoder` + `make_tracer_from_env`.
3. **Update `brain/llm/client.py`** — add `tracer` parameter to `AnthropicAPIClient` and `CachedClient` constructors; emit `llm.request` / `llm.response` / `llm.cache_hit` / `llm.cache_miss` at the right points.
4. **Update `brain/llm/ptcns_backed.py`** — add `tracer` parameter to `LLMBackedPtCns.__init__`; emit `llm.retry` / `parse.success` / `parse.failure` in the retry loop.
5. **Update `brain/tick.py`** — add `tracer` and `tick_id` parameters; emit `tick.start` / `tick.end` / `eval.complete` / `mode.dispatch` / `state.update`. Update `assert_state_invariants` to take optional tracer and emit `invariant.check` per row plus `error` on failure (this is also the C6 maintenance contract extension — new rows added there must also emit `invariant.check`).
6. **Update `brain/scenario.py`** — accept `--trace` CLI flag; consult `make_tracer_from_env` if no explicit flag; pass tracer through; call `tracer.close()` in a `finally`.
7. **New fixture `brain/fixtures/trace_v1_1.py`** — exercises I-TRACE-01. Runs the first scenario through each of the three tracer backends with the same MockClient seed; asserts final BrainState equality and mode_trace equality.
8. **Update `.gitignore`** — add a line for trace output: `*.jsonl` under any path the user is likely to pipe traces into (or just suggest the convention `brain/.trace/` and gitignore that directory).

Per v0 discipline: do not start coding until step 1 lands.

## Verification

1. `python -m tools.catalog counts` → 84 REQUIRED / 11 STRUCTURAL / 3 NOT-EXERCISED / 12 DEFERRED / 1 OBSERVED. Banner says v0.4.
2. `python -m tools.citations verify` → 100/100 (new row has no Lean citation; parser ignores).
3. `python -m tools.import_audit` → still clean (new `brain/trace.py` does not import `brain/tlica/pce.py`).
4. `python -m brain.invariants run` → all 84 REQUIRED green, 11 STRUCTURAL green (including I-TRACE-01), 1 OBSERVED logged.
5. `tools/check_all.sh` exits 0.
6. Smoke test for the trace itself:
   ```sh
   BRAIN_TRACE_PATH=/tmp/test.jsonl python -m brain.scenario run scenarios/first_scenario_v1.json
   wc -l /tmp/test.jsonl   # should be > 30 lines (every event type at least once)
   jq -r '.type' /tmp/test.jsonl | sort -u   # should list every expected event type
   jq 'select(.type == "llm.response") | .raw' /tmp/test.jsonl   # should show four PRESERVE/DAMAGE/NEUTRAL responses
   ```

## Still deferred

Inherited from v0.3 — unchanged. Plus newly out of scope for v1.1:

- **Replay capability.** A trace is currently observation-only; you can't load a JSONL and re-execute the scenario from it. Future v1.2 or v1.3 work — would require capturing seed material (LLM cache state, initial state hash) sufficient to deterministically reproduce.
- **Aggregation / metrics.** Trace files carry raw events with latencies; aggregating into histograms, percentiles, mode-dispatch frequency etc. is a query problem, not a feature. Use `jq` for ad-hoc; build a separate `brain.trace.analyze` tool later if patterns emerge.
- **OpenTelemetry / distributed tracing export.** The architecture supports it (just another backend implementing `CognitionTracer`) but it's not v1.1. Add when there's an actual distributed-system reason.
- **Real-time visualization.** Out of scope; the file is the artifact. Build a separate tool to render JSONL if needed.
- **Trace redaction.** All prompts and responses go to the trace verbatim. If the user is comfortable with that on local disk (the only place a trace can go in v1.1), no redaction is needed. If trace files ever leave the local machine, that's a separate problem to solve.

## What this kickoff does *not* change

- The four TLICA Protocol seams keep their existing v0.2 interfaces.
- The `LLMClient` Protocol seam keeps its v0.3 interface (just gains an optional `tracer` parameter on the two concrete backends' constructors).
- The `PtCnsLike` Protocol from v0.3 is unchanged.
- The functional `tick(state, events, client) → (BrainState, TickRecord)` signature gains optional `tracer` and `tick_id` parameters — both default to safe no-op values. Existing callers (the v0.3 fixtures) continue to work without modification.
- All v0 / Phase 2 v1 inherited deferrals stay deferred.
- The scenario file format is unchanged.
- The cogito sentinel and I-RT-07 are unchanged.
- The `Fraction` numeric convention is unchanged. The trace encoder serializes Fractions as their string form (`"1/2"`) for human readability and roundtrip via `Fraction("1/2")`.

If anything in this kickoff contradicts `INVARIANT_CATALOG.md` v0.4 after patching, the catalog wins.

## Validation checklist for Claude Code

1. `python -m tools.catalog show I-TRACE-01` prints the new row.
2. `python -m tools.catalog list --status STRUCTURAL` returns 11 rows including I-TRACE-01.
3. `python -m brain.invariants run` → I-TRACE-01 passes; all v0.3 rows still pass.
4. `python -c "from brain.trace import NullTracer, MemoryTracer, FileTracer, CognitionTracer; assert isinstance(NullTracer(), CognitionTracer)"` succeeds.
5. `BRAIN_TRACE_PATH=/tmp/test.jsonl python -m brain.scenario run scenarios/first_scenario_v1.json` produces a file. `head -1 /tmp/test.jsonl` is valid JSON with type `tick.start`. `tail -1` is valid JSON with type `tick.end` and `tick_id: 4`.
6. The same run twice with `BRAIN_TRACE_PATH` set to different paths produces traces of the same length and the same sequence of event `type` values (the only differences should be timestamps and latencies).
7. `jq 'select(.type == "llm.cache_miss")' /tmp/test.jsonl` returns four hits on first run with empty cache; zero hits on a second run with warm cache (all `llm.cache_hit` instead).
8. The `trace_v1_1.py` fixture passes — final BrainState equality across all three backends.

Phase 2 v1.1 is complete when checks 1–8 are all green and the CLI smoke test produces inspectable JSONL.
