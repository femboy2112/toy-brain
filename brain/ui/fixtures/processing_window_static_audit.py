"""Phase 3.18 processing_window.py static audit.

Drives ``I-PWND-02`` (STRUCTURAL). The audit confirms that:

* ``brain/development/processing_window.py`` imports only from the
  documented seam (``__future__``, ``dataclasses``, ``enum``,
  ``typing``, ``brain.development.text_stream``,
  ``brain.tlica.profile``).
* No forbidden module / submodule appears in any import
  statement (``os``, ``subprocess``, ``socket``, ``urllib``, ``http``,
  ``requests``, ``pathlib``, ``tempfile``, ``shutil``, ``curses``,
  ``brain.tick``, ``brain.llm``, ``brain.ui``, ``brain.tlica`` other
  than ``brain.tlica.profile`` for ``COGITO_ID``, ``threading``,
  ``asyncio``, ``atexit``, ``signal``, ``importlib``, ``math``,
  ``hashlib``, ``time``, ``random``).
* No dynamic-execution call appears (``eval``, ``exec``, ``compile``,
  ``__import__``, ``importlib.import_module``).
* No ``float`` / ``round`` / ``open`` / ``math.*`` call participates
  in any module-level function (defense in depth on determinism).
* Module-level statements are limited to imports, constants,
  function defs, class defs, and a module docstring.
* :class:`InternalEventSource` is a closed ``str, Enum`` whose
  membership exactly matches the locked set
  ``{REHEARSAL, PLEDGER_SUMMARY, COHMON_SUMMARY}``.
* No string in :data:`MODULE_PRODUCED_STRINGS` contains any term
  from
  :data:`brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS`
  (case-insensitive).
* The module source itself contains none of those terms (case-
  insensitive). This is the non-claim discipline inherited from
  the Phase 3.12c Coherence Monitor; the Phase 3.18 module reuses
  the canonical tuple.
* :func:`build_rehearsal_provenance` over the v1-emitted source
  set produces strings that are bounded printable and contain no
  forbidden non-claim term.
* No callable / handle / client / scalar field appears on
  :class:`RehearsalStep` (the record is frozen / slotted; its
  fields are all bounded primitives).
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.development.coherence_monitor import (
    _FORBIDDEN_NON_CLAIM_TERMS,
)
from brain.development.processing_window import (
    InternalEventSource,
    MODULE_PRODUCED_STRINGS,
    PROCESSING_WINDOW_CALL_BUDGET_MAX,
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
    PROCESSING_WINDOW_SIZE_MAX,
    RehearsalStep,
    build_rehearsal_provenance,
)
from brain.invariants import register


_PROCESSING_WINDOW_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "development"
    / "processing_window.py"
)


_FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "os",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "pathlib",
    "tempfile",
    "shutil",
    "curses",
    "brain.tick",
    "brain.llm",
    "brain.ui",
    "threading",
    "asyncio",
    "atexit",
    "signal",
    "importlib",
    "math",
    "hashlib",
    "time",
    "random",
)


# Allow only brain.tlica.profile from brain.tlica (for COGITO_ID).
_FORBIDDEN_TLICA_SUBMODULES: tuple[str, ...] = (
    "brain.tlica.action_projection",
    "brain.tlica.agency",
    "brain.tlica.preservation",
    "brain.tlica.affect",
    "brain.tlica.modes",
    "brain.tlica.msi",
    "brain.tlica.ptcns",
    "brain.tlica.iboundary",
    "brain.tlica.project_map",
    "brain.tlica.pce",
    "brain.tlica.trajectory",
    "brain.tlica.builders",
    "brain.tlica.integration_graph",
    "brain.tlica.phi_coordinate",
    "brain.tlica.free_will",
    "brain.tlica.dynamics",
    "brain.tlica.mode_aggregation",
    "brain.tlica.non_reducibility",
    "brain.tlica.comparison",
)


_ALLOWED_IMPORT_NAMES: frozenset[str] = frozenset({
    "__future__",
    "dataclasses",
    "enum",
    "typing",
    "brain.development.text_stream",
    "brain.tlica.profile",
})


_FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "float",
    "round",
})


_FORBIDDEN_CALL_PREFIXES: tuple[str, ...] = (
    "importlib.",
    "atexit.",
    "signal.",
    "math.",
    "hashlib.",
    "time.",
    "random.",
)


_EXPECTED_INTERNAL_EVENT_SOURCE_VALUES: frozenset[str] = frozenset({
    "rehearsal",
    "pledger_summary",
    "cohmon_summary",
})


def _parse_module() -> ast.Module:
    source = _PROCESSING_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(_PROCESSING_WINDOW_SOURCE_PATH))


def _import_targets(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level
            prefix = "." * level
            out.append(prefix + module)
    return out


def _is_forbidden_import(name: str) -> bool:
    bare = name.lstrip(".")
    if not bare:
        return False
    for prefix in _FORBIDDEN_IMPORT_PREFIXES:
        if bare == prefix or bare.startswith(prefix + "."):
            return True
    for prefix in _FORBIDDEN_TLICA_SUBMODULES:
        if bare == prefix or bare.startswith(prefix + "."):
            return True
    return False


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


def _is_allowed_module_level(stmt: ast.stmt) -> bool:
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return True
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
        return True
    if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return True
    return False


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-PWND-02", status="STRUCTURAL")
def check_processing_window_static_audit() -> None:
    """Static AST audit on the new processing_window module."""
    assert _PROCESSING_WINDOW_SOURCE_PATH.exists(), (
        "I-PWND-02 violated: processing_window.py not found at "
        f"{_PROCESSING_WINDOW_SOURCE_PATH}"
    )
    tree = _parse_module()

    # 1. Imports.
    targets = _import_targets(tree)
    bad_forbidden = [name for name in targets if _is_forbidden_import(name)]
    assert not bad_forbidden, (
        "I-PWND-02 violated: processing_window.py imports forbidden "
        f"modules {bad_forbidden}"
    )
    for name in targets:
        bare = name.lstrip(".")
        if not bare:
            continue
        assert bare in _ALLOWED_IMPORT_NAMES, (
            "I-PWND-02 violated: processing_window.py imports unexpected "
            f"target {name!r} (allowed: {sorted(_ALLOWED_IMPORT_NAMES)})"
        )

    # 2. Module-level statements limited.
    for stmt in tree.body:
        assert _is_allowed_module_level(stmt), (
            "I-PWND-02 violated: disallowed module-level statement "
            f"{type(stmt).__name__} at line {stmt.lineno}"
        )

    # 3. No forbidden call anywhere in the module.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            assert name not in _FORBIDDEN_CALL_NAMES, (
                f"I-PWND-02 violated: forbidden call {name!r} at "
                f"line {node.lineno}"
            )
            for prefix in _FORBIDDEN_CALL_PREFIXES:
                assert not name.startswith(prefix), (
                    f"I-PWND-02 violated: forbidden call prefix "
                    f"{prefix} in {name!r} at line {node.lineno}"
                )

    # 4. InternalEventSource is a closed (str, Enum) with the locked
    # value set.
    assert issubclass(InternalEventSource, str), (
        "I-PWND-02 violated: InternalEventSource is not a str enum"
    )
    actual_source_values = frozenset(m.value for m in InternalEventSource)
    assert actual_source_values == _EXPECTED_INTERNAL_EVENT_SOURCE_VALUES, (
        "I-PWND-02 violated: InternalEventSource value set drifted "
        f"(got {sorted(actual_source_values)!r}, expected "
        f"{sorted(_EXPECTED_INTERNAL_EVENT_SOURCE_VALUES)!r})"
    )

    # 5. PROCESSING_WINDOW_SIZE_MAX is the locked value (255).
    assert PROCESSING_WINDOW_SIZE_MAX == 255, (
        "I-PWND-02 violated: PROCESSING_WINDOW_SIZE_MAX "
        f"{PROCESSING_WINDOW_SIZE_MAX!r} != 255"
    )
    assert PROCESSING_WINDOW_CALL_BUDGET_MAX == 65535, (
        "I-PWND-02 violated: PROCESSING_WINDOW_CALL_BUDGET_MAX "
        f"{PROCESSING_WINDOW_CALL_BUDGET_MAX!r} != 65535"
    )
    assert PROCESSING_WINDOW_PROVENANCE_PREFIX == (
        "internal_processing_window"
    ), (
        "I-PWND-02 violated: PROCESSING_WINDOW_PROVENANCE_PREFIX "
        f"{PROCESSING_WINDOW_PROVENANCE_PREFIX!r} drifted"
    )

    # 6. No forbidden non-claim term in any produced string.
    for produced in MODULE_PRODUCED_STRINGS:
        term = _has_forbidden_term(produced)
        assert term is None, (
            "I-PWND-02 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden non-claim term {term!r}"
        )

    # 7. Module source itself contains no forbidden non-claim term.
    source = _PROCESSING_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")
    bad_term_in_source = _has_forbidden_term(source)
    assert bad_term_in_source is None, (
        "I-PWND-02 violated: processing_window.py source contains "
        f"forbidden non-claim term {bad_term_in_source!r}"
    )

    # 8. build_rehearsal_provenance over the v1-emitted source set
    # produces strings that contain no forbidden non-claim term.
    for k in (1, 2, 3, 42, 255):
        provenance = build_rehearsal_provenance(
            tick_index=k, source=InternalEventSource.REHEARSAL
        )
        term = _has_forbidden_term(provenance)
        assert term is None, (
            "I-PWND-02 violated: build_rehearsal_provenance output "
            f"{provenance!r} contains forbidden non-claim term {term!r}"
        )

    # 9. RehearsalStep has no callable / handle / client / scalar-
    # aggregate field. We construct one and walk its slots.
    step = RehearsalStep(
        tick_index=1,
        source=InternalEventSource.REHEARSAL,
        provenance="internal_processing_window:1:rehearsal",
        text="probe",
    )
    expected_slots = ("tick_index", "source", "provenance", "text")
    assert step.__slots__ == expected_slots, (
        "I-PWND-02 violated: RehearsalStep slots drifted "
        f"(got {step.__slots__!r}, expected {expected_slots!r})"
    )
    for slot in expected_slots:
        value = getattr(step, slot)
        assert not callable(value), (
            f"I-PWND-02 violated: RehearsalStep.{slot} is callable"
        )
        assert not hasattr(value, "eval_consistency"), (
            f"I-PWND-02 violated: RehearsalStep.{slot} looks like an "
            "LLM client"
        )
        assert not hasattr(value, "fileno"), (
            f"I-PWND-02 violated: RehearsalStep.{slot} exposes fileno()"
        )
        assert not hasattr(value, "send_signal"), (
            f"I-PWND-02 violated: RehearsalStep.{slot} looks like a "
            "subprocess handle"
        )

    # 10. Reserved enum members raise when passed to
    # build_rehearsal_provenance — they MUST NOT be emitted by v1.
    for reserved in (
        InternalEventSource.PLEDGER_SUMMARY,
        InternalEventSource.COHMON_SUMMARY,
    ):
        raised = False
        try:
            build_rehearsal_provenance(tick_index=1, source=reserved)
        except ValueError:
            raised = True
        assert raised, (
            "I-PWND-02 violated: build_rehearsal_provenance accepted "
            f"reserved source {reserved.value!r}"
        )
