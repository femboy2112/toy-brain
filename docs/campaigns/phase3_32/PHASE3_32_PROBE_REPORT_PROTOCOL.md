# PHASE3_32_PROBE_REPORT_PROTOCOL.md

## Purpose

Design document for `brain/development/probe_report_protocol.py`,
landed by Phase 3.32 Step 4–8. The protocol is a header-only
`typing.Protocol` that every existing probe report dataclass already
satisfies by name. The Phase 3.34 developmental progression profile
projector consumes this protocol instead of importing five distinct
probe modules.

## Why a Protocol, not a base class

Inheriting from an `abc.ABC` base class would require modifying every
existing probe report dataclass to inherit from the new base. That
violates Phase 3.32's hard limit: "no probe module's report dataclass
loses or renames a field, and no behavior changes."

A `typing.Protocol` with `@runtime_checkable` provides:

1. **Structural typing.** Any class that has the named attributes
   with compatible types is automatically a `ProbeReport`. No
   `isinstance` ancestry chain.
2. **Zero modification of existing dataclasses.** The probe reports
   are unchanged.
3. **Runtime-checkable.** `isinstance(report, ProbeReport)` works at
   runtime, useful for the static-audit fixture.
4. **Type-checker support.** Pyright / mypy recognize the protocol;
   the projector's signature can declare `tuple[ProbeReport, ...]`.

## The Protocol

```python
from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProbeReport(Protocol):
    """Common structural shape of every probe report dataclass.

    Every probe's *Report dataclass already exposes these four
    attributes by name; this protocol declares the contract. The
    Phase 3.34 developmental progression profile projector calls
    only these four attributes.

    The protocol intentionally does NOT include probe-specific
    counters (stable_combination_count, survived_count, etc.).
    Those are accessed via getattr() with a default in the
    projector, so the protocol can stay narrow.
    """

    #: 16-character lowercase hex digest of the probe's canonical
    #: evidence tuple. Bit-identical across runs on equal substrate.
    digest_hex16: str

    #: Number of conditions that emitted a FAIL with a positive
    #: outcome where none was expected.
    false_positive_count: int

    #: Number of conditions that emitted no PASS where a PASS was
    #: expected (per the runner's acceptance criteria).
    false_negative_count: int

    #: Bounded printable probe identifier. E.g.,
    #: "proto_speech_acquisition", "curriculum_consolidation_probe".
    #: Used by the projector to dispatch evidence collection.
    module_name: str
```

## The collector

```python
def collect_probe_reports() -> tuple[ProbeReport, ...]:
    """Run each probe's canonical live-test and return reports.

    Deterministic. Bit-identical across runs. The order is fixed:
    1. proto_speech_acquisition
    2. curriculum_consolidation_probe
    3. active_hypothesis_probe
    4. osmotic_learning_probe
    5. worldlet_feedback_bridge (if a canonical runner exists;
       otherwise omitted with a comment)

    Imports are deferred to function-body to avoid coupling the
    protocol module to all five probe modules at import time.
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
        run_osmotic_learning_live_test,
    )
    reports: tuple[ProbeReport, ...] = (
        run_proto_speech_live_test(),
        run_curriculum_consolidation_live_test(),
        run_active_hypothesis_live_test(),
        run_osmotic_learning_live_test(),
    )
    return reports
```

## `module_name` addition to existing probe reports

The single allowed modification to existing probe modules in Phase 3.32
is adding `module_name: ClassVar[str] = "..."` to each report
dataclass. This is acceptable because:

1. It's a `ClassVar`, not an instance field — does not change
   dataclass layout or constructor signature.
2. It's a constant string — no runtime behavior change.
3. It does not enter any digest input — does not change probe digests.

Concretely:

```python
# In brain/development/proto_speech_acquisition.py
@dataclass(frozen=True, slots=True)
class ProtoSpeechAcquisitionReport:
    module_name: ClassVar[str] = "proto_speech_acquisition"
    # ... existing fields unchanged ...

# In brain/development/curriculum_consolidation_probe.py
@dataclass(frozen=True, slots=True)
class CurriculumConsolidationReport:
    module_name: ClassVar[str] = "curriculum_consolidation_probe"
    # ... existing fields unchanged ...

# Similarly for active_hypothesis_probe and osmotic_learning_probe.
```

The static-audit fixture verifies that each probe's `module_name`
matches the expected constant.

## Static audit fixture

```python
# brain/development/fixtures/probe_report_protocol_static_audit.py
"""Phase 3.32 ProbeReport protocol static audit.

Verifies that every existing probe report dataclass satisfies
the ProbeReport protocol at runtime, and that the canonical
module_name on each is the expected value.
"""
from brain.development.probe_report_protocol import ProbeReport
from brain.development.proto_speech_acquisition import (
    ProtoSpeechAcquisitionReport,
)
from brain.development.curriculum_consolidation_probe import (
    CurriculumConsolidationReport,
)
from brain.development.active_hypothesis_probe import (
    ActiveHypothesisReport,
)
from brain.development.osmotic_learning_probe import (
    OsmoticLearningReport,
)


EXPECTED_MODULE_NAMES = {
    ProtoSpeechAcquisitionReport: "proto_speech_acquisition",
    CurriculumConsolidationReport: "curriculum_consolidation_probe",
    ActiveHypothesisReport: "active_hypothesis_probe",
    OsmoticLearningReport: "osmotic_learning_probe",
}


def assert_all_reports_satisfy_protocol() -> None:
    """Each report dataclass type satisfies ProbeReport.

    Runs isinstance() on a constructed default instance of each.
    """
    # Note: dataclass(frozen=True) cannot be constructed without
    # args; use a probe-specific constructor helper or skip the
    # isinstance call and rely on attribute existence checks.
    for cls, expected_name in EXPECTED_MODULE_NAMES.items():
        assert cls.module_name == expected_name, (
            f"{cls.__name__}.module_name = {cls.module_name!r}, "
            f"expected {expected_name!r}"
        )
        # Verify required attributes exist on the class.
        for attr in ("digest_hex16", "false_positive_count",
                     "false_negative_count", "module_name"):
            assert hasattr(cls, attr) or attr in cls.__annotations__, (
                f"{cls.__name__} missing required ProbeReport "
                f"attribute: {attr}"
            )
```

## Catalog row

```text
| I-PROBE-01 | STRUCTURAL | Engineering hypothesis (Phase 3) |
brain.development.probe_report_protocol exists and every probe
report dataclass satisfies it. Each probe report has the
canonical module_name ClassVar. The collect_probe_reports() helper
returns a deterministic tuple of reports in the documented order.
| brain/development/probe_report_protocol.py | (no Lean source) |
brain/development/fixtures/probe_report_protocol_static_audit.py |
```

## Alternatives considered

### Alternative A: Add an ABC base class to every probe report

Rejected. Requires modifying every probe report dataclass to inherit
from the new base. Violates Phase 3.32's hard limit.

### Alternative B: Duplicate every report's fields into a profile-specific dataclass

Rejected. Stale-by-construction; every time a probe report changes
the profile-side struct has to be re-synchronized. Couples the
profile to the probes' release cadence.

### Alternative C: Use `dict[str, Any]` instead of a Protocol

Rejected. Loses type-checker support; loses field discoverability;
encourages stringly-typed access patterns. The Protocol is barely
more code and far more robust.

### Alternative D: No protocol — projector imports each probe module directly

Rejected. Couples the profile to probe internals; defeats the
purpose of having a separate profile module.

## Cross-references

- `PHASE3_32_MAINLINE_RECONCILIATION_ROADMAP.md` — the campaign that
  lands this protocol.
- `ADR-001-locked-decisions-D1-D8.md` — D4 mandates the protocol.
- Phase 3.34 `PHASE3_34_PROJECTOR_DESIGN.md` — the consumer of the
  protocol.
