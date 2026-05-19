"""Phase 3.22b Abstract Pattern Signatures — bounded structural-form layer.

This module is a strict pure helper layer. It extracts a bounded
abstract structural form (token-equality class, recurrence class,
shape string) from an input text. No semantic interpretation is
performed; the layer operates purely on surface tokens.

Non-claim discipline (binding):

* No claim of cognitive properties is made. The function names use
  "derive" deliberately; this module performs no semantic
  interpretation and asserts no cognitive property of the running
  system.
* Every produced string passes the canonical
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  audit (case-insensitive substring).

Closed import set:

* ``__future__``, ``dataclasses``, ``hashlib``, ``typing``
* ``brain.development.coherence_monitor`` (read-only;
  ``_FORBIDDEN_NON_CLAIM_TERMS``)

No ``brain.llm.*``. No ``brain.tick``. No curses, subprocess, socket,
urllib, http, requests, tempfile, shutil, threading, asyncio,
atexit, signal, importlib, time, random.

Drives ``I-AGENTLEARN-01``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS


# ---------------------------------------------------------------------------
# Bounded constants.
# ---------------------------------------------------------------------------

ABSTRACT_PATTERN_MAX_TOKENS: int = 32
ABSTRACT_PATTERN_MAX_INPUT_LEN: int = 1024
ABSTRACT_PATTERN_DIGEST_HEX_LEN: int = 16
ABSTRACT_PATTERN_SHAPE_MAX_LEN: int = 128
ABSTRACT_PATTERN_EXPLANATION_MAX_LEN: int = 240
ABSTRACT_PATTERN_MODULE_VERSION: str = "phase3.22b.v1"

# Letter labels used when synthesizing the shape string. Bounded.
_SHAPE_LABELS: tuple[str, ...] = tuple(chr(ord("A") + i) for i in range(26))


# ---------------------------------------------------------------------------
# Forbidden-term audit (single point).
# ---------------------------------------------------------------------------


def _text_has_forbidden_term(text: str) -> Optional[str]:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


# ---------------------------------------------------------------------------
# Closed enums-as-constants for classifications.
# ---------------------------------------------------------------------------

ABSTRACT_PATTERN_CLASS_EMPTY: str = "empty"
ABSTRACT_PATTERN_CLASS_OVERLONG: str = "overlong"
ABSTRACT_PATTERN_CLASS_NON_PRINTABLE: str = "non-printable"
ABSTRACT_PATTERN_CLASS_TOO_MANY_TOKENS: str = "too-many-tokens"
ABSTRACT_PATTERN_CLASS_SINGLETON: str = "singleton"
ABSTRACT_PATTERN_CLASS_DISTINCT: str = "all-distinct"
ABSTRACT_PATTERN_CLASS_REPEATED: str = "repeated"
ABSTRACT_PATTERN_CLASS_RECURRING: str = "recurring-form"
ABSTRACT_PATTERN_CLASS_PARTIAL: str = "partial-recurring"

_VALID_CLASSES: frozenset[str] = frozenset(
    {
        ABSTRACT_PATTERN_CLASS_EMPTY,
        ABSTRACT_PATTERN_CLASS_OVERLONG,
        ABSTRACT_PATTERN_CLASS_NON_PRINTABLE,
        ABSTRACT_PATTERN_CLASS_TOO_MANY_TOKENS,
        ABSTRACT_PATTERN_CLASS_SINGLETON,
        ABSTRACT_PATTERN_CLASS_DISTINCT,
        ABSTRACT_PATTERN_CLASS_REPEATED,
        ABSTRACT_PATTERN_CLASS_RECURRING,
        ABSTRACT_PATTERN_CLASS_PARTIAL,
    }
)


# ---------------------------------------------------------------------------
# Frozen record.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AbstractPatternSignature:
    """A bounded structural-form signature derived from a text input.

    Fields:

    * ``token_count`` — number of whitespace-delimited tokens.
    * ``distinct_token_count`` — number of distinct tokens.
    * ``shape`` — the form letters joined by spaces; e.g. "A B A B".
    * ``classification`` — closed string class label.
    * ``valid`` — True iff the input was bounded and printable.
    * ``digest_hex16`` — first 16 hex chars of sha256 over the
      canonical serialization of (classification, shape).
    * ``explanation`` — bounded printable summary line (no forbidden
      terms).
    """

    token_count: int
    distinct_token_count: int
    shape: str
    classification: str
    valid: bool
    digest_hex16: str
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.token_count, int) or self.token_count < 0:
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "token_count must be a non-negative int"
            )
        if (
            not isinstance(self.distinct_token_count, int)
            or self.distinct_token_count < 0
        ):
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "distinct_token_count must be a non-negative int"
            )
        if self.distinct_token_count > self.token_count:
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "distinct_token_count cannot exceed token_count"
            )
        if not isinstance(self.shape, str) or len(self.shape) > (
            ABSTRACT_PATTERN_SHAPE_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                f"shape must be a string under {ABSTRACT_PATTERN_SHAPE_MAX_LEN} "
                "chars"
            )
        if self.shape and not self.shape.isprintable():
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "shape must be printable"
            )
        if self.classification not in _VALID_CLASSES:
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                f"classification must be in {sorted(_VALID_CLASSES)!r}"
            )
        if not isinstance(self.valid, bool):
            raise TypeError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "valid must be bool"
            )
        if (
            not isinstance(self.digest_hex16, str)
            or len(self.digest_hex16) != ABSTRACT_PATTERN_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "digest_hex16 must be a 16-char hex string"
            )
        if (
            not isinstance(self.explanation, str)
            or len(self.explanation) > ABSTRACT_PATTERN_EXPLANATION_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "explanation must be a bounded string under "
                f"{ABSTRACT_PATTERN_EXPLANATION_MAX_LEN} chars"
            )
        if self.explanation and not self.explanation.isprintable():
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                "explanation must be printable"
            )
        term = _text_has_forbidden_term(self.explanation)
        if term is not None:
            raise ValueError(
                "I-AGENTLEARN-01 violated: AbstractPatternSignature."
                f"explanation contains forbidden non-claim term {term!r}"
            )


# ---------------------------------------------------------------------------
# Core derivation.
# ---------------------------------------------------------------------------


def _compute_shape_and_distinct(
    tokens: tuple[str, ...],
) -> tuple[str, int]:
    """Return (shape_string, distinct_count) for the bounded tokens.

    Assigns letters A, B, C, ... in first-seen order. Distinct token
    count beyond 26 reuses the last label suffixed with a numeric
    index so the shape remains printable; but the bounded constant
    ``ABSTRACT_PATTERN_MAX_TOKENS=32`` keeps the index small.
    """
    seen: dict[str, str] = {}
    labels: list[str] = []
    next_idx = 0
    for tok in tokens:
        label = seen.get(tok)
        if label is None:
            if next_idx < len(_SHAPE_LABELS):
                label = _SHAPE_LABELS[next_idx]
            else:
                # Beyond Z; safe printable suffix label.
                label = f"Z{next_idx - len(_SHAPE_LABELS) + 1}"
            seen[tok] = label
            next_idx += 1
        labels.append(label)
    shape = " ".join(labels)
    return shape, len(seen)


def _classify(
    token_count: int,
    distinct_token_count: int,
    tokens: tuple[str, ...],
) -> str:
    if token_count == 0:
        return ABSTRACT_PATTERN_CLASS_EMPTY
    if token_count == 1:
        return ABSTRACT_PATTERN_CLASS_SINGLETON
    if distinct_token_count == token_count:
        return ABSTRACT_PATTERN_CLASS_DISTINCT
    if distinct_token_count == 1:
        return ABSTRACT_PATTERN_CLASS_REPEATED
    # Detect a strictly-recurring form: every distinct label appears
    # more than once. (E.g. ABAB qualifies; ABAC does not because C
    # appears only once.)
    counts: dict[str, int] = {}
    for tok in tokens:
        counts[tok] = counts.get(tok, 0) + 1
    if all(c > 1 for c in counts.values()):
        return ABSTRACT_PATTERN_CLASS_RECURRING
    return ABSTRACT_PATTERN_CLASS_PARTIAL


def _compute_digest(classification: str, shape: str) -> str:
    payload = f"{classification}|{shape}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        : ABSTRACT_PATTERN_DIGEST_HEX_LEN
    ]


def _bounded_explanation(
    *,
    token_count: int,
    distinct_token_count: int,
    classification: str,
    shape: str,
) -> str:
    line = (
        f"abstract-pattern tokens={token_count} "
        f"distinct={distinct_token_count} "
        f"shape={shape!r} class={classification}"
    )
    if len(line) > ABSTRACT_PATTERN_EXPLANATION_MAX_LEN:
        line = line[: ABSTRACT_PATTERN_EXPLANATION_MAX_LEN - 4] + " ..."
    return line


def derive_abstract_pattern_signature(text: str) -> AbstractPatternSignature:
    """Pure deterministic derivation of an abstract-pattern signature.

    Two invocations on the same input produce equal records.
    """
    if not isinstance(text, str):
        raise TypeError(
            "I-AGENTLEARN-01 violated: derive_abstract_pattern_signature "
            "text must be a string"
        )
    # Bounded-invalid classes.
    if text == "":
        classification = ABSTRACT_PATTERN_CLASS_EMPTY
        shape = ""
        digest = _compute_digest(classification, shape)
        return AbstractPatternSignature(
            token_count=0,
            distinct_token_count=0,
            shape=shape,
            classification=classification,
            valid=False,
            digest_hex16=digest,
            explanation=_bounded_explanation(
                token_count=0,
                distinct_token_count=0,
                classification=classification,
                shape=shape,
            ),
        )
    if len(text) > ABSTRACT_PATTERN_MAX_INPUT_LEN:
        classification = ABSTRACT_PATTERN_CLASS_OVERLONG
        shape = ""
        digest = _compute_digest(classification, shape)
        return AbstractPatternSignature(
            token_count=0,
            distinct_token_count=0,
            shape=shape,
            classification=classification,
            valid=False,
            digest_hex16=digest,
            explanation=_bounded_explanation(
                token_count=0,
                distinct_token_count=0,
                classification=classification,
                shape=shape,
            ),
        )
    if not text.isprintable() and not (
        "\n" in text or "\t" in text
    ):
        classification = ABSTRACT_PATTERN_CLASS_NON_PRINTABLE
        shape = ""
        digest = _compute_digest(classification, shape)
        return AbstractPatternSignature(
            token_count=0,
            distinct_token_count=0,
            shape=shape,
            classification=classification,
            valid=False,
            digest_hex16=digest,
            explanation=_bounded_explanation(
                token_count=0,
                distinct_token_count=0,
                classification=classification,
                shape=shape,
            ),
        )

    # Tokenize on whitespace; cap at ABSTRACT_PATTERN_MAX_TOKENS.
    raw_tokens = tuple(text.split())
    if len(raw_tokens) == 0:
        # Whitespace-only string; treat as empty for the purposes of
        # the abstract form.
        classification = ABSTRACT_PATTERN_CLASS_EMPTY
        shape = ""
        digest = _compute_digest(classification, shape)
        return AbstractPatternSignature(
            token_count=0,
            distinct_token_count=0,
            shape=shape,
            classification=classification,
            valid=False,
            digest_hex16=digest,
            explanation=_bounded_explanation(
                token_count=0,
                distinct_token_count=0,
                classification=classification,
                shape=shape,
            ),
        )

    if len(raw_tokens) > ABSTRACT_PATTERN_MAX_TOKENS:
        classification = ABSTRACT_PATTERN_CLASS_TOO_MANY_TOKENS
        shape = ""
        digest = _compute_digest(classification, shape)
        return AbstractPatternSignature(
            token_count=len(raw_tokens),
            distinct_token_count=0,
            shape=shape,
            classification=classification,
            valid=False,
            digest_hex16=digest,
            explanation=_bounded_explanation(
                token_count=len(raw_tokens),
                distinct_token_count=0,
                classification=classification,
                shape=shape,
            ),
        )

    # Case-fold tokens so "Red Blue Red" maps to the same shape as
    # "red blue red". The shape is structural, not surface-textual.
    tokens = tuple(tok.lower() for tok in raw_tokens)
    shape, distinct = _compute_shape_and_distinct(tokens)
    classification = _classify(len(tokens), distinct, tokens)
    digest = _compute_digest(classification, shape)
    return AbstractPatternSignature(
        token_count=len(tokens),
        distinct_token_count=distinct,
        shape=shape,
        classification=classification,
        valid=True,
        digest_hex16=digest,
        explanation=_bounded_explanation(
            token_count=len(tokens),
            distinct_token_count=distinct,
            classification=classification,
            shape=shape,
        ),
    )


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    ABSTRACT_PATTERN_MODULE_VERSION,
    ABSTRACT_PATTERN_CLASS_EMPTY,
    ABSTRACT_PATTERN_CLASS_OVERLONG,
    ABSTRACT_PATTERN_CLASS_NON_PRINTABLE,
    ABSTRACT_PATTERN_CLASS_TOO_MANY_TOKENS,
    ABSTRACT_PATTERN_CLASS_SINGLETON,
    ABSTRACT_PATTERN_CLASS_DISTINCT,
    ABSTRACT_PATTERN_CLASS_REPEATED,
    ABSTRACT_PATTERN_CLASS_RECURRING,
    ABSTRACT_PATTERN_CLASS_PARTIAL,
)


__all__ = (
    "ABSTRACT_PATTERN_CLASS_DISTINCT",
    "ABSTRACT_PATTERN_CLASS_EMPTY",
    "ABSTRACT_PATTERN_CLASS_NON_PRINTABLE",
    "ABSTRACT_PATTERN_CLASS_OVERLONG",
    "ABSTRACT_PATTERN_CLASS_PARTIAL",
    "ABSTRACT_PATTERN_CLASS_RECURRING",
    "ABSTRACT_PATTERN_CLASS_REPEATED",
    "ABSTRACT_PATTERN_CLASS_SINGLETON",
    "ABSTRACT_PATTERN_CLASS_TOO_MANY_TOKENS",
    "ABSTRACT_PATTERN_DIGEST_HEX_LEN",
    "ABSTRACT_PATTERN_EXPLANATION_MAX_LEN",
    "ABSTRACT_PATTERN_MAX_INPUT_LEN",
    "ABSTRACT_PATTERN_MAX_TOKENS",
    "ABSTRACT_PATTERN_MODULE_VERSION",
    "ABSTRACT_PATTERN_SHAPE_MAX_LEN",
    "AbstractPatternSignature",
    "MODULE_PRODUCED_STRINGS",
    "derive_abstract_pattern_signature",
)
