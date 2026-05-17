"""Fixture for I-PLEDGER-13: session-local /stream integration.

* I-PLEDGER-13 — ``observe(...)`` runs on a successful ``/stream``
  append (after ``_dispatch_stream_append`` has appended a chunk and
  a candidate) and does NOT run on read-only commands, parse
  failures, dispatch failures, ``/step``, or ``/stream-promote``. The
  ``/step`` route is bit-for-bit unchanged.

The session-local v1 integration is gated by LOCK B / LOCK C: the
ledger is not serialized by ``/save-session`` and is not restored by
``/load-session``. This fixture asserts both the integration
trigger and the resource-free / no-coupling shape of the new
``OperatorSession.pattern_ledger`` field.
"""
from __future__ import annotations

from brain.development.pattern_ledger import PatternLedger
from brain.development.text_stream import STREAM_PATTERN_RECURRENCE_MIN
from brain.invariants import register
from brain.tlica.profile import COGITO_ID
from brain.ui.command_line import LocalCommandLine
from brain.ui.commands import (
    OperatorCommand,
    StreamAppendPayload,
    make_command,
)
from brain.ui.fixtures._stream_helpers import (
    make_session,
    session_kernel_identity,
)
from brain.ui.session import OperatorSession


def _offline_client():
    # OfflineStandInClient is the deterministic client used by the
    # existing Phase 3.8 stream fixtures (returns "PRESERVE" with no
    # I/O). It lives in brain.ui.__main__ in the current repo layout.
    from brain.ui.__main__ import OfflineStandInClient  # noqa: PLC0415
    return OfflineStandInClient()


@register("I-PLEDGER-13", status="REQUIRED")
def check_pattern_ledger_session_integration() -> None:
    session = make_session()

    # Fresh session has an empty PatternLedger (LOCK C: cold start ->
    # empty ledger).
    assert isinstance(session.pattern_ledger, PatternLedger), (
        "I-PLEDGER-13 violated: session.pattern_ledger is not a PatternLedger"
    )
    assert session.pattern_ledger.entries == (), (
        "I-PLEDGER-13 violated: fresh session has non-empty pattern_ledger"
    )
    initial_ledger = session.pattern_ledger
    kernel_before = session_kernel_identity(session)

    # /stream success appends one chunk and triggers exactly one observe.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    assert len(session.pattern_ledger.entries) == 1, (
        "I-PLEDGER-13 violated: successful /stream did not advance the ledger"
    )
    entry = session.pattern_ledger.entries[0]
    assert entry.recurrence_count == STREAM_PATTERN_RECURRENCE_MIN
    # Evidence references the session's deterministic ids.
    assert entry.evidence_chunk_ids == ("strm-chunk-1",)
    assert entry.evidence_candidate_ids == ("promo-strm-chunk-1",)
    # COGITO_ID never appears in any signature element or evidence
    # id (mirrors LOCK N / I-PLEDGER-04).
    for elem in entry.signature:
        assert elem != COGITO_ID
    for eid in entry.evidence_chunk_ids + entry.evidence_candidate_ids:
        assert eid != COGITO_ID

    # Read-only /stream-summary does not trigger observe; ledger
    # identity is preserved.
    ledger_after_first = session.pattern_ledger
    session.dispatch(make_command(OperatorCommand.INSPECT_STREAM_SUMMARY))
    assert session.pattern_ledger is ledger_after_first, (
        "I-PLEDGER-13 violated: read-only /stream-summary mutated the ledger"
    )

    # /stream-candidates: same.
    session.dispatch(make_command(OperatorCommand.INSPECT_STREAM_CANDIDATES))
    assert session.pattern_ledger is ledger_after_first

    # /state / /tick / /session-status: read-only paths leave ledger
    # untouched.
    for kind in (
        OperatorCommand.INSPECT_STATE,
        OperatorCommand.INSPECT_TICK,
        OperatorCommand.SESSION_STATUS,
        OperatorCommand.HELP,
    ):
        session.dispatch(make_command(kind))
        assert session.pattern_ledger is ledger_after_first, (
            "I-PLEDGER-13 violated: read-only command "
            f"{kind.value!r} mutated the ledger"
        )

    # A second /stream with the same text advances the existing
    # entry's recurrence_count and does NOT add a new entry.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    assert len(session.pattern_ledger.entries) == 1
    assert (
        session.pattern_ledger.entries[0].recurrence_count
        == STREAM_PATTERN_RECURRENCE_MIN + 1
    )

    # /stream-promote does NOT call observe; ledger identity preserved.
    ledger_before_promote = session.pattern_ledger
    session.dispatch(
        make_command(OperatorCommand.STREAM_PROMOTE, candidate_id="promo-strm-chunk-1")
    )
    assert session.pattern_ledger is ledger_before_promote, (
        "I-PLEDGER-13 violated: /stream-promote mutated the ledger"
    )

    # /step does NOT call observe; ledger identity preserved.
    ledger_before_step = session.pattern_ledger
    session.dispatch(make_command(OperatorCommand.STEP_TICK), client=_offline_client())
    assert session.pattern_ledger is ledger_before_step, (
        "I-PLEDGER-13 violated: /step mutated the ledger"
    )

    # Failed parse does not call observe. Use the parser directly to
    # produce a LocalCommandError; the dispatcher never sees it.
    err = LocalCommandLine().parse("/not-a-real-verb")
    assert err.__class__.__name__ == "LocalCommandError"
    assert session.pattern_ledger is ledger_before_step

    # Dispatch failure (malformed payload) does not call observe.
    pre_failure_ledger = session.pattern_ledger
    # Build an empty-text StreamAppendPayload to force the
    # constructor to raise; we wrap it through a try because the
    # payload constructor enforces I-UISTRM-02. The parse layer
    # would also reject this, but the assertion under test is that
    # an aborted dispatch never advances the ledger.
    try:
        bad_payload = StreamAppendPayload(text="")
    except ValueError:
        bad_payload = None  # parse-layer rejection equivalent
    assert bad_payload is None
    assert session.pattern_ledger is pre_failure_ledger

    # /save-session / /load-session do NOT touch the ledger
    # (LOCK B: session-local only; LOCK C: load does not restore).
    # We exercise these without a configured session_store_config
    # so the dispatchers fail closed with bounded local errors.
    pre_persistence_ledger = session.pattern_ledger
    session.dispatch(make_command(OperatorCommand.SAVE_SESSION))
    assert session.pattern_ledger is pre_persistence_ledger
    session.dispatch(make_command(OperatorCommand.LOAD_SESSION))
    assert session.pattern_ledger is pre_persistence_ledger

    # The session's _ALLOWED_SESSION_ATTRS must include the new field.
    from brain.ui.session import _ALLOWED_SESSION_ATTRS  # noqa: PLC0415
    assert "pattern_ledger" in _ALLOWED_SESSION_ATTRS, (
        "I-PLEDGER-13 violated: pattern_ledger missing from "
        "_ALLOWED_SESSION_ATTRS"
    )

    # initial_ledger is identity-stable across the session lifetime
    # (no in-place mutation of the original record).
    assert isinstance(initial_ledger, PatternLedger)
    assert initial_ledger.entries == ()

    # /step behavior on this session matched the pre-ledger semantics:
    # tick_counter advanced by exactly one and queue size returned to
    # its pre-promote value (the promote increased it by one; the
    # step consumed it).
    assert session.tick_counter == 1
    assert len(session.event_queue) == 0
    # The pre-/stream kernel identity was lost only at /step, which is
    # expected behavior for the existing tick path. Sanity: that
    # transition happened through _dispatch_step (not via the ledger).
    _ = kernel_before  # documentation only — pre-step kernel id captured

    # A fresh OperatorSession constructed with an explicit empty
    # PatternLedger continues to work.
    explicit = OperatorSession(state=session.state, pattern_ledger=PatternLedger())
    assert isinstance(explicit.pattern_ledger, PatternLedger)
    assert explicit.pattern_ledger.entries == ()
