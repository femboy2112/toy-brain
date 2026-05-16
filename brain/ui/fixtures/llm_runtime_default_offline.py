"""Phase 3.8b default-offline factory fixture.

Drives:

* ``I-LLMTOG-01`` (REQUIRED) — Default ``LlmRuntimeConfig()`` builds
  ``OfflineStandInClient``; the factory does not consult
  ``os.environ``.
"""
from __future__ import annotations

import os

from brain.invariants import register
from brain.ui.__main__ import OfflineStandInClient
from brain.ui.llm_runtime import (
    LlmRuntimeConfig,
    LlmRuntimeMode,
    build_llm_client_from_config,
)


@register("I-LLMTOG-01", status="REQUIRED")
def check_I_LLMTOG_01_default_builds_offline() -> None:
    config = LlmRuntimeConfig()

    assert config.mode is LlmRuntimeMode.OFFLINE, (
        "I-LLMTOG-01 violated: default LlmRuntimeConfig().mode is not "
        f"OFFLINE (got {config.mode!r})"
    )
    assert config.enable_cache is False, (
        "I-LLMTOG-01 violated: default LlmRuntimeConfig().enable_cache "
        f"is not False (got {config.enable_cache!r})"
    )

    # Set a stale ANTHROPIC_API_KEY in the process env and confirm the
    # factory ignores it: build_llm_client_from_config(config) must
    # never read os.environ (catalog patch plan section 4).
    sentinel = "I-LLMTOG-01-sentinel-key"
    saved_anthropic = os.environ.get("ANTHROPIC_API_KEY")
    saved_brain = os.environ.get("BRAIN_ANTHROPIC_API_KEY")
    saved_mode = os.environ.get("BRAIN_LLM_MODE")
    os.environ["ANTHROPIC_API_KEY"] = sentinel
    os.environ["BRAIN_ANTHROPIC_API_KEY"] = sentinel
    os.environ["BRAIN_LLM_MODE"] = "anthropic-api"
    try:
        client = build_llm_client_from_config(config)
    finally:
        # Restore the original env to keep the runner deterministic.
        if saved_anthropic is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = saved_anthropic
        if saved_brain is None:
            os.environ.pop("BRAIN_ANTHROPIC_API_KEY", None)
        else:
            os.environ["BRAIN_ANTHROPIC_API_KEY"] = saved_brain
        if saved_mode is None:
            os.environ.pop("BRAIN_LLM_MODE", None)
        else:
            os.environ["BRAIN_LLM_MODE"] = saved_mode

    assert isinstance(client, OfflineStandInClient), (
        "I-LLMTOG-01 violated: build_llm_client_from_config(LlmRuntimeConfig()) "
        f"did not return OfflineStandInClient (got {type(client).__name__})"
    )
