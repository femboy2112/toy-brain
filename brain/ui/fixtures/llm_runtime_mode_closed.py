"""Phase 3.8b closed-mode-enumeration fixture (extended in Phase 3.11).

Drives:

* ``I-LLMTOG-02`` (REQUIRED) — ``LlmRuntimeMode`` is a finite closed
  enumeration; unknown strings raise.
* ``I-LLMTOG-12`` (STRUCTURAL) — ``LlmRuntimeMode`` is a closed
  ``str, Enum``; member set is exactly the documented five values
  (Phase 3.11 extended from four to five).
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
    {"offline", "mock", "anthropic-api", "claude-cli", "codex-cli"}
)
_EXPECTED_MEMBER_COUNT: int = 5


@register("I-LLMTOG-02", status="REQUIRED")
def check_I_LLMTOG_02_mode_closed_runtime() -> None:
    # Member set is exactly the documented five values (Phase 3.11
    # extended from four to five with CODEX_CLI).
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

    # Exact membership (Phase 3.11 extends from four to five).
    actual = frozenset(m.value for m in LlmRuntimeMode)
    assert actual == _EXPECTED_VALUES, (
        "I-LLMTOG-12 violated: LlmRuntimeMode member set drifted "
        f"(got {sorted(actual)})"
    )

    # Member count is exactly five (Phase 3.11 corrigenda Section 3).
    actual_count = sum(1 for _ in LlmRuntimeMode)
    assert actual_count == _EXPECTED_MEMBER_COUNT, (
        "I-LLMTOG-12 violated: LlmRuntimeMode member count is not "
        f"{_EXPECTED_MEMBER_COUNT} (got {actual_count})"
    )

    # Members have str semantics (an explicit affordance of str-Enum).
    assert LlmRuntimeMode.OFFLINE == "offline", (
        "I-LLMTOG-12 violated: LlmRuntimeMode.OFFLINE does not equal "
        "the underlying str value"
    )
    assert LlmRuntimeMode.CODEX_CLI == "codex-cli", (
        "I-LLMTOG-12 violated: LlmRuntimeMode.CODEX_CLI does not equal "
        "the underlying str value"
    )
