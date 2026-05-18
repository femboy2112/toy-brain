"""Phase 3.14 LLM cache runtime policy fixture.

Drives:

* ``I-LLMCACHE-02`` (REQUIRED) — Model-backed modes enable L1 transport
  cache by default after explicit model-backed opt-in; offline remains
  default.
* ``I-LLMCACHE-03`` (REQUIRED) — ``--llm-disable-cache`` disables cache
  for model-backed modes; ``--llm-enable-cache`` remains a compatible
  affirmation; conflicting flags raise ``LlmRuntimeError``.
* ``I-LLMCACHE-04`` (REQUIRED) — OFFLINE / MOCK never read or write
  L1 / L2 cache files; ``--llm-enable-cache`` rejects for those modes;
  ``--llm-disable-cache`` is a no-op for those modes.
"""
from __future__ import annotations

import sys

from brain.invariants import register
from brain.llm.client import (
    AnthropicAPIClient,
    CachedClient,
    ClaudeCLIClient,
    CodexCLIClient,
    MockClient,
)
from brain.ui.__main__ import OfflineStandInClient
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeError,
    LlmRuntimeMode,
    build_llm_client_from_config,
    parse_llm_runtime_args,
)


@register("I-LLMCACHE-02", status="REQUIRED")
def check_I_LLMCACHE_02_default_on_for_model_backed() -> None:
    # Empty argv + empty env: OFFLINE default; cache stays off.
    config = parse_llm_runtime_args([], {})
    assert config.mode is LlmRuntimeMode.OFFLINE, (
        "I-LLMCACHE-02 violated: empty argv did not resolve to OFFLINE "
        f"(got {config.mode!r})"
    )
    assert config.enable_cache is False, (
        "I-LLMCACHE-02 violated: OFFLINE default flipped cache on "
        f"(got enable_cache={config.enable_cache!r})"
    )

    # Each model-backed mode flips cache on by default at the parser.
    for value in ("anthropic-api", "claude-cli", "codex-cli"):
        config = parse_llm_runtime_args(["--llm-mode", value], {})
        assert config.enable_cache is True, (
            "I-LLMCACHE-02 violated: --llm-mode "
            f"{value} did not default cache on "
            f"(got enable_cache={config.enable_cache!r})"
        )

    # BRAIN_LLM_MODE env override also flips cache on by default.
    config = parse_llm_runtime_args(
        [], {"BRAIN_LLM_MODE": "anthropic-api"}
    )
    assert config.enable_cache is True, (
        "I-LLMCACHE-02 violated: BRAIN_LLM_MODE=anthropic-api did not "
        f"default cache on (got enable_cache={config.enable_cache!r})"
    )

    # MOCK does not flip the cache default.
    config = parse_llm_runtime_args(["--llm-mode", "mock"], {})
    assert config.enable_cache is False, (
        "I-LLMCACHE-02 violated: --llm-mode mock should keep cache off "
        f"(got enable_cache={config.enable_cache!r})"
    )

    # Factory under parsed default for codex-cli yields CachedClient
    # wrapping CodexCLIClient. Use sys.executable so the local _which
    # check finds the binary without depending on real codex.
    config = parse_llm_runtime_args(
        ["--llm-mode", "codex-cli", "--llm-codex-cli-executable", sys.executable],
        {},
    )
    client = build_llm_client_from_config(config)
    assert isinstance(client, CachedClient), (
        "I-LLMCACHE-02 violated: codex-cli default did not produce "
        f"CachedClient (got {type(client).__name__})"
    )
    assert isinstance(client._inner, CodexCLIClient), (
        "I-LLMCACHE-02 violated: CachedClient does not wrap "
        f"CodexCLIClient (got {type(client._inner).__name__})"
    )


@register("I-LLMCACHE-03", status="REQUIRED")
def check_I_LLMCACHE_03_disable_cache_flag() -> None:
    # --llm-disable-cache forces cache off for model-backed modes.
    config = parse_llm_runtime_args(
        ["--llm-mode", "codex-cli", "--llm-disable-cache"], {}
    )
    assert config.enable_cache is False, (
        "I-LLMCACHE-03 violated: --llm-disable-cache did not force "
        f"cache off (got enable_cache={config.enable_cache!r})"
    )

    # --llm-enable-cache remains accepted; for model-backed it is a
    # compatible explicit affirmation that does not change the new
    # default.
    config = parse_llm_runtime_args(
        ["--llm-mode", "codex-cli", "--llm-enable-cache"], {}
    )
    assert config.enable_cache is True, (
        "I-LLMCACHE-03 violated: --llm-enable-cache did not affirm "
        f"cache-on (got enable_cache={config.enable_cache!r})"
    )

    # Conflicting flags raise.
    for argv in (
        ["--llm-mode", "codex-cli", "--llm-enable-cache", "--llm-disable-cache"],
        ["--llm-mode", "anthropic-api", "--llm-disable-cache", "--llm-enable-cache"],
        ["--llm-mode", "offline", "--llm-enable-cache", "--llm-disable-cache"],
    ):
        try:
            parse_llm_runtime_args(argv, {})
        except LlmRuntimeError as exc:
            msg = str(exc).lower()
            assert "enable-cache" in msg and "disable-cache" in msg, (
                "I-LLMCACHE-03 violated: conflicting-flag error does not "
                f"name both flags (got {exc!r})"
            )
        else:
            raise AssertionError(
                "I-LLMCACHE-03 violated: conflicting flags did not raise "
                f"for argv={argv!r}"
            )

    # Factory: codex-cli + disable -> bare CodexCLIClient (no wrap).
    config = parse_llm_runtime_args(
        [
            "--llm-mode", "codex-cli",
            "--llm-codex-cli-executable", sys.executable,
            "--llm-disable-cache",
        ],
        {},
    )
    client = build_llm_client_from_config(config)
    assert isinstance(client, CodexCLIClient), (
        "I-LLMCACHE-03 violated: codex-cli + disable-cache did not "
        f"produce bare CodexCLIClient (got {type(client).__name__})"
    )
    assert not isinstance(client, CachedClient), (
        "I-LLMCACHE-03 violated: codex-cli + disable-cache wrapped in "
        "CachedClient unexpectedly"
    )


@register("I-LLMCACHE-04", status="REQUIRED")
def check_I_LLMCACHE_04_offline_mock_isolation() -> None:
    # --llm-enable-cache continues to raise for OFFLINE.
    try:
        build_llm_client_from_config(
            LlmRuntimeConfig(mode=LlmRuntimeMode.OFFLINE, enable_cache=True)
        )
    except LlmRuntimeError as exc:
        assert "offline" in str(exc).lower(), (
            "I-LLMCACHE-04 violated: OFFLINE cache rejection does not "
            f"name the mode (got {exc!r})"
        )
    else:
        raise AssertionError(
            "I-LLMCACHE-04 violated: OFFLINE + enable_cache did not raise"
        )

    # --llm-enable-cache continues to raise for MOCK.
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
            "I-LLMCACHE-04 violated: MOCK cache rejection does not name "
            f"the mode (got {exc!r})"
        )
    else:
        raise AssertionError(
            "I-LLMCACHE-04 violated: MOCK + enable_cache did not raise"
        )

    # --llm-disable-cache for OFFLINE is a no-op at the parser; the
    # resolved config keeps enable_cache=False and the factory returns
    # the bare OfflineStandInClient.
    config = parse_llm_runtime_args(
        ["--llm-mode", "offline", "--llm-disable-cache"], {}
    )
    assert config.enable_cache is False, (
        "I-LLMCACHE-04 violated: OFFLINE + --llm-disable-cache did not "
        f"keep cache off (got enable_cache={config.enable_cache!r})"
    )
    client = build_llm_client_from_config(config)
    assert isinstance(client, OfflineStandInClient), (
        "I-LLMCACHE-04 violated: OFFLINE + --llm-disable-cache did not "
        f"produce OfflineStandInClient (got {type(client).__name__})"
    )

    # --llm-disable-cache for MOCK is a no-op.
    config = parse_llm_runtime_args(
        [
            "--llm-mode", "mock",
            "--llm-mock-response", "PRESERVE",
            "--llm-disable-cache",
        ],
        {},
    )
    assert config.enable_cache is False, (
        "I-LLMCACHE-04 violated: MOCK + --llm-disable-cache did not "
        f"keep cache off (got enable_cache={config.enable_cache!r})"
    )
    client = build_llm_client_from_config(config)
    assert isinstance(client, MockClient), (
        "I-LLMCACHE-04 violated: MOCK + --llm-disable-cache did not "
        f"produce MockClient (got {type(client).__name__})"
    )
    assert not isinstance(client, CachedClient), (
        "I-LLMCACHE-04 violated: MOCK + --llm-disable-cache wrapped in "
        "CachedClient unexpectedly"
    )

    # Sanity: anthropic-api can still construct under enable_cache when
    # the api_key is supplied (existing I-LLMTOG-08 path).
    client = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.ANTHROPIC_API,
            api_key="I-LLMCACHE-04-dummy",
            enable_cache=True,
        )
    )
    assert isinstance(client, CachedClient), (
        "I-LLMCACHE-04 violated: anthropic-api + enable_cache did not "
        f"produce CachedClient (got {type(client).__name__})"
    )
    assert isinstance(client._inner, AnthropicAPIClient), (
        "I-LLMCACHE-04 violated: CachedClient does not wrap "
        f"AnthropicAPIClient (got {type(client._inner).__name__})"
    )
    # Sanity: claude-cli also wraps when enable_cache=True (I-LLMTOG-08).
    client = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CLAUDE_CLI,
            claude_cli_executable=sys.executable,
            enable_cache=True,
        )
    )
    assert isinstance(client, CachedClient), (
        "I-LLMCACHE-04 violated: claude-cli + enable_cache did not "
        f"produce CachedClient (got {type(client).__name__})"
    )
    assert isinstance(client._inner, ClaudeCLIClient), (
        "I-LLMCACHE-04 violated: CachedClient does not wrap "
        f"ClaudeCLIClient (got {type(client._inner).__name__})"
    )
