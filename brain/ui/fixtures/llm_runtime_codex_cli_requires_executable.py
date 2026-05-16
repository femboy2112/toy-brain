"""Phase 3.11 codex-cli-requires-executable fixture.

Drives:

* ``I-LLMTOG-16`` (REQUIRED) — ``CODEX_CLI`` without a discoverable
  executable raises ``LlmRuntimeError`` before launch; no
  ``CodexCLIClient`` instance is returned; the factory does not consult
  ``os.environ``.
"""
from __future__ import annotations

from brain.invariants import register
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeError,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-16", status="REQUIRED")
def check_I_LLMTOG_16_codex_cli_requires_executable() -> None:
    # A path-like name that should not exist on any reasonable PATH.
    missing = "/nonexistent/codex-binary-I-LLMTOG-16"

    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(
                mode=LlmRuntimeMode.CODEX_CLI,
                codex_cli_executable=missing,
            )
        )
    except LlmRuntimeError as exc:
        msg = str(exc)
        assert missing in msg, (
            "I-LLMTOG-16 violated: missing-executable error does not name "
            f"the executable (got {msg!r})"
        )
        assert "codex-cli" in msg.lower(), (
            "I-LLMTOG-16 violated: missing-executable error does not name "
            f"the mode (got {msg!r})"
        )
    else:
        raise AssertionError(
            "I-LLMTOG-16 violated: CODEX_CLI without executable did not "
            "raise LlmRuntimeError"
        )
