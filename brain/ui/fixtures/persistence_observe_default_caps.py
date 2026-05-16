"""Phase 3.10b locked-default-cap fixture.

Drives:

* ``I-OBSERVE-09`` (STRUCTURAL) — locked default row caps. The
  module-level constants
  ``PROFILE_SUMMARY_ROW_CAP = 64``,
  ``STREAM_DB_SUMMARY_HEAD_CAP = 8``,
  ``STREAM_DB_SUMMARY_TAIL_CAP = 8``,
  ``DB_DIFF_ROW_CAP = 32``,
  ``STREAM_TEXT_PREVIEW_MAX_LEN = 64``,
  ``PROFILE_VALUE_STRING_MAX_LEN = 64``,
  ``OPS_REPORT_TEXT_MAX_LEN = 256``
  are declared in :mod:`brain.ui.persistence_observe`. The fixture
  asserts the values, asserts the helpers default to them, and confirms
  the :data:`OPS_REPORT_TEXT_MAX_LEN` re-export parity with
  :mod:`brain.ui.persistence_ops`.
"""
from __future__ import annotations

import inspect

from brain.invariants import register
from brain.ui import persistence_observe
from brain.ui.persistence_ops import (
    OPS_REPORT_TEXT_MAX_LEN as OPS_REPORT_TEXT_MAX_LEN_FROM_OPS,
)


_EXPECTED_CAPS: dict[str, int] = {
    "PROFILE_SUMMARY_ROW_CAP": 64,
    "STREAM_DB_SUMMARY_HEAD_CAP": 8,
    "STREAM_DB_SUMMARY_TAIL_CAP": 8,
    "DB_DIFF_ROW_CAP": 32,
    "STREAM_TEXT_PREVIEW_MAX_LEN": 64,
    "PROFILE_VALUE_STRING_MAX_LEN": 64,
    "OPS_REPORT_TEXT_MAX_LEN": 256,
}


@register("I-OBSERVE-09", status="STRUCTURAL")
def check_i_observe_09_default_caps() -> None:
    errors: list[str] = []

    # Constant value parity.
    for name, expected in _EXPECTED_CAPS.items():
        if not hasattr(persistence_observe, name):
            errors.append(
                f"persistence_observe missing constant {name!r}"
            )
            continue
        value = getattr(persistence_observe, name)
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(
                f"persistence_observe.{name} is not an int "
                f"(got {type(value).__name__})"
            )
            continue
        if value != expected:
            errors.append(
                f"persistence_observe.{name} = {value!r}; expected "
                f"{expected!r}"
            )

    # OPS_REPORT_TEXT_MAX_LEN must match the persistence_ops definition.
    if persistence_observe.OPS_REPORT_TEXT_MAX_LEN != OPS_REPORT_TEXT_MAX_LEN_FROM_OPS:
        errors.append(
            "OPS_REPORT_TEXT_MAX_LEN parity broken: "
            f"persistence_observe={persistence_observe.OPS_REPORT_TEXT_MAX_LEN!r} "
            f"vs persistence_ops={OPS_REPORT_TEXT_MAX_LEN_FROM_OPS!r}"
        )

    # Helper defaults reference the same module-level constants.
    sig_profile = inspect.signature(persistence_observe.profile_summary)
    row_cap_param = sig_profile.parameters.get("row_cap")
    if row_cap_param is None or row_cap_param.default != persistence_observe.PROFILE_SUMMARY_ROW_CAP:
        errors.append(
            "profile_summary(row_cap=...) default does not match "
            "PROFILE_SUMMARY_ROW_CAP"
        )

    sig_stream = inspect.signature(persistence_observe.stream_db_summary)
    head_cap_param = sig_stream.parameters.get("head_cap")
    tail_cap_param = sig_stream.parameters.get("tail_cap")
    if head_cap_param is None or head_cap_param.default != persistence_observe.STREAM_DB_SUMMARY_HEAD_CAP:
        errors.append(
            "stream_db_summary(head_cap=...) default does not match "
            "STREAM_DB_SUMMARY_HEAD_CAP"
        )
    if tail_cap_param is None or tail_cap_param.default != persistence_observe.STREAM_DB_SUMMARY_TAIL_CAP:
        errors.append(
            "stream_db_summary(tail_cap=...) default does not match "
            "STREAM_DB_SUMMARY_TAIL_CAP"
        )

    sig_diff = inspect.signature(persistence_observe.db_diff)
    diff_cap_param = sig_diff.parameters.get("row_cap")
    if diff_cap_param is None or diff_cap_param.default != persistence_observe.DB_DIFF_ROW_CAP:
        errors.append(
            "db_diff(row_cap=...) default does not match DB_DIFF_ROW_CAP"
        )

    if errors:
        raise AssertionError(
            "I-OBSERVE-09 violated:\n  - " + "\n  - ".join(errors)
        )
