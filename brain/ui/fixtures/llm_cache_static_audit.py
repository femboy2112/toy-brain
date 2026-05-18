"""Phase 3.14 / 3.15 LLM cache static-audit fixture.

Drives:

* ``I-LLMCACHE-17`` (REQUIRED) — Static AST audit over
  ``brain/llm/ptcns_backed.py`` rejects hidden model-call / network /
  subprocess / filesystem-mutation / raw-prompt-leakage / disallowed
  imports in the new L2 cache code path.
* ``I-LLMCACHE-18`` (REQUIRED) — No cognitive / claim-boundary drift:
  the term "semantic" in the new cache code refers to cache identity
  only; the inherited
  :data:`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
  tuple is not present in the new code's source.
* ``I-LLMCACHE-19`` (STRUCTURAL) — Cache dependency direction is
  one-way: ``brain.llm.ptcns_backed`` does not import ``brain.ui.*``
  or ``brain.tick``.
* ``I-LLMCACHE-26`` (STRUCTURAL) — Phase 3.15 L1 hygiene static audit
  over ``brain/llm/client.py``: rejects forbidden imports, eval/exec
  calls, and confirms the new ``llm.cache_skip`` event payload uses
  only ``cache_key_prefix`` and ``reason`` as payload keys. Distinct
  from the existing L2 audit by target path and function name.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


_PTCNS_BACKED_PATH = (
    Path(__file__).resolve().parents[2] / "llm" / "ptcns_backed.py"
)


_ALLOWED_IMPORT_NAMES: frozenset[str] = frozenset({
    "__future__",
    "hashlib",
    "json",
    "time",
    "collections.abc",
    "pathlib",
    "types",
    "brain.llm.client",
    "brain.llm.parse",
    "brain.llm.prompts",
    "brain.tlica.msi",
    "brain.tlica.profile",
    "brain.tlica.ptcns",
    "brain.trace",
})


_FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "brain.ui",
    "brain.tick",
    "brain.development",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "sqlite3",
    "tempfile",
    "shutil",
    "atexit",
    "threading",
    "asyncio",
    "signal",
)


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "tick",
    "save_session",
    "load_session",
    "maybe_autosave_after_mutation",
})


_FORBIDDEN_CALL_PREFIXES: tuple[str, ...] = (
    "subprocess.",
    "socket.",
    "urllib.",
    "http.",
    "sqlite3.",
    "shutil.",
    "tempfile.",
    "atexit.",
    "threading.",
    "asyncio.",
    "signal.",
    "importlib.",
    "os.system",
    "os.popen",
    "os.exec",
    "os.spawn",
)


def _parse() -> tuple[ast.Module, str]:
    source = _PTCNS_BACKED_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_PTCNS_BACKED_PATH)), source


def _import_targets(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            out.append(node.module)
    return out


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


@register("I-LLMCACHE-17", status="REQUIRED")
def check_I_LLMCACHE_17_static_audit() -> None:
    assert _PTCNS_BACKED_PATH.exists(), (
        "I-LLMCACHE-17 violated: ptcns_backed.py not found at "
        f"{_PTCNS_BACKED_PATH}"
    )
    tree, source = _parse()

    # 1. Import allowlist.
    targets = _import_targets(tree)
    for name in targets:
        for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
            if name == forbidden or name.startswith(forbidden + "."):
                raise AssertionError(
                    "I-LLMCACHE-17 violated: forbidden import "
                    f"{name!r} in ptcns_backed.py"
                )
        if name not in _ALLOWED_IMPORT_NAMES:
            raise AssertionError(
                "I-LLMCACHE-17 violated: unrecognized import "
                f"{name!r} in ptcns_backed.py"
            )

    # 2. Forbidden call names / prefixes.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in _FORBIDDEN_CALL_NAMES:
                raise AssertionError(
                    "I-LLMCACHE-17 violated: forbidden call "
                    f"{name!r} at line {node.lineno}"
                )
            for prefix in _FORBIDDEN_CALL_PREFIXES:
                if name.startswith(prefix):
                    raise AssertionError(
                        "I-LLMCACHE-17 violated: forbidden call "
                        f"{name!r} at line {node.lineno}"
                    )

    # 3. No raw-prompt persistence: no module-level write of any key
    # named "prompt" / "response" / "raw" / "error" / "headers" / "trace"
    # into a path under brain/.llm_cache/eval_v1/. The L2 entry schema
    # is exactly {"key_prefix", "parsed"} (see I-LLMCACHE-12). We do a
    # narrow text-form audit: the literal string "\"prompt\"" must not
    # appear next to a json.dumps call in the new L2 write code.
    forbidden_payload_pairs = (
        '"prompt"',
        '"response"',
        '"raw"',
        '"error"',
        '"trace"',
        '"headers"',
    )
    # Look at the body of the _l2_store function for forbidden keys.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_l2_store":
            body_src = ast.unparse(node)
            for needle in forbidden_payload_pairs:
                assert needle not in body_src, (
                    "I-LLMCACHE-17 violated: _l2_store body contains "
                    f"forbidden payload key text {needle!r}"
                )


_PHASE3_14_L2_SYMBOLS: frozenset[str] = frozenset({
    "SEMANTIC_CACHE_SCHEMA_VERSION",
    "SEMANTIC_CACHE_MAX_ENTRIES",
    "SEMANTIC_CACHE_DIR",
    "_derive_l2_metadata",
    "_canonical_l2_key",
    "_VALID_PARSED_NAMES",
    "_derive_existing_msi_context",
    "_l2_lookup",
    "_l2_store",
})


def _phase3_14_l2_source(tree: ast.Module, source: str) -> str:
    """Return the source text of the new Phase 3.14 L2 nodes only.

    Existing pre-Phase-3.14 docstrings on ``LLMBackedPtCns`` legitimately
    reference ``ConsistencyEval.PRESERVE`` / ``DAMAGE`` (the enum
    members defined by the v0.2 PtCns API); they are out of scope for
    the Phase 3.14 claim-boundary audit, which polices the *new* L2
    cache code path only.
    """
    parts: list[str] = []
    for node in tree.body:
        name: str | None = None
        if isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                name = node.target.id
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
        if name in _PHASE3_14_L2_SYMBOLS:
            parts.append(ast.get_source_segment(source, node) or "")
    # Also include the methods on LLMBackedPtCns that were added or
    # extended by Phase 3.14 (the L2 helper methods); existing methods
    # like eval(...) carry pre-existing PRESERVE / DAMAGE references in
    # their docstrings and are out of scope for I-LLMCACHE-18.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "LLMBackedPtCns":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name in _PHASE3_14_L2_SYMBOLS:
                        parts.append(ast.get_source_segment(source, item) or "")
    return "\n".join(parts)


@register("I-LLMCACHE-18", status="REQUIRED")
def check_I_LLMCACHE_18_no_claim_boundary_drift() -> None:
    tree, source = _parse()
    new_source = _phase3_14_l2_source(tree, source)
    assert new_source, (
        "I-LLMCACHE-18 violated: could not locate Phase 3.14 L2 cache "
        "symbols in ptcns_backed.py source"
    )
    lowered_lines = new_source.lower().splitlines()
    for idx, line in enumerate(lowered_lines, start=1):
        for term in _FORBIDDEN_NON_CLAIM_TERMS:
            assert term not in line, (
                "I-LLMCACHE-18 violated: forbidden term "
                f"{term!r} in new Phase 3.14 L2 code at relative line "
                f"{idx}: {line.strip()!r}"
            )


@register("I-LLMCACHE-19", status="STRUCTURAL")
def check_I_LLMCACHE_19_dependency_direction() -> None:
    # brain/llm/* must not import brain.ui.* or brain.tick.
    llm_root = _PTCNS_BACKED_PATH.parent
    for module_path in sorted(llm_root.glob("*.py")):
        if module_path.name.startswith("__"):
            continue
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(module_path))
        for name in _import_targets(tree):
            assert not (name == "brain.ui" or name.startswith("brain.ui.")), (
                "I-LLMCACHE-19 violated: "
                f"{module_path.relative_to(llm_root.parent.parent)} "
                f"imports {name!r}"
            )
            assert name != "brain.tick", (
                "I-LLMCACHE-19 violated: "
                f"{module_path.relative_to(llm_root.parent.parent)} "
                f"imports {name!r}"
            )


# Phase 3.15 L1 hygiene static audit. Scope: brain/llm/client.py only.
# Distinct from the L2 audit (I-LLMCACHE-17) by target path and label.
_CLIENT_PATH = _PTCNS_BACKED_PATH.parent / "client.py"


_CLIENT_ALLOWED_IMPORT_NAMES: frozenset[str] = frozenset({
    "__future__",
    "hashlib",
    "json",
    "os",
    "shutil",
    "subprocess",
    "time",
    "urllib.error",
    "urllib.request",
    "dataclasses",
    "pathlib",
    "typing",
    "brain.trace",
})


_CLIENT_FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "brain.ui",
    "brain.tick",
    "brain.development",
    "socket",
    "http",
    "requests",
    "sqlite3",
    "tempfile",
    "atexit",
    "threading",
    "asyncio",
    "signal",
)


_CLIENT_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "tick",
    "save_session",
    "load_session",
    "maybe_autosave_after_mutation",
})


@register("I-LLMCACHE-26", status="STRUCTURAL")
def check_I_LLMCACHE_26_l1_hygiene_static_audit() -> None:
    assert _CLIENT_PATH.exists(), (
        "I-LLMCACHE-26 violated: client.py not found at "
        f"{_CLIENT_PATH}"
    )
    source = _CLIENT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_CLIENT_PATH))

    # 1. Import allowlist: client.py legitimately imports stdlib
    # subprocess + urllib for the CLI/HTTP backends, but must not
    # import brain.ui / brain.tick / brain.development or net/IPC
    # surfaces the L1 hygiene policy does not need.
    for name in _import_targets(tree):
        for forbidden in _CLIENT_FORBIDDEN_IMPORT_PREFIXES:
            if name == forbidden or name.startswith(forbidden + "."):
                raise AssertionError(
                    "I-LLMCACHE-26 violated: forbidden import "
                    f"{name!r} in client.py"
                )
        assert name in _CLIENT_ALLOWED_IMPORT_NAMES, (
            "I-LLMCACHE-26 violated: unrecognized import "
            f"{name!r} in client.py (extend the allowlist if "
            "intentional)"
        )

    # 2. Forbidden calls.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in _CLIENT_FORBIDDEN_CALL_NAMES:
                raise AssertionError(
                    "I-LLMCACHE-26 violated: forbidden call "
                    f"{name!r} at line {node.lineno}"
                )

    # 3. The new llm.cache_skip event payload must use only
    # ``cache_key_prefix`` and ``reason``. We locate the
    # ``_tracer.record("llm.cache_skip", {...})`` call inside the
    # CachedClient class and inspect the dict literal keys.
    found_skip = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "record":
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Constant):
            continue
        if first.value != "llm.cache_skip":
            continue
        # Second positional arg must be a dict literal with keys
        # exactly {"cache_key_prefix", "reason"}.
        assert len(node.args) >= 2, (
            "I-LLMCACHE-26 violated: llm.cache_skip record(...) call "
            "missing payload dict argument"
        )
        payload = node.args[1]
        assert isinstance(payload, ast.Dict), (
            "I-LLMCACHE-26 violated: llm.cache_skip payload is not "
            "a dict literal"
        )
        keys: set[str] = set()
        for key_node in payload.keys:
            assert isinstance(key_node, ast.Constant) and isinstance(
                key_node.value, str
            ), (
                "I-LLMCACHE-26 violated: llm.cache_skip payload key "
                "is not a string literal"
            )
            keys.add(key_node.value)
        assert keys == {"cache_key_prefix", "reason"}, (
            "I-LLMCACHE-26 violated: llm.cache_skip payload keys "
            f"are {sorted(keys)}; expected "
            "{'cache_key_prefix', 'reason'}"
        )
        found_skip = True
    assert found_skip, (
        "I-LLMCACHE-26 violated: no llm.cache_skip record(...) call "
        "found in client.py"
    )
