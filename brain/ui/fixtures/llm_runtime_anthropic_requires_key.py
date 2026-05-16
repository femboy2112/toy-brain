"""Phase 3.8b anthropic-requires-key fixture.

Drives:

* ``I-LLMTOG-05`` (REQUIRED) — ``ANTHROPIC_API`` without a resolved
  ``api_key`` raises ``LlmRuntimeError`` before launch. The
  precedence for resolution is CLI > ``BRAIN_ANTHROPIC_API_KEY`` >
  ``ANTHROPIC_API_KEY``. The factory does not consult
  ``os.environ``.
"""
from __future__ import annotations

import os

from brain.invariants import register
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeError,
    LlmRuntimeMode,
    build_llm_client_from_config,
    parse_llm_runtime_args,
)


@register("I-LLMTOG-05", status="REQUIRED")
def check_I_LLMTOG_05_anthropic_requires_key() -> None:
    # Direct factory call with mode=ANTHROPIC_API and api_key=None
    # raises before any HTTP probe.
    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(mode=LlmRuntimeMode.ANTHROPIC_API, api_key=None)
        )
    except LlmRuntimeError as exc:
        msg = str(exc)
        assert "anthropic" in msg.lower(), (
            "I-LLMTOG-05 violated: missing-key error does not name the "
            f"mode (got {msg!r})"
        )
    else:
        raise AssertionError(
            "I-LLMTOG-05 violated: ANTHROPIC_API without api_key did not "
            "raise LlmRuntimeError"
        )

    # The factory must not consult os.environ. Set a stale env key,
    # confirm the factory still fails.
    saved_anthropic = os.environ.get("ANTHROPIC_API_KEY")
    saved_brain = os.environ.get("BRAIN_ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "I-LLMTOG-05-stale"
    os.environ["BRAIN_ANTHROPIC_API_KEY"] = "I-LLMTOG-05-stale"
    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(mode=LlmRuntimeMode.ANTHROPIC_API, api_key=None)
        )
    except LlmRuntimeError:
        pass
    else:
        raise AssertionError(
            "I-LLMTOG-05 violated: factory consulted os.environ for the "
            "API key"
        )
    finally:
        if saved_anthropic is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = saved_anthropic
        if saved_brain is None:
            os.environ.pop("BRAIN_ANTHROPIC_API_KEY", None)
        else:
            os.environ["BRAIN_ANTHROPIC_API_KEY"] = saved_brain

    # parse_llm_runtime_args precedence: CLI > BRAIN_ANTHROPIC_API_KEY
    # > ANTHROPIC_API_KEY.
    config = parse_llm_runtime_args(
        ["--llm-mode", "anthropic-api", "--llm-anthropic-api-key", "cli-key"],
        {"BRAIN_ANTHROPIC_API_KEY": "brain-key", "ANTHROPIC_API_KEY": "any-key"},
    )
    assert config.api_key == "cli-key", (
        "I-LLMTOG-05 violated: CLI api key did not win "
        f"(got {config.api_key!r})"
    )

    config = parse_llm_runtime_args(
        ["--llm-mode", "anthropic-api"],
        {"BRAIN_ANTHROPIC_API_KEY": "brain-key", "ANTHROPIC_API_KEY": "any-key"},
    )
    assert config.api_key == "brain-key", (
        "I-LLMTOG-05 violated: BRAIN_ANTHROPIC_API_KEY did not beat "
        f"ANTHROPIC_API_KEY (got {config.api_key!r})"
    )

    config = parse_llm_runtime_args(
        ["--llm-mode", "anthropic-api"],
        {"ANTHROPIC_API_KEY": "any-key"},
    )
    assert config.api_key == "any-key", (
        "I-LLMTOG-05 violated: ANTHROPIC_API_KEY fallback did not apply "
        f"(got {config.api_key!r})"
    )

    config = parse_llm_runtime_args(["--llm-mode", "anthropic-api"], {})
    assert config.api_key is None, (
        "I-LLMTOG-05 violated: parse_llm_runtime_args invented an api key "
        f"with empty env (got {config.api_key!r})"
    )

    # With api_key explicitly resolved, the factory must succeed.
    config = parse_llm_runtime_args(
        ["--llm-mode", "anthropic-api"], {"ANTHROPIC_API_KEY": "real-key"}
    )
    client = build_llm_client_from_config(config)
    assert client is not None, (
        "I-LLMTOG-05 violated: factory returned None for a valid config"
    )
