"""Fixture for I-STRM-08: text-stream ops do not mutate BrainState / MSI / PtCns / registry."""
from __future__ import annotations

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


@register("I-STRM-08", status="REQUIRED")
def check_text_stream_does_not_mutate_brainstate() -> None:
    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry
    before_profile_values = dict(state.profile.values)
    before_msi_contents = frozenset(state.msi.contents)
    before_ptcns_pos = frozenset(state.ptcns.positive_contents)
    before_registry_texts = dict(state.registry.texts)

    chunk = make_text_stream_chunk(
        chunk_id="chunk:nb",
        text="alpha beta\ngamma delta",
        source=TextStreamSource.OPERATOR,
        provenance="origin:operator",
    )
    history = TextStreamHistory().append(chunk)
    feats = extract_stream_features(chunk)
    segs = extract_segment_candidates(chunk)
    pattern = make_stream_pattern(
        pattern_id="pat:nb",
        signature=("alpha", "beta"),
        recurrence_count=3,
    )
    promotion = make_stream_promotion_candidate(
        candidate_id="pc:nb",
        target_content_id="content:nb",
        source=TextStreamSource.OPERATOR,
        chunk_id=chunk.chunk_id,
        text="alpha beta gamma",
        provenance="origin:operator",
        pattern_id=pattern.pattern_id,
    )

    assert len(history.chunks) == 1
    assert feats.text_length == len(chunk.text)
    assert len(segs) >= 1
    assert pattern.recurrence_count == 3
    assert promotion.target_content_id == "content:nb"

    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert dict(state.profile.values) == before_profile_values
    assert frozenset(state.msi.contents) == before_msi_contents
    assert frozenset(state.ptcns.positive_contents) == before_ptcns_pos
    assert dict(state.registry.texts) == before_registry_texts
    assert "chunk:nb" not in state.profile.domain
    assert "chunk:nb" not in state.registry.texts
    assert "content:nb" not in state.profile.domain
    assert "content:nb" not in state.registry.texts
