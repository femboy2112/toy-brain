"""Phase 3.8b print-once-independence fixture.

Drives:

* ``I-LLMTOG-10`` (REQUIRED) — ``--print-once`` remains independent of
  the selected client. Each ``--llm-mode`` choice exits 0 from
  ``--print-once`` even when the factory inputs would otherwise fail
  (missing API key, missing executable, no mock responses), because
  the ``--print-once`` branch returns before the factory is invoked.
"""
from __future__ import annotations

import io

from brain.invariants import register
from brain.ui.__main__ import main


class _FakeTerminal(io.StringIO):
    """A StringIO that reports itself as a TTY."""

    def isatty(self) -> bool:  # type: ignore[override]
        return True


@register("I-LLMTOG-10", status="REQUIRED")
def check_I_LLMTOG_10_print_once_independent() -> None:
    # Each --llm-mode + --print-once combination must exit 0 without
    # constructing a real backend. Pass an env without
    # ANTHROPIC_API_KEY etc. so a hidden factory call would fail loudly.
    combos = (
        ["--print-once", "--llm-mode", "offline"],
        ["--print-once", "--llm-mode", "mock", "--llm-mock-response", "PRESERVE"],
        ["--print-once", "--llm-mode", "anthropic-api"],
        ["--print-once", "--llm-mode", "claude-cli",
         "--llm-claude-cli-executable", "I-LLMTOG-10-missing"],
        # mock with no responses: also must succeed because --print-once
        # short-circuits before factory checks.
        ["--print-once", "--llm-mode", "mock"],
    )

    for argv in combos:
        stdout = _FakeTerminal()
        stderr = _FakeTerminal()
        rc = main(
            argv=argv,
            stdin=_FakeTerminal(),
            stdout=stdout,
            stderr=stderr,
            env={},
        )
        assert rc == 0, (
            "I-LLMTOG-10 violated: --print-once + " + " ".join(argv[2:])
            + f" exited non-zero (rc={rc}, stderr={stderr.getvalue()!r})"
        )
        rendered = stdout.getvalue()
        assert rendered, (
            "I-LLMTOG-10 violated: --print-once + " + " ".join(argv[2:])
            + " produced no stdout output"
        )
