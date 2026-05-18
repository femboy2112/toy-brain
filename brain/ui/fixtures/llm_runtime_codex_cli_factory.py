"""Phase 3.11 codex-cli-factory fixture.

Drives:

* ``I-LLMTOG-17`` (REQUIRED) — ``CODEX_CLI`` factory returns the
  documented backend without invoking it. The fixture uses
  ``sys.executable`` as a guaranteed-present executable so CI does not
  require the real codex CLI. The fixture asserts construction only; it
  does not invoke ``eval_consistency``.
"""
from __future__ import annotations

import sys

from brain.invariants import register
from brain.llm.client import CodexCLIClient
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-17", status="REQUIRED")
def check_I_LLMTOG_17_codex_cli_factory() -> None:
    # CODEX_CLI -> CodexCLIClient (no subprocess invocation; just
    # constructed). Use sys.executable so the local _which() helper
    # resolves a path that always exists on the runner.
    client = build_llm_client_from_config(
        LlmRuntimeConfig(
            mode=LlmRuntimeMode.CODEX_CLI,
            codex_cli_executable=sys.executable,
        )
    )
    assert isinstance(client, CodexCLIClient), (
        "I-LLMTOG-17 violated: CODEX_CLI mode did not produce "
        f"CodexCLIClient (got {type(client).__name__})"
    )
    # The factory binds command[0] to the resolved executable path so
    # the OBSERVED smoke path (I-LLMTOG-18) can rely on a single
    # invocation against the operator-supplied binary.
    assert client.command[0] == sys.executable, (
        "I-LLMTOG-17 violated: CodexCLIClient.command[0] is not the "
        f"resolved executable (got {client.command[0]!r}, expected "
        f"{sys.executable!r})"
    )
    # The locked command tuple is
    # ("<resolved-exe>", "exec", "--skip-git-repo-check") at the
    # LlmRuntimeConfig boundary; the factory substitutes the resolved
    # executable in position 0, keeps "exec" in position 1
    # (corrigenda Section 7), and adds "--skip-git-repo-check" in
    # position 2 so codex-cli >= 0.130 does not refuse the neutral
    # cwd=/tmp before forwarding the prompt (Phase 3.17 Step 3).
    assert client.command[1] == "exec", (
        "I-LLMTOG-17 violated: CodexCLIClient.command[1] is not 'exec' "
        f"(got {client.command[1]!r})"
    )
    # Phase 3.17: --skip-git-repo-check must be present so codex-cli
    # >= 0.130 does not refuse cwd=/tmp before sending the prompt.
    assert "--skip-git-repo-check" in client.command, (
        "I-LLMTOG-17 violated: CodexCLIClient.command lacks "
        f"--skip-git-repo-check (got {client.command!r})"
    )
    assert client.command[2] == "--skip-git-repo-check", (
        "I-LLMTOG-17 violated: CodexCLIClient.command[2] is not "
        f"--skip-git-repo-check (got {client.command[2]!r})"
    )
    # Tuple shape audit: bounded tuple of plain strings; no shell=True
    # hooks; no callable smuggled in.
    assert isinstance(client.command, tuple), (
        "I-LLMTOG-17 violated: CodexCLIClient.command is not a tuple "
        f"(got {type(client.command).__name__})"
    )
    assert all(isinstance(part, str) for part in client.command), (
        "I-LLMTOG-17 violated: CodexCLIClient.command contains a "
        f"non-str entry (got {client.command!r})"
    )
    # Neutral cwd preserved (Phase 3.11 corrigenda Section 7).
    assert client.cwd == "/tmp", (
        "I-LLMTOG-17 violated: CodexCLIClient.cwd drifted from /tmp "
        f"(got {client.cwd!r})"
    )
