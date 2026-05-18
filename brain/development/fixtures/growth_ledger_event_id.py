"""Fixture for I-GROW-04: deterministic event_id derivation.

The Growth Ledger ``event_id`` is

    "growth:" + sha256(repr((event_type.value, tick, source.value,
    references, provenance)).encode("utf-8")).hexdigest()[:16]

over the closed immutable acceptance payload. No ``dict`` / ``set`` /
raw object / time / random / PID / hostname / ``id(...)`` / env
participates. The id length is exactly ``len("growth:") + 16 = 23``.
"""
from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path

from brain.development.growth_ledger import (
    GrowthEventSource,
    GrowthEventType,
    derive_growth_event_id,
)
from brain.invariants import register


_GROWTH_LEDGER_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "growth_ledger.py"
)


_NONDETERMINISTIC_CALL_NAMES: frozenset[str] = frozenset({
    "id",
    "open",
})


_NONDETERMINISTIC_CALL_PREFIXES: tuple[str, ...] = (
    "time.",
    "random.",
    "secrets.",
    "uuid.",
    "os.getpid",
    "os.environ",
    "os.urandom",
    "socket.gethostname",
    "platform.",
    "datetime.",
)


def _expected_event_id(
    *,
    event_type: GrowthEventType,
    tick: int,
    source: GrowthEventSource,
    references: tuple[str, ...],
    provenance: str,
) -> str:
    payload = (
        event_type.value,
        tick,
        source.value,
        references,
        provenance,
    )
    digest = sha256(repr(payload).encode("utf-8")).hexdigest()[:16]
    return "growth:" + digest


@register("I-GROW-04", status="REQUIRED")
def check_growth_event_id_deterministic() -> None:
    # Same payload yields the same id (across two consecutive calls).
    payload_args = dict(
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=1,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-1",),
        provenance="stream_append:_dispatch_stream_append",
    )
    id_a = derive_growth_event_id(**payload_args)
    id_b = derive_growth_event_id(**payload_args)
    assert id_a == id_b, (
        f"I-GROW-04 violated: same payload produced different ids "
        f"({id_a!r} vs {id_b!r})"
    )

    # Prefix is always "growth:" and length is exactly 23.
    assert id_a.startswith("growth:"), (
        f"I-GROW-04 violated: id missing 'growth:' prefix ({id_a!r})"
    )
    assert len(id_a) == 23, (
        f"I-GROW-04 violated: id length {len(id_a)} != 23 ({id_a!r})"
    )

    # The derived id matches the locked formula exactly.
    expected = _expected_event_id(**payload_args)
    assert id_a == expected, (
        f"I-GROW-04 violated: derived id {id_a!r} does not match the "
        f"locked sha256-over-closed-payload formula (expected {expected!r})"
    )

    # Different payloads yield different ids.
    variants = [
        dict(payload_args, tick=2),
        dict(payload_args, event_type=GrowthEventType.TICK_SUCCEEDED),
        dict(payload_args, source=GrowthEventSource.STEP_DISPATCH),
        dict(payload_args, references=("strm-chunk-2",)),
        dict(payload_args, references=()),
        dict(payload_args, references=("strm-chunk-1", "promo-strm-chunk-1")),
        dict(payload_args, provenance="step_dispatch:_dispatch_step"),
    ]
    seen_ids = {id_a}
    for variant in variants:
        variant_id = derive_growth_event_id(**variant)
        assert variant_id not in seen_ids, (
            f"I-GROW-04 violated: variant payload collided with prior id "
            f"({variant!r} -> {variant_id!r})"
        )
        seen_ids.add(variant_id)

    # Closed input shape: derive_growth_event_id only accepts the five
    # fixed keyword arguments. Calling with an extra kwarg raises.
    try:
        derive_growth_event_id(  # type: ignore[call-arg]
            event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
            tick=1,
            source=GrowthEventSource.STREAM_APPEND,
            references=("strm-chunk-1",),
            provenance="x",
            extra="should-not-be-accepted",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-GROW-04 violated: derive_growth_event_id accepted an "
            "extra keyword argument"
        )

    # event_type / source must be the closed enums.
    try:
        derive_growth_event_id(
            event_type="stream_chunk_accepted",  # type: ignore[arg-type]
            tick=1,
            source=GrowthEventSource.STREAM_APPEND,
            references=("strm-chunk-1",),
            provenance="x",
        )
    except ValueError as exc:
        assert "I-GROW-04" in str(exc)
    else:
        raise AssertionError(
            "I-GROW-04 violated: derive_growth_event_id accepted a "
            "str for event_type"
        )

    try:
        derive_growth_event_id(
            event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
            tick=1,
            source="stream_append",  # type: ignore[arg-type]
            references=("strm-chunk-1",),
            provenance="x",
        )
    except ValueError as exc:
        assert "I-GROW-04" in str(exc)
    else:
        raise AssertionError(
            "I-GROW-04 violated: derive_growth_event_id accepted a "
            "str for source"
        )

    # Static check: no nondeterministic call appears in growth_ledger.py
    # on any path that contributes to the event_id derivation.
    assert _GROWTH_LEDGER_SOURCE_PATH.exists(), (
        "I-GROW-04 violated: growth_ledger.py not found at "
        f"{_GROWTH_LEDGER_SOURCE_PATH}"
    )
    source_text = _GROWTH_LEDGER_SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text, filename=str(_GROWTH_LEDGER_SOURCE_PATH))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name in _NONDETERMINISTIC_CALL_NAMES:
            raise AssertionError(
                "I-GROW-04 violated: nondeterministic call "
                f"{name!r} appears at line {node.lineno}"
            )
        for prefix in _NONDETERMINISTIC_CALL_PREFIXES:
            if name.startswith(prefix):
                raise AssertionError(
                    "I-GROW-04 violated: nondeterministic call "
                    f"{name!r} appears at line {node.lineno}"
                )

    # No dict / set literal participates in the id derivation path.
    # Defense-in-depth string scan.
    for needle in (
        "time.time",
        "time.monotonic",
        "random.",
        "secrets.",
        "uuid.",
        "os.getpid",
        "os.environ",
        "os.urandom",
        "socket.gethostname",
        "platform.",
        "datetime.",
    ):
        assert needle not in source_text, (
            "I-GROW-04 violated: growth_ledger.py contains nondeterministic "
            f"text {needle!r}"
        )


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""
