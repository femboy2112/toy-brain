"""Fixtures for I-PLEDGER-04, I-PLEDGER-05 (signature + deterministic id).

* I-PLEDGER-04 — pattern signatures are structural/non-semantic,
  bounded by ``STREAM_PATTERN_SIG_MAX``, contain no raw text payload
  and no ``COGITO_ID``, and are derived from exact
  ``StreamFeatureVector`` values.
* I-PLEDGER-05 — deterministic pattern id formula
  ``"pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]``.
"""
from __future__ import annotations

from hashlib import sha256

from brain.development.pattern_ledger import (
    PATTERN_LEDGER_SIGNATURE_ELEM_MAX,
    derive_pattern_id,
    derive_pattern_signature,
)
from brain.development.text_stream import (
    STREAM_PATTERN_SIG_MAX,
    TextStreamSource,
    make_text_stream_chunk,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _chunk(
    *,
    chunk_id: str = "c1",
    text: str = "hello world",
    source: TextStreamSource = TextStreamSource.OPERATOR,
    provenance: str = "operator",
):
    return make_text_stream_chunk(
        chunk_id=chunk_id,
        text=text,
        source=source,
        provenance=provenance,
    )


@register("I-PLEDGER-04", status="REQUIRED")
def check_pattern_signature_is_structural() -> None:
    chunk = _chunk(text="alpha beta gamma\nmore text")
    sig = derive_pattern_signature(chunk)

    # Tuple of bounded printable strings, length in [1, SIG_MAX].
    assert isinstance(sig, tuple), (
        f"I-PLEDGER-04 violated: signature is not a tuple (got {type(sig).__name__})"
    )
    assert 1 <= len(sig) <= STREAM_PATTERN_SIG_MAX, (
        f"I-PLEDGER-04 violated: signature length {len(sig)} out of bounds"
    )
    for elem in sig:
        assert isinstance(elem, str) and elem and elem.isprintable(), (
            f"I-PLEDGER-04 violated: signature element {elem!r} is not "
            "bounded printable str"
        )
        assert len(elem) <= PATTERN_LEDGER_SIGNATURE_ELEM_MAX, (
            f"I-PLEDGER-04 violated: signature element length {len(elem)} "
            f"exceeds PATTERN_LEDGER_SIGNATURE_ELEM_MAX="
            f"{PATTERN_LEDGER_SIGNATURE_ELEM_MAX}"
        )
        assert elem != COGITO_ID, (
            "I-PLEDGER-04 violated: signature element equals COGITO_ID"
        )

    # No raw-text payload. The chunk text contains the words "alpha"
    # / "beta" / "gamma" / "more"; none of those substrings must
    # appear inside any signature element.
    raw_tokens = ("alpha", "beta", "gamma", "more")
    for elem in sig:
        for token in raw_tokens:
            assert token not in elem, (
                "I-PLEDGER-04 violated: signature element "
                f"{elem!r} carries raw text token {token!r}"
            )

    # Signature shape: keyed prefixes from extract_stream_features.
    prefixes = ("source:", "len:", "lines:", "ws:", "distinct:", "repeat:")
    for elem, expected_prefix in zip(sig, prefixes):
        assert elem.startswith(expected_prefix), (
            f"I-PLEDGER-04 violated: signature element {elem!r} missing "
            f"expected prefix {expected_prefix!r}"
        )
    # source: value comes from the closed TextStreamSource enum.
    assert sig[0] == "source:operator"
    # Repeated derivation is stable (determinism precondition for
    # I-PLEDGER-05).
    assert derive_pattern_signature(chunk) == sig


@register("I-PLEDGER-05", status="REQUIRED")
def check_pattern_id_is_deterministic() -> None:
    chunk_a = _chunk(text="alpha beta gamma")
    chunk_a_again = _chunk(
        chunk_id="c1-bis",
        text="alpha beta gamma",
        provenance="operator-bis",
    )
    chunk_b = _chunk(text="another line of text\nwith two lines")

    sig_a = derive_pattern_signature(chunk_a)
    sig_a_again = derive_pattern_signature(chunk_a_again)
    sig_b = derive_pattern_signature(chunk_b)

    # Structurally identical chunks (same features) share signatures
    # even when chunk_id / provenance differ.
    assert sig_a == sig_a_again, (
        "I-PLEDGER-05 violated: identical structural chunks produced "
        f"different signatures ({sig_a!r} vs {sig_a_again!r})"
    )
    # Structurally distinct chunks produce distinct signatures.
    assert sig_a != sig_b, (
        "I-PLEDGER-05 violated: structurally distinct chunks produced "
        f"identical signatures ({sig_a!r})"
    )

    pid_a = derive_pattern_id(sig_a)
    pid_a_again = derive_pattern_id(sig_a_again)
    pid_b = derive_pattern_id(sig_b)

    # Deterministic: same signature -> same id.
    assert pid_a == pid_a_again, (
        f"I-PLEDGER-05 violated: deterministic id drift ({pid_a!r} vs "
        f"{pid_a_again!r})"
    )
    # Structurally distinct -> distinct id.
    assert pid_a != pid_b, (
        f"I-PLEDGER-05 violated: distinct signatures produced identical id "
        f"({pid_a!r})"
    )

    # Exact formula: "pledger:" + sha256(repr(signature))[:16].
    expected = "pledger:" + sha256(repr(sig_a).encode("utf-8")).hexdigest()[:16]
    assert pid_a == expected, (
        f"I-PLEDGER-05 violated: id formula drift (got {pid_a!r}, expected "
        f"{expected!r})"
    )

    # Repeated derivation across the same process produces the same
    # bytes (no module-level cache surprises).
    for _ in range(3):
        assert derive_pattern_id(sig_a) == pid_a
