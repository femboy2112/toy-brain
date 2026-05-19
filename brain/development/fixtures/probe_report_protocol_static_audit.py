"""Phase 3.32 ProbeReport protocol static audit (I-PROBE-01).

Verifies the contract that the Phase 3.34 developmental progression
profile projector depends on:

1. ``brain/development/probe_report_protocol.py`` exists with the
   ``@runtime_checkable`` :class:`ProbeReport` Protocol class and the
   :func:`collect_probe_reports` adapter.
2. The protocol declares the four documented attributes:
   ``digest_hex16``, ``false_positive_count``, ``false_negative_count``,
   ``module_name``.
3. Each existing probe report dataclass has the expected
   ``module_name`` class-level constant and exposes the four
   protocol attributes (as annotations or class attributes).
4. Each existing probe report dataclass's ``__slots__`` does NOT
   contain ``module_name`` (so the ClassVar addition did not change
   instance-field layout).
5. The protocol module's import set is closed: ``__future__`` plus
   ``typing`` only at module-import time.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import brain.development.probe_report_protocol as _protocol
from brain.development.active_hypothesis_probe import (
    ActiveHypothesisLiveTestReport,
)
from brain.development.curriculum_consolidation_probe import (
    CurriculumConsolidationReport,
)
from brain.development.osmotic_learning_probe import OsmoticLiveTestReport
from brain.development.probe_report_protocol import (
    ProbeReport,
    collect_probe_reports,
)
from brain.development.proto_speech_acquisition import (
    ProtoSpeechAcquisitionReport,
)
from brain.invariants import register


_PROTOCOL_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "probe_report_protocol.py"
)


_EXPECTED_MODULE_NAMES: dict[type, str] = {
    ProtoSpeechAcquisitionReport: "proto_speech_acquisition",
    CurriculumConsolidationReport: "curriculum_consolidation_probe",
    ActiveHypothesisLiveTestReport: "active_hypothesis_probe",
    OsmoticLiveTestReport: "osmotic_learning_probe",
}


_REQUIRED_PROTOCOL_ATTRS: tuple[str, ...] = (
    "digest_hex16",
    "false_positive_count",
    "false_negative_count",
    "module_name",
)


_ALLOWED_PROTOCOL_IMPORT_MODULES: frozenset[str] = frozenset({
    "__future__",
    "typing",
})


@register("I-PROBE-01", status="STRUCTURAL")
def check_probe_report_protocol_static_audit() -> None:
    """Static audit on ``brain/development/probe_report_protocol.py``."""

    # 1. Protocol class exists, is runtime_checkable, declares the four
    # documented attributes by annotation.
    assert inspect.isclass(ProbeReport), (
        "I-PROBE-01 violated: ProbeReport must be a class"
    )
    assert getattr(ProbeReport, "_is_runtime_protocol", False), (
        "I-PROBE-01 violated: ProbeReport must be "
        "@runtime_checkable"
    )
    protocol_annotations = ProbeReport.__annotations__
    for attr in _REQUIRED_PROTOCOL_ATTRS:
        assert attr in protocol_annotations, (
            f"I-PROBE-01 violated: ProbeReport missing required "
            f"annotation {attr!r}"
        )

    # 2. collect_probe_reports() is callable, returns a tuple of the
    # expected length, and every entry satisfies the protocol at runtime.
    assert callable(collect_probe_reports), (
        "I-PROBE-01 violated: collect_probe_reports must be "
        "callable"
    )
    reports = collect_probe_reports()
    assert isinstance(reports, tuple), (
        "I-PROBE-01 violated: collect_probe_reports must return "
        "a tuple"
    )
    assert len(reports) == 4, (
        "I-PROBE-01 violated: collect_probe_reports must return "
        f"exactly 4 reports, got {len(reports)}"
    )
    for r in reports:
        assert isinstance(r, ProbeReport), (
            f"I-PROBE-01 violated: report {r!r} does not satisfy "
            f"ProbeReport protocol"
        )

    # 3. Each probe report class has the expected module_name constant
    # and the four protocol attributes (as annotation or class attribute).
    for cls, expected_name in _EXPECTED_MODULE_NAMES.items():
        assert getattr(cls, "module_name", None) == expected_name, (
            f"I-PROBE-01 violated: {cls.__name__}.module_name = "
            f"{getattr(cls, 'module_name', None)!r}, expected "
            f"{expected_name!r}"
        )
        for attr in _REQUIRED_PROTOCOL_ATTRS:
            present = attr in cls.__annotations__ or hasattr(cls, attr)
            assert present, (
                f"I-PROBE-01 violated: {cls.__name__} missing "
                f"required ProbeReport attribute {attr!r}"
            )

    # 4. module_name must be a ClassVar (NOT an instance field), so
    # __slots__ must not include it.
    for cls in _EXPECTED_MODULE_NAMES:
        assert "module_name" not in cls.__slots__, (
            f"I-PROBE-01 violated: {cls.__name__}.__slots__ "
            f"contains 'module_name' (must be ClassVar, not instance "
            f"field)"
        )

    # 5. Reports are deterministic — two collects produce equal
    # digest_hex16 per report in the documented order.
    reports_a = collect_probe_reports()
    reports_b = collect_probe_reports()
    assert len(reports_a) == len(reports_b)
    for a, b in zip(reports_a, reports_b):
        assert a.digest_hex16 == b.digest_hex16, (
            f"I-PROBE-01 violated: probe {a.module_name} "
            f"digest non-deterministic across two collects: "
            f"{a.digest_hex16!r} vs {b.digest_hex16!r}"
        )
        assert a.module_name == b.module_name

    # 6. Protocol module's import set is closed: only __future__ and
    # typing at module-import time.
    src = _PROTOCOL_SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    top_level_import_modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top_level_import_modules.add(mod.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                top_level_import_modules.add(alias.name.split(".", 1)[0])
    assert top_level_import_modules <= _ALLOWED_PROTOCOL_IMPORT_MODULES, (
        f"I-PROBE-01 violated: protocol module has unexpected "
        f"top-level imports "
        f"{sorted(top_level_import_modules - _ALLOWED_PROTOCOL_IMPORT_MODULES)!r}"
    )

    # 7. Sanity: the protocol module itself exposes the expected names.
    for name in ("ProbeReport", "collect_probe_reports"):
        assert hasattr(_protocol, name), (
            f"I-PROBE-01 violated: protocol module missing "
            f"public name {name!r}"
        )
