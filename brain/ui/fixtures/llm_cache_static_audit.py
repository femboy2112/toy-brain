"""Phase 3.14 LLM cache static-audit fixture.

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
