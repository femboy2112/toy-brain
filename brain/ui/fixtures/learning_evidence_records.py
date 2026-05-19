"""Phase 3.22b learning evidence record bounds fixture.

Drives ``I-AGENTLEARN-03`` (REQUIRED). Audits the constructor
discipline of ``LearningEvidenceRecord`` and ``LearningEvidenceTrace``.
"""
from __future__ import annotations

from brain.development.abstract_pattern import derive_abstract_pattern_signature
from brain.development.learning_evidence import (
    LEARNING_FACTS_MAX_ENTRIES,
    LEARNING_FACT_KEY_MAX_LEN,
    LEARNING_FACT_VALUE_MAX_LEN,
    LEARNING_INTERACTION_ID_MAX_LEN,
    LEARNING_RECORD_SUMMARY_MAX_LEN,
    LEARNING_TRACE_MAX_RECORDS,
    LearningEvidenceKind,
    LearningEvidenceRecord,
    LearningEvidenceTrace,
    append_record,
    empty_trace,
    make_abstract_pattern_acquired_record,
)
from brain.invariants import register


@register("I-AGENTLEARN-03", status="REQUIRED")
def check_learning_evidence_record_bounds() -> None:
    """Audit LearningEvidenceRecord + LearningEvidenceTrace bounds."""
    sig = derive_abstract_pattern_signature("alpha beta alpha")
    base = make_abstract_pattern_acquired_record(
        interaction_id="agent-input:00001",
        signature=sig,
        pattern_id="pid:abc",
    )
    assert isinstance(base, LearningEvidenceRecord)
    assert base.kind is LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED

    # 1. interaction_id bounds.
    raised = False
    try:
        LearningEvidenceRecord(
            kind=LearningEvidenceKind.OBSERVED,
            interaction_id="",
            abstract_pattern_digest=sig.digest_hex16,
            pattern_id="pid:abc",
            pre_facts=(),
            post_facts=(),
            summary="x",
        )
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 2. abstract_pattern_digest must be empty or 16-char hex.
    raised = False
    try:
        LearningEvidenceRecord(
            kind=LearningEvidenceKind.OBSERVED,
            interaction_id="agent-input:00001",
            abstract_pattern_digest="bad-length",
            pattern_id="pid:abc",
            pre_facts=(),
            post_facts=(),
            summary="x",
        )
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 3. Summary bound.
    raised = False
    try:
        LearningEvidenceRecord(
            kind=LearningEvidenceKind.OBSERVED,
            interaction_id="agent-input:00001",
            abstract_pattern_digest=sig.digest_hex16,
            pattern_id="pid:abc",
            pre_facts=(),
            post_facts=(),
            summary="x" * (LEARNING_RECORD_SUMMARY_MAX_LEN + 1),
        )
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 4. pre_facts bound.
    raised = False
    try:
        LearningEvidenceRecord(
            kind=LearningEvidenceKind.OBSERVED,
            interaction_id="agent-input:00001",
            abstract_pattern_digest=sig.digest_hex16,
            pattern_id="pid:abc",
            pre_facts=tuple(("k", "v") for _ in range(LEARNING_FACTS_MAX_ENTRIES + 1)),
            post_facts=(),
            summary="x",
        )
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 5. LearningEvidenceTrace bounded ledger: appending past
    # LEARNING_TRACE_MAX_RECORDS drops the oldest record (FIFO).
    trace = empty_trace()
    for i in range(LEARNING_TRACE_MAX_RECORDS):
        rec = make_abstract_pattern_acquired_record(
            interaction_id=f"agent-input:{i:05d}",
            signature=sig,
            pattern_id=f"pid:{i}",
        )
        trace = append_record(trace, rec)
    assert len(trace.records) == LEARNING_TRACE_MAX_RECORDS
    # Append one more.
    extra = make_abstract_pattern_acquired_record(
        interaction_id="agent-input:overflow",
        signature=sig,
        pattern_id="pid:overflow",
    )
    trace = append_record(trace, extra)
    assert len(trace.records) == LEARNING_TRACE_MAX_RECORDS
    assert trace.records[-1].interaction_id == "agent-input:overflow"
    assert trace.records[0].interaction_id == "agent-input:00001"
