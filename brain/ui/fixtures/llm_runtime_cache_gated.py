"""Phase 3.8b cache-gated fixture.

Drives:

* ``I-LLMTOG-08`` (REQUIRED) — Cache wrapping is opt-in and
  mode-gated. Cache rejection applies to ``OFFLINE`` and ``MOCK``;
  cache acceptance applies to ``ANTHROPIC_API`` and ``CLAUDE_CLI``.
  The cache directory is the ``brain/.llm_cache`` default.
"""
from __future__ import annotations

import sys
from pathlib import Path

from brain.invariants import register
from brain.llm.client import (
    AnthropicAPIClient,
    CachedClient,
    ClaudeCLIClient,
    CodexCLIClient,
)
from brain.ui.llm_runtime import (
    LLM_RUNTIME_CACHE_DIR,
    LlmRuntimeConfig,
    LlmRuntimeError,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-08", status="REQUIRED")
def check_I_LLMTOG_08_cache_gated() -> None:
    # OFFLINE + enable_cache -> raises.
    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(
                mode=LlmRuntimeMode.OFFLINE,
                enable_cache=True,
            )
        )
    except LlmRuntimeError as exc:
        assert "offline" in str(exc).lower(), (
            "I-LLMTOG-08 violated: OFFLINE cache rejection does not name "
            f"the mode (got {exc!r})"
        )
    else:
        raise AssertionError(
            "I-LLMTOG-08 violated: OFFLINE + enable_cache did not raise"
        )

    # MOCK + enable_cache -> raises.
    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(
                mode=LlmRuntimeMode.MOCK,
                enable_cache=True,
                mock_responses=("PRESERVE",),
            )
        )
    except LlmRuntimeError as exc:
        assert "mock" in str(exc).lower(), (
            "I-LLMTOG-08 violated: MOCK cache rejection does not name "
            f"the mode (got {exc!r})"
        )
    else:
        raise AssertionError(
            "I-LLMTOG-08 violated: MOCK + enable_cache did not raise"
        )

    # ANTHROPIC_API + enable_cache -> CachedClient wrapping
    # AnthropicAPIClient with cache_dir=brain/.llm_cache.
    cached_anthropic = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.ANTHROPIC_API,
            api_key="I-LLMTOG-08-dummy",
            enable_cache=True,
        )
    )
    assert isinstance(cached_anthropic, CachedClient), (
        "I-LLMTOG-08 violated: ANTHROPIC_API + cache did not produce "
        f"CachedClient (got {type(cached_anthropic).__name__})"
    )
    assert isinstance(cached_anthropic._inner, AnthropicAPIClient), (
        "I-LLMTOG-08 violated: CachedClient does not wrap "
        f"AnthropicAPIClient (got {type(cached_anthropic._inner).__name__})"
    )
    assert cached_anthropic._cache_dir == Path("brain/.llm_cache"), (
        "I-LLMTOG-08 violated: cache_dir is not the brain/.llm_cache "
        f"default (got {cached_anthropic._cache_dir!r})"
    )

    # CLAUDE_CLI + enable_cache -> CachedClient wrapping ClaudeCLIClient.
    cached_cli = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CLAUDE_CLI,
            claude_cli_executable=sys.executable,
            enable_cache=True,
        )
    )
    assert isinstance(cached_cli, CachedClient), (
        "I-LLMTOG-08 violated: CLAUDE_CLI + cache did not produce "
        f"CachedClient (got {type(cached_cli).__name__})"
    )
    assert isinstance(cached_cli._inner, ClaudeCLIClient), (
        "I-LLMTOG-08 violated: CachedClient does not wrap ClaudeCLIClient "
        f"(got {type(cached_cli._inner).__name__})"
    )

    # CODEX_CLI + enable_cache -> CachedClient wrapping CodexCLIClient
    # (Phase 3.11 extension).
    cached_codex = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CODEX_CLI,
            codex_cli_executable=sys.executable,
            enable_cache=True,
        )
    )
    assert isinstance(cached_codex, CachedClient), (
        "I-LLMTOG-08 violated: CODEX_CLI + cache did not produce "
        f"CachedClient (got {type(cached_codex).__name__})"
    )
    assert isinstance(cached_codex._inner, CodexCLIClient), (
        "I-LLMTOG-08 violated: CachedClient does not wrap CodexCLIClient "
        f"(got {type(cached_codex._inner).__name__})"
    )

    # CODEX_CLI without cache -> bare CodexCLIClient (no wrapper).
    bare_codex = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CODEX_CLI,
            codex_cli_executable=sys.executable,
            enable_cache=False,
        )
    )
    assert isinstance(bare_codex, CodexCLIClient), (
        "I-LLMTOG-08 violated: CODEX_CLI without cache did not produce "
        f"bare CodexCLIClient (got {type(bare_codex).__name__})"
    )
    assert not isinstance(bare_codex, CachedClient), (
        "I-LLMTOG-08 violated: CODEX_CLI without cache wrapped the "
        "backend in CachedClient unexpectedly"
    )

    # Module-level constant parity check.
    assert LLM_RUNTIME_CACHE_DIR == Path("brain/.llm_cache"), (
        "I-LLMTOG-08 violated: LLM_RUNTIME_CACHE_DIR drifted "
        f"(got {LLM_RUNTIME_CACHE_DIR!r})"
    )
