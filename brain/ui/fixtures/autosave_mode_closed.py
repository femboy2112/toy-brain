"""Phase 3.10c AutosaveConfig closed-mode fixture.

Drives:

* ``I-AUTOSAVE-02`` (REQUIRED) — AutosaveConfig with mode != OFF +
  empty ``db_path_str`` raises ``ValueError``. The cold-start default
  (``AutosaveConfig(mode=OFF, db_path_str="")``) succeeds. Any value
  outside :data:`SUPPORTED_AUTOSAVE_MODES` is rejected at construction
  time.
"""
from __future__ import annotations

from brain.invariants import register
from brain.ui.autosave import (
    AutosaveConfig,
    AutosaveMode,
    SUPPORTED_AUTOSAVE_MODES,
)


@register("I-AUTOSAVE-02", status="REQUIRED")
def check_i_autosave_02_mode_closed() -> None:
    # AutosaveConfig with mode != OFF and empty db_path_str raises.
    try:
        AutosaveConfig(
            mode=AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
            db_path_str="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-AUTOSAVE-02 violated: AutosaveConfig accepted non-OFF "
            "mode + empty db_path_str"
        )

    # The cold-start default (OFF + empty) succeeds.
    cfg_default = AutosaveConfig(
        mode=AutosaveMode.OFF, db_path_str=""
    )
    if cfg_default.mode is not AutosaveMode.OFF:
        raise AssertionError(
            "I-AUTOSAVE-02 violated: default AutosaveConfig mode is "
            f"{cfg_default.mode!r}"
        )
    if cfg_default.db_path_str != "":
        raise AssertionError(
            "I-AUTOSAVE-02 violated: default AutosaveConfig db_path_str "
            f"is {cfg_default.db_path_str!r}"
        )

    # Constructing with a non-AutosaveMode mode raises TypeError.
    try:
        AutosaveConfig(mode="off", db_path_str="")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-AUTOSAVE-02 violated: AutosaveConfig accepted a str mode"
        )

    # A non-OFF mode with a valid db_path_str succeeds.
    cfg_enabled = AutosaveConfig(
        mode=AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
        db_path_str="/tmp/brain-i-autosave-02.sqlite3",
    )
    if cfg_enabled.mode is not AutosaveMode.AFTER_SUCCESSFUL_MUTATION:
        raise AssertionError(
            "I-AUTOSAVE-02 violated: enabled AutosaveConfig mode "
            f"drifted to {cfg_enabled.mode!r}"
        )

    # SUPPORTED_AUTOSAVE_MODES contains exactly the two documented modes.
    actual = frozenset(SUPPORTED_AUTOSAVE_MODES)
    expected = frozenset({
        AutosaveMode.OFF,
        AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
    })
    if actual != expected:
        raise AssertionError(
            "I-AUTOSAVE-02 violated: SUPPORTED_AUTOSAVE_MODES drifted "
            f"(got {sorted(m.value for m in actual)!r}, "
            f"expected {sorted(m.value for m in expected)!r})"
        )
