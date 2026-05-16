"""Fixture for I-STRM-10: text-stream ops do not call tick / append to event_queue."""
from __future__ import annotations

import ast
from pathlib import Path

from brain.development.text_stream import (
    TextStreamHistory,
    TextStreamSource,
    extract_segment_candidates,
    extract_stream_features,
    make_stream_pattern,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.session import OperatorSession


_TEXT_STREAM_SOURCE_PATH = Path(__file__).resolve().parent.parent / "text_stream.py"


def _collect_call_names(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                parts: list[str] = [func.attr]
                cur: ast.AST | None = func.value
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                names.append(".".join(reversed(parts)))
    return names


def _collect_import_targets(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            out.append("." * node.level + (node.module or ""))
    return out


@register("I-STRM-10", status="REQUIRED")
def check_text_stream_does_not_tick() -> None:
    # Static audit: text_stream.py does not import tick / event queue / TLICA
    # and never names ``tick`` as a call target.
    assert _TEXT_STREAM_SOURCE_PATH.exists(), (
        f"I-STRM-10 violated: text_stream.py not found at {_TEXT_STREAM_SOURCE_PATH}"
    )
    tree = ast.parse(
        _TEXT_STREAM_SOURCE_PATH.read_text(encoding="utf-8"),
        filename=str(_TEXT_STREAM_SOURCE_PATH),
    )
    imports = _collect_import_targets(tree)
    for forbidden in (
        "brain.tick",
        "brain.tlica",
        "brain.ui",
        "brain.ui.session",
        "brain.llm",
    ):
        for imp in imports:
            bare = imp.lstrip(".")
            assert not (bare == forbidden or bare.startswith(forbidden + ".")), (
                f"I-STRM-10 violated: text_stream.py imports {imp!r}"
            )
    calls = _collect_call_names(tree)
    for name in calls:
        # No bare `tick(...)` or `OperatorEventQueue.append(...)` from
        # text_stream.py.
        assert name != "tick", (
            "I-STRM-10 violated: text_stream.py calls tick()"
        )
        assert "event_queue.append" not in name, (
            f"I-STRM-10 violated: text_stream.py calls {name!r}"
        )
        assert not name.endswith(".tick"), (
            f"I-STRM-10 violated: text_stream.py calls {name!r}"
        )

    # Behavioral audit: a fresh OperatorSession is untouched across a
    # complete text-stream walk.
    session = OperatorSession(state=initial_state())
    queue_before = session.event_queue
    items_before = queue_before.snapshot()
    len_before = len(items_before)

    chunk = make_text_stream_chunk(
        chunk_id="chunk:notick",
        text="hello\nworld",
        source=TextStreamSource.OPERATOR,
        provenance="origin:operator",
    )
    history = TextStreamHistory().append(chunk)
    extract_stream_features(chunk)
    extract_segment_candidates(chunk)
    pattern = make_stream_pattern(
        pattern_id="pat:notick",
        signature=("hello",),
        recurrence_count=2,
    )
    make_stream_promotion_candidate(
        candidate_id="pc:notick",
        target_content_id="content:notick",
        source=TextStreamSource.OPERATOR,
        chunk_id=chunk.chunk_id,
        text="hello",
        provenance="origin:operator",
        pattern_id=pattern.pattern_id,
    )

    assert session.event_queue is queue_before
    assert len(session.event_queue) == len_before
    assert session.event_queue.snapshot() == items_before
    assert session.tick_counter == 0
    assert session.latest_tick is None
    assert len(history.chunks) == 1
