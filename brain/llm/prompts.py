"""Prompt templates for ``LLMBackedPtCns`` (Phase 2 v1).

Edit-and-iterate target: v1 ships these as a deliberately simple
starting point. Templates are exposed as module-level constants so they
can be patched at runtime by experiments without touching the retry
shell logic.
"""
from __future__ import annotations

PROMPT_TEMPLATE = """You are evaluating a new piece of content for inclusion in a self-modeling system.

The system has an identity anchor (the "cogito": the system's bare self-as-self) and currently contains the following non-cogito contents in its maximally-self-defined I (MSI):

{existing_msi}

The new content to evaluate is:
- ID: {new_id}
- Description: {new_text}

Evaluate whether integrating this content into the self-model would:

- PRESERVE: positively integrate with the existing self-model (consistency-preserving; identity-correlation-positive).
- DAMAGE: threaten the consistency of the existing self-model (frame-threatening contradiction; identity-correlation-negative).
- NEUTRAL: neither preserve nor damage — identity-irrelevant information that can be encapsulated without disturbing the frame.

Respond with exactly one word: PRESERVE, DAMAGE, or NEUTRAL. No other text.
"""


RETRY_TEMPLATE = """Your previous response could not be parsed.

Original prompt:
{original}

Your response was:
{raw}

Parse error: {error}

Please respond with exactly one word: PRESERVE, DAMAGE, or NEUTRAL. No other text.
"""
