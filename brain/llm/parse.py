"""Strict response parser. Maps raw LLM output to ``ConsistencyEval``.

Used by ``LLMBackedPtCns`` between the client call and the result cache.
Strictness is the point: anything that isn't unambiguously one of the
three canonical tokens raises ``ParseError``, which the retry shell
catches and uses to assemble a sharper retry prompt.
"""
from __future__ import annotations

from brain.tlica.ptcns import ConsistencyEval


class ParseError(ValueError):
    """Raised when a raw LLM response cannot be coerced into a
    ``ConsistencyEval``. Caught by ``LLMBackedPtCns`` to trigger retry.
    """


_VALID = {"PRESERVE", "DAMAGE", "NEUTRAL"}
_STRIP_CHARS = ".,;:!?\"'`*_"


def parse_consistency_eval(raw: str) -> ConsistencyEval:
    """Parse one of ``{PRESERVE, DAMAGE, NEUTRAL}`` from ``raw``.

    Tolerates trailing punctuation, surrounding markdown markers, and
    full-sentence drift by scanning whitespace-separated tokens. Anything
    less unambiguous raises ``ParseError``.
    """
    cleaned = raw.strip().upper()
    if cleaned in _VALID:
        return ConsistencyEval[cleaned]
    for token in cleaned.split():
        stripped = token.strip(_STRIP_CHARS)
        if stripped in _VALID:
            return ConsistencyEval[stripped]
    raise ParseError(
        f"Could not parse {raw!r} as one of PRESERVE / DAMAGE / NEUTRAL"
    )
