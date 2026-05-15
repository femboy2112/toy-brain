# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below, unless the user gives a more specific instruction.

---

## Current mission

Implement the trace reserved-key micro-hardening mission before Phase 3.1 implementation.

This is a **boundary-hardening implementation task**, not Phase 3 runtime development.

Do **not** implement the Osmotic Chamber or any Phase 3 developmental subsystem.

---

## Why this mission exists

`PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md` decided that trace reserved-key protection must happen before Phase 3.1 implementation.

Reason:

```text
trace reserved-key protection is a trace-envelope boundary issue, not a developmental feature
it predates Phase 3.1
it should be fixed before developmental trace volume increases
```

Current tracer payloads can overwrite reserved envelope fields such as:

```text
type
timestamp_ns
tick_id
```

Phase 3.1 will introduce richer source-tagged developmental trace payloads. The trace seam must reject or protect reserved keys before that happens.

---

## Required source files to read first

Read these before editing:

```text
CURRENT_MISSION.md
README.md
INVARIANT_CATALOG.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
brain/trace.py
brain/fixtures/trace_v1_1.py
brain/invariants.py
tools/catalog.py
```

Do not rely on unstated conversation context. The patch must stand on repo-local files.

---

## Required behavior decision

Use **reject-on-reserved-key** behavior.

When a tracer receives a payload containing reserved envelope keys, it should reject that payload rather than silently allowing overwrite.

Reserved keys:

```text
type
timestamp_ns
tick_id
```

Preferred semantics:

```text
MemoryTracer.record(...) raises ValueError on reserved payload keys.
FileTracer.record(...) raises ValueError on reserved payload keys.
SafeTracer swallows those failures when wrapping a tracer, preserving observation-only semantics.
NullTracer may ignore all payloads without validation.
```

Rationale:

```text
MemoryTracer and FileTracer are concrete trace sinks and should protect their event envelope.
SafeTracer is the observation-only boundary and should prevent trace-sink failures from affecting the kernel.
NullTracer discards everything and need not validate.
```

---

## Required catalog policy

Add one new STRUCTURAL trace row to `INVARIANT_CATALOG.md`.

Recommended ID:

```text
I-TRACE-03
```

Recommended row meaning:

```text
Tracer payloads cannot overwrite reserved event-envelope keys. MemoryTracer and FileTracer reject payloads containing `type`, `timestamp_ns`, or `tick_id`; SafeTracer preserves observation-only behavior by swallowing trace-sink validation failures.
```

Catalog versioning:

```text
Do not start Phase 3 catalog rows yet.
Keep this as a v0.5 micro-hardening completion unless the existing catalog tooling requires a banner/count update.
If adding I-TRACE-03 changes STRUCTURAL count, update the catalog banner and tools EXPECTED_COUNTS consistently.
Do not label this as Phase 3.1 developmental work.
```

Important: keep source kind as `PLAN_CONVENTION` or equivalent plan-convention wording, not `ENGINEERING_HYPOTHESIS`, because this is a trace boundary rule, not a developmental hypothesis.

---

## Required implementation scope

Allowed files for this mission:

```text
brain/trace.py
brain/fixtures/trace_v1_1.py
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
CURRENT_MISSION.md only if absolutely necessary
```

Optional if needed:

```text
brain/invariants.py
README.md
```

But avoid README unless the catalog version/count change requires documentation sync.

Do not modify:

```text
brain/development/
brain/tlica/
brain/tick.py
brain/llm/
lean_reference/
traces/
scenarios/
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
```

---

## Required implementation details

### 1. Add reserved-key helper

In `brain/trace.py`, define a small helper or constant:

```python
_RESERVED_TRACE_KEYS = frozenset({"type", "timestamp_ns", "tick_id"})
```

Add a validator such as:

```python
def _reject_reserved_payload_keys(payload: Mapping[str, Any]) -> None:
    overlap = _RESERVED_TRACE_KEYS & set(payload)
    if overlap:
        raise ValueError(
            "I-TRACE-03 violated: trace payload contains reserved envelope keys "
            f"{sorted(overlap)!r}"
        )
```

### 2. Apply to MemoryTracer and FileTracer

In `MemoryTracer.record(...)` and `FileTracer.record(...)`, call the validator before building/updating the event envelope.

The implementation should ensure payload keys cannot overwrite:

```text
type
timestamp_ns
tick_id
```

### 3. Keep SafeTracer fail-open behavior

`SafeTracer` should continue swallowing exceptions from the wrapped tracer.

A reserved-key failure inside a raw MemoryTracer/FileTracer should raise.

A reserved-key failure inside `SafeTracer(MemoryTracer(...))` or `SafeTracer(FileTracer(...))` should be swallowed and not affect kernel behavior.

### 4. Add fixture coverage

Extend `brain/fixtures/trace_v1_1.py` with a registered check for the new row.

Recommended check:

```python
@register("I-TRACE-03", status="STRUCTURAL")
def check_I_TRACE_03() -> None:
    # raw MemoryTracer rejects reserved keys
    # raw FileTracer rejects reserved keys
    # SafeTracer(raw MemoryTracer) swallows reserved-key failure
    # SafeTracer(raw FileTracer) swallows reserved-key failure
```

Use `tempfile.TemporaryDirectory()` for FileTracer.

Make sure the raised error message contains `I-TRACE-03`.

### 5. Update generated catalog IDs

After catalog row addition:

```bash
python -m tools.catalog generate-ids
```

Commit the generated `brain/_catalog_ids.py` if it changes.

---

## Validation

Run:

```bash
python -m tools.catalog counts
python -m brain.invariants run --id I-TRACE
bash tools/check_all.sh
```

If the runner does not support prefix `--id I-TRACE`, use the exact relevant row IDs individually.

Do **not** run:

```bash
python -m brain.scenario run ...
```

unless explicitly asked.

---

## Git persistence requirement

After validation passes, Codex must commit and push its result.

Rules:

```text
stage only intended mission files
commit with a clear message
push to the current branch / main as appropriate
report the commit SHA
```

Do not commit accidental changes to guarded files.

If there are no changes, Codex should report that no commit was made and explain why.

---

## Final report

When done, report:

```text
Created/updated:
- brain/trace.py
- brain/fixtures/trace_v1_1.py
- INVARIANT_CATALOG.md
- tools/catalog.py if count changed
- brain/_catalog_ids.py if regenerated

Validation:
- python -m tools.catalog counts: ...
- python -m brain.invariants run --id I-TRACE: ...
- bash tools/check_all.sh: ...

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- review trace reserved-key hardening
- then update mission for Phase 3.1 catalog patch / implementation planning
```

---

## Stop condition

Stop after implementing trace reserved-key protection, validating, committing, pushing, and reporting the result.

Do not proceed into Phase 3.1 Osmotic Chamber implementation unless the user gives a new explicit instruction.
