"""``LLMClient`` Protocol + three v1 backends.

Per the Phase 2 v1 plan, the brain stays decoupled from any specific LLM
access mechanism via the ``LLMClient`` Protocol seam. v1 ships:

  - ``AnthropicAPIClient``: direct HTTP via stdlib ``urllib.request``
    (no third-party dep). Used in cloud-sandbox runs.
  - ``MockClient``: pre-canned sequential responses. Used by every
    fixture that needs a deterministic LLM stand-in.
  - ``CachedClient``: wraps another client with a SHA-256 prompt cache
    on disk under ``brain/.llm_cache/``. Used by the scenario CLI to
    make replays deterministic across runs.

Future backends (``SubprocessClient``, ``IPCClient``) are deliberately
out of scope for v1 — see ``PHASE2_v1_KICKOFF.md`` and the plan.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol, runtime_checkable

from brain.trace import CognitionTracer, NullTracer


@runtime_checkable
class LLMClient(Protocol):
    """Minimal LLM transport seam.

    Implementations submit ``prompt`` to the underlying model and return
    the raw string response. The caller is responsible for parsing /
    validating; transport failures (network, auth, rate limit) raise as
    ordinary exceptions and are *operational* failures, not invariant
    violations.
    """

    def eval_consistency(self, prompt: str) -> str:
        ...


# ---------------------------------------------------------------------------
# AnthropicAPIClient — direct HTTP, no SDK dependency.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AnthropicAPIClient:
    """Direct HTTP client for the Anthropic Messages API.

    Uses ``urllib.request`` so we incur no third-party runtime dep
    (consistent with v0's stdlib-only convention). Reads
    ``ANTHROPIC_API_KEY`` from env when ``api_key`` is None; raises
    ``RuntimeError`` if neither is set at first call time.

    Default model: ``claude-sonnet-4-6`` (Sonnet 4.5 is on a retirement
    path, per corrigenda C2).

    Phase 2 v1.1: ``tracer`` is stored at construction for symmetry with
    ``CachedClient``. The retry shell (``LLMBackedPtCns``) owns the
    ``llm.request`` / ``llm.response`` events because it has the
    content_id / attempt context the taxonomy requires. ``tracer`` is
    observation-only; its presence cannot affect the returned string.
    """

    api_key: str | None = None
    model: str = "claude-sonnet-4-6"
    base_url: str = "https://api.anthropic.com"
    # max_tokens=256: enough budget for verbose failure responses so the
    # retry feedback loop can include the LLM's actual bad output verbatim.
    # Happy path uses ~5 tokens; the headroom is for retry observability
    # (corrigenda C3).
    max_tokens: int = 256
    anthropic_version: str = "2023-06-01"
    timeout_seconds: float = 30.0
    tracer: CognitionTracer = field(default_factory=NullTracer)

    def _resolved_key(self) -> str:
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "AnthropicAPIClient: no API key (set ANTHROPIC_API_KEY or "
                "pass api_key= explicitly)"
            )
        return key

    def eval_consistency(self, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/v1/messages",
            data=body,
            method="POST",
            headers={
                "content-type": "application/json",
                "x-api-key": self._resolved_key(),
                "anthropic-version": self.anthropic_version,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise RuntimeError(
                f"AnthropicAPIClient HTTP {exc.code}: {err_body[:500]}"
            ) from exc
        # Messages API returns {"content": [{"type":"text","text":"..."}], ...}
        content = payload.get("content")
        if not content or not isinstance(content, list):
            raise RuntimeError(
                f"AnthropicAPIClient: unexpected response payload: {payload!r}"
            )
        first = content[0]
        text = first.get("text") if isinstance(first, dict) else None
        if not isinstance(text, str):
            raise RuntimeError(
                f"AnthropicAPIClient: response missing text content: {payload!r}"
            )
        return text


# ---------------------------------------------------------------------------
# MockClient — deterministic canned responses for fixtures.
# ---------------------------------------------------------------------------


class MockClient:
    """Sequential canned-response client. Pops one response per call.

    Used by ``brain/fixtures/llm_protocol.py`` and
    ``brain/fixtures/scenario_v1.py`` to drive deterministic test
    behavior without touching the real API.
    """

    def __init__(self, responses: Iterable[str]) -> None:
        self._iter: Iterator[str] = iter(responses)
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise RuntimeError("MockClient exhausted") from exc


# ---------------------------------------------------------------------------
# CachedClient — disk-backed prompt cache wrapping any inner client.
# ---------------------------------------------------------------------------


class CachedClient:
    """SHA-256 prompt-keyed disk cache wrapping an inner ``LLMClient``.

    On hit: returns the cached response without calling ``inner``.
    On miss: calls ``inner``, persists ``{key}.json`` under
    ``cache_dir``, returns the response.

    This is the across-tick / across-run determinism layer that I-LLM-02
    reports on. ``LLMBackedPtCns`` does its own per-instance caching for
    cogito short-circuit only; everything else flows through here.

    Phase 2 v1.1: optional ``tracer`` records ``llm.cache_hit`` and
    ``llm.cache_miss`` events with an 8-char key prefix for debugging.
    """

    def __init__(
        self,
        inner: LLMClient,
        cache_dir: Path = Path("brain/.llm_cache"),
        tracer: CognitionTracer | None = None,
    ) -> None:
        self._inner = inner
        self._cache_dir = cache_dir
        self._tracer: CognitionTracer = tracer if tracer is not None else NullTracer()
        self.hit_count = 0
        self.miss_count = 0

    def _key_path(self, prompt: str) -> tuple[Path, str]:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json", digest

    def eval_consistency(self, prompt: str) -> str:
        path, digest = self._key_path(prompt)
        key_prefix = digest[:8]
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                response = payload["response"]
            except (OSError, ValueError, KeyError) as exc:
                raise RuntimeError(
                    f"CachedClient: corrupt cache entry at {path}: {exc}"
                ) from exc
            self.hit_count += 1
            self._tracer.record("llm.cache_hit", {"cache_key_prefix": key_prefix})
            return response
        self.miss_count += 1
        self._tracer.record("llm.cache_miss", {"cache_key_prefix": key_prefix})
        response = self._inner.eval_consistency(prompt)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"prompt": prompt, "response": response}, indent=2),
            encoding="utf-8",
        )
        return response


# ---------------------------------------------------------------------------
# ClaudeCLIClient — subprocess wrapper for the local `claude -p` CLI.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ClaudeCLIClient:
    """``LLMClient`` that delegates to the local Claude Code CLI in
    non-interactive mode (``claude -p <prompt>``).

    This is the ``SubprocessClient`` pattern explicitly anticipated by
    ``PHASE2_v1_KICKOFF.md``'s "Future backends" section, shipped here
    as a small additive backend so a real-LLM trace can be produced
    against a Max/Pro subscription without provisioning an
    ``ANTHROPIC_API_KEY``. Authentication is whatever the local CLI
    already has — no env var management, no token plumbing.

    Honors the ``LLMClient`` Protocol (I-LLM-04); a stored ``tracer``
    field exists for symmetry with the other backends but the retry
    shell (``LLMBackedPtCns``) owns the ``llm.request`` / ``llm.response``
    events because it has the content_id / attempt context.
    """

    # `-p` runs non-interactively; `--no-session-persistence` keeps each
    # call stateless so the parent Claude Code session's permissions or
    # memory cannot leak into the child; `--permission-mode default`
    # keeps the call from inheriting an elevated mode from the parent.
    command: tuple[str, ...] = (
        "claude",
        "-p",
        "--no-session-persistence",
        "--permission-mode",
        "default",
    )
    timeout_seconds: float = 60.0
    tracer: CognitionTracer = field(default_factory=NullTracer)
    # When invoking the nested CLI, drop into a neutral cwd so the child
    # session does not auto-discover this repo's CLAUDE.md / hooks.
    cwd: str = "/tmp"

    def __post_init__(self) -> None:
        # Resolve the command's executable once so a missing binary
        # surfaces immediately rather than at the first call.
        exe = self.command[0] if self.command else ""
        if not exe or shutil.which(exe) is None:
            raise RuntimeError(
                f"ClaudeCLIClient: executable {exe!r} not found on PATH. "
                "Install the Claude Code CLI or override `command` with a "
                "callable subprocess (e.g. ('codex', '-p'))."
            )

    def eval_consistency(self, prompt: str) -> str:
        try:
            completed = subprocess.run(
                [*self.command, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                cwd=self.cwd,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"ClaudeCLIClient: `{' '.join(self.command)}` timed out after "
                f"{self.timeout_seconds}s"
            ) from exc
        if completed.returncode != 0:
            raise RuntimeError(
                f"ClaudeCLIClient: subprocess returned non-zero exit "
                f"{completed.returncode}. stderr: {completed.stderr[:500]!r}"
            )
        return completed.stdout


# ---------------------------------------------------------------------------
# CodexCLIClient — subprocess wrapper for the local `codex exec` CLI.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CodexCLIClient:
    """``LLMClient`` that delegates to the local OpenAI Codex CLI in
    non-interactive mode (``codex exec <prompt>``).

    Phase 3.11 Codex CLI Runtime Option — mirrors :class:`ClaudeCLIClient`
    but targets the OpenAI codex CLI's non-interactive ``exec``
    subcommand. The default command tuple is ``("codex", "exec")``;
    operators may override the executable via
    ``--llm-codex-cli-executable``. Authentication is whatever the local
    codex binary already has — no env var management, no token plumbing.

    Honors the ``LLMClient`` Protocol (I-LLM-04); a stored ``tracer``
    field exists for symmetry with the other backends but the retry
    shell (``LLMBackedPtCns``) owns the ``llm.request`` / ``llm.response``
    events because it has the content_id / attempt context.

    Drives I-LLMTOG-16 / I-LLMTOG-17 (REQUIRED) and I-LLMTOG-18
    (OBSERVED).
    """

    # ``exec`` runs the codex CLI non-interactively for a single
    # prompt-response cycle. The tuple is minimal: no version-specific
    # flags whose semantics could shift between codex binary versions
    # (corrigenda Section 7).
    command: tuple[str, ...] = ("codex", "exec")
    timeout_seconds: float = 60.0
    tracer: CognitionTracer = field(default_factory=NullTracer)
    # When invoking the nested CLI, drop into a neutral cwd so the child
    # session does not auto-discover this repo's hooks or configuration.
    cwd: str = "/tmp"

    def __post_init__(self) -> None:
        # Resolve the command's executable once so a missing binary
        # surfaces immediately rather than at the first call.
        exe = self.command[0] if self.command else ""
        if not exe or shutil.which(exe) is None:
            raise RuntimeError(
                f"CodexCLIClient: executable {exe!r} not found on PATH. "
                "Install the codex CLI or override `command` with a "
                "callable subprocess."
            )

    def eval_consistency(self, prompt: str) -> str:
        try:
            completed = subprocess.run(
                [*self.command, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                cwd=self.cwd,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"CodexCLIClient: `{' '.join(self.command)}` timed out after "
                f"{self.timeout_seconds}s"
            ) from exc
        if completed.returncode != 0:
            raise RuntimeError(
                f"CodexCLIClient: subprocess returned non-zero exit "
                f"{completed.returncode}. stderr: {completed.stderr[:500]!r}"
            )
        return completed.stdout


__all__ = [
    "LLMClient",
    "AnthropicAPIClient",
    "MockClient",
    "CachedClient",
    "ClaudeCLIClient",
    "CodexCLIClient",
]
