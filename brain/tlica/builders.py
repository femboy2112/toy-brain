"""Construction-time entry points. Raises ValueError on invalid input.

The dataclasses themselves also raise (corrigenda C1) — builders exist on
top to:
  - normalize friendlier input shapes (e.g., ``Fraction(str(v))`` for floats),
  - combine field-level checks into atomic operations,
  - emit axiom-tagged error messages.

Catalog rows owned: I-RT-06 (cross-cutting; builders fail loudly on
invalid construction).

Dependency rule: ``builders → validation`` only. **No imports from
``brain.invariants``.**
"""
from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import Any, Mapping

from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.ptcns import ConsistencyEval, PtCns


def rho(value: int | float | str | Fraction) -> Fraction:
    """Normalize a value to ``Fraction`` and raise if outside ``[0, 1]``.

    - ``int``/``Fraction``: passed through directly.
    - ``float``: normalized via ``Fraction(str(value))`` (M7 confirmed) to
      avoid the binary-drift surprise of ``Fraction(0.1)`` returning
      ``Fraction(3602879701896397, 36028797018963968)``.
    - ``str``: parsed by ``Fraction(value)`` (supports ``"1/2"``, ``"0.5"``).

    Never silently clamps — out-of-range raises ``ValueError``. This is
    the construction-time enforcement of I-PROF-01/02 at the I/O boundary
    and the canonical entry point for ``brain/io_types.PerceptEvent``.
    """
    if isinstance(value, Fraction):
        v = value
    elif isinstance(value, bool):
        # bool is an int subclass; reject to avoid accidental coercion.
        raise TypeError("rho() refuses bool input; pass int(0) or int(1) explicitly")
    elif isinstance(value, int):
        v = Fraction(value)
    elif isinstance(value, float):
        v = Fraction(str(value))
    elif isinstance(value, str):
        v = Fraction(value)
    else:
        raise TypeError(
            f"rho() accepts int|float|str|Fraction, got {type(value).__name__}"
        )
    if v < 0 or v > 1:
        raise ValueError(
            f"rho() input {value!r} normalizes to {v}, outside [0, 1]"
        )
    return v


def make_profile_with_cogito(
    values: Mapping[ContentID, Any] | Mapping[str, Any],
) -> ScalarProfile:
    """Construct a ``ScalarProfile`` with COGITO_ID anchored at value 1.

    All values are normalized via ``rho``; ``COGITO_ID`` must be present
    and equal to ``Fraction(1)`` after normalization (I-MSI-01 at
    construction time, by the time MSI wraps the profile).
    """
    if COGITO_ID not in values:
        raise ValueError(
            f"make_profile_with_cogito: COGITO_ID ({COGITO_ID!r}) "
            f"must be present in values"
        )
    normalized: dict[ContentID, Fraction] = {}
    for k, v in values.items():
        if not isinstance(k, str):
            raise TypeError(f"profile keys must be str (got {type(k).__name__})")
        normalized[ContentID(k)] = rho(v)
    if normalized[COGITO_ID] != Fraction(1):
        raise ValueError(
            "I-MSI-01 violated (cogito_value): "
            f"COGITO_ID value normalizes to {normalized[COGITO_ID]}, must be 1"
        )
    domain = frozenset(normalized.keys())
    return ScalarProfile(domain=domain, values=MappingProxyType(normalized))


def make_msi(
    profile: ScalarProfile,
    contents: frozenset[ContentID] | set[ContentID] | set[str],
    threshold: int | float | str | Fraction,
) -> MSI:
    """Construct an ``MSI`` wrapping the supplied profile.

    Enforces I-MSI-02, I-MSI-03, I-MSI-04 explicitly (the dataclass also
    does, but the builder gives a sharper error path).
    """
    threshold_f = (
        threshold if isinstance(threshold, Fraction)
        else rho(threshold)  # same [0,1] normalization, plus the open-interval check below
    )
    if not (Fraction(0) < threshold_f < Fraction(1)):
        raise ValueError(
            "I-MSI-04 violated (threshold_pos / threshold_lt_one): "
            f"threshold {threshold_f} must lie strictly in (0, 1)"
        )
    contents_f = frozenset(ContentID(c) if isinstance(c, str) else c for c in contents)
    if COGITO_ID not in contents_f:
        raise ValueError(
            "I-MSI-02 violated (cogito_in / Axiom 3.3.1): "
            f"COGITO_ID ({COGITO_ID!r}) must be in contents"
        )
    return MSI(profile=profile, contents=contents_f, threshold=threshold_f)


def make_ptcns(
    msi: MSI,
    eval_map: Mapping[ContentID, ConsistencyEval] | Mapping[str, ConsistencyEval],
) -> PtCns:
    """Construct a ``PtCns`` over an MSI's profile domain.

    Enforces I-PTC-01 and totality over the profile domain explicitly.
    """
    normalized: dict[ContentID, ConsistencyEval] = {}
    for k, v in eval_map.items():
        if not isinstance(v, ConsistencyEval):
            raise TypeError(
                f"eval_map[{k!r}] must be ConsistencyEval (got {type(v).__name__})"
            )
        normalized[ContentID(k) if isinstance(k, str) else k] = v
    domain = msi.profile.domain
    if set(normalized.keys()) != domain:
        missing = domain - set(normalized.keys())
        extra = set(normalized.keys()) - domain
        raise ValueError(
            "make_ptcns: eval_map must cover msi.profile.domain exactly "
            f"(missing={sorted(missing)!r}, extra={sorted(extra)!r})"
        )
    if normalized.get(COGITO_ID) is not ConsistencyEval.PRESERVE:
        raise ValueError(
            "I-PTC-01 violated (cogito_invariance / Axiom 7.3.1): "
            f"eval_map[COGITO_ID] = {normalized.get(COGITO_ID)!r}, "
            "must be ConsistencyEval.PRESERVE"
        )
    return PtCns(msi=msi, eval_map=MappingProxyType(normalized))
