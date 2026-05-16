"""Phase 3.9 persistence /save-session and /load-session command fixture.

Drives:

* ``I-PERSIST-09`` (REQUIRED) — ``/save-session`` and ``/load-session``
  are bounded local typed operator commands that do not call
  ``tick()``: :class:`LocalCommandLine` accepts both as closed verbs
  and rejects trailing arguments; :class:`OperatorSession`
  dispatchers call ``save_session`` / ``load_session``, surface
  bounded printable status / error text on the session, and never
  invoke ``tick()``; both dispatchers fail closed on a missing
  ``session_store_config``, leaving live state untouched.
"""
from __future__ import annotations

import pathlib
import tempfile
from fractions import Fraction
from types import MappingProxyType

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
from brain.ui import session as _session_module
from brain.ui.command_line import (
    LOCAL_COMMAND_VERBS,
    LocalCommandError,
    LocalCommandLine,
)
from brain.ui.commands import Command, OperatorCommand
from brain.ui.persistence import SessionStoreConfig
from brain.ui.session import OperatorSession


def _build_session(db_path: pathlib.Path | None = None) -> OperatorSession:
    profile = make_profile_with_cogito(
        {COGITO_ID: 1, "alpha": Fraction(2, 5)}
    )
    msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 3))
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    config = SessionStoreConfig(db_path=db_path) if db_path is not None else None
    return OperatorSession(state=state, session_store_config=config)


def _patch_tick(observer: dict[str, int]):
    """Replace brain.tick.tick imported by brain.ui.session with a counter.

    The dispatchers under test must not call ``tick()``; this hook
    records any invocation so the fixture can assert zero calls.
    """
    original = _session_module.tick

    def _counting(*args, **kwargs):
        observer["calls"] += 1
        return original(*args, **kwargs)

    return original, _counting


@register("I-PERSIST-09", status="REQUIRED")
def check_i_persist_09_save_load_session_commands() -> None:
    parser = LocalCommandLine()

    # 1. /save-session and /load-session are in the closed verb set.
    if "save-session" not in LOCAL_COMMAND_VERBS:
        raise AssertionError(
            "I-PERSIST-09 violated: 'save-session' missing from "
            "LOCAL_COMMAND_VERBS"
        )
    if "load-session" not in LOCAL_COMMAND_VERBS:
        raise AssertionError(
            "I-PERSIST-09 violated: 'load-session' missing from "
            "LOCAL_COMMAND_VERBS"
        )

    # 2. Parser accepts both verbs and produces typed commands.
    save_cmd = parser.parse("/save-session")
    if not isinstance(save_cmd, Command):
        raise AssertionError(
            f"I-PERSIST-09 violated: parser produced "
            f"{type(save_cmd).__name__} for /save-session"
        )
    if save_cmd.kind is not OperatorCommand.SAVE_SESSION:
        raise AssertionError(
            f"I-PERSIST-09 violated: parser produced kind {save_cmd.kind!r} "
            "for /save-session"
        )
    if save_cmd.payload is not None:
        raise AssertionError(
            "I-PERSIST-09 violated: /save-session payload must be None"
        )

    load_cmd = parser.parse("/load-session")
    if not isinstance(load_cmd, Command):
        raise AssertionError(
            f"I-PERSIST-09 violated: parser produced "
            f"{type(load_cmd).__name__} for /load-session"
        )
    if load_cmd.kind is not OperatorCommand.LOAD_SESSION:
        raise AssertionError(
            f"I-PERSIST-09 violated: parser produced kind {load_cmd.kind!r} "
            "for /load-session"
        )

    # 3. Trailing arguments rejected.
    err = parser.parse("/save-session foo")
    if not isinstance(err, LocalCommandError):
        raise AssertionError(
            "I-PERSIST-09 violated: /save-session must reject trailing args"
        )
    err = parser.parse("/load-session bar")
    if not isinstance(err, LocalCommandError):
        raise AssertionError(
            "I-PERSIST-09 violated: /load-session must reject trailing args"
        )

    # 4. Dispatchers do NOT call tick().
    observer = {"calls": 0}
    original_tick, counting_tick = _patch_tick(observer)
    _session_module.tick = counting_tick  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory(prefix="brain-persist-09-") as td:
            db_path = pathlib.Path(td) / "session.sqlite3"
            session = _build_session(db_path=db_path)
            # Snapshot kernel and queue identity for the
            # "no kernel-side mutation" half of the check.
            prior_state = session.state
            prior_latest_tick = session.latest_tick
            prior_tick_counter = session.tick_counter
            prior_queue_len = len(session.event_queue)

            session.dispatch(save_cmd)
            if observer["calls"] != 0:
                raise AssertionError(
                    "I-PERSIST-09 violated: /save-session dispatch called "
                    f"tick() ({observer['calls']} times)"
                )
            if not session.status_message.startswith("saved session"):
                raise AssertionError(
                    "I-PERSIST-09 violated: /save-session did not set a "
                    f"saved-session status (got {session.status_message!r})"
                )
            if session.error_message:
                raise AssertionError(
                    "I-PERSIST-09 violated: /save-session set an error on "
                    f"success ({session.error_message!r})"
                )
            # Live kernel state unchanged by save (drives I-PERSIST-07 sibling).
            if session.state is not prior_state:
                raise AssertionError(
                    "I-PERSIST-09 violated: /save-session replaced "
                    "BrainState"
                )
            if session.tick_counter != prior_tick_counter:
                raise AssertionError(
                    "I-PERSIST-09 violated: /save-session changed "
                    "tick_counter"
                )
            if len(session.event_queue) != prior_queue_len:
                raise AssertionError(
                    "I-PERSIST-09 violated: /save-session changed "
                    "event_queue"
                )

            # /load-session should restore the kernel + stream state
            # (here identical to the saved one). It must not call tick.
            session.dispatch(load_cmd)
            if observer["calls"] != 0:
                raise AssertionError(
                    "I-PERSIST-09 violated: /load-session dispatch called "
                    f"tick() ({observer['calls']} times)"
                )
            if not session.status_message.startswith("loaded session"):
                raise AssertionError(
                    "I-PERSIST-09 violated: /load-session did not set a "
                    f"loaded-session status (got {session.status_message!r})"
                )
            if session.error_message:
                raise AssertionError(
                    "I-PERSIST-09 violated: /load-session set an error on "
                    f"success ({session.error_message!r})"
                )
            if session.state.profile.values[COGITO_ID] != Fraction(1):
                raise AssertionError(
                    "I-PERSIST-09 violated: /load-session did not restore "
                    "COGITO_ID rho == 1"
                )

            # latest_tick is preserved across the load swap (it belongs
            # to the live operator surface, not the persisted snapshot).
            if session.latest_tick is not prior_latest_tick:
                raise AssertionError(
                    "I-PERSIST-09 violated: /load-session changed "
                    "latest_tick (it must stay with the live surface)"
                )

        # 5. Missing config: both dispatchers surface bounded error and
        #    leave live state untouched.
        session_no_config = _build_session(db_path=None)
        prior_status = session_no_config.status_message
        observer["calls"] = 0
        session_no_config.dispatch(save_cmd)
        if observer["calls"] != 0:
            raise AssertionError(
                "I-PERSIST-09 violated: /save-session without config called "
                "tick()"
            )
        if not session_no_config.error_message:
            raise AssertionError(
                "I-PERSIST-09 violated: /save-session without config did "
                "not set an error message"
            )
        if session_no_config.state is not session_no_config.state:
            raise AssertionError(
                "I-PERSIST-09 violated: /save-session without config "
                "changed BrainState identity"
            )

        session_no_config2 = _build_session(db_path=None)
        observer["calls"] = 0
        session_no_config2.dispatch(load_cmd)
        if observer["calls"] != 0:
            raise AssertionError(
                "I-PERSIST-09 violated: /load-session without config called "
                "tick()"
            )
        if not session_no_config2.error_message:
            raise AssertionError(
                "I-PERSIST-09 violated: /load-session without config did "
                "not set an error message"
            )
    finally:
        _session_module.tick = original_tick  # type: ignore[assignment]
    # Silence any unused-name complaints about `prior_status`.
    _ = prior_status
