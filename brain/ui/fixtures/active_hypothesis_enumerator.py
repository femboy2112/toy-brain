"""Phase 3.26 enumerator determinism + per-key bucket fixture.

Drives ``I-AHYP-03`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    ACTIVE_HYPOTHESIS_MAX_CANDIDATES,
    ActiveHypothesisCandidate,
    build_active_hypothesis_trials,
    enumerate_hypotheses,
)
from brain.invariants import register


@register("I-AHYP-03", status="REQUIRED")
def check_active_hypothesis_enumerator() -> None:
    """Enumerator is deterministic and bounded; CONTROL inputs yield ()."""
    # Empty + singleton: no candidates.
    assert enumerate_hypotheses("") == ()
    assert enumerate_hypotheses("alpha") == ()

    # Determinism: two calls return equal tuples.
    for input_text in (
        "red blue red",
        "red blue blue",
        "red blue green",
        "red blue red blue",
        "red blue red green",
        "red red",
        "red red blue",
    ):
        a = enumerate_hypotheses(input_text)
        b = enumerate_hypotheses(input_text)
        assert a == b, f"enumerator not deterministic for {input_text!r}"
        assert isinstance(a, tuple)
        for c in a:
            assert isinstance(c, ActiveHypothesisCandidate)
        assert len(a) <= ACTIVE_HYPOTHESIS_MAX_CANDIDATES

    # partial-recurring/3 bucket: every v1 input shares the same
    # candidate-id set drawn from the curated tuple.
    expected_ids = frozenset({
        "H_RENAME_S_ABA",
        "H_RENAME_S_ABB",
        "H_APPEND_POS0_S_ABCA",
        "H_APPEND_NEW_S_ABCD",
    })
    for input_text in ("red blue red", "red blue blue", "red red blue"):
        cands = enumerate_hypotheses(input_text)
        assert len(cands) == 4
        assert frozenset(c.candidate_id for c in cands) == expected_ids

    # repeated/2 bucket: 4 candidates.
    cands = enumerate_hypotheses("red red")
    assert len(cands) == 4
    assert frozenset(c.candidate_id for c in cands) == frozenset({
        "H_RENAME_S_AB",
        "H_APPEND_NEW_S_ABA",
        "H_APPEND_NEW_S_ABC",
        "H_APPEND_POS0_S_ABAA",
    })

    # all-distinct/3 bucket.
    cands = enumerate_hypotheses("red blue green")
    assert len(cands) == 4
    assert frozenset(c.candidate_id for c in cands) == frozenset({
        "H_RENAME_S_ABC",
        "H_RENAME_S_ABA",
        "H_APPEND_NEW_S_ABCD",
        "H_APPEND_POS0_S_ABCA",
    })

    # recurring-form/4 bucket.
    cands = enumerate_hypotheses("red blue red blue")
    assert len(cands) == 4
    assert frozenset(c.candidate_id for c in cands) == frozenset({
        "H_RENAME_S_ABAB",
        "H_RENAME_S_ABCD",
        "H_APPEND_NEW_S_ABABC",
        "H_APPEND_POS0_S_ABABA",
    })

    # Every v1 trial input enumerates a bounded tuple.
    for t in build_active_hypothesis_trials():
        cands = enumerate_hypotheses(t.input_text)
        assert len(cands) <= ACTIVE_HYPOTHESIS_MAX_CANDIDATES
