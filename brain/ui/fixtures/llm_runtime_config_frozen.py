"""Phase 3.8b config-frozen fixture.

Drives:

* ``I-LLMTOG-11`` (STRUCTURAL) — ``LlmRuntimeConfig`` is a frozen /
  slots-bearing record. Fields are bounded primitives, optional
  bounded strings, a bounded ``float`` timeout, a ``bool``, and a
  tuple of bounded printable strings; no field is a callable, file
  handle, socket, subprocess handle, or LLM client instance.
"""
from __future__ import annotations

import dataclasses
from typing import Optional, get_type_hints

from brain.invariants import register
from brain.ui.llm_runtime import LlmRuntimeConfig, LlmRuntimeMode


@register("I-LLMTOG-11", status="STRUCTURAL")
def check_I_LLMTOG_11_config_frozen() -> None:
    # Dataclass with frozen=True and slots=True.
    assert dataclasses.is_dataclass(LlmRuntimeConfig), (
        "I-LLMTOG-11 violated: LlmRuntimeConfig is not a dataclass"
    )
    params = LlmRuntimeConfig.__dataclass_params__  # type: ignore[attr-defined]
    assert params.frozen, (
        "I-LLMTOG-11 violated: LlmRuntimeConfig is not frozen"
    )
    assert hasattr(LlmRuntimeConfig, "__slots__"), (
        "I-LLMTOG-11 violated: LlmRuntimeConfig has no __slots__"
    )

    # Field type set is the documented bounded set.
    hints = get_type_hints(LlmRuntimeConfig)
    expected = {
        "mode": LlmRuntimeMode,
        "api_key": Optional[str],
        "model": str,
        "claude_cli_executable": str,
        "timeout_seconds": float,
        "enable_cache": bool,
        "mock_responses": tuple[str, ...],
    }
    assert hints == expected, (
        "I-LLMTOG-11 violated: LlmRuntimeConfig field types drifted "
        f"(got {hints!r})"
    )

    # Frozen behavior: attribute assignment raises.
    config = LlmRuntimeConfig()
    try:
        config.mode = LlmRuntimeMode.MOCK  # type: ignore[misc]
    except (dataclasses.FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError(
            "I-LLMTOG-11 violated: LlmRuntimeConfig allowed attribute "
            "assignment"
        )

    # Default mock_responses is the empty tuple.
    assert config.mock_responses == (), (
        "I-LLMTOG-11 violated: default mock_responses is not the empty "
        f"tuple (got {config.mock_responses!r})"
    )

    # __slots__ contents include exactly the documented fields.
    actual_slots = frozenset(LlmRuntimeConfig.__slots__)
    expected_slots = frozenset(expected.keys())
    assert actual_slots == expected_slots, (
        "I-LLMTOG-11 violated: LlmRuntimeConfig.__slots__ drifted "
        f"(got {sorted(actual_slots)})"
    )
