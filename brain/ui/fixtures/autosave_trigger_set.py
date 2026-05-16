"""Phase 3.10c closed-enum fixture for AutosaveMode + AutosaveTrigger.

Drives:

* ``I-AUTOSAVE-12`` (STRUCTURAL) — :class:`AutosaveMode` and
  :class:`AutosaveTrigger` are closed ``(str, Enum)`` types.
  :data:`SUPPORTED_AUTOSAVE_MODES` and
  :data:`SUPPORTED_AUTOSAVE_TRIGGERS` match their enum membership;
  unknown string values raise :class:`ValueError`.
"""
from __future__ import annotations

from enum import Enum

from brain.invariants import register
from brain.ui.autosave import (
    AutosaveMode,
    AutosaveTrigger,
    SUPPORTED_AUTOSAVE_MODES,
    SUPPORTED_AUTOSAVE_TRIGGERS,
)


@register("I-AUTOSAVE-12", status="STRUCTURAL")
def check_i_autosave_12_enums_are_closed() -> None:
    # Both enums are (str, Enum) subclasses.
    if not issubclass(AutosaveMode, str):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveMode is not a str subclass"
        )
    if not issubclass(AutosaveMode, Enum):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveMode is not an Enum subclass"
        )
    if not issubclass(AutosaveTrigger, str):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveTrigger is not a str subclass"
        )
    if not issubclass(AutosaveTrigger, Enum):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveTrigger is not an Enum subclass"
        )

    # Exactly the two documented members in each enum.
    actual_modes = frozenset(m.value for m in AutosaveMode)
    expected_modes = frozenset({"off", "after-successful-mutation"})
    if actual_modes != expected_modes:
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveMode members drifted "
            f"(got {sorted(actual_modes)!r}, "
            f"expected {sorted(expected_modes)!r})"
        )

    actual_triggers = frozenset(t.value for t in AutosaveTrigger)
    expected_triggers = frozenset({"step_tick", "stream_promote"})
    if actual_triggers != expected_triggers:
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveTrigger members drifted "
            f"(got {sorted(actual_triggers)!r}, "
            f"expected {sorted(expected_triggers)!r})"
        )

    # SUPPORTED_AUTOSAVE_MODES / SUPPORTED_AUTOSAVE_TRIGGERS are
    # frozensets matching the enum membership exactly.
    if not isinstance(SUPPORTED_AUTOSAVE_MODES, frozenset):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: SUPPORTED_AUTOSAVE_MODES is not a "
            f"frozenset (got {type(SUPPORTED_AUTOSAVE_MODES).__name__})"
        )
    if not isinstance(SUPPORTED_AUTOSAVE_TRIGGERS, frozenset):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: SUPPORTED_AUTOSAVE_TRIGGERS is "
            f"not a frozenset (got "
            f"{type(SUPPORTED_AUTOSAVE_TRIGGERS).__name__})"
        )
    if SUPPORTED_AUTOSAVE_MODES != frozenset(AutosaveMode):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: SUPPORTED_AUTOSAVE_MODES does "
            "not match the AutosaveMode membership"
        )
    if SUPPORTED_AUTOSAVE_TRIGGERS != frozenset(AutosaveTrigger):
        raise AssertionError(
            "I-AUTOSAVE-12 violated: SUPPORTED_AUTOSAVE_TRIGGERS does "
            "not match the AutosaveTrigger membership"
        )

    # Unknown string values raise on enum lookup.
    try:
        AutosaveMode("invalid")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveMode('invalid') did not "
            "raise ValueError"
        )
    try:
        AutosaveTrigger("invalid")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-AUTOSAVE-12 violated: AutosaveTrigger('invalid') did "
            "not raise ValueError"
        )
