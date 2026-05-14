"""Cognition trace seam (Phase 2 v1.1).

Catalog row owned: I-TRACE-01 (STRUCTURAL).

A ``CognitionTracer`` Protocol with three v1.1 backends:
  - ``NullTracer``  — does nothing; zero overhead. The default.
  - ``MemoryTracer``— accumulates events in a list for inspection.
  - ``FileTracer``  — streams JSONL to disk with one event per line.

The tracer is **observation-only**: ``tick()`` output must be byte-identical
regardless of which backend is supplied. I-TRACE-01 enforces this by running
the first scenario through all three backends and comparing the resulting
``BrainState`` and ``mode_trace`` for equality.

Toggle:
  - ``BRAIN_TRACE_PATH`` env var → ``FileTracer(Path($BRAIN_TRACE_PATH))``.
  - ``--trace /path`` CLI flag on ``brain.scenario`` → same, overrides env.
  - Otherwise: ``NullTracer()``.

Per the kickoff: ``brain/trace.py`` does not import ``brain/tlica/pce.py``;
I-PCE-05 is unaffected. It is also independent of ``brain/llm/`` and
``brain/tick.py`` (callers thread the tracer through; the trace module
only knows about transport).
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from enum import Enum
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CognitionTracer(Protocol):
    """Observation-only cognition trace surface.

    Implementations must not affect ``tick()`` output. The brain calls
    ``record()`` at every interesting boundary; ``set_tick()`` /
    ``clear_tick()`` bracket each tick so events inside automatically
    inherit ``tick_id``.
    """

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """Record one event. ``event_type`` follows the kickoff taxonomy."""
        ...

    def set_tick(self, tick_id: int) -> None:
        """Set the current tick id; subsequent ``record()`` calls auto-tag."""
        ...

    def clear_tick(self) -> None:
        """Clear the current tick id (called at ``tick.end``)."""
        ...

    def close(self) -> None:
        """Flush and release resources. Called by the scenario runner on exit."""
        ...


# ---------------------------------------------------------------------------
# NullTracer — default. Zero overhead.
# ---------------------------------------------------------------------------


class NullTracer:
    """No-op tracer. Used everywhere a real trace isn't requested."""

    __slots__ = ()

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        pass

    def set_tick(self, tick_id: int) -> None:
        pass

    def clear_tick(self) -> None:
        pass

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# MemoryTracer — accumulates events in a list.
# ---------------------------------------------------------------------------


class MemoryTracer:
    """In-memory tracer. Records events into ``self.events`` for inspection."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._current_tick_id: int | None = None

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        event: dict[str, Any] = {
            "type": event_type,
            "timestamp_ns": time.time_ns(),
        }
        if self._current_tick_id is not None:
            event["tick_id"] = self._current_tick_id
        event.update(payload)
        self.events.append(event)

    def set_tick(self, tick_id: int) -> None:
        self._current_tick_id = tick_id

    def clear_tick(self) -> None:
        self._current_tick_id = None

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# FileTracer — JSONL stream with crash-resilient flush.
# ---------------------------------------------------------------------------


class FileTracer:
    """Stream-to-disk JSONL tracer. One event per line; flush after every write."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")
        self._current_tick_id: int | None = None
        self._closed = False

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("FileTracer.record called after close()")
        event: dict[str, Any] = {
            "type": event_type,
            "timestamp_ns": time.time_ns(),
        }
        if self._current_tick_id is not None:
            event["tick_id"] = self._current_tick_id
        event.update(payload)
        self._file.write(json.dumps(event, cls=_BrainJSONEncoder) + "\n")
        self._file.flush()

    def set_tick(self, tick_id: int) -> None:
        self._current_tick_id = tick_id

    def clear_tick(self) -> None:
        self._current_tick_id = None

    def close(self) -> None:
        if not self._closed:
            self._file.close()
            self._closed = True


# ---------------------------------------------------------------------------
# JSON encoder for brain types.
# ---------------------------------------------------------------------------


class _BrainJSONEncoder(json.JSONEncoder):
    """Serialize Fraction, Enum, frozenset, dataclass, and MappingProxyType.

    - ``Fraction`` → ``str(frac)``  (parseable back via ``Fraction("1/2")``).
    - ``Enum``     → ``obj.name``.
    - ``frozenset``/``set`` → sorted list (deterministic).
    - dataclass instance → ``asdict(obj)`` recursively.
    - ``MappingProxyType`` → plain dict.
    """

    def default(self, obj: Any) -> Any:  # noqa: D401 — JSON contract
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


# ---------------------------------------------------------------------------
# Environment factory.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# SafeTracer — fail-open wrapper (Phase 2 v1.2; implements I-TRACE-02).
# ---------------------------------------------------------------------------


class SafeTracer:
    """Wraps a ``CognitionTracer`` so backend failures never propagate.

    Implements I-TRACE-02: ``tick()`` output must be identical whether
    ``tracer.record`` (or ``set_tick`` / ``clear_tick`` / ``close``)
    raises or not. This is the runtime enforcement of the
    observation-only guarantee already documented in I-TRACE-01 — the
    fixture exercises three backends under normal conditions; the
    SafeTracer wrapper makes the kernel robust to backend failures
    (full disk, permission denied, write-after-close, …).

    Construct directly via ``SafeTracer(inner)``; the factory
    ``make_tracer_from_env`` wraps automatically by default.
    """

    __slots__ = ("_inner",)

    def __init__(self, inner: CognitionTracer) -> None:
        self._inner = inner

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        try:
            self._inner.record(event_type, payload)
        except Exception:  # noqa: BLE001 — I-TRACE-02: never propagate
            pass

    def set_tick(self, tick_id: int) -> None:
        try:
            self._inner.set_tick(tick_id)
        except Exception:  # noqa: BLE001
            pass

    def clear_tick(self) -> None:
        try:
            self._inner.clear_tick()
        except Exception:  # noqa: BLE001
            pass

    def close(self) -> None:
        try:
            self._inner.close()
        except Exception:  # noqa: BLE001
            pass


def make_tracer_from_env(*, safe: bool = True) -> CognitionTracer:
    """Return ``FileTracer($BRAIN_TRACE_PATH)`` if set, otherwise ``NullTracer()``.

    Single source of truth for the env-driven toggle. Callers that want
    to override (e.g. CLI ``--trace``) construct the tracer directly.

    Phase 2 v1.2 (P1): wraps the inner tracer in :class:`SafeTracer` by
    default so backend exceptions are swallowed (I-TRACE-02). Pass
    ``safe=False`` to opt out (debugging only — bare tracer exceptions
    will then propagate into ``tick()``).
    """
    path = os.environ.get("BRAIN_TRACE_PATH")
    inner: CognitionTracer = FileTracer(Path(path)) if path else NullTracer()
    return SafeTracer(inner) if safe else inner


__all__ = [
    "CognitionTracer",
    "NullTracer",
    "MemoryTracer",
    "FileTracer",
    "SafeTracer",
    "make_tracer_from_env",
]
