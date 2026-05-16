"""Phase 3.9 persistence exact-round-trip fixture.

Drives:

* ``I-PERSIST-03`` (REQUIRED) — Fractions persist exactly as integer
  pairs and round-trip byte-for-byte through SQLite.
"""
from __future__ import annotations

import pathlib
import tempfile
from fractions import Fraction
from types import MappingProxyType

from brain.development.text_stream import (
    TextStreamHistory,
    TextStreamSource,
    make_text_stream_chunk,
)
from brain.invariants import register
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.io_types import ContentRegistry
from brain.ui.persistence import (
    SCHEMA_VERSION_V1,
    SessionStoreConfig,
    load_session,
    save_session,
)
from brain.ui.session import OperatorSession


def _build_sample_session() -> OperatorSession:
    profile = make_profile_with_cogito(
        {
            COGITO_ID: 1,
            "alpha": Fraction(3, 7),
            "beta": Fraction(11, 13),
        }
    )
    msi = make_msi(
        profile,
        contents={COGITO_ID, "alpha"},
        threshold=Fraction(1, 3),
    )
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
            "beta": ConsistencyEval.NEUTRAL,
        },
    )
    registry = ContentRegistry(
        texts=MappingProxyType({"alpha": "alpha text", "beta": "beta text"})
    )
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    history = TextStreamHistory(
        chunks=(
            make_text_stream_chunk(
                chunk_id="strm-chunk-1",
                text="hello world",
                source=TextStreamSource.OPERATOR,
                provenance="op-1",
            ),
            make_text_stream_chunk(
                chunk_id="strm-chunk-2",
                text="second chunk",
                source=TextStreamSource.OPERATOR,
                provenance="op-2",
            ),
        )
    )
    return OperatorSession(
        state=state,
        tick_counter=7,
        stream_history=history,
        stream_chunk_serial=2,
    )


@register("I-PERSIST-03", status="REQUIRED")
def check_i_persist_03_save_roundtrip_exact() -> None:
    """Save then load yields a session with exactly equal kernel records."""
    session = _build_sample_session()
    with tempfile.TemporaryDirectory(prefix="brain-persist-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        config = SessionStoreConfig(db_path=db_path)

        save_result = save_session(session, config)
        if save_result.schema_version != SCHEMA_VERSION_V1:
            raise AssertionError(
                f"I-PERSIST-03 violated: save_result.schema_version "
                f"{save_result.schema_version} != {SCHEMA_VERSION_V1}"
            )
        if save_result.saved_chunks != 2:
            raise AssertionError(
                f"I-PERSIST-03 violated: saved_chunks "
                f"{save_result.saved_chunks} != 2"
            )

        loaded, load_result = load_session(config)
        if load_result.schema_version != SCHEMA_VERSION_V1:
            raise AssertionError(
                "I-PERSIST-03 violated: load_result schema_version mismatch"
            )
        if load_result.loaded_chunks != 2:
            raise AssertionError(
                f"I-PERSIST-03 violated: loaded_chunks "
                f"{load_result.loaded_chunks} != 2"
            )

        # Exact ScalarProfile equality under Fraction __eq__.
        if loaded.state.profile.domain != session.state.profile.domain:
            raise AssertionError(
                f"I-PERSIST-03 violated: profile.domain "
                f"{loaded.state.profile.domain!r} != "
                f"{session.state.profile.domain!r}"
            )
        for cid in session.state.profile.domain:
            original = session.state.profile.values[cid]
            restored = loaded.state.profile.values[cid]
            if original != restored:
                raise AssertionError(
                    f"I-PERSIST-03 violated: profile.values[{cid!r}] "
                    f"{restored!r} != {original!r}"
                )
            if not isinstance(restored, Fraction):
                raise AssertionError(
                    f"I-PERSIST-03 violated: profile.values[{cid!r}] "
                    "is not a Fraction"
                )

        # Exact MSI contents + threshold.
        if loaded.state.msi.contents != session.state.msi.contents:
            raise AssertionError(
                f"I-PERSIST-03 violated: msi.contents "
                f"{loaded.state.msi.contents!r} != "
                f"{session.state.msi.contents!r}"
            )
        if loaded.state.msi.threshold != session.state.msi.threshold:
            raise AssertionError(
                f"I-PERSIST-03 violated: msi.threshold "
                f"{loaded.state.msi.threshold!r} != "
                f"{session.state.msi.threshold!r}"
            )

        # Exact PtCns eval_map.
        for cid in session.state.profile.domain:
            original_eval = session.state.ptcns.eval_map[cid]
            restored_eval = loaded.state.ptcns.eval_map[cid]
            if original_eval != restored_eval:
                raise AssertionError(
                    f"I-PERSIST-03 violated: ptcns.eval_map[{cid!r}] "
                    f"{restored_eval!r} != {original_eval!r}"
                )

        # Exact ContentRegistry texts.
        original_keys = set(session.state.registry.texts.keys())
        restored_keys = set(loaded.state.registry.texts.keys())
        if original_keys != restored_keys:
            raise AssertionError(
                "I-PERSIST-03 violated: registry keys "
                f"{restored_keys!r} != {original_keys!r}"
            )
        for cid in original_keys:
            if loaded.state.registry.texts[cid] != session.state.registry.texts[cid]:
                raise AssertionError(
                    f"I-PERSIST-03 violated: registry.texts[{cid!r}] "
                    f"{loaded.state.registry.texts[cid]!r} != "
                    f"{session.state.registry.texts[cid]!r}"
                )

        # Operator-session local fields.
        if loaded.tick_counter != session.tick_counter:
            raise AssertionError(
                f"I-PERSIST-03 violated: tick_counter "
                f"{loaded.tick_counter} != {session.tick_counter}"
            )
        if loaded.stream_chunk_serial != session.stream_chunk_serial:
            raise AssertionError(
                f"I-PERSIST-03 violated: stream_chunk_serial "
                f"{loaded.stream_chunk_serial} != {session.stream_chunk_serial}"
            )
        if len(loaded.stream_history.chunks) != len(session.stream_history.chunks):
            raise AssertionError(
                f"I-PERSIST-03 violated: stream_history.chunks len "
                f"{len(loaded.stream_history.chunks)} != "
                f"{len(session.stream_history.chunks)}"
            )
        for original_chunk, restored_chunk in zip(
            session.stream_history.chunks, loaded.stream_history.chunks
        ):
            if original_chunk.chunk_id != restored_chunk.chunk_id:
                raise AssertionError(
                    f"I-PERSIST-03 violated: chunk_id "
                    f"{restored_chunk.chunk_id!r} != "
                    f"{original_chunk.chunk_id!r}"
                )
            if original_chunk.text != restored_chunk.text:
                raise AssertionError(
                    f"I-PERSIST-03 violated: chunk.text "
                    f"{restored_chunk.text!r} != {original_chunk.text!r}"
                )
            if original_chunk.source != restored_chunk.source:
                raise AssertionError(
                    f"I-PERSIST-03 violated: chunk.source "
                    f"{restored_chunk.source!r} != {original_chunk.source!r}"
                )
            if original_chunk.provenance != restored_chunk.provenance:
                raise AssertionError(
                    f"I-PERSIST-03 violated: chunk.provenance "
                    f"{restored_chunk.provenance!r} != "
                    f"{original_chunk.provenance!r}"
                )

        # Re-save round-trip is idempotent.
        save_session(loaded, config)
        reloaded, _ = load_session(config)
        if (
            reloaded.state.profile.values != loaded.state.profile.values
            or reloaded.state.msi.threshold != loaded.state.msi.threshold
        ):
            raise AssertionError(
                "I-PERSIST-03 violated: idempotent re-save changed kernel state"
            )
