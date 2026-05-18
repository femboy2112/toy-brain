"""Phase 3.8b tick-seam fixture.

Drives:

* ``I-LLMTOG-09`` (REQUIRED) — Selected client enters ``tick()``
  through the existing argument. The ``main()`` entrypoint passes the
  ``build_llm_client_from_config(...)`` result through to
  ``run_curses(session, client=..., ...)``; no second client surface
  is constructed and no alternate classification path is invoked.

The fixture performs:

1. A behavioral check against the entrypoint plumbing: substitute a
   no-op ``run_curses`` to observe the client argument and confirm it
   is the factory output.
2. An AST audit that confirms every ``run_curses(`` call in
   ``brain/ui/__main__.py`` uses the factory output (no literal
   ``OfflineStandInClient()`` argument outside the toggle factory).
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path
from types import SimpleNamespace

from brain.invariants import register
from brain.llm.client import CachedClient, CodexCLIClient, MockClient
from brain.ui.__main__ import OfflineStandInClient, main
from brain.ui.llm_runtime import LlmRuntimeMode


def _unwrap_for_test(client):
    """Return the inner transport client, unwrapping ``CachedClient``.

    Phase 3.14 flips the cache default to on for explicit model-backed
    modes, so ``main(["--llm-mode", "codex-cli", ...])`` now produces a
    ``CachedClient`` wrapping a ``CodexCLIClient`` instead of the bare
    ``CodexCLIClient``. The tick-seam contract is "the operator-selected
    transport reaches ``run_curses``"; whether it is wrapped in
    ``CachedClient`` is governed by the separate I-LLMCACHE-02 default
    policy. Unwrap before the type assertion so this fixture's intent
    (mode selection drives transport type) survives the cache default.
    """
    return client._inner if isinstance(client, CachedClient) else client


class _FakeTerminal(io.StringIO):
    """A StringIO that reports itself as a TTY."""

    def isatty(self) -> bool:  # type: ignore[override]
        return True


@register("I-LLMTOG-09", status="REQUIRED")
def check_I_LLMTOG_09_tick_seam() -> None:
    # ---- 1. Behavioral check: substitute a no-op run_curses --------------
    captured: dict = {"session": None, "client": None, "calls": 0}

    def _fake_run_curses(session, *, client=None, percept_factory=None,
                        percept_factory_builder=None) -> None:
        captured["session"] = session
        captured["client"] = client
        captured["calls"] += 1

    def _fake_make_curses_percept_factory(*args, **kwargs):
        return lambda session: None

    # Monkey-patch brain.ui.tui surface only; restore afterward.
    import brain.ui.tui as _tui_mod

    saved_run_curses = _tui_mod.run_curses
    saved_factory_builder = _tui_mod.make_curses_percept_factory
    _tui_mod.run_curses = _fake_run_curses  # type: ignore[assignment]
    _tui_mod.make_curses_percept_factory = (
        _fake_make_curses_percept_factory  # type: ignore[assignment]
    )

    try:
        # OFFLINE path: client should be an OfflineStandInClient.
        stdin = _FakeTerminal()
        stdout = _FakeTerminal()
        stderr = _FakeTerminal()
        rc = main(
            argv=["--llm-mode", "offline"],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env={"TERM": "xterm-256color"},
        )
        assert rc == 0, (
            f"I-LLMTOG-09 violated: main exit code != 0 in OFFLINE path "
            f"(got {rc})"
        )
        assert captured["calls"] == 1, (
            "I-LLMTOG-09 violated: run_curses was not invoked exactly once "
            f"(got {captured['calls']})"
        )
        offline_client = _unwrap_for_test(captured["client"])
        assert isinstance(offline_client, OfflineStandInClient), (
            "I-LLMTOG-09 violated: OFFLINE main did not pass "
            f"OfflineStandInClient to run_curses "
            f"(got {type(offline_client).__name__})"
        )

        # MOCK path: client should be a MockClient with our responses.
        captured["calls"] = 0
        rc = main(
            argv=[
                "--llm-mode", "mock",
                "--llm-mock-response", "PRESERVE",
            ],
            stdin=_FakeTerminal(),
            stdout=_FakeTerminal(),
            stderr=_FakeTerminal(),
            env={"TERM": "xterm-256color"},
        )
        assert rc == 0, (
            f"I-LLMTOG-09 violated: main exit code != 0 in MOCK path "
            f"(got {rc})"
        )
        mock_client = _unwrap_for_test(captured["client"])
        assert isinstance(mock_client, MockClient), (
            "I-LLMTOG-09 violated: MOCK main did not pass MockClient to "
            f"run_curses (got {type(mock_client).__name__})"
        )

        # CODEX_CLI path (Phase 3.11 extension): client should be a
        # CodexCLIClient. Use sys.executable so the local _which()
        # check finds the binary without depending on a real codex
        # CLI; the factory binds command[0] to the resolved path.
        captured["calls"] = 0
        rc = main(
            argv=[
                "--llm-mode", "codex-cli",
                "--llm-codex-cli-executable", sys.executable,
            ],
            stdin=_FakeTerminal(),
            stdout=_FakeTerminal(),
            stderr=_FakeTerminal(),
            env={"TERM": "xterm-256color"},
        )
        assert rc == 0, (
            f"I-LLMTOG-09 violated: main exit code != 0 in CODEX_CLI "
            f"path (got {rc})"
        )
        codex_client = _unwrap_for_test(captured["client"])
        assert isinstance(codex_client, CodexCLIClient), (
            "I-LLMTOG-09 violated: CODEX_CLI main did not pass "
            f"CodexCLIClient to run_curses "
            f"(got {type(codex_client).__name__})"
        )
    finally:
        _tui_mod.run_curses = saved_run_curses  # type: ignore[assignment]
        _tui_mod.make_curses_percept_factory = (
            saved_factory_builder  # type: ignore[assignment]
        )

    # ---- 2. AST audit: run_curses(...) uses the factory result ----------
    # The factory output is bound to a local name `client` in main()
    # (after we removed the unconditional OfflineStandInClient
    # construction). Confirm every run_curses(...) call in
    # brain/ui/__main__.py either uses the named local `client` or has
    # no client argument (none should exist).
    main_path = Path(__file__).resolve().parents[1] / "__main__.py"
    source = main_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(main_path))

    found_calls = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match `run_curses(...)` direct identifier calls.
        if isinstance(func, ast.Name) and func.id == "run_curses":
            found_calls += 1
            # Look for client=<name='client'> in kwargs.
            client_kw = None
            for kw in node.keywords:
                if kw.arg == "client":
                    client_kw = kw
                    break
            assert client_kw is not None, (
                "I-LLMTOG-09 violated: run_curses(...) in "
                f"{main_path.name} omitted the client keyword "
                f"(line {node.lineno})"
            )
            assert isinstance(client_kw.value, ast.Name), (
                "I-LLMTOG-09 violated: run_curses(...) client= argument "
                "is not a bare local name "
                f"(got {ast.dump(client_kw.value)} at line {node.lineno})"
            )
            assert client_kw.value.id == "client", (
                "I-LLMTOG-09 violated: run_curses(...) client= argument "
                f"is not bound to the local `client` "
                f"(got name={client_kw.value.id!r} at line {node.lineno})"
            )

    assert found_calls >= 1, (
        "I-LLMTOG-09 violated: no run_curses(...) call found in "
        f"{main_path.name}"
    )
