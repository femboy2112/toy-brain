"""Phase 3.8b claude-cli-requires-executable fixture.

Drives:

* ``I-LLMTOG-06`` (REQUIRED) — ``CLAUDE_CLI`` without a discoverable
  executable raises ``LlmRuntimeError`` before launch; no
  ``ClaudeCLIClient`` instance is returned.
"""
from __future__ import annotations

from brain.invariants import register
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeError,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-06", status="REQUIRED")
def check_I_LLMTOG_06_claude_cli_requires_executable() -> None:
    # A path-like name that should not exist on any reasonable PATH.
    missing = "I-LLMTOG-06-not-an-executable"

    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(
                mode=LlmRuntimeMode.CLAUDE_CLI,
                claude_cli_executable=missing,
            )
        )
    except LlmRuntimeError as exc:
        msg = str(exc)
        assert missing in msg, (
            "I-LLMTOG-06 violated: missing-executable error does not name "
            f"the executable (got {msg!r})"
        )
        assert "claude-cli" in msg.lower(), (
            "I-LLMTOG-06 violated: missing-executable error does not name "
            f"the mode (got {msg!r})"
        )
    else:
        raise AssertionError(
            "I-LLMTOG-06 violated: CLAUDE_CLI without executable did not "
            "raise LlmRuntimeError"
        )
