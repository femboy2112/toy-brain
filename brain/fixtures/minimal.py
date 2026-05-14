"""Minimal fixture.

Drives (per catalog roster):
  I-PROF-01, I-PROF-02, I-MSI-03, I-MSI-04, I-MSI-06,
  I-PTC-02, I-PTC-03, I-PRES-01..05.

Builds the simplest valid (profile, msi, ptcns, preservation_ranking)
quartet: cogito + two ordinary contents above threshold.
"""
from __future__ import annotations

from fractions import Fraction

from brain.invariants import register
from brain.tlica.builders import make_msi, make_profile_with_cogito, make_ptcns
from brain.tlica.preservation import PreservationRanking
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval
from brain.validation import assert_partition, assert_subset_rank_le


def _make_world():
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "a": "3/4",
        "b": "7/10",
    })
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("a"), ContentID("b")},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi=msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "a": ConsistencyEval.PRESERVE,
            "b": ConsistencyEval.DAMAGE,
        },
    )
    pi = PreservationRanking(msi=msi)
    return profile, msi, ptcns, pi


@register("I-PROF-01")
def check_I_PROF_01() -> None:
    """toFun_nonneg: every profile value is >= 0."""
    profile, _, _, _ = _make_world()
    for k, v in profile.values.items():
        assert v >= 0, f"value for {k!r} is {v}, must be >= 0"


@register("I-PROF-02")
def check_I_PROF_02() -> None:
    """toFun_le_one: every profile value is <= 1."""
    profile, _, _, _ = _make_world()
    for k, v in profile.values.items():
        assert v <= 1, f"value for {k!r} is {v}, must be <= 1"


@register("I-MSI-03")
def check_I_MSI_03() -> None:
    """density (Axiom 3.3.3): every non-cogito MSI member meets threshold."""
    _, msi, _, _ = _make_world()
    for c in msi.contents:
        if c == COGITO_ID:
            continue
        v = msi.profile.values[c]
        assert v >= msi.threshold, (
            f"non-cogito MSI member {c!r} has value {v} below threshold {msi.threshold}"
        )


@register("I-MSI-04")
def check_I_MSI_04() -> None:
    """threshold_pos + threshold_lt_one: 0 < threshold < 1."""
    _, msi, _, _ = _make_world()
    assert 0 < msi.threshold < 1, f"threshold {msi.threshold} not in (0, 1)"


@register("I-MSI-06")
def check_I_MSI_06() -> None:
    """mem_msi_positive: every MSI member has strictly positive profile value."""
    _, msi, _, _ = _make_world()
    for c in msi.contents:
        v = msi.profile.values[c]
        assert v > 0, f"MSI member {c!r} has value {v}, not strictly positive"


@register("I-PTC-02")
def check_I_PTC_02() -> None:
    """partition_disjoint: the three eval classes are pairwise disjoint."""
    _, _, ptcns, _ = _make_world()
    # Reuse the shared helper; it raises with a precise message.
    assert_partition(
        pos=ptcns.positive_contents,
        neg=ptcns.negative_contents,
        neu=ptcns.neutral_contents,
        domain=ptcns.msi.profile.domain,
    )


@register("I-PTC-03")
def check_I_PTC_03() -> None:
    """partition_cover: the three eval classes cover the profile domain."""
    _, _, ptcns, _ = _make_world()
    union = ptcns.positive_contents | ptcns.negative_contents | ptcns.neutral_contents
    assert union == ptcns.msi.profile.domain, (
        f"partition_cover failed: union {union!r} != domain {ptcns.msi.profile.domain!r}"
    )


@register("I-PRES-01")
def check_I_PRES_01() -> None:
    """rank_nonneg: every set's rank is non-negative."""
    _, msi, _, pi = _make_world()
    test_sets: list[frozenset[ContentID]] = [
        frozenset(),
        frozenset({COGITO_ID}),
        msi.contents,
        frozenset({ContentID("a")}),
        frozenset({COGITO_ID, ContentID("a")}),
    ]
    for S in test_sets:
        assert pi.rank(S) >= 0, f"rank({S!r}) = {pi.rank(S)}, must be >= 0"


@register("I-PRES-02")
def check_I_PRES_02() -> None:
    """cogito_necessity (Axiom 4.3.1): rank > 0 ⇒ COGITO_ID ∈ S."""
    _, msi, _, pi = _make_world()
    test_sets: list[frozenset[ContentID]] = [
        frozenset(),
        frozenset({COGITO_ID}),
        msi.contents,
        frozenset({ContentID("a")}),
        frozenset({ContentID("b")}),
        frozenset({COGITO_ID, ContentID("a")}),
    ]
    for S in test_sets:
        if pi.rank(S) > 0:
            assert COGITO_ID in S, (
                f"rank({S!r}) = {pi.rank(S)} > 0 but COGITO_ID not in S"
            )


@register("I-PRES-03")
def check_I_PRES_03() -> None:
    """msi_maximality (Axiom 4.3.2): MSI realizes the rank maximum."""
    _, msi, _, pi = _make_world()
    msi_rank = pi.rank(msi.contents)
    test_sets: list[frozenset[ContentID]] = [
        frozenset(),
        frozenset({COGITO_ID}),
        msi.contents,
        frozenset({COGITO_ID, ContentID("a")}),
        frozenset({COGITO_ID, ContentID("b")}),
    ]
    for S in test_sets:
        assert pi.rank(S) <= msi_rank, (
            f"rank({S!r}) = {pi.rank(S)} > rank(msi.contents) = {msi_rank}"
        )


@register("I-PRES-04")
def check_I_PRES_04() -> None:
    """no_cogito_zero_rank: COGITO_ID ∉ S ⇒ rank(S) == 0."""
    _, _, _, pi = _make_world()
    no_cogito: list[frozenset[ContentID]] = [
        frozenset(),
        frozenset({ContentID("a")}),
        frozenset({ContentID("b")}),
        frozenset({ContentID("a"), ContentID("b")}),
    ]
    for S in no_cogito:
        r = pi.rank(S)
        assert r == 0, f"rank({S!r}) = {r} for cogito-less set, must be 0"


@register("I-PRES-05", status="STRUCTURAL")
def check_I_PRES_05() -> None:
    """msi_monotonicity (Axiom 4.3.3): conditional MSI-component monotonicity.

    STRUCTURAL row: holds by construction under the cogito-gated stub;
    the catalog still asks for a sampling-based smoke check.
    """
    _, _, _, pi = _make_world()
    pairs: list[tuple[frozenset[ContentID], frozenset[ContentID]]] = [
        (frozenset({COGITO_ID}), frozenset({COGITO_ID, ContentID("a")})),
        (frozenset({COGITO_ID}), frozenset({COGITO_ID, ContentID("b")})),
        (
            frozenset({COGITO_ID, ContentID("a")}),
            frozenset({COGITO_ID, ContentID("a"), ContentID("b")}),
        ),
    ]
    assert_subset_rank_le(pi.rank, pairs)
