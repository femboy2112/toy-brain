"""Phase 3.10b /stream-db-summary fixture.

Drives:

* ``I-OBSERVE-03`` (REQUIRED) — ``/stream-db-summary`` returns bounded
  head + tail with text-preview cap. ``stream_db_summary(config, *,
  head_cap=8, tail_cap=8)`` reads ``stream_chunks`` /
  ``stream_candidates`` counts plus a head slice (first ``head_cap``
  chunks by ordinal) and a tail slice (last ``tail_cap`` chunks by
  ordinal). Each row's ``text_preview`` is bounded by
  ``STREAM_TEXT_PREVIEW_MAX_LEN = 64``; full chunk text is never
  returned. ``truncated=True`` iff the chunk count exceeds
  ``head_cap + tail_cap``.
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
from brain.io_types import ContentRegistry
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.ui.persistence import (
    SessionStoreConfig,
    save_session,
)
from brain.ui.persistence_observe import (
    STREAM_DB_SUMMARY_HEAD_CAP,
    STREAM_DB_SUMMARY_TAIL_CAP,
    STREAM_TEXT_PREVIEW_MAX_LEN,
    StreamDbSummaryReport,
    StreamDbSummaryRow,
    stream_db_summary,
)
from brain.ui.session import OperatorSession


def _build_session_with_chunks(n_chunks: int, *, text_per_chunk: str) -> OperatorSession:
    profile = make_profile_with_cogito({COGITO_ID: 1, "alpha": Fraction(1, 2)})
    msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 2))
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    chunks = tuple(
        make_text_stream_chunk(
            chunk_id=f"strm-chunk-{i + 1}",
            text=text_per_chunk,
            source=TextStreamSource.OPERATOR,
            provenance=f"op-{i + 1}",
        )
        for i in range(n_chunks)
    )
    history = TextStreamHistory(chunks=chunks)
    return OperatorSession(
        state=state,
        stream_history=history,
        stream_chunk_serial=n_chunks,
    )


@register("I-OBSERVE-03", status="REQUIRED")
def check_i_observe_03_stream_db_summary() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-observe-03-") as td:
        # Empty stream case.
        empty_db = pathlib.Path(td) / "empty.sqlite3"
        empty_session = _build_session_with_chunks(0, text_per_chunk="x")
        empty_config = SessionStoreConfig(db_path=empty_db)
        save_session(empty_session, empty_config)
        empty_report = stream_db_summary(empty_config)
        if empty_report.chunk_count != 0:
            raise AssertionError(
                "I-OBSERVE-03 violated: empty stream chunk_count "
                f"{empty_report.chunk_count!r} != 0"
            )
        if empty_report.head or empty_report.tail:
            raise AssertionError(
                "I-OBSERVE-03 violated: empty stream has non-empty head/tail"
            )
        if empty_report.truncated:
            raise AssertionError(
                "I-OBSERVE-03 violated: empty stream reports truncated=True"
            )

        # Small stream (5 chunks; head=tail=8 -> not truncated; head
        # contains all 5).
        small_db = pathlib.Path(td) / "small.sqlite3"
        small_session = _build_session_with_chunks(5, text_per_chunk="short")
        small_config = SessionStoreConfig(db_path=small_db)
        save_session(small_session, small_config)
        small_report = stream_db_summary(small_config)
        if small_report.chunk_count != 5:
            raise AssertionError(
                "I-OBSERVE-03 violated: small stream chunk_count "
                f"{small_report.chunk_count!r} != 5"
            )
        if small_report.truncated:
            raise AssertionError(
                "I-OBSERVE-03 violated: 5-chunk stream reports truncated=True"
            )
        if len(small_report.head) != 5:
            raise AssertionError(
                "I-OBSERVE-03 violated: small stream head size "
                f"{len(small_report.head)} != 5"
            )
        if small_report.first_ordinal != 1:
            raise AssertionError(
                "I-OBSERVE-03 violated: small stream first_ordinal "
                f"{small_report.first_ordinal!r} != 1"
            )
        if small_report.last_ordinal != 5:
            raise AssertionError(
                "I-OBSERVE-03 violated: small stream last_ordinal "
                f"{small_report.last_ordinal!r} != 5"
            )

        # Big stream (20 chunks; head=tail=8 -> head+tail=16 < 20 -> truncated).
        big_db = pathlib.Path(td) / "big.sqlite3"
        big_session = _build_session_with_chunks(20, text_per_chunk="payload")
        big_config = SessionStoreConfig(db_path=big_db)
        save_session(big_session, big_config)
        big_report = stream_db_summary(big_config)
        if not isinstance(big_report, StreamDbSummaryReport):
            raise AssertionError(
                "I-OBSERVE-03 violated: stream_db_summary did not return a "
                f"StreamDbSummaryReport (got {type(big_report).__name__})"
            )
        if big_report.chunk_count != 20:
            raise AssertionError(
                "I-OBSERVE-03 violated: big stream chunk_count "
                f"{big_report.chunk_count!r} != 20"
            )
        if not big_report.truncated:
            raise AssertionError(
                "I-OBSERVE-03 violated: 20-chunk stream did not set "
                "truncated=True"
            )
        if len(big_report.head) != STREAM_DB_SUMMARY_HEAD_CAP:
            raise AssertionError(
                "I-OBSERVE-03 violated: big stream head size "
                f"{len(big_report.head)} != head_cap "
                f"{STREAM_DB_SUMMARY_HEAD_CAP}"
            )
        if len(big_report.tail) != STREAM_DB_SUMMARY_TAIL_CAP:
            raise AssertionError(
                "I-OBSERVE-03 violated: big stream tail size "
                f"{len(big_report.tail)} != tail_cap "
                f"{STREAM_DB_SUMMARY_TAIL_CAP}"
            )
        # Head ordinals are ASC starting at first_ordinal.
        head_ordinals = [r.ordinal for r in big_report.head]
        if head_ordinals != list(range(1, STREAM_DB_SUMMARY_HEAD_CAP + 1)):
            raise AssertionError(
                "I-OBSERVE-03 violated: head ordinals "
                f"{head_ordinals!r} != 1..{STREAM_DB_SUMMARY_HEAD_CAP}"
            )
        # Tail ordinals are ASC ending at last_ordinal.
        tail_ordinals = [r.ordinal for r in big_report.tail]
        expected_tail = list(range(
            21 - STREAM_DB_SUMMARY_TAIL_CAP, 21
        ))
        if tail_ordinals != expected_tail:
            raise AssertionError(
                "I-OBSERVE-03 violated: tail ordinals "
                f"{tail_ordinals!r} != {expected_tail!r}"
            )

        # text_preview is bounded by STREAM_TEXT_PREVIEW_MAX_LEN.
        long_text = "x" * (STREAM_TEXT_PREVIEW_MAX_LEN * 3)
        long_db = pathlib.Path(td) / "long.sqlite3"
        long_session = _build_session_with_chunks(2, text_per_chunk=long_text)
        long_config = SessionStoreConfig(db_path=long_db)
        save_session(long_session, long_config)
        long_report = stream_db_summary(long_config)
        for row in long_report.head:
            if not isinstance(row, StreamDbSummaryRow):
                raise AssertionError(
                    "I-OBSERVE-03 violated: row is not StreamDbSummaryRow"
                )
            if len(row.text_preview) > STREAM_TEXT_PREVIEW_MAX_LEN:
                raise AssertionError(
                    "I-OBSERVE-03 violated: text_preview length "
                    f"{len(row.text_preview)} exceeds "
                    f"STREAM_TEXT_PREVIEW_MAX_LEN="
                    f"{STREAM_TEXT_PREVIEW_MAX_LEN}"
                )
            if row.text_preview == long_text:
                raise AssertionError(
                    "I-OBSERVE-03 violated: full chunk text returned in "
                    "text_preview"
                )

        # Locked default cap values.
        if STREAM_TEXT_PREVIEW_MAX_LEN != 64:
            raise AssertionError(
                "I-OBSERVE-03 violated: STREAM_TEXT_PREVIEW_MAX_LEN "
                f"{STREAM_TEXT_PREVIEW_MAX_LEN!r} != 64"
            )
        if STREAM_DB_SUMMARY_HEAD_CAP != 8:
            raise AssertionError(
                "I-OBSERVE-03 violated: STREAM_DB_SUMMARY_HEAD_CAP "
                f"{STREAM_DB_SUMMARY_HEAD_CAP!r} != 8"
            )
        if STREAM_DB_SUMMARY_TAIL_CAP != 8:
            raise AssertionError(
                "I-OBSERVE-03 violated: STREAM_DB_SUMMARY_TAIL_CAP "
                f"{STREAM_DB_SUMMARY_TAIL_CAP!r} != 8"
            )
