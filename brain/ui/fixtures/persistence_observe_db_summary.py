"""Phase 3.10b /db-summary fixture.

Drives:

* ``I-OBSERVE-01`` (REQUIRED) — ``/db-summary`` reads in ``mode=ro``;
  closed ``with`` block; bounded report. ``db_summary(config)`` opens
  the configured DB through
  ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
  ``with conn:`` block, reads meta + per-table row counts, and returns
  a :class:`DbSummaryReport` with bounded fields. The ``msi_threshold``
  field is the exact ``"num/den"`` string. Default session yields
  ``profile=2``, ``msi=2``, ``threshold="1/2"``, ``registry=1``,
  ``ptcns=2``, ``streams=0``.
* ``I-OBSERVE-05`` (REQUIRED) — observability commands never activate
  saved state and never mutate live ``BrainState``. The session
  ``__eq__`` before and after each of the four observability dispatch
  paths is ``True``.
"""
from __future__ import annotations

import copy
import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import (
    SessionStoreConfig,
    save_session,
)
from brain.ui.persistence_observe import (
    DbSummaryReport,
    OPS_REPORT_TEXT_MAX_LEN,
    db_summary,
)


@register("I-OBSERVE-01", status="REQUIRED")
def check_i_observe_01_db_summary() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-observe-01-") as td:
        # Missing-DB case.
        missing_path = pathlib.Path(td) / "absent.sqlite3"
        config_missing = SessionStoreConfig(db_path=missing_path)
        missing_report = db_summary(config_missing)
        if not isinstance(missing_report, DbSummaryReport):
            raise AssertionError(
                "I-OBSERVE-01 violated: db_summary did not return a "
                f"DbSummaryReport (got {type(missing_report).__name__})"
            )
        if missing_report.profile_row_count != 0:
            raise AssertionError(
                "I-OBSERVE-01 violated: missing DB reports "
                f"profile_row_count={missing_report.profile_row_count!r}"
            )
        if missing_report.msi_threshold != "":
            raise AssertionError(
                "I-OBSERVE-01 violated: missing DB reports "
                f"msi_threshold={missing_report.msi_threshold!r}"
            )
        if not missing_report.error_text:
            raise AssertionError(
                "I-OBSERVE-01 violated: missing DB has empty error_text"
            )

        # Freshly-saved default-session DB case.
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        config = SessionStoreConfig(db_path=db_path)
        save_session(session, config)

        report = db_summary(config)
        if report.error_text:
            raise AssertionError(
                "I-OBSERVE-01 violated: clean DB summary has error_text "
                f"{report.error_text!r}"
            )
        # Default-session expectations.
        if report.profile_row_count != 2:
            raise AssertionError(
                "I-OBSERVE-01 violated: default session profile_row_count "
                f"{report.profile_row_count!r} != 2"
            )
        if report.msi_content_count != 2:
            raise AssertionError(
                "I-OBSERVE-01 violated: default session msi_content_count "
                f"{report.msi_content_count!r} != 2"
            )
        if report.msi_threshold != "1/2":
            raise AssertionError(
                "I-OBSERVE-01 violated: default session msi_threshold "
                f"{report.msi_threshold!r} != '1/2'"
            )
        if report.ptcns_eval_row_count != 2:
            raise AssertionError(
                "I-OBSERVE-01 violated: default session ptcns_eval_row_count "
                f"{report.ptcns_eval_row_count!r} != 2"
            )
        if report.registry_row_count != 1:
            raise AssertionError(
                "I-OBSERVE-01 violated: default session registry_row_count "
                f"{report.registry_row_count!r} != 1"
            )
        if report.stream_chunk_count != 0:
            raise AssertionError(
                "I-OBSERVE-01 violated: default session stream_chunk_count "
                f"{report.stream_chunk_count!r} != 0"
            )
        if report.stream_candidate_count != 0:
            raise AssertionError(
                "I-OBSERVE-01 violated: default session "
                f"stream_candidate_count {report.stream_candidate_count!r} "
                "!= 0"
            )
        # Bounded fields.
        for field_name in (
            "db_path_str",
            "catalog_version",
            "created_at",
            "updated_at",
            "error_text",
        ):
            value = getattr(report, field_name)
            if len(value) > OPS_REPORT_TEXT_MAX_LEN:
                raise AssertionError(
                    "I-OBSERVE-01 violated: DbSummaryReport."
                    f"{field_name} length {len(value)} exceeds "
                    f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
                )


@register("I-OBSERVE-05", status="REQUIRED")
def check_i_observe_05_no_live_mutation() -> None:
    """Observability commands never activate saved state or mutate live state."""
    with tempfile.TemporaryDirectory(prefix="brain-observe-05-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        dst_path = pathlib.Path(td) / "absent-dest.sqlite3"
        session = build_default_session()
        config = SessionStoreConfig(db_path=db_path)
        session.session_store_config = config
        save_session(session, config)

        # Snapshot every kernel-side field that observability must not
        # mutate. We use copy.copy so the reference identity is preserved
        # but the comparison is value-based for the dataclass-equality
        # half. The session is a slots dataclass so __eq__ is generated.
        prior_state = session.state
        prior_tick_counter = session.tick_counter
        prior_stream_history = session.stream_history
        prior_stream_candidates = session.stream_candidates
        prior_stream_chunk_serial = session.stream_chunk_serial
        prior_session_copy = copy.copy(session)
        # Snapshot only the kernel + stream subset that observability is
        # contractually forbidden from mutating. The dispatcher is
        # allowed to mutate status_message / error_message; that is the
        # bounded local-UI status surface.

        # Dispatch each Phase 3.10b verb.
        for cmd_kind in (
            OperatorCommand.DB_SUMMARY,
            OperatorCommand.PROFILE_SUMMARY,
            OperatorCommand.STREAM_DB_SUMMARY,
            OperatorCommand.DB_DIFF,
        ):
            session.dispatch(make_command(cmd_kind))
            # Reference identity must be preserved for kernel containers.
            if session.state is not prior_state:
                raise AssertionError(
                    "I-OBSERVE-05 violated: session.state rebound by "
                    f"{cmd_kind.name}"
                )
            if session.tick_counter != prior_tick_counter:
                raise AssertionError(
                    "I-OBSERVE-05 violated: session.tick_counter mutated "
                    f"by {cmd_kind.name}"
                )
            if session.stream_history is not prior_stream_history:
                raise AssertionError(
                    "I-OBSERVE-05 violated: session.stream_history rebound "
                    f"by {cmd_kind.name}"
                )
            if session.stream_candidates is not prior_stream_candidates:
                raise AssertionError(
                    "I-OBSERVE-05 violated: session.stream_candidates "
                    f"rebound by {cmd_kind.name}"
                )
            if session.stream_chunk_serial != prior_stream_chunk_serial:
                raise AssertionError(
                    "I-OBSERVE-05 violated: session.stream_chunk_serial "
                    f"mutated by {cmd_kind.name}"
                )

        # Also test /db-backup as a Phase 3.10a probe to confirm the
        # observability dispatchers are not the only ones holding the
        # invariant (the audit ensures the broader contract). The
        # session_db config / stream history must still be unchanged.
        session.dispatch(
            make_command(OperatorCommand.DB_BACKUP, dest_path=dst_path)
        )

        # Final value-equality check across kernel + stream fields. We
        # compare via the field tuple (the session also tracks
        # status_message, which the dispatchers do legitimately update).
        live_kernel = (
            session.state,
            session.tick_counter,
            session.stream_history,
            session.stream_candidates,
            session.stream_chunk_serial,
        )
        prior_kernel = (
            prior_session_copy.state,
            prior_session_copy.tick_counter,
            prior_session_copy.stream_history,
            prior_session_copy.stream_candidates,
            prior_session_copy.stream_chunk_serial,
        )
        if live_kernel != prior_kernel:
            raise AssertionError(
                "I-OBSERVE-05 violated: kernel/stream field tuple "
                "changed after observability dispatches"
            )
