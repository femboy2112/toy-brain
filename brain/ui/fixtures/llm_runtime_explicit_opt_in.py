"""Phase 3.8b explicit-opt-in fixture.

Drives:

* ``I-LLMTOG-04`` (REQUIRED) — Model-backed modes require explicit
  opt-in. ``parse_llm_runtime_args([], {})`` returns a config whose
  mode is ``OFFLINE`` regardless of whether ``ANTHROPIC_API_KEY``,
  ``BRAIN_ANTHROPIC_API_KEY``, or ``claude`` is present in the
  ambient environment; only ``--llm-mode`` or ``BRAIN_LLM_MODE``
  selects a non-offline mode.
"""
from __future__ import annotations

from brain.invariants import register
from brain.ui.llm_runtime import (
    LlmRuntimeMode,
    parse_llm_runtime_args,
)


@register("I-LLMTOG-04", status="REQUIRED")
def check_I_LLMTOG_04_explicit_opt_in() -> None:
    # Empty argv + empty env -> OFFLINE.
    config = parse_llm_runtime_args([], {})
    assert config.mode is LlmRuntimeMode.OFFLINE, (
        "I-LLMTOG-04 violated: empty argv/env did not resolve to OFFLINE "
        f"(got {config.mode!r})"
    )

    # Stale ANTHROPIC_API_KEY in env, no opt-in -> still OFFLINE.
    config = parse_llm_runtime_args(
        [], {"ANTHROPIC_API_KEY": "I-LLMTOG-04-stale"}
    )
    assert config.mode is LlmRuntimeMode.OFFLINE, (
        "I-LLMTOG-04 violated: ANTHROPIC_API_KEY in env without "
        f"--llm-mode produced non-offline mode (got {config.mode!r})"
    )

    # Stale BRAIN_ANTHROPIC_API_KEY -> still OFFLINE.
    config = parse_llm_runtime_args(
        [], {"BRAIN_ANTHROPIC_API_KEY": "I-LLMTOG-04-stale"}
    )
    assert config.mode is LlmRuntimeMode.OFFLINE, (
        "I-LLMTOG-04 violated: BRAIN_ANTHROPIC_API_KEY in env without "
        f"--llm-mode produced non-offline mode (got {config.mode!r})"
    )

    # CLI flag selects each non-offline mode.
    for value, expected in (
        ("offline", LlmRuntimeMode.OFFLINE),
        ("mock", LlmRuntimeMode.MOCK),
        ("anthropic-api", LlmRuntimeMode.ANTHROPIC_API),
        ("claude-cli", LlmRuntimeMode.CLAUDE_CLI),
    ):
        config = parse_llm_runtime_args(["--llm-mode", value], {})
        assert config.mode is expected, (
            f"I-LLMTOG-04 violated: --llm-mode {value} did not resolve to "
            f"{expected!r} (got {config.mode!r})"
        )

    # BRAIN_LLM_MODE env override also selects the non-offline mode.
    config = parse_llm_runtime_args([], {"BRAIN_LLM_MODE": "mock"})
    assert config.mode is LlmRuntimeMode.MOCK, (
        "I-LLMTOG-04 violated: BRAIN_LLM_MODE=mock did not resolve to "
        f"MOCK (got {config.mode!r})"
    )

    # CLI flag wins over env override.
    config = parse_llm_runtime_args(
        ["--llm-mode", "offline"], {"BRAIN_LLM_MODE": "anthropic-api"}
    )
    assert config.mode is LlmRuntimeMode.OFFLINE, (
        "I-LLMTOG-04 violated: --llm-mode offline did not override "
        f"BRAIN_LLM_MODE=anthropic-api (got {config.mode!r})"
    )
