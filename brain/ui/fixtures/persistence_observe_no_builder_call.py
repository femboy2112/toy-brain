"""Phase 3.10b no-builder-call static AST audit fixture.

Drives:

* ``I-OBSERVE-07`` (STRUCTURAL) — ``brain/ui/persistence_observe.py``
  contains no call to any kernel builder
  (``make_profile_with_cogito``, ``make_msi``, ``make_ptcns``,
  ``make_text_stream_chunk``, ``make_stream_promotion_candidate``) and
  no instantiation of ``ContentRegistry`` / ``BrainState`` /
  ``TextStreamHistory`` / ``OperatorSession``. This complements
  ``I-OBSERVE-05`` (behavioral non-mutation) with structural
  absence-of-construction.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register


_PERSISTENCE_OBSERVE_PATH = (
    Path(__file__).resolve().parents[1] / "persistence_observe.py"
)


#: Names that, if called or instantiated inside persistence_observe.py,
#: violate I-OBSERVE-07. The check inspects both bare-name calls
#: (``make_msi(...)``) and attribute calls (``module.make_msi(...)``).
_FORBIDDEN_BUILDER_NAMES: frozenset[str] = frozenset({
    "make_profile_with_cogito",
    "make_msi",
    "make_ptcns",
    "make_text_stream_chunk",
    "make_stream_promotion_candidate",
    "ContentRegistry",
    "BrainState",
    "TextStreamHistory",
    "OperatorSession",
})


@register("I-OBSERVE-07", status="STRUCTURAL")
def check_i_observe_07_no_builder_call() -> None:
    """persistence_observe.py contains no kernel-builder call."""
    source = _PERSISTENCE_OBSERVE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_OBSERVE_PATH))

    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name is not None and name in _FORBIDDEN_BUILDER_NAMES:
                errors.append(
                    f"forbidden builder call {name!r}() at line "
                    f"{node.lineno} (I-OBSERVE-07)"
                )

    # Imports of the forbidden names are tolerated only because
    # ``OperatorSession`` must be imported for the ``isinstance``
    # narrowing inside :func:`db_diff`. The audit relies on the call
    # check above: any actual builder invocation or constructor call is
    # rejected, regardless of how the name was imported.

    if errors:
        raise AssertionError(
            "I-OBSERVE-07 violated:\n  - " + "\n  - ".join(errors)
        )
