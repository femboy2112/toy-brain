"""Phase 3.8b mock-requires-responses fixture.

Drives:

* ``I-LLMTOG-07`` (REQUIRED) — ``MOCK`` with empty ``mock_responses``
  raises ``LlmRuntimeError`` before launch.
"""
from __future__ import annotations

from brain.invariants import register
from brain.llm.client import MockClient
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeError,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-07", status="REQUIRED")
def check_I_LLMTOG_07_mock_requires_responses() -> None:
    # MOCK with empty mock_responses raises.
    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(mode=LlmRuntimeMode.MOCK)
        )
    except LlmRuntimeError as exc:
        msg = str(exc)
        assert "mock" in msg.lower(), (
            "I-LLMTOG-07 violated: empty-mock-responses error does not "
            f"name the mode (got {msg!r})"
        )
        assert "--llm-mock-response" in msg, (
            "I-LLMTOG-07 violated: empty-mock-responses error does not "
            f"name the CLI flag (got {msg!r})"
        )
    else:
        raise AssertionError(
            "I-LLMTOG-07 violated: MOCK with empty responses did not raise "
            "LlmRuntimeError"
        )

    # MOCK with at least one response succeeds.
    client = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.MOCK,
            mock_responses=("PRESERVE",),
        )
    )
    assert isinstance(client, MockClient), (
        "I-LLMTOG-07 violated: valid MOCK config did not produce "
        f"MockClient (got {type(client).__name__})"
    )
