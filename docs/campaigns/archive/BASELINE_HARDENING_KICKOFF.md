# BASELINE_HARDENING_KICKOFF.md — Phase 2 v1.2 (Baseline Hardening)

This document is the implementation spec for a focused hardening pass before any Phase 3 work begins. It patches `INVARIANT_CATALOG.md` from v0.4 to v0.5, adds four STRUCTURAL invariants, fixes five correctness issues, adds two tooling improvements, introduces a `Source Kind` schema field on catalog rows, and syncs README to current state.

This is **not** a feature phase. It is a quality phase. The audit identified specific gaps in the current v0.4 baseline that would compound under Phase 3's ~51 new rows; closing them now keeps the foundation honest before the developmental layer starts to lean on it.

## Status of the project at the time of this kickoff

- Catalog: v0.4, 84 REQUIRED / 11 STRUCTURAL / 3 NOT-EXERCISED / 12 DEFERRED / 1 OBSERVED.
- v0 + Phase 2 v1 + Phase 2 v1.1 (trace) complete on `claude/implement-brain-invariants-4citD` (commits `6bc1187`, `245b301`, `26bb864`).
- 182-event FileTracer JSONL verified on the first scenario; three-backend determinism green.
- The traced behavioral CLI with real API has **not yet been run**.

This kickoff lands as Phase 2 v1.2. After it lands, the next step is the real-API traced behavioral CLI run, then `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md`, then `PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md`.

## Scope summary

**Five correctness patches** (existing-code defects):

| Patch | Issue | Catalog row |
|---|---|---|
| P1 | `FileTracer.record()` can raise and propagate into kernel | + I-TRACE-02 |
| P2 | `tick()` accepts list of events but v1 semantics handle only one | + I-RT-11 |
| P3 | Duplicate `content_id` silently overwrites profile entries | + I-RT-12 |
| P4 | `parse_consistency_eval` ambiguous when multiple valid tokens appear | — (tightens I-LLM-01) |
| P5 | `FutureMSIModel.domain_match` has no runtime guard | — (tightens I-APRJ-01) |

**Two tooling patches**:

| Patch | Issue | Catalog row |
|---|---|---|
| P6 | `tools.catalog counts` returns success on banner mismatch | — |
| P7 | Runner doesn't verify every REQUIRED row has a registered check | + I-CAT-01 |

**One schema patch**:

| Patch | Addition | Catalog row |
|---|---|---|
| P8 | `Source Kind` field on parsed catalog rows (LEAN / PLAN_CONVENTION / ENGINEERING_HYPOTHESIS / OBSERVED / DEFERRED) | — (schema, not row) |

**One documentation patch**:

| Patch | Action |
|---|---|
| P9 | README sync from "v0.2 / 80 REQUIRED" to "v0.5 / 84 REQUIRED + 15 STRUCTURAL" |

## Catalog patch — v0.4 → v0.5

### New rows

```
| I-RT-11 | Plan convention (Phase 2 v1.2 baseline hardening) | tick() rejects events list with length > 1 in v1 semantics. Multi-event mode aggregation is deferred. | tick(state, [e1, e2], client) raises ValueError naming I-RT-11. | scenario_v1.py | STRUCTURAL |

| I-RT-12 | Plan convention (Phase 2 v1.2 baseline hardening) | tick() rejects PerceptEvent whose content_id is already in state.profile.domain. v1 promotion is one-shot per content. | tick(state, [event_with_existing_id], client) raises ValueError naming I-RT-12. | scenario_v1.py | STRUCTURAL |

| I-TRACE-02 | Plan convention (Phase 2 v1.2 baseline hardening) | Tracer record failures do not propagate. tick() output is identical whether tracer.record raises or not. | Run scenario through a TracerThatAlwaysRaises (wrapping each backend); assert BrainState and mode_trace identical to NullTracer baseline. | trace_v1_1.py | STRUCTURAL |

| I-CAT-01 | Plan convention (Phase 2 v1.2 baseline hardening) | Every catalog row with status REQUIRED or STRUCTURAL has a registered check. The runner refuses to claim "all green" if any row is missing registration. | After load + import of FIXTURE_MODULES, REGISTRY ids ⊇ catalog's REQUIRED ∪ STRUCTURAL ids; mismatch raises before any check runs. | _meta (runner-side, no fixture row) | STRUCTURAL |
```

### Schema change

Add the `Source Kind` parser field. This is **not** a new catalog column in the markdown — it is inferred by `tools.catalog` from each row's existing `Source` field, with new rows free to declare it explicitly later. Five values:

- `LEAN` — derived from a Lean theorem (matches `*.lean::declaration_name` patterns).
- `PLAN_CONVENTION` — architectural convention, TLICA-aligned but no Lean derivation (matches `Plan convention` source strings).
- `ENGINEERING_HYPOTHESIS` — engineering decision, not theory-derived (matches `Phase 2 v1` / `Phase 3` / `developmental layer` markers).
- `OBSERVED` — observation-only row, regardless of source.
- `DEFERRED` — deferred row, regardless of source.

Inference rules (in `tools/catalog.py`):

```python
def infer_source_kind(source: str, status: str) -> SourceKind:
    # Status overrides if it's a non-row status.
    if status == "OBSERVED":
        return SourceKind.OBSERVED
    if status in ("DEFERRED", "NOT-EXERCISED"):
        return SourceKind.DEFERRED
    src_low = source.lower()
    # Lean: matches *.lean::* pattern.
    if "::" in source and ".lean" in src_low:
        return SourceKind.LEAN
    # Engineering: explicit Phase 2 v1 / Phase 3 / developmental markers.
    if any(marker in src_low for marker in (
        "phase 2 v1", "phase 3", "developmental layer", "phase 2 v1.1",
        "phase 2 v1.2", "engineering hypothesis"
    )):
        return SourceKind.ENGINEERING_HYPOTHESIS
    # Default for plan-convention-style sources.
    if "convention" in src_low or "plan" in src_low:
        return SourceKind.PLAN_CONVENTION
    return SourceKind.PLAN_CONVENTION
```

Add `--source-kind` filter to `python -m tools.catalog list`:

```sh
python -m tools.catalog list --source-kind LEAN              # → v0 Lean-derived rows
python -m tools.catalog list --source-kind PLAN_CONVENTION   # → architectural conventions
python -m tools.catalog list --source-kind ENGINEERING_HYPOTHESIS  # → Phase 2 v1+ rows
```

This filter becomes load-bearing in Phase 3 when developmental rows need to be enumerable separately from theory-derived rows.

### Updated summary counts

- REQUIRED: 84 (unchanged)
- STRUCTURAL: 15 (was 11; +I-RT-11, +I-RT-12, +I-TRACE-02, +I-CAT-01)
- NOT-EXERCISED: 3 (unchanged)
- DEFERRED: 12 (unchanged)
- OBSERVED: 1 (unchanged)
- Total tabular entries: 115 (was 111)
- Fixtures: 13 (unchanged — new rows added to existing fixtures)

Banner bumps from `v0.4` to `v0.5`.

## Correctness patches

### P1. Trace fail-open

**Issue.** `FileTracer.record()` can raise: filesystem write failures, disk-full, permission denied, attempted write after close. `tick()` calls `tracer.record(...)` directly at every event boundary. If `record()` raises, the exception propagates up through `tick()`, potentially altering the kernel's control flow or aborting a tick that would otherwise have succeeded. This violates I-TRACE-01's "tracer is observation-only" guarantee — the tracer is supposed to never affect kernel behavior.

The current I-TRACE-01 fixture proves backend equality under normal writable conditions, but does not exercise the failure path.

**Fix.** Wrap every tracer at the factory level via a `SafeTracer` adapter that swallows exceptions in `record()`. `make_tracer_from_env()` returns a `SafeTracer(inner)` by default; explicit construction can opt out via `safe=False` for debugging.

```python
# brain/trace.py

class SafeTracer:
    """Wraps a CognitionTracer so that record/set_tick/clear_tick/close
    failures never propagate. Implements I-TRACE-02.

    The inner tracer's failure is silently swallowed; the kernel must
    not be affected by trace-sink failures. This is the runtime
    enforcement of the I-TRACE-01 observation-only guarantee.
    """

    def __init__(self, inner: CognitionTracer) -> None:
        self._inner = inner

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        try:
            self._inner.record(event_type, payload)
        except Exception:
            pass  # I-TRACE-02: trace sink failures must not propagate.

    def set_tick(self, tick_id: int) -> None:
        try:
            self._inner.set_tick(tick_id)
        except Exception:
            pass

    def clear_tick(self) -> None:
        try:
            self._inner.clear_tick()
        except Exception:
            pass

    def close(self) -> None:
        try:
            self._inner.close()
        except Exception:
            pass


def make_tracer_from_env(*, safe: bool = True) -> CognitionTracer:
    """If BRAIN_TRACE_PATH is set, return SafeTracer(FileTracer(path)).
    Otherwise return SafeTracer(NullTracer()).
    Pass safe=False to opt out of wrapping (debugging only)."""
    path = os.environ.get("BRAIN_TRACE_PATH")
    inner = FileTracer(Path(path)) if path else NullTracer()
    return SafeTracer(inner) if safe else inner
```

**Fixture.** Extend `brain/fixtures/trace_v1_1.py` with an additional check_I_TRACE_02:

```python
class _TracerThatAlwaysRaises:
    def record(self, *args, **kwargs): raise RuntimeError("simulated sink failure")
    def set_tick(self, *args, **kwargs): raise RuntimeError("simulated")
    def clear_tick(self, *args, **kwargs): raise RuntimeError("simulated")
    def close(self, *args, **kwargs): raise RuntimeError("simulated")

@register("I-TRACE-02", fixture="trace_v1_1.py", status="STRUCTURAL")
def check_I_TRACE_02() -> None:
    """Run the scenario with a tracer that raises on every call,
    wrapped in SafeTracer. Output must equal NullTracer baseline."""
    null_result = run_scenario(_load_scenario(), _mock_client(), tracer=NullTracer())
    raising = SafeTracer(_TracerThatAlwaysRaises())
    raising_result = run_scenario(_load_scenario(), _mock_client(), tracer=raising)
    assert null_result.final_state == raising_result.final_state
    assert null_result.mode_trace == raising_result.mode_trace
```

### P2. Single-event tick guard

**Issue.** `tick(state, events: list[PerceptEvent], client, tracer, tick_id)` accepts arbitrarily many events, but v1 semantics are only well-defined for one event per tick. With multiple events:

- `triggered_mode = mode_trace[0]` is arbitrary (first event wins).
- Mode dispatch order matters but is undefined.
- The `TickRecord` reflects an order the kernel didn't commit to.

The scenario file format already enforces one percept per tick. The kernel should match. Multi-event mode aggregation is deferred to a future kickoff (per `PHASE2_v1_KICKOFF.md`'s "Still deferred" list).

Additionally: `TickRecord.tick_index` is currently always set to `0` and stamped later by the scenario runner. This is brittle.

**Fix.** Add guard at the top of `tick()`:

```python
def tick(
    state: BrainState,
    events: list[PerceptEvent],
    client: LLMClient,
    tracer: CognitionTracer = NullTracer(),
    tick_id: int = 0,
) -> tuple[BrainState, TickRecord]:
    if len(events) > 1:
        raise ValueError(
            f"I-RT-11 violated: v1 tick() accepts at most one PerceptEvent; "
            f"got {len(events)}. Multi-event mode aggregation is deferred to a "
            f"future kickoff. See INVARIANT_CATALOG.md."
        )
    # ... existing logic, but propagate tick_id correctly:
    return new_state, TickRecord(tick_index=tick_id, ...)
```

**Fixture.** Extend `brain/fixtures/scenario_v1.py` with:

```python
@register("I-RT-11", fixture="scenario_v1.py", status="STRUCTURAL")
def check_I_RT_11() -> None:
    """tick() with more than one event raises ValueError naming I-RT-11."""
    state = _initial_state()
    events = [_dummy_event("a"), _dummy_event("b")]
    try:
        tick(state, events, _mock_client())
    except ValueError as e:
        assert "I-RT-11" in str(e)
        return
    raise AssertionError("expected ValueError for multi-event tick, got none")
```

### P3. Duplicate `content_id` rejection

**Issue.** `tick()` does not check whether the incoming `PerceptEvent`'s `content_id` already exists in `state.profile.domain`. If a duplicate comes in, behavior is undefined: the new `initial_rho` may overwrite the old value silently at builder time, or `make_profile_with_cogito` may raise with an unhelpful error. Either way, v1 commits to one-shot promotion per content — re-promotion semantics are deferred.

**Fix.** Add guard immediately after the multi-event check:

```python
def tick(state, events, client, tracer=NullTracer(), tick_id=0):
    if len(events) > 1:
        raise ValueError("I-RT-11 violated: ...")

    if events:
        event = events[0]
        if event.content_id in state.profile.domain:
            raise ValueError(
                f"I-RT-12 violated: PerceptEvent.content_id "
                f"{event.content_id!r} is already in state.profile.domain. "
                f"v1 promotion is one-shot per content; update semantics "
                f"for existing content are deferred."
            )
    # ... existing logic
```

**Fixture.** Extend `brain/fixtures/scenario_v1.py`:

```python
@register("I-RT-12", fixture="scenario_v1.py", status="STRUCTURAL")
def check_I_RT_12() -> None:
    """tick() rejects an event whose content_id is already in profile.domain."""
    state, _ = tick(_initial_state(), [_dummy_event("foo")], _mock_client())
    # state.profile.domain now contains {cogito, "foo"}
    try:
        tick(state, [_dummy_event("foo")], _mock_client())
    except ValueError as e:
        assert "I-RT-12" in str(e)
        return
    raise AssertionError("expected ValueError for duplicate content_id, got none")
```

### P4. LLM parser ambiguity

**Issue.** `parse_consistency_eval(raw)` in `brain/llm/parse.py` searches for valid tokens left-to-right and returns the first match. If the LLM emits multiple valid tokens (e.g., `"PRESERVE AND DAMAGE"`, `"Neither preserve nor damage"`, `"DAMAGE, not PRESERVE"`), the parser returns the first one — which may not be the LLM's intended answer. The current behavior makes "wrong but parseable" responses silently succeed.

The prompt asked for *exactly one* word. Multiple matches should be a parse failure.

**Fix.**

```python
# brain/llm/parse.py

def parse_consistency_eval(raw: str) -> ConsistencyEval:
    cleaned = raw.strip().upper()
    if cleaned in _VALID:
        return ConsistencyEval[cleaned]
    found: set[str] = set()
    for token in cleaned.split():
        stripped = token.strip(".,;:!?\"'`*_")
        if stripped in _VALID:
            found.add(stripped)
    if len(found) == 1:
        return ConsistencyEval[found.pop()]
    if len(found) > 1:
        raise ParseError(
            f"Ambiguous response — found multiple valid tokens "
            f"{sorted(found)} in {raw!r}. Expected exactly one of "
            f"PRESERVE / DAMAGE / NEUTRAL."
        )
    raise ParseError(
        f"Could not parse {raw!r} as one of PRESERVE / DAMAGE / NEUTRAL"
    )
```

This tightens I-LLM-01 (the retry shell will treat ambiguous responses as parse failures and retry, just like syntax garbage).

**Fixture.** Extend `brain/fixtures/llm_protocol.py`'s I-LLM-01 check with two new sub-cases:

```python
# Multiple valid tokens → ambiguous → ParseError → retry chain consumed.
mock = MockClient(["PRESERVE AND DAMAGE", "DAMAGE NOT PRESERVE", "PRESERVE"])
ptcns = LLMBackedPtCns(msi, content_texts, client=mock)
assert ptcns.eval("x") == ConsistencyEval.PRESERVE  # third attempt succeeds

# All three attempts ambiguous → final failure.
mock = MockClient(["PRESERVE OR DAMAGE", "NEUTRAL AND PRESERVE", "DAMAGE PRESERVE NEUTRAL"])
ptcns = LLMBackedPtCns(msi, content_texts, client=mock)
try:
    ptcns.eval("x")
except ValueError as e:
    assert "I-LLM-01" in str(e)
```

No new catalog row — this hardens existing I-LLM-01.

### P5. `FutureMSIModel.domain_match` runtime guard

**Issue.** I-APRJ-01 commits `(msi_of P).profile.domain == P.domain` for all P. The v0 stub satisfies this *by construction* because `make_msi(profile=P, ...)` reuses `P`. But there is no runtime assertion. If anyone replaces or extends the stub with a non-conforming implementation, the violation is silent.

**Fix.** Wrap any `Callable[[ScalarProfile], MSI]` in a `FutureMSIModel` class whose `msi_of` method enforces the domain match at runtime:

```python
# brain/tlica/action_projection.py

@dataclass(frozen=True, slots=True)
class FutureMSIModel:
    """Future MSI model wrapper. Enforces I-APRJ-01 at runtime regardless
    of which underlying msi_of stub is supplied.

    Existing v0 stub satisfies the invariant by construction; this
    wrapper makes the runtime check explicit so future replacements
    cannot silently drift.
    """

    _inner: Callable[[ScalarProfile], MSI]

    def msi_of(self, P: ScalarProfile) -> MSI:
        result = self._inner(P)
        if result.profile.domain != P.domain:
            raise ValueError(
                f"I-APRJ-01 violated at runtime: msi_of(P).profile.domain "
                f"({sorted(result.profile.domain)}) != P.domain "
                f"({sorted(P.domain)}). The supplied stub must return an MSI "
                f"whose profile domain equals the input profile's domain."
            )
        return result
```

Then existing fixtures and tick orchestration construct `FutureMSIModel(msi_of_stub)` rather than passing the bare callable.

No new catalog row — this hardens existing I-APRJ-01.

**Fixture.** Extend `brain/fixtures/projected_pce.py`'s I-APRJ-01 check with a runtime-violation case:

```python
def _bad_msi_of(P: ScalarProfile) -> MSI:
    # Deliberately return an MSI with a different profile.domain.
    return make_msi(profile=_other_profile, contents=..., threshold=...)

model = FutureMSIModel(_bad_msi_of)
try:
    model.msi_of(_test_profile)
except ValueError as e:
    assert "I-APRJ-01" in str(e)
```

## Tooling patches

### P6. `tools.catalog` strict count gate

**Issue.** Current `_cmd_counts` prints `!!` for banner-vs-actual mismatches but only sets `ok = False` on `actual != expected`. So a stale banner with correct actual rows prints `!!` next to the banner column and still returns success. This means catalog version drift can sneak past the gate.

**Fix.**

```python
# tools/catalog.py — _cmd_counts

def _cmd_counts(path: Path) -> bool:
    banner = banner_counts(path)
    actual = actual_counts(path)
    expected = EXPECTED_COUNTS  # {REQUIRED: 84, STRUCTURAL: 15, ...}
    ok = True
    for status, e in expected.items():
        b = banner.get(status, 0)
        a = actual.get(status, 0)
        flag = "OK" if (b == a == e) else "!!"
        if not (b == a == e):
            ok = False
        print(f"  {status:14s} banner={b:4d}  actual={a:4d}  expected={e:4d}  {flag}")
    return ok
```

Update `EXPECTED_COUNTS` to v0.5 values: `{"REQUIRED": 84, "STRUCTURAL": 15, "NOT-EXERCISED": 3, "DEFERRED": 12, "OBSERVED": 1}`.

No new catalog row.

### P7. Catalog↔registry coverage audit (+ I-CAT-01)

**Issue.** `brain/invariants.py` imports a hardcoded `FIXTURE_MODULES` list and runs whatever `@register(...)` entries exist. It does not verify every catalog REQUIRED or STRUCTURAL row has a corresponding registered check. A missing registration goes unnoticed — the runner reports "all green" while silently skipping the unregistered row. With Phase 3 adding ~51 new rows, this becomes a real risk.

**Fix.** Generate `brain/_catalog_ids.py` from the catalog and audit at runner startup.

```python
# tools/catalog.py — new subcommand

def _cmd_generate_ids(path: Path, out_path: Path) -> bool:
    rows = parse_catalog(path)
    required = sorted(r.id for r in rows if r.status == "REQUIRED")
    structural = sorted(r.id for r in rows if r.status == "STRUCTURAL")

    content = f'''"""Auto-generated from INVARIANT_CATALOG.md by tools/catalog.py.

DO NOT EDIT BY HAND. Regenerate via:

    python -m tools.catalog generate-ids

This file is the source of truth for I-CAT-01 (every REQUIRED or
STRUCTURAL catalog row has a corresponding @register entry).
"""

EXPECTED_REQUIRED_IDS: frozenset[str] = frozenset({tuple(required)!r})
EXPECTED_STRUCTURAL_IDS: frozenset[str] = frozenset({tuple(structural)!r})
'''
    out_path.write_text(content, encoding="utf-8")
    return True
```

```python
# brain/invariants.py — audit at runner entry

from brain._catalog_ids import EXPECTED_REQUIRED_IDS, EXPECTED_STRUCTURAL_IDS

def _audit_coverage(registry: list[InvariantSpec]) -> list[str]:
    """I-CAT-01: every catalog REQUIRED/STRUCTURAL row has a registered
    check. Returns list of error messages; empty list means coverage is
    complete."""
    registered = frozenset(spec.id for spec in registry)
    missing_required = EXPECTED_REQUIRED_IDS - registered
    missing_structural = EXPECTED_STRUCTURAL_IDS - registered
    errors = []
    if missing_required:
        errors.append(
            f"I-CAT-01 violated: REQUIRED catalog rows missing registration: "
            f"{sorted(missing_required)}"
        )
    if missing_structural:
        errors.append(
            f"I-CAT-01 violated: STRUCTURAL catalog rows missing registration: "
            f"{sorted(missing_structural)}"
        )
    return errors


def run() -> RunReport:
    # Import all fixture modules to populate REGISTRY (existing behavior).
    for mod in FIXTURE_MODULES:
        importlib.import_module(mod)

    # I-CAT-01 audit: must pass before any check runs.
    coverage_errors = _audit_coverage(REGISTRY)
    if coverage_errors:
        raise RuntimeError(
            "I-CAT-01 violated. Catalog rows without registered checks:\n"
            + "\n".join(coverage_errors)
        )

    # ... existing run logic
```

Add to `tools/check_all.sh`:

```bash
# Stage 0: regenerate IDs and verify the generated file matches what's in git.
python -m tools.catalog generate-ids
if ! git diff --quiet brain/_catalog_ids.py; then
    echo "ERROR: brain/_catalog_ids.py is stale. Run 'python -m tools.catalog generate-ids' and commit."
    exit 1
fi
```

`brain/_catalog_ids.py` is committed to the repo as part of v0.5. The check_all.sh stage ensures it stays in sync.

**Catalog row I-CAT-01:** "Every catalog row with status REQUIRED or STRUCTURAL has a registered check; the runner refuses to claim all green if any row is missing registration." STRUCTURAL.

Note: I-CAT-01's "fixture" is `_meta` because the check is enforced at runner entry, not by a fixture-registered function. This is the first non-fixture-owned row in the catalog; document the convention in the catalog's "Validation procedure" section.

## Schema patch

### P8. `Source Kind` enumeration

**Issue.** Catalog rows have a free-text `Source` field. The engineering-vs-theory distinction (load-bearing for Phase 3) is implicit. With ~51 new engineering-hypothesis rows incoming, an explicit enumeration becomes load-bearing.

**Fix.** Add a `SourceKind` enum to `tools/catalog.py` and have the parser infer it from the existing `Source` field (no markdown changes required for existing rows):

```python
# tools/catalog.py

from enum import Enum

class SourceKind(Enum):
    LEAN = "lean"                                # *.lean::* citations
    PLAN_CONVENTION = "plan_convention"          # architectural conventions
    ENGINEERING_HYPOTHESIS = "engineering_hypothesis"  # Phase 2 v1+ / Phase 3
    OBSERVED = "observed"                        # observation-only rows
    DEFERRED = "deferred"                        # deferred rows

def infer_source_kind(source: str, status: str) -> SourceKind:
    # Status-driven overrides.
    if status == "OBSERVED":
        return SourceKind.OBSERVED
    if status in ("DEFERRED", "NOT-EXERCISED"):
        return SourceKind.DEFERRED
    src_low = source.lower()
    # Lean: pattern <file>.lean::<decl>.
    if "::" in source and ".lean" in src_low:
        return SourceKind.LEAN
    # Engineering: explicit Phase 2 v1 / Phase 3 / hypothesis markers.
    engineering_markers = (
        "phase 2 v1", "phase 2 v1.1", "phase 2 v1.2",
        "phase 3", "developmental layer", "engineering hypothesis",
    )
    if any(marker in src_low for marker in engineering_markers):
        return SourceKind.ENGINEERING_HYPOTHESIS
    # Default: plan-convention.
    return SourceKind.PLAN_CONVENTION
```

`InvariantRow` dataclass gains a `source_kind: SourceKind` field, populated by the parser.

Add `--source-kind` filter to `python -m tools.catalog list`:

```python
def _cmd_list(path: Path, status=None, module=None, fixture=None,
              id_prefix=None, source_kind=None) -> bool:
    rows = parse_catalog(path)
    if source_kind:
        rows = [r for r in rows if r.source_kind == SourceKind[source_kind.upper()]]
    # ... existing filters
```

Future Phase 3 rows declare their source kind explicitly via their Source field text (e.g., `Source: Engineering hypothesis (Phase 3.1 Osmotic Chamber)`); the inference rule will pick them up.

**Expected post-patch distribution** for v0.5:

- `LEAN`: ~76 (v0 rows with Lean citations)
- `PLAN_CONVENTION`: ~26 (I-RT-NN, I-PCE-05, I-TRACE-01/02, I-RT-11/12, I-CAT-01, etc.)
- `ENGINEERING_HYPOTHESIS`: ~4 (I-LLM-NN, I-BHV-01)
- `OBSERVED`: 1 (I-LLM-02)
- `DEFERRED`: 12

Exact counts depend on parser inference; verified by `python -m tools.catalog counts --by-source-kind` (new subcommand also added in P8).

No new catalog row.

## Documentation patch

### P9. README v0.4 sync

**Issue.** `README.md` says:

```
INVARIANT_CATALOG.md v0.2:
- 80 REQUIRED runtime assertions
- 7 STRUCTURAL
- 3 NOT-EXERCISED
- 12 DEFERRED
- 11 fixtures

Implement from v0.2 exactly.
```

All of this is stale. Current state is v0.4 (about to be v0.5 after this kickoff).

**Fix.** Update README to:

```
INVARIANT_CATALOG.md v0.5 (Phase 2 v1.2 baseline hardening):
- 84 REQUIRED runtime assertions
- 15 STRUCTURAL
- 3 NOT-EXERCISED
- 12 DEFERRED
- 1 OBSERVED
- 13 fixtures

Implement from the current INVARIANT_CATALOG.md exactly.

History:
- v0.2: initial Lean-bound catalog (Phase 1).
- v0.3: +I-LLM-01/02/03/04, +I-RT-08, +I-BHV-01 (Phase 2 v1 LLM-backed PtCns).
- v0.4: +I-TRACE-01 (Phase 2 v1.1 cognition trace).
- v0.5: +I-RT-11, +I-RT-12, +I-TRACE-02, +I-CAT-01 (Phase 2 v1.2 baseline hardening).

Companion docs:
- PLAN_CORRIGENDA.md (v0 plan corrigenda).
- PHASE2_v1_KICKOFF.md / PHASE2_v1_CORRIGENDA.md (LLM-backed PtCns).
- PHASE2_v1_1_TRACE_KICKOFF.md (cognition trace).
- BASELINE_HARDENING_KICKOFF.md (this document).
```

Remove the "Implement from v0.2 exactly" line. Replace with "Implement from the current INVARIANT_CATALOG.md exactly; the catalog is canonical."

## Build order

Same discipline as v0 and v1: spec first, then code, no shortcuts.

1. **Patch `INVARIANT_CATALOG.md` to v0.5.** Add the four new STRUCTURAL rows in their owning module sections. Bump banner. Update summary counts. Confirm by `python -m tools.catalog counts` showing 84 / 15 / 3 / 12 / 1.
2. **Update `tools/catalog.py`** — add `SourceKind` enum, `infer_source_kind()`, `--source-kind` filter, `generate-ids` subcommand, strict count gate (P6). Bump `EXPECTED_COUNTS` to v0.5 values.
3. **Generate `brain/_catalog_ids.py`** via `python -m tools.catalog generate-ids`. Commit the generated file.
4. **Update `brain/invariants.py`** — add `_audit_coverage()` call at runner entry. Import from `brain._catalog_ids`.
5. **Update `brain/trace.py`** — add `SafeTracer` class. Update `make_tracer_from_env()` to wrap in SafeTracer by default.
6. **Update `brain/tick.py`** — add I-RT-11 and I-RT-12 guards at the top of `tick()`. Propagate `tick_id` to `TickRecord.tick_index`.
7. **Update `brain/llm/parse.py`** — tighten `parse_consistency_eval` to reject ambiguous responses (P4).
8. **Update `brain/tlica/action_projection.py`** — wrap `FutureMSIModel` to runtime-check `domain_match` (P5).
9. **Update `brain/fixtures/trace_v1_1.py`** — add `check_I_TRACE_02` with `_TracerThatAlwaysRaises`.
10. **Update `brain/fixtures/scenario_v1.py`** — add `check_I_RT_11` and `check_I_RT_12`.
11. **Update `brain/fixtures/llm_protocol.py`** — extend `check_I_LLM_01` with ambiguity cases.
12. **Update `brain/fixtures/projected_pce.py`** — extend `check_I_APRJ_01` with bad-stub runtime-violation case.
13. **Update `tools/check_all.sh`** — add stage 0 (regenerate-ids freshness check). Confirm all stages still pass.
14. **Update `README.md`** — sync to v0.5 per P9.

Per v0 discipline: do not start coding until step 1 lands.

## Validation checklist

After all fourteen build-order steps land:

1. `python -m tools.catalog counts` reports 84 / 15 / 3 / 12 / 1 OBSERVED. Banner says `v0.5`. Strict gate fires (exit 1) if any banner/actual/expected divergence exists.
2. `python -m tools.catalog generate-ids` produces a `brain/_catalog_ids.py` byte-identical to the committed version.
3. `python -m tools.catalog list --source-kind ENGINEERING_HYPOTHESIS` returns the ~4 Phase 2 v1+ rows (I-LLM-NN, I-BHV-01). `--source-kind LEAN` returns ~76 v0 rows. `--source-kind PLAN_CONVENTION` returns ~26.
4. `python -m tools.citations verify` → 100/100 (the four new rows have no Lean citations; parser ignores them).
5. `python -m tools.import_audit` → still clean.
6. `python -m brain.invariants run` → all 84 REQUIRED green + 15 STRUCTURAL green + 1 OBSERVED logged.
7. The I-TRACE-02 check confirms three-backend (Null/Memory/File) equality under a `_TracerThatAlwaysRaises` wrapper.
8. The I-RT-11 check confirms multi-event tick raises with "I-RT-11" in the message.
9. The I-RT-12 check confirms duplicate `content_id` raises with "I-RT-12" in the message.
10. The I-CAT-01 audit runs at runner entry. Deliberately omitting a `@register` for some existing REQUIRED row produces "I-CAT-01 violated: ..." with the offending row's ID.
11. The tightened parser rejects ambiguous responses ("PRESERVE AND DAMAGE") as ParseError; the retry shell handles them like syntax garbage.
12. The wrapped `FutureMSIModel` rejects a stub that returns a wrong-domain MSI with "I-APRJ-01" in the error message.
13. `tools/check_all.sh` exits 0 across all stages (including the new stage 0).
14. `README.md` no longer mentions v0.2.

Phase 2 v1.2 is complete when checks 1–14 are all green.

## What this kickoff does *not* change

- The TLICA kernel structural invariants are unchanged.
- All v0/v1/v1.1 REQUIRED rows stay green.
- The `LLMClient` Protocol is unchanged.
- The `CognitionTracer` Protocol is unchanged. `SafeTracer` is a new implementation, not a Protocol change.
- The scenario file format is unchanged.
- COGITO_ID protection is unchanged.
- The dependency graph rule (`builders → validation; invariants → fixtures + validation; tick → builders + invariants`) is preserved; `brain/_catalog_ids.py` is imported by `brain/invariants.py` but is itself a generated module with no further imports (acyclic).
- The `SPEC_UPDATES.md` Lean-refresh protocol is unchanged.
- The roadmap toward Phase 3 (developmental layer) is unchanged in spirit; the synthesis `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.1.md` will be revised to v0.2 *after* this kickoff lands and the traced behavioral CLI is run.

If anything in this kickoff contradicts `INVARIANT_CATALOG.md` v0.5 after patching, the catalog wins.

## After this lands

The path from v0.5 to Phase 3.1:

1. **This kickoff lands.** Catalog at v0.5, all 14 checklist items green.
2. **Real-API traced behavioral CLI run.** `BRAIN_TRACE_PATH=traces/first_scenario_real.jsonl python -m brain.scenario run scenarios/first_scenario_v1.json`. Inspect: does the LLM correctly classify sunset→PRESERVE, identity-threat→DAMAGE, weather→NEUTRAL, self-continuity→PRESERVE? Cache behavior correct? No retries on the first run? Latencies reasonable?
3. **Synthesis v0.2.** `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md` revises the v0.1 synthesis to reflect: corrected v0.5 baseline, worldlet-before-REPL phase ordering, refined REQUIRED / STRUCTURAL / OBSERVED status mix, `SubstrateHistory` in Phase 3.1 scope, the `SourceKind` filter availability for Phase 3 row management, and whatever the traced behavioral CLI revealed.
4. **`PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md`.** First Phase 3 kickoff. Locks the formulas (stability, salience, prediction_gain), the bucketing convention, the two primitive probes, the substrate history store, and the first deterministic chamber scenario. Plan + corrigenda before code, as always.

Nothing builds at step 4 until step 3 is reviewed and the chamber kickoff is corrigenda-clean.
