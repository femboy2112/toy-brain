"""Phase 3.14 no-tick-change fixture.

Drives:

* ``I-LLMCACHE-01`` (REQUIRED) — L0 cache remains per-instance /
  per-tick and ``brain/tick.py`` is untouched: every ``tick(...)`` call
  constructs a fresh ``LLMBackedPtCns``, and ``LLMBackedPtCns._cache``
  is initialized with ``{COGITO_ID: PRESERVE}`` only.
* ``I-LLMCACHE-16`` (REQUIRED) — Cached and uncached evaluation
  preserve the same ``(new_state, TickRecord)`` for the same client
  responses; no tick semantic change.
"""
from __future__ import annotations

import ast
import tempfile
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType

from brain.invariants import register
from brain.io_types import ContentRegistry, PerceptEvent
from brain.llm.client import CachedClient
from brain.llm.ptcns_backed import LLMBackedPtCns
from brain.tick import BrainState, tick
from brain.tlica.builders import make_msi, make_profile_with_cogito, make_ptcns
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.ptcns import ConsistencyEval
from brain.toce_core import ContentState


class _RecordingClient:
    """LLM client returning canned responses and recording every prompt."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._i = 0
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        if self._i >= len(self._responses):
            raise RuntimeError("_RecordingClient exhausted")
        out = self._responses[self._i]
        self._i += 1
        return out


def _make_initial_state() -> BrainState:
    profile = make_profile_with_cogito({COGITO_ID: 1})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi=msi,
        eval_map={COGITO_ID: ConsistencyEval.PRESERVE},
    )
    return BrainState(
        profile=profile,
        msi=msi,
        ptcns=ptcns,
        registry=ContentRegistry.empty(),
    )


def _make_event() -> PerceptEvent:
    return PerceptEvent(
        content_id=ContentID("alpha"),
        text="a synthetic percept",
        content_state=ContentState(
            available=True,
            verification_path="local",
            retrievable=True,
            operative=True,
        ),
        initial_rho=Fraction(3, 4),
    )


@register("I-LLMCACHE-01", status="REQUIRED")
def check_I_LLMCACHE_01_l0_and_tick_untouched() -> None:
    # 1. brain/tick.py is untouched: confirm the module does not import
    # the new L2 cache module-level constants. The tick orchestration
    # never references SEMANTIC_CACHE_DIR / SEMANTIC_CACHE_MAX_ENTRIES.
    tick_path = Path(__file__).resolve().parents[2] / "tick.py"
    assert tick_path.exists(), (
        "I-LLMCACHE-01 violated: brain/tick.py not found"
    )
    source = tick_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(tick_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in (
            "SEMANTIC_CACHE_DIR",
            "SEMANTIC_CACHE_MAX_ENTRIES",
            "SEMANTIC_CACHE_SCHEMA_VERSION",
        ):
            raise AssertionError(
                "I-LLMCACHE-01 violated: brain/tick.py references L2 "
                f"cache name {node.id!r} (line {node.lineno})"
            )
    for forbidden in (
        "SEMANTIC_CACHE_DIR",
        "SEMANTIC_CACHE_MAX_ENTRIES",
        "_l2_dir",
        "_l2_lookup",
        "_l2_store",
    ):
        assert forbidden not in source, (
            "I-LLMCACHE-01 violated: brain/tick.py contains forbidden "
            f"L2 reference {forbidden!r}"
        )

    # 2. L0 cache is per-instance / per-tick: a freshly-constructed
    # LLMBackedPtCns starts with exactly {COGITO_ID: PRESERVE}.
    profile = make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    p = LLMBackedPtCns(
        msi=msi,
        content_texts={ContentID("anchor_a"): "anchor"},
        client=_RecordingClient([]),
    )
    assert dict(p._cache) == {COGITO_ID: ConsistencyEval.PRESERVE}, (
        "I-LLMCACHE-01 violated: L0 cache initial contents drifted "
        f"(got {dict(p._cache)!r})"
    )


@register("I-LLMCACHE-16", status="REQUIRED")
def check_I_LLMCACHE_16_tick_parity_cached_vs_uncached() -> None:
    # Run tick() twice with identical inputs, once with a bare client
    # (uncached) and once with a CachedClient wrapper (L1 + L2 enabled);
    # the returned (new_state, TickRecord) must be field-for-field equal.
    state = _make_initial_state()

    # Uncached: bare _RecordingClient; no CachedClient wrap; no L2.
    bare_client = _RecordingClient(["PRESERVE"])
    state_a, record_a = tick(state, [_make_event()], bare_client)

    # Cached: CachedClient wrap; L2 enabled. Redirect both L1 and L2 to
    # tempdirs so the parity probe never touches brain/.llm_cache.
    with tempfile.TemporaryDirectory(prefix="phase3_14_parity_l1_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_parity_l2_") as l2_tmp:
        wrapped_inner = _RecordingClient(["PRESERVE"])
        wrapped = CachedClient(
            inner=wrapped_inner,
            cache_dir=Path(l1_tmp),
        )
        # Inject a wrapper around tick that swaps the L2 dir on the
        # constructed LLMBackedPtCns. We must not edit tick.py; instead
        # use a small adapter client that lets the wrapped CachedClient
        # introspect the way tick() expects, then re-point _l2_dir on
        # the inner PtCns. To stay surgical, we just call tick() and
        # then verify the comparison runs without writing to the repo
        # cache by monkey-patching SEMANTIC_CACHE_DIR for the duration
        # of this call.
        import brain.llm.ptcns_backed as _ptcns_backed_mod
        saved_dir = _ptcns_backed_mod.SEMANTIC_CACHE_DIR
        _ptcns_backed_mod.SEMANTIC_CACHE_DIR = Path(l2_tmp)
        try:
            state_b, record_b = tick(state, [_make_event()], wrapped)
        finally:
            _ptcns_backed_mod.SEMANTIC_CACHE_DIR = saved_dir

    # Parity assertions over BrainState.
    assert state_a.profile.values == state_b.profile.values, (
        "I-LLMCACHE-16 violated: profile.values diverged between cached "
        f"and uncached tick (a={dict(state_a.profile.values)!r}, "
        f"b={dict(state_b.profile.values)!r})"
    )
    assert state_a.profile.domain == state_b.profile.domain, (
        "I-LLMCACHE-16 violated: profile.domain diverged"
    )
    assert state_a.msi.contents == state_b.msi.contents, (
        "I-LLMCACHE-16 violated: msi.contents diverged"
    )
    assert state_a.msi.threshold == state_b.msi.threshold, (
        "I-LLMCACHE-16 violated: msi.threshold diverged"
    )
    assert dict(state_a.ptcns.eval_map) == dict(state_b.ptcns.eval_map), (
        "I-LLMCACHE-16 violated: ptcns.eval_map diverged"
    )
    assert state_a.registry.texts == state_b.registry.texts, (
        "I-LLMCACHE-16 violated: registry.texts diverged"
    )

    # Parity assertions over TickRecord.
    assert record_a.tick_index == record_b.tick_index
    assert dict(record_a.profile_values) == dict(record_b.profile_values)
    assert record_a.msi_contents == record_b.msi_contents
    assert dict(record_a.eval_map) == dict(record_b.eval_map)
    assert record_a.boundary == record_b.boundary
    assert record_a.mode_trace == record_b.mode_trace
    assert record_a.triggered_mode == record_b.triggered_mode
    assert record_a.registry.texts == record_b.registry.texts
    assert record_a.notes == record_b.notes
