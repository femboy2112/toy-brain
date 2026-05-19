"""Phase 3.22b abstract pattern signature fixture.

Drives ``I-AGENTLEARN-01`` (REQUIRED). Audits
``brain.development.abstract_pattern.derive_abstract_pattern_signature``
for closed-form deterministic structural-form derivation, shape
discrimination across renamed inputs, and bounded-invalid handling.
"""
from __future__ import annotations

from brain.development.abstract_pattern import (
    ABSTRACT_PATTERN_DIGEST_HEX_LEN,
    ABSTRACT_PATTERN_MAX_INPUT_LEN,
    ABSTRACT_PATTERN_MAX_TOKENS,
    AbstractPatternSignature,
    derive_abstract_pattern_signature,
)
from brain.invariants import register


@register("I-AGENTLEARN-01", status="REQUIRED")
def check_abstract_pattern_signature() -> None:
    """Audit the abstract-pattern signature derivation."""

    # 1. Renamed ABAB inputs share digest.
    a = derive_abstract_pattern_signature("red blue red blue")
    b = derive_abstract_pattern_signature("cat dog cat dog")
    assert isinstance(a, AbstractPatternSignature)
    assert a.shape == "A B A B"
    assert a.classification == "recurring-form"
    assert a.digest_hex16 == b.digest_hex16, (
        "I-AGENTLEARN-01 violated: renamed ABAB inputs must share digest"
    )

    # 2. ABBA differs from ABAB.
    abba = derive_abstract_pattern_signature("red blue blue red")
    assert abba.shape == "A B B A"
    assert abba.digest_hex16 != a.digest_hex16

    # 3. AAB differs from ABA.
    aab = derive_abstract_pattern_signature("alpha alpha beta")
    aba = derive_abstract_pattern_signature("alpha beta alpha")
    assert aab.shape == "A A B"
    assert aba.shape == "A B A"
    assert aab.digest_hex16 != aba.digest_hex16

    # 4. Determinism: two calls on the same text produce equal records.
    again = derive_abstract_pattern_signature("red blue red blue")
    assert again == a

    # 5. Bounded-invalid classes.
    empty = derive_abstract_pattern_signature("")
    assert empty.classification == "empty"
    assert empty.valid is False
    assert empty.token_count == 0

    overlong = derive_abstract_pattern_signature(
        "x" * (ABSTRACT_PATTERN_MAX_INPUT_LEN + 1)
    )
    assert overlong.classification == "overlong"
    assert overlong.valid is False

    too_many = derive_abstract_pattern_signature(
        " ".join(["w"] * (ABSTRACT_PATTERN_MAX_TOKENS + 1))
    )
    assert too_many.classification == "too-many-tokens"
    assert too_many.valid is False

    # 6. Singleton / repeated / all-distinct classifications.
    singleton = derive_abstract_pattern_signature("alpha")
    assert singleton.classification == "singleton"
    assert singleton.shape == "A"
    repeated = derive_abstract_pattern_signature("x x x")
    assert repeated.classification == "repeated"
    assert repeated.shape == "A A A"
    distinct = derive_abstract_pattern_signature("one two three four")
    assert distinct.classification == "all-distinct"

    # 7. Digest format.
    assert len(a.digest_hex16) == ABSTRACT_PATTERN_DIGEST_HEX_LEN

    # 8. Explanation is bounded printable.
    assert a.explanation
    assert a.explanation.isprintable()
