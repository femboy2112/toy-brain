"""Phase 3.8b factory-per-mode fixture.

Drives:

* ``I-LLMTOG-03`` (REQUIRED) — Each accepted mode returns the expected
  concrete client type without invoking it. For ``CLAUDE_CLI``, the
  fixture uses ``sys.executable`` as a guaranteed-present executable
  so CI does not require the real Claude CLI. The fixture asserts
  construction only; it does not invoke ``eval_consistency``.
"""
from __future__ import annotations

import sys

from brain.invariants import register
from brain.llm.client import (
    AnthropicAPIClient,
    CachedClient,
    ClaudeCLIClient,
    MockClient,
)
from brain.ui.__main__ import OfflineStandInClient
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-03", status="REQUIRED")
def check_I_LLMTOG_03_factory_per_mode() -> None:
    # OFFLINE -> OfflineStandInClient
    client_offline = build_llm_client_from_config(LlmRuntimeConfig())
    assert isinstance(client_offline, OfflineStandInClient), (
        "I-LLMTOG-03 violated: OFFLINE mode did not produce "
        f"OfflineStandInClient (got {type(client_offline).__name__})"
    )

    # MOCK -> MockClient
    client_mock = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.MOCK,
            mock_responses=("PRESERVE",),
        )
    )
    assert isinstance(client_mock, MockClient), (
        "I-LLMTOG-03 violated: MOCK mode did not produce MockClient "
        f"(got {type(client_mock).__name__})"
    )

    # ANTHROPIC_API -> AnthropicAPIClient (no HTTP call; just constructed).
    client_anthropic = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.ANTHROPIC_API,
            api_key="I-LLMTOG-03-dummy-key",
        )
    )
    assert isinstance(client_anthropic, AnthropicAPIClient), (
        "I-LLMTOG-03 violated: ANTHROPIC_API mode did not produce "
        f"AnthropicAPIClient (got {type(client_anthropic).__name__})"
    )

    # CLAUDE_CLI -> ClaudeCLIClient (no subprocess invocation; just
    # constructed). Use sys.executable so shutil.which() resolves a
    # path that always exists on the runner.
    client_cli = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CLAUDE_CLI,
            claude_cli_executable=sys.executable,
        )
    )
    assert isinstance(client_cli, ClaudeCLIClient), (
        "I-LLMTOG-03 violated: CLAUDE_CLI mode did not produce "
        f"ClaudeCLIClient (got {type(client_cli).__name__})"
    )

    # ANTHROPIC_API with caching -> CachedClient wrapping AnthropicAPIClient.
    cached_anthropic = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.ANTHROPIC_API,
            api_key="I-LLMTOG-03-dummy-key",
            enable_cache=True,
        )
    )
    assert isinstance(cached_anthropic, CachedClient), (
        "I-LLMTOG-03 violated: ANTHROPIC_API + enable_cache did not "
        f"produce CachedClient (got {type(cached_anthropic).__name__})"
    )
    assert isinstance(cached_anthropic._inner, AnthropicAPIClient), (
        "I-LLMTOG-03 violated: CachedClient does not wrap "
        f"AnthropicAPIClient (got {type(cached_anthropic._inner).__name__})"
    )

    # CLAUDE_CLI with caching -> CachedClient wrapping ClaudeCLIClient.
    cached_cli = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CLAUDE_CLI,
            claude_cli_executable=sys.executable,
            enable_cache=True,
        )
    )
    assert isinstance(cached_cli, CachedClient), (
        "I-LLMTOG-03 violated: CLAUDE_CLI + enable_cache did not "
        f"produce CachedClient (got {type(cached_cli).__name__})"
    )
    assert isinstance(cached_cli._inner, ClaudeCLIClient), (
        "I-LLMTOG-03 violated: CachedClient does not wrap "
        f"ClaudeCLIClient (got {type(cached_cli._inner).__name__})"
    )

    # No backend should have been invoked during construction. The
    # MockClient records calls in `.calls` (a list); the OfflineStandIn
    # records calls as an int. Confirm both stayed at zero.
    assert client_mock.calls == [], (
        "I-LLMTOG-03 violated: MockClient was invoked at construction"
    )
    assert client_offline.calls == 0, (
        "I-LLMTOG-03 violated: OfflineStandInClient was invoked at "
        "construction"
    )
