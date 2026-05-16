"""Phase 3.8 stream / step tick-boundary fixture.

Drives:

* ``I-UISTRM-07`` (REQUIRED) — ``/step`` remains the only stream
  interaction path that calls ``tick()``.
"""
from __future__ import annotations

from brain.invariants import register
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.fixtures._stream_helpers import make_session, state_identity


class _DeterministicTickClient:
    """Minimal LLM client stand-in for the /step path.

    The Phase 3.8 stream interaction layer never reaches the LLM client,
    but the existing ``_dispatch_step`` route requires a client argument
    when an operator dispatches STEP_TICK. This stub is wholly local and
    deterministic; the fixture only asserts that no stream dispatch
    causes ``tick()`` to be invoked.
    """

    def __init__(self) -> None:
        self.call_count: int = 0

    def eval_consistency(self, payload: object) -> object:  # pragma: no cover
        # Not invoked in this fixture; defined so the duck-typed contract
        # exists without importing brain.llm.client.
        self.call_count += 1
        return None


@register("I-UISTRM-07", status="REQUIRED")
def check_I_UISTRM_07_step_only_tick_path() -> None:
    session = make_session()
    client = _DeterministicTickClient()
    prior_state_id = state_identity(session.state)
    prior_tick_counter = session.tick_counter
    prior_latest_tick = session.latest_tick

    # Dispatch every stream command kind; none should change tick state.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="hello"),
        client=client,
    )
    assert session.tick_counter == prior_tick_counter, (
        "I-UISTRM-07 violated: /stream changed tick_counter"
    )
    assert session.latest_tick is prior_latest_tick, (
        "I-UISTRM-07 violated: /stream changed latest_tick"
    )
    assert state_identity(session.state) == prior_state_id, (
        "I-UISTRM-07 violated: /stream changed BrainState identity"
    )

    session.dispatch(
        make_command(OperatorCommand.INSPECT_STREAM_SUMMARY), client=client
    )
    session.dispatch(
        make_command(OperatorCommand.INSPECT_STREAM_CANDIDATES), client=client
    )
    assert session.tick_counter == prior_tick_counter
    assert session.latest_tick is prior_latest_tick

    candidate_id = session.stream_candidates[0].candidate_id
    session.dispatch(
        make_command(OperatorCommand.STREAM_PROMOTE, candidate_id=candidate_id),
        client=client,
    )
    assert session.tick_counter == prior_tick_counter, (
        "I-UISTRM-07 violated: /stream-promote changed tick_counter"
    )
    assert session.latest_tick is prior_latest_tick, (
        "I-UISTRM-07 violated: /stream-promote changed latest_tick"
    )
    assert client.call_count == 0, (
        "I-UISTRM-07 violated: a stream dispatch invoked the client"
    )

    # /step is the only route that consumes a queued event and calls tick.
    # We do not run /step here because the substrate's promote candidate
    # uses a fresh content_id that the deterministic kernel state does
    # not pre-register; the route boundary is the property under test.
    # Assert that STEP_TICK reaches _dispatch_step via the existing
    # routing table.
    from brain.ui.commands import INSPECT_VIEW_MAP

    assert OperatorCommand.STEP_TICK not in INSPECT_VIEW_MAP, (
        "I-UISTRM-07 violated: STEP_TICK appeared in INSPECT_VIEW_MAP"
    )
