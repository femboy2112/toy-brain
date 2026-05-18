"""Phase 3.14 cache observability fixture.

Drives:

* ``I-LLMCACHE-13`` (REQUIRED) — L1 / L2 observability emits bounded
  tracer events without raw prompt / response / secret / full key.
"""
from __future__ import annotations

import tempfile
from fractions import Fraction
from pathlib import Path

from brain.invariants import register
from brain.llm.client import CachedClient
from brain.llm.ptcns_backed import LLMBackedPtCns
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval
from brain.trace import MemoryTracer


class _SequentialClient:
    def __init__(self, responses: list[str]) -> None:
        self._iter = iter(responses)
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return next(self._iter)


def _make_msi() -> tuple:
    profile = make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    texts = {
        ContentID("anchor_a"): "anchor a description",
        ContentID("new_x"): "the new content under evaluation",
        ContentID("new_y"): "the new content under evaluation",  # same text
    }
    return msi, texts


_ALLOWED_L1_EVENT_FIELDS: frozenset[str] = frozenset({
    "type",
    "timestamp_ns",
    "tick_id",
    "cache_key_prefix",
})

_ALLOWED_L2_EVENT_FIELDS: frozenset[str] = frozenset({
    "type",
    "timestamp_ns",
    "tick_id",
    "content_id",
    "key_prefix",
    "reason",
})

_FORBIDDEN_PAYLOAD_KEYS: frozenset[str] = frozenset({
    "prompt",
    "response",
    "raw",
    "error",
    "secret",
    "api_key",
    "headers",
    "full_key",
})

_RAW_TEXT_NEEDLES: tuple[str, ...] = (
    "the new content under evaluation",
    "anchor a description",
)


@register("I-LLMCACHE-13", status="REQUIRED")
def check_I_LLMCACHE_13_cache_observability() -> None:
    msi, texts = _make_msi()
    inner = _SequentialClient(["PRESERVE", "PRESERVE"])
    tracer = MemoryTracer()
    with tempfile.TemporaryDirectory(prefix="phase3_14_obs_l1_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_obs_l2_") as l2_tmp:
        # CachedClient L1 with a tracer so L1 cache_hit / cache_miss fire.
        l1 = CachedClient(
            inner=inner, cache_dir=Path(l1_tmp), tracer=tracer
        )
        p = LLMBackedPtCns(
            msi=msi, content_texts=texts, client=l1, tracer=tracer
        )
        p._l2_dir = Path(l2_tmp)
        # First eval: L2 miss + L1 miss + L2 store.
        r1 = p.eval(ContentID("new_x"))
        # Second eval with different new_id, same semantic inputs:
        # L2 hit (no inner call).
        r2 = p.eval(ContentID("new_y"))
        assert r1 is ConsistencyEval.PRESERVE
        assert r2 is ConsistencyEval.PRESERVE

    # L1 events.
    l1_event_types = [e["type"] for e in tracer.events if e["type"].startswith("llm.cache_")]
    assert "llm.cache_miss" in l1_event_types, (
        "I-LLMCACHE-13 violated: no llm.cache_miss event "
        f"(got types={l1_event_types})"
    )

    # L2 events.
    l2_types = [e["type"] for e in tracer.events if e["type"].startswith("llm.semantic_cache_")]
    for required in ("llm.semantic_cache_miss", "llm.semantic_cache_store", "llm.semantic_cache_hit"):
        assert required in l2_types, (
            f"I-LLMCACHE-13 violated: missing tracer event {required!r} "
            f"(got types={l2_types})"
        )

    # Bounded payloads on the CACHE event families only. The
    # pre-existing ``llm.request`` / ``llm.response`` / ``parse.*``
    # events legitimately carry the raw prompt / raw response under
    # their original I-LLM-* / I-TRACE-* contracts; those events are
    # not part of the Phase 3.14 cache observability surface and are
    # out of scope for the I-LLMCACHE-13 bounded-payload audit.
    for e in tracer.events:
        if e["type"].startswith("llm.cache_"):
            for forbidden in _FORBIDDEN_PAYLOAD_KEYS:
                assert forbidden not in e, (
                    "I-LLMCACHE-13 violated: L1 cache event "
                    f"{e['type']!r} carries forbidden key {forbidden!r}"
                )
            extras = set(e.keys()) - _ALLOWED_L1_EVENT_FIELDS
            assert not extras, (
                "I-LLMCACHE-13 violated: L1 event "
                f"{e['type']!r} has unexpected fields {sorted(extras)!r}"
            )
        if e["type"].startswith("llm.semantic_cache_"):
            for forbidden in _FORBIDDEN_PAYLOAD_KEYS:
                assert forbidden not in e, (
                    "I-LLMCACHE-13 violated: L2 cache event "
                    f"{e['type']!r} carries forbidden key {forbidden!r}"
                )
            extras = set(e.keys()) - _ALLOWED_L2_EVENT_FIELDS
            assert not extras, (
                "I-LLMCACHE-13 violated: L2 event "
                f"{e['type']!r} has unexpected fields {sorted(extras)!r}"
            )

    # No raw prompt or raw response text appears in any cache event
    # value.
    for e in tracer.events:
        if not (
            e["type"].startswith("llm.cache_")
            or e["type"].startswith("llm.semantic_cache_")
        ):
            continue
        for value in e.values():
            if not isinstance(value, str):
                continue
            for needle in _RAW_TEXT_NEEDLES:
                assert needle not in value, (
                    "I-LLMCACHE-13 violated: cache event "
                    f"{e['type']!r} leaks raw text {needle!r}"
                )

    # key_prefix on L2 events is exactly 8 hex characters.
    for e in tracer.events:
        if e["type"].startswith("llm.semantic_cache_"):
            prefix = e.get("key_prefix")
            if prefix is None:
                continue
            assert isinstance(prefix, str) and len(prefix) == 8, (
                "I-LLMCACHE-13 violated: L2 event "
                f"{e['type']!r} key_prefix is not 8 hex chars "
                f"(got {prefix!r})"
            )
            int(prefix, 16)  # raises if not hex
