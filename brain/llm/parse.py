"""Strict response parser. Maps raw LLM output to ``ConsistencyEval``.

Used by ``LLMBackedPtCns`` between the client call and the result cache.
Strictness is the point: anything that isn't unambiguously one of the
three canonical tokens raises ``ParseError``, which the retry shell
catches and uses to assemble a sharper retry prompt.
"""
from __future__ import annotations

from brain.tlica.ptcns import ConsistencyEval


# Bump rule (Phase 3.14 LOCK D / LOCK M): any change to the parse
# grammar, the ``ConsistencyEval`` enum membership, or the parse-failure
# classification requires bumping this version string. Bumping
# invalidates older L2 semantic cache entries by key namespace
# separation; no migration / silent reuse.
PARSE_SCHEMA_VERSION = "consistency-eval-v1"


class ParseError(ValueError):
    """Raised when a raw LLM response cannot be coerced into a
    ``ConsistencyEval``. Caught by ``LLMBackedPtCns`` to trigger retry.
    """


_VALID = {"PRESERVE", "DAMAGE", "NEUTRAL"}
_STRIP_CHARS = ".,;:!?\"'`*_"


def parse_consistency_eval(raw: str) -> ConsistencyEval:
    """Parse one of ``{PRESERVE, DAMAGE, NEUTRAL}`` from ``raw``.

    Tolerates trailing punctuation, surrounding markdown markers, and
    full-sentence drift by scanning whitespace-separated tokens. The
    canonical exact-match short-circuit fires first.

    Phase 2 v1.2 (P4): rejects ambiguous responses. If the scan finds
    multiple distinct valid tokens (e.g. ``"PRESERVE AND DAMAGE"``,
    ``"DAMAGE, not PRESERVE"``), raises ``ParseError`` so the retry
    shell can ask the LLM for a single-word answer.
    """
    cleaned = raw.strip().upper()
    if cleaned in _VALID:
        return ConsistencyEval[cleaned]
    found: set[str] = set()
    for token in cleaned.split():
        stripped = token.strip(_STRIP_CHARS)
        if stripped in _VALID:
            found.add(stripped)
    if len(found) == 1:
        return ConsistencyEval[found.pop()]
    if len(found) > 1:
        raise ParseError(
            f"Ambiguous response — found multiple valid tokens "
            f"{sorted(found)} in {raw!r}. Expected exactly one of "
            f"PRESERVE / DAMAGE / NEUTRAL."
        )
    raise ParseError(
        f"Could not parse {raw!r} as one of PRESERVE / DAMAGE / NEUTRAL"
    )
