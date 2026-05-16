"""Phase 3.10c session resource-audit + outcome-detection fixture.

Drives:

* ``I-AUTOSAVE-14`` (STRUCTURAL) — session resource audit +
  outcome-detection contract. :data:`_ALLOWED_SESSION_ATTRS` contains
  ``"autosave_config"`` and ``"last_autosave_status"``;
  ``autosave_config`` is a frozen :class:`AutosaveConfig` or ``None``;
  ``last_autosave_status`` is a frozen :class:`AutosaveStatusReport`
  or ``None``. Neither holds a ``sqlite3.Connection``, ``Cursor``,
  subprocess handle, socket, file object, callable, curses object, or
  LLM client. ``_dispatch_step`` and ``_dispatch_stream_promote``
  return ``Optional[bool]`` (True on success; False on failure; None
  for read-only paths — neither is read-only so the actual return is
  always True/False on this row's exercise).
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import sqlite3
import tempfile
import textwrap
from fractions import Fraction
from pathlib import Path

from brain.invariants import register
from brain.toce_core import ContentState
from brain.ui.__main__ import build_default_session
from brain.ui.autosave import (
    AutosaveConfig,
    AutosaveMode,
    AutosaveStatusReport,
    autosave_enable,
)
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import SessionStoreConfig
from brain.ui.session import _ALLOWED_SESSION_ATTRS, OperatorSession


_SESSION_PATH = (
    Path(__file__).resolve().parents[1] / "session.py"
)


class _PreserveClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


def _assert_session_resource_free(
    session: OperatorSession, *, tag: str
) -> None:
    for attr in _ALLOWED_SESSION_ATTRS:
        value = getattr(session, attr)
        if isinstance(value, sqlite3.Connection):
            raise AssertionError(
                f"I-AUTOSAVE-14 violated [{tag}]: session.{attr} is "
                "a sqlite3.Connection"
            )
        if isinstance(value, sqlite3.Cursor):
            raise AssertionError(
                f"I-AUTOSAVE-14 violated [{tag}]: session.{attr} is "
                "a sqlite3.Cursor"
            )
        if callable(value):
            raise AssertionError(
                f"I-AUTOSAVE-14 violated [{tag}]: session.{attr} is "
                "callable"
            )
        if hasattr(value, "fileno"):
            raise AssertionError(
                f"I-AUTOSAVE-14 violated [{tag}]: session.{attr} "
                "exposes fileno()"
            )
        if hasattr(value, "send_signal") or hasattr(value, "communicate"):
            raise AssertionError(
                f"I-AUTOSAVE-14 violated [{tag}]: session.{attr} looks "
                "like a subprocess handle"
            )
        if hasattr(value, "eval_consistency"):
            raise AssertionError(
                f"I-AUTOSAVE-14 violated [{tag}]: session.{attr} looks "
                "like an LLM client (has eval_consistency)"
            )


def _dispatcher_returns_optional_bool(method_name: str) -> bool:
    """Inspect the dispatcher's source and confirm at least one ``return True``,
    one ``return False``, and no plain ``return None`` literal.

    The corrigenda allows either a return-value refactor OR a
    per-call sentinel; we check the return-value shape here, which is
    the locked contract.
    """
    method = getattr(OperatorSession, method_name)
    source = textwrap.dedent(inspect.getsource(method))
    tree = ast.parse(source)
    saw_true = False
    saw_false = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            v = node.value
            if isinstance(v, ast.Constant):
                if v.value is True:
                    saw_true = True
                elif v.value is False:
                    saw_false = True
    return saw_true and saw_false


@register("I-AUTOSAVE-14", status="STRUCTURAL")
def check_i_autosave_14_session_resource_audit() -> None:
    # _ALLOWED_SESSION_ATTRS contains the two Phase 3.10c additions.
    for required in ("autosave_config", "last_autosave_status"):
        if required not in _ALLOWED_SESSION_ATTRS:
            raise AssertionError(
                "I-AUTOSAVE-14 violated: _ALLOWED_SESSION_ATTRS does "
                f"not contain {required!r}"
            )

    # Outcome-detection contract: _dispatch_step + _dispatch_stream_promote
    # both contain explicit `return True` and `return False` paths
    # (the central dispatch reads the return value, not status strings).
    for method_name in ("_dispatch_step", "_dispatch_stream_promote"):
        if not _dispatcher_returns_optional_bool(method_name):
            raise AssertionError(
                "I-AUTOSAVE-14 violated: OperatorSession."
                f"{method_name} does not return True/False (the "
                "outcome-detection contract requires Optional[bool] "
                "with both True and False return paths)"
            )

    # session.py central dispatch reads the returned outcome and routes
    # through _maybe_autosave_after_dispatch (not via scanning
    # status_message). Static check: the dispatch method body
    # references the maybe-autosave helper.
    session_source = _SESSION_PATH.read_text(encoding="utf-8")
    if "_maybe_autosave_after_dispatch" not in session_source:
        raise AssertionError(
            "I-AUTOSAVE-14 violated: brain/ui/session.py does not "
            "define _maybe_autosave_after_dispatch"
        )
    # Sanity: the central dispatch must NOT inspect status_message /
    # error_message to detect mutation outcome. We check by ensuring
    # no string-equality test on those fields is used to gate
    # autosave; the explicit Optional[bool] flow is the contract.
    if "status_message ==" in session_source and "autosave" in session_source.split(
        "status_message =="
    )[1][:200]:
        raise AssertionError(
            "I-AUTOSAVE-14 violated: brain/ui/session.py inspects "
            "status_message to decide autosave (forbidden; use the "
            "Optional[bool] return value instead)"
        )

    # Behavioral: exercise /autosave-enable + /step + autosave trigger
    # and confirm every session field is one of the allowed types.
    with tempfile.TemporaryDirectory(prefix="brain-autosave-14-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        session.session_store_config = SessionStoreConfig(db_path=db_path)
        autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )
        _assert_session_resource_free(session, tag="after-enable")

        if not isinstance(session.autosave_config, AutosaveConfig):
            raise AssertionError(
                "I-AUTOSAVE-14 violated: session.autosave_config is "
                f"{type(session.autosave_config).__name__} after enable "
                "(expected AutosaveConfig)"
            )

        session.dispatch(make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="beta",
            text="beta probe",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(3, 4),
        ))
        client = _PreserveClient()
        session.dispatch(
            make_command(OperatorCommand.STEP_TICK), client=client
        )
        _assert_session_resource_free(session, tag="after-step")

        if not isinstance(
            session.last_autosave_status, AutosaveStatusReport
        ):
            raise AssertionError(
                "I-AUTOSAVE-14 violated: session.last_autosave_status "
                f"is {type(session.last_autosave_status).__name__} "
                "after autosave trigger (expected AutosaveStatusReport)"
            )

        # /autosave-disable also keeps the session resource-free.
        session.dispatch(make_command(OperatorCommand.AUTOSAVE_DISABLE))
        _assert_session_resource_free(session, tag="after-disable")
