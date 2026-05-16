"""Phase 3.8 stream UI static audit fixtures.

Drives:

* ``I-UISTRM-10`` (REQUIRED) — Stream interaction introduces no
  language / truth / social / agency / Mode B / model-backed behavior.
* ``I-UISTRM-13`` (STRUCTURAL) — Stream UI static audit rejects
  forbidden side effects.
* ``I-UISTRM-15`` (STRUCTURAL) — Stream command constructors are pure
  and register no callbacks.

The audits are local to this fixture and do not extend
``tools.import_audit``.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register
from brain.ui.commands import OperatorCommand
from brain.ui.command_line import LOCAL_COMMAND_VERBS


_UI_DIR = Path(__file__).resolve().parent.parent
_AUDIT_RUNTIME_FILES: tuple[Path, ...] = (
    _UI_DIR / "commands.py",
    _UI_DIR / "command_line.py",
    _UI_DIR / "session.py",
    _UI_DIR / "snapshot.py",
    _UI_DIR / "render.py",
)
_AUDIT_FIXTURE_FILES: tuple[Path, ...] = tuple(
    sorted((_UI_DIR / "fixtures").glob("stream_*.py"))
)
_ALL_AUDITED_FILES: tuple[Path, ...] = _AUDIT_RUNTIME_FILES + _AUDIT_FIXTURE_FILES


_FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "brain.llm",
)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _is_type_checking_block(node: ast.If) -> bool:
    """Return True when ``node`` is an ``if TYPE_CHECKING:`` guard."""
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
        return True
    return False


def _runtime_imports(tree: ast.Module) -> list[str]:
    """Collect import targets that are evaluated at runtime.

    Skips imports nested inside an ``if TYPE_CHECKING:`` guard since
    those are typing-only and have no runtime effect.
    """
    out: list[str] = []

    def _walk(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, ast.If) and _is_type_checking_block(node):
                # Skip the typing-only branch entirely; the else branch
                # (if any) still counts at runtime.
                _walk(node.orelse)
                continue
            if isinstance(node, ast.Import):
                for alias in node.names:
                    out.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                out.append(("." * node.level) + module)
            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                # Inline imports inside function/class bodies are
                # function-local and run at call time; include them so
                # the audit covers them.
                _walk(node.body)
            elif isinstance(node, ast.If):
                _walk(node.body)
                _walk(node.orelse)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                _walk(node.body)
            elif isinstance(node, ast.Try):
                _walk(node.body)
                for handler in node.handlers:
                    _walk(handler.body)
                _walk(node.orelse)
                _walk(node.finalbody)

    _walk(tree.body)
    return out


def _is_forbidden_import(name: str) -> bool:
    bare = name.lstrip(".")
    if not bare:
        return False
    for prefix in _FORBIDDEN_IMPORT_PREFIXES:
        if bare == prefix or bare.startswith(prefix + "."):
            return True
    if bare == "os.system":
        return True
    return False


def _stream_named_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    out: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            lower = node.name.lower()
            if "stream" in lower:
                out.append(node)
    return out


def _calls_in(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _call_target_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "system",
    "popen",
    "Popen",
    "fork",
    "spawn",
    "tick",
})


# These language / truth / social / agency / Mode B / model-backed
# tokens must not appear inside Phase 3.8 stream-related identifiers.
# The audit is conservative and rejects substring matches.
_FORBIDDEN_STREAM_NAME_TOKENS: tuple[str, ...] = (
    "preserve",
    "damage",
    "mode_b",
    "modeb",
    "agency",
    "freewill",
    "free_will",
    "language",
    "grammar",
    "parser_tree",
    "parse_tree",
    "truth_score",
    "readability",
    "llm_call",
    "model_backed",
)


@register("I-UISTRM-10", status="REQUIRED")
def check_I_UISTRM_10_no_forbidden_surfaces() -> None:
    # OperatorCommand stream additions carry no forbidden tokens.
    stream_kinds = (
        OperatorCommand.STREAM_APPEND,
        OperatorCommand.INSPECT_STREAM_SUMMARY,
        OperatorCommand.INSPECT_STREAM_CANDIDATES,
        OperatorCommand.STREAM_PROMOTE,
    )
    for kind in stream_kinds:
        lower = kind.value.lower()
        for tok in _FORBIDDEN_STREAM_NAME_TOKENS:
            assert tok not in lower, (
                f"I-UISTRM-10 violated: OperatorCommand value {kind.value!r} "
                f"contains forbidden token {tok!r}"
            )

    # Stream verbs carry no forbidden tokens.
    for verb in ("stream", "stream-summary", "stream-candidates", "stream-promote"):
        assert verb in LOCAL_COMMAND_VERBS
        lower = verb.replace("-", "_").lower()
        for tok in _FORBIDDEN_STREAM_NAME_TOKENS:
            assert tok not in lower, (
                f"I-UISTRM-10 violated: verb {verb!r} contains forbidden token"
            )

    # Stream-named functions across the audited files contain no
    # forbidden token in any identifier they reference.
    for path in _ALL_AUDITED_FILES:
        if not path.exists():
            continue
        tree = _parse(path)
        for fn in _stream_named_functions(tree):
            for node in ast.walk(fn):
                if isinstance(node, (ast.Name, ast.Attribute)):
                    name = (
                        node.id
                        if isinstance(node, ast.Name)
                        else node.attr
                    )
                    lower = name.lower()
                    for tok in _FORBIDDEN_STREAM_NAME_TOKENS:
                        assert tok not in lower, (
                            f"I-UISTRM-10 violated: identifier {name!r} in "
                            f"{path.name}::{fn.name} contains forbidden "
                            f"token {tok!r}"
                        )

    # No stream-named function calls tick() directly. The legitimate
    # tick() call inside _dispatch_step is in a non-stream-named function.
    for path in _ALL_AUDITED_FILES:
        if not path.exists():
            continue
        tree = _parse(path)
        for fn in _stream_named_functions(tree):
            for call in _calls_in(fn):
                name = _call_target_name(call)
                if name == "tick":
                    raise AssertionError(
                        f"I-UISTRM-10 violated: stream-named function "
                        f"{path.name}::{fn.name} calls tick() directly"
                    )


@register("I-UISTRM-13", status="STRUCTURAL")
def check_I_UISTRM_13_static_audit_no_forbidden_side_effects() -> None:
    # Forbidden imports across the audited files (runtime only;
    # typing-only imports inside ``if TYPE_CHECKING:`` are exempted).
    for path in _ALL_AUDITED_FILES:
        if not path.exists():
            continue
        tree = _parse(path)
        for name in _runtime_imports(tree):
            assert not _is_forbidden_import(name), (
                f"I-UISTRM-13 violated: {path.name} imports forbidden "
                f"module {name!r}"
            )

    # Stream-named functions contain no obviously-dangerous call
    # targets (eval, exec, subprocess, etc).
    for path in _ALL_AUDITED_FILES:
        if not path.exists():
            continue
        tree = _parse(path)
        for fn in _stream_named_functions(tree):
            for call in _calls_in(fn):
                name = _call_target_name(call)
                if name in _FORBIDDEN_CALL_NAMES:
                    raise AssertionError(
                        f"I-UISTRM-13 violated: stream-named function "
                        f"{path.name}::{fn.name} calls forbidden {name!r}"
                    )


@register("I-UISTRM-15", status="STRUCTURAL")
def check_I_UISTRM_15_pure_constructors_no_callbacks() -> None:
    # No module-level call into atexit/register/append in the audited
    # files. We allow module-level constant assignments, imports, and
    # class/function defs.
    for path in _ALL_AUDITED_FILES:
        if not path.exists():
            continue
        tree = _parse(path)
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                name = _call_target_name(stmt.value)
                # Fixtures legitimately use @register, which is a
                # decorator (FunctionDef-attached), not a module-level
                # call expression. Reject any other module-level call
                # in audited files.
                assert name == "", (
                    f"I-UISTRM-15 violated: module-level call to {name!r} "
                    f"in {path.name}"
                )

    # Stream-named functions do not register atexit hooks or invoke
    # an `atexit.register` style callback.
    for path in _ALL_AUDITED_FILES:
        if not path.exists():
            continue
        tree = _parse(path)
        for fn in _stream_named_functions(tree):
            for node in ast.walk(fn):
                if isinstance(node, ast.Attribute):
                    if node.attr == "register":
                        # The @register decorator on fixture functions
                        # is a Name + Decorator construction handled
                        # outside Attribute; this Attribute branch is a
                        # legitimate attribute access path.
                        parent_chain = node
                        # Reject `atexit.register` and `signal.signal`
                        # patterns specifically.
                        if (
                            isinstance(parent_chain.value, ast.Name)
                            and parent_chain.value.id in ("atexit", "signal")
                        ):
                            raise AssertionError(
                                f"I-UISTRM-15 violated: {path.name}::{fn.name} "
                                f"uses {parent_chain.value.id}.register"
                            )
