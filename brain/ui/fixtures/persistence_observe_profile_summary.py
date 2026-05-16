"""Phase 3.10b /profile-summary fixture.

Drives:

* ``I-OBSERVE-02`` (REQUIRED) — ``/profile-summary`` returns
  exact-Fraction ``"num/den"`` rows, COGITO first, deterministic sort.
  ``profile_summary(config, *, row_cap=64)`` reads ``profile_values``
  in ``mode=ro``, sorts with ``COGITO_ID`` first then by content_id
  ASCII-ascending, renders each Fraction as the exact ``"num/den"``
  string via the single shared renderer, and truncates at ``row_cap``
  with ``truncated=True`` when the cap is hit.
"""
from __future__ import annotations

import pathlib
import tempfile
from fractions import Fraction
from types import MappingProxyType

from brain.development.text_stream import TextStreamHistory
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
    PROFILE_SUMMARY_ROW_CAP,
    PROFILE_VALUE_STRING_MAX_LEN,
    ProfileSummaryReport,
    ProfileSummaryRow,
    profile_summary,
)
from brain.ui.session import OperatorSession


def _build_session_with(profile_dict: dict[str, Fraction | int]) -> OperatorSession:
    profile = make_profile_with_cogito(profile_dict)
    contents = {cid for cid in profile_dict}
    msi = make_msi(profile, contents=contents, threshold=Fraction(1, 2))
    eval_map = {cid: ConsistencyEval.PRESERVE for cid in profile_dict}
    ptcns = make_ptcns(msi, eval_map=eval_map)
    texts = {
        cid: f"text-{cid}" for cid in profile_dict if cid != COGITO_ID
    }
    registry = ContentRegistry(texts=MappingProxyType(texts))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    return OperatorSession(state=state, stream_history=TextStreamHistory())


@register("I-OBSERVE-02", status="REQUIRED")
def check_i_observe_02_profile_summary() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-observe-02-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        # Three content_ids: COGITO + two others that bracket COGITO
        # alphabetically. Used to confirm COGITO_ID is sorted first
        # regardless of ASCII order.
        session = _build_session_with({
            COGITO_ID: 1,
            "alpha": Fraction(5, 7),
            "zeta": Fraction(11, 13),
        })
        config = SessionStoreConfig(db_path=db_path)
        save_session(session, config)

        report = profile_summary(config)
        if not isinstance(report, ProfileSummaryReport):
            raise AssertionError(
                "I-OBSERVE-02 violated: profile_summary did not return a "
                f"ProfileSummaryReport (got {type(report).__name__})"
            )
        if report.error_text:
            raise AssertionError(
                "I-OBSERVE-02 violated: profile_summary error_text "
                f"{report.error_text!r}"
            )
        if len(report.rows) != 3:
            raise AssertionError(
                "I-OBSERVE-02 violated: expected 3 rows, got "
                f"{len(report.rows)}"
            )
        if report.truncated:
            raise AssertionError(
                "I-OBSERVE-02 violated: small profile reports truncated=True"
            )
        # COGITO_ID first.
        if report.rows[0].content_id != COGITO_ID:
            raise AssertionError(
                "I-OBSERVE-02 violated: first row content_id "
                f"{report.rows[0].content_id!r} is not COGITO_ID "
                f"({COGITO_ID!r})"
            )
        # Remaining rows are sorted ASCII-ascending.
        remaining = [r.content_id for r in report.rows[1:]]
        if remaining != sorted(remaining):
            raise AssertionError(
                "I-OBSERVE-02 violated: non-COGITO rows not sorted "
                f"({remaining!r})"
            )
        # Exact "num/den" format.
        by_cid = {r.content_id: r.value_str for r in report.rows}
        if by_cid[COGITO_ID] != "1/1":
            raise AssertionError(
                "I-OBSERVE-02 violated: COGITO value_str "
                f"{by_cid[COGITO_ID]!r} != '1/1'"
            )
        if by_cid["alpha"] != "5/7":
            raise AssertionError(
                "I-OBSERVE-02 violated: alpha value_str "
                f"{by_cid['alpha']!r} != '5/7'"
            )
        if by_cid["zeta"] != "11/13":
            raise AssertionError(
                "I-OBSERVE-02 violated: zeta value_str "
                f"{by_cid['zeta']!r} != '11/13'"
            )
        # No float / repr leakage: every value_str matches the "<int>/<int>"
        # pattern.
        for row in report.rows:
            if not isinstance(row, ProfileSummaryRow):
                raise AssertionError(
                    "I-OBSERVE-02 violated: row is not ProfileSummaryRow"
                )
            if "." in row.value_str or "Fraction" in row.value_str:
                raise AssertionError(
                    "I-OBSERVE-02 violated: row.value_str "
                    f"{row.value_str!r} contains float / repr marker"
                )
            if "/" not in row.value_str:
                raise AssertionError(
                    "I-OBSERVE-02 violated: row.value_str "
                    f"{row.value_str!r} missing '/' separator"
                )
            if len(row.value_str) > PROFILE_VALUE_STRING_MAX_LEN:
                raise AssertionError(
                    "I-OBSERVE-02 violated: row.value_str length "
                    f"{len(row.value_str)} exceeds "
                    f"PROFILE_VALUE_STRING_MAX_LEN="
                    f"{PROFILE_VALUE_STRING_MAX_LEN}"
                )

        # Row-cap truncation. row_cap=2 with 3 rows -> truncated=True
        # and only the first 2 sorted rows survive (COGITO + alpha).
        truncated_report = profile_summary(config, row_cap=2)
        if not truncated_report.truncated:
            raise AssertionError(
                "I-OBSERVE-02 violated: row_cap=2 did not set "
                "truncated=True"
            )
        if len(truncated_report.rows) != 2:
            raise AssertionError(
                "I-OBSERVE-02 violated: row_cap=2 kept "
                f"{len(truncated_report.rows)} rows; expected 2"
            )
        if truncated_report.rows[0].content_id != COGITO_ID:
            raise AssertionError(
                "I-OBSERVE-02 violated: row_cap=2 first row "
                f"{truncated_report.rows[0].content_id!r} is not "
                f"COGITO_ID ({COGITO_ID!r})"
            )

        # row_cap default matches the locked module constant.
        default_report = profile_summary(config)
        if default_report.truncated:
            raise AssertionError(
                "I-OBSERVE-02 violated: tiny profile triggers default-cap "
                "truncation"
            )

        # Bound enforcement: ProfileSummaryRow with a too-long value_str
        # raises at construction.
        too_long = "1/" + ("9" * (PROFILE_VALUE_STRING_MAX_LEN + 1))
        try:
            ProfileSummaryRow(content_id="x", value_str=too_long)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "I-OBSERVE-02 violated: ProfileSummaryRow accepted "
                f"over-cap value_str (len {len(too_long)})"
            )

        # Default row_cap matches the locked constant.
        if PROFILE_SUMMARY_ROW_CAP != 64:
            raise AssertionError(
                "I-OBSERVE-02 violated: PROFILE_SUMMARY_ROW_CAP "
                f"{PROFILE_SUMMARY_ROW_CAP!r} != 64"
            )
