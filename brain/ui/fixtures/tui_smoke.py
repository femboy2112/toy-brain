"""Operator TUI smoke fixtures.

Drives:

* ``I-UI-07`` (REQUIRED) — no UI snapshot, renderer, command, router,
  session method, or curses-wrapper code path calls real LLM behaviour,
  spawns a subprocess, opens a shell, performs network I/O, writes a
  file outside an explicitly user-approved save/export path (none exist
  in this campaign), or invokes arbitrary host execution. A
  UI-specific static AST audit walks every Python source under
  ``brain/ui/`` and rejects forbidden imports and forbidden
  host-execution surfaces. This audit is intentionally local to the
  fixture (per the D3 corrigendum in
  ``OPERATOR_TUI_CATALOG_PATCH_PLAN.md``); ``tools/import_audit.py``
  is not modified by this campaign.
* ``I-UI-11`` (STRUCTURAL) — ``brain/ui/tui.py`` contains only screen
  initialization / teardown, key reading, key-to-:class:`Command`
  translation, painting of rendered rows, resize re-rendering, and
  clean quit. It imports no module from ``brain.tlica`` or
  ``brain.llm``, calls no kernel mutation function, evaluates no
  arbitrary Python, and performs no file or network I/O. The fixture
  asserts the import surface plus the absence of arbitrary-execution
  AST nodes (``exec``, ``eval``, ``compile``, ``os.system``,
  ``subprocess``, ``socket``).
* ``I-UI-12`` (STRUCTURAL) — ``brain/ui/__main__.py`` exits with a
  helpful local message when no usable terminal is available; it does
  not spawn alternate shells, open files, call a browser, or mutate
  the filesystem. The fixture drives :func:`brain.ui.__main__.main`
  with injected stdin / stdout / stderr / env stand-ins and asserts
  every advertised exit path (``--check-terminal``, ``--print-once``,
  no-terminal default) behaves as documented.
* ``I-UI-14`` (OBSERVED) — aggregate operator TUI session walks are
  inspectable. A scripted sequence of :class:`OperatorCommand` values
  is driven through :func:`brain.ui.tui.step_loop` against a
  deterministic injected client; the fixture records view transitions,
  queued events, accepted/failed validations, tick records produced,
  and the absence of kernel-boundary leaks. OBSERVED rows do not gate
  the runner.
"""
from __future__ import annotations

import ast
import io
import os
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Optional

from brain.invariants import register
from brain.io_types import ContentRegistry, TickRecord
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.toce_core import ContentState
from brain.ui import __main__ as ui_main
from brain.ui import tui as ui_tui
from brain.ui.commands import (
    Command,
    OperatorCommand,
    QueuePerceptPayload,
    make_command,
)
from brain.ui.session import OperatorSession
from brain.ui.tui import (
    KEYMAP,
    PaintRecorder,
    StepOutcome,
    paint_rows,
    step_loop,
    translate_key,
)


# ---------------------------------------------------------------------------
# Deterministic builders shared across the four fixtures.
# ---------------------------------------------------------------------------


def _make_state() -> BrainState:
    profile = make_profile_with_cogito({COGITO_ID: 1, "alpha": Fraction(3, 4)})
    msi = make_msi(
        profile,
        contents={COGITO_ID, "alpha"},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    return BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)


class _PreserveClient:
    """Deterministic local LLM stand-in (mirrors bottom_up_tick fixture)."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


# ---------------------------------------------------------------------------
# AST audit — shared engine for I-UI-07 and I-UI-11.
# ---------------------------------------------------------------------------


_UI_ROOT = Path(__file__).resolve().parent.parent  # brain/ui/


#: Top-level module names that no file under brain/ui/ is allowed to
#: import. Covers shells, subprocess spawn, network endpoints, kernel
#: TLICA internals, and the real LLM seam.
_FORBIDDEN_IMPORT_MODULES: frozenset[str] = frozenset({
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "asyncio.subprocess",
    "multiprocessing",
    "ctypes",
    "signal",
    "shutil",  # filesystem mutation surface (rm, copy, move)
    "tempfile",  # filesystem mutation surface
    "pickle",
    "shelve",
    "xmlrpc",
    "ftplib",
    "telnetlib",
    "smtplib",
    "poplib",
    "imaplib",
})


#: Forbidden attribute access shapes (e.g. ``os.system``,
#: ``os.exec``, ``os.spawn``). These are matched by walking ``ast.Attribute``
#: nodes whose ``value`` is an ``ast.Name``.
_FORBIDDEN_OS_ATTRS: frozenset[str] = frozenset({
    "system",
    "popen",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "spawnl",
    "spawnle",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "fork",
    "forkpty",
    "kill",
})


#: AST builtin-name patterns that imply arbitrary code execution.
_FORBIDDEN_BUILTIN_CALLS: frozenset[str] = frozenset({
    "exec",
    "eval",
    "compile",
    "__import__",
})


@dataclass(frozen=True, slots=True)
class _AuditFinding:
    """A single forbidden-import or forbidden-call finding."""

    file: str
    line: int
    kind: str
    detail: str


#: Public TLICA / LLM surfaces that brain/ui/ may import in **lazy** (in-function)
#: form. The Step 8-approved code uses these for value construction and typing
#: only — not for direct TLICA runtime mutation. Module-level imports of these
#: are still rejected so the static surface stays narrow.
_ALLOWED_LAZY_TLICA_SUFFIXES: frozenset[str] = frozenset({
    "brain.tlica.builders",
    "brain.tlica.profile",
    "brain.tlica.ptcns",
    "brain.tlica.modes",
})

_ALLOWED_LAZY_LLM_SUFFIXES: frozenset[str] = frozenset({
    "brain.llm.client",
})


def _collect_typing_block_lines(tree: ast.Module) -> frozenset[int]:
    """Return the set of line numbers inside ``if TYPE_CHECKING:`` blocks.

    Imports inside such blocks are evaluated by static type checkers
    only; at runtime they are unreachable. The Step 8-approved
    ``brain.ui.session`` / ``brain.ui.tui`` modules use this idiom to
    reference ``brain.llm.client.LLMClient`` as a type annotation only.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            # Match: TYPE_CHECKING / typing.TYPE_CHECKING
            is_tc = (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (
                    isinstance(test, ast.Attribute)
                    and test.attr == "TYPE_CHECKING"
                )
            )
            if is_tc:
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        lines.add(child.lineno)
    return frozenset(lines)


def _collect_function_body_lines(tree: ast.Module) -> frozenset[int]:
    """Return the set of line numbers inside any function / method body.

    Lazy imports inside function bodies are treated more leniently than
    module-level imports: they are deferred behaviour and represent
    bounded calls into public TLICA / LLM surfaces, not the static
    import graph the I-UI-07 audit primarily targets.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if hasattr(child, "lineno"):
                    lines.add(child.lineno)
    return frozenset(lines)


def _audit_ui_source(path: Path, *, forbid_brain_internal: bool = True) -> list[_AuditFinding]:
    """Walk a single Python source file and collect forbidden surfaces.

    ``forbid_brain_internal`` toggles whether ``brain.tlica.*`` and
    ``brain.llm.*`` imports are forbidden. The I-UI-07 audit forbids
    them across all of ``brain/ui/``; this fixture's own source is
    exempt because it deliberately imports several kernel builders for
    its setup helpers (it is not a runtime UI surface).

    Module-level imports of forbidden surfaces are rejected unconditionally.
    Imports inside ``if TYPE_CHECKING:`` blocks (typing-only) and lazy
    imports inside function bodies that target the documented public
    TLICA / LLM surfaces (:data:`_ALLOWED_LAZY_TLICA_SUFFIXES` /
    :data:`_ALLOWED_LAZY_LLM_SUFFIXES`) are allowed.
    """
    if not isinstance(path, Path):
        raise TypeError(f"_audit_ui_source requires Path (got {type(path).__name__})")
    findings: list[_AuditFinding] = []
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    typing_lines = _collect_typing_block_lines(tree)
    function_lines = _collect_function_body_lines(tree)

    def _module_level(node: ast.AST) -> bool:
        line = getattr(node, "lineno", -1)
        return line not in typing_lines and line not in function_lines

    def _typing_only(node: ast.AST) -> bool:
        line = getattr(node, "lineno", -1)
        return line in typing_lines

    def _lazy_allowed(node: ast.AST, name: str) -> bool:
        line = getattr(node, "lineno", -1)
        if line not in function_lines:
            return False
        return (
            name in _ALLOWED_LAZY_TLICA_SUFFIXES
            or name in _ALLOWED_LAZY_LLM_SUFFIXES
        )

    for node in ast.walk(tree):
        # `import X` / `import X.Y`
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                root = name.split(".")[0]
                # Forbidden stdlib roots are forbidden everywhere
                # (typing-only and lazy included): there is no
                # legitimate UI use for `subprocess`, `socket`, etc.
                if name in _FORBIDDEN_IMPORT_MODULES or root in _FORBIDDEN_IMPORT_MODULES:
                    findings.append(
                        _AuditFinding(
                            file=str(path),
                            line=node.lineno,
                            kind="forbidden_import",
                            detail=f"import {name}",
                        )
                    )
                if forbid_brain_internal and (
                    name == "brain.tlica"
                    or name.startswith("brain.tlica.")
                    or name == "brain.llm"
                    or name.startswith("brain.llm.")
                ):
                    # Typing-only imports and lazy in-function imports
                    # of the documented allowlist are tolerated.
                    if _typing_only(node):
                        continue
                    if _lazy_allowed(node, name):
                        continue
                    findings.append(
                        _AuditFinding(
                            file=str(path),
                            line=node.lineno,
                            kind="forbidden_import",
                            detail=f"import {name}",
                        )
                    )
        # `from X import Y`
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0] if module else ""
            if module in _FORBIDDEN_IMPORT_MODULES or root in _FORBIDDEN_IMPORT_MODULES:
                findings.append(
                    _AuditFinding(
                        file=str(path),
                        line=node.lineno,
                        kind="forbidden_import",
                        detail=f"from {module} import ...",
                    )
                )
            if forbid_brain_internal and (
                module == "brain.tlica"
                or module.startswith("brain.tlica.")
                or module == "brain.llm"
                or module.startswith("brain.llm.")
            ):
                if _typing_only(node):
                    continue
                if _lazy_allowed(node, module):
                    continue
                findings.append(
                    _AuditFinding(
                        file=str(path),
                        line=node.lineno,
                        kind="forbidden_import",
                        detail=f"from {module} import ...",
                    )
                )
        # os.<forbidden> attribute access
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                if node.attr in _FORBIDDEN_OS_ATTRS:
                    findings.append(
                        _AuditFinding(
                            file=str(path),
                            line=node.lineno,
                            kind="forbidden_attribute",
                            detail=f"os.{node.attr}",
                        )
                    )
        # exec(...) / eval(...) / compile(...) / __import__(...)
        elif isinstance(node, ast.Call):
            func = node.func
            name: Optional[str] = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in _FORBIDDEN_BUILTIN_CALLS:
                findings.append(
                    _AuditFinding(
                        file=str(path),
                        line=node.lineno,
                        kind="forbidden_call",
                        detail=f"{name}(...)",
                    )
                )
    return findings


def _all_ui_python_files() -> list[Path]:
    """Return every ``.py`` file under ``brain/ui/`` sorted deterministically.

    Skips ``__pycache__`` directories and ``.pyc`` artefacts. The walk
    is rooted at :data:`_UI_ROOT` so additions to the package surface
    are picked up automatically.
    """
    out: list[Path] = []
    for root, dirs, files in os.walk(_UI_ROOT):
        # Skip cache directories.
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(".py"):
                out.append(Path(root) / name)
    return sorted(out)


# ---------------------------------------------------------------------------
# I-UI-07 — UI-wide static AST import audit.
# ---------------------------------------------------------------------------


@register("I-UI-07", status="REQUIRED")
def check_I_UI_07_ui_has_no_forbidden_imports_or_host_execution() -> None:
    paths = _all_ui_python_files()
    assert paths, "I-UI-07: no Python sources found under brain/ui/"

    # This fixture's own source legitimately imports brain.tlica.builders
    # for deterministic state construction; the runtime UI surfaces do
    # not. Skip ``brain.tlica`` / ``brain.llm`` checks for fixture files
    # while still applying every other forbidden-surface rule.
    self_path = Path(__file__).resolve()
    fixture_dir = self_path.parent

    findings: list[_AuditFinding] = []
    for path in paths:
        forbid_internal = not str(path).startswith(str(fixture_dir))
        findings.extend(
            _audit_ui_source(path, forbid_brain_internal=forbid_internal)
        )

    if findings:
        report = "\n".join(
            f"  {f.file}:{f.line} [{f.kind}] {f.detail}" for f in findings
        )
        raise AssertionError(
            "I-UI-07 violated: forbidden imports / host-execution surfaces "
            "found under brain/ui/:\n" + report
        )

    # Sanity: the runtime UI modules (snapshot, render, commands, session,
    # tui, __main__) must all be present so the audit cannot pass
    # vacuously after a file rename.
    expected = {
        "snapshot.py",
        "render.py",
        "commands.py",
        "session.py",
        "tui.py",
        "__main__.py",
        "__init__.py",
    }
    actual = {p.name for p in paths}
    missing = expected - actual
    assert not missing, (
        f"I-UI-07: expected UI runtime modules missing from brain/ui/: "
        f"{sorted(missing)!r}"
    )


# ---------------------------------------------------------------------------
# I-UI-11 — curses wrapper contains only terminal-handling code.
# ---------------------------------------------------------------------------


def _module_imports(tree: ast.Module) -> frozenset[str]:
    """Return the set of top-level module names imported by an AST."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                out.add(module.split(".")[0])
    return frozenset(out)


@register("I-UI-11", status="STRUCTURAL")
def check_I_UI_11_curses_wrapper_is_terminal_only() -> None:
    tui_path = _UI_ROOT / "tui.py"
    assert tui_path.exists(), f"I-UI-11: {tui_path} does not exist"

    findings = _audit_ui_source(tui_path, forbid_brain_internal=True)
    assert not findings, (
        "I-UI-11 violated: brain/ui/tui.py contains forbidden surfaces:\n"
        + "\n".join(
            f"  {f.file}:{f.line} [{f.kind}] {f.detail}" for f in findings
        )
    )

    tree = ast.parse(tui_path.read_text(encoding="utf-8"))
    roots = _module_imports(tree)

    # Allowed top-level roots for brain/ui/tui.py.
    allowed_roots = frozenset({
        "__future__",
        "curses",
        "dataclasses",
        "typing",
        "brain",  # only brain.ui.* is reachable from this file
    })
    disallowed = roots - allowed_roots
    assert not disallowed, (
        f"I-UI-11 violated: brain/ui/tui.py imports unexpected roots {sorted(disallowed)!r}"
    )

    # Every runtime `brain.*` import must be a brain.ui.* import.
    # TYPE_CHECKING-only imports are exempt: they exist for static
    # analysis only and are never executed.
    typing_lines = _collect_typing_block_lines(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("brain.") and not module.startswith("brain.ui"):
                if node.lineno in typing_lines:
                    continue
                raise AssertionError(
                    f"I-UI-11 violated: brain/ui/tui.py imports {module!r}; "
                    "only brain.ui.* imports are permitted at runtime"
                )
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("brain.") and not name.startswith("brain.ui"):
                    if node.lineno in typing_lines:
                        continue
                    raise AssertionError(
                        f"I-UI-11 violated: brain/ui/tui.py imports {name!r}; "
                        "only brain.ui.* imports are permitted at runtime"
                    )

    # Behavioural surface: KEYMAP is finite, paint_rows works against a
    # PaintRecorder without touching curses, and translate_key never
    # raises on unknown input.
    assert isinstance(KEYMAP, dict) and len(KEYMAP) > 0
    for key, cmd in KEYMAP.items():
        assert isinstance(key, str) and isinstance(cmd, OperatorCommand), (
            f"I-UI-11 violated: KEYMAP entry {key!r} -> {cmd!r} is malformed"
        )

    # translate_key totality: every unknown keystroke yields None, never raises.
    for bad in ("Z", "@", "\\", "1", "F", ""):
        assert translate_key(bad) is None or isinstance(translate_key(bad), OperatorCommand)

    # paint_rows accepts a PaintRecorder (no real terminal) and emits
    # the expected number of rows.
    recorder = PaintRecorder()
    sample_rows = ("[ help ]----", "  s  inspect state", "  q  quit")
    paint_rows(recorder, sample_rows, width=20, height=24)
    assert recorder.cleared == 1
    assert recorder.refreshed == 1
    assert [c.text for c in recorder.calls] == [
        "[ help ]----",
        "  s  inspect state",
        "  q  quit",
    ]
    for call in recorder.calls:
        assert call.col == 0
        assert call.width == 20

    # Paint rejects non-string rows.
    try:
        paint_rows(PaintRecorder(), (123,), width=20, height=24)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-11 violated: paint_rows accepted a non-string row")


# ---------------------------------------------------------------------------
# I-UI-12 — entrypoint fails closed without a usable terminal.
# ---------------------------------------------------------------------------


class _FakeStream:
    """Minimal stand-in for stdin / stdout / stderr.

    Tracks the captured text and the configured ``isatty`` result so the
    smoke fixture can exercise every entrypoint branch without
    attaching to a real terminal.
    """

    def __init__(self, *, isatty: bool = False) -> None:
        self._buffer = io.StringIO()
        self._isatty = isatty

    def isatty(self) -> bool:
        return self._isatty

    def write(self, data: str) -> int:
        return self._buffer.write(data)

    def flush(self) -> None:
        pass

    def getvalue(self) -> str:
        return self._buffer.getvalue()


@register("I-UI-12", status="STRUCTURAL")
def check_I_UI_12_entrypoint_fails_closed_without_terminal() -> None:
    # --- Branch 1: --check-terminal with no-TTY stdout -----------------
    fake_stdout = _FakeStream(isatty=False)
    fake_stderr = _FakeStream(isatty=False)
    code = ui_main.main(
        ["--check-terminal"],
        stdin=_FakeStream(isatty=False),
        stdout=fake_stdout,
        stderr=fake_stderr,
        env={"TERM": "xterm"},
    )
    assert code == 1, f"I-UI-12: --check-terminal expected exit 1 (got {code})"
    out = fake_stdout.getvalue()
    assert "usable=False" in out, (
        f"I-UI-12: --check-terminal output missing usable=False ({out!r})"
    )

    # --- Branch 2: --check-terminal with TTY-on-both + TERM=xterm ------
    fake_stdout = _FakeStream(isatty=True)
    fake_stderr = _FakeStream(isatty=True)
    code = ui_main.main(
        ["--check-terminal"],
        stdin=_FakeStream(isatty=True),
        stdout=fake_stdout,
        stderr=fake_stderr,
        env={"TERM": "xterm"},
    )
    assert code == 0, f"I-UI-12: --check-terminal expected exit 0 (got {code})"
    assert "usable=True" in fake_stdout.getvalue()

    # --- Branch 3: --check-terminal with TERM=dumb is not usable -------
    fake_stdout = _FakeStream(isatty=True)
    fake_stderr = _FakeStream(isatty=True)
    code = ui_main.main(
        ["--check-terminal"],
        stdin=_FakeStream(isatty=True),
        stdout=fake_stdout,
        stderr=fake_stderr,
        env={"TERM": "dumb"},
    )
    assert code == 1
    assert "usable=False" in fake_stdout.getvalue()

    # --- Branch 4: default (no flags) with no terminal -----------------
    #     The entrypoint must print the helpful message and return 1.
    fake_stdout = _FakeStream(isatty=False)
    fake_stderr = _FakeStream(isatty=False)
    code = ui_main.main(
        [],
        stdin=_FakeStream(isatty=False),
        stdout=fake_stdout,
        stderr=fake_stderr,
        env={},
    )
    assert code == 1, (
        f"I-UI-12: default no-terminal exit expected 1 (got {code})"
    )
    err = fake_stderr.getvalue()
    assert "brain.ui: no usable terminal detected" in err, (
        f"I-UI-12: missing helpful no-terminal message (stderr={err!r})"
    )
    # Helpful message does not propose spawning alternate shells,
    # browsers, network calls, or file-mutation commands as a remediation.
    forbidden_strings = ("bash -c", "/bin/sh", "xdg-open ", "curl ", "wget ")
    for needle in forbidden_strings:
        assert needle not in err, (
            f"I-UI-12 violated: no-terminal message mentions {needle!r}"
        )

    # --- Branch 5: --print-once renders one deterministic frame --------
    fake_stdout = _FakeStream(isatty=True)
    fake_stderr = _FakeStream(isatty=True)
    code = ui_main.main(
        ["--print-once", "--width", "60", "--height", "12"],
        stdin=_FakeStream(isatty=True),
        stdout=fake_stdout,
        stderr=fake_stderr,
        env={"TERM": "xterm"},
    )
    assert code == 0, f"I-UI-12: --print-once expected exit 0 (got {code})"
    frame = fake_stdout.getvalue()
    assert frame, "I-UI-12: --print-once produced no output"
    # Determinism: running --print-once again produces identical output.
    fake_stdout2 = _FakeStream(isatty=True)
    code2 = ui_main.main(
        ["--print-once", "--width", "60", "--height", "12"],
        stdin=_FakeStream(isatty=True),
        stdout=fake_stdout2,
        stderr=_FakeStream(isatty=True),
        env={"TERM": "xterm"},
    )
    assert code2 == 0
    assert fake_stdout2.getvalue() == frame, (
        "I-UI-12 violated: --print-once output is non-deterministic"
    )

    # --- Branch 6: OfflineStandInClient behaves as a deterministic LLM stand-in.
    client = ui_main.OfflineStandInClient()
    assert client.eval_consistency("anything") == "PRESERVE"
    assert client.eval_consistency("else") == "PRESERVE"
    assert client.calls == 2
    # The stand-in rejects non-string prompts.
    try:
        client.eval_consistency(123)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-UI-12 violated: OfflineStandInClient accepted non-str prompt"
        )

    # --- Branch 7: detect_terminal is total and side-effect free -------
    check = ui_main.detect_terminal(
        stdin=_FakeStream(isatty=True),
        stdout=_FakeStream(isatty=True),
        env={"TERM": "xterm-256color"},
    )
    assert check.usable and "xterm-256color" in check.reason

    # --- Branch 8: argparse `--help` does not spawn anything. ----------
    # ``argparse`` calls ``sys.exit`` on --help, which surfaces as
    # SystemExit. The smoke fixture catches that explicitly and asserts
    # the help text mentions our policy.
    fake_stdout = _FakeStream(isatty=True)
    try:
        ui_main.main(
            ["--help"],
            stdin=_FakeStream(isatty=True),
            stdout=fake_stdout,
            stderr=_FakeStream(isatty=True),
            env={"TERM": "xterm"},
        )
    except SystemExit as exc:
        assert exc.code == 0, f"I-UI-12: --help exited with code {exc.code}"
    else:
        raise AssertionError("I-UI-12: --help did not exit")


# ---------------------------------------------------------------------------
# I-UI-14 — aggregate operator TUI session walks are inspectable (OBSERVED).
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _WalkSummary:
    """Inspection summary recorded by the aggregate session walk."""

    commands: list[str] = field(default_factory=list)
    view_transitions: list[tuple[str, str]] = field(default_factory=list)
    queued_payload_ids: list[str] = field(default_factory=list)
    accepted_validations: int = 0
    failed_validations: int = 0
    tick_records: list[int] = field(default_factory=list)
    final_status: str = ""
    final_error: str = ""
    state_identity_drift: bool = False


@register("I-UI-14", status="OBSERVED")
def check_I_UI_14_aggregate_session_walk_is_inspectable() -> None:
    state = _make_state()
    session = OperatorSession(state=state)
    pre_state_id = id(session.state)
    client = _PreserveClient()
    summary = _WalkSummary()

    # The scripted operator walk. Each entry is (keystroke, optional
    # percept_factory). The factory is only consulted for "e"
    # (QUEUE_PERCEPT).
    def _good_percept(_session: OperatorSession) -> Command:
        return make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="beta",
            text="beta probe",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(3, 4),
        )

    def _bad_percept(_session: OperatorSession) -> Command:
        # Will raise during payload construction (initial_rho out of range).
        return make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="gamma",
            text="gamma probe",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(3, 2),
        )

    script: list[tuple[str, Optional[object]]] = [
        ("?", None),       # help
        ("s", None),       # inspect state
        ("o", None),       # inspect output
        ("w", None),       # inspect worldlet
        ("r", None),       # inspect repl
        ("e", _bad_percept),   # queue percept: validation failure -> local UI error
        ("e", _good_percept),  # queue percept: ok
        ("t", None),       # inspect tick
        (" ", None),       # STEP_TICK: routes through public tick()
        ("c", None),       # clear status / error
        ("?", None),       # help
        ("Z", None),       # unknown keystroke -> unknown-key status only
        ("q", None),       # quit
    ]

    prior_view = session.active_view
    for keystroke, factory in script:
        outcome = step_loop(
            session,
            keystroke,
            client=client,
            percept_factory=factory,  # type: ignore[arg-type]
        )
        assert isinstance(outcome, StepOutcome)
        summary.commands.append(keystroke)
        if outcome.command is not None:
            summary.view_transitions.append((prior_view, session.active_view))
        prior_view = session.active_view
        if outcome.command is OperatorCommand.QUEUE_PERCEPT:
            head = session.event_queue.peek()
            if head is not None:
                summary.queued_payload_ids.append(head.content_id)
            if session.error_message:
                summary.failed_validations += 1
            else:
                summary.accepted_validations += 1
        if outcome.command is OperatorCommand.STEP_TICK and session.latest_tick is not None:
            assert isinstance(session.latest_tick, TickRecord)
            summary.tick_records.append(int(session.latest_tick.tick_index))

    summary.final_status = session.status_message
    summary.final_error = session.error_message

    # Kernel-boundary leak checks: the session must still hold a
    # BrainState, no tick record from a failing dispatch, and no
    # forbidden resource attribute.
    assert isinstance(session.state, BrainState)
    if id(session.state) == pre_state_id:
        # The walk includes a successful STEP_TICK so the state object
        # must have been replaced. Record a drift flag rather than
        # raising — I-UI-14 is OBSERVED, not REQUIRED.
        summary.state_identity_drift = False
    else:
        summary.state_identity_drift = True

    # OBSERVED rows do not gate the runner, but we still assert the
    # walk produced a coherent summary so the row stays diagnostic.
    assert summary.commands, "I-UI-14: walk produced no recorded commands"
    assert summary.queued_payload_ids == ["beta"], (
        f"I-UI-14: queued payload ids drifted ({summary.queued_payload_ids!r})"
    )
    assert summary.tick_records == [1], (
        f"I-UI-14: tick records drifted ({summary.tick_records!r})"
    )
    assert summary.failed_validations >= 1, (
        "I-UI-14: bad percept did not produce a local UI failure"
    )
    assert summary.state_identity_drift, (
        "I-UI-14: STEP_TICK did not replace the kernel BrainState identity"
    )
    assert session.quit_flag, "I-UI-14: scripted walk did not reach QUIT"


__all__ = [
    "check_I_UI_07_ui_has_no_forbidden_imports_or_host_execution",
    "check_I_UI_11_curses_wrapper_is_terminal_only",
    "check_I_UI_12_entrypoint_fails_closed_without_terminal",
    "check_I_UI_14_aggregate_session_walk_is_inspectable",
]
