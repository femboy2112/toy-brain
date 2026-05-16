"""Phase 3.8 stream UI constant parity fixture.

Drives:

* ``I-UISTRM-14`` (STRUCTURAL) — Stream UI constants preserve Phase 3.7
  bounds.
"""
from __future__ import annotations

from brain.development import text_stream as _text_stream
from brain.invariants import register
from brain.ui.command_line import LOCAL_CMD_MAX_ERROR_LEN
from brain.ui.commands import STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN
from brain.ui.session import MAX_STATUS_TEXT_LEN


@register("I-UISTRM-14", status="STRUCTURAL")
def check_I_UISTRM_14_stream_constant_parity() -> None:
    # The accepted Phase 3.7 substrate bounds, frozen at the catalog
    # patch plan's "Accepted Constants" table.
    assert _text_stream.STREAM_TEXT_MAX_LEN == 1024, (
        f"I-UISTRM-14 violated: STREAM_TEXT_MAX_LEN drifted "
        f"(got {_text_stream.STREAM_TEXT_MAX_LEN})"
    )
    assert _text_stream.STREAM_PROVENANCE_MAX_LEN == 64, (
        f"I-UISTRM-14 violated: STREAM_PROVENANCE_MAX_LEN drifted "
        f"(got {_text_stream.STREAM_PROVENANCE_MAX_LEN})"
    )
    assert _text_stream.STREAM_PROMOTION_MAX == 64, (
        f"I-UISTRM-14 violated: STREAM_PROMOTION_MAX drifted "
        f"(got {_text_stream.STREAM_PROMOTION_MAX})"
    )
    # Operator TUI side: error / status limits.
    assert LOCAL_CMD_MAX_ERROR_LEN == 240, (
        f"I-UISTRM-14 violated: LOCAL_CMD_MAX_ERROR_LEN drifted "
        f"(got {LOCAL_CMD_MAX_ERROR_LEN})"
    )
    assert MAX_STATUS_TEXT_LEN == 240, (
        f"I-UISTRM-14 violated: MAX_STATUS_TEXT_LEN drifted "
        f"(got {MAX_STATUS_TEXT_LEN})"
    )

    # /stream-promote candidate_id cap mirrors STREAM_PROVENANCE_MAX_LEN.
    assert STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN == _text_stream.STREAM_PROVENANCE_MAX_LEN, (
        f"I-UISTRM-14 violated: STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN "
        f"({STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN}) drifted from "
        f"STREAM_PROVENANCE_MAX_LEN "
        f"({_text_stream.STREAM_PROVENANCE_MAX_LEN})"
    )
