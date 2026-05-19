"""Phase 3.32 ProbeReport protocol.

Header-only :class:`typing.Protocol` plus a deterministic
:func:`collect_probe_reports` adapter. Every existing probe report
dataclass already exposes ``digest_hex16``, ``false_positive_count``,
``false_negative_count`` by name; this module adds ``module_name``
as a ``ClassVar[str]`` constant on each report (the only allowed
modification to existing probe modules in Phase 3.32) and declares
the protocol they satisfy.

Closed import set: ``__future__``, ``typing``. No probe-module
imports at module-import time; :func:`collect_probe_reports` defers
its probe imports to function body so the protocol module does not
couple itself to every probe at import time.

The Phase 3.34 developmental progression profile projector consumes
this protocol so it does not have to import five distinct probe
modules. The protocol intentionally does NOT include probe-specific
counters (``stable_combination_count``, ``survived_count``, ...);
those are accessed via ``getattr()`` with a default in the
projector, keeping the protocol narrow.

This module is header-only typing. It has no runtime side effects
except enabling type-checked consumers.

Catalog row: I-PROTO-PROBE-01 (STRUCTURAL).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProbeReport(Protocol):
    """Common structural shape of every probe report dataclass.

    Every probe's ``*Report`` dataclass exposes these four
    attributes by name; this protocol declares the contract. The
    Phase 3.34 developmental progression profile projector calls
    only these four attributes.
    """

    #: 16-character lowercase hex digest of the probe's canonical
    #: evidence tuple. Bit-identical across runs on equal substrate.
    digest_hex16: str

    #: Number of conditions that emitted a positive outcome where
    #: none was expected (per the runner's acceptance criteria).
    false_positive_count: int

    #: Number of conditions that emitted no PASS where a PASS was
    #: expected (per the runner's acceptance criteria).
    false_negative_count: int

    #: Bounded printable probe identifier. E.g.
    #: ``"proto_speech_acquisition"``, ``"curriculum_consolidation_probe"``,
    #: ``"active_hypothesis_probe"``, ``"osmotic_learning_probe"``.
    #: Used by the projector to dispatch evidence collection.
    module_name: str


def collect_probe_reports() -> tuple[ProbeReport, ...]:
    """Run each probe's canonical live-test and return the reports.

    Deterministic. Bit-identical across runs on equal substrate.
    Return order is fixed:

    1. ``proto_speech_acquisition`` -> :class:`ProtoSpeechAcquisitionReport`
    2. ``curriculum_consolidation_probe`` -> :class:`CurriculumConsolidationReport`
    3. ``active_hypothesis_probe`` -> :class:`ActiveHypothesisLiveTestReport`
    4. ``osmotic_learning_probe`` -> :class:`OsmoticLiveTestReport`

    Probe imports are deferred to function body so this module
    does not couple to every probe at import time.
    """
    from brain.development.proto_speech_acquisition import (
        run_proto_speech_live_test,
    )
    from brain.development.curriculum_consolidation_probe import (
        run_curriculum_consolidation_live_test,
    )
    from brain.development.active_hypothesis_probe import (
        run_active_hypothesis_live_test,
    )
    from brain.development.osmotic_learning_probe import (
        run_osmotic_live_test,
    )
    reports: tuple[ProbeReport, ...] = (
        run_proto_speech_live_test(),
        run_curriculum_consolidation_live_test(),
        run_active_hypothesis_live_test(),
        run_osmotic_live_test(),
    )
    return reports
