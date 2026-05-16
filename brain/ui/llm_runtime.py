"""Phase 3.8b LLM Runtime Toggle.

Operator-facing helper that selects an ``LLMClient`` backend based on
CLI / env input. Default mode is offline; model-backed modes are
explicit opt-in only.

This module is the seam owner — it is the only ``brain/ui/`` module
permitted to import ``brain.llm.client``. It defines:

* :class:`LlmRuntimeMode` — closed ``str, Enum`` of accepted modes.
* :class:`LlmRuntimeConfig` — frozen / slots-bearing config record.
* :class:`LlmRuntimeError` — local exception for startup failures.
* :func:`parse_llm_runtime_args` — pure ``(argv, env) -> config`` parser.
* :func:`build_llm_client_from_config` — factory; never reads
  ``os.environ``.

Catalog rows driven from here:

* ``I-LLMTOG-01`` (REQUIRED) — Default ``LlmRuntimeConfig()`` builds
  ``OfflineStandInClient``.
* ``I-LLMTOG-02`` (REQUIRED) — ``LlmRuntimeMode`` is a finite closed
  enumeration.
* ``I-LLMTOG-03`` (REQUIRED) — Each accepted mode returns the expected
  concrete backend (or ``CachedClient`` wrapping the backend when
  caching is enabled).
* ``I-LLMTOG-04`` (REQUIRED) — Model-backed modes require explicit
  opt-in via ``--llm-mode`` or ``BRAIN_LLM_MODE``.
* ``I-LLMTOG-05`` (REQUIRED) — ``ANTHROPIC_API`` without a resolved
  ``api_key`` raises before launch.
* ``I-LLMTOG-06`` (REQUIRED) — ``CLAUDE_CLI`` without a discoverable
  executable raises before launch.
* ``I-LLMTOG-07`` (REQUIRED) — ``MOCK`` with empty ``mock_responses``
  raises before launch.
* ``I-LLMTOG-08`` (REQUIRED) — Cache wrapping is opt-in and mode-gated.
* ``I-LLMTOG-11`` (STRUCTURAL) — ``LlmRuntimeConfig`` is frozen /
  slots-bearing.
* ``I-LLMTOG-12`` (STRUCTURAL) — ``LlmRuntimeMode`` is a closed
  ``str, Enum``.
* ``I-LLMTOG-13`` (STRUCTURAL) — Static AST audit over this module
  rejects forbidden imports and module-level side effects.
* ``I-LLMTOG-16`` (REQUIRED) — ``CODEX_CLI`` without a discoverable
  ``codex_cli_executable`` raises ``LlmRuntimeError`` before launch.
* ``I-LLMTOG-17`` (REQUIRED) — ``CODEX_CLI`` factory returns a
  ``CodexCLIClient`` whose ``command[0]`` is the resolved executable.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Closed mode enumeration.
# ---------------------------------------------------------------------------


class LlmRuntimeMode(str, Enum):
    """Finite closed enumeration of accepted LLM runtime modes."""

    OFFLINE = "offline"
    MOCK = "mock"
    ANTHROPIC_API = "anthropic-api"
    CLAUDE_CLI = "claude-cli"
    CODEX_CLI = "codex-cli"


# ---------------------------------------------------------------------------
# Local exception.
# ---------------------------------------------------------------------------


class LlmRuntimeError(RuntimeError):
    """Local startup error for the LLM runtime toggle.

    Raised by :func:`parse_llm_runtime_args` and
    :func:`build_llm_client_from_config` when the operator-supplied
    config is insufficient. The entrypoint catches this exception and
    prints a bounded printable message to stderr before exiting with a
    non-zero return code.
    """


# ---------------------------------------------------------------------------
# Constants (defaults).
# ---------------------------------------------------------------------------


# Cache directory matches the existing CachedClient default; do not
# re-route writes elsewhere (corrigenda ruling E).
LLM_RUNTIME_CACHE_DIR: Path = Path("brain/.llm_cache")

# Default per-mode constants. These match the kickoff "Accepted constants"
# table and the catalog patch plan section 10. The constant-parity audit
# inside llm_runtime_static_audit.py asserts these against the kickoff /
# corrigenda numbers.
DEFAULT_TIMEOUT_SECONDS: float = 30.0
DEFAULT_MODEL: str = "claude-sonnet-4-6"
DEFAULT_CLAUDE_CLI_EXECUTABLE: str = "claude"
DEFAULT_CODEX_CLI_EXECUTABLE: str = "codex"


# ---------------------------------------------------------------------------
# LlmRuntimeConfig.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LlmRuntimeConfig:
    """Frozen / slots-bearing record describing the resolved LLM mode.

    All fields are bounded primitives, optional bounded strings, a
    bounded ``float`` timeout, a ``bool``, and a tuple of bounded
    printable strings (drives I-LLMTOG-11). No field is a callable,
    file handle, socket, subprocess handle, or LLM client instance.
    """

    mode: LlmRuntimeMode = LlmRuntimeMode.OFFLINE
    api_key: Optional[str] = None
    model: str = DEFAULT_MODEL
    claude_cli_executable: str = DEFAULT_CLAUDE_CLI_EXECUTABLE
    codex_cli_executable: str = DEFAULT_CODEX_CLI_EXECUTABLE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    enable_cache: bool = False
    mock_responses: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Argument / environment parser.
# ---------------------------------------------------------------------------


_ACCEPTED_MODE_VALUES: tuple[str, ...] = tuple(m.value for m in LlmRuntimeMode)


def _resolve_mode(value: str) -> LlmRuntimeMode:
    """Resolve a raw string into a :class:`LlmRuntimeMode`.

    Performs a single ``.strip()`` on the operator-supplied value
    (corrigenda ruling A) and matches case-sensitively against the
    closed enumeration. Anything else raises
    :class:`LlmRuntimeError`.
    """
    if not isinstance(value, str):
        raise LlmRuntimeError(
            "--llm-mode requires a string value (got "
            f"{type(value).__name__})"
        )
    stripped = value.strip()
    if not stripped:
        raise LlmRuntimeError("--llm-mode requires a non-empty value")
    try:
        return LlmRuntimeMode(stripped)
    except ValueError:
        accepted = ", ".join(_ACCEPTED_MODE_VALUES)
        raise LlmRuntimeError(
            f"unknown --llm-mode: {stripped!r}; expected one of "
            f"{{{accepted}}}"
        ) from None


def parse_llm_runtime_args(
    argv: list[str],
    env: dict[str, str],
) -> LlmRuntimeConfig:
    """Resolve operator-supplied argv + env into an :class:`LlmRuntimeConfig`.

    Environment resolution happens only here, never inside
    :func:`build_llm_client_from_config` (catalog patch plan section 4
    and ruling D). The CLI flag wins over the env override; the API
    key is resolved in order: CLI ``--llm-anthropic-api-key``, then
    ``BRAIN_ANTHROPIC_API_KEY`` (supplied env only), then
    ``ANTHROPIC_API_KEY`` (supplied env only).

    The parser only inspects the toggle-specific flags; unknown / other
    flags are ignored (the entrypoint's main argparse parser handles
    everything else). This keeps the toggle parser composable with the
    existing ``--print-once`` / ``--check-terminal`` / ``--width`` /
    ``--height`` flags.

    Raises :class:`LlmRuntimeError` on any local validation failure.
    """
    if not isinstance(argv, list):
        raise LlmRuntimeError(
            "parse_llm_runtime_args: argv must be a list "
            f"(got {type(argv).__name__})"
        )
    if not isinstance(env, dict):
        raise LlmRuntimeError(
            "parse_llm_runtime_args: env must be a dict "
            f"(got {type(env).__name__})"
        )

    # 1. Default mode is OFFLINE.
    resolved_mode: LlmRuntimeMode = LlmRuntimeMode.OFFLINE

    # 2. Environment override: BRAIN_LLM_MODE.
    env_mode_raw = env.get("BRAIN_LLM_MODE")
    if env_mode_raw is not None:
        resolved_mode = _resolve_mode(env_mode_raw)

    # 3. Per-mode CLI inputs collected before mode override resolution.
    cli_mode_raw: Optional[str] = None
    cli_api_key: Optional[str] = None
    cli_model: Optional[str] = None
    cli_claude_cli_executable: Optional[str] = None
    cli_codex_cli_executable: Optional[str] = None
    cli_timeout: Optional[float] = None
    cli_enable_cache: bool = False
    cli_mock_responses: list[str] = []

    i = 0
    n = len(argv)
    while i < n:
        token = argv[i]
        if not isinstance(token, str):
            i += 1
            continue
        # Support --flag=value and --flag value forms for each accepted
        # toggle flag. Anything else is ignored at this layer (the
        # outer argparse handles --print-once etc.).
        if token.startswith("--llm-mode="):
            cli_mode_raw = token[len("--llm-mode="):]
            i += 1
            continue
        if token == "--llm-mode":
            if i + 1 >= n:
                raise LlmRuntimeError("--llm-mode requires a value")
            cli_mode_raw = argv[i + 1]
            i += 2
            continue
        if token.startswith("--llm-anthropic-api-key="):
            cli_api_key = token[len("--llm-anthropic-api-key="):]
            i += 1
            continue
        if token == "--llm-anthropic-api-key":
            if i + 1 >= n:
                raise LlmRuntimeError(
                    "--llm-anthropic-api-key requires a value"
                )
            cli_api_key = argv[i + 1]
            i += 2
            continue
        if token.startswith("--llm-anthropic-model="):
            cli_model = token[len("--llm-anthropic-model="):]
            i += 1
            continue
        if token == "--llm-anthropic-model":
            if i + 1 >= n:
                raise LlmRuntimeError(
                    "--llm-anthropic-model requires a value"
                )
            cli_model = argv[i + 1]
            i += 2
            continue
        if token.startswith("--llm-claude-cli-executable="):
            cli_claude_cli_executable = token[
                len("--llm-claude-cli-executable="):
            ]
            i += 1
            continue
        if token == "--llm-claude-cli-executable":
            if i + 1 >= n:
                raise LlmRuntimeError(
                    "--llm-claude-cli-executable requires a value"
                )
            cli_claude_cli_executable = argv[i + 1]
            i += 2
            continue
        if token.startswith("--llm-codex-cli-executable="):
            cli_codex_cli_executable = token[
                len("--llm-codex-cli-executable="):
            ]
            i += 1
            continue
        if token == "--llm-codex-cli-executable":
            if i + 1 >= n:
                raise LlmRuntimeError(
                    "--llm-codex-cli-executable requires a value"
                )
            cli_codex_cli_executable = argv[i + 1]
            i += 2
            continue
        if token.startswith("--llm-timeout="):
            cli_timeout = _parse_timeout(token[len("--llm-timeout="):])
            i += 1
            continue
        if token == "--llm-timeout":
            if i + 1 >= n:
                raise LlmRuntimeError("--llm-timeout requires a value")
            cli_timeout = _parse_timeout(argv[i + 1])
            i += 2
            continue
        if token == "--llm-enable-cache":
            cli_enable_cache = True
            i += 1
            continue
        if token.startswith("--llm-mock-response="):
            cli_mock_responses.append(token[len("--llm-mock-response="):])
            i += 1
            continue
        if token == "--llm-mock-response":
            if i + 1 >= n:
                raise LlmRuntimeError(
                    "--llm-mock-response requires a value"
                )
            cli_mock_responses.append(argv[i + 1])
            i += 2
            continue
        i += 1

    # 4. CLI mode overrides env mode.
    if cli_mode_raw is not None:
        resolved_mode = _resolve_mode(cli_mode_raw)

    # 5. Resolve api_key precedence: CLI > BRAIN_ANTHROPIC_API_KEY >
    #    ANTHROPIC_API_KEY. Only the supplied env is consulted.
    api_key: Optional[str] = None
    if cli_api_key is not None and cli_api_key != "":
        api_key = cli_api_key
    elif env.get("BRAIN_ANTHROPIC_API_KEY"):
        api_key = env["BRAIN_ANTHROPIC_API_KEY"]
    elif env.get("ANTHROPIC_API_KEY"):
        api_key = env["ANTHROPIC_API_KEY"]

    # 6. Other per-mode fields take defaults unless the operator
    #    supplied an override.
    model: str = cli_model if cli_model is not None else DEFAULT_MODEL
    claude_cli_executable: str = (
        cli_claude_cli_executable
        if cli_claude_cli_executable is not None
        else DEFAULT_CLAUDE_CLI_EXECUTABLE
    )
    codex_cli_executable: str = (
        cli_codex_cli_executable
        if cli_codex_cli_executable is not None
        else DEFAULT_CODEX_CLI_EXECUTABLE
    )
    timeout_seconds: float = (
        cli_timeout if cli_timeout is not None else DEFAULT_TIMEOUT_SECONDS
    )

    return LlmRuntimeConfig(
        mode=resolved_mode,
        api_key=api_key,
        model=model,
        claude_cli_executable=claude_cli_executable,
        codex_cli_executable=codex_cli_executable,
        timeout_seconds=timeout_seconds,
        enable_cache=cli_enable_cache,
        mock_responses=tuple(cli_mock_responses),
    )


def _which(executable: str) -> Optional[str]:
    """Locate ``executable`` on PATH.

    Local stdlib-only replacement for :func:`shutil.which`. The I-UI-07
    audit rejects ``shutil`` (filesystem mutation surface) from any
    file under ``brain/ui/``; we only need read-only PATH resolution
    for the ``CLAUDE_CLI`` availability check (corrigenda ruling D),
    so we walk ``PATH`` ourselves using :mod:`os.path` and
    :func:`os.access`. No filesystem mutation occurs.

    Returns the absolute path of the first executable match, or
    ``None`` when no match is found.
    """
    if not isinstance(executable, str) or not executable:
        return None

    # Absolute or explicit-relative path: probe directly.
    if os.path.sep in executable or (
        os.path.altsep is not None and os.path.altsep in executable
    ):
        if os.path.isfile(executable) and os.access(executable, os.X_OK):
            return executable
        return None

    path_value = os.environ.get("PATH", os.defpath)
    if not path_value:
        return None
    for directory in path_value.split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, executable)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _parse_timeout(value: str) -> float:
    """Parse a printable float timeout value."""
    if not isinstance(value, str):
        raise LlmRuntimeError(
            "--llm-timeout requires a string value "
            f"(got {type(value).__name__})"
        )
    try:
        parsed = float(value)
    except ValueError:
        raise LlmRuntimeError(
            f"--llm-timeout requires a numeric value (got {value!r})"
        ) from None
    if parsed <= 0.0:
        raise LlmRuntimeError(
            f"--llm-timeout must be positive (got {parsed!r})"
        )
    return parsed


# ---------------------------------------------------------------------------
# Factory.
# ---------------------------------------------------------------------------


def build_llm_client_from_config(config: LlmRuntimeConfig) -> object:
    """Build an ``LLMClient``-compatible backend from a config.

    The factory NEVER reads ``os.environ``: every environment value
    has already been folded into ``config`` by
    :func:`parse_llm_runtime_args`. Per-mode credential / tool
    availability checks happen here, before any session is constructed
    (corrigenda ruling D). All local failures raise
    :class:`LlmRuntimeError`.

    Returns one of:

    * :class:`OfflineStandInClient` — for ``OFFLINE``.
    * :class:`brain.llm.client.MockClient` — for ``MOCK``.
    * :class:`brain.llm.client.AnthropicAPIClient` — for ``ANTHROPIC_API``.
    * :class:`brain.llm.client.ClaudeCLIClient` — for ``CLAUDE_CLI``.

    When ``config.enable_cache`` is ``True`` and the mode is one of
    ``ANTHROPIC_API`` / ``CLAUDE_CLI``, the returned backend is wrapped
    in :class:`brain.llm.client.CachedClient` with ``cache_dir=
    LLM_RUNTIME_CACHE_DIR``.
    """
    if not isinstance(config, LlmRuntimeConfig):
        raise LlmRuntimeError(
            "build_llm_client_from_config requires LlmRuntimeConfig "
            f"(got {type(config).__name__})"
        )

    mode = config.mode

    # OFFLINE / MOCK reject caching at the factory boundary.
    if config.enable_cache and mode in (
        LlmRuntimeMode.OFFLINE,
        LlmRuntimeMode.MOCK,
    ):
        raise LlmRuntimeError(
            f"--llm-enable-cache is not supported for mode {mode.value!r}; "
            "caching deterministic clients adds no value"
        )

    if mode is LlmRuntimeMode.OFFLINE:
        return _build_offline_client()

    if mode is LlmRuntimeMode.MOCK:
        if len(config.mock_responses) == 0:
            raise LlmRuntimeError(
                "mode 'mock' requires at least one --llm-mock-response"
            )
        return _build_mock_client(config)

    if mode is LlmRuntimeMode.ANTHROPIC_API:
        if not config.api_key:
            raise LlmRuntimeError(
                "mode 'anthropic-api' requires --llm-anthropic-api-key, "
                "BRAIN_ANTHROPIC_API_KEY, or ANTHROPIC_API_KEY"
            )
        backend = _build_anthropic_client(config)
        if config.enable_cache:
            return _wrap_cache(backend)
        return backend

    if mode is LlmRuntimeMode.CLAUDE_CLI:
        if _which(config.claude_cli_executable) is None:
            raise LlmRuntimeError(
                f"mode 'claude-cli' requires executable "
                f"{config.claude_cli_executable!r} on PATH"
            )
        backend = _build_claude_cli_client(config)
        if config.enable_cache:
            return _wrap_cache(backend)
        return backend

    if mode is LlmRuntimeMode.CODEX_CLI:
        if _which(config.codex_cli_executable) is None:
            raise LlmRuntimeError(
                f"mode 'codex-cli' requires executable "
                f"{config.codex_cli_executable!r} on PATH"
            )
        backend = _build_codex_cli_client(config)
        if config.enable_cache:
            return _wrap_cache(backend)
        return backend

    # Defensive: LlmRuntimeMode is closed, but keep the branch fail-loud.
    raise LlmRuntimeError(f"unhandled LlmRuntimeMode: {mode!r}")


def _build_offline_client() -> object:
    """Construct the deterministic offline stand-in client."""
    from brain.ui.__main__ import OfflineStandInClient

    return OfflineStandInClient()


def _build_mock_client(config: LlmRuntimeConfig) -> object:
    """Construct a :class:`brain.llm.client.MockClient` from config."""
    from brain.llm.client import MockClient

    return MockClient(config.mock_responses)


def _build_anthropic_client(config: LlmRuntimeConfig) -> object:
    """Construct a :class:`brain.llm.client.AnthropicAPIClient`."""
    from brain.llm.client import AnthropicAPIClient

    return AnthropicAPIClient(
        api_key=config.api_key,
        model=config.model,
        timeout_seconds=config.timeout_seconds,
    )


def _build_claude_cli_client(config: LlmRuntimeConfig) -> object:
    """Construct a :class:`brain.llm.client.ClaudeCLIClient`."""
    from brain.llm.client import ClaudeCLIClient

    return ClaudeCLIClient(
        command=(
            config.claude_cli_executable,
            "-p",
            "--no-session-persistence",
            "--permission-mode",
            "default",
        ),
        timeout_seconds=config.timeout_seconds,
    )


def _build_codex_cli_client(config: LlmRuntimeConfig) -> object:
    """Construct a :class:`brain.llm.client.CodexCLIClient`.

    Mirrors :func:`_build_claude_cli_client`. The command tuple is
    locked to ``(<resolved-executable>, "exec")`` per the Phase 3.11
    corrigenda Section 7.
    """
    from brain.llm.client import CodexCLIClient

    return CodexCLIClient(
        command=(config.codex_cli_executable, "exec"),
        timeout_seconds=config.timeout_seconds,
    )


def _wrap_cache(inner: object) -> object:
    """Wrap an inner client in :class:`brain.llm.client.CachedClient`."""
    from brain.llm.client import CachedClient

    return CachedClient(inner, cache_dir=LLM_RUNTIME_CACHE_DIR)


# ---------------------------------------------------------------------------
# Startup message helper.
# ---------------------------------------------------------------------------


def format_startup_mode_line(config: LlmRuntimeConfig) -> str:
    """Format the bounded printable startup line for the launch path.

    The line is printed once on launch (not under ``--print-once`` /
    ``--check-terminal``) so the operator gets tactile feedback that
    the mode they requested is the mode they got (corrigenda ruling
    F).
    """
    mode = config.mode
    if mode is LlmRuntimeMode.OFFLINE:
        explanation = "default offline stand-in; no network, no shell"
    elif mode is LlmRuntimeMode.MOCK:
        explanation = "deterministic mock; no network, no shell"
    elif mode is LlmRuntimeMode.ANTHROPIC_API:
        explanation = (
            f"anthropic-api; cache={'on' if config.enable_cache else 'off'}"
        )
    elif mode is LlmRuntimeMode.CLAUDE_CLI:
        explanation = (
            f"claude-cli; executable={config.claude_cli_executable}; "
            f"cache={'on' if config.enable_cache else 'off'}"
        )
    elif mode is LlmRuntimeMode.CODEX_CLI:
        explanation = (
            f"codex-cli; executable={config.codex_cli_executable}; "
            f"cache={'on' if config.enable_cache else 'off'}"
        )
    else:  # defensive
        explanation = "unknown mode"
    return f"brain.ui: llm runtime mode = {mode.value} ({explanation})"


__all__ = [
    "DEFAULT_CLAUDE_CLI_EXECUTABLE",
    "DEFAULT_CODEX_CLI_EXECUTABLE",
    "DEFAULT_MODEL",
    "DEFAULT_TIMEOUT_SECONDS",
    "LLM_RUNTIME_CACHE_DIR",
    "LlmRuntimeConfig",
    "LlmRuntimeError",
    "LlmRuntimeMode",
    "build_llm_client_from_config",
    "format_startup_mode_line",
    "parse_llm_runtime_args",
]
