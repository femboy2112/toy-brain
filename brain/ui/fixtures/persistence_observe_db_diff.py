"""Phase 3.10b /db-diff fixture.

Drives:

* ``I-OBSERVE-04`` (REQUIRED) — ``/db-diff`` reports finite field
  enumeration; ``"<missing>"`` on one-sided absence; never invents
  defaults. ``db_diff(session, config, *, row_cap=32)`` snapshots the
  live session via the public :func:`brain.ui.persistence.snapshot_session`
  helper, reads the saved snapshot in ``mode=ro``, diffs over the
  closed field enumeration, and reports each
  :class:`DbDiffField` with ``live`` and ``saved`` as exact
  ``"num/den"`` strings, integer-text for counters, or the literal
  ``"<missing>"`` on one-sided absence. ``truncated=True`` iff
  ``diff_count > row_cap``.
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
    DB_DIFF_ROW_CAP,
    DIFF_MISSING_MARKER,
    DbDiffField,
    DbDiffReport,
    db_diff,
)
from brain.ui.session import OperatorSession


def _build_session(profile_dict: dict[str, Fraction | int]) -> OperatorSession:
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


@register("I-OBSERVE-04", status="REQUIRED")
def check_i_observe_04_db_diff() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-observe-04-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        # Saved == Live case.
        session = _build_session({
            COGITO_ID: 1,
            "alpha": Fraction(5, 7),
        })
        config = SessionStoreConfig(db_path=db_path)
        save_session(session, config)

        report = db_diff(session, config)
        if not isinstance(report, DbDiffReport):
            raise AssertionError(
                "I-OBSERVE-04 violated: db_diff did not return a "
                f"DbDiffReport (got {type(report).__name__})"
            )
        if not report.matches:
            raise AssertionError(
                "I-OBSERVE-04 violated: identical session/DB did not "
                f"match (differences={[(d.field, d.live, d.saved) for d in report.differences]!r})"
            )
        if report.diff_count != 0:
            raise AssertionError(
                "I-OBSERVE-04 violated: identical session/DB has "
                f"diff_count={report.diff_count!r} != 0"
            )
        if report.error_text:
            raise AssertionError(
                "I-OBSERVE-04 violated: identical session/DB has "
                f"error_text={report.error_text!r}"
            )
        if report.truncated:
            raise AssertionError(
                "I-OBSERVE-04 violated: identical session/DB has "
                "truncated=True"
            )

        # Divergent profile case: live has an extra content_id that the
        # saved DB lacks. Must report a profile.<cid> diff with
        # saved="<missing>" and live = exact "num/den".
        divergent = _build_session({
            COGITO_ID: 1,
            "alpha": Fraction(5, 7),
            "beta": Fraction(11, 13),
        })
        divergent_report = db_diff(divergent, config)
        if divergent_report.matches:
            raise AssertionError(
                "I-OBSERVE-04 violated: divergent profile matched "
                "(saved lacks 'beta')"
            )
        beta_diffs = [
            d for d in divergent_report.differences
            if d.field == "profile.beta"
        ]
        if not beta_diffs:
            raise AssertionError(
                "I-OBSERVE-04 violated: divergent profile diff missing "
                "profile.beta entry "
                f"(fields={[d.field for d in divergent_report.differences]!r})"
            )
        beta_diff = beta_diffs[0]
        if beta_diff.live != "11/13":
            raise AssertionError(
                "I-OBSERVE-04 violated: profile.beta live "
                f"{beta_diff.live!r} != '11/13'"
            )
        if beta_diff.saved != DIFF_MISSING_MARKER:
            raise AssertionError(
                "I-OBSERVE-04 violated: profile.beta saved "
                f"{beta_diff.saved!r} != {DIFF_MISSING_MARKER!r}"
            )

        # Opposite direction: saved has more content_ids than live.
        big_db = pathlib.Path(td) / "big.sqlite3"
        big_session = _build_session({
            COGITO_ID: 1,
            "alpha": Fraction(5, 7),
            "gamma": Fraction(2, 3),
        })
        big_config = SessionStoreConfig(db_path=big_db)
        save_session(big_session, big_config)

        small_session = _build_session({
            COGITO_ID: 1,
            "alpha": Fraction(5, 7),
        })
        small_report = db_diff(small_session, big_config)
        if small_report.matches:
            raise AssertionError(
                "I-OBSERVE-04 violated: live-missing-gamma matched a DB "
                "that has gamma"
            )
        gamma_diffs = [
            d for d in small_report.differences
            if d.field == "profile.gamma"
        ]
        if not gamma_diffs:
            raise AssertionError(
                "I-OBSERVE-04 violated: profile.gamma missing from diff"
            )
        gamma_diff = gamma_diffs[0]
        if gamma_diff.live != DIFF_MISSING_MARKER:
            raise AssertionError(
                "I-OBSERVE-04 violated: profile.gamma live "
                f"{gamma_diff.live!r} != {DIFF_MISSING_MARKER!r}"
            )
        if gamma_diff.saved != "2/3":
            raise AssertionError(
                "I-OBSERVE-04 violated: profile.gamma saved "
                f"{gamma_diff.saved!r} != '2/3'"
            )

        # Differing values for the same content_id.
        diff_value_db = pathlib.Path(td) / "diff_value.sqlite3"
        save_session(
            _build_session({COGITO_ID: 1, "alpha": Fraction(5, 7)}),
            SessionStoreConfig(db_path=diff_value_db),
        )
        live_session = _build_session(
            {COGITO_ID: 1, "alpha": Fraction(6, 7)}
        )
        value_report = db_diff(
            live_session,
            SessionStoreConfig(db_path=diff_value_db),
        )
        alpha_diffs = [
            d for d in value_report.differences
            if d.field == "profile.alpha"
        ]
        if not alpha_diffs:
            raise AssertionError(
                "I-OBSERVE-04 violated: changed profile.alpha missing "
                "from diff"
            )
        alpha_diff = alpha_diffs[0]
        if alpha_diff.live != "6/7" or alpha_diff.saved != "5/7":
            raise AssertionError(
                "I-OBSERVE-04 violated: profile.alpha diff "
                f"live={alpha_diff.live!r} saved={alpha_diff.saved!r} "
                "(expected '6/7' vs '5/7')"
            )

        # Missing DB: error_text populated, matches=False, no kernel
        # builder invoked (the helper short-circuits before opening sqlite).
        missing_db = pathlib.Path(td) / "no-such-file.sqlite3"
        missing_report = db_diff(
            session, SessionStoreConfig(db_path=missing_db)
        )
        if missing_report.matches:
            raise AssertionError(
                "I-OBSERVE-04 violated: missing DB reported matches=True"
            )
        if not missing_report.error_text:
            raise AssertionError(
                "I-OBSERVE-04 violated: missing DB has empty error_text"
            )

        # DbDiffField rejects unknown field names.
        for bad_name in ("unknown_field", "msi.unknown", "profile."):
            try:
                DbDiffField(field=bad_name, live="x", saved="y")
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "I-OBSERVE-04 violated: DbDiffField accepted "
                    f"unknown field name {bad_name!r}"
                )

        # Locked default cap.
        if DB_DIFF_ROW_CAP != 32:
            raise AssertionError(
                "I-OBSERVE-04 violated: DB_DIFF_ROW_CAP "
                f"{DB_DIFF_ROW_CAP!r} != 32"
            )
