"""TOCE Boolean classifier layer. Encodes TOCE_Core.lean.

Catalog rows owned: I-TOCE-01..05 (REQUIRED).

Lean source: ``lean_reference/TOCE_Core.lean``.

This layer is structurally independent of ``brain/tlica/``; classification
branches only on ``available``, ``verificationPath``, and ``retrievable``.
``operative`` is not consulted (per Lean ``classifyContent``).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContentClass(Enum):
    CONSCIOUS_CLEAR = "consciousClear"
    CONSCIOUS_FUZZY = "consciousFuzzy"
    LATENT_RETRIEVABLE = "latentRetrievable"
    UNCONSCIOUS_OPERATIVE = "unconsciousOperative"


@dataclass(frozen=True, slots=True)
class ContentState:
    """Mirrors ``TOCE_Core.lean::ContentState``."""

    available: bool
    verification_path: bool
    retrievable: bool
    operative: bool


def classify_content(s: ContentState) -> ContentClass:
    """``TOCE_Core.lean::classifyContent``.

    Truth table (matches Lean exactly):
      - available=true, verificationPath=true  → consciousClear
      - available=true, verificationPath=false → consciousFuzzy
      - available=false, retrievable=true      → latentRetrievable
      - available=false, retrievable=false     → unconsciousOperative

    ``operative`` is never consulted (I-TOCE-01 verifies this).
    """
    if s.available and s.verification_path:
        return ContentClass.CONSCIOUS_CLEAR
    if s.available and not s.verification_path:
        return ContentClass.CONSCIOUS_FUZZY
    if not s.available and s.retrievable:
        return ContentClass.LATENT_RETRIEVABLE
    return ContentClass.UNCONSCIOUS_OPERATIVE
