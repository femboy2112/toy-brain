"""Phase 3.8b closed-mode-enumeration fixture.

Drives:

* ``I-LLMTOG-02`` (REQUIRED) — ``LlmRuntimeMode`` is a finite closed
  enumeration; unknown strings raise.
* ``I-LLMTOG-12`` (STRUCTURAL) — ``LlmRuntimeMode`` is a closed
  ``str, Enum``; member set is exactly the documented four values.
"""
from __future__ import annotations

from enum import Enum

from brain.invariants import register
from brain.ui.llm_runtime import (
    LlmRuntimeError,
    LlmRuntimeMode,
    parse_llm_runtime_args,
)


_EXPECTED_VALUES: frozenset[str] = frozenset(
    {"offline", "mock", "anthropic-api", "claude-cli"}
)


@register("I-LLMTOG-02", status="REQUIRED")
def check_I_LLMTOG_02_mode_closed_runtime() -> None:
    # Member set is exactly the documented four values.
    actual = frozenset(m.value for m in LlmRuntimeMode)
    assert actual == _EXPECTED_VALUES, (
        "I-LLMTOG-02 violated: LlmRuntimeMode member set drifted "
        f"(got {sorted(actual)})"
    )

    # Constructor accepts each documented value.
    for value in _EXPECTED_VALUES:
        assert LlmRuntimeMode(value).value == value, (
            f"I-LLMTOG-02 violated: LlmRuntimeMode({value!r}) round-trip "
            "failed"
        )

    # parse_llm_runtime_args raises LlmRuntimeError on an unknown mode.
    for bad in ("Offline", "ANTHROPIC", "claude_cli", "openai-api", " "):
        try:
            parse_llm_runtime_args(["--llm-mode", bad], {})
        except LlmRuntimeError:
            continue
        raise AssertionError(
            f"I-LLMTOG-02 violated: parse_llm_runtime_args accepted unknown "
            f"--llm-mode={bad!r}"
        )


@register("I-LLMTOG-12", status="STRUCTURAL")
def check_I_LLMTOG_12_mode_closed_structural() -> None:
    # LlmRuntimeMode is a (str, Enum) subclass.
    assert issubclass(LlmRuntimeMode, str), (
        "I-LLMTOG-12 violated: LlmRuntimeMode is not a str subclass"
    )
    assert issubclass(LlmRuntimeMode, Enum), (
        "I-LLMTOG-12 violated: LlmRuntimeMode is not an Enum subclass"
    )

    # Exact membership.
    actual = frozenset(m.value for m in LlmRuntimeMode)
    assert actual == _EXPECTED_VALUES, (
        "I-LLMTOG-12 violated: LlmRuntimeMode member set drifted "
        f"(got {sorted(actual)})"
    )

    # Members have str semantics (an explicit affordance of str-Enum).
    assert LlmRuntimeMode.OFFLINE == "offline", (
        "I-LLMTOG-12 violated: LlmRuntimeMode.OFFLINE does not equal "
        "the underlying str value"
    )
