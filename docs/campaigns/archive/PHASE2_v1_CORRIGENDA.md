# PHASE2_v1_CORRIGENDA.md — Phase 2 v1 Implementation Plan

Read alongside the Phase 2 v1 implementation plan and `PHASE2_v1_KICKOFF.md`. This file lists three corrections, four clarifications, and the apply order — ordered by severity. Apply C1–C3 before any code is written; pin C4–C7 in the row-implementer briefing. The plan as written is otherwise faithful to the kickoff spec; this corrigenda exists to close specific gaps surfaced on review.

## Corrections (must apply before coding)

### C1. I-BHV-01 fixture row description must reflect that it tests orchestration, not LLM behavior

**Issue.** The `scenario_v1.py` fixture seeds `MockClient` with each tick's `expected_eval` string. So the fixture's "actual mode trace matches expected_mode" assertion is tautological — the LLM is forced to return the expected answer, and the runner only verifies that the brain's eval→mode→state pipeline maps that forced answer correctly. This is *orchestration verification*, not *behavioral verification*. The runner cannot catch an LLM-behavior mismatch in this fixture.

The real behavioral test happens in the CLI (`python -m brain.scenario run scenarios/first_scenario_v1.json` with a real `AnthropicAPIClient`), which is **not** part of the runner gate. The plan's own verification section confirms this in passing ("This is not part of the runner gate — the fixture already covers I-BHV-01 deterministically with MockClient.").

The catalog row description currently overstates what the runner is checking.

**Fix.** Update the I-BHV-01 row in `INVARIANT_CATALOG.md`:

| Field | Old | New |
|---|---|---|
| Proposition | The scenario's actual mode trace matches its `expected_mode` sequence. | Given a forced eval sequence (via MockClient seeded from `expected_eval`), the resulting mode trace matches `expected_mode`. Verifies the eval→mode→state-update orchestration; *does not* verify LLM behavior. |
| Python assertion | `actual_modes == [tick["expected_mode"] for tick in scenario.ticks]` | (unchanged) |

Add a one-line note under the Behavioral section in the catalog:

> **Note.** I-BHV-01 verifies the brain's deterministic orchestration of eval→mode under controlled MockClient inputs. The actual LLM behavioral check (does the LLM correctly classify the scenario's percepts?) happens in `python -m brain.scenario run …` with a real `AnthropicAPIClient` and is not part of the runner gate.

This is honesty about what the gate proves. The CLI remains the place where real LLM behavior is exercised.

### C2. Default LLM model string is legacy

**Issue.** The plan specifies `AnthropicAPIClient.__init__(..., model: str = "claude-sonnet-4-5", ...)`. As of May 2026, `claude-sonnet-4-5` is a legacy model — the current Sonnet generation is Sonnet 4.6 (per Anthropic's published model list). Sonnet 4.5 is still functional with a retirement date not sooner than Sept 29, 2026, but defaulting new code to a model on a retirement path is a footgun.

**Fix.** Set the default to `"claude-sonnet-4-6"`:

```python
class AnthropicAPIClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        base_url: str = "https://api.anthropic.com",
        max_tokens: int = 256,  # see C3
    ) -> None:
        ...
```

The user can still override at construction. If the SDK or API changes the canonical naming again before code lands, verify against `https://docs.claude.com/en/docs/about-claude/models` and pick whatever is current.

### C3. `max_tokens=64` is too tight for retry observability

**Issue.** The plan hardcodes `max_tokens=64` in `AnthropicAPIClient`. The happy-path response (one word: PRESERVE / DAMAGE / NEUTRAL) needs maybe 5 tokens. But the unhappy path — where the LLM ignores instructions and emits a verbose explanation — gets truncated at 64 tokens, which kills the retry feedback loop's usefulness. The retry prompt template includes `Your response was: {raw}`; if `raw` is truncated mid-sentence, the LLM doesn't know what's wrong, and the retry is less likely to recover.

**Fix.** Bump `max_tokens` to 256 (still tiny by API standards; cost impact negligible):

```python
max_tokens: int = 256
```

Add a docstring note:

```python
# max_tokens=256: enough budget for verbose failure responses so the
# retry feedback loop can include the LLM's actual bad output verbatim.
# Happy path uses ~5 tokens; the headroom is for retry observability.
```

## Clarifications (pin in the row-implementer briefing)

### C4. Rename `max_retries` → `max_attempts`, or document the semantics

**Issue.** The plan uses `max_retries: int = 3` and then iterates `for attempt in range(self._max_retries):`. With `range(3)`, this is **3 total attempts**, not 1 initial + 3 retries. The naming is ambiguous — "retries" conventionally means "after the first attempt." A reader could reasonably expect 4 total attempts.

**Fix.** Either:
- Rename `max_retries` → `max_attempts` everywhere (cleaner; matches semantics);
- Or keep the name and add a docstring explicit about the convention:

```python
def __init__(
    self,
    msi: MSI,
    content_texts: Mapping[ContentID, str],
    client: LLMClient,
    max_retries: int = 3,
) -> None:
    """...

    max_retries: Total number of attempts (NOT additional attempts after
    the first). With max_retries=3, the LLM is called up to 3 times;
    after the 3rd parse failure, ValueError is raised. The fixture
    `llm_protocol.py::check_I_LLM_01` exercises this with
    MockClient(["nonsense", "still bad", "PRESERVE"]) — third attempt
    succeeds, two parse failures consumed.
    """
```

Recommendation: rename. It's a one-token change with no semantic impact and removes the footgun for any future implementer.

### C5. `triggered_mode: ModeOp | None` — pin "None means no events" for v1

**Issue.** `TickRecord.triggered_mode` is typed `ModeOp | None`. The plan doesn't say when it's None. With v1's scenario format (one percept per tick), this is unambiguous in practice, but the field invites confusion when multi-percept-per-tick is eventually un-deferred.

**Fix.** Pin the v1 semantics explicitly in the `TickRecord` docstring:

```python
@dataclass(frozen=True, slots=True)
class TickRecord:
    """...

    triggered_mode: The single mode dispatched in this tick. None if
    `events` was empty (a no-op tick). In v1, the scenario format
    constrains every tick to exactly one PerceptEvent, so
    triggered_mode == mode_trace[0] when events is non-empty.
    Multi-percept-per-tick semantics are out of scope for v1; a future
    catalog patch will define dominance rules if needed.
    """
    ...
    mode_trace: tuple[ModeOp, ...]
    triggered_mode: ModeOp | None
```

This puts the v1-only assumption on the field rather than scattered in tick logic.

### C6. `assert_state_invariants` is a maintenance contract

**Issue.** `brain/tick.py::assert_state_invariants(state)` re-asserts roughly half the v0.2 REQUIRED rows inline (I-PROF-01/02, I-MSI-01..06, I-PTC-01..05, I-MOD-04, I-IBND-01..04, I-RT-02/03/04/07). If a future catalog patch adds new I-RT-NN rows whose semantics are "must hold over live tick state," this function has to be updated in lockstep. Otherwise, the catalog will say "REQUIRED" but the live state checker will silently skip it.

**Fix.** Add a docstring at the top of `assert_state_invariants` that names this contract explicitly:

```python
def assert_state_invariants(state: BrainState) -> None:
    """Re-assert all runtime-applicable v0.2 REQUIRED invariants against
    live BrainState. Called once per tick by `tick(...)`.

    MAINTENANCE CONTRACT: This function mirrors the subset of
    INVARIANT_CATALOG.md rows whose semantics are 'must hold over the
    live runtime state' (as opposed to 'enforced by construction at
    builder time'). When a new I-RT-NN or runtime-applicable row lands
    in the catalog, add the corresponding assertion here. The runner
    fixtures check rows against hand-built fixture data; this function
    checks the same rows against post-tick state.

    The current row set covered:
      - I-PROF-01/02 (profile domain == values, values in [0, 1])
      - I-MSI-01..06 (MSI consistency and cogito membership)
      - I-PTC-01..05 (PtCns total, cogito always PRESERVE, partition)
      - I-MOD-04 (cogito mode is MODE_C)
      - I-IBND-01..04 (boundary = pos ∪ neg)
      - I-RT-02 (post-tick profile values in [0, 1])
      - I-RT-03 (MSI density: positive_contents and cogito in MSI)
      - I-RT-04 (PtCns total over profile.domain)
      - I-RT-07 (cogito at value 1 in profile)

    Raises ValueError naming the violated row on failure.
    """
```

Same maintenance contract should be mentioned in a one-line comment in `INVARIANT_CATALOG.md` near the I-RT-08 row, so future authors know where to look:

> *(I-RT-08 is enforced by `brain/tick.py::assert_state_invariants`. New runtime-applicable rows must be added there too.)*

### C7. `LLMBackedPtCns._cache` lifecycle — pin "per-instance, per-tick"

**Issue.** The plan mentions `_cache: dict[ContentID, ConsistencyEval]` and also says "rebuild LLMBackedPtCns if MSI membership changed." That implies the cache can be rebuilt within a tick — but the plan doesn't say whether the cache persists across ticks. The reader might assume it does. It doesn't: each call to `tick()` constructs a fresh `LLMBackedPtCns` (line: "Construct an LLMBackedPtCns(msi=new_msi, content_texts=new_registry.texts, client=client)").

**Fix.** Add a docstring at the top of `LLMBackedPtCns`:

```python
class LLMBackedPtCns:
    """LLM-backed PtCns implementation.

    Cache lifecycle: The internal `_cache` is per-instance and per-tick.
    Each `tick(...)` call constructs a fresh LLMBackedPtCns; the cache
    starts seeded only with {COGITO_ID: PRESERVE} (I-LLM-03). Across-
    tick determinism — same prompt → same response, even across runs —
    is provided by `CachedClient` at the LLM transport layer, not here.

    Rationale: MSI membership changes between ticks alter the prompt
    context (the list of existing MSI contents in the PROMPT_TEMPLATE),
    so a prompt for content X under MSI = {cogito, A} is semantically
    different from a prompt for content X under MSI = {cogito, A, B}.
    Caching at the LLM-prompt-hash level (CachedClient) handles this
    correctly because different prompts → different cache keys.
    """
```

This makes the two cache layers explicit and prevents future confusion.

## Apply order

1. Apply **C1–C3** to the plan text before any module is written. C2 in particular: update the AnthropicAPIClient default model string to `claude-sonnet-4-6` and `max_tokens` to 256.
2. Pin **C4–C7** in the briefing for whoever implements the modules (`brain-row-implementer` subagent, or Claude Code directly). These are docstring/clarification edits — no behavior change.
3. After Phase 2 v1 lands and reports green, M8 from PLAN_CORRIGENDA.md (the mypy gate) is still on the table. The new `brain/llm/` package is exactly the kind of code where strict typing would catch real bugs (Protocol method-signature drift, `Mapping` vs `dict` confusion, `Fraction` vs `float`). Adding `mypy --strict brain/ tools/` between stages 2 and 3 of `check_all.sh` is still the cheapest place to slot it.

## What this corrigenda does *not* change

- The build order (catalog patch first, then io_types, then brain/llm/, then tick.py, then scenario.py, then fixtures) is correct.
- The functional `tick(state, events, client) → (BrainState, TickRecord)` API is correct.
- The `PtCnsLike` Protocol seam in `brain/tlica/ptcns.py` is correct.
- The 5-column → 7-column extension of the Cross-cutting table is correct.
- The OBSERVED status as a new catalog category is correct.
- The dual-runner pattern (MockClient in fixtures for determinism, CachedClient + AnthropicAPIClient in CLI for real LLM exercise) is correct in shape — just needs C1's honest framing.
- The use of `urllib.request` rather than the SDK (no new runtime dep) is correct.
- All inherited deferrals from v0.2 stay deferred.

If anything in this corrigenda contradicts `INVARIANT_CATALOG.md` v0.3 after patching, the catalog wins.

## Validation checklist for Claude Code (after applying)

1. `python -m tools.catalog show I-BHV-01` prints the updated row description (orchestration verification, not behavioral).
2. `grep "claude-sonnet-4-6" brain/llm/client.py` returns a hit; `grep "claude-sonnet-4-5" brain/llm/client.py` returns no hits.
3. `grep "max_tokens" brain/llm/client.py` shows 256, not 64.
4. `python -c "from brain.llm.ptcns_backed import LLMBackedPtCns; help(LLMBackedPtCns)"` shows the cache lifecycle docstring.
5. `python -c "from brain.tick import assert_state_invariants; help(assert_state_invariants)"` shows the maintenance contract docstring.
6. Either: `grep "max_attempts" brain/llm/ptcns_backed.py` returns a hit (rename applied), OR the `max_retries` docstring explicitly states "Total number of attempts (NOT additional attempts after the first)" (documentation applied).
7. `TickRecord.triggered_mode` field has a v1-semantics docstring naming "None if events was empty."
